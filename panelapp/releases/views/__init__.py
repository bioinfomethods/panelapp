from datetime import timedelta
from typing import cast

from django.db import (
    models,
    transaction,
)
from django.db.models import (
    Count,
    Q,
)
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
)
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
)
from django_htmx.http import push_url

from accounts.views.decorators import require_gel_reviewer
from panelapp.components import (
    CheckBox,
    CheckBoxFilter,
    Facet,
    FacetGroup,
    HtmxParams,
    SearchBar,
    SortableTableHeader,
)
from releases.forms import ReleaseForm
from releases.models import (
    Release,
    ReleaseDeployment,
)
from releases.tasks import deploy_release
from releases.utils import (
    paginate,
    parse_sort_field,
)


@require_gel_reviewer
@require_GET
def release_list_view(request: HttpRequest) -> HttpResponse:
    releases = Release.objects.annotate(
        panel_count=models.Count("panels")
    ).prefetch_related("deployment")

    order_by = request.GET.get("order_by", "-created")
    releases = releases.order_by(order_by)

    if request.GET.get("deployment") is not None:
        q_deployment = Q()
        for deployment in request.GET.getlist("deployment"):
            match deployment:
                case "pending":
                    q_deployment |= Q(deployment__isnull=True) | Q(
                        deployment__end__isnull=True
                    )
                case "done":
                    q_deployment |= Q(deployment__end__isnull=False)
                case _:
                    raise ValueError("Invalid release deployment status")
        releases = releases.filter(q_deployment)

    if request.GET.get("search"):
        releases = releases.filter(name__icontains=request.GET.get("search"))

    page, page_range = paginate(releases, 20, int(request.GET.get("page", 1)))

    url = reverse("releases:list")

    sort_field, sort_direction = parse_sort_field(order_by)

    context = {
        "url": url,
        "name_header": SortableTableHeader(
            field="name",
            hx_get=url,
            hx_include="closest form",
            sort=sort_direction if sort_field == "name" else None,
        ),
        "created_header": SortableTableHeader(
            field="created",
            hx_get=url,
            hx_include="closest form",
            sort=sort_direction if sort_field == "created" else None,
        ),
        "facets": FacetGroup(
            id="facets",
            facets=[
                Facet(
                    CheckBoxFilter(
                        label="Deployment",
                        checkboxes=[
                            CheckBox(
                                name="deployment",
                                value="pending",
                                label="pending",
                                checked="pending"
                                in request.GET.getlist("deployment", []),
                                htmx=HtmxParams(
                                    get=url,
                                    include="closest form",
                                    indicator=".loading,.loaded",
                                    swap="none",
                                    sync="closest form:abort",
                                ),
                            ),
                            CheckBox(
                                name="deployment",
                                value="done",
                                label="done",
                                checked="done" in request.GET.getlist("deployment", []),
                                htmx=HtmxParams(
                                    get=url,
                                    include="closest form",
                                    indicator=".loading,.loaded",
                                    swap="none",
                                    sync="closest form:abort",
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        "releases": page,
        "page_range": page_range,
        "searchbar": SearchBar(
            id="releases-search",
            name="search",
            value=request.GET.get("search", ""),
            label="Search",
            placeholder="Search",
            page=page,
            object_name_plural="releases",
            htmx=HtmxParams(
                get=url,
                include="closest form",
                trigger="keyup changed delay:300ms",
                indicator=".loading,.loaded",
                swap="none",
                sync="closest form:abort",
            ),
        ),
    }

    if request.htmx:  # type: ignore
        if request.GET.values():
            return push_url(
                TemplateResponse(request, "release/list.html", context),
                f"{url}?{request.GET.urlencode()}",
            )
        return TemplateResponse(request, "release/list.html", context)

    return TemplateResponse(request, "release/list.html", context)


@require_gel_reviewer
@require_http_methods(["GET", "POST"])
def release_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ReleaseForm(request.POST)
        if form.is_valid():
            release = form.save()
            return redirect(release)
    else:
        form = ReleaseForm()
    return TemplateResponse(request, "release/create.html", context={"form": form})


@require_gel_reviewer
@require_GET
def release_detail_view(request: HttpRequest, pk: str) -> HttpResponse:
    release = get_object_or_404(
        Release.objects.filter(pk=pk)
        .prefetch_related("deployment")
        .annotate(
            sign_off_count=Count("releasepanel", distinct=True),
            promote_count=Count(
                "releasepanel", filter=Q(releasepanel__promote=True), distinct=True
            ),
        )
    )

    return TemplateResponse(request, "release/detail.html", {"release": release})


@require_gel_reviewer
@require_http_methods(["GET", "POST"])
def release_edit_view(request: HttpRequest, pk: str) -> HttpResponse:
    release = get_object_or_404(
        Release.objects.filter(pk=pk).prefetch_related("deployment")
    )

    if request.method == "POST":
        form = ReleaseForm(request.POST, instance=release)
        if form.is_valid():
            release = form.save()
            return redirect(release)
    else:
        form = ReleaseForm(instance=release)
    return TemplateResponse(
        request, "release/edit.html", context={"release": release, "form": form}
    )


@require_gel_reviewer
@require_http_methods(["GET", "POST"])
@transaction.atomic
def release_deployment_view(request: HttpRequest, pk: str):
    release = get_object_or_404(
        Release.objects.filter(pk=pk).annotate(
            panel_count=Count("releasepanel", distinct=True)
        )
    )

    if request.method == "POST":
        try:
            deployment = cast(ReleaseDeployment, release.deployment)  # type: ignore
        except ReleaseDeployment.DoesNotExist:
            deployment = ReleaseDeployment(release=release, start=timezone.now())
            deployment.save()
            release.deployment = deployment  # type: ignore
        else:
            if deployment.timed_out():
                # Allow retry on time out
                deployment.start = timezone.now()
            else:
                return HttpResponseBadRequest("Release already deployed")

        deploy_release.delay(pk=pk, user_pk=request.user.pk)

    return TemplateResponse(
        request, "release/deployment/detail.html", {"release": release}
    )


@require_gel_reviewer
@require_GET
def release_deployment_status_view(request: HttpRequest, pk: str):
    release = get_object_or_404(Release.objects.filter(pk=pk))

    try:
        release.deployment  # type: ignore
    except ReleaseDeployment.DoesNotExist:
        raise Http404
    return TemplateResponse(
        request, "release/deployment/status.html", {"release": release}
    )

import csv
import io
from dataclasses import dataclass
from typing import (
    Any,
    Sequence,
    cast,
)

import tablib
from django.core.paginator import Paginator
from django.db import (
    DatabaseError,
    transaction,
)
from django.db.models import F
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import (
    DetailView,
    FormView,
)
from django_htmx.http import push_url
from import_export.formats.base_formats import CSV

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
from panelapp.mixins import GELReviewerRequiredMixin
from panels.models import (
    GenePanel,
    PanelType,
)
from releases import domain_logic
from releases.forms import ReleasePanelsImportForm
from releases.models import (
    Release,
    ReleaseDeployment,
    ReleasePanel,
    ReleasePanelQuerySet,
    convert,
)
from releases.resources import ReleasePanelResource
from releases.utils import (
    paginate,
    parse_sort_field,
)


@require_gel_reviewer
@require_GET
def release_panels_list_view(request: HttpRequest, pk: str) -> HttpResponse:
    release = get_object_or_404(Release.objects.filter(pk=pk))

    url = reverse_lazy("releases:releasepanel-list", args=(pk,))

    types = (
        PanelType.objects.filter(genepanel__genepanelsnapshot__release=release)
        .order_by("name")
        .distinct()
    )
    statuses = (
        GenePanel.objects.filter(genepanelsnapshot__release=release)
        .distinct("status")
        .order_by("status")
        .values_list("status", flat=True)
    )

    release_panels = cast(
        ReleasePanelQuerySet,
        ReleasePanel.objects.filter(release=release)
        .annotate(
            signed_off_before_major=F("deployment__signed_off_before__major_version"),
            signed_off_before_minor=F("deployment__signed_off_before__minor_version"),
            signed_off_after_major=F("deployment__signed_off_after__major_version"),
            signed_off_after_minor=F("deployment__signed_off_after__minor_version"),
        )
        .prefetch_related(
            "panel",
            "panel__panel",
            "panel__panel__types",
            "deployment",
            "deployment__before",
            "deployment__after",
        ),
    )

    order_by = request.GET.get("order_by", "name")
    sort_field, sort_direction = parse_sort_field(order_by)
    release_panels = release_panels.search(
        search=request.GET.get("search"),
        statuses=request.GET.getlist("status"),
        types=request.GET.getlist("type"),
        order_by=order_by,
    )

    page, page_range = paginate(release_panels, 20, int(request.GET.get("page", 1)))

    try:
        release.deployment  # type: ignore
    except ReleaseDeployment.DoesNotExist:
        release_panels = Page(
            [
                domain_logic.ReleasePanelDeploymentHistory(
                    before=convert(x), after=x.as_deployed()
                )
                for x in page
            ],
            number=page.number,
            paginator=page.paginator,
        )
    else:
        release_panels = Page(
            [
                domain_logic.ReleasePanelDeploymentHistory(
                    before=domain_logic.ReleasePanel(
                        release=convert(release),
                        panel=domain_logic.PanelSnapshot(
                            panel_id=x.panel.panel.pk,
                            name=x.deployment.before.data["name"],
                            version=domain_logic.Version(
                                major=x.deployment.before.major_version,
                                minor=x.deployment.before.minor_version,
                            ),
                            signed_off=(
                                domain_logic.Version(
                                    major=x.signed_off_before_major,
                                    minor=x.signed_off_before_minor,
                                )
                                if x.signed_off_before_major
                                else None
                            ),
                            status=x.panel.panel.status,
                            types={x.name for x in x.panel.panel.types.all()},
                            comment=x.panel.version_comment,
                        ),
                        promote=x.promote,
                    ),
                    after=domain_logic.ReleasePanel(
                        release=convert(release),
                        panel=domain_logic.PanelSnapshot(
                            panel_id=x.panel.panel.pk,
                            name=x.deployment.after.data["name"],
                            version=domain_logic.Version(
                                major=x.deployment.after.major_version,
                                minor=x.deployment.after.minor_version,
                            ),
                            signed_off=(
                                domain_logic.Version(
                                    major=x.signed_off_after_major,
                                    minor=x.signed_off_after_minor,
                                )
                                if x.signed_off_after_major
                                else None
                            ),
                            status=x.panel.panel.status,
                            types={x.name for x in x.panel.panel.types.all()},
                            comment=x.panel.version_comment,
                        ),
                        promote=x.promote,
                    ),
                )
                for x in page
            ],
            number=page.number,
            paginator=page.paginator,
        )

    ctx = {
        "url": url,
        "release": release,
        "name_header": SortableTableHeader(
            field="name",
            hx_get=url,
            hx_include="closest form",
            sort=sort_direction if sort_field == "name" else None,
        ),
        "facets": FacetGroup(
            id="facets",
            facets=[
                Facet(
                    CheckBoxFilter(
                        label="Status",
                        checkboxes=[
                            CheckBox(
                                name="status",
                                value=status,
                                label=status,
                                checked=status in request.GET.getlist("status", []),
                                htmx=HtmxParams(
                                    get=url,
                                    include="closest form",
                                    indicator=".loading,.loaded",
                                    swap="none",
                                    sync="closest form:abort",
                                ),
                            )
                            for status in statuses
                        ],
                    )
                ),
                Facet(
                    CheckBoxFilter(
                        label="Type",
                        checkboxes=[
                            CheckBox(
                                name="type",
                                value=type_.slug,
                                label=type_.name,
                                checked=type_.slug in request.GET.getlist("type", []),
                                htmx=HtmxParams(
                                    get=url,
                                    include="closest form",
                                    indicator=".loading,.loaded",
                                    swap="none",
                                    sync="closest form:abort",
                                ),
                            )
                            for type_ in types
                        ],
                    )
                ),
            ],
        ),
        "releasepanels": release_panels,
        "page_range": page_range,
        "searchbar": SearchBar(
            id="panels-search",
            name="search",
            value=request.GET.get("search", ""),
            label="Search",
            placeholder="Search",
            page=page,
            object_name_plural="panels",
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

    if request.htmx:
        if request.GET.values():
            return push_url(
                TemplateResponse(request, "release/releasepanels/list.html", ctx),
                f"{reverse_lazy('releases:releasepanel-list', args=(pk,))}?{request.GET.urlencode()}",
            )
        return TemplateResponse(request, "release/releasepanels/list.html", ctx)

    return TemplateResponse(request, "release/releasepanels/list.html", ctx)


@require_gel_reviewer
@require_GET
def release_panels_export_view(request: HttpRequest, pk: str) -> StreamingHttpResponse:
    release = get_object_or_404(Release.objects.filter(pk=pk))

    rows: list[dict] = []
    try:
        release.deployment  # type: ignore
    except ReleaseDeployment.DoesNotExist:
        filename = (
            f"{release.name}-panels-before-{timezone.now().strftime('%Y%m%d-%H%M')}.csv"
        )

        for release_panel in release.releasepanel_set.annotate(  # type: ignore
            signed_off_major=F("panel__panel__signed_off__major_version"),
            signed_off_minor=F("panel__panel__signed_off__minor_version"),
        ).prefetch_related(
            "panel",
            "panel__panel",
        ):
            command = domain_logic.DeployReleasePanel(
                created_at=timezone.now(), release_panel=convert(release_panel)
            )
            release_deployment = command()
            if release_panel.signed_off_major is None:
                signed_off_before = ""
            else:
                signed_off_before = (
                    f"{release_panel.signed_off_major}.{release_panel.signed_off_minor}"
                )
            rows.append(
                {
                    "Panel ID": release_panel.panel.panel.pk,
                    "Promote": repr(release_panel.promote).lower(),
                    "Signed Off (Before)": signed_off_before,
                    "Signed Off (After)": str(release_deployment.signed_off),
                    "Comment (Before)": release_panel.panel.version_comment,
                    "Comment (After)": release_deployment.release_panel.panel.comment,
                }
            )
    else:
        filename = (
            f"{release.name}-panels-after-{timezone.now().strftime('%Y%m%d-%H%M')}.csv"
        )

        for release_panel in release.releasepanel_set.annotate(  # type: ignore
            signed_off_before_major=F("deployment__signed_off_before__major_version"),
            signed_off_before_minor=F("deployment__signed_off_before__minor_version"),
            signed_off_after_major=F("deployment__signed_off_after__major_version"),
            signed_off_after_minor=F("deployment__signed_off_after__minor_version"),
        ).prefetch_related(
            "deployment",
            "panel",
            "panel__panel",
        ):
            if release_panel.signed_off_before_major is None:
                signed_off_before = ""
            else:
                signed_off_before = f"{release_panel.signed_off_before_major}.{release_panel.signed_off_before_minor}"
            rows.append(
                {
                    "Panel ID": release_panel.panel.panel.pk,
                    "Promote": repr(release_panel.promote).lower(),
                    "Signed Off (Before)": signed_off_before,
                    "Signed Off (After)": f"{release_panel.signed_off_after_major}.{release_panel.signed_off_after_minor}",
                    "Comment (Before)": release_panel.deployment.comment_before,
                    "Comment (After)": release_panel.deployment.comment_after,
                }
            )

    writer = csv.DictWriter(
        EchoWriter(),
        fieldnames=[
            "Panel ID",
            "Promote",
            "Signed Off (Before)",
            "Signed Off (After)",
            "Comment (Before)",
            "Comment (After)",
        ],
    )
    response = StreamingHttpResponse(
        [writer.writeheader()] + [writer.writerow(row) for row in rows],
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


class EchoWriter(object):
    def write(self, value):
        return value


class ReleasePanelsImportView(GELReviewerRequiredMixin, FormView, DetailView):
    template_name = "release/releasepanels/import.html"
    model = Release
    form_class = ReleasePanelsImportForm

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        # Combination of FormView and DetailView get() method
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(object=self.object))

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        # Combination of FormView and DetailView post() method
        self.object = self.get_object()
        try:
            self.object.deployment  # type: ignore
        except ReleaseDeployment.DoesNotExist:
            pass
        else:
            return HttpResponseBadRequest("Release has been deployed")

        form = self.get_form()
        if form.is_valid():
            try:
                Release.objects.select_for_update(nowait=True).get(pk=self.object.pk)
            except DatabaseError:
                return HttpResponseBadRequest("Release in use")

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "formats": [CSV],
                "resources": [ReleasePanelResource],
                "instance": self.object,
            }
        )
        return kwargs

    def form_valid(self, form):
        resource = ReleasePanelResource(self.object)
        resource.import_data(
            tablib.import_set(
                stream=io.TextIOWrapper(
                    form.cleaned_data["import_file"], encoding="utf-8"
                ),
                format=dict(form.fields["format"].choices)[form.cleaned_data["format"]],
            ),
            use_transactions=True,
            raise_errors=True,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("releases:releasepanel-list", args=(self.object.pk,))


@dataclass
class Page:
    """
    Copy of django.core.paginator.Page that can be used for
    non django-types.
    """

    object_list: Sequence[Any]
    number: int
    paginator: Paginator

    def __repr__(self):
        return "<Page %s of %s>" % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError(
                "Page indices must be integers or slices, not %s."
                % type(index).__name__
            )
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)

    def start_index(self):
        """
        Return the 1-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """
        Return the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page

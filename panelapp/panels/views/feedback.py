from functools import wraps
from typing import Any

from django.contrib import messages
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import PermissionDenied
from django.db.models import (
    Case,
    Count,
    F,
    When,
)
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_safe,
)

from panels.forms import (
    GeneReadyForm,
    GeneReviewForm,
    PanelGeneForm,
    RegionReadyForm,
    STRReadyForm,
)
from panels.forms.ajax import (
    EditCommentForm,
    UpdateGeneMOIForm,
    UpdateGeneMOPForm,
    UpdateGenePhenotypesForm,
    UpdateGenePublicationsForm,
    UpdateGeneRatingForm,
    UpdateGeneTagsForm,
    UpdateRegionMOIForm,
    UpdateRegionPhenotypesForm,
    UpdateRegionPublicationsForm,
    UpdateRegionRatingForm,
    UpdateRegionTagsForm,
    UpdateSTRMOIForm,
    UpdateSTRPhenotypesForm,
    UpdateSTRPublicationsForm,
    UpdateSTRRatingForm,
    UpdateSTRTagsForm,
)
from panels.forms.region import PanelRegionForm
from panels.forms.region_review import RegionReviewForm
from panels.forms.str import PanelSTRForm
from panels.forms.strreview import STRReviewForm
from panels.models import (
    STR,
    Comment,
    GenePanelEntrySnapshot,
    GenePanelSnapshot,
    Region,
)


def get_gene_or_404(pk: str, entity_name: str) -> GenePanelEntrySnapshot:
    return get_object_or_404(
        GenePanelEntrySnapshot.objects.filter(
            panel__panel__pk=pk,
            gene_core__gene_symbol=entity_name,
        )
        .annotate(
            entity_tags=ArrayAgg("tags__name", distinct=True),
            number_of_green_evaluations=Count(
                Case(When(evaluation__rating="GREEN", then=F("evaluation"))),
                distinct=True,
            ),
            number_of_red_evaluations=Count(
                Case(When(evaluation__rating="RED", then=F("evaluation"))),
                distinct=True,
            ),
            evaluators=ArrayAgg("evaluation__user_id"),
            number_of_evaluations=Count("evaluation", distinct=True),
        )
        .prefetch_related("panel", "panel__panel", "gene_core")
    )


def get_str_or_404(pk: str, entity_name: str) -> STR:
    return get_object_or_404(
        STR.objects.filter(
            panel__panel__pk=pk,
            name=entity_name,
        )
        .annotate(
            entity_tags=ArrayAgg("tags__name", distinct=True),
            number_of_green_evaluations=Count(
                Case(When(evaluation__rating="GREEN", then=F("evaluation"))),
                distinct=True,
            ),
            number_of_red_evaluations=Count(
                Case(When(evaluation__rating="RED", then=F("evaluation"))),
                distinct=True,
            ),
            evaluators=ArrayAgg("evaluation__user_id"),
            number_of_evaluations=Count("evaluation", distinct=True),
        )
        .prefetch_related("panel", "panel__panel")
    )


def get_region_or_404(pk: str, entity_name: str) -> Region:
    return get_object_or_404(
        Region.objects.filter(
            panel__panel__pk=pk,
            name=entity_name,
        )
        .annotate(
            entity_tags=ArrayAgg("tags__name", distinct=True),
            number_of_green_evaluations=Count(
                Case(When(evaluation__rating="GREEN", then=F("evaluation"))),
                distinct=True,
            ),
            number_of_red_evaluations=Count(
                Case(When(evaluation__rating="RED", then=F("evaluation"))),
                distinct=True,
            ),
            evaluators=ArrayAgg("evaluation__user_id"),
            number_of_evaluations=Count("evaluation", distinct=True),
        )
        .prefetch_related("panel", "panel__panel")
    )


PanelEntity = GenePanelEntrySnapshot | STR | Region


def get_entity_or_404(pk: str, entity_type: str, entity_name: str) -> PanelEntity:
    match entity_type:
        case "gene":
            return get_gene_or_404(pk, entity_name)
        case "str":
            return get_str_or_404(pk, entity_name)
        case "region":
            return get_region_or_404(pk, entity_name)
        case _:
            raise Http404


def panel_gene_detail_context(
    user,
    gene: GenePanelEntrySnapshot,
    form_initial: dict[str, Any],
    panel_genes: list[dict[str, Any]],
) -> dict[str, Any]:
    is_admin = user.is_authenticated and user.reviewer.is_GEL()
    cgi = [g.get("pk") for g in panel_genes].index(gene.pk)
    return {
        "entity_name": gene.gene_core.gene_symbol,
        "sharing_panels": GenePanelSnapshot.objects.get_shared_panels(
            gene.name, all=is_admin, internal=is_admin
        ),
        "form": GeneReviewForm(
            user=user,
            gene=gene,
            initial=form_initial,
        ),
        "form_edit": PanelGeneForm(
            user=user,
            instance=gene,
            initial=gene.get_form_initial(),
            panel=gene.panel.panel,
        ),
        "entity_ready_form": GeneReadyForm(user=user, instance=gene, initial={}),
        "edit_entity_tags_form": UpdateGeneTagsForm(user=user, instance=gene),
        "edit_entity_mop_form": UpdateGeneMOPForm(user=user, instance=gene),
        "edit_entity_moi_form": UpdateGeneMOIForm(user=user, instance=gene),
        "edit_entity_phenotypes_form": UpdateGenePhenotypesForm(
            user=user, instance=gene
        ),
        "edit_entity_publications_form": UpdateGenePublicationsForm(
            user=user, instance=gene
        ),
        "edit_entity_rating_form": UpdateGeneRatingForm(user=user, instance=gene),
        "next_gene": (None if cgi == len(panel_genes) - 1 else panel_genes[cgi + 1]),
        "prev_gene": None if cgi == 0 else panel_genes[cgi - 1],
        "feedback_review_parts": [
            "Rating",
            "Mode of inheritance",
            "Mode of pathogenicity",
            "Publications",
            "Phenotypes",
        ],
    }


def panel_str_detail_context(
    user,
    str_: STR,
    form_initial: dict[str, Any],
    panel_strs: list[dict[str, Any]],
) -> dict[str, Any]:
    is_admin = user.is_authenticated and user.reviewer.is_GEL()
    cgi = [g.get("pk") for g in panel_strs].index(str_.pk)
    return {
        "entity_name": str_.name,
        "sharing_panels": GenePanelSnapshot.objects.get_shared_panels(
            str_.name, all=is_admin, internal=is_admin
        ),
        "form": STRReviewForm(
            user=user,
            str_item=str_,
            initial=form_initial,
        ),
        "form_edit": PanelSTRForm(
            user=user,
            instance=str_,
            initial=str_.get_form_initial(),
            panel=str_.panel.panel,
        ),
        "entity_ready_form": STRReadyForm(user=user, instance=str_, initial={}),
        "edit_entity_tags_form": UpdateSTRTagsForm(user=user, instance=str_),
        "edit_entity_moi_form": UpdateSTRMOIForm(user=user, instance=str_),
        "edit_entity_phenotypes_form": UpdateSTRPhenotypesForm(
            user=user, instance=str_
        ),
        "edit_entity_publications_form": UpdateSTRPublicationsForm(
            user=user, instance=str_
        ),
        "edit_entity_rating_form": UpdateSTRRatingForm(user=user, instance=str_),
        "next_str": (None if cgi == len(panel_strs) - 1 else panel_strs[cgi + 1]),
        "prev_str": None if cgi == 0 else panel_strs[cgi - 1],
        "feedback_review_parts": [
            "Rating",
            "Mode of inheritance",
            "Publications",
            "Phenotypes",
        ],
    }


def panel_region_detail_context(
    user,
    region: Region,
    form_initial: dict[str, Any],
    panel_regions: list[dict[str, Any]],
) -> dict[str, Any]:
    is_admin = user.is_authenticated and user.reviewer.is_GEL()
    cgi = [g.get("pk") for g in panel_regions].index(region.pk)
    return {
        "entity_name": region.name,
        "sharing_panels": GenePanelSnapshot.objects.get_shared_panels(
            region.name, all=is_admin, internal=is_admin
        ),
        "form": RegionReviewForm(
            user=user,
            region=region,
            initial=form_initial,
        ),
        "form_edit": PanelRegionForm(
            user=user,
            instance=region,
            initial=region.get_form_initial(),
            panel=region.panel.panel,
        ),
        "entity_ready_form": RegionReadyForm(user=user, instance=region, initial={}),
        "edit_entity_tags_form": UpdateRegionTagsForm(user=user, instance=region),
        "edit_entity_moi_form": UpdateRegionMOIForm(user=user, instance=region),
        "edit_entity_phenotypes_form": UpdateRegionPhenotypesForm(
            user=user, instance=region
        ),
        "edit_entity_publications_form": UpdateRegionPublicationsForm(
            user=user, instance=region
        ),
        "edit_entity_rating_form": UpdateRegionRatingForm(user=user, instance=region),
        "next_region": (
            None if cgi == len(panel_regions) - 1 else panel_regions[cgi + 1]
        ),
        "prev_region": None if cgi == 0 else panel_regions[cgi - 1],
        "feedback_review_parts": [
            "Rating",
            "Mode of inheritance",
            "Mode of pathogenicity",
            "Publications",
            "Phenotypes",
        ],
    }


def panel_entity_detail_context(
    request: HttpRequest, user, entity_type: str, entity: PanelEntity
) -> dict[str, Any]:
    ctx = {
        "request": request,
        "entity": entity,
        "entity_name": entity.name,
        "entity_type": entity_type,
        "panel": entity.panel,
        "next_str": None,
        "prev_str": None,
        "next_gene": None,
        "prev_gene": None,
        "next_region": None,
        "prev_region": None,
        "updated": None,
        "panel_genes": list(
            entity.panel.get_all_genes_extra.values(
                "pk", "gene", "evaluators", "number_of_evaluations", "saved_gel_status"
            )
        ),
        "panel_strs": list(
            entity.panel.get_all_strs_extra.values(
                "pk",
                "gene",
                "name",
                "evaluators",
                "number_of_evaluations",
                "saved_gel_status",
            )
        ),
        "panel_regions": list(
            entity.panel.get_all_regions_extra.values(
                "pk",
                "gene",
                "name",
                "verbose_name",
                "evaluators",
                "number_of_evaluations",
                "saved_gel_status",
            )
        ),
    }

    form_initial = {}
    if user.is_authenticated:
        user_review = entity.review_by_user(user)
        if user_review:
            form_initial = user_review.dict_tr()
            form_initial["comments"] = None

    match entity:
        case GenePanelEntrySnapshot():
            ctx |= panel_gene_detail_context(
                user, entity, form_initial=form_initial, panel_genes=ctx["panel_genes"]
            )
        case STR():
            ctx |= panel_str_detail_context(
                user, entity, form_initial=form_initial, panel_strs=ctx["panel_strs"]
            )
        case Region():
            ctx |= panel_region_detail_context(
                user,
                entity,
                form_initial=form_initial,
                panel_regions=ctx["panel_regions"],
            )

    return ctx


@require_safe
def panel_entity_detail_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


def require_verified_reviewer(func):
    """
    Decorator to make a view only allow verified reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.reviewer.is_verified()):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner


def require_gel_reviewer(func):
    """
    Decorator to make a view only allow GEL reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.reviewer.is_GEL()):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner


def require_gel_or_verified_reviewer(func):
    """
    Decorator to make a view only allow GEL or verified reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (
            request.user.is_authenticated
            and (request.user.reviewer.is_GEL() or request.user.reviewer.is_verified())
        ):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner


@require_gel_or_verified_reviewer
@require_GET
def delete_entity_comment_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str, comment_pk: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.delete_comment(comment_pk, request.user)

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_tags_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = UpdateGeneTagsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case STR():
            form = UpdateSTRTagsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case Region():
            form = UpdateRegionTagsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()

    if is_valid:
        entity = form.save()
        ctx = panel_entity_detail_context(
            request=request, user=request.user, entity_type=entity_type, entity=entity
        ) | {"updated": timezone.now().strftime("%H:%M:%S")}
    else:
        ctx = panel_entity_detail_context(
            request=request, user=request.user, entity_type=entity_type, entity=entity
        ) | {"edit_entity_tags_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_rating_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = UpdateGeneRatingForm(
                user=request.user, instance=entity, data=request.POST
            )
        case STR():
            form = UpdateSTRRatingForm(
                user=request.user, instance=entity, data=request.POST
            )
        case Region():
            form = UpdateRegionRatingForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()

    if is_valid:
        entity = form.save()
        ctx = panel_entity_detail_context(
            request=request, user=request.user, entity_type=entity_type, entity=entity
        )
    else:
        ctx = panel_entity_detail_context(
            request=request, user=request.user, entity_type=entity_type, entity=entity
        ) | {"edit_entity_rating_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_moi_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = UpdateGeneMOIForm(
                user=request.user, instance=entity, data=request.POST
            )
        case STR():
            form = UpdateSTRMOIForm(
                user=request.user, instance=entity, data=request.POST
            )
        case Region():
            form = UpdateRegionMOIForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()
    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    if is_valid:
        form.save()
        messages.success(request, "Successfully updated mode of inheritance")
    else:
        ctx |= {"edit_entity_moi_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_mop_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_gene_or_404(pk, entity_name)

    form = UpdateGeneMOPForm(user=request.user, instance=entity, data=request.POST)
    is_valid = form.is_valid()
    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    if is_valid:
        form.save()
        messages.success(request, "Successfully updated mode of pathogenicity")
    else:
        ctx |= {"edit_entity_mop_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_publications_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = UpdateGenePublicationsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case STR():
            form = UpdateSTRPublicationsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case Region():
            form = UpdateRegionPublicationsForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()
    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    if is_valid:
        form.save()
        messages.success(request, "Successfully updated publications")
    else:
        ctx |= {"edit_entity_publications_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def update_entity_phenotypes_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = UpdateGenePhenotypesForm(
                user=request.user, instance=entity, data=request.POST
            )
        case STR():
            form = UpdateSTRPhenotypesForm(
                user=request.user, instance=entity, data=request.POST
            )
        case Region():
            form = UpdateRegionPhenotypesForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()
    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    if is_valid:
        form.save()
    else:
        ctx |= {"edit_entity_phenotypes_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_POST
def toggle_entity_ready_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    match entity:
        case GenePanelEntrySnapshot():
            form = GeneReadyForm(user=request.user, instance=entity, data=request.POST)
        case STR():
            form = STRReadyForm(user=request.user, instance=entity, data=request.POST)
        case Region():
            form = RegionReadyForm(
                user=request.user, instance=entity, data=request.POST
            )
        case _:
            raise ValueError("Invalid entity")

    is_valid = form.is_valid()
    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    if is_valid:
        form.save()
    else:
        ctx |= {"edit_entity_ready_form": form}

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_publications_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.panel.increment_version()
    entity.publications = []
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_phenotypes_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.panel.increment_version()
    entity.phenotypes = []
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_mode_of_pathogenicity_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_gene_or_404(pk, entity_name)

    entity.panel.increment_version()
    entity.mode_of_pathogenicity = ""
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_transcript_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_gene_or_404(pk, entity_name)

    entity.panel.increment_version()
    entity.transcript = []
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_sources_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.panel.increment_version()
    entity.clear_evidences(user=request.user)
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_source_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str, source: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.panel.increment_version()
    entity.clear_evidences(user=request.user, evidence=source)
    entity.save()

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_reviewer
@require_GET
def clear_entity_source_for_entity_list_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str, source: str
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.panel.increment_version()
    entity.clear_evidences(user=request.user, evidence=source)
    entity.save()

    ctx = {"panel": entity.panel, "entities": entity.panel.get_all_entities_extra}

    return TemplateResponse(request, "panels/entities_list_table.html", ctx)


@require_gel_or_verified_reviewer
@require_GET
def delete_evaluation_by_user_view(
    request: HttpRequest,
    pk: str,
    entity_type: str,
    entity_name: str,
    evaluation_pk: str,
) -> HttpResponse:
    entity = get_entity_or_404(pk, entity_type, entity_name)

    entity.delete_evaluation(evaluation_pk, request.user)
    entity.save()

    # Refresh cached properties
    entity = get_entity_or_404(pk, entity_type, entity_name)

    ctx = panel_entity_detail_context(
        request=request, user=request.user, entity_type=entity_type, entity=entity
    )

    return TemplateResponse(request, "panels/genepanelsnapshot_detail.html", ctx)


@require_gel_or_verified_reviewer
@require_GET
def edit_entity_comment_form_view(
    request: HttpRequest, pk: str, entity_type: str, entity_name: str, comment_pk: str
):
    entity = get_entity_or_404(pk, entity_type, entity_name)
    comment = Comment.objects.get(pk=comment_pk)
    if comment.user != request.user:
        raise PermissionDenied

    edit_comment_form = EditCommentForm(initial={"comment": comment.comment})
    return TemplateResponse(
        request,
        "panels/entity/edit_comment.html",
        {
            "edit_comment_form": edit_comment_form,
            "panel_id": entity.panel.panel.pk,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "comment_pk": comment_pk,
        },
    )

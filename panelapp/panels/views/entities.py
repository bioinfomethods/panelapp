##
## Copyright (c) 2016-2019 Genomics England Ltd.
##
## This file is part of PanelApp
## (see https://panelapp.genomicsengland.co.uk).
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
from django.contrib import messages
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    get_list_or_404,
    redirect,
)
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)

from panelapp.mixins import (
    GELReviewerRequiredMixin,
    VerifiedReviewerRequiredMixin,
)
from panels.forms import (
    GeneReadyForm,
    GeneReviewForm,
    PanelGeneForm,
    PanelRegionForm,
    PanelSTRForm,
    RegionReadyForm,
    RegionReviewForm,
    STRReadyForm,
    STRReviewForm,
)
from panels.forms.ajax import (
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
from panels.mixins import (
    ActAndRedirectMixin,
    PanelMixin,
)
from panels.models import (
    STR,
    Gene,
    GenePanel,
    GenePanelEntrySnapshot,
    GenePanelSnapshot,
    Region,
    Tag,
)


class EchoWriter(object):
    def write(self, value):
        return value


class EntityMixin:
    def is_gene(self):
        return "gene" == self.kwargs["entity_type"]

    def is_str(self):
        return "str" == self.kwargs["entity_type"]

    def is_region(self):
        return "region" == self.kwargs["entity_type"]

    def get_object(self):
        try:
            if self.is_gene():
                if self.request.GET.get("pk"):
                    return self.panel.get_gene_by_pk(
                        self.request.GET.get("pk"), prefetch_extra=True
                    )
                else:
                    return self.panel.get_gene(
                        self.kwargs["entity_name"], prefetch_extra=True
                    )
            elif self.is_str():
                return self.panel.get_str(
                    self.kwargs["entity_name"], prefetch_extra=True
                )
            elif self.is_region():
                return self.panel.get_region(
                    self.kwargs["entity_name"], prefetch_extra=True
                )
        except GenePanelEntrySnapshot.DoesNotExist:
            raise Http404


class ModifyEntityCommonMixin(EntityMixin):
    entity_name = None

    def get_form_class(self):
        if self.is_gene():
            return PanelGeneForm
        elif self.is_str():
            return PanelSTRForm
        elif self.is_region():
            return PanelRegionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["panel"] = self.panel
        kwargs["user"] = self.request.user
        if self.object:
            kwargs["initial"] = self.object.get_form_initial()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["panel"] = self.panel
        return ctx

    @property
    def panel(self):
        return GenePanel.objects.get_active_panel(pk=self.kwargs["pk"])

    def get_success_url(self):
        return reverse_lazy(
            "panels:evaluation",
            kwargs={
                "pk": self.kwargs["pk"],
                "entity_type": self.kwargs["entity_type"],
                "entity_name": self.entity_name,
            },
        )


class PanelAddEntityView(
    ModifyEntityCommonMixin, VerifiedReviewerRequiredMixin, CreateView
):
    def get_template_names(self):
        if self.is_gene():
            return "panels/genepanel_add_gene.html"
        elif self.is_str():
            return "panels/genepanel_add_str.html"
        elif self.is_region():
            return "panels/genepanel_add_region.html"

    def form_valid(self, form):
        label = ""
        if self.is_gene():
            form.save_gene()
            self.entity_name = form.cleaned_data["gene"].gene_symbol
            label = "gene: {}".format(self.entity_name)

        elif self.is_str():
            form.save_str()
            self.entity_name = form.cleaned_data["name"]
            label = "STR: {}".format(self.entity_name)

        elif self.is_region():
            form.save_region()
            self.entity_name = form.cleaned_data["name"]
            label = "Region: {}".format(self.entity_name)

        ret = super().form_valid(form)
        msg = "Successfully added a new {} to the panel {}".format(
            label, self.panel.panel.name
        )
        messages.success(self.request, msg)
        return ret


class PanelEditEntityView(
    ModifyEntityCommonMixin, GELReviewerRequiredMixin, UpdateView
):
    def get_template_names(self):
        if self.is_gene():
            return "panels/gene_edit.html"
        elif self.is_str():
            return "panels/str_edit.html"
        elif self.is_region():
            return "panels/region_edit.html"

    def form_valid(self, form):
        label = ""
        if self.is_gene():
            form.save_gene()
            self.entity_name = form.cleaned_data["gene"].gene_symbol
            label = "gene: {}".format(self.entity_name)
        elif self.is_str():
            form.save_str()
            self.entity_name = form.cleaned_data["name"]
            label = "STR: {}".format(self.entity_name)
        elif self.is_region():
            form.save_region()
            self.entity_name = form.cleaned_data["name"]
            label = "region: {}".format(self.entity_name)
        ret = super().form_valid(form)
        msg = "Successfully changed gene information for panel {}".format(
            label, self.panel.panel.name
        )
        messages.success(self.request, msg)
        return ret


class PanelMarkNotReadyView(
    GELReviewerRequiredMixin, PanelMixin, ActAndRedirectMixin, DetailView
):
    model = GenePanelSnapshot

    def act(self):
        self.get_object().mark_entities_not_ready()


class EntityReviewView(VerifiedReviewerRequiredMixin, EntityMixin, UpdateView):
    context_object_name = "entity"

    def get_form_class(self):
        if self.is_gene():
            return GeneReviewForm
        elif self.is_str():
            return STRReviewForm
        elif self.is_region():
            return RegionReviewForm

    def get_template_names(self):
        return "panels/entity/evaluation_create.html"

    def get_object(self):
        if self.is_gene():
            return self.panel.get_gene(self.kwargs["entity_name"], prefetch_extra=True)
        elif self.is_str():
            return self.panel.get_str(self.kwargs["entity_name"], prefetch_extra=True)
        elif self.is_region():
            return self.panel.get_region(
                self.kwargs["entity_name"], prefetch_extra=True
            )

    @cached_property
    def panel(self):
        return GenePanel.objects.get_active_panel(pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        if self.is_gene():
            kwargs["gene"] = self.object
        elif self.is_str():
            kwargs["str_item"] = self.object
        elif self.is_region():
            kwargs["region"] = self.object

        if not kwargs["initial"]:
            kwargs["initial"] = {}
            if self.request.user.is_authenticated:
                user_review = self.object.review_by_user(self.request.user)
                if user_review:
                    kwargs["initial"] = user_review.dict_tr()
                    kwargs["initial"]["comments"] = None
        kwargs["instance"] = None
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["panel"] = self.panel.panel
        ctx["entity_name"] = self.kwargs["entity_name"]
        ctx["entity_type"] = self.kwargs["entity_type"]
        return ctx

    def form_valid(self, form):
        ret = super().form_valid(form)
        if self.is_gene():
            msg = "Successfully reviewed gene {}".format(self.kwargs["entity_name"])
        elif self.is_str():
            msg = "Successfully reviewed STR {}".format(self.kwargs["entity_name"])
        elif self.is_region():
            msg = "Successfully reviewed region {}".format(self.kwargs["entity_name"])
        messages.success(self.request, msg)
        return ret

    def get_success_url(self):
        return reverse_lazy(
            "panels:evaluation",
            kwargs={
                "pk": self.kwargs["pk"],
                "entity_type": self.kwargs["entity_type"],
                "entity_name": self.kwargs["entity_name"],
            },
        )


class EntityDetailView(DetailView):
    """List panels current gene belongs to

    URL: /panels/entities/:entity_name

    Also lists # of reviews, MOI, sources, tags, and phenotypes for the entity
    in that panel"""

    model = Gene
    context_object_name = "gene"
    template_name = "panels/gene_detail.html"

    def get_object(self, queryset=None):
        try:
            return self.model.objects.get(gene_symbol=self.kwargs["entity_name"])
        except self.model.DoesNotExist:
            # try STR
            try:
                return get_list_or_404(STR, name=self.kwargs["entity_name"])[0]
            except Http404:
                # try region
                return get_list_or_404(Region, name=self.kwargs["entity_name"])[0]

    def get_context_data(self, *args, **kwargs):
        """Context data for Gene Detail page"""

        ctx = super().get_context_data(*args, **kwargs)
        tag_filter = self.request.GET.get("tag_filter", None)
        entity_name = self.kwargs["entity_name"]
        ctx["tag_filter"] = tag_filter
        ctx["gene_symbol"] = entity_name

        statuses = [GenePanel.STATUS.public, GenePanel.STATUS.promoted]
        is_admin_user = (
            self.request.user.is_authenticated and self.request.user.reviewer.is_GEL()
        )

        if is_admin_user:
            statuses.append(GenePanel.STATUS.internal)

        gps = list(
            GenePanelSnapshot.objects.get_shared_panels(
                entity_name, all=is_admin_user, internal=is_admin_user
            ).values_list("pk", flat=True)
        )

        entries_genes = GenePanelEntrySnapshot.objects.get_gene_panels(
            entity_name, pks=gps
        ).annotate(
            superpanels_names=ArrayAgg(
                "panel__genepanelsnapshot__level4title__name",
                filter=Q(panel__genepanelsnapshot__panel__status__in=statuses),
                distinct=True,
            )
        )

        if isinstance(self.object, STR):
            # we couldn't find a gene linked to this STR, lookup by name
            entries_strs = STR.objects.get_str_panels(name=entity_name, pks=gps)
        else:
            entries_strs = STR.objects.get_gene_panels(gene_symbol=entity_name, pks=gps)

        entries_strs = entries_strs.annotate(
            superpanels_names=ArrayAgg(
                "panel__genepanelsnapshot__level4title__name",
                filter=Q(panel__genepanelsnapshot__panel__status__in=statuses),
                distinct=True,
            )
        )

        if isinstance(self.object, Region):
            # we couldn't find a gene linked to this STR, lookup by name
            entries_regions = Region.objects.get_region_panels(
                name=entity_name, pks=gps
            )
        else:
            entries_regions = Region.objects.get_gene_panels(
                gene_symbol=entity_name, pks=gps
            )

        entries_regions = entries_regions.annotate(
            superpanels_names=ArrayAgg(
                "panel__genepanelsnapshot__level4title__name",
                filter=Q(panel__genepanelsnapshot__panel__status__in=statuses),
                distinct=True,
            )
        )

        if (
            not self.request.user.is_authenticated
            or not self.request.user.reviewer.is_GEL()
        ):
            entries_genes = entries_genes.filter(
                Q(panel__panel__status=GenePanel.STATUS.public)
                | Q(panel__panel__status=GenePanel.STATUS.promoted)
            )
            entries_strs = entries_strs.filter(
                Q(panel__panel__status=GenePanel.STATUS.public)
                | Q(panel__panel__status=GenePanel.STATUS.promoted)
            )
            entries_regions = entries_regions.filter(
                Q(panel__panel__status=GenePanel.STATUS.public)
                | Q(panel__panel__status=GenePanel.STATUS.promoted)
            )

        if tag_filter:
            entries_genes = entries_genes.filter(tag__name=tag_filter)
            entries_strs = entries_strs.filter(tag__name=tag_filter)
            entries_regions = entries_regions.filter(tag__name=tag_filter)

        ctx["entries_genes"] = entries_genes
        ctx["entries_strs"] = entries_strs
        ctx["entries_regions"] = entries_regions

        ctx["entries"] = (
            list(entries_genes) + list(entries_strs) + list(entries_regions)
        )

        return ctx


class EntitiesListView(ListView):
    model = Gene
    context_object_name = "entities"
    template_name = "panels/gene_list.html"

    def get_queryset(self, *args, **kwargs):
        is_admin_user = (
            self.request.user.is_authenticated and self.request.user.reviewer.is_GEL()
        )
        tag_filter = self.request.GET.get("tag", "")

        panel_ids = GenePanelSnapshot.objects.get_active(
            all=is_admin_user, internal=is_admin_user
        ).values_list("pk", flat=True)

        qs = GenePanelEntrySnapshot.objects.filter(
            gene_core__active=True, panel__in=panel_ids
        )

        strs_qs = STR.objects.filter(panel__in=panel_ids)
        regions_qs = Region.objects.filter(panel__in=panel_ids)

        if tag_filter:
            qs = qs.filter(tags__name=tag_filter)
            strs_qs = strs_qs.filter(tags__name=tag_filter)
            regions_qs = regions_qs.filter(tags__name=tag_filter)

        entities = []
        for gene in (
            qs.order_by()
            .distinct("gene_core__gene_symbol")
            .values_list("gene_core__gene_symbol", flat=True)
            .iterator()
        ):
            entities.append(("gene", gene, gene))

        for str_item in strs_qs.values_list("name", "name").iterator():
            entities.append(("str", str_item[0], str_item[1]))

        for region in regions_qs.values_list("name", "name").iterator():
            entities.append(("region", region[0], region[1]))

        entities = list(set(entities))

        sorted_entities = sorted(entities, key=lambda i: i[1].lower())
        return sorted_entities

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["tags"] = Tag.objects.all().order_by("name")
        ctx["tag_filter"] = self.request.GET.get("tag")
        return ctx


class GeneDetailRedirectView(RedirectView):
    """Redirect /panels/genes/<gene> to /panels/entities/<entity>"""

    def dispatch(self, request, *args, **kwargs):
        self.url = reverse_lazy(
            "panels:entity_detail", kwargs={"entity_name": self.kwargs["entity_name"]}
        )
        return super().dispatch(request, *args, **kwargs)


class RedirectGenesToEntities(RedirectView):
    """Redirect URL schema which was supported before, i.e. /panels/<pk>/<gene_symbol>"""

    def dispatch(self, request, *args, **kwargs):
        self.url = reverse_lazy(
            "panels:evaluation",
            kwargs={
                "pk": self.kwargs["pk"],
                "entity_type": "gene",
                "entity_name": self.kwargs["entity_name"],
            },
        )
        return super().dispatch(request, *args, **kwargs)

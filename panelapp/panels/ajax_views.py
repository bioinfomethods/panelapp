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
from django.shortcuts import (
    redirect,
    render,
)
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic.base import View
from django_ajax.mixin import AJAXMixin

from panelapp.mixins import (
    GELReviewerRequiredMixin,
    VerifiedReviewerRequiredMixin,
)

from .forms.ajax import EditCommentForm
from .models import (
    Comment,
    GenePanel,
    GenePanelSnapshot,
)
from .views.entities import EntityMixin


class BaseAjaxGeneMixin:
    """Abstract Base Ajax Mixin with methods used by other views.

    Any GET or POST request will call `process` method on the child class or
    throws NotImprementedError in case the method isn't defined
    """

    def process(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        return self.process()

    def post(self, request, *args, **kwargs):
        return self.process()

    @cached_property
    def panel(self):
        return GenePanel.objects.get(pk=self.kwargs["pk"]).active_panel

    @property
    def is_admin(self):
        return (
            self.request.user.is_authenticated and self.request.user.reviewer.is_GEL()
        )


class PanelAjaxMixin(BaseAjaxGeneMixin):
    template_name = "panels/genepanel_list_table.html"

    def return_data(self):
        if self.request.user.is_authenticated and self.request.user.reviewer.is_GEL():
            panels = GenePanelSnapshot.objects.get_active(all=True, internal=True)
        else:
            panels = GenePanelSnapshot.objects.get_active()
        ctx = {"panels": panels, "view_panels": panels}
        table = render(self.request, self.template_name, ctx)
        return {
            "inner-fragments": {"#panels_table": table, "#panels_count": len(panels)}
        }


class DeletePanelAjaxView(GELReviewerRequiredMixin, PanelAjaxMixin, AJAXMixin, View):
    def process(self):
        panel = GenePanel.objects.get(pk=self.kwargs["pk"])
        panel.status = GenePanel.STATUS.deleted
        panel.save()
        panel.add_activity(self.request.user, "Panel deleted")
        return self.return_data()


class RejectPanelAjaxView(GELReviewerRequiredMixin, PanelAjaxMixin, AJAXMixin, View):
    def process(self):
        GenePanel.objects.get(pk=self.kwargs["pk"]).reject()
        return self.return_data()


class ApprovePanelAjaxView(GELReviewerRequiredMixin, PanelAjaxMixin, AJAXMixin, View):
    def process(self):
        GenePanel.objects.get(pk=self.kwargs["pk"]).approve()
        return self.return_data()


class DeleteEntityAjaxView(
    EntityMixin, GELReviewerRequiredMixin, BaseAjaxGeneMixin, AJAXMixin, View
):
    def get_template_names(self):
        return "panels/entities_list_table.html"

    def process(self):
        if self.is_gene():
            self.panel.delete_gene(self.kwargs["entity_name"], True, self.request.user)
        elif self.is_str():
            self.panel.delete_str(self.kwargs["entity_name"], True, self.request.user)
        elif self.is_region():
            self.panel.delete_region(
                self.kwargs["entity_name"], True, self.request.user
            )

        del self.panel
        return self.return_data()

    def return_data(self):
        ctx = {"panel": self.panel, "entities": self.panel.get_all_entities_extra}
        table = render(self.request, self.get_template_names(), ctx)
        return {"inner-fragments": {"#entities_table": table}}


class ApproveEntityAjaxView(
    GELReviewerRequiredMixin, BaseAjaxGeneMixin, AJAXMixin, View
):
    template_name = "panels/entities_list_table.html"

    def process(self):
        if self.is_gene():
            self.panel.get_gene(self.kwargs["entity_symbol"]).approve_entity()
        if self.is_str():
            self.panel.get_str(self.kwargs["entity_symbol"]).approve_entity()
        if self.is_region():
            self.panel.get_region(self.kwargs["entity_symbol"]).approve_entity()
        del self.panel

        return self.return_data()

    def return_data(self):
        ctx = {"panel": self.panel, "entities": self.panel.get_all_entities_extra}
        table = render(self.request, self.template_name, ctx)
        return {"inner-fragments": {"#entities_table": table}}  # TODO(Oleg) refactor


class SubmitEntityCommentFormAjaxView(
    VerifiedReviewerRequiredMixin, EntityMixin, BaseAjaxGeneMixin, View
):
    @cached_property
    def object(self):
        return self.get_object()

    def process(self):
        comment = Comment.objects.get(pk=self.kwargs["comment_pk"])
        form = EditCommentForm(data=self.request.POST)
        if form.is_valid() and self.request.user == comment.user:
            self.object.edit_comment(
                comment.pk, self.request.POST.get("comment"), self.request.user
            )

        return self.return_post_data()

    def post(self, request, *args, **kwargs):
        return self.process()

    def return_post_data(self):
        if self.is_gene():
            kwargs = {
                "pk": self.panel.panel.pk,
                "entity_name": self.object.gene.get("gene_symbol"),
                "entity_type": "gene",
            }
        elif self.is_str():
            kwargs = {
                "pk": self.panel.panel.pk,
                "entity_name": self.object.name,
                "entity_type": "str",
            }
        elif self.is_region():
            kwargs = {
                "pk": self.panel.panel.pk,
                "entity_name": self.object.name,
                "entity_type": "region",
            }
        return redirect(reverse_lazy("panels:evaluation", kwargs=kwargs))

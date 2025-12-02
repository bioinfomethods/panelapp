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
import csv
from datetime import datetime
from django.contrib import messages
from django.http import StreamingHttpResponse
from django.template.defaultfilters import pluralize
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView
from django.shortcuts import redirect
from panels.forms import CopySTRForm
from panels.models import GenePanelSnapshot, GenePanel
from .entities import EchoWriter
from panelapp.mixins import GELReviewerRequiredMixin


class DownloadAllSTRs(GELReviewerRequiredMixin, View):
    def strs_iterator(self):
        yield (
            "Name",
            "Chromosome",
            "Position GRCh37 start",
            "Position GRCh37 end",
            "Position GRCh38 start",
            "Position GRCh38 end",
            "Repeated sequence",
            "Normal repeats",
            "Pathogenic repeats",
            "Symbol",
            "Panel Id",
            "Panel Name",
            "Panel Version",
            "Panel Status",
            "List",
            "Sources",
            "Mode of inheritance",
            "Tags",
            "EnsemblId(GRch37)",
            "EnsemblId(GRch38)",
            "Biotype",
            "Phenotypes",
            "GeneLocation(GRch37)",
            "GeneLocation(GRch38)",
            "Panel Types",
            "Super Panel Id",
            "Super Panel Name",
            "Super Panel Version",
        )

        for gps in GenePanelSnapshot.objects.get_active(
            all=True, internal=True
        ).iterator():
            is_super_panel = gps.is_super_panel
            super_panel_id = gps.panel_id
            super_panel_name = gps.level4title.name
            super_panel_version = gps.version

            for entry in gps.get_all_strs_extra:
                color = entry.entity_color_name

                if isinstance(entry.phenotypes, list):
                    phenotypes = ";".join(entry.phenotypes)
                else:
                    phenotypes = "-"

                row = [
                    entry.name,
                    entry.chromosome,
                    entry.position_37.lower if entry.position_37 else "",
                    entry.position_37.upper if entry.position_37 else "",
                    entry.position_38.lower,
                    entry.position_38.upper,
                    entry.repeated_sequence,
                    entry.normal_repeats,
                    entry.pathogenic_repeats,
                    entry.gene.get("gene_symbol") if entry.gene else "-",
                    entry.panel.panel.pk,
                    entry.panel.level4title.name,
                    entry.panel.version,
                    str(entry.panel.panel.status).upper(),
                    color,
                    ";".join([evidence.name for evidence in entry.evidence.all()]),
                    entry.moi,
                    ";".join([tag.name for tag in entry.tags.all()]),
                    entry.gene.get("ensembl_genes", {})
                    .get("GRch37", {})
                    .get("82", {})
                    .get("ensembl_id", "-")
                    if entry.gene
                    else "-",
                    entry.gene.get("ensembl_genes", {})
                    .get("GRch38", {})
                    .get("90", {})
                    .get("ensembl_id", "-")
                    if entry.gene
                    else "-",
                    entry.gene.get("biotype", "-") if entry.gene else "-",
                    phenotypes,
                    entry.gene.get("ensembl_genes", {})
                    .get("GRch37", {})
                    .get("82", {})
                    .get("location", "-")
                    if entry.gene
                    else "-",
                    entry.gene.get("ensembl_genes", {})
                    .get("GRch38", {})
                    .get("90", {})
                    .get("location", "-")
                    if entry.gene
                    else "-",
                    ";".join([t.name for t in entry.panel.panel.types.all()]),
                    super_panel_id if is_super_panel else "-",
                    super_panel_name if is_super_panel else "-",
                    super_panel_version if is_super_panel else "-",
                ]
                yield row

    def get(self, request, *args, **kwargs):
        pseudo_buffer = EchoWriter()
        writer = csv.writer(pseudo_buffer, delimiter="\t")

        response = StreamingHttpResponse(
            (writer.writerow(row) for row in self.strs_iterator()),
            content_type="text/tab-separated-values",
        )
        attachment = "attachment; filename=All_strs_{}.tsv".format(
            datetime.now().strftime("%Y%m%d-%H%M")
        )
        response["Content-Disposition"] = attachment
        return response


class CopySTRView(GELReviewerRequiredMixin, FormView):
    template_name = "panels/copy_str.html"
    form_class = CopySTRForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["str_name"] = self.kwargs["str_name"]
        kwargs["user"] = self.request.user
        kwargs["source_panel_id"] = self.kwargs["pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["str_name"] = self.kwargs["str_name"]
        ctx["source_panel"] = source_panel = GenePanel.objects.get_panel(
            pk=str(self.kwargs["pk"])
        ).active_panel
        ctx["source_str_entry"] = source_panel.get_str(
            self.kwargs["str_name"], prefetch_extra=True
        )
        ctx["entity_type"] = "str"
        return ctx

    def form_valid(self, form):
        form.copy_str_to_panels()
        panel_count = len(form.cleaned_data["target_panels"])
        msg = "STR copy initiated for {} panel{}. The operation is processing in the background.".format(
            panel_count,
            pluralize(panel_count),
        )
        messages.success(self.request, msg)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "panels:entity_detail", kwargs={"slug": self.kwargs["str_name"]}
        )

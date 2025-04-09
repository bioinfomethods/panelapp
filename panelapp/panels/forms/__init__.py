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
from django import forms
from django.db import transaction

from panels.models import (
    GenePanel,
    ProcessingRunCode,
)
from panels.tasks.reviews import background_copy_reviews

from .activity import ActivityFilterForm
from .geneready import GeneReadyForm  # noqa
from .genereview import GeneReviewForm  # noqa
from .panel import PanelForm  # noqa
from .panelgene import PanelGeneForm  # noqa
from .promotepanel import PromotePanelForm  # noqa
from .region import PanelRegionForm  # noqa
from .region_ready import RegionReadyForm  # noqa
from .region_review import RegionReviewForm  # noqa
from .str import PanelSTRForm  # noqa
from .str_ready import STRReadyForm  # noqa
from .strreview import STRReviewForm  # noqa
from .uploads import UploadGenesForm  # noqa
from .uploads import UploadPanelsForm  # noqa
from .uploads import UploadReviewsForm  # noqa


class ComparePanelsForm(forms.Form):
    panels = GenePanel.objects.none()
    panel_1 = forms.ModelChoiceField(
        queryset=panels, widget=forms.Select(attrs={"class": "form-control"})
    )
    panel_2 = forms.ModelChoiceField(
        queryset=panels, widget=forms.Select(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        qs = None

        try:
            qs = kwargs.pop("panels")
        except KeyError:
            pass

        super(ComparePanelsForm, self).__init__(*args, **kwargs)
        if qs:
            self.fields["panel_1"].queryset = qs
            self.fields["panel_2"].queryset = qs


class CopyReviewsForm(forms.Form):
    panel_1 = forms.CharField(required=True, widget=forms.widgets.HiddenInput())
    panel_2 = forms.CharField(required=True, widget=forms.widgets.HiddenInput())

    def copy_reviews(self, user, gene_symbols, panel_from, panel_to):
        if len(panel_to.current_genes) > 1000 or len(panel_from.current_genes) > 1000:
            background_copy_reviews.delay(
                user, gene_symbols, panel_from.pk, panel_to.pk
            )
            return ProcessingRunCode.PROCESS_BACKGROUND, 0
        else:
            with transaction.atomic():
                panel_to = panel_to.increment_version()
                return (
                    ProcessingRunCode.PROCESSED,
                    panel_to.copy_gene_reviews_from(gene_symbols, panel_from),
                )

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
"""Contains a form which is used to add/edit a gene in a panel."""

import logging
from collections import OrderedDict

from dal_select2.widgets import (
    ModelSelect2,
    ModelSelect2Multiple,
    Select2Multiple,
)
from django import forms

from panelapp.forms import Select2ListMultipleChoiceField
from panels.models import (
    Evaluation,
    Evidence,
    Gene,
    GenePanel,
    GenePanelEntrySnapshot,
    GenePanelSnapshot,
    Tag,
)

from .helpers import GELSimpleArrayField
from .mixins import EntityFormMixin

LOGGER = logging.getLogger(__name__)


class PanelGeneForm(EntityFormMixin, forms.ModelForm):
    """The goal for this form is to add a Gene to a Panel.

    How this works:

    This form actually contains data for multiple models: GenePanelEntrySnapshot,
    Evidence, Evaluation. Some of this data is duplicated, and it's not clear if
    it needs to stay this way or should be refactored and moved to the models where
    it belongs. I.e. GenePanelEntrySnapshot has moi, mop, comments, etc. It's
    not clear if we need to keep it here, or move it to Evaluation model since
    it has the same values.

    When user clicks save we:

    1) Get Gene data and add it to the JSONField
    2) Create Comment
    3) Create Evaluation
    4) Create Evidence
    5) Create new copy of GenePanelSnapshot, increment minor version
    6) Create new GenePanelEntrySnapshot with a link to the new GenePanelSnapshot
    """

    # https://stackoverflow.com/questions/75249988/why-is-django-autocomplete-light-single-select-badly-styled-and-broken-when-mult
    # https://github.com/yourlabs/django-autocomplete-light/issues/1318
    gene = forms.ModelChoiceField(
        label="Gene symbol",
        queryset=Gene.objects.filter(active=True),
        widget=ModelSelect2(
            url="autocomplete-gene",
            attrs={
                "data-minimum-input-length": 1,
                "data-theme": "bootstrap-5",
                "style": "width: 100%;",
                "data-testid": "gene-symbol",
            },
        ),
    )

    gene_name = forms.CharField()

    source = Select2ListMultipleChoiceField(
        choice_list=Evidence.ALL_SOURCES,
        required=False,
        widget=Select2Multiple(
            url="autocomplete-source",
            attrs={
                "style": "width: 100%;",
                "data-testid": "source",
            },
        ),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=ModelSelect2Multiple(
            url="autocomplete-tags",
            attrs={"style": "width: 100%;"},
        ),
    )

    publications = GELSimpleArrayField(
        forms.CharField(),
        label="Publications (PMID: 1234;4321)",
        delimiter=";",
        required=False,
    )
    phenotypes = GELSimpleArrayField(
        forms.CharField(),
        label="Phenotypes (separate using a semi-colon - ;)",
        delimiter=";",
        required=False,
    )

    rating = forms.ChoiceField(
        choices=[("", "Provide rating")] + Evaluation.RATINGS, required=False
    )
    current_diagnostic = forms.BooleanField(required=False)
    comments = forms.CharField(widget=forms.Textarea, required=False)
    transcript = GELSimpleArrayField(
        forms.CharField(),
        label="Transcripts (separate using a semi-colon - ;)",
        delimiter=";",
        required=False,
    )

    additional_panels = forms.ModelMultipleChoiceField(
        queryset=GenePanelSnapshot.objects.only("panel__name", "pk"),
        required=False,
        widget=ModelSelect2Multiple(
            url="autocomplete-simple-panels-all",
            attrs={"style": "width: 100%;"},
        ),
    )

    class Meta:
        model = GenePanelEntrySnapshot
        fields = (
            "mode_of_pathogenicity",
            "moi",
            "penetrance",
            "publications",
            "phenotypes",
            "transcript",
            "additional_panels",
        )

    def __init__(self, *args, **kwargs):
        self.panel = kwargs.pop("panel")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        original_fields = self.fields

        self.fields = OrderedDict()
        self.fields["gene"] = original_fields.get("gene")
        if self.instance.pk:
            self.fields["gene_name"] = original_fields.get("gene_name")
        self.fields["source"] = original_fields.get("source")

        # Fix for disappearing sources
        # Select2ListMultipleChoiceField removes any values that don't belong in choices
        # Any custom values are removed, including expert review
        if self.initial and self.initial.get("source", []):
            source_choices = set(self.fields["source"].choices)
            source_choices.update(
                [(val, val) for val in self.initial.get("source", [])]
            )
            self.fields["source"].choices = list(source_choices)
            self.fields["source"].initial = self.initial.get("source", [])

        self.fields["mode_of_pathogenicity"] = original_fields.get(
            "mode_of_pathogenicity"
        )
        self.fields["moi"] = original_fields.get("moi")
        self.fields["moi"].required = False
        self.fields["penetrance"] = original_fields.get("penetrance")
        self.fields["publications"] = original_fields.get("publications")
        self.fields["phenotypes"] = original_fields.get("phenotypes")
        if self.request.user.is_authenticated and self.request.user.reviewer.is_GEL():
            self.fields["tags"] = original_fields.get("tags")
            self.fields["transcript"] = original_fields.get("transcript")
            self.fields["additional_panels"] = original_fields.get("additional_panels")
        if not self.instance.pk:
            self.fields["rating"] = original_fields.get("rating")
            self.fields["current_diagnostic"] = original_fields.get(
                "current_diagnostic"
            )
            self.fields["comments"] = original_fields.get("comments")

    def clean_gene(self):
        """Check if gene exists in a panel if we add a new gene or change the gene"""

        gene_symbol = self.cleaned_data["gene"].gene_symbol
        if not self.instance.pk and self.panel.has_gene(gene_symbol):
            raise forms.ValidationError(
                "Gene has already been added to the panel", code="gene_exists_in_panel"
            )
        elif (
            self.instance.pk
            and "gene" in self.changed_data
            and gene_symbol != self.instance.gene.get("gene_symbol")
            and self.panel.has_gene(gene_symbol)
        ):
            raise forms.ValidationError(
                "Gene has already been added to the panel", code="gene_exists_in_panel"
            )
        if not self.cleaned_data.get("gene_name"):
            self.cleaned_data["gene_name"] = self.cleaned_data["gene"].gene_name

        return self.cleaned_data["gene"]

    def clean_additional_panels(self):
        gene_symbol = self.cleaned_data["gene"].gene_symbol

        for panel in GenePanelSnapshot.objects.filter(
            pk__in=self.cleaned_data["additional_panels"]
        ):
            if panel.has_gene(gene_symbol):
                raise forms.ValidationError(
                    "Entity is already on additional panel",
                    code="gene_exists_in_additional_panel",
                )
        return self.cleaned_data["additional_panels"]

    def save_gene(self, *args, **kwargs):
        """Saves the gene, increments version and returns the gene back"""

        gene_data = self.cleaned_data
        gene_data["sources"] = gene_data.pop("source")

        additional_panels = gene_data.pop("additional_panels", None)

        if gene_data.get("comments"):
            gene_data["comment"] = gene_data.pop("comments")

        if self.initial:
            initial_gene_symbol = self.initial["gene_json"].get("gene_symbol")
        else:
            initial_gene_symbol = None

        new_gene_symbol = gene_data.get("gene").gene_symbol

        if self.initial and self.panel.has_gene(initial_gene_symbol):
            # When only copying entities don't create new version for the original one
            if self.changed_data and self.changed_data != ["additional_panels"]:
                self.panel = self.panel.increment_version()
                self.panel.update_gene(
                    self.request.user, initial_gene_symbol, gene_data
                )
                self.panel = GenePanel.objects.get(pk=self.panel.panel.pk).active_panel
            else:
                LOGGER.info("Copying gene to other panel")

            entity = self.panel.get_gene(new_gene_symbol)
        else:
            increment_version = (
                self.request.user.is_authenticated
                and self.request.user.reviewer.is_GEL()
            )
            entity = self.panel.add_gene(
                self.request.user, new_gene_symbol, gene_data, increment_version
            )

        if additional_panels:
            entity.copy_to_panels(
                panels=additional_panels,
                user=self.request.user,
                entity_data=gene_data,
                copy_data=bool(self.initial),
            )

        return entity

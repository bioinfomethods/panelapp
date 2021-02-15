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
from django.contrib.postgres.forms import (
    IntegerRangeField,
    SimpleArrayField,
)

from panelapp.forms import Select2ListMultipleChoiceField
from panels.forms.mixins import EntityFormMixin
from panels.models import (
    STR,
    Evaluation,
    Evidence,
    Gene,
    GenePanel,
    GenePanelSnapshot,
    Tag,
)

LOGGER = logging.getLogger(__name__)


class PanelSTRForm(EntityFormMixin, forms.ModelForm):
    """
    The goal for this form is to add a STR to a Panel.

    How this works:

    This form actually contains data for multiple models: STR,
    Evidence, Evaluation. Some of this data is duplicated, and it's not clear if
    it needs to stay this way or should be refactored and moved to the models where
    it belongs. I.e. GenePanelEntrySnapshot has moi, comments, etc. It's
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

    gene = forms.ModelChoiceField(
        label="Gene symbol",
        required=False,
        queryset=Gene.objects.filter(active=True),
        widget=ModelSelect2(
            url="autocomplete-gene", attrs={"data-minimum-input-length": 1}
        ),
    )

    position_37 = IntegerRangeField(require_all_fields=True, required=False)
    position_38 = IntegerRangeField(require_all_fields=True, required=True)

    gene_name = forms.CharField(required=False)

    source = Select2ListMultipleChoiceField(
        choice_list=Evidence.ALL_SOURCES,
        required=False,
        widget=Select2Multiple(url="autocomplete-source"),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=ModelSelect2Multiple(url="autocomplete-tags"),
    )

    publications = SimpleArrayField(
        forms.CharField(),
        label="Publications (PMID: 1234;4321)",
        delimiter=";",
        required=False,
    )
    phenotypes = SimpleArrayField(
        forms.CharField(),
        label="Phenotypes (separate using a semi-colon - ;)",
        delimiter=";",
        required=False,
    )

    rating = forms.ChoiceField(
        choices=[("", "Provide rating")] + Evaluation.RATINGS, required=False
    )
    current_diagnostic = forms.BooleanField(required=False)
    clinically_relevant = forms.BooleanField(
        label="Interruptions are clinically relevant",
        required=False,
        help_text="Interruptions in the repeated sequence are reported as part of standard diagnostic practice",
    )
    comments = forms.CharField(widget=forms.Textarea, required=False)

    additional_panels = forms.ModelMultipleChoiceField(
        queryset=GenePanelSnapshot.objects.all().only("panel__name", "pk"),
        required=False,
        widget=ModelSelect2Multiple(url="autocomplete-simple-panels-all"),
    )

    class Meta:
        model = STR
        fields = (
            "name",
            "chromosome",
            "position_37",
            "position_38",
            "repeated_sequence",
            "normal_repeats",
            "pathogenic_repeats",
            "moi",
            "penetrance",
            "publications",
            "phenotypes",
            "additional_panels",
        )

    def __init__(self, *args, **kwargs):
        self.panel = kwargs.pop("panel")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        original_fields = self.fields

        self.fields = OrderedDict()
        self.fields["name"] = original_fields.get("name")
        self.fields["chromosome"] = original_fields.get("chromosome")
        self.fields["position_37"] = original_fields.get("position_37")
        self.fields["position_37"].widget.widgets[0].attrs = {
            "placeholder": "Position start (GRCh37)"
        }
        self.fields["position_37"].widget.widgets[1].attrs = {
            "placeholder": "Position end (GRCh37)"
        }
        self.fields["position_38"] = original_fields.get("position_38")
        self.fields["position_38"].widget.widgets[0].attrs = {
            "placeholder": "Position start (GRCh38)"
        }
        self.fields["position_38"].widget.widgets[1].attrs = {
            "placeholder": "Position end (GRCh38)"
        }
        self.fields["repeated_sequence"] = original_fields.get("repeated_sequence")
        self.fields["normal_repeats"] = original_fields.get("normal_repeats")
        self.fields["pathogenic_repeats"] = original_fields.get("pathogenic_repeats")
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

        self.fields["moi"] = original_fields.get("moi")
        self.fields["moi"].required = False
        self.fields["penetrance"] = original_fields.get("penetrance")
        self.fields["publications"] = original_fields.get("publications")
        self.fields["phenotypes"] = original_fields.get("phenotypes")
        if self.request.user.is_authenticated and self.request.user.reviewer.is_GEL():
            self.fields["tags"] = original_fields.get("tags")
            self.fields["additional_panels"] = original_fields.get("additional_panels")
        if not self.instance.pk:
            self.fields["rating"] = original_fields.get("rating")
            self.fields["current_diagnostic"] = original_fields.get(
                "current_diagnostic"
            )
            if self.instance.is_str():
                self.fields["clinically_relevant"] = original_fields.get(
                    "clinically_relevant"
                )
            self.fields["comments"] = original_fields.get("comments")

    def clean_repeated_sequence(self):
        if (
            len(
                set(self.cleaned_data["repeated_sequence"]).difference(
                    {"A", "T", "C", "G", "N"}
                )
            )
            > 0
        ):
            raise forms.ValidationError(
                "Repeated sequence contains incorrect nucleotides"
            )
        return self.cleaned_data["repeated_sequence"]

    def clean_name(self):
        """Check if gene exists in a panel if we add a new gene or change the gene"""

        name = self.cleaned_data["name"]
        if not self.instance.pk and self.panel.has_str(name):
            raise forms.ValidationError(
                "STR has already been added to the panel", code="str_exists_in_panel"
            )
        elif (
            self.instance.pk
            and "name" in self.changed_data
            and name != self.instance.name
            and self.panel.has_str(name)
        ):
            raise forms.ValidationError(
                "STR has already been added to the panel", code="str_exists_in_panel"
            )
        if not self.cleaned_data.get("name"):
            self.cleaned_data["name"] = self.cleaned_data["name"]

        return self.cleaned_data["name"]

    def clean_additional_panels(self):
        entity_name = self.cleaned_data["name"]

        for panel in GenePanelSnapshot.objects.filter(
            pk__in=self.cleaned_data["additional_panels"]
        ):
            if panel.has_str(entity_name):
                raise forms.ValidationError(
                    "Entity is already on additional panel",
                    code="entitiy_exists_in_additional_panel",
                )
        return self.cleaned_data["additional_panels"]

    def save_str(self, *args, **kwargs):
        """Saves the gene, increments version and returns the gene back"""

        str_data = self.cleaned_data
        str_data["sources"] = str_data.pop("source")

        additional_panels = str_data.pop("additional_panels", None)

        if str_data.get("comments"):
            str_data["comment"] = str_data.pop("comments")

        if self.initial:
            initial_name = self.initial["name"]
        else:
            initial_name = None

        new_str_name = str_data["name"]

        if self.initial and self.panel.has_str(initial_name):
            # When only copying entities don't create new version for the original one
            if self.changed_data and self.changed_data != ["additional_panels"]:
                self.panel = self.panel.increment_version()
                self.panel.update_str(
                    self.request.user,
                    initial_name,
                    str_data,
                    remove_gene=True if not str_data.get("gene") else False,
                )
                self.panel = GenePanel.objects.get(pk=self.panel.panel.pk).active_panel
            else:
                LOGGER.info("Copying str to other panel")

            entity = self.panel.get_str(new_str_name)
        else:
            increment_version = (
                self.request.user.is_authenticated
                and self.request.user.reviewer.is_GEL()
            )
            entity = self.panel.add_str(
                self.request.user, new_str_name, str_data, increment_version
            )

        if additional_panels:
            entity.copy_to_panels(
                panels=additional_panels,
                user=self.request.user,
                entity_data=str_data,
                copy_data=bool(self.initial),
            )

        return entity

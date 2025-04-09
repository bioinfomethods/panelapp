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
from collections import OrderedDict

from dal_select2.widgets import ModelSelect2Multiple
from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from panels.models import (
    GenePanel,
    GenePanelEntrySnapshot,
    Tag,
)


class UpdateGeneTagsForm(forms.ModelForm):
    # Use "prefix" as this allows multiple DAL select2 widgets for tags to be used in
    # a single template.
    # In this case in the UpdateGeneTagsForm and PanelGeneForm
    # https://github.com/yourlabs/django-autocomplete-light/issues/1235#issuecomment-825257967
    prefix = "tags"

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("tags",)

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=ModelSelect2Multiple(
            url="autocomplete-tags",
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if "tags" in self.changed_data:
            self.instance.update_tags(self.user, self.cleaned_data["tags"])
        return self.instance


class UpdateGeneMOPForm(forms.ModelForm):
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("mode_of_pathogenicity",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        mop = self.cleaned_data["mode_of_pathogenicity"]
        comment = self.cleaned_data["comment"]
        self.instance.panel.increment_version()
        self.instance = GenePanel.objects.get(
            pk=self.instance.panel.panel.pk
        ).active_panel.get_gene(self.instance.gene["gene_symbol"])
        self.instance.update_pathogenicity(mop, self.user, comment)
        self.instance.panel._update_saved_stats()
        return self.instance


class UpdateGeneMOIForm(forms.ModelForm):
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("moi",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        moi = self.cleaned_data["moi"]
        comment = self.cleaned_data["comment"]
        self.instance.panel.increment_version()
        self.instance = GenePanel.objects.get(
            pk=self.instance.panel.panel.pk
        ).active_panel.get_gene(self.instance.gene["gene_symbol"])
        self.instance.update_moi(moi, self.user, comment)
        self.instance.panel._update_saved_stats()
        return self.instance


class UpdateGenePhenotypesForm(forms.ModelForm):
    comment = forms.CharField(required=False, widget=forms.Textarea)
    phenotypes = SimpleArrayField(
        forms.CharField(max_length=255),
        label="Phenotypes (separate using a semi-colon - ;)",
        delimiter=";",
    )

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("phenotypes",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        phenotypes = self.cleaned_data["phenotypes"]
        comment = self.cleaned_data["comment"]
        self.instance.panel.increment_version()
        self.instance = GenePanel.objects.get(
            pk=self.instance.panel.panel.pk
        ).active_panel.get_gene(self.instance.gene["gene_symbol"])
        self.instance.update_phenotypes(phenotypes, self.user, comment)
        self.instance.panel._update_saved_stats()
        return self.instance


class UpdateGenePublicationsForm(forms.ModelForm):
    comment = forms.CharField(required=False, widget=forms.Textarea)

    publications = SimpleArrayField(
        forms.CharField(max_length=255),
        label="Publications (separate using a semi-colon - ;)",
        delimiter=";",
    )

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("publications",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        publications = self.cleaned_data["publications"]
        comment = self.cleaned_data["comment"]
        self.instance.panel.increment_version()
        self.instance = GenePanel.objects.get(
            pk=self.instance.panel.panel.pk
        ).active_panel.get_gene(self.instance.gene["gene_symbol"])
        self.instance.update_publications(publications, self.user, comment)
        self.instance.panel._update_saved_stats()
        return self.instance


class UpdateGeneRatingForm(forms.ModelForm):
    comment = forms.CharField(required=False, widget=forms.Textarea)
    status = forms.ChoiceField(choices=GenePanelEntrySnapshot.GEL_STATUS)

    class Meta:
        model = GenePanelEntrySnapshot
        fields = ("saved_gel_status",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        original_fields = self.fields
        self.fields = OrderedDict()
        self.fields["status"] = original_fields["status"]
        self.fields["status"].initial = self.instance.saved_gel_status
        self.fields["comment"] = original_fields["comment"]

    def save(self, *args, **kwargs):
        status = self.cleaned_data["status"]
        self.instance.panel.increment_version()
        self.instance = GenePanel.objects.get(
            pk=self.instance.panel.panel.pk
        ).active_panel.get_gene(self.instance.gene["gene_symbol"])
        self.instance.update_rating(status, self.user, self.cleaned_data["comment"])
        self.instance.panel._update_saved_stats()
        return self.instance

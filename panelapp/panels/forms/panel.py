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
from itertools import chain
from django import forms
from django.utils import timezone
from dal_select2.widgets import ModelSelect2Multiple
from panels.models import Level4Title
from panels.models import GenePanel
from panels.models import GenePanelSnapshot
from panels.models import PanelType
from panels.models import HistoricalSnapshot


class PanelForm(forms.ModelForm):
    level2 = forms.CharField(required=False)
    level3 = forms.CharField(required=False)
    level4 = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    omim = forms.CharField(required=False)
    orphanet = forms.CharField(required=False)
    hpo = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=True, choices=GenePanel.STATUS, initial=GenePanel.STATUS.internal
    )
    signed_off_version = forms.CharField(label="Signed Off Version", required=False)
    signed_off_date = forms.DateField(label='Signed Off Date', required=False,
                                      widget=forms.DateInput(attrs={"placeholder":"Signed Off Date in format dd/mm/yyyy"}))
    child_panels = forms.ModelMultipleChoiceField(
        label="Child Panels",
        required=False,
        queryset=GenePanelSnapshot.objects.get_active_annotated().exclude(
            is_super_panel=True
        ),
        widget=ModelSelect2Multiple(
            url="autocomplete-simple-panels", attrs={"data-minimum-input-length": 3}
        ),
    )

    types = forms.ModelMultipleChoiceField(
        label="Panel Types",
        required=False,
        queryset=PanelType.objects.all(),
        widget=ModelSelect2Multiple(
            url="autocomplete-simple-panel-types",
            attrs={"data-minimum-input-length": 1},
        ),
    )

    class Meta:
        model = GenePanelSnapshot
        fields = ("old_panels",)

    def __init__(self, *args, **kwargs):
        gel_curator = kwargs.pop("gel_curator")
        self.request = kwargs.pop("request")

        super().__init__(*args, **kwargs)

        original_fields = self.fields

        self.fields = OrderedDict()
        self.fields["level2"] = original_fields.get("level2")
        self.fields["level3"] = original_fields.get("level3")
        self.fields["level4"] = original_fields.get("level4")
        self.fields["description"] = original_fields.get("description")
        self.fields["omim"] = original_fields.get("omim")
        self.fields["orphanet"] = original_fields.get("orphanet")
        self.fields["hpo"] = original_fields.get("hpo")
        self.fields["old_panels"] = original_fields.get("old_panels")
        self.fields["types"] = original_fields.get("types")
        self.fields["signed_off_version"] = original_fields.get("signed_off_version")
        self.fields["signed_off_date"] = original_fields.get("signed_off_date")
        if gel_curator:  # TODO (Oleg) also check if we have entities in this panel
            self.fields["child_panels"] = original_fields.get("child_panels")
        self.fields["status"] = original_fields.get("status")

        if self.instance.pk:
            self.fields["status"].initial = self.instance.panel.status
            self.fields["signed_off_version"].initial = '{}.{}'.format(self.instance.signed_off[0],
                                                               self.instance.signed_off[1]) if self.instance.signed_off else None
            self.fields["signed_off_date"].initial = self.instance.signed_off[2] if self.instance.signed_off else None
            if gel_curator:
                self.fields[
                    "child_panels"
                ].initial = self.instance.child_panels.values_list("pk", flat=True)
                self.fields["types"].initial = self.instance.panel.types.values_list(
                    "pk", flat=True
                )

    def clean_level4(self):
        if (
            not self.instance.pk
            or self.cleaned_data["level4"] != self.instance.level4title.name
        ):
            if (
                GenePanelSnapshot.objects.get_active(all=True, internal=True)
                .exclude(panel__status=GenePanel.STATUS.deleted)
                .filter(level4title__name=self.cleaned_data["level4"])
                .exists()
            ):
                raise forms.ValidationError("Panel with this name already exists")

        return self.cleaned_data["level4"]

    def clean_omim(self):
        return self._clean_array(self.cleaned_data["omim"])

    def clean_orphanet(self):
        return self._clean_array(self.cleaned_data["orphanet"])

    def clean_hpo(self):
        return self._clean_array(self.cleaned_data["hpo"])

    def save(self, *args, **kwargs):
        new_level4 = Level4Title(
            level2title=self.cleaned_data["level2"].strip(),
            level3title=self.cleaned_data["level3"].strip(),
            name=self.cleaned_data["level4"].strip(),
            description=self.cleaned_data["description"].strip(),
            omim=self.cleaned_data["omim"],
            hpo=self.cleaned_data["hpo"],
            orphanet=self.cleaned_data["orphanet"],
        )

        activities = []

        if self.instance.id:
            current_instance = GenePanelSnapshot.objects.get(pk=self.instance.id)

            panel = self.instance.panel
            level4title = self.instance.level4title

            data_changed = False
            if level4title.dict_tr() != new_level4.dict_tr():
                data_changed = True
                new_level4.save()
                if level4title.name != new_level4.name:
                    activities.append(
                        "Panel name changed from {} to {}".format(
                            level4title.name, new_level4.name
                        )
                    )

                if level4title.hpo != new_level4.hpo:
                    activities.append(
                        "HPO terms changed from {} to {}".format(
                            ", ".join(level4title.hpo), ", ".join(new_level4.hpo)
                        )
                    )

                self.instance.level4title = new_level4
                self.instance.panel.name = new_level4.name

            if "old_panels" in self.changed_data:
                activities.append(
                    "List of related panels changed from {} to {}".format(
                        "; ".join(current_instance.old_panels),
                        "; ".join(self.cleaned_data["old_panels"]),
                    )
                )
                self.instance.old_panels = self.cleaned_data["old_panels"]

            if "status" in self.changed_data:
                activities.append(
                    "Panel status changed from {} to {}".format(
                        current_instance.panel.status, self.cleaned_data["status"]
                    )
                )
                self.instance.panel.status = self.cleaned_data["status"]

            update_stats_superpanel = True
            if "child_panels" in self.changed_data:
                self.instance.child_panels.set(self.cleaned_data["child_panels"])
                activities.append(
                    "Changed child panels to: {}".format(
                        "; ".join(
                            self.instance.child_panels.values_list(
                                "panel__name", flat=True
                            )
                        )
                    )
                )
                update_stats_superpanel = False

            if "types" in self.changed_data:
                panel.types.set(self.cleaned_data["types"])
                activities.append(
                    "Panel types changed to {}".format(
                        "; ".join(panel.types.values_list("name", flat=True))
                    )
                )

            if data_changed or self.changed_data:
                self.instance.increment_version()
                panel.save()
                self.instance._update_saved_stats(use_db=update_stats_superpanel)

                if "signed_off_version" in self.changed_data or "signed_off_date" in self.changed_data:
                    gene_panel = self.instance.panel

                    if not self.cleaned_data['signed_off_version'] and not self.cleaned_data['signed_off_date']:
                        gene_panel.signed_off.signed_off_date = None
                        gene_panel.signed_off.save()
                        gene_panel.signed_off = None
                        gene_panel.save()
                        activities.append("Panel signed off version has been removed")
                    else:
                        version = self.cleaned_data["signed_off_version"]

                        try:
                            major_version, minor_version = version.split(".")
                        except ValueError:
                            raise forms.ValidationError("Signed off version incorrect format")

                        snapshot = HistoricalSnapshot.objects.filter(panel=gene_panel,
                                                                     major_version=int(major_version),
                                                                     minor_version=int(minor_version)).first()
                        if snapshot:
                            HistoricalSnapshot.objects.filter(
                                panel=self.instance.panel,
                                signed_off_date__isnull=False).update(signed_off_date=None)

                            if self.cleaned_data["signed_off_date"]:
                                snapshot.signed_off_date = self.cleaned_data["signed_off_date"]
                            else:
                                snapshot.signed_off_date = timezone.now().date()
                            snapshot.save()
                            gene_panel.signed_off = snapshot
                            gene_panel.save()
                            activities.append("Panel version has been signed off")
                        else:
                            raise forms.ValidationError("Signed off version does not exist")
            else:
                panel.save()

        else:
            panel = GenePanel.objects.create(
                name=self.cleaned_data["level4"].strip(),
                status=self.cleaned_data["status"],
            )
            new_level4.save()

            activities.append("Added Panel {}".format(panel.name))
            if self.cleaned_data["old_panels"]:
                activities.append(
                    "Set list of related panels to {}".format(
                        "; ".join(self.cleaned_data["old_panels"])
                    )
                )

            self.instance.panel = panel
            self.instance.level4title = new_level4
            self.instance.old_panels = self.cleaned_data["old_panels"]
            self.instance.save()
            if self.cleaned_data.get("child_panels"):
                self.instance.child_panels.set(self.cleaned_data["child_panels"])
                self.instance.major_version = max(
                    self.instance.child_panels.values_list("major_version", flat=True)
                )
                self.instance.save(update_fields=["major_version"])
                self.instance._update_saved_stats(use_db=False)
                activities.append(
                    "Set child panels to: {}".format(
                        "; ".join(
                            list(
                                self.instance.child_panels.values_list(
                                    "panel__name", flat=True
                                )
                            )
                        )
                    )
                )
            if self.cleaned_data.get("types"):
                panel.types.set(self.cleaned_data["types"])
                activities.append(
                    "Set panel types to: {}".format(
                        "; ".join(panel.types.values_list("name", flat=True))
                    )
                )

        if activities:
            panel.add_activity(self.request.user, "\n".join(activities))

    @staticmethod
    def _clean_array(data, separator=","):
        return [x.strip() for x in data.split(separator) if x.strip()]

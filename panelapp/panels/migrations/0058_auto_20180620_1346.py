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
# Generated by Django 2.0.6 on 2018-06-20 12:46

from django.db import migrations
from django.db import models
from django.db.models import Count
from django.db.models import Case
from django.db.models import When
from django.db.models import Subquery
from django.db.models import Value
from django.contrib.postgres.aggregates import ArrayAgg
from panels.models import GenePanel


def skip(apps, schema_editor):
    pass


def populate_stats(apps, schema_editor):

    GenePanelSnapshot = apps.get_model("panels", "GenePanelSnapshot")
    for panel in (
        GenePanelSnapshot.objects.filter(
            pk__in=Subquery(
                GenePanelSnapshot.objects.exclude(
                    panel__status=GenePanel.STATUS.deleted
                )
                .distinct("panel__pk")
                .values("pk")
                .order_by("panel__pk", "-major_version", "-minor_version")
            )
        )
        .annotate(child_panels_count=Count("child_panels"))
        .annotate(superpanels_count=Count("genepanelsnapshot"))
        .annotate(
            is_super_panel=Case(
                When(child_panels_count__gt=0, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            ),
            is_child_panel=Case(
                When(superpanels_count__gt=0, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            ),
        )
    ):

        pks = [panel.pk]
        if panel.is_super_panel:
            pks = panel.child_panels.values_list("pk", flat=True)

        keys = [
            "gene_reviewers",
            "number_of_evaluated_genes",
            "number_of_genes",
            "number_of_ready_genes",
            "number_of_green_genes",
            "str_reviewers",
            "number_of_evaluated_strs",
            "number_of_strs",
            "number_of_ready_strs",
            "number_of_green_strs",
        ]

        out = {"gene_reviewers": [], "str_reviewers": []}

        for pk in pks:
            # This is ~ 3000x faster than `.filter(pk__in=pks)`. Not a typo: 24 seconds vs 4ms per pk
            info = (
                GenePanelSnapshot.objects.filter(pk=pk)
                .prefetch_related(
                    "str",
                    "str__evaluation",
                    "str__evaluation__user",
                    "genepanelentrysnapshot",
                    "genepanelentrysnapshot__evaluation",
                    "genepanelentrysnapshot__evaluation__user",
                )
                .aggregate(
                    gene_reviewers=ArrayAgg(
                        "genepanelentrysnapshot__evaluation__user__pk", distinct=True
                    ),
                    number_of_evaluated_genes=Count(
                        Case(
                            # Count unique genes if that gene has more than 1 evaluation
                            When(
                                genepanelentrysnapshot__evaluation__isnull=False,
                                then=models.F("genepanelentrysnapshot__pk"),
                            )
                        ),
                        distinct=True,
                    ),
                    number_of_genes=Count("genepanelentrysnapshot__pk", distinct=True),
                    number_of_ready_genes=Count(
                        Case(
                            When(
                                genepanelentrysnapshot__ready=True,
                                then=models.F("genepanelentrysnapshot__pk"),
                            )
                        ),
                        distinct=True,
                    ),
                    number_of_green_genes=Count(
                        Case(
                            When(
                                genepanelentrysnapshot__saved_gel_status__gte=3,
                                then=models.F("genepanelentrysnapshot__pk"),
                            )
                        ),
                        distinct=True,
                    ),
                    str_reviewers=ArrayAgg("str__evaluation__user__pk", distinct=True),
                    number_of_evaluated_strs=Count(
                        Case(
                            # Count unique genes if that gene has more than 1 evaluation
                            When(
                                str__evaluation__isnull=False, then=models.F("str__pk")
                            )
                        ),
                        distinct=True,
                    ),
                    number_of_strs=Count("str__pk", distinct=True),
                    number_of_ready_strs=Count(
                        Case(When(str__ready=True, then=models.F("str__pk"))),
                        distinct=True,
                    ),
                    number_of_green_strs=Count(
                        Case(
                            When(str__saved_gel_status__gte=3, then=models.F("str__pk"))
                        ),
                        distinct=True,
                    ),
                )
            )

            for key in keys:
                out[key] = out.get(key, 0) + info.get(key, 0)

        out["gene_reviewers"] = [r for r in out["gene_reviewers"] if r]  #  remove None
        out["str_reviewers"] = [r for r in out["str_reviewers"] if r]  # remove None
        out["entity_reviewers"] = list(
            set(out["gene_reviewers"] + out["str_reviewers"])
        )
        out["number_of_reviewers"] = len(out["entity_reviewers"])
        out["number_of_evaluated_entities"] = (
            out["number_of_evaluated_genes"] + out["number_of_evaluated_strs"]
        )
        out["number_of_entities"] = out["number_of_genes"] + out["number_of_strs"]
        out["number_of_ready_entities"] = (
            out["number_of_ready_genes"] + out["number_of_ready_strs"]
        )
        out["number_of_green_entities"] = (
            out["number_of_green_genes"] + out["number_of_green_strs"]
        )
        panel.stats = out
        panel.save(update_fields=["stats"])


class Migration(migrations.Migration):

    dependencies = [("panels", "0057_auto_20180620_1342")]

    operations = [migrations.RunPython(populate_stats, skip)]

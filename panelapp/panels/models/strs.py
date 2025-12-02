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
"""STRs (Short Tandem Repeats) manager and model

Author: Oleg Gerasimenko

(c) 2018 Genomics England
"""

from copy import deepcopy

from django.db import models
from django.db.models import Count
from django.db.models import Subquery
from django.db.models import Value as V
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import IntegerRangeField
from django.urls import reverse

from model_utils.models import TimeStampedModel
from .entity import AbstractEntity
from .entity import EntityManager
from .gene import Gene
from .genepanel import GenePanel
from .evidence import Evidence
from .evaluation import Evaluation
from .trackrecord import TrackRecord
from .comment import Comment
from .tag import Tag
from .genepanelsnapshot import GenePanelSnapshot


class STRManager(EntityManager):
    """Objects manager for STR."""

    def get_latest_ids(self, deleted=False):
        """Get STR ids"""

        qs = super().get_queryset()
        if not deleted:
            qs = qs.exclude(panel__panel__status=GenePanel.STATUS.deleted)

        return (
            qs.distinct("panel__panel_id")
            .values_list("panel_id", flat=True)
            .order_by(
                "panel__panel_id", "-panel__major_version", "-panel__minor_version"
            )
        )

    def get_active_slim(self, pks):
        qs = super().get_queryset().filter(panel_id__in=pks)
        return qs.annotate(
            entity_type=V("str", output_field=models.CharField()),
            entity_name=models.F("name"),
        )

    def get_active(
        self, deleted=False, name=None, gene_symbol=None, pks=None, panel_types=None
    ):
        """Get active STRs"""

        # TODO (Oleg) there is a lot of similar logic between entities models, simplify

        if pks:
            qs = super().get_queryset().filter(panel_id__in=pks)
        else:
            qs = (
                super()
                .get_queryset()
                .filter(panel_id__in=Subquery(self.get_latest_ids(deleted)))
            )
        if name:
            if isinstance(name, list):
                qs = qs.filter(name__in=name)
            else:
                qs = qs.filter(name=name)
        if gene_symbol:
            if isinstance(gene_symbol, list):
                qs = qs.filter(gene_core__gene_symbol__in=gene_symbol)
            else:
                qs = qs.filter(gene_core__gene_symbol=gene_symbol)

        if panel_types:
            qs = qs.filter(panel__panel__types__slug__in=panel_types)

        return (
            qs.annotate(
                number_of_reviewers=Count("evaluation__user", distinct=True),
                number_of_evaluations=Count("evaluation", distinct=True),
                entity_type=V("str", output_field=models.CharField()),
                entity_name=models.F("name"),
            )
            .prefetch_related(
                "evaluation",
                "tags",
                "evidence",
                "panel",
                "panel__level4title",
                "panel__panel",
                "panel__panel__types",
            )
            .order_by("panel_id", "-panel__major_version", "-panel__minor_version")
        )

    def get_str_panels(self, name, deleted=False, pks=None):
        """Get panels for the specified STR name"""

        return self.get_active(deleted=deleted, name=name, pks=pks)


class STR(AbstractEntity, TimeStampedModel):
    """Short Tandem Repeat (STR) Entity"""

    CHROMOSOMES = [
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
        ("7", "7"),
        ("8", "8"),
        ("9", "9"),
        ("10", "10"),
        ("11", "11"),
        ("12", "12"),
        ("13", "13"),
        ("14", "14"),
        ("15", "15"),
        ("16", "16"),
        ("17", "17"),
        ("18", "18"),
        ("19", "19"),
        ("20", "20"),
        ("21", "21"),
        ("22", "22"),
        ("X", "X"),
        ("Y", "Y"),
    ]

    class Meta:
        get_latest_by = "created"
        ordering = ["-saved_gel_status"]
        indexes = [models.Index(fields=["name"])]

    panel = models.ForeignKey(GenePanelSnapshot, on_delete=models.CASCADE)

    name = models.CharField(max_length=128)
    repeated_sequence = models.CharField(max_length=128)
    chromosome = models.CharField(max_length=8, choices=CHROMOSOMES)
    position_37 = IntegerRangeField(blank=True, null=True)
    position_38 = IntegerRangeField()
    normal_repeats = models.IntegerField(
        help_text="=< Maximum normal number of repeats", verbose_name="Normal"
    )
    pathogenic_repeats = models.IntegerField(
        help_text=">= Minimum fully penetrant pathogenic number of repeats",
        verbose_name="Pathogenic",
    )

    gene = JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True
    )  # copy data from Gene.dict_tr
    gene_core = models.ForeignKey(
        Gene, blank=True, null=True, on_delete=models.PROTECT
    )  # reference to the original Gene
    evidence = models.ManyToManyField(Evidence)
    evaluation = models.ManyToManyField(Evaluation, db_index=True)
    moi = models.CharField(
        "Mode of inheritance", choices=Evaluation.MODES_OF_INHERITANCE, max_length=255
    )
    penetrance = models.CharField(
        choices=AbstractEntity.PENETRANCE, max_length=255, blank=True, null=True
    )
    track = models.ManyToManyField(TrackRecord)
    publications = ArrayField(models.TextField(), blank=True, null=True)
    phenotypes = ArrayField(models.TextField(), blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    flagged = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    comments = models.ManyToManyField(Comment)
    mode_of_pathogenicity = models.CharField(
        choices=Evaluation.MODES_OF_PATHOGENICITY, max_length=255, null=True, blank=True
    )
    saved_gel_status = models.IntegerField(null=True, db_index=True)

    objects = STRManager()

    def __str__(self):
        return "Panel: {panel_name} STR: {str_name}".format(
            panel_name=self.panel.panel.name, str_name=self.name
        )

    @property
    def _entity_type(self):
        return "str"

    @property
    def label(self):
        return "STR: {name}".format(name=self.name)

    def get_absolute_url(self):
        """Returns absolute url for this STR in a panel"""

        return reverse(
            "panels:evaluation", args=(self.panel.panel.pk, "str", self.name)
        )

    def dict_tr(self):
        return {
            "name": self.name,
            "chromosome": self.chromosome,
            "position_37": (self.position_37.lower, self.position_37.upper)
            if self.position_37
            else None,
            "position_38": (self.position_38.lower, self.position_38.upper),
            "repeated_sequence": self.repeated_sequence,
            "normal_repeats": self.normal_repeats,
            "pathogenic_repeats": self.pathogenic_repeats,
            "gene": self.gene,
            "evidence": [evidence.dict_tr() for evidence in self.evidence.all()],
            "evaluation": [
                evaluation.dict_tr() for evaluation in self.evaluation.all()
            ],
            "track": [track.dict_tr() for track in self.track.all()],
            "moi": self.moi,
            "publications": self.publications,
            "phenotypes": self.phenotypes,
            "flagged": self.flagged,
            "penetrance": self.penetrance,
            "tags": [tag.name for tag in self.tags.all()],
        }

    def get_form_initial(self):
        """Since we create a new version every time we want to update something this method
        gets the initial data for the form.
        """

        return {
            "name": self.name,
            "chromosome": self.chromosome,
            "position_37": self.position_37,
            "position_38": self.position_38,
            "repeated_sequence": self.repeated_sequence,
            "normal_repeats": self.normal_repeats,
            "pathogenic_repeats": self.pathogenic_repeats,
            "gene": self.gene_core,
            "gene_json": self.gene,
            "gene_name": self.gene.get("gene_name") if self.gene else None,
            "source": [e.name for e in self.evidence.all() if e.is_GEL],
            "tags": self.tags.all(),
            "publications": self.publications,
            "phenotypes": self.phenotypes,
            "moi": self.moi,
            "penetrance": self.penetrance,
        }

    def copy_reviews_to_new_str(self, source_str, source_panel_name, user_ids_to_copy):
        """Copy selected reviews from source STR to this STR.

        Reviews from evaluators who have already reviewed this STR in the target
        panel will be skipped (not overwritten).

        Args:
            source_str: STR to copy reviews from
            source_panel_name: Name of the source panel (for attribution)
            user_ids_to_copy: Set/list of user IDs whose reviews should be copied
        """
        # Get existing evaluator IDs to avoid duplicates
        existing_evaluator_ids = set(self.evaluation.values_list("user_id", flat=True))

        # Filter evaluations to the selected users who haven't already reviewed
        evaluations_to_copy = [
            ev
            for ev in source_str.evaluation.all()
            if ev.user_id in user_ids_to_copy and ev.user_id not in existing_evaluator_ids
        ]

        if not evaluations_to_copy:
            return

        # Filter evidences from the selected reviewers
        filtered_user_ids = {ev.user_id for ev in evaluations_to_copy}
        evidences_to_copy = [
            ev
            for ev in source_str.evidence.all()
            if ev.reviewer and ev.reviewer.user_id in filtered_user_ids
        ]

        new_evaluations = {}

        for evaluation in evaluations_to_copy:
            version = evaluation.version if evaluation.version else "0"
            evaluation.version = "Imported from {} panel version {}".format(
                source_panel_name, version
            )

            comments = deepcopy(list(evaluation.comments.all()))
            evaluation.pk = None
            evaluation.create_comments = []

            for comment in comments:
                comment.pk = None
                evaluation.create_comments.append(comment)

            new_evaluations[evaluation.user_id] = {
                "evaluation": evaluation,
                "evidences": [],
            }

        for evidence in evidences_to_copy:
            evidence.pk = None
            if new_evaluations.get(evidence.reviewer.user_id):
                new_evaluations[evidence.reviewer.user_id]["evidences"].append(evidence)

        Evaluation.objects.bulk_create(
            [new_evaluations[key]["evaluation"] for key in new_evaluations]
        )

        Evidence.objects.bulk_create(
            [
                ev
                for key in new_evaluations
                for ev in new_evaluations[key]["evidences"]
            ]
        )

        Comment.objects.bulk_create(
            [
                c
                for key in new_evaluations
                for c in new_evaluations[key]["evaluation"].create_comments
            ]
        )

        for user_id in new_evaluations:
            evaluation = new_evaluations[user_id]["evaluation"]
            evaluation.comments.set(evaluation.create_comments)

        self.evaluation.add(
            *[new_evaluations[key]["evaluation"] for key in new_evaluations]
        )
        self.evidence.add(
            *[ev for key in new_evaluations for ev in new_evaluations[key]["evidences"]]
        )

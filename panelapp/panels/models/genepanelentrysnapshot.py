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
from copy import deepcopy
from django.db import models
from django.db.models import Subquery
from django.db.models import Value as V
from django.urls import reverse

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField

from model_utils.models import TimeStampedModel

from .gene import Gene
from .genepanel import GenePanel
from .evidence import Evidence
from .evaluation import Evaluation
from .trackrecord import TrackRecord
from .comment import Comment
from .tag import Tag
from .genepanelsnapshot import GenePanelSnapshot
from .entity import AbstractEntity
from .entity import EntityManager


class GenePanelEntrySnapshotManager(EntityManager):
    """Objects manager for GenePanelEntrySnapshot."""

    def get_latest_ids(self, deleted=False):
        """Get GenePanelSnapshot ids"""

        qs = super().get_queryset()
        if not deleted:
            qs = qs.exclude(panel__panel__status=GenePanel.STATUS.deleted)

        return (
            qs.distinct("panel__panel_id")
            .values_list("panel_id", flat=True)
            .order_by(
                "panel__panel_id",
                "-panel__major_version",
                "-panel__minor_version",
                "-panel__modified",
                "-panel_id",
            )
        )

    def get_active_slim(self, pks):
        qs = super().get_queryset().filter(panel_id__in=pks)
        return qs.annotate(
            entity_type=V("gene", output_field=models.CharField()),
            entity_name=models.F("gene_core__gene_symbol"),
        )

    def get_active(self, deleted=False, gene_symbol=None, pks=None, panel_types=None):
        """Get active Gene Entry Snapshots"""

        if pks:
            qs = super().get_queryset().filter(panel_id__in=pks)
        else:
            qs = (
                super()
                .get_queryset()
                .filter(panel_id__in=Subquery(self.get_latest_ids(deleted)))
            )
        if gene_symbol:
            if type(gene_symbol) == list:
                qs = qs.filter(gene_core__gene_symbol__in=gene_symbol)
            else:
                qs = qs.filter(gene_core__gene_symbol=gene_symbol)

        if panel_types:
            qs = qs.filter(panel__panel__types__slug__in=panel_types)

        return (
            qs.annotate(
                number_of_reviewers=models.Count("evaluation__user", distinct=True),
                number_of_evaluated_genes=models.Count("evaluation"),
                number_of_evaluated_entities=models.Count("evaluation"),
                entity_type=V("gene", output_field=models.CharField()),
                entity_name=models.F("gene_core__gene_symbol"),
            )
            .prefetch_related(
                "tags",
                "evidence",
                "panel",
                "panel__level4title",
                "panel__panel",
                "panel__panel__types",
            )
            .order_by(
                "panel_id",
                "-panel__major_version",
                "-panel__minor_version",
                "-panel__modified",
                "-panel_id",
            )
        )

    def get_gene_panels(self, gene_symbol, deleted=False, pks=None):
        """Get panels for the specified gene"""

        return self.get_active(deleted=deleted, gene_symbol=gene_symbol, pks=pks)


class GenePanelEntrySnapshot(AbstractEntity, TimeStampedModel):
    class Meta:
        get_latest_by = "created"
        ordering = ["-saved_gel_status"]
        indexes = [
            models.Index(fields=["ready"]),
            models.Index(fields=["saved_gel_status"]),
        ]

    panel = models.ForeignKey(GenePanelSnapshot, on_delete=models.CASCADE)
    gene = JSONField(encoder=DjangoJSONEncoder)  # copy data from Gene.dict_tr
    gene_core = models.ForeignKey(
        Gene, on_delete=models.PROTECT
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
    saved_gel_status = models.IntegerField(
        null=True, db_index=True
    )  # this should be enum red, green, etc
    transcript = ArrayField(models.CharField(max_length=255, blank=True, null=True), blank=True, null=True)

    objects = GenePanelEntrySnapshotManager()

    def __str__(self):
        return "Panel: {} Gene: {}".format(
            self.panel.panel.name, self.gene.get("gene_symbol")
        )

    @property
    def _entity_type(self):
        return "gene"

    @property
    def label(self):
        return "gene: {gene_symbol}".format(gene_symbol=self.gene.get("gene_symbol"))

    @property
    def name(self):
        return self.gene.get("gene_symbol")

    def get_absolute_url(self):
        """Returns absolute url for this gene in a panel"""

        return reverse(
            "panels:evaluation",
            args=(self.panel.panel.pk, "gene", self.gene.get("gene_symbol")),
        )

    def dict_tr(self):
        return {
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
            "mode_of_pathogenicity": self.mode_of_pathogenicity,
            "penetrance": self.penetrance,
            "tags": [tag.name for tag in self.tags.all()],
        }

    def get_form_initial(self):
        """Since we create a new version every time we want to update something this method
        gets the initial data for the form.
        """

        return {
            "gene": self.gene_core,
            "gene_json": self.gene,
            "gene_name": self.gene.get("gene_name"),
            "source": [e.name for e in self.evidence.all() if e.is_GEL],
            "tags": self.tags.all(),
            "publications": self.publications,
            "phenotypes": self.phenotypes,
            "mode_of_pathogenicity": self.mode_of_pathogenicity,
            "moi": self.moi,
            "penetrance": self.penetrance,
        }

    def copy_reviews_to_new_gene(self, source_gene_entry, source_panel_name, user_ids_to_copy):
        """Copy selected reviews from source gene to this newly created gene entry.

        This method is specifically for copying reviews to a gene that was just added
        to a panel and has no existing reviews.

        Args:
            source_gene_entry: GenePanelEntrySnapshot to copy reviews from
            source_panel_name: Name of the source panel (for attribution)
            user_ids_to_copy: Set/list of user IDs whose reviews should be copied

        Raises:
            ValueError: If this gene already has reviews (not a new gene)
        """
        # Safety check: ensure this is actually a new gene with no reviews
        if self.evaluation.exists():
            raise ValueError(
                f"Cannot copy reviews to gene {self.name} - it already has existing reviews. "
                "This method is only for newly added genes."
            )

        # Filter evaluations to the selected users
        evaluations_to_copy = [
            ev for ev in source_gene_entry.evaluation.all()
            if ev.user_id in user_ids_to_copy
        ]

        if not evaluations_to_copy:
            return

        # Filter evidences from the selected reviewers
        filtered_user_ids = {ev.user_id for ev in evaluations_to_copy}
        evidences_to_copy = [
            ev for ev in source_gene_entry.evidence.all()
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

        self.evaluation.add(*[new_evaluations[key]["evaluation"] for key in new_evaluations])
        self.evidence.add(*[ev for key in new_evaluations for ev in new_evaluations[key]["evidences"]])

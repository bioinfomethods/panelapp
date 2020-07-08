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
from django.db import models
from django.db.models import (
    Case,
    Sum,
    Value,
    When,
)
from django.urls import reverse
from django.utils.functional import cached_property
from model_utils import Choices
from model_utils.models import TimeStampedModel

from .panel_types import PanelType


class GenePanelManager(models.Manager):
    def get_panel(self, pk):
        if pk.isdigit():
            return super().get_queryset().get(pk=pk)
        else:
            return super().get_queryset().get(old_pk=pk)

    def get_active_panel(self, pk):
        return self.get_panel(pk).active_panel


class GenePanel(TimeStampedModel):
    STATUS = Choices("promoted", "public", "retired", "internal", "deleted")

    old_pk = models.CharField(
        max_length=24, null=True, blank=True, db_index=True
    )  # Mongo ObjectID hex string
    name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        choices=STATUS, default=STATUS.internal, max_length=36, db_index=True
    )
    types = models.ManyToManyField(PanelType)
    signed_off = models.ForeignKey(
        "panels.HistoricalSnapshot", on_delete=models.PROTECT, blank=True, null=True
    )

    objects = GenePanelManager()

    def __str__(self):
        ap = self.active_panel
        return "{} version {}.{}".format(self.name, ap.major_version, ap.minor_version)

    @property
    def unique_id(self):
        return self.old_pk if self.old_pk else str(self.pk)

    def approve(self):
        self.status = GenePanel.STATUS.public
        self.save()

    def is_approved(self):
        return self.status in [GenePanel.STATUS.public, GenePanel.STATUS.promoted]

    def is_public(self):
        return self.status in [GenePanel.STATUS.public, GenePanel.STATUS.promoted]

    def is_deleted(self):
        return self.status == GenePanel.STATUS.deleted

    def reject(self):
        self.status = GenePanel.STATUS.internal
        self.save()

    def get_absolute_url(self):
        return reverse("panels:detail", args=(self.pk,))

    def _prepare_panel_query(self):
        """Returns a queryset for all snapshots ordered by version"""

        return (
            self.genepanelsnapshot_set.prefetch_related("panel", "level4title")
            .annotate(
                number_of_green_genes=Sum(
                    Case(
                        When(
                            genepanelentrysnapshot__saved_gel_status__gt=3,
                            then=Value(1),
                        ),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    )
                ),
                number_of_amber_genes=Sum(
                    Case(
                        When(genepanelentrysnapshot__saved_gel_status=2, then=Value(1)),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    )
                ),
                number_of_red_genes=Sum(
                    Case(
                        When(genepanelentrysnapshot__saved_gel_status=1, then=Value(1)),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    )
                ),
                number_of_gray_genes=Sum(
                    Case(
                        When(genepanelentrysnapshot__saved_gel_status=0, then=Value(1)),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    )
                ),
            )
            .order_by("-major_version", "-minor_version", "-modified", "-pk")
        )

    def clear_cache(self):
        if self.active_panel:
            del self.__dict__["active_panel"]

    @cached_property
    def active_panel(self):
        """Return the panel with the largest version"""

        return self.genepanelsnapshot_set.order_by(
            "-major_version", "-minor_version", "-modified", "-pk"
        ).first()

    @cached_property
    def active_panel_extra(self):
        """Return the panel with the largest version and related info"""

        return (
            self.genepanelsnapshot_set.prefetch_related(
                "panel",
                "level4title",
                "genepanelentrysnapshot_set",
                "genepanelentrysnapshot_set__tags",
                "genepanelentrysnapshot_set__evidence",
                "genepanelentrysnapshot_set__gene_core",
                "genepanelentrysnapshot_set__evaluation__comments",
            )
            .order_by("-major_version", "-minor_version", "-modified", "-pk")
            .first()
        )

    def get_panel_version(self, version):
        """Get a specific version. Version argument should be a string"""

        major_version, minor_version = version.split(".")
        return (
            self._prepare_panel_query()
            .filter(major_version=int(major_version), minor_version=int(minor_version))
            .first()
        )

    def add_activity(self, user, text, entity=None):
        """Adds activity for this panel"""

        self.active_panel.add_activity(user, text)

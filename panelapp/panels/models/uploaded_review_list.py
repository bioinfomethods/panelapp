##
## Copyright (c) 2016-2020 Genomics England Ltd.
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
import logging
import re

from django.db import (
    models,
    transaction,
)
from django.utils.encoding import force_str
from model_utils.models import TimeStampedModel

from accounts.models import User
from panels.enums import VALID_ENTITY_FORMAT
from panels.exceptions import (
    GenesDoNotExist,
    ImportValidationError,
    IsSuperPanelException,
    TSVIncorrectFormat,
    UsersDoNotExist,
)
from panels.tasks.reviews import import_reviews

from ._uploaded_common import (
    AbstractRow,
    InvalidRow,
    check_panels,
    get_missing_genes,
)
from .codes import ProcessingRunCode
from .evaluation import Evaluation
from .genepanelentrysnapshot import GenePanelEntrySnapshot
from .genepanelsnapshot import GenePanelSnapshot

LOGGER = logging.getLogger(__name__)

MAP_COLUMN_TO_ENTITY_DATA = [
    {
        "name": "gene_symbol",
        "type": str,
        "validators": [lambda val, _: re.fullmatch(VALID_ENTITY_FORMAT, val)],
    },
    {"name": "source", "ignore": True},
    {
        "name": "level4",
        "type": str,
    },
    {"name": "level3", "ignore": True},
    {"name": "level2", "ignore": True},
    {"name": "moi", "type": str},
    {"name": "phenotypes", "type": "unique-list"},
    {"name": "omim", "ignore": True},
    {"name": "oprahanet", "ignore": True},
    {"name": "hpo", "ignore": True},
    {"name": "publications", "type": "unique-list"},
    {"name": "description", "ignore": True},
    {"name": "12", "ignore": True},
    {"name": "13", "ignore": True},
    {"name": "14", "ignore": True},
    {"name": "15", "ignore": True},
    {"name": "16", "ignore": True},
    {"name": "mop", "type": str},
    {"name": "rating", "type": str},
    {
        "name": "current_diagnostic",
        "type": bool,
        "validators": [
            lambda val, _: val.replace("\t", " ").strip().lower()
            in ["true", "false", ""]
        ],
    },
    {"name": "comment", "type": str},
    {"name": "username", "type": str},
]

PANELAPP_RATINGS_MAP = {
    "Green List (high evidence)": "GREEN",
    "Red List (low evidence)": "RED",
    "I don't know": "AMBER",
}

VALID_PANELAPP_RATINGS = set(
    list(PANELAPP_RATINGS_MAP.keys()) + list(PANELAPP_RATINGS_MAP.values())
)


class ReviewRow(AbstractRow):
    MAP_COLUMN_TO_ENTITY_DATA = MAP_COLUMN_TO_ENTITY_DATA

    def validate(self):
        panel_name = self.data["level4"]
        gene_symbol = self.data["gene_symbol"]
        gene = GenePanelEntrySnapshot.objects.filter(
            panel__panel__name=panel_name, gene__gene_symbol=gene_symbol
        ).first()
        if not gene:
            msg = f"Gene:{gene_symbol} is not on Panel:{panel_name}"
            self.invalid.append(InvalidRow(self.line_number, msg, "gene_symbol"))

        moi = self.data["moi"]
        if moi and moi not in Evaluation.MODES_OF_INHERITANCE:
            msg = f"MOI value ({moi}) is invalid"
            self.invalid.append(
                InvalidRow(self.line_number, msg, "mode of inheritance")
            )

        rating = self.data["rating"]
        if rating and rating not in VALID_PANELAPP_RATINGS:
            msg = f"Incorrect gene rating: {rating}"
            self.invalid.append(InvalidRow(self.line_number, msg, "rating"))

        mop = self.data["mop"]
        if mop and mop not in Evaluation.MODES_OF_PATHOGENICITY:
            msg = f"Incorrect mode of pathogenicity: {mop}"
            self.invalid.append(
                InvalidRow(self.line_number, msg, "mode of pathogenicity")
            )

    def post_process(self):
        if self.invalid:
            return False

        rating = self.data["rating"]
        if rating in PANELAPP_RATINGS_MAP:
            self.data["rating"] = PANELAPP_RATINGS_MAP[rating]


def check_genes(unique_genes):
    missing_genes = get_missing_genes(unique_genes)
    if missing_genes:
        raise GenesDoNotExist(", ".join(missing_genes))


def check_users(unique_users):
    db_unique_users = User.objects.filter(username__in=unique_users).values_list(
        "username", flat=True
    )

    if db_unique_users.count() != len(unique_users):
        missing_users = unique_users - set(db_unique_users)
        raise UsersDoNotExist(", ".join(missing_users))


class UploadedReviewsList(TimeStampedModel):
    """Review files uploaded by the curation team"""

    imported = models.BooleanField(default=False)
    reviews = models.FileField(upload_to="reviews", max_length=255)
    import_log = models.TextField(default="")

    panels = None
    database_users = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.panels = {}
        self.database_users = {}

    def process_line(self, row: ReviewRow, user):
        """Process individual line"""

        panel_name = row.data["level4"]
        gene_symbol = row.data["gene_symbol"]
        user = self.database_users.get(row.data["username"])

        panel = self.panels.get(panel_name)
        gene = panel.get_gene(gene_symbol)

        evaluation_data = {
            "comment": row.data["comment"],
            "mode_of_pathogenicity": row.data["mop"],
            "phenotypes": row.data["phenotypes"],
            "moi": row.data["moi"],
            "current_diagnostic": row.data["current_diagnostic"],
            "rating": row.data["rating"],
            "publications": row.data["publications"],
        }

        gene.update_evaluation(user, evaluation_data, append_only=True)

    def process_file(self, user, background=False):
        """Process uploaded file.

        If file has more than 200 lines process it in the background.

        Returns ProcessingRunCode
        """
        with self.reviews.open(mode="rb") as file:
            try:
                textfile_content = force_str(
                    file.read(), encoding="utf-8", errors="ignore"
                )
                reader = csv.reader(textfile_content.splitlines(), delimiter="\t")
                next(reader)  # skip header
            except csv.Error:
                LOGGER.error("File Import. Wrong file format", exc_info=True)
                raise TSVIncorrectFormat("Wrong File Format. Please use TSV.")

            with transaction.atomic():
                lines = list(reader)

                incorrect_lines = [l for l in lines if len(l) < 21]
                if incorrect_lines:
                    raise TSVIncorrectFormat(
                        f"Following lines have less than 21 columns: {'; '.join(incorrect_lines)}"
                    )

                unique_panels = {l[2].strip() for l in lines}
                check_panels(unique_panels)

                unique_genes = {l[0].strip() for l in lines}
                check_genes(unique_genes)

                unique_users = {l[21].strip() for l in lines}
                check_users(unique_users)

                # process line by line
                # validate data before processing it
                rows = []
                invalid_messages = []
                for index, line in enumerate(lines):
                    row = ReviewRow.from_row(line_number=index + 2, row_data=line)
                    if row.invalid:
                        invalid_messages.extend([str(i) for i in row.invalid])
                    rows.append(row)

                if invalid_messages:
                    raise ImportValidationError(
                        "Some lines failed validation", invalid_messages
                    )

                if (
                    not background and len(lines) > 50
                ):  # panel is too big, process in the background
                    import_reviews.delay(user.pk, self.pk)
                    return ProcessingRunCode.PROCESS_BACKGROUND

                panel_names = set([r.data["level4"] for r in rows])
                self.panels = {}
                panels = GenePanelSnapshot.objects.filter(
                    panel__name__in=panel_names
                ).prefetch_related("panel")
                for gps in panels:
                    if gps.is_super_panel:
                        raise IsSuperPanelException
                    self.panels[gps.panel.name] = gps.increment_version()

                self.database_users = {
                    u.username: u
                    for u in User.objects.filter(username__in=unique_users)
                }

                errors = {"invalid_lines": []}
                for row in rows:
                    try:
                        self.process_line(row, user)
                    except TSVIncorrectFormat as line_error:
                        errors["invalid_lines"].append(str(line_error))

                if errors["invalid_lines"]:
                    raise TSVIncorrectFormat(", ".join(errors["invalid_lines"]))

                self.imported = True
                self.save()
                return ProcessingRunCode.PROCESSED

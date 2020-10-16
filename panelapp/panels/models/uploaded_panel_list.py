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
from typing import (
    Optional,
    Set,
)

from django.db import (
    models,
    transaction,
)
from django.utils.encoding import force_text
from model_utils.models import TimeStampedModel
from psycopg2.extras import NumericRange

from accounts.models import User
from panels.enums import VALID_ENTITY_FORMAT
from panels.exceptions import (
    GenesDoNotExist,
    ImportException,
    ImportValidationError,
    RegionsDoNotExist,
    STRsDoNotExist,
    TSVIncorrectFormat,
)
from panels.tasks.panels import import_panel

from ._uploaded_common import (
    AbstractRow,
    InvalidRow,
    check_panels,
    get_missing_genes,
    validate_moi,
    validate_mop,
)
from .codes import ProcessingRunCode
from .gene import Gene
from .genepanelsnapshot import GenePanelSnapshot
from .region import Region
from .strs import STR

LOGGER = logging.getLogger(__name__)


def validate_gene_symbol(value, line_data):
    """Gene symbol for regions can be empty"""
    if line_data[1] == "region" and not value:
        return True

    return re.fullmatch(VALID_ENTITY_FORMAT, value)


MAP_COLUMN_TO_ENTITY_DATA = [
    {
        "name": "entity_name",
        "type": str,
        "validators": [lambda val, _: re.fullmatch(VALID_ENTITY_FORMAT, val)],
    },
    {"name": "entity_type", "type": str,},
    {"name": "gene_symbol", "type": str, "validators": [validate_gene_symbol],},
    {"name": "sources", "type": "unique-list"},
    {"name": "level4", "type": str,},
    {"name": "level3", "type": str},
    {"name": "level2", "type": str},
    {"name": "moi", "type": str},
    {"name": "phenotypes", "type": "unique-list"},
    {"name": "omim", "type": "unique-list"},
    {"name": "orphanet", "type": "unique-list"},
    {"name": "hpo", "type": "unique-list"},
    {"name": "publications", "type": "unique-list"},
    {"name": "description", "type": "str"},
    {"name": "flagged", "type": "boolean"},
    {"name": "gel_status", "ignore": True},
    {"name": "user_ratings", "ignore": True},
    {"name": "version", "ignore": True},
    {"name": "ready", "ignore": True},
    {"name": "mode_of_pathogenicity", "type": str},
    {"name": "EnsemblId(GRch37)", "ignore": True},
    {"name": "EnsemblId(GRch38)", "ignore": True},
    {"name": "HGNC", "ignore": True},
    {"name": "chromosome", "type": str},
    {"name": "position_37_start", "type": int},
    {"name": "position_37_end", "type": int},
    {"name": "position_38_start", "type": int},
    {"name": "position_38_end", "type": int},
    {"name": "repeated_sequence", "type": str},
    {"name": "normal_repeats", "type": int},
    {"name": "pathogenic_repeats", "type": int},
    {
        "name": "haploinsufficiency_score",
        "type": str,
        "validators": [lambda v, _: len(v) < 3],
    },
    {
        "name": "triplosensitivity_score",
        "type": str,
        "validators": [lambda v, _: len(v) < 3],
    },
    {"name": "required_overlap_percentage", "type": int},
    {"name": "type_of_variants", "type": str},
    {"name": "verbose_name", "type": str},
]

REQUIRED_LINE_LENGTH = {"gene": 15, "str": 31, "region": 35}

MAP_ENTITY_METHODS = {
    "gene": {
        "check_exists": "has_gene",
        "add": "add_gene",
        "update": "update_gene",
        "clear": [
            "cached_genes",
            "current_genes_count",
            "current_genes_duplicates",
            "current_genes",
            "get_all_genes",
            "get_all_genes_extra",
        ],
    },
    "str": {
        "check_exists": "has_str",
        "add": "add_str",
        "update": "update_str",
        "clear": ["cached_strs", "get_all_strs", "get_all_strs_extra"],
    },
    "region": {
        "check_exists": "has_region",
        "add": "add_region",
        "update": "update_region",
        "clear": ["cached_regions", "get_all_regions", "get_all_regions_extra"],
    },
}


class UploadedPanelList(TimeStampedModel):
    imported = models.BooleanField(default=False)
    panel_list = models.FileField(upload_to="panels", max_length=255)
    import_log = models.TextField(default="")

    _cached_panels = {}

    def process_line(self, entity_row: "EntityRow", user: User):
        entity_data = entity_row.data
        panel = self.get_panel(entity_data)

        # Add or update entity
        methods = MAP_ENTITY_METHODS[entity_data["entity_type"]]

        if not getattr(panel, methods["check_exists"])(entity_data["entity_name"]):
            getattr(panel, methods["add"])(
                user, entity_data["entity_name"], entity_data, False
            )
        else:
            getattr(panel, methods["update"])(
                user, entity_data["entity_name"], entity_data, True
            )

        getattr(panel, "clear_cache")(methods["clear"])

    def get_panel(self, line_data):
        return self._cached_panels[line_data["level4"]]

    def process_file(self, user, background=False):
        """Process uploaded file

        If the file has too many lines it wil run the import in the background.abs

        returns ProcessingRunCode
        """
        with self.panel_list.open(mode="rt") as file:
            # When file is stored in S3 we need to read the file returned by FieldFile.open(), then force it into text
            # and split the content into lines
            try:
                textfile_content = force_text(
                    file.read(), encoding="utf-8", errors="ignore"
                )
                reader = csv.reader(textfile_content.splitlines(), delimiter="\t")
                next(reader)  # skip header
            except csv.Error:
                LOGGER.error("File Import. Wrong file format", exc_info=True)
                raise TSVIncorrectFormat("Wrong File Format. Please use TSV.")

        lines = list(reader)

        empty_lines = [str(i + 2) for i, l in enumerate(lines) if not l]

        if empty_lines:
            raise ImportValidationError("Some lines are empty", empty_lines)

        unique_panels = {l[4].strip() for l in lines}

        check_panels(unique_panels)
        check_genes(lines)
        check_strs(lines)
        check_regions(lines)

        # validate data before processing it
        rows = []
        invalid_messages = []
        for index, line in enumerate(lines):
            row = EntityRow.from_row(line_number=index + 2, row_data=line)
            if row.invalid:
                invalid_messages.extend([str(i) for i in row.invalid])
            rows.append(row)

        if invalid_messages:
            raise ImportValidationError(
                "Some lines failed validation", invalid_messages
            )

        errors = {"invalid_lines": []}

        max_entities = get_panel_entities_count_max(unique_panels)

        if not background and (len(lines) > 200 or max_entities > 200):
            import_panel.delay(user.pk, self.pk)
            return ProcessingRunCode.PROCESS_BACKGROUND

        with transaction.atomic():
            for panel_name in unique_panels:
                gp = GenePanelSnapshot.objects.get(panel__name=panel_name)
                self._cached_panels[panel_name] = gp.increment_version()

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


def get_panel_entities_count_max(unique_panels):
    num_of_entities = [
        stat.get("number_of_entities", 0)
        for stat in GenePanelSnapshot.objects.filter(
            panel__name__in=unique_panels
        ).values_list("stats", flat=True)
        if stat
    ]
    return max(num_of_entities) if num_of_entities else 0


def check_genes(lines):
    unique_genes = {l[2] for l in lines if l[2]}

    missing_genes = get_missing_genes(unique_genes)
    if missing_genes:
        raise GenesDoNotExist(", ".join(missing_genes))

    # check genes symbol and entity name match
    mismatching_genes_lines = []
    for index, line in enumerate(lines):
        if not line:
            continue

        if line[1] == "gene" and line[0] != line[2]:
            mismatching_genes_lines.append(index + 2)

    if mismatching_genes_lines:
        affected_lines = ", ".join(sorted(map(str, mismatching_genes_lines)))
        raise ImportException(f"Mismatching gene symbol on lines: {affected_lines}")


def check_strs(lines):
    unique_strs = {l[0] for l in lines if l[1] == "str"}

    missing_strs = get_missing_strs(unique_strs)
    if missing_strs:
        raise STRsDoNotExist(", ".join(sorted(missing_strs)))


def check_regions(lines):
    unique_regions = {l[0] for l in lines if l[1] == "region"}

    missing_regions = get_missing_regions(unique_regions)
    if missing_regions:
        raise RegionsDoNotExist(", ".join(sorted(missing_regions)))


def get_missing_strs(unique_strs: Set[str]) -> Set[str]:
    db_unique_strs = STR.objects.filter(name__in=unique_strs).values_list(
        "name", flat=True
    )
    missing_items = set()
    if db_unique_strs.count() != len(unique_strs):
        missing_items = unique_strs - set(db_unique_strs)
    return missing_items


def get_missing_regions(unique_regions: Set[str]) -> Set[str]:
    db_unique_regions = Region.objects.filter(name__in=unique_regions).values_list(
        "name", flat=True
    )
    missing_items = set()
    if db_unique_regions.count() != len(unique_regions):
        missing_items = unique_regions - set(db_unique_regions)
    return missing_items


def get_gene(gene_symbol: str) -> Gene:
    return Gene.objects.get(gene_symbol=gene_symbol, active=True)


class EntityRow(AbstractRow):
    MAP_COLUMN_TO_ENTITY_DATA = MAP_COLUMN_TO_ENTITY_DATA

    def validate(self):
        stop_further_processing = self.validate_type_and_length()
        if stop_further_processing:
            # Don't process further as we don't have all data
            return

        self.validate_fields()

    def validate_type_and_length(self):
        """Check entity type and length

        Returns `True` if further processing should be stopped.
        """

        sanity_validators = [
            validate_required_length,
            validate_entity_type,
        ]

        stop_further_processing = False

        for validator in sanity_validators:
            invalid = validator(self.line_number, self.data)
            if invalid:
                self.invalid.append(invalid)
                stop_further_processing = True

        return stop_further_processing

    def post_process(self):
        if self.invalid:
            return False

        self.data["name"] = self.data["entity_name"]

        self.data["sources"] = [
            source.title()
            if source.lower()
            in {
                "expert review green",
                "expert review amber",
                "expert review red",
                "expert review removed",
            }
            else source
            for source in self.data.get("sources")
        ]

        if self.data.get("entity_type") == "str":
            self.data["position_37"] = [
                self.data["position_37_start"],
                self.data["position_37_end"],
            ]

        if (
            self.data.get("entity_type") in {"str", "region"}
            and self.data["position_38_start"]
            and self.data["position_38_end"]
        ):
            self.data["position_38"] = [
                self.data["position_38_start"],
                self.data["position_38_end"],
            ]

        gene_symbol = self.data["gene_symbol"]
        if self.data["entity_type"] == "gene" or gene_symbol:
            # Check if we want to add a gene which doesn't exist in our database
            try:
                self.data["gene"] = get_gene(gene_symbol)
            except Gene.DoesNotExist:
                self.invalid.append(
                    InvalidRow(
                        self.line_number,
                        f"Gene {gene_symbol} does not exist",
                        "gene_symbol",
                    )
                )

    def validate_fields(self):
        validators = [
            validate_moi,
            validate_mop,
            validate_sources,
        ]

        for validator in validators:
            invalid = validator(self.line_number, self.data)
            if invalid:
                self.invalid.append(invalid)

        if self.data["entity_type"] == "str":
            str_validators = [
                validate_str_data,
                validate_position_37,
                validate_position_38,
                validate_str_exists,
            ]
            for validator in str_validators:
                invalid = validator(self.line_number, self.data)
                if invalid:
                    self.invalid.append(invalid)
                    break  # stop processing as some value isn't available

        if self.data["entity_type"] == "region":
            region_validators = [
                validate_region_37_position,
                validate_position_38,
                validate_region_data,
                validate_region_exists,
            ]
            for validator in region_validators:
                invalid = validator(self.line_number, self.data)
                if invalid:
                    self.invalid.append(invalid)
                    break  # stop processing as some value isn't available


def validate_entity_type(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    if entity_data.get("entity_type", "") not in ["gene", "region", "str"]:
        LOGGER.error(
            f"TSV Import. Line: {line_number} Incorrect entity type: {entity_data.get('entity_type')}"
        )

        return InvalidRow(line_number, "Incorrect entity type", column="entity_type")


def validate_required_length(
    line_number: int, entity_data: dict
) -> Optional[InvalidRow]:
    if len(entity_data.keys()) < REQUIRED_LINE_LENGTH.get(
        entity_data["entity_type"], 1000
    ):
        LOGGER.error(
            f"TSV Import. Line: {line_number} Incorrect line length: {len(entity_data.keys())}"
        )
        return InvalidRow(line_number, "Incorrect line length")


def validate_missing_sources(
    line_number: int, entity_data: dict
) -> Optional[InvalidRow]:
    if not entity_data.get("sources"):
        LOGGER.error(f"TSV Import. Line: {line_number} Missing Sources")
        return InvalidRow(line_number, "Missing sources", "sources")


def validate_sources(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    sources = entity_data.get("sources")
    if sources and "Expert Review Green" in sources:
        moi = entity_data.get("moi")
        if moi == "Unknown":
            LOGGER.error(
                f"TSV Import. Line: {line_number} Incorrect MOI for Expert Review Green: {moi}"
            )
            return InvalidRow(
                line_number, f"Incorrect MOI For Expert Review Green: {moi}", "moi"
            )


def validate_str_data(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    if not all(
        [
            entity_data.get(value)
            for value in [
                "gene_symbol",
                "moi",
                "chromosome",
                "position_38_start",
                "position_38_end",
                "position_37_start",
                "position_38_end",
                "repeated_sequence",
                "normal_repeats",
                "pathogenic_repeats",
            ]
        ]
    ):
        LOGGER.error(f"TSV Import. Line: {line_number} Required STR Data Missing")
        return InvalidRow(line_number, "Required STR Data Missing")


def validate_str_exists(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    str_query = STR.objects.filter(
        name=entity_data["entity_name"],
        gene_core__gene_symbol=entity_data.get("gene_symbol"),
        chromosome=entity_data["chromosome"],
        position_38=NumericRange(
            entity_data["position_38_start"], entity_data["position_38_end"]
        ),
        position_37=NumericRange(
            entity_data["position_37_start"], entity_data["position_37_end"],
        ),
        repeated_sequence=entity_data.get("repeated_sequence"),
        normal_repeats=entity_data.get("normal_repeats"),
        pathogenic_repeats=entity_data.get("pathogenic_repeats"),
    )

    if not str_query.exists():
        LOGGER.error(
            f"TSV Import. Line: {line_number} STR Data Not Matching Panelapp STR"
        )
        return InvalidRow(line_number, "STR Data Not Matching Panelapp STR records")


def validate_region_37_position(
    line_number: int, entity_data: dict
) -> Optional[InvalidRow]:
    if entity_data["position_37_start"] or entity_data["position_37_end"]:
        LOGGER.error(f"TSV Import. Line: {line_number} Position 37 Must Be Blank")
        return InvalidRow(line_number, "Position 37 Must Be Blank", "position_37")


def validate_region_data(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    if not all(
        [
            entity_data.get(value)
            for value in [
                "chromosome",
                "position_38_start",
                "position_38_end",
                "type_of_variants",
                "verbose_name",
                "required_overlap_percentage",
            ]
        ]
    ):
        LOGGER.error(
            f"TSV Import. Line: {line_number} Required Region Data Missing: {len(entity_data.keys())}"
        )
        return InvalidRow(line_number, "Region Data Missing")


def validate_region_exists(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    query = Region.objects.filter(
        name=entity_data["entity_name"],
        chromosome=entity_data["chromosome"],
        position_38=NumericRange(
            entity_data["position_38_start"], entity_data["position_38_end"]
        ),
        type_of_variants=entity_data["type_of_variants"],
        verbose_name=entity_data["verbose_name"],
        required_overlap_percentage=entity_data["required_overlap_percentage"],
    )
    if not query.exists():
        LOGGER.error(
            f"TSV Import. Line: {line_number} Region Data Not Matching Panelapp Region"
        )
        return InvalidRow(
            line_number, "Region Data Not Matching Panelapp Region records"
        )

    if entity_data.get("type_of_variants") == "cnv_loss":
        haploinsufficiency_score = entity_data.get("haploinsufficiency_score")
        if not haploinsufficiency_score:
            LOGGER.error(
                f"TSV Import. Line: {line_number} Haploinsufficieny Score is required for cnv_loss variant: {haploinsufficiency_score}"
            )
            return InvalidRow(
                line_number,
                "Missing Haploinsufficieny Score",
                "haploinsufficiency_score",
            )

        if not query.filter(haploinsufficiency_score=haploinsufficiency_score).exists():
            LOGGER.error(
                f"TSV Import. Line: {line_number} Wrong Haploinsufficieny Score: f{haploinsufficiency_score}"
            )
            return InvalidRow(
                line_number,
                f"Haploinsufficieny Score Not Found in PanelApp: {haploinsufficiency_score}",
                "haploinsufficiency_score",
            )

    if entity_data.get("type_of_variants") == "cnv_gain":
        triplosensitivity_score = entity_data.get("triplosensitivity_score")
        if not triplosensitivity_score:
            LOGGER.error(
                f"TSV Import. Line: {line_number} Triplosensitivity Score is required for cnv_gain variant"
            )
            return InvalidRow(
                line_number,
                "Missing Triplosensitivity Score",
                "triplosensitivity_score",
            )

        if not query.filter(triplosensitivity_score=triplosensitivity_score).exists():
            LOGGER.error(
                f"TSV Import. Line: {line_number} Triplosensitivity Score for Region does not match the one in Panelapp: {triplosensitivity_score}"
            )
            return InvalidRow(
                line_number,
                f"Triplosensitivity Score Not Found in PanelApp: {triplosensitivity_score}",
                "triplosensitivity_score",
            )


def validate_position_37(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    pos_37 = [entity_data["position_37_start"], entity_data["position_37_end"]]
    if (any(pos_37) and not all(pos_37)) or (
        all(pos_37)
        and entity_data["position_37_start"] >= entity_data["position_37_end"]
    ):
        LOGGER.error(
            f"TSV Import. Line: {line_number} Incorrect build 37 coordinates: {pos_37}"
        )
        return InvalidRow(line_number, "Incorrect b37 coordinates", "position_37")


def validate_position_38(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    if not entity_data["position_38_start"] or not entity_data["position_38_end"]:
        LOGGER.error(f"TSV Import. Line: {line_number} Missing b38 start or end")
        return InvalidRow(line_number, "Missing b38 start or end", "position_38")
    elif entity_data["position_38_start"] >= entity_data["position_38_end"]:
        LOGGER.error(f"TSV Import. Line: {line_number} Incorrect b38 start")
        return InvalidRow(line_number, "Incorrect b38 start position", "position_38")

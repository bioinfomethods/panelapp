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

"""Set of common validation rules for uploaded files, entity upload or review upload.
"""
import logging
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Callable,
    List,
    Optional,
    Set,
    TypedDict,
    Union,
)

from django.db.models import Count

from panels.exceptions import ImportException
from panels.models.evaluation import Evaluation
from panels.models.gene import Gene
from panels.models.genepanel import GenePanel
from panels.models.genepanelsnapshot import GenePanelSnapshot

LOGGER = logging.getLogger(__name__)


class InvalidRow:
    def __init__(self, line: int, message: str, column: Optional[str] = None):
        self.line = line
        self.message = message
        self.column = column

    def __str__(self):
        if self.column is not None:
            return f"Row {self.line}, column '{self.column}' is invalid: {self.message}"
        return f"Row {self.line} is invalid: {self.message}"


class RowFieldMapping(TypedDict, total=False):
    """Map each column to a separate definition for processing when file is uploaded

    `name` is the dict attribute which will be passed to the update function later, can
        be any value when ignore is set to True
    `ignore` - if it's ok to ignore the column
    `type` - convert value to a type, `unique-list` is converted to Set[str] and removes
        TAB and also strips the values
    `modifiers` - list of functions which can be used to modify the original value
    """

    name: str
    ignore: Optional[bool]
    type: Optional[Union[Callable, str]]
    modifiers: Optional[List[Callable]]
    validators: Optional[List[Callable]]


class AbstractRow(ABC):
    MAP_COLUMN_TO_ENTITY_DATA: List[RowFieldMapping] = []

    def __init__(self, line_number: int, row_data: List[str]):
        self.line_number = line_number
        self.row_data = row_data
        self.invalid: List[InvalidRow] = []
        self.data = {}  # entity data

    @classmethod
    def from_row(cls, line_number: int, row_data: List[str]):
        """Depending on the row type, i.e. gene, str, region import correct fields."""

        obj = cls(line_number, row_data)
        obj.map_row()
        if not obj.invalid:
            obj.validate()

        if not obj.invalid:
            obj.post_process()
        return obj

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def post_process(self):
        pass

    def map_row(self):
        """Map TSV row data to `data` dictionary"""
        column = ""
        try:
            for index, item in enumerate(self.row_data):
                item_mapping = self.MAP_COLUMN_TO_ENTITY_DATA[index]
                column = item_mapping["name"]

                for validators in item_mapping.get("validators", []):
                    if not validators(item, self.row_data):
                        raise ValueError("Validation error")

                if item_mapping.get("ignore", False):
                    item = None
                elif item_mapping["type"] in ["boolean", bool]:
                    item = item.capitalize()
                    item = item.replace("\t", " ").strip().lower() == "true"
                elif item_mapping["type"] in [str, int]:
                    if item == "":
                        item = ""
                    else:
                        item = item_mapping["type"](item)

                        if isinstance(item, str):
                            item = item.replace("\t", " ").strip()

                        for modifier in item_mapping.get("modifiers", []):
                            item = modifier(item)
                elif item_mapping["type"] == "unique-list":
                    item = list(
                        set(
                            [
                                i.strip().replace("\t", " ")
                                for i in item.split(";")
                                if i.strip()
                            ]
                        )
                    )

                self.data[item_mapping["name"]] = item
        except IndexError:
            # it's not really an error as file can contain more columns
            # that we need to parse
            LOGGER.warning(f"Extra columns on line {self.line_number}", exc_info=True)
            pass
        except ValueError as e:
            LOGGER.exception(
                f"Line {self.line_number} column {column} has incorrect field value",
                exc_info=True,
            )
            self.invalid.append(
                InvalidRow(
                    self.line_number, message="Incorrect field value", column=column
                )
            )


# Some common validators for both types of upload files (entities and reviews)


def validate_moi(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    moi = entity_data.get("moi")
    if moi:
        if moi not in Evaluation.MODES_OF_INHERITANCE:
            LOGGER.error(f"TSV Import. Line: {line_number} Incorrect MOI: {moi}")
            return InvalidRow(line_number, f"Incorrect MOI: {moi}", "moi")


def validate_mop(line_number: int, entity_data: dict) -> Optional[InvalidRow]:
    mop = entity_data.get("mode_of_pathogenicity")
    if mop:
        if mop not in Evaluation.MODES_OF_PATHOGENICITY:
            LOGGER.error(
                f"TSV Import. Line: {line_number} Incorrect Modes of Pathogenicity: {mop}"
            )
            return InvalidRow(
                line_number,
                f"Incorrect Mode of Pathogenicity: {mop}",
                "mode_of_pathogenicity",
            )


def get_missing_panels(unique_panels: Set[str]) -> Set[str]:
    """Get any panels missing in the db

    :param unique_panels: Unique panels in the file
    :return: missing panels
    """

    db_unique_panels = (
        GenePanelSnapshot.objects.filter(panel__name__in=unique_panels,)
        .exclude(panel__status=GenePanel.STATUS.deleted)
        .values_list("panel__name", flat=True)
    )

    missing_panels = {}
    if db_unique_panels.count() != len(unique_panels):
        missing_panels = unique_panels - set(db_unique_panels)
    return missing_panels


def get_missing_genes(unique_genes: Set[str]) -> Set[str]:
    """Check if any genes are missing in our database (or aren't active)

    :param unique_genes: set of gene symbols
    :return: set of genes missing in the db
    """

    db_unique_genes = Gene.objects.filter(
        gene_symbol__in=unique_genes, active=True
    ).values_list("gene_symbol", flat=True)

    missing_genes = set()

    if db_unique_genes.count() != len(unique_genes):
        missing_genes = unique_genes - set(db_unique_genes)

    return missing_genes


def check_panels(unique_panels):
    missing_panels = get_missing_panels(unique_panels)
    if missing_panels:
        affected_panels = "; ".join(missing_panels)
        raise ImportException(
            f"Following panels are missing in PanelApp: {affected_panels}"
        )

    super_panels = (
        GenePanelSnapshot.objects.filter(panel__name__in=unique_panels)
        .annotate(child_panels_count=Count("child_panels"))
        .filter(child_panels_count__gt=0)
        .values_list("panel__name", flat=True)
    )

    if super_panels:
        affected_panels = "; ".join(super_panels)
        raise ImportException(f"Following panels are super panels: {affected_panels}")

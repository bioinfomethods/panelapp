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

"""
Daily checks for mode of inheritances in public v1+ panels for green genes and
helper functions.
Also checks if MOI data doesn't match OMIM.
Emails are scheduled via celery beat, time set in settings.
"""

import csv
import logging
import tempfile
from enum import Enum
from functools import lru_cache
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
)

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from requests.exceptions import HTTPError

from panels.enums import MODE_OF_INHERITANCE_VALID_CHOICES

LOGGER = logging.getLogger(__name__)

MoiMistmatchDict = Dict[str, Dict[str, Any]]


MOI_MAPPING = {
    "MONOALLELIC,": ["Autosomal dominant", "dominant", "AD", "DOMINANT"],
    "BIALLELIC,": ["Autosomal recessive", "recessive", "AR", "RECESSIVE"],
    "BOTH": [
        "Autosomal recessive",
        "Autosomal dominant",
        "recessive",
        "dominant",
        "AR/AD",
        "AD/AR",
        "DOMINANT/RECESSIVE",
        "RECESSIVE/DOMINANT",
    ],
    "X-LINKED:": [
        "X-linked recessive",
        "XLR",
        "X-linked dominant",
        "x-linked over-dominance",
        "X-LINKED",
        "X-linked",
        "XLD",
        "XL",
    ],
    "MITOCHONDRIAL": ["Mitochondrial"],
}

X_LINKED_MOI = {
    "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
    "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may "
    "cause disease (may be less severe, later onset than males)",
}

MONOALLELIC_MOI = {
    "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
    "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
}

VALID_MOI_VALUES = [k for k, _ in MODE_OF_INHERITANCE_VALID_CHOICES]


class CheckType(Enum):
    OMIM_COMPARISON = "OMIM Comparison"
    ACROSS_PANELS_CHECKS = "Across Panel Checks"
    VALUE_NOT_ALLOWED = "MOI Not Allowed Values"


class IncorrectMoiGene:
    """Model to keep the incorrect data for each Gene"""

    CSV_HEADER = (
        "check_type",
        "gene",
        "panel",
        "panel_id",
        "moi",
        "message",
    )

    __slots__ = CSV_HEADER

    def __init__(
        self,
        gene_name: str,
        panel_name: str,
        panel_id: int,
        moi: str,
        message: str,
        check_type: CheckType,
    ):
        self.check_type = check_type
        self.gene = gene_name
        self.panel = panel_name
        self.panel_id = panel_id
        self.moi = moi
        self.message = message

    @classmethod
    def from_gene(cls, gene: "GenePanelEntrySnapshot", check_type: CheckType, msg: str):
        return cls(
            gene_name=gene.name,
            panel_name=str(gene.panel),
            panel_id=gene.panel.panel_id,
            moi=gene.moi,
            message=msg,
            check_type=check_type.value,
        )

    @property
    def row(self):
        """Returns values for CSV row"""

        return [getattr(self, attr) for attr in self.CSV_HEADER]


@shared_task
def moi_check():
    """
    AUTOMATED MOI CHECK
    Does a daily systematic check of all MOIs for current Green genes on Panels V1+.
    Checking for consistency with chromosome, between panels and with OMIM database.

    Data integrity checks:
        - Each Green gene on a public Version 1+ has a mode of inheritance that follows
          the standardised terms here.
        - No Green genes on a public Version 1+ panel should have a missing mode of
          inheritance or 'Unknown' selected - all MOIs will be applied to these genes
          when run through the pipeline.
        - No Green genes on a public Version 1+ panel should have a MOI 'Other - please
          specify in evaluation comments' as variants in this gene will not be tiered.
          The exception to this are if there are on the Y-chromosome (e.g. SRY).
        - Genes with X-linked MOI are on the X-chromosome.

    For Green genes on version 1+ panels also:
        - review MOI between panels to ensure the MOI for a gene is consistent in all
          panels: pull out differences and provide a file to the Curation team. This
          file should include following columns:
          gene, panel, panel code, MOI
          These differences may be valid, and the gene may have a different MOI for
          different phenotypes, but this will allow us to check this.
        - compare MOI in PanelApp against the MOI in OMIM
    """

    green_genes = get_genes()

    incorrect_moi = []

    checks = [
        moi_check_is_empty,
        moi_check_non_standard,
        moi_check_other,
        moi_check_chr_x,
        moi_check_mt,
    ]

    if settings.OMIM_API_KEY:
        checks.append(moi_check_omim)
    else:
        LOGGER.warning("No OMIM API key specified")

    for gene in green_genes:
        for check in checks:
            incorrect = check(gene)
            if incorrect:
                LOGGER.debug(
                    "Found incorrect MOI",
                    extra={
                        "func": str(check),
                        "gene_symbol": gene.name,
                        "panel": str(gene.panel),
                    },
                )
                incorrect_moi.append(incorrect)
                break

    # add mismatching genes
    incorrect_moi.extend(multiple_moi_genes(get_genes()))

    if incorrect_moi:
        LOGGER.info("Found incorrect MOIs", extra={"count": len(incorrect_moi)})
        content = get_csv_content(incorrect_moi)
        notify_panelapp_curators(content)
    else:
        LOGGER.info("Not sending email, no MOI errors detected")


def get_genes():
    """Get all active green genes in v1+ panels sorted by OMIM id

    :return: QuerySet Iterator
    """
    from panels.models.genepanelentrysnapshot import (
        GenePanel,
        GenePanelEntrySnapshot,
    )

    queryset = (
        GenePanelEntrySnapshot.objects.get_active()
        .filter(
            saved_gel_status__gte=3,
            panel__major_version__gte=1,
            panel__panel__status__in=[
                GenePanel.STATUS.public,
                GenePanel.STATUS.promoted,
            ],
        )
        .prefetch_related("panel", "panel__level4title", "gene_core")
        .only(
            "moi",
            "gene",
            "panel__panel_id",
            "panel__level4title__name",
            "panel__major_version",
            "panel__minor_version",
        )
        .order_by("gene_core__omim_gene__0")  # for LRU caching
    )

    LOGGER.info("Found %s green genes", queryset.count())

    return queryset.iterator()


#
# Email related


def notify_panelapp_curators(content):
    """Notify PanelApp curation team about incorrect MOI data

    :param content: CSV attachement
    :return:
    """

    now = timezone.now().strftime("%Y-%m-%d")

    email = EmailMessage(
        f"MOI Errors - {now}",
        "Errors are attached in csv file.",
        settings.DEFAULT_FROM_EMAIL,
        [settings.PANEL_APP_EMAIL],
    )
    email.attach(f"incorrect_moi_{now}.csv", content, "text/csv")
    email.send()

    LOGGER.info("MOI Errors email sent")


def get_csv_content(incorrect_moi: List[IncorrectMoiGene]) -> str:
    """Create CSV File

    :param incorrect_moi: list of incorrect genes
    :return: file content
    """

    with tempfile.TemporaryFile(mode="w+t") as file:
        writer = csv.writer(file)
        writer.writerow(IncorrectMoiGene.CSV_HEADER)
        for incorrect_item in incorrect_moi:
            writer.writerow(incorrect_item.row)

        file.seek(0)
        return file.read()


# MOI Checks
def moi_check_omim(gene: "GenePanelEntrySnapshot") -> Optional[IncorrectMoiGene]:
    """Check if PanelApp MOI for the gene matches OMIM records

    :param gene:  GenePanelEntrySnapshot
    :return: IncorrectMoiGene if it doesn't match
    """

    omim_ids = gene.gene.get("omim_gene")
    if not omim_ids or len(omim_ids) == 0:
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.OMIM_COMPARISON, msg="Gene has no OMIM ID"
        )

    moi_prefix = gene.moi.split()[0]
    if moi_prefix not in MOI_MAPPING:
        return IncorrectMoiGene.from_gene(
            gene,
            check_type=CheckType.OMIM_COMPARISON,
            msg="Gene MOI can't be checked with OMIM",
        )

    omim_id = omim_ids[0]
    omim_moi = retrieve_omim_moi(omim_id)
    if not any(omim_moi):
        # could be due to networking issue
        LOGGER.warning(
            "OMIM has no MOI data",
            extra={
                "omim_id": omim_id,
                "gene_symbol": gene.name,
                "panel": str(gene.panel),
            },
        )
        return

    moi = set(MOI_MAPPING[moi_prefix])
    if moi & omim_moi:
        # all good, we have overlapping MOI
        return

    msg = "Green gene {} with discrepant OMIM MOI {} and {} on panel {}".format(
        gene.name, omim_moi, gene.moi, gene.panel
    )

    return IncorrectMoiGene.from_gene(
        gene, check_type=CheckType.OMIM_COMPARISON, msg=msg
    )


def moi_check_is_empty(gene: "GenePanelEntrySnapshot") -> Optional[IncorrectMoiGene]:
    """Check if MOI is empty or unknown

    :param gene: Gene snapshot
    :return: IncorrectMoiGene if it's empty
    """

    if not gene.moi or gene.moi == "Unknown":
        msg = "Green gene {} with {} MOI on panel {}".format(
            gene.name, gene.moi or "empty", gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )


def moi_check_other(gene: "GenePanelEntrySnapshot") -> Optional[IncorrectMoiGene]:
    """Check if MOI is Other on non chrY gene

    :param gene: GenePanelEntrySnapshot
    :return: IncorrectMoiGene or None
    """

    moi = gene.moi
    chromosome = get_chromosome(gene)

    if (
        moi in {"Other - please specifiy in evaluation comments", "Other"}
        and chromosome != "Y"
    ):
        msg = "Green gene {} with {} MOI on panel {}".format(
            gene.name, gene.moi, gene.panel
        )

        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )


def moi_check_chr_x(gene: "GenePanelEntrySnapshot") -> Optional[IncorrectMoiGene]:
    """Check if MOI is chrX linked

    :param gene: GenePanelEntrySnapshot
    :return: IncorrectMoiGene if it's non chrX MOI
    """

    moi = gene.moi
    chromosome = get_chromosome(gene)

    if chromosome == "X" and moi not in X_LINKED_MOI:
        msg = "Green gene {} on chromosome X with {} MOI on panel {}".format(
            gene.name, gene.moi, gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )

    if chromosome != "X" and moi in X_LINKED_MOI:
        msg = "Green gene {} on chromosome {} with X-LINKED MOI on panel {}".format(
            gene.name, chromosome, gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )


def moi_check_non_standard(gene):
    moi = gene.moi

    if moi not in VALID_MOI_VALUES:
        msg = "Green gene {} with non-standard {} MOI on panel {}".format(
            gene.name, moi, gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )


def moi_check_mt(gene) -> Optional[IncorrectMoiGene]:
    moi = gene.moi
    chromosome = get_chromosome(gene)

    if chromosome == "MT" and moi != "MITOCHONDRIAL":
        msg = "Green gene {} on chromosome MT with {} MOI on panel {}".format(
            gene.name, gene.moi, gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )

    if chromosome != "MT" and moi == "MITOCHONDRIAL":
        msg = "Green gene {} on chromosome {} with MITOCHONDRIAL MOI on panel {}".format(
            gene.name, chromosome, gene.panel
        )
        return IncorrectMoiGene.from_gene(
            gene, check_type=CheckType.VALUE_NOT_ALLOWED, msg=msg
        )


#
# MOI checks related


def multiple_moi_genes(
    genes: List["GenePanelEntrySnapshot"],
) -> List[IncorrectMoiGene]:
    """Get genes which have different MOI on different panels

    Unique genes and MOIs

    ```
    unique_genes: {
        "Gene1": {
            "moi": Set("A", "B", etc),
            "gpes": Set("Gene1, Panel 1", etc)
            "incorrect_moi": [IncorrectMoiGene],
            "processed_gpes": Set("Gene1, Panel 1")
        }
    }
    ```

    If each gene has more than 1 MOI - report them

    :param genes: GenePanelEntrySnapshot list
    :return: List of genes with mismatching MOIs
    """

    multiple_mois = get_unique_moi_genes(genes)
    LOGGER.info(f"Found {len(multiple_mois)} genes with duplicates")
    result = process_multiple_moi_dict(multiple_mois)
    LOGGER.info(f"Generated {len(result)} IncorrectMoiGenes")

    return result


def get_unique_moi_genes(genes: List["GenePanelEntrySnapshot"]) -> MoiMistmatchDict:
    unique_genes: MoiMistmatchDict = {}

    genes_with_moi = [g for g in genes if has_non_empty_moi(g.moi)]
    for gene in genes_with_moi:
        key = gene.name
        if key not in unique_genes:
            unique_genes[key] = {
                "moi": set(),
                "gpes": set(),
            }

        unique_genes[key]["moi"].add(gene.moi)
        unique_genes[key]["gpes"].add(gene)

    mismatching_genes = {
        key: val for key, val in unique_genes.items() if len(val["moi"]) > 1
    }
    LOGGER.debug("Genes with non unique MOI: %s", len(mismatching_genes))

    return mismatching_genes


def check_is_mismatching_gene(moi_set: Set[str]) -> bool:
    if moi_set == MONOALLELIC_MOI:
        return False
    return len(moi_set) > 1


def process_multiple_moi_dict(data: MoiMistmatchDict) -> List[IncorrectMoiGene]:
    """This doesn't generate every single combination as it would take more time.
    Example is provided in the tests.

    I.e. each GPES is only processed once.

    :param data: dictionary with genes and values (moi, gpes)
    :return: List of incorrect moi errors
    """
    out = []

    # in test it took ~ 15 seconds to run this for 728 genes
    # since it runs in async the performance isn't critical factor here, but
    # something to keep in mind and improve in the future

    for moi_data in data.values():
        gpes = sorted(moi_data["gpes"], key=lambda g: g.panel_id)
        out.extend(process_multiple_moi_single_gene(gpes))

    return out


def process_multiple_moi_single_gene(gpes):
    processed = set()  # to avoid processed genes
    out = []

    for gpe in gpes:
        for other_gpe in _get_unprocessed_genes(gpes, gpe, processed):
            out.append(
                IncorrectMoiGene.from_gene(
                    gpe,
                    check_type=CheckType.ACROSS_PANELS_CHECKS,
                    msg=f"Is {other_gpe.moi} on {other_gpe.panel}",
                )
            )
            processed.add(other_gpe)
        processed.add(gpe)

    return out


def _get_unprocessed_genes(genes, current_gene, processed):
    """Return the list of GPES which don't match current gene moi and haven't been processed

    :param genes: list of GPES
    :param current_gene: GPES
    :param processed: set of processed GPES
    :return: list of GPES which haven't been processed
    """
    return [
        other_gene
        for other_gene in genes
        if current_gene.moi != other_gene.moi
        and other_gene not in processed
        and {current_gene.moi, other_gene.moi} != MONOALLELIC_MOI
    ]


def has_non_empty_moi(moi: str) -> bool:
    """Check if MOI is empty or unknown"""

    return bool(moi and moi != "Unknown")


def get_chromosome(gene: "GenePanelEntrySnapshot") -> Optional[str]:
    """Get the chromosome

    :param gene: Gene snapshot
    :return: chromosome
    """

    gene_dict = gene.gene.get("ensembl_genes")
    if not gene_dict:
        return

    for grch_data in gene_dict.values():
        for build_data in grch_data.values():
            if build_data.get("location"):
                return build_data["location"].split(":")[0]

    LOGGER.warning(
        "Can't get chromosome from gene data",
        extra={"gene_symbol": gene.name, "panel": str(gene.panel)},
    )


@lru_cache(maxsize=1000)
def retrieve_omim_moi(omim_id):
    """
    OMIM API CALL
    Retrieve MOIs for a specific gene from OMIM and return them as a set to check against.
    param: str
        OMIM number
    """
    url = (
        f"https://api.omim.org/api/entry?mimNumber={omim_id}&include=geneMap&"
        f"include=externalLinks&format=json&apiKey={settings.OMIM_API_KEY}"
    )

    moi = set()
    try:
        res = requests.get(url)
        res.raise_for_status()
        omim_data = res.json()
        for omim_entry in omim_data["omim"]["entryList"]:
            phenotypes = (
                omim_entry["entry"].get("geneMap", {}).get("phenotypeMapList", [])
            )
            for phenotype in phenotypes:
                phenotype_inheritance = phenotype["phenotypeMap"][
                    "phenotypeInheritance"
                ]
                if phenotype_inheritance:
                    moi.update(phenotype_inheritance.split(";"))
    except HTTPError:
        LOGGER.error(
            "HTTP error on request to OMIM.", exc_info=True, extra={"omim_id": omim_id},
        )
    except ValueError:
        LOGGER.error(
            "OMIM response not in JSON format.",
            exc_info=True,
            extra={"omim_id": omim_id},
        )
    except Exception as err:
        LOGGER.error("Unexpected error", exc_info=True, extra={"omim_id": omim_id})

    return moi

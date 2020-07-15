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
from functools import lru_cache
from typing import (
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
)

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from requests.exceptions import HTTPError

from panels.models.genepanel import GenePanel
from panels.models.genepanelentrysnapshot import GenePanelEntrySnapshot

LOGGER = logging.getLogger(__name__)


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

MULTIPLE_MOI_EXCEPTIONS = [
    "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
    "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
]


class IncorrectMoiGene:
    """Model to keep the incorrect data for each Gene"""

    CSV_HEADER = (
        "gene",
        "panel",
        "panel_id",
        "moi",
        "phenotypes",
        "publications",
        "message",
    )

    __slots__ = CSV_HEADER

    def __init__(
        self,
        gene_name: str,
        panel_name: str,
        panel_id: int,
        moi: str,
        phenotypes: str,
        publications: str,
        message: str,
    ):
        self.gene = gene_name
        self.panel = panel_name
        self.panel_id = panel_id
        self.moi = moi
        self.phenotypes = phenotypes
        self.publications = publications
        self.message = message

    @classmethod
    def from_gene(cls, gene: GenePanelEntrySnapshot, msg: str):
        return cls(
            gene_name=gene.name,
            panel_name=str(gene.panel),
            panel_id=gene.panel_id,
            moi=gene.moi,
            phenotypes=";".join(gene.phenotypes) if gene.phenotypes else "",
            publications=";".join(gene.publications) if gene.publications else "",
            message=msg,
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
          gene, panel, panel code, MOI, phenotypes, publications.
          These differences may be valid, and the gene may have a different MOI for
          different phenotypes, but this will allow us to check this.
        - compare MOI in PanelApp against the MOI in OMIM
    """

    green_genes = get_genes()

    incorrect_moi = []

    checks = [
        moi_check_is_empty,
        moi_check_other,
        moi_check_chr_x,
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
                    extra_data={
                        "func": str(check),
                        "gene_symbol": gene.name,
                        "panel": str(gene.panel),
                    },
                )
                incorrect_moi.append(incorrect)
                break

    for gene, moi_values in multiple_moi_genes(green_genes):
        msg = "Green gene {} has different moi {} on panel {} than {}".format(
            gene.name, gene.moi, gene.panel, ";".join(moi_values)
        )
        incorrect_moi.append(IncorrectMoiGene.from_gene(gene, msg))

    if incorrect_moi:
        LOGGER.info("Found incorrect MOIs", extra_data={"count": len(incorrect_moi)})
        content = get_csv_content(incorrect_moi)
        notify_panelapp_curators(content)
    else:
        LOGGER.info("Not sending email, no MOI errors detected")


def get_genes():
    """Get all active green genes in v1+ panels sorted by OMIM id

    :return: QuerySet Iterator
    """

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

    email = EmailMessage(
        "MOI Errors",
        "Errors are attached in csv file.",
        settings.DEFAULT_FROM_EMAIL,
        [settings.PANEL_APP_EMAIL],
    )
    email.attach("incorrect_moi.csv", content, "text/csv")
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
def moi_check_omim(gene: GenePanelEntrySnapshot) -> Optional[IncorrectMoiGene]:
    """Check if PanelApp MOI for the gene matches OMIM records

    :param gene:  GenePanelEntrySnapshot
    :return: IncorrectMoiGene if it doesn't match
    """

    omim_ids = gene.gene.get("omim_gene")
    if not omim_ids or len(omim_ids) == 0:
        return IncorrectMoiGene.from_gene(gene, msg="Gene has no OMIM ID")

    moi_prefix = gene.moi.split()[0]
    if moi_prefix not in MOI_MAPPING:
        return IncorrectMoiGene.from_gene(
            gene, msg="Gene MOI can't be checked with OMIM"
        )

    omim_id = omim_ids[0]
    omim_moi = retrieve_omim_moi(omim_id)
    if not any(omim_moi):
        # could be due to networking issue
        LOGGER.warning(
            "OMIM has no MOI data",
            extra_data={
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

    msg = "Green gene {} with discrepant OMIM moi {} and {} on panel {}".format(
        gene.name, omim_moi, gene.moi, gene.panel
    )

    return IncorrectMoiGene.from_gene(gene, msg)


def moi_check_is_empty(gene: GenePanelEntrySnapshot) -> Optional[IncorrectMoiGene]:
    """Check if MOI is empty or unknown

    :param gene: Gene snapshot
    :return: IncorrectMoiGene if it's empty
    """

    if not gene.moi or gene.moi == "Unknown":
        msg = "Green gene {} with {} moi on panel {}".format(
            gene.name, gene.moi, gene.panel
        )
        return IncorrectMoiGene.from_gene(gene, msg)


def moi_check_other(gene: GenePanelEntrySnapshot) -> Optional[IncorrectMoiGene]:
    """Check if MOI is Other on non chrY gene

    :param gene: GenePanelEntrySnapshot
    :return: IncorrectMoiGene or None
    """

    moi = gene.moi
    chromosome = get_chromosome(gene)

    if moi == "Other - please specifiy in evaluation comments" and chromosome != "Y":
        msg = "Green gene {} with {} moi on panel {}".format(
            gene.name, gene.moi, gene.panel
        )

        return IncorrectMoiGene.from_gene(gene, msg)


def moi_check_chr_x(gene: GenePanelEntrySnapshot) -> Optional[IncorrectMoiGene]:
    """Check if MOI is chrX linked

    :param gene: GenePanelEntrySnapshot
    :return: IncorrectMoiGene if it's non chrX MOI
    """

    moi = gene.moi
    chromosome = get_chromosome(gene)

    if chromosome == "X" and moi not in [
        "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
        "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may "
        "cause disease (may be less severe, later onset than males)",
    ]:
        msg = "Green gene {} on X chromosome with {} moi on panel {}".format(
            gene.name, gene.moi, gene.panel
        )
        return IncorrectMoiGene.from_gene(gene, msg)


#
# MOI checks related


def multiple_moi_genes(
    genes: List[GenePanelEntrySnapshot],
) -> Generator[Tuple[GenePanelEntrySnapshot, Set[str]], None, None]:
    """Get genes which have different MOI on different panels

    Only values that aren't MONOALLELIC MOI will be added

    :param genes: GenePanelEntrySnapshot
    :return: Generator of tuple values of GenePanelEntrySnapshot and set of MOIs
    """
    unique_genes: Dict[str, Set[str]] = {}

    genes_with_moi = [g for g in genes if has_non_empty_moi(g.moi)]
    for gene in genes_with_moi:
        if gene.moi in MULTIPLE_MOI_EXCEPTIONS:
            continue
        key = gene.name
        if key not in unique_genes:
            unique_genes[key] = set()

        unique_genes[key].add(gene.moi)

    LOGGER.debug("Genes with non unique MOI: %s", len(unique_genes))

    for key, value in unique_genes.items():
        if len(value) > 1:
            yield unique_genes[key], value


def has_non_empty_moi(moi: str) -> bool:
    """Check if MOI is empty or unknown"""

    return bool(moi and moi != "Unknown")


def get_chromosome(gene: GenePanelEntrySnapshot) -> Optional[str]:
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
        extra_data={"gene_symbol": gene.name, "panel": str(gene.panel)},
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
            "HTTP error on request to OMIM.",
            exc_info=True,
            extra_data={"omim_id": omim_id},
        )
    except ValueError:
        LOGGER.error(
            "OMIM response not in JSON format.",
            exc_info=True,
            extra_data={"omim_id": omim_id},
        )
    except Exception as err:
        LOGGER.error("Unexpected error", exc_info=True, extra_data={"omim_id": omim_id})

    return moi

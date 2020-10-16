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

"""
HOW TO UPDATE GENE COLLECTION
-----------------------------

Gene collections in PanelApp can be updated uploading a json file containing the
information to be updated (see method `update_gene_collection` below).

This file should contains 3 lists of genes (see Gene Model below), the list are:

* insert: It will insert the gene as a new entry, the gene will be inactivated
  if there is no ensembl information. To be use when the gene_symbol is new.
* delete: It will inactivated genes (they are not really deleted as they can be
  used in old panels)
* update: It will update the gene using the gene_symbol as the search key for
  matching the record to update. the gene will be inactivated
  if there is no ensembl information. To be used when the gene_symbol is OK, but
  not the gene information.

The file should also contain an additional list for genes where a gene symbol
change is required:

* update_symbol: This field is a list of list, each item should be a list of
  with 2 items, first one a Gene Model, and second one th old symbol. This one
  is specially useful as it will perform the update of the gene information in
  each one of the panel entities. The gene will be inactivated
  if there is no ensembl information.


Gene Model:

    {
      "hgnc_id": "HGNC:16518",
      "biotype": "protein_coding",
      "ensembl_genes": {
        "GRch38": {
          "ensemble_version": "89",
          "ensemble_id": "ENSG00000187223"
        },
        "GRch37": {
          "ensemble_version": "82",
          "ensemble_id": "ENSG00000187223"
        }
      },
      "alias_name": null,
      "omim_gene": [
        "612612"
      ],
      "alias": [
        "LEP12"
      ],
      "gene_symbol": "LCE2D",
      "hgnc_date_symbol_changed": "2004-10-15",
      "hgnc_symbol": "LCE2D",
      "hgnc_release": "21/07/17",
      "gene_name": "late cornified envelope 2D",
      "location": "1:152663396-152664659"
    }


FULL example:

    {
      "update": [],
      "delete": [],
      "insert": [
          {
          "hgnc_id": "HGNC:16518",
          "biotype": "protein_coding",
          "ensembl_genes": {
            "GRch38": {
              "ensemble_version": "89",
              "ensemble_id": "ENSG00000187223"
            },
            "GRch37": {
              "ensemble_version": "82",
              "ensemble_id": "ENSG00000187223"
            }
          },
          "alias_name": null,
          "omim_gene": [
            "612612"
          ],
          "alias": [
            "LEP12"
          ],
          "gene_symbol": "LCE2D",
          "hgnc_date_symbol_changed": "2004-10-15",
          "hgnc_symbol": "LCE2D",
          "hgnc_release": "21/07/17",
          "gene_name": "late cornified envelope 2D",
          "location": "1:152663396-152664659"
        }],
       "update_symbol": [
       [{
          "hgnc_id": "HGNC:123232",
          "biotype": "protein_coding",
          "ensembl_genes": {
            "GRch38": {
              "ensemble_version": "89",
              "ensemble_id": "ENSG0000099999"
            },
            "GRch37": {
              "ensemble_version": "82",
              "ensemble_id": "ENSG0000099999"
            }
          },
          "alias_name": null,
          "omim_gene": [
            "999999"
          ],
          "alias": [
            "GENEX"
          ],
          "gene_symbol": "GENEX",
          "hgnc_date_symbol_changed": "2004-10-15",
          "hgnc_symbol": "GENEX",
          "hgnc_release": "21/07/17",
          "gene_name": "gene x",
          "location": "1:152663396-152664659"
        }, "GENEA"]
       ]
    }
"""


import json
import logging
from datetime import datetime

from django.db import (
    models,
    transaction,
)
from model_utils.models import TimeStampedModel

from accounts.models import (
    Reviewer,
    User,
)

from .gene import Gene
from .genepanelentrysnapshot import GenePanelEntrySnapshot
from .genepanelsnapshot import GenePanelSnapshot
from .region import Region
from .strs import STR

logger = logging.getLogger(__name__)


def update_gene_collection(results):
    with transaction.atomic():
        to_insert = results["insert"]
        to_update = results["update"]
        to_update_gene_symbol = results["update_symbol"]
        to_delete = results["delete"]

        for p in GenePanelSnapshot.objects.get_active(
            all=True, internal=True, superpanels=False
        ):
            p = p.increment_version()

        for record in to_insert:
            new_gene = Gene.from_dict(record)
            if not new_gene.ensembl_genes:
                new_gene.active = False
            new_gene.save()
            logger.debug("Inserted {} gene".format(record["gene_symbol"]))

        to_insert = None
        results["insert"] = None

        try:
            user = User.objects.get(username="GEL")
        except User.DoesNotExist:
            user = User.objects.create(username="GEL", first_name="Genomics England")
            Reviewer.objects.create(
                user=user,
                user_type="GEL",
                affiliation="Genomics England",
                workplace="Other",
                role="Other",
                group="Other",
            )

        genes_in_panels = GenePanelEntrySnapshot.objects.get_active()
        grouped_genes = {gp.gene_core.gene_symbol: [] for gp in genes_in_panels}
        for gene_in_panel in genes_in_panels:
            grouped_genes[gene_in_panel.gene_core.gene_symbol].append(gene_in_panel)

        strs_in_panels = STR.objects.get_active()
        grouped_strs = {
            gp.gene_core.gene_symbol: [] for gp in strs_in_panels if gp.gene_core
        }
        for str_in_panel in strs_in_panels:
            grouped_strs[str_in_panel.gene_core.gene_symbol].append(str_in_panel)

        regions_in_panels = Region.objects.get_active()
        grouped_regions = {
            gp.gene_core.gene_symbol: [] for gp in regions_in_panels if gp.gene_core
        }
        for region_in_panel in regions_in_panels:
            grouped_regions[region_in_panel.gene_core.gene_symbol].append(
                region_in_panel
            )

        for record in to_update:
            try:
                gene = Gene.objects.get(gene_symbol=record["gene_symbol"])
            except Gene.DoesNotExist:
                gene = Gene(gene_symbol=record["gene_symbol"])

            gene.gene_name = record.get("gene_name", None)
            gene.ensembl_genes = record.get("ensembl_genes", {})
            gene.omim_gene = record.get("omim_gene", [])
            gene.alias = record.get("alias", [])
            gene.biotype = record.get("biotype", "unknown")
            gene.alias_name = record.get("alias_name", [])
            gene.hgnc_symbol = record["hgnc_symbol"]
            gene.hgnc_date_symbol_changed = record.get("hgnc_date_symbol_changed", None)
            gene.hgnc_release = record.get("hgnc_release", None)
            gene.hgnc_id = record.get("hgnc_id", None)
            if not gene.ensembl_genes:
                gene.active = False

            gene.clean_import_dates(record)

            gene.save()

            for gene_entry in grouped_genes.get(record["gene_symbol"], []):
                gene_entry.gene_core = gene
                gene_entry.gene = gene.dict_tr()
                gene_entry.save()

            for str_entry in grouped_strs.get(record["gene_symbol"], []):
                str_entry.gene_core = gene
                str_entry.gene = gene.dict_tr()
                str_entry.save()

            for region_entry in grouped_regions.get(record["gene_symbol"], []):
                region_entry.gene_core = gene
                region_entry.gene = gene.dict_tr()
                region_entry.save()

            logger.debug("Updated {} gene".format(record["gene_symbol"]))

        grouped_genes = None
        to_update = None
        results["update"] = None

        for record in to_update_gene_symbol:
            active = True
            ensembl_genes = record[0].get("ensembl_genes", {})
            if not ensembl_genes:
                active = False

            # some dates are in the wrong format: %d-%m-%y, Django expects %Y-%m-%-d
            hgnc_date_symbol_changed = record[0].get("hgnc_date_symbol_changed", "")
            if hgnc_date_symbol_changed and len(hgnc_date_symbol_changed) == 8:
                record[0]["hgnc_date_symbol_changed"] = datetime.strptime(
                    hgnc_date_symbol_changed, "%d-%m-%y"
                )

            if (
                record[0].get("hgnc_release", "")
                and len(record[0].get("hgnc_release", "")) == 8
            ):
                record[0]["hgnc_release"] = datetime.strptime(
                    record[0]["hgnc_release"], "%d-%m-%y"
                )

            try:
                new_gene = Gene.objects.get(gene_symbol=record[0]["gene_symbol"])
            except Gene.DoesNotExist:
                new_gene = Gene()

            # check if record has ensembl genes data if it doesn't and gene has
            # it - keep it as it is and mark gene as active
            if new_gene.pk:
                if not new_gene.ensembl_genes:
                    new_gene.active = active
                    new_gene.ensembl_genes = ensembl_genes
                else:
                    if not ensembl_genes:
                        new_gene.active = True
            else:
                new_gene.active = active
                new_gene.ensembl_genes = ensembl_genes

            new_gene.gene_symbol = record[0]["gene_symbol"]
            new_gene.gene_name = record[0].get("gene_name", None)
            new_gene.omim_gene = record[0].get("omim_gene", [])
            new_gene.alias = record[0].get("alias", [])
            new_gene.biotype = record[0].get("biotype", "unknown")
            new_gene.alias_name = record[0].get("alias_name", [])
            new_gene.hgnc_symbol = record[0]["hgnc_symbol"]
            new_gene.hgnc_date_symbol_changed = record[0].get(
                "hgnc_date_symbol_changed", None
            )
            new_gene.hgnc_release = record[0].get("hgnc_release", None)
            new_gene.hgnc_id = record[0].get("hgnc_id", None)

            new_gene.clean_import_dates(record[0])
            new_gene.save()

            for gene_entry in GenePanelEntrySnapshot.objects.get_active().filter(
                gene_core__gene_symbol=record[1]
            ):
                panel = gene_entry.panel
                panel.update_gene(user, record[1], {"gene": new_gene})

            for str_entry in STR.objects.get_active().filter(
                gene_core__gene_symbol=record[1]
            ):
                panel = str_entry.panel
                panel.update_str(user, str_entry.name, {"gene": new_gene})

            for region_entry in Region.objects.get_active().filter(
                gene_core__gene_symbol=record[1]
            ):
                panel = region_entry.panel
                panel.update_region(user, region_entry.name, {"gene": new_gene})

            try:
                d = Gene.objects.get(gene_symbol=record[1])
                d.active = False
                d.save()
                logger.debug(
                    "Updated {} gene. Renamed to {}".format(
                        record[1], record[0]["gene_symbol"]
                    )
                )
            except Gene.DoesNotExist:
                logger.debug(
                    "Created {} gene. Old gene {} didn't exist".format(
                        record[0]["gene_symbol"], record[1]
                    )
                )

        for record in to_delete:
            gene_in_panels = GenePanelEntrySnapshot.objects.get_active().filter(
                gene_core__gene_symbol=record
            )
            if gene_in_panels.count() > 0:
                distinct_panels = gene_in_panels.distinct().values_list(
                    "panel__panel__name", flat=True
                )
                logger.warning(
                    "Deleted {} gene, this one is still used in {}".format(
                        record, distinct_panels
                    )
                )

            strs_in_panels = STR.objects.get_active().filter(
                gene_core__gene_symbol=record
            )
            if strs_in_panels.count() > 0:
                distinct_panels = strs_in_panels.distinct().values_list(
                    "panel__panel__name", flat=True
                )
                logger.warning(
                    "Deleted {} gene, this one is still used in {}".format(
                        record, distinct_panels
                    )
                )

            regions_in_panels = Region.objects.get_active().filter(
                gene_core__gene_symbol=record
            )
            if regions_in_panels.count() > 0:
                distinct_panels = regions_in_panels.distinct().values_list(
                    "panel__panel__name", flat=True
                )
                logger.warning(
                    "Deleted {} gene, this one is still used in {}".format(
                        record, distinct_panels
                    )
                )

            try:
                old_gene = Gene.objects.get(gene_symbol=record)
                old_gene.active = False
                old_gene.save()
                logger.debug("Deleted {} gene".format(record))
            except Gene.DoesNotExist:
                logger.debug("Didn't delete {} gene - doesn't exist".format(record))

        duplicated_genes = get_duplicated_genes_in_panels()
        if duplicated_genes:
            logger.info("duplicated genes:")
            for g in duplicated_genes:
                logger.info(g)
                print(g)


def get_duplicated_genes_in_panels():
    duplicated_genes = []
    items = GenePanelSnapshot.objects.get_active_annotated(True)
    for item in items:
        dups = item.current_genes_duplicates
        if dups:
            duplicated_genes.append((item.pk, item.panel.name, dups))
    return duplicated_genes


class UploadedGeneList(TimeStampedModel):
    imported = models.BooleanField(default=False)
    gene_list = models.FileField(upload_to="genes", max_length=255)

    def create_genes(self):
        with open(self.gene_list.path) as file:
            logger.info("Started importing list of genes")
            results = json.load(file)
            update_gene_collection(results)

            self.imported = True
            self.save()

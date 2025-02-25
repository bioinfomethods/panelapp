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
import csv
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.http import HttpResponse


from .genepanel import GenePanel
from panels.utils import remove_non_ascii
from webservices.utils import make_null, convert_moi, convert_gel_status
import panelapp


class HistoricalSnapshot(models.Model):
    panel = models.ForeignKey(GenePanel, on_delete=models.PROTECT)
    major_version = models.IntegerField(default=0, db_index=True)
    minor_version = models.IntegerField(default=0, db_index=True)
    reason = models.TextField(null=True)
    schema_version = models.CharField(max_length=100)  # JSON schema version
    data = JSONField()
    signed_off_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return "{} v{}.{}".format(self.panel.name, self.major_version, self.minor_version)

    def to_tsv(self):
        data = self.data
        panel_name = self.panel.name

        response = HttpResponse(content_type="text/tab-separated-values")
        panel_name = remove_non_ascii(panel_name, replacemenet="_")
        response["Content-Disposition"] = (
            'attachment; filename="' + panel_name + '.tsv"'
        )

        writer = csv.writer(response, delimiter="\t")

        writer.writerow(
            (
                "Entity Name",
                "Entity type",
                "Gene Symbol",
                "Sources(; separated)",
                "Level4",
                "Level3",
                "Level2",
                "Model_Of_Inheritance",
                "Phenotypes",
                "Omim",
                "Orphanet",
                "HPO",
                "Publications",
                "Description",
                "Flagged",
                "GEL_Status",
                "UserRatings_Green_amber_red",
                "version",
                "ready",
                "Mode of pathogenicity",
                "EnsemblId(GRch37)",
                "EnsemblId(GRch38)",
                "HGNC",
                "Position Chromosome",
                "Position GRCh37 Start",
                "Position GRCh37 End",
                "Position GRCh38 Start",
                "Position GRCh38 End",
                "STR Repeated Sequence",
                "STR Normal Repeats",
                "STR Pathogenic Repeats",
                "Region Haploinsufficiency Score",
                "Region Triplosensitivity Score",
                "Region Required Overlap Percentage",
                "Region Variant Type",
                "Region Verbose Name",
            )
        )

        for gene in data["genes"]:
            writer.writerow(
                (
                    gene.get("entity_name", ""),
                    gene.get("entity_type", ""),
                    gene.get("entity_name", ""),
                    ";".join([ev for ev in gene["evidence"] if ev]),
                    panel_name,
                    data.get("panel", {}).get("disease_sub_group", ""),
                    data.get("panel", {}).get("disease_group", ""),
                    gene.get("mode_of_inheritance", ""),
                    ";".join(map(remove_non_ascii, gene["phenotypes"]))
                    if gene.get("phenotypes") else "",
                    ";".join(map(remove_non_ascii, gene["gene_data"]["omim_gene"]))
                    if gene.get("gene_data").get("omim_gene") else "",
                    "",
                    "",
                    ";".join(map(remove_non_ascii, gene["publications"]))
                    if gene.get("publications") else "",
                    "",
                    "",
                    gene.get("confidence_level", ""),
                    "",
                    "{}.{}".format(self.major_version, self.minor_version),
                    "",
                    gene.get("mode_of_pathogenicity", ""),
                    gene.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch38", {}).get("90", {}).get("ensembl_id", "")
                    if gene.get("gene_data") is not None else "",
                    gene.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch37", {}).get("82", {}).get("ensembl_id", "")
                    if gene.get("gene_data") is not None else "",
                    gene.get("gene_data", {}).get("hgnc_id", ""),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            )

        for str in data["strs"]:
            writer.writerow(
                (
                    str.get("entity_name", ""),
                    str.get("entity_type", ""),
                    str["gene_data"].get("gene_symbol", "") if str.get("gene_data") else "",
                    ";".join([ev for ev in str["evidence"] if ev])
                    if str.get("evidence") else "",
                    panel_name,
                    data.get("panel", {}).get("disease_sub_group", ""),
                    data.get("panel", {}).get("disease_group", ""),
                    str.get("mode_of_inheritance", ""),
                    ";".join(map(remove_non_ascii, str["phenotypes"]))
                    if str.get('phenotypes') else "",
                    ";".join(map(remove_non_ascii, str["gene_data"].get("omim_gene", "")))
                    if str.get("gene_data") else "",
                    "",
                    "",
                    ";".join(map(remove_non_ascii, str["publications"]))
                    if str.get("publications") else "",
                    "",
                    "",
                    str.get("confidence_level", ""),
                    "",
                    "{}.{}".format(self.major_version, self.minor_version),
                    "",
                    "",
                    str.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch38", {}).get("90", {}).get("ensembl_id", "")
                    if str.get("gene_data") is not None else "",
                    str.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch37", {}).get("82", {}).get("ensembl_id", "")
                    if str.get("gene_data") is not None else "",
                    str.get("gene_data", {}).get("hgnc_id", ""),
                    str.get("chromosome", ""),
                    str["grch37_coordinates"][0] if str.get("grch37_coordinates") else "",
                    str["grch37_coordinates"][1] if str.get("grch37_coordinates") else "",
                    str["grch38_coordinates"][0] if str.get("grch38_coordinates") else "",
                    str["grch38_coordinates"][1] if str.get("grch38_coordinates") else "",
                    str.get("repeated_sequence", ""),
                    str.get("normal_repeats", ""),
                    str.get("pathogenic_repeats", ""),
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            )

        for region in data["regions"]:
            writer.writerow(
                (
                    region.get("entity_name", ""),
                    region.get("entity_type", ""),
                    region["gene_data"].get("gene_symbol", "") if region.get("gene_data") else "",
                    ";".join([ev for ev in region["evidence"] if ev]) if region.get("evidence") else "",
                    panel_name,
                    data.get("panel", {}).get("disease_sub_group", ""),
                    data.get("panel", {}).get("disease_group", ""),
                    region.get("mode_of_inheritance", ""),
                    ";".join(map(remove_non_ascii, region["phenotypes"]))
                    if region.get("phenotypes") else "",
                    region["gene_data"].get("omim_gene", "") if region.get("gene_data") is not None else "",
                    "",
                    "",
                    ";".join(map(remove_non_ascii, region["publications"]))
                    if region.get("publications") else "",
                    "",
                    "",
                    region.get("confidence_level", ""),
                    "",
                    "{}.{}".format(self.major_version, self.minor_version),
                    "",
                    "",
                    region.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch38", {}).get("90", {}).get("ensembl_id", "")
                    if region.get("gene_data") is not None else "",
                    region.get("gene_data", {}).get("ensembl_genes", {})
                        .get("GRch37", {}).get("82", {}).get("ensembl_id", "")
                    if region.get("gene_data") is not None else "",
                    region.get("gene_data", {}).get("hgnc_id", "") if region.get("gene_data") is not None else "",
                    region.get("chromosome", ""),
                    region["grch37_coordinates"][0] if region.get("grch37_coordinates") else "",
                    region["grch37_coordinates"][1] if region.get("grch37_coordinates") else "",
                    region["grch38_coordinates"][0] if region.get("grch38_coordinates") else "",
                    region["grch38_coordinates"][1] if region.get("grch38_coordinates") else "",
                    "",
                    "",
                    "",
                    region.get("haploinsufficiency_score", ""),
                    region.get("triplosensitivity_score", ""),
                    region.get("required_overlap_percentage", ""),
                    region.get("type_of_variants", ""),
                    region.get("verbose_name", ""),
                )
            )
        return response

    @classmethod
    def import_panel(cls, panel, comment=None):
        from api.v1.serializers import PanelSerializer

        json = PanelSerializer(panel, include_entities=True)

        instance = cls()
        instance.panel = panel.panel
        instance.major_version = panel.major_version
        instance.minor_version = panel.minor_version
        instance.reason = comment
        instance.schema_version = panelapp.__version__
        instance.data = json.data

        instance.save()
        return instance

    @staticmethod
    def ensemble(entity):
        ensemble = None
        if entity.get("gene_data") and entity["gene_data"].get("ensemble_genes"):
            ensemble = {
                entity["gene_data"]["ensembl_genes"]["GRch38"]["90"]["ensembl_id"],
                entity["gene_data"]["ensembl_genes"]["GRch37"]["82"]["ensembl_id"],
            }
            ensemble = list(ensemble)
        return ensemble

    def to_api_0(self):
        data = self.data

        result = {
            "result": {
                "Genes": [],
                "STRs": [],
                "Regions": [],
                "SpecificDiseaseName": data["name"],
                "version": data["version"],
                "Created": data["version_created"],
                "DiseaseGroup": data["disease_group"],
                "DiseaseSubGroup": data["disease_sub_group"],
                "Status": data["status"],
                "Signed Off": self.signed_off_date,
            }
        }
        for gene in data["genes"]:

            result["result"]["Genes"].append(
                {
                    "GeneSymbol": gene["gene_data"]["gene_symbol"],
                    "EnsembleGeneIds": self.ensemble(gene),
                    "ModeOfInheritance": make_null(
                        convert_moi(gene["mode_of_inheritance"])
                    ),
                    "Penetrance": make_null(gene["penetrance"]),
                    "Publications": make_null(gene["publications"]),
                    "Phenotypes": make_null(gene["phenotypes"]),
                    "ModeOfPathogenicity": make_null(gene["mode_of_pathogenicity"]),
                    "LevelOfConfidence": convert_gel_status(
                        int(gene["confidence_level"])
                    ),
                    "Evidences": gene["evidence"],
                }
            )

        for str in data["strs"]:
            result["result"]["STRs"].append(
                {
                    "Name": str["entity_name"],
                    "Chromosome": str["chromosome"],
                    "GRCh37Coordinates": str["grch37_coordinates"],
                    "GRCh38Coordinates": str["grch38_coordinates"],
                    "RepeatedSequence": str["repeated_sequence"],
                    "NormalRepeats": str["normal_repeats"],
                    "PathogenicRepeats": str["pathogenic_repeats"],
                    "GeneSymbol": str["gene_data"]["gene_symbol"]
                    if str["gene_data"]
                    else None,
                    "EnsembleGeneIds": self.ensemble(str),
                    "ModeOfInheritance": make_null(
                        convert_moi(str["mode_of_inheritance"])
                    ),
                    "Penetrance": make_null(str["penetrance"]),
                    "Publications": make_null(str["publications"]),
                    "Phenotypes": make_null(str["phenotypes"]),
                    "LevelOfConfidence": convert_gel_status(
                        int(str["confidence_level"])
                    ),
                    "Evidences": str["evidence"],
                }
            )

        for region in data["regions"]:
            result["result"]["Regions"].append(
                {
                    "Name": region["entity_name"],
                    "VerboseName": region["verbose_name"],
                    "Chromosome": region["chromosome"],
                    "GRCh37Coordinates": region["grch37_coordinates"],
                    "GRCh38Coordinates": region["grch38_coordinates"],
                    "HaploinsufficiencyScore": region["haploinsufficiency_score"],
                    "TriplosensitivityScore": region["triplosensitivity_score"],
                    "RequiredOverlapPercentage": region["required_overlap_percentage"],
                    "GeneSymbol": region["gene_data"]["gene_symbol"]
                    if region["gene_data"]
                    else None,
                    "EnsembleGeneIds": self.ensemble(region),
                    "ModeOfInheritance": make_null(
                        convert_moi(region["mode_of_inheritance"])
                    ),
                    "Penetrance": make_null(region["penetrance"]),
                    "TypeOfVariants": region["type_of_variants"],
                    "Publications": make_null(region["publications"]),
                    "Phenotypes": make_null(region["phenotypes"]),
                    "LevelOfConfidence": convert_gel_status(
                        int(region["confidence_level"])
                    ),
                    "Evidences": region["evidence"],
                }
            )

        return result

    def to_api_1(self, exclude_entities=False):
        if exclude_entities:
            self.data.pop('genes', None)
            self.data.pop('regions', None)
            self.data.pop('strs', None)
        self.data['signed_off'] = self.signed_off_date
        return self.data

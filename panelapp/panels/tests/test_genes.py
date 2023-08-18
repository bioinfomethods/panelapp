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
import json
import os
from datetime import (
    date,
    datetime,
)

from django.test.client import RequestFactory
from django.urls import reverse_lazy
from faker import Factory

from accounts.models import (
    Reviewer,
    User,
)
from accounts.tests.setup import LoginGELUser
from panels.forms import PanelGeneForm
from panels.models import (
    STR,
    Comment,
    Evaluation,
    Evidence,
    Gene,
    GenePanel,
    GenePanelEntrySnapshot,
    GenePanelSnapshot,
    HistoricalSnapshot,
    Region,
    Tag,
)
from panels.models.import_tools import update_gene_collection
from panels.tests.factories import (
    CommentFactory,
    EvidenceFactory,
    GeneFactory,
    GenePanelEntrySnapshotFactory,
    GenePanelSnapshotFactory,
    Level4TitleFactory,
    RegionFactory,
    STRFactory,
    TagFactory,
)

fake = Factory.create()


class GeneTest(LoginGELUser):
    "Test gene import"

    def test_import_gene(self):
        """
        Test Gene import.
        """

        file_path = os.path.join(os.path.dirname(__file__), "test_import.json")
        test_gene_file = os.path.abspath(file_path)

        # Create genes to update
        update_symbol = []
        update = []
        with open(test_gene_file) as f:
            results = json.load(f)
            for r in results["update"]:
                update.append(GeneFactory(gene_symbol=r["gene_symbol"]).gene_symbol)
            for r in results["update_symbol"]:
                update_symbol.append(GeneFactory(gene_symbol=r[1]).gene_symbol)

        with open(test_gene_file) as f:
            url = reverse_lazy("panels:upload_genes")
            self.client.post(url, {"gene_list": f})

        for us in update_symbol:
            self.assertFalse(Gene.objects.get(gene_symbol=us).active)
        for u in update:
            gene = Gene.objects.get(gene_symbol=u)
            if gene.ensembl_genes:
                self.assertTrue(gene.active)
            else:
                self.assertFalse(gene.active)

    def test_gene_from_json(self):
        gene_dict_file = os.path.join(os.path.dirname(__file__), "gene_dict.json")
        with open(gene_dict_file) as f:
            dictionary = json.load(f)
            g = Gene.from_dict(dictionary=dictionary)
            dictionary["hgnc_date_symbol_changed"] = date(2004, 10, 15)
            dictionary["hgnc_release"] = datetime(2017, 7, 21, 0, 0)
            self.assertEqual(dictionary, g.dict_tr())

    def test_download_genes(self):
        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)

        res = self.client.get(reverse_lazy("panels:download_genes"))
        self.assertEqual(res.status_code, 200)

    def test_download_genes_multiple_ensembl_genes(self):
        gps = GenePanelSnapshotFactory(level4title=Level4TitleFactory(name="Test"))
        gene_core = GeneFactory(
            gene_symbol="ABCA1",
            gene_name="ABCA1",
            ensembl_genes={
                "GRch37": {
                    "82": {
                        "location": "9:107543283-107690518",
                        "ensembl_id": "ENSG00000165029",
                    },
                    "107": {
                        "location": "22:50961997-50964890",
                        "ensembl_id": "ENSG00000284194",
                    },
                },
                "GRch38": {
                    "90": {
                        "location": "9:104781002-104928237",
                        "ensembl_id": "ENSG00000165029",
                    },
                    "107": {
                        "location": "22:50523568-50526461",
                        "ensembl_id": "ENSG00000284194",
                    },
                },
            },
        )
        GenePanelEntrySnapshotFactory(
            panel=gps,
            gene_core=gene_core,
            evidence=[EvidenceFactory(name="Other")],
            tags=[TagFactory(name="test")],
            phenotypes=["one", "two"],
        )

        res = self.client.get(reverse_lazy("panels:download_genes"))

        assert res.status_code == 200

        content = b"".join(res.streaming_content).decode("utf-8")

        [row] = list(csv.DictReader(content.splitlines(), delimiter="\t"))

        assert row == {
            "Symbol": "ABCA1",
            "Panel Id": str(gps.panel.id),
            "Panel Name": "Test",
            "Panel Version": "0.0",
            "Panel Status": "INTERNAL",
            "List": "grey",
            "Sources": "Other",
            "Mode of inheritance": "Unknown",
            "Mode of pathogenicity": "Other",
            "Tags": "test",
            "HGNC": "",
            "Biotype": "",
            "Phenotypes": "one;two",
            "EnsemblId(GRch37)": "ENSG00000165029",
            "EnsemblId(GRch38)": "ENSG00000165029",
            "GeneLocation((GRch37)": "9:107543283-107690518",
            "GeneLocation((GRch38)": "9:104781002-104928237",
            "Panel Types": "",
            "Super Panel Id": "-",
            "Super Panel Name": "-",
            "Super Panel Version": "-",
        }

    def test_list_genes(self):
        GenePanelEntrySnapshotFactory.create_batch(3)
        r = self.client.get(reverse_lazy("panels:entities_list"))
        self.assertEqual(r.status_code, 200)

    def test_gene_not_ready(self):
        gpes = GenePanelEntrySnapshotFactory()
        url = reverse_lazy(
            "panels:mark_entity_as_not_ready",
            args=(gpes.panel.panel.pk, "gene", gpes.gene.get("gene_symbol")),
        )
        r = self.client.post(url, {})
        self.assertEqual(r.status_code, 302)

    def test_update_gene_collection(self):
        gene_to_update = GeneFactory()
        gene_to_delete = GeneFactory()
        gene_to_update_symbol = GeneFactory()

        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene_to_update, panel=gps)
        STRFactory.create_batch(2, panel=gps)  # random STRs
        STRFactory.create(gene_core=gene_to_update, panel=gps)
        RegionFactory.create_batch(2, panel=gps)  # random STRs
        RegionFactory.create(gene_core=gene_to_update, panel=gps)

        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)  # random genes
        STRFactory.create_batch(2, panel=gps)  # random STRs
        GenePanelEntrySnapshotFactory.create(gene_core=gene_to_update_symbol, panel=gps)
        STRFactory.create(gene_core=gene_to_update_symbol, panel=gps)
        RegionFactory.create_batch(2, panel=gps)  # random STRs
        RegionFactory.create(gene_core=gene_to_update_symbol, panel=gps)

        to_insert = [
            Gene(gene_symbol="A", ensembl_genes={"inserted": True}).dict_tr(),
            Gene(gene_symbol="B", ensembl_genes={"inserted": True}).dict_tr(),
        ]

        to_update = [
            Gene(
                gene_symbol=gene_to_update.gene_symbol, ensembl_genes={"updated": True}
            ).dict_tr()
        ]

        to_update_symbol = [
            (
                Gene(gene_symbol="C", ensembl_genes={"updated": True}).dict_tr(),
                gene_to_update_symbol.gene_symbol,
            )
        ]

        to_delete = [gene_to_delete.gene_symbol]

        migration = {
            "insert": to_insert,
            "update": to_update,
            "delete": to_delete,
            "update_symbol": to_update_symbol,
        }

        update_gene_collection(migration)

        self.assertTrue(
            GenePanelEntrySnapshot.objects.get_active()
            .get(gene_core__gene_symbol=gene_to_update.gene_symbol)
            .gene.get("ensembl_genes")["updated"]
        )

        self.assertTrue(
            STR.objects.get_active()
            .get(gene_core__gene_symbol=gene_to_update.gene_symbol)
            .gene.get("ensembl_genes")["updated"]
        )

        self.assertTrue(
            Region.objects.get_active()
            .get(gene_core__gene_symbol=gene_to_update.gene_symbol)
            .gene.get("ensembl_genes")["updated"]
        )

        updated_not_updated = [
            gpes.gene["ensembl_genes"]
            for gpes in GenePanelEntrySnapshot.objects.filter(
                gene_core__gene_symbol=gene_to_update.gene_symbol
            )
        ]
        not_updated = HistoricalSnapshot.objects.all()[1].data["genes"][0]["gene_data"][
            "ensembl_genes"
        ]
        self.assertNotEqual(updated_not_updated[0], not_updated)

        updated_not_updated = [
            str_item.gene["ensembl_genes"]
            for str_item in STR.objects.filter(
                gene_core__gene_symbol=gene_to_update.gene_symbol
            )
        ]
        not_updated = HistoricalSnapshot.objects.all()[1].data["strs"][0]["gene_data"][
            "ensembl_genes"
        ]

        self.assertNotEqual(updated_not_updated[0], not_updated)

        updated_not_updated = [
            region_item.gene["ensembl_genes"]
            for region_item in Region.objects.filter(
                gene_core__gene_symbol=gene_to_update.gene_symbol
            )
        ]
        not_updated = HistoricalSnapshot.objects.all()[1].data["regions"][0][
            "gene_data"
        ]["ensembl_genes"]

        self.assertNotEqual(updated_not_updated[0], not_updated)

        self.assertFalse(
            Gene.objects.get(gene_symbol=gene_to_update_symbol.gene_symbol).active
        )
        self.assertFalse(
            Gene.objects.get(gene_symbol=gene_to_delete.gene_symbol).active
        )
        self.assertTrue(Gene.objects.get(gene_symbol="A").active)

        self.assertTrue(
            GenePanelEntrySnapshot.objects.get(gene_core__gene_symbol="C").gene.get(
                "ensembl_genes"
            )["updated"]
        )

        self.assertTrue(
            STR.objects.get(gene_core__gene_symbol="C").gene.get("ensembl_genes")[
                "updated"
            ]
        )

        self.assertTrue(
            Region.objects.get(gene_core__gene_symbol="C").gene.get("ensembl_genes")[
                "updated"
            ]
        )

    def test_get_panels_for_a_gene(self):
        gene = GeneFactory()

        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=gps)

        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=gps)

        gps3 = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps3)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=gps3)

        gps4 = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps4)  # random genes

        assert (
            GenePanelEntrySnapshot.objects.get_gene_panels(gene.gene_symbol).count()
            == 3
        )

        url = reverse_lazy(
            "panels:entity_detail", kwargs={"entity_name": gene.gene_symbol}
        )
        res = self.client.get(url)
        assert len(res.context_data["entries"]) == 3

    def test_get_internal_panels_for_a_gene(self):
        gene = GeneFactory()

        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=gps)

        gps2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.internal)
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps2)  # random genes
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=gps2)

        gps3 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(2, panel=gps3)  # random genes

        self.assertEqual(
            GenePanelEntrySnapshot.objects.get_gene_panels(gene.gene_symbol).count(), 2
        )
        self.assertEqual(
            GenePanelSnapshot.objects.get_gene_panels(gene.gene_symbol).count(), 1
        )
        self.assertEqual(
            GenePanelSnapshot.objects.get_gene_panels(
                gene.gene_symbol, all=True, internal=True
            ).count(),
            2,
        )

        url = reverse_lazy(
            "panels:entity_detail", kwargs={"entity_name": gene.gene_symbol}
        )
        res = self.client.get(url)
        self.assertEqual(len(res.context_data["entries"]), 2)


class CopyToPanelsTest(LoginGELUser):
    def setUp(self):
        self.gene = GeneFactory()
        self.gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        self.gps2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        self.user = User.objects.create(username="GEL", first_name="Genomics England")
        Reviewer.objects.create(
            user=self.user,
            user_type="GEL",
            affiliation="Genomics England",
            workplace="Other",
            role="Other",
            group="Other",
        )
        self.request = RequestFactory()
        self.request.user = self.user

    def test_copy_gene_to_panel(self):
        form_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene.gene_symbol,
            "source": ["Expert Review"],
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
            "comments": "new comment",
        }
        form = PanelGeneForm(form_data, panel=self.gps, request=self.request)
        assert form.is_valid()
        form.save_gene()
        copied_gene = self.gps2.get_gene(self.gene.gene_symbol)
        assert copied_gene
        assert copied_gene.comments.count() == 1
        assert copied_gene.evaluation.count() == 1

    def test_copy_existing_gene_to_panel(self):
        gene = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)
        form_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene.gene_symbol,
            "source": ["Expert Review", "Expert Review"],
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
        }
        form = PanelGeneForm(
            form_data,
            panel=self.gps,
            request=self.request,
            instance=gene,
            initial=gene.get_form_initial(),
        )
        assert form.is_valid()
        form.save_gene()
        copied_gene = self.gps2.get_gene(self.gene.gene_symbol)
        assert copied_gene

    def test_copy_additional_info(self):
        """Copy addition data as well as the gene
        - comments
        - evaluations and their comments
        - evidences

        Make sure IDs are different.
        """

        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)

        comment = Comment.objects.create(user=self.user, comment="Comment")
        gpes.comments.add(comment)
        gpes.evaluation.first().comments.add(comment)

        form_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene.gene_symbol,
            "source": list(gpes.evidence.values_list("name", flat=True)),
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
            "tags": list(gpes.tags.values_list("pk", flat=True)),
        }

        form = PanelGeneForm(
            form_data,
            panel=self.gps,
            request=self.request,
            instance=gpes,
            initial=gpes.get_form_initial(),
        )
        assert form.is_valid()
        form.save_gene()
        assert self.gps2.has_gene(self.gene.gene_symbol)

        gpes2 = self.gps2.get_gene(self.gene.gene_symbol)

        self.assertEqual(gpes2.evidence.count(), gpes.evidence.count())
        self.assertNotEqual(
            set(gpes2.evidence.values_list("pk", flat=True)),
            set(gpes.evidence.values_list("pk", flat=True)),
        )

        gpes_pks = set(gpes.evaluation.values_list("pk", flat=True))
        gpes2_pks = set(gpes2.evaluation.values_list("pk", flat=True))
        self.assertEqual(gpes2.evaluation.count(), gpes.evidence.count())
        self.assertNotEqual(gpes2_pks, gpes_pks)

        gpes_comments = Comment.objects.filter(evaluation__pk__in=gpes_pks)
        gpes2_comments = Comment.objects.filter(evaluation__pk__in=gpes2_pks)
        self.assertEqual(gpes_comments.count(), gpes2_comments.count())
        self.assertEqual(gpes2_comments.count(), 1)
        self.assertEqual(gpes_comments.first().comment, gpes2_comments.first().comment)

        self.assertEqual(gpes2.comments.count(), gpes.comments.count())
        self.assertNotEqual(gpes2.comments.first().pk, comment.pk)

        self.assertEqual(gpes2.tags.count(), gpes.tags.count())
        # Same tag used in multiple panels
        self.assertEqual(gpes2.tags.first().pk, gpes.tags.first().pk)

    def test_non_standard_source(self):
        """Make sure non standard sources aren't wiped out"""

        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)
        gpes.tags.all().delete()

        evidence = Evidence(
            name="something-123", rating=5, legacy_type=Reviewer.TYPES.GEL
        )
        evidence.save()
        gpes.evidence.add(evidence)

        version = self.gps.version

        comment = Comment.objects.create(user=self.user, comment="Comment")
        gpes.comments.add(comment)
        gpes.evaluation.first().comments.add(comment)

        sources = list(gpes.evidence.values_list("name", flat=True))

        form_data = gpes.get_form_initial()
        form_data["gene"] = self.gene.gene_symbol
        form_data["gene_name"] = self.gene.gene_name
        form_data["source"] = form_data["source"]

        form = PanelGeneForm(
            form_data,
            panel=self.gps,
            request=self.request,
            instance=gpes,
            initial=gpes.get_form_initial(),
        )
        assert form.is_valid()
        entity = form.save_gene()

        assert entity.evidence.count() == len(sources)
        assert entity.panel.version == version

    def test_edit_multiple_exper_reviews(self):
        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)

        for evidence_name in ["Expert Review Green", "Expert Review Amber"]:
            evidence = Evidence(
                name=evidence_name, rating=5, legacy_type=Reviewer.TYPES.GEL
            )
            evidence.save()
            gpes.evidence.add(evidence)

        form_data = gpes.get_form_initial()
        form_data["gene"] = self.gene.gene_symbol
        form_data["gene_name"] = self.gene.gene_name
        form_data["source"] = form_data["source"]

        form = PanelGeneForm(
            form_data,
            panel=self.gps,
            request=self.request,
            instance=gpes,
            initial=gpes.get_form_initial(),
        )
        assert not form.is_valid()
        assert form.errors == {
            "source": ["Entity contains multiple Expert Review sources"]
        }

    def test_copy_original_panel(self):
        """Copy original panel in the evaluations"""

        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)

        comment_text = "Comment123"
        comment = Comment.objects.create(user=self.user, comment=comment_text)
        ev = Evaluation.objects.create(
            user=self.user,
            rating=Evaluation.RATINGS.AMBER,
        )
        ev.comments.add(comment)
        gpes.evaluation.add(ev)

        entity_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene,
            "sources": gpes.evidence.values_list("name", flat=True),
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
            "tags": gpes.tags.all(),
        }
        gpes.copy_to_panels([self.gps2], self.user, entity_data, copy_data=True)
        copied_gene = self.gps2.get_gene(self.gene.gene_symbol)
        copied_evaluation = copied_gene.evaluation.filter(
            comments__comment=comment_text
        ).first()
        assert copied_gene
        assert copied_evaluation.original_panel

        url = reverse_lazy(
            "panels:evaluation",
            kwargs={
                "pk": self.gps2.pk,
                "entity_type": "gene",
                "entity_name": gpes.gene.get("gene_symbol"),
            },
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f"<strong>Copied from panel: </strong>")

    def test_copy_multiple_panels_original_panel(self):
        """Copy original panel in the evaluations"""

        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)

        gps3 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        comment_text = "Comment123"
        comment = Comment.objects.create(user=self.user, comment=comment_text)
        ev = Evaluation.objects.create(
            user=self.user,
            rating=Evaluation.RATINGS.AMBER,
        )
        ev.comments.add(comment)
        gpes.evaluation.add(ev)

        original_panel_version = str(gpes.panel)

        entity_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene,
            "sources": gpes.evidence.values_list("name", flat=True),
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
            "tags": gpes.tags.all(),
        }
        gpes.copy_to_panels([self.gps2, gps3], self.user, entity_data, copy_data=True)
        copied_gene = self.gps2.get_gene(self.gene.gene_symbol)
        copied_evaluation = copied_gene.evaluation.filter(
            comments__comment=comment_text
        ).first()
        assert copied_gene
        assert copied_evaluation.original_panel.count(original_panel_version) == 1

        copied_gene_2 = gps3.get_gene(self.gene.gene_symbol)
        copied_evaluation_2 = copied_gene_2.evaluation.filter(
            comments__comment=comment_text
        ).first()
        assert copied_gene_2
        assert copied_evaluation_2.original_panel.count(original_panel_version) == 1

    def test_copy_multiple_origins(self):
        """Copy original panel in the evaluations"""

        gpes = GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps)

        comment_text = "Comment123"
        comment = Comment.objects.create(user=self.user, comment=comment_text)
        ev = Evaluation.objects.create(
            user=self.user,
            rating=Evaluation.RATINGS.AMBER,
            original_panel="initial source v1.1",
        )
        ev.comments.add(comment)
        gpes.evaluation.add(ev)

        entity_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene,
            "sources": gpes.evidence.values_list("name", flat=True),
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
            "tags": gpes.tags.all(),
        }
        gpes.copy_to_panels([self.gps2], self.user, entity_data, copy_data=True)

        url = reverse_lazy(
            "panels:evaluation",
            kwargs={
                "pk": self.gps2.pk,
                "entity_type": "gene",
                "entity_name": gpes.gene.get("gene_symbol"),
            },
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f"{str(gpes.panel)}, initial source v1.1")

    def test_copy_gene_to_panel_with_same_gene(self):
        GenePanelEntrySnapshotFactory.create(gene_core=self.gene, panel=self.gps2)

        form_data = {
            "additional_panels": [self.gps2.pk],
            "gene": self.gene.gene_symbol,
            "source": ["Expert Review", "Expert Review"],
            "moi": "Unknown",
            "panel": self.gps,
            "gene_name": self.gene.gene_symbol,
        }

        form = PanelGeneForm(form_data, panel=self.gps, request=self.request)
        assert not form.is_valid()
        assert self.gps2.has_gene(self.gene.gene_symbol)

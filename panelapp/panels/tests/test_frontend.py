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
from datetime import timedelta
from random import randint
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import Group
from faker import Factory
from accounts.tests.setup import LoginReviewerUser
from accounts.tests.setup import LoginGELUser
from accounts.models import Reviewer
from panels.tests.factories import GenePanelEntrySnapshotFactory
from panels.tests.factories import GenePanelSnapshotFactory
from panels.tests.factories import GeneFactory
from panels.models import GenePanel
from panels.models import Evidence
from panels.models import Evaluation
from panels.models import GenePanelEntrySnapshot
from panels.models import Activity


fake = Factory.create()


class TestActivities(LoginReviewerUser):
    def test_activities(self):
        GenePanelEntrySnapshotFactory.create_batch(4)
        res = self.client.get(reverse_lazy("panels:activity"))
        self.assertEqual(res.status_code, 200)

    def test_adding_gene_create_activity(self):
        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()

        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        req = self.client.post(url, gene_data)

        self.assertEqual(Activity.objects.count(), 1)

    def test_adding_gene_save_source(self):
        gps = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()

        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        self.client.post(url, gene_data)
        gpes = gps.panel.active_panel.get_gene(gene.gene_symbol)
        self.assertTrue(
            gene_data["source"]
            in gpes.evaluation.get(user=self.verified_user).comments.first().comment
        )

    def test_filter_by_panel_id(self):
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()

        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        req = self.client.post(url, gene_data)

        activities_url = reverse("panels:activity") + "?panel=" + str(gps.panel.pk)
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

        activities_url = reverse("panels:activity") + "?panel=" + str(gps.panel.pk + 1)
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_panel_version(self):
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        req = self.client.post(url, gene_data)

        activities_url = (
            reverse("panels:activity") + "?version=0.0&panel=" + str(gps.panel.pk)
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

        activities_url = (
            reverse("panels:activity") + "?version=0.1&panel=" + str(gps.panel.pk)
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_panel_entity(self):
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        self.client.post(url, gene_data)

        activities_url = (
            reverse("panels:activity")
            + "?entity="
            + gene.gene_symbol
            + "&version=0.0&panel="
            + str(gps.panel.pk)
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

        activities_url = (
            reverse("panels:activity")
            + "?entity=ABCD&version=0.0&panel="
            + str(gps.panel.pk)
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_panel_date_range(self):
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        self.client.post(url, gene_data)

        now = timezone.now()
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        activities_url = (
            reverse("panels:activity")
            + "?date_from="
            + date_from
            + "&date_to="
            + date_to
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

        now = timezone.now() - timedelta(days=30)
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        activities_url = (
            reverse("panels:activity")
            + "?date_from="
            + date_from
            + "&date_to="
            + date_to
        )
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_user_type(self):
        """Test filtering activities by user type (GEL, REVIEWER, EXTERNAL)"""
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        # Activity created by verified_user (REVIEWER type)
        self.client.post(url, gene_data)

        # Filter for REVIEWER user type - should find the activity
        activities_url = reverse("panels:activity") + "?user_type=REVIEWER"
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

        # Filter for GEL user type - should find nothing
        activities_url = reverse("panels:activity") + "?user_type=GEL"
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_training_group(self):
        """Test filtering activities by training group membership"""
        # Ensure Training group exists
        training_group, _ = Group.objects.get_or_create(name="Training")

        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        # Activity created by verified_user
        self.client.post(url, gene_data)

        # Filter for training group - should find nothing (user not in group yet)
        activities_url = reverse("panels:activity") + "?training_group=on"
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

        # Add verified_user to training group
        self.verified_user.groups.add(training_group)

        # Filter for training group - should find the activity now
        # (filter is based on current user group membership)
        activities_url = reverse("panels:activity") + "?training_group=on"
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 1)

    def test_filter_by_event_type_gene_addition(self):
        """Test filtering activities by gene addition event type"""
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        # Adding gene creates activity with "was added" text
        self.client.post(url, gene_data)

        # Filter for gene_addition event type - should find the activity
        activities_url = reverse("panels:activity") + "?event_type=gene_addition"
        res = self.client.get(activities_url)
        self.assertGreater(len(res.context["activities"]), 0)

        # Filter for rating_change event type - should find nothing (we only added a gene)
        activities_url = reverse("panels:activity") + "?event_type=rating_change"
        res = self.client.get(activities_url)
        self.assertEqual(len(res.context["activities"]), 0)

    def test_filter_by_event_type_multiple(self):
        """Test filtering activities with multiple event types selected"""
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        # Adding gene creates activity with "was added" text
        self.client.post(url, gene_data)

        # Filter for both gene_addition and rating_change - should find gene addition
        activities_url = reverse("panels:activity") + "?event_type=gene_addition&event_type=rating_change"
        res = self.client.get(activities_url)
        self.assertGreater(len(res.context["activities"]), 0)

    def test_filter_by_flagged_genes(self):
        """Test filtering activities for flagged genes only"""
        gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        gene = GeneFactory()
        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        # Add gene - when added by REVIEWER, it gets flagged=True
        self.client.post(url, gene_data)

        # Filter for flagged genes - should find the activity
        activities_url = reverse("panels:activity") + "?flagged_genes=on"
        res = self.client.get(activities_url)
        # The gene should be flagged since it was added by a REVIEWER (not GEL)
        self.assertGreater(len(res.context["activities"]), 0)


class TestExportActivities(LoginGELUser):
    def test_export_activities_functionality(self):
        gps = GenePanelSnapshotFactory()

        GenePanelEntrySnapshotFactory.create_batch(4, panel=gps)
        gene = GeneFactory()

        url = reverse_lazy(
            "panels:add_entity", kwargs={"pk": gps.panel.pk, "entity_type": "gene"}
        )
        gene_data = {
            "gene": gene.pk,
            "source": Evidence.OTHER_SOURCES[0],
            "phenotypes": "{};{};{}".format(*fake.sentences(nb=3)),
            "rating": Evaluation.RATINGS.AMBER,
            "moi": [x for x in Evaluation.MODES_OF_INHERITANCE][randint(1, 12)][0],
            "mode_of_pathogenicity": [x for x in Evaluation.MODES_OF_PATHOGENICITY][
                randint(1, 2)
            ][0],
            "penetrance": GenePanelEntrySnapshot.PENETRANCE.Incomplete,
        }
        self.client.post(url, gene_data)

        activities_url = (
            reverse("panels:activity") + "?format=csv&panel=" + str(gps.panel.pk)
        )
        res = self.client.get(activities_url)
        self.assertTrue(gps.panel.name.encode() in res.content)

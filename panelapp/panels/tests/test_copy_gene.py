"""Tests for copying a gene to multiple panels."""

from django.urls import reverse_lazy
from accounts.tests.setup import LoginGELUser, LoginReviewerUser
from panels.models import GenePanel
from panels.tests.factories import (
    GeneFactory,
    GenePanelSnapshotFactory,
    GenePanelEntrySnapshotFactory,
    EvaluationFactory,
)
from panels.forms import CopyGeneForm


class CopyGeneTest(LoginGELUser):
    """Test gene copying functionality."""

    def test_copy_gene_form_valid(self):
        """Test that form validates correctly with valid data."""
        gene = GeneFactory()

        # Create source panel with gene
        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=source_panel)

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel without gene
        target_panel = GenePanelSnapshotFactory()

        form = CopyGeneForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())

    def test_copy_gene_form_requires_target_panels(self):
        """Test that form requires at least one target panel."""
        gene = GeneFactory()
        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=source_panel)

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        form = CopyGeneForm(
            data={
                "target_panels": [],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("target_panels", form.errors)

    def test_copy_gene_form_requires_reviews(self):
        """Test that form requires at least one review to be selected."""
        gene = GeneFactory()
        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=source_panel)

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel without gene
        target_panel = GenePanelSnapshotFactory()

        form = CopyGeneForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [],  # No reviews selected
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reviews_to_copy", form.errors)

    def test_copy_gene_to_panels(self):
        """Test copying a gene to multiple panels."""
        gene = GeneFactory()

        # Create source panel with gene
        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Test phenotype"],
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panels without gene
        target_panel_1 = GenePanelSnapshotFactory()
        target_panel_2 = GenePanelSnapshotFactory()

        # Submit form
        form = CopyGeneForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_gene_to_panels()

        # Verify gene was copied to both target panels
        target_1_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        target_2_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel

        self.assertTrue(target_1_updated.has_gene(gene.gene_symbol))
        self.assertTrue(target_2_updated.has_gene(gene.gene_symbol))

        # Verify metadata was copied
        copied_entry_1 = target_1_updated.get_gene(gene.gene_symbol)
        self.assertEqual(copied_entry_1.moi, source_entry.moi)
        self.assertEqual(copied_entry_1.phenotypes, source_entry.phenotypes)

    def test_copy_gene_view_requires_auth(self):
        """Test that copy gene view requires authentication."""
        gene = GeneFactory()
        panel = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=panel)

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )

        self.client.logout()
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 403)

    def test_copy_gene_view_get(self):
        """Test GET request to copy gene view."""
        gene = GeneFactory()
        panel = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=panel)

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["gene_symbol"], gene.gene_symbol)
        self.assertEqual(response.context["source_panel"].pk, panel.pk)

    def test_copy_gene_view_post_success(self):
        """Test successful POST to copy gene view."""
        gene = GeneFactory()

        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=source_panel)

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        target_panel = GenePanelSnapshotFactory()

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": source_panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )
        response = self.client.post(
            url,
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
        )

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Verify gene was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        self.assertTrue(updated_target.has_gene(gene.gene_symbol))

    def test_copy_gene_with_reviews(self):
        """Test copying a gene with selected reviews."""
        gene = GeneFactory()

        # Create source panel with gene and reviews
        source_panel = GenePanelSnapshotFactory()
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
        )

        # Add evaluations
        eval1 = EvaluationFactory(user=self.gel_user)
        eval2 = EvaluationFactory()
        source_entry.evaluation.add(eval1, eval2)

        # Create target panel
        target_panel = GenePanelSnapshotFactory()

        # Submit form with selected reviews
        form = CopyGeneForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],  # Only copy first review
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_gene_to_panels()

        # Verify gene was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_gene = updated_target.get_gene(gene.gene_symbol)

        # Verify only the selected review was copied
        self.assertEqual(copied_gene.evaluation.count(), 1)
        self.assertEqual(copied_gene.evaluation.first().user.pk, eval1.user.pk)


class CopyGeneReviewerTest(LoginReviewerUser):
    """Test that non-GEL reviewers cannot copy genes."""

    def test_reviewer_cannot_access_copy_gene_view(self):
        """Test that non-GEL reviewers cannot access the copy gene view."""
        gene = GeneFactory()
        panel = GenePanelSnapshotFactory()
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=panel)

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )
        response = self.client.get(url)

        # Should be forbidden for non-GEL users
        self.assertEqual(response.status_code, 403)

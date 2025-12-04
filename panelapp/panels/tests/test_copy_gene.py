"""Tests for copying a gene to multiple panels."""

from django.urls import reverse_lazy
from accounts.tests.setup import LoginGELUser, LoginReviewerUser
from panels.models import GenePanel
from panels.tests.factories import (
    GeneFactory,
    GenePanelSnapshotFactory,
    GenePanelEntrySnapshotFactory,
    EvaluationFactory,
    CommentFactory,
)
from panels.forms import CopyGeneForm


class CopyGeneTest(LoginGELUser):
    """Test gene copying functionality."""

    def test_copy_gene_form_valid(self):
        """Test that form validates correctly with valid data."""
        gene = GeneFactory()

        # Create source panel with gene
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel without gene
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

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
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel
        )

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
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel without gene
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

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
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
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
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

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
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
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
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
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

    def test_copy_gene_view_with_user_comments(self):
        """Test GET request to copy gene view when logged-in user has comments on reviews.

        This tests the fix for a bug where the template would fail with NoReverseMatch
        when trying to render edit/delete comment links because entity_name wasn't
        passed to the included entity_evaluation.html template.
        """
        gene = GeneFactory()
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        gene_entry = GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=panel)

        # Create an evaluation from the logged-in user with a comment
        evaluation = EvaluationFactory(user=self.gel_user)
        gene_entry.evaluation.add(evaluation)

        # Add a comment to the evaluation
        comment = CommentFactory(user=self.gel_user)
        evaluation.comments.add(comment)

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )
        response = self.client.get(url)

        # Should render successfully without NoReverseMatch error
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        # Verify the review and comment are shown in the response
        self.assertContains(response, comment.comment)

    def test_copy_gene_view_post_success(self):
        """Test successful POST to copy gene view."""
        gene = GeneFactory()

        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

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
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
        )

        # Add evaluations
        eval1 = EvaluationFactory(user=self.gel_user)
        eval2 = EvaluationFactory()
        source_entry.evaluation.add(eval1, eval2)

        # Create target panel
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

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

    def test_copy_to_panel_with_gene_no_conflicts(self):
        """Test copying to panel that already has the gene but no review conflicts."""
        gene = GeneFactory()

        # Create source panel with gene and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Source phenotype"],
            evaluation=(None,),
        )
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel with the SAME gene but different metadata and NO reviews
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=target_panel,
            moi="BIALLELIC",  # Different MOI
            phenotypes=["Target phenotype"],  # Different phenotype
            evaluation=(None,),
        )

        # Copy gene
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
        form.copy_gene_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_gene = updated_target.get_gene(gene.gene_symbol)

        # Gene metadata should NOT be changed (kept from target)
        self.assertEqual(copied_gene.moi, "BIALLELIC")
        self.assertEqual(copied_gene.phenotypes, ["Target phenotype"])

        # Review should be copied
        self.assertEqual(copied_gene.evaluation.count(), 1)
        self.assertEqual(copied_gene.evaluation.first().user.pk, eval1.user.pk)

    def test_copy_to_panel_with_gene_some_conflicts(self):
        """Test copying when some reviewers already reviewed the gene in target."""
        from accounts.tests.factories import UserFactory

        gene = GeneFactory()

        # Create source panel with gene and two reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel, evaluation=(None,)
        )

        user1 = self.gel_user
        user2 = UserFactory()

        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_entry.evaluation.add(eval1, eval2)

        # Create target panel with same gene and one existing review (from user1)
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=user1)
        target_entry.evaluation.add(existing_eval)

        # Try to copy both reviews
        form = CopyGeneForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_gene_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_gene = updated_target.get_gene(gene.gene_symbol)

        # Should have 2 reviews: existing one + new one from user2 (user1 skipped)
        self.assertEqual(copied_gene.evaluation.count(), 2)
        evaluator_ids = set(copied_gene.evaluation.values_list("user_id", flat=True))
        self.assertIn(user1.pk, evaluator_ids)
        self.assertIn(user2.pk, evaluator_ids)

    def test_copy_to_panel_with_gene_all_conflicts(self):
        """Test copying when all reviewers already reviewed the gene in target."""
        gene = GeneFactory()

        # Create source panel with gene and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel, evaluation=(None,)
        )
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create target panel with same gene and same reviewer
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=self.gel_user)
        target_entry.evaluation.add(existing_eval)

        # Try to copy the review
        form = CopyGeneForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(self.gel_user.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_gene_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_gene = updated_target.get_gene(gene.gene_symbol)

        # Should still have only 1 review (existing one, none added)
        self.assertEqual(copied_gene.evaluation.count(), 1)

    def test_copy_to_mixed_targets(self):
        """Test copying to multiple panels where some have gene and some don't."""
        from accounts.tests.factories import UserFactory

        gene = GeneFactory()

        # Create source panel with gene and reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
            moi="MONOALLELIC",
            evaluation=(None,),
        )
        user1 = self.gel_user
        user2 = UserFactory()
        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_entry.evaluation.add(eval1, eval2)

        # Target 1: doesn't have gene
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Target 2: has gene with one existing review
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_entry_2 = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=target_panel_2,
            moi="BIALLELIC",
            evaluation=(None,),
        )
        existing_eval = EvaluationFactory(user=user1)
        target_entry_2.evaluation.add(existing_eval)

        # Copy to both
        form = CopyGeneForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_gene_to_panels()

        # Target 1: should have new gene with both reviews
        updated_target_1 = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        self.assertTrue(updated_target_1.has_gene(gene.gene_symbol))
        gene_1 = updated_target_1.get_gene(gene.gene_symbol)
        self.assertEqual(gene_1.moi, "MONOALLELIC")  # Copied from source
        self.assertEqual(gene_1.evaluation.count(), 2)

        # Target 2: should have same metadata, 2 reviews (existing + user2)
        updated_target_2 = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel
        gene_2 = updated_target_2.get_gene(gene.gene_symbol)
        self.assertEqual(gene_2.moi, "BIALLELIC")  # Unchanged from target
        self.assertEqual(gene_2.evaluation.count(), 2)

    def test_gel_user_can_copy_to_internal_panel(self):
        """Test that GEL users can copy genes to internal panels."""
        gene = GeneFactory()

        # Create source panel (public) with gene
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene,
            panel=source_panel,
            moi="MONOALLELIC",
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create INTERNAL target panel
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.internal)

        # Submit form - should succeed for GEL user
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
        form.copy_gene_to_panels()

        # Verify gene was copied to internal panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        self.assertTrue(updated_target.has_gene(gene.gene_symbol))

    def test_form_queryset_includes_internal_for_gel(self):
        """Test that form queryset includes internal panels for GEL users."""
        gene = GeneFactory()
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_entry = GenePanelEntrySnapshotFactory.create(
            gene_core=gene, panel=source_panel
        )
        eval1 = EvaluationFactory(user=self.gel_user)
        source_entry.evaluation.add(eval1)

        # Create both public and internal panels
        public_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        internal_panel = GenePanelSnapshotFactory(
            panel__status=GenePanel.STATUS.internal
        )

        form = CopyGeneForm(
            data={},
            gene_symbol=gene.gene_symbol,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        queryset = form.fields["target_panels"].queryset
        queryset_pks = list(queryset.values_list("pk", flat=True))

        # GEL user should see both public and internal panels
        self.assertIn(public_panel.pk, queryset_pks)
        self.assertIn(internal_panel.pk, queryset_pks)


class CopyGeneReviewerTest(LoginReviewerUser):
    """Test that non-GEL reviewers cannot copy genes."""

    def test_reviewer_cannot_access_copy_gene_view(self):
        """Test that non-GEL reviewers cannot access the copy gene view."""
        gene = GeneFactory()
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        GenePanelEntrySnapshotFactory.create(gene_core=gene, panel=panel)

        url = reverse_lazy(
            "panels:copy_gene_from_panel",
            kwargs={"pk": panel.panel.pk, "gene_symbol": gene.gene_symbol},
        )
        response = self.client.get(url)

        # Should be forbidden for non-GEL users
        self.assertEqual(response.status_code, 403)

"""Tests for copying a Region to multiple panels."""

from django.urls import reverse_lazy
from accounts.tests.setup import LoginGELUser, LoginReviewerUser
from panels.models import GenePanel
from panels.tests.factories import (
    GenePanelSnapshotFactory,
    RegionFactory,
    EvaluationFactory,
    CommentFactory,
)
from panels.forms import CopyRegionForm


class CopyRegionTest(LoginGELUser):
    """Test Region copying functionality."""

    def test_copy_region_form_valid(self):
        """Test that form validates correctly with valid data."""
        # Create source panel with Region
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        # Create target panel without Region
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())

    def test_copy_region_form_requires_target_panels(self):
        """Test that form requires at least one target panel."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        form = CopyRegionForm(
            data={
                "target_panels": [],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("target_panels", form.errors)

    def test_copy_region_form_requires_reviews(self):
        """Test that form requires at least one review to be selected."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        # Create target panel without Region
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [],  # No reviews selected
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reviews_to_copy", form.errors)

    def test_copy_region_to_panels(self):
        """Test copying a Region to multiple panels."""
        # Create source panel with Region
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Test phenotype"],
            evaluation=(None,),
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        # Create target panels without Region
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Submit form
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Verify Region was copied to both target panels
        target_1_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        target_2_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel

        self.assertTrue(target_1_updated.has_region(source_region.name))
        self.assertTrue(target_2_updated.has_region(source_region.name))

        # Verify metadata was copied
        copied_region_1 = target_1_updated.get_region(source_region.name)
        self.assertEqual(copied_region_1.moi, source_region.moi)
        self.assertEqual(copied_region_1.phenotypes, source_region.phenotypes)

    def test_copy_region_view_requires_auth(self):
        """Test that copy Region view requires authentication."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        region_entry = RegionFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_region_from_panel",
            kwargs={"pk": panel.panel.pk, "region_name": region_entry.name},
        )

        self.client.logout()
        response = self.client.get(url)

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_copy_region_view_get(self):
        """Test GET request to copy Region view."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        region_entry = RegionFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_region_from_panel",
            kwargs={"pk": panel.panel.pk, "region_name": region_entry.name},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["region_name"], region_entry.name)
        self.assertEqual(response.context["source_panel"].pk, panel.pk)

    def test_copy_region_view_with_user_comments(self):
        """Test GET request to copy Region view when logged-in user has comments on reviews.

        This tests that the template renders correctly when trying to render
        edit/delete comment links because entity_name is passed to the
        included entity_evaluation.html template.
        """
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        region_entry = RegionFactory(panel=panel, evaluation=(None,))

        # Create an evaluation from the logged-in user with a comment
        evaluation = EvaluationFactory(user=self.gel_user)
        region_entry.evaluation.add(evaluation)

        # Add a comment to the evaluation
        comment = CommentFactory(user=self.gel_user)
        evaluation.comments.add(comment)

        url = reverse_lazy(
            "panels:copy_region_from_panel",
            kwargs={"pk": panel.panel.pk, "region_name": region_entry.name},
        )
        response = self.client.get(url)

        # Should render successfully without NoReverseMatch error
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        # Verify the review and comment are shown in the response
        self.assertContains(response, comment.comment)

    def test_copy_region_view_post_success(self):
        """Test successful POST to copy Region view."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        url = reverse_lazy(
            "panels:copy_region_from_panel",
            kwargs={"pk": source_panel.panel.pk, "region_name": source_region.name},
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

        # Verify Region was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        self.assertTrue(updated_target.has_region(source_region.name))

    def test_copy_region_with_reviews(self):
        """Test copying a Region with selected reviews."""
        # Create source panel with Region and reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        # Add evaluations
        eval1 = EvaluationFactory(user=self.gel_user)
        eval2 = EvaluationFactory()
        source_region.evaluation.add(eval1, eval2)

        # Create target panel
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Submit form with selected reviews
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],  # Only copy first review
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Verify Region was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_region = updated_target.get_region(source_region.name)

        # Verify only the selected review was copied
        self.assertEqual(copied_region.evaluation.count(), 1)
        self.assertEqual(copied_region.evaluation.first().user.pk, eval1.user.pk)

    def test_copy_to_panel_with_region_no_conflicts(self):
        """Test copying to panel that already has the Region but no review conflicts."""
        # Create source panel with Region and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Source phenotype"],
            evaluation=(None,),
        )
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        # Create target panel with the SAME Region (same name) but different metadata and NO reviews
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        RegionFactory(
            name=source_region.name,
            panel=target_panel,
            moi="BIALLELIC",  # Different MOI
            phenotypes=["Target phenotype"],  # Different phenotype
            evaluation=(None,),
        )

        # Copy Region
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_region = updated_target.get_region(source_region.name)

        # Region metadata should NOT be changed (kept from target)
        self.assertEqual(copied_region.moi, "BIALLELIC")
        self.assertEqual(copied_region.phenotypes, ["Target phenotype"])

        # Review should be copied
        self.assertEqual(copied_region.evaluation.count(), 1)
        self.assertEqual(copied_region.evaluation.first().user.pk, eval1.user.pk)

    def test_copy_to_panel_with_region_some_conflicts(self):
        """Test copying when some reviewers already reviewed the Region in target."""
        from accounts.tests.factories import UserFactory

        # Create source panel with Region and two reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))

        user1 = self.gel_user
        user2 = UserFactory()

        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_region.evaluation.add(eval1, eval2)

        # Create target panel with same Region and one existing review (from user1)
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_region = RegionFactory(
            name=source_region.name, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=user1)
        target_region.evaluation.add(existing_eval)

        # Try to copy both reviews
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_region = updated_target.get_region(source_region.name)

        # Should have 2 reviews: existing one + new one from user2 (user1 skipped)
        self.assertEqual(copied_region.evaluation.count(), 2)
        evaluator_ids = set(copied_region.evaluation.values_list("user_id", flat=True))
        self.assertIn(user1.pk, evaluator_ids)
        self.assertIn(user2.pk, evaluator_ids)

    def test_copy_to_panel_with_region_all_conflicts(self):
        """Test copying when all reviewers already reviewed the Region in target."""
        # Create source panel with Region and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(panel=source_panel, evaluation=(None,))
        eval1 = EvaluationFactory(user=self.gel_user)
        source_region.evaluation.add(eval1)

        # Create target panel with same Region and same reviewer
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_region = RegionFactory(
            name=source_region.name, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=self.gel_user)
        target_region.evaluation.add(existing_eval)

        # Try to copy the review
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(self.gel_user.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_region = updated_target.get_region(source_region.name)

        # Should still have only 1 review (existing one, none added)
        self.assertEqual(copied_region.evaluation.count(), 1)

    def test_copy_to_mixed_targets(self):
        """Test copying to multiple panels where some have Region and some don't."""
        from accounts.tests.factories import UserFactory

        # Create source panel with Region and reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_region = RegionFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            evaluation=(None,),
        )
        user1 = self.gel_user
        user2 = UserFactory()
        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_region.evaluation.add(eval1, eval2)

        # Target 1: doesn't have Region
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Target 2: has Region with one existing review
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_region_2 = RegionFactory(
            name=source_region.name,
            panel=target_panel_2,
            moi="BIALLELIC",
            evaluation=(None,),
        )
        existing_eval = EvaluationFactory(user=user1)
        target_region_2.evaluation.add(existing_eval)

        # Copy to both
        form = CopyRegionForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            region_name=source_region.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_region_to_panels()

        # Target 1: should have new Region with both reviews
        updated_target_1 = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        self.assertTrue(updated_target_1.has_region(source_region.name))
        region_1 = updated_target_1.get_region(source_region.name)
        self.assertEqual(region_1.moi, "MONOALLELIC")  # Copied from source
        self.assertEqual(region_1.evaluation.count(), 2)

        # Target 2: should have same metadata, 2 reviews (existing + user2)
        updated_target_2 = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel
        region_2 = updated_target_2.get_region(source_region.name)
        self.assertEqual(region_2.moi, "BIALLELIC")  # Unchanged from target
        self.assertEqual(region_2.evaluation.count(), 2)


class CopyRegionReviewerTest(LoginReviewerUser):
    """Test that non-GEL reviewers cannot copy Regions."""

    def test_reviewer_cannot_access_copy_region_view(self):
        """Test that non-GEL reviewers cannot access the copy Region view."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        region_entry = RegionFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_region_from_panel",
            kwargs={"pk": panel.panel.pk, "region_name": region_entry.name},
        )
        response = self.client.get(url)

        # Should be forbidden for non-GEL users
        self.assertEqual(response.status_code, 403)

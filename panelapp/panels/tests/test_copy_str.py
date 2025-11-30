"""Tests for copying an STR to multiple panels."""

from django.urls import reverse_lazy
from accounts.tests.setup import LoginGELUser, LoginReviewerUser
from panels.models import GenePanel
from panels.tests.factories import (
    GenePanelSnapshotFactory,
    STRFactory,
    EvaluationFactory,
    CommentFactory,
)
from panels.forms import CopySTRForm


class CopySTRTest(LoginGELUser):
    """Test STR copying functionality."""

    def test_copy_str_form_valid(self):
        """Test that form validates correctly with valid data."""
        # Create source panel with STR
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        # Create target panel without STR
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())

    def test_copy_str_form_requires_target_panels(self):
        """Test that form requires at least one target panel."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        form = CopySTRForm(
            data={
                "target_panels": [],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("target_panels", form.errors)

    def test_copy_str_form_requires_reviews(self):
        """Test that form requires at least one review to be selected."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        # Create target panel without STR
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [],  # No reviews selected
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("reviews_to_copy", form.errors)

    def test_copy_str_to_panels(self):
        """Test copying an STR to multiple panels."""
        # Create source panel with STR
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Test phenotype"],
            evaluation=(None,),
        )

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        # Create target panels without STR
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Submit form
        form = CopySTRForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Verify STR was copied to both target panels
        target_1_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        target_2_updated = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel

        self.assertTrue(target_1_updated.has_str(source_str.name))
        self.assertTrue(target_2_updated.has_str(source_str.name))

        # Verify metadata was copied
        copied_str_1 = target_1_updated.get_str(source_str.name)
        self.assertEqual(copied_str_1.moi, source_str.moi)
        self.assertEqual(copied_str_1.phenotypes, source_str.phenotypes)

    def test_copy_str_view_requires_auth(self):
        """Test that copy STR view requires authentication."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        str_entry = STRFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_str_from_panel",
            kwargs={"pk": panel.panel.pk, "str_name": str_entry.name},
        )

        self.client.logout()
        response = self.client.get(url)

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_copy_str_view_get(self):
        """Test GET request to copy STR view."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        str_entry = STRFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_str_from_panel",
            kwargs={"pk": panel.panel.pk, "str_name": str_entry.name},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["str_name"], str_entry.name)
        self.assertEqual(response.context["source_panel"].pk, panel.pk)

    def test_copy_str_view_with_user_comments(self):
        """Test GET request to copy STR view when logged-in user has comments on reviews.

        This tests that the template renders correctly when trying to render
        edit/delete comment links because entity_name is passed to the
        included entity_evaluation.html template.
        """
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        str_entry = STRFactory(panel=panel, evaluation=(None,))

        # Create an evaluation from the logged-in user with a comment
        evaluation = EvaluationFactory(user=self.gel_user)
        str_entry.evaluation.add(evaluation)

        # Add a comment to the evaluation
        comment = CommentFactory(user=self.gel_user)
        evaluation.comments.add(comment)

        url = reverse_lazy(
            "panels:copy_str_from_panel",
            kwargs={"pk": panel.panel.pk, "str_name": str_entry.name},
        )
        response = self.client.get(url)

        # Should render successfully without NoReverseMatch error
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        # Verify the review and comment are shown in the response
        self.assertContains(response, comment.comment)

    def test_copy_str_view_post_success(self):
        """Test successful POST to copy STR view."""
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        url = reverse_lazy(
            "panels:copy_str_from_panel",
            kwargs={"pk": source_panel.panel.pk, "str_name": source_str.name},
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

        # Verify STR was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        self.assertTrue(updated_target.has_str(source_str.name))

    def test_copy_str_with_reviews(self):
        """Test copying an STR with selected reviews."""
        # Create source panel with STR and reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluations
        eval1 = EvaluationFactory(user=self.gel_user)
        eval2 = EvaluationFactory()
        source_str.evaluation.add(eval1, eval2)

        # Create target panel
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Submit form with selected reviews
        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],  # Only copy first review
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Verify STR was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_str = updated_target.get_str(source_str.name)

        # Verify only the selected review was copied
        self.assertEqual(copied_str.evaluation.count(), 1)
        self.assertEqual(copied_str.evaluation.first().user.pk, eval1.user.pk)

    def test_copy_to_panel_with_str_no_conflicts(self):
        """Test copying to panel that already has the STR but no review conflicts."""
        # Create source panel with STR and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            phenotypes=["Source phenotype"],
            evaluation=(None,),
        )
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        # Create target panel with the SAME STR (same name) but different metadata and NO reviews
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        STRFactory(
            name=source_str.name,
            panel=target_panel,
            moi="BIALLELIC",  # Different MOI
            phenotypes=["Target phenotype"],  # Different phenotype
            evaluation=(None,),
        )

        # Copy STR
        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_str = updated_target.get_str(source_str.name)

        # STR metadata should NOT be changed (kept from target)
        self.assertEqual(copied_str.moi, "BIALLELIC")
        self.assertEqual(copied_str.phenotypes, ["Target phenotype"])

        # Review should be copied
        self.assertEqual(copied_str.evaluation.count(), 1)
        self.assertEqual(copied_str.evaluation.first().user.pk, eval1.user.pk)

    def test_copy_to_panel_with_str_some_conflicts(self):
        """Test copying when some reviewers already reviewed the STR in target."""
        from accounts.tests.factories import UserFactory

        # Create source panel with STR and two reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        user1 = self.gel_user
        user2 = UserFactory()

        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_str.evaluation.add(eval1, eval2)

        # Create target panel with same STR and one existing review (from user1)
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_str = STRFactory(
            name=source_str.name, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=user1)
        target_str.evaluation.add(existing_eval)

        # Try to copy both reviews
        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_str = updated_target.get_str(source_str.name)

        # Should have 2 reviews: existing one + new one from user2 (user1 skipped)
        self.assertEqual(copied_str.evaluation.count(), 2)
        evaluator_ids = set(copied_str.evaluation.values_list("user_id", flat=True))
        self.assertIn(user1.pk, evaluator_ids)
        self.assertIn(user2.pk, evaluator_ids)

    def test_copy_to_panel_with_str_all_conflicts(self):
        """Test copying when all reviewers already reviewed the STR in target."""
        # Create source panel with STR and review
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))
        eval1 = EvaluationFactory(user=self.gel_user)
        source_str.evaluation.add(eval1)

        # Create target panel with same STR and same reviewer
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_str = STRFactory(
            name=source_str.name, panel=target_panel, evaluation=(None,)
        )
        existing_eval = EvaluationFactory(user=self.gel_user)
        target_str.evaluation.add(existing_eval)

        # Try to copy the review
        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(self.gel_user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Get updated target panel
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_str = updated_target.get_str(source_str.name)

        # Should still have only 1 review (existing one, none added)
        self.assertEqual(copied_str.evaluation.count(), 1)

    def test_copy_to_mixed_targets(self):
        """Test copying to multiple panels where some have STR and some don't."""
        from accounts.tests.factories import UserFactory

        # Create source panel with STR and reviews
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(
            panel=source_panel,
            moi="MONOALLELIC",
            evaluation=(None,),
        )
        user1 = self.gel_user
        user2 = UserFactory()
        eval1 = EvaluationFactory(user=user1)
        eval2 = EvaluationFactory(user=user2)
        source_str.evaluation.add(eval1, eval2)

        # Target 1: doesn't have STR
        target_panel_1 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Target 2: has STR with one existing review
        target_panel_2 = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        target_str_2 = STRFactory(
            name=source_str.name,
            panel=target_panel_2,
            moi="BIALLELIC",
            evaluation=(None,),
        )
        existing_eval = EvaluationFactory(user=user1)
        target_str_2.evaluation.add(existing_eval)

        # Copy to both
        form = CopySTRForm(
            data={
                "target_panels": [target_panel_1.pk, target_panel_2.pk],
                "reviews_to_copy": [str(user1.pk), str(user2.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )
        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Target 1: should have new STR with both reviews
        updated_target_1 = GenePanel.objects.get_panel(
            pk=str(target_panel_1.panel.pk)
        ).active_panel
        self.assertTrue(updated_target_1.has_str(source_str.name))
        str_1 = updated_target_1.get_str(source_str.name)
        self.assertEqual(str_1.moi, "MONOALLELIC")  # Copied from source
        self.assertEqual(str_1.evaluation.count(), 2)

        # Target 2: should have same metadata, 2 reviews (existing + user2)
        updated_target_2 = GenePanel.objects.get_panel(
            pk=str(target_panel_2.panel.pk)
        ).active_panel
        str_2 = updated_target_2.get_str(source_str.name)
        self.assertEqual(str_2.moi, "BIALLELIC")  # Unchanged from target
        self.assertEqual(str_2.evaluation.count(), 2)

    def test_copy_str_clinically_relevant(self):
        """Test that clinically_relevant field is copied with evaluations."""
        # Create source panel with STR
        source_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        source_str = STRFactory(panel=source_panel, evaluation=(None,))

        # Add evaluation with clinically_relevant set
        eval1 = EvaluationFactory(user=self.gel_user, clinically_relevant=True)
        source_str.evaluation.add(eval1)

        # Create target panel
        target_panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Submit form
        form = CopySTRForm(
            data={
                "target_panels": [target_panel.pk],
                "reviews_to_copy": [str(eval1.user.pk)],
            },
            str_name=source_str.name,
            user=self.gel_user,
            source_panel_id=source_panel.panel.pk,
        )

        self.assertTrue(form.is_valid())
        form.copy_str_to_panels()

        # Verify STR was copied
        updated_target = GenePanel.objects.get_panel(
            pk=str(target_panel.panel.pk)
        ).active_panel
        copied_str = updated_target.get_str(source_str.name)

        # Verify clinically_relevant was copied
        copied_eval = copied_str.evaluation.first()
        self.assertTrue(copied_eval.clinically_relevant)


class CopySTRReviewerTest(LoginReviewerUser):
    """Test that non-GEL reviewers cannot copy STRs."""

    def test_reviewer_cannot_access_copy_str_view(self):
        """Test that non-GEL reviewers cannot access the copy STR view."""
        panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        str_entry = STRFactory(panel=panel)

        url = reverse_lazy(
            "panels:copy_str_from_panel",
            kwargs={"pk": panel.panel.pk, "str_name": str_entry.name},
        )
        response = self.client.get(url)

        # Should be forbidden for non-GEL users
        self.assertEqual(response.status_code, 403)

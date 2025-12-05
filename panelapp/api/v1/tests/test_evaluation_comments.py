from django.test import TestCase
from django.urls import reverse_lazy
from panels.models import GenePanel
from panels.tests.factories import (
    CommentFactory,
    EvaluationFactory,
    GenePanelEntrySnapshotFactory,
    GenePanelSnapshotFactory,
    RegionFactory,
    STRFactory,
)
from accounts.tests.factories import UserFactory


class TestEvaluationCommentsAPI(TestCase):
    """Tests for optional comment inclusion in evaluation endpoints."""

    def setUp(self):
        super().setUp()
        self.gps = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        self.gpes = GenePanelEntrySnapshotFactory(panel=self.gps, evaluation=(None,))
        self.str = STRFactory(panel=self.gps, evaluation=(None,))
        self.region = RegionFactory(panel=self.gps, evaluation=(None,))

        # Create evaluations with comments
        self.user = UserFactory(first_name="Jane", last_name="Curator")
        self.evaluation = EvaluationFactory(user=self.user)
        self.comment = CommentFactory(user=self.user, comment="Test comment text")
        self.evaluation.comments.add(self.comment)
        self.gpes.evaluation.add(self.evaluation)

        # STR evaluation with comment
        self.str_evaluation = EvaluationFactory(user=self.user)
        self.str_comment = CommentFactory(user=self.user, comment="STR comment")
        self.str_evaluation.comments.add(self.str_comment)
        self.str.evaluation.add(self.str_evaluation)

        # Region evaluation with comment
        self.region_evaluation = EvaluationFactory(user=self.user)
        self.region_comment = CommentFactory(user=self.user, comment="Region comment")
        self.region_evaluation.comments.add(self.region_comment)
        self.region.evaluation.add(self.region_evaluation)

    def test_gene_comments_excluded_by_default(self):
        """Comments should not appear in gene evaluation response by default."""
        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertNotIn("comments", results[0])

    def test_gene_comments_included_when_requested(self):
        """Comments should appear when include_comments=true."""
        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("comments", results[0])
        self.assertEqual(len(results[0]["comments"]), 1)
        self.assertEqual(results[0]["comments"][0]["comment"], "Test comment text")

    def test_gene_comments_include_user_name(self):
        """Comment user_name should show reviewer's full name."""
        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        comment = response.json()["results"][0]["comments"][0]
        self.assertEqual(comment["user_name"], "Jane Curator")
        self.assertIn("created", comment)

    def test_gene_include_comments_false_excludes(self):
        """Explicit include_comments=false should exclude comments."""
        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "false"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("comments", response.json()["results"][0])

    def test_str_comments_included_when_requested(self):
        """STR evaluation endpoint should support comments."""
        url = reverse_lazy(
            "api:v1:strs-evaluations-list",
            args=(self.gps.panel.pk, self.str.name),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertIn("comments", results[0])
        self.assertEqual(results[0]["comments"][0]["comment"], "STR comment")

    def test_region_comments_included_when_requested(self):
        """Region evaluation endpoint should support comments."""
        url = reverse_lazy(
            "api:v1:regions-evaluations-list",
            args=(self.gps.panel.pk, self.region.name),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertIn("comments", results[0])
        self.assertEqual(results[0]["comments"][0]["comment"], "Region comment")

    def test_empty_comments_returns_empty_array(self):
        """Evaluation with no comments should return empty array when requested."""
        # Create an evaluation without comments
        evaluation_no_comments = EvaluationFactory(user=self.user)
        self.gpes.evaluation.add(evaluation_no_comments)

        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        # Should have 2 evaluations now
        self.assertEqual(len(results), 2)
        # Find the one without comments
        for result in results:
            self.assertIn("comments", result)
            # One should have 1 comment, one should have 0
        comments_counts = sorted(len(r["comments"]) for r in results)
        self.assertEqual(comments_counts, [0, 1])

    def test_comments_ordered_newest_first(self):
        """Comments should be ordered newest first."""
        # Add a second comment
        second_comment = CommentFactory(user=self.user, comment="Second comment")
        self.evaluation.comments.add(second_comment)

        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        comments = response.json()["results"][0]["comments"]
        self.assertEqual(len(comments), 2)
        # Verify newest first by checking created timestamps
        first_created = comments[0]["created"]
        second_created = comments[1]["created"]
        self.assertGreaterEqual(first_created, second_created)

    def test_comment_without_user(self):
        """Comment with no user should return user_name as null."""
        # Create comment without user
        comment_no_user = CommentFactory(user=None, comment="Anonymous comment")
        self.evaluation.comments.add(comment_no_user)

        url = reverse_lazy(
            "api:v1:genes-evaluations-list",
            args=(self.gps.panel.pk, self.gpes.gene_core.gene_symbol),
        )
        response = self.client.get(url, {"include_comments": "true"})

        self.assertEqual(response.status_code, 200)
        comments = response.json()["results"][0]["comments"]
        # Find the comment without user
        anon_comment = next(c for c in comments if c["comment"] == "Anonymous comment")
        self.assertIsNone(anon_comment["user_name"])

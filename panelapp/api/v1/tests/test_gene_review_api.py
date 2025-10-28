from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.tests.factories import UserFactory
from accounts.models import Reviewer
from panels.tests.factories import (
    GenePanelSnapshotFactory,
    GeneFactory,
    GenePanelEntrySnapshotFactory,
)
from panels.models import Evaluation, GenePanel


class GeneReviewAPITestCase(TestCase):
    """Tests for gene review submission endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create users
        self.gel_user = UserFactory(reviewer__user_type=Reviewer.TYPES.GEL)
        self.verified_user = UserFactory(reviewer__user_type=Reviewer.TYPES.REVIEWER)
        self.external_user = UserFactory(reviewer__user_type=Reviewer.TYPES.EXTERNAL)

        # Create panel with gene (using DNAH5 - primary ciliary dyskinesia)
        self.panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        self.gene = GeneFactory(gene_symbol="DNAH5", active=True)
        self.gene_entry = GenePanelEntrySnapshotFactory(
            panel=self.panel,
            gene_core=self.gene,
            moi="BIALLELIC, autosomal or pseudoautosomal",
            evaluation=[],  # No evaluations initially
        )

        # URL
        self.url = reverse(
            "api:v1:panel-gene-reviews-list",
            kwargs={"panel_pk": self.panel.panel.pk, "gene_entity_name": "DNAH5"},
        )

        # Valid review data
        self.valid_data = {
            "rating": "GREEN",
            "comments": "Strong evidence for primary ciliary dyskinesia",
        }

    # --- Permission Tests ---

    def test_unauthenticated_cannot_review(self):
        """Unauthenticated users cannot submit reviews"""
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_external_user_cannot_review(self):
        """External users cannot submit reviews"""
        self.client.force_authenticate(user=self.external_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_reviewer_can_review(self):
        """Verified reviewers can submit reviews"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_gel_user_can_review(self):
        """GEL users can submit reviews"""
        self.client.force_authenticate(user=self.gel_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Validation Tests ---

    def test_gene_not_in_panel_404(self):
        """Reviewing non-existent gene returns 404"""
        self.client.force_authenticate(user=self.verified_user)
        url = reverse(
            "api:v1:panel-gene-reviews-list",
            kwargs={"panel_pk": self.panel.panel.pk, "gene_entity_name": "TP53"},
        )
        response = self.client.post(url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_panel_not_found_404(self):
        """Non-existent panel returns 404"""
        self.client.force_authenticate(user=self.verified_user)
        url = reverse(
            "api:v1:panel-gene-reviews-list",
            kwargs={"panel_pk": 99999, "gene_entity_name": "DNAH5"},
        )
        response = self.client.post(url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_at_least_one_field_required(self):
        """Empty review is rejected"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Evaluation Creation Tests ---

    def test_creates_evaluation(self):
        """Review creates Evaluation record"""
        self.client.force_authenticate(user=self.verified_user)
        initial_count = self.gene_entry.evaluation.count()
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.gene_entry.evaluation.count(), initial_count + 1)

    def test_links_to_gene_entry(self):
        """Evaluation is linked to GenePanelEntrySnapshot"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        evaluation = Evaluation.objects.latest("created")
        self.assertIn(evaluation, self.gene_entry.evaluation.all())

    def test_creates_comment_if_provided(self):
        """Comment created when comments field provided"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        evaluation = Evaluation.objects.latest("created")
        self.assertEqual(evaluation.comments.count(), 1)
        comment = evaluation.comments.first()
        self.assertEqual(
            comment.comment, "Strong evidence for primary ciliary dyskinesia"
        )

    def test_review_with_all_fields(self):
        """All review fields stored correctly"""
        self.client.force_authenticate(user=self.verified_user)
        data = {
            "rating": "GREEN",
            "comments": "Test comment",
            "moi": "BIALLELIC, autosomal or pseudoautosomal",
            "mode_of_pathogenicity": "Loss-of-function variants (as defined in pop up message) DO NOT cause this phenotype - please provide details in the comments",
            "publications": ["12345678", "87654321"],
            "phenotypes": ["Cystic fibrosis", "Pancreatic insufficiency"],
            "current_diagnostic": True,
            "clinically_relevant": False,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        evaluation = Evaluation.objects.latest("created")
        self.assertEqual(evaluation.rating, "GREEN")
        self.assertEqual(len(evaluation.publications), 2)
        self.assertEqual(len(evaluation.phenotypes), 2)
        self.assertTrue(evaluation.current_diagnostic)

    # --- Multiple Reviews Tests ---

    def test_multiple_reviews_allowed(self):
        """Same user can submit multiple reviews"""
        self.client.force_authenticate(user=self.verified_user)

        # First review
        response1 = self.client.post(self.url, {"rating": "GREEN"}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["rating"], "GREEN")

        # Second review
        response2 = self.client.post(self.url, {"rating": "AMBER"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data["rating"], "AMBER")

        # Verify both evaluations were created by the same user
        recent_evals = Evaluation.objects.filter(user=self.verified_user).order_by(
            "-created"
        )[:2]
        self.assertEqual(len(recent_evals), 2)
        self.assertEqual(recent_evals[0].rating, "AMBER")  # Most recent
        self.assertEqual(recent_evals[1].rating, "GREEN")

    def test_different_users_can_review(self):
        """Different users can review same gene"""
        # First user
        self.client.force_authenticate(user=self.verified_user)
        response1 = self.client.post(self.url, {"rating": "GREEN"}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["rating"], "GREEN")

        # Second user
        self.client.force_authenticate(user=self.gel_user)
        response2 = self.client.post(self.url, {"rating": "AMBER"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data["rating"], "AMBER")

        # Verify evaluations were created by different users
        eval_by_verified = Evaluation.objects.filter(user=self.verified_user).latest(
            "created"
        )
        eval_by_gel = Evaluation.objects.filter(user=self.gel_user).latest("created")
        self.assertEqual(eval_by_verified.rating, "GREEN")
        self.assertEqual(eval_by_gel.rating, "AMBER")

    # --- Does Not Modify Entry Tests ---

    def test_does_not_modify_entry_metadata(self):
        """Review doesn't change GenePanelEntrySnapshot fields"""
        self.client.force_authenticate(user=self.verified_user)
        original_moi = self.gene_entry.moi

        # Submit review with different MOI
        data = {"rating": "GREEN", "moi": "BIALLELIC, autosomal or pseudoautosomal"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Gene entry MOI should be unchanged
        self.gene_entry.refresh_from_db()
        self.assertEqual(self.gene_entry.moi, original_moi)

    def test_does_not_increment_version(self):
        """Submitting review doesn't increment panel version"""
        self.client.force_authenticate(user=self.gel_user)  # Even GEL user
        initial_version = self.panel.version

        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.panel.refresh_from_db()
        self.assertEqual(self.panel.version, initial_version)

    # --- Edge Cases ---

    def test_review_with_only_rating(self):
        """Can submit review with only rating"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, {"rating": "GREEN"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_review_with_only_comment(self):
        """Can submit review with only comment"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(
            self.url, {"comments": "Interesting gene"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_review_with_only_publications(self):
        """Can submit review with only publications"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(
            self.url, {"publications": ["12345678"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_review_with_boolean_fields(self):
        """Can submit review with only boolean fields"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(
            self.url, {"current_diagnostic": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

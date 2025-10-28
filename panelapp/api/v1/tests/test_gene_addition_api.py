from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.tests.factories import UserFactory
from accounts.models import Reviewer
from panels.tests.factories import GenePanelSnapshotFactory, GeneFactory, TagFactory
from panels.models import GenePanelEntrySnapshot, GenePanel


class GeneAdditionAPITestCase(TestCase):
    """Tests for minimal gene addition endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create users with different permission levels
        self.gel_user = UserFactory(reviewer__user_type=Reviewer.TYPES.GEL)
        self.verified_user = UserFactory(reviewer__user_type=Reviewer.TYPES.REVIEWER)
        self.external_user = UserFactory(reviewer__user_type=Reviewer.TYPES.EXTERNAL)

        # Create panel
        self.panel = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)

        # Create genes in reference database
        self.gene = GeneFactory(gene_symbol="DNAH5", active=True)
        self.gene2 = GeneFactory(gene_symbol="TP53", active=True)

        # Create tags for testing
        self.tag1 = TagFactory()
        self.tag2 = TagFactory()

        # Base URL
        self.url = reverse(
            "api:v1:panels_genes-list", kwargs={"panel_pk": self.panel.panel.pk}
        )

        # Minimal valid data
        self.valid_data = {
            "gene_symbol": "DNAH5",
            "moi": "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
            "sources": ["Expert Review"],
        }

    # --- Permission Tests ---

    def test_unauthenticated_cannot_add_gene(self):
        """Unauthenticated users cannot add genes (403)"""
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_external_user_cannot_add_gene(self):
        """External (unverified) users cannot add genes (403)"""
        self.client.force_authenticate(user=self.external_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_reviewer_can_add_gene(self):
        """Verified reviewers can add genes (201)"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_gel_user_can_add_gene(self):
        """GEL users can add genes (201)"""
        self.client.force_authenticate(user=self.gel_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Validation Tests ---

    def test_gene_symbol_required(self):
        """gene_symbol field is required"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        del data["gene_symbol"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gene_symbol", response.data)

    def test_invalid_gene_symbol_rejected(self):
        """Non-existent gene symbols return 400 with clear error"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["gene_symbol"] = "NONEXISTENT"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gene_symbol", response.data)
        self.assertIn("not found in reference database", str(response.data))

    def test_inactive_gene_rejected(self):
        """Inactive genes are rejected"""
        GeneFactory(gene_symbol="INACTIVE", active=False)
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["gene_symbol"] = "INACTIVE"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gene_symbol", response.data)
        self.assertIn("not active", str(response.data))

    def test_moi_required(self):
        """moi field is required"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        del data["moi"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("moi", response.data)

    def test_sources_required(self):
        """sources field is required"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        del data["sources"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sources", response.data)

    def test_sources_non_empty(self):
        """sources must have at least one element"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["sources"] = []
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_gene_rejected(self):
        """Cannot add same gene twice to panel"""
        self.client.force_authenticate(user=self.verified_user)
        # Add once
        response1 = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        # Try to add again
        response2 = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gene_symbol", response2.data)
        self.assertIn("already exists", str(response2.data))

    # --- Behavior Tests ---

    def test_gel_user_increments_version(self):
        """GEL users increment panel version when adding gene"""
        self.client.force_authenticate(user=self.gel_user)
        initial_version = self.panel.version
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Refresh panel from database - need to get the latest version
        from panels.models import GenePanelSnapshot

        updated_panel = GenePanelSnapshot.objects.get_active_annotated(
            name=str(self.panel.panel.pk)
        ).first()
        self.assertNotEqual(updated_panel.version, initial_version)

    def test_verified_reviewer_no_version_increment(self):
        """Non-GEL verified reviewers don't increment version"""
        self.client.force_authenticate(user=self.verified_user)
        initial_version = self.panel.version
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Version should be unchanged
        self.panel.refresh_from_db()
        self.assertEqual(self.panel.version, initial_version)

    def test_gene_flagged_for_non_gel(self):
        """Genes added by non-GEL reviewers are flagged"""
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        gene_entry = GenePanelEntrySnapshot.objects.get(
            gene_core__gene_symbol="DNAH5", panel=self.panel
        )
        self.assertTrue(gene_entry.flagged)

    def test_gene_not_flagged_for_gel(self):
        """Genes added by GEL users are not flagged"""
        self.client.force_authenticate(user=self.gel_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Note: Need to get from new version if GEL incremented
        from panels.models import GenePanelSnapshot

        panel = GenePanelSnapshot.objects.get_active_annotated(
            name=str(self.panel.panel.pk)
        ).first()
        gene_entry = panel.get_gene("DNAH5")
        self.assertFalse(gene_entry.flagged)

    # --- Critical Test: No Evaluation Created ---

    def test_no_evaluation_created(self):
        """
        Adding gene without rating/comments doesn't create Evaluation.
        This is the KEY test for the minimal endpoint.
        """
        self.client.force_authenticate(user=self.verified_user)
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that no Evaluation was created
        gene_entry = GenePanelEntrySnapshot.objects.get(
            gene_core__gene_symbol="DNAH5", panel=self.panel
        )
        self.assertEqual(gene_entry.evaluation.count(), 0)

    def test_creates_evidence_records(self):
        """Sources create Evidence records"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["sources"] = ["Expert Review", "Literature"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        gene_entry = GenePanelEntrySnapshot.objects.get(
            gene_core__gene_symbol="DNAH5", panel=self.panel
        )
        self.assertEqual(gene_entry.evidence.count(), 2)

    # --- Optional Fields Tests ---

    def test_add_gene_with_publications(self):
        """Publications stored on gene entry (not evaluation)"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["publications"] = ["12345678", "87654321"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        gene_entry = GenePanelEntrySnapshot.objects.get(
            gene_core__gene_symbol="DNAH5", panel=self.panel
        )
        self.assertEqual(len(gene_entry.publications), 2)
        self.assertIn("12345678", gene_entry.publications)

    def test_add_gene_with_all_optional_fields(self):
        """Can add gene with all optional metadata fields"""
        self.client.force_authenticate(user=self.gel_user)
        data = self.valid_data.copy()
        data.update(
            {
                "penetrance": "Complete",
                "mode_of_pathogenicity": "Loss-of-function variants (as defined in pop up message) DO NOT cause this phenotype - please provide details in the comments",
                "publications": ["12345678"],
                "phenotypes": ["Hereditary spastic paraplegia"],
                "transcript": ["ENST00000357654"],
                "tags": [self.tag1.pk, self.tag2.pk],
            }
        )
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- GEL-Only Features ---

    def test_non_gel_cannot_add_tags(self):
        """Non-GEL users cannot assign tags"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["tags"] = [self.tag1.pk]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)
        self.assertIn("GEL", str(response.data))

    def test_gel_can_add_tags(self):
        """GEL users can assign tags"""
        self.client.force_authenticate(user=self.gel_user)
        data = self.valid_data.copy()
        data["tags"] = [self.tag1.pk, self.tag2.pk]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_gel_cannot_add_transcript(self):
        """Non-GEL users cannot add transcript info"""
        self.client.force_authenticate(user=self.verified_user)
        data = self.valid_data.copy()
        data["transcript"] = ["ENST00000357654"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("transcript", response.data)

    def test_gel_can_add_transcript(self):
        """GEL users can add transcript"""
        self.client.force_authenticate(user=self.gel_user)
        data = self.valid_data.copy()
        data["transcript"] = ["ENST00000357654"]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_tag_ids_rejected(self):
        """Invalid tag IDs are rejected"""
        self.client.force_authenticate(user=self.gel_user)
        data = self.valid_data.copy()
        data["tags"] = [99999]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

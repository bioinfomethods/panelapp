from unittest.mock import MagicMock
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import Reviewer
from accounts.tests.factories import ReviewerFactory
from accounts.tests.factories import UserFactory
from panels.tests.factories import GeneFactory
from panels.tests.factories import GenePanelSnapshotFactory


class ReportProxyTestCase(TestCase):
    """Test report proxy view with mocked S3."""

    def setUp(self):
        # Create GEL user
        self.gel_user = UserFactory(reviewer=None)
        ReviewerFactory(user=self.gel_user, user_type=Reviewer.TYPES.GEL)

        # Create non-GEL user
        self.regular_user = UserFactory(reviewer=None)
        ReviewerFactory(user=self.regular_user, user_type=Reviewer.TYPES.EXTERNAL)

        # Sample report HTML
        self.sample_report_html = b"""
        <!DOCTYPE html>
        <html>
        <body>
            <form method="POST" action="/panels/reports/prefill/">
                <input type="hidden" name="csrfmiddlewaretoken" value="{{CSRF_TOKEN}}">
                <input type="hidden" name="form_type" value="review">
                <button type="submit">Prefill</button>
            </form>
        </body>
        </html>
        """

    @patch("s3_storages.ReportsStorage")
    def test_report_proxy_gel_user(self, mock_storage_class):
        """GEL user can access reports."""
        mock_storage = MagicMock()
        mock_storage.open.return_value.__enter__.return_value.read.return_value = (
            self.sample_report_html
        )
        mock_storage_class.return_value = mock_storage

        self.client.force_login(self.gel_user)
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "index.html"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prefill", response.content)

    @patch("s3_storages.ReportsStorage")
    def test_report_proxy_non_gel_user_forbidden(self, mock_storage_class):
        """Non-GEL user cannot access reports."""
        self.client.force_login(self.regular_user)
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "index.html"})
        )

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_report_proxy_anonymous_forbidden(self):
        """Anonymous user cannot access reports."""
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "index.html"})
        )

        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

    @patch("s3_storages.ReportsStorage")
    def test_report_proxy_csrf_injection(self, mock_storage_class):
        """Report proxy injects CSRF token into HTML."""
        mock_storage = MagicMock()
        mock_storage.open.return_value.__enter__.return_value.read.return_value = (
            self.sample_report_html
        )
        mock_storage_class.return_value = mock_storage

        self.client.force_login(self.gel_user)
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "report.html"})
        )

        self.assertEqual(response.status_code, 200)
        # CSRF token should be injected (placeholder replaced)
        self.assertNotIn(b"{{CSRF_TOKEN}}", response.content)
        # Form should still be present
        self.assertIn(b"csrfmiddlewaretoken", response.content)

    @patch("s3_storages.ReportsStorage")
    def test_report_proxy_not_found(self, mock_storage_class):
        """Report proxy returns 404 for missing file."""
        mock_storage = MagicMock()
        mock_storage.open.side_effect = FileNotFoundError()
        mock_storage_class.return_value = mock_storage

        self.client.force_login(self.gel_user)
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "nonexistent.html"})
        )

        self.assertEqual(response.status_code, 404)

    @patch("s3_storages.ReportsStorage")
    def test_report_proxy_pdf_no_csrf_injection(self, mock_storage_class):
        """PDF files are proxied without CSRF injection."""
        pdf_content = b"%PDF-1.4 fake pdf content"
        mock_storage = MagicMock()
        mock_storage.open.return_value.__enter__.return_value.read.return_value = (
            pdf_content
        )
        mock_storage_class.return_value = mock_storage

        self.client.force_login(self.gel_user)
        response = self.client.get(
            reverse("panels:report_proxy", kwargs={"path": "report.pdf"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response.content, pdf_content)


class PrefillFormTestCase(TestCase):
    """Test prefill endpoint and session storage."""

    def setUp(self):
        # Create GEL user
        self.gel_user = UserFactory(reviewer=None)
        ReviewerFactory(user=self.gel_user, user_type=Reviewer.TYPES.GEL)

        # Create test gene
        self.gene = GeneFactory(gene_symbol="CFTR")

        # Create test panel
        self.panel = GenePanelSnapshotFactory()

    def test_prefill_add_stores_session_data(self):
        """Prefill add endpoint stores data in session and redirects."""
        self.client.force_login(self.gel_user)

        response = self.client.post(
            reverse("panels:prefill_form"),
            {
                "form_type": "add",
                "panel_id": "137",
                "gene_symbol": "CFTR",
                "gene_name": "CFTR",
                "source": "Literature",
                "rating": "3",
                "moi": "BIALLELIC",
                "publications": "12345;67890",
                "phenotypes": "Cystic fibrosis;Pancreatitis",
                "comments": "Test summary",
            },
        )

        # Should redirect to add form
        self.assertEqual(response.status_code, 302)
        self.assertIn("/panels/137/gene/add", response.url)

        # Check session data
        session = self.client.session
        prefill_data = session.get("prefill_data")
        self.assertIsNotNone(prefill_data)
        self.assertEqual(prefill_data["form_type"], "add")
        self.assertEqual(prefill_data["gene"], self.gene.pk)
        self.assertEqual(prefill_data["rating"], "3")
        self.assertEqual(prefill_data["publications"], "12345;67890")

    def test_prefill_review_stores_session_data(self):
        """Prefill review endpoint stores data in session and redirects."""
        self.client.force_login(self.gel_user)

        response = self.client.post(
            reverse("panels:prefill_form"),
            {
                "form_type": "review",
                "panel_id": str(self.panel.panel.pk),
                "gene_name": "CFTR",
                "rating": "3",
                "moi": "BIALLELIC",
                "publications": "12345",
                "phenotypes": "Cystic fibrosis",
                "comments": "Review comment",
            },
        )

        # Should redirect to review form
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gene/CFTR/review", response.url)

        # Check session data
        session = self.client.session
        prefill_data = session.get("prefill_data")
        self.assertIsNotNone(prefill_data)
        self.assertEqual(prefill_data["form_type"], "review")
        self.assertEqual(prefill_data["comments"], "Review comment")

    def test_prefill_unknown_gene_symbol(self):
        """Prefill handles unknown gene symbol gracefully."""
        self.client.force_login(self.gel_user)

        response = self.client.post(
            reverse("panels:prefill_form"),
            {
                "form_type": "add",
                "panel_id": "137",
                "gene_symbol": "UNKNOWN_GENE",
                "rating": "3",
            },
        )

        # Should still redirect
        self.assertEqual(response.status_code, 302)

        # Gene PK should be None
        session = self.client.session
        prefill_data = session.get("prefill_data")
        self.assertIsNone(prefill_data["gene"])


class FormViewPrefillTestCase(TestCase):
    """Test that form views read prefill data from session."""

    def setUp(self):
        # Create GEL user
        self.gel_user = UserFactory(reviewer=None)
        ReviewerFactory(user=self.gel_user, user_type=Reviewer.TYPES.GEL)

        # Create test gene and panel with gene
        self.gene = GeneFactory(gene_symbol="CFTR")
        self.panel = GenePanelSnapshotFactory()
        # Add gene to panel for review test
        self.panel.add_gene(
            self.gel_user,
            self.gene.gene_symbol,
            {
                "moi": "BIALLELIC",
                "sources": ["Literature"],
            },
        )

    def test_add_form_reads_prefill_data(self):
        """Add gene form is prefilled from session data."""
        self.client.force_login(self.gel_user)

        # Set up session with prefill data
        session = self.client.session
        session["prefill_data"] = {
            "form_type": "add",
            "gene": self.gene.pk,
            "gene_name": "CFTR",
            "source": ["Literature"],
            "rating": "3",
            "moi": "BIALLELIC",
            "publications": "12345;67890",
            "phenotypes": "Cystic fibrosis",
            "comments": "Test summary",
        }
        session.save()

        # Access the add form
        response = self.client.get(
            reverse(
                "panels:add_entity",
                kwargs={"pk": self.panel.panel.pk, "entity_type": "gene"},
            )
        )

        self.assertEqual(response.status_code, 200)

        # Check that form is prefilled
        self.assertIn(b"12345;67890", response.content)
        self.assertIn(b"Test summary", response.content)

        # Session data should be cleared (one-time use)
        session = self.client.session
        self.assertIsNone(session.get("prefill_data"))

    def test_review_form_reads_prefill_data(self):
        """Review gene form is prefilled from session data."""
        self.client.force_login(self.gel_user)

        # Set up session with prefill data
        session = self.client.session
        session["prefill_data"] = {
            "form_type": "review",
            "rating": "3",
            "moi": "BIALLELIC",
            "publications": "99999",
            "phenotypes": "Cystic fibrosis",
            "comments": "Review from report",
        }
        session.save()

        # Access the review form
        response = self.client.get(
            reverse(
                "panels:review_entity",
                kwargs={
                    "pk": self.panel.panel.pk,
                    "entity_type": "gene",
                    "entity_name": "CFTR",
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        # Check that form is prefilled
        self.assertIn(b"99999", response.content)
        self.assertIn(b"Review from report", response.content)

        # Session data should be cleared
        session = self.client.session
        self.assertIsNone(session.get("prefill_data"))

    def test_prefill_data_cleared_after_use(self):
        """Prefill data is cleared from session after form is loaded."""
        self.client.force_login(self.gel_user)

        # Set up session
        session = self.client.session
        session["prefill_data"] = {
            "form_type": "add",
            "gene": self.gene.pk,
            "rating": "3",
        }
        session.save()

        # Load form once
        self.client.get(
            reverse(
                "panels:add_entity",
                kwargs={"pk": self.panel.panel.pk, "entity_type": "gene"},
            )
        )

        # Load form again - should not be prefilled
        response = self.client.get(
            reverse(
                "panels:add_entity",
                kwargs={"pk": self.panel.panel.pk, "entity_type": "gene"},
            )
        )

        # Form should not have prefill data
        self.assertEqual(response.status_code, 200)

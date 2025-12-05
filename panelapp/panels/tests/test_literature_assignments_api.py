"""Tests for LiteratureAssignment API endpoints."""

from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Reviewer
from accounts.tests.factories import UserFactory
from accounts.tests.setup import LoginGELUser
from panels.models import LiteratureAssignment
from panels.tests.factories import GeneFactory


class LiteratureAssignmentAPITests(LoginGELUser):
    """Test LiteratureAssignment API endpoints."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Get or create Curators group and add GEL users
        self.curator_group, _ = Group.objects.get_or_create(name="Curators")

        # Make gel_user a curator
        self.curator_group.user_set.add(self.gel_user)

        # Create another curator
        self.curator2 = UserFactory(reviewer__user_type=Reviewer.TYPES.GEL)
        self.curator_group.user_set.add(self.curator2)

        self.gene = GeneFactory()
        self.client.force_login(self.gel_user)

    def test_assign_creates_and_assigns(self):
        """Assign endpoint creates record if needed and assigns."""
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "assigned")
        self.assertEqual(data["assigned_to"], self.gel_user.id)
        self.assertIn("updated_at", data)

        # Verify database record
        assignment = LiteratureAssignment.objects.get(
            report_id="report_2025-01-15", gene=self.gene
        )
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.assigned_to_id, self.gel_user.id)

    def test_assign_requires_report_id(self):
        """Assign endpoint requires report_id."""
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "missing_field")

    def test_assign_requires_gene_symbol(self):
        """Assign endpoint requires gene_symbol."""
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "assigned_to": self.gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "missing_field")

    def test_assign_gene_not_found(self):
        """Assign returns 404 for non-existent gene."""
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": "NONEXISTENT",
                "assigned_to": self.gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "gene_not_found")

    def test_assign_rejects_non_curator(self):
        """Assign returns 400 when assigning to non-Curator user."""
        non_curator = UserFactory(reviewer__user_type=Reviewer.TYPES.GEL)
        # Note: non_curator is NOT added to curator_group

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": non_curator.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_assignee")

    def test_assign_conflict_when_record_exists_unexpectedly(self):
        """Conflict when client expects new record but it exists."""
        # Create existing assignment
        LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
        )

        # curator2 thinks record doesn't exist (expected_updated_at=None)
        self.client.force_login(self.curator2)
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.curator2.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "conflict")
        self.assertIn("current_state", response.json())
        self.assertIn("updated_at", response.json()["current_state"])

    def test_assign_conflict_on_stale_updated_at(self):
        """Conflict when client has stale updated_at."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
        )
        stale_updated_at = assignment.updated_at.isoformat()

        # Simulate concurrent update
        assignment.skipped_reason = "changed"
        assignment.save()

        self.client.force_login(self.curator2)
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.curator2.id,
                "expected_updated_at": stale_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "conflict")

    def test_assign_success_with_correct_updated_at(self):
        """Success when client has correct updated_at."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
        )
        current_updated_at = assignment.updated_at.isoformat()

        self.client.force_login(self.curator2)
        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.curator2.id,
                "expected_updated_at": current_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["assigned_to"], self.curator2.id)

    def test_unassign_resets_to_pending(self):
        """Assigning with null assignee resets to pending."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
            assigned_at=timezone.now(),
        )
        current_updated_at = assignment.updated_at.isoformat()

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": None,
                "expected_updated_at": current_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertIsNone(response.json()["assigned_to"])

    def test_skip_requires_reason(self):
        """Skip endpoint requires a reason."""
        response = self.client.post(
            "/api/v1/literature-assignments/skip/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "reason_required")

    def test_skip_creates_and_skips(self):
        """Skip endpoint creates record if needed and skips."""
        response = self.client.post(
            "/api/v1/literature-assignments/skip/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "reason": "Out of scope (cancer gene)",
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "skipped")
        self.assertEqual(data["skipped_reason"], "Out of scope (cancer gene)")
        self.assertIn("updated_at", data)

        # Verify is_triaged (no prior assignee)
        assignment = LiteratureAssignment.objects.get(
            report_id="report_2025-01-15", gene=self.gene
        )
        self.assertTrue(assignment.is_triaged)

    def test_skip_conflict_detection(self):
        """Skip detects concurrent modifications."""
        LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
        )

        # curator2 thinks record doesn't exist
        self.client.force_login(self.curator2)
        response = self.client.post(
            "/api/v1/literature-assignments/skip/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "reason": "Not relevant",
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "conflict")

    def test_unskip_via_assign(self):
        """Assigning a skipped gene clears the skip state."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            status="skipped",
            skipped_by=self.gel_user,
            skipped_at=timezone.now(),
            skipped_reason="Initial skip",
        )
        current_updated_at = assignment.updated_at.isoformat()

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.curator2.id,
                "expected_updated_at": current_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "assigned")
        self.assertIsNone(response.json()["skipped_by"])
        self.assertEqual(response.json()["skipped_reason"], "")

    def test_skip_preserves_assignee(self):
        """Skipping an assigned gene preserves the assignee for history."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.gel_user,
            status="assigned",
            assigned_at=timezone.now(),
        )
        current_updated_at = assignment.updated_at.isoformat()

        response = self.client.post(
            "/api/v1/literature-assignments/skip/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "reason": "Investigated, no action needed",
                "expected_updated_at": current_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "skipped")

        # Verify is_investigated (has prior assignee)
        assignment.refresh_from_db()
        self.assertEqual(assignment.assigned_to, self.gel_user)
        self.assertTrue(assignment.is_investigated)

    def test_non_gel_user_forbidden(self):
        """Non-GEL users cannot access the API."""
        non_gel_user = UserFactory(reviewer__user_type=Reviewer.TYPES.REVIEWER)
        self.client.force_login(non_gel_user)

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": non_gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_forbidden(self):
        """Unauthenticated requests are forbidden."""
        self.client.logout()

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": self.gel_user.id,
                "expected_updated_at": None,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_restore_from_skipped_to_pending(self):
        """Assigning with null to a skipped gene restores to pending."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            status="skipped",
            skipped_by=self.gel_user,
            skipped_at=timezone.now(),
            skipped_reason="Initial skip",
        )
        current_updated_at = assignment.updated_at.isoformat()

        response = self.client.post(
            "/api/v1/literature-assignments/assign/",
            {
                "report_id": "report_2025-01-15",
                "gene_symbol": self.gene.gene_symbol,
                "assigned_to": None,
                "expected_updated_at": current_updated_at,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "pending")
        self.assertIsNone(response.json()["assigned_to"])
        self.assertEqual(response.json()["skipped_reason"], "")

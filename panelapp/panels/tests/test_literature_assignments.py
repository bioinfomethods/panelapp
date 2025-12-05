"""Tests for LiteratureAssignment model."""

from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.tests.factories import UserFactory
from panels.models import LiteratureAssignment
from panels.tests.factories import GeneFactory


class LiteratureAssignmentModelTests(TestCase):
    """Test LiteratureAssignment model functionality."""

    def setUp(self):
        self.curator_group, _ = Group.objects.get_or_create(name="Curators")
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.curator_group.user_set.add(self.user1, self.user2)
        self.gene = GeneFactory()

    def test_create_assignment_defaults_to_pending(self):
        """New assignments should default to pending status."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        self.assertEqual(assignment.status, "pending")
        self.assertIsNone(assignment.assigned_to)
        self.assertIsNone(assignment.assigned_at)

    def test_unique_constraint_report_gene(self):
        """Cannot create duplicate assignment for same report+gene."""
        LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        with self.assertRaises(IntegrityError):
            LiteratureAssignment.objects.create(
                report_id="report_2025-01-15", gene=self.gene
            )

    def test_same_gene_different_reports_allowed(self):
        """Same gene can be assigned in different reports."""
        a1 = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        a2 = LiteratureAssignment.objects.create(
            report_id="report_2025-01-16", gene=self.gene
        )
        self.assertNotEqual(a1.pk, a2.pk)

    def test_different_genes_same_report_allowed(self):
        """Different genes can be assigned in same report."""
        gene2 = GeneFactory()
        a1 = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        a2 = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=gene2
        )
        self.assertNotEqual(a1.pk, a2.pk)

    def test_skip_preserves_assignee(self):
        """When skipping an assigned gene, assigned_to should be preserved."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.user1,
            status="assigned",
            assigned_at=timezone.now(),
        )
        # Skip the assignment
        assignment.status = "skipped"
        assignment.skipped_by = self.user1
        assignment.skipped_at = timezone.now()
        assignment.skipped_reason = "Out of scope"
        assignment.save()

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, "skipped")
        self.assertEqual(assignment.assigned_to, self.user1)
        self.assertTrue(assignment.is_investigated)
        self.assertFalse(assignment.is_triaged)

    def test_skip_without_assignment_is_triaged(self):
        """Skipping without prior assignment marks as triaged."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        assignment.status = "skipped"
        assignment.skipped_by = self.user1
        assignment.skipped_at = timezone.now()
        assignment.skipped_reason = "Low priority"
        assignment.save()

        assignment.refresh_from_db()
        self.assertTrue(assignment.is_triaged)
        self.assertFalse(assignment.is_investigated)

    def test_str_representation(self):
        """Test string representation includes gene symbol and report."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            status="assigned",
        )
        str_repr = str(assignment)
        self.assertIn(self.gene.gene_symbol, str_repr)
        self.assertIn("report_2025-01-15", str_repr)
        self.assertIn("assigned", str_repr)

    def test_updated_at_changes_on_save(self):
        """updated_at timestamp should change when assignment is modified."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        original_updated_at = assignment.updated_at

        # Modify and save
        assignment.status = "assigned"
        assignment.assigned_to = self.user1
        assignment.save()

        assignment.refresh_from_db()
        self.assertGreater(assignment.updated_at, original_updated_at)

    def test_gene_protection_on_delete(self):
        """Deleting a gene should raise ProtectedError if assignments exist."""
        from django.db.models import ProtectedError

        LiteratureAssignment.objects.create(
            report_id="report_2025-01-15", gene=self.gene
        )
        with self.assertRaises(ProtectedError):
            self.gene.delete()

    def test_user_deletion_sets_null(self):
        """Deleting user should set assigned_to to NULL."""
        assignment = LiteratureAssignment.objects.create(
            report_id="report_2025-01-15",
            gene=self.gene,
            assigned_to=self.user1,
            status="assigned",
        )

        # Remove user from group first (to avoid group membership issues)
        self.curator_group.user_set.remove(self.user1)
        self.user1.delete()

        assignment.refresh_from_db()
        self.assertIsNone(assignment.assigned_to)
        # Status is NOT automatically changed - this is expected behavior
        self.assertEqual(assignment.status, "assigned")

from django.contrib.auth import get_user_model
from django.db import models
from model_utils import Choices

from .gene import Gene

User = get_user_model()


class LiteratureAssignment(models.Model):
    """Tracks curator assignments for literature review tasks."""

    STATUS = Choices(
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("skipped", "Skipped"),
    )

    # Composite key (enforced via unique_together)
    report_id = models.CharField(
        max_length=100, help_text="Report directory name, e.g. 'report_2025-01-15'"
    )
    gene = models.ForeignKey(
        Gene,
        on_delete=models.PROTECT,
        related_name="literature_assignments",
    )

    # Assignment tracking
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="literature_assignments",
        help_text="Current or last assignee (preserved when skipped)",
    )
    status = models.CharField(max_length=20, choices=STATUS, default=STATUS.pending)
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Skip tracking
    skipped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skipped_literature_assignments",
        help_text="User who marked this as skipped",
    )
    skipped_at = models.DateTimeField(null=True, blank=True)
    skipped_reason = models.TextField(
        blank=True, default="", help_text="Required reason for skipping (free text)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["report_id", "gene"]]
        indexes = [
            models.Index(fields=["report_id"], name="lit_assign_report_idx"),
            models.Index(fields=["assigned_to"], name="lit_assign_user_idx"),
        ]

    def __str__(self):
        return f"{self.gene.gene_symbol} in {self.report_id} ({self.status})"

    @property
    def is_triaged(self):
        """Skipped during quick assessment, without deep investigation."""
        return self.status == self.STATUS.skipped and self.assigned_to is None

    @property
    def is_investigated(self):
        """Was assigned, curator examined literature, decided no action needed."""
        return self.status == self.STATUS.skipped and self.assigned_to is not None

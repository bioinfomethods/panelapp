"""Form for copying a gene to multiple panels."""

from django import forms
from django.db import transaction
from dal_select2.widgets import ModelSelect2Multiple
from panels.models import GenePanelSnapshot, GenePanel


class CopyGeneForm(forms.Form):
    """Form to copy a gene from one panel to multiple other panels.

    This form allows GEL reviewers to copy an existing gene entry
    (with all its metadata) from a source panel to multiple target panels
    in a single operation.
    """

    gene_symbol_hidden = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    target_panels = forms.ModelMultipleChoiceField(
        queryset=GenePanelSnapshot.objects.none(),
        label="Target panels",
        widget=ModelSelect2Multiple(
            url="autocomplete-panels-without-gene",
            forward=["gene_symbol_hidden"],
            attrs={"data-minimum-input-length": 1},
        ),
        help_text="Search and select one or more panels (panels already containing this gene are excluded)",
    )

    reviews_to_copy = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Reviews to copy",
        help_text="Select which reviews to copy to the target panels (at least one required)",
    )

    def __init__(self, *args, **kwargs):
        self.gene_symbol = kwargs.pop("gene_symbol")
        self.user = kwargs.pop("user")
        source_panel_id = kwargs.pop("source_panel_id")
        super().__init__(*args, **kwargs)

        # Set the hidden field with the gene symbol for forwarding to autocomplete
        self.fields["gene_symbol_hidden"].initial = self.gene_symbol

        # Get the source panel
        self.source_panel = GenePanel.objects.get_panel(
            pk=str(source_panel_id)
        ).active_panel

        # Determine if user has admin access
        is_admin = self.user.is_authenticated and self.user.reviewer.is_GEL()

        # Get all active panels (for target selection)
        all_panels = GenePanelSnapshot.objects.get_active(
            all=is_admin, internal=is_admin
        )

        # Target panels should NOT already contain this gene
        # The autocomplete view handles this filtering, but we also set
        # the queryset here as a fallback for validation
        panels_with_gene = GenePanelSnapshot.objects.get_shared_panels(
            self.gene_symbol, all=is_admin, internal=is_admin
        )
        panels_without_gene = all_panels.exclude(
            pk__in=panels_with_gene.values_list("pk", flat=True)
        )

        self.fields["target_panels"].queryset = panels_without_gene

        # Populate review choices from source gene's evaluations
        source_gene_entry = self.source_panel.get_gene(
            self.gene_symbol, prefetch_extra=True
        )
        evaluations = source_gene_entry.evaluation.all()

        # Create choices: (user_id, reviewer_name)
        review_choices = [
            (str(ev.user.pk), ev.user.get_reviewer_name()) for ev in evaluations
        ]
        self.fields["reviews_to_copy"].choices = review_choices

        # Default: select all reviews
        self.fields["reviews_to_copy"].initial = [str(ev.user.pk) for ev in evaluations]

    def clean_target_panels(self):
        """Validate that at least one target panel is selected."""
        target_panels = self.cleaned_data.get("target_panels")
        if not target_panels or len(target_panels) == 0:
            raise forms.ValidationError(
                "Please select at least one target panel to copy the gene to."
            )
        return target_panels

    def clean_reviews_to_copy(self):
        """Validate that at least one review is selected."""
        reviews = self.cleaned_data.get("reviews_to_copy")
        if not reviews or len(reviews) == 0:
            raise forms.ValidationError(
                "Please select at least one review to copy. "
                "You must copy at least one review when copying a gene."
            )
        return reviews

    def clean(self):
        """Validate that source panel actually contains the gene."""
        cleaned_data = super().clean()

        if not self.source_panel.has_gene(self.gene_symbol):
            raise forms.ValidationError(
                f"The source panel does not contain gene {self.gene_symbol}."
            )

        return cleaned_data

    def copy_gene_to_panels(self):
        """Copy the gene from source panel to all target panels.

        All operations are performed atomically - either all panels are updated
        or none are (all-or-nothing transaction). If any panel fails, an
        exception is raised and all changes are rolled back.
        """
        target_panels = self.cleaned_data["target_panels"]
        selected_review_user_ids = self.cleaned_data.get("reviews_to_copy", [])

        # Get the gene entry from source panel with all metadata
        source_gene_entry = self.source_panel.get_gene(
            self.gene_symbol, prefetch_extra=True
        )

        # Build gene_data dict with all metadata from source
        # Note: Don't include rating/comment here - reviews are copied separately
        gene_data = {
            "moi": source_gene_entry.moi,
            "penetrance": source_gene_entry.penetrance,
            "publications": source_gene_entry.publications,
            "phenotypes": source_gene_entry.phenotypes,
            "mode_of_pathogenicity": source_gene_entry.mode_of_pathogenicity,
            "transcript": source_gene_entry.transcript,
            "sources": [ev.name for ev in source_gene_entry.evidence.all()],
            "tags": [tag.pk for tag in source_gene_entry.tags.all()],
        }

        # Wrap entire operation in atomic transaction - all or nothing
        with transaction.atomic():
            # Copy to each target panel
            for target_panel_snapshot in target_panels:
                # Get the fresh active panel (in case it was incremented)
                target_panel = GenePanel.objects.get_panel(
                    pk=str(target_panel_snapshot.panel.pk)
                ).active_panel

                # Add the gene with all metadata
                new_gene_entry = target_panel.add_gene(
                    user=self.user,
                    gene_symbol=self.gene_symbol,
                    gene_data=gene_data,
                    increment_version=True,
                )

                if not new_gene_entry:
                    # This shouldn't happen since we validated in clean(),
                    # but if it does, raise to rollback the transaction
                    raise forms.ValidationError(
                        f"Failed to add gene to panel {target_panel.panel.name}"
                    )

                # Copy selected reviews to the new gene
                user_ids_as_ints = [int(uid) for uid in selected_review_user_ids]
                new_gene_entry.copy_reviews_to_new_gene(
                    source_gene_entry=source_gene_entry,
                    source_panel_name=self.source_panel.panel.name,
                    user_ids_to_copy=user_ids_as_ints,
                )

                # Add activity log
                target_panel.add_activity(
                    self.user,
                    f"Copied gene {self.gene_symbol} from panel "
                    f"{self.source_panel.panel.name}",
                )

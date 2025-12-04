"""Form for copying an STR to multiple panels."""

from django import forms
from dal_select2.widgets import ModelSelect2Multiple
from panels.models import GenePanelSnapshot, GenePanel
from panels.tasks import background_copy_str


class CopySTRForm(forms.Form):
    """Form to copy an STR from one panel to multiple other panels.

    This form allows GEL reviewers to copy an existing STR entry
    (with all its metadata) from a source panel to multiple target panels
    in a single operation.
    """

    target_panels = forms.ModelMultipleChoiceField(
        queryset=GenePanelSnapshot.objects.get_active_annotated(
            internal=False, deleted=False
        ).exclude(is_super_panel=True),
        label="Target panels",
        widget=ModelSelect2Multiple(
            url="autocomplete-simple-panels",
            attrs={"data-minimum-input-length": 1},
        ),
        help_text="STR and selected reviews will be copied to panels without the STR. For panels that already have the STR, only new reviews from selected reviewers will be added.",
    )

    reviews_to_copy = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Reviews to copy",
        help_text="Select which reviews to copy to the target panels (at least one required)",
    )

    def __init__(self, *args, **kwargs):
        self.str_name = kwargs.pop("str_name")
        self.user = kwargs.pop("user")
        source_panel_id = kwargs.pop("source_panel_id")
        super().__init__(*args, **kwargs)

        # Update queryset to include internal panels for GEL users
        is_gel = hasattr(self.user, "reviewer") and self.user.reviewer.is_GEL()
        self.fields[
            "target_panels"
        ].queryset = GenePanelSnapshot.objects.get_active_annotated(
            all=is_gel, internal=is_gel, deleted=False
        ).exclude(is_super_panel=True)

        # Get the source panel
        self.source_panel = GenePanel.objects.get_panel(
            pk=str(source_panel_id)
        ).active_panel

        # Populate review choices from source STR's evaluations
        source_str_entry = self.source_panel.get_str(self.str_name, prefetch_extra=True)
        evaluations = source_str_entry.evaluation.all()

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
                "Please select at least one target panel to copy the STR to."
            )
        return target_panels

    def clean_reviews_to_copy(self):
        """Validate that at least one review is selected."""
        reviews = self.cleaned_data.get("reviews_to_copy")
        if not reviews or len(reviews) == 0:
            raise forms.ValidationError(
                "Please select at least one review to copy. "
                "You must copy at least one review when copying an STR."
            )
        return reviews

    def clean(self):
        """Validate that source panel actually contains the STR."""
        cleaned_data = super().clean()

        if not self.source_panel.has_str(self.str_name):
            raise forms.ValidationError(
                f"The source panel does not contain STR {self.str_name}."
            )

        return cleaned_data

    def copy_str_to_panels(self):
        """Copy the STR from source panel to all target panels.

        Queues a background task to perform the copy operation asynchronously
        to avoid timeouts when copying to many panels.

        All operations are performed atomically - either all panels are updated
        or none are (all-or-nothing transaction). If any panel fails, an
        exception is raised and all changes are rolled back.
        """
        target_panels = self.cleaned_data["target_panels"]
        selected_review_user_ids = self.cleaned_data.get("reviews_to_copy", [])

        # Extract PKs for serializable parameters
        target_panel_pks = [panel.pk for panel in target_panels]

        # Queue background task
        background_copy_str.delay(
            user_pk=self.user.pk,
            str_name=self.str_name,
            source_panel_pk=self.source_panel.pk,
            target_panel_pks=target_panel_pks,
            selected_review_user_ids=selected_review_user_ids,
        )

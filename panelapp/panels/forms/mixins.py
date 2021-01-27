from django import forms

from panels.models import GenePanelSnapshot


class EntityFormMixin:
    def clean_source(self):
        # check if there is an expert review evidence, i.e. green is rated
        # it's set manually and not via edit gene page

        initial_sources = self.initial.get("source", [])
        cleaned_sources = self.cleaned_data["source"]

        if not cleaned_sources:
            raise forms.ValidationError("Please select a source")

        expert_review = [s for s in cleaned_sources if s.startswith("Expert Review ")]
        initial_expert_review = [
            s for s in initial_sources if s.startswith("Expert Review ")
        ]

        if len(expert_review) > 1:
            raise forms.ValidationError(
                "Entity contains multiple Expert Review sources"
            )
        elif len(expert_review) < len(initial_expert_review):
            # This prevents silently saving the data as there is a fail-safe in
            # edit entity code which doesn't remove Expert Review sources
            # These sources need to be removed manually via panel detail page

            raise forms.ValidationError(
                "Please remove extra Expert Review sources from panel detail page"
            )

        return cleaned_sources

    def clean_moi(self):
        if not self.cleaned_data["moi"]:
            raise forms.ValidationError("Please select a mode of inheritance")
        return self.cleaned_data["moi"]

    def save(self, *args, **kwargs):
        """Don't save the original panel as we need to increment version first"""
        return False

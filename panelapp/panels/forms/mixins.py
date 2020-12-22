from django import forms

from panels.models import GenePanelSnapshot


class EntityFormMixin:
    def clean_source(self):
        # check if there is an expert review evidence, i.e. green is rated
        # it's set manually and not via edit gene page

        cleaned_sources = self.cleaned_data["source"]

        if not cleaned_sources:
            raise forms.ValidationError("Please select a source")

        expert_review = [s for s in cleaned_sources if s.startswith("Expert Review ")]

        if len(expert_review) > 1:
            raise forms.ValidationError(
                "Entity contains multiple Expert Review sources"
            )

        return cleaned_sources

    def clean_moi(self):
        if not self.cleaned_data["moi"]:
            raise forms.ValidationError("Please select a mode of inheritance")
        return self.cleaned_data["moi"]

    def save(self, *args, **kwargs):
        """Don't save the original panel as we need to increment version first"""
        return False

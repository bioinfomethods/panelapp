from django import forms

from panels.models import GenePanelSnapshot


class EntityFormMixin:
    def clean_source(self):
        # check if there is an expert review evidence, i.e. green is rated
        # it's set manually and not via edit gene page

        expert_review = [
            s for s in self.initial.get("source", []) if s.startswith("Expert Review ")
        ]

        if len(self.cleaned_data["source"]) < 1 and not expert_review:
            raise forms.ValidationError("Please select a source")
        return self.cleaned_data["source"]

    def clean_moi(self):
        if not self.cleaned_data["moi"]:
            raise forms.ValidationError("Please select a mode of inheritance")
        return self.cleaned_data["moi"]

    def save(self, *args, **kwargs):
        """Don't save the original panel as we need to increment version first"""
        return False

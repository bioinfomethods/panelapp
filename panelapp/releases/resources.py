from typing import Iterable

from django import forms
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import (
    BooleanWidget,
    CharWidget,
    ForeignKeyWidget,
)

from panels.models import GenePanelSnapshot
from releases.models import ReleasePanel


class CharChoicesWidget(CharWidget):
    def __init__(self, choices: Iterable[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def clean(self, value, row=None, **kwargs):
        cleaned = super().clean(value, row=row, **kwargs)
        if value not in self.choices:
            raise ValueError(f"Not a valid choice: {value}")
        return cleaned


class StrictBooleanWidget(BooleanWidget):
    def clean(self, value, row=None, **kwargs):
        if value in self.NULL_VALUES:
            return None
        if value in self.TRUE_VALUES:
            return True
        if value in self.FALSE_VALUES:
            return False
        raise ValueError(f"`{value}` value must be either `true` or `false`.")


class ReleasePanelResource(ModelResource):
    class Meta:
        model = ReleasePanel
        clean_model_instances = True
        import_id_fields = ("panel", "release")

    panel = Field(
        column_name="Panel ID",
        attribute="panel",
        widget=ForeignKeyWidget(GenePanelSnapshot, field="panel__pk"),
    )
    promote = Field(
        column_name="Promote",
        attribute="promote",
        widget=StrictBooleanWidget(),
    )

    def __init__(self, release):
        self.release = release

    def before_import(self, dataset, **kwargs):
        missing_headers = {"Panel ID", "Promote"} - set(dataset.headers)
        if missing_headers:
            missing_headers = [f"`{x}`" for x in sorted(missing_headers)]
            raise forms.ValidationError(
                f"Missing headers: {', '.join(sorted(missing_headers))}"
            )
        panel_id_index = dataset.headers.index("Panel ID")
        panels = set()
        errors = []
        for i, row in enumerate(dataset, 1):
            if row[panel_id_index] in panels:
                errors.append(forms.ValidationError(f"Row {i}: Panel is a duplicate."))
            panels.add(row[panel_id_index])
        if errors:
            raise forms.ValidationError(errors)
        dataset.headers.append("release")

        # The import file is the source of truth for release panels
        # Remove existing release panels
        self.release.releasepanel_set.all().delete()

        super().before_import(dataset, **kwargs)

    def before_import_row(self, row, **kwargs):
        row["release"] = self.release.pk

    def before_save_instance(self, instance: ReleasePanel, row, **kwargs):
        instance.release = self.release

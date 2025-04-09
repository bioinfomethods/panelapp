import io
import re

import tablib
from django import forms
from import_export.forms import ImportForm
from import_export.results import (
    Error,
    InvalidRow,
)
from jinja2 import TemplateSyntaxError
from jinja2.sandbox import ImmutableSandboxedEnvironment

from panels.models.genepanelsnapshot import GenePanelSnapshot
from releases.models import Release
from releases.resources import ReleasePanelResource


class ReleaseForm(forms.ModelForm):
    class Meta:
        model = Release
        fields = (
            "name",
            "promotion_comment",
        )

    promotion_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(),
        help_text=(
            'The comment uses <a href="https://jinja.palletsprojects.com/en/stable/templates/">jinja2</a> template syntax.<br /><br />'
            "Variables available for use are <code>version</code> and <code>now.yyyy_mm_dd_hh_mm</code>."
        ),
    )

    def clean_promotion_comment(self):
        template_environment = ImmutableSandboxedEnvironment()
        try:
            template_environment.from_string(self.cleaned_data["promotion_comment"])
        except TemplateSyntaxError as e:
            raise forms.ValidationError(e.message or "")
        return self.cleaned_data["promotion_comment"]


def map_error(error: Error | InvalidRow) -> list[str]:
    match error:
        case Error():
            match error.error:
                case GenePanelSnapshot.DoesNotExist():
                    return [f"Row {error.number}: Panel does not exist"]
                case ValueError():
                    if m := re.match(
                        r"^Field 'id' expected a number but got '([^']+)'.$",
                        str(error.error),
                    ):
                        return [
                            f"Row {error.number}: Field 'Panel ID' expected a number but got '{m.group(1)}'."
                        ]
                case _:
                    return [f"Row {error.number}: Unexpected error"]
        case InvalidRow():
            messages = []
            for attribute, validation_errors in error.error.error_dict.items():
                match attribute:
                    case "panel":
                        messages.append(
                            f"Row {error.number}: Panel ID: {' '.join([' '.join(x) for x in validation_errors])}"
                        )
                    case "promote":
                        messages.append(
                            f"Row {error.number}: Promote: {' '.join([' '.join(x) for x in validation_errors])}"
                        )
                    case _:
                        messages.append(f"Row {error.number}: Unexpected error")
            return messages
    raise ValueError("Invalid error")


class ReleasePanelsImportForm(ImportForm):
    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def clean(self):
        cleaned_data = super().clean()
        resource = ReleasePanelResource(self.instance)
        data = io.TextIOWrapper(cleaned_data["import_file"], encoding="utf-8")
        dataset = tablib.import_set(
            stream=data,
            format=dict(self.fields["format"].choices)[cleaned_data["format"]],
        )
        result = resource.import_data(
            dataset,
            use_transactions=True,
            dry_run=True,
        )

        # Allow the file to be read after this function exits
        # otherwise it will raise this exception:
        # ValueError: I/O operation on closed file.
        data.detach()
        cleaned_data["import_file"].seek(0)

        if result.invalid_rows or result.error_rows or result.base_errors:
            errors = [
                error for error_row in result.error_rows for error in error_row.errors
            ] + result.invalid_rows
            errors = [base_error.error for base_error in result.base_errors] + [
                forms.ValidationError(error)
                for messages in map(map_error, errors)
                for error in messages
            ]
            raise forms.ValidationError(errors)

        return cleaned_data

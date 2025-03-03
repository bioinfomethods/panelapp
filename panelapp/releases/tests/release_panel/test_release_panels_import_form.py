from typing import cast

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from import_export.formats.base_formats import CSV

from panels.tests.factories import GenePanelSnapshotFactory
from releases.forms import ReleasePanelsImportForm
from releases.models import (
    Release,
    ReleasePanel,
)
from releases.resources import ReleasePanelResource
from releases.tests.factories import ReleaseFactory


@pytest.mark.django_db
def test_panel_does_not_exist():
    release = cast(Release, ReleaseFactory())

    form = ReleasePanelsImportForm(
        instance=release,
        formats=[CSV],
        resources=[ReleasePanelResource],
        data={"format": "0"},
        files={
            "import_file": SimpleUploadedFile(
                name="import.csv", content=b"Panel ID,Promote\n0,true\n"
            )
        },
    )

    assert not form.is_valid()
    assert form.errors == {"__all__": ["Row 1: Panel does not exist"]}

    assert len(ReleasePanel.objects.all()) == 0


@pytest.mark.django_db
def test_invalid_panel_id():
    release = cast(Release, ReleaseFactory())

    form = ReleasePanelsImportForm(
        instance=release,
        formats=[CSV],
        resources=[ReleasePanelResource],
        data={"format": "0"},
        files={
            "import_file": SimpleUploadedFile(
                name="import.csv", content=b"Panel ID,Promote\none,true\n"
            )
        },
    )

    assert not form.is_valid()
    assert form.errors == {
        "__all__": ["Row 1: Field 'Panel ID' expected a number but got 'one'."]
    }

    assert len(ReleasePanel.objects.all()) == 0


@pytest.mark.django_db
def test_invalid_headers():
    release = cast(Release, ReleaseFactory())

    form = ReleasePanelsImportForm(
        instance=release,
        formats=[CSV],
        resources=[ReleasePanelResource],
        data={"format": "0"},
        files={
            "import_file": SimpleUploadedFile(
                name="import.csv", content=b"invalid,field\n1,true\n"
            )
        },
    )

    assert not form.is_valid()
    assert form.errors == {
        "__all__": [
            "Missing headers: `Panel ID`, `Promote`",
            "Row 1: Panel ID: This field cannot be null.",
            "Row 1: Promote: “None” value must be either True or False.",
        ]
    }

    assert len(ReleasePanel.objects.all()) == 0


@pytest.mark.django_db
def test_invalid_promote_value():
    release = cast(Release, ReleaseFactory())
    gps = GenePanelSnapshotFactory()

    form = ReleasePanelsImportForm(
        instance=release,
        formats=[CSV],
        resources=[ReleasePanelResource],
        data={"format": "0"},
        files={
            "import_file": SimpleUploadedFile(
                name="import.csv",
                content=f"Panel ID,Promote\n{gps.panel.pk},yes\n".encode("utf-8"),
            )
        },
    )

    assert not form.is_valid()
    assert form.errors == {
        "__all__": [
            "Row 1: Promote: `yes` value must be either `true` or `false`.",
        ]
    }

    assert len(ReleasePanel.objects.all()) == 0


@pytest.mark.django_db
def test_duplicates():
    release = cast(Release, ReleaseFactory())
    gps = GenePanelSnapshotFactory()

    content = f"Panel ID,Promote\n{gps.panel.pk},true\n{gps.panel.pk},false\n"
    form = ReleasePanelsImportForm(
        instance=release,
        formats=[CSV],
        resources=[ReleasePanelResource],
        data={"format": "0"},
        files={
            "import_file": SimpleUploadedFile(
                name="import.csv",
                content=content.encode("utf-8"),
            )
        },
    )

    assert not form.is_valid()
    assert form.errors == {
        "__all__": [
            "Row 2: Panel is a duplicate.",
        ]
    }

    assert len(ReleasePanel.objects.all()) == 0

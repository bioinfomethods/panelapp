from datetime import datetime
from typing import cast

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from testfixtures.django import compare

from accounts.models import User
from panels.tests.factories import GenePanelSnapshotFactory
from releases.models import (
    Release,
    ReleasePanel,
)
from releases.tests.factories import (
    ReleaseDeploymentFactory,
    ReleaseFactory,
    ReleasePanelFactory,
)


@pytest.mark.django_db
def test_primary(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory())
    gps = GenePanelSnapshotFactory()

    client.login(username=curator_user.username, password="pass")

    import_file = SimpleUploadedFile(
        name="import.csv",
        content=f"Panel ID,Promote\n{gps.panel.pk},true\n".encode("utf-8"),
        content_type="text/csv",
    )

    res = client.post(
        reverse("releases:releasepanel-import", args=(release.pk,)),
        {"import_file": import_file, "format": "0"},
    )

    assert res.status_code == 302

    compare(
        expected=[ReleasePanel(release=release, panel=gps, promote=True)],
        actual=list(ReleasePanel.objects.all()),
        ignore_fields=["id"],
    )


@pytest.mark.django_db
def test_import_file_source_of_truth(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory())
    ReleasePanelFactory(release=release, promote=True)
    gps = GenePanelSnapshotFactory()

    client.login(username=curator_user.username, password="pass")

    import_file = SimpleUploadedFile(
        name="import.csv",
        content=f"Panel ID,Promote\n{gps.panel.pk},false\n".encode("utf-8"),
        content_type="text/csv",
    )

    res = client.post(
        reverse("releases:releasepanel-import", args=(release.pk,)),
        {"import_file": import_file, "format": "0"},
    )

    assert res.status_code == 302

    compare(
        expected=[ReleasePanel(release=release, panel=gps, promote=False)],
        actual=list(ReleasePanel.objects.all()),
        ignore_fields=["id"],
    )


@pytest.mark.django_db
def test_error(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory())
    gps = GenePanelSnapshotFactory()

    client.login(username=curator_user.username, password="pass")

    import_file = SimpleUploadedFile(
        name="import.csv",
        content=f"Panel ID,Promote\n{gps.panel.pk},yes\n".encode("utf-8"),
        content_type="text/csv",
    )

    res = client.post(
        reverse("releases:releasepanel-import", args=(release.pk,)),
        {"import_file": import_file, "format": "0"},
    )

    assert res.status_code == 200

    assert len(ReleasePanel.objects.all()) == 0


@pytest.mark.django_db
def test_after_deployment(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory())
    gps = GenePanelSnapshotFactory()
    ReleaseDeploymentFactory(release=release, start=datetime.now(), end=datetime.now())

    client.login(username=curator_user.username, password="pass")

    import_file = SimpleUploadedFile(
        name="import.csv",
        content=f"Panel ID,Promote\n{gps.panel.pk},true\n".encode("utf-8"),
        content_type="text/csv",
    )

    res = client.post(
        reverse("releases:releasepanel-import", args=(release.pk,)),
        {"import_file": import_file, "format": "0"},
    )

    assert res.status_code == 400

    assert len(ReleasePanel.objects.all()) == 0

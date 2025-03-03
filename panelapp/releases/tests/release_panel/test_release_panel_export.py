import csv
from datetime import datetime
from io import StringIO
from typing import cast

import pytest
from django.http import StreamingHttpResponse
from django.test import Client
from django.urls import reverse
from testfixtures import SequenceComparison as S
from testfixtures import compare

from accounts.models import User
from panels.tests.factories import HistoricalSnapshotFactory
from releases.models import (
    Release,
    ReleasePanel,
    ReleasePanelDeployment,
)
from releases.tests.factories import (
    ReleaseDeploymentFactory,
    ReleaseFactory,
    ReleasePanelDeploymentFactory,
    ReleasePanelFactory,
)


@pytest.mark.django_db
def test_before_deployment(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory(promotion_comment="Release comment"))
    rp1 = cast(
        ReleasePanel,
        ReleasePanelFactory(
            release=release,
            promote=True,
            panel__major_version=0,
            panel__minor_version=1,
        ),
    )
    rp1.panel.panel.signed_off = HistoricalSnapshotFactory(
        panel=rp1.panel.panel, major_version=0, minor_version=0
    )
    rp1.panel.panel.save()
    rp2 = cast(
        ReleasePanel,
        ReleasePanelFactory(
            release=release,
            promote=False,
            panel__major_version=0,
            panel__minor_version=1,
        ),
    )
    rp2.panel.panel.signed_off = HistoricalSnapshotFactory(
        panel=rp2.panel.panel, major_version=0, minor_version=0
    )
    rp2.panel.panel.save()

    client.login(username=curator_user.username, password="pass")

    res = cast(
        StreamingHttpResponse,
        client.get(reverse("releases:releasepanel-export", args=(release.pk,))),
    )

    assert res.status_code == 200

    content = b"".join(res.streaming_content)  # type: ignore
    reader = csv.DictReader(StringIO(content.decode("utf-8")))

    compare(
        expected=S(
            {
                "Panel ID": str(rp1.panel.panel.pk),
                "Promote": "true",
                "Signed Off (Before)": "0.0",
                "Signed Off (After)": "1.0",
                "Comment (Before)": "",
                "Comment (After)": "Release comment",
            },
            {
                "Panel ID": str(rp2.panel.panel.pk),
                "Promote": "false",
                "Signed Off (Before)": "0.0",
                "Signed Off (After)": "0.1",
                "Comment (Before)": "",
                "Comment (After)": "",
            },
            ordered=False,
        ),
        actual=list(reader),
    )


@pytest.mark.django_db
def test_after_deployment(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory())
    ReleaseDeploymentFactory(release=release, start=datetime.now(), end=datetime.now())
    rpd1 = cast(
        ReleasePanelDeployment,
        ReleasePanelDeploymentFactory(
            release_panel__release=release,
            release_panel__promote=True,
            before__major_version=0,
            before__minor_version=1,
            signed_off_before__major_version=0,
            signed_off_before__minor_version=0,
            comment_before="",
            after__major_version=1,
            after__minor_version=1,
            signed_off_after__major_version=1,
            signed_off_after__minor_version=0,
            comment_after="Release comment",
        ),
    )
    rpd2 = cast(
        ReleasePanelDeployment,
        ReleasePanelDeploymentFactory(
            release_panel__release=release,
            release_panel__promote=False,
            before__major_version=0,
            before__minor_version=1,
            signed_off_before__major_version=0,
            signed_off_before__minor_version=0,
            after__major_version=0,
            after__minor_version=3,
            signed_off_after__major_version=0,
            signed_off_after__minor_version=1,
        ),
    )

    client.login(username=curator_user.username, password="pass")

    res = cast(
        StreamingHttpResponse,
        client.get(reverse("releases:releasepanel-export", args=(release.pk,))),
    )

    assert res.status_code == 200

    content = b"".join(res.streaming_content)  # type: ignore
    reader = csv.DictReader(StringIO(content.decode("utf-8")))

    compare(
        expected=S(
            {
                "Panel ID": str(rpd1.release_panel.panel.panel.pk),
                "Promote": "true",
                "Signed Off (Before)": "0.0",
                "Signed Off (After)": "1.0",
                "Comment (Before)": "",
                "Comment (After)": "Release comment",
            },
            {
                "Panel ID": str(rpd2.release_panel.panel.panel.pk),
                "Promote": "false",
                "Signed Off (Before)": "0.0",
                "Signed Off (After)": "0.1",
                "Comment (Before)": "",
                "Comment (After)": "",
            },
            ordered=False,
        ),
        actual=list(reader),
    )

from typing import cast

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from releases.models import (
    Release,
    ReleasePanel,
)
from releases.tests.factories import (
    ReleaseFactory,
    ReleasePanelFactory,
)


@pytest.mark.django_db
def test_list(client: Client, curator_user: User):
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
    rp2 = cast(
        ReleasePanel,
        ReleasePanelFactory(
            release=release,
            promote=False,
            panel__major_version=0,
            panel__minor_version=1,
        ),
    )

    client.login(username=curator_user.username, password="pass")

    res = client.get(reverse("releases:releasepanel-list", args=(release.pk,)))

    assert res.status_code == 200

    content = res.content.decode("utf-8")

    assert rp1.panel.panel.name in content
    assert rp2.panel.panel.name in content

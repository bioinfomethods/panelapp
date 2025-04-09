import uuid
from typing import cast

import pytest
from testfixtures import Comparison as Cmp
from testfixtures import SequenceComparison as SeqCmp
from testfixtures.django import compare

from accounts.models import User
from panels.models import (
    GenePanel,
    GenePanelSnapshot,
    HistoricalSnapshot,
)
from panels.tests.factories import HistoricalSnapshotFactory
from releases.models import (
    Release,
    ReleasePanel,
)
from releases.tasks import deploy_release
from releases.tests.factories import (
    ReleaseDeploymentFactory,
    ReleaseFactory,
    ReleasePanelFactory,
)


@pytest.mark.django_db
def test_primary(curator_user: User):
    release = cast(Release, ReleaseFactory(promotion_comment="Release comment"))
    panel1_name = f"panel1-{str(uuid.uuid4())}"
    panel2_name = f"panel2-{str(uuid.uuid4())}"
    rp1 = cast(
        ReleasePanel,
        ReleasePanelFactory(
            release=release,
            promote=True,
            panel__major_version=0,
            panel__minor_version=1,
            panel__version_comment="",
            panel__panel__name=panel1_name,
            panel__panel__status="public",
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
            panel__version_comment="",
            panel__panel__name=panel2_name,
            panel__panel__status="internal",
        ),
    )
    rp2.panel.panel.signed_off = HistoricalSnapshotFactory(
        panel=rp2.panel.panel, major_version=0, minor_version=0
    )
    rp2.panel.panel.save()

    ReleaseDeploymentFactory(release=release)

    deploy_release(pk=release.pk, user_pk=curator_user.pk)

    compare(
        actual=list(GenePanelSnapshot.objects.all()),
        expected=SeqCmp(
            Cmp(
                GenePanelSnapshot,
                major_version=1,
                minor_version=1,
                version_comment="Release comment",
                panel=Cmp(
                    GenePanel,
                    name=panel1_name,
                    status="public",
                    signed_off=Cmp(
                        HistoricalSnapshot,
                        major_version=1,
                        minor_version=0,
                        partial=True,
                    ),
                    partial=True,
                ),
                partial=True,
            ),
            Cmp(
                GenePanelSnapshot,
                major_version=0,
                minor_version=2,
                version_comment="",
                panel=Cmp(
                    GenePanel,
                    name=panel2_name,
                    status="internal",
                    signed_off=Cmp(
                        HistoricalSnapshot,
                        major_version=0,
                        minor_version=1,
                        partial=True,
                    ),
                    partial=True,
                ),
                partial=True,
            ),
            ordered=False,
        ),
    )


@pytest.mark.django_db
def test_release_panel_deploy_failure(mocker, curator_user: User):
    release = cast(Release, ReleaseFactory(promotion_comment="Release comment"))
    panel1_name = f"panel1-{str(uuid.uuid4())}"
    panel2_name = f"panel2-{str(uuid.uuid4())}"
    rp1 = cast(
        ReleasePanel,
        ReleasePanelFactory(
            release=release,
            promote=True,
            panel__major_version=0,
            panel__minor_version=1,
            panel__version_comment="",
            panel__panel__name=panel1_name,
            panel__panel__status="public",
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
            panel__version_comment="",
            panel__panel__name=panel2_name,
            panel__panel__status="internal",
        ),
    )
    rp2.panel.panel.signed_off = HistoricalSnapshotFactory(
        panel=rp2.panel.panel, major_version=0, minor_version=0
    )
    rp2.panel.panel.save()

    ReleaseDeploymentFactory(release=release)

    mocker.patch.object(ReleasePanel, "deploy", side_effect=Exception)

    with pytest.raises(Exception):
        deploy_release(pk=release.pk, user_pk=curator_user.pk)

    compare(
        actual=list(GenePanelSnapshot.objects.all()),
        expected=SeqCmp(
            Cmp(
                GenePanelSnapshot,
                major_version=0,
                minor_version=1,
                version_comment="",
                panel=Cmp(
                    GenePanel,
                    name=panel1_name,
                    status="public",
                    signed_off=Cmp(
                        HistoricalSnapshot,
                        major_version=0,
                        minor_version=0,
                        partial=True,
                    ),
                    partial=True,
                ),
                partial=True,
            ),
            Cmp(
                GenePanelSnapshot,
                major_version=0,
                minor_version=1,
                version_comment="",
                panel=Cmp(
                    GenePanel,
                    name=panel2_name,
                    status="internal",
                    signed_off=Cmp(
                        HistoricalSnapshot,
                        major_version=0,
                        minor_version=0,
                        partial=True,
                    ),
                    partial=True,
                ),
                partial=True,
            ),
            ordered=False,
        ),
    )

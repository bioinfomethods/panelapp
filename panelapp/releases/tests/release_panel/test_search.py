from typing import cast

import pytest
from testfixtures.django import compare

from panels.models.genepanel import GenePanel
from panels.models.panel_types import PanelType
from panels.tests.factories import (
    GenePanelFactory,
    PanelTypeFactory,
)
from releases.models import (
    ReleasePanel,
    ReleasePanelQuerySet,
)
from releases.tests.factories import (
    ReleaseFactory,
    ReleasePanelFactory,
)


@pytest.mark.django_db
def test_multiple_types():
    release = ReleaseFactory()
    type1 = cast(PanelType, PanelTypeFactory())
    type2 = cast(PanelType, PanelTypeFactory())
    panel = cast(GenePanel, GenePanelFactory())
    panel.types.add(type1, type2)
    release_panel = cast(
        ReleasePanel, ReleasePanelFactory(release=release, panel__panel=panel)
    )

    actual = list(
        cast(ReleasePanelQuerySet, ReleasePanel.objects).search(
            search=None, statuses=None, types=[type1.slug, type2.slug], order_by=None
        )
    )

    compare(expected=[release_panel], actual=actual)

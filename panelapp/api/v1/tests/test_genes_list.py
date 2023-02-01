from datetime import datetime
from typing import (
    List,
    Tuple,
)

import pytest
from pytest_cases import (
    fixture,
    parametrize_with_cases,
)
from rest_framework.pagination import PageNumberPagination

from panels.models import GenePanel
from panels.models.genepanelentrysnapshot import GenePanelEntrySnapshot
from panels.tests.factories import (
    GenePanelEntrySnapshotFactory,
    GenePanelSnapshotFactory,
)


def case_page_size_3_panels_5_genes_5(mocker) -> List[GenePanelEntrySnapshot]:
    # Django Rest Framework uses a class attribute to store the settings.PAGE_SIZE
    # value so this is only evaluated once. This means we cannot use this to change
    # the page size independently for each test using settings.

    mocker.patch.object(PageNumberPagination, "page_size", 3)

    entries = []
    for _ in range(5):
        panel_snapshot = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        entries.extend(
            GenePanelEntrySnapshotFactory.create_batch(5, panel=panel_snapshot)
        )

    return entries


def case_page_size_4_panels_5_genes_5(mocker) -> List[GenePanelEntrySnapshot]:
    mocker.patch.object(PageNumberPagination, "page_size", 4)

    entries = []
    for _ in range(5):
        panel_snapshot = GenePanelSnapshotFactory(panel__status=GenePanel.STATUS.public)
        entries.extend(
            GenePanelEntrySnapshotFactory.create_batch(5, panel=panel_snapshot)
        )

    return entries


@pytest.mark.django_db
@pytest.mark.xfail(reason="KMDS-1959: reported bug", strict=True, raises=AssertionError)
@parametrize_with_cases(["entries"], cases=".")
def test_consistent_paging(entries: List[GenePanelEntrySnapshot], client):
    def fetch_genes():
        results = []
        url = "/api/v1/genes/"
        while url is not None:
            resp = client.get(url)
            body = resp.json()
            results.extend(body["results"])
            url = body["next"]
        return results

    genes1 = fetch_genes()
    genes2 = fetch_genes()

    assert genes1 == genes2

    genes1_unique = {(x["panel"]["id"], x["entity_name"]) for x in genes1}
    genes2_unique = {(x["panel"]["id"], x["entity_name"]) for x in genes2}

    assert genes1_unique == genes2_unique

    assert len(genes1_unique) == len(genes2_unique) == len(entries)

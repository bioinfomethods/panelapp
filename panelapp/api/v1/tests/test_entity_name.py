from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from pytest_cases import parametrize_with_cases

from panels.models import (
    STR,
    GenePanelEntrySnapshot,
    Region,
)
from panels.tests.factories import (
    GenePanelEntrySnapshotFactory,
    RegionFactory,
    STRFactory,
)


@pytest.fixture(params=["NAME", "NAME.1"])
def entity_name(request) -> str:
    return request.param


@pytest.fixture
def gene(entity_name: str) -> GenePanelEntrySnapshot:
    return GenePanelEntrySnapshotFactory(
        panel__panel__status="public", gene_core__gene_symbol=entity_name
    )


@pytest.fixture
def str_(entity_name: str) -> STR:
    return STRFactory(panel__panel__status="public", name=entity_name)


@pytest.fixture
def region(entity_name: str) -> Region:
    return RegionFactory(panel__panel__status="public", name=entity_name)


@pytest.mark.usefixtures("gene")
def case_genes_detail(entity_name: str) -> tuple[str, list[Any]]:
    return ("genes-detail", [entity_name])


def case_genes_evaluations_list(
    gene: GenePanelEntrySnapshot, entity_name: str
) -> tuple[str, list[Any]]:
    return ("genes-evaluations-list", [gene.panel.panel.pk, entity_name])


@pytest.mark.usefixtures("str_")
def case_strs_detail(entity_name: str) -> tuple[str, list[Any]]:
    return ("strs-detail", [entity_name])


def case_strs_evaluations_list(str_: STR, entity_name: str) -> tuple[str, list[Any]]:
    return ("strs-evaluations-list", [str_.panel.panel.pk, entity_name])


@pytest.mark.usefixtures("region")
def case_regions_detail(entity_name: str) -> tuple[str, list[Any]]:
    return ("regions-detail", [entity_name])


def case_regions_evaluations_list(
    region: Region, entity_name: str
) -> tuple[str, list[Any]]:
    return ("regions-evaluations-list", [region.panel.panel.pk, entity_name])


@parametrize_with_cases(["view", "args"], cases=".")
@pytest.mark.django_db
def test_response_ok(client: Client, view: str, args: tuple[Any]):
    url = reverse(f"api:v1:{view}", args=args)

    res = client.get(url)

    assert res.status_code == 200

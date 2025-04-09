import pytest

from panels.exceptions import (
    GenesDoNotExist,
    ImportException,
)
from panels.models.uploaded_panel_list import check_genes
from panels.tests.factories import GeneFactory

LINES = ["ABC", "gene", "BCA"]


@pytest.mark.django_db
def test_check_genes_missing():
    with pytest.raises(GenesDoNotExist):
        check_genes(LINES)


@pytest.mark.django_db
def test_check_genes_mismatch():
    GeneFactory(gene_symbol="ABC")

    with pytest.raises(ImportException):
        check_genes(LINES)

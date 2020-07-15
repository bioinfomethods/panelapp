import pytest

from panels.models.import_tools import get_missing_genes
from panels.tests.factories import GeneFactory


@pytest.mark.django_db
def test_no_missing_genes():
    GeneFactory(gene_symbol="ABC")
    missing_genes = get_missing_genes({"ABC"})
    assert len(missing_genes) == 0


@pytest.mark.django_db
def test_missing_genes():
    GeneFactory(gene_symbol="ABC")
    missing_genes = get_missing_genes({"ABCD"})
    assert len(missing_genes) == 1

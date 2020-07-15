from unittest import mock

import pytest
import responses
from django.core import mail

from panels.models import GenePanel
from panels.tasks.moi_checks import (
    IncorrectMoiGene,
    get_chromosome,
    get_csv_content,
    get_genes,
    has_non_empty_moi,
    moi_check,
    moi_check_chr_x,
    moi_check_is_empty,
    moi_check_other,
    multiple_moi_genes,
    notify_panelapp_curators,
    retrieve_omim_moi,
)
from panels.tests.factories import (
    GeneFactory,
    GenePanelEntrySnapshotFactory,
    GenePanelSnapshotFactory,
)

OMIM_RESPONSE_SUCCESS = {
    "omim": {
        "entryList": [
            {
                "entry": {
                    "geneMap": {
                        "phenotypeMapList": [
                            {
                                "phenotypeMap": {
                                    "phenotypeInheritance": "X-linked recessive"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }
}


@pytest.fixture
def incorrect_moi():
    return IncorrectMoiGene(
        gene_name="ABC",
        panel_name="panel 1",
        panel_id=1,
        moi="moi1",
        phenotypes="a;b;c",
        publications="1;2;3",
        message="message",
    )


@pytest.mark.django_db
@responses.activate
def test_moi_check(settings):
    settings.OMIM_API_KEY = "TEST-KEY"
    responses.add(
        responses.GET,
        f"https://api.omim.org/api/entry?mimNumber=123456&include=geneMap&include=externalLinks&format=json&apiKey={settings.OMIM_API_KEY}",
        json=OMIM_RESPONSE_SUCCESS,
        status=200,
    )
    gene = GeneFactory(omim_gene=["123456"])
    gps = GenePanelSnapshotFactory(
        panel__status=GenePanel.STATUS.public, major_version=2
    )
    GenePanelEntrySnapshotFactory.create_batch(2, panel=gps, saved_gel_status=3)
    GenePanelEntrySnapshotFactory.create(
        gene_core=gene,
        panel=gps,
        saved_gel_status=3,
        moi="BIALLELIC, autosomal or pseudoautosomal",
    )

    with mock.patch(
        "panels.tasks.moi_checks.get_csv_content", return_value="csv content"
    ):
        moi_check()

    assert mail.outbox[0].attachments == [
        ("incorrect_moi.csv", "csv content", "text/csv")
    ]


def test_incorrect_moi_gene_row(incorrect_moi):
    assert incorrect_moi.row == [
        "ABC",
        "panel 1",
        1,
        "moi1",
        "a;b;c",
        "1;2;3",
        "message",
    ]


@pytest.mark.django_db
def test_get_genes():
    public_gps = GenePanelSnapshotFactory(major_version=1, panel__status="public")
    internal_gps = GenePanelSnapshotFactory(major_version=1, panel__status="internal")
    public_green_genes = GenePanelEntrySnapshotFactory(
        panel=public_gps, saved_gel_status=3
    )
    # internal green genes
    GenePanelEntrySnapshotFactory(panel=internal_gps, saved_gel_status=3)
    # public red genes
    GenePanelEntrySnapshotFactory(panel=public_gps, saved_gel_status=1)
    # internal red genes
    GenePanelEntrySnapshotFactory(panel=internal_gps, saved_gel_status=1)

    genes = list(get_genes())

    assert len(genes) == 1
    assert genes == [public_green_genes]


def test_notify_panelapp_curators():
    notify_panelapp_curators("csv content")

    assert mail.outbox[0].attachments == [
        ("incorrect_moi.csv", "csv content", "text/csv")
    ]


def test_get_csv_content(incorrect_moi):
    outcome = "gene,panel,panel_id,moi,phenotypes,publications,message\nABC,panel 1,1,moi1,a;b;c,1;2;3,message\n"
    res = get_csv_content([incorrect_moi])
    assert res == outcome


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,error",
    [
        ("", True),
        ("Unknown", True),
        ("MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", False),
    ],
)
def test_moi_is_empty(moi, error):
    gps = GenePanelSnapshotFactory.build()
    gene = GenePanelEntrySnapshotFactory.build(panel=gps, moi=moi)

    result = moi_check_is_empty(gene)
    assert bool(result) is error


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,chromosome,error",
    [
        ("Other - please specifiy in evaluation comments", "X", True),
        ("Other - please specifiy in evaluation comments", "Y", False),
    ],
)
def test_moi_other(moi, chromosome, error):
    gps = GenePanelSnapshotFactory.build()
    gene = GenePanelEntrySnapshotFactory.build(panel=gps, moi=moi)

    with mock.patch("panels.tasks.moi_checks.get_chromosome", return_value=chromosome):
        result = moi_check_other(gene)

    assert bool(result) is error


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,chromosome,error",
    [
        (
            "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
            "X",
            False,
        ),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            "X",
            False,
        ),
        ("MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", "Y", False),
        ("MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", "X", True),
    ],
)
def test_moi_chr_x(moi, chromosome, error):
    gps = GenePanelSnapshotFactory.build()
    gene = GenePanelEntrySnapshotFactory.build(panel=gps, moi=moi)

    with mock.patch("panels.tasks.moi_checks.get_chromosome", return_value=chromosome):
        result = moi_check_chr_x(gene)

    assert bool(result) is error


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi_1,moi_2,count",
    [
        ("A", "A", 0),
        ("A", "B", 1),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", 0),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown", 0),
    ],
)
def test_multiple_moi_genes(moi_1, moi_2, count):
    """Get genes where gene MOI has different values except MONOALLELIC"""

    gene = {"gene_symbol": "GENE1"}
    gps_1 = GenePanelSnapshotFactory.build()
    gps_2 = GenePanelSnapshotFactory.build()
    gene_1 = GenePanelEntrySnapshotFactory.build(panel=gps_1, gene=gene, moi=moi_1)
    gene_2 = GenePanelEntrySnapshotFactory.build(panel=gps_2, gene=gene, moi=moi_2)
    gene_3 = GenePanelEntrySnapshotFactory.build(panel=gps_1, gene=gene, moi=moi_2)

    multiple_moi = list(multiple_moi_genes([gene_1, gene_2, gene_3]))

    assert count == len(multiple_moi)


@pytest.mark.parametrize(
    "moi,result", [("", False), ("Unknown", False), ("Some val", True),],
)
def test_non_empty(moi, result):
    assert result == has_non_empty_moi(moi)


@pytest.mark.django_db
def test_get_chromosome():
    gene = GenePanelEntrySnapshotFactory()
    gene.gene = {"ensembl_genes": {"GRch37": {"38": {"location": "1:123-234"}}}}

    assert "1" == get_chromosome(gene)


@responses.activate
def test_retrieve_omim_data(settings):
    settings.OMIM_API_KEY = "TEST-KEY"

    omim_id = 123456

    responses.add(
        responses.GET,
        f"https://api.omim.org/api/entry?mimNumber={omim_id}&include=geneMap&include=externalLinks&format=json&apiKey={settings.OMIM_API_KEY}",
        json=OMIM_RESPONSE_SUCCESS,
        status=200,
    )

    moi = retrieve_omim_moi(omim_id)

    assert "X-linked recessive" in moi

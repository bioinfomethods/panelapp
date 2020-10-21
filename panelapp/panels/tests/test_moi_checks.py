from unittest import mock

import pytest
import responses
from django.core import mail
from django.utils import timezone

from panels.models import GenePanel
from panels.tasks.moi_checks import (
    CheckType,
    IncorrectMoiGene,
    get_chromosome,
    get_csv_content,
    get_genes,
    get_unique_moi_genes,
    has_non_empty_moi,
    moi_check,
    moi_check_chr_x,
    moi_check_chr_y,
    moi_check_is_empty,
    moi_check_mt,
    moi_check_non_standard,
    moi_check_omim,
    moi_check_other,
    multiple_moi_genes,
    notify_panelapp_curators,
    process_multiple_moi_dict,
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
        message="message",
        check_type=CheckType.VALUE_NOT_ALLOWED.value,
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
    now = timezone.now().strftime("%Y-%m-%d")

    with mock.patch(
        "panels.tasks.moi_checks.get_csv_content", return_value="csv content"
    ):
        moi_check()

    assert mail.outbox[0].attachments == [
        (f"incorrect_moi_{now}.csv", "csv content", "text/csv")
    ]


def test_incorrect_moi_gene_row(incorrect_moi):
    assert incorrect_moi.row == [
        CheckType.VALUE_NOT_ALLOWED.value,
        "ABC",
        "panel 1",
        1,
        "moi1",
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
    now = timezone.now().strftime("%Y-%m-%d")
    notify_panelapp_curators("csv content")

    assert mail.outbox[0].attachments == [
        (f"incorrect_moi_{now}.csv", "csv content", "text/csv")
    ]


def test_get_csv_content(incorrect_moi):
    outcome = "check_type,gene,panel,panel_id,moi,message\nMOI Not Allowed Values,ABC,panel 1,1,moi1,message\n"
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
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,chromosome,error",
    [
        ("Other", "X", True),
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
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,chromosome,error",
    [
        ("Other", "MT", True),
        ("MITOCHONDRIAL", "7", True),
        ("MITOCHONDRIAL", "MT", False),
    ],
)
def test_moi_mt(moi, chromosome, error):
    gps = GenePanelSnapshotFactory.build()
    gene = GenePanelEntrySnapshotFactory.build(panel=gps, moi=moi)

    with mock.patch("panels.tasks.moi_checks.get_chromosome", return_value=chromosome):
        result = moi_check_mt(gene)

    assert bool(result) is error
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


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
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            "3",
            True,
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
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,chromosome,error",
    [
        ("Other", "Y", False,),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            "Y",
            True,
        ),
    ],
)
def test_moi_chr_y(moi, chromosome, error):
    gps = GenePanelSnapshotFactory.build()
    gene = GenePanelEntrySnapshotFactory.build(panel=gps, moi=moi)

    with mock.patch("panels.tasks.moi_checks.get_chromosome", return_value=chromosome):
        result = moi_check_chr_y(gene)

    assert bool(result) is error
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi_1,moi_2,count",
    [
        ("A", "A", 0),
        ("A", "B", 2),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", 2),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown", 2),
        (
            "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
            "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
            0,
        ),
    ],
)
def test_multiple_moi_genes(moi_1, moi_2, count):
    """Get genes where gene MOI has different values

    MOI A (on panel PA) will be compared against other MOI and panels, sorted by
    panel_id. Instead of 6 Incorrect MOI we should get just 2, as the others are
    duplicates.
    """

    gene = {"gene_symbol": "GENE1"}
    gps_1 = GenePanelSnapshotFactory(level4title__name="PA")
    gps_2 = GenePanelSnapshotFactory(level4title__name="PB")
    gps_3 = GenePanelSnapshotFactory(level4title__name="PC")
    gene_1 = GenePanelEntrySnapshotFactory(panel=gps_1, gene=gene, moi=moi_1)
    gene_2 = GenePanelEntrySnapshotFactory(panel=gps_2, gene=gene, moi=moi_2)
    gene_3 = GenePanelEntrySnapshotFactory(panel=gps_3, gene=gene, moi=moi_2)

    result = multiple_moi_genes([gene_1, gene_2, gene_3])

    assert count == len(result)
    if count:
        assert {r.check_type for r in result} == {CheckType.ACROSS_PANELS_CHECKS.value}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi_1,moi_2,count",
    [
        ("A", "A", 0),
        ("A", "B", 1),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", 1),
        ("A", "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown", 1),
    ],
)
def test_get_unique_moi_genes(moi_1, moi_2, count):
    """Get genes where gene MOI has different values"""

    gene = {"gene_symbol": "GENE1"}
    gps_1 = GenePanelSnapshotFactory()
    gps_2 = GenePanelSnapshotFactory()
    gene_1 = GenePanelEntrySnapshotFactory(panel=gps_1, gene=gene, moi=moi_1)
    gene_2 = GenePanelEntrySnapshotFactory(panel=gps_2, gene=gene, moi=moi_2)
    gene_3 = GenePanelEntrySnapshotFactory(panel=gps_1, gene=gene, moi=moi_2)

    multiple_moi = get_unique_moi_genes([gene_1, gene_2, gene_3])

    assert count == len(multiple_moi)

    if count:
        assert gene_1.moi in multiple_moi["GENE1"]["moi"]
        assert gene_1 in multiple_moi["GENE1"]["gpes"]
        assert gene_3.moi in multiple_moi["GENE1"]["moi"]
        assert gene_2 in multiple_moi["GENE1"]["gpes"]
        assert gene_3 in multiple_moi["GENE1"]["gpes"]


@pytest.mark.django_db
def test_process_multiple_moi():
    gene = {"gene_symbol": "GENE1"}
    gene_1 = GenePanelEntrySnapshotFactory(gene=gene, moi="A")
    gene_2 = GenePanelEntrySnapshotFactory(gene=gene, moi="B")
    gene_3 = GenePanelEntrySnapshotFactory(gene=gene, moi="C")
    gene_4 = GenePanelEntrySnapshotFactory(gene=gene, moi="D")
    gene_5 = GenePanelEntrySnapshotFactory(gene=gene, moi="E")

    input_dict = {
        "GENE1": {
            "gpes": {gene_1, gene_2, gene_3, gene_4, gene_5},
            "moi": {"A", "B", "C", "D", "E"},
        }
    }

    res = process_multiple_moi_dict(input_dict)

    # (Pdb++) for r in res: print(r.panel, r.moi, r.message)
    # Panel1 v0.0 A Is B on Panel2 v0.0
    # Panel1 v0.0 A Is C on Panel3 v0.0
    # Panel1 v0.0 A Is D on Panel4 v0.0
    # Panel1 v0.0 A Is E on Panel5 v0.0
    # Panel2 v0.0 B Is C on Panel3 v0.0
    # Panel2 v0.0 B Is D on Panel4 v0.0
    # Panel2 v0.0 B Is E on Panel5 v0.0
    # Panel3 v0.0 C Is D on Panel4 v0.0
    # Panel3 v0.0 C Is E on Panel5 v0.0
    # Panel4 v0.0 D Is E on Panel5 v0.0

    assert len(res) == 10
    assert {r.check_type for r in res} == {CheckType.ACROSS_PANELS_CHECKS.value}


@pytest.mark.django_db
def test_process_multiple_moi_exclude_monoallelic():
    # genes with MONOALLELIC... moi shouldn't be reported as they are treated the same
    # by the pipeline

    gene = {"gene_symbol": "GENE1"}
    gene_1 = GenePanelEntrySnapshotFactory(
        gene=gene, moi="MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted"
    )
    gene_2 = GenePanelEntrySnapshotFactory(
        gene=gene,
        moi="MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
    )
    gene_3 = GenePanelEntrySnapshotFactory(gene=gene, moi="C")

    input_dict = {
        "GENE1": {
            "gpes": {gene_1, gene_2, gene_3},
            "moi": {
                "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
                "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
                "C",
            },
        }
    }

    res = process_multiple_moi_dict(input_dict)

    # (Pdb++) for r in res: print(r.panel, r.moi, r.message)
    # Panel1 v0.0 MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted Is C on Panel3 v0.0
    # Panel2 v0.0 MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown Is C on Panel3 v0.0
    assert len(res) == 2
    assert {r.check_type for r in res} == {CheckType.ACROSS_PANELS_CHECKS.value}


@pytest.mark.parametrize(
    "moi,result", [("", False), ("Unknown", False), ("Some val", True),],
)
def test_non_empty(moi, result):
    assert result == has_non_empty_moi(moi)


@pytest.mark.django_db
def test_get_chromosome():
    gene = GenePanelEntrySnapshotFactory()
    gene.gene = {
        "alias": ["hWNT5A"],
        "biotype": "protein_coding",
        "hgnc_id": "HGNC:12784",
        "gene_name": "Wnt family member 5A",
        "omim_gene": ["164975"],
        "alias_name": ["WNT-5A protein"],
        "gene_symbol": "WNT5A",
        "hgnc_symbol": "WNT5A",
        "hgnc_release": "2017-11-03",
        "ensembl_genes": {
            "GRch37": {
                "82": {
                    "location": "3:55499743-55523973",
                    "ensembl_id": "ENSG00000114251",
                }
            },
            "GRch38": {
                "90": {
                    "location": "3:55465715-55490539",
                    "ensembl_id": "ENSG00000114251",
                }
            },
        },
        "hgnc_date_symbol_changed": "1993-07-06",
    }

    assert "3" == get_chromosome(gene)


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "moi,error",
    [
        ("Unknown", False),
        ("MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted", False),
        ("Something", True),
    ],
)
def test_moi_check_non_standard(moi, error):
    gene = GenePanelEntrySnapshotFactory.build(moi=moi)

    result = moi_check_non_standard(gene)
    assert bool(result) is error
    if result:
        assert result.check_type == CheckType.VALUE_NOT_ALLOWED.value


@pytest.mark.django_db
@mock.patch("panels.tasks.moi_checks.retrieve_omim_moi")
@pytest.mark.parametrize(
    "moi,omim_values,error",
    [
        ("MONOALLELIC,", {"Autosomal dominant"}, False),
        ("BOTH", {"Autosomal recessive", "Autosomal dominant"}, False),
        ("MONOALLELIC,", {"Autosomal recessive"}, True),
        ("MONOALLELIC,", {"Autosomal recessive", "Autosomal dominant"}, True),
        ("BOTH", {"Autosomal dominant", "XLD"}, True),
        ("BOTH", {"Autosomal dominant",}, True),
        ("BOTH", {"AD/AR",}, False),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            {"Autosomal dominant", "XLD"},
            True,
        ),
        (
            "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
            {"XLR"},
            False,
        ),
        (
            "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
            {"XLD"},
            True,
        ),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            {"XLD"},
            False,
        ),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            {"XLR"},
            True,
        ),
        (
            "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            {"XLD", "XLR"},
            True,
        ),
    ],
)
def test_omim_check_multiple(retrieve_omim_mock, moi, omim_values, error):
    # Report if OMIM MOI links to multiple MOI groups in PanelApp

    retrieve_omim_mock.return_value = omim_values
    gene = GenePanelEntrySnapshotFactory.build(moi=moi, gene={"omim_gene": ["164975"],})

    res = moi_check_omim(gene)
    assert bool(res) is error

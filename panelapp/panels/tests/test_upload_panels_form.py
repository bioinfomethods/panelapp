from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from psycopg2.extras import NumericRange

from accounts.models import Reviewer
from accounts.tests.factories import UserFactory
from panels.forms.uploads import UploadPanelsForm
from panels.tests.factories import STRFactory


@pytest.mark.django_db
def test_process_file_upload_two_sources():
    bilbo = UserFactory(username="bilbo", reviewer__user_type=Reviewer.TYPES.GEL)
    ar_cag = STRFactory(
        name="AR_CAG",
        gene_core__gene_symbol="AR",
        panel__panel__name="Amyotrophic lateral sclerosis/motor neuron disease",
        chromosome="X",
        position_38=NumericRange(67545316, 67545383),
        position_37=NumericRange(66765160, 66765225),
        repeated_sequence="CAG",
        normal_repeats=35,
        pathogenic_repeats=38,
    )

    data = b"""Entity Name	Entity type	Gene Symbol	Sources(; separated)	Level4	Level3	Level2	Model_Of_Inheritance	Phenotypes	Omim	Orphanet	HPO	Publications	Description	Flagged	GEL_Status	UserRatings_Green_amber_red	version	ready	Mode of pathogenicity	EnsemblId(GRch37)	EnsemblId(GRch38)	HGNC	Position Chromosome	Position GRCh37 Start	Position GRCh37 End	Position GRCh38 Start	Position GRCh38 End	STR Repeated Sequence	STR Normal Repeats	STR Pathogenic Repeats	Region Haploinsufficiency Score	Region Triplosensitivity Score	Region Required Overlap Percentage	Region Variant Type	Region Verbose Name
AR_CAG	str	AR	NHS GMS;Expert Review Green	Amyotrophic lateral sclerosis/motor neuron disease			"X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)"																X	66765160	66765225	67545316	67545383	CAG	35	38					"""
    buffer = BytesIO(data)
    file_ = SimpleUploadedFile("test.tsv", buffer.read())
    form = UploadPanelsForm(files={"panel_list": file_})

    form.full_clean()
    assert form.errors == {}

    form.process_file(user=bilbo)

    ar_cag.refresh_from_db()

    assert len(ar_cag.evidence.all()) == 2

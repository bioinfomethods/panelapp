from io import BytesIO

import pytest
from django.test.client import Client
from django.urls import reverse_lazy
from psycopg2.extras import NumericRange

from accounts.models import Reviewer
from accounts.tests.factories import UserFactory
from panels.tests.factories import STRFactory


@pytest.mark.django_db
@pytest.mark.xfail(
    reason="PANELAPP-799: reported bug", strict=True, raises=AssertionError
)
def test_regression_panelapp_799(client: Client):
    """GEL Curator becomes Reviewer after giving the STR AR_CAG a Green rating"""
    bilbo = UserFactory(username="bilbo", reviewer__user_type=Reviewer.TYPES.GEL)
    UserFactory(username="frodo", reviewer__user_type=Reviewer.TYPES.GEL)
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

    client.login(username="bilbo", password="pass")

    url = reverse_lazy(
        "panels:update_entity_rating",
        kwargs={
            "pk": ar_cag.panel.panel.pk,
            "entity_type": "str",
            "entity_name": "AR_CAG",
        },
    )

    # Bilbo uses the web interface to directly change the entity rating
    client.post(
        url, {"comment": "testing", "status": 3}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    ar_cag.refresh_from_db()

    client.logout()

    # Bilbo leaves GEL and has their GEL status revoked
    # making them a Reviewer.
    bilbo.reviewer.user_type = Reviewer.TYPES.REVIEWER
    bilbo.reviewer.save()

    client.login(username="frodo", password="pass")

    data = b"""Entity Name	Entity type	Gene Symbol	Sources(; separated)	Level4	Level3	Level2	Model_Of_Inheritance	Phenotypes	Omim	Orphanet	HPO	Publications	Description	Flagged	GEL_Status	UserRatings_Green_amber_red	version	ready	Mode of pathogenicity	EnsemblId(GRch37)	EnsemblId(GRch38)	HGNC	Position Chromosome	Position GRCh37 Start	Position GRCh37 End	Position GRCh38 Start	Position GRCh38 End	STR Repeated Sequence	STR Normal Repeats	STR Pathogenic Repeats	Region Haploinsufficiency Score	Region Triplosensitivity Score	Region Required Overlap Percentage	Region Variant Type	Region Verbose Name
AR_CAG	str	AR	NHS GMS;Expert Review Green	Amyotrophic lateral sclerosis/motor neuron disease			"X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)"																X	66765160	66765225	67545316	67545383	CAG	35	38					"""

    url = reverse_lazy("panels:upload_panels")

    buffer = BytesIO(data)

    # Frodo attempts to maintain AR_CAG rating as Green as part of an
    # upload by including the Expert Review Green source.
    client.post(url, {"panel_list": buffer})

    ar_cag.refresh_from_db()

    assert ar_cag.saved_gel_status == 3

from typing import (
    List,
    Tuple,
)

import pytest
from pytest_cases import parametrize_with_cases

from accounts.models import Reviewer
from panels.models.strs import STR
from panels.tests.factories import (
    EvidenceFactory,
    STRFactory,
)


def case_latest_expert_review_green() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Expert Review Red",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Amber",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Green",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 3


def case_latest_expert_review_amber() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Expert Review Red",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Green",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Amber",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 2


def case_latest_expert_review_red() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Expert Review Green",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Amber",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Expert Review Red",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 1


@pytest.mark.parametrize(
    "user_type, expected",
    [
        [Reviewer.TYPES.GEL, 3],
        [Reviewer.TYPES.REVIEWER, 0],
        [Reviewer.TYPES.EXTERNAL, 0],
    ],
)
def case_expert_source_green_reviewer_type(
    user_type: str, expected: int
) -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Expert Review Green",
                rating=5,
                reviewer__user_type=user_type,
            )
        ]
    )
    return str_, expected


def case_flagged_expert_review_green() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        flagged=True,
        evidence=[
            EvidenceFactory(
                name="Expert Review Green",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            )
        ],
    )
    return str_, 0


def case_one_high_confidence_source() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Radboud University Medical Center, Nijmegen",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            )
        ]
    )
    return str_, 1


def case_two_high_confidence_sources() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Radboud University Medical Center, Nijmegen",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Illumina TruGenome Clinical Sequencing Services",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 2


def case_three_high_confidence_sources() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Radboud University Medical Center, Nijmegen",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Illumina TruGenome Clinical Sequencing Services",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Emory Genetics Laboratory",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 3


def case_four_high_confidence_sources() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Radboud University Medical Center, Nijmegen",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Illumina TruGenome Clinical Sequencing Services",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="Emory Genetics Laboratory",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
            EvidenceFactory(
                name="UKGTN",
                rating=5,
                reviewer__user_type=Reviewer.TYPES.GEL,
            ),
        ]
    )
    return str_, 3


def case_one_high_confidence_source_rating_3() -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(
                name="Radboud University Medical Center, Nijmegen",
                rating=3,
                reviewer__user_type=Reviewer.TYPES.GEL,
            )
        ]
    )
    return str_, 1


@pytest.mark.parametrize(
    "names",
    [
        ["Expert Review Green", "Radboud University Medical Center, Nijmegen"],
        ["Radboud University Medical Center, Nijmegen", "Expert Review Green"],
    ],
)
def case_one_high_confidence_source_and_one_expert_review_green(
    names: List[str],
) -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(name=name, rating=5, reviewer__user_type=Reviewer.TYPES.GEL)
            for name in names
        ]
    )
    return str_, 3


@pytest.mark.parametrize(
    "names",
    [
        ["Other"],
        ["Other", "Expert list"],
        ["Other", "Expert list", "Expert Review"],
        ["Other", "Expert list", "Expert Review", "Literature"],
    ],
)
def case_non_expert_non_high_confidence_gel_sources(
    names: List[str],
) -> Tuple[STR, int]:
    str_ = STRFactory.create(
        evidence=[
            EvidenceFactory(name=name, rating=5, reviewer__user_type=Reviewer.TYPES.GEL)
            for name in names
        ]
    )
    return str_, 1


@pytest.mark.django_db
@parametrize_with_cases("str_, expected", cases=".")
def test_success(str_: STR, expected: int):
    actual = str_.evidence_status()

    assert actual == expected

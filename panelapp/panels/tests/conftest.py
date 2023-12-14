import pytest

from accounts.models import Reviewer
from accounts.tests.factories import UserFactory


@pytest.fixture
def curator_user():
    return UserFactory(username="gel_user", reviewer__user_type=Reviewer.TYPES.GEL)


@pytest.fixture
def reviewer_user():
    return UserFactory(
        username="verified_user", reviewer__user_type=Reviewer.TYPES.REVIEWER
    )


@pytest.fixture
def external_user():
    return UserFactory(username="external_user")

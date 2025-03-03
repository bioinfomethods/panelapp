import pytest

from accounts.models import (
    Reviewer,
    User,
)
from accounts.tests.factories import UserFactory


@pytest.fixture
def curator_user() -> User:
    return UserFactory(username="gel_user", reviewer__user_type=Reviewer.TYPES.GEL)

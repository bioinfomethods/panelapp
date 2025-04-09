from datetime import (
    datetime,
    timedelta,
)

import pytest
import time_machine
from django.utils import timezone

from releases.models import ReleaseDeployment


@pytest.mark.parametrize(
    ["start", "end", "elapsed", "expected"],
    [
        [
            None,
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=50, second=12)
            ),
            timedelta(minutes=5),
            None,
        ],
        [
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=0, second=0)
            ),
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=50, second=12)
            ),
            timedelta(minutes=20),
            timedelta(minutes=50, seconds=12),
        ],
        [
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=0, second=0)
            ),
            None,
            timedelta(minutes=10, seconds=2),
            timedelta(minutes=10, seconds=2),
        ],
    ],
)
def test_elapsed(
    start: datetime | None,
    end: datetime | None,
    elapsed: timedelta,
    expected: timedelta,
):
    deployment = ReleaseDeployment(start=start, end=end)
    if start is not None:
        with time_machine.travel(start + elapsed):
            actual = deployment.elapsed()
    else:
        actual = deployment.elapsed()
    assert expected == actual


@pytest.mark.parametrize(
    ["start", "end", "elapsed", "expected"],
    [
        [
            None,
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=50, second=12)
            ),
            timedelta(minutes=5),
            False,
        ],
        [
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=0, second=0)
            ),
            None,
            timedelta(minutes=20),
            False,
        ],
        [
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=0, second=0)
            ),
            None,
            timedelta(minutes=31),
            True,
        ],
        [
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=0, second=0)
            ),
            timezone.make_aware(
                datetime(year=2025, month=1, day=20, hour=10, minute=50, second=12)
            ),
            timedelta(minutes=31),
            False,
        ],
    ],
)
def test_timed_out(
    start: datetime | None,
    end: datetime | None,
    elapsed: timedelta,
    expected: bool,
):
    deployment = ReleaseDeployment(start=start, end=end)
    if start is not None:
        with time_machine.travel(start + elapsed):
            actual = deployment.timed_out()
    else:
        actual = deployment.timed_out()
    assert expected == actual

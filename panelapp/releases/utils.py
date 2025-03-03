import re
from itertools import islice
from typing import Literal

from django.core.paginator import (
    Page,
    Paginator,
)
from django.db.models.query import QuerySet


def paginate(qs: QuerySet, page_size: int, page_number: int) -> tuple[Page, range]:
    paginator = Paginator(qs, page_size)
    return paginator.page(page_number), paginator.get_elided_page_range(page_number)


def batched(iterable, n):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def parse_sort_field(s: str) -> tuple[str, Literal["asc"] | Literal["desc"]]:
    """
    Parse a django-formatted field sort string into field and direction.

    >>> parse_sort_field("name")
    ('name', 'asc')
    >>> parse_sort_field("-name")
    ('name', 'desc')
    """
    if m := re.match(r"^(?P<sign>-)?(?P<field>.+)$", s):
        # invert the direction as we want interactions to do the opposite
        return (m.group("field"), "desc" if m.group("sign") else "asc")
    raise ValueError("Invalid sort field")

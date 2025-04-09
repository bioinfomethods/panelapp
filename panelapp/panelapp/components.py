import json
from dataclasses import dataclass
from typing import Literal

from django.core.paginator import Page


@dataclass
class HtmxParams:
    get: str | None = None
    post: str | None = None
    target: str | None = None
    swap: str | None = None
    include: str | None = None
    trigger: str | None = None
    indicator: str | None = None
    sync: str | None = None

    def __str__(self) -> str:
        attrs = []
        if self.get is not None:
            attrs.append(f'hx-get="{self.get}"')
        if self.post is not None:
            attrs.append(f'hx-post="{self.post}"')
        if self.target is not None:
            attrs.append(f'hx-target="{self.target}"')
        if self.swap is not None:
            attrs.append(f'hx-swap="{self.swap}"')
        if self.include is not None:
            attrs.append(f'hx-include="{self.include}"')
        if self.trigger is not None:
            attrs.append(f'hx-trigger="{self.trigger}"')
        if self.indicator is not None:
            attrs.append(f'hx-indicator="{self.indicator}"')
        if self.sync is not None:
            attrs.append(f'hx-sync="{self.sync}"')
        return " ".join(attrs)


@dataclass
class CheckBox:
    name: str
    value: str
    label: str
    checked: bool
    htmx: HtmxParams


@dataclass
class CheckBoxFilter:
    label: str
    checkboxes: list[CheckBox]


@dataclass
class Facet:
    component: CheckBoxFilter


@dataclass
class FacetGroup:
    id: str
    facets: list[Facet]


@dataclass
class SearchBar:
    id: str
    name: str
    value: str
    label: str
    placeholder: str
    page: Page
    object_name_plural: str
    htmx: HtmxParams


@dataclass
class SortableTableHeader:
    field: str
    hx_get: str
    hx_include: str
    sort: Literal["asc"] | Literal["desc"] | None = None

    @property
    def hx_vals(self) -> str:
        if self.sort in [None, "desc"]:
            vals = {"order_by": self.field}
        else:
            vals = {"order_by": f"-{self.field}"}
        return json.dumps(vals, indent=0)

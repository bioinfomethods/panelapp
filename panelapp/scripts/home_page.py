"""
Manage home pages
"""

import argparse
import difflib
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import (
    Dict,
    List,
    Optional,
    Union,
)

import django
import typer
from django.db import transaction
from serde import (
    serde,
    to_dict,
)

logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("serde").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

sys.path.insert(0, os.path.abspath(os.path.curdir))
django.setup()

from panelapp.models import HomeText
from panelapp.utils import home_page
from panelapp.utils.home_page import (
    Error,
    FileAsset,
    FileDomainEvent,
    HomePage,
    ImageAsset,
    ImageDomainEvent,
    MarkdownChanged,
    PageDomainEvent,
    standardise,
)

cli = typer.Typer()
cli_links = typer.Typer()

cli.add_typer(cli_links, name="links")


@dataclass
class Shared:
    section: Optional[int]


@cli.callback()
def shared(ctx: typer.Context, section: Optional[int] = typer.Option(None)):
    ctx.obj = Shared(section=section)


EventOrError = Union[FileDomainEvent, ImageDomainEvent, PageDomainEvent, Error]


@serde
@dataclass
class Output:
    events: List[EventOrError]


@cli.command(name="standardise")
@transaction.atomic
def standardise_pages(
    ctx: typer.Context,
    dry_run: bool = typer.Option(default=False),
):
    """Standardise markdown to CommonMark format."""
    events: List[EventOrError] = []
    if ctx.obj.section:
        home_texts = HomeText.objects.filter(section__in=[ctx.obj.section])
    else:
        home_texts = HomeText.objects.all()
    for home_text in home_texts:
        new_text = standardise(home_text.text)
        if home_text.text != new_text:
            diff = difflib.unified_diff(
                home_text.text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile="before.md",
                tofile="after.md",
            )
            diff = [x.rstrip("\n") for x in diff]
            diff = "\n".join(diff)
            events.append(PageDomainEvent(pk=home_text.pk, event=MarkdownChanged(diff)))
            home_text.text = new_text
            home_text.save()

    if dry_run:
        transaction.set_rollback(True)

    print(json.dumps(to_dict(Output(events)), indent=2))


@serde
@dataclass(frozen=True)
class LinkOutput:
    url: str


@serde
@dataclass
class PageOutput:
    title: str
    links: List[LinkOutput]
    images: Dict[str, ImageAsset]
    files: Dict[str, FileAsset]


@serde
@dataclass
class ViewLinksOutput:
    pages: List[PageOutput]


@cli_links.command(name="view")
def view_links(ctx: typer.Context):
    """Display the current state of links and assets for the home pages."""
    pages = []
    if ctx.obj.section:
        home_texts = HomeText.objects.filter(section__in=[ctx.obj.section])
    else:
        home_texts = HomeText.objects.all()
    for home_text in home_texts:
        page = HomePage.from_home_text(home_text)
        links = page.media_links()
        links_output = []
        images = {}
        files = {}
        for link in links:
            asset = link.asset()
            if isinstance(asset, ImageAsset):
                images[asset.name] = asset
            elif isinstance(asset, FileAsset):
                files[asset.name] = asset
            else:
                raise ValueError(f"Invalid asset: {asset}")
            links_output.append(LinkOutput(link.url))
        pages.append(
            PageOutput(
                title=home_text.title,
                links=links_output,
                images=images,
                files=files,
            )
        )
    print(json.dumps(to_dict(ViewLinksOutput(pages)), indent=2))


@cli_links.command(name="fix-absolute")
@transaction.atomic
def fix_absolute_media_links(
    ctx: typer.Context,
    hosts: List[str] = typer.Argument(
        help="The host names of the absolute links to consider"
    ),
    dry_run: bool = typer.Option(default=False),
):
    """Convert absolute media links to relative and upload missing referenced files if possible."""
    if ctx.obj.section:
        home_texts = HomeText.objects.filter(section__in=[ctx.obj.section])
    else:
        home_texts = HomeText.objects.all()
    events: List[EventOrError] = []
    for home_text in home_texts:
        old_text = home_text.text
        page = HomePage.from_home_text(home_text)
        page, results = home_page.fix_absolute_media_links(page, hosts=hosts)
        events.extend(results)
        new_text = page.text()
        if home_text.text != new_text:
            home_text.text = new_text
            home_text.save()
            diff = difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile="before.md",
                tofile="after.md",
            )
            diff = [x.rstrip("\n") for x in diff]
            diff = "\n".join(diff)
            events.append(PageDomainEvent(pk=home_text.pk, event=MarkdownChanged(diff)))

    if dry_run:
        transaction.set_rollback(True)

    print(json.dumps(to_dict(Output(events)), indent=2))


if __name__ == "__main__":
    cli()

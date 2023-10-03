"""
Utilities for working with PanelApp home pages.
"""

import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import (
    List,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import urlparse

import lenses
import mistletoe
import requests
from bs4 import (
    BeautifulSoup,
    Tag,
)
from django.conf import settings
from django.core.files.base import ContentFile
from mistletoe import (
    block_token,
    span_token,
    token,
)
from mistletoe.markdown_renderer import (
    BlankLine,
    LinkReferenceDefinitionBlock,
    MarkdownRenderer,
)
from returns.result import (
    Failure,
    Result,
    Success,
    safe,
)
from serde import serde

from panelapp.models import (
    File,
    HomeText,
    Image,
)


@serde
@dataclass(frozen=True)
class Present:
    asset_id: int


@serde
@dataclass(frozen=True)
class Missing:
    pass


AssetState = Union[Present, Missing]


@serde
@dataclass
class Created:
    name: str


@serde
@dataclass
class FileDomainEvent:
    pk: int
    event: Created


@serde
@dataclass
class ImageDomainEvent:
    pk: int
    event: Created


@serde
@dataclass(frozen=True)
class ImageAsset:
    name: str
    state: AssetState

    @safe(exceptions=(requests.HTTPError,))
    def upload(self, url: str) -> List[ImageDomainEvent]:
        if not isinstance(self.state, Missing):
            return []

        src = requests.get(url)
        src.raise_for_status()

        image = Image(image=ContentFile(src.content, name=self.name))
        image.save()

        return [ImageDomainEvent(pk=image.pk, event=Created(self.name))]


@dataclass(frozen=True)
class FileAsset:
    name: str
    state: AssetState

    @safe(exceptions=(requests.HTTPError,))
    def upload(self, url: str) -> List[FileDomainEvent]:
        if not isinstance(self.state, Missing):
            return []

        src = requests.get(url)
        src.raise_for_status()

        file = File(file=ContentFile(src.content, name=self.name))
        file.save()

        return [FileDomainEvent(pk=file.pk, event=Created(self.name))]


Asset = Union[FileAsset, ImageAsset]


@dataclass
class HtmlImage:
    url: str
    lens: lenses.UnboundLens
    token: Union[block_token.HtmlBlock, span_token.HtmlSpan]
    tag: Tag

    def as_relative(self) -> "HtmlLink":
        parts = urlparse(self.url)
        return HtmlImage(url=parts.path, lens=self.lens, token=self.token, tag=self.tag)

    def asset(self) -> Union[FileAsset, ImageAsset]:
        path = PurePath(urlparse(self.url).path)
        try:
            image = (
                Image.objects.filter(image=f"images/{path.name}")
                .order_by("-pk")[0:1]
                .get()
            )
        except Image.DoesNotExist:
            return ImageAsset(name=path.name, state=Missing())
        else:
            return ImageAsset(name=path.name, state=Present(image.pk))


@dataclass
class HtmlLink:
    url: str
    lens: lenses.UnboundLens
    token: Union[block_token.HtmlBlock, span_token.HtmlSpan]
    tag: Tag

    def as_relative(self) -> "HtmlLink":
        parts = urlparse(self.url)
        return HtmlLink(url=parts.path, lens=self.lens, token=self.token, tag=self.tag)

    def asset(self) -> Union[FileAsset, ImageAsset]:
        path = PurePath(urlparse(self.url).path)
        if path.parts[-2] == "images":
            try:
                image = Image.objects.get(image=f"images/{path.name}")
            except Image.DoesNotExist:
                return ImageAsset(name=path.name, state=Missing())
            else:
                return ImageAsset(name=path.name, state=Present(image.pk))
        else:
            try:
                file = File.objects.get(file=f"files/{path.name}")
            except File.DoesNotExist:
                return FileAsset(name=path.name, state=Missing())
            else:
                return FileAsset(name=path.name, state=Present(file.pk))


@dataclass
class MdImage:
    url: str
    lens: lenses.UnboundLens

    def as_relative(self) -> "MdImage":
        parts = urlparse(self.url)
        return MdImage(url=parts.path, lens=self.lens)

    def asset(self) -> Union[FileAsset, ImageAsset]:
        path = PurePath(urlparse(self.url).path)
        try:
            image = (
                Image.objects.filter(image=f"images/{path.name}")
                .order_by("-pk")[0:1]
                .get()
            )
        except Image.DoesNotExist:
            return ImageAsset(name=path.name, state=Missing())
        else:
            return ImageAsset(name=path.name, state=Present(image.pk))


@dataclass
class MdLink:
    url: str
    lens: lenses.UnboundLens

    def as_relative(self) -> "MdLink":
        parts = urlparse(self.url)
        return MdLink(url=parts.path, lens=self.lens)

    def asset(self) -> Union[FileAsset, ImageAsset]:
        path = PurePath(urlparse(self.url).path)
        if path.parts[-2] == "images":
            try:
                image = Image.objects.get(image=f"images/{path.name}")
            except Image.DoesNotExist:
                return ImageAsset(name=path.name, state=Missing())
            else:
                return ImageAsset(name=path.name, state=Present(image.pk))
        else:
            try:
                file = File.objects.get(file=f"files/{path.name}")
            except File.DoesNotExist:
                return FileAsset(name=path.name, state=Missing())
            else:
                return FileAsset(name=path.name, state=Present(file.pk))


Link = Union[MdLink, MdImage, HtmlLink, HtmlImage]


def parse_markdown(text: str) -> mistletoe.Document:
    block_token.reset_tokens()
    span_token.reset_tokens()
    block_token.remove_token(block_token.Footnote)
    block_token.add_token(block_token.HtmlBlock)
    block_token.add_token(BlankLine)
    block_token.add_token(LinkReferenceDefinitionBlock)
    span_token.add_token(span_token.HtmlSpan)
    return mistletoe.Document(text)


def render_markdown(doc: mistletoe.Document) -> str:
    block_token.reset_tokens()
    span_token.reset_tokens()
    with MarkdownRenderer() as renderer:
        text = renderer.render(doc)
    return text


@dataclass
class HomePage:
    home_text_id: int
    doc: mistletoe.Document

    @classmethod
    def from_home_text(cls, home_text: HomeText) -> "HomePage":
        return HomePage(home_text.pk, parse_markdown(home_text.text))

    def text(self) -> str:
        return render_markdown(self.doc)

    def replace_link(self, old: Link, new: Link) -> "HomePage":
        if isinstance(old, MdLink):
            token = old.lens.get()(self.doc)
            token.target = new.url
        elif isinstance(old, MdImage):
            token = old.lens.get()(self.doc)
            token.src = new.url
        elif isinstance(old, HtmlLink):
            token = old.lens.get()(self.doc)

            if isinstance(old.token, block_token.HtmlBlock):
                soup = BeautifulSoup(token.content, "html.parser")
                tag = soup.find(attrs=old.tag.attrs)
                assert isinstance(tag, Tag)
                tag["href"] = new.url

                token.content = soup.prettify(formatter="minimal")
            else:
                token.content = re.sub(old.url, new.url, token.content)
        elif isinstance(old, HtmlImage):
            token = old.lens.get()(self.doc)

            if isinstance(old.token, block_token.HtmlBlock):
                soup = BeautifulSoup(token.content, "html.parser")
                tag = soup.find(attrs=old.tag.attrs)
                assert isinstance(tag, Tag)
                tag["src"] = new.url

                token.content = soup.prettify(formatter="minimal")
            else:
                token.content = re.sub(old.url, new.url, token.content)
        else:
            raise ValueError(f"Invalid link: {old}")

        return HomePage(home_text_id=self.home_text_id, doc=self.doc)

    def media_links(self) -> List[Link]:
        """
        All links whose path is under the path given by
        settings.MEDIA_URL.
        """
        media_path_prefix = str(PurePath(urlparse(settings.MEDIA_URL).path))

        def _find_links(token: token.Token, lens: lenses.UnboundLens) -> List[Link]:
            if isinstance(token, span_token.Link):
                parts = urlparse(token.target)
                if parts.path.startswith(media_path_prefix):
                    return [MdLink(url=token.target, lens=lens)]
            if isinstance(token, span_token.Image):
                parts = urlparse(token.src)
                if parts.path.startswith(media_path_prefix):
                    return [MdImage(url=token.src, lens=lens)]
            elif isinstance(token, block_token.HtmlBlock):
                links = []
                soup = BeautifulSoup(token.content, "html.parser")
                a_tags = soup("a")
                img_tags = soup("img")
                links = []
                for a in a_tags:
                    href = a["href"]
                    parts = urlparse(href)
                    if parts.path.startswith(media_path_prefix):
                        links.append(
                            HtmlLink(
                                url=href, lens=lens.children[0], token=token, tag=a
                            )
                        )
                for img in img_tags:
                    src = img["src"]
                    parts = urlparse(src)
                    if parts.path.startswith(media_path_prefix):
                        links.append(
                            HtmlImage(
                                url=src, lens=lens.children[0], token=token, tag=img
                            )
                        )
                return links
            elif isinstance(token, span_token.HtmlSpan):
                soup = BeautifulSoup(token.content, "html.parser")
                a_tags = soup("a")
                img_tags = soup("img")
                links = []
                for a in a_tags:
                    href = a["href"]
                    parts = urlparse(href)
                    if parts.path.startswith(media_path_prefix):
                        links.append(HtmlLink(url=href, lens=lens, token=token, tag=a))
                for img in img_tags:
                    src = img["src"]
                    parts = urlparse(src)
                    if parts.path.startswith(media_path_prefix):
                        links.append(
                            HtmlImage(url=src, lens=lens, token=token, tag=img)
                        )
                return links
            elif isinstance(token, block_token.BlockToken):
                links = []
                for i, child in enumerate(token.children):
                    links.extend(_find_links(child, lens.children[i]))
                return links
            return []

        return _find_links(self.doc, lenses.lens)

    def absolute_media_links(self, hosts: List[str]) -> List[Link]:
        links = self.media_links()
        return [x for x in links if urlparse(x.url).netloc in hosts]


@serde
@dataclass(frozen=True)
class SourceAssetNotFound:
    url: str
    error: str


Error = SourceAssetNotFound


@serde
@dataclass
class MarkdownChanged:
    diff: str


@serde
@dataclass
class PageDomainEvent:
    pk: int
    event: MarkdownChanged


def fix_absolute_media_link(
    page: HomePage, link: Link
) -> Result[Tuple[HomePage, List[Union[FileDomainEvent, ImageDomainEvent]]], Error]:
    events = []
    asset = link.asset()
    if isinstance(asset.state, Missing):
        result = asset.upload(link.url)
        if isinstance(result, Failure):
            return Failure(
                SourceAssetNotFound(url=link.url, error=str(result.failure()))
            )
        events = result.unwrap()

    page = page.replace_link(link, link.as_relative())

    return Success((page, events))


def fix_absolute_media_links(
    page: HomePage, hosts: List[str]
) -> Tuple[HomePage, List[Union[FileDomainEvent, ImageDomainEvent, Error]]]:
    """
    Convert all absolute URLs with hostname in `hosts`
    to relative URLs and upload any files that are missing
    from the original absolute URL.
    """
    results = []
    links = page.absolute_media_links(hosts)
    for link in links:
        result = fix_absolute_media_link(page, link)
        if isinstance(result, Success):
            page, events = result.unwrap()
            results.extend(events)
        else:
            results.append(result.failure())

    return page, results


def standardise(text: str) -> str:
    """Standardise markdown text for compatibility."""
    return re.sub(
        (
            r"^[^\S\n\r]*"  # https://stackoverflow.com/questions/3469080/match-whitespace-but-not-newlines
            r"(#+)([^#\s]+)"
        ),
        r"\1 \2",
        text,
        flags=re.MULTILINE,
    )

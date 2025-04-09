import tempfile
import uuid
from textwrap import dedent
from typing import Tuple

import pytest
import responses
from django.core.files.base import ContentFile
from django.test import override_settings
from pytest_cases import parametrize_with_cases
from serde.json import from_json
from typer.testing import CliRunner

from panelapp.models import (
    File,
    HomeText,
    Image,
)
from panelapp.tests.factories import (
    FileFactory,
    HomeTextFactory,
    ImageFactory,
)
from panelapp.utils.home_page import (
    Created,
    FileAsset,
    HomePage,
    ImageAsset,
    ImageDomainEvent,
    MarkdownChanged,
    Missing,
    PageDomainEvent,
    Present,
    SourceAssetNotFound,
)
from scripts.home_page import (
    LinkOutput,
    Output,
    PageOutput,
    ViewLinksOutput,
    cli,
)

runner = CliRunner()


class TestFixAbsoluteMediaLinks:
    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_absolute_md_link(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](http://test.local/media/images/test.jpg)\n",
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "[Thing](/media/images/test.jpg)\n"

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created("test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1 @@
                        -[Thing](http://test.local/media/images/test.jpg)
                        +[Thing](/media/images/test.jpg)"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_absolute_md_link_https(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](https://test.local/media/images/test.jpg)\n",
        )

        responses.get(
            "https://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "[Thing](/media/images/test.jpg)\n"

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created("test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1 @@
                        -[Thing](https://test.local/media/images/test.jpg)
                        +[Thing](/media/images/test.jpg)"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_absolute_md_image(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="![Thing](http://test.local/media/images/test.jpg)\n",
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "![Thing](/media/images/test.jpg)\n"

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created("test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1 @@
                        -![Thing](http://test.local/media/images/test.jpg)
                        +![Thing](/media/images/test.jpg)"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_one_relative_link(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](/media/images/test.jpg)\n",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == f"[Thing](/media/images/test.jpg)\n"

        output = from_json(Output, result.stdout)

        assert output == Output([])

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_html_inline_img_element(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#News",
            text='<img src="http://test.local/media/images/test.jpg" alt="NHS logo"  width=100% height=100% align=middle>\n',
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert (
            home_text.text
            == '<img align="middle" alt="NHS logo" height="100%" src="/media/images/test.jpg" width="100%"/>\n\n'
        )

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created(name="test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1,2 @@
                        -<img src="http://test.local/media/images/test.jpg" alt="NHS logo"  width=100% height=100% align=middle>
                        +<img align="middle" alt="NHS logo" height="100%" src="/media/images/test.jpg" width="100%"/>
                        +"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_html_inline_a_element(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text='<a href="http://test.local/media/images/test.jpg">Link text</a>\n',
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == '<a href="/media/images/test.jpg">Link text</a>\n'

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created(name="test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1 @@
                        -<a href="http://test.local/media/images/test.jpg">Link text</a>
                        +<a href="/media/images/test.jpg">Link text</a>"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_html_table_embedded_media_links(self):
        text = """\
<table style="width:100%">
  <tr>
    <td style="width:10%;padding-right:10px;align:center"><img src="http://test.local/media/images/test.jpg" alt="NHS logo"  width=100% height=100% align=middle></td>
    <td>NHS users should view the set of genes/panels that are available for testing as part of the GMS on the <a href="https://nhsgms-panelapp.genomicsengland.co.uk/" style="color:#005EB8">NHS GMS Panels Resource</a> website. These are the panels that can be chosen when requesting a genomic test.  The green (diagnostic evidence level) genes shown on these panels are those that are analysed as part of the diagnostic pathway*. The panel versions are periodically updated from PanelApp. Single gene tests and small non-WGS panels for the GMS are currently <i>not</i> included. </td>
  </tr>
 <tr></tr>
</table>"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        expected_page_text = """\
<table style="width:100%">
 <tr>
  <td style="width:10%;padding-right:10px;align:center">
   <img align="middle" alt="NHS logo" height="100%" src="/media/images/test.jpg" width="100%"/>
  </td>
  <td>
   NHS users should view the set of genes/panels that are available for testing as part of the GMS on the
   <a href="https://nhsgms-panelapp.genomicsengland.co.uk/" style="color:#005EB8">
    NHS GMS Panels Resource
   </a>
   website. These are the panels that can be chosen when requesting a genomic test.  The green (diagnostic evidence level) genes shown on these panels are those that are analysed as part of the diagnostic pathway*. The panel versions are periodically updated from PanelApp. Single gene tests and small non-WGS panels for the GMS are currently
   <i>
    not
   </i>
   included.
  </td>
 </tr>
 <tr>
 </tr>
</table>

"""

        home_text.refresh_from_db()
        assert home_text.text == expected_page_text

        [image] = Image.objects.all()

        assert image.image.name == "images/test.jpg"

        with image.image.open() as f:
            content = f.read()

        assert content == b"Hello there"

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created(name="test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1,7 +1,21 @@
                         <table style="width:100%">
                        -  <tr>
                        -    <td style="width:10%;padding-right:10px;align:center"><img src="http://test.local/media/images/test.jpg" alt="NHS logo"  width=100% height=100% align=middle></td>
                        -    <td>NHS users should view the set of genes/panels that are available for testing as part of the GMS on the <a href="https://nhsgms-panelapp.genomicsengland.co.uk/" style="color:#005EB8">NHS GMS Panels Resource</a> website. These are the panels that can be chosen when requesting a genomic test.  The green (diagnostic evidence level) genes shown on these panels are those that are analysed as part of the diagnostic pathway*. The panel versions are periodically updated from PanelApp. Single gene tests and small non-WGS panels for the GMS are currently <i>not</i> included. </td>
                        -  </tr>
                        - <tr></tr>
                        -</table>
                        + <tr>
                        +  <td style="width:10%;padding-right:10px;align:center">
                        +   <img align="middle" alt="NHS logo" height="100%" src="/media/images/test.jpg" width="100%"/>
                        +  </td>
                        +  <td>
                        +   NHS users should view the set of genes/panels that are available for testing as part of the GMS on the
                        +   <a href="https://nhsgms-panelapp.genomicsengland.co.uk/" style="color:#005EB8">
                        +    NHS GMS Panels Resource
                        +   </a>
                        +   website. These are the panels that can be chosen when requesting a genomic test.  The green (diagnostic evidence level) genes shown on these panels are those that are analysed as part of the diagnostic pathway*. The panel versions are periodically updated from PanelApp. Single gene tests and small non-WGS panels for the GMS are currently
                        +   <i>
                        +    not
                        +   </i>
                        +   included.
                        +  </td>
                        + </tr>
                        + <tr>
                        + </tr>
                        +</table>
                        +"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_missing_source_image_asset(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](http://test.local/media/images/test.jpg)\n",
        )

        responses.get("http://test.local/media/images/test.jpg", status=404)

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "[Thing](http://test.local/media/images/test.jpg)\n"

        assert list(Image.objects.all()) == []
        assert list(File.objects.all()) == []

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                SourceAssetNotFound(
                    url="http://test.local/media/images/test.jpg",
                    error="404 Client Error: Not Found for url: http://test.local/media/images/test.jpg",
                )
            ]
        )

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_missing_source_file_asset(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](http://test.local/media/files/document.pdf)\n",
        )

        responses.get("http://test.local/media/files/document.pdf", status=404)

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "[Thing](http://test.local/media/files/document.pdf)\n"

        assert list(Image.objects.all()) == []
        assert list(File.objects.all()) == []

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                SourceAssetNotFound(
                    url="http://test.local/media/files/document.pdf",
                    error="404 Client Error: Not Found for url: http://test.local/media/files/document.pdf",
                )
            ]
        )

        assert result.exit_code == 0

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_non_media_links(self):
        text = """\
Two small panels for clinical indications in the current NHS National Genomic Test Directory v4 \
(<a href="https://panelapp.genomicsengland.co.uk/panels/1221/" target="_blank">R215</a href> \
CDH1-related cancer syndrome and <a href="https://panelapp.genomicsengland.co.uk/panels/1222/" \
target="_blank">R216</a href> Li Fraumeni Syndrome) have been added. Further small panels \
will be added to PanelApp in the coming months.
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        expected_page_text = """\
Two small panels for clinical indications in the current NHS National Genomic Test Directory v4 \
(<a href="https://panelapp.genomicsengland.co.uk/panels/1221/" target="_blank">R215</a href> \
CDH1-related cancer syndrome and <a href="https://panelapp.genomicsengland.co.uk/panels/1222/" \
target="_blank">R216</a href> Li Fraumeni Syndrome) have been added. Further small panels \
will be added to PanelApp in the coming months.
"""

        home_text.refresh_from_db()
        assert home_text.text == expected_page_text

        assert list(Image.objects.all()) == []
        assert list(File.objects.all()) == []

        output = from_json(Output, result.stdout)

        assert output == Output([])

        assert result.exit_code == 0

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_noop(self):
        text = """\
First paragraph.

Second paragraph.
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert (
            home_text.text
            == """\
First paragraph.

Second paragraph.
"""
        )

        assert list(Image.objects.all()) == []
        assert list(File.objects.all()) == []

        output = from_json(Output, result.stdout)

        assert output == Output([])

        assert result.exit_code == 0

    @responses.activate
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_dry_run(self):
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text="[Thing](http://test.local/media/images/test.jpg)\n",
        )

        responses.get(
            "http://test.local/media/images/test.jpg",
            body=b"Hello there",
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "links", "fix-absolute", "test.local", "--dry-run"],
            catch_exceptions=False,
        )

        home_text.refresh_from_db()
        assert home_text.text == "[Thing](http://test.local/media/images/test.jpg)\n"

        assert list(Image.objects.all()) == []
        assert list(File.objects.all()) == []

        output = from_json(Output, result.stdout)

        assert output == Output(
            [
                ImageDomainEvent(pk=1, event=Created("test.jpg")),
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1 +1 @@
                        -[Thing](http://test.local/media/images/test.jpg)
                        +[Thing](/media/images/test.jpg)"""
                        )
                    ),
                ),
            ]
        )

        assert result.exit_code == 0


class TestLinksViewCases:
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def case_multiple_media_links(
        self,
    ) -> Tuple[HomeText, ViewLinksOutput]:
        text = """\
![Image](http://test.local/media/images/test.jpg)
[Document](http://test.local/media/files/document.pdf)
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )
        image = ImageFactory.create(image=ContentFile(b"hello", name="test.jpg"))

        return (
            home_text,
            ViewLinksOutput(
                [
                    PageOutput(
                        title=home_text.title,
                        links=[
                            LinkOutput("http://test.local/media/images/test.jpg"),
                            LinkOutput("http://test.local/media/files/document.pdf"),
                        ],
                        images={
                            "test.jpg": ImageAsset(
                                name="test.jpg", state=Present(image.pk)
                            )
                        },
                        files={
                            "document.pdf": FileAsset(
                                name="document.pdf", state=Missing()
                            )
                        },
                    )
                ]
            ),
        )

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def case_no_media_links(self) -> Tuple[HomeText, ViewLinksOutput]:
        text = """\
# Heading
Some text without links
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        return (
            home_text,
            ViewLinksOutput([PageOutput(title="Home", links=[], images={}, files={})]),
        )


@parametrize_with_cases(["home_text", "expected"], cases=TestLinksViewCases)
def test_links_view(home_text: HomeText, expected: ViewLinksOutput):
    result = runner.invoke(
        cli,
        ["--section", str(home_text.section), "links", "view"],
        catch_exceptions=False,
    )

    output = from_json(ViewLinksOutput, result.stdout)
    assert output == expected

    assert result.exit_code == 0


class TestStandardise:
    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_invalid_html_and_heading(self):
        text = """\
<hr>
##22nd March 2023: Update of GMS panels
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "standardise"],
            catch_exceptions=False,
        )

        output = from_json(Output, result.stdout)
        assert output == Output(
            [
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1,2 +1,2 @@
                         <hr>
                        -##22nd March 2023: Update of GMS panels
                        +## 22nd March 2023: Update of GMS panels"""
                        )
                    ),
                )
            ]
        )

        assert result.exit_code == 0

        home_text.refresh_from_db()
        assert (
            home_text.text
            == """\
<hr>
## 22nd March 2023: Update of GMS panels
"""
        )

    @override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
    @pytest.mark.django_db(transaction=True, reset_sequences=True)
    def test_dry_run(self):
        text = """\
<hr>
##22nd March 2023: Update of GMS panels
"""
        home_text = HomeTextFactory.create(
            section=1,
            title="Home",
            href="#Introduction",
            text=text,
        )

        result = runner.invoke(
            cli,
            ["--section", "1", "standardise", "--dry-run"],
            catch_exceptions=False,
        )

        output = from_json(Output, result.stdout)
        assert output == Output(
            [
                PageDomainEvent(
                    pk=1,
                    event=MarkdownChanged(
                        dedent(
                            """\
                        --- before.md
                        +++ after.md
                        @@ -1,2 +1,2 @@
                         <hr>
                        -##22nd March 2023: Update of GMS panels
                        +## 22nd March 2023: Update of GMS panels"""
                        )
                    ),
                )
            ]
        )

        assert result.exit_code == 0

        home_text.refresh_from_db()
        assert (
            home_text.text
            == """\
<hr>
##22nd March 2023: Update of GMS panels
"""
        )

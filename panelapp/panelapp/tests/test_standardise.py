from typing import Tuple

import markdown
import pytest
from bs4 import BeautifulSoup
from pytest_cases import parametrize_with_cases

from panelapp.utils.home_page import (
    parse_markdown,
    render_markdown,
    standardise,
)


def case_invalid_html_and_heading_one() -> Tuple[str, str]:
    text = """\
<hr>
##22nd March 2023: Update of GMS panels
"""
    expected = """\
<hr>
## 22nd March 2023: Update of GMS panels
"""
    return text, expected


def case_invalid_html_and_heading_two() -> Tuple[str, str]:
    text = """\
<hr>
## 30th November 2022: New GMS panel versions signed-off
"""
    expected = """\
<hr>
## 30th November 2022: New GMS panel versions signed-off
"""
    return text, expected


def case_inline_hashes() -> Tuple[str, str]:
    text = "###Header #something"
    expected = "### Header #something"
    return text, expected


def case_invalid_header_with_list() -> Tuple[str, str]:
    text = """\
  - Item 1

 - Item 2

##Header 1
"""
    expected = """\
  - Item 1

 - Item 2

## Header 1
"""
    return text, expected


def case_link_with_uri_fragment() -> Tuple[str, str]:
    text = "[link](https://host.invalid/path/#!fragment)"
    return text, text


def case_paragraph_second_line_indented() -> Tuple[str, str]:
    text = """\
First line
    Second line.
"""
    return text, text


def case_list_paragraph_not_indented() -> Tuple[str, str]:
    text = r"""\
* Search for panels by gene:
/crowdsourcing/WebServices/search\_genes/BTK/
"""
    return text, text


@parametrize_with_cases("text, expected", cases=".")
def test_output(text: str, expected: str):
    actual = standardise(text)

    assert actual == expected


@pytest.mark.xfail
def case_paragraph_second_line_indented_fail() -> Tuple[str, str]:
    text = """\
First line
    Second line.
"""
    return text, text


@pytest.mark.xfail
def case_list_paragraph_not_indented_fail() -> Tuple[str, str]:
    text = r"""\
* Search for panels by gene:
/crowdsourcing/WebServices/search\_genes/BTK/
"""
    return text, text


@parametrize_with_cases(
    "text, _",
    cases=[
        case_invalid_html_and_heading_one,
        case_invalid_html_and_heading_two,
        case_inline_hashes,
        case_invalid_header_with_list,
        case_link_with_uri_fragment,
        case_paragraph_second_line_indented_fail,
        case_list_paragraph_not_indented_fail,
    ],
)
def test_stable_output(text: str, _):
    """Test that using mistletoe to render markdown does not affect output HTML."""
    standardised = standardise(text)

    md = markdown.Markdown()
    before = BeautifulSoup(md.convert(text), "html.parser").prettify(
        formatter="minimal"
    )

    doc = parse_markdown(standardised)
    rendered = render_markdown(doc)
    after = BeautifulSoup(md.convert(rendered), "html.parser").prettify(
        formatter="minimal"
    )

    assert before == after

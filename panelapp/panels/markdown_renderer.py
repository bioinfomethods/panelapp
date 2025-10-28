"""Markdown rendering with HTML sanitization for comments."""

import markdown
import bleach


# Allowed HTML tags (Markdown-generated + custom features)
ALLOWED_TAGS = [
    # Markdown generates these
    "p",
    "br",
    "strong",
    "em",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "a",
    "blockquote",
    "hr",
    # Custom HTML for report features
    "details",
    "summary",  # Collapsible sections
    "span",
    "div",  # For badges and containers
]

# Allowed HTML attributes
ALLOWED_ATTRS = {
    "*": ["class", "id"],  # Classes/IDs on any element
    "a": ["href", "title", "target"],  # Links
    "details": ["open", "markdown"],  # Collapsible default state, Markdown processing
    "span": ["data-title", "markdown"],  # Tooltips, Markdown processing
    "th": ["data-title", "colspan", "rowspan"],
    "td": ["data-title", "colspan", "rowspan"],
    "div": ["class", "id", "markdown"],  # Markdown processing
    "table": ["class", "markdown"],  # Markdown processing
}


def render_comment_markdown(text):
    """
    Render comment text as Markdown with embedded HTML support.

    Follows the same pattern as HomeText.render_markdown but with:
    - Additional extensions (extra, nl2br, sane_lists)
    - Bleach sanitization for security

    Args:
        text: Markdown text (may contain HTML)

    Returns:
        Safe HTML string ready for display

    Security:
        - Markdown generates known-safe HTML
        - Bleach strips any disallowed tags/attributes
        - No inline styles allowed (class-based only)
        - No JavaScript (script tags, event handlers stripped)
    """
    if not text:
        return ""

    # Configure markdown with extensions
    md = markdown.Markdown(
        extensions=[
            "markdown.extensions.extra",  # Tables, footnotes, def_list, attr_list, etc.
            "markdown.extensions.md_in_html",  # Parse Markdown inside HTML blocks
            "markdown.extensions.nl2br",  # Newline to <br> (replaces linebreaksbr)
            "markdown.extensions.sane_lists",  # Better list handling
        ]
    )

    # Convert markdown to HTML
    html = md.convert(text)

    # Sanitize with bleach (strip disallowed tags/attrs)
    safe_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,  # Remove disallowed tags entirely
    )

    return safe_html

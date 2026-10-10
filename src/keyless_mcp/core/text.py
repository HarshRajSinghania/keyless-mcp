"""Helpers for keeping tool results compact and agent-friendly."""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")


def tidy(text: str | None) -> str:
    """Collapse all whitespace runs (including newlines) into single spaces."""
    return " ".join((text or "").split())


def truncate(text: str | None, limit: int) -> str:
    """Tidy ``text`` and cut it to at most ``limit`` characters, ending with an ellipsis."""
    flat = tidy(text)
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def strip_html(text: str | None) -> str:
    """Remove HTML tags and decode entities, e.g. search-result snippets and HN comment text.

    ``<p>`` and ``<br>`` become spaces so paragraphs do not run together. The result is tidied.
    """
    spaced = re.sub(r"<(p|br)\b[^>]*>", " ", text or "", flags=re.IGNORECASE)
    return tidy(html.unescape(_TAG_RE.sub("", spaced)))

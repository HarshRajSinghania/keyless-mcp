"""Text helpers that keep tool results compact."""

from __future__ import annotations

import pytest

from keyless_mcp.core import strip_html, tidy, truncate

pytestmark = pytest.mark.m3(suite_name="core")


def test_tidy_collapses_whitespace_and_none() -> None:
    assert tidy("  a \n b\t c ") == "a b c"
    assert tidy(None) == ""


def test_truncate_ends_with_an_ellipsis_within_the_limit() -> None:
    assert truncate("short", 10) == "short"
    cut = truncate("word " * 20, 12)
    assert len(cut) <= 12
    assert cut.endswith("…")


def test_strip_html_removes_tags_decodes_entities_and_keeps_paragraphs_apart() -> None:
    raw = 'Hi <span class="searchmatch">Turing</span> &quot;q&quot;<p>Second &amp; last<br>line'
    assert strip_html(raw) == 'Hi Turing "q" Second & last line'
    assert strip_html(None) == ""

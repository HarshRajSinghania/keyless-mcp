"""Read what a cassette recorded, so replay tests can derive expected values from it."""

from __future__ import annotations

from typing import Any

from keyless_mcp.core import cassette
from m3_tests._support.servers import cassette_dir


def recorded(adapter: str, url: str, *, method: str = "GET", body: Any = None) -> Any:
    """The recorded response body for a request, loaded the way replay mode loads it.

    Use it inside an ``if replaying:`` branch for values that move upstream (a front page, a
    latest version): compare the tool's output with what the cassette holds, never with a literal
    copied from it. A re-record then updates the expectation along with the cassette.
    """
    found = cassette.load(cassette_dir(adapter), method, cassette.canonical_url(url), body)
    assert found is not None, (
        f"no {adapter} cassette for {method} {url}; run make record ADAPTER={adapter}"
    )
    return found.body

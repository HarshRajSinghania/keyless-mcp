"""Shared fixtures for every keyless-mcp M3 suite."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from m3_tests._support.servers import keyless_server


@pytest.fixture
def connect(m3_kit: Any) -> Callable[..., Any]:
    """``with connect("arxiv") as client:`` opens an M3 direct client on a keyless-mcp server.

    The server runs in the mode from ``KEYLESS_MCP_HTTP_MODE`` (default: offline replay of the
    adapter's cassettes). Tool input schemas are validated client-side unless
    ``validate_schemas=False``, which you need to test the server's own input errors with
    schema-invalid arguments.
    """

    @contextmanager
    def _connect(
        adapter: str,
        *,
        toolsets: list[str] | None = None,
        mode: str | None = None,
        cassettes: Path | None = None,
        validate_schemas: bool = True,
    ) -> Iterator[Any]:
        server = keyless_server(adapter, toolsets, mode=mode, cassettes=cassettes)
        with m3_kit.direct(server, validate_schemas=validate_schemas) as client:
            yield client

    return _connect

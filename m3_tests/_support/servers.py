"""Factory that launches keyless-mcp as an M3 stdio server, offline by default."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

from m3 import StdioServer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_TESTS = PROJECT_ROOT / "m3_tests" / "adapters"

MODE_ENV = "KEYLESS_MCP_HTTP_MODE"
CASSETTE_DIR_ENV = "KEYLESS_MCP_CASSETTE_DIR"
# `make record` sets this to a temp directory so cassettes are recorded there and only swapped
# into the repo when every test passed. Unset normally.
RECORD_ROOT_ENV = "KEYLESS_MCP_RECORD_ROOT"


def cassette_dir(adapter_name: str) -> Path:
    """Where an adapter's cassettes live: m3_tests/adapters/<name>/cassettes."""
    return ADAPTER_TESTS / adapter_name / "cassettes"


def http_mode() -> str:
    """The HTTP mode the servers started by tests run in: replay unless the env says otherwise."""
    return os.environ.get(MODE_ENV, "replay")


def keyless_server(
    adapter_name: str,
    toolsets: Iterable[str] | None = None,
    *,
    mode: str | None = None,
    cassettes: Path | None = None,
    name: str | None = None,
) -> StdioServer:
    """An M3 ``StdioServer`` running ``python -m keyless_mcp`` against one adapter's cassettes.

    The HTTP mode comes from ``KEYLESS_MCP_HTTP_MODE`` and defaults to ``replay`` so tests are
    offline unless you ask otherwise (``make record`` sets ``record``, ``make test-live`` sets
    ``live``). Pass ``mode`` to force one, which is how ``live`` tests stay live under replay.
    ``cassettes`` overrides the cassette directory (for tests that craft their own cassettes);
    otherwise ``KEYLESS_MCP_RECORD_ROOT``, when set, redirects it to ``<root>/<adapter_name>``.
    ``name`` overrides the server alias (default ``keyless-<adapter_name>``); agent tests use it to
    expose every tool under one short alias.
    """
    record_root = os.environ.get(RECORD_ROOT_ENV)
    if cassettes is None and record_root:
        cassettes = Path(record_root) / adapter_name
    args = ["-m", "keyless_mcp"]
    if toolsets is not None:
        args += ["--toolsets", ",".join(toolsets)]
    return StdioServer(
        name=name or f"keyless-{adapter_name}",
        command=sys.executable,
        args=tuple(args),
        cwd=str(PROJECT_ROOT),
        environment={
            MODE_ENV: mode or http_mode(),
            CASSETTE_DIR_ENV: str(cassettes or cassette_dir(adapter_name)),
        },
    )

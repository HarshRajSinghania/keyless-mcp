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


def cassette_dir(adapter_name: str) -> Path:
    """Where an adapter's cassettes live: m3_tests/adapters/<name>/cassettes."""
    return ADAPTER_TESTS / adapter_name / "cassettes"


def keyless_server(
    adapter_name: str,
    toolsets: Iterable[str] | None = None,
    *,
    mode: str | None = None,
    cassettes: Path | None = None,
) -> StdioServer:
    """An M3 ``StdioServer`` running ``python -m keyless_mcp`` against one adapter's cassettes.

    The HTTP mode comes from ``KEYLESS_MCP_HTTP_MODE`` and defaults to ``replay`` so tests are
    offline unless you ask otherwise (``make record`` sets ``record``, ``make test-live`` sets
    ``live``). Pass ``mode`` to force one, which is how ``live`` tests stay live under replay.
    ``cassettes`` overrides the cassette directory (for tests that craft their own cassettes).
    """
    args = ["-m", "keyless_mcp"]
    if toolsets is not None:
        args += ["--toolsets", ",".join(toolsets)]
    return StdioServer(
        name=f"keyless-{adapter_name}",
        command=sys.executable,
        args=tuple(args),
        cwd=str(PROJECT_ROOT),
        environment={
            MODE_ENV: mode or os.environ.get(MODE_ENV, "replay"),
            CASSETTE_DIR_ENV: str(cassettes or cassette_dir(adapter_name)),
        },
    )

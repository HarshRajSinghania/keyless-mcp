"""Command line entry point: ``keyless-mcp`` or ``python -m keyless_mcp``."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

import anyio

from keyless_mcp import __version__
from keyless_mcp.core import TOOLSETS, AdapterError, parse_toolsets
from keyless_mcp.server import BuiltServer, build_server

TOOLSETS_ENV = "KEYLESS_MCP_TOOLSETS"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keyless-mcp",
        description="MCP server wrapping free, no-auth public APIs. Serves stdio by default.",
    )
    parser.add_argument("--version", action="version", version=f"keyless-mcp {__version__}")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="stdio (default) or Streamable HTTP",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address for --transport http")
    parser.add_argument("--port", type=int, default=8000, help="port for --transport http")
    parser.add_argument(
        "--toolsets",
        help=f"comma-separated toolsets to serve ({', '.join(TOOLSETS)}); "
        f"default: ${TOOLSETS_ENV} or all",
    )
    parser.add_argument(
        "--list-tools", action="store_true", help="print the registered tools and exit"
    )
    return parser


def _first_sentence(text: str | None, limit: int = 70) -> str:
    flat = " ".join((text or "").split())
    sentence = flat.split(". ")[0].rstrip(".")
    return sentence if len(sentence) <= limit else sentence[: limit - 1] + "…"


def format_tool_table(built: BuiltServer) -> str:
    """Table of registered tools: toolset, adapter, tool name and a short description."""
    descriptions = {t.name: t.description for t in anyio.run(built.mcp.list_tools)}
    rows = [("TOOLSET", "ADAPTER", "TOOL", "DESCRIPTION")]
    for adapter in built.adapters:
        for name in adapter.tool_names:
            rows.append(
                (adapter.spec.toolset, adapter.spec.name, name, _first_sentence(descriptions[name]))
            )
    widths = [max(len(row[i]) for row in rows) for i in range(3)]
    return "\n".join(
        f"{a:<{widths[0]}}  {b:<{widths[1]}}  {c:<{widths[2]}}  {d}" for a, b, c, d in rows
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        toolsets = parse_toolsets(args.toolsets or os.environ.get(TOOLSETS_ENV))
        built = build_server(toolsets)
    except (ValueError, AdapterError) as exc:
        sys.exit(f"keyless-mcp: {exc}")
    if args.list_tools:
        print(format_tool_table(built))
        return
    if args.transport == "http":
        built.mcp.run("streamable-http", host=args.host, port=args.port)
    else:
        built.mcp.run("stdio")


if __name__ == "__main__":
    main()

"""Builds the MCP server: a core ``MCPServer`` plus every selected adapter's tools."""

from __future__ import annotations

from dataclasses import dataclass

from mcp.server.mcpserver import MCPServer

from keyless_mcp import __version__
from keyless_mcp.core import HttpClient, HttpConfig, LoadedAdapter, register_adapters

INSTRUCTIONS = (
    "keyless-mcp exposes free public APIs that need no API key. Tool names are "
    "<adapter>_<verb>. All tools are read-only. If a tool returns an error, the message "
    "explains whether the input was invalid or the upstream service failed."
)


@dataclass(frozen=True)
class BuiltServer:
    mcp: MCPServer
    http: HttpClient
    adapters: list[LoadedAdapter]


def build_server(
    toolsets: set[str] | None = None, http_config: HttpConfig | None = None
) -> BuiltServer:
    """Create the server. ``toolsets=None`` registers every adapter."""
    mcp = MCPServer("keyless-mcp", instructions=INSTRUCTIONS, version=__version__)
    http = HttpClient(http_config if http_config is not None else HttpConfig.from_env())
    adapters = register_adapters(mcp, http, toolsets)
    return BuiltServer(mcp, http, adapters)

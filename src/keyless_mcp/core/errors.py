"""Errors that surface to the MCP client as readable ``isError`` tool results.

Every class here subclasses the SDK's ``ToolError``. When a tool raises one, the SDK returns a
normal tool result with ``is_error=True`` and the message as text, so an agent can read it and
recover. Anything else raised from a tool is treated as a crash, so adapters should raise these.
"""

from __future__ import annotations

from mcp.server.mcpserver.exceptions import ToolError


class KeylessError(ToolError):
    """Base class for every error keyless-mcp raises on purpose."""


class InvalidInput(KeylessError):
    """A tool argument is out of range or malformed. The message says how to fix it."""


class UpstreamError(KeylessError):
    """The upstream API failed: HTTP 4xx/5xx, timeout, network error or an unparseable body."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class CassetteMiss(UpstreamError):
    """Replay mode saw a request that has no recorded cassette."""


class AdapterError(Exception):
    """An adapter is malformed (bad adapter.yaml, wrong tool names). Raised at startup."""

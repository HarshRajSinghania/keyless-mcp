"""Small helpers for reading M3 tool results in assertions."""

from __future__ import annotations

from typing import Any


def result_text(result: Any) -> str:
    """All text content of a tool result joined together (useful as an assertion message)."""
    return "\n".join(str(block.get("text", "")) for block in result.content)

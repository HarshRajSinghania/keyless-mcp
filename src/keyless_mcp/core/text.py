"""Helpers for keeping tool results compact and agent-friendly."""

from __future__ import annotations


def tidy(text: str | None) -> str:
    """Collapse all whitespace runs (including newlines) into single spaces."""
    return " ".join((text or "").split())


def truncate(text: str | None, limit: int) -> str:
    """Tidy ``text`` and cut it to at most ``limit`` characters, ending with an ellipsis."""
    flat = tidy(text)
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"

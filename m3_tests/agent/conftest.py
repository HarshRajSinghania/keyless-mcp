"""Guards for the real-agent lane: collect only when asked, skip cleanly without access.

``test_tool_selection.py`` requests M3's ``agent`` fixture, and M3 refuses to even collect such a
test unless a harness is selected (``--harness KIND=MODEL``). So ``make test``, which selects no
harness, would die at collection. Two guards keep that from happening:

* ``pytest_ignore_collect`` leaves the file uncollected while no ``--harness`` is given. Name the
  file on the command line and M3 reports its own "agent test requires --harness" instead.
* ``_require_agent_access`` skips (never fails, never fakes a pass) when the selected harness
  cannot run on this machine: its CLI is not installed or no credential is available for it.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

REAL_AGENT_TESTS = "test_tool_selection.py"

# M3 starts each native harness in an isolated HOME, so the host's own login is not visible to
# Claude Code. It needs a key from the environment (or an explicit --credential-env mapping).
CLAUDE_CREDENTIALS = ("ANTHROPIC_API_KEY",)
CODEX_CREDENTIALS = ("OPENAI_API_KEY", "CODEX_API_KEY")

EXECUTABLES = {"claude_code": "claude", "codex": "codex", "opencode": "opencode", "pi": "pi"}


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if collection_path.name == REAL_AGENT_TESTS and not config.getoption("--harness", default=None):
        return True
    return None


def pytest_report_header(config: pytest.Config) -> str | None:
    if config.getoption("--harness", default=None):
        return None
    return f"keyless-mcp: {REAL_AGENT_TESTS} not collected (no --harness). Run `make agent`."


def _kind(harness: str) -> str:
    kind = harness.lower().replace("-", "_")
    return "claude_code" if kind == "claude" else kind


def skip_reason(kind: str, entry: Mapping[str, Any]) -> str | None:
    """Why this harness cannot run here, or None when it looks usable."""
    executable = entry.get("executable") or EXECUTABLES.get(kind)
    if executable and shutil.which(str(executable)) is None:
        return f"the {kind} harness needs the `{executable}` CLI, which is not on PATH"
    mapped = entry.get("credential_env") or {}
    if mapped:
        missing = sorted(source for source in mapped.values() if source not in os.environ)
        return f"--credential-env source(s) not set: {', '.join(missing)}" if missing else None
    if kind == "claude_code" and not any(os.environ.get(k) for k in CLAUDE_CREDENTIALS):
        return (
            "Claude Code runs in an isolated HOME, so it cannot use your `claude` login; "
            "set ANTHROPIC_API_KEY (see .env.example)"
        )
    if kind == "codex" and not any(os.environ.get(k) for k in CODEX_CREDENTIALS):
        auth = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "auth.json"
        if not auth.is_file():
            return "Codex has no login: run `codex login` or set OPENAI_API_KEY (see .env.example)"
    return None


@pytest.fixture(autouse=True)
def _require_agent_access(request: pytest.FixtureRequest) -> None:
    if "agent" not in request.fixturenames:
        return
    selected = request.getfixturevalue("agent")
    reason = skip_reason(_kind(selected.harness), selected.entry)
    if reason:
        pytest.skip(reason)

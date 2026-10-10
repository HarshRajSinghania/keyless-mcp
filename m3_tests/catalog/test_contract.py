"""Catalog contract: every adapter follows docs/adapter-contract.md.

Parametrised over every adapter found in ``keyless_mcp.adapters``, so a new adapter is checked
the moment it exists. A failure message says exactly what to fix.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import anyio
import pytest

import keyless_mcp.adapters as adapters_pkg
from keyless_mcp.core import TOOLSETS, discover_adapters
from keyless_mcp.core.cassette import EMAIL_RE, REDACTED_EMAIL
from keyless_mcp.server import build_server
from m3_tests._support.servers import ADAPTER_TESTS, cassette_dir

pytestmark = pytest.mark.m3(suite_name="catalog")

ADAPTERS_DIR = Path(adapters_pkg.__path__[0])
# Left in adapter.yaml by `make new-adapter`; a real adapter replaces all of them.
SCAFFOLD_PLACEHOLDERS = ("TODO", "example.com", "your-github-handle", "ADAPTER_")
SPECS = discover_adapters()
BUILT = build_server()
TOOLS = {t.name: t for t in anyio.run(BUILT.mcp.list_tools)}


def _only_caches(directory: Path) -> bool:
    """True for a leftover directory that holds nothing but ``__pycache__`` (for example after
    switching branches), which is not an adapter and not worth failing for."""
    return all(child.name == "__pycache__" for child in directory.iterdir())


def test_every_adapter_directory_has_an_adapter_yaml() -> None:
    """A directory under adapters/ without adapter.yaml would be silently ignored."""
    dirs = {
        p.name
        for p in ADAPTERS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and not _only_caches(p)
    }
    loaded = {s.name for s in SPECS}
    missing = sorted(dirs - loaded)
    assert not missing, (
        f"adapters/{', adapters/'.join(missing)} has no adapter.yaml, so it is not loaded. "
        "Add one (see docs/adapter-contract.md) or delete the directory."
    )


def test_the_template_is_not_loaded_as_an_adapter() -> None:
    assert (ADAPTERS_DIR / "_template" / "adapter.yaml").is_file()
    assert "_template" not in {s.name for s in SPECS}


def test_each_toolset_loads_exactly_its_own_adapters() -> None:
    """Every toolset an adapter declares is a known one, and selecting it registers only the
    adapters that declare it. Data-driven, so adding an adapter or a toolset needs no edit here."""
    used = {s.toolset for s in SPECS}
    assert used <= set(TOOLSETS), f"unknown toolset(s): {sorted(used - set(TOOLSETS))}"
    for toolset in sorted(used):
        loaded = {a.spec.name for a in build_server({toolset}).adapters}
        expected = {s.name for s in SPECS if s.toolset == toolset}
        assert loaded == expected, f"--toolsets {toolset} loaded {sorted(loaded)}"


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_adapter_yaml_is_valid_and_toolset_is_known(spec) -> None:
    assert spec.toolset in TOOLSETS
    assert spec.description.strip() and spec.title.strip()
    assert spec.rate_limit_per_minute > 0


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_adapter_yaml_has_no_leftover_scaffold_placeholders(spec) -> None:
    text = (ADAPTERS_DIR / spec.name / "adapter.yaml").read_text(encoding="utf-8")
    left = [marker for marker in SCAFFOLD_PLACEHOLDERS if marker in text]
    assert not left, (
        f"{spec.name}/adapter.yaml still has scaffold placeholder(s) {left}: fill in the real "
        "description, base_url, docs_url, rate limit and GitHub handle, and drop the TODO notes"
    )


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_every_tool_and_parameter_has_a_description(spec) -> None:
    loaded = next(a for a in BUILT.adapters if a.spec.name == spec.name)
    assert loaded.tool_names, f"{spec.name} registers no tools"
    for name in loaded.tool_names:
        assert name.startswith(f"{spec.name}_"), name
        tool = TOOLS[name]
        assert (tool.description or "").strip(), f"{name}: add a docstring/description"
        for param, schema in tool.input_schema.get("properties", {}).items():
            assert schema.get("description", "").strip(), (
                f"{name}.{param}: describe it with Annotated[..., Field(description=...)]"
            )


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_adapter_has_an_m3_test_file_with_its_own_suite_name(spec) -> None:
    test_file = ADAPTER_TESTS / spec.name / f"test_{spec.name}.py"
    assert test_file.is_file(), f"create {test_file.relative_to(ADAPTER_TESTS.parents[1])}"
    marker = re.search(r'pytest\.mark\.m3\(suite_name="([^"]+)"\)', test_file.read_text())
    assert marker and marker.group(1) == spec.name, (
        f'{test_file.name} needs pytestmark = pytest.mark.m3(suite_name="{spec.name}")'
    )


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_adapter_has_at_least_one_cassette(spec) -> None:
    cassettes = list(cassette_dir(spec.name).glob("*.json"))
    assert cassettes, f"record some with: make record ADAPTER={spec.name}"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def test_adapters_never_import_an_http_library() -> None:
    """All upstream traffic goes through the shared client so User-Agent, rate limits and
    cassette record/replay apply. The template is checked too, so new adapters start clean."""
    offenders = {
        str(path.relative_to(ADAPTERS_DIR)): sorted(_imported_modules(path) & {"httpx", "requests"})
        for path in ADAPTERS_DIR.rglob("*.py")
        if _imported_modules(path) & {"httpx", "requests"}
    }
    assert not offenders, (
        f"adapters must use the `http` handle given to register(), not an HTTP library: {offenders}"
    )


def test_cassettes_contain_no_email_addresses() -> None:
    """Registries list maintainer emails. Recording redacts them (core/cassette.py); this fails
    if a cassette was hand-edited or recorded with an older version."""
    found = {}
    for path in ADAPTER_TESTS.glob("*/cassettes/*.json"):
        emails = set(EMAIL_RE.findall(path.read_text(encoding="utf-8"))) - {REDACTED_EMAIL}
        if emails:
            found[str(path.relative_to(ADAPTER_TESTS))] = sorted(emails)
    assert not found, (
        f"email-shaped strings in cassettes: {found}. Re-record with `make record ADAPTER=<name>` "
        "(the writer redacts emails) or run them through cassette.redact_emails."
    )

"""Catalog contract: every adapter follows docs/adapter-contract.md.

Parametrised over every adapter found in ``keyless_mcp.adapters``, so a new adapter is checked
the moment it exists. A failure message says exactly what to fix.
"""

from __future__ import annotations

import re
from pathlib import Path

import anyio
import pytest

import keyless_mcp.adapters as adapters_pkg
from keyless_mcp.core import TOOLSETS, discover_adapters
from keyless_mcp.server import build_server
from m3_tests._support.servers import ADAPTER_TESTS, cassette_dir

pytestmark = pytest.mark.m3(suite_name="catalog")

ADAPTERS_DIR = Path(adapters_pkg.__path__[0])
SPECS = discover_adapters()
BUILT = build_server()
TOOLS = {t.name: t for t in anyio.run(BUILT.mcp.list_tools)}


def test_every_adapter_directory_has_an_adapter_yaml() -> None:
    """A directory under adapters/ without adapter.yaml would be silently ignored."""
    dirs = {
        p.name for p in ADAPTERS_DIR.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))
    }
    assert dirs == {s.name for s in SPECS}, "every adapter directory needs a valid adapter.yaml"


def test_the_template_is_not_loaded_as_an_adapter() -> None:
    assert (ADAPTERS_DIR / "_template" / "adapter.yaml").is_file()
    assert "_template" not in {s.name for s in SPECS}


def test_there_is_at_least_one_adapter_per_reference_toolset() -> None:
    assert {"science", "dev"} <= {s.toolset for s in SPECS}


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.name)
def test_adapter_yaml_is_valid_and_toolset_is_known(spec) -> None:
    assert spec.toolset in TOOLSETS
    assert spec.description.strip() and spec.title.strip()
    assert spec.rate_limit_per_minute > 0


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

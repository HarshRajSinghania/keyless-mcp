"""Toolset selection: flag, environment variable, validation and the --list-tools table."""

from __future__ import annotations

import os
import subprocess
import sys

import anyio
import pytest

from keyless_mcp.core import AdapterSpec, discover_adapters, parse_toolsets
from keyless_mcp.server import build_server

pytestmark = pytest.mark.m3(suite_name="core")

ARXIV_TOOLS = {"arxiv_search", "arxiv_get_paper"}
OSV_TOOLS = {"osv_query_package", "osv_get_vulnerability"}


def registered_tools(toolsets: set[str] | None) -> set[str]:
    built = build_server(toolsets)
    return {t.name for t in anyio.run(built.mcp.list_tools)}


def toolset_of(tool_name: str) -> str:
    """The toolset of a tool, found through the adapter.yaml of the adapter its name starts with."""
    return next(s.toolset for s in discover_adapters() if tool_name.startswith(f"{s.name}_"))


def cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = {k: v for k, v in os.environ.items() if k != "KEYLESS_MCP_TOOLSETS"}
    full_env.update(env or {})
    return subprocess.run(
        [sys.executable, "-m", "keyless_mcp", *args],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=60,
    )


def test_default_registers_every_adapter() -> None:
    assert registered_tools(None) >= ARXIV_TOOLS | OSV_TOOLS


@pytest.mark.parametrize("toolset", ["science", "dev", "geo", "news"])
def test_a_toolset_registers_exactly_its_own_adapters_tools(toolset) -> None:
    tools = registered_tools({toolset})
    assert {toolset_of(t) for t in tools} <= {toolset}
    assert tools == {t for t in registered_tools(None) if toolset_of(t) == toolset}


def test_reference_adapters_sit_in_their_documented_toolsets() -> None:
    assert registered_tools({"science"}) >= ARXIV_TOOLS
    assert not OSV_TOOLS & registered_tools({"science"})
    assert registered_tools({"dev"}) >= OSV_TOOLS
    assert not ARXIV_TOOLS & registered_tools({"dev"})
    assert registered_tools({"science", "dev"}) >= ARXIV_TOOLS | OSV_TOOLS


def test_parse_toolsets_accepts_commas_case_and_blanks() -> None:
    assert parse_toolsets("Science, dev,") == {"science", "dev"}
    assert parse_toolsets("") is None
    assert parse_toolsets(None) is None


def test_parse_toolsets_rejects_unknown_names_and_lists_valid_ones() -> None:
    with pytest.raises(ValueError, match=r"unknown toolset\(s\): weather.*science, dev, geo, news"):
        parse_toolsets("science,weather")


def test_list_tools_flag_prints_toolset_adapter_and_tool_name() -> None:
    out = cli("--list-tools")
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines()[0].split() == ["TOOLSET", "ADAPTER", "TOOL", "DESCRIPTION"]
    rows = {tuple(line.split()[:3]) for line in out.stdout.splitlines()[1:]}
    assert {
        ("science", "arxiv", "arxiv_search"),
        ("science", "arxiv", "arxiv_get_paper"),
        ("dev", "osv", "osv_query_package"),
        ("dev", "osv", "osv_get_vulnerability"),
    } <= rows


def test_toolsets_flag_limits_the_listing() -> None:
    out = cli("--toolsets", "dev", "--list-tools")
    assert out.returncode == 0, out.stderr
    rows = [line.split() for line in out.stdout.splitlines()[1:]]
    assert {r[0] for r in rows} == {"dev"}
    assert {"osv_query_package", "osv_get_vulnerability"} <= {r[2] for r in rows}


def test_toolsets_env_var_is_used_and_the_flag_overrides_it() -> None:
    from_env = cli("--list-tools", env={"KEYLESS_MCP_TOOLSETS": "science"})
    assert {line.split()[0] for line in from_env.stdout.splitlines()[1:]} == {"science"}
    flag_wins = cli("--toolsets", "dev", "--list-tools", env={"KEYLESS_MCP_TOOLSETS": "science"})
    assert {line.split()[0] for line in flag_wins.stdout.splitlines()[1:]} == {"dev"}


def test_unknown_toolset_exits_with_a_helpful_message() -> None:
    out = cli("--toolsets", "weather", "--list-tools")
    assert out.returncode != 0
    assert "unknown toolset(s): weather" in out.stderr


def test_version_flag() -> None:
    out = cli("--version")
    assert out.returncode == 0
    assert out.stdout.startswith("keyless-mcp ")


def valid_spec() -> dict:
    return {
        "name": "demo",
        "title": "Demo",
        "description": "A demo API.",
        "toolset": "dev",
        "base_url": "https://api.demo.test",
        "docs_url": "https://demo.test/docs",
        "rate_limit_per_minute": 30,
        "author": "someone",
    }


def test_adapter_spec_accepts_a_valid_mapping() -> None:
    spec = AdapterSpec.from_mapping(valid_spec(), expected_name="demo")
    assert (spec.name, spec.toolset, spec.rate_limit_per_minute) == ("demo", "dev", 30)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"toolset": "weather"}, "toolset 'weather' is not one of"),
        ({"rate_limit_per_minute": 0}, "positive integer"),
        ({"rate_limit_per_minute": "fast"}, "positive integer"),
        ({"base_url": "ftp://x"}, "base_url must be an http"),
        ({"name": "Demo-API"}, "lowercase snake_case"),
        ({"name": "other"}, "must match its directory"),
        ({"extra": 1}, "unknown field"),
        ({"author": None}, "missing required field"),
    ],
)
def test_adapter_spec_rejects_invalid_values(change, message) -> None:
    from keyless_mcp.core import AdapterError

    data = {**valid_spec(), **change}
    with pytest.raises(AdapterError, match=message):
        AdapterSpec.from_mapping(data, expected_name="demo")

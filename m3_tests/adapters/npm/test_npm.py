"""npm adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.cassettes import recorded
from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="npm")


def test_lists_both_npm_tools_with_documented_inputs(connect) -> None:
    """The catalog has npm_get_package(name) and npm_search(query, size)."""
    with connect("npm") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("npm_")}
    assert set(tools) == {"npm_get_package", "npm_search"}
    assert list(tools["npm_get_package"].input_schema["required"]) == ["name"]
    assert list(tools["npm_search"].input_schema["required"]) == ["query"]
    assert tools["npm_search"].input_schema["properties"]["size"]["default"] == 10


def test_get_package_summarises_left_pad(connect) -> None:
    """left-pad's last release is 1.3.0 (2018, WTFPL) and carries a deprecation notice."""
    with connect("npm") as client:
        result = client.call_tool("npm_get_package", {"name": "left-pad"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["name"] == "left-pad"
    assert data["latest_version"] == "1.3.0"
    assert data["license"] == "WTFPL"
    assert data["description"] == "String left pad"
    assert data["repository"] == "https://github.com/stevemao/left-pad"
    assert data["last_published"].startswith("2018-04-09")
    assert data["maintainers_count"] >= 1
    assert len(data["maintainers"]) == data["maintainers_count"]
    assert "padStart" in data["deprecated"]
    assert data["version_count"] >= 10
    assert data["url"] == "https://www.npmjs.com/package/left-pad"
    assert "readme" not in data and "versions" not in data, "the huge registry doc is trimmed"


def test_get_package_reports_license_author_and_repository_of_is_odd(connect, replaying) -> None:
    """is-odd is an MIT package by Jon Schlinkert; its git+https repository URL is cleaned up."""
    with connect("npm") as client:
        result = client.call_tool("npm_get_package", {"name": "is-odd"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["license"] == "MIT"
    assert data["author"] == "Jon Schlinkert"
    assert data["repository"] == "https://github.com/jonschlinkert/is-odd"
    assert data["latest_version"].count(".") == 2
    assert data["deprecated"] is None
    if replaying:
        doc = recorded("npm", "https://registry.npmjs.org/is-odd")
        assert data["latest_version"] == doc["dist-tags"]["latest"]


def test_get_package_accepts_a_scoped_name(connect) -> None:
    """A scoped package (@isaacs/string-locale-compare, ISC licensed) is looked up and linked."""
    with connect("npm") as client:
        result = client.call_tool("npm_get_package", {"name": "@isaacs/string-locale-compare"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["name"] == "@isaacs/string-locale-compare"
    assert data["license"] == "ISC"
    assert data["url"] == "https://www.npmjs.com/package/@isaacs/string-locale-compare"
    assert "isaacs" in data["maintainers"]


def test_search_returns_ranked_packages_with_links(connect) -> None:
    """Searching 'lodash' finds the lodash package itself among a few results."""
    with connect("npm") as client:
        result = client.call_tool("npm_search", {"query": "lodash", "size": 3})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["returned"] == len(data["packages"]) == 3
    assert data["total"] >= 3
    lodash = next(p for p in data["packages"] if p["name"] == "lodash")
    assert lodash["url"] == "https://www.npmjs.com/package/lodash"
    assert lodash["weekly_downloads"] > 1_000_000
    assert lodash["version"].startswith("4.")


def test_get_package_reports_an_unknown_package(connect) -> None:
    """The registry's HTTP 404 becomes a readable is_error result pointing at npm_search."""
    with connect("npm") as client:
        result = client.call_tool("npm_get_package", {"name": "zzzz-not-a-real-pkg-qq1"})
    assert result.is_error is True
    text = result_text(result)
    assert "No npm package named 'zzzz-not-a-real-pkg-qq1'" in text
    assert "npm_search" in text


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("npm_get_package", {"name": "../secret"}, "not a valid npm package name"),
        ("npm_get_package", {"name": "a b"}, "not a valid npm package name"),
        ("npm_search", {"query": " "}, "query must not be empty"),
        ("npm_search", {"query": "x", "size": 26}, "size must be between 1 and 25"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Bad names and sizes are is_error results with a fix-it message; no cassette is needed."""
    with connect("npm") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


@pytest.mark.live
def test_live_search_hits_the_real_api(connect) -> None:
    """Smoke test against the real npm registry (excluded from PR CI)."""
    with connect("npm", mode="live") as client:
        result = client.call_tool("npm_search", {"query": "lodash", "size": 1})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["returned"] == 1

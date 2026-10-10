"""PyPI adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.cassettes import recorded
from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="pypi")


def test_lists_both_pypi_tools_with_documented_inputs(connect) -> None:
    """The catalog has pypi_get_package(name) and pypi_get_release(name, version)."""
    with connect("pypi") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("pypi_")}
    assert set(tools) == {"pypi_get_package", "pypi_get_release"}
    assert list(tools["pypi_get_package"].input_schema["required"]) == ["name"]
    assert list(tools["pypi_get_release"].input_schema["required"]) == ["name", "version"]


def test_get_package_returns_the_latest_release_of_six(connect, replaying) -> None:
    """six is a long-stable MIT-licensed package by Benjamin Peterson with a GitHub homepage."""
    with connect("pypi") as client:
        result = client.call_tool("pypi_get_package", {"name": "six"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["name"] == "six"
    assert data["summary"] == "Python 2 and 3 compatibility utilities"
    assert data["license"] == "MIT"
    assert ">=2.7" in data["requires_python"]
    assert data["author"] == "Benjamin Peterson"
    assert data["project_urls"]["Homepage"] == "https://github.com/benjaminp/six"
    assert data["url"] == "https://pypi.org/project/six/"
    assert data["version"].count(".") >= 1
    assert data["release_count"] >= 29
    assert data["release_date"].endswith("Z")
    assert isinstance(data["yanked"], bool)
    if replaying:
        # The latest version and release count grow upstream, so expect the recorded document.
        doc = recorded("pypi", "https://pypi.org/pypi/six/json")
        assert data["version"] == doc["info"]["version"]
        assert data["release_count"] == len(doc["releases"])
        assert data["release_date"] == min(f["upload_time_iso_8601"] for f in doc["urls"])
        assert data["yanked"] is bool(doc["info"]["yanked"])


def test_get_release_returns_a_specific_version_with_its_files(connect) -> None:
    """six 1.16.0 was released on 2021-05-05 as a universal wheel plus a source archive."""
    with connect("pypi") as client:
        result = client.call_tool("pypi_get_release", {"name": "six", "version": "1.16.0"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["version"] == "1.16.0"
    assert data["release_date"].startswith("2021-05-05")
    assert data["license"] == "MIT"
    assert data["url"] == "https://pypi.org/project/six/1.16.0/"
    files = {f["filename"]: f for f in data["files"]}
    assert files["six-1.16.0-py2.py3-none-any.whl"]["type"] == "bdist_wheel"
    assert files["six-1.16.0.tar.gz"]["type"] == "sdist"
    assert all(f["url"].startswith("https://files.pythonhosted.org/") for f in files.values())


def test_get_package_reports_an_unknown_package(connect) -> None:
    """The API's HTTP 404 becomes a readable is_error result naming the package."""
    with connect("pypi") as client:
        result = client.call_tool("pypi_get_package", {"name": "nonexistentpkg-zzzqq"})
    assert result.is_error is True
    assert "No PyPI package named 'nonexistentpkg-zzzqq'" in result_text(result)


def test_get_release_reports_an_unknown_version(connect) -> None:
    """An unknown version is an is_error result that points at pypi_get_package."""
    with connect("pypi") as client:
        result = client.call_tool("pypi_get_release", {"name": "six", "version": "99.99.99"})
    assert result.is_error is True
    text = result_text(result)
    assert "No release '99.99.99' of PyPI package 'six'" in text
    assert "pypi_get_package" in text


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("pypi_get_package", {"name": "../etc/passwd"}, "not a valid PyPI package name"),
        ("pypi_get_package", {"name": " "}, "not a valid PyPI package name"),
        ("pypi_get_release", {"name": "six", "version": "1/../2"}, "not a valid version"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Names and versions that could escape the URL path are rejected without a request."""
    with connect("pypi") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


@pytest.mark.live
def test_live_get_package_hits_the_real_api(connect) -> None:
    """Smoke test against the real PyPI API (excluded from PR CI)."""
    with connect("pypi", mode="live") as client:
        result = client.call_tool("pypi_get_package", {"name": "six"})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["name"] == "six"

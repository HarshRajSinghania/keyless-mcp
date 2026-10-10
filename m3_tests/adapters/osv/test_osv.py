"""OSV adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="osv")

# lodash 4.17.20 is affected by CVE-2021-23337 (command injection), fixed in 4.17.21.
LODASH_COMMAND_INJECTION = "GHSA-35jh-r3h4-6jhm"


def test_lists_both_osv_tools_with_documented_inputs(connect) -> None:
    """The catalog has osv_query_package(name, ecosystem required) and osv_get_vulnerability."""
    with connect("osv") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("osv_")}
    assert set(tools) == {"osv_query_package", "osv_get_vulnerability"}
    assert list(tools["osv_query_package"].input_schema["required"]) == ["name", "ecosystem"]
    assert set(tools["osv_query_package"].input_schema["properties"]) == {
        "name",
        "ecosystem",
        "version",
    }
    assert list(tools["osv_get_vulnerability"].input_schema["required"]) == ["vuln_id"]


def test_query_finds_the_known_lodash_vulnerability(connect) -> None:
    """lodash 4.17.20 (npm) is affected by CVE-2021-23337, which is fixed in 4.17.21."""
    with connect("osv") as client:
        result = client.call_tool(
            "osv_query_package", {"name": "lodash", "ecosystem": "npm", "version": "4.17.20"}
        )
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["ecosystem"] == "npm"
    assert data["total"] == data["returned"] > 0
    vuln = next(v for v in data["vulnerabilities"] if v["id"] == LODASH_COMMAND_INJECTION)
    assert "CVE-2021-23337" in vuln["aliases"]
    assert "4.17.21" in vuln["fixed_versions"]
    assert vuln["url"] == f"https://osv.dev/vulnerability/{LODASH_COMMAND_INJECTION}"


def test_query_accepts_a_case_insensitive_ecosystem_and_reports_no_vulnerabilities(connect) -> None:
    """'pypi' is normalised to 'PyPI'; a patched version returns an empty list, not an error."""
    with connect("osv") as client:
        result = client.call_tool(
            "osv_query_package", {"name": "jinja2", "ecosystem": "pypi", "version": "3.1.6"}
        )
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["ecosystem"] == "PyPI"
    assert data["total"] == 0
    assert list(data["vulnerabilities"]) == []


def test_get_vulnerability_returns_advisory_details(connect) -> None:
    """The lodash advisory has its alias, severity, fixed version and reference links."""
    with connect("osv") as client:
        result = client.call_tool("osv_get_vulnerability", {"vuln_id": LODASH_COMMAND_INJECTION})
    assert result.is_error is False, result_text(result)
    vuln = result.structured_content
    assert vuln["id"] == LODASH_COMMAND_INJECTION
    assert "CVE-2021-23337" in vuln["aliases"]
    assert "command injection" in vuln["summary"].lower()
    assert vuln["severity"] == "HIGH"
    assert any(
        a["package"] == "lodash" and "4.17.21" in a["fixed_versions"] for a in vuln["affected"]
    )
    assert vuln["references"] and all(r["url"] for r in vuln["references"])


def test_query_rejects_an_unknown_ecosystem(connect) -> None:
    """An unknown ecosystem is an is_error result that lists the valid ecosystems."""
    with connect("osv") as client:
        result = client.call_tool("osv_query_package", {"name": "x", "ecosystem": "Bogus"})
    assert result.is_error is True
    text = result_text(result)
    assert "Unknown ecosystem" in text
    assert "PyPI" in text
    assert "npm" in text


def test_get_vulnerability_reports_an_unknown_id(connect) -> None:
    """The API's HTTP 404 becomes a readable is_error result naming the id."""
    with connect("osv") as client:
        result = client.call_tool("osv_get_vulnerability", {"vuln_id": "GHSA-0000-0000-0000"})
    assert result.is_error is True
    assert "No OSV record found with id 'GHSA-0000-0000-0000'" in result_text(result)


def test_get_vulnerability_rejects_a_malformed_id(connect) -> None:
    """An id containing path characters is rejected before any request."""
    with connect("osv") as client:
        result = client.call_tool("osv_get_vulnerability", {"vuln_id": "../etc/passwd"})
    assert result.is_error is True
    assert "not a valid vulnerability id" in result_text(result)


@pytest.mark.live
def test_live_get_vulnerability_hits_the_real_api(connect) -> None:
    """Smoke test against the real OSV API (excluded from PR CI)."""
    with connect("osv", mode="live") as client:
        result = client.call_tool("osv_get_vulnerability", {"vuln_id": LODASH_COMMAND_INJECTION})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["id"] == LODASH_COMMAND_INJECTION

"""Upstream failures reach an MCP client as readable is_error results, never crashes.

These run the real server over stdio against hand-written cassettes, so they exercise the whole
path: HTTP layer -> adapter -> SDK -> MCP result.
"""

from __future__ import annotations

import pytest

from keyless_mcp.core import cassette
from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="core")

OSV_VULN_URL = "https://api.osv.dev/v1/vulns/GHSA-aaaa-bbbb-cccc"


def record(tmp_path, status: int, content_type: str, body) -> None:
    cassette.save(
        tmp_path, "GET", OSV_VULN_URL, None, cassette.RecordedResponse(status, content_type, body)
    )


def call_osv(connect, tmp_path):
    with connect("osv", cassettes=tmp_path) as client:
        result = client.call_tool("osv_get_vulnerability", {"vuln_id": "GHSA-aaaa-bbbb-cccc"})
        # The server must still be alive and answering after a failed call.
        assert any(t.name == "osv_query_package" for t in client.list_all_tools())
    return result


def test_upstream_503_is_an_error_result_with_status_and_url(connect, tmp_path) -> None:
    record(tmp_path, 503, "application/json", {"message": "backend unavailable"})
    result = call_osv(connect, tmp_path)
    assert result.is_error is True
    text = result_text(result)
    assert "HTTP 503" in text
    assert OSV_VULN_URL in text
    assert "backend unavailable" in text


def test_non_json_body_is_an_error_result(connect, tmp_path) -> None:
    record(tmp_path, 200, "application/json", "<html>gateway page</html>")
    result = call_osv(connect, tmp_path)
    assert result.is_error is True
    assert "did not return valid JSON" in result_text(result)


def test_missing_cassette_fails_loudly_with_recording_instructions(connect, tmp_path) -> None:
    result = call_osv(connect, tmp_path)  # empty cassette directory
    assert result.is_error is True
    text = result_text(result)
    assert "no cassette for GET" in text
    assert "GHSA-aaaa-bbbb-cccc" in text
    assert "KEYLESS_MCP_HTTP_MODE=record" in text
    assert "make record ADAPTER=osv" in text


def test_unexpected_response_shape_is_an_error_result_naming_the_missing_field(
    connect, tmp_path
) -> None:
    """A 200 body without the field the adapter reads (KeyError) must not crash the tool."""
    record(tmp_path, 200, "application/json", {"unexpected": "shape"})
    result = call_osv(connect, tmp_path)
    assert result.is_error is True
    text = result_text(result)
    assert "osv: upstream response had an unexpected shape (missing 'id')" in text
    assert "osv_get_vulnerability" in text


def test_a_wrongly_typed_response_is_an_error_result_too(connect, tmp_path) -> None:
    """A JSON list where an object was expected (AttributeError) is reported the same way."""
    record(tmp_path, 200, "application/json", ["not", "an", "object"])
    result = call_osv(connect, tmp_path)
    assert result.is_error is True
    assert "osv: upstream response had an unexpected shape (AttributeError" in result_text(result)

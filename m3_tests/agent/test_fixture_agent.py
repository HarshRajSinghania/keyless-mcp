"""Keyless agent lane: a scripted ACP agent drives keyless-mcp offline, with no model or keys.

This proves the whole agent path end to end (M3 launches an agent, hands it the server, captures
its tool calls off the wire, and ``expect`` asserts on them) without a model. It does NOT show
that a real model picks the right tool; that is ``test_tool_selection.py``.

Marked ``agent_fixture`` and not ``agent``, so ``make test`` and PR CI run it. The server is
pinned to replay mode and serves the adapter's cassettes, so it is offline even when
``KEYLESS_MCP_HTTP_MODE=live`` is exported.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import pytest
from m3 import ExecutionOutcome, MCPTestKit, expect

from m3_tests._support.servers import PROJECT_ROOT, keyless_server

pytestmark = [pytest.mark.m3(suite_name="agent-fixture"), pytest.mark.agent_fixture]

SCRIPTED_AGENT = PROJECT_ROOT / "m3_tests" / "_support" / "scripted_acp_agent.py"
MANIFEST = {
    "schema_version": "m3.harness.v1",
    "protocol": "acp",
    "protocol_version": 1,
    "command": sys.executable,
    "args": [str(SCRIPTED_AGENT)],
}


def _run_script(adapter: str, calls: list[dict[str, Any]], tools: list[str]) -> tuple[Any, str]:
    """Run a scripted ACP agent on ``adapter``'s cassettes; return ``(M3 result, server alias)``."""
    server = keyless_server(adapter, mode="replay")
    with MCPTestKit(env={}) as kit:
        agent = kit.agents([{"harness": "acp", "models": ["scripted"], "manifest": MANIFEST}])[0]
        result = agent.run(
            json.dumps({"calls": calls}),
            server=server,
            tools=[f"{server.name}:{name}" for name in tools],
            timeout=60,
        )
    assert result.snapshot.outcome is ExecutionOutcome.COMPLETED, result.error
    return result, server.name


def test_scripted_agent_queries_osv_for_a_vulnerable_package() -> None:
    """The captured osv_query_package call and its replayed result are visible to M3."""
    args = {"name": "lodash", "ecosystem": "npm", "version": "4.17.20"}
    result, alias = _run_script(
        "osv", [{"tool": "osv_query_package", "arguments": args}], ["osv_query_package"]
    )
    expect(result).to_have_tool_call(
        "osv_query_package", server=alias, arguments=args, status="success", count=1
    )
    captured = result.trace_view.tool_calls[0].result.value
    assert "GHSA-35jh-r3h4-6jhm" in captured.content[0].text


def test_scripted_agent_reads_a_wikipedia_summary() -> None:
    """A second adapter, to show the lane is not wired to one server."""
    args = {"title": "Alan Turing"}
    result, alias = _run_script(
        "wikipedia",
        [{"tool": "wikipedia_get_summary", "arguments": args}],
        ["wikipedia_get_summary"],
    )
    expect(result).to_have_tool_call(
        "wikipedia_get_summary", server=alias, arguments=args, status="success", count=1
    )
    captured = result.trace_view.tool_calls[0].result.value
    assert "mathematician" in captured.content[0].text


def test_replay_never_reaches_the_network_for_an_unrecorded_request() -> None:
    """A call with no cassette fails loudly as a tool error instead of going to the real API."""
    args = {"name": "keyless-mcp-no-such-cassette", "ecosystem": "npm", "version": "0.0.1"}
    result, alias = _run_script(
        "osv", [{"tool": "osv_query_package", "arguments": args}], ["osv_query_package"]
    )
    expect(result).to_have_tool_call(
        "osv_query_package", server=alias, arguments=args, status="tool_error", count=1
    )
    captured = result.trace_view.tool_calls[0].result.value
    assert "make record" in captured.content[0].text

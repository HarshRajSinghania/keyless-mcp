"""A deterministic ACP agent for the keyless agent lane: no model, no network, no API keys.

M3 launches this file as an ACP agent (see ``m3_tests/agent/test_fixture_agent.py``). It does
not decide anything. The prompt is a JSON script, ``{"calls": [{"tool": ..., "arguments":
{...}}, ...]}``, and the agent runs each call against the MCP server M3 hands it in
``session/new``, in order, then reports every tool result as its answer.

Because M3 gives the agent a capture proxy rather than the server itself, the calls show up in
M3's trace exactly as a real agent's would. That is what lets ``expect(result).to_have_tool_call``
run offline against the same code path a real harness uses.

This is the same shape as the ``deterministic_acp_agent.py`` example in M3's ACP docs, extended
to run a list of calls and to stop on the first error.
"""

from __future__ import annotations

import asyncio
import json

from acp import Agent, Client, run_agent
from acp.schema import (
    AgentMessageChunk,
    Implementation,
    InitializeResponse,
    NewSessionResponse,
    PromptResponse,
    TextContentBlock,
)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ScriptedAgent(Agent):
    def on_connect(self, conn: Client) -> None:
        self.client = conn

    async def initialize(self, protocol_version, **kwargs):
        return InitializeResponse(
            protocol_version=1,
            agent_info=Implementation(name="keyless-scripted-agent", version="1"),
        )

    async def new_session(self, cwd, mcp_servers=None, **kwargs):
        self.server = mcp_servers[0]
        self.cwd = cwd
        return NewSessionResponse(session_id="scripted-session")

    async def prompt(self, session_id, prompt, **kwargs):
        text = " ".join(block.text for block in prompt if isinstance(block, TextContentBlock))
        script = json.loads(text)
        params = StdioServerParameters(
            command=self.server.command,
            args=self.server.args,
            env={item.name: item.value for item in self.server.env},
            cwd=self.cwd,
        )
        answers: list[str] = []
        async with stdio_client(params) as (read, write), ClientSession(read, write) as mcp:
            await mcp.initialize()
            await mcp.list_tools()
            for call in script["calls"]:
                result = await mcp.call_tool(call["tool"], call["arguments"])
                answers.append("".join(item.text for item in result.content if item.type == "text"))
                if result.is_error:
                    break
        await self.client.session_update(
            session_id,
            AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text="\n".join(answers)),
            ),
        )
        return PromptResponse(stop_reason="end_turn")


if __name__ == "__main__":
    asyncio.run(run_agent(ScriptedAgent()))

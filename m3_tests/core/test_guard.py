"""The registry's shape guard: KeyError/TypeError/IndexError/AttributeError in a tool become
readable errors, are logged with a traceback, and leave the tool's signature intact."""

from __future__ import annotations

import inspect
import logging

import anyio
import pytest

from keyless_mcp.core import ToolRegistry, UpstreamError

pytestmark = pytest.mark.m3(suite_name="core")


class StubServer:
    """Stands in for MCPServer: remembers the function registered for each tool name."""

    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def add_tool(self, fn, *, name, **_kwargs) -> None:
        self.tools[name] = fn


def registered(adapter: str = "demo") -> tuple[ToolRegistry, StubServer]:
    stub = StubServer()
    return ToolRegistry(stub, adapter), stub  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("exc", "detail"),
    [
        (KeyError("id"), "missing 'id'"),
        (IndexError("list index out of range"), "IndexError: list index out of range"),
        (TypeError("'NoneType' object is not subscriptable"), "TypeError: 'NoneType'"),
        (AttributeError("'list' object has no attribute 'get'"), "AttributeError: 'list'"),
    ],
)
def test_sync_tool_shape_errors_become_upstream_errors(exc, detail, caplog) -> None:
    """The sync branch of the guard maps the error, names the adapter and tool, and logs it."""
    registry, stub = registered()

    @registry.tool()
    def demo_read(value: int = 1) -> dict:
        """Demo tool."""
        raise exc

    with (
        caplog.at_level(logging.WARNING, logger="keyless_mcp"),
        pytest.raises(UpstreamError) as caught,
    ):
        stub.tools["demo_read"](value=2)
    message = str(caught.value)
    assert message.startswith("demo: upstream response had an unexpected shape")
    assert detail in message
    assert "demo_read" in message
    assert "adapter has a bug" in message
    assert caught.value.__cause__ is exc
    record = next(r for r in caplog.records if r.name == "keyless_mcp")
    assert record.levelno == logging.WARNING
    assert record.exc_info and record.exc_info[1] is exc, "the traceback must be logged"


def test_async_tool_shape_errors_are_mapped_and_logged(caplog) -> None:
    registry, stub = registered()

    @registry.tool()
    async def demo_fetch() -> dict:
        """Demo tool."""
        return {}["missing"]

    with (
        caplog.at_level(logging.WARNING, logger="keyless_mcp"),
        pytest.raises(UpstreamError, match="missing 'missing'"),
    ):
        anyio.run(stub.tools["demo_fetch"])
    assert any(r.exc_info for r in caplog.records)


def test_other_errors_and_results_pass_through_unchanged() -> None:
    registry, stub = registered()

    @registry.tool()
    def demo_ok(value: int = 1) -> dict:
        """Demo tool."""
        if value < 0:
            raise ValueError("not a shape error")
        return {"value": value}

    assert stub.tools["demo_ok"](value=5) == {"value": 5}
    with pytest.raises(ValueError, match="not a shape error"):
        stub.tools["demo_ok"](value=-1)


def test_the_wrapper_keeps_the_original_signature_and_docstring() -> None:
    registry, stub = registered()

    @registry.tool()
    def demo_sig(a: int, b: str = "x") -> dict:
        """Original docstring."""
        return {}

    wrapper = stub.tools["demo_sig"]
    assert str(inspect.signature(wrapper)) == str(inspect.signature(demo_sig))
    assert wrapper.__doc__ == "Original docstring."

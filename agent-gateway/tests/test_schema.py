from __future__ import annotations
from typing import Literal
from unittest.mock import MagicMock

import pytest

from agent_gateway.runner import SubprocessRunner
from agent_gateway.schema import CapturingMCP, ToolRecord, _make_proxy


def test_capturing_mcp_records_tool() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = {"ok": True}
    cap = CapturingMCP("agent-gateway", runner)

    def my_tool(name: str = "world") -> str:
        """Say hello."""
        return f"hello, {name}"

    decorator = cap.tool(name="ns__my_tool", description="greets")
    decorator(my_tool)

    assert len(cap.captures) == 1
    rec = cap.captures[0]
    assert rec.full_name == "ns__my_tool"
    assert rec.bare_name == "my_tool"
    assert rec.description == "greets"
    assert rec.source_func is my_tool


def test_capturing_mcp_registers_proxy_with_real_fastmcp() -> None:
    from mcp.server.fastmcp import FastMCP
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = "ok"
    cap = CapturingMCP("agent-gateway", runner)

    def my_tool(name: str = "world") -> str:
        """Say hello."""
        return f"hi, {name}"

    cap.tool(name="ns__my_tool", description="greets")(my_tool)

    real = cap.real
    tools = real._tool_manager.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "ns__my_tool"
    assert tools[0].description == "greets"


def test_proxy_preserves_signature_for_schema() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = "ok"
    cap = CapturingMCP("agent-gateway", runner)

    def greet(name: str, greeting: Literal["hi", "hey"] = "hi") -> str:
        """Say hi."""
        return f"{greeting}, {name}"

    cap.tool(name="ns__greet")(greet)
    real = cap.real
    tool_obj = real._tool_manager.get_tool("ns__greet")

    # The registered function should have type hints so FastMCP builds a schema
    fn = tool_obj.fn
    assert fn.__name__ == "greet"
    schema = tool_obj.parameters
    assert "name" in schema["properties"]
    assert "greeting" in schema["properties"]
    assert set(schema["required"]) == {"name"}


def test_proxy_invokes_runner_with_full_name_and_args() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = {"echoed": "hi"}
    cap = CapturingMCP("agent-gateway", runner)

    def echo(text: str) -> dict:
        return {"echoed": text}

    cap.tool(name="ns__echo")(echo)
    real = cap.real
    tool_obj = real._tool_manager.get_tool("ns__echo")

    result = tool_obj.fn(text="hi")
    runner.run.assert_called_once()
    args = runner.run.call_args
    # First positional arg is the full_name
    assert args[0][0] == "ns__echo"
    # Second positional arg is the kwargs dict
    assert args[0][1] == {"text": "hi"}
    assert result == {"echoed": "hi"}


def test_make_proxy_carries_docstring() -> None:
    def f(x: int) -> int:
        """the doc"""
        return x

    proxy = _make_proxy("ns__f", "f", MagicMock(), f)
    assert proxy.__doc__ == "the doc"
    assert proxy.__name__ == "f"


def test_captures_property_returns_copy() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    cap = CapturingMCP("agent-gateway", runner)

    def f(x: int) -> int:
        return x

    cap.tool(name="ns__f")(f)
    caps1 = cap.captures
    caps2 = cap.captures
    assert caps1 is not caps2
    assert caps1 == caps2

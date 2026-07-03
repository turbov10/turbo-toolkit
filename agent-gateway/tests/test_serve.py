from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_gateway.mcp_server import build_server, ServerHandle
from agent_gateway.config import GatewayConfig


def test_build_server_with_no_tools(tmp_path: Path) -> None:
    cfg = GatewayConfig(root=tmp_path, exclude=["agent-gateway"], timeout_seconds=30, tools={})
    handle = build_server(cfg)
    assert isinstance(handle, ServerHandle)
    assert handle.captures == []
    assert handle.fastmcp is not None


def test_build_server_registers_discovered_tools(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    cfg = GatewayConfig(root=fake_monorepo, exclude=["agent-gateway"], timeout_seconds=30, tools={})
    handle = build_server(cfg)
    names = {c.full_name for c in handle.captures}
    assert "alpha__hello" in names
    # The real FastMCP should also have the tool
    fast_tools = handle.fastmcp._tool_manager.list_tools()
    fast_names = {t.name for t in fast_tools}
    assert "alpha__hello" in fast_names


def test_build_server_uses_per_tool_timeout(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    cfg = GatewayConfig(
        root=fake_monorepo,
        exclude=["agent-gateway"],
        timeout_seconds=30,
        tools={"alpha": {"timeout_seconds": 99}},
    )
    handle = build_server(cfg)
    rec = next(c for c in handle.captures if c.full_name == "alpha__hello")
    # The captured record doesn't store timeout; verify it's used in the runner instead
    # by checking that the runner per-tool timeout dict got populated
    assert handle.runner_timeouts.get("alpha") == 99

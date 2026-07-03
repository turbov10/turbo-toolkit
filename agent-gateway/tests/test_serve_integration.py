"""End-to-end: spawn the real CLI as a subprocess, drive it via mcp.client.

This is the P1 acceptance test: `serve` starts, `list` reports tools, and
`call` works through real stdio.
"""
from __future__ import annotations
import asyncio
import json
import sys
import textwrap
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _write_stub_tool(tool_dir: Path, namespace: str, fn_name: str, return_value: str) -> None:
    tool_dir.mkdir(parents=True, exist_ok=True)
    (tool_dir / "mcp_tools.py").write_text(textwrap.dedent(f'''
        import argparse
        import json
        TOOL_NAMESPACE = {namespace!r}

        def {fn_name}(name: str = "world") -> dict:
            return {{"value": {return_value!r}}}

        def register(mcp):
            mcp.tool(
                name=f"{{TOOL_NAMESPACE}}__{fn_name}",
                description=f"stub tool returning {return_value!r}",
            )({fn_name})

        if __name__ == "__main__":
            _parser = argparse.ArgumentParser()
            _sub = _parser.add_subparsers(dest="cmd", required=True)
            _call_p = _sub.add_parser("call")
            _call_p.add_argument("--name", required=True)
            _call_p.add_argument("--args", default="{{}}")
            _ns = _parser.parse_args()
            if _ns.cmd == "call":
                _func = globals()[_ns.name]
                _result = _func(**json.loads(_ns.args))
                print(json.dumps(_result, ensure_ascii=False))
    ''').lstrip())


@pytest.mark.asyncio
async def test_serve_lists_tools_via_mcp(tmp_path: Path) -> None:
    _write_stub_tool(tmp_path / "alpha-tool", "alpha", "hello", "hi")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent_gateway", "serve", "--root", str(tmp_path)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = {t.name for t in result.tools}
            assert "alpha__hello" in names


@pytest.mark.asyncio
async def test_serve_calls_tool_via_mcp(tmp_path: Path) -> None:
    _write_stub_tool(tmp_path / "alpha-tool", "alpha", "echo", "pong")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent_gateway", "serve", "--root", str(tmp_path)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("alpha__echo", {"name": "x"})
            assert not result.isError
            text = result.content[0].text
            assert json.loads(text) == {"value": "pong"}


@pytest.mark.asyncio
async def test_serve_with_no_tools(tmp_path: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "agent_gateway", "serve", "--root", str(tmp_path)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            assert result.tools == []

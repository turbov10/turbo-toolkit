from __future__ import annotations
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke the gateway CLI as a subprocess and capture output."""
    cmd = [sys.executable, "-m", "agent_gateway", *args]
    return subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=str(cwd) if cwd else None,
    )


def test_version_prints_to_stdout() -> None:
    result = run_cli("version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_help_prints_subcommands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    for sub in ("serve", "list", "call", "info", "version"):
        assert sub in result.stdout


def test_no_args_prints_help_and_exits_nonzero() -> None:
    result = run_cli()
    assert result.returncode != 0


def test_list_with_no_tools(tmp_path: Path) -> None:
    result = run_cli("list", "--root", str(tmp_path))
    assert result.returncode == 0
    assert "no tools" in result.stdout.lower()


def test_list_with_stub_tool(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    result = run_cli("list", "--root", str(fake_monorepo))
    assert result.returncode == 0
    assert "alpha__hello" in result.stdout
    assert "stub tool" in result.stdout


def test_list_json_format(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    result = run_cli("list", "--root", str(fake_monorepo), "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert any(t["full_name"] == "alpha__hello" for t in data)


def test_info_with_unknown_tool(tmp_path: Path) -> None:
    result = run_cli("info", "nonexistent__nope", "--root", str(tmp_path))
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


def test_info_with_known_tool(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    result = run_cli("info", "alpha__hello", "--root", str(fake_monorepo))
    assert result.returncode == 0
    assert "alpha__hello" in result.stdout
    # Should include the function signature / parameter schema
    assert "name" in result.stdout


def test_call_with_known_tool(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    # Tool returns the literal string "world" regardless of input
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="world")
    result = run_cli(
        "call", "alpha__hello", "--args", '{"name": "x"}',
        "--root", str(fake_monorepo),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == "world"


def test_call_unknown_tool(tmp_path: Path) -> None:
    result = run_cli("call", "missing__nope", "--root", str(tmp_path))
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


def test_call_propagates_tool_error(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    # Tool that raises
    tool_dir = fake_monorepo / "alpha-tool"
    (tool_dir / "mcp_tools.py").write_text(textwrap.dedent("""
        import argparse
        import json
        TOOL_NAMESPACE = "alpha"
        def boom() -> str:
            raise RuntimeError("kaboom")
        def register(mcp):
            mcp.tool(name="alpha__boom", description="explodes")(boom)
        if __name__ == "__main__":
            _parser = argparse.ArgumentParser()
            _sub = _parser.add_subparsers(dest="cmd", required=True)
            _call_p = _sub.add_parser("call")
            _call_p.add_argument("--name", required=True)
            _call_p.add_argument("--args", default="{}")
            _ns = _parser.parse_args()
            if _ns.cmd == "call":
                _func = globals()[_ns.name]
                _result = _func(**json.loads(_ns.args))
                print(json.dumps(_result, ensure_ascii=False))
    """).lstrip())
    result = run_cli("call", "alpha__boom", "--root", str(fake_monorepo))
    assert result.returncode != 0
    # stderr should contain the original error
    combined = (result.stdout + result.stderr).lower()
    assert "kaboom" in combined

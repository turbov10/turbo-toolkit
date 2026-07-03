from __future__ import annotations
import json
import subprocess
import sys
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

from __future__ import annotations
import json
from pathlib import Path
import textwrap
from unittest.mock import patch, MagicMock

import pytest

from agent_gateway.discovery import DiscoveredTool
from agent_gateway.runner import SubprocessRunner, ToolRunError


def _make_tool(tmp_path: Path, *, with_venv: bool = True) -> DiscoveredTool:
    if with_venv:
        venv_bin = tmp_path / "fake-tool" / ".venv" / "bin"
        venv_bin.mkdir(parents=True)
        venv_py = venv_bin / "python"
        venv_py.write_text("")  # exists
    else:
        venv_py = Path("/usr/bin/python3")
    return DiscoveredTool(
        namespace="fake",
        tool_dir=tmp_path / "fake-tool",
        mcp_tools_path=tmp_path / "fake-tool" / "mcp_tools.py",
        venv_python=venv_py,
        system_python=Path("/usr/bin/python3"),
    )


def test_run_builds_correct_command(tmp_path: Path) -> None:
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    fake_proc = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
    with patch("agent_gateway.runner.subprocess.run", return_value=fake_proc) as mock_run:
        result = runner.run("fake__hello", {"name": "world"}, timeout=10)
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[0] == str(tool.venv_python)
    assert cmd[1] == str(tool.mcp_tools_path)
    assert cmd[2] == "call"
    assert cmd[3] == "--name"
    assert cmd[4] == "hello"
    assert cmd[5] == "--args"
    assert json.loads(cmd[6]) == {"name": "world"}
    assert kwargs["timeout"] == 10
    assert kwargs["cwd"] == tool.tool_dir
    assert result == {"ok": True}


def test_run_returns_parsed_json(tmp_path: Path) -> None:
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    fake_proc = MagicMock(returncode=0, stdout=json.dumps({"text": "hi"}), stderr="")
    with patch("agent_gateway.runner.subprocess.run", return_value=fake_proc):
        result = runner.run("fake__echo", {"x": 1}, timeout=10)
    assert result == {"text": "hi"}


def test_run_nonzero_exit_raises(tmp_path: Path) -> None:
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    fake_proc = MagicMock(returncode=2, stdout="", stderr="unknown tool")
    with patch("agent_gateway.runner.subprocess.run", return_value=fake_proc):
        with pytest.raises(ToolRunError, match="unknown tool"):
            runner.run("fake__missing", {}, timeout=10)


def test_run_timeout_raises(tmp_path: Path) -> None:
    import subprocess as sp
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    with patch(
        "agent_gateway.runner.subprocess.run",
        side_effect=sp.TimeoutExpired(cmd=["x"], timeout=5),
    ):
        with pytest.raises(ToolRunError, match="timeout"):
            runner.run("fake__slow", {}, timeout=5)


def test_run_bad_json_raises(tmp_path: Path) -> None:
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    fake_proc = MagicMock(returncode=0, stdout="not json", stderr="")
    with patch("agent_gateway.runner.subprocess.run", return_value=fake_proc):
        with pytest.raises(ToolRunError, match="invalid JSON"):
            runner.run("fake__broken", {}, timeout=10)


def test_run_empty_stderr_uses_exit_code_in_error(tmp_path: Path) -> None:
    tool = _make_tool(tmp_path)
    runner = SubprocessRunner()
    runner.register(tool)
    fake_proc = MagicMock(returncode=7, stdout="", stderr="")
    with patch("agent_gateway.runner.subprocess.run", return_value=fake_proc):
        with pytest.raises(ToolRunError, match="exit 7"):
            runner.run("fake__x", {}, timeout=10)


def test_run_unknown_namespace_raises(tmp_path: Path) -> None:
    runner = SubprocessRunner()
    with pytest.raises(ToolRunError, match="no tool registered"):
        runner.run("nosuch__nope", {}, timeout=10)

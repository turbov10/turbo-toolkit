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

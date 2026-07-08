"""Smoke tests for ``image-ocr/mcp_tools.py``."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mcp_tools import ocr_image, TOOL_NAMESPACE, register


def test_namespace_constant():
    assert TOOL_NAMESPACE == "image-ocr"


def test_ocr_image_default_text_detail(tiny_png):
    out = ocr_image(image_path=str(tiny_png))
    assert "text" in out
    assert "meta" in out
    assert out["meta"]["engine"] in ("vision", "rapidocr")


def test_ocr_image_path_and_base64_exclusive():
    with pytest.raises(Exception):
        ocr_image(image_path="x", image_base64="y")


def test_ocr_image_pass_through_engine_and_detail(tiny_png):
    out = ocr_image(
        image_path=str(tiny_png), engine="rapidocr", detail="lines",
    )
    assert "lines" in out
    assert out["meta"]["engine"] == "rapidocr"


def test_register_wires_tool(monkeypatch, tiny_png):
    """Stub CapturingMCP locally — agent_gateway's package is not installed in
    this tool's venv by design (tool isolation: AGENTS.md §1)."""
    class _StubCap:
        def __init__(self):
            self.captures = []
        def tool(self, *, name, description=None):
            def deco(fn):
                self.captures.append((name, description))
                return fn
            return deco
    cap = _StubCap()
    register(cap)
    assert any(n == "image-ocr__ocr_image" for n, _ in cap.captures)


def test_cli_call_via_subprocess_text(tiny_png):
    """Contract §4 rule 5: mcp_tools.py call ... exits 0 on success, prints JSON."""
    tool_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tool_dir) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(tool_dir / "mcp_tools.py"),
         "call", "--name", "ocr_image",
         "--args", json.dumps({
             "image_path": str(tiny_png),
             "engine": "rapidocr",
             "detail": "text",
         })],
        capture_output=True, text=True, env=env, cwd=str(tool_dir),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert "text" in payload
    assert payload["meta"]["engine"] == "rapidocr"


def test_cli_call_unknown_tool_exits_2():
    tool_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tool_dir) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(tool_dir / "mcp_tools.py"),
         "call", "--name", "no_such_tool", "--args", "{}"],
        capture_output=True, text=True, env=env, cwd=str(tool_dir),
    )
    assert proc.returncode == 2
    assert "unknown tool" in proc.stderr

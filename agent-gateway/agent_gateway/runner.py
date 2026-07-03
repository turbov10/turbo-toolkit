"""Spawn a tool's venv python to execute a tool call as a subprocess."""
from __future__ import annotations
import json
import logging
import subprocess
from pathlib import Path

from agent_gateway.discovery import DiscoveredTool

log = logging.getLogger(__name__)


class ToolRunError(Exception):
    """Raised when a tool subprocess fails (non-zero exit, timeout, bad output)."""


class SubprocessRunner:
    """Dispatches tool calls to `<tool>/.venv/bin/python <tool>/mcp_tools.py call ...`.

    The runner holds a registry of DiscoveredTool objects indexed by namespace,
    so callers (CLI or CapturingMCP proxy) only need the full name.
    """

    def __init__(self) -> None:
        self._registry: dict[str, DiscoveredTool] = {}

    def register(self, tool: DiscoveredTool) -> None:
        """Register a tool so its namespace can be dispatched."""
        self._registry[tool.namespace] = tool

    def lookup(self, namespace: str) -> DiscoveredTool | None:
        return self._registry.get(namespace)

    def run(
        self,
        full_name: str,
        args: dict,
        *,
        timeout: float = 30,
    ) -> dict:
        """Dispatch a call to the tool's venv python. Returns the parsed JSON result.

        `full_name` is `<namespace>__<bare_name>` (e.g. "image-ocr__ocr_image").
        """
        namespace, sep, bare_name = full_name.partition("__")
        if not sep or not bare_name:
            raise ToolRunError(f"invalid full_name (expected namespace__tool): {full_name!r}")
        tool = self._registry.get(namespace)
        if tool is None:
            raise ToolRunError(f"no tool registered for namespace: {namespace!r}")

        cmd = [
            str(tool.venv_python),
            str(tool.mcp_tools_path),
            "call",
            "--name",
            bare_name,
            "--args",
            json.dumps(args, ensure_ascii=False),
        ]
        log.debug("dispatching: %s", cmd)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tool.tool_dir,
            )
        except subprocess.TimeoutExpired as e:
            raise ToolRunError(f"timeout after {timeout}s") from e
        except FileNotFoundError as e:
            raise ToolRunError(f"python not found: {cmd[0]}") from e

        if proc.returncode != 0:
            msg = proc.stderr.strip() if proc.stderr else f"exit {proc.returncode}"
            raise ToolRunError(msg)
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise ToolRunError(f"invalid JSON from tool: {e}") from e

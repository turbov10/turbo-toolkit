"""Wire discovery + runner + CapturingMCP into a runnable FastMCP server."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from agent_gateway.config import GatewayConfig
from agent_gateway.discovery import discover_all
from agent_gateway.runner import SubprocessRunner
from agent_gateway.schema import CapturingMCP, ToolRecord

log = logging.getLogger(__name__)


@dataclass
class ServerHandle:
    """Result of build_server(): everything the CLI needs to serve or inspect."""
    fastmcp: FastMCP
    captures: list[ToolRecord]
    runner: SubprocessRunner
    runner_timeouts: dict[str, int] = field(default_factory=dict)


def build_server(cfg: GatewayConfig) -> ServerHandle:
    """Discover tools, build a CapturingMCP, register each module, return the handle."""
    runner = SubprocessRunner()
    capturing = CapturingMCP("agent-gateway", runner)

    discovered = discover_all(cfg.root, exclude=cfg.exclude, strict=False)
    runner_timeouts: dict[str, int] = {}

    for tool in discovered:
        runner.register(tool)
        if tool.namespace in cfg.tools:
            override = cfg.tools[tool.namespace]
            if "timeout_seconds" in override:
                runner_timeouts[tool.namespace] = int(override["timeout_seconds"])
        try:
            module = _reload_module(tool.mcp_tools_path)
        except Exception as e:
            log.error("failed to import %s: %s", tool.mcp_tools_path, e)
            continue
        try:
            module.register(capturing)
        except Exception as e:
            log.error("register() raised in %s: %s", tool.mcp_tools_path, e)
            continue
        log.info("registered namespace %s from %s", tool.namespace, tool.tool_dir.name)

    return ServerHandle(
        fastmcp=capturing.real,
        captures=capturing.captures,
        runner=runner,
        runner_timeouts=runner_timeouts,
    )


def _reload_module(mcp_tools_path: Path) -> Any:
    """Re-import a tool's mcp_tools.py (cached) so multiple tools with same name work."""
    import importlib.util
    import sys
    mod_name = f"_agent_gateway_loaded_{mcp_tools_path.parent.name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, mcp_tools_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module

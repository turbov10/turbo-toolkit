"""Walk the monorepo, import each tool's mcp_tools.py, validate the contract."""
from __future__ import annotations
import importlib.util
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterable

log = logging.getLogger(__name__)


class DiscoveryError(Exception):
    """Raised when a tool's mcp_tools.py fails validation (strict mode only)."""


@dataclass(frozen=True)
class DiscoveredTool:
    namespace: str
    tool_dir: Path
    mcp_tools_path: Path
    venv_python: Path
    system_python: Path

    @property
    def bare_python(self) -> str:
        return str(self.venv_python)

    @property
    def call_args_template(self) -> tuple[str, ...]:
        return (str(self.venv_python), str(self.mcp_tools_path), "call")


def discover_all(
    monorepo_root: Path,
    *,
    exclude: Iterable[str] = ("agent-gateway", ".github", "docs"),
    strict: bool = False,
) -> list[DiscoveredTool]:
    """Find every `<dir>/mcp_tools.py` in `monorepo_root` and load it.

    `exclude` is a list of directory names (not paths) to skip.
    In strict mode, missing TOOL_NAMESPACE / non-callable register raise.
    In non-strict mode (default), such tools are logged and skipped.
    """
    monorepo_root = Path(monorepo_root).resolve()
    exclude_set = set(exclude)
    system_python = Path(sys.executable).resolve()

    results: list[DiscoveredTool] = []
    for child in sorted(monorepo_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in exclude_set or child.name.startswith("."):
            continue
        mcp_tools = child / "mcp_tools.py"
        if not mcp_tools.is_file():
            continue
        try:
            tool = _load_one(child, mcp_tools, system_python)
        except DiscoveryError as e:
            if strict:
                raise
            log.warning("skipping %s: %s", child.name, e)
            continue
        results.append(tool)
    return results


def _load_one(tool_dir: Path, mcp_tools_path: Path, system_python: Path) -> DiscoveredTool:
    module = _import_module(mcp_tools_path)
    if not hasattr(module, "TOOL_NAMESPACE"):
        raise DiscoveryError(f"{mcp_tools_path}: missing TOOL_NAMESPACE")
    namespace = module.TOOL_NAMESPACE
    if not isinstance(namespace, str) or not namespace:
        raise DiscoveryError(f"{mcp_tools_path}: TOOL_NAMESPACE must be a non-empty string")
    if not callable(getattr(module, "register", None)):
        raise DiscoveryError(f"{mcp_tools_path}: missing callable register(mcp)")
    return DiscoveredTool(
        namespace=namespace,
        tool_dir=tool_dir.resolve(),
        mcp_tools_path=mcp_tools_path.resolve(),
        venv_python=_detect_venv_python(tool_dir, system_python),
        system_python=system_python,
    )


def _import_module(path: Path) -> ModuleType:
    """Import a tool's mcp_tools.py and cache it in sys.modules.

    Using a stable synthetic name and caching means `mcp_server._reload_module`
    (which uses the same naming scheme) reuses the cached module instead of
    re-executing the file's top-level code. This matters for P2+ tools that
    have non-idempotent top-level side effects (logging init, network pools,
    env var mutation).
    """
    mod_name = f"_agent_gateway_tool_{path.parent.name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise DiscoveryError(f"{path}: cannot import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _detect_venv_python(tool_dir: Path, fallback: Path) -> Path:
    """Return <tool_dir>/.venv/bin/python (or Scripts\\python.exe) if it exists."""
    if sys.platform == "win32":
        candidate = tool_dir / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = tool_dir / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else fallback

"""Gateway configuration: optional gateway.yaml with sensible defaults."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_EXCLUDE = ["agent-gateway", ".github", "docs"]
DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class GatewayConfig:
    root: Path
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))
    timeout_seconds: int = DEFAULT_TIMEOUT
    tools: dict[str, dict[str, Any]] = field(default_factory=dict)


def load_config(path: Path | None) -> GatewayConfig:
    """Load a GatewayConfig from a YAML file, or return defaults.

    If `path` is None or does not exist, defaults are used with `root` set
    to the parent of the agent-gateway/ directory (i.e. the monorepo root).
    """
    if path is None or not Path(path).exists():
        return _default_config(path)

    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"gateway config must be a mapping, got {type(raw).__name__}")

    root = Path(raw.get("root", path.parent))
    if not root.is_absolute():
        root = (path.parent / root).resolve()
    else:
        root = root.resolve()

    exclude = raw.get("exclude", list(DEFAULT_EXCLUDE))
    if isinstance(exclude, str):
        exclude = [exclude]

    return GatewayConfig(
        root=root,
        exclude=list(exclude),
        timeout_seconds=int(raw.get("timeout_seconds", DEFAULT_TIMEOUT)),
        tools=dict(raw.get("tools") or {}),
    )


def _default_config(path: Path | None) -> GatewayConfig:
    """Build a default config rooted at the parent of the agent-gateway/ dir."""
    here = Path(__file__).resolve().parent  # .../agent-gateway/agent_gateway/
    if path is not None and not path.exists():
        root = path.resolve().parent
    else:
        root = here.parent.parent  # monorepo root
    return GatewayConfig(root=root)

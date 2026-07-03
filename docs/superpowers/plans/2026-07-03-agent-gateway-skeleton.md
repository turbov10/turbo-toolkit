# Agent Gateway Skeleton (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `agent-gateway/` skeleton: a stdio MCP server that discovers sibling tool directories' `mcp_tools.py`, exposes their functions as MCP tools, and dispatches tool calls to each tool's own Python venv as a subprocess. Ships a CLI (`serve` / `list` / `call` / `info` / `version`).

**Architecture:** Single Python package `agent_gateway/`. The gateway runs as one process; each `tools/call` spawns a subprocess via `<tool>/.venv/bin/python <tool>/mcp_tools.py call --name <bare> --args '<json>'`. Discovery uses `importlib.util` to load each tool's `mcp_tools.py` in-process. The `CapturingMCP` wrapper intercepts `register(mcp)` calls, builds proxy functions that delegate to the subprocess runner, and registers those proxies with the real `FastMCP` instance.

**Tech Stack:** Python 3.12, `mcp[cli]` SDK, `PyYAML` for optional config, `pytest` for tests.

**Reference Spec:** `docs/superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md` (especially §3, §4, §5, §6, §7, §9, §10.1).

**Scope (P1 only):** No real tools have `mcp_tools.py` yet. All tests use stub `mcp_tools.py` files in `tmp_path` monorepos.

---

## File Structure

Files created in this plan (relative to `agent-gateway/`):

```
agent-gateway/
├── .gitignore
├── .python-version
├── README.md
├── requirements.txt
├── pyrightconfig.json
├── pytest.ini
├── agent_gateway/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── discovery.py
│   ├── runner.py
│   ├── schema.py
│   ├── mcp_server.py
│   └── cli.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_discovery.py
    ├── test_runner.py
    ├── test_schema.py
    ├── test_serve.py
    └── test_cli.py
```

Each module has one clear responsibility:
- `config.py` — load optional `gateway.yaml`, return a `GatewayConfig` dataclass with defaults.
- `discovery.py` — walk the monorepo for `*/mcp_tools.py`, importlib-load each, validate the contract, return `DiscoveredTool` records.
- `runner.py` — `SubprocessRunner.run(full_name, args, timeout)` dispatches to `<venv>/python <mcp_tools.py> call --name <bare> --args '<json>'`.
- `schema.py` — `CapturingMCP` wrapper + `_make_proxy` that preserves the source function's signature.
- `mcp_server.py` — `build_server(monorepo_root)` wires discovery + runner + CapturingMCP into a real `FastMCP` instance.
- `cli.py` — argparse entrypoint: `serve | list | call | info | version`.

---

## Task 1: Project Skeleton

**Files:**
- Create: `agent-gateway/.gitignore`
- Create: `agent-gateway/.python-version`
- Create: `agent-gateway/README.md`
- Create: `agent-gateway/requirements.txt`
- Create: `agent-gateway/pyrightconfig.json`
- Create: `agent-gateway/pytest.ini`
- Create: `agent-gateway/agent_gateway/__init__.py`
- Create: `agent-gateway/tests/__init__.py`

- [ ] **Step 1.1: Create `.gitignore`**

Write `agent-gateway/.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
.mypy_cache/
.ruff_cache/
*.egg-info/
build/
dist/
```

- [ ] **Step 1.2: Create `.python-version`**

Write `agent-gateway/.python-version` with the single line: `3.12.12`

- [ ] **Step 1.3: Create `requirements.txt`**

Write `agent-gateway/requirements.txt`:

```
mcp[cli]>=1.0
PyYAML>=6.0
```

- [ ] **Step 1.4: Create `pyrightconfig.json`**

Write `agent-gateway/pyrightconfig.json`:

```json
{
  "include": ["agent_gateway", "tests"],
  "pythonVersion": "3.12",
  "typeCheckingMode": "basic"
}
```

- [ ] **Step 1.5: Create `pytest.ini`**

Write `agent-gateway/pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers
```

- [ ] **Step 1.6: Create package `__init__.py`**

Write `agent-gateway/agent_gateway/__init__.py`:

```python
"""agent-gateway: a single MCP server that aggregates every tool in the turbo-toolkit monorepo."""
__version__ = "0.1.0"
```

- [ ] **Step 1.7: Create `tests/__init__.py`**

Write `agent-gateway/tests/__init__.py` as an empty file (so pytest can discover tests).

- [ ] **Step 1.8: Create `README.md`**

Write `agent-gateway/README.md`:

```markdown
# agent-gateway

Single MCP (Model Context Protocol) server that aggregates every tool in the
[turbo-toolkit](../) monorepo. Each tool directory that ships a `mcp_tools.py`
file is auto-discovered and exposed as MCP tools under a `<namespace>__<tool>`
naming convention.

See [the design spec](../superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md)
for the full architecture.

## Install

```bash
cd agent-gateway
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## CLI

```bash
.venv/bin/python -m agent_gateway serve         # start stdio MCP server
.venv/bin/python -m agent_gateway list          # list all discovered tools
.venv/bin/python -m agent_gateway call <full_name> --args '<json>'
.venv/bin/python -m agent_gateway info <full_name>
.venv/bin/python -m agent_gateway version
```

## Configure your Agent

In Claude Desktop / Cursor / Cline, point the MCP server at:

```json
{
  "command": "/absolute/path/to/agent-gateway/.venv/bin/python",
  "args": ["-m", "agent_gateway", "serve"]
}
```
```

- [ ] **Step 1.9: Install dependencies and verify package imports**

```bash
cd agent-gateway
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install pytest
.venv/bin/python -c "import agent_gateway; print(agent_gateway.__version__)"
```

Expected output: `0.1.0`

- [ ] **Step 1.10: Commit**

```bash
cd agent-gateway
git add .gitignore .python-version README.md requirements.txt pyrightconfig.json pytest.ini agent_gateway/__init__.py tests/__init__.py
git commit -m "feat(agent-gateway): project skeleton (Phase 1)"
```

---

## Task 2: Config Module (TDD)

**Files:**
- Create: `agent-gateway/agent_gateway/config.py`
- Test: `agent-gateway/tests/test_config.py`

- [ ] **Step 2.1: Write the failing test**

Write `agent-gateway/tests/test_config.py`:

```python
from pathlib import Path
import textwrap
import pytest

from agent_gateway.config import GatewayConfig, load_config


def test_defaults_when_no_file(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.root == tmp_path
    assert cfg.exclude == ["agent-gateway", ".github", "docs"]
    assert cfg.timeout_seconds == 30
    assert cfg.tools == {}


def test_loads_yaml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text(textwrap.dedent("""
        root: "."
        exclude: ["foo", "bar"]
        timeout_seconds: 60
        tools:
          web-trigger:
            timeout_seconds: 120
    """).strip())
    cfg = load_config(cfg_file)
    assert cfg.root == tmp_path
    assert cfg.exclude == ["foo", "bar"]
    assert cfg.timeout_seconds == 60
    assert cfg.tools == {"web-trigger": {"timeout_seconds": 120}}


def test_root_resolved_relative_to_yaml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "sub" / "gateway.yaml"
    cfg_file.parent.mkdir()
    cfg_file.write_text('root: ".."\n')
    cfg = load_config(cfg_file)
    assert cfg.root == tmp_path


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text("this: is: not: valid: yaml: [\n")
    with pytest.raises(Exception):
        load_config(cfg_file)


def test_exclude_accepts_string_or_list(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text('exclude: "only-one"\n')
    cfg = load_config(cfg_file)
    assert cfg.exclude == ["only-one"]
```

- [ ] **Step 2.2: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.config'`

- [ ] **Step 2.3: Implement `config.py`**

Write `agent-gateway/agent_gateway/config.py`:

```python
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
```

- [ ] **Step 2.4: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_config.py -v
```

Expected: 5 tests pass.

- [ ] **Step 2.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/config.py tests/test_config.py
git commit -m "feat(agent-gateway): config module with gateway.yaml loader"
```

---

## Task 3: Discovery Module (TDD)

**Files:**
- Create: `agent-gateway/agent_gateway/discovery.py`
- Test: `agent-gateway/tests/test_discovery.py`
- Test fixtures: `agent-gateway/tests/conftest.py`

- [ ] **Step 3.1: Create conftest with shared fixtures**

Write `agent-gateway/tests/conftest.py`:

```python
"""Shared pytest fixtures."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import textwrap
import pytest


@pytest.fixture
def fake_monorepo(tmp_path: Path) -> Path:
    """Return a tmp_path monorepo pre-populated with two stub tool dirs."""
    (tmp_path / "alpha-tool").mkdir()
    (tmp_path / "beta-tool").mkdir()
    (tmp_path / "agent-gateway").mkdir()  # should be excluded
    (tmp_path / ".github").mkdir()         # should be excluded
    (tmp_path / "docs").mkdir()            # should be excluded
    return tmp_path


def write_mcp_tools(
    tool_dir: Path,
    namespace: str,
    fn_name: str = "hello",
    return_value: str = "world",
) -> Path:
    """Write a minimal valid mcp_tools.py in `tool_dir` and return the path.

    The stub includes both the `register(mcp)` function (for gateway discovery)
    and an `if __name__ == "__main__"` block that handles the gateway's
    `<python> mcp_tools.py call --name X --args JSON` invocation. Without the
    __main__ block, the subprocess would produce empty stdout and the runner
    would fail with "invalid JSON from tool".
    """
    path = tool_dir / "mcp_tools.py"
    path.write_text(textwrap.dedent(f'''
        import argparse
        import json
        TOOL_NAMESPACE = {namespace!r}

        def {fn_name}(name: str = "world") -> str:
            return {return_value!r}

        def register(mcp):
            mcp.tool(
                name=f"{{TOOL_NAMESPACE}}__{fn_name}",
                description="stub tool",
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
    return path
```

- [ ] **Step 3.2: Write the failing test**

Write `agent-gateway/tests/test_discovery.py`:

```python
from pathlib import Path
import textwrap
import pytest

from agent_gateway.discovery import (
    DiscoveredTool,
    discover_all,
    DiscoveryError,
)


def test_discovers_tool_dirs_with_mcp_tools_py(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    write_mcp_tools(fake_monorepo / "beta-tool", "beta")

    tools = discover_all(fake_monorepo)
    namespaces = {t.namespace for t in tools}
    assert namespaces == {"alpha", "beta"}


def test_excludes_listed_dirs(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    # agent-gateway/, .github/, docs/ must never be discovered even with mcp_tools.py
    write_mcp_tools(fake_monorepo / "agent-gateway", "self")
    write_mcp_tools(fake_monorepo / ".github", "gh")
    write_mcp_tools(fake_monorepo / "docs", "docs")

    tools = discover_all(fake_monorepo)
    namespaces = {t.namespace for t in tools}
    assert "self" not in namespaces
    assert "gh" not in namespaces
    assert "docs" not in namespaces
    assert "alpha" in namespaces


def test_excludes_dirs_without_mcp_tools_py(fake_monorepo: Path) -> None:
    # beta-tool has no mcp_tools.py; only alpha-tool should appear
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo)
    assert [t.namespace for t in tools] == ["alpha"]


def test_validates_too_namespace_present(tmp_path: Path) -> None:
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "mcp_tools.py").write_text("def register(mcp): pass\n")
    with pytest.raises(DiscoveryError, match="TOOL_NAMESPACE"):
        discover_all(tmp_path, strict=True)


def test_validates_register_callable(tmp_path: Path) -> None:
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "mcp_tools.py").write_text(
        "TOOL_NAMESPACE = 'bad'\nregister = 'not a function'\n"
    )
    with pytest.raises(DiscoveryError, match="register"):
        discover_all(tmp_path, strict=True)


def test_venv_python_attribute(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo)
    t = tools[0]
    # sys.executable can be 'python', 'python3.12', 'python.exe', etc.
    import re
    assert re.match(r"^python(\d+(\.\d+)?)?(\.exe)?$", t.venv_python.name), t.venv_python.name
    assert t.venv_python.parent.name in ("bin", "Scripts")
    # Falls back to sys.executable when no .venv exists
    assert t.venv_python.exists() or t.venv_python == t.system_python


def test_exclude_is_overridable(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo, exclude=[])
    assert "alpha" in {t.namespace for t in tools}
```

- [ ] **Step 3.3: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_discovery.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.discovery'`

- [ ] **Step 3.4: Implement `discovery.py`**

Write `agent-gateway/agent_gateway/discovery.py`:

```python
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
    spec = importlib.util.spec_from_file_location(
        f"_agent_gateway_mcp_{path.parent.name}", path
    )
    if spec is None or spec.loader is None:
        raise DiscoveryError(f"{path}: cannot import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _detect_venv_python(tool_dir: Path, fallback: Path) -> Path:
    """Return <tool_dir>/.venv/bin/python (or Scripts\\python.exe) if it exists."""
    if sys.platform == "win32":
        candidate = tool_dir / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = tool_dir / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else fallback
```

- [ ] **Step 3.5: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_discovery.py -v
```

Expected: 7 tests pass.

- [ ] **Step 3.6: Commit**

```bash
cd agent-gateway
git add agent_gateway/discovery.py tests/test_discovery.py tests/conftest.py
git commit -m "feat(agent-gateway): discovery module with validation"
```

---

## Task 4: Subprocess Runner (TDD)

**Files:**
- Create: `agent-gateway/agent_gateway/runner.py`
- Test: `agent-gateway/tests/test_runner.py`

- [ ] **Step 4.1: Write the failing test**

Write `agent-gateway/tests/test_runner.py`:

```python
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
```

- [ ] **Step 4.2: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_runner.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.runner'`

- [ ] **Step 4.3: Implement `runner.py`**

Write `agent-gateway/agent_gateway/runner.py`:

```python
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
```

- [ ] **Step 4.4: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_runner.py -v
```

Expected: 7 tests pass.

- [ ] **Step 4.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/runner.py tests/test_runner.py
git commit -m "feat(agent-gateway): subprocess runner with timeout and error handling"
```

---

## Task 5: Schema Extraction with CapturingMCP (TDD)

**Files:**
- Create: `agent-gateway/agent_gateway/schema.py`
- Test: `agent-gateway/tests/test_schema.py`

- [ ] **Step 5.1: Write the failing test**

Write `agent-gateway/tests/test_schema.py`:

```python
from __future__ import annotations
from typing import Literal
from unittest.mock import MagicMock

import pytest

from agent_gateway.runner import SubprocessRunner
from agent_gateway.schema import CapturingMCP, ToolRecord, _make_proxy


def test_capturing_mcp_records_tool() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = {"ok": True}
    cap = CapturingMCP("agent-gateway", runner)

    def my_tool(name: str = "world") -> str:
        """Say hello."""
        return f"hello, {name}"

    decorator = cap.tool(name="ns__my_tool", description="greets")
    decorator(my_tool)

    assert len(cap.captures) == 1
    rec = cap.captures[0]
    assert rec.full_name == "ns__my_tool"
    assert rec.bare_name == "my_tool"
    assert rec.description == "greets"
    assert rec.source_func is my_tool


def test_capturing_mcp_registers_proxy_with_real_fastmcp() -> None:
    from mcp.server.fastmcp import FastMCP
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = "ok"
    cap = CapturingMCP("agent-gateway", runner)

    def my_tool(name: str = "world") -> str:
        """Say hello."""
        return f"hi, {name}"

    cap.tool(name="ns__my_tool", description="greets")(my_tool)

    real = cap.real
    tools = real._tool_manager.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "ns__my_tool"
    assert tools[0].description == "greets"


def test_proxy_preserves_signature_for_schema() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = "ok"
    cap = CapturingMCP("agent-gateway", runner)

    def greet(name: str, greeting: Literal["hi", "hey"] = "hi") -> str:
        """Say hi."""
        return f"{greeting}, {name}"

    cap.tool(name="ns__greet")(greet)
    real = cap.real
    tool_obj = real._tool_manager.get_tool("ns__greet")

    # The registered function should have type hints so FastMCP builds a schema
    fn = tool_obj.fn
    assert fn.__name__ == "greet"
    schema = tool_obj.parameters
    assert "name" in schema["properties"]
    assert "greeting" in schema["properties"]
    assert set(schema["required"]) == {"name"}


def test_proxy_invokes_runner_with_full_name_and_args() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    runner.run.return_value = {"echoed": "hi"}
    cap = CapturingMCP("agent-gateway", runner)

    def echo(text: str) -> dict:
        return {"echoed": text}

    cap.tool(name="ns__echo")(echo)
    real = cap.real
    tool_obj = real._tool_manager.get_tool("ns__echo")

    result = tool_obj.fn(text="hi")
    runner.run.assert_called_once()
    args = runner.run.call_args
    # First positional arg is the full_name
    assert args[0][0] == "ns__echo"
    # Second positional arg is the kwargs dict
    assert args[0][1] == {"text": "hi"}
    assert result == {"echoed": "hi"}


def test_make_proxy_carries_docstring() -> None:
    def f(x: int) -> int:
        """the doc"""
        return x

    proxy = _make_proxy("ns__f", "f", MagicMock(), f)
    assert proxy.__doc__ == "the doc"
    assert proxy.__name__ == "f"


def test_captures_property_returns_copy() -> None:
    runner = MagicMock(spec=SubprocessRunner)
    cap = CapturingMCP("agent-gateway", runner)

    def f(x: int) -> int:
        return x

    cap.tool(name="ns__f")(f)
    caps1 = cap.captures
    caps2 = cap.captures
    assert caps1 is not caps2
    assert caps1 == caps2
```

- [ ] **Step 5.2: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_schema.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.schema'`

- [ ] **Step 5.3: Implement `schema.py`**

Write `agent-gateway/agent_gateway/schema.py`:

```python
"""CapturingMCP: an MCP stand-in that records tool registrations and proxies them."""
from __future__ import annotations
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from agent_gateway.runner import SubprocessRunner

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolRecord:
    full_name: str        # e.g. "image-ocr__ocr_image"
    bare_name: str        # e.g. "ocr_image"
    source_func: Callable
    description: str | None


def _make_proxy(
    full_name: str,
    bare_name: str,
    runner: SubprocessRunner,
    source_func: Callable,
) -> Callable[..., Any]:
    """Return a wrapper that calls the runner and preserves source's signature.

    FastMCP introspects the registered function's `__signature__` and
    `__annotations__` to build the input JSON schema, so we copy them across.
    """
    sig = inspect.signature(source_func, eval_str=True)

    def proxy(**kwargs: Any) -> Any:
        return runner.run(full_name, kwargs)

    proxy.__name__ = bare_name
    proxy.__qualname__ = bare_name
    proxy.__signature__ = sig
    proxy.__annotations__ = dict(source_func.__annotations__)
    proxy.__doc__ = source_func.__doc__
    proxy.__wrapped__ = source_func
    return proxy


class CapturingMCP:
    """MCP-compatible wrapper that captures tool registrations and proxies them.

    Usage:
        cap = CapturingMCP("agent-gateway", runner)
        for module in discovered_modules:
            module.register(cap)
        # cap.real is the FastMCP instance ready to .run()
        # cap.captures is a list of ToolRecord for the gateway's CLI/registry
    """

    def __init__(self, server_name: str, runner: SubprocessRunner) -> None:
        self._real = FastMCP(server_name)
        self._runner = runner
        self._captures: list[ToolRecord] = []

    @property
    def real(self) -> FastMCP:
        return self._real

    @property
    def captures(self) -> list[ToolRecord]:
        return list(self._captures)

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
        **_: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            bare_name = func.__name__
            full_name = name or bare_name
            desc = description or (func.__doc__ or "").strip().splitlines()[0] if func.__doc__ else None
            proxy = _make_proxy(full_name, bare_name, self._runner, func)
            self._real.add_tool(
                fn=proxy,
                name=full_name,
                description=desc,
            )
            self._captures.append(
                ToolRecord(
                    full_name=full_name,
                    bare_name=bare_name,
                    source_func=func,
                    description=desc,
                )
            )
            return func

        return decorator
```

- [ ] **Step 5.4: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_schema.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/schema.py tests/test_schema.py
git commit -m "feat(agent-gateway): CapturingMCP for schema extraction and proxy wiring"
```

---

## Task 6: Server Builder

**Files:**
- Create: `agent-gateway/agent_gateway/mcp_server.py`
- Test: `agent-gateway/tests/test_serve.py` (minimal unit test of `build_server`)

- [ ] **Step 6.1: Write the failing test**

Write `agent-gateway/tests/test_serve.py`:

```python
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_gateway.mcp_server import build_server, ServerHandle
from agent_gateway.config import GatewayConfig


def test_build_server_with_no_tools(tmp_path: Path) -> None:
    cfg = GatewayConfig(root=tmp_path, exclude=["agent-gateway"], timeout_seconds=30, tools={})
    handle = build_server(cfg)
    assert isinstance(handle, ServerHandle)
    assert handle.captures == []
    assert handle.fastmcp is not None


def test_build_server_registers_discovered_tools(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    cfg = GatewayConfig(root=fake_monorepo, exclude=["agent-gateway"], timeout_seconds=30, tools={})
    handle = build_server(cfg)
    names = {c.full_name for c in handle.captures}
    assert "alpha__hello" in names
    # The real FastMCP should also have the tool
    fast_tools = handle.fastmcp._tool_manager.list_tools()
    fast_names = {t.name for t in fast_tools}
    assert "alpha__hello" in fast_names


def test_build_server_uses_per_tool_timeout(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha", fn_name="hello", return_value="hi")
    cfg = GatewayConfig(
        root=fake_monorepo,
        exclude=["agent-gateway"],
        timeout_seconds=30,
        tools={"alpha": {"timeout_seconds": 99}},
    )
    handle = build_server(cfg)
    rec = next(c for c in handle.captures if c.full_name == "alpha__hello")
    # The captured record doesn't store timeout; verify it's used in the runner instead
    # by checking that the runner per-tool timeout dict got populated
    assert handle.runner_timeouts.get("alpha") == 99
```

- [ ] **Step 6.2: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_serve.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.mcp_server'`

- [ ] **Step 6.3: Implement `mcp_server.py`**

Write `agent-gateway/agent_gateway/mcp_server.py`:

```python
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
```

- [ ] **Step 6.4: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_serve.py -v
```

Expected: 3 tests pass.

- [ ] **Step 6.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/mcp_server.py tests/test_serve.py
git commit -m "feat(agent-gateway): build_server wires discovery + runner + CapturingMCP"
```

---

## Task 7: CLI — argparse skeleton + version (TDD)

**Files:**
- Create: `agent-gateway/agent_gateway/cli.py`
- Create: `agent-gateway/agent_gateway/__main__.py`
- Test: `agent-gateway/tests/test_cli.py`

- [ ] **Step 7.1: Write the failing test (version + help only)**

Append to `agent-gateway/tests/test_cli.py`:

```python
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
```

- [ ] **Step 7.2: Run the test to verify it fails**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent_gateway.cli'`

- [ ] **Step 7.3: Implement `cli.py` (skeleton with version + help)**

Write `agent-gateway/agent_gateway/cli.py`:

```python
"""Command-line entrypoint: serve | list | call | info | version."""
from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path

import agent_gateway
from agent_gateway.config import GatewayConfig, load_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-gateway",
        description="Single MCP server aggregating every tool in turbo-toolkit.",
    )
    p.add_argument(
        "--root", type=Path, default=None,
        help="monorepo root (default: parent of agent-gateway/)",
    )
    p.add_argument(
        "--config", type=Path, default=None,
        help="path to gateway.yaml (optional)",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="enable DEBUG logging",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="start the stdio MCP server")
    sub.add_parser("list", help="list all discovered tools")
    sub.add_parser("version", help="print gateway version")

    call_p = sub.add_parser("call", help="invoke a single tool by full name")
    call_p.add_argument("full_name")
    call_p.add_argument("--args", default="{}")

    info_p = sub.add_parser("info", help="show one tool's schema")
    info_p.add_argument("full_name")

    return p


def resolve_config(args: argparse.Namespace) -> GatewayConfig:
    """Load config (gateway.yaml if --config) and apply --root override."""
    cfg = load_config(args.config)
    if args.root is not None:
        cfg = GatewayConfig(
            root=args.root.resolve(),
            exclude=cfg.exclude,
            timeout_seconds=cfg.timeout_seconds,
            tools=cfg.tools,
        )
    return cfg


def cmd_version(_: argparse.Namespace) -> int:
    print(f"agent-gateway {agent_gateway.__version__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return _DISPATCH[args.cmd](args)


_DISPATCH = {
    "version": cmd_version,
    # serve / list / call / info filled in by Tasks 8-10
}


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7.4: Implement `__main__.py`**

Write `agent-gateway/agent_gateway/__main__.py`:

```python
"""Allow `python -m agent_gateway`."""
import sys
from agent_gateway.cli import main

sys.exit(main())
```

- [ ] **Step 7.5: Run the test to verify it passes**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py -v
```

Expected: 3 tests pass.

- [ ] **Step 7.6: Commit**

```bash
cd agent-gateway
git add agent_gateway/cli.py agent_gateway/__main__.py tests/test_cli.py
git commit -m "feat(agent-gateway): CLI skeleton with version + help"
```

---

## Task 8: CLI — `list` and `info` subcommands (TDD)

**Files:**
- Modify: `agent-gateway/agent_gateway/cli.py`
- Modify: `agent-gateway/tests/test_cli.py`

- [ ] **Step 8.1: Add the failing tests for `list` and `info`**

Append to `agent-gateway/tests/test_cli.py`:

```python
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
```

- [ ] **Step 8.2: Run the new tests to verify they fail**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py -v
```

Expected: 5 of the new tests FAIL (the 3 from Task 7 still pass).

- [ ] **Step 8.3: Implement `cmd_list` and `cmd_info`**

Replace `agent-gateway/agent_gateway/cli.py` with:

```python
"""Command-line entrypoint: serve | list | call | info | version."""
from __future__ import annotations
import argparse
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any

import agent_gateway
from agent_gateway.config import GatewayConfig, load_config
from agent_gateway.mcp_server import build_server


def _common_parent(add_help: bool = False) -> argparse.ArgumentParser:
    """ArgumentParser fragment with the flags accepted before OR after the subcommand.

    We attach this to BOTH the top-level parser and every subparser via
    `parents=[common]`, so `--root`/`--config`/`--verbose`/`--json` may be
    placed before OR after the subcommand name (e.g. both
    `agent-gateway --root /tmp list` and `agent-gateway list --root /tmp` work).
    """
    p = argparse.ArgumentParser(add_help=add_help)
    p.add_argument("--root", type=Path, default=None,
                   help="monorepo root (default: parent of agent-gateway/)")
    p.add_argument("--config", type=Path, default=None,
                   help="path to gateway.yaml (optional)")
    p.add_argument("--verbose", "-v", action="store_true", help="DEBUG logging")
    p.add_argument("--json", action="store_true",
                   help="(list/info) emit JSON instead of human-readable text")
    return p


def build_parser() -> argparse.ArgumentParser:
    common = _common_parent(add_help=False)
    p = argparse.ArgumentParser(
        prog="agent-gateway",
        description="Single MCP server aggregating every tool in turbo-toolkit.",
        parents=[common],
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="start the stdio MCP server", parents=[common])
    sub.add_parser("list", help="list all discovered tools", parents=[common])
    sub.add_parser("version", help="print gateway version", parents=[common])

    call_p = sub.add_parser("call", help="invoke a single tool by full name",
                            parents=[common])
    call_p.add_argument("full_name")
    call_p.add_argument("--args", default="{}")

    info_p = sub.add_parser("info", help="show one tool's schema", parents=[common])
    info_p.add_argument("full_name")

    return p


def resolve_config(args: argparse.Namespace) -> GatewayConfig:
    cfg = load_config(args.config)
    if args.root is not None:
        cfg = GatewayConfig(
            root=args.root.resolve(),
            exclude=cfg.exclude,
            timeout_seconds=cfg.timeout_seconds,
            tools=cfg.tools,
        )
    return cfg


def cmd_version(_: argparse.Namespace) -> int:
    print(f"agent-gateway {agent_gateway.__version__}")
    return 0


def _build_handle(args: argparse.Namespace):
    cfg = resolve_config(args)
    return build_server(cfg)


def cmd_list(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    if not handle.captures:
        if args.json:
            print("[]")
        else:
            print("(no tools discovered)")
        return 0
    if args.json:
        out = [
            {
                "full_name": c.full_name,
                "bare_name": c.bare_name,
                "description": c.description,
            }
            for c in handle.captures
        ]
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    for c in handle.captures:
        print(c.full_name)
        if c.description:
            print(f"  {c.description}")
        sig = inspect.signature(c.source_func)
        print(f"  signature: {sig}")
        print()
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    rec = next((c for c in handle.captures if c.full_name == args.full_name), None)
    if rec is None:
        print(f"tool not found: {args.full_name}", file=sys.stderr)
        return 2
    sig = inspect.signature(rec.source_func)
    payload = {
        "full_name": rec.full_name,
        "bare_name": rec.bare_name,
        "description": rec.description,
        "signature": str(sig),
        "parameters": rec.source_func.__annotations__,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(rec.full_name)
        if rec.description:
            print(f"  {rec.description}")
        print(f"  signature: {sig}")
        print(f"  parameters: {rec.source_func.__annotations__}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    log.info("serving %d tools on stdio", len(handle.captures))
    handle.fastmcp.run(transport="stdio")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return _DISPATCH[args.cmd](args)


_DISPATCH = {
    "version": cmd_version,
    "list": cmd_list,
    "info": cmd_info,
    "serve": cmd_serve,
    # "call" added in Task 9
}


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 8.4: Run the tests to verify they pass**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py -v
```

Expected: 8 tests pass (3 from Task 7 + 5 new).

- [ ] **Step 8.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/cli.py tests/test_cli.py
git commit -m "feat(agent-gateway): CLI list and info subcommands"
```

---

## Task 9: CLI — `call` subcommand (TDD)

**Files:**
- Modify: `agent-gateway/agent_gateway/cli.py`
- Modify: `agent-gateway/tests/test_cli.py`

- [ ] **Step 9.1: Add the failing test for `call`**

Append to `agent-gateway/tests/test_cli.py`:

```python
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
        TOOL_NAMESPACE = "alpha"
        def boom() -> str:
            raise RuntimeError("kaboom")
        def register(mcp):
            mcp.tool(name="alpha__boom", description="explodes")(boom)
    """).lstrip())
    result = run_cli("call", "alpha__boom", "--root", str(fake_monorepo))
    assert result.returncode != 0
    # stderr should contain the original error
    combined = (result.stdout + result.stderr).lower()
    assert "kaboom" in combined
```

Add the import at the top of `tests/test_cli.py` (after the existing imports):

```python
import textwrap
```

- [ ] **Step 9.2: Run the new tests to verify they fail**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py::test_call_with_known_tool tests/test_cli.py::test_call_unknown_tool tests/test_cli.py::test_call_propagates_tool_error -v
```

Expected: 3 tests FAIL (call subcommand not implemented).

- [ ] **Step 9.3: Implement `cmd_call` and wire it into `_DISPATCH`**

Add this function to `agent-gateway/agent_gateway/cli.py` (place it just above `cmd_serve`):

```python
def cmd_call(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    rec = next((c for c in handle.captures if c.full_name == args.full_name), None)
    if rec is None:
        print(f"tool not found: {args.full_name}", file=sys.stderr)
        return 2
    cfg = resolve_config(args)
    namespace = rec.full_name.split("__", 1)[0]
    timeout = handle.runner_timeouts.get(namespace, cfg.timeout_seconds)
    try:
        parsed_args = json.loads(args.args)
        if not isinstance(parsed_args, dict):
            raise ValueError("--args must be a JSON object")
        result = handle.runner.run(args.full_name, parsed_args, timeout=timeout)
    except json.JSONDecodeError as e:
        print(f"invalid --args JSON: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"tool error: {e}", file=sys.stderr)
        return 4
    print(json.dumps(result, ensure_ascii=False))
    return 0
```

Update the `_DISPATCH` mapping in `cli.py`:

```python
_DISPATCH = {
    "version": cmd_version,
    "list": cmd_list,
    "info": cmd_info,
    "call": cmd_call,
    "serve": cmd_serve,
}
```

- [ ] **Step 9.4: Run all CLI tests to verify they pass**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_cli.py -v
```

Expected: 11 tests pass.

- [ ] **Step 9.5: Commit**

```bash
cd agent-gateway
git add agent_gateway/cli.py tests/test_cli.py
git commit -m "feat(agent-gateway): CLI call subcommand with subprocess dispatch"
```

---

## Task 10: End-to-end smoke test (TDD)

**Files:**
- Create: `agent-gateway/tests/test_serve_integration.py`

- [ ] **Step 10.1: Write the integration test**

Write `agent-gateway/tests/test_serve_integration.py`:

```python
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
    (tool_dir / "mcp_tools.py").write_text(textwrap.dedent(f"""
        TOOL_NAMESPACE = {namespace!r}

        def {fn_name}(name: str = "world") -> str:
            return {return_value!r}

        def register(mcp):
            mcp.tool(
                name=f"{{TOOL_NAMESPACE}}__{fn_name}",
                description=f"stub tool returning {return_value!r}",
            )({fn_name})
    """).lstrip())


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
            assert json.loads(text) == "pong"


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
```

- [ ] **Step 10.2: Install pytest-asyncio for the async tests**

```bash
cd agent-gateway && .venv/bin/pip install pytest-asyncio
```

Append to `agent-gateway/pytest.ini`:

```ini
asyncio_mode = auto
```

- [ ] **Step 10.3: Run the integration test**

```bash
cd agent-gateway && .venv/bin/pytest tests/test_serve_integration.py -v
```

Expected: 3 tests pass.

- [ ] **Step 10.4: Run the full test suite to confirm nothing regressed**

```bash
cd agent-gateway && .venv/bin/pytest -v
```

Expected: ALL tests pass (config 5 + discovery 7 + runner 7 + schema 6 + serve 3 + cli 11 + integration 3 = 42 tests).

- [ ] **Step 10.5: Commit**

```bash
cd agent-gateway
git add tests/test_serve_integration.py requirements.txt pytest.ini
git commit -m "test(agent-gateway): end-to-end stdio MCP server smoke test"
```

- [ ] **Step 10.6: Update `requirements.txt` to pin `pytest-asyncio`**

Edit `agent-gateway/requirements.txt` to:

```
mcp[cli]>=1.0
PyYAML>=6.0
pytest>=8.0
pytest-asyncio>=0.23
```

Then commit:

```bash
cd agent-gateway
git add requirements.txt
git commit -m "chore(agent-gateway): pin pytest + pytest-asyncio in requirements"
```

---

## Task 11: Final P1 acceptance check + docs polish

- [ ] **Step 11.1: Manual smoke test from the project root**

```bash
cd /Users/turbov10/Documents/workspace/turbo-toolkit
mkdir -p /tmp/p1-smoke/alpha-tool
cat > /tmp/p1-smoke/alpha-tool/mcp_tools.py << 'PYEOF'
TOOL_NAMESPACE = "alpha"

def hello(name: str = "world") -> str:
    return f"hello, {name}"

def register(mcp):
    mcp.tool(name="alpha__hello", description="greets")(hello)
PYEOF

cd /Users/turbov10/Documents/workspace/turbo-toolkit/agent-gateway
.venv/bin/python -m agent_gateway list --root /tmp/p1-smoke
.venv/bin/python -m agent_gateway info alpha__hello --root /tmp/p1-smoke
.venv/bin/python -m agent_gateway call alpha__hello --args '{"name":"kilo"}' --root /tmp/p1-smoke
```

Expected:
- `list` shows `alpha__hello` with description
- `info` shows the function signature
- `call` prints `hello, kilo`

- [ ] **Step 11.2: Verify the gateway starts with the real monorepo (zero tools)**

```bash
cd /Users/turbov10/Documents/workspace/turbo-toolkit/agent-gateway
.venv/bin/python -m agent_gateway list --root ..
```

Expected: `(no tools discovered)` (because no tool dir has `mcp_tools.py` yet).

- [ ] **Step 11.3: Run lint/typecheck if available**

```bash
cd /Users/turbov10/Documents/workspace/turbo-toolkit/agent-gateway
.venv/bin/pip install pyright 2>/dev/null || true
.venv/bin/pyright 2>&1 | tail -20
```

If `pyright` reports no errors → P1 is clean. Fix any reported errors before continuing.

- [ ] **Step 11.4: Final commit if any docs were updated**

```bash
cd /Users/turbov10/Documents/workspace/turbo-toolkit/agent-gateway
git status
# If README or docs were tweaked:
git add -A
git commit -m "docs(agent-gateway): polish README for P1 release"
```

---

## P1 Acceptance Checklist

- [ ] All 42+ tests pass via `cd agent-gateway && .venv/bin/pytest`
- [ ] `python -m agent_gateway serve` starts and stays running on stdio
- [ ] `python -m agent_gateway list` reports zero tools against the real monorepo
- [ ] `python -m agent_gateway call` dispatches to a stub tool and returns its output
- [ ] No real tool has `mcp_tools.py` yet (P3-P5 will add them)
- [ ] Spec §11 P1 row is satisfied

Once P1 is green, hand off to the next phase (P2 = `image-ocr/`) with a fresh `writing-plans` invocation.

# turbo-toolkit Agent Gateway — MCP Integration Design

**Status:** Approved (brainstorm complete)
**Date:** 2026-07-03
**Owner:** turbo-toolkit maintainers
**Scope:** Monorepo-level architecture for exposing every tool directory to LLM Agents via a single MCP server, while preserving the existing CLI and per-tool isolation guarantees defined in `AGENTS.md`.

---

## 1. Background and Motivation

`turbo-toolkit` is a monorepo of self-contained Python tools (`web-search/`, `web-trigger/`, `convert-audio/`) with the principle: **each tool directory is independent** — its own language, deps, venv, config, README, and CLI entry point (see `AGENTS.md` §1).

The owner wants to integrate the toolkit with LLM Agents (Claude Desktop, Cursor, Cline, or any MCP-compatible client). Concretely:

1. **Single MCP server.** The Agent sees one MCP endpoint that exposes every tool.
2. **CLI must keep working.** Humans and Agents that prefer subprocess can still call each tool's CLI directly.
3. **Future-proof.** Adding a new tool directory should require only a new `mcp_tools.py` — no gateway changes.
4. **Isolation preserved.** Each tool still runs in its own venv with its own dependencies; the gateway never leaks one tool's deps into another.

A new image-OCR tool (`image-ocr/`) is also being introduced as the first tool built natively against this pattern.

---

## 2. Goals and Non-Goals

### Goals

- A single MCP stdio server (`agent-gateway`) discovers and aggregates tools from every sibling tool directory.
- Each tool directory declares its MCP surface via one standard file: `mcp_tools.py`.
- Tool calls are dispatched into the **target tool's own venv** as a subprocess, so the `AGENTS.md` isolation rule is not violated.
- Existing CLI behaviors of `web-search`, `web-trigger`, and `convert-audio` are unchanged.
- The `agent-gateway` itself ships with a small CLI (`serve` / `list` / `call` / `info` / `version`) for human use, debugging, and Agent introspection.

### Non-Goals (v1)

- HTTP / SSE / WebSocket transport for the gateway. The Agent connects via stdio. The user explicitly chose "CLI only" for non-MCP Agent access.
- Hot-reload of `mcp_tools.py` after the gateway starts. A restart picks up new tools.
- Cross-tool composition (chaining tools in one gateway call). Each call maps to exactly one tool.
- Tool-level authentication, rate limiting, or quota tracking. Tools handle their own auth (e.g., web-search's API keys).
- Replacing or refactoring existing tool internals. `mcp_tools.py` is purely additive.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LLM Agent  (Claude Desktop / Cursor / Cline / 自建)        │
└──────────────────────┬──────────────────────────────────────┘
                       │ MCP (stdio, JSON-RPC)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  agent-gateway/                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  FastMCP Server (stdio)                            │     │
│  │  ├─ discover(monorepo_root)  → finds mcp_tools.py  │     │
│  │  ├─ list_tools()             → aggregates schemas  │     │
│  │  └─ call(name, args)         → subprocess dispatch │     │
│  └────────────────────────────────────────────────────┘     │
│  CLI: serve | list | call | info | version                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ subprocess.run(..., capture_output=True)
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   web-search/    web-trigger/   convert-audio/  image-ocr/
   .venv/         .venv/         .venv/         .venv/
   mcp_tools.py   mcp_tools.py   mcp_tools.py   mcp_tools.py
```

The gateway is the only process the Agent launches. Every tool runs in its own subprocess with its own venv.

---

## 4. The `mcp_tools.py` Contract

Each tool directory MUST contain a `mcp_tools.py` file with this shape:

```python
# image-ocr/mcp_tools.py
"""image-ocr's MCP tool registration entrypoint."""
from __future__ import annotations
import json
import sys
import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# The namespace prefix for all tools in this file.
TOOL_NAMESPACE: str = "image-ocr"


# --- Pure functions (importable, testable, callable directly) ---

def ocr_image(image_path: str | None = None,
              image_base64: str | None = None,
              languages: list[str] | None = None,
              detail: str = "text") -> dict:
    """Extract text from an image. ..."""
    from image_ocr.cli import run_ocr
    return run_ocr(
        image_path=image_path,
        image_base64=image_base64,
        languages=languages or ["zh-Hans", "en-US"],
        detail=detail,
    )


# --- Gateway integration ---

def register(mcp: "FastMCP") -> None:
    """Register all tools from this module into the given MCP server."""
    mcp.tool(
        name=f"{TOOL_NAMESPACE}__ocr_image",
        description="从图片中提取文字。",
    )(ocr_image)


# --- Subprocess entrypoint (used by the gateway's call dispatch) ---

def _cli_call(name: str, args_json: str) -> int:
    fn = getattr(sys.modules[__name__], name, None)
    if fn is None:
        print(f"unknown tool: {name}", file=sys.stderr)
        return 2
    result = fn(**json.loads(args_json))
    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    call_p = sub.add_parser("call")
    call_p.add_argument("--name", required=True)
    call_p.add_argument("--args", default="{}")
    ns = p.parse_args()
    if ns.cmd == "call":
        sys.exit(_cli_call(ns.name, ns.args))
```

### Contract rules

1. **No runtime `mcp` import.** `mcp` is referenced only under `TYPE_CHECKING` so the tool's own venv does not need it.
2. **One `TOOL_NAMESPACE` constant** per file. Multiple `mcp_tools.py` files must not share a namespace.
3. **One `register(mcp)` function** per file. It is called by the gateway at startup.
4. **Tool functions are pure Python** (no MCP decorators, no global state). They can be imported and unit-tested directly.
5. **Script mode**: `python mcp_tools.py call --name <tool> --args '<json>'` prints the JSON result to stdout and exits 0 on success, 2 on unknown tool, non-zero on tool failure.
6. **Errors from tool functions** should be raised as exceptions; the gateway catches and reports them as MCP `isError: true`. Tools MUST NOT write to stdout in error paths (only via the `call` subcommand's JSON output).

---

## 5. Tool Naming

Tools are exposed to the Agent as `<TOOL_NAMESPACE>__<tool_function_name>` (double underscore separator). Examples:

| Namespace | Tool function | MCP-exposed name |
|---|---|---|
| web-search | `search` | `web-search__search` |
| convert-audio | `audio_to_base64` | `convert-audio__audio_to_base64` |
| convert-audio | `base64_to_audio` | `convert-audio__base64_to_audio` |
| web-trigger | `check_config` | `web-trigger__check_config` |
| web-trigger | `dry_run` | `web-trigger__dry_run` |
| image-ocr | `ocr_image` | `image-ocr__ocr_image` |

**Collision policy:** If the gateway discovers two tools with the same exposed name, it logs a `WARNING` and keeps the first one encountered (sibling-directory alphabetical order). Future versions may fail fast instead.

---

## 6. agent-gateway Structure

```
agent-gateway/
├── .gitignore                   # .venv/, __pycache__/, .DS_Store
├── .python-version              # 3.12
├── README.md
├── requirements.txt             # mcp[cli]  (only hard dep)
├── pyrightconfig.json
├── agent_gateway/
│   ├── __init__.py
│   ├── __main__.py              # python -m agent_gateway
│   ├── cli.py                   # argparse: serve/list/call/info/version
│   ├── discovery.py             # walks <monorepo_root> for */mcp_tools.py
│   ├── mcp_server.py            # FastMCP, registers discovered tools, dispatches calls
│   ├── runner.py                # subprocess invoker (per-tool venv)
│   └── config.py                # optional gateway.yaml (include/exclude, timeout)
└── tests/
    ├── conftest.py              # tmp_path monorepo fixtures
    ├── test_discovery.py
    ├── test_runner.py
    ├── test_serve.py            # mcp.client.session over real stdio
    └── test_cli.py
```

### 6.1 Discovery (`discovery.py`)

- `discover_all(monorepo_root: Path) -> list[DiscoveredTool]`
- Walks `monorepo_root` (depth = 1). Excludes: `agent-gateway/` itself, hidden dirs, any dir in `config.exclude`.
- For each `<dir>/mcp_tools.py` that exists and is importable, loads it via `importlib.util.spec_from_file_location` and `module_from_spec`.
- Validates `TOOL_NAMESPACE` is set and `register` is callable.
- Returns a list of `DiscoveredTool(dir, mcp_tools_path, venv_python, namespace, module)`.

### 6.2 Tool Schema Extraction (`mcp_server.py`)

- For each discovered module, build a "shadow" FastMCP instance and call `module.register(shadow_mcp)`. The shadow instance has its `tool()` method mocked to record `(name, description, func)` into a list.
- After all modules are registered into the shadow, hand the recorded functions to the real `FastMCP` instance, which uses Python type hints to build the input JSON schema.

### 6.3 Subprocess Dispatch (`runner.py`)

`run_tool(full_name: str, args: dict, timeout: float) -> dict`:

```python
# Gateway keeps a registry: full_name (e.g. "image-ocr__ocr_image")
#   → (DiscoveredTool, bare_function_name)
tool, bare_name = REGISTRY[full_name]
cmd = [
    str(tool.venv_python),
    str(tool.mcp_tools_path),
    "call",
    "--name", bare_name,
    "--args", json.dumps(args),
]
proc = subprocess.run(
    cmd, capture_output=True, text=True,
    timeout=timeout, cwd=tool.tool_dir,
)
if proc.returncode != 0:
    raise ToolRunError(proc.stderr.strip() or f"exit {proc.returncode}")
return json.loads(proc.stdout)
```

The registry is built during the discovery phase (§6.1) and the schema-extraction phase (§6.2), so the runner never needs to re-parse the full name.

- `venv_python` is `<tool>/.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows — handled by `sys.platform`).
- If `.venv/` is missing, fall back to `sys.executable` and log a `WARNING`.
- Default timeout: 30s. Configurable per-tool via `gateway.yaml`.

### 6.4 CLI (`cli.py`)

| Subcommand | Behavior |
|---|---|
| `serve` | Start the stdio MCP server. Blocks until stdin closes. |
| `list` | Print all discovered tools (namespace, name, description, parameters). |
| `call <full_name> --args '<json>'` | Run a single tool call, print result JSON. |
| `info <full_name>` | Print the full input schema for one tool. |
| `version` | Print the gateway version. |

Global flags: `--root PATH` (monorepo root, default = auto-detected by walking up from the gateway's own location), `--config PATH` (gateway.yaml), `--verbose`.

---

## 7. Gateway Configuration (Optional)

A `gateway.yaml` next to the gateway may override defaults:

```yaml
root: ".."                      # monorepo root relative to this file
exclude:                        # tool dirs to skip
  - ".github"
  - "docs"
  - "scripts"
timeout_seconds: 30             # default per-tool timeout
tools:                          # per-tool overrides
  web-trigger:
    timeout_seconds: 120        # dry-run can take longer
```

If absent, the gateway uses sensible defaults (root = parent of `agent-gateway/`, no exclusions, 30s timeout).

---

## 8. Per-Tool MCP Surface

### 8.1 `image-ocr__ocr_image` (new tool)

```yaml
input:
  image_path:    string?          # absolute or relative path
  image_base64:  string?          # base64 without data: prefix
  languages:     string[] = ["zh-Hans", "en-US"]
  engine:        "auto" | "vision" | "rapidocr" = "auto"
  detail:        "text" | "lines" | "blocks" = "text"
constraints:
  - exactly one of image_path or image_base64 is required
output:
  text:    string                 # always present (default detail)
  lines:   Line[]                 # when detail="lines"
  blocks:  Block[]                # when detail="blocks"
  meta:
    engine: "vision" | "rapidocr"
    elapsed_ms: int
    image_size: [w, h]
backend resolution:
  "auto"      → macOS picks vision, other platforms pick rapidocr
  "vision"    → macOS Vision (errors on non-darwin)
  "rapidocr"  → rapidocr-onnxruntime (always available)
```

### 8.2 `convert-audio__audio_to_base64`

```yaml
input:
  input_path:       string        # audio file path
  data_uri:         bool = false
  wrap:             int = 76      # 0 = no wrap
output:
  result:           string        # base64 or data URI
  meta:             { size, mime, length }
```

### 8.3 `convert-audio__base64_to_audio`

```yaml
input:
  input:            string        # base64 text, data URI, or path
  output_path:      string?
  json_key:         string?       # dotted path
  urlsafe:          bool = false
  force:            bool = false
output:
  output_path:      string
  bytes:            int
```

### 8.4 `web-search__search`

```yaml
input:
  query:            string
  type:             "google" | "bing" | "baidu" | "gemini" = "google"
  num:              int = 10
  env_file:         string?       # path to .env (for per-call API keys)
output:
  duration:         int           # ms
  results:          [{ title, link, snippet }]
errors:
  - engine misconfigured / upstream failure → tool raises, gateway reports isError
```

### 8.5 `web-trigger__check_config`

```yaml
input:
  config_path:      string
output:
  ok:               bool
  status:           "active" | "idle"
  now:              string (ISO 8601)
  next_window:      string?       # if idle
  message:          string?       # human-readable notes
```

`web-trigger__dry_run` is identical except it opens Playwright headless, attempts one window, and returns the same fields plus a `triggered: bool`.

**Out of scope for MCP** (CLI-only, documented in `web-trigger/README.md`):
- `web-trigger__login` — interactive browser session.
- `web-trigger__run` — long-running scheduler, not a request/response tool call.

---

## 9. Error Handling

| Failure | Gateway behavior |
|---|---|
| `mcp_tools.py` import error | Log `ERROR`, skip that tool, continue discovery. |
| Missing `TOOL_NAMESPACE` or `register` | Log `ERROR`, skip. |
| Tool name collision | Log `WARNING`, keep first, skip duplicates. |
| Subprocess non-zero exit | Return MCP `isError: true` with stderr text in `content[0].text`. |
| Subprocess timeout | Return MCP `isError: true` with `"timeout after Ns"`. |
| JSON parse failure on stdout | Return MCP `isError: true` with parse error. |
| Tool raises exception | Caught by gateway; logged at `ERROR`; surfaced as `isError: true` with the exception class + message. |
| `mcp_tools.py call` invoked with unknown name | Exit code `2`; gateway returns `isError: true` with `"unknown tool: <name>"`. |

**Logging:** stdlib `logging` to `sys.stderr`. Levels: `INFO` for lifecycle (start, discovered N tools, dispatch), `WARNING` for skips/collisions, `ERROR` for failures. `--verbose` raises everything to `DEBUG`. Stdout is reserved for the MCP JSON-RPC stream.

---

## 10. Testing Strategy

### 10.1 Gateway tests

- `test_discovery.py`: use `tmp_path` to build a fake monorepo with 3-4 stub `mcp_tools.py` files; assert correct discovery, exclusion, and `TOOL_NAMESPACE` validation.
- `test_runner.py`: mock `subprocess.run` to verify command construction, timeout handling, and error propagation.
- `test_serve.py`: start the gateway as a real subprocess, use `mcp.client.session` to call `tools/list` and `tools/call`, assert responses.
- `test_cli.py`: use `subprocess.run` against `python -m agent_gateway {list,call,info,version}`.

### 10.2 image-ocr tests

- `test_engine_factory.py`: auto picks `vision` on darwin, `rapidocr` elsewhere; explicit override works.
- `test_vision_backend.py`: `@pytest.mark.skipif(sys.platform != "darwin")`.
- `test_rapidocr_backend.py`: runs in CI on Linux.
- `test_image_input.py`: path / base64 / HEIC conversion / size limits.
- `test_cli.py`: argparse + subprocess.
- `test_mcp_tools.py`: import `mcp_tools` and call `ocr_image` directly with a fixture image.

### 10.3 Retrofit tests

- `convert-audio/tests/test_mcp_tools.py`: smoke-test both tool functions with fixture audio.
- `web-search/tests/test_mcp_tools.py`: smoke-test `search` (use a stubbed engine to avoid needing real API keys in CI).
- `web-trigger/tests/test_mcp_tools.py`: test `check_config` with valid + invalid YAML; `dry_run` against the bundled `test_page.html` (started via `python -m http.server`).

### 10.4 Cross-tool integration

- A P6 test that runs the gateway with all five tools registered, calls each one in sequence against stub data, and asserts no crashes.

---

## 11. Phased Delivery

| Phase | Deliverable | Acceptance |
|---|---|---|
| **P1** | `agent-gateway/` skeleton: discovery, stdio server, CLI (`serve`/`list`/`call`/`info`/`version`) | `agent-gateway serve` starts; `list` reports zero tools. |
| **P2** | `image-ocr/` tool + `mcp_tools.py` | `list` shows `image-ocr__ocr_image`; `call` extracts text from a fixture image. |
| **P3** | `convert-audio/mcp_tools.py` | `convert-audio__audio_to_base64` and `__base64_to_audio` callable end-to-end. |
| **P4** | `web-search/mcp_tools.py` | `web-search__search` callable; smoke test uses a stubbed engine. |
| **P5** | `web-trigger/mcp_tools.py` | `web-trigger__check_config` and `__dry_run` callable; `run`/`login` documented as CLI-only. |
| **P6** | Cross-tool integration test + per-tool README updates | All six tools callable through one gateway; CI green. |

Each Phase is independently mergeable. The current design doc covers all six Phases. The first implementation plan (produced via the `writing-plans` skill) targets **P1 only**; later Phases each get their own plan.

---

## 12. Risks and Open Questions

- **Subprocess latency.** Each tool call spawns a Python interpreter (~100-300ms overhead). For LLM Agents that batch tool calls, this is negligible. If a hot path emerges, v2 can switch to in-process execution with per-tool venv bootstrapping.
- **HEIC and other macOS-specific formats in `image-ocr`.** Pillow may need `pillow-heif` on non-Mac. Phase P2 implementation plan will resolve.
- **web-search engine availability in CI.** Integration tests must avoid hitting real APIs; stubbed engines are used in CI.
- **web-trigger Playwright availability in CI.** P5's `dry_run` test needs Playwright + a browser. CI may need to skip or mock.
- **Future tool dirs.** The discovery walk is shallow (depth = 1). If a tool is ever nested (e.g., `tools/image-ocr/`), the discovery rules need a revisit. Documented as out-of-scope for v1.
- **No formal schema registry.** Tool schemas are derived from Python type hints at gateway startup. This is the standard FastMCP behavior; any drift between CLI argparse and type hints is a known fragility.

---

## 13. References

- `AGENTS.md` — monorepo conventions, isolation rules, Python version.
- `web-search/README.md`, `web-trigger/README.md`, `convert-audio/README.md` — current tool documentation.
- Model Context Protocol specification — https://modelcontextprotocol.io
- FastMCP SDK — `mcp[cli]` on PyPI.

# turbo-toolkit

A monorepo of small, self-contained, single-purpose CLI utilities. Each
top-level directory is its own project with its own language, dependencies,
configuration and README — they share no state.

The repository also ships a **single MCP (Model Context Protocol) server**
([`agent-gateway/`](./agent-gateway/)) that aggregates every tool that
declares an `mcp_tools.py` and exposes them to any MCP-compatible LLM
agent (Claude Desktop, Cursor, Cline, or a custom agent).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](./.python-version)

---

## Tools

| Tool | Language | Description | Status | MCP tools exposed |
| --- | --- | --- | --- | --- |
| [`convert-audio/`](./convert-audio/) | Python | Audio ⇄ Base64 converters for embedding audio in JSON payloads, LLM prompts, etc. | Stable | `convert-audio__audio_to_base64`, `convert-audio__base64_to_audio` |
| [`web-search/`](./web-search/) | Python | Multi-engine search CLI (Google / Bing / Baidu / Gemini) with JSON output. | Stable | _(P4 — planned)_ |
| [`web-trigger/`](./web-trigger/) | Python | Playwright-based windowed web automation: open window by cron / time range → poll element → trigger → post-flow. | Stable | _(P5 — planned)_ |
| [`image-ocr/`](./image-ocr/) | Python | Extract text from images (PNG / JPEG / WebP / HEIC). macOS Vision + cross-platform rapidocr. | Stable | `image-ocr__ocr_image` |
| [`agent-gateway/`](./agent-gateway/) | Python | Single MCP stdio server aggregating all tools above. CLI: `serve` / `list` / `call` / `info` / `version`. | Phase P1+P2+P3 done | _(is the gateway itself)_ |

See each tool's own `README.md` for setup and usage.

---

## Quick start

Requirements: Python 3.12 (see `.python-version`). `pyenv` is recommended.

```bash
git clone https://github.com/turbov10/turbo-toolkit.git
cd turbo-toolkit

# Each tool has its own virtualenv; create one per tool:
cd convert-audio && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../web-search && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../web-trigger && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../image-ocr   && python -m venv .venv && .venv/bin/pip install -r requirements.txt

# Gateway itself:
cd ../agent-gateway && python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

---

## Agent integration (MCP) — end-to-end

Tools that ship `mcp_tools.py` are auto-aggregated by
[`agent-gateway/`](./agent-gateway/). One MCP endpoint, N underlying tool
processes, each running in **its own venv** (per `AGENTS.md` §1).

### Sequence: your LLM agent → `image-ocr` via the gateway

```
       你的 LLM Agent                                               agent-gateway                             image-ocr/.venv
            │                                                             │                                          │
            │── spawn ───────────────────────────────────────────────────▶│                                          │
            │  (.venv/bin/python -m agent_gateway serve)                  │                                          │
            │                                                             │ build_server():                          │
            │                                                             │   for each tool's mcp_tools.py:          │
            │                                                             │     module.register(capturing)           │
            │                                                             │     runner.register(tool)                │
            │                                                             │ fastmcp.run(transport="stdio")           │
            │                                                             │                                          │
            │── JSON-RPC tools/list ─────────────────────────────────────▶│                                          │
            │◀─ {tools:[{name:"image-ocr__ocr_image",inputSchema:{…}}]} ──│                                          │
            │                                                             │                                          │
            │── JSON-RPC tools/call ─────────────────────────────────────▶│                                          │
            │  name="image-ocr__ocr_image"                                │                                          │
            │  args={image_path:"…/p.png",                                │ proxy(**kwargs) → runner.run(...)        │
            │         detail:"text"}                                      │   └─ subprocess.run([                    │
            │                                                             │          python, image-ocr/mcp_tools.py, │
            │                                                             │           "call", "--name","ocr_image",  │
            │                                                             │           "--args","{…}"]) ─────────────▶│
            │                                                             │                                          │ ocr_image(...)
            │                                                             │                                          │ json.dump → stdout
            │                                                             │ ◀── stdout='{"text":"Hello OCR"}' ───────│
            │                                                             │ json.loads(stdout)                       │
            │◀─ {content:[{text:"{…}"}]} ─────────────────────────────────│                                          │
            │  → feedback text to LLM, continue inferring                 │                                          │
```

### Wire it up

**Claude Desktop / Cursor / Cline** — add this to your MCP config:

```json
{
  "mcpServers": {
    "agent-gateway": {
      "command": "/absolute/path/to/turbo-toolkit/agent-gateway/.venv/bin/python",
      "args": ["-m", "agent_gateway", "serve"]
    }
  }
}
```

**Your own agent (Python)** — minimum viable client:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="/…/turbo-toolkit/agent-gateway/.venv/bin/python",
        args=["-m", "agent_gateway", "serve"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover tools dynamically — no hard-coding in your agent.
            tools = (await session.list_tools()).tools
            for t in tools:
                print(t.name, "—", t.description)

            # Call one (this is what your LLM tool-use loop produces).
            result = await session.call_tool(
                "image-ocr__ocr_image",
                {"image_path": "/tmp/photo.png", "detail": "text"},
            )
            print(result.content[0].text)
```

### CLI debugging (no LLM required)

```bash
cd agent-gateway
.venv/bin/python -m agent_gateway list --root ..                              # discover
.venv/bin/python -m agent_gateway info  image-ocr__ocr_image  --root ..       # schema
.venv/bin/python -m agent_gateway call image-ocr__ocr_image \
    --args '{"image_path":"/tmp/p2-fixture.png","engine":"rapidocr","detail":"text"}' \
    --root ..
```

Add a new tool later → just drop a new `<dir>/mcp_tools.py` and restart the
gateway; the Agent picks it up via `tools/list` without code changes on
either side.

---

## Repository conventions

- **Tool independence.** Tools do not share dependencies, virtualenvs, or
  configuration. Never install packages from one tool into another.
- **Python version.** All Python tools target the version pinned in the
  repository root `.python-version` (3.12). Tools may opt in to a local
  `.python-version` to pin a different minor if needed.
- **Virtualenvs.** Each tool owns its own `.venv/` (already in `.gitignore`).
- **Environment variables.** Tool-specific secrets live in the tool's `.env`
  (gitignored). Templates go in `.env.example`.
- **AI agent guidance.** See [`AGENTS.md`](./AGENTS.md).

---

## Contributing

Contributions are welcome. Please read
[`CONTRIBUTING.md`](./CONTRIBUTING.md) before opening an issue or PR.
By participating you agree to follow the
[Code of Conduct](./CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately per [`SECURITY.md`](./SECURITY.md).
**Do not file public issues for security bugs.**

## License

[MIT](./LICENSE) © 2026 turbo-toolkit contributors.

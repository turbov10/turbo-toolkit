# image-ocr

OCR (text extraction) for images, exposed as:

1. A standalone Python API: `image_ocr.cli.run_ocr(...)`.
2. A MCP tool (`image-ocr__ocr_image`) reachable through the repo-level
   [`agent-gateway`](../agent-gateway/) (Phase P2 of the
   [MCP integration design](../superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md)).

Supports macOS **Vision** (fast, on-device) and cross-platform **rapidocr**
(default). Engine selection is automatic on Darwin, configurable per call.

---

## Why

Built because the [design spec §8.1](../superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md#81-image-ocr__ocr_image-new-tool)
calls for a first-class OCR tool from the agent-gateway side. Existing
tools in the toolkit only expose English-flavoured IO helpers; this one
targets the local LLM agent loop end-to-end.

---

## Install

```bash
cd image-ocr
python -m venv .venv

# Pillow + rapidocr (cross-platform; required for the "auto" engine)
.venv/bin/pip install pillow rapidocr-onnxruntime onnxruntime

# Optional: HEIC image support (macOS / iOS photos)
.venv/bin/pip install pillow-heif

# Optional: macOS Vision backend (only used when engine="vision")
.venv/bin/pip install pyobjc-framework-Vision pyobjc-framework-CoreImage
```

When installed, the package exposes:

```
image-ocr/
├── mcp_tools.py          ← gateway entrypoint (TOOL_NAMESPACE = "image-ocr")
├── image_ocr/
│   ├── __init__.py
│   ├── cli.py            ← run_ocr(image_path, image_base64, languages, engine, detail)
│   ├── image_input.py    ← decode from path or base64 (with HEIC and size guards)
│   ├── engine_factory.py ← resolve_engine/get_backend (auto/vision/rapidocr)
│   ├── ocr_types.py      ← Line / Block / OcrResult dataclasses
│   └── backends/
│       ├── base.py
│       ├── rapidocr_backend.py
│       └── vision_backend.py
└── tests/                ← 31 unit + integration tests, run with pytest
```

---

## Usage (Python)

```python
from image_ocr.cli import run_ocr

out = run_ocr(
    image_path="/abs/path/to/photo.png",
    engine="auto",         # "auto" | "vision" | "rapidocr"
    detail="lines",        # "text" | "lines" | "blocks"
)
print(out["text"])
for line in out.get("lines", []):
    print(line["bbox"], line["text"], line["confidence"])
print(out["meta"])
```

Output schema (matches design spec §8.1):

```jsonc
{
  "text": "Hello world",                  // always present (default detail)
  "lines": [                              // when detail="lines"
    {
      "bbox": [x1, y1, x2, y2],
      "text": "Hello world",
      "confidence": 0.987
    }
  ],
  "blocks": [...],                        // when detail="blocks"
  "meta": {
    "engine": "rapidocr",                  // "vision" or "rapidocr"
    "elapsed_ms": 196,
    "image_size": [320, 80],
    "languages": ["zh-Hans", "en-US"]
  }
}
```

Exactly one of `image_path` / `image_base64` is required. Files larger than
25 MB are rejected upfront. HEIC requires `pillow-heif`.

---

## MCP integration

```bash
cd ../agent-gateway
.venv/bin/python -m agent_gateway list --root ..       # shows image-ocr__ocr_image
.venv/bin/python -m agent_gateway info image-ocr__ocr_image --root ..

# One-shot invocation via the same code path the gateway uses for MCP calls:
.venv/bin/python -m agent_gateway call image-ocr__ocr_image \
    --args '{"image_path":"/tmp/p2-fixture.png","engine":"rapidocr","detail":"text"}' \
    --root ..
```

End-to-end (your own LLM agent):

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="../agent-gateway/.venv/bin/python",
        args=["-m", "agent_gateway", "serve"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # discover the tool dynamically (no hard-coded schema in your agent)
            tools = (await session.list_tools()).tools
            ocr = next(t for t in tools if t.name == "image-ocr__ocr_image")

            # call it with whatever the LLM produced
            result = await session.call_tool(
                "image-ocr__ocr_image",
                {"image_path": "/tmp/photo.png", "detail": "text"},
            )
            print(result.content[0].text)
```

The Agent only needs the gateway command/args; new tools added later
(convert-audio, web-search, web-trigger, future tools) are picked up by a
restart with no Agent code changes.

---

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

Covers:

- `test_image_input.py` — path / base64 / size guards / HEIC / corrupt files.
- `test_engine_factory.py` — auto / vision / rapidocr resolution + availability.
- `test_rapidocr_backend.py` — actual OCR against a fixture PNG.
- `test_vision_backend.py` — Darwin-only marker (PyObjC is optional).
- `test_cli.py` — top-level `run_ocr` contract.
- `test_mcp_tools.py` — `mcp_tools.py` registers cleanly + `call` subprocess contract (§4 rule 5).

---

## Notes & limitations

- **v1 has no layout grouping.** `detail="blocks"` returns one-block-per-line.
  A real page-segmenter is on the roadmap (would slot in via a layout backend
  in `image_ocr/backends/layout.py`).
- **rapidocr model weights** are downloaded on first use (~20-40 MB cached in
  `~/.cache` or `~/Library/Caches` depending on platform). The CLI does this
  transparently; the gateway's subprocess makes this a one-time-per-host cost.
- **macOS Vision** needs PyObjC. The factory falls back to `rapidocr` when
  PyObjC is missing, so requesting `engine="auto"` on a clean machine never
  hard-fails.
- **HEIC** on non-macOS requires `pillow-heif`; the input layer registers the
  opener if the package is present and ignores it otherwise.

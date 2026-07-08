"""image-ocr MCP surface (Phase P2).

Exposes one MCP tool, ``image-ocr__ocr_image``, matching design spec §8.1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if False:  # pragma: no cover — TYPE_CHECKING guard only
    from mcp.server.fastmcp import FastMCP

TOOL_NAMESPACE = "image-ocr"


# ---------------------------------------------------------------------------
# Pure functions (importable, testable, callable directly)
# ---------------------------------------------------------------------------

def ocr_image(
    image_path: str | None = None,
    image_base64: str | None = None,
    languages: list[str] | None = None,
    engine: str = "auto",
    detail: str = "text",
) -> dict:
    """Extract text from an image. See design spec §8.1.

    Exactly one of ``image_path`` / ``image_base64`` must be provided.
    ``engine`` ∈ ``{"auto", "vision", "rapidocr"}``.
    ``detail`` ∈ ``{"text", "lines", "blocks"}``.
    """
    # Local import so that ``import mcp_tools`` does not require Pillow /
    # image_ocr / mcp at top level — keeps the gateway's auto-discovery
    # happy even if a tool's deps are missing.
    from image_ocr.cli import run_ocr

    return run_ocr(
        image_path=image_path,
        image_base64=image_base64,
        languages=list(languages) if languages else ["zh-Hans", "en-US"],
        engine=engine,  # type: ignore[arg-type]
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Gateway integration
# ---------------------------------------------------------------------------

def register(mcp: "FastMCP") -> None:
    """Register the tool on the given MCP server."""
    mcp.tool(
        name=f"{TOOL_NAMESPACE}__ocr_image",
        description=(
            "Extract text from an image (PNG / JPEG / WebP / HEIC). "
            "Returns text plus optional per-line bounding boxes and OCR "
            "metadata (engine, elapsed_ms, image_size, languages)."
        ),
    )(ocr_image)


# ---------------------------------------------------------------------------
# Subprocess entrypoint (invoked by agent-gateway's SubprocessRunner)
# ---------------------------------------------------------------------------

def _cli_call(name: str, args_json: str) -> int:
    fn = getattr(sys.modules[__name__], name, None)
    if fn is None or not callable(fn):
        print(f"unknown tool: {name}", file=sys.stderr)
        return 2
    try:
        params = json.loads(args_json)
        result = fn(**params)
    except Exception as exc:  # surfaced as MCP isError by the gateway
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="image-ocr.mcp_tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    call_p = sub.add_parser("call")
    call_p.add_argument("--name", required=True)
    call_p.add_argument("--args", default="{}")
    ns = parser.parse_args()
    if ns.cmd == "call":
        sys.exit(_cli_call(ns.name, ns.args))

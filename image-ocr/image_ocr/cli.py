"""Top-level OCR entry point — shared by CLI + MCP tool.

See design spec §8.1 for the public schema of the returned dict.
"""
from __future__ import annotations

from typing import Any

from PIL import Image

from image_ocr.engine_factory import EngineName, get_backend, resolve_engine
from image_ocr.image_input import decode


def run_ocr(
    *,
    image_path: str | None = None,
    image_base64: str | None = None,
    languages: list[str] | None = None,
    engine: EngineName = "auto",
    detail: str = "text",
) -> dict:
    """OCR an image and return a JSON-serialisable dict.

    Returns shape::

        {
          "text":    "<concatenated text>",   # always present (default detail)
          "lines":   [<Line>],                # when detail="lines"
          "blocks":  [<Block>],               # when detail="blocks"
          "meta":    {engine, elapsed_ms, image_size, languages}
        }
    """
    if detail not in ("text", "lines", "blocks"):
        raise ValueError(
            f"detail must be one of text/lines/blocks, got {detail!r}",
        )

    langs = list(languages or ["zh-Hans", "en-US"])
    img: Image.Image = decode(image_path=image_path, image_base64=image_base64)

    chosen = resolve_engine(engine)
    backend = get_backend(chosen)
    result = backend.recognize(img, langs)

    payload: dict[str, Any] = {
        "meta": {
            "engine": result.engine,
            "elapsed_ms": result.elapsed_ms,
            "image_size": list(result.image_size),
            "languages": list(result.languages),
        },
    }
    if detail in ("text", "lines", "blocks"):
        payload["text"] = result.joined_text()
    if detail in ("lines", "blocks"):
        payload["lines"] = [
            {
                "bbox": list(line.bbox),
                "text": line.text,
                "confidence": line.confidence,
            }
            for line in result.lines
        ]
    if detail == "blocks":
        # Each line is its own block in v1 (no layout grouping yet).
        payload["blocks"] = [
            {
                "bbox": list(line.bbox),
                "lines": [{
                    "bbox": list(line.bbox),
                    "text": line.text,
                    "confidence": line.confidence,
                }],
            }
            for line in result.lines
        ]
    return payload

"""Data classes describing OCR results.

These are deliberately backend-agnostic. Each backend's
:meth:`OcrBackend.recognize` returns :class:`OcrResult` and the gateway's
``mcp_tools`` layer shape-matches that into the JSON the agent sees.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DetailLevel = Literal["text", "lines", "blocks"]


@dataclass(frozen=True)
class Line:
    """A single recognised text line with its bounding box + confidence."""

    bbox: tuple[int, int, int, int]
    text: str
    confidence: float


@dataclass(frozen=True)
class Block:
    """A group of lines that share a parent region on the page."""

    bbox: tuple[int, int, int, int]
    lines: list[Line] = field(default_factory=list)


@dataclass(frozen=True)
class OcrResult:
    """Backend-agnostic OCR output.

    ``lines`` is the canonical structured form. ``text`` and ``blocks`` are
    derived if the caller asks for them (via ``detail=`` in ``run_ocr``).
    """

    lines: list[Line]
    engine: Literal["vision", "rapidocr"]
    elapsed_ms: int
    image_size: tuple[int, int]
    languages: list[str]

    def joined_text(self) -> str:
        return "\n".join(line.text for line in self.lines)

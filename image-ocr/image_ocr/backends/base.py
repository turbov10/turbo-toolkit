"""OCR backend interface and shared helpers."""
from __future__ import annotations

from typing import Protocol

from PIL import Image

from image_ocr.ocr_types import OcrResult


class OcrBackend(Protocol):
    """An OCR backend (rapidocr, vision, ...) returns :class:`OcrResult`."""

    name: str  # "vision" or "rapidocr"

    def recognize(self, image: Image.Image, languages: list[str]) -> OcrResult:
        """Recognise text in ``image`` honouring ``languages`` preference.

        Implementations are free to interpret ``languages`` as hints (e.g.
        vision languages, tesseract lang codes). The default rapidocr backend
        ignores this parameter for now and uses the system default.
        """
        ...


def _flatten_lines(
    boxes: list[list[list[int]]], texts: list[str], confs: list[float],
) -> list:
    """Convert rapidocr-style ``[(box, text, conf), ...]`` tuples to Lines."""
    from image_ocr.ocr_types import Line

    out = []
    for box, text, conf in zip(boxes, texts, confs):
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        out.append(Line(
            bbox=(min(xs), min(ys), max(xs), max(ys)),
            text=text,
            confidence=float(conf),
        ))
    return out

"""rapidocr-onnxruntime backend (cross-platform, weights cached on first use)."""
from __future__ import annotations

import time

from image_ocr.ocr_types import OcrResult
from image_ocr.backends.base import OcrBackend, _flatten_lines


class RapidOcrBackend:
    name = "rapidocr"

    def __init__(self) -> None:
        # Lazy import — keeps the package importable even if heavy deps miss.
        from rapidocr_onnxruntime import RapidOCR
        self._engine = RapidOCR()

    def recognize(self, image, languages: list[str]) -> OcrResult:
        import numpy as np

        t0 = time.perf_counter()
        width, height = image.size
        arr = np.array(image.convert("RGB"))  # rapidocr expects RGB ndarray
        # rapidocr returns (results, elapse) where results = list of [box, text, conf]
        results, _elapse = self._engine(arr)
        lines: list = []
        if results:
            for item in results:
                box, text, conf = item
                xs = [pt[0] for pt in box]
                ys = [pt[1] for pt in box]
                from image_ocr.ocr_types import Line
                lines.append(Line(
                    bbox=(int(min(xs)), int(min(ys)),
                          int(max(xs)), int(max(ys))),
                    text=str(text),
                    confidence=float(conf),
                ))
        elapsed = int((time.perf_counter() - t0) * 1000)
        return OcrResult(
            lines=lines,
            engine="rapidocr",
            elapsed_ms=elapsed,
            image_size=(width, height),
            languages=languages,
        )

    def is_available(self) -> bool:
        try:
            import rapidocr_onnxruntime  # noqa: F401
            return True
        except ImportError:
            return False

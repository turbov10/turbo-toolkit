"""macOS Vision backend (lazy import of PyObjC).

This backend is only meaningful on Darwin.  When ``engine="vision"`` is
requested on other platforms — or when PyObjC is not installed — the factory
in :mod:`image_ocr.engine_factory` falls back to ``rapidocr``.
"""
from __future__ import annotations

import sys
import time
from typing import Any

from image_ocr.ocr_types import OcrResult, Line


class VisionBackend:
    name = "vision"

    def recognize(self, image, languages: list[str]) -> OcrResult:
        if sys.platform != "darwin":
            raise RuntimeError(
                "macOS Vision backend requested but platform is "
                f"{sys.platform!r}; only darwin is supported.",
            )
        try:
            import objc  # noqa: F401  type: ignore[import-not-found]
            from Vision import (  # type: ignore[import-not-found]
                VNRecognizeTextRequest,
                VNImageRequestHandler,
            )
            from Quartz import (  # type: ignore[import-not-found]
                CGImageRef,
            )
        except ImportError as exc:
            raise RuntimeError(
                "macOS Vision backend requires PyObjC: "
                "`pip install pyobjc-framework-Vision pyobjc-framework-CoreImage`",
            ) from exc

        t0 = time.perf_counter()
        width, height = image.size
        # Encode to raw RGBA bytes for Vision.
        rgba = image.convert("RGBA").tobytes()
        handler = VNImageRequestHandler.alloc().initWithData_options_(
            rgba, {"CIImage": None},
        )
        request = VNRecognizeTextRequest.alloc().init()
        if languages:
            # Vision supports BCP-47 like en-US, zh-Hans.
            try:
                request.setRecognitionLanguages_(languages)
            except Exception:  # noqa: BLE001
                pass

        ok = handler.performRequests_error_([request], None)
        if not ok:
            raise RuntimeError("Vision VNRecognizeTextRequest failed")

        observations = request.results() or []
        lines: list[Line] = []
        for obs in observations:
            boxes = obs.boundingBox()
            text = "".join(obs.topCandidates_(1)[0].string())
            # Normalise bbox: Vision uses normalised (0..1) coords, origin
            # bottom-left. Convert to absolute pixel coords, origin top-left.
            x = boxes.origin.x * width
            y = (1 - boxes.origin.y - boxes.size.height) * height
            w = boxes.size.width * width
            h = boxes.size.height * height
            conf = float(obs.confidence() or 0.0)
            lines.append(Line(
                bbox=(int(x), int(y), int(x + w), int(y + h)),
                text=text,
                confidence=conf,
            ))
        elapsed = int((time.perf_counter() - t0) * 1000)
        return OcrResult(
            lines=lines,
            engine="vision",
            elapsed_ms=elapsed,
            image_size=(width, height),
            languages=languages,
        )

    def is_available(self) -> bool:
        """Best-effort check: returns True only on darwin AND when PyObjC import succeeds."""
        if sys.platform != "darwin":
            return False
        try:
            import objc  # noqa: F401  type: ignore[import-not-found]
            return True
        except ImportError:
            return False

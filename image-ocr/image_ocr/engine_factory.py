"""Choose an OCR backend based on platform + caller preference."""
from __future__ import annotations

import sys
from typing import Literal

EngineName = Literal["auto", "vision", "rapidocr"]


def resolve_engine(preference: EngineName = "auto") -> str:
    """Return the backend name to use for this call.

    ``auto``:
        - on Darwin with PyObjC available → ``"vision"``
        - otherwise → ``"rapidocr"``

    ``"vision"`` is honored explicitly; if unavailable, an error is raised
    by :func:`get_backend` so the caller sees a clear message.
    """
    if preference == "vision":
        return "vision"
    if preference == "rapidocr":
        return "rapidocr"
    # auto
    if sys.platform == "darwin":
        from image_ocr.backends.vision_backend import VisionBackend
        if VisionBackend().is_available():
            return "vision"
    return "rapidocr"


def get_backend(name: str):
    """Return a backend instance by name; raise on unsupported / missing deps."""
    if name == "vision":
        from image_ocr.backends.vision_backend import VisionBackend
        be = VisionBackend()
        if not be.is_available():
            raise RuntimeError(
                "vision backend requested but unavailable "
                "(need PyObjC + macOS, or engine='rapidocr').",
            )
        return be
    if name == "rapidocr":
        from image_ocr.backends.rapidocr_backend import RapidOcrBackend
        return RapidOcrBackend()
    raise ValueError(f"unknown engine: {name!r}")

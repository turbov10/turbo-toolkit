"""RapidOCR backend smoke tests (marked; skip when imports fail)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.rapidocr


def test_rapidocr_backend_available():
    from image_ocr.backends.rapidocr_backend import RapidOcrBackend
    be = RapidOcrBackend.__init__.__doc__  # noqa: F841  just touch the class
    # Now actually import the underlying engine to confirm deps.
    from rapidocr_onnxruntime import RapidOCR  # noqa: F401
    backend = RapidOcrBackend()
    assert backend.is_available()


def test_rapidocr_recognizes_text(tiny_png):
    from image_ocr.backends.rapidocr_backend import RapidOcrBackend
    from PIL import Image
    backend = RapidOcrBackend()
    img = Image.open(tiny_png)
    result = backend.recognize(img, languages=["en-US"])
    assert result.engine == "rapidocr"
    assert result.image_size == (320, 80)
    assert isinstance(result.lines, list)
    assert any("Hello" in line.text or "OCR" in line.text
               for line in result.lines)

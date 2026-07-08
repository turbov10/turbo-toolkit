"""macOS Vision backend tests (skipped off Darwin or without PyObjC)."""
from __future__ import annotations

import sys

import pytest

pytestmark = [
    pytest.mark.vision,
    pytest.mark.skipif(sys.platform != "darwin", reason="Vision is macOS-only"),
]


def test_vision_is_available_marker_only():
    """Light-weight probe so the marker fixture exists; full recognition is
    exercised by ``test_vision_recognizes_text`` when PyObjC is installed."""
    from image_ocr.backends.vision_backend import VisionBackend
    be = VisionBackend()
    assert hasattr(be, "is_available")

"""Unit tests for engine resolution + get_backend."""
from __future__ import annotations

import sys

import pytest

from image_ocr.engine_factory import get_backend, resolve_engine


def test_auto_prefers_vision_on_darwin_when_available(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin", raising=False)

    # Pretend Vision is available by faking is_available.
    from image_ocr.backends import vision_backend

    monkeypatch.setattr(
        vision_backend.VisionBackend, "is_available", lambda self: True,
    )
    assert resolve_engine("auto") == "vision"


def test_auto_falls_back_to_rapidocr_when_vision_unavailable(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin", raising=False)
    from image_ocr.backends import vision_backend
    monkeypatch.setattr(
        vision_backend.VisionBackend, "is_available", lambda self: False,
    )
    assert resolve_engine("auto") == "rapidocr"


def test_auto_on_non_darwin_is_rapidocr(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux", raising=False)
    assert resolve_engine("auto") == "rapidocr"


def test_explicit_vision_is_preserved():
    assert resolve_engine("vision") == "vision"


def test_explicit_rapidocr_is_preserved():
    assert resolve_engine("rapidocr") == "rapidocr"


def test_unknown_engine_raises_in_factory():
    with pytest.raises(ValueError):
        get_backend("mystery")

"""Shared pytest fixtures for image-ocr tests."""
from __future__ import annotations

import base64 as _b64
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont


@pytest.fixture(scope="session")
def font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", size=28,
        )
    except OSError:
        return ImageFont.load_default()


@pytest.fixture
def tiny_png(tmp_path: Path, font) -> Path:
    """A small PNG with the word 'Hello' drawn on it (English OCR-able)."""
    img = Image.new("RGB", (320, 80), "white")
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Hello OCR", fill="black", font=font)
    path = tmp_path / "tiny.png"
    img.save(path)
    return path


@pytest.fixture
def tiny_png_b64(tiny_png: Path) -> str:
    raw = tiny_png.read_bytes()
    return _b64.b64encode(raw).decode("ascii")


@pytest.fixture
def empty_png(tmp_path: Path) -> Path:
    img = Image.new("RGB", (40, 40), "white")
    path = tmp_path / "empty.png"
    img.save(path)
    return path

"""Unit tests for ``image_ocr.image_input.decode``."""
from __future__ import annotations

import base64 as _b64

import pytest

from image_ocr.image_input import ImageInputError, decode


def test_decode_from_path(tiny_png):
    img = decode(image_path=str(tiny_png))
    assert img.size == (320, 80)


def test_decode_from_base64(tiny_png, tiny_png_b64):
    img = decode(image_base64=tiny_png_b64)
    assert img.size == (320, 80)


def test_both_inputs_raises():
    with pytest.raises(ImageInputError, match="exactly one"):
        decode(image_path="x", image_base64="y")


def test_neither_input_raises():
    with pytest.raises(ImageInputError, match="exactly one"):
        decode()


def test_missing_file(tmp_path):
    with pytest.raises(ImageInputError, match="not found"):
        decode(image_path=str(tmp_path / "no.png"))


def test_invalid_base64():
    with pytest.raises(ImageInputError, match="invalid base64"):
        decode(image_base64="not-valid-base64!!!")


def test_oversize_base64_rejected():
    huge = _b64.b64encode(b"\x00" * (26 * 1024 * 1024)).decode()
    with pytest.raises(ImageInputError, match="too large"):
        decode(image_base64=huge)


def test_corrupt_image_file_rejected(tmp_path):
    p = tmp_path / "corrupt.png"
    p.write_bytes(b"not actually an image")
    with pytest.raises(ImageInputError, match="cannot decode"):
        decode(image_path=str(p))

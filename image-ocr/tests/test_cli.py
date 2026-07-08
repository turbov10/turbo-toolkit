"""Unit tests for the top-level CLI entry point ``run_ocr``."""
from __future__ import annotations

import pytest

from image_ocr.cli import run_ocr
from image_ocr.image_input import ImageInputError


def test_run_ocr_path_text_default(tiny_png):
    out = run_ocr(image_path=str(tiny_png), engine="rapidocr", detail="text")
    assert "text" in out
    assert "meta" in out
    assert out["meta"]["engine"] in ("vision", "rapidocr")
    assert isinstance(out["meta"]["elapsed_ms"], int)
    assert out["meta"]["image_size"] == [320, 80]


def test_run_ocr_lines_detail_returns_lines(tiny_png):
    out = run_ocr(
        image_path=str(tiny_png), engine="rapidocr", detail="lines",
    )
    assert "lines" in out
    assert "text" in out
    assert isinstance(out["lines"], list)
    if out["lines"]:
        line = out["lines"][0]
        assert set(line.keys()) == {"bbox", "text", "confidence"}


def test_run_ocr_blocks_detail(tiny_png):
    out = run_ocr(
        image_path=str(tiny_png), engine="rapidocr", detail="blocks",
    )
    assert "blocks" in out
    assert isinstance(out["blocks"], list)


def test_run_ocr_invalid_detail_raises(tiny_png):
    with pytest.raises(ValueError, match="detail"):
        run_ocr(image_path=str(tiny_png), detail="bogus")  # type: ignore[arg-type]


def test_run_ocr_requires_exactly_one_input():
    with pytest.raises(ImageInputError):
        run_ocr()


def test_run_ocr_from_base64(tiny_png, tiny_png_b64):
    out = run_ocr(image_base64=tiny_png_b64, engine="rapidocr", detail="text")
    assert "text" in out
    assert out["meta"]["image_size"] == [320, 80]


def test_run_ocr_empty_image_returns_text(empty_png):
    out = run_ocr(image_path=str(empty_png), engine="rapidocr", detail="text")
    assert out["text"] == ""

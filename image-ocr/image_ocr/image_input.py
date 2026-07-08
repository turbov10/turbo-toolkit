"""Decode an image from a path or base64 string into ``PIL.Image.Image``."""
from __future__ import annotations

import base64 as _b64
import binascii
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 25 * 1024 * 1024  # 25 MB hard cap for safety.
_SUPPORTED_HEIC = {".heic", ".heif"}


class ImageInputError(ValueError):
    """Raised for unrecoverable input errors (both sources missing, OOM)."""


def _ensure_heif_registered() -> None:
    """Register pillow-heif so PIL can open HEIC/HEIF if available."""
    try:
        from pillow_heif import register_heif_opener  # type: ignore[import-not-found]
        register_heif_opener()
    except ImportError:
        pass  # HEIC support is optional.


def decode(
    *,
    image_path: str | None = None,
    image_base64: str | None = None,
) -> Image.Image:
    """Open an image from either ``image_path`` or ``image_base64``.

    Exactly one must be provided. Returns an RGB ``PIL.Image.Image``.
    """
    if (image_path is None) == (image_base64 is None):
        raise ImageInputError(
            "exactly one of image_path or image_base64 is required",
        )

    _ensure_heif_registered()

    if image_path:
        src = Path(image_path).expanduser().resolve()
        if not src.is_file():
            raise ImageInputError(f"image not found: {src}")
        size = src.stat().st_size
        if size > MAX_IMAGE_BYTES:
            raise ImageInputError(
                f"image too large: {size} bytes (max {MAX_IMAGE_BYTES})",
            )
        try:
            return Image.open(src)
        except (UnidentifiedImageError, OSError) as exc:
            raise ImageInputError(
                f"cannot decode image at {src}: {exc}",
            ) from exc

    # image_base64 path
    try:
        raw = _b64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageInputError(f"invalid base64: {exc}") from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageInputError(
            f"image too large: {len(raw)} bytes (max {MAX_IMAGE_BYTES})",
        )
    from io import BytesIO
    try:
        return Image.open(BytesIO(raw))
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageInputError(f"cannot decode base64 image: {exc}") from exc

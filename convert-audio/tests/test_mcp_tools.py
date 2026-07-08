"""Smoke tests for ``convert-audio/mcp_tools.py`` (Phase P3).

These tests exercise the two MCP tool functions directly (same code path
that the gateway's ``SubprocessRunner`` would invoke).  They do NOT spawn a
subprocess — subprocess + end-to-end behaviour is covered by
``agent-gateway/tests/test_serve_integration.py``.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest

from mcp_tools import audio_to_base64, base64_to_audio


def _write_tiny_wav(path: Path, duration_s: float = 0.05, rate: int = 8000) -> Path:
    """Write a tiny valid WAV file (silence) at ``path`` and return it."""
    n_frames = int(rate * duration_s)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n_frames)
    return path


@pytest.fixture
def tiny_wav(tmp_path: Path) -> Path:
    return _write_tiny_wav(tmp_path / "sine.wav")


# ---------------------------------------------------------------------------
# audio_to_base64
# ---------------------------------------------------------------------------


def test_audio_to_base64_returns_b64_and_meta(tiny_wav: Path) -> None:
    out = audio_to_base64(str(tiny_wav), wrap=0)
    assert set(out.keys()) == {"result", "meta"}
    assert isinstance(out["result"], str)
    assert out["result"].endswith("=") or len(out["result"]) % 4 == 0
    assert out["meta"]["size"] == tiny_wav.stat().st_size
    # mimetypes is platform-dependent (audio/wav vs audio/x-wav)
    assert out["meta"]["mime"].startswith("audio/") and "wav" in out["meta"]["mime"]
    # length is the raw base64 char count (no wrap, no data: prefix)
    assert out["meta"]["length"] == len(out["result"])


def test_audio_to_base64_strict_extension_rejects_unknown(tmp_path: Path) -> None:
    bad = tmp_path / "clip.bin"
    bad.write_bytes(b"\x00" * 10)
    with pytest.raises(ValueError, match="不支持的音频扩展名"):
        audio_to_base64(str(bad))


def test_audio_to_base64_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        audio_to_base64(str(tmp_path / "no-such.wav"))


def test_audio_to_base64_data_uri(tiny_wav: Path) -> None:
    out = audio_to_base64(str(tiny_wav), data_uri=True)
    assert out["result"].startswith("data:audio/")
    assert ";base64," in out["result"]


def test_audio_to_base64_data_uri_mime_audio_wav(tiny_wav: Path) -> None:
    """MIME may be audio/wav or audio/x-wav depending on platform mimetypes."""
    out = audio_to_base64(str(tiny_wav), data_uri=True)
    assert out["result"].startswith("data:audio/x-wav;base64,") or out[
        "result"
    ].startswith("data:audio/wav;base64,")


def test_audio_to_base64_no_wrap(tiny_wav: Path) -> None:
    out = audio_to_base64(str(tiny_wav), wrap=0)
    assert "\n" not in out["result"]


# ---------------------------------------------------------------------------
# base64_to_audio
# ---------------------------------------------------------------------------


def test_base64_to_audio_plain_text_roundtrip(tiny_wav: Path, tmp_path: Path) -> None:
    encoded = audio_to_base64(str(tiny_wav), wrap=0)["result"]
    out_path = tmp_path / "restored.wav"
    result = base64_to_audio(encoded, output_path=str(out_path))
    assert result["output_path"] == str(out_path)
    assert result["bytes"] == tiny_wav.stat().st_size
    assert out_path.read_bytes() == tiny_wav.read_bytes()


def test_base64_to_audio_data_uri_input(tmp_path: Path, tiny_wav: Path) -> None:
    encoded = audio_to_base64(str(tiny_wav), data_uri=True)["result"]
    result = base64_to_audio(encoded, output_path=str(tmp_path / "from-uri"))
    assert result["bytes"] == tiny_wav.stat().st_size
    assert Path(result["output_path"]).suffix == ".wav"


def test_base64_to_audio_data_uri_suffix_from_mime(
    tmp_path: Path, tiny_wav: Path
) -> None:
    """Suffix defaulting rules: when output has no extension, use MIME map."""
    encoded = audio_to_base64(str(tiny_wav), data_uri=True)["result"]
    result = base64_to_audio(encoded, output_path=str(tmp_path / "no-ext"))
    assert Path(result["output_path"]).suffix == ".wav"


def test_base64_to_audio_urlsafe(tiny_wav: Path, tmp_path: Path) -> None:
    raw = tiny_wav.read_bytes()
    urlsafe = _base64_urlsafe(raw).decode("ascii")
    out = tmp_path / "x.wav"
    result = base64_to_audio(urlsafe, output_path=str(out), urlsafe=True)
    assert result["bytes"] == len(raw)
    assert out.read_bytes() == raw


def test_base64_to_audio_json_field(tiny_wav: Path, tmp_path: Path) -> None:
    encoded = audio_to_base64(str(tiny_wav), wrap=0)["result"]
    payload = json.dumps({"nested": {"audio": encoded}})
    out = tmp_path / "from-json.wav"
    result = base64_to_audio(
        payload,
        output_path=str(out),
        json_key="nested.audio",
    )
    assert result["bytes"] == tiny_wav.stat().st_size
    assert out.read_bytes() == tiny_wav.read_bytes()


def test_base64_to_audio_refuses_overwrite(tiny_wav: Path, tmp_path: Path) -> None:
    encoded = audio_to_base64(str(tiny_wav), wrap=0)["result"]
    out = tmp_path / "x.wav"
    out.write_bytes(b"placeholder")
    with pytest.raises(FileExistsError, match="已存在"):
        base64_to_audio(encoded, output_path=str(out))


def test_base64_to_audio_force_overwrites(tiny_wav: Path, tmp_path: Path) -> None:
    encoded = audio_to_base64(str(tiny_wav), wrap=0)["result"]
    out = tmp_path / "x.wav"
    out.write_bytes(b"placeholder")
    base64_to_audio(encoded, output_path=str(out), force=True)
    assert out.read_bytes() == tiny_wav.read_bytes()


def test_base64_to_audio_input_is_path(tiny_wav: Path, tmp_path: Path) -> None:
    """If `input` is an existing file, read text from it first."""
    encoded = audio_to_base64(str(tiny_wav), wrap=0)["result"]
    b64_file = tmp_path / "clip.b64.txt"
    b64_file.write_text(encoded, encoding="utf-8")
    out = tmp_path / "restored.wav"
    result = base64_to_audio(str(b64_file), output_path=str(out))
    assert result["bytes"] == tiny_wav.stat().st_size


def test_base64_to_audio_invalid_b64_raises(tmp_path: Path) -> None:
    out = tmp_path / "x.wav"
    with pytest.raises(ValueError, match="Base64 解码失败"):
        base64_to_audio("not valid base64!!!", output_path=str(out))


# ---------------------------------------------------------------------------
# Subprocess entrypoint smoke test (matches design spec §4 contract rule 5)
# ---------------------------------------------------------------------------


def test_cli_call_via_subprocess(tiny_wav: Path) -> None:
    """Run `mcp_tools.py call` as a subprocess — contract §4 rule 5."""
    import os
    import subprocess
    import sys as _sys

    # tests/test_mcp_tools.py -> parents[1] = convert-audio/
    tool_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tool_dir) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [
        _sys.executable,
        str(tool_dir / "mcp_tools.py"),
        "call",
        "--name",
        "audio_to_base64",
        "--args",
        json.dumps({"input_path": str(tiny_wav)}),
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=str(tool_dir)
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert "wav" in payload["meta"]["mime"]


def test_cli_call_unknown_tool_exits_2(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys as _sys

    tool_dir = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tool_dir) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [
            _sys.executable,
            str(tool_dir / "mcp_tools.py"),
            "call",
            "--name",
            "nonexistent",
            "--args",
            "{}",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tool_dir),
    )
    assert proc.returncode == 2
    assert "unknown tool" in proc.stderr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base64_urlsafe(raw: bytes) -> bytes:
    import base64

    return base64.urlsafe_b64encode(raw)

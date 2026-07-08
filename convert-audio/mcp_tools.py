"""convert-audio MCP surface (Phase P3).

Exposes two MCP tools:

* ``convert-audio__audio_to_base64`` — encode an audio file to Base64 or Data URI.
* ``convert-audio__base64_to_audio`` — decode Base64 / Data URI / JSON-field
  text back to an audio file.

The actual encoding / decoding logic lives in ``audio_to_base64.py`` and
``base64_to_audio.py`` (preserved for direct CLI use).  This module is a thin
adapter that imports the helpers and shapes the output to match the
agent-gateway contract (see
``docs/superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md``
§8.2 / §8.3).
"""
from __future__ import annotations

import argparse
import base64 as _base64_stdlib  # noqa: F401  (forces `base64` into globals
import json                            # for the `call` subcommand's __main__)
import sys
from pathlib import Path

if False:  # pragma: no cover — TYPE_CHECKING guard only
    from mcp.server.fastmcp import FastMCP

TOOL_NAMESPACE = "convert-audio"


# ---------------------------------------------------------------------------
# Pure functions (importable, testable, callable directly)
# ---------------------------------------------------------------------------

def audio_to_base64(
    input_path: str,
    data_uri: bool = False,
    wrap: int = 76,
) -> dict:
    """Encode ``input_path`` to Base64 and return ``{result, meta}``.

    See design spec §8.2.  ``result`` is plain Base64 text (wrapped at
    ``wrap`` columns, or single-line when ``wrap == 0``) unless
    ``data_uri`` is True, in which case it is a ``data:<mime>;base64,...`` URL.
    """
    from audio_to_base64 import (
        encode_audio_to_base64,
        format_base64_output,
        guess_audio_mime_type,
        validate_input_file,
    )

    src = Path(input_path).expanduser().resolve()
    validate_input_file(src, strict_extension=True)
    b64 = encode_audio_to_base64(src)
    text = format_base64_output(
        b64,
        file_path=src,
        as_data_uri=data_uri,
        wrap_width=wrap if wrap > 0 else 0,
    )
    return {
        "result": text,
        "meta": {
            "size": src.stat().st_size,
            "mime": guess_audio_mime_type(src),
            "length": len(b64),
        },
    }


def base64_to_audio(
    input: str,
    output_path: str | None = None,
    json_key: str | None = None,
    urlsafe: bool = False,
    force: bool = False,
) -> dict:
    """Decode Base64 text / Data URI / JSON-field back to an audio file.

    ``input`` may be either a filesystem path (any existing file is read as
    text) or a raw string.  See design spec §8.3.  Returns
    ``{output_path, bytes}``; the file is written to ``output_path`` (or a
    temp location derived from MIME type if not provided).
    """
    from base64_to_audio import (
        MIME_TO_EXTENSION,
        decode_base64_to_bytes,
        ensure_can_write,
        parse_input_text,
        read_text_file,
    )

    raw_path = Path(input).expanduser()
    # Use os.path.isfile (returns False on long strings instead of raising)
    # instead of Path.is_file() which calls os.stat() and raises ENAMETOOLONG.
    import os
    raw_text = read_text_file(raw_path) if os.path.isfile(raw_path) else input

    parsed = parse_input_text(raw_text, json_key=json_key)
    audio_bytes = decode_base64_to_bytes(parsed.base64_text, urlsafe=urlsafe)

    if output_path:
        out = Path(output_path).expanduser().resolve()
    elif raw_path.is_file():
        out = raw_path.with_suffix("")
    else:
        out = Path("/tmp/convert-audio-decoded")
    if not out.suffix:
        suffix = MIME_TO_EXTENSION.get(parsed.mime_type or "", ".bin")
        out = out.with_suffix(suffix)
    ensure_can_write(out, force=force)
    out.write_bytes(audio_bytes)
    return {"output_path": str(out), "bytes": len(audio_bytes)}


# ---------------------------------------------------------------------------
# Gateway integration
# ---------------------------------------------------------------------------

def register(mcp: "FastMCP") -> None:
    """Register both tools on the given MCP server."""
    mcp.tool(
        name=f"{TOOL_NAMESPACE}__audio_to_base64",
        description="Encode an audio file (mp3/wav/flac/m4a/aac/ogg/opus/webm/aiff) to Base64 text or a data: URI.",
    )(audio_to_base64)
    mcp.tool(
        name=f"{TOOL_NAMESPACE}__base64_to_audio",
        description="Decode Base64 text (plain, data: URI, or JSON-field) back to an audio file. Returns the file path and byte count.",
    )(base64_to_audio)


# ---------------------------------------------------------------------------
# Subprocess entrypoint (invoked by agent-gateway's SubprocessRunner)
# ---------------------------------------------------------------------------

def _cli_call(name: str, args_json: str) -> int:
    fn = getattr(sys.modules[__name__], name, None)
    if fn is None or not callable(fn):
        print(f"unknown tool: {name}", file=sys.stderr)
        return 2
    try:
        result = fn(**json.loads(args_json))
    except Exception as exc:  # surfaced as MCP isError by the gateway
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="convert-audio.mcp_tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    call_p = sub.add_parser("call")
    call_p.add_argument("--name", required=True)
    call_p.add_argument("--args", default="{}")
    ns = parser.parse_args()
    if ns.cmd == "call":
        sys.exit(_cli_call(ns.name, ns.args))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
base64_to_audio.py

把 Base64 文本还原为音频文件。

支持输入：

1. 纯 Base64 文本：
   SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU...

2. 带换行的 Base64 文本：
   SUQzBAAAAAAAI1RTU0UAAAAPAAAD
   TGF2ZjU...

3. Data URI：
   data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU...

4. JSON 文件中的 Base64 字段：
   {
     "file_name": "demo.mp3",
     "mime_type": "audio/mpeg",
     "base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU..."
   }

示例：

1. 还原为 mp3：
   python base64_to_audio.py ./outputs/demo.base64.txt -o ./outputs/restored.mp3

2. 从 Data URI 自动推断扩展名：
   python base64_to_audio.py ./outputs/demo.data-uri.txt -o ./outputs/restored

3. 强制覆盖已有文件：
   python base64_to_audio.py ./outputs/demo.base64.txt -o ./outputs/restored.mp3 --force

4. 只校验 Base64，不写文件：
   python base64_to_audio.py ./outputs/demo.base64.txt --validate-only

5. 从 JSON 字段读取：
   python base64_to_audio.py ./outputs/demo.json -o ./outputs/restored.mp3 --json-key base64
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MIME_TO_EXTENSION = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/webm": ".webm",
    "audio/aiff": ".aiff",
    "audio/x-aiff": ".aiff",
}


@dataclass(frozen=True)
class ParsedBase64Input:
    """
    解析后的 Base64 输入。
    """

    base64_text: str
    mime_type: str | None = None
    source_kind: str = "plain"


def read_text_file(input_path: Path) -> str:
    """
    读取文本文件。
    """
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")

    if not input_path.is_file():
        raise ValueError(f"输入路径不是文件：{input_path}")

    return input_path.read_text(encoding="utf-8").strip()


def extract_json_value(raw_text: str, json_key: str) -> str:
    """
    从 JSON 文本中提取指定字段。
    """
    try:
        data: Any = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"输入不是合法 JSON：{e}") from e

    current: Any = data
    for part in json_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"JSON 中找不到字段：{json_key}")
        current = current[part]

    if not isinstance(current, str):
        raise TypeError(f"JSON 字段 {json_key} 的值不是字符串")

    return current.strip()


def parse_data_uri(text: str) -> ParsedBase64Input | None:
    """
    尝试解析 Data URI。

    例如：
    data:audio/mpeg;base64,xxxx
    """
    pattern = re.compile(
        r"^data:(?P<mime>[^;,]+)(?P<params>(?:;[^,]+)*);base64,(?P<data>.*)$",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.match(text.strip())
    if not match:
        return None

    mime_type = match.group("mime").lower()
    base64_text = match.group("data").strip()

    return ParsedBase64Input(
        base64_text=base64_text,
        mime_type=mime_type,
        source_kind="data-uri",
    )


def normalize_base64_text(text: str) -> str:
    """
    规范化 Base64 文本。

    - 去掉首尾空白
    - 去掉所有空白字符：换行、空格、Tab
    - 保留 Base64 URL-safe 字符：- 和 _
    """
    return "".join(text.strip().split())


def add_base64_padding(base64_text: str) -> str:
    """
    自动补齐 Base64 padding。

    标准 Base64 长度应该是 4 的倍数。
    有些系统会省略末尾的 =，这里做容错。
    """
    remainder = len(base64_text) % 4
    if remainder == 0:
        return base64_text

    return base64_text + ("=" * (4 - remainder))


def decode_base64_to_bytes(base64_text: str, *, urlsafe: bool) -> bytes:
    """
    解码 Base64 为 bytes。
    """
    normalized = normalize_base64_text(base64_text)
    padded = add_base64_padding(normalized)

    try:
        if urlsafe:
            return base64.urlsafe_b64decode(padded.encode("utf-8"))

        # validate=True 会严格校验非法字符，但不支持 urlsafe 的 - 和 _
        return base64.b64decode(padded.encode("utf-8"), validate=True)
    except binascii.Error as e:
        raise ValueError(f"Base64 解码失败：{e}") from e


def parse_input_text(raw_text: str, *, json_key: str | None) -> ParsedBase64Input:
    """
    解析输入文本，识别 JSON / Data URI / 纯 Base64。
    """
    text = raw_text.strip()

    if json_key:
        text = extract_json_value(text, json_key)

    data_uri = parse_data_uri(text)
    if data_uri:
        return data_uri

    return ParsedBase64Input(
        base64_text=text,
        mime_type=None,
        source_kind="plain",
    )


def infer_output_path(output_arg: str | None, *, input_path: Path, mime_type: str | None) -> Path:
    """
    推断输出路径。

    规则：
    - 用户显式传了 -o / --output：优先使用
    - 如果输出路径没有扩展名，且 Data URI 中有 MIME Type，则自动补扩展名
    - 如果用户没传输出路径，则基于输入文件名生成
    """
    if output_arg:
        output_path = Path(output_arg).expanduser().resolve()
    else:
        output_path = input_path.with_suffix("")

    if not output_path.suffix and mime_type:
        output_path = output_path.with_suffix(MIME_TO_EXTENSION.get(mime_type, ".bin"))

    if not output_path.suffix:
        output_path = output_path.with_suffix(".bin")

    return output_path


def ensure_can_write(output_path: Path, *, force: bool) -> None:
    """
    检查是否可以写入输出文件。
    """
    if output_path.exists() and not force:
        raise FileExistsError(
            f"输出文件已存在：{output_path}\n"
            "如需覆盖，请添加 --force。"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)


def write_binary_file(output_path: Path, data: bytes, *, force: bool) -> None:
    """
    写入二进制文件。
    """
    ensure_can_write(output_path, force=force)
    output_path.write_bytes(data)


def human_size(size_bytes: int) -> str:
    """
    把字节数格式化成人类可读形式。
    """
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size_bytes} B"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="base64_to_audio",
        description="把 Base64 文本还原为音频文件。",
    )

    parser.add_argument(
        "input",
        help="输入 Base64 文本文件路径，例如 ./outputs/demo.base64.txt",
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "输出音频文件路径。"
            "如果输入是 Data URI 且输出路径无扩展名，会根据 MIME Type 自动补扩展名。"
        ),
    )

    parser.add_argument(
        "--json-key",
        help=(
            "从 JSON 文件中的指定字段读取 Base64。"
            "支持点路径，例如 data.audio_base64。"
        ),
    )

    parser.add_argument(
        "--urlsafe",
        action="store_true",
        help="按 URL-safe Base64 解码，兼容 '-' 和 '_'。",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="如果输出文件已存在，允许覆盖。",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="只校验 Base64 是否可解码，不写入音频文件。",
    )

    parser.add_argument(
        "--show-info",
        action="store_true",
        help="在 stderr 输出输入类型、MIME Type、解码后大小等信息。",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()

    try:
        raw_text = read_text_file(input_path)

        parsed = parse_input_text(
            raw_text,
            json_key=args.json_key,
        )

        audio_bytes = decode_base64_to_bytes(
            parsed.base64_text,
            urlsafe=args.urlsafe,
        )

        output_path = infer_output_path(
            args.output,
            input_path=input_path,
            mime_type=parsed.mime_type,
        )

        if args.show_info or args.validate_only:
            print(f"[info] input: {input_path}", file=sys.stderr)
            print(f"[info] source kind: {parsed.source_kind}", file=sys.stderr)
            print(f"[info] mime type: {parsed.mime_type or 'unknown'}", file=sys.stderr)
            print(f"[info] decoded size: {human_size(len(audio_bytes))}", file=sys.stderr)

        if args.validate_only:
            print("[ok] Base64 校验通过，未写入文件。", file=sys.stderr)
            return 0

        write_binary_file(
            output_path,
            audio_bytes,
            force=args.force,
        )

        print(f"音频文件已还原到：{output_path}", file=sys.stderr)
        return 0

    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
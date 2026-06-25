#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
audio_to_base64.py

把 mp3 / wav / flac / m4a / aac / ogg 等主流音频文件编码为 Base64 文本。

示例：

1. 打印到终端：
   python audio_to_base64.py ./samples/demo.mp3

2. 保存到文本文件：
   python audio_to_base64.py ./samples/demo.mp3 -o ./outputs/demo.base64.txt

3. 输出 Data URI：
   python audio_to_base64.py ./samples/demo.mp3 --data-uri

4. 保存 Data URI：
   python audio_to_base64.py ./samples/demo.mp3 -o ./outputs/demo.data-uri.txt --data-uri

5. 不自动换行，输出单行 Base64：
   python audio_to_base64.py ./samples/demo.mp3 --no-wrap
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import sys
from pathlib import Path
from textwrap import wrap


SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".webm",
    ".aiff",
    ".aif",
}


def guess_audio_mime_type(file_path: Path) -> str:
    """
    根据文件扩展名推断 MIME Type。

    mimetypes 对部分音频格式的识别不稳定，因此这里做一些兜底处理。
    """
    ext = file_path.suffix.lower()

    fallback = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".opus": "audio/opus",
        ".webm": "audio/webm",
        ".aiff": "audio/aiff",
        ".aif": "audio/aiff",
    }

    guessed, _ = mimetypes.guess_type(str(file_path))
    return guessed or fallback.get(ext, "application/octet-stream")


def encode_audio_to_base64(file_path: Path) -> str:
    """
    读取音频文件，并返回 Base64 字符串。
    """
    with file_path.open("rb") as f:
        binary_data = f.read()

    return base64.b64encode(binary_data).decode("utf-8")


def format_base64_output(
    base64_text: str,
    *,
    file_path: Path,
    as_data_uri: bool,
    wrap_width: int | None,
) -> str:
    """
    格式化 Base64 输出。

    - as_data_uri=True 时，输出 data:<mime>;base64,<content>
    - wrap_width 不为空时，按指定宽度换行
    """
    if wrap_width and wrap_width > 0:
        base64_text = "\n".join(wrap(base64_text, wrap_width))

    if as_data_uri:
        mime_type = guess_audio_mime_type(file_path)
        return f"data:{mime_type};base64,{base64_text}"

    return base64_text


def validate_input_file(file_path: Path, *, strict_extension: bool) -> None:
    """
    校验输入文件。
    """
    if not file_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{file_path}")

    if not file_path.is_file():
        raise ValueError(f"输入路径不是文件：{file_path}")

    if strict_extension and file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"不支持的音频扩展名：{file_path.suffix}\n"
            f"当前允许：{supported}\n"
            "如果你确定这是音频文件，可以添加 --no-strict-extension 跳过扩展名检查。"
        )


def write_text_output(output_path: Path, text: str) -> None:
    """
    把 Base64 文本写入文件。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audio_to_base64",
        description="把 mp3 / wav / flac 等音频文件编码为 Base64 文本。",
    )

    parser.add_argument(
        "input",
        help="输入音频文件路径，例如 ./samples/demo.mp3",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="输出文本文件路径。如果不指定，则打印到终端。",
    )

    parser.add_argument(
        "--data-uri",
        action="store_true",
        help="输出 Data URI 格式，例如 data:audio/mpeg;base64,...",
    )

    parser.add_argument(
        "--wrap",
        type=int,
        default=76,
        help="每行 Base64 字符数，默认 76。设置为 0 表示不换行。",
    )

    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="输出单行 Base64，等价于 --wrap 0。",
    )

    parser.add_argument(
        "--no-strict-extension",
        action="store_true",
        help="跳过音频文件扩展名白名单校验。",
    )

    parser.add_argument(
        "--show-info",
        action="store_true",
        help="在 stderr 输出文件大小、MIME Type 等信息。",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else None

    try:
        validate_input_file(
            input_path,
            strict_extension=not args.no_strict_extension,
        )

        wrap_width = 0 if args.no_wrap else args.wrap
        base64_text = encode_audio_to_base64(input_path)

        result = format_base64_output(
            base64_text,
            file_path=input_path,
            as_data_uri=args.data_uri,
            wrap_width=wrap_width,
        )

        if args.show_info:
            size_bytes = input_path.stat().st_size
            mime_type = guess_audio_mime_type(input_path)
            print(f"[info] file: {input_path}", file=sys.stderr)
            print(f"[info] size: {size_bytes} bytes", file=sys.stderr)
            print(f"[info] mime: {mime_type}", file=sys.stderr)
            print(f"[info] base64 chars: {len(base64_text)}", file=sys.stderr)

        if output_path:
            write_text_output(output_path, result)
            print(f"Base64 已保存到：{output_path}", file=sys.stderr)
        else:
            print(result)

        return 0

    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
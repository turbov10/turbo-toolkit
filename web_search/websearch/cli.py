from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .engines import ENGINES, build_engine
from .engines.base import SearchEngineError

DEFAULT_TYPE = "google"
DEFAULT_LIMIT = 10


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-search",
        description="Online web search CLI with pluggable engines.",
    )
    parser.add_argument(
        "type",
        nargs="?",
        default=DEFAULT_TYPE,
        choices=sorted(ENGINES),
        help=f"search engine to use (default: {DEFAULT_TYPE})",
    )
    parser.add_argument("query", help="search query string")
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"max results to return (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="path to env file (default: ./.env, disabled if not found)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.env_file.is_file():
        load_dotenv(args.env_file)

    engine = build_engine(args.type)

    started = time.perf_counter()
    try:
        results = engine.search(args.query, limit=args.limit)
    except SearchEngineError as exc:
        payload = {"error": str(exc), "type": args.type, "query": args.query}
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 2
    duration_ms = int((time.perf_counter() - started) * 1000)

    output = {
        "duration": duration_ms,
        "results": [r.to_dict() for r in results],
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line entrypoint: serve | list | call | info | version."""
from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path

import agent_gateway
from agent_gateway.config import GatewayConfig, load_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-gateway",
        description="Single MCP server aggregating every tool in turbo-toolkit.",
    )
    p.add_argument(
        "--root", type=Path, default=None,
        help="monorepo root (default: parent of agent-gateway/)",
    )
    p.add_argument(
        "--config", type=Path, default=None,
        help="path to gateway.yaml (optional)",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="enable DEBUG logging",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="start the stdio MCP server")
    sub.add_parser("list", help="list all discovered tools")
    sub.add_parser("version", help="print gateway version")

    call_p = sub.add_parser("call", help="invoke a single tool by full name")
    call_p.add_argument("full_name")
    call_p.add_argument("--args", default="{}")

    info_p = sub.add_parser("info", help="show one tool's schema")
    info_p.add_argument("full_name")

    return p


def resolve_config(args: argparse.Namespace) -> GatewayConfig:
    """Load config (gateway.yaml if --config) and apply --root override."""
    cfg = load_config(args.config)
    if args.root is not None:
        cfg = GatewayConfig(
            root=args.root.resolve(),
            exclude=cfg.exclude,
            timeout_seconds=cfg.timeout_seconds,
            tools=cfg.tools,
        )
    return cfg


def cmd_version(_: argparse.Namespace) -> int:
    print(f"agent-gateway {agent_gateway.__version__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return _DISPATCH[args.cmd](args)


_DISPATCH = {
    "version": cmd_version,
    # serve / list / call / info filled in by Tasks 8-10
}


if __name__ == "__main__":
    sys.exit(main())

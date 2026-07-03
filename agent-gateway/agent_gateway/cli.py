"""Command-line entrypoint: serve | list | call | info | version."""
from __future__ import annotations
import argparse
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any

import agent_gateway
from agent_gateway.config import GatewayConfig, load_config
from agent_gateway.mcp_server import build_server


def _common_parent(add_help: bool = False) -> argparse.ArgumentParser:
    """ArgumentParser fragment with the flags accepted before OR after the subcommand."""
    p = argparse.ArgumentParser(add_help=add_help)
    p.add_argument("--root", type=Path, default=None,
                   help="monorepo root (default: parent of agent-gateway/)")
    p.add_argument("--config", type=Path, default=None,
                   help="path to gateway.yaml (optional)")
    p.add_argument("--verbose", "-v", action="store_true", help="DEBUG logging")
    p.add_argument("--json", action="store_true",
                   help="(list/info) emit JSON instead of human-readable text")
    return p


def build_parser() -> argparse.ArgumentParser:
    common = _common_parent(add_help=False)
    p = argparse.ArgumentParser(
        prog="agent-gateway",
        description="Single MCP server aggregating every tool in turbo-toolkit.",
        parents=[common],
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="start the stdio MCP server", parents=[common])
    sub.add_parser("list", help="list all discovered tools", parents=[common])
    sub.add_parser("version", help="print gateway version", parents=[common])

    call_p = sub.add_parser("call", help="invoke a single tool by full name",
                            parents=[common])
    call_p.add_argument("full_name")
    call_p.add_argument("--args", default="{}")

    info_p = sub.add_parser("info", help="show one tool's schema", parents=[common])
    info_p.add_argument("full_name")

    return p


def resolve_config(args: argparse.Namespace) -> GatewayConfig:
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


def _build_handle(args: argparse.Namespace):
    cfg = resolve_config(args)
    return build_server(cfg)


def cmd_list(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    if not handle.captures:
        if args.json:
            print("[]")
        else:
            print("(no tools discovered)")
        return 0
    if args.json:
        out = [
            {
                "full_name": c.full_name,
                "bare_name": c.bare_name,
                "description": c.description,
            }
            for c in handle.captures
        ]
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    for c in handle.captures:
        print(c.full_name)
        if c.description:
            print(f"  {c.description}")
        sig = inspect.signature(c.source_func)
        print(f"  signature: {sig}")
        print()
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    rec = next((c for c in handle.captures if c.full_name == args.full_name), None)
    if rec is None:
        print(f"tool not found: {args.full_name}", file=sys.stderr)
        return 2
    sig = inspect.signature(rec.source_func)
    payload = {
        "full_name": rec.full_name,
        "bare_name": rec.bare_name,
        "description": rec.description,
        "signature": str(sig),
        "parameters": rec.source_func.__annotations__,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(rec.full_name)
        if rec.description:
            print(f"  {rec.description}")
        print(f"  signature: {sig}")
        print(f"  parameters: {rec.source_func.__annotations__}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    handle = _build_handle(args)
    log.info("serving %d tools on stdio", len(handle.captures))
    handle.fastmcp.run(transport="stdio")
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
    "list": cmd_list,
    "info": cmd_info,
    "serve": cmd_serve,
    # "call" added in Task 9
}


if __name__ == "__main__":
    sys.exit(main())

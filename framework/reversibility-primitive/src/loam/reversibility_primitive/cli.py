"""`pos reversibility` / `pos rollback` CLI commands.

The CLI is thin — it wraps IPC calls so workspaces and tests can drive
the primitive without a bespoke client. Per proposal §6.

Commands:
    pos reversibility bind <scope_id> --handle <name> [--description …]
    pos reversibility handlers
    pos rollback scope <scope_id> [--reason …] [--idempotency-key …]
    pos rollback status <scope_id>

The main() entrypoint takes an IPCClient-like object injected at test
time; production wiring is a thin wrapper in the workspace bootstrap.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Awaitable, Callable


CliCall = Callable[[str, dict[str, Any]], Awaitable[Any]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos", description="pOS reversibility + rollback CLI"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    rev = sub.add_parser("reversibility", help="reversibility commands")
    rev_sub = rev.add_subparsers(dest="rev_cmd", required=True)

    bind = rev_sub.add_parser("bind", help="register a compensation binding")
    bind.add_argument("scope_id")
    bind.add_argument("--handle", required=True)
    bind.add_argument("--description", default="")
    bind.add_argument("--budget-seconds", type=int, default=None)
    bind.add_argument("--idempotency-key", default=None)

    rev_sub.add_parser("handlers", help="list handlers and bindings")

    rb = sub.add_parser("rollback", help="rollback commands")
    rb_sub = rb.add_subparsers(dest="rb_cmd", required=True)

    scope = rb_sub.add_parser("scope", help="rollback a scope")
    scope.add_argument("scope_id")
    scope.add_argument("--reason", default="cli:rollback")
    scope.add_argument("--idempotency-key", default=None)

    status = rb_sub.add_parser("status", help="show rollback invocations for a scope")
    status.add_argument("scope_id")

    return parser


async def dispatch(call: CliCall, args: argparse.Namespace) -> Any:
    if args.cmd == "reversibility":
        if args.rev_cmd == "bind":
            params: dict[str, Any] = {
                "scope_id": args.scope_id,
                "handle": args.handle,
                "description": args.description,
            }
            if args.budget_seconds is not None:
                params["budget_seconds"] = args.budget_seconds
            if args.idempotency_key is not None:
                params["idempotency_key"] = args.idempotency_key
            return await call("reversibility.register_compensation", params)
        if args.rev_cmd == "handlers":
            return await call("reversibility.list_handlers", {})
    if args.cmd == "rollback":
        if args.rb_cmd == "scope":
            params = {"scope_id": args.scope_id, "reason": args.reason}
            if args.idempotency_key is not None:
                params["idempotency_key"] = args.idempotency_key
            return await call("reversibility.rollback_scope", params)
        if args.rb_cmd == "status":
            return await call(
                "reversibility.rollback_status", {"scope_id": args.scope_id}
            )
    raise ValueError(f"unknown command: {args!r}")


def main(call: CliCall, argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = asyncio.run(dispatch(call, args))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": str(e), "type": type(e).__name__}))
        return 1
    print(json.dumps(result, default=str, indent=2))
    return 0

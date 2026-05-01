# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


# ---------------------------------------------------------------------------
# Console-script entry-point shims (M3 — AC.OSS-M3.4 + plan §10 D-build.M3.1).
#
# Two zero-arg public functions registered as `[project.scripts]`:
#
#     loam-reversibility = "loam.reversibility_primitive.cli:main_reversibility"
#     loam-rollback      = "loam.reversibility_primitive.cli:main_rollback"
#
# Each shim builds an `IPCClient` from `--socket` / `POS_SOCKET_PATH`
# (mirrors `loam.safety_layer.cli` pattern verbatim — env-var name
# `POS_SOCKET_PATH` preserved per plan §10 D-build.M3.2; M1b did not
# rename it), wraps `client.call` as a `CliCall`, parses argv against
# its own subtree-scoped parser, then invokes the existing
# `dispatch(call, args)` function. The existing `main(call, argv)`
# function above is preserved untouched per dispatch constraint
# "no change to the `main()` function itself".
# ---------------------------------------------------------------------------


def _build_reversibility_parser() -> argparse.ArgumentParser:
    """Subtree-scoped parser for `loam-reversibility {bind, handlers}`."""
    parser = argparse.ArgumentParser(
        prog="loam-reversibility",
        description="loam reversibility CLI — compensation-path bindings",
    )
    parser.add_argument(
        "--socket",
        default=None,
        help="Path to the orchestrator Unix socket (defaults to env POS_SOCKET_PATH).",
    )
    rev_sub = parser.add_subparsers(dest="rev_cmd", required=True)

    bind = rev_sub.add_parser("bind", help="register a compensation binding")
    bind.add_argument("scope_id")
    bind.add_argument("--handle", required=True)
    bind.add_argument("--description", default="")
    bind.add_argument("--budget-seconds", type=int, default=None)
    bind.add_argument("--idempotency-key", default=None)

    rev_sub.add_parser("handlers", help="list handlers and bindings")

    return parser


def _build_rollback_parser() -> argparse.ArgumentParser:
    """Subtree-scoped parser for `loam-rollback {scope, status}`."""
    parser = argparse.ArgumentParser(
        prog="loam-rollback",
        description="loam rollback CLI — scope rollback + status",
    )
    parser.add_argument(
        "--socket",
        default=None,
        help="Path to the orchestrator Unix socket (defaults to env POS_SOCKET_PATH).",
    )
    rb_sub = parser.add_subparsers(dest="rb_cmd", required=True)

    scope = rb_sub.add_parser("scope", help="rollback a scope")
    scope.add_argument("scope_id")
    scope.add_argument("--reason", default="cli:rollback")
    scope.add_argument("--idempotency-key", default=None)

    status = rb_sub.add_parser("status", help="show rollback invocations for a scope")
    status.add_argument("scope_id")

    return parser


def _resolve_socket_path(args: argparse.Namespace) -> Any:
    """Mirror `loam.safety_layer.cli._main_async` socket resolution.

    Precedence: --socket arg > POS_SOCKET_PATH env > error. Returns a
    pathlib.Path. The env-var name `POS_SOCKET_PATH` is preserved per
    plan §10 D-build.M3.2 (consistency with safety CLI; M1b did not
    rename it).
    """
    import os
    import sys
    from pathlib import Path

    if args.socket is not None:
        return Path(args.socket)
    env_path = os.environ.get("POS_SOCKET_PATH")
    if not env_path:
        print(
            "error: no --socket and POS_SOCKET_PATH not set", file=sys.stderr
        )
        return None
    return Path(env_path)


async def _shim_main_async(args: argparse.Namespace) -> int:
    """IPCClient-build + dispatch — shared body for both shims."""
    from loam.orchestrator.ipc import IPCClient

    socket_path = _resolve_socket_path(args)
    if socket_path is None:
        return 2

    client = IPCClient(socket_path)
    await client.connect()
    try:

        async def _call(method: str, params: dict[str, Any]) -> Any:
            return await client.call(method, params)

        try:
            result = await dispatch(_call, args)
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"error": str(e), "type": type(e).__name__}))
            return 1
        print(json.dumps(result, default=str, indent=2))
        return 0
    finally:
        await client.close()


def main_reversibility(argv: list[str] | None = None) -> int:
    """`loam-reversibility` console-script entry (M3 — AC.OSS-M3.4).

    Builds IPCClient from --socket / POS_SOCKET_PATH, dispatches via
    the existing `dispatch(call, args)` function with `args.cmd` set
    to the constant `"reversibility"`. Existing `main(call, argv)`
    preserved untouched per dispatch constraint.
    """
    parser = _build_reversibility_parser()
    args = parser.parse_args(argv)
    args.cmd = "reversibility"
    return asyncio.run(_shim_main_async(args))


def main_rollback(argv: list[str] | None = None) -> int:
    """`loam-rollback` console-script entry (M3 — AC.OSS-M3.4).

    Builds IPCClient from --socket / POS_SOCKET_PATH, dispatches via
    the existing `dispatch(call, args)` function with `args.cmd` set
    to the constant `"rollback"`. Existing `main(call, argv)` preserved
    untouched per dispatch constraint.
    """
    parser = _build_rollback_parser()
    args = parser.parse_args(argv)
    args.cmd = "rollback"
    return asyncio.run(_shim_main_async(args))

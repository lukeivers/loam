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

"""`pos kill ...` + `pos safety ...` CLI.

The CLI is thin — it connects to the running orchestrator's Unix socket
and calls the safety IPC methods. Commands:

    pos kill scope <id> [--reason TEXT]
    pos kill session [--reason TEXT]
    pos kill system --yes-really [--reason TEXT]
    pos safety status
    pos safety resume-session
    pos safety clear-system-kill [--reason TEXT]

The CLI does not import any sealed-component internals — it only
uses the IPCClient from pos_orchestrator.ipc. The primary surface in
tests is the IPC layer directly; this CLI is a convenience wrapper.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from loam.orchestrator.ipc import IPCClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pos", description="pOS v2 safety CLI")
    parser.add_argument(
        "--socket", type=Path, default=None,
        help="Path to the orchestrator Unix socket (defaults to env POS_SOCKET_PATH).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # `pos kill ...`
    kill = sub.add_parser("kill", help="Issue a kill switch")
    kill_sub = kill.add_subparsers(dest="level", required=True)

    k_scope = kill_sub.add_parser("scope", help="Kill one scope")
    k_scope.add_argument("scope_id")
    k_scope.add_argument("--reason", default="cli:kill_scope")

    k_session = kill_sub.add_parser("session", help="Kill the running session")
    k_session.add_argument("--reason", default="cli:kill_session")

    k_system = kill_sub.add_parser("system", help="Kill the whole orchestrator")
    k_system.add_argument(
        "--yes-really", action="store_true",
        help="Required to commit; refuses without it.",
    )
    k_system.add_argument("--reason", default="cli:kill_system")

    # `pos safety ...`
    safety = sub.add_parser("safety", help="Safety layer introspection")
    safety_sub = safety.add_subparsers(dest="op", required=True)
    safety_sub.add_parser("status")
    rs = safety_sub.add_parser("resume-session", help="Resume after session-kill")
    rs.add_argument("--reason", default="cli:resume")
    cs = safety_sub.add_parser(
        "clear-system-kill", help="Allow the next orchestrator start to activate again"
    )
    cs.add_argument("--reason", default="cli:clear_system_kill")

    return parser


async def _main_async(args: argparse.Namespace) -> int:
    socket_path = args.socket
    if socket_path is None:
        import os
        env_path = os.environ.get("POS_SOCKET_PATH")
        if not env_path:
            print("error: no --socket and POS_SOCKET_PATH not set", file=sys.stderr)
            return 2
        socket_path = Path(env_path)

    client = IPCClient(socket_path)
    await client.connect()
    try:
        if args.cmd == "kill":
            if args.level == "scope":
                result = await client.call(
                    "safety.kill_scope",
                    {"scope_id": args.scope_id, "reason": args.reason},
                )
            elif args.level == "session":
                result = await client.call(
                    "safety.kill_session", {"reason": args.reason}
                )
            elif args.level == "system":
                if not args.yes_really:
                    print(
                        "refusing: `pos kill system` requires --yes-really "
                        "(two-step commit).",
                        file=sys.stderr,
                    )
                    return 2
                nonce_resp = await client.call("safety.kill_system_request", {})
                result = await client.call(
                    "safety.kill_system",
                    {
                        "nonce": nonce_resp["nonce"],
                        "reason": args.reason,
                    },
                )
            else:
                raise SystemExit(f"unknown kill level: {args.level}")
        elif args.cmd == "safety":
            if args.op == "status":
                result = await client.call("safety.status", {})
            elif args.op == "resume-session":
                result = await client.call("resume", {})
            elif args.op == "clear-system-kill":
                result = await client.call(
                    "safety.clear_system_kill", {"reason": args.reason}
                )
            else:
                raise SystemExit(f"unknown safety op: {args.op}")
        else:
            raise SystemExit(f"unknown command: {args.cmd}")

        print(json.dumps(result, indent=2, default=str))
        return 0
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

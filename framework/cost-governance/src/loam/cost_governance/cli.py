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

"""`pos cost` subcommand family — CLI face on top of the store.

A thin read-mostly CLI. No IPC here — the CLI opens the store
directly. Adjustments go via IPC from the CLI side for audit
(not implemented yet; v1.0 CLI ships status-only, which is sufficient
for the brief).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .store import CostStore


def _default_db_path() -> Path:
    return Path.home() / ".loam" / "cost" / "cost.sqlite"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pos cost")
    parser.add_argument(
        "--db", type=Path, default=_default_db_path(),
        help="Path to the cost SQLite store (default: ~/.loam/cost/cost.sqlite)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_status = sub.add_parser("status", help="High-level status")
    sp_status.add_argument("--session", type=str, default=None)

    sp_scope = sub.add_parser("scope", help="Reservation for one scope")
    sp_scope.add_argument("scope_id", type=str)

    sp_session = sub.add_parser("session", help="Session rollup")
    sp_session.add_argument("--session", type=str, default=None)

    sp_rolling = sub.add_parser("rolling", help="Rolling-window rollups")
    sp_rolling.add_argument("--window", type=str, default=None)

    sp_adjust = sub.add_parser("adjust", help="Show ceiling adjustments audit")

    args = parser.parse_args(argv)

    store = CostStore(args.db)
    try:
        if args.cmd == "status":
            config = load_config()
            session_id = args.session or "(default-session)"
            rollup = store.get_session_rollup(session_id)
            active = store.list_active_reservations(session_id=session_id)
            out = {
                "session_id": session_id,
                "session_rollup": rollup.model_dump() if rollup else None,
                "active_reservations": [r.model_dump() for r in active],
                "config": config.model_dump(),
            }
            print(json.dumps(out, indent=2))
            return 0

        if args.cmd == "scope":
            r = store.get_reservation(args.scope_id)
            print(
                json.dumps(
                    {"scope_id": args.scope_id, "reservation": r.model_dump() if r else None},
                    indent=2,
                )
            )
            return 0

        if args.cmd == "session":
            session_id = args.session or "(default-session)"
            rollup = store.get_session_rollup(session_id)
            print(
                json.dumps(
                    {"session_id": session_id, "rollup": rollup.model_dump() if rollup else None},
                    indent=2,
                )
            )
            return 0

        if args.cmd == "rolling":
            rows = store.list_rolling_rollups(window_kind=args.window)
            print(
                json.dumps(
                    {"window_kind": args.window, "rollups": [r.model_dump() for r in rows]},
                    indent=2,
                )
            )
            return 0

        if args.cmd == "adjust":
            rows = store.list_ceiling_adjustments()
            print(
                json.dumps(
                    {"adjustments": [a.model_dump() for a in rows]},
                    indent=2,
                )
            )
            return 0
    finally:
        store.close()

    return 2


if __name__ == "__main__":
    sys.exit(main())

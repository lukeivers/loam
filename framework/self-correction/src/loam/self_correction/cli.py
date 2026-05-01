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

"""`pos correction` CLI subcommands.

Deterministic read/write operations over the CorrectionStore and the
IPC surfaces. The CLI is thin: it does not talk to the scope runtime
directly; for live trigger submission it speaks IPC.

Subcommands:

  pos correction status
  pos correction episode <episode_id>
  pos correction history --class <name>
  pos correction trigger --source user --description "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import default_config, load_config
from .store import CorrectionStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pos correction")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to correction config YAML (default: built-in defaults).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Summary of open correction episodes.")

    p_ep = sub.add_parser("episode", help="Show a single episode and its records.")
    p_ep.add_argument("episode_id")

    p_hist = sub.add_parser("history", help="List episodes filtered by class.")
    p_hist.add_argument("--class", dest="failure_class", default=None)

    p_tr = sub.add_parser(
        "trigger", help="Submit a trigger (user-report source)."
    )
    p_tr.add_argument("--source", default="user")
    p_tr.add_argument("--description", required=True)

    args = parser.parse_args(argv)
    cfg = load_config(args.config) if args.config else default_config()
    store = CorrectionStore(Path(cfg.store_path).expanduser())

    try:
        if args.cmd == "status":
            return _cmd_status(store)
        if args.cmd == "episode":
            return _cmd_episode(store, args.episode_id)
        if args.cmd == "history":
            return _cmd_history(store, args.failure_class)
        if args.cmd == "trigger":
            # The CLI cannot open scopes directly — it exits with a
            # hint pointing at the IPC method. This keeps the CLI
            # from bypassing bounds / dedup / gates.
            print(
                "To submit a user-reported correction trigger, "
                "invoke the IPC method `correction.user_reported` "
                "from the primary-persona session. The CLI is "
                "read-only for triggers; writing triggers directly "
                "here would bypass caller-identity enforcement "
                "(ruling #4).",
                file=sys.stderr,
            )
            return 2
    finally:
        store.close()
    return 0


def _cmd_status(store: CorrectionStore) -> int:
    rows = store.list_all_episodes()
    open_eps = [r for r in rows if r.state.value == "running"]
    print(
        json.dumps(
            {
                "total_episodes": len(rows),
                "running": len(open_eps),
                "running_ids": [e.episode_id for e in open_eps[:20]],
            },
            indent=2,
        )
    )
    return 0


def _cmd_episode(store: CorrectionStore, episode_id: str) -> int:
    ep = store.get_episode(episode_id)
    if ep is None:
        print(f"no episode: {episode_id}", file=sys.stderr)
        return 1
    records = store.list_records(episode_id)
    present = sorted(r["record_type"] for r in records)
    print(
        json.dumps(
            {
                "episode": ep.model_dump(mode="json"),
                "records_present": present,
                "records": records,
            },
            indent=2,
        )
    )
    return 0


def _cmd_history(store: CorrectionStore, failure_class: str | None) -> int:
    rows = store.list_all_episodes()
    if failure_class:
        rows = [r for r in rows if r.failure_class == failure_class]
    print(
        json.dumps(
            [r.model_dump(mode="json") for r in rows[-50:]],
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

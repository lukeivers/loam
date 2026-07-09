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

"""CLI production entry: ``python -m loam.fleet_collector``.

Globs the given root(s) for agent run dirs and emits the fleet-state
JSON to ``--out`` (or stdout).  This is the command WS-A3's cron/launchd
regenerator invokes; the emitted file is what the static page renders.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .collector import collect_fleet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam.fleet_collector",
        description="Emit one fleet-state JSON over on-disk agent run "
                    "records (handsoff-loop + subloam-driver).")
    parser.add_argument(
        "--root", action="append", dest="roots", metavar="DIR",
        help="A directory to scan for run dirs (a workspace, its runs/ "
             "dir, or a single run dir). Repeatable. Defaults to the "
             "current directory.")
    parser.add_argument(
        "--out", metavar="FILE",
        help="Write the fleet JSON here (default: stdout).")
    parser.add_argument(
        "--stale-after-s", type=float, default=300.0,
        help="Liveness staleness bound passed to the artifact probe "
             "(default: 300).")
    args = parser.parse_args(argv)

    roots = [Path(r) for r in (args.roots or ["."])]
    fleet = collect_fleet(roots, stale_after_s=args.stale_after_s)
    payload = json.dumps(fleet, indent=2)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

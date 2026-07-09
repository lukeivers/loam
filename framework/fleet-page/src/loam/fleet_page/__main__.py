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

"""CLI production entry: ``python -m loam.fleet_page``.

Two subcommands:

* ``render`` (default) — read every source over the given ``--root``(s)
  and write the page to ``--out``.  This is the command the launchd/cron
  job invokes; it re-reads all sources and overwrites the page.
* ``install-launchd`` — write the launchd plist that runs ``render`` on
  a ``--interval``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generate import generate_page
from .schedule import install_launchd_job
from .sources import discover_pm_dirs, read_cost_rows, read_decisions, read_fleet


def _cmd_render(args: argparse.Namespace) -> int:
    roots = [Path(r) for r in (args.roots or ["."])]
    pm_root = Path(args.pm_root) if args.pm_root else roots[0]

    def fleet_source() -> dict:
        return read_fleet(roots, stale_after_s=args.stale_after_s)

    def cost_source() -> list[dict]:
        return read_cost_rows(window_days=args.window_days)

    def decisions_source() -> list[dict]:
        pm_dirs = discover_pm_dirs(pm_root)
        return read_decisions(pm_dirs)

    out = generate_page(
        args.out,
        fleet_source=fleet_source,
        cost_source=cost_source,
        decisions_source=decisions_source,
    )
    sys.stdout.write(f"wrote {out}\n")
    return 0


def _cmd_install_launchd(args: argparse.Namespace) -> int:
    roots = [Path(r) for r in (args.roots or ["."])]
    plist = install_launchd_job(
        out_path=args.out,
        roots=roots,
        interval_s=args.interval,
    )
    sys.stdout.write(
        f"wrote launchd plist {plist}\n"
        f"load it with: launchctl load {plist}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam.fleet_page",
        description="Regenerate the static agent-fleet page, or install "
                    "the launchd job that regenerates it.")
    sub = parser.add_subparsers(dest="command")

    render = sub.add_parser("render", help="Read sources and write the page.")
    render.add_argument("--out", required=True, metavar="FILE",
                        help="Write the HTML page here (overwritten each run).")
    render.add_argument("--root", action="append", dest="roots", metavar="DIR",
                        help="A tree to scan for agent run dirs. Repeatable. "
                             "Defaults to the current directory.")
    render.add_argument("--pm-root", metavar="DIR",
                        help="Root to scan for per-project-pm state dirs "
                             "(default: the first --root).")
    render.add_argument("--stale-after-s", type=float, default=300.0,
                        help="Liveness staleness bound for the fleet read.")
    render.add_argument("--window-days", type=int, default=7,
                        help="Cost-strip lookback window (default: 7).")
    render.set_defaults(func=_cmd_render)

    install = sub.add_parser("install-launchd",
                             help="Write the launchd regenerator plist.")
    install.add_argument("--out", required=True, metavar="FILE",
                         help="Page path the scheduled job writes.")
    install.add_argument("--root", action="append", dest="roots", metavar="DIR",
                         help="A tree to scan. Repeatable.")
    install.add_argument("--interval", type=int, default=300, metavar="SECONDS",
                         help="Regeneration interval (default: 300).")
    install.set_defaults(func=_cmd_install_launchd)

    raw = list(argv) if argv is not None else sys.argv[1:]
    # `render` is the default subcommand: if the first token is not a
    # known subcommand (and not just `-h`), prepend `render` so
    # `... --out X --root Y` works without naming the subcommand.
    known = {"render", "install-launchd"}
    if raw and raw[0] not in known and raw[0] not in ("-h", "--help"):
        raw = ["render", *raw]
    args = parser.parse_args(raw)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

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

"""CLI production entry: ``python -m loam.weekly_cost_rollup``.

This is the command the weekly launchd job invokes. It reads the REAL sealed
usage probe, the REAL transcript token parser, and the gateway source, assembles
the three-section roll-up, and delivers via the chosen channel seam:

* default → stdout (captured in the launchd job's ``StandardOutPath``);
* ``--notify-cmd "<shell command>"`` → shell that command with the message on
  stdin (the launchd → workspace-poster bridge, reused from WS-A1 D-A1-3).
"""

from __future__ import annotations

import argparse
import shlex

from loam.weekly_cap_alert.notify import command_notify, stdout_notify

from .rollup import run_rollup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam.weekly_cost_rollup",
        description="Emit the weekly cost roll-up: this machine's Claude weekly "
                    "cap %, top-3 projects by Claude tokens (a proxy, not "
                    "dollars), and metered-model spend month-to-date.")
    parser.add_argument(
        "--notify-cmd", metavar="CMD",
        help="Shell command to deliver the roll-up (message piped on stdin). "
             "Default: write the message to stdout.")
    args = parser.parse_args(argv)

    notify_fn = (
        command_notify(shlex.split(args.notify_cmd))
        if args.notify_cmd
        else stdout_notify
    )
    run_rollup(notify_fn=notify_fn)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

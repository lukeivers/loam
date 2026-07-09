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

"""CLI production entry: ``python -m loam.weekly_cap_alert``.

This is the command the launchd job invokes each tick. It reads the REAL sealed
usage probe, evaluates the weekly cap against the configured threshold, and
delivers via the chosen channel seam:

* default → stdout (captured in the launchd job's ``StandardOutPath``);
* ``--notify-cmd "<shell command>"`` → shell that command with the message on
  stdin (the launchd → workspace-poster bridge, D-A1-3).

``--threshold-pct`` overrides the configured/ratified threshold for a one-off.
"""

from __future__ import annotations

import argparse
import shlex

from .alert import run_alert
from .notify import command_notify, stdout_notify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam.weekly_cap_alert",
        description="Fire a channel alert when the Claude weekly (seven_day) "
                    "cap crosses the owner-set threshold; silent below it; "
                    "on an unreadable cap, fire the categorical reason (no "
                    "fabricated number).")
    parser.add_argument(
        "--notify-cmd", metavar="CMD",
        help="Shell command to deliver the alert (message piped on stdin). "
             "Default: write the message to stdout.")
    parser.add_argument(
        "--threshold-pct", type=float, metavar="PCT",
        help="Override the configured/ratified weekly-cap alert threshold "
             "for this run.")
    args = parser.parse_args(argv)

    notify_fn = (
        command_notify(shlex.split(args.notify_cmd))
        if args.notify_cmd
        else stdout_notify
    )
    run_alert(threshold_pct=args.threshold_pct, notify_fn=notify_fn)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

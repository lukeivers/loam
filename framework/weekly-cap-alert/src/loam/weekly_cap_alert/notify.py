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

"""The channel delivery seam — **channel-agnostic** (H-3 / D-A1-3).

loam source must never import the pos3 workspace channel module
(``channel_notify.py`` / ``post_to_active_channel``) — that is the H-3 fence
proven by handsoff-loop's AC.HB.4. So the alert takes a ``notify_fn`` and this
module supplies only *generic* implementations:

* :func:`stdout_notify` — the default. Writes the message to stdout, where the
  launchd job's ``StandardOutPath`` captures it. Self-contained, no network, no
  workspace import.
* :func:`command_notify` — a factory returning a ``notify_fn`` that shells an
  external command with the message on **stdin**. The launchd plist is rendered
  with ``--notify-cmd`` pointed at a workspace poster (a thin stdin →
  ``post_to_active_channel`` wrapper, a *workspace* artifact out of loam's
  fence) so the real Discord ping happens without loam ever importing the pos3
  channel machinery.

Neither implementation knows what a "channel" is; both are pure plumbing.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Callable

# A notify_fn takes the fully-formed alert message and delivers it somewhere.
NotifyFn = Callable[[str], None]


def stdout_notify(message: str) -> None:
    """Deliver by writing to stdout (the launchd job's captured log)."""
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def command_notify(command: list[str]) -> NotifyFn:
    """Return a ``notify_fn`` that shells ``command`` with the message on stdin.

    This is the launchd → workspace-poster bridge (D-A1-3): the plist fills
    ``--notify-cmd`` and the alert pipes its message into that command's stdin.
    loam stays channel-agnostic; the command names whatever the workspace uses
    to reach Luke.
    """

    def _notify(message: str) -> None:
        subprocess.run(
            command,
            input=message,
            text=True,
            check=True,
        )

    return _notify

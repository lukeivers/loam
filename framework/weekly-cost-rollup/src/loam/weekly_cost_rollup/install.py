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

"""Render + install the **weekly** launchd agent (AC.RUP.2a).

The roll-up must run on a weekly schedule that survives a Claude session ending,
so it ships as a launchd *LaunchAgent* (independent of any session's lifetime).
This renders the ``.plist.tmpl`` into a valid plist and writes it to the
``LaunchAgents`` directory. ``loading`` the agent into ``launchd`` is left to the
operator (a system-mutating ``launchctl load`` is out of a build's remit) — the
installed plist artifact is what AC.RUP.2a verifies.
"""

from __future__ import annotations

import string
from pathlib import Path
from typing import Optional

LABEL = "com.loam.weekly-cost-rollup"

# Default weekly cadence: Monday 09:00 local. The weekly cap and token proxy move
# on a weekly bucket, so a single start-of-week digest is the right tick.
DEFAULT_WEEKDAY = 1  # Monday (launchd: 0/7 = Sunday)
DEFAULT_HOUR = 9
DEFAULT_MINUTE = 0

# install.py lives at
# framework/weekly-cost-rollup/src/loam/weekly_cost_rollup/install.py, so
# parents[3] is the component root where ops/launchd/ sits.
_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "ops"
    / "launchd"
    / "com.loam.weekly-cost-rollup.plist.tmpl"
)


def _notify_cmd_args(notify_cmd: Optional[str]) -> str:
    """Render the ``--notify-cmd`` ProgramArguments fragment (reused from WS-A1).

    When a workspace poster command is given (one shell-command string), emit
    ``--notify-cmd`` and that string as two ``<string>`` argv entries; the CLI
    ``shlex``-splits the string and shells it with the message on stdin. When
    absent, emit nothing — the roll-up falls back to its stdout default.
    """
    if not notify_cmd:
        return ""
    tokens = ["--notify-cmd", notify_cmd]
    return "".join(f"\n        <string>{t}</string>" for t in tokens)


def render_plist(
    *,
    python: str,
    working_dir: str,
    stdout_log: str,
    stderr_log: str,
    weekday: int = DEFAULT_WEEKDAY,
    hour: int = DEFAULT_HOUR,
    minute: int = DEFAULT_MINUTE,
    notify_cmd: Optional[str] = None,
    label: str = LABEL,
) -> str:
    """Render the weekly launchd plist text from the template."""
    template = string.Template(_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        LABEL=label,
        PYTHON=python,
        WORKING_DIR=working_dir,
        STDOUT_LOG=stdout_log,
        STDERR_LOG=stderr_log,
        WEEKDAY=weekday,
        HOUR=hour,
        MINUTE=minute,
        NOTIFY_CMD_ARGS=_notify_cmd_args(notify_cmd),
    )


def install(
    *,
    python: str,
    working_dir: str,
    stdout_log: str,
    stderr_log: str,
    weekday: int = DEFAULT_WEEKDAY,
    hour: int = DEFAULT_HOUR,
    minute: int = DEFAULT_MINUTE,
    notify_cmd: Optional[str] = None,
    launch_agents_dir: Optional[Path] = None,
    label: str = LABEL,
) -> Path:
    """Render the plist and write it into ``LaunchAgents``; return its path.

    ``launch_agents_dir`` defaults to ``~/Library/LaunchAgents`` (the real
    user-agent location); tests pass a tmp dir. Writing the plist is the whole of
    what a build does — the operator runs ``launchctl load`` to activate it.
    """
    plist = render_plist(
        python=python,
        working_dir=working_dir,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        weekday=weekday,
        hour=hour,
        minute=minute,
        notify_cmd=notify_cmd,
        label=label,
    )
    target_dir = (
        launch_agents_dir
        if launch_agents_dir is not None
        else Path("~/Library/LaunchAgents").expanduser()
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{label}.plist"
    target.write_text(plist, encoding="utf-8")
    return target

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

"""AC.RUP.2a — the job is registered to run WEEKLY and survives a session ending.

Verified from the installed launchd artifact (not ``.claude/settings.json``): a
valid plist with a weekly ``StartCalendarInterval`` + ``RunAtLoad`` and NO
``KeepAlive``, invoking ``python -m loam.weekly_cost_rollup``.
"""

from __future__ import annotations

import plistlib

from loam.weekly_cost_rollup.install import (
    DEFAULT_HOUR,
    DEFAULT_MINUTE,
    DEFAULT_WEEKDAY,
    LABEL,
    install,
)


def _install(tmp_path, notify_cmd=None):
    return install(
        python="/venv/bin/python",
        working_dir="/Users/lukeivers/loam",
        stdout_log="/tmp/rollup.out",
        stderr_log="/tmp/rollup.err",
        notify_cmd=notify_cmd,
        launch_agents_dir=tmp_path,
    )


def test_AC_RUP_2a_installed_plist_is_valid_weekly_and_survives_session(tmp_path):
    path = _install(tmp_path)
    assert path.exists()
    assert path.name == f"{LABEL}.plist"

    doc = plistlib.loads(path.read_bytes())

    assert doc["Label"] == LABEL
    # Invokes the production CLI module.
    assert doc["ProgramArguments"][:3] == ["/venv/bin/python", "-m", "loam.weekly_cost_rollup"]

    # Weekly schedule (StartCalendarInterval), NOT a coarse StartInterval.
    assert "StartInterval" not in doc
    cal = doc["StartCalendarInterval"]
    assert cal["Weekday"] == DEFAULT_WEEKDAY
    assert cal["Hour"] == DEFAULT_HOUR
    assert cal["Minute"] == DEFAULT_MINUTE

    # Survives a session ending (LaunchAgent), fires once on load, and is a
    # read-and-exit tick (no KeepAlive resurrection).
    assert doc["RunAtLoad"] is True
    assert "KeepAlive" not in doc


def test_AC_RUP_2a_notify_cmd_wires_into_program_arguments(tmp_path):
    path = _install(tmp_path, notify_cmd="python3 /ws/poster.py")
    doc = plistlib.loads(path.read_bytes())
    args = doc["ProgramArguments"]
    assert "--notify-cmd" in args
    assert "python3 /ws/poster.py" in args


def test_AC_RUP_2a_reinstall_is_idempotent(tmp_path):
    first = _install(tmp_path)
    second = _install(tmp_path)
    assert first == second
    assert sorted(p.name for p in tmp_path.iterdir()) == [f"{LABEL}.plist"]

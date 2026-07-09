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

"""AC.CAP.3 — the job is registered on a schedule and survives a session end.

Drives the REAL install renderer, writes the plist to a tmp LaunchAgents dir,
and verifies the installed artifact: it parses as a valid plist, carries a
periodic ``StartInterval`` + ``RunAtLoad`` and NO ``KeepAlive`` (it is a tick,
not a resurrected daemon), and invokes ``python -m loam.weekly_cap_alert``.
A LaunchAgent plist persists on disk independent of any Claude session — that is
what "survives a session ending" means; the artifact is the proof, not
``.claude/settings.json``.
"""

from __future__ import annotations

import plistlib

from loam.weekly_cap_alert import install as install_mod


def _install(tmp_path, **overrides):
    kwargs = dict(
        python="/Users/lukeivers/loam/.venv/bin/python",
        working_dir="/Users/lukeivers/loam",
        stdout_log=str(tmp_path / "out.log"),
        stderr_log=str(tmp_path / "err.log"),
        launch_agents_dir=tmp_path / "LaunchAgents",
    )
    kwargs.update(overrides)
    return install_mod.install(**kwargs)


def test_installed_plist_is_valid_and_periodic(tmp_path):
    target = _install(tmp_path)
    # The artifact was written into the LaunchAgents dir (persists across
    # sessions — it is a user LaunchAgent, not session state).
    assert target.exists()
    assert target.parent.name == "LaunchAgents"
    assert target.name == "com.loam.weekly-cap-alert.plist"

    data = plistlib.loads(target.read_bytes())

    # Periodic schedule: RunAtLoad fires once, StartInterval re-fires the tick.
    assert data["RunAtLoad"] is True
    assert isinstance(data["StartInterval"], int) and data["StartInterval"] > 0
    # It is a probe-and-exit tick, NOT a KeepAlive daemon.
    assert "KeepAlive" not in data


def test_installed_plist_invokes_the_production_module(tmp_path):
    target = _install(tmp_path)
    data = plistlib.loads(target.read_bytes())
    args = data["ProgramArguments"]
    assert args[0] == "/Users/lukeivers/loam/.venv/bin/python"
    assert args[1] == "-m"
    assert args[2] == "loam.weekly_cap_alert"


def test_interval_is_configurable(tmp_path):
    target = _install(tmp_path, interval_secs=3600)
    data = plistlib.loads(target.read_bytes())
    assert data["StartInterval"] == 3600


def test_notify_cmd_wires_the_delivery_bridge_into_program_arguments(tmp_path):
    # The launchd → workspace-poster bridge (D-A1-3): a --notify-cmd arrives as
    # its own argv pair the CLI shells with the message on stdin.
    target = _install(tmp_path, notify_cmd="python3 /ws/poster.py")
    data = plistlib.loads(target.read_bytes())
    args = data["ProgramArguments"]
    assert "--notify-cmd" in args
    assert args[args.index("--notify-cmd") + 1] == "python3 /ws/poster.py"


def test_default_has_no_notify_cmd_so_alert_falls_back_to_stdout(tmp_path):
    target = _install(tmp_path)
    data = plistlib.loads(target.read_bytes())
    assert "--notify-cmd" not in data["ProgramArguments"]

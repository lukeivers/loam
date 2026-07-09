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

"""AC.PAGE.2.

(a) Regeneration is wired to a launchd/cron job, verifiable from the
    installed plist artifact — NOT ``.claude/settings.json``.
(b) A stale page is overwritten on the next trigger.

Part (b) drives the real CLI ``render`` over ON-DISK fixtures so the
DEFAULT source readers (``collect_fleet`` / ``load_decision_queue``)
genuinely execute — the injected-source ACs never touch that wiring."""

from __future__ import annotations

from conftest import make_decision_queue, make_live_run_dir
from loam.fleet_page import install_launchd_job
from loam.fleet_page.__main__ import main


def test_AC_PAGE_2a_launchd_plist_written_and_references_regenerator(tmp_path):
    la = tmp_path / "LaunchAgents"
    out = tmp_path / "fleet.html"
    plist = install_launchd_job(
        out_path=out,
        roots=[tmp_path / "ws"],
        launch_agents_dir=la,
        interval_s=300,
    )
    assert plist.exists()
    body = plist.read_text(encoding="utf-8")
    # It runs THIS module's regenerator on an interval.
    assert "loam.fleet_page" in body
    assert "render" in body
    assert "<key>StartInterval</key>" in body
    assert "<integer>300</integer>" in body
    assert str(out) in body


def test_AC_PAGE_2a_plist_never_references_settings_json(tmp_path):
    la = tmp_path / "LaunchAgents"
    plist = install_launchd_job(
        out_path=tmp_path / "fleet.html",
        roots=[tmp_path / "ws"],
        launch_agents_dir=la,
    )
    body = plist.read_text(encoding="utf-8")
    # The §5 hard constraint: the regenerator is a launchd job, NOT a
    # settings.json hook. The artifact proves it.
    assert "settings.json" not in body
    assert ".claude" not in body


def test_AC_PAGE_2b_real_cli_regenerates_and_overwrites(tmp_path):
    ws = tmp_path / "ws"
    make_live_run_dir(ws, name="run-a")
    make_decision_queue(ws)
    out = tmp_path / "fleet.html"

    # First trigger: the real default readers run (collect_fleet finds the
    # live run; load_decision_queue reads the real queue file).
    rc = main(["render", "--out", str(out), "--root", str(ws),
               "--pm-root", str(ws)])
    assert rc == 0
    first = out.read_text(encoding="utf-8")
    assert "Live agents" in first
    assert ">live<" in first                       # collector saw it alive
    assert "Approve the WS-A3 page layout" in first  # real decision queue

    # Second trigger overwrites the stale page in place.
    make_live_run_dir(ws, name="run-b")
    rc = main(["render", "--out", str(out), "--root", str(ws),
               "--pm-root", str(ws)])
    assert rc == 0
    second = out.read_text(encoding="utf-8")
    assert second != first                         # stale content replaced
    # run-b is now a second live agent — the count grew.
    assert second.count(">live<") >= 2

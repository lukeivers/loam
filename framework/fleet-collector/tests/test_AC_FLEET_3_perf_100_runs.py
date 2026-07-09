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

"""AC.FLEET.3 — runtime under 5 seconds against 100 fixture runs, driven
through the production entry point (this feeds a regenerated page, not a
live service)."""

from __future__ import annotations

import time

from conftest import make_completed_run, make_dead_run, make_live_run

from loam.fleet_collector import collect_fleet


def test_hundred_runs_under_five_seconds(tmp_path):
    ws = tmp_path / "workspaceA"
    # A realistic mix: live, dead, and completed-with-cost runs.
    for i in range(100):
        if i % 3 == 0:
            make_live_run(ws, name=f"live-{i:03d}")
        elif i % 3 == 1:
            make_dead_run(ws, name=f"dead-{i:03d}")
        else:
            make_completed_run(ws, name=f"done-{i:03d}")

    t0 = time.monotonic()
    fleet = collect_fleet(ws)
    elapsed = time.monotonic() - t0

    assert fleet["run_count"] == 100
    assert elapsed < 5.0, f"collector took {elapsed:.2f}s for 100 runs"

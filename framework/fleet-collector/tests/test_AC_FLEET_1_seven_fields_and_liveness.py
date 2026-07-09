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

"""AC.FLEET.1 (outcome-altitude) — against a fixture dir with ≥3 run
records (live-with-recent-heartbeat, dead-stale, completed-with-cost),
the production entry point emits JSON where each run carries the seven
named fields, and the alive/dead judgment matches the artifact evidence.
Liveness is the reused ``probe_liveness`` — proven by value-equivalence
against the shared reader (reuse, not a re-roll)."""

from __future__ import annotations

import json

from conftest import make_completed_run, make_dead_run, make_live_run

from loam.fleet_collector import collect_fleet
from loam.fleet_collector.__main__ import main
from loam.fleet_collector._liveness import probe_liveness

SEVEN_FIELDS = {"workspace", "objective", "stage", "elapsed_s", "alive",
                "cost_usd", "exit_status"}


def _index_by_dir(fleet: dict) -> dict:
    return {r["run_dir"]: r for r in fleet["runs"]}


def test_three_runs_each_carry_the_seven_fields(tmp_path):
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)
    dead = make_dead_run(ws)
    done = make_completed_run(ws)

    fleet = collect_fleet(ws)

    assert fleet["run_count"] == 3
    by_dir = _index_by_dir(fleet)
    assert set(by_dir) == {str(live.resolve()), str(dead.resolve()),
                           str(done.resolve())}
    for row in fleet["runs"]:
        assert SEVEN_FIELDS.issubset(row), f"missing fields in {row}"
        # cost_source is the constraint companion: a cost is real or
        # honestly absent, never fabricated.
        assert "cost_source" in row


def test_alive_dead_judgment_matches_artifact_evidence(tmp_path):
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)
    dead = make_dead_run(ws)
    done = make_completed_run(ws)

    by_dir = _index_by_dir(collect_fleet(ws))

    assert by_dir[str(live.resolve())]["alive"] is True
    assert by_dir[str(dead.resolve())]["alive"] is False
    assert by_dir[str(done.resolve())]["alive"] is False


def test_collector_alive_equals_shared_probe(tmp_path):
    """Reuse-not-re-roll: the collector's ``alive`` is exactly what the
    shared ``probe_liveness`` reports for the same dir."""
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)
    dead = make_dead_run(ws)
    done = make_completed_run(ws)

    by_dir = _index_by_dir(collect_fleet(ws))
    for run_dir in (live, dead, done):
        expected = bool(probe_liveness(run_dir)["alive"])
        assert by_dir[str(run_dir.resolve())]["alive"] is expected


def test_completed_run_carries_objective_and_real_cost(tmp_path):
    ws = tmp_path / "workspaceA"
    done = make_completed_run(ws, objective="Build a CSV-to-JSON converter.",
                              cost_usd=0.42, exit_status=0)

    row = _index_by_dir(collect_fleet(ws))[str(done.resolve())]
    assert row["objective"] == "Build a CSV-to-JSON converter."
    assert row["stage"] == "verdict"
    assert row["cost_usd"] == 0.42
    assert row["cost_source"] == "session-/cost-echo"
    assert row["exit_status"] == 0


def test_live_run_has_null_objective_and_absent_cost(tmp_path):
    """D-A2-1/-2: a live run is not yet summarised — objective is null,
    never invented; no driver summary — cost is honestly absent."""
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)

    row = _index_by_dir(collect_fleet(ws))[str(live.resolve())]
    assert row["objective"] is None
    assert row["stage"] == "building"  # last NON-heartbeat stage
    assert row["cost_usd"] is None
    assert row["cost_source"] == "absent"
    assert row["exit_status"] is None
    assert row["workspace"] == str(ws)  # runs/<ts> -> workspace two up


def test_production_cli_writes_fleet_json_file(tmp_path):
    """Strongest altitude: drive the real CLI entry point with no
    pre-set state; it discovers the runs and writes the artifact WS-A3
    consumes."""
    ws = tmp_path / "workspaceA"
    make_live_run(ws)
    make_dead_run(ws)
    make_completed_run(ws)
    out = tmp_path / "out" / "fleet.json"

    rc = main(["--root", str(ws), "--out", str(out)])

    assert rc == 0
    fleet = json.loads(out.read_text(encoding="utf-8"))
    assert fleet["run_count"] == 3
    assert {r["alive"] for r in fleet["runs"]} == {True, False}
    # live run sorts first (live feed reads top-down).
    assert fleet["runs"][0]["alive"] is True

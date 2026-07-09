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

"""AC.FLEET.2 — a run record with a partial (mid-write) last line does
not crash the collector; the run appears with its last complete state.
Driven through the production entry point (``collect_fleet``)."""

from __future__ import annotations

import json

from conftest import make_live_run

from loam.fleet_collector import collect_fleet


def _append_partial_line(run_dir, partial: str) -> None:
    with (run_dir / "run_record.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(partial)  # no trailing newline: a torn mid-write line


def test_partial_last_line_does_not_crash(tmp_path):
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)  # last complete stage: building
    # A JSON object cut off mid-write — exactly what a concurrent
    # appender leaves between flushes.
    _append_partial_line(live, '{"ts": 1, "ts_mono": 9, "stage": "check')

    fleet = collect_fleet(ws)  # must not raise

    row = next(r for r in fleet["runs"] if r["run_dir"] == str(live.resolve()))
    # The run still appears, with its last COMPLETE state (building),
    # not the torn "check..." line.
    assert row["stage"] == "building"
    assert row["alive"] is True


def test_completely_garbage_line_is_skipped_not_fatal(tmp_path):
    ws = tmp_path / "workspaceA"
    live = make_live_run(ws)
    _append_partial_line(live, "this is not json at all")

    fleet = collect_fleet(ws)
    row = next(r for r in fleet["runs"] if r["run_dir"] == str(live.resolve()))
    assert row["stage"] == "building"


def test_empty_run_record_is_not_fatal(tmp_path):
    ws = tmp_path / "workspaceA"
    run_dir = ws / "runs" / "empty"
    run_dir.mkdir(parents=True)
    (run_dir / "run_record.jsonl").write_text("", encoding="utf-8")

    fleet = collect_fleet(ws)  # must not raise
    row = next(r for r in fleet["runs"]
               if r["run_dir"] == str(run_dir.resolve()))
    assert row["stage"] is None
    assert row["elapsed_s"] is None

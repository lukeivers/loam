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

"""Path bootstrap: put this component's src (and, transitively, the
shared handsoff-loop src via ``_liveness``) on the import path, and
provide the fixture builders the AC suites share."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # framework/fleet-collector/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def write_run_record(run_dir: Path, events: list[dict]) -> Path:
    """Write a handsoff-loop-shaped run_record.jsonl (one JSON line per
    event)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "run_record.jsonl"
    path.write_text(
        "".join(json.dumps(ev) + "\n" for ev in events), encoding="utf-8")
    return path


def age_run_dir(run_dir: Path, age_s: float) -> None:
    """Backdate every file's mtime in the run dir so ``probe_liveness``
    (newest-artifact mtime) genuinely reads it as stale — otherwise a
    freshly-written fixture always reads alive and the dead/completed
    rows would pass for the wrong reason."""
    when = time.time() - age_s
    for p in run_dir.rglob("*"):
        if p.is_file():
            os.utime(p, (when, when))


def make_live_run(root: Path, name: str = "live") -> Path:
    """A live handsoff run: recent heartbeat, mid-build, no summary, no
    cost record. Fresh mtime → probe reads it alive."""
    run_dir = root / "runs" / name
    now = time.time()
    write_run_record(run_dir, [
        {"ts": now - 200, "ts_mono": 200.0, "stage": "understanding",
         "message": "Reading your ask."},
        {"ts": now - 120, "ts_mono": 280.0, "stage": "building",
         "message": "Building now."},
        {"ts": now - 5, "ts_mono": 395.0, "stage": "heartbeat",
         "message": "Still working — progress landing on disk."},
    ])
    return run_dir


def make_dead_run(root: Path, name: str = "dead") -> Path:
    """A dead-stale handsoff run: last stage was building, no summary,
    aged well past the staleness bound → probe reads it dead."""
    run_dir = root / "runs" / name
    now = time.time()
    write_run_record(run_dir, [
        {"ts": now - 4000, "ts_mono": 10.0, "stage": "planning",
         "message": "Acceptance gate frozen."},
        {"ts": now - 3800, "ts_mono": 210.0, "stage": "building",
         "message": "Building now."},
        {"ts": now - 3700, "ts_mono": 310.0, "stage": "heartbeat",
         "message": "Still working."},
    ])
    age_run_dir(run_dir, age_s=3600)
    return run_dir


def make_completed_run(root: Path, name: str = "completed",
                       objective: str = "Build a CSV-to-JSON converter.",
                       cost_usd: float = 0.42,
                       exit_status: int = 0) -> Path:
    """A finished run: run_record + run_summary (objective) + a
    co-located subloam-driver cost summary (cost/exit_status). Aged so it
    reads dead (finished)."""
    run_dir = root / "runs" / name
    now = time.time()
    write_run_record(run_dir, [
        {"ts": now - 5000, "ts_mono": 10.0, "stage": "understanding",
         "message": "Reading your ask."},
        {"ts": now - 4600, "ts_mono": 410.0, "stage": "building",
         "message": "Building now."},
        {"ts": now - 4200, "ts_mono": 810.0, "stage": "verdict",
         "message": "Independent check passed."},
    ])
    # handsoff-loop run_summary.json shape (as_evidence): objective lives
    # under design.objective (intent.objective is the fallback).
    (run_dir / "run_summary.json").write_text(json.dumps({
        "terminal": "done",
        "run_dir": str(run_dir),
        "verdict_text": "passed",
        "intent": {"objective": objective},
        "design": {"objective": objective},
    }, indent=2), encoding="utf-8")
    # subloam-driver summary shape: the full cost key-set together.
    (run_dir / "driver_summary.json").write_text(json.dumps({
        "genuine_turns": 6,
        "exit_status": exit_status,
        "cost_usd": cost_usd,
        "cost_source": "session-/cost-echo",
    }, indent=2), encoding="utf-8")
    age_run_dir(run_dir, age_s=4000)
    return run_dir

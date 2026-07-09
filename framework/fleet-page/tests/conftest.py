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

"""Path bootstrap + shared fixtures for the WS-A3 AC suites.

Puts this component's ``src`` on the import path and provides both the
INJECTED source values the render-level ACs use (fixture fleet dict, stub
cost rows, stub decisions) and the ON-DISK fixtures the real-wiring AC
uses (a real handsoff-shaped run dir, a real ``decision-queue.yaml``) so
the default readers in ``sources`` genuinely execute."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # framework/fleet-page/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ---- injected source values (render-level ACs) ----------------------

def fixture_fleet() -> dict:
    """A fleet dict shaped exactly like WS-A2's ``collect_fleet`` output:
    one live run (no cost), one finished run (with cost + exit 0). The
    long objective string exercises the horizontal-overflow guard."""
    return {
        "generated_at": 1_760_000_000.0,
        "generated_at_iso": "2026-07-09T05:30:00",
        "run_count": 2,
        "runs": [
            {
                "run_dir": "/Users/x/ws/runs/live-one",
                "workspace": "/Users/x/ws",
                "objective": "Ship a/very/long/objective/path/that/would/"
                             "overflow/a/narrow/viewport/xxxxxxxxxxxxxxxxxx",
                "stage": "building",
                "elapsed_s": 245.0,
                "alive": True,
                "artifact_age_s": 4.0,
                "cost_usd": None,
                "cost_source": "absent",
                "exit_status": None,
            },
            {
                "run_dir": "/Users/x/ws/runs/done-one",
                "workspace": "/Users/x/ws",
                "objective": "Build a CSV-to-JSON converter",
                "stage": "verdict",
                "elapsed_s": 812.0,
                "alive": False,
                "artifact_age_s": 4000.0,
                "cost_usd": 0.42,
                "cost_source": "session-/cost-echo",
                "exit_status": 0,
            },
        ],
    }


def stub_cost_rows() -> list[dict]:
    return [
        {"prompt_name": "planner", "input_tokens": 120_000,
         "output_tokens": 30_000, "call_count": 12},
        {"prompt_name": "worker", "input_tokens": 90_000,
         "output_tokens": 260_000, "call_count": 44},
    ]


def stub_decisions() -> list[dict]:
    return [
        {"text": "Ratify the launchd default interval (300s)?",
         "provenance": "ws-a3-build", "enqueued_at": "2026-07-09T05:00:00"},
    ]


# ---- on-disk fixtures (real-wiring AC) ------------------------------

def make_live_run_dir(root: Path, name: str = "live") -> Path:
    """A real handsoff-shaped run dir with a fresh mtime so the WS-A2
    collector's ``probe_liveness`` genuinely reads it alive."""
    run_dir = root / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    now = time.time()
    events = [
        {"ts": now - 120, "ts_mono": 120.0, "stage": "understanding",
         "message": "Reading your ask."},
        {"ts": now - 40, "ts_mono": 200.0, "stage": "building",
         "message": "Building now."},
        {"ts": now - 3, "ts_mono": 237.0, "stage": "heartbeat",
         "message": "Still working."},
    ]
    (run_dir / "run_record.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return run_dir


def make_decision_queue(pm_root: Path, handle: str = "acme") -> Path:
    """A real per-project-pm state dir with a valid ``decision-queue.yaml``
    (schema_version 1) and the ``contract.yaml`` ``discover_pm_dirs``
    keys on."""
    pm_dir = pm_root / "workspace" / ".loam" / "pms" / handle
    pm_dir.mkdir(parents=True, exist_ok=True)
    (pm_dir / "contract.yaml").write_text(
        "schema_version: 1\nhandle: acme\nproject_name: Acme\n",
        encoding="utf-8")
    (pm_dir / "decision-queue.yaml").write_text(
        "schema_version: 1\n"
        "queue:\n"
        "  - text: Approve the WS-A3 page layout before it ships?\n"
        "    provenance: ws-a3\n"
        "    enqueued_at: '2026-07-09T05:00:00'\n",
        encoding="utf-8")
    return pm_dir

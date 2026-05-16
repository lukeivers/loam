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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PBR.2 — the task set is the frozen non-subjective set,
content-pinned, with a POSITIVE real-outcome floor per task (hollow
⇒ non-pass by construction), sized for a definite verdict.

Outcome under test (not method): every task carries a plain-language
non-tech statement + a positive-real-outcome floor check + a held-out
anti-overfit check absent from every prompt; the set is content-hash
pinned; and a nominal-but-hollow result drives the floor (or the
held-out conjunction) NON-zero — not a pass — for the false-success
classes (hardcoded / vacuous-extraction / target-untouched).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))
TASKS = PBR / "tasks"


def test_AC_PBR_2_set_is_content_hash_pinned_and_nonsubjective() -> None:
    from programbench_revival import load_frozen_task_set

    ts = load_frozen_task_set()
    assert len(ts.content_sha256) == 64  # sha256 hex, pinned
    assert len(ts.tasks) >= 5, (
        "sized for a definite verdict (a non-trivial baseline-miss "
        "subset must be definable)"
    )
    for t in ts.tasks:
        assert t.statement.strip()
        assert t.floor_check and (TASKS / t.floor_check).exists()
        assert t.held_out_check and (TASKS / t.held_out_check).exists()
        # ground-truth isolation: the prompt (statement) must not
        # carry the check filename / held-out inputs
        assert t.floor_check not in t.statement
        assert t.held_out_check not in t.statement


def _run(check: str, wd: Path) -> int:
    return subprocess.run(
        [sys.executable, str(TASKS / check)], cwd=str(wd),
        capture_output=True, text=True, timeout=60,
    ).returncode


def test_AC_PBR_2_positive_floor_hollow_is_nonpass(tmp_path) -> None:
    """PB4 target-untouched (the owner's email-task false-success
    shape): an UNCHANGED named target drives the floor NON-zero —
    not a pass. PB1 hardcoded: the held-out anti-overfit drives it
    non-zero even though the floor alone passes (both-must-pass
    spine)."""
    from programbench_revival import load_frozen_task_set

    ts = load_frozen_task_set()

    # PB4 — leave settings.json UNTOUCHED -> floor must be non-pass
    pb4 = ts.task_by_id("PB4-rename-key")
    wd = tmp_path / "pb4"
    wd.mkdir()
    for rel, content in pb4.setup_files.items():
        (wd / rel).write_text(content)
    assert _run(pb4.floor_check, wd) != 0, (
        "an untouched named target MUST be a non-pass by construction "
        "(the 'I would have' / didn't-touch false-success class)"
    )

    # PB1 — a hardcoded literal passes the floor but the held-out
    # anti-overfit MUST reject it (no real generalisable effect)
    pb1 = ts.task_by_id("PB1-csv-sum")
    wd1 = tmp_path / "pb1"
    wd1.mkdir()
    for rel, content in pb1.setup_files.items():
        (wd1 / rel).write_text(content)
    (wd1 / "solve.py").write_text("print(120.74)\n")
    assert _run(pb1.floor_check, wd1) == 0
    assert _run(pb1.held_out_check, wd1) != 0, (
        "a hardcoded literal MUST fail the held-out anti-overfit "
        "check (the produced-but-no-real-effect false-success class)"
    )


def test_AC_PBR_2_positive_floor_real_outcome_passes(tmp_path) -> None:
    """A genuine real-outcome solution passes BOTH the floor and the
    held-out check (the gate is not impossibly strict)."""
    from programbench_revival import load_frozen_task_set

    ts = load_frozen_task_set()
    pb1 = ts.task_by_id("PB1-csv-sum")
    wd = tmp_path / "pb1ok"
    wd.mkdir()
    for rel, content in pb1.setup_files.items():
        (wd / rel).write_text(content)
    (wd / "solve.py").write_text(
        "import csv\n"
        "r=csv.reader(open('sales.csv'))\n"
        "next(r)\n"
        "print(round(sum(float(x[1]) for x in r), 2))\n"
    )
    assert _run(pb1.floor_check, wd) == 0
    assert _run(pb1.held_out_check, wd) == 0

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

"""AC.RPB.2 — the task set IS the REAL public ProgramBench (real
digest-pinned task images + real HF blobs, scored by the REAL
upstream programbench eval), content-pinned, sized for a
non-degenerate verdict; a nominal-but-hollow result is a non-pass by
construction (the GRADED-floor positive-real-outcome rule, D-RPB-2).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
sys.path.insert(0, str(REALPB / "src"))


def test_AC_RPB_2_is_real_public_pb_not_substitute() -> None:
    from programbench_revival_realpb.loader import (
        load_frozen_realpb_set,
    )

    ts = load_frozen_realpb_set()

    # it IS the real public ProgramBench, content-hash-pinned, and is
    # explicitly NOT the v2 substitute task set
    assert ts.is_real_public_programbench is True
    assert ts.task_set_id != \
        "programbench-revival-v2-honest-scope-6task"
    assert "real-public" in ts.task_set_id
    assert len(ts.content_sha256) == 64  # sha256 hex, pinned

    # every task binds to a REAL upstream public ProgramBench instance
    # by digest-pinned :task image + the real HF dataset
    assert ts.hf_dataset == "programbench/ProgramBench-Tests"
    assert ts.hf_revision_snapshot
    for t in ts.tasks:
        assert t.image.startswith("programbench/")
        assert t.image.endswith(":task")
        assert t.image_digest.startswith("sha256:")
        assert "_1776_" in t.image
        assert t.statement.strip()      # plain-language statement
        # the agent gets ONLY the statement — no test suite, no
        # scoring command, no setup that leaks ground truth
        assert "test" not in t.filter_regex.lower() or \
            t.filter_regex.startswith("^")

    # the per-task positive-real-outcome floor theta is FROZEN over
    # the GRADED upstream score (D-RPB-2): a hollow / compile_failed
    # / vacuous submission scores ~0 < theta => non-pass by
    # construction; theta is meaningful (>0, <1)
    for t in ts.tasks:
        assert 0.0 < t.floor_theta < 1.0

    # sized so the AC.RPB.5 baseline-miss denominator can be
    # non-degenerate OR the verdict explicitly returns indeterminate
    # naming the small-denominator reason (the k_min small-k floor)
    assert len(ts.tasks) >= ts.k_min
    assert ts.k_min >= 2

    # the upstream eval contract is the real one (Tier-0 from the
    # local clone) — the deterministic floor signal
    assert "n_resolved / len(test_results)" in \
        ts.upstream_eval["score_contract"]
    assert "compile_failed" in ts.upstream_eval["score_contract"]

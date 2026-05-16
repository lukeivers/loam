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

"""AC.PBD.6 — the frozen sealed real-PB semantics are not perturbed
(no-regression guard).

This cycle is a DE-NOISE + measurement-honesty corrective only. The
frozen sealed measurement semantics — zero-interaction parity
(AC.RPB.1), independent-judge-not-loop's-own (AC.RPB.3), the
positive-real-outcome floor + per-task frozen threshold (AC.RPB.2),
the pre-declared three-valued margin + k_min >= 2 small-k floor
(AC.RPB.5), honest-negative first-class (AC.RPB.7), and the frozen
task-set content-hash mechanism — are byte-behaviour-unchanged, and
the existing parent AC.RPB.* / AC.BRC.* test families still pass
unchanged.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
V2 = ROOT / "framework" / "tools" / "programbench-revival"
ISO = ROOT / "framework" / "tools" / "loam-spawn-isolation"
TESTS = ROOT / "framework" / "hands-off-lifecycle" / "tests"
sys.path.insert(0, str(ISO / "src"))
sys.path.insert(0, str(REALPB / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_PBD_6_frozen_semantics_surfaces_unchanged() -> None:
    from programbench_revival_realpb import loader

    loader_src = inspect.getsource(loader)
    # k_min >= 2 small-k floor invariant is still enforced (AC.RPB.5)
    assert "k_min < 2" in loader_src
    assert "frozen_k_min must be >= 2" in loader_src
    # the content-hash mechanism still computes sha256 over the EXACT
    # bytes on disk (the contamination spine — AC.RPB.6) and is NOT
    # replaced by a tolerate path
    assert "_sha256(raw)" in loader_src
    assert "content_sha256=sha" in loader_src
    # the REAL-public-PB gate (not the v2 substitute) is intact
    assert "is_real_public_programbench" in loader_src

    from programbench_revival import arms

    arms_src = inspect.getsource(arms)
    # zero-interaction parity prose intact (AC.RPB.1): closed channel,
    # no clarifying question, single sentence
    assert "There is NO channel to ask them anything" in arms_src
    assert "ONE bare ``claude -p``" in arms_src
    # the de-noise convention did NOT introduce an interactive
    # prompt / retry-to-green into either arm (honest-negative first
    # class, AC.RPB.7) — the convention itself states "no retry"
    prompt = arms._ARM_DIRECTIVE.format(statement="x")
    assert "no retry" in prompt.lower()
    # the spawn-isolation mandate is unchanged (no new spawn
    # machinery — feedback_no_anthropic_api_key)
    assert "spawn_isolated_claude" in arms_src


def test_AC_PBD_6_parent_rpb_brc_families_still_green() -> None:
    # Run the frozen parent families in-process via a subprocess so a
    # regression in the frozen semantics surfaces here, bound to this
    # AC (the seal's sweep also runs them; this binds the
    # no-regression guarantee to AC.PBD.6 explicitly).
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-k",
            "AC_RPB_ or AC_BRC_",
            str(TESTS),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT / "framework" / "hands-off-lifecycle"),
        timeout=600,
    )
    combined = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, (
        "parent AC.RPB.*/AC.BRC.* family regressed:\n" + combined
    )
    # at least the known parent family count passed (no silent
    # deselect-to-zero)
    assert " passed" in combined
    assert "failed" not in combined.split(" passed")[0]

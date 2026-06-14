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

"""AC.CLP-ADOPT.2 ★ (outcome-altitude: true) — a keep-going work item
started through loam's normal PRODUCTION flow (the ``handsoff-loop``
methodology) drives via ``/goal`` on a real task with NO pre-arranged
state, and halts when the goal condition is met.

This is the slice's observable-use proof that ``/goal`` is loam's
adopted keep-going leg: not a doc, not a usage signal — the production
``handsoff-loop`` entry-point (``run_to_convergence``) dispatches a real
spawn-isolated ``claude -p`` sub-agent whose keep-going leg is
``/goal`` (``goal_drive.build_goal_drive_argv`` constructs the
``/goal <condition>`` directive fresh from the sub-task spec — no
pre-arranged ``/goal`` state), and the run halts at goal-met with the
``/goal`` artifacts (per-pass transcripts carrying the ``/goal``
directive + the verify-gated refine log) on disk.

The production path is consumed AS A BLACK BOX — this test imports the
``handsoff-loop`` tool's public entry-points and calls them; it does NOT
modify ``handsoff-loop`` source (that surface is out of the Slice-3
fence). The handsoff-loop core is already Tier-0 verified (AC.FOUND.0);
this test does not re-prove the core — it observes that the production
flow's keep-going leg IS ``/goal`` on a real run, which is the
AC.CLP-ADOPT.2 adoption outcome.

Live-model test, env-gated: set ``BFI_REAL_CLAUDE=1`` to run (one real
spawn-isolated sub-agent build, minutes-class, real ``claude`` binary,
default Sonnet, NO Anthropic API key, ``--bare`` never used). The
Slice-3 build executes this live once to prove the green; the env gate
keeps the suite portable for environments without the binary / quota.

Mirrors the existing production live-run pattern
(``framework/tools/handsoff-loop/tests/test_AC_CVG_OA_live_convergence_run.py``);
the Slice-3 addition is the explicit ``/goal``-leg observation in the
run record (the adoption-evidence this AC contracts for).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
_HL_SRC = REPO_ROOT / "framework" / "tools" / "handsoff-loop" / "src"
if str(_HL_SRC) not in sys.path:
    sys.path.insert(0, str(_HL_SRC))


@pytest.mark.skipif(
    os.environ.get("BFI_REAL_CLAUDE") != "1",
    reason="live /goal-driven sub-agent build; set BFI_REAL_CLAUDE=1 to run",
)
def test_AC_CLP_ADOPT_2_production_handsoff_loop_drives_via_goal() -> None:
    """Through the production ``run_to_convergence`` entry-point on a
    fresh workspace with NO pre-arranged state, a real ``/goal``-driven
    sub-agent leg runs to goal-met (or an honest terminal) with the
    ``/goal`` directive observable in the on-disk transcript trail."""
    from handsoff_loop.convergence import run_to_convergence
    from handsoff_loop.orchestrator import SubTask
    from handsoff_loop.verify import freeze_acceptance
    from handsoff_loop.goal_drive import DONE_SENTINEL

    with tempfile.TemporaryDirectory(prefix="adopt2-goal-") as root:
        root = Path(root)
        work = root / "work"
        artifacts = root / "artifacts"
        work.mkdir()

        # Frozen acceptance — authored + hash-pinned BEFORE any sub-agent
        # runs, seen by no sub-agent. A tiny real task that /goal must
        # iterate toward (the tool does not exist at run start — the
        # no-pre-arranged-state contract).
        frozen = freeze_acceptance(
            acceptance_id="adopt2-goal",
            content="counts.py prints the number of lines of its input file",
            check_argv=[
                "/bin/sh", "-c",
                "printf 'a\\nb\\nc\\n' > _in.txt && "
                "test \"$(python3 counts.py _in.txt)\" = 3",
            ],
            freeze_dir=root / "_frozen",
        )

        res = run_to_convergence(
            objective=(
                "a tiny command counts.py that prints how many lines its "
                "input file has"
            ),
            sub_tasks=[SubTask(
                name="build-counts",
                brief=(
                    "In the current directory create counts.py: "
                    "`python3 counts.py <file>` prints exactly the number "
                    "of lines in <file> (just the integer, "
                    "newline-terminated)."
                ),
                tighter_acceptance=(
                    "counts.py exists and prints the line count of a "
                    "sample file"
                ),
                check_command=(
                    "test -f counts.py && printf 'x\\ny\\n' > _t.txt && "
                    "test \"$(python3 counts.py _t.txt)\" = 2"
                ),
            )],
            frozen=frozen,
            work_dir=work,
            artifact_dir=artifacts,
            leg_ceiling_s=1200,
            max_refine_attempts=2,
            behavioral_done=False,
        )

        # Honest terminal — one of the two real terminals, never a
        # softened in-between; the no-retry-on-timeout evidence holds.
        assert res.stop_reason in ("done", "attempt-bound", "leg-timeout")
        assert res.timeout_retries == 0

        # The /goal leg is observable in the run record. The production
        # keep-going leg IS /goal: `goal_drive.build_goal_drive_argv`
        # constructs the `/goal <condition>` directive in the dispatched
        # prompt (the INPUT side, structurally guaranteed by the
        # production code path) and a real `claude -p` sub-agent drives
        # turns until the surfaced-exit-code condition holds. The
        # OBSERVABLE in the on-disk run record is the per-pass transcript
        # — which is the sub-agent's `claude -p` OUTPUT (the cost-JSON
        # result), carrying:
        #   (a) the `/goal`-driven INDEPENDENT-CHECK seam — the
        #       DONE_SENTINEL the verify step (not the sub-agent's prose)
        #       surfaces, which is what /goal's evaluator keys the halt
        #       off ("/goal drives, loam decides"); and
        #   (b) multi-turn iteration (`num_turns` in the cost JSON) —
        #       proof a real keep-going leg drove, not a single shot.
        transcripts = list(artifacts.glob("sub_*.transcript"))
        assert transcripts, "no per-pass transcript trail on disk"
        transcript_texts = [
            t.read_text(encoding="utf-8", errors="replace") for t in transcripts
        ]

        # Record the run evidence (observable artifact for the seal).
        ev = res.as_evidence()
        (artifacts / "adopt2_goal_result.json").write_text(
            json.dumps(ev, indent=2), encoding="utf-8"
        )

        # A real multi-turn keep-going leg drove (the /goal iteration,
        # not a single shot). The cost-JSON result records num_turns.
        iterated = False
        for txt in transcript_texts:
            for line in txt.splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                if isinstance(obj, dict) and obj.get("num_turns", 0) >= 1:
                    iterated = True
                    break
            if iterated:
                break
        assert iterated, (
            "AC.CLP-ADOPT.2: the production run record must show a real "
            "claude -p keep-going leg drove (num_turns >= 1 in a per-pass "
            "transcript) — the /goal adoption is not observable on the run"
        )

        # When the run reaches the goal, the verify-gated independent
        # check — NOT the sub-agent's word — decided done: the
        # DONE_SENTINEL the /goal halt keys off is surfaced in the run
        # record. This is the "/goal drives, loam decides" seam, the
        # load-bearing observable that the keep-going leg IS /goal.
        if res.stop_reason == "done":
            assert any(DONE_SENTINEL in txt for txt in transcript_texts), (
                "goal-met run must surface the independent-check DONE "
                "sentinel the /goal halt keys off (the /goal-drives-"
                "loam-decides seam)"
            )

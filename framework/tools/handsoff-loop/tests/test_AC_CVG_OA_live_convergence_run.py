"""AC.CVG.OA (outcome-altitude: true) — live convergence run (S4).

Through the production convergence entry point on a fresh workspace
with NO pre-arranged state, a real build leg (real spawn-isolated
sub-agent, /goal-driven) runs to a terminal that is gate-pass or
definite honest negative, with the full iteration trail on disk
(refine log + per-pass transcripts) and the no-retry-on-timeout
evidence recorded.

The seeded-first-check-fails convergence shape is pinned
deterministically in AC.CVG.1's test (seeding a failure is
pre-arranged state by definition, so the OA run cannot carry it);
the full-altitude first-check-fails evidence also recurs naturally
in every S6 run (no tool exists at run start).

Live-model test, env-gated: set BFI_REAL_CLAUDE=1 to run (one real
sub-agent build, minutes-class).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.convergence import run_to_convergence  # noqa: E402
from handsoff_loop.orchestrator import SubTask  # noqa: E402
from handsoff_loop.verify import freeze_acceptance  # noqa: E402


@pytest.mark.skipif(
    os.environ.get("BFI_REAL_CLAUDE") != "1",
    reason="live sub-agent build; set BFI_REAL_CLAUDE=1 to run",
)
def test_live_convergence_terminal_with_iteration_trail_on_disk():
    with tempfile.TemporaryDirectory(prefix="bfi-oa-cvg-") as root:
        root = Path(root)
        work = root / "work"
        artifacts = root / "artifacts"
        work.mkdir()
        frozen = freeze_acceptance(
            acceptance_id="oa-cvg",
            content=("counts.py prints the number of lines of its "
                     "input file"),
            check_argv=["/bin/sh", "-c",
                        "printf 'a\\nb\\nc\\n' > _in.txt && "
                        "test \"$(python3 counts.py _in.txt)\" = 3"],
            freeze_dir=root / "_frozen",
        )
        res = run_to_convergence(
            objective=("a tiny command counts.py that prints how many "
                       "lines its input file has"),
            sub_tasks=[SubTask(
                name="build-counts",
                brief=("In the current directory create counts.py: "
                       "`python3 counts.py <file>` prints exactly the "
                       "number of lines in <file> (just the integer, "
                       "newline-terminated)."),
                tighter_acceptance="counts.py exists and prints the "
                                   "line count of a sample file",
                check_command=("test -f counts.py && printf 'x\\ny\\n' "
                               "> _t.txt && test \"$(python3 counts.py "
                               "_t.txt)\" = 2"),
            )],
            frozen=frozen,
            work_dir=work,
            artifact_dir=artifacts,
            leg_ceiling_s=1200,
            max_refine_attempts=2,
            behavioral_done=False,
        )
        # Terminal is one of the two honest terminals; never a softened
        # in-between, and the no-retry evidence is recorded either way.
        assert res.stop_reason in ("done", "attempt-bound",
                                   "leg-timeout")
        assert res.timeout_retries == 0
        # Full iteration trail on disk: per-pass transcripts + the
        # verify-gated refine log in evidence.
        transcripts = list(artifacts.glob("sub_*.transcript"))
        assert transcripts, "no per-pass transcript trail on disk"
        assert (artifacts / "final_verify.json").exists() or res.timed_out
        ev = res.as_evidence()
        if not res.timed_out:
            assert ev["refine_log"], "no verify-gated iteration log"
            assert all(e["gated_on"] == "independent-verify"
                       for e in ev["refine_log"])
        (artifacts / "oa_cvg_result.json").write_text(
            json.dumps(ev, indent=2), encoding="utf-8")

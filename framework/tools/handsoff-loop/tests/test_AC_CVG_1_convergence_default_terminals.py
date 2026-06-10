"""AC.CVG.1 — convergence is the default; two terminals only (S4).

  * the build leg iterates toward the frozen gate as DEFAULT behavior
    (the bounded re-drive is on unless a caller narrows it: the
    convergence entry's default refine bound is > 0);
  * a failed check re-drives bounded refinement carrying the failure
    context;
  * gate-pass and definite honest negative are the only terminals;
    every iteration is gated on the independent verify (never a
    self-report) — no retry-to-green path exists.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.convergence import (  # noqa: E402
    DEFAULT_MAX_REFINE_ATTEMPTS,
    run_to_convergence,
)
from handsoff_loop.orchestrator import (  # noqa: E402
    SubTask,
    clear_swarm_in_session_dispatcher,
    set_swarm_in_session_dispatcher,
)
from handsoff_loop.verify import freeze_acceptance  # noqa: E402


def _frozen(tmp_path, artifact="out.txt"):
    return freeze_acceptance(
        acceptance_id="t",
        content="the artifact exists with the right content",
        check_argv=["/bin/sh", "-c",
                    f"grep -q converged {tmp_path}/work/{artifact}"],
        freeze_dir=tmp_path / "_frozen",
    )


def test_redrive_is_on_by_default_and_converges_on_failure_context():
    assert DEFAULT_MAX_REFINE_ATTEMPTS > 0


def test_failed_check_redrives_then_gate_pass_terminal(tmp_path):
    (tmp_path / "work").mkdir()
    calls = []

    def _dispatcher(prompt, *, timeout):
        calls.append(prompt)
        # First pass builds the wrong content; the re-drive (which
        # carries the failure context) fixes it.
        out = tmp_path / "work" / "out.txt"
        if len(calls) == 1:
            out.write_text("wrong\n", encoding="utf-8")
        else:
            assert "PRIOR ATTEMPT DID NOT PASS" in prompt  # context carried
            out.write_text("converged\n", encoding="utf-8")
        return "transcript"

    set_swarm_in_session_dispatcher(_dispatcher)
    try:
        res = run_to_convergence(
            objective="make out.txt converged",
            sub_tasks=[SubTask(name="t", brief="build it",
                               tighter_acceptance="ok",
                               check_command="true")],
            frozen=_frozen(tmp_path),
            work_dir=tmp_path / "work",
            artifact_dir=tmp_path / "artifacts",
            behavioral_done=False,
        )
    finally:
        clear_swarm_in_session_dispatcher()
    assert res.reached_done is True
    assert res.stop_reason == "done"
    assert len(calls) == 2  # one pass + one bounded re-drive
    # Every iteration was gated on the independent verify.
    assert all(e["gated_on"] == "independent-verify"
               for e in res.result.refine_log)


def test_bound_exhaustion_is_definite_honest_negative(tmp_path):
    (tmp_path / "work").mkdir()
    calls = []

    def _never_right(prompt, *, timeout):
        calls.append(prompt)
        (tmp_path / "work" / "out.txt").write_text("wrong\n",
                                                   encoding="utf-8")
        return "transcript"

    set_swarm_in_session_dispatcher(_never_right)
    try:
        res = run_to_convergence(
            objective="make out.txt converged",
            sub_tasks=[SubTask(name="t", brief="build it",
                               tighter_acceptance="ok",
                               check_command="true")],
            frozen=_frozen(tmp_path),
            work_dir=tmp_path / "work",
            artifact_dir=tmp_path / "artifacts",
            max_refine_attempts=2,
            behavioral_done=False,
        )
    finally:
        clear_swarm_in_session_dispatcher()
    # The honest negative is terminal and named — never softened,
    # never retried-to-green past the bound.
    assert res.reached_done is False
    assert res.stop_reason == "attempt-bound"
    assert len(calls) == 3  # pass 0 + the 2 bounded re-drives, no more

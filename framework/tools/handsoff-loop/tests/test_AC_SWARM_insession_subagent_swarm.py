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

"""AC.SWARM.* — Slice 2 of the in-session-subagent-migration minor.

The handsoff-loop swarm core's LEAF dispatch (`orchestrator._dispatch_subagent`)
is converted from a detached `claude -p` subprocess to an IN-SESSION subagent
dispatched through a host-session-registered dispatcher callable
(`set_swarm_in_session_dispatcher`), so the swarm draws from the subscription
plan limits instead of the post-June-15 metered Agent SDK credit. The decompose
-> dispatch -> independent-judge -> frozen-verify spine is byte-behaviour-
equivalent — only the per-sub-task spawn primitive changes.

Per `docs/plans/claude-p-to-insession-subagent-fanout-slice2-swarm.md` §5:

  - AC.SWARM.1 — the swarm leaf dispatch no longer spawns a detached
    `claude -p` subprocess + yields a usable per-sub-task result.
  - AC.SWARM.2 — dispatch-ordering semantics preserved (no silent re-
    serialization or re-ordering). RE-SCOPED from the parent plan's "full
    parallelism": the spine is verifiably SEQUENTIAL today (SAL-2); the swap is
    dispatch-for-dispatch equivalent, not a swarm-shape change.
  - AC.SWARM.3 — the independent-judge honesty controls are intact across the
    swap (frozen-acceptance isolation + independent-verify gate + bounded
    re-drive unchanged).
  - AC.SWARM.4 (outcome-altitude) — a converted run over a REAL objective with a
    real on-disk verify check reports honest `cost_usd=None` + a definite verdict
    + `human_loop_driving=False`, walked with no pre-arranged transcript state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import orchestrator as orch  # noqa: E402
from handsoff_loop.goal_drive import DONE_SENTINEL  # noqa: E402
from handsoff_loop.orchestrator import (  # noqa: E402
    SubTask,
    clear_swarm_in_session_dispatcher,
    get_swarm_in_session_dispatcher,
    run_handsoff_loop,
    set_swarm_in_session_dispatcher,
)
from handsoff_loop.verify import (  # noqa: E402
    FrozenAcceptance,
    VerifyResult,
    freeze_acceptance,
)


def _frozen() -> FrozenAcceptance:
    return FrozenAcceptance(
        acceptance_id="swarm",
        content="frozen-graded-acceptance-never-in-any-brief",
        content_sha256="x",
        check_argv=["true"],
    )


def _subtasks(n: int) -> list[SubTask]:
    return [
        SubTask(
            name=f"t{i}",
            brief=f"do thing {i}",
            tighter_acceptance=f"thing {i} done",
            check_command="placeholder",
        )
        for i in range(n)
    ]


@pytest.fixture(autouse=True)
def _clean_dispatcher():
    """Hygiene: the swarm dispatcher registry is process-global; clear it."""
    clear_swarm_in_session_dispatcher()
    yield
    clear_swarm_in_session_dispatcher()


# ============================================================================
# AC.SWARM.1 — the leaf dispatch takes the in-session subagent path, no
#              detached `claude -p` subprocess, usable per-sub-task result.
# ============================================================================


def test_AC_SWARM_1_production_default_is_in_session_not_claude_p(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.1 — with a swarm in-session dispatcher wired, a run over >=2
    sub-tasks dispatches each via the in-session path and NEVER spawns a detached
    `claude -p` subprocess. The subprocess spawn surface is booby-trapped: any
    spawn fails the test loudly."""
    dispatched: list[str] = []

    def fake_dispatch(prompt: str, *, timeout: int) -> str:
        dispatched.append(prompt)
        # A transcript carrying the DONE sentinel (the same text the residual
        # `-p` path's stdout would carry — DONE detection is unchanged).
        return f"in-session subagent ran\n{DONE_SENTINEL}\n"

    set_swarm_in_session_dispatcher(fake_dispatch)

    # Booby-trap the detached-spawn surface: the in-session path must NOT touch
    # subprocess.run in orchestrator (no detached `claude -p`).
    def _explode_run(*a, **k):  # pragma: no cover - must not be hit
        raise AssertionError(
            "AC.SWARM.1 violated: the swarm leaf dispatch spawned a subprocess "
            "(detached `claude -p`) instead of fanning out an in-session subagent."
        )

    monkeypatch.setattr(orch.subprocess, "run", _explode_run, raising=True)
    # The independent verify is the spine's decision point, not under test here;
    # keep it deterministic so this exercises ONLY the leaf-dispatch swap.
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            True, 0, None, "ok", "", "swarm", "x"),
    )

    r = run_handsoff_loop(
        objective="o", sub_tasks=_subtasks(2), frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
    )

    # Each of the 2 sub-tasks dispatched via the in-session path; a usable
    # per-sub-task result (the self-report-done flag came off the transcript).
    assert len(dispatched) == 2
    assert len(r.sub_task_results) == 2
    assert all(sr["self_report_done"] for sr in r.sub_task_results)
    assert r.reached_done is True


def test_AC_SWARM_1_in_session_dispatch_carries_goal_driven_prompt(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.1 — the in-session dispatch carries the SAME `/goal`-driven
    sub-task prompt the residual path would build (the leaf work is unchanged;
    only the spawn primitive differs)."""
    dispatched: list[str] = []

    def fake_dispatch(prompt: str, *, timeout: int) -> str:
        dispatched.append(prompt)
        return f"{DONE_SENTINEL}\n"

    set_swarm_in_session_dispatcher(fake_dispatch)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(True, 0, None, "ok", "", "swarm", "x"),
    )
    run_handsoff_loop(
        objective="ship a parser", sub_tasks=_subtasks(1), frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
    )
    assert len(dispatched) == 1
    prompt = dispatched[0]
    # The /goal drive leg + the surfaced-exit-code completion seam are present
    # in the dispatched prompt (the residual path builds the identical prompt).
    assert "/goal" in prompt
    assert DONE_SENTINEL in prompt
    assert "ship a parser" in prompt  # the objective threaded into the directive


# ============================================================================
# AC.SWARM.2 — dispatch-ordering semantics preserved (no silent re-
#              serialization / re-ordering / collapse / drop). SAL-2.
# ============================================================================


def test_AC_SWARM_2_dispatch_ordering_and_cardinality_preserved(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.2 — N sub-tasks produce EXACTLY N in-session dispatches, in
    sub_tasks order. The swap does not collapse N into one, re-order, or drop a
    sub-task (it is dispatch-for-dispatch equivalent to the sealed spine)."""
    seen_order: list[str] = []

    def fake_dispatch(prompt: str, *, timeout: int) -> str:
        # Recover the sub-task name from the directive ("Scoped sub-task <name>").
        import re
        m = re.search(r"Scoped sub-task (\S+) of objective", prompt)
        seen_order.append(m.group(1) if m else "?")
        return f"{DONE_SENTINEL}\n"

    set_swarm_in_session_dispatcher(fake_dispatch)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(True, 0, None, "ok", "", "swarm", "x"),
    )
    run_handsoff_loop(
        objective="o", sub_tasks=_subtasks(3), frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
    )
    # Exactly N dispatches (cardinality), in declared order (no re-ordering /
    # collapse / drop).
    assert seen_order == ["t0", "t1", "t2"]


# ============================================================================
# AC.SWARM.3 — the independent-judge honesty controls are intact across the
#              swap (frozen isolation + independent-verify gate + bounded
#              re-drive). The spine is byte-behaviour-equivalent.
# ============================================================================


def test_AC_SWARM_3_done_decided_by_independent_verify_not_self_report(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.3 — even when every in-session subagent SELF-REPORTS done (the
    DONE sentinel in its transcript), the run's `reached_done` is decided by the
    INDEPENDENT verify (here forced NOT-done), never the self-report."""

    def fake_dispatch(prompt: str, *, timeout: int) -> str:
        return f"I totally finished\n{DONE_SENTINEL}\n"  # self-report DONE

    set_swarm_in_session_dispatcher(fake_dispatch)
    # Independent verify says NOT done — the gate that decides.
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "expected X got Y", "", "swarm", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=_subtasks(2), frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
    )
    # Sub-agents self-reported done, but the independent verify governs.
    assert all(sr["self_report_done"] for sr in r.sub_task_results)
    assert r.reached_done is False  # honest negative — self-report NOT trusted
    # The honesty gate is observable in the refine log.
    assert r.refine_log[0]["gated_on"] == "independent-verify"


def test_AC_SWARM_3_frozen_acceptance_isolation_still_holds(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.3 — frozen-acceptance isolation survives the swap: a brief that
    leaks the frozen acceptance body still raises (the in-session path does not
    weaken the freeze-isolation guard)."""
    set_swarm_in_session_dispatcher(
        lambda prompt, *, timeout: f"{DONE_SENTINEL}\n"
    )
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(True, 0, None, "ok", "", "swarm", "x"),
    )
    leaky = SubTask(
        name="leak",
        # The brief leaks the frozen acceptance body — must be refused.
        brief="frozen-graded-acceptance-never-in-any-brief",
        tighter_acceptance="x",
        check_command="placeholder",
    )
    from handsoff_loop.verify import FreezeIsolationBreach
    with pytest.raises(FreezeIsolationBreach):
        run_handsoff_loop(
            objective="o", sub_tasks=[leaky], frozen=_frozen(),
            work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        )


def test_AC_SWARM_3_bounded_redrive_still_verification_gated(
    tmp_path, monkeypatch,
) -> None:
    """AC.SWARM.3 — the bounded verification-gated re-drive is unchanged across
    the swap: a persistent NOT-done re-drives EXACTLY the bound through the
    in-session path, advancing only on the independent verify (anti-erosion)."""
    dispatched: list[str] = []

    def fake_dispatch(prompt: str, *, timeout: int) -> str:
        dispatched.append(prompt)
        return f"{DONE_SENTINEL}\n"

    set_swarm_in_session_dispatcher(fake_dispatch)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "still wrong", "", "swarm", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=_subtasks(1), frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=2,
    )
    # pass 0 + exactly 2 bounded re-drives = 3 in-session dispatches; bound HELD.
    assert len(dispatched) == 3
    assert r.refine_attempts == 2
    assert r.refine_bound == 2
    assert r.refine_stop_reason == "attempt-bound"
    assert r.reached_done is False
    # Every iteration gated on the independent verify (anti-erosion observable).
    assert all(e["gated_on"] == "independent-verify" for e in r.refine_log)


# ============================================================================
# AC.SWARM.4 (outcome-altitude) — a REAL converted run over a real objective
#             with a real on-disk verify check: honest cost_usd=None + a
#             definite verdict + human_loop_driving=False, no pre-arranged
#             transcript state.
# ============================================================================


def test_AC_SWARM_4_real_run_reports_honest_cost_none_and_definite_verdict(
    tmp_path,
) -> None:
    """★ AC.SWARM.4 (outcome-altitude) — walked with NO pre-arranged transcript
    state: the production `run_handsoff_loop` entry point, driven through the
    registered in-session dispatcher, where the dispatcher does REAL work (writes
    the artefact the objective describes) and loam's REAL independent verify
    (`freeze_acceptance` + a real on-disk shell check, NOT monkeypatched) decides
    done. The converted leaf dispatch reports an honest `cost_usd=None`
    (measurement-gap — no `-p` JSON envelope to fabricate a cost from), the run
    reaches a DEFINITE verdict, and no human drove the loop."""
    work_dir = tmp_path / "wd"
    work_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = tmp_path / "ad"
    freeze_dir = tmp_path / "frozen"

    target = work_dir / "built.txt"

    # The in-session dispatcher does REAL work: it writes the artefact the
    # objective describes (mirrors what a real Task-primitive subagent would do,
    # without a `claude -p` subprocess). No pre-arranged transcript exists.
    def real_dispatch(prompt: str, *, timeout: int) -> str:
        target.write_text("BUILT", encoding="utf-8")
        return f"wrote the artefact\n{DONE_SENTINEL}\n"

    set_swarm_in_session_dispatcher(real_dispatch)

    # A REAL frozen acceptance with a REAL on-disk independent check: the shell
    # check exits 0 iff the artefact the dispatcher was asked to build exists
    # with the expected content. NOT monkeypatched — the genuine verify spine.
    frozen = freeze_acceptance(
        acceptance_id="swarm-real",
        content="built.txt exists and contains BUILT",
        check_argv=[
            "sh", "-c",
            f'test "$(cat {target})" = "BUILT"',
        ],
        freeze_dir=freeze_dir,
    )

    result = run_handsoff_loop(
        objective="create built.txt containing the word BUILT",
        sub_tasks=[
            SubTask(
                name="build",
                brief="produce the artefact the objective describes",
                tighter_acceptance="built.txt exists with the right content",
                check_command="placeholder",
            )
        ],
        frozen=frozen,
        work_dir=work_dir,
        artifact_dir=artifact_dir,
    )

    # Outcome-altitude assertions on the REAL production result:
    #  (a) honest cost-None on the converted (in-session) leaf dispatch.
    assert all(sr["cost_usd"] is None for sr in result.sub_task_results)
    assert result.cost_usd is None
    #  (b) a DEFINITE verdict from the REAL independent verify (the dispatcher
    #      did the work, so the real on-disk check passes -> done).
    assert result.final_verify is not None
    assert result.reached_done is True
    assert result.final_verify.primary_exit == 0
    #  (c) no human drove the loop.
    assert result.human_loop_driving is False
    # The artefact was really produced (no pre-arranged state).
    assert target.read_text() == "BUILT"
    # And the registered dispatcher really was the in-session path.
    assert get_swarm_in_session_dispatcher() is real_dispatch

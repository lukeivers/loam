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

"""AC.BRC.2 — a failed behavioural check RE-DRIVES a BOUNDED number of
refine attempts carrying the failure context.

Outcome under test (not method): on a NOT-done independent verify the
loop does NOT terminate at the first failure — it re-dispatches a
sub-agent again, CARRYING the surfaced behavioural-failure context,
for a BOUNDED finite number of attempts (an explicit attempt count
AND the existing cost/wall ceiling, whichever binds first).  A
single-pass dispatch with no re-drive does NOT satisfy this AC; an
unbounded re-drive does NOT satisfy it either.  Deterministic: the
real `claude` sub-agent dispatch and the real verify are monkeypatched
so this exercises ONLY the orchestrator control-flow (no spawn).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import orchestrator as orch  # noqa: E402
from handsoff_loop.orchestrator import (  # noqa: E402
    SubTask,
    run_handsoff_loop,
)
from handsoff_loop.verify import (  # noqa: E402
    FrozenAcceptance,
    VerifyResult,
)


def _frozen() -> FrozenAcceptance:
    return FrozenAcceptance(
        acceptance_id="brc2",
        content="frozen-graded-acceptance-never-in-any-brief",
        content_sha256="x",
        check_argv=["true"],
    )


def _subtask() -> SubTask:
    return SubTask(
        name="t", brief="do the thing",
        tighter_acceptance="the thing is done",
        check_command="placeholder",
    )


def _patch_dispatch(monkeypatch, sink: list[str]) -> None:
    def fake_dispatch(spec, *, work_dir, timeout):
        sink.append(spec.directive)
        return ("transcript\n", 1.0, 0.01)

    monkeypatch.setattr(orch, "_dispatch_subagent", fake_dispatch)


def test_AC_BRC_2_single_pass_when_no_redrive_requested(
    tmp_path, monkeypatch,
) -> None:
    """max_refine_attempts=0 -> exactly ONE pass (byte-behaviour-
    unchanged for every pre-existing caller)."""
    sink: list[str] = []
    _patch_dispatch(monkeypatch, sink)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "expected X got Y", "", "brc2", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=0,
    )
    assert len(sink) == 1
    assert r.refine_attempts == 0
    assert r.reached_done is False  # honest negative, not retried


def test_AC_BRC_2_failed_check_redrives_bounded(
    tmp_path, monkeypatch,
) -> None:
    """Persistent NOT-done -> re-drive EXACTLY the bound, then stop
    with an honest-negative (bound HELD, never exceeded)."""
    sink: list[str] = []
    _patch_dispatch(monkeypatch, sink)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "expected RIGHT got WRONG", "",
            "brc2", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=3,
    )
    # pass 0 + exactly 3 bounded re-drives = 4 dispatches; NOT
    # single-pass and NOT unbounded.
    assert len(sink) == 4
    assert r.refine_attempts == 3
    assert r.refine_bound == 3
    assert r.refine_stop_reason == "attempt-bound"
    assert r.reached_done is False  # honest negative, not retried


def test_AC_BRC_2_redrive_carries_failure_context(
    tmp_path, monkeypatch,
) -> None:
    """The re-dispatch brief CARRIES the surfaced behavioural-failure
    context (what was expected vs what the artefact did)."""
    sink: list[str] = []
    _patch_dispatch(monkeypatch, sink)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 7, None,
            "EXPECTED stdout RIGHT, GOT stdout WRONG", "",
            "brc2", "x"),
    )
    run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=1,
    )
    redrive_brief = sink[1]  # the first re-drive's directive
    assert "DID NOT PASS THE BEHAVIOURAL SELF-CHECK" in redrive_brief
    assert "EXPECTED stdout RIGHT, GOT stdout WRONG" in redrive_brief
    assert "primary exit 7" in redrive_brief


def test_AC_BRC_2_cost_ceiling_binds_before_attempt_bound(
    tmp_path, monkeypatch,
) -> None:
    """The bound is attempts AND the existing cost ceiling, whichever
    binds FIRST — a high attempt cap does not mean unbounded burn."""
    sink: list[str] = []

    def fake_dispatch(spec, *, work_dir, timeout):
        sink.append(spec.directive)
        return ("t\n", 1.0, 5.0)  # $5/pass

    monkeypatch.setattr(orch, "_dispatch_subagent", fake_dispatch)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "still wrong", "", "brc2", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=100, cost_ceiling_usd=12.0,
    )
    # pass0=$5, r1=$10, then $10>=12 is false so r2 runs ($15),
    # ceiling trips BEFORE the 100-attempt cap. The point: a finite
    # bound stopped it; it is NOT unbounded.
    assert r.refine_stop_reason == "cost-ceiling"
    assert r.refine_attempts < 100
    assert r.reached_done is False


def test_AC_BRC_2_done_on_redrive_stops_early(
    tmp_path, monkeypatch,
) -> None:
    """A re-drive that produces a passing behavioural verify stops the
    cycle (it iterated TOWARD a working outcome, not blindly)."""
    sink: list[str] = []
    _patch_dispatch(monkeypatch, sink)
    calls = {"n": 0}

    def verify_then_pass(*a, **k):
        calls["n"] += 1
        done = calls["n"] >= 2  # fail pass0, pass on re-drive 1
        return VerifyResult(
            done, 0 if done else 1, None,
            "ok" if done else "wrong", "", "brc2", "x")

    monkeypatch.setattr(orch, "verify", verify_then_pass)
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=5,
    )
    assert r.reached_done is True
    assert r.refine_attempts == 1
    assert r.refine_stop_reason == "done"
    assert len(sink) == 2  # stopped early, did not burn the bound

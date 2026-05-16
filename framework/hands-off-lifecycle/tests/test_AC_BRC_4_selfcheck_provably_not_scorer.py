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

"""AC.BRC.4 — the behavioural self-check is the loop's OWN self-
constructed check, PROVABLY NOT the graded scorer / independent judge
/ intake judge.

Outcome under test (not method): the behavioural-self-check construct
is provably distinct from (a) the graded benchmark scorer (the real
upstream `programbench eval`), (b) the independent held-out
adversarial judge, (c) the loop's own intake faithfulness judge
(`intake._judge_faithful`); and the frozen-graded `assert_unseen_by`
freeze-isolation spine is preserved on the behaviouralised briefs.
The isolation is proved STRUCTURALLY (an AST/import assertion on the
construct module + a freeze-isolation behaviour assertion), not
asserted in prose — a self-check that IS / calls / imports the scorer
or judge does NOT satisfy this AC.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HANDSOFF_SRC = ROOT / "framework" / "tools" / "handsoff-loop" / "src"
sys.path.insert(0, str(HANDSOFF_SRC))

MODULE = (
    HANDSOFF_SRC / "handsoff_loop" / "behavioral_selfcheck.py"
)

# Substrings that would indicate the self-check imported the EXTERNAL
# scoring authority / a judge — the AC.RPB.1-class freeze isolation
# would be destroyed.
_FORBIDDEN_IMPORT_TOKENS = (
    "verify",            # the frozen graded independent authority
    "scorer",            # the benchmark scorer
    "judge",             # the independent held-out / intake judge
    "intake",            # intake._judge_faithful
    "structural_floor",  # the realpb floor (the external floor)
    "programbench",      # the real upstream eval
    "reharden",          # the independent re-harden judge runner
)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
        elif isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
    return mods


def test_AC_BRC_4_construct_imports_no_scorer_or_judge() -> None:
    """The construct module imports NEITHER verify NOR any scorer /
    judge / intake module — provable by AST, not prose."""
    assert MODULE.exists(), f"construct module missing: {MODULE}"
    mods = _imported_modules(MODULE)
    for m in mods:
        low = m.lower()
        for bad in _FORBIDDEN_IMPORT_TOKENS:
            assert bad not in low, (
                f"behavioral_selfcheck.py imports {m!r} containing "
                f"{bad!r} — the loop's OWN self-check must be "
                f"PROVABLY NOT the graded scorer/judge (AC.BRC.4)"
            )
    # Positive: it only leans on the existing /goal sentinel seam.
    assert any(m == "goal_drive" for m in mods), (
        "the construct should compose the existing /goal sentinel "
        "seam (Lens 1), not re-implement a judge"
    )


def test_AC_BRC_4_construct_does_not_consume_frozen_acceptance(
) -> None:
    """The construct produces only a command string + a directive
    from the plain-language objective; it has no parameter / field
    that could carry the frozen graded acceptance."""
    from handsoff_loop.behavioral_selfcheck import (
        BehavioralCheckSpec,
        build_behavioral_check_command,
    )

    spec = build_behavioral_check_command(
        objective="the user's plain sentence", work_dir="/wd")
    assert isinstance(spec, BehavioralCheckSpec)
    fields = set(spec.__dataclass_fields__)
    assert fields == {
        "objective", "work_dir", "reference_artifact"
    }, (
        "BehavioralCheckSpec must NOT have a field that could carry "
        "the frozen graded acceptance / held-out inputs (AC.BRC.4)"
    )
    # The command never names the frozen graded check / held-out path.
    cmd = spec.command()
    for bad in ("held_out", "structural_floor", "programbench",
                "frozen"):
        assert bad not in cmd


def test_AC_BRC_4_freeze_isolation_preserved_on_behavioralised(
    tmp_path, monkeypatch,
) -> None:
    """The behaviouralised briefs still pass FrozenAcceptance.
    assert_unseen_by — i.e. behaviouralising the in-loop check did
    NOT leak the frozen graded acceptance into a brief (the Tier-0
    honesty control survives)."""
    from handsoff_loop import orchestrator as orch
    from handsoff_loop.orchestrator import SubTask, run_handsoff_loop
    from handsoff_loop.verify import FrozenAcceptance, VerifyResult

    frozen = FrozenAcceptance(
        acceptance_id="brc4",
        content="SECRET-FROZEN-GRADED-ACCEPTANCE-BODY",
        content_sha256="x",
        check_argv=["true"],
    )
    seen_briefs: list[str] = []

    def capture_dispatch(spec, *, work_dir, timeout):
        seen_briefs.append(spec.directive)
        return ("t\n", 1.0, 0.0)

    monkeypatch.setattr(orch, "_dispatch_subagent", capture_dispatch)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            True, 0, None, "ok", "", "brc4", "x"),
    )
    run_handsoff_loop(
        objective="produce X that behaves like Y",
        sub_tasks=[SubTask(
            name="t", brief="do it",
            tighter_acceptance="done",
            check_command="placeholder")],
        frozen=frozen,
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        behavioral_done=True,
    )
    # The behaviouralised brief was dispatched AND it does not
    # contain the frozen graded acceptance body (assert_unseen_by
    # would have raised inside run_handsoff_loop otherwise).
    assert seen_briefs, "no brief dispatched"
    for b in seen_briefs:
        assert "SECRET-FROZEN-GRADED-ACCEPTANCE-BODY" not in b


def test_AC_BRC_4_leaked_frozen_into_behavioralised_brief_refuses(
    tmp_path, monkeypatch,
) -> None:
    """If the frozen graded acceptance body WERE present in a brief,
    behaviouralising must not paper over it — assert_unseen_by still
    refuses (the freeze-isolation guard is preserved, not bypassed)."""
    from handsoff_loop.orchestrator import SubTask, run_handsoff_loop
    from handsoff_loop.verify import (
        FreezeIsolationBreach,
        FrozenAcceptance,
    )

    frozen = FrozenAcceptance(
        acceptance_id="brc4b",
        content="LEAKED-FROZEN-BODY",
        content_sha256="x",
        check_argv=["true"],
    )
    with pytest.raises(FreezeIsolationBreach):
        run_handsoff_loop(
            objective="o",
            sub_tasks=[SubTask(
                name="t",
                brief="do it; LEAKED-FROZEN-BODY is the answer",
                tighter_acceptance="done",
                check_command="placeholder")],
            frozen=frozen,
            work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
            behavioral_done=True,
        )

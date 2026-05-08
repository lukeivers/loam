"""D5 cross-session — partial ratification batch resumable across
fresh-process boundary.

Simulates the `/clear` analog: enqueue batch in one "process" (the
test); construct a fresh PMRuntime + load ratification-state.yaml in
a "second process" (a fresh subprocess invocation); verify state is
visible.

Per plan-doc §6 D5.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import yaml

from loam.per_project_pm import PMRuntime
from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    enqueue_ratification_batch,
    load_ratification_state,
)
from loam_odd_extractor.state import extraction_dir


_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _author_pm(workspace_root: Path, pm_name: str) -> None:
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
                "project_name": "test",
                "project_kind": "general",
                "owner_name": "Tester",
                "workspace_root": str(workspace_root),
                "decision_surfacing_policy": {
                    "onboarding_mode": False,
                    "max_questions_per_turn": 1,
                    "cool_down_seconds": 0,
                    "require_owner_response": False,
                },
            }
        )
    )


def test_ratification_state_persists_across_fresh_load(
    tmp_path: Path,
) -> None:
    """A fresh load of ratification-state.yaml from a brand-new
    PMRuntime + load_ratification_state call surfaces all the prior
    state."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "resume-pm"
    _author_pm(ws, pm_name)

    pm_runtime_a = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = [
        BandedAC(
            ac_id=f"AC.RX.{i}",
            text=f"AC text {i}",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale=f"rationale {i}",
            ),
        )
        for i in range(1, 4)
    ]
    extraction_id = "resume-test-extraction"
    enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime_a,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    # First "process" surfaces one question.
    pm_runtime_a.surface_next_questions_batch(n=1)

    # New "process" — fresh PMRuntime instance + fresh state load.
    pm_runtime_b = PMRuntime.from_workspace(ws, pm_name)
    sw = pm_runtime_b.state_of_world()
    assert sw.queue_depth == 2  # one was surfaced

    # Ratification state still has all 3 in pending_acs (none of the
    # apply_ratification_action calls have run yet — the persona has
    # only surfaced, not applied).
    ext_dir = extraction_dir(ws, extraction_id)
    state = load_ratification_state(ext_dir)
    assert state is not None
    assert state.extraction_id == extraction_id
    assert set(state.pending_acs) == {"AC.RX.1", "AC.RX.2", "AC.RX.3"}
    assert state.completed_actions == []


def test_subprocess_can_read_ratification_state(
    tmp_path: Path,
) -> None:
    """A fresh subprocess invocation of Python loads the same state.

    This is the strict /clear analog — full process boundary, not
    just a fresh PMRuntime instance in the same process.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "subproc-pm"
    _author_pm(ws, pm_name)

    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = [
        BandedAC(
            ac_id="AC.SUBP.1",
            text="subproc test",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="x"),
        )
    ]
    extraction_id = "subproc-test"
    enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    # Subprocess reads ratification-state.yaml directly.
    script = textwrap.dedent(
        f"""
        import sys
        from pathlib import Path
        from loam_odd_extractor import load_ratification_state
        from loam_odd_extractor.state import extraction_dir

        ws = Path({str(ws)!r})
        ext_dir = extraction_dir(ws, {extraction_id!r})
        state = load_ratification_state(ext_dir)
        if state is None:
            sys.exit(2)
        if state.extraction_id != {extraction_id!r}:
            sys.exit(3)
        if "AC.SUBP.1" not in state.pending_acs:
            sys.exit(4)
        sys.exit(0)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: rc={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_resume_continues_pending_after_partial(
    tmp_path: Path,
) -> None:
    """After applying one action, ratification-state shows 2 pending
    + 1 completed; a new enqueue against the same banded list is a
    no-op for the completed AC.
    """
    from loam_odd_extractor import (
        apply_ratification_action,
        promote,
    )

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "partial-pm"
    _author_pm(ws, pm_name)
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    banded_acs = [
        BandedAC(
            ac_id="AC.PA.1",
            text="A",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="x"),
        ),
        BandedAC(
            ac_id="AC.PA.2",
            text="B",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="y"),
        ),
        BandedAC(
            ac_id="AC.PA.3",
            text="C",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="z"),
        ),
    ]
    extraction_id = "partial-test"
    enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    # Apply one action.
    apply_ratification_action(
        promote(
            ac_id="AC.PA.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=extraction_id,
    )

    # Verify state.
    ext_dir = extraction_dir(ws, extraction_id)
    state = load_ratification_state(ext_dir)
    assert state is not None
    assert "AC.PA.1" not in state.pending_acs
    assert set(state.pending_acs) == {"AC.PA.2", "AC.PA.3"}
    assert len(state.completed_actions) == 1
    assert state.completed_actions[0].ac_id == "AC.PA.1"
    assert state.completed_actions[0].action_kind == "promote"

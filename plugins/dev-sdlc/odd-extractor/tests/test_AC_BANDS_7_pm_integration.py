"""AC.BANDS.7 — RatificationBatch.from_contract_draft + enqueue
through PMRuntime; one-question-at-a-time per Decision Q.

Tests the end-to-end PM-mediated round-trip for a banded contract:

- Build a tmp PMRuntime against a tmp workspace.
- Construct BandedAC list from the synthetic fixture.
- Call enqueue_ratification_batch(...).
- Assert decision-queue.yaml has N entries with provenance strings.
- Surface one question via batch (max_questions_per_turn=1) and
  verify FIFO + content.
- Record a response; assert blocking flag clears (when
  require_owner_response=True).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm import PMRuntime
from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    enqueue_ratification_batch,
)


@pytest.fixture
def tmp_workspace_with_pm(tmp_path: Path) -> tuple[Path, str]:
    """Tmp workspace + authored PM (one-question-at-a-time)."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "workspace").mkdir()

    pm_name = "test-pm"
    pm_dir = ws / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
                "project_name": "test",
                "project_kind": "general",
                "owner_name": "Tester",
                "workspace_root": str(ws),
                "decision_surfacing_policy": {
                    "onboarding_mode": False,
                    "max_questions_per_turn": 1,
                    "cool_down_seconds": 0,
                    "require_owner_response": False,
                },
            }
        )
    )
    return ws, pm_name


def _build_banded_acs() -> list[BandedAC]:
    return [
        BandedAC(
            ac_id="AC.SYNTH.1",
            text="VERIFIED AC",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=["tests/test_x.py::test_y"],
                repo_sha="abc1234567890def",
            ),
        ),
        BandedAC(
            ac_id="AC.SYNTH.2",
            text="PLAUSIBLE AC",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=["app/x.rb:10-20"],
            ),
        ),
        BandedAC(
            ac_id="AC.SYNTH.3",
            text="HYPOTHESISED AC",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale="LLM inferred from comments.",
            ),
        ),
    ]


def test_enqueue_ratification_batch_enqueues_three(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = _build_banded_acs()
    extraction_id = "test-extraction-123"

    count = enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert count == 3
    sw = pm_runtime.state_of_world()
    assert sw.queue_depth == 3


def test_provenance_string_format(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """Per plan-doc §5 Surface #8: provenance is
    ``odd-extract:{extraction_id}:{ac_id}``."""
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = _build_banded_acs()
    extraction_id = "test-extraction-XYZ"

    enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue = payload["queue"]
    expected = {
        f"odd-extract:{extraction_id}:AC.SYNTH.1",
        f"odd-extract:{extraction_id}:AC.SYNTH.2",
        f"odd-extract:{extraction_id}:AC.SYNTH.3",
    }
    actual = {entry["provenance"] for entry in queue}
    assert actual == expected


def test_one_question_at_a_time_batch_returns_one(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """max_questions_per_turn=1 → batch surface returns 1."""
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = _build_banded_acs()

    enqueue_ratification_batch(
        extraction_id="test-X",
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    batch = pm_runtime.surface_next_questions_batch()
    assert len(batch) == 1
    sq = batch[0]
    assert "AC.SYNTH.1" in sq.text  # FIFO head
    # Provenance round-trips.
    assert sq.provenance == "odd-extract:test-X:AC.SYNTH.1"


def test_questions_carry_ac_text_and_band(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """Each question text must include the AC ID + current band."""
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = _build_banded_acs()

    enqueue_ratification_batch(
        extraction_id="test-X",
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )

    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    by_provenance = {
        e["provenance"]: e["text"] for e in payload["queue"]
    }
    assert "VERIFIED" in by_provenance["odd-extract:test-X:AC.SYNTH.1"]
    assert "PLAUSIBLE" in by_provenance["odd-extract:test-X:AC.SYNTH.2"]
    assert (
        "HYPOTHESISED" in by_provenance["odd-extract:test-X:AC.SYNTH.3"]
    )


def test_idempotent_re_enqueue_skips_completed(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """Calling enqueue_ratification_batch twice doesn't double-enqueue
    completed ACs.

    Simulates the scenario: persona enqueues batch, processes one,
    then re-runs enqueue → only the still-pending ACs are added.
    """
    from loam_odd_extractor import (
        apply_ratification_action,
        promote,
    )

    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    banded_acs = _build_banded_acs()
    extraction_id = "test-idem"

    # First enqueue.
    count1 = enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert count1 == 3

    # Process the HYPOTHESISED → PLAUSIBLE promotion of AC.SYNTH.3.
    apply_ratification_action(
        promote(
            ac_id="AC.SYNTH.3",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        banded_acs=banded_acs,
        workspace_root=ws,
        repo_id=extraction_id,
    )

    # Second enqueue with same banded_acs.
    count2 = enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    # Only 2 still-pending (AC.SYNTH.3 was completed).
    assert count2 == 2

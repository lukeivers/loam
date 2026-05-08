"""Full pipeline e2e integration test (v0.2.3 Cycle 2).

Walks: enqueue → backing-map populate (stubbed) → surface → parse →
apply (PLAUSIBLE → VERIFIED) → audit-log present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from loam_odd_extractor import (
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    apply_objective_ratification_action,
    enqueue_objective_ratification_batch,
    parse_altitude_provenance,
    populate_backing_map,
    promote_objective,
)
from loam_odd_extractor.observability import list_entries


@pytest.fixture
def workspace_with_pm(tmp_path: Path) -> tuple[Path, str]:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "integration-pm"
    pm_dir = ws / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    contract = {
        "schema_version": 1,
        "handle": pm_name,
        "project_name": "integration",
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
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))
    return ws, pm_name


class _StubResp:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self.content = [type("B", (), {"text": json.dumps(payload)})()]
        self.usage = type(
            "U", (), {"input_tokens": 500, "output_tokens": 100}
        )()


class _StubClient:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self._resp = _StubResp(payload)
        self.messages = self

    def create(self, **kwargs: Any) -> _StubResp:
        return self._resp


def test_full_pipeline_end_to_end(
    workspace_with_pm: tuple[Path, str],
) -> None:
    from loam.per_project_pm import PMRuntime

    ws, pm_name = workspace_with_pm
    extraction_id = "integration-extraction"
    ext_dir = ws / ".loam" / "extractions" / extraction_id
    ext_dir.mkdir(parents=True)

    obj = Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal at scale",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
        domain="dispute",
    )
    rows = [
        {
            "ac_id": "route:src/disputeRoutes.js:42",
            "kind": "route",
            "path": "src/disputeRoutes.js",
            "symbol": "POST /dispute",
            "text": "POST handler for filing dispute",
            "line_range": [42, 47],
        },
    ]

    # 1. Populate backing-map.
    client = _StubClient(
        [
            {
                "objective_id": "O.dispute.1",
                "evidence_row_id": "route:src/disputeRoutes.js:42",
                "verdict": "STRONG",
                "rationale": "stub",
            }
        ]
    )
    bm = populate_backing_map(
        [obj],
        rows,
        extraction_id=extraction_id,
        anthropic_client=client,
        extraction_dir=ext_dir,
    )
    assert bm.entries[0].evidence_rows[0].confidence == "STRONG"

    # 2. Enqueue altitude-tagged ratification batch.
    pm = PMRuntime.from_workspace(ws, pm_name)
    enqueued = enqueue_objective_ratification_batch(
        extraction_id=extraction_id,
        objectives=[obj],
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert enqueued == 1

    # 3. Surface + parse provenance.
    batch = pm.surface_next_questions_batch()
    assert len(batch) == 1
    eid, altitude, target_id = parse_altitude_provenance(
        batch[0].provenance
    )
    assert altitude == "objective"
    assert target_id == "O.dispute.1"

    # 4. Apply PLAUSIBLE → VERIFIED with explicit_yes + STRONG backing.
    action = promote_objective(
        target_id=target_id,
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/disputeRoutes.js:42"],
    )
    out = apply_objective_ratification_action(
        action,
        objectives=[obj],
        backing_map=bm,
        workspace_root=ws,
        repo_id=extraction_id,
        pm_audit_path="audit-log/2026/05/04/0001.yaml",
    )
    assert out["objectives"][0].confidence is ConfidenceBand.VERIFIED

    # 5. Audit-log captures both backing_map_populated +
    # ratification_objective_promote.
    entries = list_entries(ext_dir)
    kinds = []
    for e in entries:
        kinds.append(yaml.safe_load(e.read_text(encoding="utf-8"))["event_kind"])
    assert "backing_map_populated" in kinds
    assert "ratification_objective_promote" in kinds


def test_v1_bandedac_integration_unchanged(
    workspace_with_pm: tuple[Path, str],
) -> None:
    """v0.1.8 BandedAC ratification path still operates end-to-end."""
    from loam.per_project_pm import PMRuntime
    from loam_odd_extractor import (
        BandedAC,
        Evidence,
        apply_ratification_action,
        enqueue_ratification_batch,
        promote,
    )

    ws, pm_name = workspace_with_pm
    pm = PMRuntime.from_workspace(ws, pm_name)
    banded = [
        BandedAC(
            ac_id="AC.LEG.1",
            text="legacy",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="r"),
        )
    ]
    enqueued = enqueue_ratification_batch(
        extraction_id="legacy",
        banded_acs=banded,
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert enqueued == 1

    out = apply_ratification_action(
        promote(
            ac_id="AC.LEG.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        banded_acs=banded,
        workspace_root=ws,
        repo_id="legacy",
    )
    assert out[0].confidence is ConfidenceBand.PLAUSIBLE

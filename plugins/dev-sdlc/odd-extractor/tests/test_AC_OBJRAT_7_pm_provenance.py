"""AC.OBJRAT.7 — PM-side altitude-tagging via provenance string.

- enqueue_objective_ratification_batch produces altitude-tagged
  provenance strings.
- PM-side decision-queue.yaml schema unchanged (provenance is free-
  form).
- parse_altitude_provenance round-trips altitude + target_id.
- Persona-side response router parses altitude.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor import (
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    Constraint,
    ConstraintEvidence,
    Objective,
    ObjectiveEvidence,
    enqueue_objective_ratification_batch,
    parse_altitude_provenance,
)


@pytest.fixture
def tmp_workspace_with_pm(tmp_path: Path) -> tuple[Path, str]:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "test-pm"
    pm_dir = ws / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    contract = {
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
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))
    return ws, pm_name


def _build_typed_lists() -> tuple[list[Objective], list[Constraint], list[Capability]]:
    objs = [
        Objective(
            objective_id="O.alpha.1",
            text="Operators see alpha outcome through the dashboard interface",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=ObjectiveEvidence(readme_excerpts=["alpha"]),
            domain="alpha",
        ),
    ]
    cons = [
        Constraint(
            constraint_id="K.compliance.1",
            text="System SOC-2 compliant",
            bounds_kind="compliance",
            evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
        ),
    ]
    caps = [
        Capability(
            capability_id="C.alpha.1",
            text="Alpha capability",
            serves=["O.alpha.1"],
            evidence=CapabilityEvidence(readme_excerpts=["alpha"]),
        ),
    ]
    return objs, cons, caps


def test_enqueue_altitude_tagged_provenance(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    from loam.per_project_pm import PMRuntime

    ws, pm_name = tmp_workspace_with_pm
    pm = PMRuntime.from_workspace(ws, pm_name)
    objs, cons, caps = _build_typed_lists()
    extraction_id = "test-x"

    count = enqueue_objective_ratification_batch(
        extraction_id=extraction_id,
        objectives=objs,
        constraints=cons,
        capabilities=caps,
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert count == 3

    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    provenances = {e["provenance"] for e in payload["queue"]}
    assert f"odd-extract:{extraction_id}:objective:O.alpha.1" in provenances
    assert f"odd-extract:{extraction_id}:constraint:K.compliance.1" in provenances
    assert f"odd-extract:{extraction_id}:capability:C.alpha.1" in provenances


def test_parse_altitude_provenance_v0_2_3() -> None:
    extraction_id, altitude, target_id = parse_altitude_provenance(
        "odd-extract:test-x:objective:O.alpha.1"
    )
    assert extraction_id == "test-x"
    assert altitude == "objective"
    assert target_id == "O.alpha.1"


def test_parse_altitude_provenance_v0_1_8_legacy() -> None:
    """Legacy v0.1.8 provenance has no altitude segment."""
    extraction_id, altitude, target_id = parse_altitude_provenance(
        "odd-extract:test-x:AC.LEGACY.1"
    )
    assert extraction_id == "test-x"
    assert altitude is None
    assert target_id == "AC.LEGACY.1"


def test_parse_altitude_provenance_rejects_non_odd_extract() -> None:
    with pytest.raises(ValueError):
        parse_altitude_provenance("not-odd-extract:x:y")


def test_pm_schema_unchanged(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """PM-side decision-queue schema doesn't gain new keys; provenance
    is treated as a free-form string from PM's perspective.
    """
    from loam.per_project_pm import PMRuntime

    ws, pm_name = tmp_workspace_with_pm
    pm = PMRuntime.from_workspace(ws, pm_name)
    objs, _, _ = _build_typed_lists()
    enqueue_objective_ratification_batch(
        extraction_id="t",
        objectives=objs,
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    # Top-level shape — schema_version + queue.
    assert "schema_version" in payload
    assert "queue" in payload
    # Each entry has `provenance` + `text` and similar v0.1.8 fields;
    # no new altitude-tag column.
    for entry in payload["queue"]:
        assert "altitude" not in entry

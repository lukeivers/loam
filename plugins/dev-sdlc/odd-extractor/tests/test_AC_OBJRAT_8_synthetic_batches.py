"""AC.OBJRAT.8 — Component tests against 3 synthetic ratification fixtures.

- all-plausible: 5 P-band + populated backing-map; full enqueue→
  surface→parse→apply→audit cycle.
- mixed-bands: V/P/H band objectives + mixed backing.
- edge-cases: P→V-without-backing blocked + capability-with-H-served-
  objective.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
    RatificationRefusedError,
    apply_objective_ratification_action,
    enqueue_objective_ratification_batch,
    parse_altitude_provenance,
    promote_capability,
    promote_objective,
)


_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "objective-ratification"
)


def _load_objectives(path: Path) -> tuple[
    list[Objective], list[Capability], dict
]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    objs: list[Objective] = []
    for d in raw.get("objectives", []):
        ev = d["evidence"]
        objs.append(
            Objective(
                objective_id=d["objective_id"],
                text=d["text"],
                confidence=ConfidenceBand(d["confidence"]),
                evidence=ObjectiveEvidence(**ev),
                domain=d["domain"],
            )
        )
    caps: list[Capability] = []
    for d in raw.get("capabilities", []) or []:
        caps.append(
            Capability(
                capability_id=d["capability_id"],
                text=d["text"],
                serves=d["serves"],
                evidence=CapabilityEvidence(**d["evidence"]),
            )
        )
    return objs, caps, raw


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
        "project_name": "t",
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


def test_all_plausible_full_cycle(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    from loam.per_project_pm import PMRuntime

    ws, pm_name = tmp_workspace_with_pm
    objs, _, _ = _load_objectives(
        _FIXTURES_ROOT / "all-plausible" / "objectives.yaml"
    )
    pm = PMRuntime.from_workspace(ws, pm_name)
    extraction_id = "all-p-test"
    enqueued = enqueue_objective_ratification_batch(
        extraction_id=extraction_id,
        objectives=objs,
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    assert enqueued == 5

    # Build a backing-map with STRONG entries for each.
    bm = BackingMap(
        extraction_id=extraction_id,
        entries=[
            BackingMapEntry(
                objective_id=o.objective_id,
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id=f"route:src/{o.domain}.js:1",
                        kind="route",
                        path=f"src/{o.domain}.js",
                        confidence="STRONG",
                    ),
                ],
            )
            for o in objs
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=5,
        objective_count=5,
    )

    # Surface one + parse provenance + apply.
    surfaced = pm.surface_next_questions_batch()
    assert len(surfaced) == 1
    eid, altitude, target_id = parse_altitude_provenance(
        surfaced[0].provenance
    )
    assert altitude == "objective"
    # Promote it.
    a = promote_objective(
        target_id=target_id,
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=[
            f"route:src/{[o for o in objs if o.objective_id == target_id][0].domain}.js:1"
        ],
    )
    out = apply_objective_ratification_action(
        a,
        objectives=objs,
        backing_map=bm,
        workspace_root=ws,
        repo_id=extraction_id,
    )
    target = next(
        o for o in out["objectives"] if o.objective_id == target_id
    )
    assert target.confidence is ConfidenceBand.VERIFIED


def test_mixed_bands_demote_v_to_p(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """V-band objective demotion: still possible without backing."""
    from loam.per_project_pm import PMRuntime

    ws, pm_name = tmp_workspace_with_pm
    objs, _, _ = _load_objectives(
        _FIXTURES_ROOT / "mixed-bands" / "objectives.yaml"
    )
    pm = PMRuntime.from_workspace(ws, pm_name)
    extraction_id = "mixed"
    enqueue_objective_ratification_batch(
        extraction_id=extraction_id,
        objectives=objs,
        workspace_root=ws,
        pm_runtime=pm,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    from loam_odd_extractor import demote_objective

    a = demote_objective(
        target_id="O.v1.1",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    out = apply_objective_ratification_action(
        a,
        objectives=objs,
        workspace_root=ws,
        repo_id=extraction_id,
    )
    target = next(o for o in out["objectives"] if o.objective_id == "O.v1.1")
    assert target.confidence is ConfidenceBand.PLAUSIBLE


def test_edge_cases_p_to_v_without_backing_refused(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    objs, caps, _ = _load_objectives(
        _FIXTURES_ROOT / "edge-cases" / "objectives.yaml"
    )
    # No backing-map for O.no-backing.1 — promotion blocks even with
    # cited rows because the entry doesn't exist.
    bm = BackingMap(
        extraction_id="edge",
        entries=[],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=0,
        objective_count=2,
    )
    a = promote_objective(
        target_id="O.no-backing.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/missing.js:1"],
    )
    with pytest.raises(RatificationRefusedError):
        apply_objective_ratification_action(
            a,
            objectives=objs,
            backing_map=bm,
            workspace_root=ws,
            repo_id="edge",
        )


def test_edge_cases_capability_h_band_served_blocked(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    objs, caps, _ = _load_objectives(
        _FIXTURES_ROOT / "edge-cases" / "objectives.yaml"
    )
    a = promote_capability(
        target_id="C.depends-on-h.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    with pytest.raises(RatificationRefusedError) as e:
        apply_objective_ratification_action(
            a,
            objectives=objs,
            capabilities=caps,
            workspace_root=ws,
            repo_id="edge",
        )
    assert "HYPOTHESISED" in str(e.value)

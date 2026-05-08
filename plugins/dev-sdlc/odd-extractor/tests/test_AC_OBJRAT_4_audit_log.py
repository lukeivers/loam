"""AC.OBJRAT.4 — Audit-log per ratification action.

12 new event_kinds: ``ratification_<altitude>_<action>`` for
altitude ∈ {objective, constraint, capability} × action ∈ {promote,
demote, edit, reject}.

Each entry carries: target_id + altitude + band_before + band_after
+ explicit_yes + backing_evidence_cited + pm_audit_path.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    Constraint,
    ConstraintEvidence,
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
    apply_objective_ratification_action,
    demote_capability,
    demote_constraint,
    demote_objective,
    edit_capability,
    edit_constraint,
    edit_objective,
    promote_capability,
    promote_constraint,
    promote_objective,
    reject_capability,
    reject_constraint,
    reject_objective,
)
from loam_odd_extractor.observability import list_entries


def _objective(oid: str = "O.alpha.1") -> Objective:
    return Objective(
        objective_id=oid,
        text="Operators see alpha outcome delivered through the dashboard ok",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["alpha"]),
        domain="alpha",
    )


def _constraint(cid: str = "K.alpha.1") -> Constraint:
    return Constraint(
        constraint_id=cid,
        text="System SOC-2 compliant",
        bounds_kind="compliance",
        evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
    )


def _capability(cid: str = "C.alpha.1") -> Capability:
    return Capability(
        capability_id=cid,
        text="Alpha capability",
        serves=["O.alpha.1"],
        evidence=CapabilityEvidence(readme_excerpts=["x"]),
    )


def test_all_12_event_kinds_present(tmp_path: Path) -> None:
    objs = [_objective()]
    cons = [_constraint()]
    caps = [_capability()]
    bm = BackingMap(
        extraction_id="t",
        entries=[
            BackingMapEntry(
                objective_id="O.alpha.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:src/alpha.js:1",
                        kind="route",
                        path="src/alpha.js",
                        confidence="STRONG",
                    ),
                ],
            ),
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=1,
        objective_count=1,
    )

    actions = [
        # objective × 4
        promote_objective(
            target_id="O.alpha.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        demote_objective(
            target_id="O.alpha.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.HYPOTHESISED,
        ),
        edit_objective(
            target_id="O.alpha.1", edit_text="updated outcome text"
        ),
        # objective reject — apply + check.
        reject_objective(
            target_id="O.alpha.1",
            reject_reason="duplicate",
        ),
        # constraint × 4
        promote_constraint(
            target_id="K.alpha.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        demote_constraint(
            target_id="K.alpha.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.HYPOTHESISED,
        ),
        edit_constraint(target_id="K.alpha.1", edit_text="x updated"),
        reject_constraint(
            target_id="K.alpha.1", reject_reason="duplicate"
        ),
        # capability × 4
        promote_capability(
            target_id="C.alpha.1",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        ),
        demote_capability(
            target_id="C.alpha.1",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.HYPOTHESISED,
        ),
        edit_capability(target_id="C.alpha.1", edit_text="y updated"),
        reject_capability(
            target_id="C.alpha.1", reject_reason="duplicate"
        ),
    ]

    # Re-create lists between actions because reject mutates.
    cur_objs = list(objs)
    cur_cons = list(cons)
    cur_caps = list(caps)
    for a in actions:
        # Re-add the rejected target back so subsequent actions on the
        # same id (across altitudes) succeed.
        if not cur_objs and a.kind != "reject":
            cur_objs = [_objective()]
        if not cur_cons and a.altitude == "constraint" and a.kind != "reject":
            cur_cons = [_constraint()]
        if not cur_caps and a.altitude == "capability" and a.kind != "reject":
            cur_caps = [_capability()]
        # Capability promotions need the served objective present.
        if a.altitude == "capability" and a.kind == "promote":
            if not any(o.objective_id == "O.alpha.1" for o in cur_objs):
                cur_objs.append(_objective())
        out = apply_objective_ratification_action(
            a,
            objectives=cur_objs,
            constraints=cur_cons,
            capabilities=cur_caps,
            backing_map=bm,
            workspace_root=tmp_path,
            repo_id="t",
        )
        cur_objs = out["objectives"]
        cur_cons = out["constraints"]
        cur_caps = out["capabilities"]

    ext_dir = tmp_path / ".loam" / "extractions" / "t"
    entries = list_entries(ext_dir)
    kinds_seen = set()
    for entry in entries:
        payload = yaml.safe_load(entry.read_text(encoding="utf-8"))
        kinds_seen.add(payload["event_kind"])
    expected = {
        f"ratification_{alt}_{act}"
        for alt in ("objective", "constraint", "capability")
        for act in ("promote", "demote", "edit", "reject")
    }
    assert expected <= kinds_seen


def test_audit_payload_carries_pm_audit_path(tmp_path: Path) -> None:
    obj = _objective()
    a = edit_objective(target_id="O.alpha.1", edit_text="updated text")
    apply_objective_ratification_action(
        a,
        objectives=[obj],
        workspace_root=tmp_path,
        repo_id="t",
        pm_audit_path="audit-log/2026/05/04/0001.yaml",
    )
    ext_dir = tmp_path / ".loam" / "extractions" / "t"
    entries = list_entries(ext_dir)
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["estimate"]["pm_audit_path"] == "audit-log/2026/05/04/0001.yaml"


def test_audit_payload_carries_backing_evidence_cited(tmp_path: Path) -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[
            BackingMapEntry(
                objective_id="O.alpha.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:src/alpha.js:1",
                        kind="route",
                        path="src/alpha.js",
                        confidence="STRONG",
                    ),
                ],
            ),
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=1,
        objective_count=1,
    )
    a = promote_objective(
        target_id="O.alpha.1",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
        backing_evidence_cited=["route:src/alpha.js:1"],
    )
    apply_objective_ratification_action(
        a,
        objectives=[_objective()],
        backing_map=bm,
        workspace_root=tmp_path,
        repo_id="t",
    )
    ext_dir = tmp_path / ".loam" / "extractions" / "t"
    entries = list_entries(ext_dir)
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["estimate"]["backing_evidence_cited"] == [
        "route:src/alpha.js:1"
    ]
    assert payload["estimate"]["explicit_yes"] is True

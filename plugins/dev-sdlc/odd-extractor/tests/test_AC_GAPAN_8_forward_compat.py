"""AC.GAPAN.8 — Forward-compat field for v0.2.6+ negative-alignment.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.8:

- Gap.negative_alignment_evidence: list[EvidenceRowRef] | None
  defaults to None.
- At v0.2.4 the field is never populated (analyze_gaps always emits None).
- v0.2.6+ negative-alignment populates the field on category-a gaps
  where evidence rows actively contradict the objective.
- Round-trip safety: legacy v0.2.4 inventories deserialise via
  model_validate with field absent / None → no schema-version bump
  needed at v0.2.6+.
- Field absent in serialised YAML when None (no
  negative_alignment_evidence: null clutter via
  model_dump(exclude_none=True)).
"""

from __future__ import annotations

import yaml

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    EvidenceRowRef,
    Gap,
    GapInventory,
    GapSummary,
    analyze_gaps,
    save_gap_inventory,
)

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
)


def test_field_defaults_to_none() -> None:
    g = Gap(
        gap_id="G.BACKING.o-test-1",
        category="objective_without_verified_backing",
        confidence="STRONG",
        objective_id="O.test.1",
        rationale="Default forward-compat field is None at v0.2.4 always.",
    )
    assert g.negative_alignment_evidence is None


def test_round_trip_with_field_populated() -> None:
    """v0.2.6+-shape Gap round-trips through Pydantic."""
    rows = [
        EvidenceRowRef(
            evidence_row_id="route:src/auth.js:36",
            kind="route",
            path="src/auth.js",
            line_range=(36, 55),
            confidence="STRONG",
            language="jsts",
        ),
    ]
    g = Gap(
        gap_id="G.BACKING.o-security-audit-trail-1",
        category="objective_without_verified_backing",
        confidence="STRONG",
        objective_id="O.security.1",
        rationale="v0.2.6+ shape — auth-bypass paths actively contradict the audit-trail objective.",
        negative_alignment_evidence=rows,
    )
    payload = g.model_dump(mode="json")
    g2 = Gap.model_validate(payload)
    assert g2.negative_alignment_evidence is not None
    assert len(g2.negative_alignment_evidence) == 1
    assert g2.negative_alignment_evidence[0].path == "src/auth.js"


def test_field_absent_when_none_in_serialised_yaml(tmp_path) -> None:
    """exclude_none semantics keep v0.2.4 YAML clean."""
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[]),
    ])
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[
            make_raw_dict(path="src/orphan.js", kind="route"),
        ],
        extraction_id="repo-1",
    )
    p, _ = save_gap_inventory(inv, tmp_path)
    # No null clutter.
    raw_text = p.read_text(encoding="utf-8")
    assert "negative_alignment_evidence" not in raw_text


def test_v024_inventories_load_into_v026_shape_round_trip(tmp_path) -> None:
    """Field absence in v0.2.4 YAML loads cleanly (None default)."""
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[]),
    ])
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[],
        extraction_id="repo-1",
    )
    p, _ = save_gap_inventory(inv, tmp_path)
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    payload.pop("schema_version", None)
    inv2 = GapInventory.model_validate(payload)
    for g in inv2.gaps:
        assert g.negative_alignment_evidence is None


def test_v024_analyze_gaps_never_populates_field() -> None:
    """At v0.2.4 the production analyze_gaps never sets the field."""
    obj_p = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    obj_h = make_objective(idx=2, band=ConfidenceBand.HYPOTHESISED)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj_p.objective_id, evidence_rows=[]),
        BackingMapEntry(objective_id=obj_h.objective_id, evidence_rows=[]),
    ])
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj_p, obj_h]),
        backing_map=bm,
        evidence_rows=[
            make_raw_dict(path="src/a.js"),
            make_raw_dict(path="src/b.js", kind="callback"),
        ],
        extraction_id="repo-1",
    )
    for g in inv.gaps:
        assert g.negative_alignment_evidence is None

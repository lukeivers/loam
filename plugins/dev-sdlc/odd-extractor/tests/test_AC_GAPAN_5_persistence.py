"""AC.GAPAN.5 — Persistence at canonical workspace path.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.5:

- Writes to <extraction_dir>/gap-inventory.yaml.
- Atomic tmp+rename (no partial residue on completion).
- Round-trip via model_dump / model_validate.
- Idempotent on no-change: byte-identical re-write when inputs
  unchanged (excluding analyzed_at).
- Schema-versioned at v1.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    analyze_gaps,
    gap_inventory_path,
    load_gap_inventory,
    save_gap_inventory,
)

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
)


def _build_inventory(extraction_id: str = "repo-1", analyzed_at: str = "2026-05-04T16:00:00+00:00"):
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[]),
    ])
    return analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[
            make_raw_dict(path="src/orphan.js", kind="route"),
        ],
        extraction_id=extraction_id,
        analyzed_at=analyzed_at,
        audit_path="/tmp/audit",
    )


def test_save_writes_to_canonical_path(tmp_path: Path) -> None:
    inv = _build_inventory()
    p, wrote = save_gap_inventory(inv, tmp_path)
    assert wrote is True
    assert p == tmp_path / "gap-inventory.yaml"
    assert p.exists()


def test_path_helper(tmp_path: Path) -> None:
    assert gap_inventory_path(tmp_path) == tmp_path / "gap-inventory.yaml"


def test_round_trip_via_load(tmp_path: Path) -> None:
    inv = _build_inventory()
    save_gap_inventory(inv, tmp_path)
    loaded = load_gap_inventory(tmp_path)
    assert loaded is not None
    assert loaded.extraction_id == "repo-1"
    assert loaded.summary.total == inv.summary.total


def test_load_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_gap_inventory(tmp_path) is None


def test_atomic_write_no_partial_residue(tmp_path: Path) -> None:
    inv = _build_inventory()
    save_gap_inventory(inv, tmp_path)
    siblings = list(tmp_path.iterdir())
    # Only the gap-inventory.yaml; no .tmp residue.
    assert len(siblings) == 1
    assert siblings[0].name == "gap-inventory.yaml"


def test_persisted_payload_includes_schema_version(tmp_path: Path) -> None:
    inv = _build_inventory()
    p, _ = save_gap_inventory(inv, tmp_path)
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["extraction_id"] == "repo-1"


def test_idempotent_skip_on_unchanged_input(tmp_path: Path) -> None:
    """Re-saving identical content (sans analyzed_at) is a no-op write."""
    inv = _build_inventory(analyzed_at="2026-05-04T16:00:00+00:00")
    p, wrote_first = save_gap_inventory(inv, tmp_path)
    assert wrote_first is True
    first_mtime = p.stat().st_mtime_ns

    # Re-build the inventory with a different analyzed_at — content
    # should hash identical (analyzed_at is excluded from hash).
    inv2 = _build_inventory(analyzed_at="2026-05-04T17:00:00+00:00")
    p2, wrote_second = save_gap_inventory(inv2, tmp_path)
    assert wrote_second is False  # skip-write fired
    assert p2 == p
    # File untouched.
    assert p.stat().st_mtime_ns == first_mtime


def test_idempotent_skip_disabled_writes_anyway(tmp_path: Path) -> None:
    """skip_on_no_change=False forces a re-write even on identical content."""
    inv = _build_inventory()
    save_gap_inventory(inv, tmp_path)
    inv2 = _build_inventory()
    _, wrote = save_gap_inventory(inv2, tmp_path, skip_on_no_change=False)
    assert wrote is True


def test_changed_content_writes(tmp_path: Path) -> None:
    """Changed gap content → re-write fires."""
    inv1 = _build_inventory()
    save_gap_inventory(inv1, tmp_path)
    # Build a different inventory (different objective shape).
    obj = make_objective(idx=2, band=ConfidenceBand.HYPOTHESISED)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[]),
    ])
    inv2 = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[],
        extraction_id="repo-1",
        analyzed_at="2026-05-04T17:00:00+00:00",
        audit_path="/tmp/audit",
    )
    _, wrote = save_gap_inventory(inv2, tmp_path)
    assert wrote is True


def test_negative_alignment_field_omitted_when_none(tmp_path: Path) -> None:
    """exclude_none on save → no negative_alignment_evidence: null clutter."""
    inv = _build_inventory()
    p, _ = save_gap_inventory(inv, tmp_path)
    raw = p.read_text(encoding="utf-8")
    # The forward-compat field defaults to None at v0.2.4 and should
    # not appear in the serialised payload.
    assert "negative_alignment_evidence" not in raw

"""AC.GAPAN.6 — Audit-log event_kinds.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.6:

- 3 new event_kinds: gap_analysis_start, gap_inventory_persisted,
  gap_analysis_end.
- Structured payloads via existing ``estimate`` field (no schema bump).
- Start payload: extraction_id, augmented_objective_count,
  backing_map_objective_count, evidence_row_count.
- Persisted payload: extraction_id, gap_count, category_a_count,
  category_b_count, strong_count, weak_count, gap_inventory_path.
- End payload: extraction_id, duration_ms.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    analyze_gaps,
    emit_end_audit,
    emit_persisted_audit,
    emit_start_audit,
    save_gap_inventory,
)
from loam_odd_extractor.observability import GAP_ANALYSIS_EVENT_KINDS

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
)


def _read_audit_entries(audit_dir: Path) -> list[dict]:
    out: list[dict] = []
    if not audit_dir.exists():
        return out
    for f in sorted(audit_dir.iterdir()):
        if f.is_file() and f.name.endswith(".yaml"):
            payload = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                out.append(payload)
    return out


def test_event_kinds_constant_is_three_kinds() -> None:
    assert len(GAP_ANALYSIS_EVENT_KINDS) == 3
    assert set(GAP_ANALYSIS_EVENT_KINDS) == {
        "gap_analysis_start",
        "gap_inventory_persisted",
        "gap_analysis_end",
    }


def test_full_run_emits_all_three_kinds_in_order(tmp_path: Path) -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[]),
    ])
    rows = [make_raw_dict(path="src/orphan.js")]

    emit_start_audit(
        tmp_path,
        extraction_id="repo-1",
        augmented_objective_count=1,
        backing_map_objective_count=1,
        evidence_row_count=1,
    )
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=rows,
        extraction_id="repo-1",
        audit_path=str(tmp_path / "audit-log"),
    )
    p, _ = save_gap_inventory(inv, tmp_path)
    emit_persisted_audit(
        tmp_path,
        extraction_id="repo-1",
        inventory=inv,
        gap_inventory_path_str=str(p),
    )
    emit_end_audit(tmp_path, extraction_id="repo-1", duration_ms=42)

    entries = _read_audit_entries(tmp_path / "audit-log")
    kinds = [e["event_kind"] for e in entries]
    assert kinds == [
        "gap_analysis_start",
        "gap_inventory_persisted",
        "gap_analysis_end",
    ]


def test_start_payload_present(tmp_path: Path) -> None:
    emit_start_audit(
        tmp_path,
        extraction_id="repo-1",
        augmented_objective_count=3,
        backing_map_objective_count=2,
        evidence_row_count=7,
    )
    entries = _read_audit_entries(tmp_path / "audit-log")
    starts = [e for e in entries if e["event_kind"] == "gap_analysis_start"]
    assert len(starts) == 1
    est = starts[0]["estimate"]
    assert est["extraction_id"] == "repo-1"
    assert est["augmented_objective_count"] == 3
    assert est["backing_map_objective_count"] == 2
    assert est["evidence_row_count"] == 7


def test_persisted_payload_carries_summary_fields(tmp_path: Path) -> None:
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
    emit_persisted_audit(
        tmp_path,
        extraction_id="repo-1",
        inventory=inv,
        gap_inventory_path_str="/abs/path/gap-inventory.yaml",
    )
    entries = _read_audit_entries(tmp_path / "audit-log")
    persisted = [e for e in entries if e["event_kind"] == "gap_inventory_persisted"]
    assert len(persisted) == 1
    est = persisted[0]["estimate"]
    assert est["gap_count"] == inv.summary.total
    assert est["category_a_count"] == inv.summary.category_a_count
    assert est["category_b_count"] == inv.summary.category_b_count
    assert est["strong_count"] == inv.summary.strong_count
    assert est["weak_count"] == inv.summary.weak_count
    assert est["gap_inventory_path"] == "/abs/path/gap-inventory.yaml"
    assert persisted[0]["artefact_path"] == "/abs/path/gap-inventory.yaml"


def test_end_payload_carries_duration(tmp_path: Path) -> None:
    emit_end_audit(tmp_path, extraction_id="repo-1", duration_ms=123)
    entries = _read_audit_entries(tmp_path / "audit-log")
    ends = [e for e in entries if e["event_kind"] == "gap_analysis_end"]
    assert len(ends) == 1
    est = ends[0]["estimate"]
    assert est["duration_ms"] == 123
    assert est["extraction_id"] == "repo-1"

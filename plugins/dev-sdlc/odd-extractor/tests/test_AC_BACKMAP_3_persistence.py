"""AC.BACKMAP.3 — Persistence at backing-map.yaml.

- Atomic write (tmp+rename).
- Round-trips Pydantic.
- D5 cross-session survival via load_backing_map.
- Generate-stage post-synthesis state.yaml ``backing_map`` artefact key.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    EvidenceRowRef,
    OrphanRow,
    backing_map_path,
    load_backing_map,
    save_backing_map,
)


def _build_backing_map() -> BackingMap:
    return BackingMap(
        extraction_id="rd-automation",
        entries=[
            BackingMapEntry(
                objective_id="O.dispute-flow.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:src/disputeRoutes.js:42",
                        kind="route",
                        path="src/disputeRoutes.js",
                        line_range=(42, 47),
                        confidence="STRONG",
                        language="jsts",
                    ),
                ],
                match_rationale="dispute path match",
            ),
        ],
        orphan_rows=[
            OrphanRow(
                evidence_row_id="pattern:src/util/log.js:1",
                kind="pattern",
                path="src/util/log.js",
                reason="no-objective-match",
            ),
        ],
        created_at="2026-05-04T12:00:00+00:00",
        model_id="claude-sonnet-4-5",
        cost_actual_cents=4.2,
        total_evidence_rows=2,
        objective_count=1,
    )


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    bm = _build_backing_map()
    path = save_backing_map(tmp_path, bm)
    assert path.exists()
    assert path == tmp_path / "backing-map.yaml"

    loaded = load_backing_map(tmp_path)
    assert loaded is not None
    assert loaded.extraction_id == "rd-automation"
    assert len(loaded.entries) == 1
    assert loaded.entries[0].objective_id == "O.dispute-flow.1"
    assert loaded.entries[0].evidence_rows[0].confidence == "STRONG"
    assert loaded.orphan_rows[0].reason == "no-objective-match"


def test_persisted_payload_includes_schema_version(tmp_path: Path) -> None:
    bm = _build_backing_map()
    path = save_backing_map(tmp_path, bm)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["extraction_id"] == "rd-automation"
    # Non-key fields preserved.
    assert payload["model_id"] == "claude-sonnet-4-5"


def test_load_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_backing_map(tmp_path) is None


def test_atomic_write_no_partial_residue(tmp_path: Path) -> None:
    """tmp file is cleaned up on completion."""
    bm = _build_backing_map()
    save_backing_map(tmp_path, bm)
    siblings = list(tmp_path.iterdir())
    # Only the backing-map.yaml; no .tmp residue.
    assert len(siblings) == 1
    assert siblings[0].name == "backing-map.yaml"


def test_path_helper(tmp_path: Path) -> None:
    assert backing_map_path(tmp_path) == tmp_path / "backing-map.yaml"

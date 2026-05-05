"""AC.BACKMAP.4 — Coverage report in contract-draft.md.

- "Backing-implementation map" section rendered.
- Per-objective row → STRONG / WEAK / total counts.
- First-3 path:line previews.
- Orphan section: count + first-10 paths annotated by reason.
- HYPOTHESISED objectives' empty backing rendered as ``(none)``.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    EvidenceRowRef,
    OrphanRow,
)
from loam_odd_extractor.verify import _render_backing_map_section


def _make_entry(
    oid: str, n_strong: int, n_weak: int
) -> BackingMapEntry:
    rows: list[EvidenceRowRef] = []
    for i in range(n_strong):
        rows.append(
            EvidenceRowRef(
                evidence_row_id=f"route:src/x_{i}.js:{i}",
                kind="route",
                path=f"src/x_{i}.js",
                line_range=(i, i + 5),
                confidence="STRONG",
                language="jsts",
            )
        )
    for j in range(n_weak):
        rows.append(
            EvidenceRowRef(
                evidence_row_id=f"pattern:src/y_{j}.js:{j}",
                kind="pattern",
                path=f"src/y_{j}.js",
                line_range=(j, j + 3),
                confidence="WEAK",
                language="jsts",
            )
        )
    return BackingMapEntry(
        objective_id=oid,
        evidence_rows=rows,
        match_rationale="stub",
    )


def test_renders_section_header() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[_make_entry("O.alpha.1", 2, 1)],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=3,
        objective_count=1,
    )
    lines = _render_backing_map_section(bm)
    md = "\n".join(lines)
    assert "## Backing-implementation map" in md
    assert "Total evidence rows:** 3" in md
    assert "Objectives:** 1" in md


def test_per_objective_counts_rendered() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[
            _make_entry("O.alpha.1", 3, 2),
            _make_entry("O.beta.1", 0, 1),
        ],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=6,
        objective_count=2,
    )
    md = "\n".join(_render_backing_map_section(bm))
    # Table row for O.alpha.1: 3 STRONG, 2 WEAK, 5 total.
    assert "| `O.alpha.1` | 3 | 2 | 5 |" in md
    assert "| `O.beta.1` | 0 | 1 | 1 |" in md


def test_first_3_preview_paths_rendered() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[_make_entry("O.alpha.1", 5, 0)],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=5,
        objective_count=1,
    )
    md = "\n".join(_render_backing_map_section(bm))
    # First 3 paths cited; later ones not in preview.
    assert "src/x_0.js" in md
    assert "src/x_1.js" in md
    assert "src/x_2.js" in md
    # Subsequent rows truncated from preview (still in count).
    # Confirm "src/x_4.js" not in the preview line:
    preview_line = next(l for l in md.split("\n") if "O.alpha.1" in l)
    assert "src/x_4.js" not in preview_line


def test_hypothesised_empty_backing_rendered_as_none() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[_make_entry("O.alpha.1", 0, 0)],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=0,
        objective_count=1,
    )
    md = "\n".join(_render_backing_map_section(bm))
    # The preview cell renders "(none)" rather than empty.
    preview_line = next(l for l in md.split("\n") if "O.alpha.1" in l)
    assert "(none)" in preview_line


def test_orphan_section_with_annotated_reasons() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[],
        orphan_rows=[
            OrphanRow(
                evidence_row_id=f"pattern:src/junk_{i}.js:{i}",
                kind="pattern",
                path=f"src/junk_{i}.js",
                reason="no-objective-match",
            )
            for i in range(15)
        ],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=15,
        objective_count=0,
    )
    md = "\n".join(_render_backing_map_section(bm))
    assert "Orphan evidence rows" in md
    assert "first 10" in md
    # First 10 rows in the table.
    for i in range(10):
        assert f"src/junk_{i}.js" in md
    # Row 14 is past the preview.
    assert "src/junk_14.js" not in md


def test_unmatched_objectives_listed() -> None:
    bm = BackingMap(
        extraction_id="t",
        entries=[_make_entry("O.alpha.1", 0, 0)],
        orphan_rows=[],
        created_at="2026-05-04T12:00:00+00:00",
        total_evidence_rows=0,
        objective_count=1,
        unmatched_objective_ids=["O.alpha.1"],
    )
    md = "\n".join(_render_backing_map_section(bm))
    assert "Unmatched objectives" in md
    assert "`O.alpha.1`" in md


def test_no_backing_map_renders_placeholder() -> None:
    md = "\n".join(_render_backing_map_section(None))
    assert "## Backing-implementation map" in md
    assert "No backing-map persisted" in md

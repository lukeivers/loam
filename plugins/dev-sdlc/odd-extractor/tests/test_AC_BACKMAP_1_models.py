"""AC.BACKMAP.1 — BackingMap + BackingMapEntry + EvidenceRowRef +
OrphanRow Pydantic models (id regexes + role validators).

- Construction with valid + invalid IDs.
- ValidationError on malformed IDs.
- Round-trip via model_dump / model_validate.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    BackingMap,
    BackingMapEntry,
    EvidenceRowRef,
    OrphanRow,
)


def test_evidence_row_ref_valid_construction() -> None:
    ref = EvidenceRowRef(
        evidence_row_id="route:src/routes/disputeRoutes.js:42",
        kind="route",
        path="src/routes/disputeRoutes.js",
        line_range=(42, 47),
        symbol_name="POST /dispute",
        language="jsts",
        confidence="STRONG",
    )
    assert ref.kind == "route"
    assert ref.confidence == "STRONG"
    assert ref.line_range == (42, 47)


def test_evidence_row_ref_id_regex_rejects_malformed() -> None:
    """The composite kind:path:line shape is enforced."""
    with pytest.raises(ValidationError):
        EvidenceRowRef(
            evidence_row_id="MALFORMED",  # missing colons
            kind="route",
            path="src/x.js",
        )


def test_evidence_row_ref_default_confidence_weak() -> None:
    ref = EvidenceRowRef(
        evidence_row_id="route:src/x.js",
        kind="route",
        path="src/x.js",
    )
    assert ref.confidence == "WEAK"
    assert ref.language == "other"


def test_orphan_row_valid_construction() -> None:
    orow = OrphanRow(
        evidence_row_id="pattern:src/util/log.js:1",
        kind="pattern",
        path="src/util/log.js",
        reason="no-objective-match",
        language="jsts",
    )
    assert orow.reason == "no-objective-match"


def test_orphan_row_reason_enum_three_values() -> None:
    """Per AC.BACKMAP.5 — three values accepted."""
    for r in ("no-objective-match", "weak-signal-only", "anti-feature-candidate"):
        OrphanRow(
            evidence_row_id="pattern:src/x.js",
            kind="pattern",
            path="src/x.js",
            reason=r,  # type: ignore[arg-type]
        )


def test_orphan_row_rejects_unknown_reason() -> None:
    with pytest.raises(ValidationError):
        OrphanRow(
            evidence_row_id="pattern:src/x.js",
            kind="pattern",
            path="src/x.js",
            reason="not-a-real-reason",  # type: ignore[arg-type]
        )


def test_backing_map_entry_objective_id_regex() -> None:
    """The objective_id regex is enforced."""
    with pytest.raises(ValidationError):
        BackingMapEntry(
            objective_id="not-an-objective-id",
            evidence_rows=[],
        )
    # Good shape:
    entry = BackingMapEntry(
        objective_id="O.dispute-flow.1",
        evidence_rows=[],
        match_rationale="",
    )
    assert entry.objective_id == "O.dispute-flow.1"
    # Empty evidence_rows allowed (HYPOTHESISED objectives).
    assert entry.evidence_rows == []


def test_backing_map_round_trip() -> None:
    """Pydantic round-trip preserves the full structure."""
    bm = BackingMap(
        extraction_id="rd-automation",
        entries=[
            BackingMapEntry(
                objective_id="O.dispute-flow.1",
                evidence_rows=[
                    EvidenceRowRef(
                        evidence_row_id="route:src/routes/disputeRoutes.js:42",
                        kind="route",
                        path="src/routes/disputeRoutes.js",
                        line_range=(42, 47),
                        confidence="STRONG",
                        language="jsts",
                    ),
                ],
                match_rationale="path matches dispute domain",
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
        unmatched_objective_ids=[],
    )
    payload = bm.model_dump(mode="json")
    bm2 = BackingMap.model_validate(payload)
    assert bm2.extraction_id == "rd-automation"
    assert len(bm2.entries) == 1
    assert bm2.entries[0].evidence_rows[0].confidence == "STRONG"
    assert bm2.orphan_rows[0].reason == "no-objective-match"


def test_backing_map_extra_field_forbidden() -> None:
    """ConfigDict(extra='forbid') is in force."""
    with pytest.raises(ValidationError):
        BackingMap(
            extraction_id="x",
            created_at="2026-05-04T12:00:00+00:00",
            unknown_field="bad",  # type: ignore[call-arg]
        )

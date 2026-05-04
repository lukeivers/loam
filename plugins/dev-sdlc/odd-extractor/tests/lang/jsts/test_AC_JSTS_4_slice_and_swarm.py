"""AC.JSTS.4 — Slice-and-swarm orchestrator + aggregator.

Verifies:

- Single-slice fast path: cost ≤ budget → one all-files slice.
- Multi-slice path: cost > budget → ≥ 6 slices (every JS/TS-domain).
- Aggregator merges deterministically (lexicographic ``ac_id``
  sort).
- Duplicate ``ac_id``s deduplicated with audit-log entry.
- ``SliceDriftError`` raised at >50% duplicate-ratio (F3
  ``needs_fresh_start`` analog).
- Aggregator + ``SliceDriftError`` reused from
  ``lang/ruby/slicer.py`` per Surface #4 / RF §10 #6.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence
from loam_odd_extractor.lang.jsts.slicer import (
    SliceDriftError,
    aggregate_slice_results,
    slice_repo,
)
from loam_odd_extractor.spec import RawACs


def _bac(ac_id: str, text: str = "test") -> dict:
    return BandedAC(
        ac_id=ac_id,
        text=text,
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=[f"{ac_id}.ts:1"],
        ),
    ).model_dump(mode="json")


def test_single_slice_fast_path() -> None:
    files = [
        Path("/repo/src/server.js"),
        Path("/repo/src/playwright/login-page.ts"),
    ]
    slices = slice_repo(
        files=files,
        estimate_money_cents=10,
        budget_hard_cap_cents=100,
    )
    assert len(slices) == 1
    assert slices[0].slice_id == "jsts-root"
    assert slices[0].adapter_name == "jsts"
    assert sorted(p.as_posix() for p in slices[0].paths) == sorted(
        p.as_posix() for p in files
    )


def test_multi_slice_partitioning_by_domain() -> None:
    files = [
        Path("/repo/src/server.js"),
        Path("/repo/src/routes/users.js"),
        Path("/repo/src/routes/sessions.mjs"),
        Path("/repo/src/middleware/auth.js"),
        Path("/repo/src/schemas/user.ts"),
        Path("/repo/src/schemas/session-class-validator.ts"),
        Path("/repo/src/playwright/login-page.ts"),
        Path("/repo/src/playwright/dashboard-page.ts"),
        Path("/repo/tests/playwright/login.spec.ts"),
        Path("/repo/tests/unit/users.test.ts"),
        Path("/repo/public/index.html"),
    ]
    slices = slice_repo(
        files=files,
        estimate_money_cents=1000,
        budget_hard_cap_cents=100,
    )
    # Per Surface #4 — at least 6 distinct domains exercised by
    # the fixture.
    assert len(slices) >= 6
    domain_set = {sl.slice_id for sl in slices}
    # Domains we expect: routes, controllers (absent here), middleware,
    # schemas, playwright (combined for src + tests), unit_tests, html,
    # src_root (server.js).
    expected_present = {
        "jsts-routes",
        "jsts-middleware",
        "jsts-schemas",
        "jsts-playwright",
        "jsts-unit_tests",
        "jsts-html",
        "jsts-src_root",
    }
    assert expected_present.issubset(domain_set), (
        f"missing domains: {expected_present - domain_set}; "
        f"got {domain_set}"
    )
    for sl in slices:
        assert sl.adapter_name == "jsts"


def test_aggregator_deterministic_sort() -> None:
    """ACs sorted by ac_id lexicographically."""
    s1 = RawACs(
        extraction_id="e",
        acs=[_bac("AC.JSTS.zod.user_email"), _bac("AC.JSTS.express.get")],
        unhandled_paths=[],
        per_slice_costs={"jsts-routes": {"cents": 5}},
        created_at="2026-01-01",
    )
    s2 = RawACs(
        extraction_id="e",
        acs=[_bac("AC.JSTS.test.playwright")],
        unhandled_paths=[],
        per_slice_costs={"jsts-playwright": {"cents": 3}},
        created_at="2026-01-01",
    )
    agg, dedup = aggregate_slice_results([s1, s2])
    ac_ids = [a["ac_id"] for a in agg.acs]
    assert ac_ids == sorted(ac_ids)
    assert dedup == []  # no duplicates


def test_aggregator_dedup_logs_occurrences() -> None:
    """Duplicate ac_id → last-write-wins; dedup_log records."""
    s1 = RawACs(
        extraction_id="e",
        acs=[_bac("AC.JSTS.x", "first"), _bac("AC.JSTS.y")],
        unhandled_paths=[],
        per_slice_costs={"a": {}},
        created_at="2026-01-01",
    )
    s2 = RawACs(
        extraction_id="e",
        acs=[_bac("AC.JSTS.x", "second")],
        unhandled_paths=[],
        per_slice_costs={"b": {}},
        created_at="2026-01-01",
    )
    agg, dedup = aggregate_slice_results([s1, s2])
    assert len(agg.acs) == 2  # one X (last wins) + one Y
    assert len(dedup) == 1
    assert dedup[0]["ac_id"] == "AC.JSTS.x"
    assert dedup[0]["occurrences"] == 2


def test_slice_drift_error_above_threshold() -> None:
    """When >50% of ACs are duplicates across slices, raise
    SliceDriftError.
    """
    # 3 unique AC IDs total, 2 of which are duplicated → ratio = 2/3
    # > 0.5 → SliceDriftError.
    s1 = RawACs(
        extraction_id="e",
        acs=[
            _bac("AC.JSTS.a"), _bac("AC.JSTS.b"), _bac("AC.JSTS.c"),
        ],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="",
    )
    s2 = RawACs(
        extraction_id="e",
        acs=[_bac("AC.JSTS.a"), _bac("AC.JSTS.b")],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="",
    )
    with pytest.raises(SliceDriftError) as exc_info:
        aggregate_slice_results([s1, s2])
    assert "duplicate_ratio" in str(exc_info.value).lower() or "drift" in str(exc_info.value).lower()


def test_aggregator_empty_slices() -> None:
    agg, dedup = aggregate_slice_results([])
    assert agg.acs == []
    assert dedup == []


def test_slice_drift_error_reused_from_ruby() -> None:
    """Per Surface #4 / RF §10 #6 — SliceDriftError is reused from
    lang.ruby.slicer (same class identity).
    """
    from loam_odd_extractor.lang.ruby.slicer import (
        SliceDriftError as RubyDriftError,
    )

    # Same class object (re-export).
    assert SliceDriftError is RubyDriftError

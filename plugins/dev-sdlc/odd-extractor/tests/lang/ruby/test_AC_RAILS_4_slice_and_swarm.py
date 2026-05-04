"""AC.RAILS.4 — Slice-and-swarm.

Verifies:

- ``slice_repo()`` returns a single all-files slice when estimate ≤
  budget.
- Returns ≥6 slices for the synthetic fixture when estimate >
  budget (every Rails-idiom domain represented).
- ``aggregate_slice_results()`` merges per-slice RawACs
  deterministically; lexicographic sort by ``ac_id``.
- Duplicate ``ac_id`` is deduplicated with audit-log entry.
- :class:`SliceDriftError` raised when >50% duplicates injected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.lang.ruby.slicer import (
    SliceDriftError,
    aggregate_slice_results,
    slice_repo,
)
from loam_odd_extractor.spec import RawACs


def _ruby_files(repo: Path) -> list[Path]:
    """Return every Ruby file under ``repo``."""
    return sorted(
        p for p in repo.rglob("*.rb")
    )


def test_slice_repo_single_slice_when_under_budget(
    synthetic_rails_repo: Path,
) -> None:
    """estimate ≤ budget → single all-files slice."""
    files = _ruby_files(synthetic_rails_repo)
    out = slice_repo(
        files=files,
        estimate_money_cents=10,
        budget_hard_cap_cents=1000,
    )
    assert len(out) == 1
    assert out[0].slice_id == "ruby-root"
    assert out[0].adapter_name == "ruby"
    assert sorted(out[0].paths) == sorted(files)


def test_slice_repo_multi_slice_when_over_budget(
    synthetic_rails_repo: Path,
) -> None:
    """estimate > budget → multiple slices by Rails-idiom domain."""
    files = _ruby_files(synthetic_rails_repo)
    out = slice_repo(
        files=files,
        estimate_money_cents=5000,
        budget_hard_cap_cents=1000,
    )
    # Synthetic fixture has files spanning: models, concerns,
    # migrations, jobs, controllers, routes, specs, tests. At least
    # 6 distinct domains visible; the slicer produces a slice per
    # domain that has files.
    assert len(out) >= 6
    domain_names = {s.slice_id for s in out}
    # Each slice should be domain-prefixed with "ruby-"
    assert all(s.slice_id.startswith("ruby-") for s in out)
    # Stable ordering by slice_id.
    assert [s.slice_id for s in out] == sorted(
        s.slice_id for s in out
    )


def test_aggregate_merges_and_sorts_lexicographically() -> None:
    """Aggregator concatenates + dedupes + sorts by ac_id."""
    raw_a = RawACs(
        extraction_id="x",
        acs=[
            {"ac_id": "AC.RAILS.b", "text": "second"},
            {"ac_id": "AC.RAILS.a", "text": "first"},
        ],
        unhandled_paths=[Path("a.rb")],
        per_slice_costs={"ruby-models": {"status": "ok"}},
        created_at="2026-05-04T00:00:00+00:00",
    )
    raw_b = RawACs(
        extraction_id="x",
        acs=[
            {"ac_id": "AC.RAILS.c", "text": "third"},
        ],
        unhandled_paths=[Path("b.rb"), Path("a.rb")],
        per_slice_costs={"ruby-jobs": {"status": "ok"}},
        created_at="2026-05-04T00:00:00+00:00",
    )
    aggregated, dedup_log = aggregate_slice_results([raw_a, raw_b])
    ac_ids = [a.get("ac_id") for a in aggregated.acs]
    assert ac_ids == ["AC.RAILS.a", "AC.RAILS.b", "AC.RAILS.c"]
    # Unhandled deduplicated.
    assert sorted(p.name for p in aggregated.unhandled_paths) == [
        "a.rb",
        "b.rb",
    ]
    # Per-slice costs merged.
    assert "ruby-models" in aggregated.per_slice_costs
    assert "ruby-jobs" in aggregated.per_slice_costs
    # No duplicates → empty dedup_log.
    assert dedup_log == []


def test_aggregate_dedup_logs_duplicates() -> None:
    """Duplicate ``ac_id`` across slices logged."""
    raw_a = RawACs(
        extraction_id="x",
        acs=[{"ac_id": "AC.SHARED", "text": "v1"}],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    raw_b = RawACs(
        extraction_id="x",
        acs=[{"ac_id": "AC.SHARED", "text": "v2"}],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    raw_c = RawACs(
        extraction_id="x",
        acs=[{"ac_id": "AC.OTHER", "text": "v3"}],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    # 2 unique ac_ids, 1 duplicated → ratio 1/2 = 50% — at threshold,
    # not exceeded. So this should succeed; bump up.
    raw_d = RawACs(
        extraction_id="x",
        acs=[{"ac_id": "AC.SHARED", "text": "v4"}],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    aggregated, dedup_log = aggregate_slice_results(
        [raw_a, raw_b, raw_c, raw_d]
    )
    # AC.SHARED appears 3x; AC.OTHER 1x.
    assert any(
        d["ac_id"] == "AC.SHARED" and d["occurrences"] == 3
        for d in dedup_log
    )
    # Last-write-wins: AC.SHARED's text is "v4".
    shared = next(
        a for a in aggregated.acs if a["ac_id"] == "AC.SHARED"
    )
    assert shared["text"] == "v4"


def test_aggregate_raises_on_drift() -> None:
    """>50% duplicate-ratio raises SliceDriftError."""
    # 2 unique IDs, both duplicated → ratio = 2/2 = 100% > 50%.
    raw_a = RawACs(
        extraction_id="x",
        acs=[
            {"ac_id": "AC.A", "text": "1"},
            {"ac_id": "AC.B", "text": "2"},
        ],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    raw_b = RawACs(
        extraction_id="x",
        acs=[
            {"ac_id": "AC.A", "text": "1b"},
            {"ac_id": "AC.B", "text": "2b"},
        ],
        unhandled_paths=[],
        per_slice_costs={},
        created_at="2026-05-04T00:00:00+00:00",
    )
    with pytest.raises(SliceDriftError, match="duplicate_ratio"):
        aggregate_slice_results([raw_a, raw_b])


def test_aggregate_empty_slice_list() -> None:
    """Empty input → empty aggregate (defensive)."""
    aggregated, dedup_log = aggregate_slice_results([])
    assert aggregated.acs == []
    assert aggregated.unhandled_paths == []
    assert dedup_log == []

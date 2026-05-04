"""AC.RAILS.7 — Cost-governance dry-run + budget envelope.

Verifies:

- Dry-run produces an estimate via the cost-governance primitive
  (smoke-level — Cycle 1 + 2 already exercised the primitive itself).
- Slicer's slice-vs-single decision uses the estimate-vs-budget
  comparison.
- The slicer's behaviour is deterministic and budget-aware.

Note: full live-extraction-with-LLM-cost-tracking is out of scope for
Cycle 3 — the heuristic inference layer is text-only / free, so live
extraction against the synthetic fixture costs $0. The budget
envelope is exercised at the slicer level (single vs multi-slice
decision); the live-extraction-halt-on-overrun path was sealed in
Cycle 1's ``test_AC_OREK_6_budget_envelope.py``.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.lang.ruby.slicer import slice_repo


def test_slicer_uses_estimate_vs_budget_threshold(
    synthetic_rails_repo: Path,
) -> None:
    """estimate > budget → multi-slice; estimate ≤ budget → single."""
    files = sorted(synthetic_rails_repo.rglob("*.rb"))

    # Under budget.
    single = slice_repo(
        files=files,
        estimate_money_cents=10,
        budget_hard_cap_cents=1000,
    )
    assert len(single) == 1

    # Over budget.
    multi = slice_repo(
        files=files,
        estimate_money_cents=5000,
        budget_hard_cap_cents=1000,
    )
    assert len(multi) > 1


def test_slicer_at_exact_budget(synthetic_rails_repo: Path) -> None:
    """estimate == budget → single slice (boundary on ≤)."""
    files = sorted(synthetic_rails_repo.rglob("*.rb"))
    single = slice_repo(
        files=files,
        estimate_money_cents=1000,
        budget_hard_cap_cents=1000,
    )
    assert len(single) == 1


def test_slicer_partition_sums_to_total(
    synthetic_rails_repo: Path,
) -> None:
    """The partition is exhaustive — every file lands in some slice."""
    files = sorted(synthetic_rails_repo.rglob("*.rb"))
    multi = slice_repo(
        files=files,
        estimate_money_cents=99999,
        budget_hard_cap_cents=1,
    )
    all_partitioned = []
    for sl in multi:
        all_partitioned.extend(sl.paths)
    assert sorted(all_partitioned) == sorted(files)


def test_slicer_chunks_large_migration_cohorts(tmp_path: Path) -> None:
    """A db/migrate/ cohort with >25 files splits into chunks of 25."""
    migrate = tmp_path / "db" / "migrate"
    migrate.mkdir(parents=True)
    files = []
    for i in range(60):
        p = migrate / f"{i:020d}_x.rb"
        p.write_text(f"# migration {i}\n", encoding="utf-8")
        files.append(p)

    multi = slice_repo(
        files=files,
        estimate_money_cents=99999,
        budget_hard_cap_cents=1,
    )
    migration_slices = [
        s for s in multi if s.slice_id.startswith("ruby-migrations")
    ]
    # 60 / 25 = 3 chunks (25 + 25 + 10)
    assert len(migration_slices) == 3
    assert sum(len(s.paths) for s in migration_slices) == 60


def test_slicer_categorises_by_rails_domain(
    synthetic_rails_repo: Path,
) -> None:
    """Multi-slice partitions by Rails-idiom domain (per Surface #2)."""
    files = sorted(synthetic_rails_repo.rglob("*.rb"))
    multi = slice_repo(
        files=files,
        estimate_money_cents=99999,
        budget_hard_cap_cents=1,
    )
    slice_ids = {s.slice_id for s in multi}
    # The synthetic fixture has files in: models, concerns, jobs,
    # controllers, migrations, routes, specs, tests.
    expected_domains = {
        "ruby-models",
        "ruby-concerns",
        "ruby-jobs",
        "ruby-controllers",
        "ruby-migrations",
        "ruby-routes",
        "ruby-specs",
        "ruby-tests",
    }
    # Every domain that has files in the fixture is represented.
    missing = expected_domains - slice_ids
    assert not missing, f"missing domains: {missing}"

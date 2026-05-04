"""Smoke D2 (idempotency variant) — n/a structurally for one-shot
CLI; idempotency variant exercised here.

Per plan-doc §6 D2:

- 5 extractions against the synthetic fixture produce byte-identical
  artefacts (modulo timestamps via clock injection).
- Cycle-3-specific addition: per-slice idempotency — the same slice
  extracted twice produces byte-identical per-slice RawACs.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs


def test_extract_is_byte_identical_across_runs(
    synthetic_rails_repo: Path,
) -> None:
    """5 extractions of the synthetic fixture produce identical
    AC dicts (modulo created_at)."""
    runs = [
        extract_rails_acs(repo=synthetic_rails_repo)
        for _ in range(5)
    ]

    # Strip created_at fields from the comparison.
    def _normalise(raw):
        return {
            "acs": raw.acs,
            "unhandled_paths": [str(p) for p in raw.unhandled_paths],
            "per_slice_costs": raw.per_slice_costs,
        }

    first = _normalise(runs[0])
    for r in runs[1:]:
        assert _normalise(r) == first, (
            "extraction is non-deterministic; D2 idempotency variant "
            "broken"
        )


def test_acs_sorted_lexicographically(
    synthetic_rails_repo: Path,
) -> None:
    """RawACs.acs is sorted by ac_id (the determinism mechanism per
    Surface #9).
    """
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    ac_ids = [ac.get("ac_id", "") for ac in raw.acs]
    assert ac_ids == sorted(ac_ids), (
        "AC list not sorted by ac_id; idempotency at risk"
    )


def test_per_slice_idempotency(synthetic_rails_repo: Path) -> None:
    """The same input slice produces the same output across two
    extractions.
    """
    from loam_odd_extractor.spec import AnalysisPlan, Slice
    from loam_odd_extractor.lang.ruby.adapter import RubyAdapter

    files = sorted(synthetic_rails_repo.rglob("*.rb"))
    plan = AnalysisPlan(
        extraction_id="t",
        slices=[
            Slice(
                slice_id="ruby-root",
                adapter_name="ruby",
                paths=files,
            )
        ],
        unhandled_paths=[],
        created_at="2026-05-04T00:00:00+00:00",
    )
    adapter = RubyAdapter()
    raw1 = adapter.extract(synthetic_rails_repo, plan)
    raw2 = adapter.extract(synthetic_rails_repo, plan)
    assert raw1.acs == raw2.acs
    assert raw1.unhandled_paths == raw2.unhandled_paths

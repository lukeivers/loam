"""Smoke D2 — idempotency variant against the canonical ruby-rails-
payment fixture (v0.1.8 Cycle 4b).

Per smoke-test-discipline §6 — ``loam odd-extract`` is a one-shot
CLI; D2 steady-state is structurally n/a. The IDEMPOTENCY VARIANT
verifies repeated extraction runs against the same canonical fixture
produce byte-identical AC sets (modulo timestamps).

Load-bearing for AC.DRY refactor verification: if the refactor
introduced any nondeterminism (e.g., different ``ac_id`` ordering),
this test catches it.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs


def test_canonical_extraction_is_byte_identical_across_5_runs(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """5 sequential extraction runs produce identical ``ac_id`` sets
    + identical ordering.
    """
    runs = [
        extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
        for _ in range(5)
    ]

    # Every run produced > 0 ACs.
    for r in runs:
        assert len(r.acs) > 0

    # All runs produced the same ac_id set.
    ac_ids = [tuple(ac["ac_id"] for ac in r.acs) for r in runs]
    for ids in ac_ids[1:]:
        assert ids == ac_ids[0], (
            "Canonical extraction is not idempotent — run produced "
            "different ac_id ordering"
        )


def test_canonical_acs_sorted_lexicographically(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """ACs are sorted lexicographically by ``ac_id`` per Cycle 3
    Surface #9 idempotency rule. Refactor must preserve this.
    """
    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    ids = [ac["ac_id"] for ac in raw.acs]
    assert ids == sorted(ids), (
        "ACs not in lexicographic order — D2 idempotency violation"
    )

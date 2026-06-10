"""AC.PRG.OA (outcome-altitude: true) — the live-room comfort test.

A fresh-workspace run observed end to end: from typed ask to verdict,
gaps between user-visible updates stay within the heartbeat bound
during active work, and an after-the-fact audit matches every
update's claim against the run record with ZERO unverifiable claims.

Shares the single session live run (conftest.live_bfi_run; env-gated
BFI_REAL_CLAUDE=1).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.progress import HEARTBEAT_INTERVAL_S  # noqa: E402


def test_observed_gaps_within_bound_and_zero_unverifiable_claims(
        live_bfi_run):
    result = live_bfi_run["result"]
    audit = result.progress_audit

    # Every narrated line the observer saw verifies against the run
    # record — zero unverifiable claims.
    assert audit["unverifiable_claims"] == []
    assert audit["n_user_visible"] >= 6  # the full stage ladder showed

    # No user-visible silence beyond the named heartbeat bound during
    # active work (the record's own timestamps are the evidence).
    assert audit["gap_within_bound"] is True, (
        f"max inter-update gap {audit['max_gap_s']}s exceeded the "
        f"{HEARTBEAT_INTERVAL_S}s heartbeat bound")

    # The observer-side timestamps corroborate the record-side audit:
    # the observed stream had no gap beyond the bound either.
    ts = live_bfi_run["narrated_ts"]
    if len(ts) >= 2:
        observed_max = max(b - a for a, b in zip(ts, ts[1:]))
        assert observed_max <= HEARTBEAT_INTERVAL_S * 1.25, (
            f"observed narration gap {round(observed_max, 1)}s over "
            f"the bound")

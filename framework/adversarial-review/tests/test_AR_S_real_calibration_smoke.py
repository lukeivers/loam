# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.10 real-run smoke (opt-in) — a REAL isolated critic against a seeded
-flaw artifact reads back a nonzero catch rate. Proves the reviewer actually
catches planted flaws end-to-end (not just that the scoring logic works).

Opt-in (makes real subscription `claude -p` spawns via the sealed isolation):
    AR_REAL_CALIBRATION=1 python -m pytest tests/test_AR_S_real_calibration_smoke.py -q -s
Default: skipped, so the suite stays deterministic + offline."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SEEDED = Path(__file__).resolve().parents[1] / "calibration" / "seeded"
if str(_SEEDED) not in sys.path:
    sys.path.insert(0, str(_SEEDED))


@pytest.mark.skipif(
    os.environ.get("AR_REAL_CALIBRATION") != "1",
    reason="opt-in real-spawn calibration; set AR_REAL_CALIBRATION=1",
)
def test_AR_S_real_critic_catches_seeded_flaws():
    import revenue_memo as rm

    from adversarial_review.calibration import calibrate

    result = calibrate(rm.ARTIFACT, rm.OBJECTIVE, rm.FLAWS, tier="STANDARD")
    assert result.ran is True, "the isolated critic did not run"
    # A genuinely-harsh reviewer catches the majority of glaring planted flaws.
    assert result.catch_rate >= 0.5, (
        f"catch rate {result.catch_rate} too low — caught {result.caught}, "
        f"missed {result.missed}"
    )

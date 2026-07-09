# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.CDX.1 real-run smoke (opt-in, owner-gated) — a REAL ``codex exec`` critic
leg against a seeded-flaw artifact reads back a nonzero catch rate. Proves the
LIVE Codex leg actually catches a planted flaw end-to-end (the model-quality
claim the deterministic AC.CDX.1 test defers per D-CDX.5).

Owner-gated (needs ``codex`` installed + ChatGPT sign-in, D2; the plan's own
dependency line, ~5 min):
    AR_REAL_CODEX=1 python -m pytest tests/test_AR_S_real_codex_smoke.py -q -s
Default: skipped, and auto-skips if ``codex`` is not on PATH — so the suite
stays deterministic + offline and CI without codex never fails on it."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

_SEEDED = Path(__file__).resolve().parents[1] / "calibration" / "seeded"
if str(_SEEDED) not in sys.path:
    sys.path.insert(0, str(_SEEDED))


@pytest.mark.skipif(
    os.environ.get("AR_REAL_CODEX") != "1" or shutil.which("codex") is None,
    reason="opt-in live-codex calibration; set AR_REAL_CODEX=1 with codex installed + signed in",
)
def test_AR_S_real_codex_leg_catches_seeded_flaws():
    import revenue_memo as rm

    from adversarial_review.calibration import calibrate
    from adversarial_review.codex import codex_critic_registry

    # Codex-only CRITIC so the catch is attributable to the live codex leg.
    registry = codex_critic_registry(include_claude=False)
    result = calibrate(rm.ARTIFACT, rm.OBJECTIVE, rm.FLAWS, registry=registry)
    assert result.ran is True, "the live codex leg did not run (auth? install?)"
    assert result.catch_rate >= 0.5, (
        f"catch rate {result.catch_rate} too low — caught {result.caught}, "
        f"missed {result.missed}"
    )

"""Shared fixtures for the build-from-intent OA tests.

``live_bfi_run`` performs ONE full live run of the general path on a
fresh workspace (real model dispatches, real web research, real build
agents) and shares it session-wide so the three outcome-altitude
tests (AC.GEN.OA / AC.DGR.OA / AC.PRG.OA) assert against the same
honest run instead of paying for three.  Env-gated per the
component's live-test convention: BFI_REAL_CLAUDE=1.

The ask is deliberately OFF the back-office trio (a sports-league
scheduling domain) so no vertical shortcut could help — the same
anti-overfit posture the S6 off-vertical probe institutionalises.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Composed for these OA tests alone; exists in no pipeline prompt,
# brief, or fixture.
LIVE_OA_ASK = (
    "I help run a small rec soccer league and every season I waste a "
    "weekend turning the team list into a week-by-week schedule where "
    "every team plays every other team once and nobody plays twice in "
    "the same week - can you make me something that does that"
)


@pytest.fixture(scope="session")
def live_bfi_run():
    if os.environ.get("BFI_REAL_CLAUDE") != "1":
        pytest.skip("live full-path run; set BFI_REAL_CLAUDE=1 to run")
    from handsoff_loop.build_from_intent import run_build_from_intent

    workspace = Path(tempfile.mkdtemp(prefix="bfi-oa-live-"))
    t_start = time.time()
    narrated_ts: list[float] = []

    def _say(line: str) -> None:
        narrated_ts.append(time.time())

    result = run_build_from_intent(
        LIVE_OA_ASK,
        workspace_dir=workspace,
        say=_say,
        # Hands-off: standing agreement at the gate; questions (if
        # any) recorded as unanswered human gates — honest, logged.
        approve_fn=None,
        answer_fn=None,
        wall_ceiling_s=3000,
    )
    return {
        "ask": LIVE_OA_ASK,
        "workspace": workspace,
        "t_start": t_start,
        "result": result,
        "narrated_ts": narrated_ts,
    }

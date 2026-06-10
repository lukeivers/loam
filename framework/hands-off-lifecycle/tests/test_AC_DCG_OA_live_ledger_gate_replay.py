# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.DCG.OA (outcome-altitude: true) — through the production gate
entry point against the LIVE ledger with NO pre-arranged state:

  (a) a draft asserting the Tilth raise size "is an open
      contradiction" draws a steer citing the $750k ruling;
  (b) a draft calling a genuinely-open ledger question open draws
      none.

The second half of the $750k failure-surface, replayed and caught: on
2026-06-09 the persona told the owner the raise number was an open
contradiction between $400k and $750k — hours after the owner had
ruled it. The gate now holds the ledger as ground truth at send time.

Runs with the hook's production runtime shape (cwd = the live
workspace, exactly how the draft-gate hook executes). Skips when the
live ledger is absent (CI / fresh machine).

Memory recall cycle, Slice 5.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from draft_gate import Verdict, gate  # noqa: E402


LIVE_WORKSPACE = Path.home() / "pos3"
LIVE_DECISIONS = LIVE_WORKSPACE / "workspace" / ".loam" / "memory" / "decisions"


def _live_records_present() -> bool:
    if not LIVE_DECISIONS.is_dir():
        return False
    names = [p.name.lower() for p in LIVE_DECISIONS.glob("*.md")]
    return any("tilth" in n for n in names) and any(
        "frame-kernel" in n for n in names
    )


@pytest.mark.skipif(
    not _live_records_present(),
    reason="live ledger records absent (CI / fresh machine)",
)
def test_AC_DCG_OA_reopened_tilth_ruling_caught_live(monkeypatch) -> None:
    monkeypatch.chdir(LIVE_WORKSPACE)  # the hook's production runtime cwd
    result = gate(
        "Heads up: the Tilth raise size is an open contradiction in our "
        "notes — I see both numbers floating around."
    )
    assert result.verdict is Verdict.FLAG, (
        f"expected a FLAG steer; got {result.verdict}: {result.reasons}"
    )
    dcg = [
        r
        for r in result.reasons
        if r.label == "decision-claim-contradicts-ledger"
    ]
    assert dcg, f"expected the decision steer; reasons: {result.reasons}"
    assert "750" in dcg[0].detail, "the steer cites the $750k ruling"
    assert "14053" in dcg[0].detail, "the steer cites the source evidence"
    assert not result.blocked(), "steer-not-block: the send is never refused"


@pytest.mark.skipif(
    not _live_records_present(),
    reason="live ledger records absent (CI / fresh machine)",
)
def test_AC_DCG_OA_genuinely_open_question_passes_live(monkeypatch) -> None:
    monkeypatch.chdir(LIVE_WORKSPACE)
    result = gate(
        "The frame-kernel dispatch-pack activation timing in pos3 "
        "remains undecided — your call on when."
    )
    dcg = [
        r
        for r in result.reasons
        if r.label == "decision-claim-contradicts-ledger"
    ]
    assert dcg == [], (
        f"a genuinely-open ledger question drew a steer: {dcg}"
    )

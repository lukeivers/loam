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

"""AC.DCGID.OA (outcome-altitude: true) — through the production gate
entry point against the LIVE ledger with NO pre-arranged state, run
with the hook's production cwd (the live workspace):

  (a) the exact false-positive pair — the genuinely-OPEN question
      "Which model runs substantive loam build work, and what happens
      on a model stall?" (an on-file record whose status is NOT ruled)
      vs the UNRELATED ruled FBM co-citation record that merely shares
      claim-language + the ubiquitous "loam" token — does NOT produce a
      ``decision-claim-contradicts-ledger`` reason; AND
  (b) a genuine same-question contradiction (re-opening the FBM ruled
      question, sharing its DISTINCTIVE identity tokens) DOES produce
      that reason.

This is the live-ledger replay of the question-identity fix: it
reaches the real production gate, the real corpus-frequency read, and
the real ledger — no seam, no synthetic state. Skips when the live
ledger is absent (CI / fresh machine), matching the DCG.OA convention.

dcg-question-identity-match, owner ruling D-DCGID.1.
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

from draft_gate import gate  # noqa: E402


LIVE_WORKSPACE = Path.home() / "pos3"
LIVE_DECISIONS = LIVE_WORKSPACE / "workspace" / ".loam" / "memory" / "decisions"


def _live_records_present() -> bool:
    if not LIVE_DECISIONS.is_dir():
        return False
    names = [p.name.lower() for p in LIVE_DECISIONS.glob("*.md")]
    # the false-positive pair's two records: the open model-stall record
    # and the ruled FBM co-citation record.
    return any("fbm-co-citation" in n for n in names) and any(
        "which-model-runs-substantive-loam-build" in n for n in names
    )


def _dcg_reasons(result) -> list:
    return [
        r
        for r in result.reasons
        if r.label == "decision-claim-contradicts-ledger"
    ]


@pytest.mark.skipif(
    not _live_records_present(),
    reason="live ledger false-positive-pair records absent (CI / fresh machine)",
)
def test_AC_DCGID_OA_open_question_does_not_flag_unrelated_ruled(
    monkeypatch,
) -> None:
    monkeypatch.chdir(LIVE_WORKSPACE)  # the hook's production runtime cwd
    draft = (
        '"Which model runs substantive loam build work, and what happens '
        'on a model stall?" remains undecided.'
    )
    result = gate(draft)
    assert _dcg_reasons(result) == [], (
        "a genuinely-open question sharing only claim-language + the "
        f"ubiquitous 'loam' token false-positived: {_dcg_reasons(result)}"
    )


@pytest.mark.skipif(
    not _live_records_present(),
    reason="live ledger false-positive-pair records absent (CI / fresh machine)",
)
def test_AC_DCGID_OA_same_question_reopen_still_flags(monkeypatch) -> None:
    monkeypatch.chdir(LIVE_WORKSPACE)
    # lower-cased "fbm" so an incidental Layer-1 ALLCAPS leak does not
    # mask the decision-layer behaviour this OA test isolates (the
    # ruled record's distinctive identity tokens still resolve).
    draft = (
        "The fbm co-citation spread and power-law activation question "
        "remains undecided."
    )
    result = gate(draft)
    dcg = _dcg_reasons(result)
    assert dcg, (
        "a genuine same-question reopen (sharing distinctive identity "
        "tokens) must still flag against the live ledger"
    )

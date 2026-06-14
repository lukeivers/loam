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

"""AC.DCGID.2/.3/.4 — through ``check_decision_claims`` with a synthetic
ledger (the ``ledger_query=`` seam, deterministic, no live dependency):

  * .2 — a genuinely-open question that shares ONLY generic claim-
    language with an unrelated ruled record draws NO steer.
  * .3 — a draft that re-opens the SAME question as a ruled record
    (sharing its distinctive identity tokens) STILL draws the steer
    (recall preserved).
  * .4 — a corpus-frequency read error never raises into the send path;
    the identity filter degrades to the stopword leg and the gate
    stays fail-open.

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

from claim_guard import check_decision_claims  # noqa: E402
from draft_gate import Verdict, gate  # noqa: E402

from loam.primary_persona.decision_ledger import (  # noqa: E402
    search_decisions,
    write_decision,
)


@pytest.fixture()
def ledger(tmp_path: Path):
    # An UNRELATED ruled record. Its declared vocabulary shares only
    # generic claim-language with the open-question draft below — no
    # question identity.
    write_decision(
        tmp_path,
        question="What happens to the FBM co-citation spread after the eval?",
        ruling="Spread: KILL. Activation: FIX behind a default-off flag.",
        reasoning="The eval showed the spread underperforms the BM25 floor.",
        entities=("FBM", "co-citation", "spread", "power-law"),
        aliases=("the spread",),
        source="fbm-eval-results-2026-06-07.md",
        workstream="memory",
    )

    def query(subject: str):
        import re

        tokens = re.findall(r"[A-Za-z0-9_$]+", subject)
        return search_decisions(tmp_path, tokens)

    return query


def test_AC_DCGID_2_open_question_sharing_only_claim_language_passes(
    ledger,
) -> None:
    # The open question shares with the FBM record only the generic
    # tokens "what"/"happens"/"the" (all stopwords) — NO distinctive
    # identity overlap → no steer.
    draft = (
        '"What happens to the deployment schedule next sprint?" '
        "remains undecided."
    )
    steers = check_decision_claims(draft, ledger_query=ledger)
    assert steers == [], (
        f"a genuinely-open question sharing only claim-language drew a "
        f"steer: {steers}"
    )


def test_AC_DCGID_3_same_question_reopen_still_flags(ledger) -> None:
    # A real re-open of the FBM ruled question — shares the record's
    # DISTINCTIVE identity tokens (fbm / co-citation / spread) → the
    # steer must still fire (recall preserved).
    draft = "The FBM co-citation spread question remains undecided."
    steers = check_decision_claims(draft, ledger_query=ledger)
    assert steers, "a genuine same-question reopen must still steer"
    assert steers[0].label == "decision-claim-contradicts-ledger"
    assert "KILL" in steers[0].detail, "the steer carries the ruling"


def test_AC_DCGID_4_corpus_frequency_error_never_raises(monkeypatch) -> None:
    # The production path computes corpus frequency; if that read
    # raises, the identity filter degrades to the stopword leg and the
    # gate stays fail-open (no exception into the send path).
    import claim_guard as cg_mod

    def boom_freq() -> dict:
        raise RuntimeError("ledger corpus read failed")

    def open_query(subject: str):
        from loam.primary_persona.decision_ledger import search_decisions
        # empty live query — no records, the path still exercises the
        # corpus-frequency branch.
        return []

    monkeypatch.setattr(cg_mod, "_ledger_corpus_frequency", boom_freq)
    monkeypatch.setattr(cg_mod, "_default_ledger_query", open_query)
    result = gate("The deployment schedule remains undecided.")
    assert result.verdict in (Verdict.PASS, Verdict.FLAG)
    assert not result.blocked()

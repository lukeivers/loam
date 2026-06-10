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

"""AC.DCG.1 — when an outbound draft asserts decision-state — "X is
open / undecided / unresolved" or "we never decided X" — about a
subject resolvable to a ``status: ruled`` decision record, the guard
steers with the record's ruling + source evidence before the send,
under the sealed guard's existing contracts (model-facing-only,
steer-not-block, fail-open, no LLM/API).

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

from claim_guard import (  # noqa: E402
    check_decision_claims,
    detect_decision_state_claims,
)
from draft_gate import Verdict, gate  # noqa: E402

from loam.primary_persona.decision_ledger import (  # noqa: E402
    search_decisions,
    write_decision,
)


@pytest.fixture()
def ledger(tmp_path: Path):
    write_decision(
        tmp_path,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "raise", "valuation"),
        aliases=("the raise",),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
    )

    def query(subject: str):
        import re

        tokens = re.findall(r"[A-Za-z0-9_$]+", subject)
        return search_decisions(tmp_path, tokens)

    return query


@pytest.mark.parametrize(
    "draft",
    [
        "The Tilth raise size is an open contradiction we still need to settle.",
        "The Tilth raise amount remains undecided.",
        "We never decided the Tilth raise size.",
        "There is no ruling on the Tilth raise yet.",
        "The Tilth raise question is still unresolved.",
    ],
)
def test_AC_DCG_1_reopened_ruling_steered_with_evidence(
    draft: str, ledger
) -> None:
    steers = check_decision_claims(draft, ledger_query=ledger)
    assert steers, f"expected a steer for: {draft!r}"
    s = steers[0]
    assert s.label == "decision-claim-contradicts-ledger"
    assert "$750,000" in s.detail, "the steer carries the ruling"
    assert "telegram message 14053" in s.detail, (
        "the steer carries the source evidence"
    )


def test_AC_DCG_1_detection_is_sentence_scoped() -> None:
    claims = detect_decision_state_claims(
        "The build is green. The raise size remains undecided. Tests pass."
    )
    assert len(claims) == 1
    assert "raise size" in claims[0].subject


def test_AC_DCG_1_steer_not_block_through_production_gate(
    monkeypatch, tmp_path: Path, ledger
) -> None:
    # Through the production gate entry point the decision steer is a
    # FLAG (steer-not-block) — never a BLOCK, never a refused send.
    import claim_guard as cg_mod

    monkeypatch.setattr(cg_mod, "_default_ledger_query", ledger)
    result = gate("The Tilth raise amount remains undecided.")
    assert result.verdict is Verdict.FLAG
    assert any(
        r.label == "decision-claim-contradicts-ledger" for r in result.reasons
    )
    assert not result.blocked()


def test_AC_DCG_1_fail_open_when_ledger_unreachable(monkeypatch) -> None:
    # A broken ledger query never blocks (and never raises) — the
    # sealed fail-open contract extends to the new ground-truth source.
    import claim_guard as cg_mod

    def boom(subject: str):
        raise RuntimeError("ledger unreachable")

    monkeypatch.setattr(cg_mod, "_default_ledger_query", boom)
    result = gate("The Tilth raise amount remains undecided.")
    assert result.verdict in (Verdict.PASS, Verdict.FLAG)
    assert not result.blocked()

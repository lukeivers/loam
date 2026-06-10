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

"""AC.DCG.2 — true decision-state claims (genuinely-open questions
called open) and ordinary prose pass with no steer, and the existing
work-state precision corpus (AC.CLG.3) still passes unchanged.

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

from loam.primary_persona.decision_ledger import (  # noqa: E402
    search_decisions,
    write_decision,
)


@pytest.fixture()
def open_ledger(tmp_path: Path):
    write_decision(
        tmp_path,
        question="Who is Aaron in the deal?",
        ruling="(open)",
        reasoning="Owner has not ruled yet.",
        entities=("Aaron", "deal"),
        source="proposal review, 2026-06-07",
        status="open",
    )

    def query(subject: str):
        import re

        tokens = re.findall(r"[A-Za-z0-9_$]+", subject)
        return search_decisions(tmp_path, tokens)

    return query


def test_AC_DCG_2_genuinely_open_called_open_passes(open_ledger) -> None:
    steers = check_decision_claims(
        "Who Aaron is in the deal remains undecided — flagging it for "
        "your call.",
        ledger_query=open_ledger,
    )
    assert steers == [], (
        "a genuinely-open ledger question called open must draw no steer"
    )


def test_AC_DCG_2_unknown_subject_passes(open_ledger) -> None:
    steers = check_decision_claims(
        "The conference venue is still an open question.",
        ledger_query=open_ledger,
    )
    assert steers == [], "no ledger record => no steer (no eternal-negative)"


@pytest.mark.parametrize(
    "prose",
    [
        "The door is open, come on in whenever.",
        "The PR is open and waiting on review.",
        "Port 8080 is open on that host.",
        "We decided to go with the narrow fence yesterday.",
        "No decision needed here — it's mechanical.",
        "The tests pass and the build is green.",
        "I'll keep the file open while we work.",
        "She remains the strongest candidate for the role.",
    ],
)
def test_AC_DCG_2_ordinary_prose_never_detected(prose: str) -> None:
    assert detect_decision_state_claims(prose) == [], (
        f"ordinary prose drew a decision-state detection: {prose!r}"
    )


def test_AC_DCG_2_no_ledger_query_for_prose(open_ledger) -> None:
    # AC.DCG.2 + the hot-path discipline: no detection => the ledger is
    # never queried at all.
    calls = []

    def counting_query(subject: str):
        calls.append(subject)
        return []

    check_decision_claims(
        "The tests pass and the build is green.",
        ledger_query=counting_query,
    )
    assert calls == []

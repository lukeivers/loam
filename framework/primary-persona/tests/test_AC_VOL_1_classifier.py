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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.VOL.1 — write-side volatility classifier.

``classify_volatility`` is deterministic + stdlib-only and sorts a fact
into DURABLE / HARD / SOFT on the named tells. The D2 safe bias: a hard
tell co-occurring with a durable-decision signal de-escalates to SOFT
(a ruling is never hard-excluded).
"""

from __future__ import annotations

import pytest

from loam.primary_persona.file_memory import (
    VOLATILITY_DURABLE,
    VOLATILITY_HARD,
    VOLATILITY_SOFT,
    classify_volatility,
)


# One case per named HARD tell — each must classify HARD (no durable veto).
HARD_CASES = [
    ("is-broken", "the deploy shim is broken right now"),
    ("up-down", "the graphiti service is down again"),
    ("back-up", "the telegram bridge is back up"),
    ("current-version", "the current version is v1.8.0"),
    ("running-version", "we are now on v2 of the indexer"),
    ("latest-sha", "the latest commit is a7c9f1b2ac1f0c62ab"),
    ("head-at", "HEAD is at the spine-plan commit"),
    ("pending-count", "there are 3 PRs pending review"),
    ("whos-allowed", "alan is approved on the allowlist"),
]

# Borderline freshness language with no hard operational claim → SOFT.
SOFT_CASES = [
    ("right-now", "right now the corpus has the new lens text"),
    ("as-of-today", "as of today the roadmap leads with the money push"),
    ("at-the-moment", "at the moment the litrpg loop is paused"),
]

# Durable rulings — no hard tell, no soft freshness language → DURABLE.
DURABLE_CASES = [
    ("ruling", "we decided every LLM call goes through claude -p"),
    ("policy", "the rule is no Anthropic API key, subscription only"),
    ("plain-fact", "Luke lives in Apple Valley, Minnesota"),
    ("design", "the prime lens is per-user-tuned translation"),
]

# D2 — a hard tell that co-occurs with a durable-decision signal stays
# visible-but-annotated (SOFT), never hard-excluded.
AMBIGUOUS_CASES = [
    (
        "ruling-with-broken",
        "we decided that whenever the shim is broken we fall back to the venv",
    ),
    (
        "policy-with-pending",
        "going forward, 5 items pending is the cap before we halt the queue",
    ),
]


@pytest.mark.parametrize("label,text", HARD_CASES, ids=[c[0] for c in HARD_CASES])
def test_AC_VOL_1_hard_tells_classify_hard(label: str, text: str) -> None:
    assert classify_volatility(text) == VOLATILITY_HARD, (
        f"{label!r} should classify HARD: {text!r}"
    )


@pytest.mark.parametrize("label,text", SOFT_CASES, ids=[c[0] for c in SOFT_CASES])
def test_AC_VOL_1_soft_tells_classify_soft(label: str, text: str) -> None:
    assert classify_volatility(text) == VOLATILITY_SOFT, (
        f"{label!r} should classify SOFT: {text!r}"
    )


@pytest.mark.parametrize(
    "label,text", DURABLE_CASES, ids=[c[0] for c in DURABLE_CASES]
)
def test_AC_VOL_1_durable_rulings_classify_durable(label: str, text: str) -> None:
    assert classify_volatility(text) == VOLATILITY_DURABLE, (
        f"{label!r} should classify DURABLE: {text!r}"
    )


@pytest.mark.parametrize(
    "label,text", AMBIGUOUS_CASES, ids=[c[0] for c in AMBIGUOUS_CASES]
)
def test_AC_VOL_1_durable_signal_vetoes_hard_to_soft(label: str, text: str) -> None:
    # D2 — the dangerous failure (a durable decision hard-excluded) is
    # structurally prevented: ambiguity de-escalates HARD -> SOFT.
    assert classify_volatility(text) == VOLATILITY_SOFT, (
        f"{label!r} (hard tell + durable signal) must de-escalate to SOFT: {text!r}"
    )


def test_AC_VOL_1_deterministic_and_failsafe() -> None:
    sample = "the indexer is down right now"
    assert classify_volatility(sample) == classify_volatility(sample)
    # Fail-safe: a non-str / empty input resolves to DURABLE (never drops).
    assert classify_volatility("") == VOLATILITY_DURABLE
    assert classify_volatility(None) == VOLATILITY_DURABLE  # type: ignore[arg-type]

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

"""AC.KP9.2 — Layer C draft-vs-active-constraint contradiction check.

A draft that contradicts an active high-salience constraint-memory (a
seeded canon rule, a sealed ruling) is FLAGGED before send; a compliant
draft passes. This is the mid-draft tonight-failure catch the
UserPromptSubmit hook structurally cannot make (design §1 fix #2).

Per RF-4 / D-KP9.2 the active-constraint set is the narrow seeded set
(canon rules + sealed rulings) — precision-first. The seeded
tonight-failure case: a draft placing Aaron at his own pod contradicts
the on-file canon rule that Aaron is at Priya's pod.

Method is the builder's call (ODD §1.1): the contradiction + the
compliant case are exercised against the seeded narrow set, and a
custom constraint tuple proves the check generalises.
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

from draft_gate import (  # noqa: E402
    Constraint,
    Verdict,
    gate,
    layerC_check,
)


def test_AC_KP9_2_litrpg_canon_contradiction_flagged() -> None:
    """The seeded tonight-failure case: a draft placing Aaron at his own
    pod contradicts the canon rule (Aaron is at Priya's pod) → FLAG."""
    draft = "In this scene Aaron settles in at his own pod and starts the run."
    result = gate(draft)
    assert result.flagged(), f"contradiction should FLAG: {result.verdict}"
    assert result.verdict == Verdict.FLAG
    assert any(r.layer == "LC" for r in result.reasons)
    assert any("aaron" in r.label for r in result.reasons)


def test_AC_KP9_2_compliant_canon_draft_passes() -> None:
    """A draft carrying the correct value (Aaron at Priya's pod) passes."""
    draft = "Aaron settles in at Priya's pod and starts the run."
    result = gate(draft)
    assert result.passed(), (
        f"compliant draft should PASS: {result.verdict} "
        f"{[r.label for r in result.reasons]}"
    )


def test_AC_KP9_2_sealed_ruling_contradiction_flagged() -> None:
    """A draft proposing an Anthropic API key contradicts the sealed
    no-API-key ruling → FLAG (the constraint set includes sealed rulings,
    not just canon)."""
    draft = "We can call the model by adding an api key to the env."
    result = gate(draft)
    assert result.flagged()
    assert any(r.label == "loam-no-anthropic-api-key" for r in result.reasons)


def test_AC_KP9_2_off_topic_draft_passes() -> None:
    """A draft that never touches a constraint topic passes Layer C."""
    draft = "Your dinner reservation is confirmed for seven o'clock tonight."
    result = gate(draft)
    assert result.passed()


def test_AC_KP9_2_custom_constraint_generalises() -> None:
    """Layer C generalises to any tagged constraint, not just the seed."""
    custom = (
        Constraint(
            slug="hero-name-is-mara",
            assertion="The protagonist's name is Mara, never Sara.",
            topic_tokens=("protagonist", "hero", "mara", "sara"),
            correct_value=("mara",),
            violation_values=("sara",),
            kind="canon",
        ),
    )
    contradict = layerC_check(
        "The hero, Sara, draws her blade.", constraints=custom
    )
    assert any(r.label == "hero-name-is-mara" for r in contradict)
    ok = layerC_check("The hero, Mara, draws her blade.", constraints=custom)
    assert not ok

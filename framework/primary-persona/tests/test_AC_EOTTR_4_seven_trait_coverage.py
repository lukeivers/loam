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

"""AC.EOTTR.4 — Seven-trait coverage.

Outcome: every one of the seven persona top-value traits is named in
``TRAIT_HEURISTICS`` and has at least one keyword/heuristic
configured (a non-empty signal list — positive_signals OR
anti_signals counts). ``evaluate_all_traits`` returns exactly seven
verdicts, one per named trait.
"""

from __future__ import annotations


EXPECTED_TRAITS = {
    "Autonomy",
    "Asymmetric problem solving",
    "Parallelism",
    "Test theories before acting on them",
    "Calibration",
    "Self-correction",
    "Pruning",
}


def test_AC_EOTTR_4_seven_traits_named() -> None:
    """``TRAIT_HEURISTICS`` carries entries for exactly the seven
    persona top-value traits — no more, no fewer, exact names."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        TRAIT_HEURISTICS,
    )

    names = {h.trait for h in TRAIT_HEURISTICS}
    assert names == EXPECTED_TRAITS


def test_AC_EOTTR_4_every_trait_has_at_least_one_keyword() -> None:
    """Every trait has at least one positive_signal OR anti_signal
    keyword/heuristic configured. A trait with both lists empty
    would be unscoreable."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        TRAIT_HEURISTICS,
    )

    for h in TRAIT_HEURISTICS:
        total_signals = len(h.positive_signals) + len(h.anti_signals)
        assert total_signals >= 1, (
            f"trait {h.trait!r} has no positive_signals and no "
            "anti_signals — it cannot produce a meaningful verdict"
        )


def test_AC_EOTTR_4_evaluate_returns_one_verdict_per_trait() -> None:
    """``evaluate_all_traits`` returns exactly 7 verdicts, one per
    named trait, in the same order as ``TRAIT_HEURISTICS``."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        TRAIT_HEURISTICS,
        evaluate_all_traits,
    )

    verdicts = evaluate_all_traits("some assistant reply text")
    assert len(verdicts) == 7
    for verdict, heuristic in zip(verdicts, TRAIT_HEURISTICS):
        assert verdict["trait"] == heuristic.trait


def test_AC_EOTTR_4_positive_signal_yields_pass(tmp_path) -> None:
    """A text containing a positive_signal for the Autonomy trait
    produces a PASS verdict on that trait."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        evaluate_all_traits,
    )

    verdicts = evaluate_all_traits("dispatching the agent now.")
    autonomy = next(v for v in verdicts if v["trait"] == "Autonomy")
    assert autonomy["verdict"] == "PASS"
    assert "dispatching" in autonomy["reason"]


def test_AC_EOTTR_4_anti_signal_yields_concern(tmp_path) -> None:
    """A text containing an anti_signal for the Autonomy trait
    produces a CONCERN verdict on that trait."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        evaluate_all_traits,
    )

    verdicts = evaluate_all_traits("Are you sure? I can wait.")
    autonomy = next(v for v in verdicts if v["trait"] == "Autonomy")
    assert autonomy["verdict"] == "CONCERN"
    assert "are you sure" in autonomy["reason"].lower()

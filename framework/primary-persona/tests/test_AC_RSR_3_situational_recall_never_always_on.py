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

"""AC.RSR.3 — situational recall: a rule fires only on a matching
situation, never always-on.

A rule surfaces on a turn whose detected situation is in the rule's
situation set, and to NO turn whose situation is outside it — including a
turn with HIGH topical overlap but a non-matching situation (no relevance
score can admit a rule). A rule with an empty situation set never fires.
The cautious detector emits NOTHING on an ambiguous turn.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace.retrieval import detect_situation


def _seed(tmp_path: Path) -> None:
    rs.write_rule(
        tmp_path,
        directive="Dispatch briefs carry scope only.",
        situation=["dispatching-subagent"],
        provenance=["feedback_agent_prompts_scope_only.md"],
    )


def test_AC_RSR_3_matching_situation_surfaces_the_rule(tmp_path: Path) -> None:
    _seed(tmp_path)
    hits = rs.rules_for_situation(tmp_path, ["dispatching-subagent"])
    assert [h.directive for h in hits] == ["Dispatch briefs carry scope only."]


def test_AC_RSR_3_non_matching_situation_surfaces_nothing(
    tmp_path: Path,
) -> None:
    _seed(tmp_path)
    assert rs.rules_for_situation(tmp_path, ["authoring-outbound-text"]) == []


def test_AC_RSR_3_empty_turn_situation_surfaces_nothing(tmp_path: Path) -> None:
    """The always-on failure mode's inverse: an empty detected-situation
    set (the cautious detector firing on nothing) matches NO rule."""
    _seed(tmp_path)
    assert rs.rules_for_situation(tmp_path, []) == []


def test_AC_RSR_3_empty_situation_rule_never_fires(tmp_path: Path) -> None:
    """A rule authored with an empty situation set is stored (parked) but
    never surfaces through recall — even for a turn with tags."""
    rs.write_rule(
        tmp_path,
        directive="A parked directive with no detectable situation.",
        situation=[],
        provenance=["feedback_x.md"],
    )
    # Stored on disk...
    assert len(rs.iter_rules(tmp_path)) == 1
    # ...but never recalled, for any situation.
    assert rs.rules_for_situation(tmp_path, ["dispatching-subagent"]) == []
    assert rs.rules_for_situation(tmp_path, ["authoring-outbound-text"]) == []


def test_AC_RSR_3_high_topical_overlap_non_matching_situation(
    tmp_path: Path,
) -> None:
    """A rule about dispatching does NOT surface on a turn that is topically
    ABOUT dispatching but whose SITUATION is authoring outbound text — the
    match is on the situation tag, never on topical/keyword relevance."""
    _seed(tmp_path)
    # The turn's detected situation is authoring-outbound-text (it is
    # composing an email), even though the email's subject is dispatching.
    situation = detect_situation(
        "draft an email to the team about our agent-dispatch policy"
    )
    assert "authoring-outbound-text" in situation
    assert "dispatching-subagent" not in situation
    assert rs.rules_for_situation(tmp_path, situation) == []


def test_AC_RSR_3_detector_silent_on_ambiguous_turn() -> None:
    """The cautious detector emits NO situation on an ambiguous turn — the
    deliberate under-fire bias (over-fire = over-injection reborn)."""
    for ambiguous in (
        "ok sounds good, continue",
        "what do you think about this?",
        "thanks, that works",
        "",
    ):
        assert detect_situation(ambiguous) == frozenset(), ambiguous


def test_AC_RSR_3_detector_fires_on_unambiguous_turn() -> None:
    assert "dispatching-subagent" in detect_situation(
        "dispatch a background agent to run the build"
    )
    assert "amending-sealed-component" in detect_situation(
        "run loam amend apply then seal"
    )

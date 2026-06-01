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

"""AC.INTENT.S — outcome-altitude: the four-step loop, real entry-point.

outcome-altitude: true — drive the REAL production ``run_first_run_intake`` on a
genuinely-empty instance (no pre-arranged state, isolated throwaway home) with a
scripted role-play answerer whose confirmation adds detail AND raises a doubt, and
assert ALL FOUR legs of the loop are visible in the transcript + the close
addresses the doubt. No STUB pre-arranged distillation: the loop runs end-to-end
through the production path (the disabled extractor's regex fallback distills, so
this is a faithful offline cold-walk; the smoke exercises the LLM extractor live).
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.first_run_intake import run_first_run_intake


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []
        self.prompts: dict[str, str] = {}

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        self.prompts[slug] = prompt
        return self._answers.get(slug, "")


def _empty_instance(tmp_path: Path):
    home = tmp_path / "home" / ".claude"
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)
    assert not home.exists()
    assert not (ws / ".loam").exists()
    return home, ws


def test_AC_INTENT_S_cold_walk_four_legs_visible_and_doubt_addressed(tmp_path: Path):
    home, ws = _empty_instance(tmp_path)

    answerer = ScriptedAnswerer(
        {
            "stop_start": (
                "writing listing descriptions, every night I'm staring at a "
                "blank page trying to make a split-level sound poetic"
            ),
            # The confirmation CONFIRMS and raises a concrete capability DOUBT —
            # leg 4 must adjust from this (address the doubt honestly).
            "confirm_proposal": (
                "yes that's it, but honestly I don't really understand how this "
                "would work — can it actually write something that sounds like me?"
            ),
        }
    )

    result = run_first_run_intake(
        ws,
        answerer=answerer,
        global_home=home,
        run_capability_ritual=False,
    )

    intake = result.intake
    slugs = [slug for slug, _ in intake.transcript]

    # Leg 1 (infer) + Leg 2 (surface-and-check): the inferred intent was proposed
    # back as a checkable hypothesis BEFORE the close.
    assert "stop_start" in slugs
    assert "confirm_proposal" in slugs
    # Leg 3 (check): the user's confirmation was read and the intent confirmed.
    assert intake.confirmed is True
    # The inferred intent appears as a hypothesis (the surface-and-check leg's
    # confirm prompt named it back before any close).
    assert "It sounds like you want" in answerer.prompts["confirm_proposal"]

    # Leg 4 (adjust): the close ADDRESSES the capability doubt honestly — it does
    # not restate the proposal and ignore the question (the smoke's PARTIAL gap),
    # and it makes no unqualified invented-capability claim (protection-floor).
    assert intake.has_leverage_idea
    close = " ".join(i.text for i in intake.leverage_ideas).lower()
    assert "your question" in close or "you review" in close or "judgment" in close
    assert "you review" in close or "the call stays yours" in close

    # Cold-walk fidelity: real seed landed in the isolated home (no pre-arranged
    # state was used; the production path ran).
    assert (home / "OBJECTIVES.md").exists()
    assert (home / "INTERACTION-MODEL.md").exists()

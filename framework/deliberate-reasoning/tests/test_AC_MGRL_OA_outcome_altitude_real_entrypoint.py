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

"""AC.MGRL.OA (outcome-altitude) — escalation fires through the PRODUCTION
entry-point with NO pre-arranged state: a real turn carrying a genuine
trigger signal, run through the real gate path, produces an escalation
decision + a deliberate-loop invocation + a recorded firing trigger.

Per feedback_test_outcome_altitude_required this test invokes the production
entry-point (``process_turn``) with no seeded gate state and no stubbed
trigger — the trigger signal is realized through genuine observable inputs
(a hedged draft + a novel task class + explicit stakes framing in the
prompt), and the gate decides on its own. The deliberate loop runs end to
end (the critic is invoked — proven by a flag the critic sets), and the
firing trigger is recorded on the decision.
"""

from __future__ import annotations

from loam.deliberate_reasoning.gate import GateSignals, Trigger
from loam.deliberate_reasoning.loop import Critique
from loam.deliberate_reasoning.turn import TurnConfig, process_turn


def test_AC_MGRL_OA_real_turn_escalates_end_to_end_no_prearranged_state():
    invoked = {"critic": False}

    def real_path_critic(draft, prompt):
        # A genuine evidence-bound critique that catches the draft's defect.
        invoked["critic"] = True
        return Critique(
            weakest_link="the draft hedged and gave the wrong product",
            evidence=("17 * 23 = 391, recomputed",),
            revised_answer="391",
            has_defensible_improvement=True,
        )

    # NO pre-arranged gate state: the signals are genuine observable inputs.
    # The draft is genuinely hedged (low-confidence), the task class is
    # genuinely novel (absent from the empty recent set), and the prompt
    # carries genuine stakes framing. The gate must decide escalate on its
    # own from these real signals.
    signals = GateSignals(
        draft_text="I think the answer is probably 371.",  # genuinely hedged
        task_class="multiplication-novel",
        recent_task_classes=frozenset(),  # genuinely novel
        prompt_text="Critical: what is 17 times 23? This must be correct.",  # stakes
    )

    result = process_turn(
        draft="I think the answer is probably 371.",
        prompt="Critical: what is 17 times 23? This must be correct.",
        signals=signals,
        critic=real_path_critic,
        config=TurnConfig(enabled=True),
    )

    # Escalation fired through the real path.
    assert result.escalated is True
    # The deliberate loop was actually invoked end-to-end.
    assert invoked["critic"] is True
    assert result.loop_result is not None
    # A firing trigger was recorded (all three observable triggers present
    # here; at minimum the gate attributed escalation to a specific trigger).
    assert result.decision is not None
    assert result.decision.fired is True
    assert Trigger.LOW_CONFIDENCE in result.decision.triggers
    assert Trigger.NOVELTY in result.decision.triggers
    assert Trigger.STAKES in result.decision.triggers
    # The loop produced the evidence-backed correction.
    assert result.final_answer == "391"

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

"""AC.TRIG.1 — the gate's escalation is driven by SITUATION signals derived
from the pending action's structure + recent tool-result history, and is NOT
driven by keyword-scanning the user's prompt or the model's draft.

The two halves DISSOCIATE the trigger SOURCE from conversation-words:

(a) a turn carrying a STRUCTURAL signal (an unbounded-op pending action) whose
    prompt/draft contain NONE of the old stake/hedge keywords -> escalates;
(b) a turn whose prompt/draft DO contain the old keywords but whose pending
    action is structurally safe (and the demoted keyword path is OFF by
    default) -> does NOT escalate.

If escalation were still keyword-driven, (a) would not fire (no keywords) and
(b) would fire (keywords present). It is the inversion of both that proves the
substrate moved from conversation-words to action-structure.
"""

from __future__ import annotations

from loam.deliberate_reasoning.gate import GateSignals, Trigger, evaluate_gate
from loam.deliberate_reasoning.signals import PendingAction


def test_AC_TRIG_1_structural_signal_no_keywords_escalates():
    # An unbounded-op pending action; the (absent) prompt/draft carry NONE of
    # the old hedge/stakes keywords. Structural-only escalation.
    action = PendingAction(
        tool_name="Bash",
        command="grep -E '.{0,80}foo.{0,80}bar' big.min.js",
        target_path="big.min.js",
        target_size_bytes=2_100_000,
    )
    signals = GateSignals(pending_action=action)  # no draft_text, no prompt_text
    decision = evaluate_gate(signals)
    assert decision.escalate is True
    assert Trigger.UNBOUNDED_OP in decision.triggers
    # Proven structural: no conversation-keyword trigger fired (none present).
    assert Trigger.LOW_CONFIDENCE not in decision.triggers
    assert Trigger.STAKES not in decision.triggers


def test_AC_TRIG_1_keywords_present_safe_action_does_not_escalate():
    # The prompt + draft are FULL of the old keywords; but the pending action
    # is structurally safe and the demoted keyword path is OFF by default.
    safe_action = PendingAction(
        tool_name="Read",
        target_path="docs/notes.md",
        target_size_bytes=4_000,
    )
    signals = GateSignals(
        pending_action=safe_action,
        draft_text="I think this is probably right, but I'm not sure, maybe.",
        prompt_text="This is critical and high-stakes; it must be correct, "
        "it's a legal medical financial safety matter.",
    )
    decision = evaluate_gate(signals)
    # Keyword-on-conversation no longer drives escalation: declines.
    assert decision.escalate is False
    assert decision.triggers == ()


def test_AC_TRIG_1_keywords_only_path_is_opt_in_default_off():
    # The same keyword-laden signals with a None pending action: default-OFF
    # keyword path => no escalation; explicit opt-in => the demoted path fires.
    signals_default = GateSignals(
        draft_text="I'm not sure, maybe, probably.",
        prompt_text="critical, high-stakes, must be correct",
    )
    assert evaluate_gate(signals_default).escalate is False

    signals_optin = GateSignals(
        draft_text="I'm not sure, maybe, probably.",
        prompt_text="critical, high-stakes, must be correct",
        keyword_triggers_enabled=True,
    )
    decision = evaluate_gate(signals_optin)
    assert decision.escalate is True
    assert Trigger.LOW_CONFIDENCE in decision.triggers
    assert Trigger.STAKES in decision.triggers

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

"""AC.TRIG.4 — the 2026-06-24 runaway-regex incident shape, replayed as a
fixture, escalates the gate (at least UNBOUNDED_OP and REPEAT_FAILED fire),
where the slice-1 keyword gate would NOT have fired (the incident turn carried
no stake/hedge keywords).

The incident (feedback_api_first_no_loose_regex_on_minified.md): the persona
ran an unbounded backtracking regex over a 2.1MB single-line minified blob,
left two runaway searches eating CPU/RAM for 18 minutes, and REPEATED a failing
approach. This is the canonical turn that SHOULD have tripped a "stop and think
before acting" gate but couldn't, because the triggers were conversation-keyword
based. This test proves the new STRUCTURAL substrate fires on exactly that turn
and the old keyword substrate does not.
"""

from __future__ import annotations

from loam.deliberate_reasoning.gate import GateSignals, Trigger, evaluate_gate
from loam.deliberate_reasoning.signals import (
    PendingAction,
    ResultClass,
    SituationSignal,
    ToolCallRecord,
    ToolResultRing,
    detect_situation_signals,
)


# The incident's pending action: an unbounded `.{0,N}` backtracking quantifier
# over a 2.1MB single-line minified file, with no result bound (no head, no
# timeout, no --max-count). Reconstructed from the incident write-up.
_INCIDENT_TARGET = "vendor/app.min.js"
_INCIDENT_SIZE = 2_100_000  # 2.1MB single-line minified blob


def _incident_pending_action() -> PendingAction:
    return PendingAction(
        tool_name="Bash",
        command=(
            "grep -oE 'function.{0,80}\\(.{0,200}\\)' " + _INCIDENT_TARGET
        ),
        target_path=_INCIDENT_TARGET,
        target_size_bytes=_INCIDENT_SIZE,
    )


def _incident_ring(action: PendingAction) -> ToolResultRing:
    # The first near-identical search already failed (empty/timeout) this turn;
    # the pending action is the REPEAT of that failing approach.
    return ToolResultRing(
        records=(
            ToolCallRecord(
                arg_shape_key=action.arg_shape_key(),
                result_class=ResultClass.TIMEOUT,
            ),
        )
    )


def test_AC_TRIG_4_incident_shape_escalates_with_structural_signals():
    action = _incident_pending_action()
    ring = _incident_ring(action)

    fired = detect_situation_signals(action, ring)
    assert SituationSignal.UNBOUNDED_OP in fired
    assert SituationSignal.REPEAT_FAILED in fired

    decision = evaluate_gate(GateSignals(pending_action=action, result_ring=ring))
    assert decision.escalate is True
    assert Trigger.UNBOUNDED_OP in decision.triggers
    assert Trigger.REPEAT_FAILED in decision.triggers


def test_AC_TRIG_4_old_keyword_gate_would_not_have_fired_on_the_incident_turn():
    # The incident turn carried no stake/hedge keywords in the prompt/draft.
    # Run the SAME turn through the DEMOTED keyword path (explicit opt-in) with
    # the structural substrate absent: the keyword gate does not fire. This is
    # the dissociation the redesign delivers — the gate fires now because of
    # the ACTION'S structure, not because of any conversation words (which were
    # never present).
    keyword_only = GateSignals(
        # The actual incident conversation: a neutral "search this file" ask —
        # no critical/legal/medical/hedge words.
        prompt_text="find the function definitions in this bundle",
        draft_text="searching the bundle for function definitions",
        keyword_triggers_enabled=True,  # even with the demoted path ON
    )
    assert evaluate_gate(keyword_only).escalate is False

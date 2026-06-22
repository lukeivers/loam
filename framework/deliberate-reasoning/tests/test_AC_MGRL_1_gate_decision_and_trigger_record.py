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

"""AC.MGRL.1 — on every turn the harness produces an escalate /
don't-escalate decision AND records which trigger (or none) fired, from
observable signals, with NO LLM call on the don't-escalate path.

The gate module is LLM-free by construction (it imports only re / enum /
dataclasses — no print-client, no anthropic). This test pins both halves of
the AC: (a) a turn with a trigger signal -> escalate + the firing trigger
recorded; (b) a turn with no signal -> don't-escalate + no trigger, and
(c) structurally, the gate makes no LLM call on any path.
"""

from __future__ import annotations

import sys

from loam.deliberate_reasoning.gate import GateSignals, Trigger, evaluate_gate


def test_AC_MGRL_1_trigger_present_escalates_and_records_trigger():
    # A hedged draft carries the low-confidence signal.
    signals = GateSignals(draft_text="I think it's probably 42.")
    decision = evaluate_gate(signals)
    assert decision.escalate is True
    assert Trigger.LOW_CONFIDENCE in decision.triggers


def test_AC_MGRL_1_no_trigger_does_not_escalate_and_records_none():
    # A confident, non-novel, non-stakes turn carries no signal.
    signals = GateSignals(
        draft_text="The answer is 42.",
        task_class="arithmetic",
        recent_task_classes=frozenset({"arithmetic"}),
        prompt_text="What is 6 times 7?",
    )
    decision = evaluate_gate(signals)
    assert decision.escalate is False
    assert decision.triggers == ()
    assert decision.fired is False


def test_AC_MGRL_1_gate_makes_no_llm_call_on_any_path():
    # The gate is LLM-free by construction: its module must not import any
    # print-client / anthropic surface. Verifying the loaded module's
    # dependency graph carries no LLM client is the structural guard.
    import loam.deliberate_reasoning.gate as gate_mod

    src = gate_mod.__file__
    text = open(src).read()
    assert "claude_print_client" not in text
    assert "anthropic" not in text.lower()
    # And no such module was pulled into sys.modules by importing the gate.
    assert "anthropic" not in sys.modules

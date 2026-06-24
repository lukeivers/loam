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

"""AC.WIRE.3 — the live wiring COMPOSES with the existing PreToolUse safety
guards without regressing them: the deliberate gate is a sibling classifier,
and a hard block already decided by a safety guard
(wd_discipline_guard / in_thread_work_budget_guard) is NOT overridden by the
deliberate gate.

The compose-not-override contract is expressed as the ``safety_guard_blocked``
short-circuit: when an upstream safety guard has already blocked the action,
the deliberate adapter does NOT consult the gate and does NOT un-block it — it
returns ALLOW from its own perspective, leaving the upstream block standing.
The ordering is deterministic (the safety guard runs first; its block
short-circuits this adapter), which is what the live settings.json registration
would fix.
"""

from __future__ import annotations

from loam.deliberate_reasoning.loop import Critique
from loam.deliberate_reasoning.turn import TurnConfig
from loam.deliberate_reasoning.wiring import (
    WireOutcome,
    evaluate_pretooluse,
)


def _revising_critic(draft, prompt):
    return Critique(
        weakest_link="x",
        evidence=("y",),
        revised_answer="z",
        has_defensible_improvement=True,
    )


def test_AC_WIRE_3_safety_guard_block_is_not_overridden():
    # An envelope that WOULD trip the deliberate gate (high-blast rm -rf), but a
    # safety guard has ALREADY blocked it. The deliberate adapter must not run
    # the loop and must not emit anything that un-blocks it.
    envelope = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf important/", "file_path": "important/"},
    }
    result = evaluate_pretooluse(
        envelope,
        critic=_revising_critic,
        config=TurnConfig(enabled=True),
        safety_guard_blocked=True,
    )
    # The deliberate adapter adds nothing (the upstream block stands).
    assert result.outcome is WireOutcome.ALLOW
    assert result.decision is None  # the gate was not even consulted
    assert result.loop_result is None  # the loop did not run


def test_AC_WIRE_3_without_a_safety_block_the_gate_still_fires_normally():
    # Control: the SAME envelope, with no upstream safety block, DOES fire the
    # deliberate gate — proving the short-circuit is the safety-guard guard, not
    # a blanket suppression.
    envelope = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf important/", "file_path": "important/"},
    }
    result = evaluate_pretooluse(
        envelope,
        critic=_revising_critic,
        config=TurnConfig(enabled=True),
        safety_guard_blocked=False,
    )
    assert result.outcome is WireOutcome.BLOCK
    assert result.decision is not None and result.decision.fired is True


def test_AC_WIRE_3_safety_block_short_circuit_runs_no_loop_tokens():
    # The short-circuit must spend zero loop tokens — a critic that raises if
    # called proves the loop is never reached on the safety-blocked path.
    def _exploding_critic(draft, prompt):
        raise AssertionError("loop must not run when a safety guard already blocked")

    envelope = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf important/", "file_path": "important/"},
    }
    result = evaluate_pretooluse(
        envelope,
        critic=_exploding_critic,
        config=TurnConfig(enabled=True),
        safety_guard_blocked=True,
    )
    assert result.outcome is WireOutcome.ALLOW

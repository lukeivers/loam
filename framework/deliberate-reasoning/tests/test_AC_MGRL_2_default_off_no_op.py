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

"""AC.MGRL.2 — on a turn the gate declines to escalate (or the layer is
disabled), the final output is byte-identical to the draft and NO
deliberate-loop tokens are spent (the critic is never called).

The "no tokens spent" half is verified with a critic that raises if ever
invoked — if the no-op path touched the loop, the test would error. The
byte-identical half compares ``final_answer`` to the input draft exactly.
"""

from __future__ import annotations

import pytest

from loam.deliberate_reasoning.gate import GateSignals
from loam.deliberate_reasoning.turn import TurnConfig, process_turn


def _exploding_critic(draft, prompt):
    raise AssertionError("critic must not be called on a non-escalated turn")


DRAFT = "The answer is 42."


def test_AC_MGRL_2_disabled_layer_returns_draft_byte_identical_no_critic():
    # Layer disabled (default-OFF): gate not consulted, critic never called.
    result = process_turn(
        draft=DRAFT,
        prompt="What is 6 times 7?",
        signals=GateSignals(draft_text="I think probably 42"),  # would trigger if enabled
        critic=_exploding_critic,
        config=TurnConfig(enabled=False),
    )
    assert result.final_answer == DRAFT
    assert result.final_answer is DRAFT or result.final_answer == DRAFT
    assert result.escalated is False
    assert result.loop_result is None
    assert result.decision is None  # gate never consulted when disabled


def test_AC_MGRL_2_enabled_but_gate_declines_returns_draft_no_critic():
    # Layer enabled but no trigger signal => gate declines, critic not called.
    result = process_turn(
        draft=DRAFT,
        prompt="What is 6 times 7?",
        signals=GateSignals(
            draft_text=DRAFT,
            task_class="arithmetic",
            recent_task_classes=frozenset({"arithmetic"}),
            prompt_text="What is 6 times 7?",
        ),
        critic=_exploding_critic,
        config=TurnConfig(enabled=True),
    )
    assert result.final_answer == DRAFT
    assert result.escalated is False
    assert result.loop_result is None
    assert result.decision is not None and result.decision.escalate is False

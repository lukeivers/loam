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

"""AC.WIRE.1 — the gate fires inside a LIVE primary-session turn: on a real
turn (a simulated PreToolUse envelope) carrying a structural signal, the live
wiring engages the slice-1 re-think loop, and the deliberate output affects the
turn's outcome (a warn surface or a block-toward-rethink). A structurally-safe
turn produces none.

The wiring is driven by SIMULATED PreToolUse envelopes (the same envelope the
existing in_thread_work_budget_guard / wd_discipline_guard read), exactly as
slice-1's experiment harness drives the gate. The live pos3 settings/hooks are
NOT touched (the activation is a separate owner-gated step).
"""

from __future__ import annotations

from loam.deliberate_reasoning.loop import Critique
from loam.deliberate_reasoning.turn import TurnConfig
from loam.deliberate_reasoning.wiring import (
    WireOutcome,
    evaluate_pretooluse,
    run_pretooluse_hook,
)


def _critic(draft, prompt):
    # A deterministic critic that produces a defensible, evidence-backed
    # revision so the loop's intervention is observable end-to-end.
    return Critique(
        weakest_link="the pending action is unbounded and will run away",
        evidence=("the regex has an unbounded quantifier over a 2MB target",),
        revised_answer="bound the search: add a result limit and a timeout",
        has_defensible_improvement=True,
    )


def test_AC_WIRE_1_structural_signal_envelope_fires_loop_and_affects_outcome():
    # A simulated PreToolUse envelope for an unbounded-op action.
    envelope = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "grep -oE 'fn.{0,200}' app.min.js",
            "file_path": "app.min.js",
            "target_size_bytes": 2_100_000,
        },
    }
    result = evaluate_pretooluse(
        envelope, critic=_critic, config=TurnConfig(enabled=True)
    )
    # The gate fired and the loop ran end-to-end.
    assert result.outcome in (WireOutcome.WARN, WireOutcome.BLOCK)
    assert result.decision is not None and result.decision.fired is True
    assert result.loop_result is not None
    # The deliberate output affects the surfaced outcome (the revision shows).
    assert result.loop_result.revised is True
    assert "bound the search" in result.message


def test_AC_WIRE_1_machine_irreversible_blocks_toward_rethink():
    # A high-severity structural signal (irreversible machine action) BLOCKS.
    envelope = {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /Users/luke/project", "file_path": "/Users/luke/project"},
    }
    exit_code, stdout, stderr = run_pretooluse_hook(
        envelope, critic=_critic, config=TurnConfig(enabled=True)
    )
    assert exit_code == 2  # block-toward-rethink
    assert stderr  # feedback on stderr per the PreToolUse contract


def test_AC_WIRE_1_safe_envelope_produces_no_intervention():
    envelope = {
        "tool_name": "Read",
        "tool_input": {"file_path": "docs/readme.md"},
    }
    result = evaluate_pretooluse(
        envelope, critic=_critic, config=TurnConfig(enabled=True)
    )
    assert result.outcome is WireOutcome.ALLOW
    assert result.loop_result is None  # the loop was never invoked
    assert result.message == ""


def test_AC_WIRE_1_warn_emits_systemMessage_on_stdout():
    envelope = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "grep -oE 'fn.{0,200}' app.min.js",
            "file_path": "app.min.js",
            "target_size_bytes": 2_100_000,
        },
    }
    exit_code, stdout, stderr = run_pretooluse_hook(
        envelope, critic=_critic, config=TurnConfig(enabled=True)
    )
    # WARN contract: exit 0 + a systemMessage JSON on stdout.
    assert exit_code == 0
    assert "systemMessage" in stdout

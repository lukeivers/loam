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

"""AC.WIRE.OA (outcome-altitude: true) — a LIVE end-to-end real-situation fire
through the production live-wiring entry-point with NO pre-arranged gate state:
a real turn whose pending action carries a genuine structural signal yields a
gate escalation + a deliberate-loop invocation that changes the outcome — AND,
on the SAME enabled configuration, a set of structurally-normal turns produces
ZERO fires.

Per feedback_test_outcome_altitude_required this invokes the production
entry-point (``evaluate_pretooluse``) with NO seeded gate state and NO stubbed
trigger — the structural signal is realized through a genuine PreToolUse
envelope (an unbounded-op pending action over a large target), and the gate
decides on its own. The deliberate loop runs end to end (the critic is invoked,
proven by a flag) and the outcome is changed (the revision shows in the surface).
The zero-collateral half runs the SAME enabled config over normal envelopes.
"""

from __future__ import annotations

from loam.deliberate_reasoning.loop import Critique
from loam.deliberate_reasoning.turn import TurnConfig
from loam.deliberate_reasoning.wiring import WireOutcome, evaluate_pretooluse


def test_AC_WIRE_OA_live_real_situation_fire_changes_outcome_no_seeded_state():
    invoked = {"critic": False}

    def real_path_critic(draft, prompt):
        invoked["critic"] = True
        return Critique(
            weakest_link="the pending search is unbounded over a 2MB blob",
            evidence=("the regex has no result bound and the target is 2.1MB",),
            revised_answer="add `| head -50` and a `timeout 5` before running",
            has_defensible_improvement=True,
        )

    # NO pre-arranged gate state: a genuine PreToolUse envelope. The structural
    # signal is realized from the action's own structure (an unbounded
    # quantifier over a large target). The gate must decide escalate on its own.
    envelope = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "grep -oE 'function.{0,200}\\(.{0,400}\\)' vendor/app.min.js",
            "file_path": "vendor/app.min.js",
            "target_size_bytes": 2_100_000,
        },
    }

    result = evaluate_pretooluse(
        envelope,
        critic=real_path_critic,
        config=TurnConfig(enabled=True),  # the single explicit enable
    )

    # Escalation fired through the real production entry-point.
    assert result.outcome in (WireOutcome.WARN, WireOutcome.BLOCK)
    assert result.decision is not None and result.decision.fired is True
    # The deliberate loop was actually invoked end-to-end.
    assert invoked["critic"] is True
    assert result.loop_result is not None
    # The outcome was CHANGED: the deliberate revision is surfaced.
    assert result.loop_result.revised is True
    assert "head -50" in result.message


def test_AC_WIRE_OA_same_enabled_config_zero_collateral_on_normal_turns():
    # The SAME enabled configuration over a set of structurally-normal turns:
    # zero fires. A critic that raises if called proves zero loop tokens.
    def _exploding_critic(draft, prompt):
        raise AssertionError("no loop on a normal turn under the enabled config")

    normal_envelopes = [
        {"tool_name": "Read", "tool_input": {"file_path": "main.py"}},
        {"tool_name": "Grep", "tool_input": {"pattern": "class Foo", "path": "src/"}},
        {"tool_name": "Bash", "tool_input": {"command": "git log --oneline -5"}},
        {"tool_name": "Bash", "tool_input": {"command": "grep -n foo bar.py | head -3", "file_path": "bar.py"}},
        {"tool_name": "Write", "tool_input": {"file_path": "/tmp/out.txt", "content": "ok"}},
    ]
    fires = 0
    for env in normal_envelopes:
        r = evaluate_pretooluse(
            env, critic=_exploding_critic, config=TurnConfig(enabled=True)
        )
        if r.outcome is not WireOutcome.ALLOW:
            fires += 1
    assert fires == 0

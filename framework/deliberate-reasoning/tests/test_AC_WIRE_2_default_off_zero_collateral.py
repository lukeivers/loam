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

"""AC.WIRE.2 (no-collateral / default-OFF) — the layer ships DEFAULT-OFF, and
with it ON a turn carrying NO structural signal is byte-identical to baseline:
the gate fires on ZERO normal turns (the live form of slice-1's
``gain_on_unflagged == 0``).

This is one of the three HARD GATES. Two halves:

(a) DEFAULT-OFF: with the layer disabled, the live wiring is a pure no-op
    (ALLOW, no gate consult, no loop, no message) on EVERY envelope — including
    one that WOULD fire if enabled. A critic that raises if called proves no
    loop tokens are spent.
(b) ZERO-COLLATERAL-ON-NORMAL-TURNS: with the layer ENABLED, a corpus of
    structurally-normal envelopes produces ZERO fires (ALLOW, no loop, no
    message) — only structural-signal envelopes fire.
"""

from __future__ import annotations

import pytest

from loam.deliberate_reasoning.turn import TurnConfig
from loam.deliberate_reasoning.wiring import (
    WireOutcome,
    evaluate_pretooluse,
)


def _exploding_critic(draft, prompt):
    raise AssertionError("the loop must not run on a zero-collateral turn")


# A risky envelope that WOULD fire if the layer were enabled.
_RISKY_ENVELOPE = {
    "tool_name": "Bash",
    "tool_input": {
        "command": "grep -oE 'fn.{0,200}' app.min.js",
        "file_path": "app.min.js",
        "target_size_bytes": 2_100_000,
    },
}

# A corpus of structurally-NORMAL envelopes — the kind of action a normal turn
# takes. None carries a structural signal.
_NORMAL_ENVELOPES = [
    {"tool_name": "Read", "tool_input": {"file_path": "src/app.py"}},
    {"tool_name": "Grep", "tool_input": {"pattern": "def main", "path": "src/"}},
    {"tool_name": "Bash", "tool_input": {"command": "git status"}},
    {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
    {"tool_name": "Bash", "tool_input": {"command": "grep -n 'foo' small.py | head -5", "file_path": "small.py"}},
    {"tool_name": "Write", "tool_input": {"file_path": "/tmp/scratch.txt", "content": "x"}},
    {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/notes.md"}},
    {"tool_name": "Bash", "tool_input": {"command": "python -m pytest -q"}},
]


def test_AC_WIRE_2_default_off_is_pure_noop_even_on_risky_envelope():
    # DEFAULT-OFF: config defaults to env-read (the env var is unset in tests),
    # so the layer is OFF. The risky envelope is a pure no-op; the loop is
    # never invoked (the exploding critic proves it).
    result = evaluate_pretooluse(_RISKY_ENVELOPE, critic=_exploding_critic)
    assert result.outcome is WireOutcome.ALLOW
    assert result.decision is None  # gate never consulted when disabled
    assert result.loop_result is None
    assert result.message == ""


def test_AC_WIRE_2_explicit_disabled_is_pure_noop():
    result = evaluate_pretooluse(
        _RISKY_ENVELOPE, critic=_exploding_critic, config=TurnConfig(enabled=False)
    )
    assert result.outcome is WireOutcome.ALLOW
    assert result.decision is None
    assert result.loop_result is None


@pytest.mark.parametrize("envelope", _NORMAL_ENVELOPES)
def test_AC_WIRE_2_enabled_normal_turns_fire_zero_collateral(envelope):
    # ENABLED, but the envelope is structurally normal: ZERO fires. The loop is
    # never invoked (the exploding critic proves zero loop tokens).
    result = evaluate_pretooluse(
        envelope, critic=_exploding_critic, config=TurnConfig(enabled=True)
    )
    assert result.outcome is WireOutcome.ALLOW, f"{envelope} should not fire"
    assert result.loop_result is None
    assert result.message == ""
    assert result.decision is not None and result.decision.escalate is False


def test_AC_WIRE_2_gate_fires_on_zero_of_the_normal_corpus():
    # The aggregate live invariant: across the whole normal corpus, the count
    # of fires is exactly zero.
    fires = 0
    for env in _NORMAL_ENVELOPES:
        r = evaluate_pretooluse(
            env, critic=lambda d, p: (_ for _ in ()).throw(AssertionError("no loop")),
            config=TurnConfig(enabled=True),
        )
        if r.outcome is not WireOutcome.ALLOW:
            fires += 1
    assert fires == 0

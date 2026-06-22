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

"""The production turn-processing entry-point (plan D-MGRL.5).

:func:`process_turn` is the single surface a real turn flows through and
the surface AC.MGRL.OA fires through with no pre-arranged state. It wires
the gate (gate.py) to the deliberate loop (loop.py) under the default-OFF
switch:

- AC.MGRL.2 — on a turn the gate declines to escalate, the final output is
  byte-identical to the draft and **no deliberate-loop tokens are spent**
  (the critic is never called on the don't-escalate path).
- AC.MGRL.5 / D-MGRL.5 — the layer is **default OFF**: with
  ``TurnConfig.enabled is False`` (the default), the gate is not even
  consulted and the draft is returned unchanged. Enabling is a single,
  explicit, reversible flag (AC.MGRL.7).
- AC.MGRL.OA — a real turn carrying a genuine trigger signal, run through
  this entry-point with no seeded gate state, produces an escalation
  decision + a deliberate-loop invocation + a recorded firing trigger.

The default-OFF guarantee is structural: when disabled, this function does
the same thing the baseline harness does — returns the draft — and touches
neither the gate nor the loop. That is what keeps the experiment's baseline
genuinely unperturbed (AC.MGRL.2 / RF-4).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .gate import GateDecision, GateSignals, evaluate_gate
from .loop import Critic, LoopResult, run_deliberate_loop

# The explicit, reversible opt-in switch (AC.MGRL.7). Default OFF: absent or
# any value other than the enabling tokens means disabled.
ENABLE_ENV_VAR = "LOAM_DELIBERATE_REASONING"
_ENABLED_TOKENS = frozenset({"1", "true", "on", "yes"})


def _enabled_from_env() -> bool:
    return os.environ.get(ENABLE_ENV_VAR, "").strip().lower() in _ENABLED_TOKENS


@dataclass(frozen=True)
class TurnConfig:
    """The default-OFF switch for the deliberate layer (AC.MGRL.7).

    ``enabled`` defaults to None, meaning "read the ENABLE_ENV_VAR env var"
    (default OFF when unset). An explicit True/False overrides the env var
    — the single, reversible opt-in. The flag is the *only* thing that
    turns the layer on; there is no always-partially-live code path.
    """

    enabled: bool | None = None

    def is_enabled(self) -> bool:
        if self.enabled is None:
            return _enabled_from_env()
        return self.enabled


@dataclass(frozen=True)
class TurnResult:
    """The outcome of processing one turn through the entry-point.

    ``escalated`` records whether the deliberate loop ran; ``decision`` is
    the gate's decision (None when the layer was disabled and the gate was
    never consulted — the default-OFF path); ``loop_result`` is present iff
    the loop ran. ``final_answer`` is what the harness returns to the user.
    """

    final_answer: str
    escalated: bool
    decision: GateDecision | None
    loop_result: LoopResult | None
    original_draft: str


def process_turn(
    *,
    draft: str,
    prompt: str,
    signals: GateSignals,
    critic: Critic,
    config: TurnConfig | None = None,
) -> TurnResult:
    """Process one turn: gate, then (only if escalated) the deliberate loop.

    ``draft`` is the fast-path first answer the inference engine produced;
    ``signals`` are the observable gate inputs; ``critic`` is the loop's
    injected critic (LLM-backed in production via ``make_claude_critic``,
    deterministic stub in tests). ``config`` carries the default-OFF switch.

    Behaviour:

    - **Layer disabled (default):** return the draft unchanged; the gate is
      not consulted and the critic is never called (AC.MGRL.2 / D-MGRL.5).
    - **Enabled, gate declines:** return the draft unchanged; the critic is
      never called — no deliberate-loop tokens spent (AC.MGRL.2).
    - **Enabled, gate escalates:** run the deliberate loop; return its
      final answer (the revised answer only if the no-degradation guard
      accepted it, else the draft) (AC.MGRL.3, AC.MGRL.OA).
    """

    cfg = config or TurnConfig()

    if not cfg.is_enabled():
        return TurnResult(
            final_answer=draft,
            escalated=False,
            decision=None,
            loop_result=None,
            original_draft=draft,
        )

    decision = evaluate_gate(signals)
    if not decision.escalate:
        return TurnResult(
            final_answer=draft,
            escalated=False,
            decision=decision,
            loop_result=None,
            original_draft=draft,
        )

    loop_result = run_deliberate_loop(draft=draft, prompt=prompt, critic=critic)
    return TurnResult(
        final_answer=loop_result.final_answer,
        escalated=True,
        decision=decision,
        loop_result=loop_result,
        original_draft=draft,
    )

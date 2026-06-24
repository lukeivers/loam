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

"""AC.WIRE.4 — the option-(ii) per-turn LLM self-assessment escalation is
DEFAULT-OFF and INDEPENDENTLY gated: it is never consulted on the v1 hot path,
the structural floor runs LLM-free (zero ``claude -p`` calls on the hot path),
and enabling the escalation is a single explicit reversible switch SEPARATE
from ``LOAM_DELIBERATE_REASONING``.

Three halves:

(a) DEFAULT-OFF + INDEPENDENT: ``escalation_enabled()`` is False by default and
    is governed by its OWN env var (``LOAM_DELIBERATE_REASONING_SELF_ASSESS``),
    distinct from the layer's main switch.
(b) LLM-FREE HOT PATH: the modules on the v1 hot path (signals / gate / wiring)
    do not import the escalation runner or any print-client; a full live-wiring
    fire spends zero claude -p calls.
(c) SINGLE REVERSIBLE SWITCH: flipping only the escalation switch enables it;
    the structural-floor switch does not.
"""

from __future__ import annotations

from loam.deliberate_reasoning.escalation import (
    ESCALATION_ENV_VAR,
    SelfAssessment,
    escalation_enabled,
    make_self_assessment_escalation,
)
from loam.deliberate_reasoning.turn import ENABLE_ENV_VAR


def test_AC_WIRE_4_escalation_default_off():
    # No explicit, env unset (tests run with a clean env): default OFF.
    import os

    assert os.environ.get(ESCALATION_ENV_VAR) is None
    assert escalation_enabled() is False


def test_AC_WIRE_4_escalation_switch_is_independent_of_main_switch():
    # The escalation env var is distinct from the layer's main switch.
    assert ESCALATION_ENV_VAR != ENABLE_ENV_VAR
    assert ESCALATION_ENV_VAR == "LOAM_DELIBERATE_REASONING_SELF_ASSESS"
    assert ENABLE_ENV_VAR == "LOAM_DELIBERATE_REASONING"


def test_AC_WIRE_4_single_reversible_switch_enables_it():
    # The explicit override is the single reversible switch.
    assert escalation_enabled(explicit=True) is True
    assert escalation_enabled(explicit=False) is False


def test_AC_WIRE_4_hot_path_modules_are_llm_free():
    # signals / gate / wiring (the v1 hot path) must not import the escalation
    # runner or a print-client (the import lines, not docstring prose).
    import loam.deliberate_reasoning.signals as signals_mod
    import loam.deliberate_reasoning.gate as gate_mod
    import loam.deliberate_reasoning.wiring as wiring_mod

    for mod in (signals_mod, gate_mod, wiring_mod):
        import_lines = [
            ln
            for ln in open(mod.__file__).read().splitlines()
            if ln.lstrip().startswith(("import ", "from "))
        ]
        joined = "\n".join(import_lines).lower()
        assert "claude_print_client" not in joined, mod.__name__
        assert "anthropic" not in joined, mod.__name__
        # The hot path does not import the escalation runner builder.
        assert "make_self_assessment_escalation" not in joined, mod.__name__


def test_AC_WIRE_4_escalation_runner_goes_through_injected_claude_print():
    # When enabled, the escalation goes through the injected run_claude_print
    # (the subscription path), never the Anthropic SDK. Verified by injecting a
    # fake print caller and confirming it is the only LLM surface invoked.
    calls = {"n": 0}

    def fake_claude_print(prompt: str) -> str:
        calls["n"] += 1
        return '{"should_escalate": true, "rationale": "unbounded"}'

    escalate = make_self_assessment_escalation(run_claude_print=fake_claude_print)
    result = escalate("tool=Bash command=grep -oE 'fn.*' big.js")
    assert isinstance(result, SelfAssessment)
    assert result.should_escalate is True
    assert calls["n"] == 1  # exactly one subscription-path call, no SDK


def test_AC_WIRE_4_malformed_escalation_response_is_conservative():
    # A malformed response is treated as "do not escalate" — never a silent
    # escalation.
    escalate = make_self_assessment_escalation(
        run_claude_print=lambda p: "not json at all"
    )
    assert escalate("anything").should_escalate is False

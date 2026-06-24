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

"""The option-(ii) self-assessment escalation seam — DESIGNED, DEFAULT-OFF,
NOT enabled on the v1 hot path (slice 3 — plan D-SIT.1, D-SIT.5; AC.WIRE.4).

The plan's central fork (D-SIT.1) ships ONLY the structural floor (option i)
in v1 and DEFERS the per-turn LLM self-assessment (option ii) as a designed,
default-OFF escalation. This module is that seam — built only far enough that
enabling it is a SINGLE reversible switch, independent of the layer's main
switch (``LOAM_DELIBERATE_REASONING``).

Two invariants this module enforces (AC.WIRE.4):

1. **Independently default-OFF.** The escalation has its OWN env switch
   (:data:`ESCALATION_ENV_VAR`), default OFF. Enabling the structural floor
   (``LOAM_DELIBERATE_REASONING``) does NOT turn this on — so enabling the free
   floor never silently turns on per-turn token spend. Flipping ONLY this
   switch is the single change that would enable it.

2. **Zero LLM calls on the v1 hot path.** With the escalation off (default),
   :func:`escalation_enabled` is False and no ``claude -p`` call occurs on any
   gate path — the structural floor runs LLM-free (the hot path imports only
   ``signals`` / ``gate`` / ``loop``, never this module's runner). When
   enabled, the self-assessment goes through ``claude -p`` (the subscription
   path, ``feedback_no_anthropic_api_key``), NEVER the Anthropic SDK.

The escalation is intended for the small fraction of turns where a STRUCTURAL
signal is ambiguous (or to cover the named draft-quality gap, RF-3), never
every turn — the per-turn-token trap slice-1's D-MGRL.1 ruled out.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

# The escalation's OWN switch — independent of LOAM_DELIBERATE_REASONING
# (AC.WIRE.4). Default OFF.
ESCALATION_ENV_VAR = "LOAM_DELIBERATE_REASONING_SELF_ASSESS"
_ENABLED_TOKENS = frozenset({"1", "true", "on", "yes"})


def escalation_enabled(explicit: bool | None = None) -> bool:
    """Whether the option-(ii) self-assessment escalation is enabled.

    ``explicit`` overrides the env var (the single reversible switch);
    ``None`` reads :data:`ESCALATION_ENV_VAR` (default OFF). This is the ONLY
    gate on the costly path — it is independent of the layer's main switch
    (AC.WIRE.4).
    """

    if explicit is not None:
        return explicit
    return os.environ.get(ESCALATION_ENV_VAR, "").strip().lower() in _ENABLED_TOKENS


@dataclass(frozen=True)
class SelfAssessment:
    """The escalation's verdict on an ambiguous structural signal."""

    should_escalate: bool
    rationale: str = ""


# The self-assessment prompt — forces a structural-risk verdict, not a free
# narration. Used ONLY when the escalation is explicitly enabled.
SELF_ASSESS_PROMPT_TEMPLATE = (
    "An about-to-act gate saw an AMBIGUOUS structural signal on this pending "
    "action:\n\n{action_description}\n\n"
    "Decide whether this action warrants a deliberate re-think before running. "
    "Respond as JSON: "
    '{{"should_escalate": bool, "rationale": str}}.'
)


def make_self_assessment_escalation(
    *,
    run_claude_print: Callable[[str], str],
    parse_json: Callable[[str], dict] | None = None,
) -> Callable[[str], SelfAssessment]:
    """Build the option-(ii) escalation, backed by ``claude -p``.

    ``run_claude_print`` is the subscription-path caller (the
    ``claude_print_client`` surface, ``feedback_no_anthropic_api_key`` — the
    Anthropic SDK is NEVER used). Injected rather than imported so this module
    has no hard dependency on the print-client and the v1 hot path stays
    LLM-free (it never imports this builder). A malformed response is treated
    as "do not escalate" (conservative — never a silent escalation).

    This is the SEAM only: building it does not enable it. The caller invokes
    the returned callable ONLY when :func:`escalation_enabled` is True.
    """

    import json as _json

    _parse = parse_json or _json.loads

    def _escalate(action_description: str) -> SelfAssessment:
        raw = run_claude_print(
            SELF_ASSESS_PROMPT_TEMPLATE.format(action_description=action_description)
        )
        try:
            payload = _parse(raw)
        except Exception:  # noqa: BLE001
            return SelfAssessment(should_escalate=False, rationale="(unparseable)")
        return SelfAssessment(
            should_escalate=bool(payload.get("should_escalate", False)),
            rationale=str(payload.get("rationale", "")),
        )

    return _escalate


__all__ = [
    "ESCALATION_ENV_VAR",
    "escalation_enabled",
    "SelfAssessment",
    "make_self_assessment_escalation",
]

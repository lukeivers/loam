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

"""The deliberate, evidence-bound, re-entrant loop (plan D-MGRL.2).

Invoked **only** on an escalated turn (gate-gated, off the per-turn hot
path — D-MGRL.5). Runs:

    draft -> adversarial evidence-bound critique -> revise -> re-check

and is **structurally permitted to return the original draft unchanged**
when critique finds no evidence-backed improvement. That no-degradation
guard is the load-bearing answer to the proposal §3 trap — always-on
self-critique degrades output via rationalization / confabulation /
talking past a correct first answer. The guard makes re-entrance a
*possible* improvement, never a guaranteed verbosity tax.

ACs:

- AC.MGRL.3 — the loop yields the revised answer **only when** critique
  produced an evidence-backed improvement, else the original draft.

Design — the critic is **injected**, not hard-wired:

The critic is a callable ``(draft, prompt) -> Critique``. In production it
wraps a ``claude -p`` call (subscription path, ``feedback_no_anthropic_api_key``
— never the Anthropic SDK); :func:`make_claude_critic` builds that wrapper.
In tests the critic is a deterministic stub, so the **no-degradation guard
itself** is verified without any LLM call. The guard is structural (a
field on the critique + an acceptance check here), not a property of the
LLM — that is what makes it reliable rather than a coin-flip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass(frozen=True)
class Critique:
    """The adversarial, evidence-bound critique of a draft (D-MGRL.2).

    ``has_defensible_improvement`` is the no-degradation guard's gate: the
    revised answer is accepted **only** when this is True AND ``evidence``
    is non-empty (evidence-binding — a revision with no cited reason for why
    each changed step is sound is rejected, which is the structural defence
    against post-hoc confabulation).
    """

    # The strongest counter the critic could mount against the draft —
    # "find the weakest link, name why each step is or is not sound".
    weakest_link: str
    # Cited evidence for each claimed defect/soundness. Empty => the critic
    # found no evidence-backed problem; the draft stands (no-degradation).
    evidence: tuple[str, ...] = ()
    # The critic's proposed revised answer. None => no revision proposed.
    revised_answer: str | None = None
    # The critic's own verdict that the revision is a defensible improvement
    # over the draft. The guard requires this AND non-empty evidence.
    has_defensible_improvement: bool = False


@dataclass(frozen=True)
class LoopResult:
    """The outcome of one deliberate-loop run (AC.MGRL.3)."""

    final_answer: str
    # True iff the loop accepted a revision; False iff the no-degradation
    # guard returned the original draft.
    revised: bool
    critique: Critique
    # The original draft, always carried so the comparison is auditable.
    original_draft: str


# A critic is any callable from (draft, prompt) to a Critique. Injecting it
# keeps the loop's no-degradation guard deterministically testable and keeps
# the LLM (when used) behind the seam (feedback_no_anthropic_api_key).
Critic = Callable[[str, str], Critique]


def _revision_is_acceptable(critique: Critique) -> bool:
    """The no-degradation guard (D-MGRL.2).

    A revision is accepted only when the critic both (a) declares a
    defensible improvement AND (b) cites non-empty evidence AND (c)
    actually proposes a revised answer. Any of these absent => keep the
    original draft. Evidence-binding (b) is the structural defence against
    confabulated, evidence-free "improvements".
    """

    return (
        critique.has_defensible_improvement
        and bool(critique.evidence)
        and critique.revised_answer is not None
    )


def run_deliberate_loop(draft: str, prompt: str, critic: Critic) -> LoopResult:
    """Run the evidence-bound re-entrant loop on an escalated turn.

    draft -> critique (via the injected critic) -> revise-or-keep (the
    no-degradation guard). Returns the revised answer only when the
    critique carries a defensible, evidence-backed improvement; otherwise
    returns the original draft unchanged (AC.MGRL.3).
    """

    critique = critic(draft, prompt)
    if _revision_is_acceptable(critique):
        # revised_answer is guaranteed non-None by the guard above.
        return LoopResult(
            final_answer=critique.revised_answer,  # type: ignore[arg-type]
            revised=True,
            critique=critique,
            original_draft=draft,
        )
    return LoopResult(
        final_answer=draft,
        revised=False,
        critique=critique,
        original_draft=draft,
    )


# --------------------------------------------------------------------------
# Production critic — wraps `claude -p` (subscription path), never the
# Anthropic SDK (feedback_no_anthropic_api_key, plan §3.6). Built lazily so
# the deterministic test path never imports the print-client.
# --------------------------------------------------------------------------

# The adversarial, evidence-bound critique prompt. Free-form self-narration
# is the degradation trap (D-MGRL.2); this prompt forces (a) adversarial
# stance, (b) per-step soundness with cited evidence, (c) an explicit
# return-the-original verdict when no evidence-backed improvement exists.
CRITIQUE_PROMPT_TEMPLATE = (
    "You are an adversarial reviewer. The task was:\n\n{prompt}\n\n"
    "A first-pass answer was produced:\n\n{draft}\n\n"
    "Find the single weakest link. For each load-bearing step, state "
    "whether it is sound and CITE the specific evidence for that judgment. "
    "Do NOT rewrite for style. Only propose a revised answer if you can "
    "name an evidence-backed defect in the original; if the original is "
    "already correct, say so and return it unchanged. Respond as JSON: "
    '{{"weakest_link": str, "evidence": [str], "revised_answer": str|null, '
    '"has_defensible_improvement": bool}}.'
)


def make_claude_critic(
    *,
    run_claude_print: Callable[[str], str],
    parse_json: Callable[[str], dict] | None = None,
) -> Critic:
    """Build a production critic backed by ``claude -p``.

    ``run_claude_print`` is the subscription-path caller (the
    ``claude_print_client`` surface, ``feedback_no_anthropic_api_key`` —
    the Anthropic SDK is never used). Injected rather than imported so this
    module has no hard dependency on the print-client and the test path
    stays LLM-free. A malformed response is treated as "no defensible
    improvement" (the no-degradation guard keeps the draft), never as a
    silent revision.
    """

    import json as _json

    _parse = parse_json or _json.loads

    def _critic(draft: str, prompt: str) -> Critique:
        raw = run_claude_print(
            CRITIQUE_PROMPT_TEMPLATE.format(prompt=prompt, draft=draft)
        )
        try:
            payload = _parse(raw)
        except Exception:
            return Critique(weakest_link="(unparseable critique)", evidence=())
        evidence = tuple(payload.get("evidence", ()) or ())
        return Critique(
            weakest_link=str(payload.get("weakest_link", "")),
            evidence=evidence,
            revised_answer=payload.get("revised_answer"),
            has_defensible_improvement=bool(
                payload.get("has_defensible_improvement", False)
            ),
        )

    return _critic

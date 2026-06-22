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

"""The pre-registered experiment runner (plan §3.3, AC.MGRL.5, AC.MGRL.6;
PRE_REGISTRATION §5).

Runs the FROZEN task set through both arms, scores with the blind judge,
and computes the pre-registered quantities: aggregate generic-lift delta,
the flagged-vs-unflagged discriminator (`gain_on_flagged` /
`gain_on_unflagged`), the zero-tolerance no-degradation check, and the §3
verdict (THEORY-PREDICTION CONFIRMED / GENERIC-LIFT-ONLY / NULL).

The BASELINE arm produces the fast-path draft (layer OFF). The ESCALATED
arm runs the identical draft through ``process_turn`` with the layer ON.
The critic is INJECTED: the deterministic reference critic below
(:func:`reference_critic`) is evidence-bound by construction — it proposes a
correction ONLY when it can cite the canonical answer key as evidence, never
free-form. A fully-LLM run swaps in ``make_claude_critic`` over the IDENTICAL
task set + judge + verdict rule (PRE_REGISTRATION §6).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam.deliberate_reasoning.gate import GateSignals  # noqa: E402
from loam.deliberate_reasoning.loop import Critic, Critique  # noqa: E402
from loam.deliberate_reasoning.turn import TurnConfig, process_turn  # noqa: E402

from judge import score_answer  # noqa: E402

TASK_SET_PATH = Path(__file__).resolve().parent / "task_set.json"


@dataclass(frozen=True)
class ItemResult:
    item_id: str
    trigger_intended: str
    escalated: bool
    baseline_correct: int
    escalated_correct: int


@dataclass(frozen=True)
class ExperimentResult:
    """The reported result (AC.MGRL.6: aggregate delta AND discriminator,
    plus the pre-registered verdict, all separately)."""

    baseline_correct_total: int
    escalated_correct_total: int
    aggregate_delta: int  # generic lift — confirms NOTHING about theory alone
    gain_on_flagged: int  # the theory's predicted concentration
    gain_on_unflagged: int  # MUST be 0 or the default-OFF guarantee is broken
    regressions: int  # zero-tolerance no-degradation check
    verdict: str  # CONFIRMED | GENERIC-LIFT-ONLY | NULL | INVALID-DEFAULT-OFF-BREACH
    per_item: list[ItemResult]


def load_task_set(path: Path = TASK_SET_PATH) -> list[dict]:
    data = json.loads(path.read_text())
    return list(data["items"])


def _signals_for(item: dict, baseline_draft: str, recent_classes: frozenset[str]) -> GateSignals:
    """Build the gate's observable signals for an item.

    The intended trigger is realized through a genuine observable signal,
    NOT by seeding the gate's decision: low_confidence => a hedged draft;
    novelty => a task_class absent from recent history; stakes => the
    item's prompt carries explicit high-stakes framing (already in the
    task text). 'none' control items carry no trigger signal.
    """

    intended = item["trigger_intended"]
    draft = baseline_draft
    task_class = item["task_class"]
    recent = recent_classes
    if intended == "low_confidence":
        # A genuinely hedged draft carries the low-confidence signal.
        draft = f"I think the answer is probably {baseline_draft}."
    if intended == "novelty":
        # Genuinely novel: this task_class is NOT in the recent set.
        recent = frozenset()
    if intended == "none":
        # Control: not novel (class is in recent), not hedged, no stakes
        # framing in prompt.
        recent = frozenset({task_class})
    return GateSignals(
        draft_text=draft,
        task_class=task_class,
        recent_task_classes=recent,
        prompt_text=item["prompt"],
        high_stakes_task_class=False,
    )


def reference_critic(answer_key: dict[str, str]) -> Critic:
    """A deterministic, evidence-bound reference critic (PRE_REGISTRATION §6).

    Proposes a correction ONLY when the draft (normalized) does not match the
    canonical answer for the item — and it cites the canonical answer key as
    the evidence. It never rewrites a correct draft (the no-degradation
    guard then returns the original). Keyed by canonical answer so it is
    deterministic and token-free; it is evidence-bound by construction (the
    only 'evidence' it can cite is the answer key, never free-form).
    """

    from judge import normalize

    # Map normalized-prompt-marker -> canonical answer is overkill; we key by
    # the canonical answer itself passed per-call via closure over the item.
    def _make(canonical: str) -> Critic:
        def _critic(draft: str, prompt: str) -> Critique:
            if normalize(draft) == normalize(canonical):
                # Already correct — no evidence-backed improvement; keep draft.
                return Critique(
                    weakest_link="draft already matches canonical answer",
                    evidence=(),
                    revised_answer=None,
                    has_defensible_improvement=False,
                )
            return Critique(
                weakest_link="draft does not match the canonical answer",
                evidence=(f"answer key: {canonical}",),
                revised_answer=canonical,
                has_defensible_improvement=True,
            )

        return _critic

    # answer_key maps item_id -> canonical; the runner builds a per-item
    # critic, so this returns a factory the runner specializes.
    def _dispatch(item_id: str) -> Critic:
        return _make(answer_key[item_id])

    return _dispatch  # type: ignore[return-value]


def run_experiment(
    *,
    baseline_answer_for: Callable[[dict], str],
    critic_factory: Callable[[str], Critic],
) -> ExperimentResult:
    """Run both arms over the frozen task set and compute the pre-registered
    quantities + verdict (AC.MGRL.5, AC.MGRL.6).

    ``baseline_answer_for`` produces the fast-path draft for an item (the
    BASELINE arm). ``critic_factory(item_id)`` yields the loop's critic for
    the ESCALATED arm. Both arms share the SAME draft; only the layer
    differs — so the comparison measures the deliberate layer's effect, not
    a measurement artefact (PRE_REGISTRATION §5 / RF-4).
    """

    items = load_task_set()
    per_item: list[ItemResult] = []
    base_total = esc_total = 0
    gain_flagged = gain_unflagged = regressions = 0

    for item in items:
        draft = baseline_answer_for(item)
        canonical = item["canonical_answer"]

        # BASELINE arm: layer OFF, the unperturbed draft.
        base_score = score_answer(item["prompt"], draft, canonical)

        # ESCALATED arm: identical draft through the production entry-point
        # with the layer ON.
        signals = _signals_for(item, draft, recent_classes=frozenset({item["task_class"]}))
        result = process_turn(
            draft=draft,
            prompt=item["prompt"],
            signals=signals,
            critic=critic_factory(item["id"]),
            config=TurnConfig(enabled=True),
        )
        esc_score = score_answer(item["prompt"], result.final_answer, canonical)

        base_total += base_score
        esc_total += esc_score
        delta = esc_score - base_score
        if result.escalated:
            gain_flagged += delta
        else:
            gain_unflagged += delta
        if base_score == 1 and esc_score == 0:
            regressions += 1

        per_item.append(
            ItemResult(
                item_id=item["id"],
                trigger_intended=item["trigger_intended"],
                escalated=result.escalated,
                baseline_correct=base_score,
                escalated_correct=esc_score,
            )
        )

    verdict = _verdict(gain_flagged, gain_unflagged, regressions)
    return ExperimentResult(
        baseline_correct_total=base_total,
        escalated_correct_total=esc_total,
        aggregate_delta=esc_total - base_total,
        gain_on_flagged=gain_flagged,
        gain_on_unflagged=gain_unflagged,
        regressions=regressions,
        verdict=verdict,
        per_item=per_item,
    )


def _verdict(gain_flagged: int, gain_unflagged: int, regressions: int) -> str:
    """Apply the FIXED pre-registered verdict rule (PRE_REGISTRATION §3),
    no further judgment."""

    if gain_unflagged != 0:
        # Default-OFF guarantee broken (escalated != baseline on a turn the
        # gate declined). The run is invalid, NOT a generic-lift result.
        return "INVALID-DEFAULT-OFF-BREACH"
    if gain_flagged > 0 and regressions == 0:
        return "THEORY-PREDICTION-CONFIRMED"
    if gain_flagged > 0:
        # Gain exists but a regression occurred — no-degradation failed.
        return "GENERIC-LIFT-ONLY"
    return "NULL"


def result_as_dict(result: ExperimentResult) -> dict:
    d = asdict(result)
    return d


if __name__ == "__main__":  # pragma: no cover - manual reference run
    task_items = load_task_set()
    answer_key = {it["id"]: it["canonical_answer"] for it in task_items}

    # The reference baseline: a deliberately-flawed draft on the FLAGGED
    # items (so the loop has a real, checkable defect to catch) and a
    # correct draft on the control items (so the gate's decline is genuine).
    def _baseline(item: dict) -> str:
        if item["trigger_intended"] == "none":
            return item["canonical_answer"]
        return "WRONG-PLACEHOLDER"

    factory = reference_critic(answer_key)
    res = run_experiment(baseline_answer_for=_baseline, critic_factory=factory)
    print(json.dumps(result_as_dict(res), indent=2))

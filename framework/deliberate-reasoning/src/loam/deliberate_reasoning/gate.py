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

"""The metacognitive gate — a deterministic, signal-scored per-turn
escalate / don't-escalate decision (plan D-MGRL.1, D-MGRL.4).

The gate decides, from **observable signals available at gate-time**,
whether the fast inference path answers (don't-escalate) or the deliberate
re-entrant loop engages (escalate). It makes **no LLM call** — sibling in
shape to ``intent_classifier.py`` (regex-scored, deterministic, instant,
zero token cost). An LLM-per-turn gate is the exact trap D-MGRL.1 rules out.

Slice-1 trigger set (dispatcher ruling on D-MGRL.4 — all three observable
triggers ship; surprise/prediction-error deferred to slice 2, plan §7):

- ``LOW_CONFIDENCE`` — hedging / uncertainty markers in the draft answer
  (the proxy named in §3.4; its quality is itself measured by the
  per-trigger breakdown, AC.MGRL.6 / RF-2 — not assumed good).
- ``NOVELTY`` — the task class is novel against the recent-history set the
  caller passes (task-class novelty proxy, §3.4).
- ``STAKES`` — stakes signalled by explicit user framing or task class
  (§3.4).

Each AC maps:

- AC.MGRL.1 — :func:`evaluate_gate` emits a decision + the firing trigger
  from observable signals, with no LLM call on any path (this whole module
  is LLM-free by construction).
- AC.MGRL.4 — the three observable triggers are defined and each is
  recorded when it fires.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class Trigger(str, Enum):
    """The slice-1 observable trigger set (plan D-MGRL.4, all three)."""

    LOW_CONFIDENCE = "low_confidence"
    NOVELTY = "novelty"
    STAKES = "stakes"


@dataclass(frozen=True)
class GateSignals:
    """The observable, LLM-free inputs the gate scores (AC.MGRL.1).

    All fields are computable in the harness without an LLM call. The
    caller supplies what it observes at gate-time; absent signals default
    to the non-escalating value so a bare turn never escalates.
    """

    # The candidate / first-pass draft answer text whose hedging markers
    # the LOW_CONFIDENCE proxy reads. Empty string when no draft exists yet.
    draft_text: str = ""
    # The task-class label for this turn (novelty is scored against the
    # recent-history set). None when the caller does not classify tasks.
    task_class: str | None = None
    # The recent task classes the caller has seen; a task_class absent from
    # this set is NOVELTY. Empty set => any classified task is novel.
    recent_task_classes: frozenset[str] = field(default_factory=frozenset)
    # The user's prompt text — scanned for explicit high-stakes framing.
    prompt_text: str = ""
    # True when the task class is independently known high-stakes by the
    # caller (e.g. civic/medical/legal/financial/safety task routing).
    high_stakes_task_class: bool = False


# Hedging / uncertainty markers — the LOW_CONFIDENCE proxy. Word-boundary
# matched, case-insensitive. Deliberately a small, auditable set; its
# proxy-quality is measured by the experiment, not assumed (RF-2).
_HEDGE_MARKERS = (
    r"\bi'?m not sure\b",
    r"\bnot certain\b",
    r"\bi think\b",
    r"\bprobably\b",
    r"\bmight be\b",
    r"\bmaybe\b",
    r"\bunclear\b",
    r"\bi guess\b",
    r"\bcould be\b",
    r"\bhard to say\b",
)
_HEDGE_RE = re.compile("|".join(_HEDGE_MARKERS), re.IGNORECASE)

# Explicit high-stakes framing in the user's prompt — the STAKES proxy
# from user framing (§3.4). Word-boundary matched, case-insensitive.
_STAKES_MARKERS = (
    r"\bcritical\b",
    r"\bhigh[- ]stakes\b",
    r"\bmust be (?:right|correct|accurate)\b",
    r"\bdon'?t get this wrong\b",
    r"\bthis is important\b",
    r"\bsafety\b",
    r"\blegal\b",
    r"\bmedical\b",
    r"\bfinancial\b",
)
_STAKES_RE = re.compile("|".join(_STAKES_MARKERS), re.IGNORECASE)


@dataclass(frozen=True)
class GateDecision:
    """The gate's per-turn output (AC.MGRL.1).

    ``escalate`` is the binary decision; ``triggers`` is the ordered,
    de-duplicated list of every trigger that fired (empty iff not
    escalating). Recording *which* trigger fired is load-bearing for the
    theory-vs-generic discriminator (AC.MGRL.6) — escalation must be
    attributable to a specific trigger, not a bare boolean.
    """

    escalate: bool
    triggers: tuple[Trigger, ...] = ()

    @property
    def fired(self) -> bool:
        return bool(self.triggers)


def _low_confidence(signals: GateSignals) -> bool:
    return bool(signals.draft_text) and _HEDGE_RE.search(signals.draft_text) is not None


def _novelty(signals: GateSignals) -> bool:
    # A classified task absent from the recent-history set is novel. An
    # unclassified turn (task_class is None) carries no novelty signal.
    return (
        signals.task_class is not None
        and signals.task_class not in signals.recent_task_classes
    )


def _stakes(signals: GateSignals) -> bool:
    if signals.high_stakes_task_class:
        return True
    return bool(signals.prompt_text) and _STAKES_RE.search(signals.prompt_text) is not None


# The trigger-detector table — order fixes the reported trigger order so
# the per-trigger breakdown (AC.MGRL.6) is deterministic.
_DETECTORS: Sequence[tuple[Trigger, "callable[[GateSignals], bool]"]] = (
    (Trigger.LOW_CONFIDENCE, _low_confidence),
    (Trigger.NOVELTY, _novelty),
    (Trigger.STAKES, _stakes),
)


def evaluate_gate(signals: GateSignals) -> GateDecision:
    """Score the observable signals and emit the escalation decision.

    Deterministic, LLM-free, instant (a handful of compiled-regex
    searches + set membership). Satisfies AC.MGRL.1 (decision + firing
    trigger recorded, no LLM call on any path) and AC.MGRL.4 (the three
    observable triggers, each recorded when it fires). Escalate iff at
    least one trigger fires.
    """

    fired: list[Trigger] = [trig for trig, detect in _DETECTORS if detect(signals)]
    return GateDecision(escalate=bool(fired), triggers=tuple(fired))

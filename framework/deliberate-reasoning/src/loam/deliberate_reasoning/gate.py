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
escalate / don't-escalate decision (plan D-MGRL.1, D-MGRL.4; slice-3 D-SIT.*).

The gate decides, from **observable signals available at gate-time**,
whether the fast inference path answers (don't-escalate) or the deliberate
re-entrant loop engages (escalate). It makes **no LLM call** — sibling in
shape to ``intent_classifier.py`` (regex-scored, deterministic, instant,
zero token cost). An LLM-per-turn gate is the exact trap D-MGRL.1 rules out.

Slice-3 trigger substrate (plan D-SIT.1/.2/.3) — THE SHIPPING CHANGE:

The escalation decision is now driven by **STRUCTURAL situation signals**
derived from the pending action's structure + recent tool-result history
(``signals.py``), NOT by keyword-scanning the conversation. The four v1
structural signals are the live floor:

- ``UNBOUNDED_OP``        — about to run an unbounded / expensive operation.
- ``REPEAT_FAILED``       — repeating an approach that just failed this turn.
- ``MACHINE_IRREVERSIBLE``— about to act irreversibly on the user's machine.
- ``HIGH_BLAST_RADIUS``   — about to take a high-blast-radius action.

The slice-1 conversation-keyword detectors (``_HEDGE_RE`` over ``draft_text``,
``_STAKES_RE`` over ``prompt_text``) are **DEMOTED**: they are retired from
the default escalation path and run ONLY when a caller explicitly opts in via
``GateSignals.keyword_triggers_enabled`` (default False) — a documented
deprecation, not a silent behavior change (plan §15 / D-SIT.3). The default
live path is structural-only, so the owner's objection (no
conversation-keyword triggers firing on the live path) is satisfied while the
``evaluate_gate(GateSignals) -> GateDecision`` contract SHAPE is preserved.

``NOVELTY`` is RETAINED: it is set-membership on a ``task_class`` label, NOT a
prompt keyword-scan (D-SIT.3 edge-case ruling — admissible iff the label is
structurally derived; the slice-1 experiment derives it from a static task-set
field, never a prompt scan). It is admissible as a MECHANISM but is not part
of the v1 structural ship set; it stays available for the structurally-labelled
caller.

Each AC maps:

- AC.TRIG.1 — :func:`evaluate_gate` escalates on a structural-signal turn with
  NO old keywords and declines a keyword-only turn with a safe pending action.
- AC.TRIG.3 — the structural detectors read admissible sources only; the
  keyword detectors are demoted off the default path.
- AC.MGRL.1 / AC.MGRL.4 — the contract shape (decision + firing triggers, no
  LLM call) is preserved for slice-1 callers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from .signals import (
    PendingAction,
    SituationSignal,
    ToolResultRing,
    detect_situation_signals,
)


class Trigger(str, Enum):
    """The gate's trigger set.

    Slice-3 STRUCTURAL members (the v1 situation set, plan §3.2) — these are
    the live escalation drivers:

    - ``UNBOUNDED_OP`` / ``REPEAT_FAILED`` / ``MACHINE_IRREVERSIBLE`` /
      ``HIGH_BLAST_RADIUS``.

    Retained ``NOVELTY`` — set-membership on a structurally-supplied
    ``task_class`` label (admissible mechanism, D-SIT.3 edge case).

    DEMOTED slice-1 conversation-keyword members (``LOW_CONFIDENCE`` /
    ``STAKES``) — retained in the enum for the deprecation path only; they
    fire ONLY when ``GateSignals.keyword_triggers_enabled`` is explicitly set
    (default OFF). Off the default live path entirely (D-SIT.3).
    """

    # Slice-3 structural situation signals (the v1 live floor).
    UNBOUNDED_OP = "unbounded_op"
    REPEAT_FAILED = "repeat_failed"
    MACHINE_IRREVERSIBLE = "machine_irreversible"
    HIGH_BLAST_RADIUS = "high_blast_radius"

    # Retained — structurally-derived label membership (admissible).
    NOVELTY = "novelty"

    # DEMOTED slice-1 conversation-keyword triggers (deprecation path only).
    LOW_CONFIDENCE = "low_confidence"
    STAKES = "stakes"


# Map each structural SituationSignal to its Trigger member so the gate's
# recorded trigger list stays a single enum (the slice-1 contract).
_SIGNAL_TO_TRIGGER: dict[SituationSignal, Trigger] = {
    SituationSignal.UNBOUNDED_OP: Trigger.UNBOUNDED_OP,
    SituationSignal.REPEAT_FAILED: Trigger.REPEAT_FAILED,
    SituationSignal.MACHINE_IRREVERSIBLE: Trigger.MACHINE_IRREVERSIBLE,
    SituationSignal.HIGH_BLAST_RADIUS: Trigger.HIGH_BLAST_RADIUS,
}


@dataclass(frozen=True)
class GateSignals:
    """The observable, LLM-free inputs the gate scores (AC.MGRL.1 / AC.TRIG.*).

    Slice-3: the escalation decision is driven by ``pending_action`` +
    ``result_ring`` (the STRUCTURAL substrate, ``signals.py``). The slice-1
    conversation-keyword fields (``draft_text`` / ``prompt_text``) are RETAINED
    for the deprecation path but do NOT drive escalation unless
    ``keyword_triggers_enabled`` is explicitly True (default OFF) — the
    documented demotion (plan §15 / D-SIT.3).

    All fields are computable in the harness without an LLM call. Absent
    signals default to the non-escalating value so a bare turn never escalates.
    """

    # ---- Slice-3 STRUCTURAL substrate (the live escalation drivers) --------
    # The structural description of the pending tool call (PreToolUse envelope
    # view). None on a turn with no pending action (e.g. a pure-draft turn).
    pending_action: PendingAction | None = None
    # The recent-tool-RESULT ring (the REPEAT_FAILED substrate). Action
    # metadata only — no conversation text.
    result_ring: ToolResultRing | None = None

    # ---- Retained structurally-derived label (NOVELTY) ---------------------
    # The task-class label for this turn (novelty is scored against the
    # recent-history set). None when the caller does not classify tasks. Per
    # D-SIT.3 this is admissible only when STRUCTURALLY derived (not a prompt
    # keyword-scan); the caller owns that derivation.
    task_class: str | None = None
    # The recent task classes the caller has seen; a task_class absent from
    # this set is NOVELTY. Empty set => any classified task is novel.
    recent_task_classes: frozenset[str] = field(default_factory=frozenset)

    # ---- DEMOTED slice-1 conversation-keyword fields (deprecation path) ----
    # The candidate / first-pass draft answer text. RETAINED for the
    # deprecation path only; drives escalation iff keyword_triggers_enabled.
    draft_text: str = ""
    # The user's prompt text. RETAINED for the deprecation path only; drives
    # escalation iff keyword_triggers_enabled.
    prompt_text: str = ""
    # True when the task class is independently known high-stakes by the
    # caller. Part of the demoted STAKES trigger.
    high_stakes_task_class: bool = False
    # The explicit opt-in for the DEMOTED conversation-keyword triggers
    # (``LOW_CONFIDENCE`` / ``STAKES``). Default OFF: the live path is
    # structural-only (D-SIT.3). A caller flips this to True only to exercise
    # the deprecated keyword path (the slice-1 deprecation seam).
    keyword_triggers_enabled: bool = False


# Hedging / uncertainty markers — the DEMOTED LOW_CONFIDENCE proxy. Off the
# default live path (D-SIT.3); runs only when keyword_triggers_enabled. Kept
# for the deprecation seam, never the live escalation driver.
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

# Explicit high-stakes framing in the user's prompt — the DEMOTED STAKES
# proxy. Off the default live path (D-SIT.3); runs only when
# keyword_triggers_enabled.
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
    theory-vs-generic discriminator (AC.MGRL.6) and for the live surfacing of
    *why* the gate fired (AC.WIRE.1) — escalation must be attributable to a
    specific trigger, not a bare boolean.
    """

    escalate: bool
    triggers: tuple[Trigger, ...] = ()

    @property
    def fired(self) -> bool:
        return bool(self.triggers)


def _novelty(signals: GateSignals) -> bool:
    # A classified task absent from the recent-history set is novel. An
    # unclassified turn (task_class is None) carries no novelty signal. The
    # label is structurally supplied by the caller (D-SIT.3 admissibility).
    return (
        signals.task_class is not None
        and signals.task_class not in signals.recent_task_classes
    )


def _low_confidence(signals: GateSignals) -> bool:
    # DEMOTED — runs only on the explicit keyword-deprecation path.
    return bool(signals.draft_text) and _HEDGE_RE.search(signals.draft_text) is not None


def _stakes(signals: GateSignals) -> bool:
    # DEMOTED — runs only on the explicit keyword-deprecation path.
    if signals.high_stakes_task_class:
        return True
    return bool(signals.prompt_text) and _STAKES_RE.search(signals.prompt_text) is not None


def evaluate_gate(signals: GateSignals) -> GateDecision:
    """Score the observable signals and emit the escalation decision.

    Deterministic, LLM-free, instant (a handful of compiled-regex searches +
    set membership over the pending action's structure). Slice-3 escalation
    order:

    1. The four STRUCTURAL situation signals (``signals.py``) — the live floor
       (AC.TRIG.1/.2/.3/.4). Read from ``pending_action`` + ``result_ring``.
    2. ``NOVELTY`` — structurally-derived label membership (retained).
    3. The DEMOTED conversation-keyword triggers (``LOW_CONFIDENCE`` /
       ``STAKES``) — ONLY when ``keyword_triggers_enabled`` is explicitly True
       (default OFF; off the live path, D-SIT.3).

    Escalate iff at least one trigger fires. Trigger order is deterministic
    (structural signals, then NOVELTY, then the demoted keyword triggers) so
    the recorded list is stable.
    """

    fired: list[Trigger] = []

    # (1) The structural situation floor — the live escalation drivers.
    for sig in detect_situation_signals(signals.pending_action, signals.result_ring):
        fired.append(_SIGNAL_TO_TRIGGER[sig])

    # (2) Retained NOVELTY (structurally-derived label membership).
    if _novelty(signals):
        fired.append(Trigger.NOVELTY)

    # (3) DEMOTED conversation-keyword triggers — opt-in deprecation path only.
    if signals.keyword_triggers_enabled:
        if _low_confidence(signals):
            fired.append(Trigger.LOW_CONFIDENCE)
        if _stakes(signals):
            fired.append(Trigger.STAKES)

    return GateDecision(escalate=bool(fired), triggers=tuple(fired))

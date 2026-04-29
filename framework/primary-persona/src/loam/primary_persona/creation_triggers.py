"""Creation-trigger detector (D5).

Five deterministic signals monitor ongoing work for opportunities to
author a new specialist persona. When a threshold is crossed, a
judgment LLM call decides `yes | no | defer`. `yes` triggers the
authoring pipeline (D6); `no` records the rejection; `defer` schedules
a re-check.

The five signals (proposal §Autonomous authoring):
  1. `request_decline` — repeated pushback in a domain.
  2. `domain_correction` — user corrects the primary persona's
     domain handling.
  3. `cross_domain_scope` — scopes that keep touching a domain the
     primary isn't good at.
  4. `low_relevance_memory_hit` — retrieval returns peripheral matches
     on a topic.
  5. `explicit_user_mention` — "wish I had someone for X".

Thresholds are tunable per workspace; default values follow Eve's
flagged inference in the brief (3 repeated declines in a 7-day window,
and equivalent defaults for the other signals).
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Iterable


# ---- types ------------------------------------------------------------


class TriggerSignal(str, Enum):
    request_decline = "request_decline"
    domain_correction = "domain_correction"
    cross_domain_scope = "cross_domain_scope"
    low_relevance_memory_hit = "low_relevance_memory_hit"
    explicit_user_mention = "explicit_user_mention"


@dataclass(frozen=True)
class ThresholdRubric:
    """Per-signal threshold configuration.

    Each signal is counted over a rolling window. When the count
    within the window meets `min_count`, the threshold is crossed and
    the judgment LLM runs.

    Default values (Eve's flagged inference in the brief; tunable
    per workspace):
        request_decline: 3 within 7 days
        domain_correction: 2 within 7 days
        cross_domain_scope: 5 scopes within 14 days
        low_relevance_memory_hit: 5 queries within 7 days
        explicit_user_mention: 1 (fires immediately)
    """

    signal: TriggerSignal
    min_count: int
    window_seconds: float

    @classmethod
    def defaults(cls) -> dict[TriggerSignal, "ThresholdRubric"]:
        day = 86_400.0
        return {
            TriggerSignal.request_decline: cls(
                signal=TriggerSignal.request_decline,
                min_count=3,
                window_seconds=7 * day,
            ),
            TriggerSignal.domain_correction: cls(
                signal=TriggerSignal.domain_correction,
                min_count=2,
                window_seconds=7 * day,
            ),
            TriggerSignal.cross_domain_scope: cls(
                signal=TriggerSignal.cross_domain_scope,
                min_count=5,
                window_seconds=14 * day,
            ),
            TriggerSignal.low_relevance_memory_hit: cls(
                signal=TriggerSignal.low_relevance_memory_hit,
                min_count=5,
                window_seconds=7 * day,
            ),
            TriggerSignal.explicit_user_mention: cls(
                signal=TriggerSignal.explicit_user_mention,
                min_count=1,
                window_seconds=7 * day,
            ),
        }


@dataclass(frozen=True)
class CreationTrigger:
    """Record of a single signal observation, timestamped for window
    rollup.

    `domain` is a short name the signal is bucketed under — e.g.
    "legal", "finance", "cooking". Thresholds are per-(signal, domain);
    three declines in *different* domains is not a signal that a new
    persona is wanted.
    """

    signal: TriggerSignal
    domain: str
    observed_at: float  # unix seconds
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal.value,
            "domain": self.domain,
            "observed_at": self.observed_at,
            "note": self.note,
        }


class JudgmentVerdict(str, Enum):
    yes = "yes"
    no = "no"
    defer = "defer"


@dataclass(frozen=True)
class JudgmentResult:
    verdict: JudgmentVerdict
    rationale: str
    defer_seconds: float | None = None


# The judgment callable — workspaces (and tests) inject Claude-via-Max
# here. Takes the signal, domain, and recent observations; returns
# verdict + rationale.
JudgmentFn = Callable[
    [TriggerSignal, str, list[CreationTrigger]],
    Awaitable[JudgmentResult],
]


# ---- detector --------------------------------------------------------


@dataclass
class CreationTriggerDetector:
    """Rolling-window detector.

    Workspaces feed signals via `observe(...)`; on each observation the
    detector checks whether the (signal, domain) bucket has crossed
    its threshold and, if so, runs the async judgment callable.
    """

    rubrics: dict[TriggerSignal, ThresholdRubric] = field(
        default_factory=ThresholdRubric.defaults
    )
    judgment_fn: JudgmentFn | None = None

    # In-memory observations. Production wiring will persist through
    # memory-system; for the primitive, an in-process deque is fine.
    observations: list[CreationTrigger] = field(default_factory=list)
    # Map of (signal, domain) → last-judgment-timestamp so `defer`
    # suppresses re-checks within the defer window.
    _defer_until: dict[tuple[str, str], float] = field(default_factory=dict)
    # Rejected-for-now record: (signal, domain) → rationale.
    _rejections: list[dict[str, Any]] = field(default_factory=list)

    def observe(self, trigger: CreationTrigger) -> None:
        """Record a signal observation. Pure — does not check
        thresholds. Call `evaluate` after."""
        self.observations.append(trigger)

    def count_in_window(
        self,
        signal: TriggerSignal,
        domain: str,
        *,
        now: float | None = None,
    ) -> int:
        """How many observations of (signal, domain) are in the
        configured window?"""
        rubric = self.rubrics.get(signal)
        if rubric is None:
            return 0
        current = now if now is not None else time.time()
        cutoff = current - rubric.window_seconds
        return sum(
            1
            for t in self.observations
            if t.signal == signal and t.domain == domain and t.observed_at >= cutoff
        )

    def threshold_crossed(
        self,
        signal: TriggerSignal,
        domain: str,
        *,
        now: float | None = None,
    ) -> bool:
        rubric = self.rubrics.get(signal)
        if rubric is None:
            return False
        if self._is_deferred(signal, domain, now=now):
            return False
        return self.count_in_window(signal, domain, now=now) >= rubric.min_count

    async def evaluate(
        self,
        signal: TriggerSignal,
        domain: str,
        *,
        now: float | None = None,
    ) -> JudgmentResult | None:
        """If the threshold is crossed, run the judgment callable and
        return its verdict. Returns None if the threshold is not
        crossed or no judgment function is installed.

        On `defer`, the detector records the defer window and will not
        re-evaluate this (signal, domain) until the window expires.
        On `no`, the rejection is appended to the rejections log.
        """
        if not self.threshold_crossed(signal, domain, now=now):
            return None
        if self.judgment_fn is None:
            return None
        recent = [
            t
            for t in self.observations
            if t.signal == signal and t.domain == domain
        ]
        result = await self.judgment_fn(signal, domain, recent)
        key = (signal.value, domain)
        current = now if now is not None else time.time()
        if result.verdict == JudgmentVerdict.defer:
            delay = result.defer_seconds or 3600.0
            self._defer_until[key] = current + delay
        elif result.verdict == JudgmentVerdict.no:
            self._rejections.append(
                {
                    "signal": signal.value,
                    "domain": domain,
                    "rationale": result.rationale,
                    "recorded_at": current,
                }
            )
        return result

    def rejections(self) -> list[dict[str, Any]]:
        return list(self._rejections)

    def _is_deferred(
        self,
        signal: TriggerSignal,
        domain: str,
        *,
        now: float | None = None,
    ) -> bool:
        key = (signal.value, domain)
        until = self._defer_until.get(key)
        if until is None:
            return False
        current = now if now is not None else time.time()
        return current < until

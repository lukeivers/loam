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

"""Notification + safe-mode narrative (D5 + D6).

Compound-OR threshold: wall-clock ≥ 5min OR paused-scope count ≥ 3 OR
any paused scope carries a user-relevant escalation trigger OR auth-
broken (always fires).

Delivery: the primary-persona layer's `OneOnOneChannel` type, reused
verbatim. The dispatcher here is a parallel sibling of the sealed
IntroductionDispatcher — same one-on-one invariant enforced at
construction; group channels rejected at type level.

Narrative: Claude-authored via the degradation component's ClaudeClient
when Claude is partially available (rate-limited / garbage / latency /
partial-overloaded). Deterministic fallback template when Claude is the
failure source itself (down / fully-overloaded / auth-broken).

Tier: Tier 2 default (silent); Tier 1 for auth-broken (audible push).
The tier is carried on the notification payload; the channel `send`
callable is channel-agnostic and receives the rendered text.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Sequence

from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel

from . import observability as obs
from .adapter import ClaudeClient
from .config import DegradationConfig
from .errors import ClaudeAPIError
from .fsm import DegradationMode


# ---- types -------------------------------------------------------------


class NotificationTier(int, Enum):
    tier_1 = 1  # audible / action required
    tier_2 = 2  # silent / worth knowing


class ThresholdTrigger(str, Enum):
    time = "time"
    count = "count"
    criticality = "criticality"
    auth_broken = "auth_broken"


@dataclass(frozen=True)
class DegradationNotification:
    episode_id: str
    tier: NotificationTier
    threshold_triggered: ThresholdTrigger
    text: str
    kind: str  # "alert" | "resume"


# ---- channel -----------------------------------------------------------


@dataclass(frozen=True)
class DegradationChannel(OneOnOneChannel):
    """Subclass of the sealed OneOnOneChannel.

    Reuses the `__post_init__` guard (is_group rejected at
    construction), so the one-on-one invariant is enforced by the
    sealed type, not re-implemented. v1.2 R15 compliance.
    """

    # No new fields; the subclass is a nominal distinction so tests can
    # discriminate degradation channels from intro channels.
    pass


# ---- dispatcher --------------------------------------------------------


@dataclass
class DegradationNotifier:
    """Sends degradation notifications via registered one-on-one channels.

    - Rejects group channels at construction.
    - Picks the first `is_active` channel.
    - Queues to disk if no channel is active (parallel to the sealed
      IntroductionDispatcher pattern).
    """

    channels: Sequence[OneOnOneChannel]
    queue_dir: Any | None = None  # Path, but left Any to avoid import cost
    _pending_queue: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "degradation notifications are one-on-one only "
                    "(v1.1 R13 + v1.2 R15)."
                )

    async def send(self, notification: DegradationNotification) -> bool:
        """Dispatch the notification. Returns True if delivered, False
        if queued (no active channel) or failed."""
        active = [c for c in self.channels if c.is_active]
        if not active:
            payload = {
                "episode_id": notification.episode_id,
                "tier": notification.tier.value,
                "threshold_triggered": notification.threshold_triggered.value,
                "text": notification.text,
                "kind": notification.kind,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            self._pending_queue.append(payload)
            obs.notification_dispatched(
                episode_id=notification.episode_id,
                channel="<none>",
                outcome="queued_no_channel",
                threshold_triggered=notification.threshold_triggered.value,
                tier=notification.tier.value,
            )
            return False
        channel = active[0]
        try:
            await channel.send(notification.text)
        except Exception as e:  # noqa: BLE001
            obs.notification_dispatched(
                episode_id=notification.episode_id,
                channel=channel.name,
                outcome=f"failed:{e}",
                threshold_triggered=notification.threshold_triggered.value,
                tier=notification.tier.value,
            )
            return False
        obs.notification_dispatched(
            episode_id=notification.episode_id,
            channel=channel.name,
            outcome="delivered",
            threshold_triggered=notification.threshold_triggered.value,
            tier=notification.tier.value,
        )
        return True

    async def flush_queue(self) -> list[DegradationNotification]:
        active = [c for c in self.channels if c.is_active]
        if not active:
            return []
        delivered: list[DegradationNotification] = []
        remaining: list[dict[str, Any]] = []
        for payload in self._pending_queue:
            channel = active[0]
            try:
                await channel.send(payload["text"])
                delivered.append(
                    DegradationNotification(
                        episode_id=payload["episode_id"],
                        tier=NotificationTier(payload["tier"]),
                        threshold_triggered=ThresholdTrigger(
                            payload["threshold_triggered"]
                        ),
                        text=payload["text"],
                        kind=payload["kind"],
                    )
                )
            except Exception:
                remaining.append(payload)
        self._pending_queue = remaining
        return delivered


# ---- threshold evaluator -----------------------------------------------


@dataclass
class ThresholdEvaluator:
    """Compound-OR threshold (research §3.a / Luke's decision).

    `evaluate` returns a `ThresholdTrigger` when a condition is met, or
    None otherwise. `dedupe_key` is the episode UUID; the caller
    tracks whether a given (episode, kind) has been notified already.
    """

    cfg: DegradationConfig

    def evaluate(
        self,
        *,
        mode: DegradationMode,
        episode_started_at: float,
        now: float,
        paused_scope_count: int,
        any_user_relevant_scope: bool,
    ) -> ThresholdTrigger | None:
        # Auth-broken always wins immediately.
        if mode == DegradationMode.auth_broken:
            return ThresholdTrigger.auth_broken
        # Time.
        if (now - episode_started_at) >= self.cfg.notification.thresholds.time_seconds:
            return ThresholdTrigger.time
        # Count.
        if (
            paused_scope_count
            >= self.cfg.notification.thresholds.paused_scope_count
        ):
            return ThresholdTrigger.count
        # Criticality.
        if any_user_relevant_scope:
            return ThresholdTrigger.criticality
        return None


# ---- narrative renderer ------------------------------------------------


@dataclass
class NarrativeRenderer:
    """Builds the notification text.

    Modes that should attempt Claude-authored narrative:
      rate_limited, garbage, latency_sustained

    Modes that must use the deterministic template (Claude is the
    failure source):
      down, overloaded (trip), auth_broken

    The decision is encoded in `_use_claude_narrative`.
    """

    cfg: DegradationConfig
    client: ClaudeClient | None = None  # None → always fall back

    _TEMPLATE_MODES = {
        DegradationMode.down,
        DegradationMode.overloaded,
        DegradationMode.auth_broken,
    }

    async def render_alert(
        self,
        *,
        episode_id: str,
        mode: DegradationMode,
        signal: str,
        policy: str,
        paused_scope_count: int,
    ) -> str:
        recommendation = self._recommendation_for(mode)
        resume_conditions = self._resume_conditions_for(mode)
        params = {
            "signal": signal,
            "mode": mode.value,
            "policy": policy,
            "paused_scope_count": paused_scope_count,
            "recommendation": recommendation,
            "resume_conditions": resume_conditions,
            "episode_id": episode_id,
        }
        template_text = self.cfg.narrative.fallback_template.format(**params)
        if mode in self._TEMPLATE_MODES or self.client is None:
            return template_text
        # Attempt Claude-authored narrative; fall back on timeout/error.
        prompt = (
            "Claude upstream has entered a degraded state.\n"
            f"Detected signal: {signal}\n"
            f"Mode: {mode.value}\n"
            f"Paused scope count: {paused_scope_count}\n"
            f"Policy applied: {policy}\n"
            "Write a 2-3 sentence plain-language summary for the user:\n"
            "(a) what is paused; (b) why; (c) what happens next.\n"
            "Do not speculate about cause; report only the observed signal.\n"
            "Do not use any persona voice — you are narrating from the framework layer."
        )
        try:
            coro = self.client.call(
                prompt_name="degradation-narrative",
                text=prompt,
                model=self.cfg.narrative.model,
            )
            result = await asyncio.wait_for(
                coro, timeout=self.cfg.narrative.timeout_seconds
            )
            narrative = (result.text or "").strip()
            if not narrative:
                return template_text
            return f"[pOS — claude upstream degraded]\n{narrative}"
        except (ClaudeAPIError, asyncio.TimeoutError, Exception):  # noqa: BLE001
            return template_text

    def render_recovery(
        self,
        *,
        episode_id: str,
        resumed_count: int,
        duration_seconds: float,
    ) -> str:
        return self.cfg.narrative.recovery_template.format(
            episode_id=episode_id,
            resumed_count=resumed_count,
            duration_seconds=duration_seconds,
        )

    # ---- per-mode copy ------------------------------------------------

    def _recommendation_for(self, mode: DegradationMode) -> str:
        return {
            DegradationMode.down: "Wait for upstream recovery; probe resumes automatically.",
            DegradationMode.overloaded: "Wait briefly; automatic probe recovery follows.",
            DegradationMode.rate_limited: "Wait for the rate window to clear.",
            DegradationMode.garbage: "Review recent outputs; probe recovery follows.",
            DegradationMode.auth_broken: "Update your ANTHROPIC_API_KEY, then reply 'resume'.",
            DegradationMode.latency_sustained: "Advisory only; no action required.",
        }.get(mode, "No action required.")

    def _resume_conditions_for(self, mode: DegradationMode) -> str:
        return {
            DegradationMode.down: f"{int(self.cfg.modes.down.half_open_dwell_seconds or 30)}s dwell + 1 probe",
            DegradationMode.overloaded: f"{int(self.cfg.modes.overloaded.half_open_dwell_seconds or 15)}s dwell + 1 probe",
            DegradationMode.rate_limited: "retry-after elapses + 1 probe",
            DegradationMode.garbage: f"{int(self.cfg.modes.garbage.half_open_dwell_seconds)}s dwell + 2 probes",
            DegradationMode.auth_broken: "user confirms credential fix + 1 probe",
            DegradationMode.latency_sustained: "advisory — no resume gate",
        }.get(mode, "")


def tier_for_mode(cfg: DegradationConfig, mode: DegradationMode) -> NotificationTier:
    if mode == DegradationMode.auth_broken:
        return NotificationTier(cfg.notification.auth_broken_tier)
    return NotificationTier(cfg.notification.default_tier)

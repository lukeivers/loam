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

"""Watchdog — proactive stuck-agent + dead-channel detection (AC.SR-WATCH.*).

Part 2 of the self-recovery system. The watchdog detects trouble WITHOUT
waiting for the user to notice:

  * **Stuck/silent agent (AC.SR-WATCH.1).** A progress heartbeat that has
    not advanced past a tunable threshold means the agent stalled. This is
    the *route-to-recovery* leg on a detected stall — it composes the
    dormancy detection rubric's intent (no-progress-past-threshold) and
    adds the recovery routing; it does NOT re-implement dormancy's
    degradation FSM (plan §2: "adds the route-to-plain-recovery leg, not a
    new detector"). No user distress signal is required to fire it.

  * **Dead comms channel (AC.SR-WATCH.2).** The telegram-interface
    ``AvailabilityProbe`` answers "is the user-visible channel live?". A
    negative probe triggers the outage self-heal path — out-of-band
    notify via ``write_fallback`` (the existing durable fallback surface),
    so a down channel does not become silent-night silence.

Composition boundary (plan §8 halt-trigger 3): the watchdog CALLS the
public surfaces of the sealed primitives (``AvailabilityProbe.probe_once``,
``write_fallback``); it does not edit them. The stall heartbeat is the new
in-fence code.

Determinism: the stall check is pure arithmetic over an injected clock +
a recorded heartbeat. The dead-channel leg awaits the injected probe. No
LLM, no API key.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable


# ---------------------------------------------------------------------------
# Stuck/silent-agent detection (AC.SR-WATCH.1).
# ---------------------------------------------------------------------------

#: Default stall threshold (seconds). If the progress heartbeat has not
#: advanced within this window, the agent is treated as stuck. Tunable
#: (the threshold is the builder's call per ODD §1.1; the AC pins
#: proactive detection, not the number).
DEFAULT_STALL_THRESHOLD_SECONDS = 300


@dataclass
class StallWatchdog:
    """Tracks a progress heartbeat and detects a stall past the threshold.

    Production callers ``beat()`` whenever observable progress is made (a
    tool call returns, an artifact is written). ``is_stuck()`` answers
    "has progress gone quiet past the threshold?" with NO user signal
    required — that is the proactive property AC.SR-WATCH.1 pins.

    ``clock`` is injectable for deterministic tests.
    """

    stall_threshold_seconds: float = DEFAULT_STALL_THRESHOLD_SECONDS
    clock: Callable[[], float] = field(default=time.monotonic)
    _last_beat: float | None = field(default=None, init=False)

    def beat(self) -> None:
        """Record observable progress (resets the stall timer)."""
        self._last_beat = self.clock()

    def seconds_since_progress(self) -> float | None:
        """Seconds since the last heartbeat, or ``None`` if never beaten."""
        if self._last_beat is None:
            return None
        return self.clock() - self._last_beat

    def is_stuck(self) -> bool:
        """True iff progress has gone quiet past the stall threshold.

        A watchdog that has never seen a heartbeat is NOT stuck (nothing
        has started); a watchdog whose last heartbeat is older than the
        threshold IS stuck.
        """
        elapsed = self.seconds_since_progress()
        if elapsed is None:
            return False
        return elapsed >= self.stall_threshold_seconds


@dataclass(frozen=True)
class StuckVerdict:
    """The result of a stuck-agent check routed to recovery."""

    stuck: bool
    seconds_since_progress: float | None
    #: Plain-language phrase for the recovery surface (no internal IDs).
    detail: str


def evaluate_stall(watchdog: StallWatchdog) -> StuckVerdict:
    """Evaluate the watchdog and produce a recovery-routable verdict.

    This is the route-to-recovery leg: it turns the raw stall boolean into
    a plain-language verdict the recovery surface can render, WITHOUT a
    user signal.
    """
    elapsed = watchdog.seconds_since_progress()
    stuck = watchdog.is_stuck()
    if stuck:
        detail = "work seems to have gone quiet and may be stuck"
    else:
        detail = "work is progressing normally"
    return StuckVerdict(
        stuck=stuck, seconds_since_progress=elapsed, detail=detail
    )


# ---------------------------------------------------------------------------
# Dead-channel detection + self-heal (AC.SR-WATCH.2).
# ---------------------------------------------------------------------------

#: An async probe returning True when the user-visible channel is live.
#: In production this wraps ``AvailabilityProbe.probe_once`` (mapping its
#: ``ProbeResult.available`` to a bool); the watchdog only needs the
#: boolean answer, so it accepts any async callable -> bool.
ChannelProbe = Callable[[], Awaitable[bool]]

#: The out-of-band delivery surface. In production this is the
#: telegram-interface ``write_fallback`` coroutine; tests pass a fake. It
#: takes the plain-language text + a reason and returns the surfaces that
#: accepted it.
FallbackDeliver = Callable[..., Awaitable[list[str]]]


@dataclass(frozen=True)
class ChannelVerdict:
    """The result of a dead-channel check + self-heal attempt."""

    channel_live: bool
    #: Surfaces the out-of-band notify reached (empty when channel live —
    #: no fallback needed). ``None`` when a self-heal was attempted but
    #: the caller suppressed delivery.
    fallback_surfaces: tuple[str, ...]
    detail: str


async def check_channel_and_self_heal(
    *,
    probe: ChannelProbe,
    deliver: FallbackDeliver,
    notice_text: str = (
        "It looks like the usual way I reach you went quiet, so I am sending "
        "this another way. I am still working and will keep you posted."
    ),
) -> ChannelVerdict:
    """Detect a dead channel and, if dead, attempt the out-of-band self-heal.

    Composes the availability probe (dead-channel detection) + the outage
    self-heal procedure (out-of-band notify via the durable fallback
    surface). When the channel is live, no fallback is sent. When dead,
    ``deliver`` is invoked with a plain-language notice and the surfaces it
    reached are returned — so a down channel does not become silent.

    No user signal is required: this is the proactive leg.
    """
    try:
        live = bool(await probe())
    except Exception:  # noqa: BLE001 — a probe error is treated as "dead"
        live = False

    if live:
        return ChannelVerdict(
            channel_live=True,
            fallback_surfaces=(),
            detail="your messaging channel is working",
        )

    surfaces = await deliver(
        text=notice_text,
        reason="self-recovery-watchdog/channel-down",
    )
    return ChannelVerdict(
        channel_live=False,
        fallback_surfaces=tuple(surfaces),
        detail="your messaging channel went quiet; I reached you another way",
    )


# ---------------------------------------------------------------------------
# Production adapter helpers — map the sealed primitives' richer surfaces to
# the thin boolean the watchdog consumes (keeps the composition a library
# call, not a reimplementation).
# ---------------------------------------------------------------------------


def availability_probe_to_channel_probe(probe: object) -> ChannelProbe:
    """Adapt a telegram-interface ``AvailabilityProbe`` to a ``ChannelProbe``.

    Calls ``probe.probe_once()`` and maps ``ProbeResult.available`` to the
    bool the watchdog needs. Kept as a thin adapter so the watchdog never
    imports the probe type directly (the composition stays a public-surface
    call).
    """

    async def _probe() -> bool:
        result = await probe.probe_once()  # type: ignore[attr-defined]
        return bool(getattr(result, "available", False))

    return _probe

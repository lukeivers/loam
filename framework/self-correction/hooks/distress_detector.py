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

"""Distress-signal detector — the inbound-path fire-alarm (AC.SR-DISTRESS.1).

The non-tech-user self-recovery system's first part. Repeated/escalating
user distress on the inbound-message path ("are you there? / is this
broken? / you keep saying X but don't") is detected DETERMINISTICALLY — a
phrase/escalation rubric + a persistent rolling-window counter — and, **by
the 2nd qualifying signal**, TRIPS the self-diagnosis routine.

Design constraints baked (plan §3 R-2, §8):

  * **Deterministic, no LLM, no network, no API key.** The detector is a
    phrase/escalation rubric, not an intent-classifier
    (``feedback_no_anthropic_api_key``). Stdlib only. A message either
    matches the rubric or it does not; there is no model call.

  * **2nd signal at the latest** (the fire-alarm law,
    ``feedback_user_distress_is_priority_diagnostic_signal``). The
    detector trips on the 2nd qualifying signal within the rolling
    window — biased EARLY, because a spurious self-diagnosis is cheap +
    silent-if-clean whereas a missed one is the "stuck forever" failure
    (plan §10 #3 / FORK F-2, ruling: bias-early).

  * **The detector FEEDS the existing engine, it is not a new engine**
    (Lens 1). On trip it hands a plain-language description to
    ``build_trigger_from_user_report`` (the existing self-correction
    ``user_reported`` trigger surface), which opens a real correction
    episode. This module owns DETECTION; the correction engine is reused.

The hook entry-point (``main``) reads the Claude Code inbound-hook JSON
from stdin (the ``UserPromptSubmit`` surface), updates the persistent
counter, and emits a structured decision on stdout. The SEALED deliverable
is this framework-tracked entry-point + its tests; WIRING it into a live
``settings.json`` is owner-gated instance-config (out of this cycle).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# The distress rubric (deterministic — the exact shape of the silent-night
# distress memory). Three escalation classes; any match is a qualifying
# signal. The classes are ALSO used by the self-diagnosis to bias which
# root-cause check runs first, but for the trip the only thing that matters
# is "is this a qualifying distress signal?".
# ---------------------------------------------------------------------------

#: "are you there? / hello? / you still working?" — the are-you-alive class.
_PRESENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bare you (?:there|alive|still (?:there|here|working|on))\b"),
    re.compile(r"\b(?:hello|hey|you there)\?+"),
    re.compile(r"\byou (?:still|even) (?:there|working|alive)\b"),
    re.compile(r"\banyone (?:there|home)\b"),
    re.compile(r"\bdid you (?:die|crash|freeze|stall|hang)\b"),
)

#: "is this broken? / is it stuck? / nothing's happening" — the is-it-broken
#: class.
_BROKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "is this broken / is this thing stuck / is it all frozen" — allow an
    # intervening noun phrase between the subject and the state word.
    re.compile(
        r"\bis (?:this|it|that|loam|everything|the \w+)(?: \w+){0,3}? "
        r"(?:broken|stuck|frozen|dead|hung|working)\b"
    ),
    re.compile(r"\bnothing(?:'s| is)? (?:happening|working|moving)\b"),
    re.compile(r"\b(?:this|it)(?:'s| is) (?:broken|stuck|frozen|not working)\b"),
    re.compile(r"\bwhy (?:isn't|is nothing|won't (?:it|this))\b"),
    re.compile(r"\bit (?:stopped|froze|hung|crashed)\b"),
)

#: "you keep saying X but don't / you said you would but" — the
#: claim-without-action class (the narration-not-action distress shape).
_UNFULFILLED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\byou keep saying\b"),
    re.compile(r"\byou (?:said|told me|claimed|promised)\b.*\bbut\b"),
    re.compile(r"\byou (?:said|keep saying) (?:you('?d| would| will))?\b.*\b(?:didn'?t|never|haven'?t|not)\b"),
    re.compile(r"\bbut (?:nothing|it didn'?t|you didn'?t|you never)\b"),
    re.compile(r"\b(?:still|yet) (?:waiting|nothing)\b"),
)


class DistressClass:
    """The three qualifying distress classes (string constants, not an Enum
    — the hook surface serializes them to JSON and the values are part of
    the recovery surface's plain-language routing)."""

    presence = "presence"
    broken = "broken"
    unfulfilled = "unfulfilled"


def classify_distress(text: str) -> str | None:
    """Return the DistressClass of *text*, or ``None`` if not distress.

    Deterministic. Case-insensitive. The FIRST class whose rubric matches
    wins; ``None`` means the message is not a qualifying distress signal
    (so a chatty non-distress user never trips the counter).
    """
    low = text.lower()
    for patt in _UNFULFILLED_PATTERNS:
        if patt.search(low):
            return DistressClass.unfulfilled
    for patt in _PRESENCE_PATTERNS:
        if patt.search(low):
            return DistressClass.presence
    for patt in _BROKEN_PATTERNS:
        if patt.search(low):
            return DistressClass.broken
    return None


# ---------------------------------------------------------------------------
# The rolling-window counter (persistent, deterministic).
# ---------------------------------------------------------------------------

#: Default rolling window (seconds). Qualifying signals older than this are
#: evicted before the trip check. FORK F-2 ruling: short window, bias-early.
DEFAULT_WINDOW_SECONDS = 600

#: Default trip threshold (count of qualifying signals within the window).
#: FORK F-2 ruling: 2nd signal at the latest (the fire-alarm law). The trip
#: is ``>=`` so the 2nd qualifying signal fires.
DEFAULT_TRIP_THRESHOLD = 2


@dataclass
class DistressDetector:
    """Persistent rolling-window distress counter.

    State is a small JSON file (``state_path``) holding the timestamps +
    classes of recent qualifying signals. ``window_seconds`` and
    ``trip_threshold`` are tunable (FORK F-2); the defaults bias early.

    ``clock`` is injectable for deterministic tests.
    """

    state_path: Path
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    trip_threshold: int = DEFAULT_TRIP_THRESHOLD
    clock: "callable[[], float]" = field(default=time.time)

    def __post_init__(self) -> None:
        self.state_path = Path(self.state_path)

    # ---- state I/O (atomic, stdlib-only) -----------------------------

    def _load(self) -> list[dict]:
        if not self.state_path.exists():
            return []
        try:
            data = json.loads(self.state_path.read_text())
        except (json.JSONDecodeError, OSError):
            # Malformed / unreadable state is treated as empty — the
            # detector never raises on environmental failure; a corrupt
            # counter resets rather than blocks the inbound path.
            return []
        signals = data.get("signals") if isinstance(data, dict) else None
        return signals if isinstance(signals, list) else []

    def _save(self, signals: list[dict]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps({"signals": signals}, indent=2))
        os.replace(tmp, self.state_path)

    def _evict_stale(self, signals: list[dict], now: float) -> list[dict]:
        cutoff = now - self.window_seconds
        return [s for s in signals if float(s.get("at", 0)) >= cutoff]

    # ---- the observe + trip decision ---------------------------------

    def observe(self, text: str) -> "DistressObservation":
        """Record one inbound message and decide whether it trips.

        Returns a ``DistressObservation``: ``classified`` (the class or
        None), ``window_count`` (qualifying signals now in the window),
        and ``tripped`` (True iff the count reached ``trip_threshold`` —
        i.e. by the 2nd qualifying signal at the default threshold).

        A non-distress message does not add to the counter and never
        trips. Stale signals are evicted before the count is taken, so
        the trip reflects only the rolling window.
        """
        now = self.clock()
        signals = self._evict_stale(self._load(), now)

        cls = classify_distress(text)
        if cls is None:
            # Persist the eviction so the window stays bounded, but do not
            # count a non-distress message.
            self._save(signals)
            return DistressObservation(
                classified=None,
                window_count=len(signals),
                tripped=False,
                window_classes=tuple(s.get("class", "") for s in signals),
            )

        signals.append({"at": now, "class": cls, "text": text})
        self._save(signals)
        count = len(signals)
        tripped = count >= self.trip_threshold
        return DistressObservation(
            classified=cls,
            window_count=count,
            tripped=tripped,
            window_classes=tuple(s.get("class", "") for s in signals),
        )

    def reset(self) -> None:
        """Clear the counter (called after a trip is handled, so the next
        distress sequence starts fresh)."""
        self._save([])


@dataclass(frozen=True)
class DistressObservation:
    """The result of ``DistressDetector.observe`` — a pure value object."""

    classified: str | None
    window_count: int
    tripped: bool
    window_classes: tuple[str, ...]


# ---------------------------------------------------------------------------
# The description the trip hands to the existing user_reported trigger. This
# is plain-language by construction (it becomes part of the correction
# episode's provenance) — no internal IDs.
# ---------------------------------------------------------------------------


def distress_trigger_description(obs: DistressObservation) -> str:
    """Render the plain-language description for the ``user_reported``
    trigger built on a trip.

    The text names WHAT the user expressed (repeated worry that something
    is stuck / not reaching them), not any internal mechanism — it feeds
    ``build_trigger_from_user_report(description=...)`` and surfaces in the
    correction provenance.
    """
    return (
        "The user expressed worry more than once in a short span that "
        "something might be stuck or not getting through to them. This is "
        "the fire-alarm signal: stop and check whether replies are actually "
        "reaching them and whether any claimed work was really done."
    )


# ---------------------------------------------------------------------------
# Hook entry-point (Claude Code inbound surface, e.g. UserPromptSubmit).
# Stdin: the hook JSON. Stdout: a structured decision. The SEALED
# deliverable is this entry-point + tests; wiring into a live settings.json
# is owner-gated instance-config (out of cycle).
# ---------------------------------------------------------------------------


def _default_state_path() -> Path:
    """Workspace-local counter path. Honours ``LOAM_DISTRESS_STATE`` for
    tests / instance-config; otherwise ``<cwd>/.loam/distress-counter.json``.
    """
    override = os.environ.get("LOAM_DISTRESS_STATE")
    if override:
        return Path(override)
    return Path.cwd() / ".loam" / "distress-counter.json"


def _extract_text(payload: dict) -> str:
    """Pull the user message text from the inbound hook JSON.

    Tolerant of the common shapes: ``prompt`` (UserPromptSubmit),
    ``message`` / ``text`` (generic). Returns "" when none present.
    """
    for key in ("prompt", "message", "text", "user_message"):
        val = payload.get(key)
        if isinstance(val, str):
            return val
    return ""


def main(argv: list[str] | None = None) -> int:
    """Read the inbound hook JSON from stdin; update the counter; emit a
    decision on stdout.

    Output JSON shape:
      {
        "distress": "<class>"|null,
        "window_count": <int>,
        "tripped": <bool>,
        "description": "<plain-language>"|null
      }

    Exit code is always 0 — the detector is advisory on the inbound path
    and must never block a user's message. The ``tripped`` flag is what a
    downstream wiring (owner-configured) routes on.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — inbound detector never crashes the path
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    text = _extract_text(payload) if isinstance(payload, dict) else ""
    detector = DistressDetector(state_path=_default_state_path())
    obs = detector.observe(text)

    decision = {
        "distress": obs.classified,
        "window_count": obs.window_count,
        "tripped": obs.tripped,
        "description": (
            distress_trigger_description(obs) if obs.tripped else None
        ),
    }
    sys.stdout.write(json.dumps(decision))
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised via main(argv)
    raise SystemExit(main())

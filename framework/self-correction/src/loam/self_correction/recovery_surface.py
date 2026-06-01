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

"""Plain-language recovery surface (AC.SR-RECOVER.1/.2).

Part 3 of the self-recovery system. Whatever the watchdog or the
self-diagnosis finds is rendered to the non-technical user as **clear
plain-English steps to get unstuck** — never a stack trace, never internal
IDs (the abstraction-first contract; the v0.7.0 stranger-clone probe shape
applied to the recovery surface).

Two hard properties this module guarantees:

  * **AC.SR-RECOVER.1** — the rendered surface is plain-language +
    actionable (gives the user a concrete next step a non-technical person
    can take), and never asks them to read logs, run dev commands, or know
    internal concepts.

  * **AC.SR-RECOVER.2** — the rendered surface carries ZERO internal
    vocabulary: no stack traces, no AC-IDs, no commit SHAs, no file paths,
    no agent-IDs, no ODD/methodology vocabulary. This is a HARD invariant
    (plan §8) verified by ``contains_internal_vocabulary`` — a probe over
    the rendered text. If the render cannot avoid leaking an internal ID,
    that is a halt condition, not best-effort.

Determinism: the render is a pure function over the findings; the probe is
a pure scan. No LLM, no API key.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# The zero-internal-vocabulary probe (AC.SR-RECOVER.2).
# ---------------------------------------------------------------------------

#: Patterns that mark internal vocabulary. The probe is intentionally
#: conservative — it flags the shapes the abstraction-first contract forbids
#: from ever reaching a non-technical user.
_INTERNAL_VOCAB_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # AC-IDs: AC.SR-RECOVER.2, AC.MIG-SAFE.4, etc.
    ("ac-id", re.compile(r"\bAC\.[A-Z0-9][A-Z0-9_\-]*\.[0-9]+")),
    # Commit SHAs: 7-40 hex chars as a standalone token.
    ("commit-sha", re.compile(r"\b[0-9a-f]{7,40}\b")),
    # File paths: anything with a slash + an extension, or a src/ tree, or a
    # dotted module path like loam.self_correction.foo.
    ("file-path", re.compile(r"[\w./-]+/[\w./-]+\.\w+")),
    ("module-path", re.compile(r"\bloam\.[a-z_]+(?:\.[a-z_]+)+")),
    ("src-tree", re.compile(r"\b(?:src|framework|tests?)/[\w./-]+")),
    # Stack-trace markers.
    ("traceback", re.compile(r"\bTraceback \(most recent call last\)")),
    ("exception-line", re.compile(r"\b[A-Za-z_]+(?:Error|Exception):")),
    ('file-line', re.compile(r'\bFile \"[^\"]+\", line \d+')),
    # Agent / scope / trigger IDs.
    ("agent-id", re.compile(r"\b(?:agent|scope|trigger|episode)[-_][0-9a-f]{4,}")),
    ("uuid-ish", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}")),
    # ODD / methodology vocabulary that must never surface to the user.
    (
        "methodology-vocab",
        re.compile(
            r"\b(?:ODD|CDC|acceptance criteri|reversibility class|"
            r"ProtectionFloorRefusal|MigrationSafetyEnvelope|"
            r"build_trigger_from_user_report|user_reported|AvailabilityProbe|"
            r"seal[- ]?test|fence|baseline|manifest|sidecar)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class VocabularyHit:
    """One internal-vocabulary match found in a rendered surface."""

    kind: str
    matched: str


def find_internal_vocabulary(text: str) -> tuple[VocabularyHit, ...]:
    """Return every internal-vocabulary hit in *text* (empty if clean).

    Used both by the AC.SR-RECOVER.2 test and (defensively) by the
    renderer's own self-check before it returns text to a user.
    """
    hits: list[VocabularyHit] = []
    for kind, patt in _INTERNAL_VOCAB_PATTERNS:
        for m in patt.finditer(text):
            hits.append(VocabularyHit(kind=kind, matched=m.group(0)))
    return tuple(hits)


def contains_internal_vocabulary(text: str) -> bool:
    """True iff *text* carries any forbidden internal vocabulary."""
    return bool(find_internal_vocabulary(text))


class RecoverySurfaceLeak(RuntimeError):
    """A rendered recovery surface leaked internal vocabulary.

    Raised by the renderer's self-check (plan §8 halt-trigger 5):
    AC.SR-RECOVER.2 is a hard invariant, so a render that would leak an
    internal ID/path fails loudly rather than shipping the leak to the
    user.
    """


# ---------------------------------------------------------------------------
# The recovery situations the surface renders. Each maps to a plain-language
# block + a concrete next action (AC.SR-RECOVER.1).
# ---------------------------------------------------------------------------


class RecoverySituation:
    """The situations a render can describe (string constants).

    These are the user-visible outcomes of the watchdog / self-diagnosis,
    NOT internal failure classes — the mapping from an internal finding to
    one of these happens in ``render_recovery``."""

    channel_down = "channel_down"
    work_stuck = "work_stuck"
    claimed_not_done = "claimed_not_done"
    reset_offered = "reset_offered"
    all_clear = "all_clear"


_SITUATION_BLOCKS: dict[str, tuple[str, str]] = {
    # (headline, next-action) — both plain-language, both actionable.
    RecoverySituation.channel_down: (
        "It looks like my messages stopped reaching you for a bit.",
        "You do not need to do anything — I have switched to another way to "
        "reach you and I am still working. If you stop hearing from me again, "
        "close this and open it fresh, and I will pick right back up.",
    ),
    RecoverySituation.work_stuck: (
        "The work I was doing seems to have gone quiet and may be stuck.",
        "Try sending me a short message like \"are you still going?\" — that "
        "wakes me up to check. If it stays quiet, close this and open it "
        "again; nothing you have saved will be lost.",
    ),
    RecoverySituation.claimed_not_done: (
        "I told you something was done, but when I double-checked, it was not "
        "actually finished.",
        "I am sorry about that. I have flagged it and will redo it now. You "
        "do not need to do anything.",
    ),
    RecoverySituation.reset_offered: (
        "Things are tangled enough that the cleanest fix is to start your "
        "saved settings fresh.",
        "I will make a complete backup first, so nothing is lost, and only "
        "then start fresh. Just reply \"yes, start fresh\" and I will do it. "
        "If you would rather not, reply \"no\" and I will keep trying gently.",
    ),
    RecoverySituation.all_clear: (
        "I checked, and everything is actually working fine on my end.",
        "You do not need to do anything — carry on, and I will keep going.",
    ),
}


@dataclass(frozen=True)
class RecoveryMessage:
    """A rendered recovery surface — headline + next action, both plain."""

    situation: str
    headline: str
    next_action: str

    @property
    def text(self) -> str:
        return f"{self.headline}\n\n{self.next_action}"


def render_recovery(situation: str) -> RecoveryMessage:
    """Render the plain-language recovery surface for *situation*.

    Guarantees AC.SR-RECOVER.1 (plain-language + actionable: every block
    carries a concrete next step) and AC.SR-RECOVER.2 (the rendered text
    is self-checked for internal vocabulary; a leak raises
    ``RecoverySurfaceLeak`` rather than shipping to the user).
    """
    if situation not in _SITUATION_BLOCKS:
        raise ValueError(f"unknown recovery situation: {situation!r}")
    headline, next_action = _SITUATION_BLOCKS[situation]
    message = RecoveryMessage(
        situation=situation, headline=headline, next_action=next_action
    )
    # Self-check: the hard invariant (plan §8).
    if contains_internal_vocabulary(message.text):
        hits = find_internal_vocabulary(message.text)
        raise RecoverySurfaceLeak(
            f"recovery surface for {situation!r} leaked internal vocabulary: "
            f"{[h.matched for h in hits]}"
        )
    return message

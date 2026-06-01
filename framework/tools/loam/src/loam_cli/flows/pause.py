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

"""PAUSE-IF-LOST made structural (AC.PAUSE.* — D4).

The pause-if-lost rule is the single most load-bearing behaviour in the
defined-workflow system: *if you cannot say where you are in the flow,
PAUSE and re-establish position before proceeding.* This module makes it
a positive-resolution gate rather than prose (plan §1 piece 3; D4).

The gate is POSITIVE-resolution (D4 — the safe-by-default posture the
owner law demands): the check passes ONLY when the cursor resolves to a
DEFINITE one-sentence restatement ("step N of flow X, branch B"). The
inability to fill that sentence is the pause condition. This makes
"lost" the DEFAULT until position is positively re-established — an
empty / corrupt / ambiguous / stale cursor defaults to PAUSE, never to
"probably fine."

ACs proven here (method = builder's call per ODD §1.1):

  - **AC.PAUSE.1** — at a context-loss point, a RESOLVED cursor
    surfaces the position (flow + step + the follow-it / pause-if-lost
    directive) into context.
  - **AC.PAUSE.2** — at a context-loss point OR before a consequential
    action, an UNRESOLVED cursor (missing / stale / non-existent step)
    yields a PAUSE signal — "re-establish position before proceeding" —
    not a silent continue.
  - **AC.PAUSE.3** — positive-resolution: the check passes ONLY on a
    one-sentence restatement; absence of a positive resolution defaults
    to PAUSE. The lost state is the default.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

from loam_cli.flows.cursor import CursorResolution

# The follow-it / pause-if-lost directive text (the doctrine commitment,
# loam-doctrine.md 245-250). Carried into context alongside a resolved
# position (AC.PAUSE.1) so the agent always sees BOTH where it is AND the
# rule that governs losing its place.
FOLLOW_DIRECTIVE = (
    "Follow the defined workflow. If you lose your place — if you "
    "cannot say which step of which flow you are on — PAUSE all other "
    "work and re-establish position before proceeding."
)

# The PAUSE directive emitted when position is UNRESOLVED (AC.PAUSE.2).
PAUSE_DIRECTIVE = (
    "PAUSE — re-establish position before proceeding. Your position in "
    "the active flow is UNRESOLVED: you cannot currently say which step "
    "of which flow you are on. Do NOT continue other work and do NOT "
    "take a consequential action until you have re-established a "
    "definite position (re-run EXAMINE against git refs + live state, "
    "then write the cursor). The lost state is the default; positive "
    "resolution is required to clear it."
)


@dataclass(frozen=True)
class PauseDecision:
    """The outcome of a position check.

    ``paused`` is True when position is UNRESOLVED (the pause condition
    fired). ``directive`` is the text to surface into context — the
    position block + FOLLOW_DIRECTIVE on a resolved cursor (AC.PAUSE.1),
    or PAUSE_DIRECTIVE on an unresolved one (AC.PAUSE.2). ``one_sentence``
    is the positive-resolution restatement (empty when paused).
    """

    paused: bool
    directive: str
    one_sentence: str = ""
    reason: str = ""


def position_check(resolution: CursorResolution) -> PauseDecision:
    """Run the positive-resolution pause gate over a CursorResolution.

    AC.PAUSE.3 — the gate passes (not paused) ONLY when ``resolution``
    is RESOLVED to a one-sentence restatement. Any unresolved input
    (the default) yields the PAUSE decision. There is no "probably
    fine" branch.
    """
    if resolution.resolved and resolution.one_sentence():
        sentence = resolution.one_sentence()
        directive = (
            f"POSITION: {sentence}.\n{FOLLOW_DIRECTIVE}"
        )
        return PauseDecision(
            paused=False,
            directive=directive,
            one_sentence=sentence,
            reason="",
        )
    # AC.PAUSE.2 / AC.PAUSE.3 — unresolved (the default) => PAUSE.
    reason = resolution.reason or "position could not be resolved"
    directive = f"{PAUSE_DIRECTIVE}\nReason: {reason}."
    return PauseDecision(
        paused=True,
        directive=directive,
        one_sentence="",
        reason=reason,
    )

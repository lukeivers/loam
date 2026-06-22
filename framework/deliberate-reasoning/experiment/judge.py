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

"""The blind judge (plan §3.3 / AC.MGRL.5; PRE_REGISTRATION §4).

The judge scores an answer against the canonical answer via the FIXED
normalizer from PRE_REGISTRATION §2. It is **blind to the hypothesis and to
the arm** by construction: :func:`score_answer`'s signature accepts only
``(prompt, answer, canonical_answer)`` — there is NO parameter through which
the arm label (baseline vs escalated), the trigger, or any hypothesis
framing could enter. Blindness is therefore total and structurally
enforced, not a discipline the caller must remember.
"""

from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """The FIXED normalizer (PRE_REGISTRATION §2): trim + lowercase +
    collapse internal whitespace. Frozen by the pre-registration."""

    return _WS_RE.sub(" ", text.strip().lower())


def score_answer(prompt: str, answer: str, canonical_answer: str) -> int:
    """Score one answer: 1 iff it matches the canonical answer under the
    fixed normalizer, else 0.

    The signature deliberately excludes any arm/hypothesis label — the
    judge cannot tell which experimental arm produced ``answer`` (AC.MGRL.5,
    PRE_REGISTRATION §4). ``prompt`` is accepted for protocol symmetry
    (the judge sees what the arm saw) but does not influence the exact-match
    score.
    """

    return 1 if normalize(answer) == normalize(canonical_answer) else 0

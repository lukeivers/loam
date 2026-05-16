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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PBF.3 — the jargon guard is deterministic and does not trip on
ordinary words.

Plan: pos3 phase-b-fix-plan-2026-05-16.md §4 AC.PBF.3
Evidence base: phase-b-hardening-2026-05-16.md "The process crash" —
the AC.B.3 guard's naive substring `"ac." in text.lower()` matched the
ordinary word "Mac." and uncaught-ValueError'd the WHOLE intake
non-deterministically (whether it crashed depended on whether the
model happened to end a sentence with "Mac.").

Outcome under test (not method): ordinary words that merely *contain*
a forbidden substring do NOT raise; genuine jargon tokens still do;
behaviour is deterministic (same plain "done" always raises or never
raises, independent of incidental phrasing). Satisfiable by
word-boundary regex / tokenize+match / curated anchored patterns —
multiple methods; the AC constrains the observable, not the technique.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop.intake import assert_plain_language  # noqa: E402


# The exact hardening-report crash cases + the broader ordinary-word
# class they generalise to (any benign word containing a forbidden
# substring: "Mac." -> "ac.", "odd" -> "ODD", "revealed"/"seal the
# envelope" -> "seal").
BENIGN = [
    "Back up to your Mac.",                       # hardening exact
    "Sign into iCloud on your Mac.",              # hardening exact
    "save it to your Mac and done",               # hardening exact
    "Every photo on your phone and laptop is automatically "
    "backed up to iCloud.",
    "It is a bit odd but it works the way you expect.",
    "The deal is revealed when you tap the card.",
    "You can seal the envelope and mail it.",
    "Seal the deal with a handshake.",
    "The jar seals tightly so your food stays fresh.",
    "Your recipes are saved and you can search them later.",
    "It reads your file and tells you the totals.",
    "You get one clear sentence telling you who owes whom.",
]

# Genuine jargon tokens the guard MUST still refuse (AC.B.3 preserved).
JARGON = [
    "Done when AC.B.4 passes and pytest exit code is 0",
    "Done when the manifest is sealed",
    "Check the sha256 and run pytest",
    "This satisfies the acceptance criterion",
    "The acceptance criteria are machine-checkable",
    "The ODD methodology requires it",
    "Run pytest and seal the amendment",
    "Seal the manifest after the build",
    "The component seal must pass before publish",
]


@pytest.mark.parametrize("text", BENIGN)
def test_AC_PBF_3_ordinary_words_do_not_trip(text: str) -> None:
    """No benign plain-English 'done' may raise — the non-deterministic
    crash on 'Mac.' (and the same defect class for 'odd'/'seal') is
    closed."""
    assert_plain_language(text)  # must NOT raise


@pytest.mark.parametrize("text", JARGON)
def test_AC_PBF_3_genuine_jargon_still_refused(text: str) -> None:
    """The guard still fires on real jargon tokens — the fix tightens
    matching, it does not loosen the AC.B.3 protection."""
    with pytest.raises(ValueError):
        assert_plain_language(text)


@pytest.mark.parametrize("text", BENIGN + JARGON)
def test_AC_PBF_3_deterministic_repeated_calls(text: str) -> None:
    """Deterministic: the same text yields the same outcome on every
    call (the hardening defect was a phrasing-dependent crash; the fix
    must be phrasing-independent and stable)."""
    def outcome(t: str) -> bool:
        try:
            assert_plain_language(t)
            return False
        except ValueError:
            return True

    first = outcome(text)
    for _ in range(5):
        assert outcome(text) == first

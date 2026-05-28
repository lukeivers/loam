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

"""AC.KP9.1 — Layer 1 deterministic jargon / abstraction-voice lint.

A draft containing a file path, a ``.md`` / source file name, an AC-ID,
a commit SHA, a §-doc pointer, a loam-process jargon token, an internal
mechanism token, or an un-introduced ALLCAPS token is BLOCKED before
send. A clean plain-language draft PASSES.

Method is the builder's call (ODD §1.1): the leak classes are exercised
one per case (parametrized), the clean drafts assert no false positive,
and the AC.PBF.3 token-boundary discipline (ordinary words containing a
forbidden substring do NOT trip) is asserted as a regression guard.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from draft_gate import Verdict, gate, layer1_lint  # noqa: E402


# Each leak class → at least one block-worthy draft.
_LEAK_DRAFTS = [
    ("file-path", "The fix is in framework/primary-persona/src/retrieval.py for you."),
    ("abs-path", "Your status is at /Users/lukeivers/loam/status here."),
    ("file-name", "I updated OBJECTIVES.md with the two objectives."),
    ("ac-id", "AC.KP9.1 passed so you're good."),
    ("commit-sha", "It landed at seal a5946f304c0d1fb34549928cb74eec71a7faa5bb today."),
    ("doc-section-pointer", "See §14 of the roadmap for the rest."),
    ("manifest", "I wrote the manifest and ran it for you."),
    ("internal-mechanism", "The BM25 score put it at the top."),
    ("internal-abbrev", "This is an F4 scope call."),
    ("un-introduced-allcaps", "I promoted it via the ARCPROMO path."),
]


@pytest.mark.parametrize("label,draft", _LEAK_DRAFTS)
def test_AC_KP9_1_each_leak_class_blocks(label: str, draft: str) -> None:
    """Each Layer 1 leak class blocks the draft before send."""
    result = gate(draft)
    assert result.blocked(), f"{label!r} draft should BLOCK: {draft!r}"
    assert result.verdict == Verdict.BLOCK
    assert result.reasons, "a blocked draft must carry model-facing reasons"


# Clean plain-language drafts — NO false positive.
_CLEAN_DRAFTS = [
    "I added work-anchored recall so the right context surfaces against your live work.",
    "Done — your fiction batch is queued and I'll keep your canon close at hand.",
    "Yes, that's working now. Want me to keep going on the next chapter?",
    # AC.PBF.3 token-boundary guard: ordinary words containing a
    # forbidden substring must NOT trip.
    "I sealed the envelope and revealed the odd result on my Mac.",
    "That's an odd outcome, but the deal is sealed.",
]


@pytest.mark.parametrize("draft", _CLEAN_DRAFTS)
def test_AC_KP9_1_clean_drafts_pass(draft: str) -> None:
    """A clean plain-language draft passes Layer 1 (no false positive)."""
    result = gate(draft)
    assert result.passed(), (
        f"clean draft should PASS but got {result.verdict} "
        f"with reasons {[r.label for r in result.reasons]}: {draft!r}"
    )


def test_AC_KP9_1_layer1_lint_returns_one_reason_per_class() -> None:
    """A draft carrying two distinct leak classes yields >=2 reasons."""
    reasons = layer1_lint("See §3 and AC.KP9.1 for the answer.")
    labels = {r.label for r in reasons}
    assert "doc-section-pointer" in labels
    assert "ac-id" in labels


def test_AC_KP9_1_deterministic_repeated_calls() -> None:
    """Same draft → same verdict every time (deterministic)."""
    draft = "The fix is in retrieval.py."
    verdicts = {gate(draft).verdict for _ in range(5)}
    assert verdicts == {Verdict.BLOCK}

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

"""AC.CLG.3 — precision / no alarm fatigue: a work-state claim the
ground truth CONFIRMS passes with no steer, and non-claim prose passes
with no steer — demonstrated against a corpus of true-claim +
ordinary-prose drafts.
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

from claim_guard import check_claims, detect_work_state_claims  # noqa: E402

_SEALED_MATCH = {
    "project": "loam",
    "slug": "widget-pipeline-revamp",
    "title": "widget pipeline revamp",
    "build_state": "sealed",
    "seal_evidence": ("def5678 chore(seals): widget-pipeline-revamp — x",),
    "in_sealed_archive": True,
}

_PARTIAL_MATCH = {
    "project": "loam",
    "slug": "widget-pipeline-revamp",
    "title": "widget pipeline revamp",
    "build_state": "partially-sealed",
    "seal_evidence": ("abc1234 chore(amend): widget-pipeline-revamp …",),
    "in_sealed_archive": False,
}

_PENDING_MATCH = {
    "project": "loam",
    "slug": "widget-pipeline-revamp",
    "title": "widget pipeline revamp",
    "build_state": "no-build-evidence",
    "seal_evidence": (),
    "in_sealed_archive": False,
}


def _ground_truth_with(matches: list[dict]) -> dict:
    return {
        "matches": matches,
        "searched": ("loam plan-docs + git subjects",),
        "unsearched": ("scratch artefacts",),
    }


# True-claim corpus: each (draft, the ground truth that CONFIRMS it).
_TRUE_CLAIMS = (
    ("The widget pipeline revamp is sealed.", [_SEALED_MATCH]),
    ("The widget pipeline revamp has been shipped.", [_SEALED_MATCH]),
    ("Yes — the widget pipeline revamp is planned.", [_PENDING_MATCH]),
    ("The widget pipeline revamp was built last week.", [_PARTIAL_MATCH]),
    ("The widget pipeline revamp isn't built yet.", [_PENDING_MATCH]),
)


@pytest.mark.parametrize("draft, matches", _TRUE_CLAIMS)
def test_AC_CLG_3_confirmed_claims_pass_clean(
    draft: str, matches: list[dict]
) -> None:
    assert check_claims(draft, query=lambda t: _ground_truth_with(matches)) == [], (
        f"a ground-truth-confirmed claim must pass un-steered: {draft!r}"
    )


# Ordinary-prose corpus: no work-state assertion shape at all — the
# detector itself must stay silent (and therefore no query runs).
_ORDINARY_PROSE = (
    "Here's the summary you asked for — three options, ranked.",
    "Dinner at seven works; the reservation is under your name.",
    "The test suite finished and everything looks healthy.",
    "I'd lean toward the second option; it keeps the long-term path open.",
    "That movie was better than I expected, honestly.",
    "The bridge was built in 1937 and still carries traffic today.",
    "Rome wasn't built in a day.",
)


@pytest.mark.parametrize("draft", _ORDINARY_PROSE)
def test_AC_CLG_3_ordinary_prose_never_queries_never_steers(
    draft: str,
) -> None:
    calls: list[str] = []

    def _counting_query(topic: str) -> dict:
        calls.append(topic)
        return _ground_truth_with([])

    steers = check_claims(draft, query=_counting_query)
    # Prose ABOUT building (a bridge, Rome) may legitimately detect a
    # claim shape; the precision contract is NO STEER. For prose with
    # no claim shape at all, additionally no query may run.
    assert steers == [], f"ordinary prose must never steer: {draft!r}"
    if not detect_work_state_claims(draft):
        assert calls == []

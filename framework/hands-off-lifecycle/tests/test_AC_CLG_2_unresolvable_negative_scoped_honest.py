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

"""AC.CLG.2 — a negative EXISTENCE claim whose subject the guard
cannot resolve against any ground-truth source yields a steer
prompting the scoped-honest form ("not found in <searched surfaces>;
<unsearched> unchecked") rather than a silent pass — the
eternal-negative shape specifically; ordinary unresolvable prose is
not steered.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from claim_guard import check_claims  # noqa: E402

_EMPTY_SCOPED = {
    "matches": [],
    "searched": (
        "loam plan-docs (docs/plans incl. sealed archive) + git "
        "apply/seal commit subjects",
    ),
    "unsearched": ("scratch/research artefacts", "chat/session history"),
}


def test_AC_CLG_2_unresolvable_flat_negative_gets_warning_light() -> None:
    """'X isn't planned' with NOTHING on file → a steer prompting the
    scoped-honest form, naming searched + unsearched surfaces."""
    draft = "The quantum gravy separator isn't planned anywhere."
    steers = check_claims(draft, query=lambda t: dict(_EMPTY_SCOPED))
    assert len(steers) == 1
    s = steers[0]
    assert s.label == "unverified-flat-negative"
    assert "plan-docs" in s.detail, "the steer names what WAS searched"
    assert "scratch" in s.detail, "the steer names what was NOT checked"
    assert "isn't planned" in s.detail


def test_AC_CLG_2_doesnt_exist_shape_also_steered() -> None:
    """'no plan for X exists' / 'X doesn't exist' are the same poison
    shape."""
    for draft in (
        "There is no plan for the gravy separator.",
        "The gravy separator project doesn't exist.",
    ):
        steers = check_claims(draft, query=lambda t: dict(_EMPTY_SCOPED))
        assert steers, f"the eternal-negative must be steered: {draft!r}"
        assert steers[0].label == "unverified-flat-negative"


def test_AC_CLG_2_ordinary_unresolvable_prose_not_steered() -> None:
    """Ordinary prose — including ordinary negatives that are NOT
    work-state existence claims — is not steered (no claim detected,
    no query ever runs)."""
    calls: list[str] = []

    def _counting_query(topic: str) -> dict:
        calls.append(topic)
        return dict(_EMPTY_SCOPED)

    for draft in (
        "The weather today isn't great, maybe tomorrow.",
        "I don't think we should order from there again.",
        "No plan survives contact with the enemy, as they say.",
        "She wasn't ready to leave the party yet.",
    ):
        assert check_claims(draft, query=_counting_query) == [], (
            f"ordinary prose must pass clean: {draft!r}"
        )
    assert calls == [], (
        "no ground-truth query may run for prose with no detected claim "
        f"(the hot-path latency contract); ran for: {calls}"
    )


def test_AC_CLG_2_unverifiable_build_negative_is_not_the_poison_shape() -> None:
    """A negative about BUILD progress ('isn't built yet') on an
    unresolvable subject is not the eternal-negative existence shape —
    no steer (precision; the existence class is the named target)."""
    draft = "The gravy separator isn't built yet."
    assert check_claims(draft, query=lambda t: dict(_EMPTY_SCOPED)) == []

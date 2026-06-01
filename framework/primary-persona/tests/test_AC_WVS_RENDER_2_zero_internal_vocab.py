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

"""AC.WVS-RENDER.2 — the rendered surface carries ZERO internal
vocabulary (no stack traces, AC-IDs, commit SHAs, file paths,
agent-IDs, slugs, or ODD/methodology vocabulary), verified by the
existing ``contains_internal_vocabulary`` probe. A render that cannot
avoid leaking an internal token is a HALT, not best-effort.

Plan: docs/plans/work-visibility-surface.md §5 / §8 halt #2.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.work_visibility import (
    HEALTH_OK,
    HEALTH_STUCK,
    HEALTH_UNKNOWN,
    WorkSnapshot,
    WorkVisibilityLeak,
    render_surface,
)
from loam.self_correction.recovery_surface import contains_internal_vocabulary


@pytest.mark.parametrize(
    "snapshot",
    [
        WorkSnapshot(running_now=3, queued=2, owner_pending=1, health=HEALTH_OK),
        WorkSnapshot(running_now=1, health=HEALTH_STUCK),
        WorkSnapshot(health=HEALTH_UNKNOWN, health_unknown=True),
        WorkSnapshot(work_unknown=True),
        WorkSnapshot(owner_pending=5, health=HEALTH_OK),
        WorkSnapshot(health=HEALTH_OK),  # all-clear
    ],
)
def test_AC_WVS_RENDER_2_no_internal_vocabulary(snapshot: WorkSnapshot) -> None:
    """Across every snapshot shape the rendered surface carries NO
    internal vocabulary per the sealed probe."""
    text = render_surface(snapshot)
    assert not contains_internal_vocabulary(text), (
        f"AC.WVS-RENDER.2 — rendered surface leaked internal vocab: {text!r}"
    )


def test_AC_WVS_RENDER_2_position_with_internal_token_is_dropped() -> None:
    """A position phrase whose underlying state carries an internal
    token (a SHA-named flow, a path) is DROPPED from the render — the
    surface never ships it (the probe finds nothing)."""
    # A cursor one-sentence that smuggles a file-path-ish token.
    leaky_phrase = "step build of flow framework/self_correction/watchdog.py, branch x"
    assert contains_internal_vocabulary(leaky_phrase), (
        "fixture sanity — the leaky phrase must trip the probe"
    )
    snapshot = WorkSnapshot(
        running_now=1,
        position_known=True,
        position_phrase=leaky_phrase,
        health=HEALTH_OK,
    )
    text = render_surface(snapshot)
    # The leaky position line is dropped; the surface stays clean.
    assert not contains_internal_vocabulary(text)
    assert "watchdog.py" not in text


def test_AC_WVS_RENDER_2_leak_in_fixed_text_would_halt() -> None:
    """The HARD invariant: if the rendered text DID carry an internal
    token, the renderer raises WorkVisibilityLeak rather than shipping
    it (plan §8 halt #2). Proven by feeding render_surface's own probe
    a known-leaky string through a monkeypatched now-line."""
    import loam.primary_persona.work_visibility as wv

    original = wv._render_now_line
    try:
        wv._render_now_line = lambda s: "Right now: see commit deadbeef1234567."
        with pytest.raises(WorkVisibilityLeak):
            render_surface(WorkSnapshot(health=HEALTH_OK))
    finally:
        wv._render_now_line = original

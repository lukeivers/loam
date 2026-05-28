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

"""AC.KP7.2 — survives one compaction via UserPromptSubmit re-assert
(the #15174 mitigation).

A SessionStart-injected surface can be evaporated by a compaction (the
Claude-Code #15174 SessionStart-compact bug). KP0.3's recorded probe
confirmed the UserPromptSubmit re-assert route reaches the model; KP7
re-emits the SAME plain-language surface via
``reassert_surface_for_user_prompt_submit`` so the first
UserPromptSubmit after a compaction restores it.

Verifies the re-assert produces the IDENTICAL gated surface as the
SessionStart step (a compaction must restore the same state, not a
different one), and that it is silent when there is nothing to surface.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCH_SCRIPTS = REPO_ROOT / "framework" / "orchestrator" / "scripts"
KP9_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
for _p in (str(ORCH_SCRIPTS), str(KP9_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from session_surface import (  # noqa: E402
    build_session_surface,
    reassert_surface_for_user_prompt_submit,
)


class _Obj:
    def __init__(self, objective, subgoals, active=True):
        self.objective = objective
        self.subgoals = subgoals
        self._active = active

    def is_active(self):
        return self._active


_OBJS = [
    _Obj(
        "Produce the LitRPG series. A revenue path via self-publishing.",
        ["book-1-batch-production", "canon-consistency-across-the-series"],
    )
]


def test_reassert_restores_identical_surface() -> None:
    # The SessionStart surface (what a compaction may evaporate).
    session_start = build_session_surface(objectives=_OBJS)
    assert session_start, "expected a SessionStart surface to begin with"

    # Simulate a compaction: the surface is gone from context. The first
    # UserPromptSubmit re-asserts it via the confirmed-live route.
    reasserted = reassert_surface_for_user_prompt_submit(objectives=_OBJS)

    # The re-assert restores the SAME plain-language state (not a
    # different one) — this is the #15174 mitigation property.
    assert reasserted == session_start
    assert reasserted, "the re-assert must restore a non-empty surface"


def test_reassert_silent_when_nothing_to_surface() -> None:
    # No active objective → the re-assert is silent (no phantom surface
    # injected on every prompt).
    assert reassert_surface_for_user_prompt_submit(objectives=[]) == ""


def test_reassert_surface_is_lint_clean() -> None:
    # The re-asserted surface routes through the SAME gate, so it carries
    # no leak (the #15174 route must not be a leak backdoor).
    from draft_gate import layer1_lint

    reasserted = reassert_surface_for_user_prompt_submit(objectives=_OBJS)
    assert reasserted
    assert layer1_lint(reasserted) == []

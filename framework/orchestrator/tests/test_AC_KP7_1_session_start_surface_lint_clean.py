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

"""AC.KP7.1 — session opens with a plain-language last-state surface,
routed through KP9's gate (passes the lint).

keep-pace MVP Cycle 4 (KP7). Verifies the SessionStart surface:
  - is present (non-empty) when there is an active objective;
  - reads as "last session you were on X; next likely Y" (active
    objective + likely-next-action);
  - passes the KP9 Layer 1 lint (no file-names / paths / IDs /
    internal-mechanism tokens leak — the surface is ROUTED THROUGH the
    gate, AC.KP7.1);
  - is silent (empty) when there is no active objective (no noise).
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

from session_surface import build_session_surface  # noqa: E402


class _Obj:
    """Minimal Objective-shaped stub (duck-typed: objective / subgoals /
    is_active) so the surface builder can be exercised with no
    pre-arranged live state."""

    def __init__(self, objective, subgoals, active=True):
        self.objective = objective
        self.subgoals = subgoals
        self._active = active

    def is_active(self):
        return self._active


def test_surface_present_with_active_objective() -> None:
    objs = [
        _Obj(
            "Produce the LitRPG series. A revenue path via self-publishing.",
            ["book-1-batch-production", "canon-consistency-across-the-series"],
        )
    ]
    surface = build_session_surface(objectives=objs)
    assert surface, "expected a non-empty last-state surface for an active objective"
    # Plain-language "next likely" clause present (de-slugged subgoal).
    assert "next likely" in surface.lower()
    assert "canon consistency across the series" in surface.lower()


def test_surface_passes_kp9_layer1_lint() -> None:
    # The live draft-gate is the SAME gate KP9 ships; route the real
    # surface through layer1_lint directly to prove no leak class fires.
    from draft_gate import layer1_lint  # imported here to keep top clean

    objs = [
        _Obj(
            "Build durable financial independence. Convert active income "
            "into passive assets.",
            ["fiction-catalog-as-in-motion-passive-asset"],
        )
    ]
    surface = build_session_surface(objectives=objs)
    assert surface
    leaks = layer1_lint(surface)
    assert leaks == [], f"surface leaked jargon/mechanism tokens: {leaks}"


def test_surface_silent_when_no_active_objective() -> None:
    # No objectives → empty surface (silent, no noise).
    assert build_session_surface(objectives=[]) == ""
    # An inactive-only set → empty surface.
    inactive = [_Obj("dormant work", ["x"], active=False)]
    assert build_session_surface(objectives=inactive) == ""


def test_surface_suppressed_when_it_would_leak() -> None:
    # A surface that WOULD carry a mechanism leak is suppressed by the
    # gate (BLOCK → "") rather than shown — the gate route is what
    # guarantees AC.KP7.1's no-leak property even on a bad objective.
    leaky = [
        _Obj(
            "see framework/primary-persona/src/retrieval.py for the BM25 index",
            ["x"],
        )
    ]
    surface = build_session_surface(objectives=leaky)
    assert surface == "", "a leaking surface must be suppressed by the gate, not shown"

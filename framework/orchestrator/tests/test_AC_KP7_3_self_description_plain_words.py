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

"""AC.KP7.3 — self-description uses plain words (no internal jargon;
composes with AC.KP9.1).

When the surface describes the memory system's OWN behaviour, it must
use plain words ("keeping your fiction work close at hand"), never
internal terms ("ARC-promoted", "w_s", "objective-match", "BM25",
"FTS5", "additionalContext"). The internal-mechanism leak class is one
of the KP9 Layer 1 patterns; this test asserts the surface — including
any self-describing phrasing — carries none of those tokens, and
verifies the gate route blocks one if it ever crept in.
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

# The internal-mechanism tokens AC.KP7.3 names — none may appear in the
# user-facing surface.
_FORBIDDEN_INTERNAL_TOKENS = (
    "ARC-promoted",
    "w_s",
    "objective-match",
    "BM25",
    "FTS5",
    "additionalContext",
    "additional_context",
)


class _Obj:
    def __init__(self, objective, subgoals, active=True):
        self.objective = objective
        self.subgoals = subgoals
        self._active = active

    def is_active(self):
        return self._active


def test_surface_carries_no_internal_mechanism_token() -> None:
    objs = [
        _Obj(
            "Produce the LitRPG series. A revenue path via self-publishing.",
            ["canon-consistency-across-the-series"],
        ),
        _Obj(
            "Build durable financial independence.",
            ["ai-operated-acquired-assets"],
        ),
    ]
    surface = build_session_surface(objectives=objs)
    assert surface
    low = surface.lower()
    for tok in _FORBIDDEN_INTERNAL_TOKENS:
        assert tok.lower() not in low, f"internal token leaked into surface: {tok}"


def test_gate_blocks_a_self_description_that_names_a_mechanism() -> None:
    # If a self-description ever named a mechanism token, the gate route
    # blocks it (BLOCK → suppressed). This proves the structural
    # guarantee, not just the seeded-objective happy path.
    leaky = [_Obj("I keep your work close using the BM25 index", ["x"])]
    assert build_session_surface(objectives=leaky) == ""

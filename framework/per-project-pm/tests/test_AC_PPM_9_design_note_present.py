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

"""AC.PPM.9 — design-note articulates PM/M-FBM boundary.

Per parent plan §5 + cycle-2 plan §4 Surface #9:
docs/design.md exists; body covers 8 sections:
  1. Purpose
  2. PM/M-FBM boundary
  3. Workspace-state directory shape
  4. Lifecycle
  5. Per-workspace, not session-bound
  6. Composition surfaces (advisory at Cycle 2)
  7. Communication shape (translation rule applied bidirectionally)
  8. Out of scope at Cycle 2 (deferred to Cycle 4)
"""

from __future__ import annotations

from pathlib import Path


COMPONENT_ROOT = Path(__file__).resolve().parent.parent
DESIGN_DOC = COMPONENT_ROOT / "docs" / "design.md"


def test_design_doc_exists() -> None:
    assert DESIGN_DOC.exists(), f"missing {DESIGN_DOC}"


def test_design_doc_covers_required_sections() -> None:
    body = DESIGN_DOC.read_text(encoding="utf-8").lower()
    # Each section header tested; matches both "## 1. Purpose" and any
    # variation with the section name.
    required_phrases = [
        "purpose",
        "pm/m-fbm boundary",
        "workspace-state",
        "lifecycle",
        "per-workspace",
        "composition surfaces",
        "communication shape",
        "out of scope",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in body]
    assert missing == [], (
        f"design.md missing required section phrases: {missing}"
    )


def test_design_doc_names_pm_m_fbm_boundary_explicitly() -> None:
    """The boundary articulation is the load-bearing claim of AC.PPM.9.
    Per cycle-2 plan §4 Surface #1 + §9 design.md §2."""
    body = DESIGN_DOC.read_text(encoding="utf-8").lower()
    # PM owns project-domain decision state; M-FBM owns episode memory.
    assert "decision" in body, (
        "design.md must articulate that PM owns project-domain decision state"
    )
    assert "episode" in body or "turn" in body, (
        "design.md must articulate that M-FBM owns turn-grain episode memory"
    )
    assert "boundary" in body


def test_design_doc_articulates_lazy_loading() -> None:
    """Per F2.C — lazy resolution must be named in the design-note."""
    body = DESIGN_DOC.read_text(encoding="utf-8").lower()
    assert "lazy" in body, (
        "design.md must articulate lazy on-demand resolution"
    )


def test_design_doc_articulates_composes_with_as_advisory() -> None:
    """Per F2.B — composes_with_* are advisory at Cycle 2."""
    body = DESIGN_DOC.read_text(encoding="utf-8").lower()
    assert "advisory" in body, (
        "design.md must name 'advisory' for composes_with_* fields"
    )


def test_design_doc_lists_cycle_4_deferrals() -> None:
    """Out of scope section must list the Cycle 4 deferred surface
    so readers know what's NOT yet wired."""
    body = DESIGN_DOC.read_text(encoding="utf-8").lower()
    assert "record_response" in body
    assert "cycle 4" in body

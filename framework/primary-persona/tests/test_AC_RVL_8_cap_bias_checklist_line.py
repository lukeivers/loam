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

"""AC.RVL.8 — the plan-review checklist carries the cap-bias line, and the
reviewer gate enforces it; a plan introducing a numeric limit with no named
resource is flagged.

The methodology doc carries the authoring checklist (for delegating personas,
the plan-author leg) AND the catching-violations checklist (for reviewers, the
gate leg). The cap-bias line must be present in BOTH.
"""

from __future__ import annotations

from pathlib import Path

_DOC = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "dev-sdlc"
    / "docs"
    / "odd-methodology.md"
)


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    # Normalize wrapping whitespace so phrase checks are line-break-insensitive.
    return " ".join(text[start:end].split())


def test_AC_RVL_8_plan_author_checklist_carries_the_cap_bias_line() -> None:
    text = _DOC.read_text(encoding="utf-8")
    authoring = _section(
        text, "## 7. Authoring checklist", "## 8. Catching violations"
    )
    assert "numeric limit" in authoring.lower()
    assert "RESOURCE" in authoring
    assert "relevance floor + byte budget" in authoring
    assert "no named resource is a defect" in authoring
    assert "retirement criterion" in authoring


def test_AC_RVL_8_reviewer_gate_enforces_the_cap_bias_line() -> None:
    text = _DOC.read_text(encoding="utf-8")
    reviewer = _section(text, "## 8. Catching violations", "## 9.")
    assert "numeric limit with no named resource" in reviewer
    assert "relevance floor + byte budget" in reviewer
    # The reviewer leg names the same exceptions so it can distinguish a defect
    # from a legitimate signal-less-channel / scaffolding count.
    assert "budget denomination" in reviewer
    assert "retirement criterion" in reviewer

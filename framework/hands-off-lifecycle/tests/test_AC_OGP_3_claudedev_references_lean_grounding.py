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

"""AC.OGP.3 — CLAUDE.dev.md references lean grounding doc as
session-start required reading.

Per v0.2.2 sub-plan-doc §3 AC.OGP.3: the workspace-root CLAUDE.dev.md
"Session-start discipline" bulleted list adds a load-FIRST reference
to ``docs/odd-llm-grounding.lean.md`` with the §self-checks discipline
named.

Static structural assertion: string-match on the file content.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CLAUDE_DEV_PATH = REPO_ROOT / "CLAUDE.dev.md"


def _load_claude_dev() -> str:
    assert CLAUDE_DEV_PATH.is_file(), (
        f"AC.OGP.3: CLAUDE.dev.md must exist at {CLAUDE_DEV_PATH}"
    )
    return CLAUDE_DEV_PATH.read_text(encoding="utf-8")


def test_AC_OGP_3_claudedev_names_lean_grounding_path() -> None:
    """CLAUDE.dev.md mentions docs/odd-llm-grounding.lean.md."""
    text = _load_claude_dev()
    assert "docs/odd-llm-grounding.lean.md" in text, (
        "AC.OGP.3: CLAUDE.dev.md must reference "
        "docs/odd-llm-grounding.lean.md as session-start required "
        "reading."
    )


def test_AC_OGP_3_claudedev_names_load_first_semantics() -> None:
    """CLAUDE.dev.md names the load-FIRST ordering for lean grounding."""
    text = _load_claude_dev().lower()
    assert "load first" in text, (
        "AC.OGP.3: CLAUDE.dev.md must name the 'load FIRST' ordering "
        "for the lean grounding doc."
    )


def test_AC_OGP_3_claudedev_names_self_checks_discipline() -> None:
    """CLAUDE.dev.md names the §self-checks discipline."""
    text = _load_claude_dev()
    assert "self-checks" in text.lower(), (
        "AC.OGP.3: CLAUDE.dev.md must name the §self-checks discipline "
        "(run on every output declared 'objective,' 'AC,' "
        "'constraint,' or 'capability')."
    )


def test_AC_OGP_3_lean_grounding_referenced_before_methodology() -> None:
    """The lean grounding ref appears BEFORE odd-methodology.md.

    Per the plan-doc §7 method-decision register: the lean doc is the
    prime + loads FIRST; the methodology is depth-as-needed. The
    bulleted list ordering reflects that.
    """
    text = _load_claude_dev()
    lean_idx = text.find("docs/odd-llm-grounding.lean.md")
    methodology_idx = text.find("plugins/dev-sdlc/docs/odd-methodology.md")
    assert lean_idx != -1 and methodology_idx != -1
    assert lean_idx < methodology_idx, (
        "AC.OGP.3: lean grounding doc must be referenced BEFORE "
        "odd-methodology.md in CLAUDE.dev.md (load-FIRST ordering)."
    )

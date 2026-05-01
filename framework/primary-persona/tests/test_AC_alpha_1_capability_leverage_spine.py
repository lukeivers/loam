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

"""AC.α.1 — Capability leverage spine + Lean on the corpus rule
present in prompt.md template.

Per plan
``docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs.md``
§4 AC.α.1, the framework template
``framework/primary-persona/templates/persona-template/prompt.md``
carries:

  - a new top-level named section **Capability leverage spine**
    containing two sub-blocks:
      * a *Leverage rule* sub-section (the declarative rule the
        persona runs on every plan that takes action — naming
        both Claude-Code-leverage and harness-leverage halves);
      * a *Capability index* sub-section (one-line entries
        pointing at corpus-doc paths under
        ``docs/rebuild/capability-corpus/``; ≥ 8 entries; ≤ 1500
        chars total for the index block).
  - a new operational-rule entry **Lean on the corpus** under
    the existing ``## Operational rules`` section (sibling to
    L's six rules).
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_PROMPT_MD = (
    REPO_ROOT
    / "framework" / "primary-persona"
    / "templates"
    / "persona-template"
    / "prompt.md"
)


def _body() -> str:
    return TEMPLATE_PROMPT_MD.read_text()


def test_AC_alpha_1_capability_leverage_spine_section_marker_present():
    """The top-level ``## Capability leverage spine`` heading exists."""
    body = _body()
    assert "## Capability leverage spine" in body, (
        "Capability leverage spine section heading missing from prompt.md"
    )


def test_AC_alpha_1_leverage_rule_sub_marker_present():
    """A *Leverage rule* sub-block sits inside the Capability
    leverage spine section."""
    body = _body()
    spine_idx = body.index("## Capability leverage spine")
    next_top_idx = body.find("\n## ", spine_idx + 5)
    assert next_top_idx > 0, "no top-level section follows the spine"
    spine_section = body[spine_idx:next_top_idx]
    assert "### Leverage rule" in spine_section, (
        "Leverage rule sub-marker missing from spine section"
    )


def test_AC_alpha_1_capability_index_sub_marker_present():
    """A *Capability index* sub-block sits inside the Capability
    leverage spine section."""
    body = _body()
    spine_idx = body.index("## Capability leverage spine")
    next_top_idx = body.find("\n## ", spine_idx + 5)
    assert next_top_idx > 0
    spine_section = body[spine_idx:next_top_idx]
    assert "### Capability index" in spine_section, (
        "Capability index sub-marker missing from spine section"
    )


def test_AC_alpha_1_leverage_rule_names_both_halves():
    """The leverage rule paragraph names both the Claude-Code
    half and the harness half of the rule (per CLAUDE.md Lens 1)."""
    body = _body()
    rule_idx = body.index("### Leverage rule")
    next_idx = body.find("\n### ", rule_idx + 5)
    assert next_idx > 0
    rule_section = body[rule_idx:next_idx].lower()
    # Both halves named.
    assert "claude code" in rule_section, (
        "leverage rule must name the Claude-Code-leverage half"
    )
    assert "harness" in rule_section, (
        "leverage rule must name the harness-leverage half"
    )


def test_AC_alpha_1_capability_index_has_at_least_eight_corpus_path_entries():
    """The capability index carries ≥ 8 one-line entries pointing at
    corpus-doc paths under ``docs/rebuild/capability-corpus/``."""
    body = _body()
    index_idx = body.index("### Capability index")
    next_idx = body.find("\n## ", index_idx + 5)
    assert next_idx > 0
    index_section = body[index_idx:next_idx]
    # Match path entries to corpus docs (any class).
    pattern = re.compile(r"docs/rebuild/capability-corpus/\S+\.md")
    matches = pattern.findall(index_section)
    assert len(matches) >= 8, (
        f"capability index must carry ≥ 8 corpus-doc path entries; "
        f"found {len(matches)}: {matches}"
    )


def test_AC_alpha_1_capability_index_is_under_1500_chars():
    """The capability index sub-block is ≤ 1500 chars (spine budget)."""
    body = _body()
    index_idx = body.index("### Capability index")
    next_idx = body.find("\n## ", index_idx + 5)
    assert next_idx > 0
    index_section = body[index_idx:next_idx]
    assert len(index_section) <= 1500, (
        f"capability index exceeds 1500-char budget: {len(index_section)}"
    )


def test_AC_alpha_1_lean_on_the_corpus_operational_rule_marker_present():
    """The ``### Lean on the corpus`` operational-rule heading exists
    inside the ``## Operational rules`` section."""
    body = _body()
    ops_idx = body.index("## Operational rules")
    # The rule sits inside Operational rules. Ensure it appears after
    # the Operational rules heading (it is the last entry in the file
    # by current authoring; future edits may move it but it must stay
    # under Operational rules).
    rule_idx = body.find("### Lean on the corpus", ops_idx)
    assert rule_idx > ops_idx, (
        "### Lean on the corpus operational-rule heading missing or "
        "located outside the ## Operational rules section"
    )


def test_AC_alpha_1_lean_on_the_corpus_rule_under_150_words():
    """The Lean on the corpus rule paragraph is ≤ 150 words (rule
    budget per plan §4 AC.α.1)."""
    body = _body()
    rule_idx = body.index("### Lean on the corpus")
    next_idx = body.find("\n### ", rule_idx + 5)
    if next_idx < 0:
        next_idx = len(body)
    rule_section = body[rule_idx:next_idx]
    # Strip the heading; count remaining words.
    rule_body = rule_section.replace("### Lean on the corpus", "", 1)
    word_count = len(rule_body.split())
    assert word_count <= 150, (
        f"Lean on the corpus rule exceeds 150 words: {word_count}"
    )


def test_AC_alpha_1_lean_on_the_corpus_names_read_tool_and_corpus_path():
    """The Lean on the corpus rule names the on-demand fetch
    convention — Read tool + capability-corpus path."""
    body = _body()
    rule_idx = body.index("### Lean on the corpus")
    next_idx = body.find("\n### ", rule_idx + 5)
    if next_idx < 0:
        next_idx = len(body)
    rule_section = body[rule_idx:next_idx].lower()
    assert "read tool" in rule_section, (
        "Lean on the corpus rule must name the Read tool"
    )
    assert "docs/rebuild/capability-corpus/" in rule_section, (
        "Lean on the corpus rule must name the capability-corpus path"
    )

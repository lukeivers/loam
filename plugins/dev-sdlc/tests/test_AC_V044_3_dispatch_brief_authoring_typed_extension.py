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

"""AC.V044.3 — ``dispatch-brief-authoring`` SKILL.md extension for
typed personas.

Per ``docs/plans/v0-4-4-subagent-personas-routing-and-priming.md``
§4 AC.V044.3: the existing ``dispatch-brief-authoring`` SKILL is
extended with a §"When subagent_type is not general-purpose"
section. Required content:

- Names that briefs dispatched via ``subagent_type: <persona>``
  MAY omit the propagated-principle block (AC.DBT.1–6) because
  the persona body carries the same discipline (PARTIAL omission
  per the v0.4.4 audit cross-walk).
- Names that briefs MUST still carry: Working directory + literal
  ``cd <abs-path> && pwd`` first action + Sub-plan path + Fence +
  ACs + Halt triggers + Out of scope + Model rationale.
- Names what the brief MAY skip when typed: per-cycle re-derivation
  of channel rules, autonomy directive, F2 RF reminder, ODD §2.5
  reminder, scope-only enforcement.
- Backward-compat clause: when ``subagent_type == general-purpose``,
  the existing AC.DBT.1–6 propagation behavior is preserved
  unchanged.
- Structural assertion: the AC.DBT.1–6 block is still present in
  the SKILL body (no regression on AC.DBT.1).
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "dispatch-brief-authoring"
    / "SKILL.md"
)


def _load_skill_body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"SKILL.md must start with YAML frontmatter at {SKILL_PATH}"
    return match.group(2)


def test_AC_V044_3_typed_extension_section_present() -> None:
    """The brief-authoring SKILL body contains a section naming
    'When subagent_type is not general-purpose' (AC.V044.3)."""
    body = _load_skill_body()
    assert "When `subagent_type` is not `general-purpose`" in body, (
        "AC.V044.3: SKILL.md must contain a 'When subagent_type is "
        "not general-purpose' section."
    )


def test_AC_V044_3_extension_references_v044_3_ac() -> None:
    """The extension is anchored to AC.V044.3 (so the link between
    SKILL section and locking AC is structural)."""
    body = _load_skill_body()
    assert "AC.V044.3" in body, (
        "AC.V044.3: extension section must cite AC.V044.3 explicitly "
        "for traceability."
    )


def test_AC_V044_3_extension_names_partial_omission() -> None:
    """The extension explicitly notes the omission is PARTIAL (not
    blanket) per the v0.4.4 audit cross-walk — protects against
    silent stripping of discipline the persona doesn't carry."""
    body = _load_skill_body()
    # Either the word 'PARTIAL' (uppercase emphasis per the SKILL's
    # convention) or a per-persona table mentioning OMIT-OK or
    # propagate per row.
    has_partial_word = "PARTIAL" in body
    has_per_persona_table = (
        "OMIT-OK" in body and "propagate" in body
    )
    assert has_partial_word or has_per_persona_table, (
        "AC.V044.3: extension must name PARTIAL omission or carry "
        "a per-persona OMIT-OK/propagate table."
    )


def test_AC_V044_3_extension_names_required_brief_slots() -> None:
    """The extension names the slots the brief MUST still carry
    when typed (Working directory + Sub-plan path + Fence + ACs +
    Halt triggers + Out of scope + Model rationale)."""
    body = _load_skill_body()
    # We assert the extension block contains these slot names. Search
    # within a reasonable window after the extension heading so we
    # don't false-positive on the canonical structural list.
    extension_idx = body.find(
        "When `subagent_type` is not `general-purpose`"
    )
    assert extension_idx >= 0
    extension_block = body[extension_idx : extension_idx + 4000]
    # Markdown line-wrapping splits multi-word slot names across
    # newlines (e.g., "Halt\n   triggers"). Normalize whitespace
    # before substring matching so the assertion tracks intent.
    extension_block_flat = " ".join(extension_block.split())
    for slot in (
        "Working directory",
        "Sub-plan path",
        "Fence",
        "Acceptance criteria",
        "Halt triggers",
        "Out of scope",
        "Model rationale",
    ):
        assert slot in extension_block_flat, (
            f"AC.V044.3: extension block must name the {slot!r} slot "
            "as still-required when typed."
        )


def test_AC_V044_3_extension_names_skippable_when_typed() -> None:
    """The extension names what MAY be skipped when typed (channel
    rules / autonomy / F2 RF / ODD §2.5 / scope-only) — these live
    in the persona body."""
    body = _load_skill_body()
    extension_idx = body.find(
        "When `subagent_type` is not `general-purpose`"
    )
    assert extension_idx >= 0
    extension_block = body[extension_idx : extension_idx + 4000]
    extension_block_lower = extension_block.lower()
    # A representative subset; we don't require all five named, just
    # that the SKILL acknowledges the skip-when-typed surface for
    # the per-cycle re-derivations.
    skip_signals = (
        "channel" in extension_block_lower
        or "autonomy" in extension_block_lower
        or "f2 rf" in extension_block_lower
        or "odd §2.5" in extension_block_lower
        or "scope-only" in extension_block_lower
    )
    assert skip_signals, (
        "AC.V044.3: extension must acknowledge the per-cycle "
        "re-derivations the brief MAY skip when typed."
    )


def test_AC_V044_3_backward_compat_clause_present() -> None:
    """When ``subagent_type == general-purpose``, the existing
    AC.DBT.1–6 propagation behavior is preserved unchanged."""
    body = _load_skill_body()
    body_lower = body.lower()
    assert "backward-compat" in body_lower or "backward compat" in body_lower, (
        "AC.V044.3: extension must carry a backward-compat clause "
        "naming the general-purpose default behavior is preserved."
    )
    # And the clause must reference general-purpose as the default.
    assert "general-purpose" in body, (
        "AC.V044.3: backward-compat clause must reference the "
        "general-purpose default."
    )


def test_AC_V044_3_no_regression_on_AC_DBT_block() -> None:
    """The AC.DBT.1–6 propagated-principle block is still present
    in the SKILL body (no regression on AC.DBT.1)."""
    body = _load_skill_body()
    assert "Propagated principles for sub-agents" in body, (
        "AC.V044.3 + AC.DBT.1: propagated-principles sub-section "
        "must still be present (no regression)."
    )
    for ac_id in ("AC.DBT.2", "AC.DBT.3", "AC.DBT.4", "AC.DBT.5", "AC.DBT.6"):
        assert ac_id in body, (
            f"AC.V044.3 + AC.DBT.1: propagated-principles block must "
            f"still reference {ac_id} (no regression)."
        )

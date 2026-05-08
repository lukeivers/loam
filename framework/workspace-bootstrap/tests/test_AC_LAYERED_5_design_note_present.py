# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LAYERED.5 — design-note ``docs/design/layered-skill-architecture.md``
exists and articulates the 3-tier model + override semantics + lifecycle
+ the auto-symlinking mechanism + collision rules + Anthropic SKILL.md
spec reference.

Per ``docs/plans/v0-1-7-cycle-3-layered-skill-discovery.md`` §4.
"""

from __future__ import annotations

from pathlib import Path


def _design_note_path() -> Path:
    """Resolve the canonical design-note path relative to the repo
    root. Tests run from the workspace root in the canonical pos-v2
    layout."""
    # Walk up from this test file to find the repo root.
    here = Path(__file__).resolve()
    # framework/workspace-bootstrap/tests/<this>.py — repo root is 3 up.
    repo_root = here.parents[3]
    return repo_root / "docs" / "design" / "layered-skill-architecture.md"


def test_design_note_exists() -> None:
    """File is present at the canonical path."""
    assert _design_note_path().is_file()


def test_design_note_articulates_three_tier_model() -> None:
    """Body names the three layers (base / plugin / workspace-local)."""
    body = _design_note_path().read_text()
    assert "Base loam skills" in body
    assert "Plugin skills" in body
    assert "Workspace-local skills" in body


def test_design_note_articulates_override_semantics() -> None:
    """Body articulates override semantics (workspace > plugin > base
    in the project-discovery surface; case A/B/C taxonomy)."""
    body = _design_note_path().read_text()
    assert "override" in body.lower()
    # Case A/B/C taxonomy from the research §2.3 reflected here.
    assert "Case A" in body
    assert "Case B" in body
    assert "Case C" in body


def test_design_note_articulates_lifecycle() -> None:
    """Body covers lifecycle (when added, when garbage-collected)."""
    body = _design_note_path().read_text()
    assert "Lifecycle" in body or "lifecycle" in body
    # Garbage-collection paths (manual + stale-detection +
    # promotion-driven).
    assert "Manual" in body
    assert "Stale-detection" in body or "stale" in body.lower()


def test_design_note_articulates_auto_symlink_mechanism() -> None:
    """Body articulates the auto-symlinking mechanism + names the
    actual function."""
    body = _design_note_path().read_text()
    assert "_symlink_plugin_skills" in body
    assert "auto-symlink" in body.lower() or "symlink" in body.lower()


def test_design_note_articulates_collision_rules() -> None:
    """Body articulates collision precedence + names the exception
    type."""
    body = _design_note_path().read_text()
    assert "PluginSkillCollisionError" in body
    assert "collision" in body.lower()
    assert "operator-precedence" in body.lower()


def test_design_note_references_anthropic_skill_md_spec() -> None:
    """Body references the Anthropic SKILL.md spec the discovery
    primitive lives on."""
    body = _design_note_path().read_text()
    assert "Anthropic" in body
    assert "SKILL.md" in body


def test_design_note_links_to_implementation() -> None:
    """Body references the implementation path for cross-discovery."""
    body = _design_note_path().read_text()
    assert "first_run_scaffold.py" in body

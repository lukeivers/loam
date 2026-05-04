# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLS-BUG.1 — `plugins/loam-skills/` named in default
bootstrap.yaml template.

Per ``docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.SKILLS-BUG.1: the rendered default ``_BOOTSTRAP_YAML`` template
references ``plugins/loam-skills/`` in a discoverable-plugins comment
block. This is the bug fix for the v0.1.0-shipper-tripping issue
where the 5 base SKILLs shipped pip-installable but were not visible
to fresh canonical workspaces because Claude Code's discovery walk
didn't know to look at ``plugins/loam-skills/skills/`` (the comment
block makes the discovery surface explicit and is read by the
operator who needs to keep an eye on which plugins are installed).
"""

from __future__ import annotations

from loam.workspace_bootstrap.adapters.first_run_scaffold import _BOOTSTRAP_YAML


def test_loam_skills_named_in_default_bootstrap_yaml() -> None:
    """The rendered template references plugins/loam-skills/."""
    assert "plugins/loam-skills/" in _BOOTSTRAP_YAML


def test_dev_sdlc_named_in_default_bootstrap_yaml() -> None:
    """Both shipped plugins are named in the discoverable-plugins
    comment so operators see the full picture."""
    assert "plugins/dev-sdlc/" in _BOOTSTRAP_YAML


def test_safety_profile_default_dev_in_template() -> None:
    """The template carries the AC.PSAFE.2 default `dev` so a fresh
    workspace boots with the dev profile."""
    assert "safety_profile: dev" in _BOOTSTRAP_YAML

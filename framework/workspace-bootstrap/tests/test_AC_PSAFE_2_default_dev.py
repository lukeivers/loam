# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PSAFE.2 — default value when safety_profile is absent is `dev`.

Per ``docs/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.PSAFE.2: when the bootstrap manifest does NOT carry a
``safety_profile`` field, the loader defaults to ``"dev"`` (matches
today's behavior — dev workspaces don't pay the production-stake tax).
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.manifest import (
    DEFAULT_SAFETY_PROFILE,
    load_manifest,
)


def _write_manifest_without_profile(tmp_path: Path) -> Path:
    body = (
        "version: 1\n"
        "contributions:\n"
        "  - name: dummy_module\n"
        "    module: nonexistent.module\n"
        "    attr: NonExistentClass\n"
    )
    p = tmp_path / "bootstrap.yaml"
    p.write_text(body)
    return p


def test_default_safety_profile_when_field_absent(tmp_path: Path) -> None:
    """Manifest without `safety_profile` defaults to `dev`."""
    p = _write_manifest_without_profile(tmp_path)
    manifest = load_manifest(p)
    assert manifest.safety_profile == "dev"
    assert manifest.safety_profile == DEFAULT_SAFETY_PROFILE


def test_default_safety_profile_constant_pinned() -> None:
    """The default is `dev` — pinned against accidental change."""
    assert DEFAULT_SAFETY_PROFILE == "dev"

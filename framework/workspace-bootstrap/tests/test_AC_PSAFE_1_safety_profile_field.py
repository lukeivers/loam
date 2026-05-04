# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PSAFE.1 — `safety_profile` field accepted at workspace-bootstrap.

Per ``docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.PSAFE.1: legal values are ``production-stake | dev | research``.
Any other value fails-closed via ``MissingConfigError`` (matches the
loader's existing fail-closed shape).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.errors import MissingConfigError
from loam.workspace_bootstrap.manifest import (
    LEGAL_SAFETY_PROFILES,
    load_manifest,
)


def _write_manifest(tmp_path: Path, safety_profile: str | None) -> Path:
    """Write a minimal bootstrap.yaml under tmp_path with the given
    safety_profile (or omit the field if None)."""
    profile_line = (
        f"safety_profile: {safety_profile}\n" if safety_profile is not None else ""
    )
    body = (
        "version: 1\n"
        f"{profile_line}"
        "contributions:\n"
        "  - name: dummy_module\n"
        "    module: nonexistent.module\n"
        "    attr: NonExistentClass\n"
    )
    p = tmp_path / "bootstrap.yaml"
    p.write_text(body)
    return p


@pytest.mark.parametrize(
    "profile",
    sorted(LEGAL_SAFETY_PROFILES),
)
def test_legal_safety_profile_values_accepted(
    tmp_path: Path, profile: str
) -> None:
    """All three legal values parse without error."""
    p = _write_manifest(tmp_path, profile)
    manifest = load_manifest(p)
    assert manifest.safety_profile == profile


def test_invalid_safety_profile_value_fails_closed(tmp_path: Path) -> None:
    """An unknown value raises MissingConfigError (fail-closed)."""
    p = _write_manifest(tmp_path, "freewheel")
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    msg = str(exc_info.value)
    assert "safety_profile" in msg
    assert "freewheel" in msg


def test_non_string_safety_profile_value_fails_closed(tmp_path: Path) -> None:
    """A non-string value (e.g., int, list) raises MissingConfigError."""
    body = (
        "version: 1\n"
        "safety_profile: 42\n"
        "contributions:\n"
        "  - name: dummy_module\n"
        "    module: nonexistent.module\n"
        "    attr: NonExistentClass\n"
    )
    p = tmp_path / "bootstrap.yaml"
    p.write_text(body)
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    assert "safety_profile" in str(exc_info.value)


def test_legal_safety_profiles_set_pinned() -> None:
    """The frozenset of legal values is exactly the three named in
    the AC; this test pins the set against accidental widening."""
    assert LEGAL_SAFETY_PROFILES == frozenset(
        {"production-stake", "dev", "research"}
    )

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

"""AC.SKILLCAP.7 (pinning test) — `Manifest` dataclass shape.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.7: the `Manifest` dataclass declares the field
`enable_auto_skill_capture: bool` with default `False` (boolean
literal, not string). This test pins that shape so an accidental
widening (e.g., to `str` to support tri-state values) gets caught
at code-review time.

Mirrors `test_AC_PSAFE_1_safety_profile_field.py::test_legal_safety_profiles_set_pinned`
shape — pin-test for the field's contract.
"""

from __future__ import annotations

from dataclasses import fields

from loam.workspace_bootstrap.manifest import (
    DEFAULT_ENABLE_AUTO_SKILL_CAPTURE,
    Manifest,
)


def test_default_enable_auto_skill_capture_is_false_literal() -> None:
    """The module-level constant is the boolean False literal —
    NOT a string ('false') and NOT an int (0). This pins the
    constant against accidental type-drift in future commits."""
    assert DEFAULT_ENABLE_AUTO_SKILL_CAPTURE is False
    assert isinstance(DEFAULT_ENABLE_AUTO_SKILL_CAPTURE, bool)
    # Belt-and-suspenders: bool is a subclass of int in Python, so
    # an `isinstance(False, int)` is True; assert against type
    # *strictly* via `type(...) is bool` — pins against accidental
    # int 0 default.
    assert type(DEFAULT_ENABLE_AUTO_SKILL_CAPTURE) is bool


def test_manifest_dataclass_has_field() -> None:
    """The `Manifest` dataclass declares an
    `enable_auto_skill_capture` field. Per AC.SKILLCAP.7."""
    field_names = {f.name for f in fields(Manifest)}
    assert "enable_auto_skill_capture" in field_names


def test_manifest_field_default_is_false() -> None:
    """The dataclass field's default is the constant
    `DEFAULT_ENABLE_AUTO_SKILL_CAPTURE` (which is False per the
    constant-pin test above) — verified by constructing a
    `Manifest` with all required positional fields and reading the
    default."""
    # Construct a Manifest with only the required-positional fields;
    # both safety_profile and enable_auto_skill_capture have defaults.
    from pathlib import Path

    m = Manifest(
        version=1,
        config_dir=Path("/tmp/config"),
        workspace_root=Path("/tmp/ws"),
        manifest_path=Path("/tmp/ws/bootstrap.yaml"),
        refs=(),
    )
    assert m.enable_auto_skill_capture is False


def test_manifest_field_accepts_explicit_true() -> None:
    """Constructing a Manifest with explicit `enable_auto_skill_capture=True`
    overrides the default."""
    from pathlib import Path

    m = Manifest(
        version=1,
        config_dir=Path("/tmp/config"),
        workspace_root=Path("/tmp/ws"),
        manifest_path=Path("/tmp/ws/bootstrap.yaml"),
        refs=(),
        enable_auto_skill_capture=True,
    )
    assert m.enable_auto_skill_capture is True


def test_manifest_safety_profile_field_unaffected() -> None:
    """Adding the new field doesn't break the existing safety_profile
    field — both coexist on the dataclass with their own defaults."""
    field_names = {f.name for f in fields(Manifest)}
    assert "safety_profile" in field_names
    assert "enable_auto_skill_capture" in field_names
    # Both should have defaults (so callers can omit either).
    field_defaults = {
        f.name: f.default
        for f in fields(Manifest)
    }
    # safety_profile default is `"dev"` (string) per AC.PSAFE.2.
    assert field_defaults["safety_profile"] == "dev"
    # enable_auto_skill_capture default is `False` per AC.SKILLCAP.7.
    assert field_defaults["enable_auto_skill_capture"] is False

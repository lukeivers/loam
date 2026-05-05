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

"""AC.SKILLCAP.7 — `enable_auto_skill_capture` flag default-false +
fail-closed on non-bool.

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.7: the workspace-bootstrap manifest carries an
`enable_auto_skill_capture: bool` field, default `False`. Mirrors
`safety_profile`'s shape — frozenset of legal values (here: bool
True/False), default literal, fail-closed `MissingConfigError` on
invalid types.

Per layered-skill research §3.6 Decision E: a fresh workspace
shouldn't auto-propose skills; the user opts in by flipping the
flag when they're ready. Default-false is the load-bearing
discipline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.errors import MissingConfigError
from loam.workspace_bootstrap.manifest import load_manifest


def _write_manifest(
    tmp_path: Path,
    enable_auto_skill_capture_line: str | None,
) -> Path:
    """Write a minimal bootstrap.yaml under tmp_path with the given
    enable_auto_skill_capture value (or omit the field if None).

    The line is an arbitrary YAML expression — the caller chooses the
    type they want to test (true / false / 'enabled' / 1 / etc.)."""
    flag_line = (
        f"enable_auto_skill_capture: {enable_auto_skill_capture_line}\n"
        if enable_auto_skill_capture_line is not None
        else ""
    )
    body = (
        "version: 1\n"
        f"{flag_line}"
        "contributions:\n"
        "  - name: dummy_module\n"
        "    module: nonexistent.module\n"
        "    attr: NonExistentClass\n"
    )
    p = tmp_path / "bootstrap.yaml"
    p.write_text(body)
    return p


def test_absent_field_defaults_to_false(tmp_path: Path) -> None:
    """When the field is omitted entirely, the default is False.

    Per layered-skill research §3.6 Decision E: a fresh workspace
    shouldn't auto-propose; default-false is the load-bearing
    discipline."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line=None)
    manifest = load_manifest(p)
    assert manifest.enable_auto_skill_capture is False


def test_explicit_true_accepted(tmp_path: Path) -> None:
    """`enable_auto_skill_capture: true` parses to Python True."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="true")
    manifest = load_manifest(p)
    assert manifest.enable_auto_skill_capture is True


def test_explicit_false_accepted(tmp_path: Path) -> None:
    """`enable_auto_skill_capture: false` parses to Python False."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="false")
    manifest = load_manifest(p)
    assert manifest.enable_auto_skill_capture is False


def test_yaml_True_capitalised_accepted(tmp_path: Path) -> None:
    """PyYAML accepts both `true` and `True` as bool true; the loader
    preserves that liberality (the fail-closed gate is on
    non-bool types, not on YAML capitalisation)."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="True")
    manifest = load_manifest(p)
    assert manifest.enable_auto_skill_capture is True


def test_string_value_fails_closed(tmp_path: Path) -> None:
    """A string value (e.g., `enabled`) raises MissingConfigError.

    Mirrors the fail-closed shape used for `safety_profile` invalid
    values."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="enabled")
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    msg = str(exc_info.value)
    assert "enable_auto_skill_capture" in msg
    assert "enabled" in msg


def test_integer_value_fails_closed(tmp_path: Path) -> None:
    """An int value (e.g., `1`) raises MissingConfigError. Per the
    plan-doc decision, the flag is bool only — integers are NOT
    coerced to bool."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="1")
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    msg = str(exc_info.value)
    assert "enable_auto_skill_capture" in msg


def test_zero_integer_value_fails_closed(tmp_path: Path) -> None:
    """An int 0 also fails-closed (NOT coerced to False)."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="0")
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    msg = str(exc_info.value)
    assert "enable_auto_skill_capture" in msg


def test_list_value_fails_closed(tmp_path: Path) -> None:
    """A list value fails-closed."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="[true]")
    with pytest.raises(MissingConfigError) as exc_info:
        load_manifest(p)
    assert "enable_auto_skill_capture" in str(exc_info.value)


def test_null_value_treated_as_absent(tmp_path: Path) -> None:
    """A literal `null` value is treated as absent (defaults to False).

    PyYAML parses `null` to Python None; the loader's branch on
    `is None` matches absent-key, so explicit-null + absent both
    default. This is consistent with `safety_profile`'s handling
    (the existing manifest loader's None-branch is the
    default-fallback for both shapes)."""
    p = _write_manifest(tmp_path, enable_auto_skill_capture_line="null")
    manifest = load_manifest(p)
    assert manifest.enable_auto_skill_capture is False


def test_existing_safety_profile_unaffected(tmp_path: Path) -> None:
    """Adding the new field doesn't break safety_profile parsing —
    a manifest with both fields parses correctly."""
    body = (
        "version: 1\n"
        "safety_profile: production-stake\n"
        "enable_auto_skill_capture: true\n"
        "contributions:\n"
        "  - name: dummy_module\n"
        "    module: nonexistent.module\n"
        "    attr: NonExistentClass\n"
    )
    p = tmp_path / "bootstrap.yaml"
    p.write_text(body)
    manifest = load_manifest(p)
    assert manifest.safety_profile == "production-stake"
    assert manifest.enable_auto_skill_capture is True

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

"""AC.SBB.4 — the baseline is a NON-tunable floor.

The three guarantees are on for every build by default and cannot be
disabled by ordinary project config; their strictness (block vs surface)
is the only tunable; the floor (a secret is never committed) is NOT among
the tunables."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.secure_build_baseline.strictness import (
    ALL_GUARANTEES,
    NON_TUNABLE_GUARANTEES,
    TUNABLE_GUARANTEES,
    Strictness,
    is_tunable,
    load_secure_build_config,
    resolve_strictness,
)


def test_all_three_guarantees_default_to_block_with_no_config() -> None:
    """Default-on: with no config every guarantee resolves to BLOCK (the
    guarantees are on for every build by default)."""
    for g in ALL_GUARANTEES:
        assert resolve_strictness(g, None) is Strictness.BLOCK


def test_the_three_guarantees_are_the_secure_build_floor() -> None:
    assert ALL_GUARANTEES == {
        "secret-commit",
        "dependency-audit",
        "artifact-cleanliness",
    }


def test_tunable_guarantees_can_be_set_to_surface() -> None:
    config = {"strictness": {"dependency-audit": "surface", "artifact-cleanliness": "surface"}}
    assert resolve_strictness("dependency-audit", config) is Strictness.SURFACE
    assert resolve_strictness("artifact-cleanliness", config) is Strictness.SURFACE


def test_secret_commit_floor_is_NOT_tunable() -> None:
    """The secret-never-committed floor cannot be downgraded to surface —
    a config attempting it is IGNORED and the floor stays BLOCK."""
    assert "secret-commit" in NON_TUNABLE_GUARANTEES
    assert "secret-commit" not in TUNABLE_GUARANTEES
    assert not is_tunable("secret-commit")
    config = {"strictness": {"secret-commit": "surface"}}
    assert resolve_strictness("secret-commit", config) is Strictness.BLOCK


def test_unknown_strictness_value_falls_back_to_block(tmp_path: Path) -> None:
    config = {"strictness": {"dependency-audit": "lenient-please"}}
    assert resolve_strictness("dependency-audit", config) is Strictness.BLOCK


def test_unknown_guarantee_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_strictness("invent-a-guarantee", {})


def test_config_loads_from_workspace(tmp_path: Path) -> None:
    loam = tmp_path / ".loam"
    loam.mkdir()
    (loam / "secure-build.yaml").write_text(
        "strictness:\n  dependency-audit: surface\n", encoding="utf-8"
    )
    config = load_secure_build_config(tmp_path)
    assert config is not None
    assert resolve_strictness("dependency-audit", config) is Strictness.SURFACE
    # The non-tunable floor is unaffected by ANY config.
    assert resolve_strictness("secret-commit", config) is Strictness.BLOCK


def test_absent_config_returns_none(tmp_path: Path) -> None:
    assert load_secure_build_config(tmp_path) is None


def test_malformed_config_raises_for_failsoft_handling(tmp_path: Path) -> None:
    """A non-mapping config raises so the hook can fail-soft to default
    strictness (the floor never escalates on a broken tuning file)."""
    loam = tmp_path / ".loam"
    loam.mkdir()
    (loam / "secure-build.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_secure_build_config(tmp_path)

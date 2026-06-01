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

"""AC.INST.S (resolver unit half) — the first-run scaffold resolves the
framework persona template against the CLONED ``<workspace>/framework/``
tree, NOT only relative to the installed module's ``__file__``.

This is the load-bearing fix for the clean-env ``loam init`` outcome
(SUB-ITEM 1a, Option-A widen). Under a wheel / pipx install the scaffold
module lives in ``site-packages/`` and the legacy ``Path(__file__)``-
relative parents-walk never finds the persona template — even though
``loam init`` has cloned canonical (which carries the template) into
``<ws>/framework/``. These tests pin that the workspace-relative branch
finds the template in each on-disk clone shape, and that the resolver
still raises the structured ``persona-template-not-found`` when the
template is genuinely absent.

The end-to-end clean-env install + real ``loam init`` proof for
AC.INST.S lives in the loam-init component's outcome-altitude test
(``test_AC_INST_S_clean_env_install_and_init.py``); this file is the
focused unit assertion on the resolver branch that makes it possible.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _PERSONA_TEMPLATE_RELPATH,
    _resolve_persona_template_dir,
)
from loam.workspace_bootstrap.errors import BootstrapError


def _seed_template(framework_root: Path) -> Path:
    """Create a minimal persona-template dir under *framework_root* and
    return the template dir path."""
    template_dir = framework_root / _PERSONA_TEMPLATE_RELPATH
    template_dir.mkdir(parents=True)
    (template_dir / "contract.yaml").write_text("handle: primary\n")
    (template_dir / "prompt.md").write_text("# persona\n")
    return template_dir


def test_resolves_from_doubled_clone_shape(tmp_path: Path) -> None:
    """The real ``loam init`` clone-into produces the doubled
    ``<ws>/framework/framework/primary-persona/...`` shape (canonical
    carries ``framework/<comp>/`` paths, cloned INTO ``<ws>/framework/``).
    The resolver must find it there."""
    ws = tmp_path / "my-workspace"
    seeded = _seed_template(ws / "framework" / "framework")

    resolved = _resolve_persona_template_dir(workspace_root=ws)

    assert resolved == seeded.resolve()


def test_resolves_from_single_level_framework_shape(tmp_path: Path) -> None:
    """Defensive: a single-level ``<ws>/framework/primary-persona/...``
    shape (a flattened / non-doubled clone) also resolves."""
    ws = tmp_path / "my-workspace"
    seeded = _seed_template(ws / "framework")

    resolved = _resolve_persona_template_dir(workspace_root=ws)

    assert resolved == seeded.resolve()


def test_resolves_from_canonical_pos_v2_shape(tmp_path: Path) -> None:
    """Canonical pos-v2 dev: the workspace root IS the repo root, so the
    template sits at ``<ws>/primary-persona/...``."""
    ws = tmp_path / "canonical"
    seeded = _seed_template(ws)

    resolved = _resolve_persona_template_dir(workspace_root=ws)

    assert resolved == seeded.resolve()


def test_doubled_shape_wins_over_absent_single_level(tmp_path: Path) -> None:
    """When only the doubled shape exists, resolution must NOT fall
    through to the ``__file__`` walk (which under a wheel install would
    miss) — it must return the cloned-workspace copy."""
    ws = tmp_path / "ws"
    seeded = _seed_template(ws / "framework" / "framework")
    # No single-level or canonical copy present.
    assert not (ws / "framework" / _PERSONA_TEMPLATE_RELPATH).exists()

    resolved = _resolve_persona_template_dir(workspace_root=ws)

    assert resolved == seeded.resolve()


def test_template_override_still_wins(tmp_path: Path) -> None:
    """The explicit test-seam override takes precedence over the
    workspace-relative resolution (back-compat with the existing
    test suite)."""
    override = tmp_path / "override-template"
    override.mkdir()
    ws = tmp_path / "ws"
    _seed_template(ws / "framework" / "framework")

    resolved = _resolve_persona_template_dir(
        template_override=override, workspace_root=ws
    )

    assert resolved == override.resolve()


def test_wheel_install_misses_then_workspace_branch_saves_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The EXACT clean-env bug: simulate a wheel install by pointing the
    module ``__file__`` at an isolated site-packages-like path with no
    framework tree above it, so the legacy ``__file__`` parents-walk
    misses entirely. Without the workspace-relative branch this raised
    ``persona-template-not-found`` (the clean-env ``loam init`` failure);
    WITH it, the cloned-workspace copy resolves.
    """
    import loam.workspace_bootstrap.adapters.first_run_scaffold as scaffold

    fake_site_packages = tmp_path / "site-packages" / "loam" / "workspace_bootstrap"
    fake_site_packages.mkdir(parents=True)
    monkeypatch.setattr(
        scaffold, "__file__", str(fake_site_packages / "first_run_scaffold.py")
    )

    ws = tmp_path / "ws"
    seeded = _seed_template(ws / "framework" / "framework")

    # With the workspace branch: resolves from the clone.
    resolved = _resolve_persona_template_dir(workspace_root=ws)
    assert resolved == seeded.resolve()


def test_wheel_install_with_no_clone_raises_structured_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When BOTH the wheel-install ``__file__`` walk misses AND the
    workspace carries no framework clone, the resolver raises the
    structured ``persona-template-not-found`` carrying the searched
    workspace_root — the honest diagnostic for a genuinely broken
    install (not a silent wrong-path)."""
    import loam.workspace_bootstrap.adapters.first_run_scaffold as scaffold

    fake_site_packages = tmp_path / "site-packages" / "loam" / "workspace_bootstrap"
    fake_site_packages.mkdir(parents=True)
    monkeypatch.setattr(
        scaffold, "__file__", str(fake_site_packages / "first_run_scaffold.py")
    )

    ws = tmp_path / "empty-workspace"
    ws.mkdir()

    with pytest.raises(BootstrapError) as exc_info:
        _resolve_persona_template_dir(workspace_root=ws)

    assert "persona-template-not-found" in str(exc_info.value)
    assert str(ws) in str(exc_info.value.data.get("workspace_root", ""))

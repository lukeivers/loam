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

"""AC.PYPKG.1 — ONE documented install surface resolves the loam CLI
dependency graph.

The chosen surface (D-INST.1) is a dependencies-only ``loam`` meta-
distribution at ``framework/loam-init/meta/``. These tests pin its
shape from the on-disk pyproject (no network, no install): it declares
the user-facing CLI verbs as dependencies, names a single distribution,
and ships ZERO ``loam/`` package code (``loam`` is a PEP 420 namespace
package; a meta-distribution shipping a ``loam/`` package would shadow
it). The single documented command is named in ONE place — this
pyproject — not re-derived per component.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
META_PYPROJECT = REPO_ROOT / "framework" / "loam-init" / "meta" / "pyproject.toml"


@pytest.fixture(scope="module")
def meta() -> dict:
    with META_PYPROJECT.open("rb") as f:
        return tomllib.load(f)


def test_meta_distribution_exists_and_is_named_loam(meta: dict) -> None:
    """AC.PYPKG.1 — there IS one documented surface, named ``loam``."""
    assert META_PYPROJECT.is_file()
    assert meta["project"]["name"] == "loam"


def test_meta_surface_pulls_the_documented_cli_verbs(meta: dict) -> None:
    """The single surface resolves the whole loam CLI graph: the console-
    script package + the user-facing verbs are listed as dependencies, so
    one install command pulls them (and their transitive bounds)."""
    deps = {
        d.split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip()
        for d in meta["project"]["dependencies"]
    }
    # The console-script binary + the init verb are the load-bearing
    # anchors AC.INST.1 / AC.INST.S drive.
    required = {"loam-cli", "loam-init", "loam-amend"}
    missing = required - deps
    assert not missing, f"meta surface omits CLI-graph anchors: {missing}"


def test_meta_distribution_ships_zero_package_code(meta: dict) -> None:
    """``loam`` is a PEP 420 implicit-namespace package. The meta-
    distribution MUST declare no packages — shipping a ``loam/`` package
    would shadow the namespace and break every component import."""
    setuptools_cfg = meta.get("tool", {}).get("setuptools", {})
    assert setuptools_cfg.get("packages") == [], (
        "meta-distribution must be dependencies-only (packages = []); "
        f"got {setuptools_cfg.get('packages')!r}"
    )


def test_no_root_pyproject_competes_with_the_surface() -> None:
    """The documented surface is the meta-distribution, not a root
    ``pyproject.toml`` (none exists at repo root — the install is a
    packaging problem composed from the per-component graph, not a
    single monolithic build)."""
    assert not (REPO_ROOT / "pyproject.toml").exists()

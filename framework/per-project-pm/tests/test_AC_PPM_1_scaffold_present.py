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

"""AC.PPM.1 — component scaffold present.

Per parent plan §5: ``framework/per-project-pm/`` exists with
``pyproject.toml`` declaring the entry-point, ``src/loam/per_project_pm/``
package, ``tests/test_no_sealed_amendments.py`` seal-test, ``tests/SEAL_COMMIT``
sidecar (written at apply time), ``README.md``, ``docs/design.md``.
"""

from __future__ import annotations

from pathlib import Path


COMPONENT_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_toml_present_and_declares_entry_point() -> None:
    pyproject = COMPONENT_ROOT / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml missing at {pyproject}"
    body = pyproject.read_text(encoding="utf-8")
    # Entry-point declaration per AC.PPM.1.
    assert '[project.entry-points."loam.bootstrap.contributions"]' in body, (
        "pyproject.toml must declare the loam.bootstrap.contributions entry-point group"
    )
    assert (
        "per_project_pm = "
        '"loam.per_project_pm.contribution:PerProjectPMContribution"' in body
    ), (
        "entry-point must register PerProjectPMContribution under "
        "the per_project_pm name"
    )


def test_src_package_present() -> None:
    pkg = COMPONENT_ROOT / "src" / "loam" / "per_project_pm"
    assert (pkg / "__init__.py").exists()
    assert (pkg / "contract.py").exists()
    assert (pkg / "errors.py").exists()
    assert (pkg / "loader.py").exists()
    assert (pkg / "runtime.py").exists()
    assert (pkg / "state.py").exists()
    assert (pkg / "contribution.py").exists()


def test_seal_test_and_sidecar_path_present() -> None:
    seal_test = COMPONENT_ROOT / "tests" / "test_no_sealed_amendments.py"
    assert seal_test.exists(), (
        "seal-test must exist at tests/test_no_sealed_amendments.py per "
        "amendment-22 NEW-component pattern"
    )
    # SEAL_COMMIT sidecar is written at apply time by `loam amend apply`;
    # the file's parent dir is what we check exists at scaffold time.
    sidecar_dir = COMPONENT_ROOT / "tests"
    assert sidecar_dir.is_dir()


def test_readme_and_design_note_present() -> None:
    assert (COMPONENT_ROOT / "README.md").exists()
    assert (COMPONENT_ROOT / "docs" / "design.md").exists()


def test_imports_resolve() -> None:
    """Every module the __init__ re-exports actually imports."""
    # If any of these fail, the package is broken at import time —
    # the AC ships a working package.
    from loam.per_project_pm import (  # noqa: F401
        DecisionSurfacingPolicy,
        PMContract,
        PMNotFoundError,
        PMRuntime,
        PMStateCorruptedError,
        PerProjectPMContribution,
        PerProjectPMRuntime,
        StateOfWorld,
        SurfacedQuestion,
    )

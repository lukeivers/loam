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

"""AC.WBM2M.4 — conftest's make_fixture_canonical builds a main-shape
fixture without depending on the archived synthesis tool.

Post-OSS-dev-architecture-migration (2026-05-04): the synthesis tool
(``loam.publish_framework_only.synth.synthesise_framework_only``) is
archived at ``docs/archive/synthesis-tool-2026-05-04/`` and
not importable from active source. The conftest's
``_make_fixture_canonical`` factory was rewritten to drop the
synthesis-tool dependency:

- Single-tree fixture: ``git init --initial-branch=main`` (was
  ``--initial-branch=pos-v2``).
- No ``publish-mode-manifest.yaml`` write (deprecated synthesis-tool
  input).
- No ``publish_framework_only`` keyword arg (deprecated).
- No second branch on the fixture canonical.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(args: list[str], *, cwd: Path) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")


def test_AC_WBM2M_4_fixture_is_initialised_on_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The fixture canonical is initialised on ``main`` (was ``pos-v2``
    pre-migration).
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    head_branch = _git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=canonical
    )
    assert head_branch == "main", (
        f"AC.WBM2M.4: fixture canonical must be on 'main'; "
        f"got {head_branch!r}"
    )


def test_AC_WBM2M_4_fixture_carries_framework_paths(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The fixture canonical carries ``framework/<comp>/...`` paths +
    top-level docs (the canonical-pos-v2 shape post-D-cutover).
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    expected_paths = [
        "framework/workspace-sync/src/workspace_sync/__init__.py",
        "framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py",
        "framework/README.md",
        "docs/odd-methodology.md",
        "CLAUDE.md",
    ]
    for rel in expected_paths:
        assert (canonical / rel).exists(), (
            f"AC.WBM2M.4: fixture canonical must carry {rel!r}"
        )


def test_AC_WBM2M_4_fixture_has_no_second_branch(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The fixture canonical has only one branch (``main``); the
    pre-migration ``framework-only`` second branch is gone.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    # `git branch --list` returns one entry per local branch.
    branches = _git(["branch", "--list"], cwd=canonical)
    branch_names = {
        line.lstrip("* ").strip() for line in branches.splitlines() if line.strip()
    }
    assert branch_names == {"main"}, (
        f"AC.WBM2M.4: fixture canonical must have only 'main' as a "
        f"local branch; got {branch_names!r}"
    )


def test_AC_WBM2M_4_synthesis_tool_not_importable_from_conftest():
    """The conftest does not import (and cannot import) the archived
    synthesis tool. Verifies the import is not on the conftest's
    module-level globals.

    The synthesis tool's source is at
    ``docs/archive/synthesis-tool-2026-05-04/``; not on the
    active import path.
    """
    # Import the conftest module itself — even though it's normally
    # auto-discovered by pytest, it lives at a known path and can be
    # imported by name.
    from tests import conftest  # noqa: PLC0415

    # The synthesis tool's name should NOT be in the conftest's
    # module-level globals.
    assert not hasattr(conftest, "synthesise_framework_only"), (
        "AC.WBM2M.4: conftest must not import synthesise_framework_only"
    )
    assert not hasattr(conftest, "_FIXTURE_MANIFEST_REL"), (
        "AC.WBM2M.4: conftest must not retain the deprecated "
        "_FIXTURE_MANIFEST_REL constant"
    )
    assert not hasattr(conftest, "_FIXTURE_MANIFEST_YAML"), (
        "AC.WBM2M.4: conftest must not retain the deprecated "
        "_FIXTURE_MANIFEST_YAML constant"
    )

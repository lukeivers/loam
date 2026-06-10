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

"""Shared test fixtures for workspace-bootstrap."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

# The real canonical loam root (this checkout): parents[3] of a tests/
# file == the repo root.
LOAM_ROOT = Path(__file__).resolve().parents[3]


def write_manifest(path: Path, contributions: list, **extras: Any) -> Path:
    """Write a bootstrap.yaml at `path` with the given contributions list."""
    payload: dict[str, Any] = {
        "version": 1,
        "contributions": contributions,
    }
    payload.update(extras)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload))
    return path


@pytest.fixture
def write_manifest_fn() -> Callable[..., Path]:
    return write_manifest


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Standard test workspace with config/ and data/ subdirs."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---- D.4 fixtures (test_pos_new_workspace.py) -----------------------


def _git(args: list[str], *, cwd: Path) -> None:
    """Run git in ``cwd``; raise on non-zero exit. Used by fixture setup."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", *args],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd!s}: "
            f"{(completed.stderr or '').strip()!r}"
        )


def _make_fixture_canonical(
    root: Path,
    *,
    files: dict[str, str] | None = None,
) -> Path:
    """Construct an ephemeral fixture canonical loam working tree.

    Initialises a git repo at ``root`` on ``main`` (canonical's
    default branch post-OSS-dev-architecture-migration, 2026-05-04),
    writes ``files`` (a mapping of relative path to content), and
    commits them. Returns ``root``.

    Defaults to a small representative file set when ``files`` is None
    (mirrors a stripped-down canonical layout — enough that the
    bootstrap's clone produces a non-trivial framework/ subtree but
    fast enough that test runtime is bounded).

    Pre-migration (synthesis era) the fixture also synthesised a
    ``framework-only`` second branch via the now-archived
    ``pos-publish-framework-only`` tool. Post-migration the bootstrap
    targets canonical's default branch directly (no synthesis layer);
    the fixture is a single-tree git repo on ``main``.
    """
    if files is None:
        files = {
            "framework/workspace-sync/src/workspace_sync/__init__.py": (
                '"""Test fixture canonical workspace-sync package."""\n'
                "__version__ = \"0.0.0-fixture\"\n"
            ),
            "framework/workspace-bootstrap/src/workspace_bootstrap/__init__.py": (
                '"""Test fixture canonical workspace-bootstrap package."""\n'
            ),
            "framework/README.md": "# fixture canonical framework/\n",
            "docs/odd-methodology.md": "# fixture odd-methodology\n",
            "CLAUDE.md": "# fixture CLAUDE.md\n",
        }
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "--initial-branch=main"], cwd=root)
    _git(["config", "user.email", "fixture@local"], cwd=root)
    _git(["config", "user.name", "fixture"], cwd=root)
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    _git(["add", "-A"], cwd=root)
    _git(["commit", "-m", "fixture canonical initial commit"], cwd=root)

    return root


@pytest.fixture
def make_fixture_canonical() -> Callable[..., Path]:
    """Factory fixture for constructing a fixture canonical repo.

    Tests call this with a target path (and optional file dict) and
    receive an absolute Path to a fresh git working tree. Mirrors the
    pattern in workspace-sync's `test_cli_d_shape.py` (D.3) so D.4's
    bootstrap tests can reuse the same canonical-shape.
    """
    return _make_fixture_canonical


# ---- AC.LIVI shared fixture — isolated real-canonical clone ---------


def _real_main_sha() -> str:
    """Tier-0 read of the REAL checkout's ``refs/heads/main``."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "-C", str(LOAM_ROOT), "rev-parse", "refs/heads/main"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture(scope="session")
def isolated_canonical_clone(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[Path]:
    """An ISOLATED local ``git clone`` of the real checkout, for tests
    that bootstrap from real canonical (the AC.LIVI family).

    Bootstrapping ``--from`` the REAL checkout is destructive: the
    local-path branch of ``bootstrap_new_workspace`` runs
    ``_materialise_canonical_branch(<source>)``, which re-points the
    SOURCE's ``refs/heads/main`` at ``refs/remotes/origin/main`` —
    rewinding the live repo's main whenever local is ahead of origin
    (always true mid-amendment). The isolated clone reproduces the
    documented-Quickstart topology MORE faithfully (a stranger's
    ``git clone`` of canonical, where main == origin/main and the
    materialise step is the intended no-op) without mutating the
    real checkout. A local clone hardlinks objects, so it is cheap
    relative to the bootstraps that consume it.

    Teardown guard (the regression assertion): the real checkout's
    ``refs/heads/main`` must be byte-identical before and after the
    consuming tests ran — if any test bootstrapped from the real
    checkout instead of the clone, this fails the session loudly.
    """
    before = _real_main_sha()
    clone = tmp_path_factory.mktemp("canonical-clone") / "loam"
    subprocess.run(  # noqa: S603 — argv constructed
        ["git", "clone", "--quiet", str(LOAM_ROOT), str(clone)],
        stdin=subprocess.DEVNULL,
        check=True,
    )
    yield clone
    after = _real_main_sha()
    assert after == before, (
        f"REGRESSION: the real checkout's refs/heads/main moved during "
        f"the test session ({before} -> {after}); a test bootstrapped "
        f"from the real checkout instead of the isolated clone."
    )

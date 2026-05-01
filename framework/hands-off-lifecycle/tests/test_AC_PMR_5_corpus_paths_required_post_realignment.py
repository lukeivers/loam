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

"""AC.PMR.5 — `compute_corpus_paths_required` returns post-realignment
paths that resolve on disk.

Per post-M6 partition realignment plan §4 AC.PMR.5: with the dev-
mode-manifest's ``roots:`` + ``always_loaded:`` blocks realigned to
``framework/<comp>/`` post-M6b.0, the
``corpus_load_sentinel.compute_corpus_paths_required(workspace_root,
"dev-mode")`` function returns a non-empty list of paths, every one
of which exists on disk relative to the workspace root (via the
function's existing two-tier fall-through).

Pre-realignment the function returned a list largely populated by
paths that don't exist post-M6b.0 (the 15 stale top-level component
refs); the A1 sentinel state classified as ``partial`` or ``missing``
because the path-existence check failed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def _load_compute_paths_required():
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    from corpus_load_sentinel import (  # type: ignore[import-not-found]
        compute_corpus_paths_required,
    )

    return compute_corpus_paths_required


def test_AC_PMR_5_dev_mode_returns_non_empty_paths() -> None:
    """In DEV MODE against canonical pos-v2, the required-paths list
    is non-empty (the manifest's `always_loaded ∪ dev_only` expands
    to many files post-realignment)."""
    compute = _load_compute_paths_required()
    paths = compute(REPO_ROOT, "dev-mode")
    assert len(paths) >= 10, (
        f"expected ≥10 required paths post-realignment; got {len(paths)}"
    )


def test_AC_PMR_5_every_required_path_resolves_on_disk() -> None:
    """Every path returned by `compute_corpus_paths_required` exists
    on disk via the existing two-tier fall-through (`<workspace_root>/
    <rel>` → `<workspace_root>/framework/<rel>`)."""
    compute = _load_compute_paths_required()
    paths = compute(REPO_ROOT, "dev-mode")
    if not paths:
        pytest.skip("manifest unreadable; AC.PMR.5 vacuous")
    framework_root = REPO_ROOT / "framework"
    missing = [
        p
        for p in paths
        if not (REPO_ROOT / p).exists()
        and not (framework_root / p).exists()
    ]
    assert missing == [], (
        f"required paths do not resolve via two-tier fall-through: "
        f"{missing[:5]}..."
    )


def test_AC_PMR_5_normal_use_subset_of_dev_mode() -> None:
    """NORMAL USE corpus is `always_loaded` only; DEV MODE is
    `always_loaded ∪ dev_only`. The NORMAL-USE set is therefore a
    subset of the DEV-MODE set."""
    compute = _load_compute_paths_required()
    normal_paths = set(compute(REPO_ROOT, "normal-use"))
    dev_paths = set(compute(REPO_ROOT, "dev-mode"))
    if not normal_paths and not dev_paths:
        pytest.skip("manifest unreadable; AC.PMR.5 vacuous")
    assert normal_paths.issubset(dev_paths)

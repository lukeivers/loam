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

"""★ AC.PMTRACK.1 — OUTCOME-ALTITUDE: the catalogue ships GIT-TRACKED.

``outcome-altitude: true``. The flagship matrix loaded locally only because
the source-of-truth catalogue was physically present in the build tree — but
it was gitignored by the over-broad ``data/`` rule, so a fresh clone resolved
``default_catalogue_path()`` to a MISSING file and could not load the matrix
at all (the correctness bug this cycle fixes).

This AC asserts the property a fresh clone actually has: from the set of
GIT-TRACKED files ONLY (``git ls-files`` — NOT the working-tree copy), the
catalogue is present, AND loading it through the production
``load_catalogue(default_catalogue_path())`` entry-point parses the full row
set. The test MUST FAIL if the catalogue is untracked / gitignored — that is
the whole point: a working-tree-copy test would pass even with the bug
present, so this asserts against ``git ls-files``, which a gitignored file is
absent from.

(feedback_test_outcome_altitude_required: assert from the real shipped state
a fresh clone would see, not from pre-arranged in-tree state.)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.protection_matrix.catalogue import (
    default_catalogue_path,
    load_catalogue,
)
from loam.protection_matrix.derive import find_repo_root


def _git_tracked_paths(repo_root: Path) -> set[str]:
    """The set of repo-relative paths git ACTUALLY tracks (a fresh clone)."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return {p for p in proc.stdout.split("\0") if p}


def test_AC_PMTRACK_1_catalogue_is_git_tracked_and_loads_from_tracked_set() -> None:
    """The catalogue is in ``git ls-files`` AND parses the full row set.

    Fails if the catalogue is untracked/gitignored (the fresh-clone bug):
    a gitignored file is absent from ``git ls-files`` regardless of whether
    a working-tree copy exists.
    """
    repo_root = find_repo_root()
    catalogue = default_catalogue_path()

    # The path the production loader resolves, as a repo-relative POSIX path
    # (the exact form `git ls-files` emits).
    rel = catalogue.resolve().relative_to(repo_root.resolve()).as_posix()

    tracked = _git_tracked_paths(repo_root)
    assert rel in tracked, (
        f"the source-of-truth catalogue is NOT git-tracked ({rel!r} absent "
        f"from `git ls-files`) — a fresh clone cannot load the matrix. The "
        f"over-broad `data/` gitignore rule must be negated for this file."
    )

    # And the production entry-point parses the tracked file into the full
    # row set (a fresh clone can actually load the matrix).
    cat = load_catalogue(default_catalogue_path())
    assert cat.rows, "the catalogue must parse into a non-empty row set"
    # The two rows this cycle adds + the folded narration row are present
    # (the fresh clone sees the complete, current catalogue).
    ids = {r.id for r in cat.rows}
    assert "FM.PROCESS-DRIFT" in ids
    assert "FM.COMMS-PATH-DEAD" in ids
    assert "FM.NARRATION-NOT-ACTION" in ids


def test_AC_PMTRACK_1_tracked_catalogue_matches_the_resolved_default_path() -> None:
    """The tracked path IS the path the loader resolves by default.

    Guards against a fix that tracks a DIFFERENT copy than the one
    ``default_catalogue_path()`` reads (which would leave the fresh-clone
    bug live while the test passed against an unrelated tracked file).
    """
    repo_root = find_repo_root()
    catalogue = default_catalogue_path()
    rel = catalogue.resolve().relative_to(repo_root.resolve()).as_posix()
    assert rel == (
        "framework/protection-matrix/data/failure-mode-guard-matrix.yaml"
    ), (
        "the loader's default catalogue path drifted from the tracked file; "
        f"resolved {rel!r}"
    )
    # The loader, given no argument, reads exactly this path.
    cat = load_catalogue()
    assert cat.source_path.resolve() == catalogue.resolve()

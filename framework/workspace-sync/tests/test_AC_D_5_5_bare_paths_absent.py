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

"""D-migration D.5.5 — Cleanup of D.1's stale bare directories (Finding B).

Amendment #66. Verifies that the two stale pre-D.1 duplicate directories
that D.1 left tracked alongside their `framework/<name>/` counterparts
are absent from the git tree post-D.5.5, AND that the framework/
counterparts remain present (HC#4 counterpart preservation).

Background. D.1's commit (`0d599bb`) was supposed to be `git mv
<comp>/ → framework/<comp>/`. For most paths it was. For three top-
level paths — `tools/`, `workspace-sync/`, and `data/observability/
spans.jsonl` — D.1 effectively did `git cp` (added under `framework/`,
left the bare originals). The bare originals were frozen at pre-D.1
state and silently masked by the seal-diff tests' bare-prefix
admissions. D.5's audit (research note:
`.scratch/claude-output/d-migration-d5-audit-2026-04-26.md`) identified
this as Finding B; D.5.5 (this amendment) cleans it up.

This test asserts:
  - AC.D.5.5.1: bare `tools/` directory is absent; `framework/tools/`
    is present with content.
  - AC.D.5.5.2: bare `workspace-sync/` directory is absent;
    `framework/workspace-sync/` is present with content.

The third candidate (`data/observability/spans.jsonl`) is excluded
from D.5.5 per HC#4 strict reading: it has no `framework/` counterpart
(it's stale runtime test output, not a duplicate); see builder-plan
§0.A and the seal narrative for the surfacing record.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _has_tracked_files(path: Path) -> bool:
    """Return True iff *path* exists, is a directory, and contains
    any regular file in its subtree (not just empty subdirectories
    or hidden files)."""
    if not path.exists() or not path.is_dir():
        return False
    for entry in path.rglob("*"):
        if entry.is_file():
            return True
    return False


# ---- AC.D.5.5.1 — bare tools/ absent + framework/tools/ present ----


def test_AC_D_5_5_1_bare_tools_absent() -> None:
    """The bare top-level `tools/` directory does NOT exist post-D.5.5
    (or, defensively, exists but contains no tracked files).

    Pre-D.5.5: 109 files tracked under bare `tools/` (heavy-b-migrate,
    loam-mode, orphan-plist-cleanup, pos-amend, upgrade-merge-resolver).
    All retired in D.5.5.
    """
    bare_tools = REPO_ROOT / "tools"
    assert not _has_tracked_files(bare_tools), (
        f"bare top-level `tools/` directory still contains tracked files "
        f"after D.5.5: {bare_tools}. Expected absent or empty (the "
        f"directory was a stale pre-D.1 duplicate of framework/tools/ "
        f"and D.5.5 retires it)."
    )


def test_AC_D_5_5_1_framework_tools_present() -> None:
    """`framework/tools/` exists and contains the canonical tools-
    package source post-D.5.5 (HC#4 counterpart preservation).

    Post-M1g (2026-04-29): the `pos-amend` CLI was renamed and MOVED
    to `framework/tools/loam/` (with `loam amend` as a subcommand) per
    Idea 10 Tier-1 rebrand.

    Post-M6b.1 (2026-04-29): the `loam amend` package was MOVED to
    `plugins/dev-sdlc/tools/loam-amend/` (extraction into the Dev/SDLC
    plugin); the `loam` console-script + dispatcher STAY at
    `framework/tools/loam/`.

    Post-M6b.0 (2026-04-29): `framework/tools/loam-mode/` was MOVED to
    `plugins/dev-sdlc/tools/loam-mode/` (Dev/SDLC plugin extraction).

    Post-M9 (2026-04-29; this commit): the assertion below tightens to
    reflect the actual post-rename / post-extraction surface — the
    structural intent (tools-tree exists with representative
    canonical-survivor files) is preserved while the per-rename / per-
    move expected paths are updated. Per the loose-AC-fix-AC-not-
    implementation rule: the AC's intent is "tools-tree exists with
    canonical survivors"; only the named paths needed updating.
    """
    framework_tools = REPO_ROOT / "framework" / "tools"
    assert framework_tools.is_dir(), (
        f"framework/tools/ must exist post-D.5.5: {framework_tools}"
    )
    # Sample-check representative survivors. Post-M1g + M6b.0 + M6b.1:
    #   - framework/tools/loam/                   — unified CLI (post-M1g rename of pos-amend);
    #                                               loam amend MOVED to plugin at M6b.1
    #                                               (subcommand re-registers via entry-point).
    #   - framework/tools/heavy-b-migrate/        — Architecture-B migration tooling (still here).
    #   - framework/tools/orphan-plist-cleanup/   — DEV-mode launchd cleanup (still here).
    #   - framework/tools/upgrade-merge-resolver/ — self-upgrade internals (still here).
    #   - framework/tools/pos-publish-framework-only/ — synthesis tool
    #                                               (M2 partition; M9 substitution-pass extension).
    expected = (
        framework_tools / "loam" / "pyproject.toml",
        framework_tools / "loam" / "src" / "loam_cli" / "cli.py",
        framework_tools / "heavy-b-migrate" / "README.md",
        framework_tools / "orphan-plist-cleanup" / "pyproject.toml",
        framework_tools / "upgrade-merge-resolver" / "pyproject.toml",
        framework_tools
        / "pos-publish-framework-only"
        / "pyproject.toml",
    )
    missing = [p for p in expected if not p.is_file()]
    assert not missing, (
        f"framework/tools/ counterpart files missing post-D.5.5 "
        f"(updated post-M1g + M6b.0 + M6b.1 + M9 to reflect actual "
        f"post-rename surface): "
        f"{[str(p.relative_to(REPO_ROOT)) for p in missing]}"
    )


# ---- AC.D.5.5.2 — bare workspace-sync/ absent + framework/workspace-sync/ present


def test_AC_D_5_5_2_bare_workspace_sync_absent() -> None:
    """The bare top-level `workspace-sync/` directory does NOT exist
    post-D.5.5 (or, defensively, exists but contains no tracked files).

    Pre-D.5.5: 43 files tracked under bare `workspace-sync/` — the
    pre-D.1 source tree, including six D.3-retired modules
    (ancestor_detection.py, conflict_detection.py, conflict_report.py,
    merge_helper.py, merge_primitives.py, staging.py) plus their
    tests. All retired in D.5.5.
    """
    bare_ws_sync = REPO_ROOT / "workspace-sync"
    assert not _has_tracked_files(bare_ws_sync), (
        f"bare top-level `workspace-sync/` directory still contains "
        f"tracked files after D.5.5: {bare_ws_sync}. Expected absent "
        f"or empty (the directory was a stale pre-D.1 duplicate of "
        f"framework/workspace-sync/ and D.5.5 retires it)."
    )


def test_AC_D_5_5_2_framework_workspace_sync_present() -> None:
    """`framework/workspace-sync/` exists and contains the canonical
    workspace-sync source post-D.5.5 (HC#4 counterpart preservation).

    The framework/ version is the post-D.3 (`git fetch + git merge
    --ff-only`) shape — substantially advanced from the pre-D.1 bare
    version (which carried D.3-retired modules).
    """
    framework_ws_sync = REPO_ROOT / "framework" / "workspace-sync"
    assert framework_ws_sync.is_dir(), (
        f"framework/workspace-sync/ must exist post-D.5.5: "
        f"{framework_ws_sync}"
    )
    # Sample-check 5 known files survive (representative across src,
    # tests, seals, top-level metadata).
    expected = (
        framework_ws_sync / "pyproject.toml",
        framework_ws_sync / "src" / "loam" / "workspace_sync" / "cli.py",
        framework_ws_sync / "src" / "loam" / "workspace_sync" / "canonical.py",
        framework_ws_sync / "tests" / "test_no_sealed_amendments.py",
        framework_ws_sync / "tests" / "SEAL_COMMIT",
    )
    missing = [p for p in expected if not p.is_file()]
    assert not missing, (
        f"framework/workspace-sync/ counterpart files missing "
        f"post-D.5.5: {[str(p.relative_to(REPO_ROOT)) for p in missing]}"
    )

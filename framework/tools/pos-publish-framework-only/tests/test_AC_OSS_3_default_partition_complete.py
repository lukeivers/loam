"""AC.OSS-M2.4 — default partition is COMPLETE for canonical HEAD.

Per amendment #83 — M2 (publish-mode partition manifest +
synthesis tool extension): the default partition assignment in
``framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``
covers EVERY path under canonical HEAD's ``pos-v2`` branch, modulo
``audit_excludes``. This test runs `git ls-tree -r HEAD` against
the canonical repo (the test's working repo —
``Path(__file__).resolve().parents[5]``), filters by
``audit_excludes``, and asserts every remaining leaf classifies
into one of the four buckets.

If this test fails, the manifest needs more entries OR a class
definition needs adjustment — see plan §8 halt-trigger #7.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam.publish_framework_only.partition import (
    classify_path,
    is_audit_excluded,
    load_manifest,
)


CANONICAL_REPO = Path(__file__).resolve().parents[4]
CANONICAL_MANIFEST = (
    CANONICAL_REPO
    / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml"
)


def _git_ls_tree_recursive(repo: Path, ref: str) -> list[str]:
    """Return the list of leaf paths under ``ref``'s tree."""
    completed = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        line for line in completed.stdout.splitlines() if line.strip()
    ]


def _is_pos_v2_branch_present(repo: Path) -> bool:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--verify",
            "--quiet",
            "refs/heads/pos-v2",
        ],
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def test_default_partition_complete_for_canonical_head() -> None:
    """Every leaf under canonical HEAD's pos-v2 tree (modulo
    audit_excludes) classifies into one of the four buckets."""
    if not CANONICAL_MANIFEST.exists():
        pytest.skip(f"canonical manifest absent: {CANONICAL_MANIFEST}")
    if not _is_pos_v2_branch_present(CANONICAL_REPO):
        pytest.skip(
            f"canonical pos-v2 branch absent in {CANONICAL_REPO}; "
            "this test only runs against the canonical pos-v2 repo"
        )

    manifest = load_manifest(CANONICAL_MANIFEST)
    leaves = _git_ls_tree_recursive(CANONICAL_REPO, "pos-v2")
    assert leaves, "canonical pos-v2 has no tree leaves; fixture error"

    unclassified: list[str] = []
    for leaf in leaves:
        if is_audit_excluded(manifest, leaf):
            continue
        if classify_path(manifest, leaf) is None:
            unclassified.append(leaf)

    assert not unclassified, (
        f"{len(unclassified)} leaf path(s) under canonical pos-v2 "
        f"are unclassified by the default publish-mode partition; "
        f"first 10 samples: {unclassified[:10]!r}. The manifest at "
        f"{CANONICAL_MANIFEST} must cover every workspace path "
        "(per AC.OSS-M2.4)."
    )


def test_default_partition_classifies_runtime_components_dev_and_public() -> None:
    """Spot-check: a sampling of runtime framework components
    classify as dev_and_public."""
    if not CANONICAL_MANIFEST.exists():
        pytest.skip(f"canonical manifest absent: {CANONICAL_MANIFEST}")
    from loam.publish_framework_only.partition import PartitionClass

    manifest = load_manifest(CANONICAL_MANIFEST)
    # Post-M-FBM (memory-substrate pivot, 2026-05-01) per AC.MFBM.3:
    # ``framework/memory-system/**`` reclassifies to ``dev_only``
    # (file-based memory at framework/primary-persona/src/loam/
    # primary_persona/file_memory.py is the v0.1.0 default substrate;
    # graphiti retires to a post-v0.1.0 plugin via M-GMP). Removed
    # from this spot-check; covered by
    # test_default_partition_classifies_dev_tools_dev_only below.
    sample_runtime_paths = [
        "framework/cost-governance/src/loam/cost_governance/__init__.py",
        "framework/dormancy/src/loam/dormancy/__init__.py",
        "framework/primary-persona/src/loam/primary_persona/__init__.py",
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py",
        # framework/tools/loam/pyproject.toml RECLASSIFIED dev_and_public
        # at FBE.2 (v0.1.0 reviewer foldback; parent plan §4 FBE.2). The
        # unified loam CLI binary is the primary user-facing executable;
        # M2 lumping it with publish/migration tooling was wrong.
        "framework/tools/loam/pyproject.toml",
        # plugins/dev-sdlc user-facing surface SPLIT-ADMITTED to
        # dev_and_public at FBE.3 (v0.1.0 reviewer foldback; parent
        # plan §4 FBE.3 + §3 Decision B.2). The plugin src/ +
        # pyproject.toml + README.md ship publicly so a stranger can
        # `pip install -e plugins/dev-sdlc` against the synth tree.
        # Dev-discipline subtree (docs/, hooks/, templates/, tools/,
        # dev-mode-manifest.yaml) STAYS dev_only — covered by the
        # 4 explicit dev_only entries in sample_dev_only_paths below.
        "plugins/dev-sdlc/pyproject.toml",
        "plugins/dev-sdlc/README.md",
        "plugins/dev-sdlc/src/loam/plugins/dev_sdlc/api.py",
    ]
    for p in sample_runtime_paths:
        klass = classify_path(manifest, p)
        assert klass == PartitionClass.DEV_AND_PUBLIC, (
            f"runtime path {p!r} classifies as {klass!r}; "
            "expected DEV_AND_PUBLIC"
        )


def test_default_partition_classifies_dev_tools_dev_only() -> None:
    """Spot-check: dev-discipline tools classify as dev_only."""
    if not CANONICAL_MANIFEST.exists():
        pytest.skip(f"canonical manifest absent: {CANONICAL_MANIFEST}")
    from loam.publish_framework_only.partition import PartitionClass

    manifest = load_manifest(CANONICAL_MANIFEST)
    # Sample dev-only paths. Post-M6b.0:
    #  - loam-mode MOVED into the plugin (now at
    #    plugins/dev-sdlc/tools/loam-mode/, covered by the
    #    plugins/dev-sdlc/** glob).
    #  - long-form ODD docs MOVED into the plugin.
    #  - dev-mode-manifest.yaml MOVED into the plugin.
    # Post-M-FBM (memory-substrate pivot, 2026-05-01) per AC.MFBM.3:
    # ``framework/memory-system/**`` is now dev_only. The kuzu_db
    # inspection tool (D-Q.MFBM.6) ships dev_only.
    sample_dev_only_paths = [
        "framework/memory-system/src/loam/memory_system/__init__.py",
        # framework/tools/loam/pyproject.toml MOVED to
        # sample_runtime_paths above at FBE.2 (reclassification dev_only
        # → dev_and_public).
        "framework/tools/heavy-b-migrate/pyproject.toml",
        "framework/tools/loam-memory-inspect/pyproject.toml",
        "framework/tools/orphan-plist-cleanup/pyproject.toml",
        "framework/tools/pos-publish-framework-only/pyproject.toml",
        "docs/rebuild/STATE.md",
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "plugins/dev-sdlc/docs/odd-in-loam.md",
        "plugins/dev-sdlc/tools/loam-mode/pyproject.toml",
        "plugins/dev-sdlc/dev-mode-manifest.yaml",
        "CLAUDE.dev.md",
    ]
    for p in sample_dev_only_paths:
        klass = classify_path(manifest, p)
        assert klass == PartitionClass.DEV_ONLY, (
            f"dev-tool path {p!r} classifies as {klass!r}; "
            "expected DEV_ONLY"
        )

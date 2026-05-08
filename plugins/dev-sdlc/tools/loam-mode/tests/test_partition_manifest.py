"""AC.F1 + AC.F4 — manifest disjointness + glob-with-exclusion shape.

AC.F1 — load the manifest, assert the two sets are disjoint and that
every entry is well-formed (path-shape or glob-with-exclude).

AC.F4 — manifest parser correctly resolves a glob with an exclude
sub-tree (e.g. ``tools/**`` minus ``tools/loam/**``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_mode.audit import _resolve_set, _walk_audit_tree
from loam_mode.manifest import (
    ManifestEntry,
    expand_entry,
    load_manifest,
)


def test_AC_F1_partition_disjoint(real_manifest_path: Path, repo_root: Path) -> None:
    """The shipped ``plugins/dev-sdlc/dev-mode-manifest.yaml`` resolves
    to disjoint always-loaded and dev-only sets across the actual
    workspace tree."""
    manifest = load_manifest(real_manifest_path)
    candidates = _walk_audit_tree(
        repo_root, manifest.roots, manifest.audit_excludes
    )
    always = _resolve_set(manifest.always_loaded, repo_root, candidates)
    dev = _resolve_set(manifest.dev_only, repo_root, candidates)
    overlap = always & dev
    assert overlap == set(), (
        f"always_loaded ∩ dev_only must be empty; got {sorted(overlap)}"
    )


def test_AC_F1_entries_well_formed(real_manifest_path: Path) -> None:
    manifest = load_manifest(real_manifest_path)
    for entry in (*manifest.always_loaded, *manifest.dev_only):
        # __post_init__ enforces exactly-one-of(path, glob); just
        # asserting the dataclass invariants here.
        assert (entry.path is None) != (entry.glob is None)
        if entry.exclude:
            assert entry.glob is not None


def test_AC_F1_manifest_rejects_malformed_entry(tmp_path: Path) -> None:
    """A manifest entry that sets both path and glob is rejected."""
    bad = {
        "roots": ["src/"],
        "always_loaded": [{"path": "a.md", "glob": "**/*.md"}],
        "dev_only": [],
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="both path and glob"):
        load_manifest(p)


def test_AC_F4_glob_with_exclusion(tmp_path: Path) -> None:
    """``glob: tools/**`` with ``exclude: [tools/loam/**]``
    matches only the non-excluded sub-tree, regardless of fs state."""
    candidates = [
        "tools/loam-mode/src/loam_mode/cli.py",
        "tools/loam-mode/pyproject.toml",
        "tools/loam/src/loam_cli/amend/cli.py",
        "tools/loam/pyproject.toml",
        "tools/orphan-plist-cleanup/README.md",
        "docs/CLAUDE_CAPABILITIES.md",
    ]
    entry = ManifestEntry(
        glob="tools/**",
        exclude=("tools/loam/**",),
    )
    matched = expand_entry(entry, tmp_path, candidate_paths=candidates)
    assert matched == {
        "tools/loam-mode/src/loam_mode/cli.py",
        "tools/loam-mode/pyproject.toml",
        "tools/orphan-plist-cleanup/README.md",
    }


def test_AC_F4_glob_double_star_matches_recursively(tmp_path: Path) -> None:
    candidates = [
        "a.md",
        "docs/x.md",
        "docs/sub/y.md",
        "docs/sub/deep/z.md",
        "other/q.md",
    ]
    entry = ManifestEntry(glob="docs/**")
    matched = expand_entry(entry, tmp_path, candidate_paths=candidates)
    assert matched == {
        "docs/x.md",
        "docs/sub/y.md",
        "docs/sub/deep/z.md",
    }


def test_AC_F4_glob_without_double_star_uses_fnmatch(tmp_path: Path) -> None:
    candidates = ["a.md", "b.md", "sub/c.md"]
    entry = ManifestEntry(glob="*.md")
    matched = expand_entry(entry, tmp_path, candidate_paths=candidates)
    # Plain fnmatch — '*' does not cross '/' here because the
    # entry has no '**'.
    assert matched == {"a.md", "b.md"}

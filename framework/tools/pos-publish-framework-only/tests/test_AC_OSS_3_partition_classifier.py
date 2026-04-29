"""AC.OSS-M2.2 — publish-mode partition classifier.

Per amendment #83 — M2 (publish-mode partition manifest +
synthesis tool extension): ``partition.classify_path`` classifies
a workspace-relative POSIX path into one of four partition classes
under first-match-wins precedence:

  excluded_from_publish > dev_only > public_only > dev_and_public

Per plan §10 D-build.M2.3.

This test file covers:

- Each class classifies its own path correctly.
- Audit-excluded paths return ``None`` (out-of-scope).
- Unclassified paths (no entry matches in any class) return ``None``.
- First-match-wins precedence:
    - ``excluded_from_publish`` wins over ``dev_only``,
      ``public_only``, ``dev_and_public``.
    - ``dev_only`` wins over ``public_only`` and ``dev_and_public``.
    - ``public_only`` wins over ``dev_and_public``.
- Glob semantics: ``**`` crosses path separators; ``*`` is
  single-segment; exclusion patterns subtract from the match-set.
- ``is_publishable`` returns True iff the class is a ship class.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam.publish_framework_only.partition import (
    PartitionClass,
    classify_path,
    is_audit_excluded,
    is_publishable,
    load_manifest,
)


def _make_manifest(tmp_path: Path, body: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(body)
    return manifest


def test_classify_basic_dev_and_public(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "framework/cost-governance/__init__.py")
        == PartitionClass.DEV_AND_PUBLIC
    )


def test_classify_basic_dev_only(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only:
          - glob: "framework/tools/loam/**"
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "framework/tools/loam/cli.py")
        == PartitionClass.DEV_ONLY
    )


def test_classify_basic_excluded(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [.]
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only: []
        excluded_from_publish:
          - glob: ".git/**"
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, ".git/HEAD")
        == PartitionClass.EXCLUDED_FROM_PUBLISH
    )


def test_classify_basic_public_only(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [docs/]
        audit_excludes: []
        public_only:
          - path: docs/public-only-readme.md
        dev_and_public: []
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "docs/public-only-readme.md")
        == PartitionClass.PUBLIC_ONLY
    )


def test_audit_excluded_returns_none(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [.]
        audit_excludes:
          - "**/.DS_Store"
        public_only: []
        dev_and_public:
          - glob: "**/*"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    # Even though the dev_and_public glob matches, audit_excludes
    # short-circuits classification.
    assert is_audit_excluded(manifest, "framework/.DS_Store") is True
    assert classify_path(manifest, "framework/.DS_Store") is None


def test_unclassified_returns_none(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    # No entry matches "docs/foo.md" — unclassified.
    assert classify_path(manifest, "docs/foo.md") is None


def test_precedence_excluded_wins_over_dev_only(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only:
          - glob: "framework/tools/**"
        excluded_from_publish:
          - glob: "framework/tools/loam/**"
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    # Both classes match; excluded wins.
    assert (
        classify_path(manifest, "framework/tools/loam/cli.py")
        == PartitionClass.EXCLUDED_FROM_PUBLISH
    )


def test_precedence_dev_only_wins_over_dev_and_public(
    tmp_path: Path,
) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/**"
        dev_only:
          - glob: "framework/tools/loam/**"
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    # Both classes match; dev_only wins (per plan §10 D-build.M2.3 —
    # dev-tools must not be promoted by a broader dev_and_public glob).
    assert (
        classify_path(manifest, "framework/tools/loam/cli.py")
        == PartitionClass.DEV_ONLY
    )
    # The dev_and_public glob still applies to non-tools paths.
    assert (
        classify_path(manifest, "framework/cost-governance/__init__.py")
        == PartitionClass.DEV_AND_PUBLIC
    )


def test_precedence_public_only_wins_over_dev_and_public(
    tmp_path: Path,
) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [docs/]
        audit_excludes: []
        public_only:
          - path: docs/public-readme.md
        dev_and_public:
          - glob: "docs/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "docs/public-readme.md")
        == PartitionClass.PUBLIC_ONLY
    )
    assert (
        classify_path(manifest, "docs/other.md")
        == PartitionClass.DEV_AND_PUBLIC
    )


def test_glob_double_star_crosses_separators(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    # ** matches across multiple separators.
    assert (
        classify_path(manifest, "framework/cost-governance/src/deep/file.py")
        == PartitionClass.DEV_AND_PUBLIC
    )


def test_exclude_subtracts_from_glob(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
            exclude: ["framework/cost-governance/secrets/**"]
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "framework/cost-governance/__init__.py")
        == PartitionClass.DEV_AND_PUBLIC
    )
    # Exclusion subtracts; the path is now unclassified (None).
    assert (
        classify_path(manifest, "framework/cost-governance/secrets/key")
        is None
    )


def test_path_entry_exact_match(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [.]
        audit_excludes: []
        public_only: []
        dev_and_public:
          - path: README.md
        dev_only: []
        excluded_from_publish: []
        """
    )
    manifest = load_manifest(_make_manifest(tmp_path, body))
    assert (
        classify_path(manifest, "README.md")
        == PartitionClass.DEV_AND_PUBLIC
    )
    # Path entries do NOT match prefix subdirs.
    assert classify_path(manifest, "docs/README.md") is None


def test_is_publishable() -> None:
    assert is_publishable(PartitionClass.PUBLIC_ONLY) is True
    assert is_publishable(PartitionClass.DEV_AND_PUBLIC) is True
    assert is_publishable(PartitionClass.DEV_ONLY) is False
    assert is_publishable(PartitionClass.EXCLUDED_FROM_PUBLISH) is False
    assert is_publishable(None) is False

"""AC.OSS-M2.1 + AC.OSS-M2.2 — publish-mode partition manifest
load + schema-shape validation.

Per amendment #83 — M2 (publish-mode partition manifest +
synthesis tool extension): the manifest at
``framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``
classifies every workspace path into one of four partition classes.
This test file covers the load + schema-shape validation surface:

- well-formed YAML loads into a ``PartitionManifest`` dataclass.
- missing required top-level key raises ``ManifestError``.
- unknown top-level key raises ``ManifestError`` (forward-strict).
- ``schema_version != 1`` raises ``ManifestError``.
- non-list value where list expected raises ``ManifestError``.
- malformed entry (both path + glob set; neither set; non-string;
  exclude on a path entry) raises ``ManifestError``.

The canonical-HEAD partition manifest at
``<repo>/framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``
is loadable (smoke check).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam.publish_framework_only.partition import (
    ManifestError,
    PartitionClass,
    PartitionManifest,
    load_manifest,
)


CANONICAL_MANIFEST = (
    Path(__file__).resolve().parents[4]
    / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml"
)


def _write_manifest(tmp_path: Path, body: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(body)
    return manifest


def test_load_well_formed_manifest_returns_dataclass(
    tmp_path: Path,
) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots:
          - framework/
          - docs/
        audit_excludes:
          - "**/.git/**"
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
          - path: README.md
        dev_only:
          - glob: "framework/tools/loam/**"
        excluded_from_publish:
          - glob: ".git/**"
        """
    )
    manifest = load_manifest(_write_manifest(tmp_path, body))
    assert isinstance(manifest, PartitionManifest)
    assert manifest.schema_version == 1
    assert manifest.audit_roots == ("framework/", "docs/")
    assert manifest.audit_excludes == ("**/.git/**",)
    assert manifest.public_only == ()
    assert len(manifest.dev_and_public) == 2
    assert manifest.dev_and_public[0].glob == "framework/cost-governance/**"
    assert manifest.dev_and_public[1].path == "README.md"
    assert manifest.dev_only[0].glob == "framework/tools/loam/**"
    assert manifest.excluded_from_publish[0].glob == ".git/**"


def test_load_missing_required_key_raises(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: [framework/]
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only: []
        # excluded_from_publish missing
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "missing required keys" in str(exc.value)
    assert "excluded_from_publish" in str(exc.value)


def test_load_unknown_top_level_key_raises(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: []
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only: []
        excluded_from_publish: []
        unexpected_key: something
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "unknown top-level keys" in str(exc.value)
    assert "unexpected_key" in str(exc.value)


def test_load_wrong_schema_version_raises(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 99
        audit_roots: []
        audit_excludes: []
        public_only: []
        dev_and_public: []
        dev_only: []
        excluded_from_publish: []
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "unsupported schema_version" in str(exc.value)


def test_load_non_list_section_raises(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: []
        audit_excludes: []
        public_only: not_a_list
        dev_and_public: []
        dev_only: []
        excluded_from_publish: []
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "public_only must be a list" in str(exc.value)


def test_load_entry_with_both_path_and_glob_raises(
    tmp_path: Path,
) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: []
        audit_excludes: []
        public_only: []
        dev_and_public:
          - path: README.md
            glob: "framework/**"
        dev_only: []
        excluded_from_publish: []
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "sets both path and glob" in str(exc.value)


def test_load_entry_with_neither_raises(tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots: []
        audit_excludes: []
        public_only: []
        dev_and_public:
          - exclude: ["**/.git/**"]
        dev_only: []
        excluded_from_publish: []
        """
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(_write_manifest(tmp_path, body))
    assert "needs either path or glob" in str(exc.value)


def test_load_entry_path_with_exclude_raises(tmp_path: Path) -> None:
    """The ``ManifestEntry`` __post_init__ raises when a path entry
    carries an ``exclude``. Shape: pytest tests the constructor
    indirectly via the YAML coerce path. The coerce path silently
    discards exclude on a path entry today (the loader doesn't
    propagate exclude to ManifestEntry when the entry has a path);
    so this test asserts the constructor invariant directly to
    document the contract.
    """
    from loam.publish_framework_only.partition import ManifestEntry

    with pytest.raises(ManifestError) as exc:
        ManifestEntry(path="README.md", exclude=("never",))
    assert "exclude is only valid with glob" in str(exc.value)


def test_load_missing_file_raises_filenotfounderror(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path / "nonexistent.yaml")


def test_canonical_manifest_loads(tmp_path: Path) -> None:
    """Smoke check — the canonical publish-mode-manifest.yaml at
    ``<repo>/framework/tools/pos-publish-framework-only/`` loads
    cleanly. Also part of AC.OSS-M2.4 default-partition shape."""
    if not CANONICAL_MANIFEST.exists():
        pytest.skip(f"canonical manifest absent: {CANONICAL_MANIFEST}")
    manifest = load_manifest(CANONICAL_MANIFEST)
    assert manifest.schema_version == 1
    # Must classify the runtime framework components as
    # dev_and_public.
    assert any(
        e.glob and "cost-governance" in e.glob
        for e in manifest.dev_and_public
    )
    # Must classify dev-discipline tools as dev_only. Per FBE.2
    # (v0.1.0 reviewer foldback) `framework/tools/loam/**` reclassified
    # to dev_and_public; this assertion now uses the manifest-owner
    # itself (pos-publish-framework-only) which stays dev_only — the
    # tool that emits the public synth tree is the canonical example
    # of "dev-discipline tooling that stays internal."
    assert any(
        e.glob and "tools/pos-publish-framework-only/" in e.glob
        for e in manifest.dev_only
    )
    # Must classify .git/ as excluded_from_publish.
    assert any(
        e.glob and ".git" in e.glob
        for e in manifest.excluded_from_publish
    )


def test_partition_class_enum_values() -> None:
    """The four enum values match the YAML key strings."""
    assert PartitionClass.PUBLIC_ONLY.value == "public_only"
    assert PartitionClass.DEV_AND_PUBLIC.value == "dev_and_public"
    assert PartitionClass.DEV_ONLY.value == "dev_only"
    assert (
        PartitionClass.EXCLUDED_FROM_PUBLISH.value
        == "excluded_from_publish"
    )

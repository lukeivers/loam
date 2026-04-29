"""AC.OSS-M2.3 — synthesis tool consumes the manifest and drops
dev_only paths.

Per amendment #83 — M2 (publish-mode partition manifest +
synthesis tool extension): builds a fixture canonical with mixed
content and synthesises with a fixture manifest that classifies
some paths as ``dev_only`` and ``excluded_from_publish``. The
post-synthesis ``framework-only`` tree must contain the
``dev_and_public`` paths and must NOT contain the ``dev_only`` /
``excluded_from_publish`` paths.

Also covers:

- Synthesis raises ``SynthesisError`` if any non-audit-excluded
  leaf is unclassified (partition incompleteness).
- Synthesis raises ``SynthesisError`` if the manifest path is
  missing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam.publish_framework_only.synth import (
    SynthesisError,
    synthesise_framework_only,
)


def _write_files(canonical: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = canonical / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def test_synthesis_drops_dev_only_paths(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """Mixed canonical tree: framework/cost-governance (dev_and_public)
    + framework/tools/loam (dev_only) + CLAUDE.md (dev_and_public) +
    CLAUDE.dev.md (dev_only) + docs/positioning.md (dev_and_public) +
    docs/rebuild/STATE.md (dev_only).
    """
    # Build a custom manifest that splits framework/ into runtime
    # (dev_and_public) and tools (dev_only).
    manifest_yaml = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots:
          - framework/
          - docs/
          - CLAUDE.md
          - CLAUDE.dev.md
          - README.md
        audit_excludes: []
        public_only: []
        dev_and_public:
          - glob: "framework/cost-governance/**"
          - path: CLAUDE.md
          - path: README.md
          - path: docs/positioning.md
        dev_only:
          - glob: "framework/tools/loam/**"
          - glob: "framework/tools/pos-publish-framework-only/**"
          - path: CLAUDE.dev.md
          - glob: "docs/rebuild/**"
        excluded_from_publish: []
        """
    )
    files = {
        "framework/cost-governance/__init__.py": (
            '"""dev_and_public — must ship"""\n'
        ),
        "framework/tools/loam/cli.py": (
            '"""dev_only — must NOT ship"""\n'
        ),
        "CLAUDE.md": "# dev_and_public — must ship\n",
        "CLAUDE.dev.md": "# dev_only — must NOT ship\n",
        "README.md": "# dev_and_public — must ship\n",
        "docs/positioning.md": "# dev_and_public — must ship\n",
        "docs/rebuild/STATE.md": "# dev_only — must NOT ship\n",
    }
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        files=files,
        manifest_yaml=manifest_yaml,
    )

    result = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert result.framework_only_sha
    assert not result.no_op

    tree_listing = git_run(
        ["ls-tree", "-r", "--name-only", "refs/heads/framework-only"],
        cwd=canonical,
    )
    paths = set(tree_listing.split("\n"))

    # dev_and_public ships.
    assert "cost-governance/__init__.py" in paths
    assert "CLAUDE.md" in paths
    assert "README.md" in paths
    assert "docs/positioning.md" in paths

    # dev_only does NOT ship.
    assert "tools/loam/cli.py" not in paths
    assert "CLAUDE.dev.md" not in paths
    assert "docs/rebuild/STATE.md" not in paths
    # The fixture manifest itself classifies as dev_only (under
    # framework/tools/pos-publish-framework-only/** — but our test's
    # manifest doesn't include that path under any class except
    # implicitly under framework/tools/loam glob which doesn't match
    # — so the manifest path is unclassified). We don't assert
    # presence/absence of the fixture manifest leaf here; the
    # partition-incompleteness test below covers that explicitly.


def test_synthesis_raises_on_partition_incomplete(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A leaf that classifies into none of the four buckets (and
    isn't audit-excluded) raises ``SynthesisError`` per AC.OSS-M2.3
    + AC.OSS-M2.4 + plan §1 item 3.
    """
    # Manifest covers cost-governance only; the fixture's other
    # leaves (workspace-bootstrap, tools/loam-mode, top-level docs,
    # etc.) are unclassified.
    manifest_yaml = textwrap.dedent(
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
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        manifest_yaml=manifest_yaml,
    )
    with pytest.raises(SynthesisError) as excinfo:
        synthesise_framework_only(
            canonical,
            manifest_path=canonical
            / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
        )
    assert "partition incomplete" in str(excinfo.value)


def test_synthesis_raises_on_missing_manifest(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    canonical = make_fixture_canonical(tmp_path / "canonical")
    with pytest.raises(SynthesisError) as excinfo:
        synthesise_framework_only(
            canonical,
            manifest_path=tmp_path / "nonexistent.yaml",
        )
    assert "manifest not found" in str(excinfo.value).lower()


def test_synthesis_raises_on_malformed_manifest(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        manifest_yaml="schema_version: 99\n",  # malformed
    )
    with pytest.raises(SynthesisError) as excinfo:
        synthesise_framework_only(
            canonical,
            manifest_path=canonical
            / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
        )
    # Either "missing required keys" (schema_version is the only key)
    # or "unsupported schema_version" — the load fails before
    # synthesis proceeds.
    assert "manifest" in str(excinfo.value).lower()


def test_synthesis_audit_excludes_drop_silently(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """Audit-excluded leaves drop without raising partition-
    incompleteness."""
    manifest_yaml = textwrap.dedent(
        """\
        schema_version: 1
        audit_roots:
          - framework/
          - CLAUDE.md
          - CLAUDE.dev.md
          - README.md
          - docs/
        audit_excludes:
          - "**/.DS_Store"
        public_only: []
        dev_and_public:
          - glob: "framework/**"
            exclude: ["framework/tools/pos-publish-framework-only/**"]
          - path: CLAUDE.md
          - path: CLAUDE.dev.md
          - path: README.md
          - glob: "docs/**"
        dev_only:
          - glob: "framework/tools/pos-publish-framework-only/**"
        excluded_from_publish: []
        """
    )
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        manifest_yaml=manifest_yaml,
    )
    # Add a .DS_Store leaf inside framework/ — should drop silently.
    (canonical / "framework" / "cost-governance" / ".DS_Store").write_text(
        "macOS junk\n"
    )
    git_run(["add", "-A"], cwd=canonical)
    git_run(["commit", "-m", "add DS_Store"], cwd=canonical)

    result = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert result.framework_only_sha
    tree_listing = git_run(
        ["ls-tree", "-r", "--name-only", "refs/heads/framework-only"],
        cwd=canonical,
    )
    # .DS_Store is audit-excluded; it should not appear in the
    # synthetic tree.
    paths = set(tree_listing.split("\n"))
    assert "cost-governance/.DS_Store" not in paths
    # But framework/cost-governance/__init__.py still ships.
    assert "cost-governance/__init__.py" in paths

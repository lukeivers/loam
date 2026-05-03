"""AC.OSS-M9.2 — substitution pass runs AFTER the partition filter.

Per oss-v0-1-0-publish-scrub.md §4 AC.OSS-M9.2: builds a fixture
canonical that contains both a ``dev_only`` blob with a substitution
token AND a ``dev_and_public`` blob with the same token. Synthesises
with a fixture manifest. Asserts:

  (a) the ``dev_only`` blob is absent from the synthetic tree (the
      partition filter dropped it; the substitution pass never reached
      it).
  (b) the ``dev_and_public`` blob's tree entry SHA does NOT match the
      source SHA (the substitution pass rewrote the blob content).
  (c) the rewritten blob's content carries the replacement tokens, not
      the source tokens.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam.publish_framework_only.synth import synthesise_framework_only


def test_AC_OSS_M9_2_substitution_runs_after_partition(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """Mixed canonical: dev_only blob + dev_and_public blob both carry
    a substitution token. Only dev_and_public ships, and its content
    is rewritten."""
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
          - glob: "docs/**"
        dev_only:
          - glob: "framework/tools/loam/**"
          - glob: "framework/tools/pos-publish-framework-only/**"
          - path: CLAUDE.dev.md
        excluded_from_publish: []
        """
    )
    # Both blobs carry the substitution token "Luke Ivers". The
    # dev_only blob ALSO carries the token but should not ship.
    files = {
        "framework/cost-governance/__init__.py": (
            '"""dev_and_public — author Luke Ivers — must rewrite"""\n'
            'CANONICAL = "/Users/lukeivers/ivers-corp-pos-v2/foo"\n'
        ),
        "framework/tools/loam/cli.py": (
            '"""dev_only — author Luke Ivers — must NOT ship"""\n'
            'CANONICAL = "/Users/lukeivers/ivers-corp-pos-v2/bar"\n'
        ),
        "CLAUDE.md": "# fixture CLAUDE.md (no token)\n",
        "CLAUDE.dev.md": "# fixture CLAUDE.dev.md\n",
        "README.md": "# fixture README.md\n",
        "docs/positioning.md": "# fixture (no token)\n",
    }
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        files=files,
        manifest_yaml=manifest_yaml,
    )

    # Capture source blob SHAs.
    source_dev_and_public_sha = git_run(
        ["rev-parse", "HEAD:framework/cost-governance/__init__.py"],
        cwd=canonical,
    )
    source_dev_only_sha = git_run(
        ["rev-parse", "HEAD:framework/tools/loam/cli.py"],
        cwd=canonical,
    )

    result = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert result.framework_only_sha
    assert not result.no_op

    tree_listing = git_run(
        ["ls-tree", "-r", "refs/heads/framework-only"],
        cwd=canonical,
    )
    # Parse: each line is "<mode> <type> <sha>\t<path>".
    tree_entries: dict[str, str] = {}  # path → sha
    for line in tree_listing.split("\n"):
        if not line:
            continue
        head, _, name = line.partition("\t")
        _, _, sha = head.split(" ")
        tree_entries[name] = sha

    # (a) dev_only blob absent from synthetic tree. Per FBE.2b —
    # Decision D: tree-entry path assertions use the canonical
    # (prefix-preserved) path shape.
    assert "framework/tools/loam/cli.py" not in tree_entries
    # (b) dev_and_public blob present BUT with a different SHA than
    #     source — the substitution pass rewrote the content.
    assert "framework/cost-governance/__init__.py" in tree_entries
    synthetic_sha = tree_entries["framework/cost-governance/__init__.py"]
    assert synthetic_sha != source_dev_and_public_sha, (
        f"substitution did not change blob SHA for "
        f"framework/cost-governance/__init__.py — substitution pass not wired"
    )
    # Negative-control: dev_only's source SHA is preserved in the
    # canonical's history (we re-fetch it; not used for the synthetic
    # tree).
    assert source_dev_only_sha != synthetic_sha

    # (c) rewritten content carries replacement tokens, not source.
    rewritten_content = git_run(
        ["cat-file", "blob", synthetic_sha],
        cwd=canonical,
    )
    assert "Luke Ivers" not in rewritten_content
    assert "Alice Anderson" in rewritten_content
    assert "/Users/lukeivers/ivers-corp-pos-v2/" not in rewritten_content
    assert "<workspace>/loam/" in rewritten_content


def test_AC_OSS_M9_2_blob_without_token_preserves_sha(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """A dev_and_public blob with NO substitution token preserves its
    source SHA exactly (no rewrite, no new blob)."""
    canonical = make_fixture_canonical(tmp_path / "canonical")
    # The DEFAULT_FIXTURE_MANIFEST_YAML classifies everything dev_and_public.
    source_sha = git_run(
        ["rev-parse", "HEAD:framework/cost-governance/__init__.py"],
        cwd=canonical,
    )

    result = synthesise_framework_only(
        canonical,
        manifest_path=canonical
        / "framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml",
    )
    assert result.framework_only_sha

    tree_listing = git_run(
        ["ls-tree", "-r", "refs/heads/framework-only"],
        cwd=canonical,
    )
    tree_entries: dict[str, str] = {}
    for line in tree_listing.split("\n"):
        if not line:
            continue
        head, _, name = line.partition("\t")
        _, _, sha = head.split(" ")
        tree_entries[name] = sha

    # No token in source → SHA preserved verbatim. Per FBE.2b —
    # Decision D: tree-entry path uses the canonical (prefix-
    # preserved) shape.
    assert tree_entries["framework/cost-governance/__init__.py"] == source_sha

"""AC.OSS-M9.6 — smoke test: substitution pass produces clean
synthesis on a sample subset.

Per oss-v0-1-0-publish-scrub.md §4 AC.OSS-M9.6: builds a fixture
canonical that mirrors a reduced version of the live canonical
surface (~5 files chosen to span doc / source / test / README);
synthesises; greps the synthetic blobs; asserts zero hits on:

  - ``Luke Ivers``
  - ``lukeivers/pos-v2``
  - ``/Users/lukeivers/ivers-corp-pos-v2``

Verifies the four-entry SUBSTITUTION_TABLE is wired end-to-end.

Also covers AC.OSS-M9.1 (fixed-table-only — no host-specific data
outside the table) by indirectly asserting the table's effects.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam.publish_framework_only.substitution import SUBSTITUTION_TABLE
from loam.publish_framework_only.synth import synthesise_framework_only


def test_AC_OSS_M9_1_substitution_table_locked_to_four_entries() -> None:
    """Master plan §13 D-Q.OSS.6 locks the M9 base to four entries; the
    C2-prime amendment (§11 D-Q.ABC.4 + D-Q.ABC-prime.2) extends the
    table by 8 additional entries (3 + 5) to cover Class C production-
    file references — base 4 + 8 = 12 total. ODD §4 in-band rebaseline
    per `feedback_loose_AC_text_fix_AC_not_implementation` analog: the
    AC.OSS-M9.1 intent ("fixed-table-only — no host-specific data
    outside the table") is preserved; only the locked size grew.
    """
    assert len(SUBSTITUTION_TABLE) == 12
    sources = {src for src, _ in SUBSTITUTION_TABLE}
    # Base M9 entries (locked).
    assert "/Users/lukeivers/ivers-corp-pos-v2/" in sources
    assert "/Users/lukeivers/ivers-corp-pos-v2" in sources
    assert "lukeivers/pos-v2" in sources
    assert "Luke Ivers" in sources
    # C2-prime D-Q.ABC.4 entries (entries 5-7).
    assert "docs/rebuild/VALUE_PROPOSITION.md" in sources
    assert "docs/rebuild/spec/loam-objectives-spec.md" in sources
    assert "docs/odd-methodology.md" in sources
    # C2-prime D-Q.ABC-prime.2 entries (entries 8-12).
    assert "docs/odd-in-loam.md" in sources
    assert "plugins/dev-sdlc/docs/odd-methodology.md" in sources
    assert "plugins/dev-sdlc/docs/odd-in-loam.md" in sources
    assert "docs/rebuild/STATE.md" in sources
    assert "docs/rebuild/plans/" in sources
    # Idempotence (AC.OSS-M9.3): no replacement appears as a source.
    replacements = {repl for _, repl in SUBSTITUTION_TABLE}
    assert sources.isdisjoint(replacements), (
        f"AC.OSS-M9.3 idempotence violation: replacement appears as "
        f"source: {sources & replacements!r}"
    )


def test_AC_OSS_M9_6_smoke_synthesis_carries_zero_substitution_residuals(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """5-file fixture canonical mirrors the live shape (doc / source /
    test / README / config). Each file carries one or more substitution
    tokens. After synthesis, NO blob in the synthetic tree carries any
    of the four source tokens."""
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
          - glob: "framework/**"
            exclude: ["framework/tools/pos-publish-framework-only/**"]
          - path: CLAUDE.md
          - path: README.md
          - glob: "docs/**"
        dev_only:
          - glob: "framework/tools/pos-publish-framework-only/**"
          - path: CLAUDE.dev.md
        excluded_from_publish: []
        """
    )
    files = {
        # Source file with a path constant.
        "framework/cost-governance/__init__.py": (
            '"""cost-governance — author Luke Ivers."""\n'
            'CANONICAL_ROOT = "/Users/lukeivers/ivers-corp-pos-v2"\n'
            'FOO = "/Users/lukeivers/ivers-corp-pos-v2/foo/bar.py"\n'
        ),
        # README with shell example.
        "framework/workspace-bootstrap/README.md": (
            "# workspace-bootstrap\n\n"
            "```\ncd /Users/lukeivers/ivers-corp-pos-v2\n"
            "pos init .\n```\n\n"
            "Source: https://github.com/lukeivers/pos-v2\n"
        ),
        # Test fixture with a name field.
        "framework/dormancy/tests/test_fixture.py": (
            'NAME_FIXTURE = {"name": "Luke Ivers", "kind": "person"}\n'
        ),
        # Top-level CLAUDE.md (no token — verifies clean blobs preserve SHA).
        "CLAUDE.md": "# fixture CLAUDE.md (no token)\n",
        # README (no token).
        "README.md": "# fixture README\n",
        # docs (no token).
        "docs/positioning.md": "# fixture positioning\n",
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

    # Walk the synthetic tree's blobs and assert NO blob content
    # carries any source token.
    tree_listing = git_run(
        ["ls-tree", "-r", "refs/heads/framework-only"], cwd=canonical
    )
    blob_shas: list[tuple[str, str]] = []  # (path, sha)
    for line in tree_listing.split("\n"):
        if not line:
            continue
        head, _, name = line.partition("\t")
        _, obj_type, sha = head.split(" ")
        if obj_type == "blob":
            blob_shas.append((name, sha))
    assert blob_shas, "synthetic tree had no blobs — fixture broken"

    forbidden_tokens = (
        "Luke Ivers",
        "lukeivers/pos-v2",
        "/Users/lukeivers/ivers-corp-pos-v2",
    )
    residuals: list[tuple[str, str]] = []  # (path, token)
    for path, sha in blob_shas:
        content = git_run(["cat-file", "blob", sha], cwd=canonical)
        for token in forbidden_tokens:
            if token in content:
                residuals.append((path, token))

    assert not residuals, (
        f"substitution residuals found in synthetic tree: {residuals!r}"
    )

    # Positive: at least one synthesised blob carries the replacement
    # tokens (sanity — confirms substitution actually ran).
    rewritten_paths = []
    for path, sha in blob_shas:
        content = git_run(["cat-file", "blob", sha], cwd=canonical)
        if "Alice Anderson" in content or "<workspace>/loam" in content:
            rewritten_paths.append(path)
    assert rewritten_paths, (
        "no blob in synthetic tree carried replacement tokens — "
        "substitution may not have been wired"
    )

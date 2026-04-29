"""AC.SFR.2 — canonical publishes a `framework-only` branch in
lockstep with the primary `pos-v2` branch.

Each test in this file constructs a fixture canonical with a `pos-v2`
branch, runs the synthesis, and asserts:

- the `framework-only` ref exists post-synthesis;
- its tree promotes `framework/<entry>` entries to root (no nested
  `framework/` subdir);
- top-level docs (`CLAUDE.md`, `CLAUDE.dev.md`, `README.md`, `docs/`)
  are present at the synthetic-branch root verbatim;
- after a follow-on `pos-v2` commit, re-running synthesis produces a
  new `framework-only` commit whose parent is the prior `framework-
  only` tip (lockstep / fast-forward graph).

HC#4 binding: byte-content match between source and synthesised tree
contents.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.publish_framework_only.synth import (
    SynthesisError,
    synthesise_framework_only,
)


def test_AC_SFR_2_synthesis_creates_framework_only_branch(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """The synthesis advances `framework-only` to a new commit whose
    tree promotes framework/ entries to root and carries top-level
    docs verbatim.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    result = synthesise_framework_only(canonical)

    assert result.framework_only_sha
    assert result.target_ref == "refs/heads/framework-only"
    assert not result.no_op

    # framework-only ref exists.
    framework_only_sha = git_run(
        ["rev-parse", "--verify", "refs/heads/framework-only"], cwd=canonical
    )
    assert framework_only_sha == result.framework_only_sha

    # framework/<entries> promoted to root.
    tree_listing = git_run(
        ["ls-tree", "-r", "--name-only", "refs/heads/framework-only"],
        cwd=canonical,
    )
    paths = set(tree_listing.split("\n"))

    # AC.SFR.2 (a): components promoted to root.
    assert "cost-governance/__init__.py" in paths
    assert "workspace-bootstrap/src/__init__.py" in paths
    assert "tools/loam-mode/__init__.py" in paths

    # AC.SFR.2 (a): no doubled framework/ prefix.
    assert "framework/cost-governance/__init__.py" not in paths
    assert all(not p.startswith("framework/") for p in paths)

    # AC.SFR.2 (b): top-level docs verbatim.
    assert "CLAUDE.md" in paths
    assert "CLAUDE.dev.md" in paths
    assert "README.md" in paths
    assert "docs/odd-methodology.md" in paths
    assert "docs/rebuild/STATE.md" in paths


def test_AC_SFR_2_HC4_byte_content_match(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """HC#4 binding — every entry in the synthesised tree byte-equals
    its source on `pos-v2`."""
    canonical = make_fixture_canonical(tmp_path / "canonical")
    synthesise_framework_only(canonical)

    pairs = [
        ("framework/cost-governance/__init__.py",
         "cost-governance/__init__.py"),
        ("framework/workspace-bootstrap/src/__init__.py",
         "workspace-bootstrap/src/__init__.py"),
        ("framework/tools/loam-mode/__init__.py",
         "tools/loam-mode/__init__.py"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CLAUDE.dev.md", "CLAUDE.dev.md"),
        ("README.md", "README.md"),
        ("docs/odd-methodology.md", "docs/odd-methodology.md"),
        ("docs/rebuild/STATE.md", "docs/rebuild/STATE.md"),
    ]
    for source_rel, fo_rel in pairs:
        source_bytes = git_run(
            ["show", f"pos-v2:{source_rel}"], cwd=canonical
        )
        fo_bytes = git_run(
            ["show", f"refs/heads/framework-only:{fo_rel}"], cwd=canonical
        )
        assert source_bytes == fo_bytes, (
            f"HC#4 mismatch: {source_rel!r} vs {fo_rel!r}"
        )


def test_AC_SFR_2_lockstep_advances_with_pos_v2(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """After a follow-on `pos-v2` commit, re-synthesis advances
    `framework-only` to a new commit whose parent is the prior
    `framework-only` tip (lockstep ff-graph).
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")

    first = synthesise_framework_only(canonical)

    # Make a new commit on pos-v2.
    (canonical / "framework" / "cost-governance" / "added.py").write_text(
        "# new file\n"
    )
    git_run(["add", "-A"], cwd=canonical)
    git_run(["commit", "-m", "second commit"], cwd=canonical)

    second = synthesise_framework_only(canonical)
    assert not second.no_op
    assert second.framework_only_sha != first.framework_only_sha

    # framework-only's new tip's parent must be first's tip
    # (fast-forward graph).
    parent_sha = git_run(
        ["rev-parse", f"{second.framework_only_sha}^"], cwd=canonical
    )
    assert parent_sha == first.framework_only_sha

    # The new file appears at root in framework-only's tree.
    new_listing = git_run(
        ["ls-tree", "-r", "--name-only", "refs/heads/framework-only"],
        cwd=canonical,
    )
    assert "cost-governance/added.py" in new_listing.split("\n")


def test_AC_SFR_2_idempotent_re_run(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """Re-running synthesis on the same `pos-v2` commit is a no-op."""
    canonical = make_fixture_canonical(tmp_path / "canonical")

    first = synthesise_framework_only(canonical)
    second = synthesise_framework_only(canonical)

    assert second.no_op is True
    assert second.framework_only_sha == first.framework_only_sha


def test_AC_SFR_5_pos_v2_branch_unchanged_post_synthesis(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """AC.SFR.5 — synthesis MUST NOT touch the `pos-v2` branch.

    Stranger-clones-canonical property: a fresh clone of canonical's
    primary `pos-v2` branch must be byte-identical pre and post
    synthesis. This test asserts the synthesis does NOT mutate
    `pos-v2`'s tip / tree.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    pre_sha = git_run(["rev-parse", "pos-v2"], cwd=canonical)
    pre_tree = git_run(
        ["ls-tree", "-r", "--name-only", "pos-v2"], cwd=canonical
    )

    synthesise_framework_only(canonical)

    post_sha = git_run(["rev-parse", "pos-v2"], cwd=canonical)
    post_tree = git_run(
        ["ls-tree", "-r", "--name-only", "pos-v2"], cwd=canonical
    )

    assert pre_sha == post_sha, (
        "synthesis advanced `pos-v2` (must not). pre=%r post=%r"
        % (pre_sha, post_sha)
    )
    assert pre_tree == post_tree


def test_AC_SFR_5_stranger_clone_byte_identical_to_pos_v2(
    tmp_path: Path,
    make_fixture_canonical,
    git_run,
) -> None:
    """AC.SFR.5 — `git clone <canonical>` (no --branch) is byte-
    identical to canonical's `pos-v2` tree.

    The synthesis pipeline runs against canonical; a stranger doing
    `git clone <canonical-url>` (default branch == `pos-v2`) must see
    canonical's full pos-v2 tree (framework/ + top-level docs +
    everything else) without needing to know about framework-only or
    the synthesis script.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    synthesise_framework_only(canonical)

    # `pos-v2` is the default branch in the fixture (per
    # `--initial-branch=pos-v2`). A no-flag clone fetches and checks
    # out the default branch.
    stranger_clone = tmp_path / "stranger-clone"
    git_run(
        ["clone", str(canonical), str(stranger_clone)],
        cwd=tmp_path,
    )
    cloned_tree = git_run(
        ["ls-tree", "-r", "--name-only", "HEAD"], cwd=stranger_clone
    )
    canonical_tree = git_run(
        ["ls-tree", "-r", "--name-only", "pos-v2"], cwd=canonical
    )
    assert cloned_tree == canonical_tree

    # And the workspace-side files match byte-for-byte.
    for rel in [
        "CLAUDE.md",
        "framework/cost-governance/__init__.py",
        "docs/rebuild/STATE.md",
    ]:
        assert (stranger_clone / rel).read_text() == (
            canonical / rel
        ).read_text()


def test_synthesis_fails_when_framework_subdir_absent(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """A source commit with no `framework/` subdir raises."""
    canonical = make_fixture_canonical(
        tmp_path / "canonical",
        files={
            "CLAUDE.md": "# fixture\n",
            "README.md": "# README\n",
            "docs/foo.md": "# foo\n",
        },
    )
    with pytest.raises(SynthesisError) as excinfo:
        synthesise_framework_only(canonical)
    assert "no entries under framework/" in str(excinfo.value)

"""AC.BACKFL — Post-publish auto-backfill (v0.7.3).

Verifies the post-tag-push state-sync step that promotes
``SHIPPED LOCAL`` rows in ``docs/STATE.md`` and
``docs/release-roadmap.md`` to ``SHIPPED PUBLIC`` after a successful
``loam release``. Closes the recurring manual-backfill defect (commits
``f0ae00c`` for v0.7.2, ``af73a69`` for v0.7.1, similar at v0.6.0 /
v0.7.0).

Test classes:

- AC.BACKFL.{1,2,3} — function-altitude tests against
  :func:`loam_cli.release.post_publish_backfill.apply_backfill` with
  inline doc fixtures (STATE.md / release-roadmap.md as plain
  strings) so each AC is testable in isolation.
- AC.BACKFL.{4,5} — idempotence + dry-run + runner integration.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path

import pytest

from loam_cli.release import post_publish_backfill, runner


# --------------------------------------------------------------------
# Inline fixture builders for the function-altitude tests.
# --------------------------------------------------------------------


def _state_md_with_shipped_local(
    version: str = "v0.9.0",
    *,
    with_v074_gap_surfaces: bool = False,
) -> str:
    """STATE.md body with the canonical SHIPPED-LOCAL trailing claim
    for *version* (matches the f0ae00c pre-image shape).

    When *with_v074_gap_surfaces* is True, the row body carries the
    canonical pre-publish v0.7.4 placeholders ``TBD-AT-COMMIT`` /
    ``TBD-AT-APPLY`` / ``TBD-AT-SEAL`` rather than hand-authored
    bbbbbbb/ccccccc/ddddddd literal SHAs. Used by AC.BACKFL2.{2,3}
    tests that exercise the placeholder backfill paths.
    """
    if with_v074_gap_surfaces:
        sha_clause = (
            "Plan-doc `aaaaaaa`; source-edit TBD-AT-COMMIT; "
            "apply TBD-AT-APPLY; seal TBD-AT-SEAL"
        )
    else:
        sha_clause = (
            "Plan-doc `aaaaaaa`; source-edit `bbbbbbb`; "
            "apply `ccccccc`; seal `ddddddd`"
        )
    return (
        "# State\n\n"
        "Some preamble prose.\n\n"
        "- **2026-05-09** — **v0.8.9 PATCH SHIPPED PUBLIC** — predecessor "
        "row.\n"
        f"- **2026-05-10** — **{version} PATCH SHIPPED LOCAL** — "
        "release-CLI auto-backfill defect-closure for v0.6.0's shipped "
        f"release-process. {sha_clause}. {version} SHIPPED LOCAL — "
        "owner gates publish.\n"
    )


def _state_md_already_public(version: str = "v0.9.0") -> str:
    """STATE.md body where *version* already carries the full
    post-v0.7.4 SHIPPED-PUBLIC state (leading title flipped per
    AC.BACKFL2.1 + trailing-sentence marker per AC.BACKFL.1 +
    no residual TBD-AT-* placeholders per AC.BACKFL2.{2,3}).

    Used as the canonical idempotence-case fixture: re-running
    apply_backfill against this state should be a clean no-op
    (per AC.BACKFL.4 + AC.BACKFL2.4).
    """
    return (
        "# State\n\n"
        f"- **2026-05-10** — **{version} PATCH SHIPPED PUBLIC** — work. "
        f"Seal `ddddddd`. **{version} SHIPPED PUBLIC 2026-05-10 at tag "
        f"`{version}` (annotated `eeeeeee`)**.\n"
    )


def _roadmap_with_shipped_local_row(
    version: str = "v0.9.0",
    *,
    with_v074_gap_surfaces: bool = False,
) -> str:
    """release-roadmap.md body with §2 row + §3 + summary line in
    pre-publish state for *version*.

    When *with_v074_gap_surfaces* is True, the §2 row carries the
    canonical pre-publish v0.7.4 placeholders ``TBD-AT-COMMIT`` /
    ``TBD-AT-APPLY`` / ``TBD-AT-SEAL`` rather than literal SHAs.
    """
    if with_v074_gap_surfaces:
        third_cell = (
            "Single-cycle PATCH: plan-doc `aaaaaaa`; "
            "source-edit TBD-AT-COMMIT; apply TBD-AT-APPLY; "
            "seal TBD-AT-SEAL"
        )
    else:
        third_cell = (
            "Single-cycle PATCH: plan-doc `aaaaaaa`; "
            "source-edit `bbbbbbb`; apply `ccccccc`; seal `ddddddd`"
        )
    return (
        "# Release Roadmap\n\n"
        "## §2 Shipped\n\n"
        "Pulled from `docs/STATE.md`.\n\n"
        "| Version | Objective sentence | Anchor |\n"
        "|---|---|---|\n"
        "| v0.8.9 | Predecessor objective for cumulative count. | "
        "Single-cycle PATCH: seal `aaaaaaa`; **SHIPPED PUBLIC 2026-05-09 "
        "at tag `v0.8.9` (annotated `bbbbbbb`)** |\n"
        f"| {version} | Loam closes the recurring post-publish state-"
        "staleness defect via auto-backfill in the release CLI. The defect "
        f"bit at every publish since v0.6.0. | {third_cell} |\n"
        "\n"
        "**Total shipped:** 18 minor + 8 patches. v0.8.9 published. "
        "Editorial prose summary unchanged.\n\n"
        "---\n\n"
        "## §3 Active version\n\n"
        "v0.8.9 SHIPPED PUBLIC 2026-05-09 (tag `v0.8.9`, annotated "
        "`bbbbbbb`; seal `aaaaaaa`).\n\n"
        "---\n\n"
        "## §4 Mapped versions (next → v1.0.0)\n\n"
        "Next entries below.\n"
    )


# --------------------------------------------------------------------
# AC.BACKFL.1 — STATE.md + roadmap row backfill.
# --------------------------------------------------------------------


def test_apply_backfill_promotes_state_md_shipped_local_to_public(
    tmp_path: Path,
) -> None:
    """STATE.md trailing-claim flips to SHIPPED-PUBLIC marker."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    state_md_body = (docs / "STATE.md").read_text(encoding="utf-8")
    assert (
        "**v0.9.0 SHIPPED PUBLIC 2026-05-11 at tag `v0.9.0` "
        "(annotated `abc1234`)**"
    ) in state_md_body, state_md_body
    # The original SHIPPED-LOCAL trailing-claim sentence must be gone.
    assert "v0.9.0 SHIPPED LOCAL — owner gates publish." not in state_md_body
    assert result.edits_applied >= 1
    assert (docs / "STATE.md") in result.files_touched


def test_apply_backfill_appends_roadmap_row_marker(
    tmp_path: Path,
) -> None:
    """release-roadmap.md §2 row gets the SHIPPED-PUBLIC marker."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    roadmap = (docs / "release-roadmap.md").read_text(encoding="utf-8")
    assert (
        "**SHIPPED PUBLIC 2026-05-11 at tag `v0.9.0` "
        "(annotated `abc1234`)**"
    ) in roadmap, roadmap


# --------------------------------------------------------------------
# AC.BACKFL.2 — aggregate-count summary line update.
# --------------------------------------------------------------------


def test_apply_backfill_updates_aggregate_count_summary(
    tmp_path: Path,
) -> None:
    """``**Total shipped:**`` line increments + flips trailing
    ``v<prev> published`` claim."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    roadmap = (docs / "release-roadmap.md").read_text(encoding="utf-8")
    # Two rows now carry SHIPPED PUBLIC markers (v0.8.9 + v0.9.0); both
    # are PATCH per their third-cell `Single-cycle PATCH` text. So
    # the new summary line should show 0 minor + 2 patches.
    assert "**Total shipped:** 0 minor + 2 patches. v0.9.0 published." in roadmap, roadmap
    # The old summary line shape is gone.
    assert "**Total shipped:** 18 minor + 8 patches. v0.8.9 published." not in roadmap


# --------------------------------------------------------------------
# AC.BACKFL.3 — §3 Active Version new bold entry.
# --------------------------------------------------------------------


def test_apply_backfill_appends_section_3_active_version_entry(
    tmp_path: Path,
) -> None:
    """A new bold entry for *version* lands in §3 body."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    roadmap = (docs / "release-roadmap.md").read_text(encoding="utf-8")
    assert "**v0.9.0 PATCH" in roadmap
    assert "SHIPPED PUBLIC 2026-05-11**" in roadmap
    assert "tag `v0.9.0`, annotated `abc1234`; seal `ddddddd`" in roadmap


# --------------------------------------------------------------------
# AC.BACKFL.4 — Idempotence (re-run is a no-op).
# --------------------------------------------------------------------


def test_apply_backfill_is_noop_when_state_already_public(
    tmp_path: Path,
) -> None:
    """When STATE.md already carries the SHIPPED-PUBLIC marker AND the
    roadmap row already has the marker AND the summary line + §3 entry
    are current, the function returns idempotent_noop=True with no
    edits."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_already_public("v0.9.0"))
    # Roadmap with the row already marked + summary already current +
    # §3 already carrying the entry. Build it inline so we can be
    # explicit about the idempotence pre-image.
    (docs / "release-roadmap.md").write_text(
        "# Release Roadmap\n\n"
        "## §2 Shipped\n\n"
        "| Version | Objective sentence | Anchor |\n"
        "|---|---|---|\n"
        "| v0.9.0 | Loam ships v0.9.0. | Single-cycle PATCH: seal "
        "`ddddddd`; **SHIPPED PUBLIC 2026-05-11 at tag `v0.9.0` "
        "(annotated `abc1234`)** |\n"
        "\n"
        "**Total shipped:** 0 minor + 1 patch. v0.9.0 published.\n\n"
        "---\n\n"
        "## §3 Active version\n\n"
        "**v0.9.0 PATCH (Loam ships v0.9.0.) SHIPPED PUBLIC 2026-05-11** "
        "(tag `v0.9.0`, annotated `abc1234`; seal `ddddddd`).\n\n"
        "---\n"
    )
    today = _dt.date(2026, 5, 11)
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    assert result.idempotent_noop is True, result
    assert result.edits_applied == 0
    assert result.files_touched == []


def test_apply_backfill_is_noop_on_re_run(tmp_path: Path) -> None:
    """First call applies edits; second call (with identical inputs)
    is fully idempotent (no further edits, no further file writes)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    r1 = post_publish_backfill.apply_backfill(
        tmp_path, "v0.9.0", "v0.9.0", "abc1234567890def", today=today
    )
    assert r1.edits_applied >= 1
    state_md_after = (docs / "STATE.md").read_text(encoding="utf-8")
    roadmap_after = (docs / "release-roadmap.md").read_text(encoding="utf-8")
    r2 = post_publish_backfill.apply_backfill(
        tmp_path, "v0.9.0", "v0.9.0", "abc1234567890def", today=today
    )
    assert r2.idempotent_noop is True
    assert r2.edits_applied == 0
    assert (docs / "STATE.md").read_text(encoding="utf-8") == state_md_after
    assert (docs / "release-roadmap.md").read_text(encoding="utf-8") == roadmap_after


# --------------------------------------------------------------------
# AC.BACKFL.5 — dry-run + runner-integration tests.
# --------------------------------------------------------------------


def test_apply_backfill_dry_run_mutates_nothing_on_disk(
    tmp_path: Path,
) -> None:
    """``dry_run=True`` returns the proposed edits as strings but does
    NOT write to disk."""
    docs = tmp_path / "docs"
    docs.mkdir()
    state_pre = _state_md_with_shipped_local("v0.9.0")
    roadmap_pre = _roadmap_with_shipped_local_row("v0.9.0")
    (docs / "STATE.md").write_text(state_pre)
    (docs / "release-roadmap.md").write_text(roadmap_pre)
    today = _dt.date(2026, 5, 11)
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
        dry_run=True,
    )
    assert result.edits_applied >= 1
    assert result.state_md_edit is not None
    assert "SHIPPED PUBLIC" in result.state_md_edit
    # Files unchanged on disk.
    assert (docs / "STATE.md").read_text(encoding="utf-8") == state_pre
    assert (docs / "release-roadmap.md").read_text(encoding="utf-8") == roadmap_pre
    assert result.files_touched == []


def test_format_backfill_preview_renders_named_edits(
    tmp_path: Path,
) -> None:
    """The dry-run preview renders the per-file edits as
    human-readable lines."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(_state_md_with_shipped_local("v0.9.0"))
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=_dt.date(2026, 5, 11),
        dry_run=True,
    )
    text = post_publish_backfill.format_backfill_preview(result)
    assert "DRY-RUN: would apply post-publish backfill" in text
    assert f"{result.edits_applied} edit(s)" in text
    assert "STATE.md" in text or "roadmap" in text


# --------------------------------------------------------------------
# Runner integration — the post-publish commit lands on the local
# remote with the canonical message.
# --------------------------------------------------------------------


@pytest.fixture
def staged_repo_with_shipped_local_state(
    staged_repo: Path, fixture_version: str
) -> Path:
    """Extend the existing :func:`staged_repo` fixture's STATE.md +
    roadmap to carry the canonical SHIPPED-LOCAL trailing-claim shape
    so the runner-integration tests exercise a real backfill (not the
    no-op no-pattern-match path)."""
    docs = staged_repo / "docs"
    # Append the SHIPPED-LOCAL trailing-claim sentence to STATE.md so
    # the backfill function has a target to flip.
    state_md = docs / "STATE.md"
    body = state_md.read_text(encoding="utf-8")
    body += (
        f"\n- **2026-05-10** — **{fixture_version} MINOR SHIPPED LOCAL** "
        f"— work. Seal `eeeeeee`. {fixture_version} SHIPPED LOCAL — "
        "owner gates publish.\n"
    )
    state_md.write_text(body, encoding="utf-8")
    subprocess.run(
        ["git", "add", "docs/STATE.md"], cwd=staged_repo, check=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "extend STATE.md for backfill test"],
        cwd=staged_repo,
        check=True,
    )
    return staged_repo


@pytest.fixture
def repo_with_local_remote_and_shipped_local(
    staged_repo_with_shipped_local_state: Path, tmp_path: Path
) -> Path:
    """Wire the extended fixture to a local bare ``origin``."""
    bare = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
        check=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(bare)],
        cwd=staged_repo_with_shipped_local_state,
        check=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", "main"],
        cwd=staged_repo_with_shipped_local_state,
        check=True,
    )
    return staged_repo_with_shipped_local_state


def test_runner_invokes_backfill_after_tag_push(
    repo_with_local_remote_and_shipped_local: Path,
    fixture_version: str,
) -> None:
    """The full publish flow invokes :func:`apply_backfill` and lands
    a follow-on commit with the canonical message on the local
    remote."""
    out = runner.run(
        repo_with_local_remote_and_shipped_local,
        fixture_version,
        dry_run=False,
        create_release=False,
    )
    assert out.rc == 0
    assert out.tag_pushed is True
    assert out.backfill is not None
    assert out.backfill.edits_applied >= 1
    assert out.backfill_committed is True
    assert out.backfill_pushed is True
    # The post-publish commit is the new HEAD; check the message.
    proc = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=repo_with_local_remote_and_shipped_local,
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        f"docs(release): {fixture_version} post-publish backfill"
        in proc.stdout
    )


def test_runner_dry_run_emits_backfill_preview(
    repo_with_local_remote_and_shipped_local: Path,
    fixture_version: str,
    capsys,
) -> None:
    """``--dry-run`` mode emits the dry-run backfill preview block in
    stdout (AC.BACKFL.6 outcome-altitude shape)."""
    out = runner.run(
        repo_with_local_remote_and_shipped_local,
        fixture_version,
        dry_run=True,
        create_release=False,
    )
    captured = capsys.readouterr()
    assert out.rc == 0
    assert "DRY-RUN: would apply post-publish backfill" in captured.out
    # No commit was made.
    assert out.backfill_committed is False
    assert out.backfill_pushed is False


def test_runner_idempotent_re_run_skips_backfill_commit(
    repo_with_local_remote_and_shipped_local: Path,
    fixture_version: str,
) -> None:
    """Re-running the publish flow on already-published state runs
    the backfill function (in case prior run failed mid-flight) but
    skips the commit when no edits are needed."""
    # First run: publishes + backfills.
    runner.run(
        repo_with_local_remote_and_shipped_local,
        fixture_version,
        dry_run=False,
        create_release=False,
    )
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_with_local_remote_and_shipped_local,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    # Second run: tag exists on remote → idempotent-noop branch; no
    # new backfill edits because state is already current; no
    # additional commit.
    out2 = runner.run(
        repo_with_local_remote_and_shipped_local,
        fixture_version,
        dry_run=False,
        create_release=False,
    )
    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_with_local_remote_and_shipped_local,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert out2.idempotent_noop is True
    assert out2.backfill is not None
    assert out2.backfill.idempotent_noop is True
    assert out2.backfill.edits_applied == 0
    assert out2.backfill_committed is False
    assert out2.backfill_pushed is False
    # HEAD did not advance (no extra commit).
    assert head_before == head_after


# --------------------------------------------------------------------
# AC.BACKFL2.1 — leading-title flip in STATE.md.
# --------------------------------------------------------------------


def test_apply_backfill_flips_state_md_leading_title(
    tmp_path: Path,
) -> None:
    """The bolded leading title ``**vX.Y.Z PATCH SHIPPED LOCAL**``
    flips to ``**vX.Y.Z PATCH SHIPPED PUBLIC**`` (preserves CLASS
    casing). v0.7.3's auto-backfill missed this surface; v0.7.4
    closes the gap (AC.BACKFL2.1)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(
        _state_md_with_shipped_local("v0.9.0")
    )
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    state_md = (docs / "STATE.md").read_text(encoding="utf-8")
    # Leading title flipped (with CLASS preserved).
    assert "**v0.9.0 PATCH SHIPPED PUBLIC**" in state_md, state_md
    # Original SHIPPED-LOCAL leader is gone.
    assert "**v0.9.0 PATCH SHIPPED LOCAL**" not in state_md


def test_apply_backfill_preserves_class_casing_minor(
    tmp_path: Path,
) -> None:
    """When the leading title says ``**v0.9.0 minor SHIPPED LOCAL**``
    (lowercase CLASS — historical v0.5.0 / v0.4.3 row shape), the
    flip preserves the ``minor`` casing."""
    docs = tmp_path / "docs"
    docs.mkdir()
    body = (
        "# State\n\n"
        "- **2026-05-10** — **v0.9.0 minor SHIPPED LOCAL** — work. "
        "Plan-doc `aaaaaaa`. v0.9.0 SHIPPED LOCAL — owner gates publish.\n"
    )
    (docs / "STATE.md").write_text(body)
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    state_md = (docs / "STATE.md").read_text(encoding="utf-8")
    assert "**v0.9.0 minor SHIPPED PUBLIC**" in state_md, state_md


# --------------------------------------------------------------------
# AC.BACKFL2.2 — STATE.md TBD-AT-* placeholder backfill.
# --------------------------------------------------------------------


def test_apply_backfill_backfills_state_md_seal_placeholder(
    tmp_path: Path,
) -> None:
    """The STATE.md row's ``seal TBD-AT-SEAL`` placeholder gets
    replaced with ``seal `<sha7>``` (mirror of v0.7.3 roadmap-row
    behavior; AC.BACKFL2.2)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(
        _state_md_with_shipped_local(
            "v0.9.0", with_v074_gap_surfaces=True
        )
    )
    # Roadmap with seal SHA in §2 row so apply_backfill can extract
    # it via gates._extract_seal_sha (drives the STATE.md backfill
    # via the same seal_sha argument).
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.9.0")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        seal_sha="ddddddd1234567890",
        today=today,
    )
    state_md = (docs / "STATE.md").read_text(encoding="utf-8")
    # The plain `seal TBD-AT-SEAL` text was replaced with `seal `ddddddd``.
    assert "seal `ddddddd`" in state_md, state_md
    assert "seal TBD-AT-SEAL" not in state_md


# --------------------------------------------------------------------
# AC.BACKFL2.3 — commit-graph walk discovery.
# --------------------------------------------------------------------


def _make_seal_apply_commit_chain(
    repo_root: Path, slug: str
) -> tuple[str, str, str]:
    """Build a real git commit graph in *repo_root* with the
    canonical seal + apply + source-edit message forms.

    Returns ``(source_edit_sha, apply_sha, seal_sha)`` of the
    constructed commits.
    """
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(repo_root)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.name", "Test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "t@t"],
        check=True,
    )
    # Initial commit (so the chain has a parent).
    (repo_root / "README.md").write_text("# test\n")
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "README.md"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-q", "-m", "init"],
        check=True,
    )
    # Source-edit commit.
    (repo_root / "src.py").write_text("x = 1\n")
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "src.py"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo_root), "commit", "-q",
            "-m", f"feat({slug}): work landed",
        ],
        check=True,
    )
    source_edit_sha = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # Apply commit (canonical message form).
    (repo_root / "manifest.txt").write_text("baseline\n")
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "manifest.txt"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo_root), "commit", "-q",
            "-m",
            f"chore(amend): {slug} manifest+apply — dev-sdlc "
            f"BASELINE+sidecar bump to {source_edit_sha}",
        ],
        check=True,
    )
    apply_sha = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # Seal commit (canonical message form).
    (repo_root / "seal.txt").write_text("seal\n")
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "seal.txt"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo_root), "commit", "-q",
            "-m",
            f"chore(seals): {slug} — dev-sdlc at {apply_sha}",
        ],
        check=True,
    )
    seal_sha = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return source_edit_sha, apply_sha, seal_sha


def test_discover_source_edit_and_apply_walks_canonical_message_forms(
    tmp_path: Path,
) -> None:
    """Direct unit test of the discovery helper — verifies the
    canonical seal + apply message-form regexes match the real
    commit graph this codebase emits (AC.BACKFL2.3)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    source_edit, apply_, seal = _make_seal_apply_commit_chain(
        repo, "v0-9-0-test"
    )
    discovered_source, discovered_apply = (
        post_publish_backfill._discover_source_edit_and_apply_shas(
            repo, seal
        )
    )
    assert discovered_source == source_edit
    assert discovered_apply == apply_


def test_discover_returns_none_on_non_canonical_message(
    tmp_path: Path,
) -> None:
    """Discovery returns (None, None) gracefully when the seal
    commit's message doesn't match the canonical form (defensive
    per D-BACKFL2.3.b)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(repo)], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@t"], check=True
    )
    (repo / "x").write_text("x")
    subprocess.run(
        ["git", "-C", str(repo), "add", "x"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo), "commit", "-q",
            "-m", "non-canonical commit message",
        ],
        check=True,
    )
    sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    src, apl = (
        post_publish_backfill._discover_source_edit_and_apply_shas(
            repo, sha
        )
    )
    assert src is None
    assert apl is None


def test_apply_backfill_discovers_source_edit_and_apply_from_seal_commit(
    tmp_path: Path,
) -> None:
    """End-to-end: full backfill against a fixture with a real
    commit graph + canonical TBD-AT-COMMIT / TBD-AT-APPLY
    placeholders → discovery succeeds + placeholders backfilled
    in BOTH STATE.md row and roadmap §2 row (AC.BACKFL2.3)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    source_edit, apply_, seal = _make_seal_apply_commit_chain(
        repo, "v0-9-0-test"
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(
        _state_md_with_shipped_local(
            "v0.9.0", with_v074_gap_surfaces=True
        )
    )
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row(
            "v0.9.0", with_v074_gap_surfaces=True
        )
    )
    # Stage + commit so the docs land in the same repo (caller can
    # find them via repo_root).
    subprocess.run(
        ["git", "-C", str(repo), "add", "docs"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo), "commit", "-q",
            "-m", "stage docs for backfill test",
        ],
        check=True,
    )
    today = _dt.date(2026, 5, 11)
    result = post_publish_backfill.apply_backfill(
        repo,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        seal_sha=seal,
        today=today,
    )
    state_md = (docs / "STATE.md").read_text(encoding="utf-8")
    roadmap = (docs / "release-roadmap.md").read_text(encoding="utf-8")
    # All four discoverable placeholders backfilled in both files.
    assert "TBD-AT-COMMIT" not in state_md, state_md
    assert "TBD-AT-APPLY" not in state_md, state_md
    assert "TBD-AT-SEAL" not in state_md, state_md
    assert "TBD-AT-COMMIT" not in roadmap, roadmap
    assert "TBD-AT-APPLY" not in roadmap, roadmap
    assert "TBD-AT-SEAL" not in roadmap, roadmap
    # Discovered SHAs landed in the row text (7-char abbreviated form).
    assert source_edit[:7] in state_md
    assert apply_[:7] in state_md
    assert source_edit[:7] in roadmap
    assert apply_[:7] in roadmap
    assert result.edits_applied >= 1


# --------------------------------------------------------------------
# AC.BACKFL2.4 — already-public title is a no-op.
# --------------------------------------------------------------------


def test_apply_backfill_state_md_already_public_title_no_op(
    tmp_path: Path,
) -> None:
    """When the STATE.md leading title is already
    ``SHIPPED PUBLIC``, the leading-title flip helper makes no
    change (no double-flip; AC.BACKFL2.4 idempotence)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    body = (
        "# State\n\n"
        "- **2026-05-10** — **v0.9.0 PATCH SHIPPED PUBLIC** — work. "
        "Seal `ddddddd`. **v0.9.0 SHIPPED PUBLIC 2026-05-11 at tag "
        "`v0.9.0` (annotated `abc1234`)**.\n"
    )
    (docs / "STATE.md").write_text(body)
    (docs / "release-roadmap.md").write_text(
        "# Release Roadmap\n\n## §2 Shipped\n\n"
        "| Version | Objective | Anchor |\n"
        "|---|---|---|\n"
        "| v0.9.0 | obj. | Single-cycle PATCH: seal `ddddddd`; "
        "**SHIPPED PUBLIC 2026-05-11 at tag `v0.9.0` (annotated "
        "`abc1234`)** |\n\n"
        "**Total shipped:** 0 minor + 1 patch. v0.9.0 published.\n\n"
        "## §3 Active version\n\n"
        "**v0.9.0 PATCH (obj.) SHIPPED PUBLIC 2026-05-11** "
        "(tag `v0.9.0`, annotated `abc1234`; seal `ddddddd`).\n"
    )
    today = _dt.date(2026, 5, 11)
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        today=today,
    )
    after = (docs / "STATE.md").read_text(encoding="utf-8")
    assert after == body, after
    assert result.idempotent_noop is True


# --------------------------------------------------------------------
# AC.BACKFL2.5 — integration: full canonical pre-image yields zero
# residual TBD-AT-* + zero residual SHIPPED LOCAL post-call;
# idempotence re-run is a clean no-op.
# --------------------------------------------------------------------


def test_apply_backfill_full_v074_pre_image_yields_zero_residual_tbd(
    tmp_path: Path,
) -> None:
    """Full canonical v0.7.4 pre-image (leading SHIPPED LOCAL +
    trailing SHIPPED LOCAL + TBD-AT-COMMIT + TBD-AT-APPLY +
    TBD-AT-SEAL in BOTH files) → first call applies all edits +
    zero residual TBD-AT-* + zero residual SHIPPED LOCAL; second
    call (idempotence re-run) → idempotent_noop, no further file
    writes (AC.BACKFL2.5 integration)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    source_edit, apply_, seal = _make_seal_apply_commit_chain(
        repo, "v0-9-0-test"
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text(
        _state_md_with_shipped_local(
            "v0.9.0", with_v074_gap_surfaces=True
        )
    )
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row(
            "v0.9.0", with_v074_gap_surfaces=True
        )
    )
    subprocess.run(
        ["git", "-C", str(repo), "add", "docs"], check=True
    )
    subprocess.run(
        [
            "git", "-C", str(repo), "commit", "-q",
            "-m", "stage docs for backfill test",
        ],
        check=True,
    )
    today = _dt.date(2026, 5, 11)
    r1 = post_publish_backfill.apply_backfill(
        repo,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        seal_sha=seal,
        today=today,
    )
    state_md_after_r1 = (docs / "STATE.md").read_text(encoding="utf-8")
    roadmap_after_r1 = (
        docs / "release-roadmap.md"
    ).read_text(encoding="utf-8")
    # Zero residual TBD-AT-* in both files.
    for body, name in (
        (state_md_after_r1, "STATE.md"),
        (roadmap_after_r1, "release-roadmap.md"),
    ):
        assert "TBD-AT-COMMIT" not in body, name
        assert "TBD-AT-APPLY" not in body, name
        assert "TBD-AT-SEAL" not in body, name
        assert "TBD-AT-TAG" not in body, name
    # Zero residual SHIPPED-LOCAL in BOTH leading title + trailing
    # sentence in STATE.md (this is the AC.BACKFL2.1 + AC.BACKFL.1
    # integration verification).
    assert "v0.9.0 PATCH SHIPPED LOCAL" not in state_md_after_r1
    assert "v0.9.0 SHIPPED LOCAL —" not in state_md_after_r1
    assert r1.edits_applied >= 4  # at least: trailing flip + leading
    # title + STATE.md placeholders + roadmap row marker / placeholders.
    # Idempotence re-run.
    r2 = post_publish_backfill.apply_backfill(
        repo,
        "v0.9.0",
        "v0.9.0",
        "abc1234567890def",
        seal_sha=seal,
        today=today,
    )
    state_md_after_r2 = (docs / "STATE.md").read_text(encoding="utf-8")
    roadmap_after_r2 = (
        docs / "release-roadmap.md"
    ).read_text(encoding="utf-8")
    assert r2.idempotent_noop is True, r2
    assert r2.edits_applied == 0
    assert state_md_after_r2 == state_md_after_r1
    assert roadmap_after_r2 == roadmap_after_r1


# --------------------------------------------------------------------
# AC.NFCLEAN.2 — walker fix tests (v0.8.1).
#
# Two compound root causes for the live `Total shipped:` count drift:
# (a) `_SUMMARY_LINE` regex required single `vX.Y.Z published.` form;
#     live line carries `v0.1.0 → v0.7.4 published.` (arrow + range)
#     so regex never matches → no auto-update.
# (b) `_count_published_versions` counted only marker-bearing rows;
#     pre-v0.7.3 historical rows lack auto-backfill markers, so the
#     walker undercounted by 18 (only 8 of 26 §2 rows have markers).
# --------------------------------------------------------------------


def test_count_published_versions_includes_marker_less_historical_rows() -> None:
    """``_count_published_versions`` counts ALL §2 version rows, not
    just the marker-bearing subset (AC.NFCLEAN.2 root-cause-B fix).

    The §2 section semantic is "shipped versions" — every row in §2
    is published regardless of whether it carries the v0.7.3+
    auto-backfill SHIPPED-PUBLIC marker. Historical rows
    (pre-v0.7.3) shipped before the marker convention existed; they
    must still count.
    """
    body = (
        "## §2 Shipped\n\n"
        "| Version | Objective | Anchor |\n"
        "|---|---|---|\n"
        # Two marker-LESS historical rows (pre-v0.7.3 shape).
        "| v0.1.0 | First public release. | seal `aaaaaaa`. |\n"
        "| v0.1.1 | First patch. | seal `bbbbbbb`. |\n"
        # One marker-bearing MINOR row (post-v0.7.3 shape).
        "| v0.2.0 | Second minor. | Single-cycle MINOR: seal "
        "`ccccccc`; **SHIPPED PUBLIC 2026-05-01 at tag `v0.2.0` "
        "(annotated `ddddddd`)** |\n"
        # One marker-bearing PATCH row.
        "| v0.2.1 | First patch on second minor. | Single-cycle PATCH: "
        "seal `eeeeeee`; **SHIPPED PUBLIC 2026-05-02 at tag `v0.2.1` "
        "(annotated `fffffff`)** |\n"
    )
    minor, patch = post_publish_backfill._count_published_versions(body)
    # 2 minors (v0.1.0 + v0.2.0) + 2 patches (v0.1.1 + v0.2.1).
    # Pre-fix walker would have returned (1, 1) — only marker-bearing.
    assert minor == 2, f"expected 2 minor, got {minor}"
    assert patch == 2, f"expected 2 patch, got {patch}"


def test_summary_line_regex_accepts_arrow_range_form() -> None:
    """``_SUMMARY_LINE`` regex matches both single-version and arrow-
    range forms (AC.NFCLEAN.2 root-cause-A fix).

    Live release-roadmap.md carried `v0.1.0 → v0.7.4 published.`
    (arrow + range form generated when the cumulative-prose tail is
    appended). Pre-fix regex only matched single `vX.Y.Z published.`
    so the auto-update never fired against the live line.
    """
    # Single-version form (existing test fixture shape).
    single_form = (
        "**Total shipped:** 5 minor + 10 patches. v0.5.0 published. "
        "Editorial prose unchanged.\n"
    )
    assert post_publish_backfill._SUMMARY_LINE.search(single_form) is not None
    # Arrow + range form (live release-roadmap shape).
    range_form = (
        "**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 "
        "published. v0.3.0 ships META-FRAMEWORK foundation.\n"
    )
    assert post_publish_backfill._SUMMARY_LINE.search(range_form) is not None


def test_classify_row_falls_back_to_version_pattern_for_historical_rows() -> None:
    """``_classify_row`` falls back to version-pattern derivation when
    the third pipe-cell lacks an explicit class keyword (AC.NFCLEAN.2
    classification fallback for pre-v0.6.0 historical rows).

    X.Y.0 form (no fourth-component segment) = MINOR; X.Y.Z (Z > 0)
    or X.Y.Z.W = PATCH. Per ``docs/release-versioning-policy.md``.
    """
    # Historical MINOR (no class keyword in third cell).
    minor_row = "| v0.1.0 | First public release. | seal `aaaaaaa`. |"
    assert post_publish_backfill._classify_row(minor_row) == "MINOR"
    # Historical PATCH (no class keyword; X.Y.Z form Z>0).
    patch_row = "| v0.1.6 | First patch shipment. | seals `xxx`, `yyy` |"
    assert post_publish_backfill._classify_row(patch_row) == "PATCH"
    # Historical 4-component (.X.Y.Z.W form) — PATCH per policy.
    four_comp_row = "| v0.2.5.1 | A four-component patch. | seal `zzz` |"
    assert post_publish_backfill._classify_row(four_comp_row) == "PATCH"
    # Explicit-class still wins over fallback (post-v0.6.0 convention).
    explicit_minor_row = (
        "| v0.6.5 | A patch-numbered row labeled MINOR. | "
        "Single-cycle MINOR: seal `aaa` |"
    )
    assert post_publish_backfill._classify_row(explicit_minor_row) == "MINOR"


# --------------------------------------------------------------------
# AC.SMLTV — STATE.md leading-title date-in-title variant (v0.10.2).
#
# Extends the v0.7.4 `_backfill_state_md_leading_title` helper to
# recognize the date-in-title variant `**v<X.Y.Z> SHIPPED LOCAL
# <YYYY-MM-DD>**` (no class keyword between version and SHIPPED; date
# appears after LOCAL inside the bold). Historical v0.4.2 row used
# this shape; F-FUNC-1 (FIDRAFT 2026-05-10) captured the extension
# proposal. AC.SMLTV.1 (positive flip with date preserved) +
# AC.SMLTV.2 (canonical-form regression preservation — handled by
# the 22 existing tests above) + AC.SMLTV.3 (already-public variant
# no-op).
# --------------------------------------------------------------------


def test_apply_backfill_flips_state_md_date_in_title_variant(
    tmp_path: Path,
) -> None:
    """The date-in-title variant ``**v<X.Y.Z> SHIPPED LOCAL
    <YYYY-MM-DD>**`` (no class keyword; date in bolded title) flips
    to ``**v<X.Y.Z> SHIPPED PUBLIC <YYYY-MM-DD>**`` preserving the
    date verbatim (AC.SMLTV.1).

    Historical v0.4.2 STATE.md row used this shape (``**v0.4.2
    SHIPPED LOCAL 2026-05-09**``); v0.8.0 AC.HONEST.4 surfaced
    F-FUNC-1 when the v0.7.4 helper's canonical-only regex skipped
    the row and required manual touch-up.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    body = (
        "# State\n\n"
        "- **2026-05-09** — **v0.4.2 SHIPPED LOCAL 2026-05-09** — "
        "F-DESIGN-2 closure patch: two specific cross-cutting fixes "
        "inside the codegen subsystem. Plan-doc `aaaaaaa`. "
        "v0.4.2 SHIPPED LOCAL — owner gates publish.\n"
    )
    (docs / "STATE.md").write_text(body)
    (docs / "release-roadmap.md").write_text(
        _roadmap_with_shipped_local_row("v0.4.2")
    )
    today = _dt.date(2026, 5, 11)
    post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.4.2",
        "v0.4.2",
        "abc1234567890def",
        today=today,
    )
    state_md = (docs / "STATE.md").read_text(encoding="utf-8")
    # Variant flipped, date preserved verbatim.
    assert (
        "**v0.4.2 SHIPPED PUBLIC 2026-05-09**" in state_md
    ), state_md
    # Original variant-LOCAL leader is gone.
    assert "**v0.4.2 SHIPPED LOCAL 2026-05-09**" not in state_md


def test_apply_backfill_date_in_title_variant_already_public_no_op(
    tmp_path: Path,
) -> None:
    """When the date-in-title variant is already in the SHIPPED-PUBLIC
    shape (``**v<X.Y.Z> SHIPPED PUBLIC <YYYY-MM-DD>**``), the
    leading-title helper makes no change — idempotence for the
    variant mirrors AC.BACKFL2.4 for the canonical form (AC.SMLTV.3).
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    body = (
        "# State\n\n"
        "- **2026-05-09** — **v0.4.2 SHIPPED PUBLIC 2026-05-09** — "
        "F-DESIGN-2 closure patch landed; tag annotated `884abcd`; "
        "seal `eeeeeee`.\n"
    )
    (docs / "STATE.md").write_text(body)
    new_body, edit_summary = (
        post_publish_backfill._backfill_state_md_leading_title(
            body, "v0.4.2"
        )
    )
    # Idempotent: no edit applied.
    assert new_body == body
    assert edit_summary is None


def test_leading_title_pattern_captures_both_shapes_distinctly() -> None:
    """The combined regex captures the CLASS keyword (canonical form)
    OR the DATE (variant) into named groups; the replacement logic
    uses whichever is present (AC.SMLTV.1 + AC.SMLTV.2 internal
    invariant — direct unit test of the dispatcher's named-group
    contract).
    """
    # Canonical form → 'cls' group populated, 'date' group None.
    canonical = "Some prose **v0.7.3 PATCH SHIPPED LOCAL** more prose."
    pat = post_publish_backfill._leading_title_pattern("v0.7.3")
    m = pat.search(canonical)
    assert m is not None
    assert m.group("cls") == "PATCH"
    assert m.group("date") is None
    # Variant → 'date' group populated, 'cls' group None.
    variant = "Some prose **v0.4.2 SHIPPED LOCAL 2026-05-09** more."
    pat2 = post_publish_backfill._leading_title_pattern("v0.4.2")
    m2 = pat2.search(variant)
    assert m2 is not None
    assert m2.group("cls") is None
    assert m2.group("date") == "2026-05-09"
    # Lowercase canonical CLASS keyword (historical v0.4.3 / v0.5.0
    # shape) still matches.
    lowercase_canonical = "**v0.5.0 minor SHIPPED LOCAL**"
    pat3 = post_publish_backfill._leading_title_pattern("v0.5.0")
    m3 = pat3.search(lowercase_canonical)
    assert m3 is not None
    assert m3.group("cls") == "minor"
    assert m3.group("date") is None


# --------------------------------------------------------------------
# AC.RBHCB — Release-backfill helpers completeness batch (v0.10.3).
#
# Three orthogonal helper extensions in one PATCH:
#
#   AC.RBHCB.1 (F-FUNC-2) — `_backfill_state_md` extended so when a
#       SHIPPED-PUBLIC marker already exists for the version AND a
#       stale `<version> SHIPPED LOCAL — owner gates publish.`
#       interim sentence still lingers, the stale sentence is
#       removed (closes the v0.5.0 / v0.8.0 AC.HONEST.5 manual-
#       touch-up pattern).
#
#   AC.RBHCB.2 (F-WALKER-1) — new
#       `_split_pipe_row_backtick_aware` helper respects backtick
#       parity so rows whose description (cell [2]) contains
#       backtick-wrapped pipes classify and extract correctly via
#       the explicit-class detection path. Existing version-pattern
#       fallback retained as defense-in-depth.
#
#   AC.RBHCB.3 (F-FUNC-3) — `_backfill_tbd_placeholders` regex-
#       anchored via positive lookbehind to canonical surrounding
#       tokens (`seal `/`tag `/`source-edit `/`apply `) so prose-
#       narrative TBD-AT-* references in row body descriptions are
#       preserved (closes the v0.10.1 Path-A halt finding).
# --------------------------------------------------------------------


# AC.RBHCB.1 — interim-shipped-local sentence removal mode (F-FUNC-2).


def test_apply_backfill_removes_stale_interim_sentence_when_marker_present(
    tmp_path: Path,
) -> None:
    """When the STATE.md body carries the SHIPPED-PUBLIC marker for
    the version AND a stale ``<version> SHIPPED LOCAL — owner gates
    publish.`` interim sentence still lingers, the stale sentence is
    removed (per AC.RBHCB.1 / F-FUNC-2 closure).

    Mirrors the v0.5.0 / v0.8.0 AC.HONEST.5 manual-touch-up pattern:
    the public-marker landed manually before v0.7.3's auto-backfill
    existed; the v0.7.4 helper's idempotence-by-skip path correctly
    avoided double-flipping but didn't clean up the stale interim
    sentence left over from the SHIPPED-LOCAL state.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    # Body shape: leading title already PUBLIC + trailing PUBLIC marker
    # already present + stale interim SHIPPED-LOCAL sentence still
    # there (the v0.5.0 pre-v0.8.0 shape).
    body = (
        "# State\n\n"
        "- **2026-05-09** — **v0.5.0 minor SHIPPED PUBLIC** — work. "
        "Plan-doc `aaaaaaa`. v0.5.0 SHIPPED LOCAL — owner gates publish. "
        "**v0.5.0 SHIPPED PUBLIC 2026-05-09 at tag `v0.5.0` "
        "(annotated `bbbbbbb`)**.\n"
    )
    (docs / "STATE.md").write_text(body)
    (docs / "release-roadmap.md").write_text(
        "# Release Roadmap\n\n## §2 Shipped\n\n"
        "| Version | Objective | Anchor |\n"
        "|---|---|---|\n"
        "| v0.5.0 | obj. | Single-cycle MINOR: seal `ccccccc`; "
        "**SHIPPED PUBLIC 2026-05-09 at tag `v0.5.0` (annotated "
        "`bbbbbbb`)** |\n\n"
        "**Total shipped:** 1 minor + 0 patches. v0.5.0 published.\n\n"
        "## §3 Active version\n\n"
        "**v0.5.0 minor (obj.) SHIPPED PUBLIC 2026-05-09** "
        "(tag `v0.5.0`, annotated `bbbbbbb`; seal `ccccccc`).\n"
    )
    today = _dt.date(2026, 5, 14)
    result = post_publish_backfill.apply_backfill(
        tmp_path,
        "v0.5.0",
        "v0.5.0",
        "abc1234567890def",
        today=today,
    )
    after = (docs / "STATE.md").read_text(encoding="utf-8")
    # Stale interim sentence is gone.
    assert "v0.5.0 SHIPPED LOCAL — owner gates publish." not in after, after
    # SHIPPED-PUBLIC marker preserved verbatim.
    assert (
        "**v0.5.0 SHIPPED PUBLIC 2026-05-09 at tag `v0.5.0` "
        "(annotated `bbbbbbb`)**" in after
    ), after
    # The leading title PUBLIC marker also preserved.
    assert "**v0.5.0 minor SHIPPED PUBLIC**" in after, after
    # An edit was applied (the removal counts as one edit).
    assert result.edits_applied >= 1
    assert result.idempotent_noop is False


def test_apply_backfill_interim_removal_is_idempotent(
    tmp_path: Path,
) -> None:
    """Re-running apply_backfill against an already-cleaned body
    (SHIPPED-PUBLIC marker present + no stale interim sentence) is a
    no-op for the trailing-sentence path (per AC.RBHCB.1 idempotence
    contract).
    """
    body = (
        "# State\n\n"
        "- **2026-05-09** — **v0.5.0 minor SHIPPED PUBLIC** — work. "
        "Plan-doc `aaaaaaa`. **v0.5.0 SHIPPED PUBLIC 2026-05-09 at "
        "tag `v0.5.0` (annotated `bbbbbbb`)**.\n"
    )
    new_body, edit_summary = post_publish_backfill._backfill_state_md(
        body, "v0.5.0", _dt.date(2026, 5, 14), "v0.5.0", "abc1234567890def"
    )
    assert new_body == body
    assert edit_summary is None


# AC.RBHCB.2 — backtick-aware pipe tokenizer (F-WALKER-1).


def test_split_pipe_row_backtick_aware_skips_pipes_inside_backticks() -> None:
    """``_split_pipe_row_backtick_aware`` walks the row treating
    backticks as parity toggles; pipes inside paired backticks are
    NOT cell separators (per AC.RBHCB.2 / F-WALKER-1 closure).

    Pre-fix shape (``row.split('|')``) over-segmented rows whose
    description contained backtick-wrapped pipes — e.g., v0.4.2's
    description with type-annotation prose like ``Y → Union[X, Y]``.
    """
    # Row with TWO backtick-wrapped pipes in cell [2] (description).
    # Naive split would yield 7 cells (5 expected + 2 spurious from
    # the backtick-wrapped pipes); backtick-aware split yields 5.
    row = (
        "| v0.4.2 | covers `Y` `|` `Union[X, Y]` `|` "
        "`Optional[X]` shapes. | Single-cycle PATCH: seal `xxx` |"
    )
    naive = row.split("|")
    cells = post_publish_backfill._split_pipe_row_backtick_aware(row)
    # Confirm the pre-fix bug shape (naive split over-segments).
    assert len(naive) == 7, naive
    # Backtick-aware split gives 5 cells (matching row's actual
    # table structure).
    assert len(cells) == 5, cells
    # Cell [0] empty (leading pipe); cell [1] = " v0.4.2 ";
    # cell [2] is the FULL description including the backtick-wrapped
    # pipes (not truncated mid-stream).
    assert cells[1].strip() == "v0.4.2"
    assert "Union[X, Y]" in cells[2]
    assert "Optional[X]" in cells[2]
    # Cell [3] is the actual class cell (Anchor column body).
    assert "PATCH" in cells[3]


def test_classify_row_uses_explicit_class_path_with_backtick_pipes() -> None:
    """``_classify_row`` returns the explicit-class value via the
    FIRST detection path (third pipe-cell) for rows whose description
    contains backtick-wrapped pipes — NOT via the version-pattern
    fallback (per AC.RBHCB.2 / F-WALKER-1 closure).

    Contradiction-shape test: the row's version (v0.4.0) would
    fallback-classify as MINOR (X.Y.0 form) but the explicit-class
    keyword in the third cell is PATCH; the backtick-aware tokenizer
    must reach the third cell correctly so the explicit-class path
    wins. Pre-fix shape would over-segment, miss the PATCH keyword in
    the actual third cell, and fall back to MINOR.
    """
    # Note: v0.4.0 fallback-classifies as MINOR (X.Y.0 + no fourth);
    # explicit class in third cell says PATCH. Tokenizer must read
    # the third cell correctly to honor the explicit-class path.
    row = (
        "| v0.4.0 | desc with `a` `|` `b` pipe-wrapped pattern. | "
        "Single-cycle PATCH: seal `xxx` |"
    )
    # Sanity check: confirm the pre-fix bug shape.
    naive_cells = row.split("|")
    assert len(naive_cells) >= 4
    assert "PATCH" not in naive_cells[3], (
        "fixture should trigger the pre-fix bug — naive split's "
        "third cell should NOT contain PATCH"
    )
    # Backtick-aware tokenizer reaches the actual third cell.
    classification = post_publish_backfill._classify_row(row)
    assert classification == "PATCH", (
        f"explicit-class path should yield PATCH; got {classification} "
        f"(version-pattern fallback would have given MINOR)"
    )


def test_extract_objective_sentence_preserves_backtick_wrapped_pipes() -> None:
    """``_extract_objective_sentence`` returns the full description
    cell content (subject to sentence-boundary truncation) even when
    the cell contains backtick-wrapped pipes (per AC.RBHCB.2 /
    F-WALKER-1 closure).

    Pre-fix shape (``row.split('|')`` in the function body) would
    truncate the cell at the first backtick-wrapped pipe.
    """
    row = (
        "| v0.4.2 | F-DESIGN-2 patch covering `Y` `|` `Union[X, Y]` "
        "shapes. | Single-cycle PATCH: seal `xxx` |"
    )
    objective = post_publish_backfill._extract_objective_sentence(row)
    # The full description (up to first sentence boundary) is preserved.
    assert "F-DESIGN-2 patch" in objective
    assert "Union[X, Y]" in objective
    # Sentence-boundary truncation still works (cuts at the first
    # period followed by space — ending at "shapes.").
    assert objective.endswith("shapes.")


def test_classify_row_fallback_still_works_for_marker_less_rows() -> None:
    """Regression: existing version-pattern fallback in
    ``_classify_row`` still fires for historical pre-v0.6.0 rows
    that lack an explicit class keyword (per AC.RBHCB.2 — defense-
    in-depth preserved).
    """
    # Historical MINOR (no class keyword in third cell, no backtick-
    # pipes — the v0.8.1 AC.NFCLEAN.2 fallback case).
    minor_row = "| v0.1.0 | First public release. | seal `aaaaaaa`. |"
    assert post_publish_backfill._classify_row(minor_row) == "MINOR"
    # Historical PATCH (X.Y.Z form Z>0).
    patch_row = "| v0.1.6 | First patch shipment. | seals `xxx`, `yyy` |"
    assert post_publish_backfill._classify_row(patch_row) == "PATCH"


# AC.RBHCB.3 — TBD-AT-* anchored to canonical surrounding context (F-FUNC-3).


def test_backfill_tbd_placeholders_preserves_prose_narrative() -> None:
    """``_backfill_tbd_placeholders`` only replaces TBD-AT-*
    placeholders preceded by their canonical surrounding token; prose-
    narrative occurrences inside backtick-wrapped descriptions are
    preserved (per AC.RBHCB.3 / F-FUNC-3 closure).

    Mirrors the v0.7.3 STATE.md row at docs/STATE.md:133 corruption
    pattern: the row body literally contains
    ``backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders`` as prose
    describing what the v0.7.3 helper does. Pre-fix `str.replace`
    would corrupt this prose; post-fix anchored regex preserves it.
    """
    # Row carries BOTH a canonical-context TBD-AT-SEAL (in
    # `seal TBD-AT-SEAL`) AND a prose-narrative TBD-AT-SEAL (inside
    # backticks describing the helper's behaviour).
    row = (
        "| v0.7.3 | release-CLI auto-backfill helper backfills "
        "`TBD-AT-SEAL` / `TBD-AT-TAG` placeholders from known SHAs. | "
        "Single-cycle PATCH: seal TBD-AT-SEAL |"
    )
    new_row, backfilled = post_publish_backfill._backfill_tbd_placeholders(
        row,
        tag="v0.7.3",
        tag_sha="ffffffffffffffff",
        seal_sha="ddddddd1234567890",
    )
    # Canonical-context occurrence WAS replaced.
    assert "seal `ddddddd`" in new_row, new_row
    assert "TBD-AT-SEAL" in backfilled
    # Prose-narrative occurrences (inside backticks, no `seal `/`tag `
    # prefix) were NOT replaced.
    assert "`TBD-AT-SEAL`" in new_row, new_row
    assert "`TBD-AT-TAG`" in new_row, new_row


def test_backfill_tbd_placeholders_skips_prose_only_rows() -> None:
    """Negative: a row containing ONLY prose-narrative TBD-AT-*
    references (no canonical-context occurrences) is unchanged
    (per AC.RBHCB.3 — narrative-safety preserved).
    """
    row = (
        "| v0.7.3 | helper backfills `TBD-AT-SEAL` / `TBD-AT-TAG` / "
        "`TBD-AT-COMMIT` / `TBD-AT-APPLY` placeholders from known "
        "SHAs. | seal `aaaaaaa` |"
    )
    new_row, backfilled = post_publish_backfill._backfill_tbd_placeholders(
        row,
        tag="v0.7.3",
        tag_sha="ffffffffffffffff",
        seal_sha="ddddddd1234567890",
        source_edit_sha="eeeeeee1234567890",
        apply_sha="fffffff1234567890",
    )
    assert new_row == row, (
        "prose-only row should be unchanged (no canonical-context "
        "anchors hit)"
    )
    assert backfilled == [], backfilled


def test_backfill_tbd_placeholders_canonical_context_unchanged_outcome() -> None:
    """Regression: the canonical context shape (the v0.7.4 fixture
    `_state_md_with_shipped_local(with_v074_gap_surfaces=True)` /
    `_roadmap_with_shipped_local_row(with_v074_gap_surfaces=True)`)
    still backfills correctly under the anchored-regex shape (per
    AC.RBHCB.3 — defense-in-depth for the canonical path).

    Direct invocation of the helper against the same canonical row
    body the existing v0.7.4 tests use; verifies all four placeholder
    backfills succeed when the canonical surrounding tokens are present.
    """
    row = (
        "Plan-doc `aaaaaaa`; source-edit TBD-AT-COMMIT; "
        "apply TBD-AT-APPLY; seal TBD-AT-SEAL"
    )
    new_row, backfilled = post_publish_backfill._backfill_tbd_placeholders(
        row,
        tag="v0.9.0",
        tag_sha="abc1234567890def",
        seal_sha="ddddddd1234567890",
        source_edit_sha="bbbbbbb1234567890",
        apply_sha="ccccccc1234567890",
    )
    assert "TBD-AT-SEAL" not in new_row, new_row
    assert "TBD-AT-COMMIT" not in new_row, new_row
    assert "TBD-AT-APPLY" not in new_row, new_row
    assert "seal `ddddddd`" in new_row
    assert "source-edit `bbbbbbb`" in new_row
    assert "apply `ccccccc`" in new_row
    assert set(backfilled) == {
        "TBD-AT-SEAL", "TBD-AT-COMMIT", "TBD-AT-APPLY"
    }

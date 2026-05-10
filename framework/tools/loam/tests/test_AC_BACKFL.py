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


def _state_md_with_shipped_local(version: str = "v0.9.0") -> str:
    """STATE.md body with the canonical SHIPPED-LOCAL trailing claim
    for *version* (matches the f0ae00c pre-image shape).
    """
    return (
        "# State\n\n"
        "Some preamble prose.\n\n"
        "- **2026-05-09** — **v0.8.9 PATCH SHIPPED PUBLIC** — predecessor "
        "row.\n"
        f"- **2026-05-10** — **{version} PATCH SHIPPED LOCAL** — "
        "release-CLI auto-backfill defect-closure for v0.6.0's shipped "
        f"release-process. Plan-doc `aaaaaaa`; source-edit `bbbbbbb`; "
        f"apply `ccccccc`; seal `ddddddd`. {version} SHIPPED LOCAL — "
        "owner gates publish.\n"
    )


def _state_md_already_public(version: str = "v0.9.0") -> str:
    """STATE.md body where *version* already carries the SHIPPED-PUBLIC
    marker (idempotence-case fixture).
    """
    return (
        "# State\n\n"
        f"- **2026-05-10** — **{version} PATCH SHIPPED LOCAL** — work. "
        f"Seal `ddddddd`. **{version} SHIPPED PUBLIC 2026-05-10 at tag "
        f"`{version}` (annotated `eeeeeee`)**.\n"
    )


def _roadmap_with_shipped_local_row(version: str = "v0.9.0") -> str:
    """release-roadmap.md body with §2 row + §3 + summary line in
    pre-publish state for *version*.
    """
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
        "bit at every publish since v0.6.0. | Single-cycle PATCH: plan-doc "
        f"`aaaaaaa`; source-edit `bbbbbbb`; apply `ccccccc`; seal "
        f"`ddddddd` |\n"
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

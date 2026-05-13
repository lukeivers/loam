"""Orchestrate the ``loam release`` publish flow (AC.V060.1 / .3 / .4 / .6).

The runner glues the per-gate verification, tag-and-push action,
optional ``gh release create``, and the post-ship review block into a
single end-to-end flow. Per AC.V060.3 the action is idempotent: a
re-run on an already-published version produces a no-op + clear
diagnostic.

Public callable: :func:`run`. Returns the exit code (``0`` =
success; non-zero on any pre-publish gate RED or push failure).
The CLI dispatcher (:mod:`loam_cli.release.cli`) delegates to it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loam_cli.release import (
    gates,
    notes,
    post_publish_backfill,
    post_ship,
)


@dataclass(frozen=True)
class PublishOutcome:
    """Aggregated result of a publish run.

    Used by tests to inspect what ran without re-parsing stdout.
    """

    rc: int
    gate_results: list[gates.GateResult]
    tag_created: bool
    tag_pushed: bool
    branch_pushed: bool
    gh_release_created: bool
    idempotent_noop: bool
    proposal: post_ship.NextScopeProposal | None
    backfill: post_publish_backfill.BackfillResult | None = None
    backfill_committed: bool = False
    backfill_pushed: bool = False


_REMOTE = "origin"
_BRANCH = "main"


def _git(
    *args: str, repo_root: Path, check: bool = True
) -> subprocess.CompletedProcess:
    """Thin ``git`` wrapper. Surfaces stderr on failure when
    ``check`` is True; returns the CompletedProcess otherwise.
    """
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=check,
    )


def _objective_sentence_for(
    repo_root: Path, version: str
) -> str:
    """Pull the objective sentence from ``docs/release-roadmap.md``
    §2 row for *version*; used as the annotated-tag message body.

    Falls back to ``"loam release {version}"`` when the roadmap row
    is absent or doesn't carry an objective sentence column.
    """
    path = repo_root / "docs" / "release-roadmap.md"
    if not path.exists():
        return f"loam release {version}"
    body = path.read_text(encoding="utf-8")
    # Match the row + capture the second pipe-cell (objective).
    pattern = re.compile(
        r"^\|\s*"
        + re.escape(version)
        + r"\s*\|\s*([^|]+?)\s*\|",
        re.MULTILINE,
    )
    m = pattern.search(body)
    if m is None:
        return f"loam release {version}"
    sentence = m.group(1).strip()
    return sentence if sentence else f"loam release {version}"


def _tag_exists_locally(repo_root: Path, tag: str) -> bool:
    proc = _git("tag", "-l", tag, repo_root=repo_root, check=False)
    return tag in proc.stdout.split()


def _tag_exists_on_remote(repo_root: Path, tag: str) -> bool:
    proc = _git(
        "ls-remote",
        "--tags",
        _REMOTE,
        f"refs/tags/{tag}",
        repo_root=repo_root,
        check=False,
    )
    return bool(proc.stdout.strip())


def _create_annotated_tag(
    repo_root: Path, tag: str, seal_sha: str, message: str
) -> None:
    """Create an annotated tag *tag* at *seal_sha* with *message*.

    Per the publish discipline (and the dispatch brief's HARD HALT
    rule), tag creation is an action-with-side-effect — it lands as
    a real ref in ``.git/``. This is the publish-side action; the
    pre-publish gates have already validated all six structural
    preconditions before this is reached.
    """
    _git(
        "tag",
        "-a",
        tag,
        seal_sha,
        "-m",
        message,
        repo_root=repo_root,
    )


def _push_branch_and_tag(repo_root: Path, tag: str) -> None:
    """``git push origin main`` + ``git push origin <tag>``."""
    _git("push", _REMOTE, _BRANCH, repo_root=repo_root)
    _git("push", _REMOTE, tag, repo_root=repo_root)


def _resolve_tag_sha(repo_root: Path, tag: str) -> str:
    """Return the annotated-tag-object SHA for *tag* (NOT the
    underlying commit's SHA — for annotated tags these differ).
    """
    proc = _git("rev-parse", tag, repo_root=repo_root, check=False)
    return proc.stdout.strip()


def _commit_and_push_backfill(
    repo_root: Path, version: str
) -> tuple[bool, bool]:
    """Stage the docs paths the backfill touched, commit with the
    canonical message, and push to ``origin main``.

    Returns ``(committed, pushed)``. Skipped when there's nothing
    staged (defensive — caller already checks ``edits_applied``).
    """
    # Stage the two known doc paths (file-level granularity preserves
    # any unrelated edits in other parts of the tree, though gate 4
    # `clean-tree` should have already failed if any existed).
    _git(
        "add",
        "docs/STATE.md",
        "docs/release-roadmap.md",
        repo_root=repo_root,
        check=False,
    )
    diff = _git(
        "diff",
        "--cached",
        "--quiet",
        repo_root=repo_root,
        check=False,
    )
    if diff.returncode == 0:
        # Nothing actually staged after the add — no commit.
        return False, False
    msg = (
        f"docs(release): {version} post-publish backfill — "
        f"SHIPPED PUBLIC"
    )
    _git("commit", "-m", msg, repo_root=repo_root)
    _git("push", _REMOTE, _BRANCH, repo_root=repo_root)
    return True, True


def _gh_release_create(
    repo_root: Path, tag: str, notes_body: str
) -> None:
    """Invoke ``gh release create <tag> --notes <body>``.

    Tests monkeypatch ``subprocess.run`` so this never reaches the
    real ``gh`` binary. In production, the operator is expected to
    have ``gh`` installed (``--release`` is opt-in only; the default
    publish path skips this).
    """
    if shutil.which("gh") is None:
        raise FileNotFoundError(
            "gh CLI not found on PATH; install gh + authenticate "
            "before passing --release."
        )
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            tag,
            "--notes",
            notes_body,
        ],
        cwd=repo_root,
        check=True,
    )


def run(
    repo_root: Path,
    version: str,
    *,
    dry_run: bool = False,
    create_release: bool = False,
    plan_doc: Path | None = None,
) -> PublishOutcome:
    """Execute the publish flow.

    Returns a :class:`PublishOutcome` carrying gate verdicts +
    side-effect summary. On any RED gate, returns rc=1 without
    touching the tree or remote (regardless of *dry_run*). On
    success, returns rc=0.

    *dry_run* skips tag creation + push + gh-release; everything
    else (gates + post-ship proposal) still runs so the operator
    sees the full state.

    Per AC.SDPD.{2,3} (v0.8.2): *plan_doc* (when set) overrides the
    version-slug-glob inference in the ``acs-verified`` and
    ``hard-smoke`` gates; supports scope-descriptive plan-doc slugs
    per ``feedback_version_numbers_at_release_time``.
    """
    # 1. Pre-publish gates (AC.V060.2).
    gate_results = gates.run_all(repo_root, version, plan_doc=plan_doc)
    print("== Pre-publish gates ==")
    print(gates.format_report(gate_results))
    print()
    failed = [r for r in gate_results if not r.ok]
    if failed:
        print(
            f"FAIL: {len(failed)} gate(s) RED; aborting. Address the "
            "corrective hints above + re-run."
        )
        return PublishOutcome(
            rc=1,
            gate_results=gate_results,
            tag_created=False,
            tag_pushed=False,
            branch_pushed=False,
            gh_release_created=False,
            idempotent_noop=False,
            proposal=None,
        )

    tag = version  # tag name == version literal (e.g., "v0.6.0").

    # 2. Idempotency check (AC.V060.3).
    if _tag_exists_on_remote(repo_root, tag):
        # Resolve the remote SHA for the friendly diagnostic.
        ls = _git(
            "ls-remote",
            "--tags",
            _REMOTE,
            f"refs/tags/{tag}",
            repo_root=repo_root,
            check=False,
        )
        remote_sha = ls.stdout.split()[0] if ls.stdout.strip() else "?"
        print(
            f"{tag} already on {_REMOTE} remote at {remote_sha}; "
            "nothing to do."
        )
        # Post-failure-recovery: still run the backfill in case a
        # prior run pushed the tag but failed before backfill landed
        # (per AC.BACKFL.4 — idempotent on already-current state).
        backfill_result = post_publish_backfill.apply_backfill(
            repo_root, version, tag, remote_sha, dry_run=False
        )
        backfill_committed = False
        backfill_pushed = False
        if backfill_result.edits_applied > 0:
            print(
                f"post-publish backfill: applied "
                f"{backfill_result.edits_applied} edit(s) "
                f"({len(backfill_result.files_touched)} file(s))"
            )
            backfill_committed, backfill_pushed = _commit_and_push_backfill(
                repo_root, version
            )
        else:
            print(
                "post-publish backfill: no edits needed (state already "
                "current)."
            )
        # Still emit the post-ship proposal — the operator may be
        # reading this output to plan the next cycle.
        proposal = post_ship.build_proposal(repo_root, version)
        print()
        print(post_ship.format_proposal(proposal))
        return PublishOutcome(
            rc=0,
            gate_results=gate_results,
            tag_created=False,
            tag_pushed=False,
            branch_pushed=False,
            gh_release_created=False,
            idempotent_noop=True,
            proposal=proposal,
            backfill=backfill_result,
            backfill_committed=backfill_committed,
            backfill_pushed=backfill_pushed,
        )

    # 3. Resolve seal SHA + objective sentence (used by tag message
    #    + GitHub Release notes body).
    roadmap_body = (
        repo_root / "docs" / "release-roadmap.md"
    ).read_text(encoding="utf-8")
    seal_sha = gates._extract_seal_sha(roadmap_body, version)
    if seal_sha is None:  # defensive — should be caught by gate 6.
        print(
            "FAIL: no seal SHA in docs/release-roadmap.md §2 for "
            f"{version}; aborting."
        )
        return PublishOutcome(
            rc=1,
            gate_results=gate_results,
            tag_created=False,
            tag_pushed=False,
            branch_pushed=False,
            gh_release_created=False,
            idempotent_noop=False,
            proposal=None,
        )
    objective = _objective_sentence_for(repo_root, version)
    tag_message = f"{version} — {objective}"

    if dry_run:
        print(
            f"DRY-RUN: would create annotated tag {tag} at {seal_sha} "
            f"with message: {tag_message!r}"
        )
        print(f"DRY-RUN: would push {_REMOTE} {_BRANCH} + tag {tag}")
        if create_release:
            print(
                f"DRY-RUN: would create GitHub Release for {tag} via gh"
            )
        # Dry-run preview of the post-publish backfill (AC.BACKFL.6).
        # Use the seal SHA as a stand-in for tag_sha (the annotated-
        # tag-object SHA isn't knowable without actually creating the
        # tag); the preview's marker form will reflect the seal SHA.
        backfill_preview = post_publish_backfill.apply_backfill(
            repo_root, version, tag, seal_sha,
            seal_sha=seal_sha, dry_run=True,
        )
        print()
        print(post_publish_backfill.format_backfill_preview(backfill_preview))
        proposal = post_ship.build_proposal(repo_root, version)
        print()
        print(post_ship.format_proposal(proposal))
        return PublishOutcome(
            rc=0,
            gate_results=gate_results,
            tag_created=False,
            tag_pushed=False,
            branch_pushed=False,
            gh_release_created=False,
            idempotent_noop=False,
            proposal=proposal,
            backfill=backfill_preview,
            backfill_committed=False,
            backfill_pushed=False,
        )

    # 4. Tag + push (AC.V060.3).
    tag_created = False
    if not _tag_exists_locally(repo_root, tag):
        _create_annotated_tag(repo_root, tag, seal_sha, tag_message)
        tag_created = True
        print(f"created annotated tag {tag} at {seal_sha}")
    _push_branch_and_tag(repo_root, tag)
    print(f"pushed {_REMOTE} {_BRANCH} + {tag}")

    # 4.5. Post-publish state-sync backfill (AC.BACKFL.{1,2,3,4}).
    #      MUST come AFTER tag push (HARD HALT #7 — the backfill
    #      commit advances main past the seal SHA the tag points to,
    #      so the tag MUST already be on remote first to avoid
    #      tag-vs-main divergence).
    tag_sha = _resolve_tag_sha(repo_root, tag)
    backfill_result = post_publish_backfill.apply_backfill(
        repo_root, version, tag, tag_sha,
        seal_sha=seal_sha, dry_run=False,
    )
    backfill_committed = False
    backfill_pushed = False
    if backfill_result.edits_applied > 0:
        print(
            f"post-publish backfill: applied "
            f"{backfill_result.edits_applied} edit(s) "
            f"({len(backfill_result.files_touched)} file(s))"
        )
        backfill_committed, backfill_pushed = _commit_and_push_backfill(
            repo_root, version
        )
        if backfill_committed:
            print(
                f"committed + pushed post-publish backfill to "
                f"{_REMOTE} {_BRANCH}"
            )
    else:
        print(
            "post-publish backfill: no edits needed (state already "
            "current)."
        )

    # 5. Optional GitHub Release (AC.V060.4).
    gh_release_created = False
    if create_release:
        notes_body = notes.generate_notes(repo_root, version)
        _gh_release_create(repo_root, tag, notes_body)
        gh_release_created = True
        print(f"created GitHub Release for {tag}")

    # 6. Post-ship review (AC.V060.6).
    proposal = post_ship.build_proposal(repo_root, version)
    print()
    print(post_ship.format_proposal(proposal))

    return PublishOutcome(
        rc=0,
        gate_results=gate_results,
        tag_created=tag_created,
        tag_pushed=True,
        branch_pushed=True,
        gh_release_created=gh_release_created,
        idempotent_noop=False,
        proposal=proposal,
        backfill=backfill_result,
        backfill_committed=backfill_committed,
        backfill_pushed=backfill_pushed,
    )

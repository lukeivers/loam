"""B-shape canonical-vs-workspace conflict detection.

Authored fresh. Replaces self-upgrade's manifest-vs-staging
``detect_conflicts`` with git-tree-vs-working-tree diffing. The
canonical tree at ``canonical_path`` resolved to ``ref`` is compared
against the workspace tree at ``workspace_root``; conflicts are
classified per the workspace's three-class envelope:

  - **Class A** workspace state: never overwritten. Pre-resolved to
    ``KEEP_LOCAL`` at detection time so the resolver is never called.
    AC.WS.2 structural enforcement.
  - **Class B** operator preference: PENDING; the helper
    (``merge_helper.resolve_inferred_conflicts``) flips to KEEP_LOCAL
    or ACCEPT_UPSTREAM based on workspace-modified state.
  - **Class C** framework code: PENDING; the helper invokes the LLM
    resolver.

Mechanism: ``git ls-tree -r --name-only <ref>`` enumerates canonical
paths; per-path comparison computes ``sha256`` of canonical text
(via ``git show <ref>:<path>``) and workspace text (via direct file
read). Both-sides-changed-vs-prior-recorded-canonical surfaces as a
ConflictEntry; one-side-only modifications fall through to clean
staging writes (no entry).

No new third-party deps (Hard Constraint #2): stdlib + ``git``
binary + Pydantic.
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    ConflictSummary,
    Resolution,
)
from .state import StateRecord
from .sync_protected import FileClass, SyncProtected


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_of_file(path: Path) -> str | None:
    """Return sha256 hex of ``path`` contents; None if missing."""
    if not path.exists() or not path.is_file():
        return None
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _git_ls_tree(canonical_path: Path, ref: str) -> list[str]:
    """Return every path tracked at ``ref`` (recursive)."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "-C", str(canonical_path), "ls-tree", "-r", "--name-only", ref],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    return [ln for ln in completed.stdout.splitlines() if ln.strip()]


def _git_show_bytes(canonical_path: Path, ref: str, path: str) -> bytes | None:
    """Return raw bytes of ``<ref>:<path>``; None if missing or binary-fail."""
    completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "-C", str(canonical_path), "show", f"{ref}:{path}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _classify_conflict_kind(
    canonical_sha: str | None,
    workspace_sha: str | None,
    prior_sha: str | None,
) -> ConflictChangeKind | None:
    """Classify the three-way-diff kind for a conflict.

    Returns None when the path does NOT need a ConflictEntry (clean
    update, identical, or canonical-only addition).
    """
    if canonical_sha == workspace_sha:
        return None  # identical — no entry
    if workspace_sha is None:
        return None  # canonical-only addition; clean staging write
    if canonical_sha is None:
        # Workspace has it; canonical removed it. Treat as
        # workspace-only modification (preserve workspace).
        return ConflictChangeKind.LOCAL_MODIFIED_ONLY
    if prior_sha is None:
        # No prior record; both sides have the path with different
        # contents. Treat as both-sides-modified.
        return ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
    if canonical_sha == prior_sha and workspace_sha != prior_sha:
        # Canonical unchanged; workspace modified. Workspace-only.
        return ConflictChangeKind.LOCAL_MODIFIED_ONLY
    if canonical_sha != prior_sha and workspace_sha == prior_sha:
        # Canonical advanced; workspace untouched. Clean update; no
        # entry needed (caller can stage canonical directly).
        return None
    if canonical_sha != prior_sha and workspace_sha != prior_sha:
        # Both sides modified vs prior. Conflict.
        if workspace_sha == canonical_sha:
            # Convergent: both sides arrived at the same content.
            return ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM
        return ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED
    return ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED


def detect_b_shape_conflicts(
    *,
    canonical_path: Path,
    ref: str,
    workspace_root: Path,
    sync_protected: SyncProtected,
    prior_state: StateRecord | None = None,
) -> tuple[ConflictReport, list[str]]:
    """Detect conflicts and produce a ConflictReport.

    Returns a tuple of (report, clean_canonical_paths) where the
    second element lists paths whose canonical content can be staged
    directly (no conflict, no resolver call). The CLI uses that list
    to populate the staging tree's clean-write set.

    ``prior_state`` is the previous sync's StateRecord (read from
    state.yaml). Used only to correlate the *prior canonical sha*
    per-path; the current implementation does not yet snapshot
    per-path SHAs in state.yaml, so when ``prior_state`` is None or
    its ref differs from the current ref's parent, the helper
    treats every both-sides-different case as both-modified
    (conservative — the resolver decides on Class C, the envelope
    decides on Class A/B).
    """
    canonical_paths = _git_ls_tree(canonical_path, ref)

    conflicts: list[ConflictEntry] = []
    clean_writes: list[str] = []
    unchanged = 0
    will_update = 0

    for path in canonical_paths:
        canonical_bytes = _git_show_bytes(canonical_path, ref, path)
        if canonical_bytes is None:
            # ls-tree listed it but show failed — likely a submodule
            # or symlink. Skip; future amendment can surface.
            continue
        canonical_sha = _sha256_bytes(canonical_bytes)

        workspace_path = workspace_root / path
        workspace_sha = _sha256_of_file(workspace_path)

        # prior_sha is conservatively None until per-path snapshotting
        # lands; the classifier treats absent prior as both-sides-
        # changed when canonical and workspace differ.
        prior_sha: str | None = None

        if canonical_sha == workspace_sha:
            unchanged += 1
            continue

        if workspace_sha is None:
            # Workspace lacks the file — clean addition.
            clean_writes.append(path)
            will_update += 1
            continue

        kind = _classify_conflict_kind(
            canonical_sha=canonical_sha,
            workspace_sha=workspace_sha,
            prior_sha=prior_sha,
        )
        if kind is None:
            # Classifier says no conflict (clean update or identical).
            clean_writes.append(path)
            will_update += 1
            continue

        # Build the entry. Class-A pre-resolution: if envelope flags
        # the path as Class A, set Resolution.KEEP_LOCAL directly so
        # the resolver is never called (AC.WS.2 structural).
        klass = sync_protected.classify(path)
        if klass is FileClass.A:
            entry = ConflictEntry(
                path=path,
                prior_release_sha256=prior_sha,
                installed_sha256=workspace_sha,
                new_release_sha256=canonical_sha,
                change_kind=kind,
                resolution=Resolution.KEEP_LOCAL,
                rationale=(
                    "Class A (workspace state): preserved at detection time. "
                    "Sync envelope refuses canonical-side overwrite."
                ),
                confidence=1.0,
            )
        else:
            entry = ConflictEntry(
                path=path,
                prior_release_sha256=prior_sha,
                installed_sha256=workspace_sha,
                new_release_sha256=canonical_sha,
                change_kind=kind,
                resolution=Resolution.PENDING,
            )
        conflicts.append(entry)

    report = ConflictReport(
        sync_ref=ref,
        prior_ref=prior_state.sync_ref if prior_state is not None else None,
        detected_at=_now_iso(),
        conflicts=conflicts,
        summary=ConflictSummary(
            total_framework_files=len(canonical_paths),
            unchanged=unchanged,
            will_update_cleanly=will_update,
            conflicts_requiring_resolution=sum(
                1 for c in conflicts if c.resolution is Resolution.PENDING
            ),
            auto_resolved=sum(
                1 for c in conflicts if c.resolution is not Resolution.PENDING
            ),
        ),
    )

    return report, clean_writes

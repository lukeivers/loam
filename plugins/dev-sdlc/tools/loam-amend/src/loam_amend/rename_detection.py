"""Per-component rename-only detection for ``loam amend apply``.

When a component's diff in the amendment's BASELINE..HEAD window
consists entirely of byte-identical renames (every file ``R100``)
plus apply-step bookkeeping sidecar add/delete pairs, the component's
fence didn't conceptually move and ``apply`` should NOT advance the
BASELINE literal or the ``SEAL_COMMIT`` sidecar. See plan
``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.1.

Algorithm — strict R100 + bookkeeping whitelist:

  1. Run ``git diff --find-renames=99% --name-status <baseline>..<head>
     -- <old_path> <new_path>``. The ``<old_path>`` + ``<new_path>``
     pathspec narrows the diff to the component's two top-level dirs;
     git's rename matcher needs both sides in scope to pair an A under
     ``<new_path>`` with a D under ``<old_path>``.
  2. Any ``M`` (modified) line → False (substantive content edit).
  3. Any ``R<sim>`` with similarity < 100 → False (rename plus content
     edit; HC#4 ``feedback_critical_thinking_on_deviations`` — strict
     reading favours false-negative over false-positive).
  4. Any ``A`` or ``D`` whose leaf basename is NOT in the bookkeeping
     whitelist → False.
  5. Otherwise (every entry is R100 or a whitelisted A/D pair) → True.

Whitelist defaults match the apply-step's own bookkeeping surface:
``SEAL_COMMIT`` (the per-component seal sidecar),
``test_no_sealed_amendments.py`` (the per-component seal-diff test
that carries the BASELINE literal), and ``test_cross_cutting.py``
(hands-off-lifecycle's analog seal-diff test). These are the files
``loam amend apply`` writes when it advances a component's fence —
their delete/create across the rename window is structural, not
substantive.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import NamedTuple


_DEFAULT_BOOKKEEPING_LEAVES: tuple[str, ...] = (
    "SEAL_COMMIT",
    "test_no_sealed_amendments.py",
    "test_cross_cutting.py",
)


class _DiffEntry(NamedTuple):
    """A single ``git diff --name-status`` entry."""

    status: str  # "A" / "D" / "M" / "R100" / "R099" / etc.
    paths: tuple[str, ...]  # 1 path for A/D/M; 2 paths for R<sim>


def _parse_diff_name_status(out: str) -> list[_DiffEntry]:
    """Parse ``git diff --name-status`` output into entries.

    Lines are tab-separated; rename entries carry two trailing paths.
    Empty lines are ignored.
    """
    entries: list[_DiffEntry] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        paths = tuple(parts[1:])
        entries.append(_DiffEntry(status=status, paths=paths))
    return entries


def _git_diff_name_status(
    repo_root: Path, baseline: str, head: str, *path_specs: str
) -> str:
    """Run ``git diff --find-renames=99% --name-status`` over the
    given pathspec union and return raw stdout."""
    cmd = [
        "git",
        "diff",
        "--find-renames=99%",
        "--name-status",
        f"{baseline}..{head}",
        "--",
        *path_specs,
    ]
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def is_rename_only(
    repo_root: Path,
    *,
    baseline: str,
    head: str,
    old_path: str,
    new_path: str,
    bookkeeping_leafnames: tuple[str, ...] = _DEFAULT_BOOKKEEPING_LEAVES,
) -> bool:
    """Return True iff *baseline..head* over (*old_path* ∪ *new_path*)
    is rename-only per the strict R100 + bookkeeping-whitelist rule.

    Parameters
    ----------
    repo_root:
        Workspace root (the cwd for ``git diff``).
    baseline:
        Diff start SHA (typically the manifest's ``baseline``).
    head:
        Diff end SHA (typically the amendment commit, NOT the seal
        commit; finding 5 in d-migration-1-5.md §13 — the seal commit
        carries post-fence-advance machinery the rename-only verdict
        must not see).
    old_path:
        Pre-rename top-level path (e.g. ``"cost-governance/"``).
    new_path:
        Post-rename top-level path (e.g. ``"framework/cost-governance/"``).
    bookkeeping_leafnames:
        Leaf basenames whose A/D entries are admitted as bookkeeping
        rather than counted as substantive. Defaults to the apply-step's
        own sidecar + seal-diff test surface.

    Behaviour
    ---------
    Empty diff (the component has no changes in the window) returns
    **False** — preserves pre-D.1.5 apply semantics for the
    common-case of an amendment whose baseline equals the component's
    last seal (BASELINE..HEAD diff is empty for the unchanged
    component). The standard apply path bumps BASELINE + SEAL_COMMIT
    to ``manifest.baseline`` in that case (HC#1 binding). The
    rename-only branch only fires when there's a genuine all-R100
    rename window inside the diff — i.e., when this amendment
    actually moved the component.
    """
    out = _git_diff_name_status(
        repo_root, baseline, head, old_path, new_path
    )
    entries = _parse_diff_name_status(out)

    # Empty diff → not rename-only (preserve existing apply behaviour
    # — let the standard component loop bump BASELINE + SEAL_COMMIT
    # to manifest.baseline as it has since amendment #22).
    if not entries:
        return False

    # Reject windows with no rename evidence at all (e.g. all-A or
    # all-D). The intent of "rename-only" is "the diff carries renames
    # plus apply-step bookkeeping, nothing else"; a pure all-A window
    # doesn't satisfy that. HC#4 — false-positive worse than
    # false-negative.
    has_rename = any(e.status.startswith("R") for e in entries)
    if not has_rename:
        return False

    # Track A/D leaf basenames so we can verify each non-bookkeeping
    # A has a paired D (and vice versa). We accept any A whose leaf is
    # bookkeeping; same for D. The pairing requirement is satisfied
    # implicitly by the bookkeeping convention (apply writes the new
    # SEAL_COMMIT + seal-test under the new path; the old path's
    # SEAL_COMMIT + seal-test are deleted by the rename. Their leaf
    # basenames match.)
    for entry in entries:
        status = entry.status
        if status == "M":
            return False
        if status.startswith("R"):
            # Strict R100 only. R099 / R<lower> = substantive content
            # edit during rename.
            try:
                sim = int(status[1:])
            except ValueError:
                return False
            if sim < 100:
                return False
            continue
        if status in ("A", "D"):
            if not entry.paths:
                return False
            leaf = Path(entry.paths[0]).name
            if leaf not in bookkeeping_leafnames:
                return False
            continue
        # Any other status (T type-change, U unmerged, X unknown) →
        # substantive (defensive default).
        return False

    return True

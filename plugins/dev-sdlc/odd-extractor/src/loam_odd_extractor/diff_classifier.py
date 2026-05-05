"""Diff-against-prior-contract logic.

Per AC.WATCHOBJ.1 (v0.2.3 Cycle 3) — `classify_evidence(prior_objectives,
prior_backing_map, repo_path)` walks each Objective's backing-map
evidence rows and classifies the objective as still_current /
out_of_date / orphaned at OBJECTIVE altitude.

Heuristic:

  1. **File-existence path:** if any evidence row's ``path`` no longer
     exists at `repo_path / path`, the objective is `orphaned`.
  2. **Line-overlap path (with SHA pin):** for objectives whose
     evidence ``repo_sha`` is set and whose backing rows have
     ``line_range``, check whether the line range was modified between
     the SHA and HEAD via `git log -L`. Any commit between prior_sha +
     HEAD touched the range → out_of_date with
     ``drift_kind="evidence_row_line_changed"``.
  3. **File-history fallback:** when no line_range OR no SHA pin, use
     file-mtime + git history fallback against the prior contract's
     ``repo_sha`` (or ``contract_created_at`` if SHA unavailable). Any
     touch → out_of_date with ``drift_kind="evidence_row_file_changed"``.
  4. **Default to still_current** when none of the above flags fire.

This module is intentionally git-aware but degrades gracefully:
non-git repos use mtime-only checks. The `git` invocation is wrapped
in try/except so missing git or non-repo paths fall back to mtime.

The classifier is pure-deterministic for fixed input given a stable
clock. Idempotency (AC.RELSMOKE.2) depends on this property.

Cycle 3 reframe (v0.2.3): the v0.2.0 AC-altitude classification is
replaced with the objective-altitude classification by swapping the
input list type. v0.1.8 BandedAC is no longer the top-level shape;
:class:`Objective` + :class:`BackingMap` from Cycles 1+2 are.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .spec import BackingMap, EvidenceRowRef, Objective


DriftKind = Literal[
    "evidence_row_line_changed",
    "evidence_row_file_changed",
    "evidence_row_path_missing",
]


# Citation shape: "<file_path>:<start>" or "<file_path>:<start>-<end>"
# or "<file_path>::<test_name>" (test-citation).
_LINE_CITATION_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$"
)
_TEST_CITATION_RE = re.compile(r"^(?P<file>[^:]+)::.+$")


@dataclass(frozen=True)
class OutOfDateObjective:
    """An objective whose backing-row evidence is out-of-date
    relative to the current repo state.

    Per AC.WATCHOBJ.1 — the objective itself is preserved verbatim
    (its text + band did not change); what's stale is the
    backing-implementation map row pointing at code lines that have
    since shifted.

    Fields:

    - ``objective`` — the prior :class:`Objective` (preserved).
    - ``drift_kind`` — discriminator naming why drift was detected.
    - ``affected_rows`` — tuple of :class:`EvidenceRowRef` instances
      that triggered drift detection.
    - ``from_sha`` — prior SHA (when known; None when prior contract
      had no VERIFIED objective with SHA pin).
    - ``to_sha`` — current HEAD SHA at watch-time.
    """

    objective: Objective
    drift_kind: DriftKind
    affected_rows: tuple[EvidenceRowRef, ...]
    from_sha: str | None
    to_sha: str

    @property
    def affected_files(self) -> tuple[str, ...]:
        """Convenience: paths from affected_rows."""
        return tuple(sorted({r.path for r in self.affected_rows}))


@dataclass(frozen=True)
class OrphanedObjective:
    """An objective whose backing-row paths no longer exist on disk."""

    objective: Objective
    missing_evidence_rows: tuple[EvidenceRowRef, ...]

    @property
    def missing_files(self) -> tuple[str, ...]:
        """Convenience: paths from missing_evidence_rows."""
        return tuple(sorted({r.path for r in self.missing_evidence_rows}))


@dataclass(frozen=True)
class EvidenceClassification:
    """Output of :func:`classify_evidence`.

    Per AC.WATCHOBJ.1 — at objective altitude. Three buckets keyed by
    objective rather than AC.
    """

    still_current: tuple[Objective, ...] = field(default_factory=tuple)
    out_of_date: tuple[OutOfDateObjective, ...] = field(default_factory=tuple)
    orphaned: tuple[OrphanedObjective, ...] = field(default_factory=tuple)

    @property
    def still_current_count(self) -> int:
        return len(self.still_current)

    @property
    def out_of_date_count(self) -> int:
        return len(self.out_of_date)

    @property
    def orphaned_count(self) -> int:
        return len(self.orphaned)


# ---- helpers --------------------------------------------------------


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: float = 10.0,
) -> tuple[int, str, str]:
    """Run a git command. Returns (returncode, stdout, stderr).

    Empty/whitespace-only output is normalized; non-zero returncode
    is NOT raised — callers branch on the code.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 127, "", "git unavailable or timed out"


def _is_git_repo(repo_path: Path) -> bool:
    code, _, _ = _run_git(
        ["rev-parse", "--show-toplevel"], cwd=repo_path
    )
    return code == 0


def _current_head_sha(repo_path: Path) -> str | None:
    code, out, _ = _run_git(
        ["rev-parse", "HEAD"], cwd=repo_path
    )
    if code != 0:
        return None
    sha = out.strip()
    return sha or None


def _evidence_row_paths(rows: list[EvidenceRowRef]) -> set[str]:
    """All file paths from a list of evidence rows."""
    return {r.path for r in rows}


def _evidence_row_line_ranges(
    rows: list[EvidenceRowRef],
) -> list[tuple[str, int, int, EvidenceRowRef]]:
    """Per-row (path, start, end, ref) triples for rows with line_range set.

    Rows without ``line_range`` are skipped — they fall through to the
    file-history fallback path.
    """
    out: list[tuple[str, int, int, EvidenceRowRef]] = []
    for r in rows:
        if r.line_range is None:
            continue
        start, end = r.line_range
        out.append((r.path, int(start), int(end), r))
    return out


def _files_missing(
    file_paths: set[str], *, repo_path: Path
) -> set[str]:
    """Return the subset of `file_paths` that don't exist under
    `repo_path`."""
    missing: set[str] = set()
    for fp in file_paths:
        full = repo_path / fp
        if not full.exists():
            missing.add(fp)
    return missing


def _commits_touching_lines(
    *,
    file_path: str,
    start: int,
    end: int,
    from_sha: str | None,
    to_sha: str,
    repo_path: Path,
) -> bool:
    """Return True if any commit between `from_sha` and `to_sha`
    touched lines [start, end] in `file_path`. Uses `git log -L`.

    If `from_sha` is None, the full history of the file up to `to_sha`
    is searched (used when the AC has no SHA pin).
    """
    range_arg = f"{start},{end}:{file_path}"
    args = ["log", "-L", range_arg, "--no-color"]
    if from_sha:
        args.extend([f"{from_sha}..{to_sha}"])
    else:
        args.extend([to_sha])
    args.extend(["--pretty=oneline", "-n", "1"])
    code, out, _ = _run_git(args, cwd=repo_path)
    if code != 0:
        # git log -L can fail on files outside HEAD or with bad
        # SHAs; treat as "no detected change" (defer to backing-files
        # check + file-mtime fallback).
        return False
    return bool(out.strip())


def _commits_touching_file_since_iso(
    *,
    file_path: str,
    since_iso: str,
    repo_path: Path,
) -> bool:
    """Return True if any commit since `since_iso` touched `file_path`."""
    code, out, _ = _run_git(
        [
            "log",
            f"--since={since_iso}",
            "--pretty=oneline",
            "-n",
            "1",
            "--",
            file_path,
        ],
        cwd=repo_path,
    )
    if code != 0:
        return False
    return bool(out.strip())


def _file_mtime_after_iso(
    *, file_path: str, since_iso: str, repo_path: Path
) -> bool:
    """Fallback: file mtime > created_at parsed as ISO."""
    import datetime as _dt

    full = repo_path / file_path
    if not full.exists():
        return False
    try:
        since_dt = _dt.datetime.fromisoformat(since_iso)
    except ValueError:
        return False
    if since_dt.tzinfo is None:
        # Naive comparison; assume UTC.
        since_dt = since_dt.replace(tzinfo=_dt.timezone.utc)
    mtime = _dt.datetime.fromtimestamp(
        full.stat().st_mtime, tz=_dt.timezone.utc
    )
    return mtime > since_dt


# ---- main classifier ------------------------------------------------


def classify_evidence(
    *,
    prior_objectives: list[Objective],
    prior_backing_map: BackingMap,
    repo_path: Path,
    contract_created_at: str,
    current_repo_sha: str | None = None,
) -> EvidenceClassification:
    """Classify each objective in ``prior_objectives`` as still_current /
    out_of_date / orphaned given the current state of ``repo_path``.

    Per AC.WATCHOBJ.1 — at objective altitude. The heuristic walks the
    backing-map's per-objective evidence rows (path + line_range +
    symbol_name) instead of v0.2.0's BandedAC citations:

      - **File-existence** — orphan if any backing-row's ``path`` is missing.
      - **Line-overlap** — out_of_date when an evidence row's
        ``line_range`` was touched between the contract's
        ``repo_sha`` (or the first VERIFIED objective's repo_sha) and
        HEAD via ``git log -L``.
      - **File-history fallback** — out_of_date when an evidence row's
        ``path`` shows commits since ``contract_created_at`` (or mtime
        > created_at when git history is unavailable).
      - **Default to still_current** otherwise.

    HYPOTHESISED objectives whose backing-map entry has zero evidence
    rows (forward-looking; no implementation yet) are still_current
    by definition — they have no rows to drift.

    Pure given a stable clock.
    """
    is_repo = _is_git_repo(repo_path)
    to_sha = current_repo_sha or (
        _current_head_sha(repo_path) if is_repo else None
    )
    if to_sha is None:
        to_sha = "<no-sha>"

    # Build objective_id → evidence rows index.
    rows_by_objective: dict[str, list[EvidenceRowRef]] = {}
    for entry in prior_backing_map.entries:
        rows_by_objective[entry.objective_id] = list(entry.evidence_rows)

    # Pick a global from_sha — first objective with a repo_sha pin.
    from_sha: str | None = None
    for o in prior_objectives:
        if o.evidence.repo_sha:
            from_sha = o.evidence.repo_sha
            break

    still_current: list[Objective] = []
    out_of_date: list[OutOfDateObjective] = []
    orphaned: list[OrphanedObjective] = []

    for objective in prior_objectives:
        rows = rows_by_objective.get(objective.objective_id, [])
        if not rows:
            # No backing rows — nothing to drift. Common for
            # HYPOTHESISED objectives with no impl yet.
            still_current.append(objective)
            continue

        # Step 1 — file-existence (orphan detection per row).
        missing_rows: list[EvidenceRowRef] = []
        for r in rows:
            if not (repo_path / r.path).exists():
                missing_rows.append(r)
        if missing_rows:
            orphaned.append(
                OrphanedObjective(
                    objective=objective,
                    missing_evidence_rows=tuple(missing_rows),
                )
            )
            continue

        # Step 2 — line-overlap path for rows with line_range pinned.
        line_changed_rows: list[EvidenceRowRef] = []
        rows_with_line_ranges: list[EvidenceRowRef] = []
        if is_repo and from_sha:
            for path, start, end, row in _evidence_row_line_ranges(rows):
                rows_with_line_ranges.append(row)
                if _commits_touching_lines(
                    file_path=path,
                    start=start,
                    end=end,
                    from_sha=from_sha,
                    to_sha=to_sha,
                    repo_path=repo_path,
                ):
                    line_changed_rows.append(row)
        if line_changed_rows:
            out_of_date.append(
                OutOfDateObjective(
                    objective=objective,
                    drift_kind="evidence_row_line_changed",
                    affected_rows=tuple(line_changed_rows),
                    from_sha=from_sha,
                    to_sha=to_sha,
                )
            )
            continue

        # If line-range pin path ran on every row (every row had a
        # line_range AND we have from_sha), and reported no drift,
        # the line-overlap result is authoritative — don't fall through
        # to file-history fallback (which uses contract_created_at and
        # would report init-commit as drift for a brand-new contract).
        all_rows_have_line_pin = (
            is_repo
            and from_sha is not None
            and len(rows_with_line_ranges) == len(rows)
            and len(rows) > 0
        )
        if all_rows_have_line_pin:
            still_current.append(objective)
            continue

        # Step 3 — file-history fallback for rows without line_range
        # OR for objectives whose contract has no SHA pin.
        file_changed_rows: list[EvidenceRowRef] = []
        for r in rows:
            # Skip rows that already participated in line-overlap
            # check (they passed; don't re-check via file-history).
            if r in rows_with_line_ranges:
                continue
            touched = False
            if is_repo:
                touched = _commits_touching_file_since_iso(
                    file_path=r.path,
                    since_iso=contract_created_at,
                    repo_path=repo_path,
                )
            if not touched:
                touched = _file_mtime_after_iso(
                    file_path=r.path,
                    since_iso=contract_created_at,
                    repo_path=repo_path,
                )
            if touched:
                file_changed_rows.append(r)
        if file_changed_rows:
            out_of_date.append(
                OutOfDateObjective(
                    objective=objective,
                    drift_kind="evidence_row_file_changed",
                    affected_rows=tuple(file_changed_rows),
                    from_sha=from_sha,
                    to_sha=to_sha,
                )
            )
            continue

        still_current.append(objective)

    return EvidenceClassification(
        still_current=tuple(still_current),
        out_of_date=tuple(out_of_date),
        orphaned=tuple(orphaned),
    )

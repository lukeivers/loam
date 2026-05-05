"""Diff-against-prior-contract logic.

Per AC.WATCH.2 (v0.2.0 Cycle 1) — `classify_evidence(prior_contract,
repo_path)` walks each AC's evidence and classifies it as
still_current / out_of_date / orphaned.

Heuristic (master plan §7.1 most-load-bearing risk; ≥90% accuracy
on synthetic test set):

  1. **File-existence path:** if any backing-file or citation file
     no longer exists at `repo_path / file`, the AC is `orphaned`.
  2. **Line-overlap path (with SHA pin):** for VERIFIED ACs whose
     `evidence.repo_sha` is set, parse each citation of shape
     `<file_path>:<start_line>[-<end_line>]`. For each cited range,
     check whether the range was modified between the SHA and HEAD.
     Cycle 1 uses `git log --follow -L <start>,<end>:<file>` reverse-
     walk; if any commit between prior_sha + HEAD touched the range
     → out_of_date.
  3. **Backing-files heuristic (no SHA pin OR PLAUSIBLE/HYPOTHESISED):**
     when `evidence.repo_sha` is unset, use file-mtime + git history
     fallback. If any backing-file's `git log --since=<contract.created_at>`
     returns commits → out_of_date. If git history unavailable,
     mtime > created_at → out_of_date.
  4. **Default to still_current** when none of the above flags fire.

This module is intentionally git-aware but degrades gracefully:
non-git repos use mtime-only checks. The `git` invocation is wrapped
in try/except so missing git or non-repo paths fall back to mtime.

The classifier is pure-deterministic for fixed input given a stable
clock — running it twice on the same (prior, repo, time) tuple
produces byte-identical output. Idempotency (AC.WATCH.4) depends on
this property.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .bands import BandedAC


DriftKind = Literal["citation_line_changed", "backing_file_changed"]


# Citation shape: "<file_path>:<start>" or "<file_path>:<start>-<end>"
# or "<file_path>::<test_name>" (test-citation).
_LINE_CITATION_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$"
)
_TEST_CITATION_RE = re.compile(r"^(?P<file>[^:]+)::.+$")


@dataclass(frozen=True)
class OutOfDateAC:
    """An AC whose evidence is out-of-date relative to the current
    repo state.

    Fields:

    - `ac` — the prior banded AC (preserved verbatim).
    - `drift_kind` — discriminator naming why drift was detected.
    - `affected_files` — tuple of file paths (relative to repo root)
      that triggered the drift detection.
    - `from_sha` — prior SHA (when known; None for PLAUSIBLE/
      HYPOTHESISED without SHA pin).
    - `to_sha` — current HEAD SHA at watch-time.
    """

    ac: BandedAC
    drift_kind: DriftKind
    affected_files: tuple[str, ...]
    from_sha: str | None
    to_sha: str


@dataclass(frozen=True)
class OrphanedAC:
    """An AC whose backing files / citation files no longer exist."""

    ac: BandedAC
    missing_files: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceClassification:
    """Output of :func:`classify_evidence`."""

    still_current: tuple[BandedAC, ...] = field(default_factory=tuple)
    out_of_date: tuple[OutOfDateAC, ...] = field(default_factory=tuple)
    orphaned: tuple[OrphanedAC, ...] = field(default_factory=tuple)

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


def _file_paths_for_ac(ac: BandedAC) -> set[str]:
    """All file paths an AC references — backing_files +
    citation file-paths (the path before ':' or '::')."""
    out: set[str] = set()
    for bf in ac.backing_files:
        out.add(str(bf))
    for cite in ac.evidence.citations:
        m = _LINE_CITATION_RE.match(cite)
        if m:
            out.add(m.group("file"))
            continue
        m = _TEST_CITATION_RE.match(cite)
        if m:
            out.add(m.group("file"))
            continue
        # Fallback: take the prefix before the first ':'; if no ':',
        # the whole string is treated as a path.
        if ":" in cite:
            out.add(cite.split(":", 1)[0])
        else:
            out.add(cite)
    return out


def _line_citations(ac: BandedAC) -> list[tuple[str, int, int]]:
    """Parse `evidence.citations` for line-citation shape; return a
    list of (file_path, start_line, end_line) tuples. Test-citations
    (`<file>::<name>`) and bare paths are skipped.
    """
    out: list[tuple[str, int, int]] = []
    for cite in ac.evidence.citations:
        m = _LINE_CITATION_RE.match(cite)
        if not m:
            continue
        start = int(m.group("start"))
        end_str = m.group("end")
        end = int(end_str) if end_str else start
        out.append((m.group("file"), start, end))
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
    prior_acs: list[BandedAC],
    repo_path: Path,
    contract_created_at: str,
    current_repo_sha: str | None = None,
) -> EvidenceClassification:
    """Classify each AC in `prior_acs` as still_current / out_of_date
    / orphaned given the current state of `repo_path`.

    Per AC.WATCH.2 — heuristic combines:

      - File-existence (orphaned if any cited file is missing).
      - Line-overlap (out_of_date for VERIFIED ACs with SHA pin if
        cited line range was modified between prior SHA and HEAD).
      - Backing-files git history (out_of_date if any backing-file
        was modified since `contract_created_at`).
      - File-mtime fallback (out_of_date if any backing-file's mtime
        > `contract_created_at`).

    Pure given a stable clock — same (prior_acs, repo state, time)
    tuple produces byte-identical output.
    """
    is_repo = _is_git_repo(repo_path)
    to_sha = current_repo_sha or (
        _current_head_sha(repo_path) if is_repo else None
    )
    if to_sha is None:
        # Non-git or git failure — use a placeholder SHA for the
        # classification record. Out_of_date detection falls back to
        # mtime-only.
        to_sha = "<no-sha>"

    still_current: list[BandedAC] = []
    out_of_date: list[OutOfDateAC] = []
    orphaned: list[OrphanedAC] = []

    for ac in prior_acs:
        all_files = _file_paths_for_ac(ac)
        # Step 1 — file-existence (orphan detection).
        missing = _files_missing(all_files, repo_path=repo_path)
        if missing:
            orphaned.append(
                OrphanedAC(
                    ac=ac,
                    missing_files=tuple(sorted(missing)),
                )
            )
            continue

        # Step 2 — line-overlap path (VERIFIED + SHA pin + git repo).
        from_sha = ac.evidence.repo_sha
        line_drift_files: set[str] = set()
        if is_repo and from_sha and ac.evidence.kind == "test":
            for fp, start, end in _line_citations(ac):
                if _commits_touching_lines(
                    file_path=fp,
                    start=start,
                    end=end,
                    from_sha=from_sha,
                    to_sha=to_sha,
                    repo_path=repo_path,
                ):
                    line_drift_files.add(fp)
        if line_drift_files:
            out_of_date.append(
                OutOfDateAC(
                    ac=ac,
                    drift_kind="citation_line_changed",
                    affected_files=tuple(sorted(line_drift_files)),
                    from_sha=from_sha,
                    to_sha=to_sha,
                )
            )
            continue

        # Step 3 — backing-files heuristic (git history + mtime
        # fallback).
        backing_drift_files: set[str] = set()
        for bf in ac.backing_files:
            bf_str = str(bf)
            touched = False
            if is_repo:
                touched = _commits_touching_file_since_iso(
                    file_path=bf_str,
                    since_iso=contract_created_at,
                    repo_path=repo_path,
                )
            if not touched:
                touched = _file_mtime_after_iso(
                    file_path=bf_str,
                    since_iso=contract_created_at,
                    repo_path=repo_path,
                )
            if touched:
                backing_drift_files.add(bf_str)
        # Also check citation files when no backing_files exist OR
        # when no backing-file drift was detected. This covers ACs
        # whose only file reference is a citation.
        if not backing_drift_files:
            citation_files = {
                fp for fp, _, _ in _line_citations(ac)
            }
            for fp in citation_files - {
                str(b) for b in ac.backing_files
            }:
                touched = False
                if is_repo:
                    touched = _commits_touching_file_since_iso(
                        file_path=fp,
                        since_iso=contract_created_at,
                        repo_path=repo_path,
                    )
                if not touched:
                    touched = _file_mtime_after_iso(
                        file_path=fp,
                        since_iso=contract_created_at,
                        repo_path=repo_path,
                    )
                if touched:
                    backing_drift_files.add(fp)
        if backing_drift_files:
            out_of_date.append(
                OutOfDateAC(
                    ac=ac,
                    drift_kind="backing_file_changed",
                    affected_files=tuple(
                        sorted(backing_drift_files)
                    ),
                    from_sha=from_sha,
                    to_sha=to_sha,
                )
            )
            continue

        # Step 4 — default still_current.
        still_current.append(ac)

    return EvidenceClassification(
        still_current=tuple(still_current),
        out_of_date=tuple(out_of_date),
        orphaned=tuple(orphaned),
    )

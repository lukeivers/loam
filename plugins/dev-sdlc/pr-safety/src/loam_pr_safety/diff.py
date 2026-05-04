"""Git-diff wrapper for loam-pr-safety.

Per AC.PRSG.3 — wraps ``git diff --unified=0 --no-color
[<sha1>..<sha2>]`` and parses the output into typed
:class:`Diff` / :class:`DiffEntry` / :class:`Hunk` records.

Working-tree-vs-HEAD: when both ``from_sha`` and ``to_sha`` are
``None``, runs ``git diff --unified=0 --no-color HEAD`` (working
tree against current HEAD, including unstaged changes).

The parser handles the standard unified-diff format:

  diff --git a/path b/path
  ... (header lines)
  --- a/path
  +++ b/path
  @@ -<old_start>,<old_lines> +<new_start>,<new_lines> @@
  -removed line
  +added line

When ``old_lines`` or ``new_lines`` is omitted in the hunk header, it
defaults to 1 per the unified-diff spec (e.g., ``@@ -10 +10 @@`` is
``-10,1 +10,1``).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from loam_pr_safety.errors import GateError
from loam_pr_safety.spec import Diff, DiffEntry, Hunk


_HUNK_HEADER_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@"
)
_DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
_NEW_FILE_RE = re.compile(r"^new file mode \d+$")
_DELETED_FILE_RE = re.compile(r"^deleted file mode \d+$")


def parse_diff(
    repo_path: Path,
    from_sha: str | None = None,
    to_sha: str | None = None,
) -> Diff:
    """Run ``git diff`` and parse the output into a :class:`Diff`.

    When both SHAs are ``None``, diffs working tree against ``HEAD``.
    Otherwise: ``<from_sha>..<to_sha>``.

    Raises :class:`GateError` on git invocation failure or unparseable
    output.
    """
    repo_path = repo_path.expanduser().resolve()
    cmd = ["git", "-C", str(repo_path), "diff", "--unified=0", "--no-color"]
    if from_sha is not None and to_sha is not None:
        cmd.append(f"{from_sha}..{to_sha}")
    elif from_sha is not None:
        cmd.append(from_sha)
    elif to_sha is not None:
        cmd.append(to_sha)
    # both None → working tree vs HEAD (default `git diff` invocation
    # already does this when no ref is supplied).

    try:
        proc = subprocess.run(  # noqa: S603 — controlled command
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GateError(
            "git executable not found on PATH"
        ) from exc
    if proc.returncode != 0:
        # Some return codes are non-fatal (e.g., 1 means "differences
        # found"), but git diff exit codes are 0 (no diff) or 1
        # (diff present); higher codes indicate errors.
        if proc.returncode > 1:
            raise GateError(
                f"git diff failed (exit {proc.returncode}): "
                f"{proc.stderr.strip()}"
            )
    return parse_unified_diff(
        proc.stdout, from_sha=from_sha, to_sha=to_sha
    )


def parse_unified_diff(
    text: str,
    *,
    from_sha: str | None = None,
    to_sha: str | None = None,
) -> Diff:
    """Parse unified-diff text into a :class:`Diff`.

    Pure parser — no subprocess invocation. Used by
    :func:`parse_diff` and directly by tests against synthetic
    fixtures.
    """
    entries: list[DiffEntry] = []
    current_entry: DiffEntry | None = None
    current_hunk: Hunk | None = None

    def _flush_hunk() -> None:
        nonlocal current_hunk
        if current_hunk is not None and current_entry is not None:
            current_entry.hunks.append(current_hunk)
            current_hunk = None

    def _flush_entry() -> None:
        nonlocal current_entry
        _flush_hunk()
        if current_entry is not None:
            entries.append(current_entry)
            current_entry = None

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m_diff = _DIFF_GIT_RE.match(line)
        if m_diff is not None:
            _flush_entry()
            file_path = Path(m_diff.group(2))
            current_entry = DiffEntry(file_path=file_path)
            i += 1
            continue
        if current_entry is not None and _NEW_FILE_RE.match(line):
            current_entry.is_new_file = True
            i += 1
            continue
        if current_entry is not None and _DELETED_FILE_RE.match(line):
            current_entry.is_deleted_file = True
            i += 1
            continue
        m_hunk = _HUNK_HEADER_RE.match(line)
        if m_hunk is not None:
            _flush_hunk()
            old_start = int(m_hunk.group(1))
            old_lines = int(m_hunk.group(2)) if m_hunk.group(2) else 1
            new_start = int(m_hunk.group(3))
            new_lines = int(m_hunk.group(4)) if m_hunk.group(4) else 1
            current_hunk = Hunk(
                old_start=old_start,
                old_lines=old_lines,
                new_start=new_start,
                new_lines=new_lines,
            )
            i += 1
            continue
        if current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.added_lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.removed_lines.append(line[1:])
            # Context lines (starting with " ") shouldn't appear with
            # --unified=0; ignore if they do.
        i += 1

    _flush_entry()

    return Diff(
        from_sha=from_sha,
        to_sha=to_sha,
        entries=entries,
    )

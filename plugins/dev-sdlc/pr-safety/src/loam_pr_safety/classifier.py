"""Diff classifier for loam-pr-safety.

Per AC.PRSG.3 — given a :class:`Diff` and a :class:`BandedContract`,
classify each touched AC and identify novel candidates.

Heuristic:

  - **Line-overlap path:** for each AC, parse ``evidence.citations``
    for entries of shape ``<file_path>:<start_line>[-<end_line>]``
    (or ``<file_path>::<test_name>`` — these match by file_path
    only, since test-citations don't carry line numbers).
    For each diff entry, mark the AC as touched (``touch_kind=
    "citation_line"``) if any cited (file, line-range) intersects
    the diff's hunk ranges.

  - **Symbol-overlap path:** for each AC, treat ``backing_files``
    as a softer match — if a diff entry touches any of
    ``ac.backing_files`` AND the AC wasn't already line-touched,
    mark the AC as touched (``touch_kind="backing_file"``).

  - **Novel path:** any added/removed line in the diff that doesn't
    fall within any AC's citation range AND lives in a file not in
    any AC's ``backing_files`` is a novel candidate. Aggregated
    per-file as :class:`CandidateAC`.

  - **Untouched signal:** ``untouched=True`` iff no AC is touched
    AND no novel candidates exist.

Citation-parsing rules (line-overlap):

  - ``"<path>:<n>"`` — single-line citation; range = ``[n, n]``.
  - ``"<path>:<a>-<b>"`` — range citation; range = ``[a, b]``.
  - ``"<path>::<test_name>"`` — test citation; matched by file_path
    only (no line range). Line-overlap path doesn't fire for this
    shape; backing-files path may.
  - ``"<path>"`` (no colon) — file-level citation; same as test
    citation (file-level match).
  - Unparseable shape — skipped (logged in audit if needed).

Path matching (line-overlap + backing-files):

  - Comparison is by string-equality on the trailing path segments.
    A diff entry with ``file_path = "src/foo.py"`` matches a
    citation/backing file equal to ``"src/foo.py"`` exactly. Path
    normalization (resolving ``./``, ``../``) is applied via
    ``PurePosixPath`` for cross-platform stability.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Optional

from loam_pr_safety.spec import (
    BandedContract,
    CandidateAC,
    ClassificationResult,
    Diff,
    DiffEntry,
    Hunk,
    TouchedAC,
)


_CITATION_LINE_RANGE_RE = re.compile(
    r"^(?P<path>[^:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$"
)
_CITATION_TEST_RE = re.compile(
    r"^(?P<path>[^:]+)::(?P<test_name>.+)$"
)


def _normalise_path(p: str) -> str:
    """Normalise a path string for cross-platform comparison."""
    return str(PurePosixPath(p))


def _parse_citation_line_range(
    citation: str,
) -> Optional[tuple[str, int, int]]:
    """Parse a citation as a (file_path, start_line, end_line) tuple.

    Returns ``None`` when the citation is a test citation
    (``<path>::<test_name>``) or a file-only reference (no colon).
    """
    # Test-citation shape — file_path::test_name (no line numbers).
    m_test = _CITATION_TEST_RE.match(citation)
    if m_test is not None:
        return None
    # Line-range shape — file:start[-end].
    m_line = _CITATION_LINE_RANGE_RE.match(citation)
    if m_line is None:
        return None
    path = _normalise_path(m_line.group("path"))
    start = int(m_line.group("start"))
    end = int(m_line.group("end")) if m_line.group("end") else start
    return (path, start, end)


def _parse_citation_file(citation: str) -> str | None:
    """Return the file_path component of a citation, regardless of
    whether the citation carries line numbers / test names / nothing.

    Used by the backing-files (symbol-overlap) path — even when the
    line-range parse returns ``None`` (test citation), we still want
    the file-level match.
    """
    # File-level citation (no colon).
    if ":" not in citation:
        return _normalise_path(citation)
    # Test citation shape.
    m_test = _CITATION_TEST_RE.match(citation)
    if m_test is not None:
        return _normalise_path(m_test.group("path"))
    # Line-range shape.
    m_line = _CITATION_LINE_RANGE_RE.match(citation)
    if m_line is not None:
        return _normalise_path(m_line.group("path"))
    return None


def _hunk_old_intersects(
    hunk: Hunk, start: int, end: int
) -> bool:
    """Return True iff the hunk's old-side range intersects ``[start, end]``."""
    if hunk.old_lines == 0:
        # Pure-addition hunk; treat as not intersecting old-range.
        return False
    h_start = hunk.old_start
    h_end = hunk.old_start + hunk.old_lines - 1
    return not (h_end < start or h_start > end)


def _hunk_new_intersects(
    hunk: Hunk, start: int, end: int
) -> bool:
    """Return True iff the hunk's new-side range intersects ``[start, end]``."""
    if hunk.new_lines == 0:
        return False
    h_start = hunk.new_start
    h_end = hunk.new_start + hunk.new_lines - 1
    return not (h_end < start or h_start > end)


def _hunk_intersects_range(
    hunk: Hunk, start: int, end: int
) -> bool:
    """Either old-side OR new-side intersects ``[start, end]``."""
    return _hunk_old_intersects(hunk, start, end) or _hunk_new_intersects(
        hunk, start, end
    )


def _find_diff_entry(diff: Diff, file_path: str) -> DiffEntry | None:
    """Return the diff entry for ``file_path`` (normalised) or None."""
    for entry in diff.entries:
        if _normalise_path(str(entry.file_path)) == file_path:
            return entry
    return None


def classify(
    diff: Diff,
    contract: BandedContract,
) -> ClassificationResult:
    """Classify ``diff`` against ``contract``.

    Returns :class:`ClassificationResult` with:
      - ``touched_acs`` — list of :class:`TouchedAC` (line-overlap or
        backing-file).
      - ``untouched`` — True iff ``touched_acs`` is empty AND
        ``novel`` is empty.
      - ``novel`` — list of :class:`CandidateAC` (per-file).
    """
    touched_acs: list[TouchedAC] = []
    touched_ac_ids: set[str] = set()
    # Track which (file_path, hunk) pairs are mapped to ACs (for novel
    # detection). A hunk is "mapped" if it intersects any AC's
    # citation range OR if its file is in any AC's backing_files.
    mapped_hunk_keys: set[tuple[str, int, int]] = set()
    # All cited file paths + backing-file paths across all ACs (for
    # the novel-detection shortcut).
    citation_file_paths: set[str] = set()
    backing_file_paths: set[str] = set()

    for ac in contract.acs:
        ac_touched = False
        line_touched_hunks: list[Hunk] = []
        # Line-overlap path.
        for cite in ac.evidence.citations:
            parsed_line = _parse_citation_line_range(cite)
            cited_file = _parse_citation_file(cite)
            if cited_file is not None:
                citation_file_paths.add(cited_file)
            if parsed_line is None:
                continue
            cited_path, cite_start, cite_end = parsed_line
            entry = _find_diff_entry(diff, cited_path)
            if entry is None:
                continue
            for hunk in entry.hunks:
                if _hunk_intersects_range(hunk, cite_start, cite_end):
                    line_touched_hunks.append(hunk)
                    ac_touched = True
                    mapped_hunk_keys.add(
                        (cited_path, hunk.new_start, hunk.new_lines)
                    )
        if ac_touched:
            touched_acs.append(
                TouchedAC(
                    ac=ac,
                    touch_kind="citation_line",
                    touched_hunks=line_touched_hunks,
                )
            )
            touched_ac_ids.add(ac.ac_id)

        # Backing-files (symbol-overlap) path — only fires if
        # line-overlap didn't.
        for bf in ac.backing_files:
            bf_norm = _normalise_path(str(bf))
            backing_file_paths.add(bf_norm)
            if ac.ac_id in touched_ac_ids:
                # already captured via line-overlap.
                continue
            entry = _find_diff_entry(diff, bf_norm)
            if entry is None:
                continue
            if entry.hunks:
                touched_acs.append(
                    TouchedAC(
                        ac=ac,
                        touch_kind="backing_file",
                        touched_hunks=list(entry.hunks),
                    )
                )
                touched_ac_ids.add(ac.ac_id)
                for hunk in entry.hunks:
                    mapped_hunk_keys.add(
                        (bf_norm, hunk.new_start, hunk.new_lines)
                    )
                # Found one backing-file match; sufficient.
                break

    # Novel detection — any diff entry's hunks that aren't mapped to
    # any AC's citation range AND whose file isn't in any AC's
    # citation files OR backing files become a novel candidate.
    novel: list[CandidateAC] = []
    for entry in diff.entries:
        entry_path = _normalise_path(str(entry.file_path))
        # File is mapped if it appears in any AC's citation files
        # OR backing files.
        file_is_mapped = (
            entry_path in citation_file_paths
            or entry_path in backing_file_paths
        )
        unmapped_hunks: list[Hunk] = []
        for hunk in entry.hunks:
            hunk_key = (entry_path, hunk.new_start, hunk.new_lines)
            if hunk_key in mapped_hunk_keys:
                continue
            if file_is_mapped:
                # File is mapped to at least one AC, but THIS hunk
                # didn't overlap the AC's line range. Not novel —
                # the file is contract-covered; the diff just edits
                # uncovered lines within it. Cycle 1 treats this as
                # PASS (not novel; not touched). The reviewer can
                # surface awareness via Cycle 2's PR-description
                # template if needed.
                continue
            unmapped_hunks.append(hunk)
        if unmapped_hunks:
            novel.append(
                CandidateAC(
                    file_path=entry.file_path,
                    hunks=unmapped_hunks,
                )
            )

    untouched = not touched_acs and not novel

    return ClassificationResult(
        touched_acs=touched_acs,
        untouched=untouched,
        novel=novel,
    )

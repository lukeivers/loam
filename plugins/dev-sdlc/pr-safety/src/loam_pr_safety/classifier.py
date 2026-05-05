"""Diff classifier for loam-pr-safety.

Per AC.PRGATE.2 (v0.2.3 Cycle 3) — given a :class:`Diff` and a
:class:`BandedContract`, classify each touched objective at OBJECTIVE
altitude by walking the backing-map's per-objective evidence rows.

Heuristic:

  - **Line-overlap path:** for each objective, walk the
    backing-map's evidence rows; for rows with a ``line_range``,
    check whether any diff hunk intersects the row's range. Mark
    the objective as touched (``touch_kind="evidence_line"``).

  - **File-overlap path:** rows without ``line_range`` (or rows whose
    line range didn't intersect any hunk) match by file path only.
    If a diff entry touches a row's file AND the objective wasn't
    already line-touched, mark the objective as touched
    (``touch_kind="evidence_file"``).

  - **Novel-diff path:** any diff hunk whose file isn't in any
    objective's backing rows is a novel diff. Aggregated per-file
    as :class:`NovelDiff`.

  - **Untouched signal:** ``untouched=True`` iff no objective is
    touched AND no novel diffs exist.

Path matching:

  - Comparison is by string-equality on POSIX-normalized path
    segments. ``PurePosixPath`` provides cross-platform stability.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from loam_odd_extractor.spec import EvidenceRowRef

from loam_pr_safety.spec import (
    BandedContract,
    ClassificationResult,
    Diff,
    DiffEntry,
    Hunk,
    NovelDiff,
    TouchedObjective,
)


def _normalise_path(p: str) -> str:
    """Normalise a path string for cross-platform comparison."""
    return str(PurePosixPath(p))


def _hunk_old_intersects(
    hunk: Hunk, start: int, end: int
) -> bool:
    """True iff the hunk's old-side range intersects ``[start, end]``."""
    if hunk.old_lines == 0:
        return False
    h_start = hunk.old_start
    h_end = hunk.old_start + hunk.old_lines - 1
    return not (h_end < start or h_start > end)


def _hunk_new_intersects(
    hunk: Hunk, start: int, end: int
) -> bool:
    """True iff the hunk's new-side range intersects ``[start, end]``."""
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

    Per AC.PRGATE.2 — at objective altitude. Walks
    ``contract.backing_map.entries`` (objective_id → evidence rows)
    and emits :class:`TouchedObjective` per matched objective +
    :class:`NovelDiff` per unmapped diff entry.

    Returns :class:`ClassificationResult`.
    """
    touched_objectives: list[TouchedObjective] = []
    touched_objective_ids: set[str] = set()

    # Track which (file_path, hunk-key) pairs are mapped to objectives
    # for novel detection.
    mapped_hunk_keys: set[tuple[str, int, int]] = set()
    # All cited file paths across all backing rows (novel-detection
    # shortcut).
    backing_file_paths: set[str] = set()

    # Build objective_id → Objective map for fast lookup.
    objectives_by_id = {o.objective_id: o for o in contract.objectives}

    for entry in contract.backing_map.entries:
        objective = objectives_by_id.get(entry.objective_id)
        if objective is None:
            # Defensive: backing-map has an entry for an objective not
            # present in the objective list (shouldn't happen post-
            # Cycle 2 backing-map populator, but tolerate gracefully).
            continue

        line_touched_rows: list[EvidenceRowRef] = []
        line_touched_hunks_set: list[Hunk] = []
        objective_touched = False

        # Track all paths from this objective's backing rows.
        for row in entry.evidence_rows:
            row_path = _normalise_path(row.path)
            backing_file_paths.add(row_path)

        # Line-overlap path.
        for row in entry.evidence_rows:
            if row.line_range is None:
                continue
            row_path = _normalise_path(row.path)
            cite_start, cite_end = row.line_range
            diff_entry = _find_diff_entry(diff, row_path)
            if diff_entry is None:
                continue
            for hunk in diff_entry.hunks:
                if _hunk_intersects_range(hunk, cite_start, cite_end):
                    line_touched_rows.append(row)
                    line_touched_hunks_set.append(hunk)
                    objective_touched = True
                    mapped_hunk_keys.add(
                        (row_path, hunk.new_start, hunk.new_lines)
                    )

        if objective_touched:
            touched_objectives.append(
                TouchedObjective(
                    objective=objective,
                    touch_kind="evidence_line",
                    touched_evidence_rows=line_touched_rows,
                    touched_hunks=line_touched_hunks_set,
                )
            )
            touched_objective_ids.add(objective.objective_id)
            continue

        # File-overlap path — only fires for rows WITHOUT a line_range
        # pin (file-level matches). Rows with line_range that didn't
        # intersect any hunk indicate the diff is on uncovered lines
        # within a contract-covered file: not touched (file is mapped
        # but THIS hunk doesn't overlap the row's range). Mirrors the
        # v0.1.9 PASS semantics for file-mapped + hunk-on-uncovered-
        # lines.
        file_touched_rows: list[EvidenceRowRef] = []
        file_touched_hunks: list[Hunk] = []
        for row in entry.evidence_rows:
            if row.line_range is not None:
                # Line-pin rows already considered in line-overlap path.
                continue
            row_path = _normalise_path(row.path)
            if objective.objective_id in touched_objective_ids:
                break
            diff_entry = _find_diff_entry(diff, row_path)
            if diff_entry is None:
                continue
            if diff_entry.hunks:
                file_touched_rows.append(row)
                file_touched_hunks.extend(diff_entry.hunks)
                touched_objective_ids.add(objective.objective_id)
                for hunk in diff_entry.hunks:
                    mapped_hunk_keys.add(
                        (row_path, hunk.new_start, hunk.new_lines)
                    )
                break

        if file_touched_rows:
            touched_objectives.append(
                TouchedObjective(
                    objective=objective,
                    touch_kind="evidence_file",
                    touched_evidence_rows=file_touched_rows,
                    touched_hunks=file_touched_hunks,
                )
            )

    # Novel detection — diff hunks whose file isn't in any backing
    # row become novel.
    novel: list[NovelDiff] = []
    for diff_entry in diff.entries:
        entry_path = _normalise_path(str(diff_entry.file_path))
        file_is_mapped = entry_path in backing_file_paths
        unmapped_hunks: list[Hunk] = []
        for hunk in diff_entry.hunks:
            hunk_key = (entry_path, hunk.new_start, hunk.new_lines)
            if hunk_key in mapped_hunk_keys:
                continue
            if file_is_mapped:
                # File contract-covered; this hunk just edited
                # uncovered lines within. Cycle 3 PASSes (not novel).
                continue
            unmapped_hunks.append(hunk)
        if unmapped_hunks:
            novel.append(
                NovelDiff(
                    file_path=diff_entry.file_path,
                    hunks=unmapped_hunks,
                )
            )

    untouched = not touched_objectives and not novel

    return ClassificationResult(
        touched_objectives=touched_objectives,
        untouched=untouched,
        novel=novel,
    )

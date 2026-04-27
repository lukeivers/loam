"""Filename-based classification of pos-v2 launchd plists.

Backs AC1 (orphan detection by label-pattern) and AC5 (positive guard
on workspace-slug-namespaced plists).

The classifier is a pure function on the filename. The on-disk scan
walks ``~/Library/LaunchAgents/`` and yields the orphans it finds.
We deliberately do NOT parse the plist's XML body to determine
orphan-ness — the filename convention from amendment #6 (filename
matches label) is load-bearing and the discriminator is the segment
count after the ``com.pos-v2.`` prefix.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator


class Classification(Enum):
    """How a filename in LaunchAgents/ relates to pos-v2's plist scheme.

    - ``ORPHAN_V2``: ``com.pos-v2.<single-segment>.plist`` — pre-#6
      pos-v2 shape with no workspace slug. Targeted for remediation.
    - ``ORPHAN_V1``: ``com.pos.<single-segment>.plist`` — pre-pos-v2
      v1-era shape (e.g. ``com.pos.orchestrator``). Also targeted for
      remediation.
    - ``NAMESPACED_V2``: ``com.pos-v2.<slug>.<kind>.plist`` — current
      workspace-slug-namespaced shape. Belongs to a live workspace;
      MUST NOT be touched (AC5).
    - ``NOT_POS_V2``: anything else (``com.apple.*``, user plists, etc).
    """

    ORPHAN_V2 = "orphan_v2"
    ORPHAN_V1 = "orphan_v1"
    NAMESPACED_V2 = "namespaced_v2"
    NOT_POS_V2 = "not_pos_v2"


@dataclass(frozen=True)
class DetectedOrphan:
    """An orphan plist on disk: its path, its launchd label, and the
    classification that flagged it."""

    path: Path
    label: str
    classification: Classification


def _strip_plist_suffix(name: str) -> str | None:
    """Return ``name`` minus a trailing ``.plist``, or ``None`` if the
    file is not a plist."""
    if not name.endswith(".plist"):
        return None
    return name[: -len(".plist")]


def classify_filename(name: str) -> Classification:
    """Classify a single LaunchAgents filename.

    The filename (not full path) is the input. Comparison is on the
    label segments — i.e. the filename minus the ``.plist`` suffix.
    """
    label = _strip_plist_suffix(name)
    if label is None:
        return Classification.NOT_POS_V2
    segments = label.split(".")
    # ``com.pos-v2.<slug>.<kind>`` -> 4 segments
    # ``com.pos-v2.<single>`` -> 3 segments
    # ``com.pos.<single>`` -> 3 segments
    if len(segments) >= 2 and segments[0] == "com" and segments[1] == "pos-v2":
        # 4 segments => namespaced; 3 segments => orphan v2; anything
        # else (5+) is not the shape pos-v2 ever wrote, leave alone.
        if len(segments) == 4:
            return Classification.NAMESPACED_V2
        if len(segments) == 3:
            return Classification.ORPHAN_V2
        return Classification.NOT_POS_V2
    if len(segments) == 3 and segments[0] == "com" and segments[1] == "pos":
        # ``com.pos.<single>`` — pre-pos-v2 v1 shape.
        return Classification.ORPHAN_V1
    return Classification.NOT_POS_V2


def is_orphan(classification: Classification) -> bool:
    """Predicate: does this classification warrant remediation?"""
    return classification in (Classification.ORPHAN_V2, Classification.ORPHAN_V1)


def scan(launch_agents_dir: Path) -> Iterator[DetectedOrphan]:
    """Walk ``launch_agents_dir`` and yield each orphan plist found.

    Only top-level entries are considered — LaunchAgents is not
    nested in practice, and recursing into subdirectories would
    risk unrelated user plist directories.

    Files whose classification is ``NAMESPACED_V2`` or ``NOT_POS_V2``
    are silently skipped — those are AC5's positive guard and the
    "leave unrelated plists alone" baseline.
    """
    if not launch_agents_dir.is_dir():
        return
    for entry in sorted(launch_agents_dir.iterdir()):
        if not entry.is_file():
            continue
        classification = classify_filename(entry.name)
        if not is_orphan(classification):
            continue
        label = _strip_plist_suffix(entry.name)
        # ``label`` is non-None here because is_orphan() implies a
        # ``.plist`` suffix.
        assert label is not None
        yield DetectedOrphan(
            path=entry, label=label, classification=classification
        )

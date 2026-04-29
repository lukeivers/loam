"""Filename-based classification of loam launchd plists.

Backs AC1 (orphan detection by label-pattern) and AC5 (positive guard
on workspace-slug-namespaced plists).

The classifier is a pure function on the filename. The on-disk scan
walks ``~/Library/LaunchAgents/`` and yields the orphans it finds.
We deliberately do NOT parse the plist's XML body to determine
orphan-ness — the filename convention from amendment #6 (filename
matches label) is load-bearing and the discriminator is the segment
count after the ``com.loam.`` prefix (post-M1c live shape) or the
``com.pos-v2.`` / ``com.pos.`` prefixes (archaeological pre-M1c shapes
that the orphan-detection arms continue to remediate).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator


class Classification(Enum):
    """How a filename in LaunchAgents/ relates to loam's plist scheme.

    - ``ORPHAN_V2``: ``com.pos-v2.<single-segment>.plist`` — pre-#6
      pre-M1c shape with no workspace slug. Targeted for remediation.
      The ``pos-v2`` literal here is archaeological — it identifies
      the historical filename shape the tool detects, not the brand.
    - ``ORPHAN_V1``: ``com.pos.<single-segment>.plist`` — pre-pos-v2
      v1-era shape (e.g. ``com.pos.orchestrator``). Also targeted for
      remediation. The ``pos`` literal is also archaeological.
    - ``NAMESPACED``: ``com.loam.<slug>.<kind>.plist`` — current post-
      M1c workspace-slug-namespaced shape. Belongs to a live workspace;
      MUST NOT be touched (AC5).
    - ``NOT_LOAM``: anything else (``com.apple.*``, user plists, the
      pre-M1c live shape ``com.pos-v2.<slug>.<kind>.plist`` — that
      transition is owned by the M1c migration helper at
      ``framework/tools/loam-migrate-launchd-labels/``, not this tool).
    """

    ORPHAN_V2 = "orphan_v2"
    ORPHAN_V1 = "orphan_v1"
    NAMESPACED = "namespaced"
    NOT_LOAM = "not_loam"


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
        return Classification.NOT_LOAM
    segments = label.split(".")
    # Post-M1c live shape:
    #   ``com.loam.<slug>.<kind>``  -> 4 segments  (NAMESPACED)
    # Archaeological pre-M1c orphan shapes (still remediated):
    #   ``com.pos-v2.<single>``     -> 3 segments  (ORPHAN_V2)
    #   ``com.pos.<single>``        -> 3 segments  (ORPHAN_V1)
    if len(segments) == 4 and segments[0] == "com" and segments[1] == "loam":
        return Classification.NAMESPACED
    if len(segments) >= 2 and segments[0] == "com" and segments[1] == "pos-v2":
        # 3 segments => archaeological orphan_v2; anything else (4+,
        # including the pre-M1c-live com.pos-v2.<slug>.<kind> 4-segment
        # shape) is not this tool's mission. The pre-M1c-live shape's
        # transition is owned by the M1c migration helper at
        # framework/tools/loam-migrate-launchd-labels/.
        if len(segments) == 3:
            return Classification.ORPHAN_V2
        return Classification.NOT_LOAM
    if len(segments) == 3 and segments[0] == "com" and segments[1] == "pos":
        # ``com.pos.<single>`` — pre-pos-v2 v1 shape.
        return Classification.ORPHAN_V1
    return Classification.NOT_LOAM


def is_orphan(classification: Classification) -> bool:
    """Predicate: does this classification warrant remediation?"""
    return classification in (Classification.ORPHAN_V2, Classification.ORPHAN_V1)


def scan(launch_agents_dir: Path) -> Iterator[DetectedOrphan]:
    """Walk ``launch_agents_dir`` and yield each orphan plist found.

    Only top-level entries are considered — LaunchAgents is not
    nested in practice, and recursing into subdirectories would
    risk unrelated user plist directories.

    Files whose classification is ``NAMESPACED`` or ``NOT_LOAM``
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

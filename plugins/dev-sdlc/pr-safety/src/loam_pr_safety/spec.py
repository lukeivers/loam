"""Pydantic models for loam-pr-safety.

Per v0.2.3 Cycle 3 + sub-plan-doc §3 — the typed contract surface
operates at OBJECTIVE altitude. The v0.1.9 BandedAC-shaped contract
is replaced with the Objective + BackingMap shape produced by Cycle
1 + Cycle 2.

Per Surface #7 (v0.1.9 plan-doc §5) — all models use
``ConfigDict(extra='forbid')`` so additional fields are rejected at
parse time.

The shape:

  - :class:`BandedContract` — read of the odd-extractor's typed
    objectives (from ``objectives.yaml``) + backing-implementation
    map (from ``backing-map.yaml``).
  - :class:`Hunk`, :class:`DiffEntry`, :class:`Diff` — typed
    representation of ``git diff --unified=0`` output (preserved).
  - :class:`TouchedObjective`, :class:`NovelDiff`,
    :class:`ClassificationResult` — classifier output at objective
    altitude.
  - :class:`GateAction`, :class:`GateDecision` — gate output.
  - :class:`OverrideRequest` — override-flow request payload at
    objective altitude.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from loam_odd_extractor.spec import (
    BackingMap,
    EvidenceRowRef,
    Objective,
)


# ---- BandedContract (Stage 1: read-contract output) ----------------


class BandedContract(BaseModel):
    """Typed read of the odd-extractor's objectives + backing-map.

    Per AC.PRGATE.1 — composes
    ``<workspace>/.loam/extractions/<repo-id>/objectives.yaml`` with
    ``<workspace>/.loam/extractions/<repo-id>/backing-map.yaml`` plus
    any approved-override overlays at
    ``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``.

    Composition is deterministic: read objectives + backing-map, then
    apply overlays in sorted order. Each overlay either:

      - Replaces an original-VERIFIED-objective with a new (typically
        PLAUSIBLE) Objective row (kind=replace_verified_objective), or
      - Records audit-only state (kind=audit_only) — Cycle 3 simplification:
        novel-diff promotion to Objective is deferred to v0.2.4
        gap-analysis.

    Fields:

    - ``extraction_id`` — repo-id (``<basename>-<8-char-sha256>``).
    - ``repo_path`` — absolute path; informational.
    - ``repo_sha`` — SHA from the first VERIFIED objective with a pin
      (informational; may be ``None``).
    - ``objectives`` — typed :class:`Objective` rows (per-band evidence
      rules enforced at construction).
    - ``backing_map`` — typed :class:`BackingMap` (per-objective
      evidence-row index).
    - ``unhandled_paths`` — paths the odd-extractor's adapters didn't
      cover; informational for the gate.
    - ``created_at`` — ISO 8601 with timezone.
    - ``override_count`` — number of overlays composed (0 = pristine).
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    repo_path: Path
    repo_sha: str | None = None
    objectives: list[Objective] = Field(default_factory=list)
    backing_map: BackingMap
    unhandled_paths: list[Path] = Field(default_factory=list)
    created_at: str
    override_count: int = 0


# ---- Hunk + DiffEntry + Diff (Stage 2: parse-diff output) ----------


class Hunk(BaseModel):
    """A single hunk from ``git diff --unified=0``.

    Per v0.1.9 AC.PRSG.3 — preserved verbatim. Line numbers are
    1-based following git's convention.
    """

    model_config = ConfigDict(extra="forbid")

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    added_lines: list[str] = Field(default_factory=list)
    removed_lines: list[str] = Field(default_factory=list)


class DiffEntry(BaseModel):
    """One file's hunks within a diff."""

    model_config = ConfigDict(extra="forbid")

    file_path: Path
    is_new_file: bool = False
    is_deleted_file: bool = False
    hunks: list[Hunk] = Field(default_factory=list)


class Diff(BaseModel):
    """The full diff between two SHAs (or working-tree vs HEAD)."""

    model_config = ConfigDict(extra="forbid")

    from_sha: str | None = None
    to_sha: str | None = None
    entries: list[DiffEntry] = Field(default_factory=list)


# ---- ClassificationResult (Stage 3: classify output) ---------------


class TouchedObjective(BaseModel):
    """An objective the diff touches.

    Per AC.PRGATE.2 — at objective altitude. ``touch_kind`` distinguishes
    line-level matches (strict; the diff hunk overlapped a backing-row's
    line range) from file-level matches (coarser; the diff touched a
    file in the objective's backing rows but no line-level overlap was
    found).

    The objective's full :class:`Objective` payload is preserved so
    the gate can render outcome prose, not symbol-altitude AC IDs.
    """

    model_config = ConfigDict(extra="forbid")

    objective: Objective
    touch_kind: Literal["evidence_line", "evidence_file"]
    touched_evidence_rows: list[EvidenceRowRef] = Field(default_factory=list)
    touched_hunks: list[Hunk] = Field(default_factory=list)


class NovelDiff(BaseModel):
    """A novel diff hunk — diff lines not mapped to any objective's
    backing row.

    Per AC.PRGATE.2 — Cycle 3 records audit-only; v0.2.4 gap-analysis
    owns objective creation from novel diffs. Aggregated per-file.
    """

    model_config = ConfigDict(extra="forbid")

    file_path: Path
    hunks: list[Hunk] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """Classifier output: which objectives the diff touches + novel
    surface.

    Per AC.PRGATE.2.
    """

    model_config = ConfigDict(extra="forbid")

    touched_objectives: list[TouchedObjective] = Field(default_factory=list)
    untouched: bool = True
    novel: list[NovelDiff] = Field(default_factory=list)


# ---- GateAction + GateDecision (Stage 4: decide output) ------------


class GateAction(str, Enum):
    """Actions the gate can take.

    Per AC.PRGATE.3 — pre-emption order:
    HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS.
    Preserved verbatim from v0.1.9 AC.PRSG.4.
    """

    HARD_BLOCK = "HARD_BLOCK"
    SURFACE_DECISION = "SURFACE_DECISION"
    DOCS_ONLY = "DOCS_ONLY"
    PASS = "PASS"


class GateDecision(BaseModel):
    """Gate engine output.

    Per AC.PRGATE.3.

    Fields:

    - ``action`` — chosen action.
    - ``requires_ratification`` — whether the action requires explicit
      owner ratification through PM (production-stake honour preserved
      per v0.1.9 AC.PRSG.8).
    - ``touched_objectives`` — objectives the diff touched.
    - ``novel`` — novel diffs from the classification.
    - ``safety_profile`` — the workspace's profile at decision time.
    - ``reason`` — structured human-readable explanation rendering
      objective text + backing rows touched (NOT AC IDs).
    - ``pm_batch_pairs`` — (question_text, provenance) pairs to
      enqueue if action is SURFACE_DECISION; empty otherwise.
    - ``audit_payload`` — structured payload for the audit-log.
    """

    model_config = ConfigDict(extra="forbid")

    action: GateAction
    requires_ratification: bool
    touched_objectives: list[TouchedObjective] = Field(default_factory=list)
    novel: list[NovelDiff] = Field(default_factory=list)
    safety_profile: str
    reason: str
    pm_batch_pairs: list[tuple[str, str]] = Field(default_factory=list)
    audit_payload: dict = Field(default_factory=dict)


# ---- OverrideRequest (override-flow input) -------------------------


class OverrideRequest(BaseModel):
    """Override-flow request payload.

    Per AC.PRGATE.4 — at objective altitude. Built by
    :func:`build_override_request` when an override-shaped commit is
    detected AND the ``--override`` flag is present.

    ``original_objectives`` carries the VERIFIED objectives the diff
    touched (the band the override is overriding); ``proposed_objectives``
    carries the conversion targets (typically VERIFIED → PLAUSIBLE
    preserving objective_id + text + domain + multi-source evidence).
    """

    model_config = ConfigDict(extra="forbid")

    original_objectives: list[Objective] = Field(default_factory=list)
    proposed_objectives: list[Objective] = Field(default_factory=list)
    rationale: str
    owner: str
    commit_sha: str
    repo_sha: str

"""Pydantic models for loam-pr-safety.

Per Surface #7 (plan-doc §5) — all models use
``ConfigDict(extra='forbid')`` so additional fields are rejected at
parse time. Mirrors odd-extractor + per-project-pm + cost-governance
conventions.

The shape:

  - :class:`BandedContract` — read of the odd-extractor's contract
    sidecar; carries ``BandedAC`` instances (typed via
    ``loam_odd_extractor.bands``).
  - :class:`Hunk`, :class:`DiffEntry`, :class:`Diff` — typed
    representation of ``git diff --unified=0`` output.
  - :class:`TouchedAC`, :class:`CandidateAC`,
    :class:`ClassificationResult` — classifier output.
  - :class:`GateAction`, :class:`GateDecision` — gate output.
  - :class:`OverrideRequest` — override-flow request payload.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from loam_odd_extractor.bands import BandedAC


# ---- BandedContract (Stage 1: read-contract output) ----------------


class BandedContract(BaseModel):
    """Typed read of the odd-extractor's contract sidecar.

    Per AC.PRSG.2 — composes
    ``<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml``
    with any approved-override overlays at
    ``<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml``.

    The composition is deterministic: read the draft, then apply
    overlays in sorted order. Each overlay replaces an
    original-VERIFIED-AC with a new-VERIFIED-AC (or extends the
    contract with a promoted novel candidate).

    Fields:

    - ``extraction_id`` — repo-id (``<basename>-<8-char-sha256>``).
    - ``repo_path`` — absolute path; informational.
    - ``repo_sha`` — the SHA from the contract sidecar's
      VERIFIED ACs' evidence (informational; may be ``None`` if no
      VERIFIED AC pinned).
    - ``acs`` — list of typed :class:`BandedAC` (per-band evidence
      rules enforced at construction).
    - ``unhandled_paths`` — paths the odd-extractor's adapters didn't
      cover; informational for the gate.
    - ``created_at`` — ISO 8601 with timezone.
    - ``override_count`` — number of overlays composed (0 = pristine).
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    repo_path: Path
    repo_sha: str | None = None
    acs: list[BandedAC] = Field(default_factory=list)
    unhandled_paths: list[Path] = Field(default_factory=list)
    created_at: str
    override_count: int = 0


# ---- Hunk + DiffEntry + Diff (Stage 2: parse-diff output) ----------


class Hunk(BaseModel):
    """A single hunk from ``git diff --unified=0``.

    Per AC.PRSG.3 — represents one change-region. Line numbers are
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
    """The full diff between two SHAs (or working-tree vs HEAD).

    Per AC.PRSG.3 — output of :func:`parse_diff`.
    """

    model_config = ConfigDict(extra="forbid")

    from_sha: str | None = None
    to_sha: str | None = None
    entries: list[DiffEntry] = Field(default_factory=list)


# ---- ClassificationResult (Stage 3: classify output) ---------------


class TouchedAC(BaseModel):
    """An AC the diff touches.

    Per AC.PRSG.3 — ``touch_kind`` distinguishes line-level matches
    (strict; the diff hunk overlapped a citation's line range) from
    backing-file matches (coarser; the diff touched a file in the
    AC's ``backing_files`` but no line-level overlap was found).
    """

    model_config = ConfigDict(extra="forbid")

    ac: BandedAC
    touch_kind: Literal["citation_line", "backing_file"]
    touched_hunks: list[Hunk] = Field(default_factory=list)


class CandidateAC(BaseModel):
    """A novel candidate — diff lines not mapped to any AC.

    Per AC.PRSG.3 — Cycle 1 aggregates per-file; Cycle 2+ may extract
    NL semantics from the novel diff content for richer surfaces.
    """

    model_config = ConfigDict(extra="forbid")

    file_path: Path
    hunks: list[Hunk] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """Classifier output: which ACs the diff touches + novel surface.

    Per AC.PRSG.3.
    """

    model_config = ConfigDict(extra="forbid")

    touched_acs: list[TouchedAC] = Field(default_factory=list)
    untouched: bool = True
    novel: list[CandidateAC] = Field(default_factory=list)


# ---- GateAction + GateDecision (Stage 4: decide output) ------------


class GateAction(str, Enum):
    """Actions the gate can take.

    Per AC.PRSG.4 — pre-emption order: HARD_BLOCK > SURFACE_DECISION
    > DOCS_ONLY > PASS.
    """

    HARD_BLOCK = "HARD_BLOCK"
    SURFACE_DECISION = "SURFACE_DECISION"
    DOCS_ONLY = "DOCS_ONLY"
    PASS = "PASS"


class GateDecision(BaseModel):
    """Gate engine output.

    Per AC.PRSG.4. Fields:

    - ``action`` — the chosen action.
    - ``requires_ratification`` — whether the action requires
      explicit owner ratification through PM (per AC.PRSG.8 +
      Decision Q).
    - ``touched_acs`` — ACs the diff touched (subset of the
      classification's ``touched_acs``; carried through for audit).
    - ``novel`` — novel candidates from the classification.
    - ``safety_profile`` — the workspace's profile at decision time.
    - ``reason`` — structured human-readable explanation.
    - ``pm_batch_pairs`` — (question_text, provenance) pairs to
      enqueue if ``action`` is SURFACE_DECISION; empty otherwise.
    - ``audit_payload`` — the structured payload written to
      audit-log.
    """

    model_config = ConfigDict(extra="forbid")

    action: GateAction
    requires_ratification: bool
    touched_acs: list[TouchedAC] = Field(default_factory=list)
    novel: list[CandidateAC] = Field(default_factory=list)
    safety_profile: str
    reason: str
    pm_batch_pairs: list[tuple[str, str]] = Field(default_factory=list)
    audit_payload: dict = Field(default_factory=dict)


# ---- OverrideRequest (override-flow input) -------------------------


class OverrideRequest(BaseModel):
    """Override-flow request payload.

    Per AC.PRSG.5. Built by :func:`recognise_override` when an
    override-shaped commit is detected AND the ``--override`` flag
    is present.
    """

    model_config = ConfigDict(extra="forbid")

    original_acs: list[BandedAC] = Field(default_factory=list)
    proposed_acs: list[BandedAC] = Field(default_factory=list)
    rationale: str
    owner: str
    commit_sha: str
    repo_sha: str

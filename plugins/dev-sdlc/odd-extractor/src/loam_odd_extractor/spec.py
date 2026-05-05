"""Pydantic models for the odd-extractor's stage artefacts.

Per AC.OREK.3 — each of the four stages (init / analyze / generate /
verify) produces a structured artefact. The Pydantic models here are
the structural contracts.

Per Surface #9 (plan-doc §5) — all models use ``ConfigDict(extra='forbid')``
so additional fields are rejected at parse time. Cycle 3 + 4 may
extend with additive fields (forward-compat); this cycle ships the
minimal-required-surface so adapters can extend per-language.

Per v0.2.3 Cycle 1 (sub-plan-doc §3 AC.OBJX.{1,2,3,4,5}) — extension
adds outcome-altitude typed models alongside the existing symbol-
altitude :class:`RawACs` shape. The legacy :class:`RawACs` is
PRESERVED unchanged at the type level; v0.2.3 reroutes adapter
output into ``evidence-rows.yaml`` (renamed from ``raw-acs.yaml``)
via :mod:`loam_odd_extractor.generate`. The legacy ``acs:`` field
in :class:`ContractDraft`'s sidecar is preserved transitionally for
v0.1.9 PR-safety reads (Cycle 3 retires per master plan §6.2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from loam.cost_governance import BudgetEnvelope

from .bands import ConfidenceBand


# ---- ExtractionConfig (Stage 1 output) -----------------------------


class ExtractionConfig(BaseModel):
    """Stage 1 (init) output — configures the run.

    Written to ``<workspace>/.loam/extractions/<repo-id>/config.yaml``.
    """

    model_config = ConfigDict(extra="forbid")

    repo_path: Path
    repo_id: str
    workspace_root: Path
    budget: BudgetEnvelope
    dry_run: bool
    created_at: str  # ISO 8601 with timezone


# ---- Slice (Stage 2 inner) -----------------------------------------


class Slice(BaseModel):
    """A unit of extraction work, scoped to a single language adapter.

    Cycle 1 ships zero adapters, so all paths land in
    :attr:`AnalysisPlan.unhandled_paths` rather than slices. The
    :class:`Slice` shape is the forward-compat contract for Cycles 3+4.
    """

    model_config = ConfigDict(extra="forbid")

    slice_id: str
    adapter_name: str
    paths: list[Path]


# ---- AnalysisPlan (Stage 2 output) ---------------------------------


class AnalysisPlan(BaseModel):
    """Stage 2 (analyze) output — a plan of slices + unhandled paths.

    Written to ``<workspace>/.loam/extractions/<repo-id>/plan.yaml``.
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    slices: list[Slice] = Field(default_factory=list)
    unhandled_paths: list[Path] = Field(default_factory=list)
    created_at: str  # ISO 8601 with timezone


# ---- RawACs (Stage 3 output) ---------------------------------------


class RawACs(BaseModel):
    """Stage 3 (generate) symbol-altitude evidence rows.

    Per v0.2.3 Cycle 1 (sub-plan-doc §3 AC.OBJX.7): the file these
    serialize to is renamed from ``raw-acs.yaml`` → ``evidence-rows.yaml``
    in the v0.2.3 generate-stage rewire. The Pydantic shape here is
    PRESERVED for adapter-output compatibility; the renamed
    persistence path is enforced by :mod:`loam_odd_extractor.generate`.

    Cycle 1 (v0.1.8) shipped zero adapters; Cycles 3-4 (v0.1.8) added
    Ruby + JS/TS adapters that emit ``BandedAC`` dicts at symbol
    altitude. v0.2.3 routes those rows into ``evidence-rows.yaml``
    (NOT into ``contract-draft.yaml acs:``). The dict-typed ``acs``
    field deliberately stays loose so adapter outputs flow through
    unchanged.
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    acs: list[dict] = Field(default_factory=list)
    unhandled_paths: list[Path] = Field(default_factory=list)
    per_slice_costs: dict[str, dict] = Field(default_factory=dict)
    created_at: str  # ISO 8601 with timezone


# ---- ContractDraft (Stage 4 output) --------------------------------


class ContractDraft(BaseModel):
    """Stage 4 (verify) output handle — points at the markdown +
    sidecar artefacts.

    The actual contract content lives in two files
    (``contract-draft.md`` + ``contract-draft.yaml``) under
    ``<workspace>/.loam/extractions/<repo-id>/``. This model is the
    structured handle for callers that want to inspect counts /
    paths without re-reading the artefacts.
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    markdown_path: Path
    sidecar_path: Path
    ac_count: int
    unhandled_count: int
    created_at: str  # ISO 8601 with timezone


# ====================================================================
# v0.2.3 Cycle 1 — outcome-altitude models (AC.OBJX.{1,2,3,4,5})
# ====================================================================
#
# Per sub-plan-doc §3: new typed models for the multi-source objective
# synthesis pipeline. These are the load-bearing types of the rebuild —
# the v0.1.8 substrate emitted symbol-altitude :class:`BandedAC` rows
# under the wrong altitude label. v0.2.3 introduces typed outcome /
# constraint / capability models that survive the implementation-swap
# test (lean grounding doc §self-check 2).


# ID-format regexes per sub-plan-doc §7 method-decision register.
_OBJECTIVE_ID_RE = re.compile(r"^O\.[a-z][a-z0-9-]*\.\d+$")
_CONSTRAINT_ID_RE = re.compile(r"^K\.[a-z][a-z0-9-]*\.\d+$")
_CAPABILITY_ID_RE = re.compile(r"^C\.[a-z][a-z0-9-]*\.\d+$")


class ObjectiveEvidence(BaseModel):
    """Multi-source citation block for an :class:`Objective`.

    Per sub-plan-doc §3 AC.OBJX.1: the multi-source banding rule
    needs a multi-source evidence shape. The single-``citations``
    list on :class:`bands.Evidence` cannot carry the
    "two-source-required-for-VERIFIED" check structurally; this
    typed evidence block does.

    Field reliability ranks (lean grounding doc §brownfield ODD-RE
    inputs):

    1. ``readme_excerpts`` / ``design_doc_refs`` — plain-English
       maintainer purpose statements.
    2. ``test_name_refs`` — outcome-asserting test names.
    3. ``survey_line_refs`` — operator-supplied context.
    4. ``code_pattern_refs`` — adapter-derived inference shapes.

    ``repo_sha`` pins evidence to a tree-state; required for VERIFIED
    band per :class:`Objective`'s per-band invariants.
    """

    model_config = ConfigDict(extra="forbid")

    readme_excerpts: list[str] = Field(default_factory=list)
    design_doc_refs: list[str] = Field(default_factory=list)
    test_name_refs: list[str] = Field(default_factory=list)
    survey_line_refs: list[str] = Field(default_factory=list)
    code_pattern_refs: list[str] = Field(default_factory=list)
    repo_sha: str | None = None
    rationale: str | None = None


class ConstraintEvidence(BaseModel):
    """Multi-source citation block for a :class:`Constraint`.

    Same shape as :class:`ObjectiveEvidence` minus ``test_name_refs``
    — tests assert outcomes, not bounds (lean grounding doc §self-
    check 4 / drift-mode #4).
    """

    model_config = ConfigDict(extra="forbid")

    readme_excerpts: list[str] = Field(default_factory=list)
    design_doc_refs: list[str] = Field(default_factory=list)
    survey_line_refs: list[str] = Field(default_factory=list)
    code_pattern_refs: list[str] = Field(default_factory=list)
    repo_sha: str | None = None
    rationale: str | None = None


class CapabilityEvidence(BaseModel):
    """Multi-source citation block for a :class:`Capability`.

    Same shape as :class:`ObjectiveEvidence`; capabilities can be
    test-asserted as outcomes-of-features even though the capability
    itself is HOW.
    """

    model_config = ConfigDict(extra="forbid")

    readme_excerpts: list[str] = Field(default_factory=list)
    design_doc_refs: list[str] = Field(default_factory=list)
    test_name_refs: list[str] = Field(default_factory=list)
    survey_line_refs: list[str] = Field(default_factory=list)
    code_pattern_refs: list[str] = Field(default_factory=list)
    repo_sha: str | None = None
    rationale: str | None = None


def _has_any_evidence(ev: ObjectiveEvidence | ConstraintEvidence | CapabilityEvidence) -> bool:
    """True if any source-list field has at least one entry."""
    return bool(
        getattr(ev, "readme_excerpts", None)
        or getattr(ev, "design_doc_refs", None)
        or getattr(ev, "test_name_refs", None)
        or getattr(ev, "survey_line_refs", None)
        or getattr(ev, "code_pattern_refs", None)
    )


class Objective(BaseModel):
    """Outcome-altitude objective — what the system delivers.

    Per sub-plan-doc §3 AC.OBJX.1 + lean grounding doc §altitudes:

    - Names purpose / value-to-someone (§self-check 5).
    - Observable from outside (§self-check 4).
    - Survives implementation rewrite (§self-check 2).
    - Builder-method-loose (§self-check 3).
    - Outcome, not fact (§self-check 1).

    Per-band invariants (model_validator):

    - VERIFIED: ``test_name_refs`` non-empty AND
      (``readme_excerpts`` OR ``design_doc_refs``) non-empty
      (two-source rule) AND ``repo_sha`` non-null.
    - PLAUSIBLE: at least one of ``readme_excerpts`` /
      ``design_doc_refs`` / ``survey_line_refs`` non-empty (single-
      source). Survey-only evidence is capped at PLAUSIBLE per
      sub-plan-doc §7 + master plan §7.7.
    - HYPOTHESISED: ``rationale`` non-empty (LLM-derived inference
      chain).

    All invariants raise :class:`pydantic.ValidationError` on
    construction; no instance can hold a malformed band/evidence
    pair.
    """

    model_config = ConfigDict(extra="forbid")

    objective_id: str = Field(min_length=1)
    text: str = Field(min_length=20)
    confidence: ConfidenceBand
    evidence: ObjectiveEvidence
    domain: str = Field(min_length=1)
    # Per v0.2.4 Cycle 1 AC.COMPINT.1: provenance for the augmented
    # objective set. Additive Literal field with default "extracted"
    # (round-trip safe — every legacy v0.2.3 objectives.yaml row
    # parses as ``source="extracted"`` without explicit field).
    # Set to "added_by_user" by Shape (b)(1)/(b)(2)/(c) of the
    # completeness interview; "flagged_by_persona" when a
    # persona-flagged candidate is accepted at Shape (b)(1).
    source: Literal["extracted", "added_by_user", "flagged_by_persona"] = (
        "extracted"
    )

    @model_validator(mode="after")
    def _enforce_id_regex_and_per_band(self) -> "Objective":
        if not _OBJECTIVE_ID_RE.match(self.objective_id):
            raise ValueError(
                f"Objective.objective_id must match {_OBJECTIVE_ID_RE.pattern!r}; "
                f"got {self.objective_id!r}"
            )
        band = self.confidence
        ev = self.evidence
        if band is ConfidenceBand.VERIFIED:
            if not ev.test_name_refs:
                raise ValueError(
                    "Objective: VERIFIED band requires non-empty "
                    "evidence.test_name_refs (test-asserted outcomes)"
                )
            if not (ev.readme_excerpts or ev.design_doc_refs):
                raise ValueError(
                    "Objective: VERIFIED band requires the two-source "
                    "rule — at least one of evidence.readme_excerpts "
                    "or evidence.design_doc_refs in addition to tests"
                )
            if not ev.repo_sha:
                raise ValueError(
                    "Objective: VERIFIED band requires non-null "
                    "evidence.repo_sha (pin evidence to a tree-state)"
                )
        elif band is ConfidenceBand.PLAUSIBLE:
            if not (
                ev.readme_excerpts
                or ev.design_doc_refs
                or ev.survey_line_refs
            ):
                raise ValueError(
                    "Objective: PLAUSIBLE band requires at least one "
                    "of evidence.readme_excerpts / design_doc_refs / "
                    "survey_line_refs (single-source minimum)"
                )
        elif band is ConfidenceBand.HYPOTHESISED:
            if not ev.rationale or not ev.rationale.strip():
                raise ValueError(
                    "Objective: HYPOTHESISED band requires non-empty "
                    "evidence.rationale (LLM-derived inference chain)"
                )
        return self


class Constraint(BaseModel):
    """Bound on the solution space — not an outcome.

    Per sub-plan-doc §3 AC.OBJX.2 + lean grounding doc §altitudes:
    constraints restrict HOW outcomes are delivered without being
    outcomes themselves (§drift-mode #6 — constraint-as-objective).
    """

    model_config = ConfigDict(extra="forbid")

    constraint_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    bounds_kind: Literal["compliance", "infra", "language", "security", "domain"]
    evidence: ConstraintEvidence

    @model_validator(mode="after")
    def _enforce_id_regex_and_evidence(self) -> "Constraint":
        if not _CONSTRAINT_ID_RE.match(self.constraint_id):
            raise ValueError(
                f"Constraint.constraint_id must match {_CONSTRAINT_ID_RE.pattern!r}; "
                f"got {self.constraint_id!r}"
            )
        if not _has_any_evidence(self.evidence):
            raise ValueError(
                "Constraint: evidence must populate at least one ref "
                "kind (readme_excerpts / design_doc_refs / "
                "survey_line_refs / code_pattern_refs)"
            )
        return self


class Capability(BaseModel):
    """A feature/function serving objectives — one HOW of many.

    Per sub-plan-doc §3 AC.OBJX.3 + lean grounding doc §altitudes:
    capabilities are tool-internal HOWs that ladder up to objectives.
    The ``serves`` field carries the cross-reference; verify-stage
    (AC.OBJX.10) checks referential integrity.
    """

    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    serves: list[str] = Field(default_factory=list)
    evidence: CapabilityEvidence

    @model_validator(mode="after")
    def _enforce_id_regex_and_serves(self) -> "Capability":
        if not _CAPABILITY_ID_RE.match(self.capability_id):
            raise ValueError(
                f"Capability.capability_id must match {_CAPABILITY_ID_RE.pattern!r}; "
                f"got {self.capability_id!r}"
            )
        if not self.serves:
            raise ValueError(
                "Capability: serves must be non-empty (a capability "
                "with no objective served is not a capability per "
                "ODD §altitudes)"
            )
        for ref in self.serves:
            if not _OBJECTIVE_ID_RE.match(ref):
                raise ValueError(
                    f"Capability.serves entry {ref!r} must match "
                    f"objective_id pattern {_OBJECTIVE_ID_RE.pattern!r}"
                )
        return self


# ---- MultiSourceBundle (AC.OBJX.4) ---------------------------------


class MultiSourceBundle(BaseModel):
    """Output of the multi-source input collector.

    Per sub-plan-doc §3 AC.OBJX.4 + §7: priority-ordered bundle
    feeding the synthesis LLM-pass. Bundle fields stay individually
    addressable so the synthesis prompt can format them per source
    rather than as a flat blob.
    """

    model_config = ConfigDict(extra="forbid")

    repo_id: str
    repo_path: str
    repo_sha: str | None = None
    readme_text: str | None = None
    readme_truncated: bool = False
    design_docs: list[dict[str, str]] = Field(default_factory=list)
    test_assertions: list[dict[str, str]] = Field(default_factory=list)
    user_survey: dict[str, Any] | None = None
    code_patterns: list[dict[str, Any]] = Field(default_factory=list)
    total_token_estimate: int = 0


# ---- SynthesisResult (AC.OBJX.5) -----------------------------------


class SynthesisResult(BaseModel):
    """Output of the LLM-pass synthesis call.

    Per sub-plan-doc §3 AC.OBJX.5 + AC.OBJX.6: typed result of the
    single LLM-pass that emits banded objectives + constraints +
    capabilities. ``cost_actual_cents`` is the tail-of-call ledger
    (paired with the dry-run estimate at the cost-governance layer).
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    objectives: list[Objective] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    raw_response: str | None = None
    token_count_input: int = 0
    token_count_output: int = 0
    cost_actual_cents: float = 0.0
    model_id: str = "unknown"
    created_at: str | None = None


# ---- ValidationReport (AC.OBJX.8) ----------------------------------


class AltitudeCheckResult(BaseModel):
    """One row's §self-check verdict."""

    model_config = ConfigDict(extra="forbid")

    row_id: str
    row_kind: Literal["objective", "constraint", "capability"]
    classification: Literal["pass", "fail", "borderline"]
    failed_check: int | None = None  # 1..5 per lean-grounding §self-checks
    decision: Literal["keep", "drop", "downgrade", "restate-as-capability"]
    rationale: str = ""


class ValidationReport(BaseModel):
    """Output of :func:`altitude_validator.validate_altitude`.

    Per sub-plan-doc §3 AC.OBJX.8: programmatic + LLM-as-judge
    altitude check. The decision tree is applied at validator-time;
    the report carries the full per-row result for downstream
    rendering (verify-stage §self-checks audit table) +
    ``synthesis_complete`` audit-log fields.
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str
    total_rows: int
    pass_count: int
    fail_count: int
    borderline_count: int
    pass_rate: float  # 0.0 .. 1.0
    dropped_count: int = 0
    downgraded_count: int = 0
    restated_count: int = 0
    drift_halt_triggered: bool = False
    fail_threshold: float = 0.30
    results: list[AltitudeCheckResult] = Field(default_factory=list)


# ====================================================================
# v0.2.3 Cycle 2 — Backing-implementation map (AC.BACKMAP.1)
# ====================================================================
#
# Per sub-plan-doc §3 AC.BACKMAP.1: typed Pydantic models linking each
# :class:`Objective` to the symbol-altitude evidence rows that back it.
# Bidirectional structure carrying orphan rows for forward-compat with
# v0.2.4 gap-analysis + v0.2.5 negative-alignment.

# Composite ``kind:path:line`` regex per sub-plan-doc §7. Tolerates
# missing line (some adapters emit ``kind:path``); ``line`` may be a
# range (``42-47``) or a single int (``42``).
_EVIDENCE_ROW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*:[^:]+(?::\d+(?:-\d+)?)?$")


class EvidenceRowRef(BaseModel):
    """Reference to a symbol-altitude evidence row backing an objective.

    Per sub-plan-doc §3 AC.BACKMAP.1: ``evidence_row_id`` mirrors the
    composite ``kind:path:line`` shape of :class:`bands.BandedAC.ac_id`.
    Stable across re-extractions; round-trips cleanly via Pydantic.

    ``confidence`` is signal-strength (STRONG/WEAK), structurally
    orthogonal to the V/P/H objective banding — STRONG means the
    backing relationship is high-confidence, regardless of the objective's
    own band.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_row_id: str = Field(min_length=1)
    kind: Literal["route", "callback", "model", "test", "pattern", "other"]
    path: str = Field(min_length=1)
    line_range: tuple[int, int] | None = None
    symbol_name: str | None = None
    language: Literal["jsts", "ruby", "python", "other"] = "other"
    confidence: Literal["STRONG", "WEAK"] = "WEAK"

    @model_validator(mode="after")
    def _enforce_id_regex(self) -> "EvidenceRowRef":
        if not _EVIDENCE_ROW_ID_RE.match(self.evidence_row_id):
            raise ValueError(
                f"EvidenceRowRef.evidence_row_id must match "
                f"{_EVIDENCE_ROW_ID_RE.pattern!r}; got "
                f"{self.evidence_row_id!r}"
            )
        return self


class OrphanRow(BaseModel):
    """An evidence row that did not match any objective.

    Per sub-plan-doc §3 AC.BACKMAP.5: forward-compat carrier for
    v0.2.4 gap-analysis + v0.2.5 negative-alignment. The ``reason``
    enum is intentionally open-shaped; new values will be added in
    forward cycles (e.g. ``negative-alignment-detected``).
    """

    model_config = ConfigDict(extra="forbid")

    evidence_row_id: str = Field(min_length=1)
    kind: Literal["route", "callback", "model", "test", "pattern", "other"]
    path: str = Field(min_length=1)
    line_range: tuple[int, int] | None = None
    symbol_name: str | None = None
    language: Literal["jsts", "ruby", "python", "other"] = "other"
    reason: Literal[
        "no-objective-match",
        "weak-signal-only",
        "anti-feature-candidate",
    ]

    @model_validator(mode="after")
    def _enforce_id_regex(self) -> "OrphanRow":
        if not _EVIDENCE_ROW_ID_RE.match(self.evidence_row_id):
            raise ValueError(
                f"OrphanRow.evidence_row_id must match "
                f"{_EVIDENCE_ROW_ID_RE.pattern!r}; got "
                f"{self.evidence_row_id!r}"
            )
        return self


class BackingMapEntry(BaseModel):
    """Per-objective backing-row list with a match rationale.

    Per sub-plan-doc §3 AC.BACKMAP.1: one entry per objective.
    ``evidence_rows`` may be empty for HYPOTHESISED objectives that
    have no implementation yet (forward-looking outcomes).
    """

    model_config = ConfigDict(extra="forbid")

    objective_id: str = Field(min_length=1)
    evidence_rows: list[EvidenceRowRef] = Field(default_factory=list)
    match_rationale: str = ""

    @model_validator(mode="after")
    def _enforce_objective_id_regex(self) -> "BackingMapEntry":
        if not _OBJECTIVE_ID_RE.match(self.objective_id):
            raise ValueError(
                f"BackingMapEntry.objective_id must match "
                f"{_OBJECTIVE_ID_RE.pattern!r}; got "
                f"{self.objective_id!r}"
            )
        return self


class BackingMap(BaseModel):
    """Bidirectional Objective ↔ evidence-row map.

    Per sub-plan-doc §3 AC.BACKMAP.1: top-level structure persisted
    at ``<workspace>/.loam/extractions/<repo-id>/backing-map.yaml``.
    ``unmatched_objective_ids`` is the gap signal for v0.2.4: lists
    non-HYPOTHESISED objectives that have no backing rows.
    """

    model_config = ConfigDict(extra="forbid")

    extraction_id: str = Field(min_length=1)
    entries: list[BackingMapEntry] = Field(default_factory=list)
    orphan_rows: list[OrphanRow] = Field(default_factory=list)
    created_at: str
    model_id: str = "(none)"
    cost_actual_cents: float = 0.0
    total_evidence_rows: int = 0
    objective_count: int = 0
    unmatched_objective_ids: list[str] = Field(default_factory=list)


# ====================================================================
# v0.2.3 Cycle 2 — Objective-altitude ratification action (AC.OBJRAT.1)
# ====================================================================
#
# Frozen-dataclass primitive parallels v0.1.8 ``RatificationAction``;
# the actual dataclass + factories live in :mod:`ratify` to avoid
# circular imports. The model_dump-equivalent payload shape is
# documented here for reference; see :mod:`ratify` for the dataclass.


# ====================================================================
# v0.2.4 Cycle 1 — Completeness interview augmented objective set
# (AC.COMPINT.1)
# ====================================================================
#
# Per sub-plan-doc §3 AC.COMPINT.1: persisted form of the user-confirmed
# (or adjusted, or extended) objective set. Symmetric with v0.2.3's
# :class:`BackingMap` shape — top-level container with ``extraction_id``
# + ``objectives`` list + ``model_validator`` enforcing no duplicate IDs.
# ``interview_audit_path`` points at the audit-log directory whose
# entries trace the interview run that produced this set.


class AugmentedObjectiveSet(BaseModel):
    """The completeness-interview output: extracted + user-augmented objectives.

    Per sub-plan-doc §3 AC.COMPINT.1: container Pydantic model
    persisted at ``<workspace>/.loam/extractions/<repo-id>/augmented-
    objectives.yaml``. Schema-versioned for forward compatibility.

    Invariants (enforced via ``model_validator``):

    - No two ``Objective.objective_id`` values collide in the set.
    - ``schema_version`` is the int 1; future bumps need a migration.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    extraction_id: str = Field(min_length=1)
    augmented_at: str  # ISO 8601 with timezone
    interview_audit_path: str = Field(min_length=1)
    objectives: list[Objective] = Field(default_factory=list)

    @model_validator(mode="after")
    def _enforce_no_duplicate_ids(self) -> "AugmentedObjectiveSet":
        seen: set[str] = set()
        for obj in self.objectives:
            if obj.objective_id in seen:
                raise ValueError(
                    f"AugmentedObjectiveSet: duplicate "
                    f"objective_id={obj.objective_id!r} (each ID must "
                    f"be unique in the augmented set)"
                )
            seen.add(obj.objective_id)
        return self


class HeuristicPrior(BaseModel):
    """A heuristic-flagged missing-objective prior.

    Per sub-plan-doc §3 AC.COMPINT.3: heuristic pre-pass output
    feeding the LLM-as-judge. Each prior names an ABSENT-objective
    pattern with structural evidence refs. The LLM-judge consumes
    these to either confirm + augment, downgrade, or filter.

    ``priority`` ranks the prior so the cap-of-5 truncation in the
    LLM-judge keeps the highest-priority candidates.
    """

    model_config = ConfigDict(extra="forbid")

    pattern_id: Literal[
        "production-stake-no-security-objective",
        "survey-compliance-no-compliance-objective",
        "data-modify-routes-no-persistence-objective",
    ]
    prior_text: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"] = "medium"
    evidence_refs: list[str] = Field(default_factory=list)


class FlaggedMissing(BaseModel):
    """An LLM-flagged missing-objective candidate.

    Per sub-plan-doc §3 AC.COMPINT.2: structured output of
    :func:`completeness.flag_missing_objectives`. Each row is a
    candidate-objective the user can choose to add (Shape (b) in the
    interview), reject, or defer.

    ``candidate_text`` is ≥20 chars (mirrors :class:`Objective.text`'s
    minimum); LLM-judge prompt enforces this, but the Pydantic model
    holds the contract structurally.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_text: str = Field(min_length=20)
    reasoning: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    priority: Literal["high", "medium", "low"] = "medium"
    domain: str = Field(min_length=1, default="uncategorized")


# ====================================================================
# v0.2.4 Cycle 2 — Gap analysis (AC.GAPAN.{1,2})
# ====================================================================
#
# Per sub-plan-doc §3 AC.GAPAN.1 + AC.GAPAN.2: typed Gap + GapInventory
# Pydantic models. Two-category inventory (objectives_without_verified_
# backing + implementation_orphans) with STRONG/WEAK confidence
# orthogonal to the objective banding.

# Gap-id regex per AC.GAPAN.1.
_GAP_ID_RE = re.compile(r"^G\.(BACKING|ORPHAN)\.[a-z0-9_-]+$")


class Gap(BaseModel):
    """A single gap finding produced by :func:`gap_analysis.analyze_gaps`.

    Per sub-plan-doc §3 AC.GAPAN.1:

    - ``gap_id`` matches ``^G\\.(BACKING|ORPHAN)\\.[a-z0-9_-]+$``.
    - ``category`` ∈ {``objective_without_verified_backing``,
      ``implementation_orphan``}.
    - ``confidence`` ∈ {``STRONG``, ``WEAK``} per :func:`_classify_confidence`.
    - ``objective_id`` set for category-a (objective_without_verified_
      backing) gaps; ``None`` for category-b (implementation_orphan)
      gaps. The ``model_validator`` enforces this invariant in both
      directions.
    - ``evidence_rows`` empty for empty-backing category-a gaps;
      populated otherwise (the WEAK rows for a category-a gap with
      WEAK-only backing; the orphan rows for a category-b gap).
    - ``rationale`` ≥20 chars; auditable explanation of why the gap
      was surfaced. Includes the orphan group-key for category-b.
    - ``negative_alignment_evidence`` per AC.GAPAN.8: forward-compat
      seam for v0.2.6+ negative-alignment. Defaults to ``None`` at
      v0.2.4; never populated by this cycle. Round-trip safe via
      ``model_dump(exclude_none=True)`` so legacy v0.2.4 YAML stays
      clean (no ``negative_alignment_evidence: null`` clutter).
    """

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(min_length=1)
    category: Literal[
        "objective_without_verified_backing",
        "implementation_orphan",
    ]
    confidence: Literal["STRONG", "WEAK"]
    objective_id: str | None = None
    evidence_rows: list[EvidenceRowRef] = Field(default_factory=list)
    rationale: str = Field(min_length=20)
    negative_alignment_evidence: list[EvidenceRowRef] | None = None

    @model_validator(mode="after")
    def _enforce_id_regex_and_category_invariants(self) -> "Gap":
        if not _GAP_ID_RE.match(self.gap_id):
            raise ValueError(
                f"Gap.gap_id must match {_GAP_ID_RE.pattern!r}; "
                f"got {self.gap_id!r}"
            )
        if self.category == "objective_without_verified_backing":
            if self.objective_id is None:
                raise ValueError(
                    "Gap: category='objective_without_verified_backing' "
                    "requires objective_id to be set"
                )
            if not _OBJECTIVE_ID_RE.match(self.objective_id):
                raise ValueError(
                    f"Gap.objective_id must match "
                    f"{_OBJECTIVE_ID_RE.pattern!r}; got "
                    f"{self.objective_id!r}"
                )
        else:  # implementation_orphan
            if self.objective_id is not None:
                raise ValueError(
                    "Gap: category='implementation_orphan' requires "
                    "objective_id=None (orphans have no claimed "
                    "objective by definition)"
                )
        return self


class GapSummary(BaseModel):
    """Pre-aggregated counts inside a :class:`GapInventory`.

    Per sub-plan-doc §3 AC.GAPAN.2: counts surface to Cycle 3 build-
    next + CLI stdout summary without re-traversing ``gaps``. The
    container's ``model_validator`` enforces these match the actual
    list aggregate.
    """

    model_config = ConfigDict(extra="forbid")

    category_a_count: int = 0
    category_b_count: int = 0
    strong_count: int = 0
    weak_count: int = 0
    total: int = 0


# ====================================================================
# v0.2.4 Cycle 3 — Build-next ranking (AC.BLDNXT.1)
# ====================================================================
#
# Per sub-plan-doc §3 AC.BLDNXT.1 + AC.BLDNXT.5: typed ranked-candidate
# + recommendation container persisted at build-next.{md,yaml}.
# Composite_score = gap_confidence_factor × priority_match_factor ×
# estimated_impact_factor (priority_match_factor=1.0 substituted when
# None, i.e. survey-degenerate path).


_PRIORITY_MATCH_SIGNAL_VALUES = (
    "survey",
    "interview",
    "keyword",
    "llm_judge",
    "none",
)


class BuildNextCandidate(BaseModel):
    """One ranked candidate in a :class:`BuildNextRecommendation`.

    Per sub-plan-doc §3 AC.BLDNXT.1:

    - ``gap_id`` matches the gap-id regex (``^G\\.(BACKING|ORPHAN)\\.[a-z0-9_-]+$``).
    - ``composite_score`` ∈ [0.0, 1.0]; equals the product of the
      three factor fields (priority_match_factor=1.0 when None).
    - ``gap_confidence_factor`` ∈ [0.0, 1.0]; STRONG=1.0 / WEAK=0.5
      (AC.BLDNXT.2).
    - ``priority_match_factor`` ∈ [0.0, 1.0] OR ``None``. ``None``
      signals survey-degenerate path (AC.BLDNXT.3).
    - ``estimated_impact_factor`` ∈ [0.0, 1.0]; deterministic
      category-base + bonuses (AC.BLDNXT.2).
    - ``priority_match_signal`` ∈ {``survey``, ``interview``,
      ``keyword``, ``llm_judge``, ``none``}.
    - ``rationale`` ≥ 40 chars; auditable explanation referencing the
      gap + which user-priority signal matched.
    - ``category`` mirrored from the source :class:`Gap`.
    - ``objective_id`` mirrored when source is category-a; ``None``
      for category-b orphans.
    """

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(min_length=1)
    composite_score: float = Field(ge=0.0, le=1.0)
    gap_confidence_factor: float = Field(ge=0.0, le=1.0)
    priority_match_factor: float | None = None
    estimated_impact_factor: float = Field(ge=0.0, le=1.0)
    priority_match_signal: Literal[
        "survey", "interview", "keyword", "llm_judge", "none"
    ]
    rationale: str = Field(min_length=40)
    category: Literal[
        "objective_without_verified_backing",
        "implementation_orphan",
    ]
    objective_id: str | None = None

    @model_validator(mode="after")
    def _enforce_id_regex_and_factor_consistency(self) -> "BuildNextCandidate":
        if not _GAP_ID_RE.match(self.gap_id):
            raise ValueError(
                f"BuildNextCandidate.gap_id must match {_GAP_ID_RE.pattern!r}; "
                f"got {self.gap_id!r}"
            )
        if self.priority_match_factor is not None:
            if not 0.0 <= self.priority_match_factor <= 1.0:
                raise ValueError(
                    "BuildNextCandidate.priority_match_factor must be in "
                    f"[0.0, 1.0]; got {self.priority_match_factor!r}"
                )
        # Factor-product-matches-composite (rounding tolerance 1e-4).
        pm = (
            self.priority_match_factor
            if self.priority_match_factor is not None
            else 1.0
        )
        expected = (
            self.gap_confidence_factor
            * pm
            * self.estimated_impact_factor
        )
        if abs(self.composite_score - expected) > 1e-4:
            raise ValueError(
                "BuildNextCandidate: composite_score must equal "
                "gap_confidence_factor × priority_match_factor × "
                "estimated_impact_factor (priority_match_factor=1.0 "
                f"when None); expected {expected:.6f} got "
                f"{self.composite_score:.6f}"
            )
        # Category / objective_id mirror invariant.
        if self.category == "objective_without_verified_backing":
            if self.objective_id is None:
                raise ValueError(
                    "BuildNextCandidate: category="
                    "'objective_without_verified_backing' requires "
                    "objective_id to be set (mirrored from source Gap)"
                )
            if not _OBJECTIVE_ID_RE.match(self.objective_id):
                raise ValueError(
                    f"BuildNextCandidate.objective_id must match "
                    f"{_OBJECTIVE_ID_RE.pattern!r}; got "
                    f"{self.objective_id!r}"
                )
        else:  # implementation_orphan
            if self.objective_id is not None:
                raise ValueError(
                    "BuildNextCandidate: category='implementation_orphan' "
                    "requires objective_id=None (orphans have no claimed "
                    "objective)"
                )
        return self


class BuildNextRecommendation(BaseModel):
    """The ranked-candidate recommendation persisted at build-next.yaml.

    Per sub-plan-doc §3 AC.BLDNXT.1 + AC.BLDNXT.5:

    - ``schema_version`` literal int 1; future bumps need migration.
    - ``extraction_id`` ties to workspace's extraction.
    - ``analyzed_at`` ISO 8601 timestamp; excluded from idempotence
      content-hash (AC.BLDNXT.4).
    - ``audit_path`` points at audit-log directory of producing run.
    - ``degenerate_survey`` True when survey absent at both canonical
      paths AND no interview-added objectives (AC.BLDNXT.3).
    - ``candidates`` ranked top-N (default 10; ``--limit`` configurable
      via CLI per AC.PERSONA-PULL.1).
    - ``truncated_count`` = (underlying-list size) − len(candidates);
      surfaced to caller when limit truncates.
    - ``llm_judge_invocations`` count of borderline-only LLM-judge
      calls actually made (AC.BLDNXT.3 cap-of-5).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    extraction_id: str = Field(min_length=1)
    analyzed_at: str  # ISO 8601 with timezone
    audit_path: str = Field(min_length=1)
    degenerate_survey: bool = False
    candidates: list[BuildNextCandidate] = Field(default_factory=list)
    truncated_count: int = 0
    llm_judge_invocations: int = 0

    @model_validator(mode="after")
    def _enforce_no_duplicate_gap_id(self) -> "BuildNextRecommendation":
        seen: set[str] = set()
        for c in self.candidates:
            if c.gap_id in seen:
                raise ValueError(
                    f"BuildNextRecommendation: duplicate gap_id="
                    f"{c.gap_id!r} (each gap_id must be unique in the "
                    f"candidate list)"
                )
            seen.add(c.gap_id)
        if self.truncated_count < 0:
            raise ValueError(
                "BuildNextRecommendation.truncated_count must be >= 0; "
                f"got {self.truncated_count}"
            )
        if self.llm_judge_invocations < 0:
            raise ValueError(
                "BuildNextRecommendation.llm_judge_invocations must be "
                f">= 0; got {self.llm_judge_invocations}"
            )
        return self


class GapInventory(BaseModel):
    """The two-category gap inventory persisted at gap-inventory.yaml.

    Per sub-plan-doc §3 AC.GAPAN.2:

    - ``schema_version`` is the literal int 1; future bumps need
      migration.
    - ``extraction_id`` ties the inventory to the workspace's
      extraction.
    - ``analyzed_at`` is the ISO 8601 timestamp; excluded from the
      idempotence content-hash per AC.GAPAN.5.
    - ``audit_path`` points at the audit-log directory whose entries
      trace the analysis run that produced this inventory.
    - ``gaps`` carries each :class:`Gap` produced by the run.
    - ``summary`` carries pre-aggregated counts; the ``model_validator``
      enforces no duplicate ``gap_id`` AND that ``summary`` matches
      the aggregate of ``gaps``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    extraction_id: str = Field(min_length=1)
    analyzed_at: str  # ISO 8601 with timezone
    audit_path: str = Field(min_length=1)
    gaps: list[Gap] = Field(default_factory=list)
    summary: GapSummary = Field(default_factory=GapSummary)

    @model_validator(mode="after")
    def _enforce_no_duplicate_gap_id_and_summary_match(
        self,
    ) -> "GapInventory":
        seen: set[str] = set()
        for g in self.gaps:
            if g.gap_id in seen:
                raise ValueError(
                    f"GapInventory: duplicate gap_id={g.gap_id!r} "
                    f"(each ID must be unique in the inventory)"
                )
            seen.add(g.gap_id)
        # Aggregate-vs-summary check.
        a_count = sum(
            1 for g in self.gaps
            if g.category == "objective_without_verified_backing"
        )
        b_count = sum(
            1 for g in self.gaps if g.category == "implementation_orphan"
        )
        s_count = sum(1 for g in self.gaps if g.confidence == "STRONG")
        w_count = sum(1 for g in self.gaps if g.confidence == "WEAK")
        total = len(self.gaps)
        s = self.summary
        if (
            s.category_a_count != a_count
            or s.category_b_count != b_count
            or s.strong_count != s_count
            or s.weak_count != w_count
            or s.total != total
        ):
            raise ValueError(
                f"GapInventory: summary mismatch — got "
                f"summary={s.model_dump()} but aggregate "
                f"category_a={a_count} category_b={b_count} "
                f"strong={s_count} weak={w_count} total={total}"
            )
        return self

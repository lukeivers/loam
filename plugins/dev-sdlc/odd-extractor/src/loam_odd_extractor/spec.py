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

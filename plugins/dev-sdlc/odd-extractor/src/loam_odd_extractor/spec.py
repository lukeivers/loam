"""Pydantic models for the odd-extractor's stage artefacts.

Per AC.OREK.3 — each of the four stages (init / analyze / generate /
verify) produces a structured artefact. The Pydantic models here are
the structural contracts.

Per Surface #9 (plan-doc §5) — all models use ``ConfigDict(extra='forbid')``
so additional fields are rejected at parse time. Cycle 3 + 4 may
extend with additive fields (forward-compat); this cycle ships the
minimal-required-surface so adapters can extend per-language.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from loam.cost_governance import BudgetEnvelope


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
    """Stage 3 (generate) output — raw ACs from per-slice extraction.

    Written to ``<workspace>/.loam/extractions/<repo-id>/raw-acs.yaml``.

    Cycle 1 ships zero adapters, so :attr:`acs` is always empty and
    every input path lands in :attr:`unhandled_paths`. Cycle 2 adds
    confidence bands as fields on each AC dict; Cycles 3+4 populate
    via real adapters. The dict-typed ``acs`` field deliberately
    stays loose so Cycle 2's schema migration is additive.
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

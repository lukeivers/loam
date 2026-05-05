"""loam odd-extractor — ODD reverse-engineering scaffold.

Cycle 1 (v0.1.8) ships the four-stage workflow shape +
language-adapter registry + dry-run cost estimate + foreign-codebase
budget envelope. Cycle 2 (v0.1.8) ships confidence bands +
ratification workflow + PM integration. Cycles 3-4 ship Ruby/Rails
+ Python first-class adapters; Cycle 5 ships dev-sdlc SKILLs.

Public surface (per AC.OREK.7 + AC.BANDS.{1..7}):

- Stage functions (pure): :func:`init_extraction`, :func:`analyze_repo`,
  :func:`generate_raw_acs`, :func:`verify_contract`.
- Pydantic models: :class:`ExtractionConfig`, :class:`AnalysisPlan`,
  :class:`Slice`, :class:`RawACs`, :class:`ContractDraft`.
- Bands (Cycle 2): :class:`ConfidenceBand` (enum), :class:`Evidence`,
  :class:`BandedAC` (Pydantic with per-band model_validator).
- Ratification (Cycle 2): :class:`RatificationAction` (frozen
  dataclass), factory funcs :func:`promote` / :func:`demote` /
  :func:`edit` / :func:`reject`, :func:`apply_ratification_action`,
  :func:`enqueue_ratification_batch`.
- Ratification state (Cycle 2): :class:`RatificationState`,
  :func:`load_ratification_state`, :func:`save_ratification_state`,
  :func:`initialise_ratification_state`.
- Registry: :class:`LanguageAdapter` (Protocol),
  :func:`register_adapter`, :func:`discover_adapters`.
- Budget: :func:`estimate_for_extraction`, :func:`enforce_budget`,
  :func:`default_budget`, :func:`budget_from_cents`.
- Errors: :class:`OddExtractorError`, :class:`StageError`,
  :class:`RegistryError`, :class:`BudgetExceededError`,
  :class:`RatificationRefusedError`.
- State: :class:`ExtractionState`, :func:`compute_repo_id`,
  :func:`extraction_dir`, :func:`load_state`, :func:`save_state`.
- CLI: :func:`build_odd_extract_subcommand` (entry-point binding).
"""

from __future__ import annotations

from .analyze import analyze_repo
from .bands import BandedAC, ConfidenceBand, Evidence
from .budget import (
    budget_from_cents,
    default_budget,
    enforce_budget,
    estimate_for_extraction,
)
from .cli import build_odd_extract_subcommand
from .errors import (
    BudgetExceededError,
    OddExtractorError,
    RatificationRefusedError,
    RegistryError,
    StageError,
)
from .generate import generate_raw_acs
from .init import init_extraction
from .ratification_state import (
    CompletedAction,
    PendingTarget,
    RatificationState,
    RatificationStateV2,
    initialise_ratification_state,
    load_ratification_state,
    save_ratification_state,
)
from .ratify import (
    ObjectiveRatificationAction,
    RatificationAction,
    apply_objective_ratification_action,
    apply_ratification_action,
    demote,
    demote_capability,
    demote_constraint,
    demote_objective,
    edit,
    edit_capability,
    edit_constraint,
    edit_objective,
    enqueue_objective_ratification_batch,
    enqueue_ratification_batch,
    parse_altitude_provenance,
    promote,
    promote_capability,
    promote_constraint,
    promote_objective,
    reject,
    reject_capability,
    reject_constraint,
    reject_objective,
    is_test_asserts_outcome,
)
from .backing_map import (
    backing_map_path,
    is_idempotent_skip,
    load_backing_map,
    populate_backing_map,
    save_backing_map,
)
from .registry import (
    LanguageAdapter,
    clear_manual_registry,
    discover_adapters,
    register_adapter,
)
from .spec import (
    AltitudeCheckResult,
    AnalysisPlan,
    AugmentedObjectiveSet,
    BackingMap,
    BackingMapEntry,
    BuildNextCandidate,
    BuildNextRecommendation,
    Capability,
    CapabilityEvidence,
    Constraint,
    ConstraintEvidence,
    ContractDraft,
    EvidenceRowRef,
    ExtractionConfig,
    FlaggedMissing,
    Gap,
    GapInventory,
    GapSummary,
    HeuristicPrior,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    OrphanRow,
    RawACs,
    Slice,
    SynthesisResult,
    ValidationReport,
)
from .gap_analysis import (
    analyze_gaps,
    emit_end_audit,
    emit_persisted_audit,
    emit_start_audit,
    gap_inventory_path,
    is_degenerate_distribution,
    load_gap_inventory,
    render_stdout_summary,
    save_gap_inventory,
)
from .build_next import (
    DEFAULT_LIMIT as BUILD_NEXT_DEFAULT_LIMIT,
    DEFAULT_LLM_JUDGE_BUDGET_CENTS as BUILD_NEXT_DEFAULT_BUDGET_CENTS,
    LLM_JUDGE_INVOCATION_CAP as BUILD_NEXT_LLM_JUDGE_INVOCATION_CAP,
    build_next_md_path,
    build_next_yaml_path,
    check_build_next_cost_band,
    emit_build_next_end_audit,
    emit_build_next_persisted_audit,
    emit_build_next_start_audit,
    estimate_build_next_cost_cents,
    load_recommendation,
    render_stdout_summary as render_build_next_stdout_summary,
    save_recommendation,
    score_candidates,
)
from .multi_source import collect_multi_source_inputs
from .synthesis import (
    estimate_synthesis_cost_cents,
    synthesize_objectives,
)
from .completeness import (
    MAX_FLAGGED_CANDIDATES,
    estimate_judge_cost_cents,
    flag_missing_objectives,
    heuristic_priors,
)
from .interview import (
    augmented_objectives_path,
    load_augmented_objectives,
    parse_response,
    render_confirm_existing,
    render_flag_missing_candidate,
    render_free_form_add,
    resolve_pm_handle,
    run_interview,
    save_augmented_objectives,
)
from .altitude_validator import validate_altitude
from .state import (
    ExtractionState,
    compute_repo_id,
    extraction_dir,
    load_state,
    save_state,
)
from .verify import verify_contract

# v0.2.3 Cycle 3 — incremental-mode watch reframed at objective altitude.
# The v0.2.0 BandedAC-altitude types are replaced with
# OutOfDateObjective + OrphanedObjective per AC.WATCHOBJ.1.
from .diff_classifier import (
    EvidenceClassification,
    OrphanedObjective,
    OutOfDateObjective,
    classify_evidence,
)
from .domain_batching import (
    LOAM_INTERNAL_AC_NAMESPACES,
    group_by_domain,
    group_proposals_by_domain,
    infer_domain,
)
from .incremental import (
    ContractNotFoundError,
    IncrementalRefusedError,
    IncrementalRunResult,
    run_incremental,
)
from .incremental_ratify import (
    EnqueueResult,
    enqueue_incremental_proposals,
)
from .proposals import (
    IncrementalProposal,
    IncrementalProposalSet,
    generate_proposals,
)

# Cycle 3 (v0.1.8) — Ruby/Rails first-class adapter. Lazy-loadable
# but re-exported here so callers can ``from loam_odd_extractor
# import RubyAdapter``. Per Surface #8, the tree-sitter import
# inside :mod:`.lang.ruby.parser` is itself lazy at first parse-call.
from .lang.ruby import RubyAdapter

# Cycle 4a (v0.1.8) — JavaScript/TypeScript/Playwright first-class
# adapter. Same lazy-import pattern as the Ruby adapter (per
# plan-doc Surface #11); ``import loam_odd_extractor`` does not
# pull tree-sitter-javascript/typescript into memory.
from .lang.jsts import JsTsAdapter

__all__ = [
    "AltitudeCheckResult",
    "AnalysisPlan",
    "AugmentedObjectiveSet",
    "BUILD_NEXT_DEFAULT_BUDGET_CENTS",
    "BUILD_NEXT_DEFAULT_LIMIT",
    "BUILD_NEXT_LLM_JUDGE_INVOCATION_CAP",
    "BackingMap",
    "BackingMapEntry",
    "BandedAC",
    "BuildNextCandidate",
    "BuildNextRecommendation",
    "BudgetExceededError",
    "Capability",
    "CapabilityEvidence",
    "CompletedAction",
    "ConfidenceBand",
    "Constraint",
    "ConstraintEvidence",
    "ContractDraft",
    "ContractNotFoundError",
    "EnqueueResult",
    "Evidence",
    "EvidenceClassification",
    "EvidenceRowRef",
    "ExtractionConfig",
    "ExtractionState",
    "FlaggedMissing",
    "Gap",
    "GapInventory",
    "GapSummary",
    "HeuristicPrior",
    "IncrementalProposal",
    "IncrementalProposalSet",
    "IncrementalRefusedError",
    "IncrementalRunResult",
    "JsTsAdapter",
    "LOAM_INTERNAL_AC_NAMESPACES",
    "LanguageAdapter",
    "MAX_FLAGGED_CANDIDATES",
    "MultiSourceBundle",
    "Objective",
    "ObjectiveEvidence",
    "ObjectiveRatificationAction",
    "OddExtractorError",
    "OrphanRow",
    "OrphanedObjective",
    "OutOfDateObjective",
    "PendingTarget",
    "RatificationAction",
    "RatificationRefusedError",
    "RatificationState",
    "RatificationStateV2",
    "RawACs",
    "RegistryError",
    "RubyAdapter",
    "Slice",
    "StageError",
    "SynthesisResult",
    "ValidationReport",
    "analyze_gaps",
    "analyze_repo",
    "apply_objective_ratification_action",
    "apply_ratification_action",
    "augmented_objectives_path",
    "backing_map_path",
    "budget_from_cents",
    "build_next_md_path",
    "build_next_yaml_path",
    "check_build_next_cost_band",
    "build_odd_extract_subcommand",
    "classify_evidence",
    "clear_manual_registry",
    "collect_multi_source_inputs",
    "compute_repo_id",
    "default_budget",
    "demote",
    "demote_capability",
    "demote_constraint",
    "demote_objective",
    "discover_adapters",
    "edit",
    "edit_capability",
    "edit_constraint",
    "edit_objective",
    "emit_build_next_end_audit",
    "emit_build_next_persisted_audit",
    "emit_build_next_start_audit",
    "emit_end_audit",
    "emit_persisted_audit",
    "emit_start_audit",
    "enforce_budget",
    "enqueue_incremental_proposals",
    "enqueue_objective_ratification_batch",
    "enqueue_ratification_batch",
    "estimate_build_next_cost_cents",
    "estimate_for_extraction",
    "estimate_judge_cost_cents",
    "estimate_synthesis_cost_cents",
    "extraction_dir",
    "flag_missing_objectives",
    "gap_inventory_path",
    "generate_proposals",
    "generate_raw_acs",
    "group_by_domain",
    "group_proposals_by_domain",
    "heuristic_priors",
    "infer_domain",
    "init_extraction",
    "initialise_ratification_state",
    "is_degenerate_distribution",
    "is_idempotent_skip",
    "load_augmented_objectives",
    "load_backing_map",
    "load_gap_inventory",
    "load_ratification_state",
    "load_recommendation",
    "load_state",
    "parse_altitude_provenance",
    "parse_response",
    "populate_backing_map",
    "promote",
    "promote_capability",
    "promote_constraint",
    "promote_objective",
    "register_adapter",
    "reject",
    "reject_capability",
    "reject_constraint",
    "reject_objective",
    "render_build_next_stdout_summary",
    "render_confirm_existing",
    "render_flag_missing_candidate",
    "render_free_form_add",
    "render_stdout_summary",
    "resolve_pm_handle",
    "run_incremental",
    "run_interview",
    "save_augmented_objectives",
    "save_backing_map",
    "save_gap_inventory",
    "save_recommendation",
    "save_ratification_state",
    "save_state",
    "score_candidates",
    "synthesize_objectives",
    "is_test_asserts_outcome",
    "validate_altitude",
    "verify_contract",
]

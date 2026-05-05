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
    BackingMap,
    BackingMapEntry,
    Capability,
    CapabilityEvidence,
    Constraint,
    ConstraintEvidence,
    ContractDraft,
    EvidenceRowRef,
    ExtractionConfig,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    OrphanRow,
    RawACs,
    Slice,
    SynthesisResult,
    ValidationReport,
)
from .multi_source import collect_multi_source_inputs
from .synthesis import (
    estimate_synthesis_cost_cents,
    synthesize_objectives,
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

# Cycle 1 (v0.2.0) — incremental-mode watch surface. Composes on top
# of v0.1.8 full-mode workflow + v0.1.7 PM batch API.
from .diff_classifier import (
    EvidenceClassification,
    OrphanedAC,
    OutOfDateAC,
    classify_evidence,
)
from .domain_batching import (
    LOAM_INTERNAL_AC_NAMESPACES,
    group_by_domain,
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
    "BackingMap",
    "BackingMapEntry",
    "BandedAC",
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
    "IncrementalProposal",
    "IncrementalProposalSet",
    "IncrementalRefusedError",
    "IncrementalRunResult",
    "JsTsAdapter",
    "LOAM_INTERNAL_AC_NAMESPACES",
    "LanguageAdapter",
    "MultiSourceBundle",
    "Objective",
    "ObjectiveEvidence",
    "ObjectiveRatificationAction",
    "OddExtractorError",
    "OrphanRow",
    "OrphanedAC",
    "OutOfDateAC",
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
    "analyze_repo",
    "apply_objective_ratification_action",
    "apply_ratification_action",
    "backing_map_path",
    "budget_from_cents",
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
    "enforce_budget",
    "enqueue_incremental_proposals",
    "enqueue_objective_ratification_batch",
    "enqueue_ratification_batch",
    "estimate_for_extraction",
    "estimate_synthesis_cost_cents",
    "extraction_dir",
    "generate_proposals",
    "generate_raw_acs",
    "group_by_domain",
    "infer_domain",
    "init_extraction",
    "initialise_ratification_state",
    "is_idempotent_skip",
    "load_backing_map",
    "load_ratification_state",
    "load_state",
    "parse_altitude_provenance",
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
    "run_incremental",
    "save_backing_map",
    "save_ratification_state",
    "save_state",
    "synthesize_objectives",
    "is_test_asserts_outcome",
    "validate_altitude",
    "verify_contract",
]

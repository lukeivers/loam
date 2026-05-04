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
    RatificationState,
    initialise_ratification_state,
    load_ratification_state,
    save_ratification_state,
)
from .ratify import (
    RatificationAction,
    apply_ratification_action,
    demote,
    edit,
    enqueue_ratification_batch,
    promote,
    reject,
)
from .registry import (
    LanguageAdapter,
    clear_manual_registry,
    discover_adapters,
    register_adapter,
)
from .spec import (
    AnalysisPlan,
    ContractDraft,
    ExtractionConfig,
    RawACs,
    Slice,
)
from .state import (
    ExtractionState,
    compute_repo_id,
    extraction_dir,
    load_state,
    save_state,
)
from .verify import verify_contract

__all__ = [
    "AnalysisPlan",
    "BandedAC",
    "BudgetExceededError",
    "CompletedAction",
    "ConfidenceBand",
    "ContractDraft",
    "Evidence",
    "ExtractionConfig",
    "ExtractionState",
    "LanguageAdapter",
    "OddExtractorError",
    "RatificationAction",
    "RatificationRefusedError",
    "RatificationState",
    "RawACs",
    "RegistryError",
    "Slice",
    "StageError",
    "analyze_repo",
    "apply_ratification_action",
    "budget_from_cents",
    "build_odd_extract_subcommand",
    "clear_manual_registry",
    "compute_repo_id",
    "default_budget",
    "demote",
    "discover_adapters",
    "edit",
    "enforce_budget",
    "enqueue_ratification_batch",
    "estimate_for_extraction",
    "extraction_dir",
    "generate_raw_acs",
    "init_extraction",
    "initialise_ratification_state",
    "load_ratification_state",
    "load_state",
    "promote",
    "register_adapter",
    "reject",
    "save_ratification_state",
    "save_state",
    "verify_contract",
]

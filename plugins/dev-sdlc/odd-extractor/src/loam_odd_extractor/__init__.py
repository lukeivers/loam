"""loam odd-extractor — ODD reverse-engineering scaffold.

Cycle 1 (v0.1.8) ships the four-stage workflow shape +
language-adapter registry + dry-run cost estimate + foreign-codebase
budget envelope. Cycles 2-4 ship confidence bands, ratification
workflow, Ruby/Rails first-class adapter, Python first-class adapter.

Public surface (per AC.OREK.7):

- Stage functions (pure): :func:`init_extraction`, :func:`analyze_repo`,
  :func:`generate_raw_acs`, :func:`verify_contract`.
- Pydantic models: :class:`ExtractionConfig`, :class:`AnalysisPlan`,
  :class:`Slice`, :class:`RawACs`, :class:`ContractDraft`.
- Registry: :class:`LanguageAdapter` (Protocol),
  :func:`register_adapter`, :func:`discover_adapters`.
- Budget: :func:`estimate_for_extraction`, :func:`enforce_budget`,
  :func:`default_budget`, :func:`budget_from_cents`.
- Errors: :class:`OddExtractorError`, :class:`StageError`,
  :class:`RegistryError`, :class:`BudgetExceededError`.
- State: :class:`ExtractionState`, :func:`compute_repo_id`,
  :func:`extraction_dir`, :func:`load_state`, :func:`save_state`.
- CLI: :func:`build_odd_extract_subcommand` (entry-point binding).
"""

from __future__ import annotations

from .analyze import analyze_repo
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
    RegistryError,
    StageError,
)
from .generate import generate_raw_acs
from .init import init_extraction
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
    "BudgetExceededError",
    "ContractDraft",
    "ExtractionConfig",
    "ExtractionState",
    "LanguageAdapter",
    "OddExtractorError",
    "RawACs",
    "RegistryError",
    "Slice",
    "StageError",
    "analyze_repo",
    "budget_from_cents",
    "build_odd_extract_subcommand",
    "clear_manual_registry",
    "compute_repo_id",
    "default_budget",
    "discover_adapters",
    "enforce_budget",
    "estimate_for_extraction",
    "extraction_dir",
    "generate_raw_acs",
    "init_extraction",
    "load_state",
    "register_adapter",
    "save_state",
    "verify_contract",
]

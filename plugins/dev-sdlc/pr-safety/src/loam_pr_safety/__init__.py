"""loam-pr-safety — PR-safety gate engine.

Public API:

  - :class:`BandedContract` — typed read of the odd-extractor's
    contract sidecar.
  - :func:`read_contract` — banded-contract reader.
  - :class:`Diff`, :class:`DiffEntry`, :class:`Hunk` — typed diff
    representation.
  - :func:`parse_diff` — git-diff wrapper.
  - :class:`ClassificationResult`, :class:`TouchedAC`,
    :class:`CandidateAC` — classifier output.
  - :func:`classify` — diff classifier (line-overlap + symbol-overlap).
  - :class:`GateDecision`, :class:`GateAction` — gate output.
  - :func:`decide` — per-band gating engine.
  - :class:`OverrideRequest` — override-flow request payload.
  - :func:`recognise_override` — override-commit recognition.
  - :func:`apply_override` — additive-overlay writer + audit-log.
  - :func:`is_production_stake` — workspace safety_profile reader.
  - :func:`write_audit_entry` — SOC-2 audit-trail floor writer.

  - typed exceptions :class:`PRSafetyError`,
    :class:`ContractMissingError`, :class:`ContractMalformedError`,
    :class:`ClassifierAccuracyError`, :class:`OverrideRejectedError`,
    :class:`GateError`.

CLI: ``loam pr-safety gate <repo>`` — registered via the
``loam.cli.subcommands`` entry-point group (pyproject.toml).

Per AC.PRSG.1 — component scaffold present. v0.1.9 Cycle 1.
"""

from __future__ import annotations

from loam_pr_safety.audit import (
    audit_log_dir,
    list_entries,
    write_audit_entry,
)
from loam_pr_safety.classifier import classify
from loam_pr_safety.contract import read_contract
from loam_pr_safety.diff import parse_diff
from loam_pr_safety.errors import (
    ClassifierAccuracyError,
    ContractMalformedError,
    ContractMissingError,
    GateError,
    OverrideRejectedError,
    PRSafetyError,
)
from loam_pr_safety.gate import decide
from loam_pr_safety.override import (
    apply_override,
    recognise_override,
)
from loam_pr_safety.profile import is_production_stake
from loam_pr_safety.spec import (
    BandedContract,
    CandidateAC,
    ClassificationResult,
    Diff,
    DiffEntry,
    GateAction,
    GateDecision,
    Hunk,
    OverrideRequest,
    TouchedAC,
)


__all__ = [
    "BandedContract",
    "CandidateAC",
    "ClassificationResult",
    "ClassifierAccuracyError",
    "ContractMalformedError",
    "ContractMissingError",
    "Diff",
    "DiffEntry",
    "GateAction",
    "GateDecision",
    "GateError",
    "Hunk",
    "OverrideRejectedError",
    "OverrideRequest",
    "PRSafetyError",
    "TouchedAC",
    "apply_override",
    "audit_log_dir",
    "classify",
    "decide",
    "is_production_stake",
    "list_entries",
    "parse_diff",
    "read_contract",
    "recognise_override",
    "write_audit_entry",
]

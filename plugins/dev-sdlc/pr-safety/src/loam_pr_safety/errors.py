"""Typed exceptions for loam-pr-safety.

Hierarchy:

  PRSafetyError
    |- ContractMissingError
    |    |- ContractMalformedError
    |- ClassifierAccuracyError
    |- OverrideRejectedError
    |- GateError

Per AC.PRSG.{2,3,4,5,6,9} — each error class corresponds to a
named failure mode in the gate workflow.
"""

from __future__ import annotations


class PRSafetyError(Exception):
    """Base for all loam-pr-safety errors."""


class ContractMissingError(PRSafetyError):
    """Raised when ``read_contract`` cannot locate the sidecar.

    Per AC.PRSG.2 — the odd-extractor's
    ``<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml``
    is absent. Caller should run ``loam odd-extract <repo>`` first.
    """


class ContractMalformedError(ContractMissingError):
    """Raised when the contract sidecar exists but doesn't validate.

    Subclass of :class:`ContractMissingError` so callers that catch
    "missing OR malformed" via a single ``except`` can do so. The
    inner reason (per-band evidence rule violation, schema version
    mismatch, etc.) is in the message.
    """


class ClassifierAccuracyError(PRSafetyError):
    """Raised when the diff-classifier accuracy on the synthetic
    test set falls below the ≥90% bar.

    Per AC.PRSG.3 + master plan §7.1 — this is the most-load-bearing
    halt-trigger of Cycle 1. Build agent halts and surfaces for
    AST-aware extension when this fires.
    """


class OverrideRejectedError(PRSafetyError):
    """Raised when an override-flow ratification is denied.

    Per AC.PRSG.5 — owner answered no through the PM batch. The
    gate's exit status is non-zero (4); audit-log records the
    rejection.
    """


class GateError(PRSafetyError):
    """Raised on internal gate-engine errors that aren't the above.

    Examples: malformed diff input; symbol-overlap heuristic
    failure on unparseable evidence citations; unexpected workspace
    state.
    """

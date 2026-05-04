"""Typed exceptions for the odd-extractor.

Every public error type derives from :class:`OddExtractorError`. The
CLI catches `OddExtractorError` and exits with status 2; structurally
distinct error types let tests assert against the right shape per AC.
"""

from __future__ import annotations


class OddExtractorError(Exception):
    """Base class for every odd-extractor error.

    Per AC.OREK.* test surface — tests assert against this base when
    scope-broad (any extractor failure); subclasses for AC-specific
    refinement.
    """


class StageError(OddExtractorError):
    """A stage (init / analyze / generate / verify) failed.

    Per AC.OREK.3 — stage contracts are pure functions; a stage that
    can't complete its input → output transition raises this.
    Carries the stage name in the message for diagnosis.
    """


class RegistryError(OddExtractorError):
    """Language-adapter registry rejected a registration or discovery
    failed.

    Per AC.OREK.4 — Protocol-violators (missing ``name``,
    ``supports``, or ``extract``), name collisions, and entry-point
    load failures route through this.
    """


class BudgetExceededError(OddExtractorError):
    """A live extraction's dry-run estimate exceeds the configured
    foreign-codebase budget envelope hard cap.

    Per AC.OREK.6 — raised when ``--live`` is requested without
    ``--budget-override`` and the dry-run estimate's
    ``estimated_money_cents`` exceeds the ``BudgetEnvelope``'s
    ``hard_cap_money_cents``. Carries the estimate + envelope on the
    message for diagnosability.
    """


class RatificationRefusedError(OddExtractorError):
    """A ratification action was rejected at construction or apply.

    Per AC.BANDS.5 (v0.1.8 Cycle 2) — raised when a PLAUSIBLE→VERIFIED
    promotion attempt lacks the explicit-yes opt-in (Decision I:
    silent promotion forbidden). Also raised for malformed action
    constructions (missing ``ac_id``, mismatched bands on a promote/
    demote, etc.) so a caller can distinguish "structurally invalid
    action" from "AC not found in pending list".
    """

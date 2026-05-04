"""Budget primitives for the odd-extractor.

Per AC.OREK.5 — every CLI invocation produces a dry-run estimate
BEFORE any extraction work runs. The estimate composes on top of
v0.1.6 cost-governance's :func:`dry_run_estimate` primitive — no
re-implementation.

Per AC.OREK.6 — live extraction (``--live``) without
``--budget-override`` enforces the foreign-codebase budget envelope:
if the dry-run estimate's ``estimated_money_cents`` exceeds the
:class:`BudgetEnvelope`'s ``hard_cap_money_cents``, refuse to run
live and raise :class:`BudgetExceededError`.

Defaults per Surface #7 (plan-doc §5):

- ``hard_cap_money_cents = 1000`` ($10)
- ``soft_cap_money_cents = 500`` ($5)
- ``overrun_action = halt``

These are starter values; Cycles 3+4 calibrate against real adapters.
"""

from __future__ import annotations

from typing import Any

from loam.cost_governance import (
    BudgetEnvelope,
    EstimateResult,
    OverrunAction,
    dry_run_estimate,
)

from .errors import BudgetExceededError


# ---- defaults -------------------------------------------------------


DEFAULT_HARD_CAP_CENTS = 1000
DEFAULT_SOFT_CAP_CENTS = 500


def default_budget() -> BudgetEnvelope:
    """Return the default foreign-codebase budget envelope.

    Per Surface #7 — $10 hard / $5 soft / halt-on-overrun. Tunable
    by the caller; configurable via CLI ``--budget-cents``.
    """
    return BudgetEnvelope(
        hard_cap_money_cents=DEFAULT_HARD_CAP_CENTS,
        soft_cap_money_cents=DEFAULT_SOFT_CAP_CENTS,
        overrun_action=OverrunAction.halt,
    )


def budget_from_cents(cents: int) -> BudgetEnvelope:
    """Construct a :class:`BudgetEnvelope` with both caps set to
    ``cents``, halt-on-overrun.

    Per AC.OREK.6 — ``--budget-cents`` flag uses this.
    """
    if cents < 0:
        raise ValueError(
            f"budget cents must be non-negative; got {cents}"
        )
    return BudgetEnvelope(
        hard_cap_money_cents=cents,
        soft_cap_money_cents=cents,
        overrun_action=OverrunAction.halt,
    )


# ---- estimate wrapper ----------------------------------------------


def estimate_for_extraction(
    *,
    scope_id: str,
    recent_actuals: list[dict[str, Any]] | None = None,
) -> EstimateResult:
    """Wrap :func:`loam.cost_governance.dry_run_estimate` for
    extraction-shaped scopes.

    Per AC.OREK.5 — the wrapper exists so callers don't have to
    import cost-governance directly + so future extraction-specific
    estimation refinements (e.g., per-slice cost projection) can
    land here without changing the call sites.

    Cold-start (no recent actuals) returns LOW band + non-empty
    reason per the cost-governance contract. Cycle 1's tests
    exercise the cold-start path explicitly.
    """
    return dry_run_estimate(
        scope_id=scope_id,
        recent_actuals=list(recent_actuals or []),
    )


# ---- envelope enforcement ------------------------------------------


def enforce_budget(
    *,
    estimate: EstimateResult,
    envelope: BudgetEnvelope,
    override: bool = False,
) -> None:
    """Raise :class:`BudgetExceededError` if ``estimate`` would
    exceed the ``envelope``'s hard cap, unless ``override=True``.

    Per AC.OREK.6 — live runs route through this gate. ``override``
    is the ``--budget-override`` opt-out.

    Estimate is in cents (integer). When the cost-governance
    estimator returns LOW band on cold-start (zeroed estimate), the
    check passes structurally — there's nothing to compare against.
    A user invoking ``--live`` with no recent actuals sees the
    LOW-band reason in stdout but is not blocked; this is the
    intended cold-start ergonomic.
    """
    if override:
        return
    if estimate.estimated_money_cents > envelope.hard_cap_money_cents:
        raise BudgetExceededError(
            "live extraction's estimated cost "
            f"({estimate.estimated_money_cents} cents) exceeds the "
            "configured foreign-codebase budget ceiling "
            f"({envelope.hard_cap_money_cents} cents). "
            "Re-run with --budget-cents <higher-N> or "
            "--budget-override to proceed."
        )

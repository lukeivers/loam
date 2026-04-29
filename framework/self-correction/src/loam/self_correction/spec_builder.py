"""Deterministic correction-scope builder.

`build_correction_spec(trigger, triggering_budget?, config)` produces a
`ScopeSpec` with:

  - `reversibility_class = compensatable` forced. Attempting to declare
    `irreversible` raises at the builder (CR11).
  - Budget inherited-and-scaled from the triggering scope (ruling #3).
    Floors applied BEFORE scaling so a tiny triggering budget still
    produces a workable correction budget. Axes the triggering scope
    did not declare stay undeclared — we do not invent caps.
  - Objective text from a template (Eve-inference #5).
  - Owner_persona = self_correction so the corrector carries a stable
    identity in spans.

Max-first: no LLM inside the builder.
"""

from __future__ import annotations

from loam.scope_of_work import (
    Budget,
    BudgetAxis,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)

from .config import CorrectionConfig, default_config
from .spec import CorrectionTrigger


class IrreversibleCorrectionSpecError(ValueError):
    """Raised when a caller tries to author an irreversible correction.

    Correction scopes must be compensatable — the four-part protocol
    requires a reversal path so a failed correction does not amplify
    the original failure.
    """


def build_correction_spec(
    trigger: CorrectionTrigger,
    *,
    failure_class: str,
    triggering_budget: Budget | None = None,
    config: CorrectionConfig | None = None,
    requested_reversibility_class: ReversibilityClass = (
        ReversibilityClass.compensatable
    ),
) -> ScopeSpec:
    """Produce a ScopeSpec for a correction.

    `triggering_budget` is optional — when the triggering scope does
    not expose a budget (e.g. user_reported on no scope), floors alone
    apply on axes where the caller explicitly passes the floor axis.
    """
    if requested_reversibility_class != ReversibilityClass.compensatable:
        raise IrreversibleCorrectionSpecError(
            f"correction scopes must be compensatable; caller requested "
            f"{requested_reversibility_class.value!r}"
        )

    cfg = config or default_config()
    budget = _build_budget(triggering_budget, cfg)

    objective = cfg.objective_template.format(
        failure_class=failure_class,
        trigger_source=trigger.source.value,
    )

    constraints = (
        "Records all four parts of the correction protocol "
        "(class, instance, cause, remedy) before completion.",
        "Does not itself trigger a cascade of corrections for the same class.",
    )

    return ScopeSpec(
        goal=objective,
        constraints=constraints,
        budget=budget,
        reversibility_class=ReversibilityClass.compensatable,
        success_criteria=(
            SuccessCriterion(
                criterion_id="four_part_protocol_complete",
                description=(
                    "All four record types persisted in "
                    "correction_episode_records."
                ),
            ),
        ),
        observers=(),
        escalation_triggers=(),
        owner_persona="self_correction",
    )


def _build_budget(
    triggering: Budget | None, cfg: CorrectionConfig
) -> Budget:
    """Apply floors-first-then-scale per ruling #3.

    The intent expressed in the proposal (§4.3, CR12):

      "Floors: 60s time and 2000 tokens apply BEFORE scaling so a very
       small triggering scope still produces a workable correction
       budget."

    Interpretation: take max(triggering, floor) on each declared axis,
    then scale by `budget_scale`. The final value is never less than
    `floor * budget_scale` on axes where a floor exists.

    Axes the triggering scope did not declare stay None — we do not
    invent caps (honest declaration; cost-governance otherwise sees a
    phantom axis it cannot reconcile).
    """
    if triggering is None:
        # No inherited budget — declare the floor on axes the floor
        # applies to (time + tokens), scaled. Honest declaration.
        time_val = int(cfg.budget_time_floor_seconds * cfg.budget_scale) or 1
        tokens_val = int(cfg.budget_token_floor * cfg.budget_scale) or 1
        return Budget(time_seconds=time_val, tokens=tokens_val)

    time_v: int | None = None
    tokens_v: int | None = None
    money_v: int | None = None

    if triggering.time_seconds is not None:
        raised = max(triggering.time_seconds, cfg.budget_time_floor_seconds)
        time_v = max(int(raised * cfg.budget_scale), 1)

    if triggering.tokens is not None:
        raised = max(triggering.tokens, cfg.budget_token_floor)
        tokens_v = max(int(raised * cfg.budget_scale), 1)

    if triggering.money_cents is not None:
        # No floor on money axis per ruling #3 (only time + tokens).
        money_v = max(int(triggering.money_cents * cfg.budget_scale), 1)

    # Budget requires at least one axis. If the triggering had only
    # undeclared axes (unlikely — cost-governance requires at least
    # one) we backfill with scaled floors.
    if time_v is None and tokens_v is None and money_v is None:
        time_v = max(
            int(cfg.budget_time_floor_seconds * cfg.budget_scale), 1
        )
        tokens_v = max(int(cfg.budget_token_floor * cfg.budget_scale), 1)

    return Budget(time_seconds=time_v, tokens=tokens_v, money_cents=money_v)


__all__ = [
    "IrreversibleCorrectionSpecError",
    "build_correction_spec",
]

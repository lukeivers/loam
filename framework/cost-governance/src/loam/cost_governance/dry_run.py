# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""v0.1.6 — dry-run primitive + foreign-codebase budget envelope.

Per AC.PSAFE.4 and AC.PSAFE.5 (sub-plan
``docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md``).

**Dry-run primitive (AC.PSAFE.4)**: a thin extrapolator that consumes
the cost-governance store's recent rolling-window actuals and projects
forward an estimate for an upcoming dispatch. Returns an
``EstimateResult`` carrying:

  - ``estimated_money_cents`` — projected money cost (int cents).
  - ``estimated_tokens``      — projected token count.
  - ``estimated_time_seconds``— projected wall-clock time.
  - ``confidence_band``       — HIGH / MEDIUM / LOW based on
                                sample-size of recent actuals.

This is NOT a model-call estimator. It is a structural seam that
consumers (the dev-sdlc extractor at v0.1.8, the production-safety
gate at v0.1.6) can use to surface a budget estimate BEFORE live
execution. When the rolling-window store is empty (cold-start), the
estimator returns a LOW-confidence zeroed result with a structured
``reason`` field.

**Foreign-codebase budget envelope (AC.PSAFE.5)**: a Pydantic model
attached to a scope, declaring hard-cap + soft-cap money limits and
an overrun-action enum (warn / halt / continue). Used by the v0.1.8
Eric-extractor to bound foreign-codebase analysis runs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---- confidence-band enum -----------------------------------------


class ConfidenceBand(str, Enum):
    """Confidence levels for ``EstimateResult``.

    Mapped from sample-size of recent actuals:
      - ``HIGH``   — ≥ 5 recent actuals; estimator has stable footing.
      - ``MEDIUM`` — 2-4 recent actuals; some signal but high variance.
      - ``LOW``    — 0-1 recent actuals; cold-start; estimate is
                     a structural seam, not load-bearing.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---- estimate-result -----------------------------------------------


class EstimateResult(BaseModel):
    """Pre-execution dry-run estimate (AC.PSAFE.4).

    All four fields are required. Numeric fields use int (cents +
    integer-token semantics; time is integer seconds).
    """

    model_config = ConfigDict(extra="forbid")

    estimated_money_cents: int = Field(ge=0)
    estimated_tokens: int = Field(ge=0)
    estimated_time_seconds: int = Field(ge=0)
    confidence_band: ConfidenceBand
    # Optional structured reason field — non-empty when
    # ``confidence_band == LOW`` (cold-start / no actuals).
    reason: str | None = None


# ---- overrun-action enum ------------------------------------------


class OverrunAction(str, Enum):
    """What the cost-governance runtime does when a
    ``BudgetEnvelope`` is breached.

    - ``warn``     — emit a notification + continue.
    - ``halt``     — refuse further activations under this scope
                     (structural refusal; matches the existing
                     halt-on-ceiling shape).
    - ``continue`` — log + continue (advisory-only envelope).
    """

    warn = "warn"
    halt = "halt"
    continue_ = "continue"

    @classmethod
    def from_value(cls, value: str) -> "OverrunAction":
        """Accept the literal `"continue"` string (`continue` is a
        Python keyword so the member name uses a trailing underscore).
        """
        if value == "continue":
            return cls.continue_
        return cls(value)


# ---- budget envelope -----------------------------------------------


class BudgetEnvelope(BaseModel):
    """Foreign-codebase budget envelope (AC.PSAFE.5).

    Attached to a scope by the consumer (e.g., the dev-sdlc extractor)
    to bound a foreign-codebase analysis run. The envelope is
    evaluated against actuals as the scope progresses; on overrun,
    the runtime takes the named action.

    soft_cap_money_cents must be <= hard_cap_money_cents. The pydantic
    validator enforces this; the runtime cannot construct an inverted
    envelope.
    """

    model_config = ConfigDict(extra="forbid")

    hard_cap_money_cents: int = Field(ge=0)
    soft_cap_money_cents: int = Field(ge=0)
    overrun_action: OverrunAction

    @model_validator(mode="after")
    def _validate_caps(self) -> "BudgetEnvelope":
        if self.soft_cap_money_cents > self.hard_cap_money_cents:
            raise ValueError(
                "soft_cap_money_cents must be <= hard_cap_money_cents; "
                f"got soft={self.soft_cap_money_cents} > "
                f"hard={self.hard_cap_money_cents}"
            )
        return self


# ---- dry-run primitive ---------------------------------------------


def dry_run_estimate(
    *,
    scope_id: str,
    recent_actuals: list[dict[str, Any]],
) -> EstimateResult:
    """Return a pre-execution estimate for an upcoming dispatch
    under ``scope_id``, based on ``recent_actuals``.

    ``recent_actuals`` is a list of dicts each carrying
    ``money_cents``, ``tokens``, ``time_seconds`` keys (ints).
    The caller is responsible for pulling these from the
    cost-governance store's rolling window (typically the last
    N completed scopes of the same shape).

    Confidence band:
      - HIGH:   len(recent_actuals) >= 5
      - MEDIUM: 2 <= len(recent_actuals) <= 4
      - LOW:    len(recent_actuals) <= 1

    Estimation method (deliberately simple):
      - Mean of recent_actuals for each of the three numeric fields.
      - On cold-start (empty list), returns zeros + LOW band + a
        structured reason naming the cold-start case.

    This is a v0.1.6 minimal-surface seam. Future releases (v0.1.8+)
    can swap in richer estimators (e.g., per-scope-shape regression)
    without changing the calling-convention.
    """
    n = len(recent_actuals)
    if n == 0:
        return EstimateResult(
            estimated_money_cents=0,
            estimated_tokens=0,
            estimated_time_seconds=0,
            confidence_band=ConfidenceBand.LOW,
            reason=(
                f"cold-start: no recent actuals available for "
                f"scope_id={scope_id!r}; estimate is a structural "
                "seam returning zeros."
            ),
        )

    money_sum = sum(int(a["money_cents"]) for a in recent_actuals)
    tokens_sum = sum(int(a["tokens"]) for a in recent_actuals)
    time_sum = sum(int(a["time_seconds"]) for a in recent_actuals)

    # Integer division — extrapolation is an estimate; a single-cent
    # rounding error is below the structural-floor of the envelope.
    money_mean = money_sum // n
    tokens_mean = tokens_sum // n
    time_mean = time_sum // n

    if n >= 5:
        band = ConfidenceBand.HIGH
        reason = None
    elif n >= 2:
        band = ConfidenceBand.MEDIUM
        reason = (
            f"medium-confidence: {n} recent actuals available for "
            f"scope_id={scope_id!r}; sample-size below stable threshold (5)."
        )
    else:
        band = ConfidenceBand.LOW
        reason = (
            f"low-confidence: only {n} recent actual available for "
            f"scope_id={scope_id!r}; high variance possible."
        )

    return EstimateResult(
        estimated_money_cents=money_mean,
        estimated_tokens=tokens_mean,
        estimated_time_seconds=time_mean,
        confidence_band=band,
        reason=reason,
    )

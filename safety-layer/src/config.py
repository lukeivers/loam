"""Safety config loader — `safety.yaml`.

The money-threshold floor (ruling #1) and its default are the only
settings this component reads from config today. Additional tunables
land here as the component matures.

Ruling #1 (Eve-inference #1, proposal §8): "tunable with floor,
minimum 1 cent." The builder has adopted the 1-cent floor as shipped —
rationale: any non-zero floor prevents a workspace dialling the gate
to zero, which would convert every money-budgeted scope into a
dangerous-op (a form of safety theatre — always-on gate degenerates
into ignored-gate).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


DEFAULT_MONEY_THRESHOLD_CENTS: int = 1000  # $10.00
MONEY_THRESHOLD_FLOOR_CENTS: int = 1  # ruling #1


class SafetyConfig(BaseModel):
    """Workspace safety configuration — loaded from safety.yaml."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    money_threshold_cents: int = Field(
        default=DEFAULT_MONEY_THRESHOLD_CENTS,
        ge=MONEY_THRESHOLD_FLOOR_CENTS,
        description=(
            "Money-budget threshold in whole cents above which a scope "
            "fires the dangerous-op gate regardless of reversibility_class. "
            f"Default {DEFAULT_MONEY_THRESHOLD_CENTS} cents ($10.00); "
            f"minimum floor {MONEY_THRESHOLD_FLOOR_CENTS} cent (ruling #1)."
        ),
    )

    @field_validator("money_threshold_cents")
    @classmethod
    def _enforce_floor(cls, v: int) -> int:
        if v < MONEY_THRESHOLD_FLOOR_CENTS:
            raise ValueError(
                f"money_threshold_cents={v} below floor "
                f"{MONEY_THRESHOLD_FLOOR_CENTS} (ruling #1)."
            )
        return v


def default_safety_config() -> SafetyConfig:
    return SafetyConfig()


def load_safety_config(path: Path) -> SafetyConfig:
    if not path.exists():
        return default_safety_config()
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return SafetyConfig.model_validate(data)

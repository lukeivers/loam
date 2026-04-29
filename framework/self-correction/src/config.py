"""Self-correction configuration.

Knobs:
  - depth_cap: max chain length of correction episodes (default 3)
  - cascade_window_seconds: same-class detection window (default 600)
  - cascade_threshold: same-class count threshold in window (default 3)
  - budget_time_floor_seconds: 60 per ruling #3
  - budget_token_floor: 2000 per ruling #3
  - budget_scale: 0.5 per ruling #3
  - dedup_ttl_seconds: 60 (Eve-inference #2)
  - aggregator_poll_interval_seconds: 30 (Eve-inference #3)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CorrectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # recursion bounds
    depth_cap: int = Field(default=3, ge=1)
    cascade_window_seconds: int = Field(default=600, ge=1)
    cascade_threshold: int = Field(default=3, ge=2)

    # budget (ruling #3)
    budget_scale: float = Field(default=0.5, gt=0, le=1.0)
    budget_time_floor_seconds: int = Field(default=60, ge=1)
    budget_token_floor: int = Field(default=2000, ge=1)

    # dedup + poll
    dedup_ttl_seconds: int = Field(default=60, ge=1)
    aggregator_poll_interval_seconds: int = Field(default=30, ge=1)

    # store path
    store_path: str = Field(default="~/.loam/correction/correction.sqlite")

    # objective template (Eve-inference #5)
    objective_template: str = (
        "Correct failure class '{failure_class}' surfaced by "
        "{trigger_source}. Apply the four-part protocol: identify the "
        "class, fix the instance, diagnose the cause, apply a "
        "structural remedy."
    )


def default_config() -> CorrectionConfig:
    return CorrectionConfig()


def load_config(path: str | Path | None = None) -> CorrectionConfig:
    if path is None:
        return default_config()
    p = Path(path).expanduser()
    if not p.exists():
        return default_config()
    data: dict[str, Any] = yaml.safe_load(p.read_text()) or {}
    return CorrectionConfig(**data)

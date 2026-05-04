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

"""CostConfig — ceiling + rolling-window configuration loaded from YAML.

Loaded from `~/.loam/cost/ceilings.yaml` by default; a path is injected
for tests. Refuses negative ceilings and `warning_fraction` outside
`(0.0, 1.0)` at load time (C28 — structural defence-in-depth).

Eve-inferences held (proposal §8):
  - Default rolling windows: daily + hourly, money-only (inference #1).
  - `warning_fraction` default: 0.8 (inference #2).

v0.1.6 AC.PSAFE.3 — production-stake floor:
  - When the workspace's `safety_profile` is `production-stake`, the
    `warning_fraction` is floored at 0.6 — anything > 0.6 is clamped.
    The user's value remains visible (we do not silently rewrite the
    file); the runtime `CostConfig` returned by
    `apply_safety_profile_floor` carries the clamped value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---- session ceiling ------------------------------------------------


class SessionCeiling(BaseModel):
    """Aggregate cap across all scopes in one session."""

    model_config = ConfigDict(extra="forbid")

    time_seconds: int | None = Field(default=None, ge=0)
    tokens: int | None = Field(default=None, ge=0)
    money_cents: int | None = Field(default=None, ge=0)


# ---- rolling-window ceiling ----------------------------------------


class RollingCeiling(BaseModel):
    """Aggregate cap across a time window (sliding / closed-interval)."""

    model_config = ConfigDict(extra="forbid")

    window_kind: str
    duration_seconds: int = Field(gt=0)
    time_seconds: int | None = Field(default=None, ge=0)
    tokens: int | None = Field(default=None, ge=0)
    money_cents: int | None = Field(default=None, ge=0)


# ---- top-level config ----------------------------------------------


class CostConfig(BaseModel):
    """Cost-governance configuration.

    `warning_fraction` must be in `(0.0, 1.0)` exclusive — 0.0 would
    fire on every activation, 1.0 is the ceiling itself (no warning).
    """

    model_config = ConfigDict(extra="forbid")

    session: SessionCeiling = Field(default_factory=SessionCeiling)
    rolling: list[RollingCeiling] = Field(default_factory=list)
    warning_fraction: float = 0.8

    @model_validator(mode="after")
    def _validate_warning_fraction(self) -> "CostConfig":
        wf = self.warning_fraction
        if not (0.0 < wf < 1.0):
            raise ValueError(
                f"warning_fraction must be in (0.0, 1.0) exclusive; got {wf!r}"
            )
        # Reject duplicate window_kind on rolling ceilings.
        seen: set[str] = set()
        for r in self.rolling:
            if r.window_kind in seen:
                raise ValueError(
                    f"duplicate rolling window_kind: {r.window_kind!r}"
                )
            seen.add(r.window_kind)
        return self


# ---- default-config factory (inferences #1, #2) --------------------


def default_config() -> CostConfig:
    """The v1.0 default — no ceilings, daily + hourly money-only windows
    declared so the rollup infrastructure has a shape to close even
    before a user sets caps.

    Ceilings are `None` by default — cost governance is opt-in, not
    opt-out. A workspace writes `~/.loam/cost/ceilings.yaml` to turn
    enforcement on.
    """
    return CostConfig(
        session=SessionCeiling(),
        rolling=[
            RollingCeiling(
                window_kind="daily",
                duration_seconds=24 * 60 * 60,
            ),
            RollingCeiling(
                window_kind="hourly",
                duration_seconds=60 * 60,
            ),
        ],
        warning_fraction=0.8,
    )


# ---- loader --------------------------------------------------------


def load_config(path: str | Path | None = None) -> CostConfig:
    """Load cost config from YAML, or return the v1.0 default.

    `path` defaults to `~/.loam/cost/ceilings.yaml`. If the file is
    absent, the default config is returned — cost governance is
    opt-in; a missing file is not an error.

    Pydantic refuses malformed configs at load time (C28).
    """
    if path is None:
        path = Path.home() / ".loam" / "cost" / "ceilings.yaml"
    else:
        path = Path(path)
    if not path.exists():
        return default_config()
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(
            f"ceilings.yaml must be a mapping at top level; got {type(data).__name__}"
        )
    return CostConfig(**data)


# v0.1.6 AC.PSAFE.3 — production-stake floor for warning_fraction.
# When the workspace's `safety_profile` is `production-stake`, this
# is the maximum value permitted for `warning_fraction`. The pydantic
# model's structural validation accepts any value in (0.0, 1.0)
# exclusive; this floor is applied *on top* by
# `apply_safety_profile_floor` when the profile is production-stake.
PRODUCTION_STAKE_WARNING_FRACTION_FLOOR: float = 0.6


def apply_safety_profile_floor(
    config: CostConfig,
    *,
    safety_profile: str,
) -> CostConfig:
    """Return a `CostConfig` with the production-stake floor applied.

    When ``safety_profile == "production-stake"`` and the user-set
    ``warning_fraction`` exceeds
    ``PRODUCTION_STAKE_WARNING_FRACTION_FLOOR`` (0.6), the returned
    config carries the clamped value. Otherwise, the original config
    is returned unchanged.

    The user-supplied YAML is *not* mutated — only the runtime
    `CostConfig` is adjusted. This matches the v0.1.6 AC.PSAFE.3
    "floor, not absolute" semantic: the user's intent is preserved on
    disk, but the production-stake profile guarantees a tighter
    governance posture at runtime (Decision P RESOLVED YES, SOC-2
    floor non-tunable).

    `dev` and `research` profiles are no-op pass-throughs.
    """
    if safety_profile != "production-stake":
        return config
    if config.warning_fraction <= PRODUCTION_STAKE_WARNING_FRACTION_FLOOR:
        return config
    # model_copy preserves session + rolling references; only
    # warning_fraction is replaced.
    return config.model_copy(
        update={"warning_fraction": PRODUCTION_STAKE_WARNING_FRACTION_FLOOR}
    )

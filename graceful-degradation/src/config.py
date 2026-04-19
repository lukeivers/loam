"""DegradationConfig — pydantic-backed, YAML-loadable configuration.

Luke's baked-in decisions + research-recommended defaults live here.
Workspaces override via `~/.pos/degradation-config.yaml`; any unset
field inherits the framework default.

Shape mirrors the research's `degradation.yaml` example. Malformed YAML
or invalid field values raise a clear error at load time (pydantic's
ValidationError — caller's choice whether to catch).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


# ---- per-mode configs --------------------------------------------------


class BinaryTripConfig(BaseModel):
    """Trip threshold for "failures in window" modes."""

    model_config = ConfigDict(extra="forbid")
    failures: int = Field(ge=1)
    window_seconds: float = Field(gt=0)


class GarbageTripConfig(BaseModel):
    """Trip threshold for the garbage detector — ratio over rolling window."""

    model_config = ConfigDict(extra="forbid")
    failures: int = Field(ge=1)
    window_calls: int = Field(ge=1)


class LatencyTripConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p95_seconds: float = Field(gt=0)
    window_calls: int = Field(ge=1)


class BinaryModeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_threshold: BinaryTripConfig
    half_open_dwell_seconds: float | None = None  # None → honour retry-after header
    probe_success_requirement: int = 1
    default_policy: str  # "pause_all" | "pause_llm_only" | ...


class GarbageModeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_threshold: GarbageTripConfig = Field(
        default_factory=lambda: GarbageTripConfig(failures=3, window_calls=10)
    )
    half_open_dwell_seconds: float = 60.0
    probe_success_requirement: int = 2
    default_policy: str = "pause_llm_only"
    judge_budget_per_hour: int = 5


class LatencyModeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_threshold: LatencyTripConfig
    action: str = "emit_signal_only"


class ModesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    down: BinaryModeConfig = Field(
        default_factory=lambda: BinaryModeConfig(
            trip_threshold=BinaryTripConfig(failures=3, window_seconds=60),
            half_open_dwell_seconds=30,
            probe_success_requirement=1,
            default_policy="pause_all",
        )
    )
    overloaded: BinaryModeConfig = Field(
        default_factory=lambda: BinaryModeConfig(
            trip_threshold=BinaryTripConfig(failures=2, window_seconds=30),
            half_open_dwell_seconds=15,
            probe_success_requirement=1,
            default_policy="pause_all",
        )
    )
    rate_limited: BinaryModeConfig = Field(
        default_factory=lambda: BinaryModeConfig(
            trip_threshold=BinaryTripConfig(failures=1, window_seconds=1),
            half_open_dwell_seconds=None,  # uses retry-after header
            probe_success_requirement=1,
            default_policy="pause_llm_only",
        )
    )
    garbage: GarbageModeConfig = Field(default_factory=GarbageModeConfig)
    auth_broken: BinaryModeConfig = Field(
        default_factory=lambda: BinaryModeConfig(
            trip_threshold=BinaryTripConfig(failures=1, window_seconds=1),
            half_open_dwell_seconds=None,
            probe_success_requirement=1,
            default_policy="request_user_decision",
        )
    )
    latency_sustained: LatencyModeConfig = Field(
        default_factory=lambda: LatencyModeConfig(
            trip_threshold=LatencyTripConfig(p95_seconds=30, window_calls=20),
            action="emit_signal_only",
        )
    )


# ---- notification + resume + narrative ---------------------------------


class NotificationThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    time_seconds: float = 300.0
    paused_scope_count: int = 3
    auth_broken_immediate: bool = True


class NotificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thresholds: NotificationThresholds = Field(default_factory=NotificationThresholds)
    default_tier: int = 2
    auth_broken_tier: int = 1
    dedup_per_episode: bool = True


class ResumeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_resume_modes: tuple[str, ...] = (
        "down",
        "overloaded",
        "rate_limited",
        "garbage",
    )
    user_confirm_after_seconds: float = 1800.0  # 30-minute dwell gate


class NarrativeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = "claude-haiku-4-5"
    timeout_seconds: float = 2.0
    fallback_template: str = (
        "[pOS — claude upstream degraded]\n"
        "Detected signal: {signal} ({mode}).\n"
        "{paused_scope_count} scope(s) affected; policy applied: {policy}.\n"
        "Recommended action: {recommendation}.\n"
        "Resume conditions: {resume_conditions}."
    )
    recovery_template: str = (
        "[pOS] Claude upstream recovered. {resumed_count} scope(s) resumed "
        "after {duration_seconds:.0f}s of degraded state."
    )


class StateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sqlite_path: str = "~/.pos/degradation.sqlite"


# ---- top-level ---------------------------------------------------------


class DegradationConfig(BaseModel):
    """Top-level config. Loaded from YAML; defaults match the research.

    Luke's decisions are encoded as defaults:

    - Six failure modes with research-recommended thresholds
    - Four policies (P1/P2/P3/P4) with per-mode defaults
    - Compound-OR notification threshold
    - Tier 2 default, Tier 1 for auth-broken
    - `claude-haiku-4-5` default narrative model
    - Automatic resume for transient modes; gated for auth-broken and
      >30-min dwells
    - Own SQLite at `~/.pos/degradation.sqlite`
    """

    model_config = ConfigDict(extra="forbid")

    modes: ModesConfig = Field(default_factory=ModesConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    resume: ResumeConfig = Field(default_factory=ResumeConfig)
    narrative: NarrativeConfig = Field(default_factory=NarrativeConfig)
    state: StateConfig = Field(default_factory=StateConfig)

    def sqlite_path(self) -> Path:
        p = Path(self.state.sqlite_path).expanduser()
        return p


# ---- loader ------------------------------------------------------------


def load_config(
    path: str | Path | None = None, *, text: str | None = None
) -> DegradationConfig:
    """Load degradation config from disk (or inline text for tests).

    Precedence:
    - If `text` is supplied, parse that.
    - Else if `path` exists, load it.
    - Else return defaults.

    Unknown top-level keys raise pydantic ValidationError ("extra inputs
    are not permitted") — clear error on malformed YAML.
    """
    if text is not None:
        raw = yaml.safe_load(text) or {}
    elif path is not None:
        p = Path(path).expanduser()
        if not p.exists():
            return DegradationConfig()
        raw = yaml.safe_load(p.read_text()) or {}
    else:
        return DegradationConfig()

    if not isinstance(raw, dict):
        raise ValueError(
            f"degradation config must be a mapping at the top level, got {type(raw).__name__}"
        )
    # Support both "flat" and "nested-under-degradation" shapes, so the
    # research's example YAML (`degradation: modes: ...`) loads too.
    if "degradation" in raw and len(raw) == 1:
        raw = raw["degradation"]
    return DegradationConfig.model_validate(raw)

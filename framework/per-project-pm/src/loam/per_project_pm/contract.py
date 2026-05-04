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

"""Pydantic contract models for the per-project PM.

Per AC.PPM.2 + AC.PPM.3 (parent plan §5) + cycle-2 plan-doc §4
Surface #4. Two models:

  - :class:`PMContract` — the persisted PM contract; loaded from
    ``<workspace>/workspace/.loam/pms/<handle>/contract.yaml``.
  - :class:`DecisionSurfacingPolicy` — policy knobs nested under the
    contract; controls Cycle 4 surfacing flow (Cycle 2 records the
    fields but does not enforce them).

Both models use Pydantic v2 (``model_config = ConfigDict(extra="forbid",
frozen=True)``). ``extra="forbid"`` rejects unknown keys at load
(catches typos in operator-authored ``contract.yaml``); ``frozen=True``
matches the workspace-bootstrap ``ContributionMetadata`` precedent
(state mutation happens via ``state.yaml`` / ``decision-queue.yaml``,
not via mutating the contract).

The ``composes_with_skills`` and ``composes_with_agents`` fields are
**advisory at Cycle 2** per cycle-2 plan-doc §2 F2.B + §4 Surface #4:
the contract carries them, validation accepts them, but the runtime
does NOT enforce or invoke them. Cycle 4+ wires composition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---- DecisionSurfacingPolicy ----------------------------------------


class DecisionSurfacingPolicy(BaseModel):
    """Decision-surfacing policy knobs nested under :class:`PMContract`.

    Cycle 2 ships the fields with validated defaults; Cycle 4 wires
    enforcement of ``onboarding_mode``, ``max_questions_per_turn``,
    and ``require_owner_response`` into the persona-side flow.

    Defaults per AC.PPM.3:

      - ``onboarding_mode = False`` (post-onboarding default).
      - ``max_questions_per_turn = 1`` (one-question-at-a-time default;
        Eric synthesis Decision Q resolution).
      - ``cool_down_seconds = 0`` (no rate limit by default).
      - ``require_owner_response = True`` (production-stake default;
        Cycle 4 wires the blocking).

    Validation:

      - ``max_questions_per_turn`` must be ``>= 1`` (zero or negative
        means "never surface" — express that via ``onboarding_mode``
        or by not enqueuing, not via ``max_questions_per_turn = 0``).
      - ``cool_down_seconds`` must be ``>= 0``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    onboarding_mode: bool = Field(
        default=False,
        description=(
            "When True (Cycle 4 enforcement), hard one-question-per-"
            "turn enforcement on the persona-side flow."
        ),
    )
    max_questions_per_turn: int = Field(
        default=1,
        ge=1,
        description=(
            "Cycle 4 enforcement: max questions surface_next_questions_"
            "batch() returns per turn. Default 1 = one-at-a-time."
        ),
    )
    cool_down_seconds: int = Field(
        default=0,
        ge=0,
        description=(
            "Cycle 4 enforcement: minimum seconds between consecutive "
            "surfacings (0 = no rate limit)."
        ),
    )
    require_owner_response: bool = Field(
        default=True,
        description=(
            "Cycle 4 enforcement: PM blocks subsequent surfacings "
            "until prior question's response is recorded via "
            "record_response()."
        ),
    )


# ---- PMContract -----------------------------------------------------


class PMContract(BaseModel):
    """Per-project PM contract.

    Persisted at
    ``<workspace>/workspace/.loam/pms/<handle>/contract.yaml``.
    Loaded by :meth:`~loam.per_project_pm.runtime.PMRuntime.from_workspace`.

    Fields per parent plan §3 Surface #4 + cycle-2 plan §4 Surface #4:

      - ``handle`` — short filesystem-safe identifier; matches PM
        directory name. Required, non-empty.
      - ``project_name`` — human-readable project name. Required,
        non-empty.
      - ``project_kind`` — one of ``"dev"``, ``"writing"``,
        ``"research"``, ``"ops"``, ``"general"``. Required.
      - ``owner_name`` — owner's preferred name. Required, non-empty.
      - ``workspace_root`` — absolute path the PM is anchored to.
        Required; rejected if not absolute.
      - ``decision_surfacing_policy`` — nested
        :class:`DecisionSurfacingPolicy`. Required (default-constructed
        if omitted in YAML).
      - ``composes_with_skills`` — advisory list of skill handles this
        PM consumes. Cycle 2: not enforced; Cycle 4+: composition wire.
      - ``composes_with_agents`` — advisory list of subagent handles
        this PM dispatches to. Cycle 2: not enforced.

    Per AC.PPM.2: validation rejects malformed contracts with errors
    that name each missing/invalid field.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    handle: str = Field(
        min_length=1,
        description=(
            "Short filesystem-safe identifier (e.g., 'eric-saas-pm'); "
            "matches PM workspace-state directory name."
        ),
    )
    project_name: str = Field(
        min_length=1,
        description="Human-readable project name (e.g., 'eric-saas').",
    )
    project_kind: Literal["dev", "writing", "research", "ops", "general"] = Field(
        description=(
            "Coarse project taxonomy. Drives PM behaviour at v0.2.0+ "
            "when methodology-bridges are wired."
        ),
    )
    owner_name: str = Field(
        min_length=1,
        description="Owner's preferred name.",
    )
    workspace_root: Path = Field(
        description=(
            "Absolute path the PM is anchored to. Rejected if not "
            "absolute. Must match the actual workspace_root the "
            "PMRuntime is loaded against."
        ),
    )
    decision_surfacing_policy: DecisionSurfacingPolicy = Field(
        default_factory=DecisionSurfacingPolicy,
        description="Surfacing policy knobs (Cycle 4 enforcement).",
    )
    composes_with_skills: tuple[str, ...] = Field(
        default=(),
        description=(
            "Advisory list of skill handles this PM consumes "
            "(e.g., ['dispatch-with-gates']). Cycle 2: not enforced; "
            "Cycle 4+: composition wire."
        ),
    )
    composes_with_agents: tuple[str, ...] = Field(
        default=(),
        description=(
            "Advisory list of subagent handles this PM dispatches to "
            "(e.g., ['loam-builder']). Cycle 2: not enforced."
        ),
    )

    # ---- validators -----------------------------------------------

    @field_validator("workspace_root")
    @classmethod
    def _absolute_workspace_root(cls, v: Path) -> Path:
        """``workspace_root`` must be absolute. Per AC.PPM.2.

        Pydantic v2 coerces strings to ``Path``; the validator runs
        after coercion. Reject non-absolute paths with a message that
        names the field (the AC requires "errors that name the field").
        """
        if not v.is_absolute():
            raise ValueError(
                f"workspace_root must be an absolute path; got: {v!s}"
            )
        return v

    @field_validator("composes_with_skills", "composes_with_agents", mode="before")
    @classmethod
    def _coerce_compose_lists_to_tuple(cls, v: object) -> object:
        """Accept YAML list shape; coerce to tuple (frozen).

        Mirrors the ``ContributionMetadata.after``/``before`` precedent
        in ``framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py``.
        """
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        raise ValueError(
            "composes_with_* must be a tuple or list of handle strings"
        )

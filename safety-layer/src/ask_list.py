"""Always-ask list — Pydantic-validated YAML schema + loader.

Implements the clause-(g) structural-impossibility pattern from
self-upgrade: the FrameworkFloorCategory enum + a model_validator that
refuses any YAML load that drops a floor category. A workspace cannot
monkey-patch the enum at runtime and change gate behaviour because the
gate reads the validated model, not the enum directly (A19).

Ruling #4 (freeform duration string Nm|Nh|Nd, 15-minute minimum) is
enforced by `parse_duration_spec`. The 15-minute floor is an Eve-
inference (proposal §8 flag #2); the builder has adopted it as-is.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .action_class import FrameworkFloorCategory


# ---- duration spec ---------------------------------------------------


_MIN_TIMEOUT_MINUTES = 15
_DURATION_RE = re.compile(r"^\s*(\d+)\s*([mhd])\s*$")


def parse_duration_spec(value: str) -> int:
    """Parse a duration string `Nm|Nh|Nd` into minutes.

    Enforces the 15-minute floor (ruling #4). Raises ValueError on any
    shape that does not match or that falls below the floor.
    """
    match = _DURATION_RE.fullmatch(value or "")
    if not match:
        raise ValueError(
            f"duration spec {value!r} must match N[m|h|d] "
            "(examples: `15m`, `4h`, `2d`)"
        )
    n = int(match.group(1))
    unit = match.group(2)
    minutes = {"m": n, "h": n * 60, "d": n * 60 * 24}[unit]
    if minutes < _MIN_TIMEOUT_MINUTES:
        raise ValueError(
            f"duration spec {value!r} resolves to {minutes} minutes — "
            f"minimum is {_MIN_TIMEOUT_MINUTES} minutes (ruling #4)."
        )
    return minutes


# ---- decision state --------------------------------------------------


class AskDecisionState(str, Enum):
    approved = "approved"
    refused = "refused"
    pending = "pending"
    expired = "expired"


# ---- entry + list ----------------------------------------------------


class AskListEntry(BaseModel):
    """One ask-list entry.

    `timeout` is a freeform duration string (`Nm|Nh|Nd`) with a
    15-minute floor enforced by the field validator (ruling #4).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    action_class: str = Field(min_length=1)
    timeout: str = Field(
        default="4h",
        description="Duration spec (Nm|Nh|Nd) — 15-minute minimum. Default 4h.",
    )
    description: str = Field(min_length=1)

    @field_validator("timeout")
    @classmethod
    def _validate_timeout(cls, v: str) -> str:
        parse_duration_spec(v)
        return v

    @property
    def timeout_minutes(self) -> int:
        return parse_duration_spec(self.timeout)


class AlwaysAskList(BaseModel):
    """The composed always-ask list.

    `framework_floor` must include every FrameworkFloorCategory. Missing
    any floor category raises a ValidationError at load time (A6, A19).
    `workspace_additions` is an open extension surface.
    `dangerous_op_subset` lists the floor categories that additionally
    fire the stricter dangerous-op gate — framework-fixed; not workspace-
    extensible.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1]
    framework_floor: tuple[AskListEntry, ...]
    workspace_additions: tuple[AskListEntry, ...] = ()
    dangerous_op_subset: tuple[FrameworkFloorCategory, ...]

    @model_validator(mode="after")
    def _floor_cannot_shrink(self) -> "AlwaysAskList":
        floor_classes = {e.action_class for e in self.framework_floor}
        required = {c.value for c in FrameworkFloorCategory}
        missing = required - floor_classes
        if missing:
            raise ValueError(
                f"AlwaysAskList framework_floor missing required categories: "
                f"{sorted(missing)}. The floor cannot be reduced below the "
                "framework-fixed set (ships with all seven; workspaces may "
                "ADD via workspace_additions, never remove)."
            )
        # Also check that dangerous_op_subset entries reference floor categories.
        subset_values = {c.value for c in self.dangerous_op_subset}
        unknown = subset_values - floor_classes
        if unknown:
            raise ValueError(
                f"AlwaysAskList dangerous_op_subset references non-floor "
                f"categories: {sorted(unknown)}."
            )
        return self

    def all_action_classes(self) -> frozenset[str]:
        """Union of floor and workspace additions — the effective ask set."""
        return frozenset(
            [e.action_class for e in self.framework_floor]
            + [e.action_class for e in self.workspace_additions]
        )

    def dangerous_op_values(self) -> frozenset[str]:
        return frozenset(c.value for c in self.dangerous_op_subset)

    def entry_for(self, action_class: str) -> AskListEntry | None:
        for e in self.framework_floor:
            if e.action_class == action_class:
                return e
        for e in self.workspace_additions:
            if e.action_class == action_class:
                return e
        return None


# ---- defaults + loader -----------------------------------------------


DEFAULT_FRAMEWORK_FLOOR: tuple[AskListEntry, ...] = (
    AskListEntry(
        action_class=FrameworkFloorCategory.commit_external_funds.value,
        timeout="4h",
        description="Committing the user's money or spending above budget.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.send_communication_as_user_to_third_party.value,
        timeout="4h",
        description="Messages that could be read as the user's voice.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.strategy_pivot_or_mission_change.value,
        timeout="24h",
        description="Changing the workspace's stated direction or abandoning a project.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.personal_life_judgment_call.value,
        timeout="24h",
        description="Decisions affecting relationships, health, or personal standing.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.destroy_user_data_beyond_workspace.value,
        timeout="4h",
        description="Deleting files outside the workspace or dropping databases.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.publish_to_public_surface_user_does_not_control.value,
        timeout="4h",
        description="Posting to social, public git, app stores, or public blog.",
    ),
    AskListEntry(
        action_class=FrameworkFloorCategory.modify_production_systems_serving_real_users.value,
        timeout="4h",
        description="Deployments, DNS changes, infra affecting real users.",
    ),
)


DEFAULT_DANGEROUS_OP_SUBSET: tuple[FrameworkFloorCategory, ...] = (
    FrameworkFloorCategory.commit_external_funds,
    FrameworkFloorCategory.send_communication_as_user_to_third_party,
    FrameworkFloorCategory.publish_to_public_surface_user_does_not_control,
    FrameworkFloorCategory.destroy_user_data_beyond_workspace,
    FrameworkFloorCategory.modify_production_systems_serving_real_users,
)


def default_ask_list() -> AlwaysAskList:
    """Returns the framework-default ask list (all seven floor entries,
    no workspace additions, default dangerous-op subset)."""
    return AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )


def load_ask_list(path: Path) -> AlwaysAskList:
    """Load the ask list from `<workspace>/.pos/safety/always_ask.yaml`.

    Returns the framework default if the file does not exist (A6 is
    evaluated against a dropped entry; absence of the file itself means
    "use the framework default," not "reject activation").

    Fail-closed only for malformed or floor-shrinking content.
    """
    if not path.exists():
        return default_ask_list()
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    # Coerce legacy/loose YAML shapes to the schema shape. The validator
    # does the rejection work; we only normalise tuples-from-lists.
    return AlwaysAskList.model_validate(data)

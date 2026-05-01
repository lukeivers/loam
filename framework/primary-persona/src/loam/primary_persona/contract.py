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

"""Persona contract — Pydantic-validated persona declaration (D1).

Each workspace persona is a directory:

    workspace/personas/<handle>/
        contract.yaml    (mandatory — Pydantic validated, this module)
        prompt.md        (mandatory — free prose the persona owns)
        voice.md         (optional — voice markers the workspace declares)
        home/            (optional — supplementary reference materials)

The contract is the machine-readable half; `prompt.md` is the prose the
workspace owns and the framework does not parse. This separation is the
"pOS validates the YAML; the workspace owns the prose" split from the
approved proposal.

Mandatory contract fields:
    handle, given_name, contract_version, responsibilities,
    authority_boundary, escalation_taxonomy, severity_vocabulary.

Optional contract fields:
    delegates_to, home_persona_for, voice_markers,
    pending_introduction, is_addressable.

The last two fields implement the introduction gate (D7): a newly-
authored persona is persisted with `pending_introduction: true` and
`is_addressable: false`. The flag flips on the user's next non-retire
message — see `introduction.py`.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---- enums and literal types -----------------------------------------


_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$")
_HANDLE_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$")


class PersonaTier(str, Enum):
    """Security tiers per security.md rule 6.

    A persona's `authority_boundary` declares one action per tier,
    scoping what the persona may do autonomously vs. what requires
    the user's explicit approval.
    """

    tier_a = "tier_a"   # External comms to real people (non-close-associates)
    tier_b = "tier_b"   # Publishing to public surfaces not fully controlled
    tier_c = "tier_c"   # Writes to user-owned surfaces / pre-authorised channels
    tier_d = "tier_d"   # Communications to close associates (attribution mandatory)


class TierAction(str, Enum):
    """The three possible actions a persona may declare per tier.

    - `execute`: persona acts autonomously at this tier.
    - `defer`: persona must escalate to user-approval before acting.
    - `not_applicable`: persona does not work in this tier (e.g. a
      personal-finance persona has no tier_a autonomy).
    """

    execute = "execute"
    defer = "defer"
    not_applicable = "not_applicable"


class PersonaState(str, Enum):
    """Addressability state tracked through the contract file.

    `pending_introduction` is True between authoring and the user's
    first non-retire message. `is_addressable` flips True when the
    user acknowledges (D7); until then, no message identifying this
    persona as sender can be delivered.
    """

    active = "active"
    pending_introduction = "pending_introduction"
    retired = "retired"


# ---- nested contract shapes ------------------------------------------


class Responsibilities(BaseModel):
    """The three functional responsibilities every primary persona
    declares (v1.0 core-primitives acceptance).

    Workspaces may extend with domain-specific responsibilities, but
    the three canonical ones are required for any primary persona
    (single point of contact, context holder, escalation judge).
    Specialist personas may declare only a subset if they are not
    primary; see `PersonaContract.is_primary` for the distinction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    single_point_of_contact: str = Field(
        min_length=1,
        description="The persona serves as sole contact for its domain.",
    )
    context_holder: str = Field(
        min_length=1,
        description="The persona maintains ongoing context across sessions.",
    )
    escalation_judge: str = Field(
        min_length=1,
        description="The persona decides when to surface matters to the user.",
    )


class AuthorityBoundary(BaseModel):
    """Per-tier action declaration (security.md rule 6).

    Every persona declares one TierAction per tier. No tier may be
    omitted — a missing tier is a validation failure (the persona
    either claims authority in it or says it does not apply).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tier_a: TierAction
    tier_b: TierAction
    tier_c: TierAction
    tier_d: TierAction

    def action_for(self, tier: PersonaTier) -> TierAction:
        return {
            PersonaTier.tier_a: self.tier_a,
            PersonaTier.tier_b: self.tier_b,
            PersonaTier.tier_c: self.tier_c,
            PersonaTier.tier_d: self.tier_d,
        }[tier]


class EscalationTaxonomy(BaseModel):
    """The persona's named escalation categories.

    Each category names a kind of situation the persona treats as
    escalation-worthy (e.g. "irreversible-action", "external-funds",
    "strategy-pivot"). The monitor and safety layer consume these
    category names when an escalation event fires on a scope this
    persona owns.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    categories: tuple[str, ...] = Field(
        min_length=1,
        description="Named escalation categories, at least one.",
    )

    @field_validator("categories")
    @classmethod
    def _each_nonempty(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(not c.strip() for c in v):
            raise ValueError("escalation_taxonomy.categories may not contain empty strings")
        return v


class SeverityVocabulary(BaseModel):
    """Domain-calibrated severity labels the persona uses.

    A generic "low / medium / high" triad is not acceptable (it
    violates the v1.0 rule-quality standard). Personas declare their
    own labels — a financial-advisor might use
    `advisory / material / urgent / crisis`; a developer persona
    might use `nit / fix / block / rollback`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    labels: tuple[str, ...] = Field(
        min_length=2,
        description="Severity labels, at least two, declared most-severe first.",
    )

    @field_validator("labels")
    @classmethod
    def _each_nonempty(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(not label.strip() for label in v):
            raise ValueError("severity_vocabulary.labels may not contain empty strings")
        return v


# ---- PersonaContract — the top-level validated type ------------------


class PersonaContract(BaseModel):
    """Pydantic-validated persona contract (D1).

    Load via `load_contract(path)`; construction from a dict will also
    validate. Missing mandatory fields raise `ValidationError` with a
    message that names the missing field (this is the acceptance
    criterion "rejects missing mandatory fields with errors that name
    each missing field").

    The file lives at `<persona-dir>/contract.yaml`. The companion
    `prompt.md` is not parsed by the framework; the loader checks its
    presence and nothing else.
    """

    model_config = ConfigDict(extra="forbid")  # note: NOT frozen — state flags mutate

    # ---- mandatory fields (order matches authoring template) ----

    handle: str = Field(
        min_length=1,
        description="Short filesystem-safe identifier; matches directory name.",
    )
    given_name: str = Field(
        min_length=1,
        description="Human-readable name the user addresses the persona by.",
    )
    contract_version: str = Field(
        default="1.0.0",
        description="Semver for the contract schema this persona conforms to.",
    )
    responsibilities: Responsibilities
    authority_boundary: AuthorityBoundary
    escalation_taxonomy: EscalationTaxonomy
    severity_vocabulary: SeverityVocabulary

    # ---- optional fields ----

    delegates_to: tuple[str, ...] = Field(
        default=(),
        description="Handles of personas this one may dispatch work to.",
    )
    home_persona_for: tuple[str, ...] = Field(
        default=(),
        description="Domains this persona is the default landing place for.",
    )
    voice_markers: tuple[str, ...] = Field(
        default=(),
        description="Short phrases or markers characteristic of this persona's voice.",
    )
    is_primary: bool = Field(
        default=False,
        description="True if this persona is the workspace's primary (single per workspace).",
    )

    # ---- mutable state flags (D7 introduction gate + D8 retirement) ----

    pending_introduction: bool = Field(
        default=False,
        description="True if this persona was autonomously authored and not yet introduced.",
    )
    is_addressable: bool = Field(
        default=True,
        description="False while pending_introduction; flips True on user acknowledgement.",
    )

    # ---- starter-flag (amendment #35 — first-run elicitation) ----

    is_starter: bool = Field(
        default=False,
        strict=True,
        description=(
            "True while the contract is a freshly-scaffolded starter "
            "awaiting first-run conversational elicitation. The "
            "workspace-bootstrap scaffold (amendment #36) sets this "
            "to true on materialisation; the onboarding flow "
            "(amendment #35) flips it to false on completed "
            "transcript write-back. Default false: any contract "
            "constructed without an explicit value is non-starter. "
            "Strict-typed: only Python ``bool`` values are accepted; "
            "a non-Boolean (e.g., a YAML string) rejects at "
            "validation time."
        ),
    )

    # ---- dev-intent (sub-plan A — two-modes-and-multi-workspace) ----

    dev_intent: Literal["unanswered", "yes", "no"] = Field(
        default="unanswered",
        description=(
            "Workspace-local answer to the dev-intent onboarding "
            "question (sub-plan A of two-modes-and-multi-workspace). "
            "``\"yes\"`` — operator intends to develop pos-v2 itself; "
            "``\"no\"`` — operator intends to use pos-v2 as a harness "
            "only; ``\"unanswered\"`` — the question has not been put "
            "to the operator yet (default for any contract scaffolded "
            "without going through onboarding write-back). The "
            "Literal constraint structurally rejects any other "
            "string at validation time. Sub-plan E's "
            "``classify_workspace`` consumes ``read_dev_intent`` "
            "with the documented mapping ``unanswered`` → non-dev."
        ),
    )

    # ---- validators ----

    @field_validator("handle")
    @classmethod
    def _handle_shape(cls, v: str) -> str:
        if not _HANDLE_RE.match(v):
            raise ValueError(
                f"handle {v!r} must be lowercase ASCII, start with a letter, "
                "end with alphanumeric, contain only [a-z0-9-], 2-64 chars"
            )
        return v

    @field_validator("contract_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not _SEMVER_RE.match(v):
            raise ValueError(
                f"contract_version {v!r} must be semver (MAJOR.MINOR.PATCH "
                "with optional pre-release/build suffix)"
            )
        return v

    def to_yaml(self) -> str:
        """Serialise to YAML. Used when authoring writes a new persona
        or when the introduction gate flips `is_addressable`."""
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            sort_keys=False,
            default_flow_style=False,
        )


# ---- loader helper ---------------------------------------------------


class ContractFileError(ValueError):
    """Raised when `contract.yaml` exists but fails to parse."""


def load_contract(yaml_path: str | Path) -> PersonaContract:
    """Read and validate a persona contract from disk.

    Any of:
    - file missing → raises FileNotFoundError
    - invalid YAML → raises `ContractFileError`
    - missing mandatory field → Pydantic `ValidationError` naming it
    - extra unknown field → Pydantic `ValidationError` (extra=forbid)
    """
    p = Path(yaml_path)
    if not p.exists():
        raise FileNotFoundError(f"contract file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise ContractFileError(f"invalid YAML in {p}: {e}") from e
    if not isinstance(raw, dict):
        raise ContractFileError(
            f"contract {p} must be a YAML mapping, got {type(raw).__name__}"
        )
    return PersonaContract.model_validate(raw)

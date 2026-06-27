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

"""Destructive-action classifier + resolved-target gate decision (AC.DSF.2/.3).

Two jobs, both keyed off STRUCTURED facts, never an environment's name:

1. **Destructive sub-action detection.** Parse a Bash command for a
   destructive verb against durable state — drop/delete a database, delete or
   empty an object-store bucket, truncate a table, ``terraform destroy``,
   ``rm -rf`` a real path. The detected sub-action is named in plain words
   for the deny message (AC.DSF.7).

2. **Resolved-target gate strength.** Resolve the command's target against
   the config's DECLARED identities (host/bucket/account substrings) and
   compute ``gate = max(declared protection of the active env,
   production-ness of the resolved target)`` (AC.DSF.2). A command that
   resolves to a declared-prod identity is gated at prod level even when the
   active environment is declared non-prod.

The classifier composes on ``safety-layer``'s framework-floor vocabulary:
``destroy_user_data_beyond_workspace`` and
``modify_production_systems_serving_real_users`` are the two
``FrameworkFloorCategory`` entries this floor's destructive set maps to (it
does not re-derive its own action-class enum).

Deterministic, stdlib-only (``re``). No LLM, no network — the floor must not
be probabilistic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import DeployConfig, Environment, GateLevel, max_gate


# Destructive sub-action patterns. Each entry: (compiled regex, plain-words
# sub-action label for the deny message). The labels are deliberately
# non-technical (AC.DSF.7 — "delete the database", not "DROP DATABASE").
_DESTRUCTIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bdrop\s+database\b", re.IGNORECASE), "delete an entire database"),
    (re.compile(r"\bdrop\s+table\b", re.IGNORECASE), "delete a database table"),
    (re.compile(r"\btruncate\s+table\b", re.IGNORECASE), "erase every row in a table"),
    (re.compile(r"\btruncate\b\s+\w", re.IGNORECASE), "erase every row in a table"),
    (re.compile(r"\bdelete\s+from\b", re.IGNORECASE), "delete records from a database"),
    (re.compile(r"\bdropdb\b", re.IGNORECASE), "delete an entire database"),
    (re.compile(r"\bterraform\s+destroy\b", re.IGNORECASE), "tear down live infrastructure"),
    (re.compile(r"\baws\s+s3\s+rb\b", re.IGNORECASE), "delete a cloud storage bucket"),
    (re.compile(r"\baws\s+s3\s+rm\b[^\n;|&]*--recursive", re.IGNORECASE), "delete the contents of cloud storage"),
    (re.compile(r"\bgsutil\s+rm\b[^\n;|&]*-r", re.IGNORECASE), "delete the contents of cloud storage"),
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "force-delete files and folders"),
    (re.compile(r"\bkubectl\s+delete\b", re.IGNORECASE), "delete a live cluster resource"),
    (re.compile(r"\bflushall\b", re.IGNORECASE), "wipe a live cache/datastore"),
    (re.compile(r"\bflushdb\b", re.IGNORECASE), "wipe a live cache/datastore"),
)

# safety-layer FrameworkFloorCategory entries this floor maps onto (Lens 1 —
# compose, don't re-derive). Carried as plain strings to avoid a hard import
# coupling in the hot path; the values mirror
# safety_layer.action_class.FrameworkFloorCategory verbatim.
FLOOR_CATEGORY_DESTROY_DATA = "destroy_user_data_beyond_workspace"
FLOOR_CATEGORY_MODIFY_PROD = "modify_production_systems_serving_real_users"


@dataclass(frozen=True)
class DestructiveMatch:
    """A destructive sub-action detected in a command."""

    is_destructive: bool
    sub_action: str  # plain-words label, "" when not destructive
    floor_category: str  # the safety-layer FrameworkFloorCategory it maps to


def classify_destructive(command: str) -> DestructiveMatch:
    """Detect a destructive sub-action against durable state in *command*.

    Returns the FIRST matching pattern's plain-words label. Non-destructive
    commands return ``is_destructive=False``."""
    if not isinstance(command, str):
        raise TypeError("command must be a string")
    for pattern, label in _DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            # terraform destroy / kubectl delete / s3 rb touch live systems;
            # the rest destroy durable user data. Both are floor categories;
            # the distinction only flavours the message, never the gate.
            if pattern.pattern.startswith(r"\bterraform") or "kubectl" in pattern.pattern or "s3\\s+rb" in pattern.pattern:
                category = FLOOR_CATEGORY_MODIFY_PROD
            else:
                category = FLOOR_CATEGORY_DESTROY_DATA
            return DestructiveMatch(
                is_destructive=True, sub_action=label, floor_category=category
            )
    return DestructiveMatch(is_destructive=False, sub_action="", floor_category="")


@dataclass(frozen=True)
class TargetResolution:
    """The result of resolving a command's target against declared identities."""

    matched_environment: Environment | None
    matched_token: str  # the declared identity token the command contained

    @property
    def resolves_to_declared_target(self) -> bool:
        return self.matched_environment is not None


def resolve_target(command: str, config: DeployConfig) -> TargetResolution:
    """Resolve *command*'s target against the config's DECLARED identities.

    A command CONTAINING a declared identity token (a prod host, bucket, or
    account string) resolves to that environment — the structured-field match
    that makes the gate rename-safe (AC.DSF.3) and resolved-target aware
    (AC.DSF.2). The first environment whose token appears wins; production
    environments are checked first so a token shared across envs resolves to
    the production one."""
    if not isinstance(command, str):
        raise TypeError("command must be a string")
    ordered = (
        *config.production_environments(),
        *(e for e in config.environments if not e.is_production_class),
    )
    for env in ordered:
        for token in env.identities.all_tokens():
            if token and token in command:
                return TargetResolution(matched_environment=env, matched_token=token)
    return TargetResolution(matched_environment=None, matched_token="")


@dataclass(frozen=True)
class GateStrength:
    """The computed gate strength for a command + its derivation (AC.DSF.2)."""

    declared: GateLevel  # the active env's declared protection
    resolved: GateLevel  # production-ness of the resolved target
    effective: GateLevel  # max(declared, resolved) — what actually gates
    resolved_environment: Environment | None
    matched_token: str

    @property
    def is_production_gated(self) -> bool:
        return self.effective == GateLevel.high


def compute_gate_strength(command: str, config: DeployConfig) -> GateStrength:
    """``gate = max(declared, resolved)`` (AC.DSF.2).

    ``declared`` is the active environment's declared protection floor.
    ``resolved`` is the production-ness of the target the command actually
    points at: ``high`` when it resolves to a production-class declared
    identity, else ``none`` (the resolved target adds no height). The
    effective gate is the ``max`` of the two — so a destructive command that
    resolves to a declared-prod host is prod-gated even when the active
    environment is non-prod."""
    active = config.active_environment()
    declared = active.declared_gate if active is not None else GateLevel.none

    resolution = resolve_target(command, config)
    if resolution.resolves_to_declared_target and (
        resolution.matched_environment is not None
        and resolution.matched_environment.is_production_class
    ):
        resolved = GateLevel.high
    else:
        resolved = GateLevel.none

    effective = max_gate(declared, resolved)
    return GateStrength(
        declared=declared,
        resolved=resolved,
        effective=effective,
        resolved_environment=resolution.matched_environment,
        matched_token=resolution.matched_token,
    )

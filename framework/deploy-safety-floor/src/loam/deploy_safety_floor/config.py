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

"""Per-environment config abstraction (AC.DSF.1).

An inert, owner-editable ``deploy.yaml`` / ``.loam/environments.yaml`` whose
only job is to be READ by the floor gate. Policy lives in the YAML;
enforcement lives in the hook (policy/enforcement split). The file itself
triggers no action — only a gate reading it does.

Schema (per environment):

    environments:
      - name: prod                 # a human label ONLY — never gates on it
        id: 01J9Z...               # immutable identity (ULID-shaped); rename-safe
        is_production: true        # the gate-height source of truth
        tier: real-infra           # local | staging | real-infra
        reversible: false
        gate: high                 # none | low | medium | high (declared floor)
        security_profile: prod
        identities:                # declared resolved-target identities
          hosts: [db.prod.example.com]
          buckets: ["s3://acme-prod-data"]
          accounts: ["acct-1234567890"]
    active: prod                   # optional: which env is "current"

A missing ``is_production`` or an invalid ``tier`` is rejected at load
(fail-CLOSED load — an unparseable policy file must not silently degrade the
floor to "no environments declared"). Gate height NEVER derives from
``name`` — only from ``is_production`` + ``tier`` + the declared ``gate``
(AC.DSF.3 rename-safety).

Stdlib + PyYAML only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """A deploy-environment config file violates the schema (fail-closed load)."""


class Tier(str, Enum):
    """Deployment tier. ``real-infra`` is the live-systems tier the floor
    treats as production-class regardless of the ``is_production`` flag."""

    local = "local"
    staging = "staging"
    real_infra = "real-infra"


class GateLevel(str, Enum):
    """Declared protection floor for an environment. Ordered: a higher level
    strictly dominates a lower one under ``max`` (AC.DSF.2)."""

    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


_GATE_ORDER: dict[str, int] = {
    GateLevel.none.value: 0,
    GateLevel.low.value: 1,
    GateLevel.medium.value: 2,
    GateLevel.high.value: 3,
}


def gate_rank(level: GateLevel) -> int:
    """Total order over gate levels so ``max(declared, resolved)`` is well
    defined (AC.DSF.2). ``none < low < medium < high``."""
    return _GATE_ORDER[level.value]


def max_gate(a: GateLevel, b: GateLevel) -> GateLevel:
    """The stronger of two gate levels — the keystone of AC.DSF.2's
    ``max(declared protection, resolved-target production-ness)``."""
    return a if gate_rank(a) >= gate_rank(b) else b


@dataclass(frozen=True)
class Identities:
    """The declared resolved-target identities for an environment. The
    classifier matches a command's resolved target against these — never
    against the environment's name (AC.DSF.3 / G-preserve)."""

    hosts: tuple[str, ...] = ()
    buckets: tuple[str, ...] = ()
    accounts: tuple[str, ...] = ()

    def all_tokens(self) -> tuple[str, ...]:
        return (*self.hosts, *self.buckets, *self.accounts)


@dataclass(frozen=True)
class Environment:
    """One declared environment. ``name`` is a human label with no gate
    authority; ``id`` is the immutable identity that survives a rename."""

    name: str
    id: str
    is_production: bool
    tier: Tier
    reversible: bool
    gate: GateLevel
    security_profile: str
    identities: Identities = field(default_factory=Identities)

    @property
    def is_production_class(self) -> bool:
        """Production-ness derived from STRUCTURED fields, never the name —
        ``is_production: true`` OR ``tier: real-infra`` (AC.DSF.3). Renaming
        an env away from "production" cannot lower this."""
        return self.is_production or self.tier == Tier.real_infra

    @property
    def declared_gate(self) -> GateLevel:
        """The environment's declared protection floor. A production-class
        env is pinned to at least ``high`` so a config that under-declares a
        prod env's gate cannot drop the floor (AC.DSF.2/.3)."""
        if self.is_production_class:
            return max_gate(self.gate, GateLevel.high)
        return self.gate


@dataclass(frozen=True)
class DeployConfig:
    """The parsed, schema-validated set of declared environments."""

    environments: tuple[Environment, ...]
    active_name: str | None

    def by_name(self, name: str) -> Environment | None:
        for env in self.environments:
            if env.name == name:
                return env
        return None

    def active_environment(self) -> Environment | None:
        """The "current" environment. ``active:`` names it; absent, the
        lowest-gate environment is assumed (the safe default — declared
        protection starts low and the resolved-target check raises it)."""
        if self.active_name is not None:
            return self.by_name(self.active_name)
        if not self.environments:
            return None
        return min(self.environments, key=lambda e: gate_rank(e.declared_gate))

    def production_environments(self) -> tuple[Environment, ...]:
        return tuple(e for e in self.environments if e.is_production_class)


def _require_bool(raw: dict[str, Any], key: str, where: str) -> bool:
    if key not in raw:
        raise ConfigError(f"{where}: missing required field '{key}'")
    val = raw[key]
    if not isinstance(val, bool):
        raise ConfigError(
            f"{where}: '{key}' must be a boolean (true/false), got {val!r}"
        )
    return val


def _parse_identities(raw: Any, where: str) -> Identities:
    if raw is None:
        return Identities()
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: 'identities' must be a mapping if present")
    out: dict[str, tuple[str, ...]] = {}
    for key in ("hosts", "buckets", "accounts"):
        seq = raw.get(key, [])
        if seq is None:
            seq = []
        if not isinstance(seq, list) or any(not isinstance(x, str) for x in seq):
            raise ConfigError(
                f"{where}: identities.{key} must be a list of strings"
            )
        out[key] = tuple(seq)
    return Identities(hosts=out["hosts"], buckets=out["buckets"], accounts=out["accounts"])


def _parse_environment(raw: Any, index: int) -> Environment:
    where = f"environments[{index}]"
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: must be a mapping")
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ConfigError(f"{where}: 'name' must be a non-empty string")
    env_id = raw.get("id")
    if not isinstance(env_id, str) or not env_id:
        raise ConfigError(
            f"{where} ({name}): 'id' must be a non-empty immutable identity string"
        )
    is_production = _require_bool(raw, "is_production", f"{where} ({name})")

    tier_raw = raw.get("tier")
    try:
        tier = Tier(tier_raw)
    except ValueError:
        raise ConfigError(
            f"{where} ({name}): 'tier' must be one of "
            f"{[t.value for t in Tier]}, got {tier_raw!r}"
        ) from None

    reversible = _require_bool(raw, "reversible", f"{where} ({name})")

    gate_raw = raw.get("gate")
    try:
        gate = GateLevel(gate_raw)
    except ValueError:
        raise ConfigError(
            f"{where} ({name}): 'gate' must be one of "
            f"{[g.value for g in GateLevel]}, got {gate_raw!r}"
        ) from None

    security_profile = raw.get("security_profile")
    if not isinstance(security_profile, str) or not security_profile:
        raise ConfigError(
            f"{where} ({name}): 'security_profile' must be a non-empty string"
        )

    identities = _parse_identities(raw.get("identities"), f"{where} ({name})")

    return Environment(
        name=name,
        id=env_id,
        is_production=is_production,
        tier=tier,
        reversible=reversible,
        gate=gate,
        security_profile=security_profile,
        identities=identities,
    )


def parse_deploy_config(text: str) -> DeployConfig:
    """Parse + schema-validate a deploy-environment config from YAML text.

    Fail-CLOSED load: a YAML parse error, a non-mapping top level, a missing
    ``is_production``, or an invalid ``tier`` raises ``ConfigError`` rather
    than returning a degraded (empty) config (AC.DSF.1)."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"deploy config does not parse: {exc}") from exc
    if data is None:
        return DeployConfig(environments=(), active_name=None)
    if not isinstance(data, dict):
        raise ConfigError("deploy config top-level must be a mapping")
    envs_raw = data.get("environments")
    if envs_raw is None:
        return DeployConfig(environments=(), active_name=None)
    if not isinstance(envs_raw, list):
        raise ConfigError("'environments' must be a list")
    environments = tuple(
        _parse_environment(e, i) for i, e in enumerate(envs_raw)
    )
    names = [e.name for e in environments]
    if len(names) != len(set(names)):
        raise ConfigError("environment names must be unique")
    active_raw = data.get("active")
    if active_raw is not None:
        if not isinstance(active_raw, str) or not active_raw:
            raise ConfigError("'active' must be a non-empty string if present")
        if active_raw not in names:
            raise ConfigError(
                f"'active' names {active_raw!r} which is not a declared environment"
            )
    return DeployConfig(environments=environments, active_name=active_raw)


# Default discovery paths, relative to a workspace root. Either is honoured;
# ``.loam/environments.yaml`` takes precedence over a top-level ``deploy.yaml``.
CONFIG_RELATIVE_PATHS: tuple[tuple[str, ...], ...] = (
    (".loam", "environments.yaml"),
    ("deploy.yaml",),
)


def find_config_path(workspace_root: Path) -> Path | None:
    """Return the first existing deploy-config path under *workspace_root*,
    or ``None`` when no config is present (the floor is inert without one)."""
    for parts in CONFIG_RELATIVE_PATHS:
        candidate = workspace_root.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return None


def load_deploy_config(workspace_root: Path) -> DeployConfig | None:
    """Load the deploy config under *workspace_root*, or ``None`` when absent.

    A present-but-unparseable config raises ``ConfigError`` (fail-closed load
    — the floor must not silently treat a broken policy file as "no
    environments")."""
    path = find_config_path(workspace_root)
    if path is None:
        return None
    return parse_deploy_config(path.read_text(encoding="utf-8"))

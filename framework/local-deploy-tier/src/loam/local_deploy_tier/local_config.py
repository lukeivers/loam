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

"""The additive TIER-EXTENSION config fields the LOCAL tier reads.

Per the P0 shared contract §5.1, the LOCAL tier introduces two optional fields
on the *same* ``deploy.yaml`` / ``.loam/environments.yaml`` the sealed floor
already reads:

    role             # development | preview | production | custom
    backing_services # declared kind+version, for parity checking

These are a STRICT ADDITIVE SUPERSET: the sealed floor ignores them entirely
(it parses only its CORE fields — ``config.py``), and changing none of them is
possible because this module never writes the file. The contract's
reconciliation (§5.2, D-SC.3) is honoured: ``tier`` stays the floor's
risk-class, the provider lives elsewhere; this module reads only the two LOCAL
fields and the floor's ``tier`` for the risk-class, never extending the sealed
``Tier`` enum.

This module discovers the config at the SAME paths the floor uses and parses
only the additive view, so the floor's own loader and this one read one file
without either depending on the other's schema.

Stdlib + PyYAML only; no import of the floor package (the additive view is
intentionally decoupled so this tier never widens the floor's fence).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


# Same discovery order as the sealed floor (config.py:CONFIG_RELATIVE_PATHS),
# named here so the additive view reads the identical file without importing
# the sealed package.
CONFIG_RELATIVE_PATHS: tuple[tuple[str, ...], ...] = (
    (".loam", "environments.yaml"),
    ("deploy.yaml",),
)

# The LOCAL risk-class value of the sealed floor's ``tier`` field. Read-only —
# this tier never adds a value to the sealed enum (D-SC.3).
LOCAL_TIER = "local"


class LocalConfigError(ValueError):
    """A backing-service / role declaration is malformed."""


@dataclass(frozen=True)
class BackingService:
    """A declared backing service for an environment — the parity unit
    (AC.LOCAL.3). ``kind`` is the engine (``postgres`` / ``redis`` / ...);
    ``version`` is the pinned tag (``16.3``); ``name`` is the human label of
    the logical service (``db`` / ``cache``) used to align services across
    environments for the parity diff."""

    name: str
    kind: str
    version: str = ""


@dataclass(frozen=True)
class EnvProfile:
    """The additive LOCAL view of one declared environment. Carries only the
    TIER-EXTENSION fields + the floor's risk-class ``tier`` (read, not owned);
    the floor's CORE fields are parsed by the floor, not duplicated here."""

    name: str
    tier: str
    role: str | None = None
    backing_services: tuple[BackingService, ...] = ()

    @property
    def is_local(self) -> bool:
        return self.tier == LOCAL_TIER


@dataclass(frozen=True)
class LocalConfigView:
    """The additive view over the declared environment set."""

    environments: tuple[EnvProfile, ...] = field(default_factory=tuple)

    def by_name(self, name: str) -> EnvProfile | None:
        for env in self.environments:
            if env.name == name:
                return env
        return None

    def local_environment(self) -> EnvProfile | None:
        """The first declared environment whose floor risk-class is ``local``."""
        for env in self.environments:
            if env.is_local:
                return env
        return None


def _parse_backing_services(raw: object, where: str) -> tuple[BackingService, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise LocalConfigError(f"{where}: 'backing_services' must be a list if present")
    out: list[BackingService] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise LocalConfigError(f"{where}: backing_services[{i}] must be a mapping")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise LocalConfigError(
                f"{where}: backing_services[{i}] needs a non-empty 'name'"
            )
        kind = item.get("kind")
        if not isinstance(kind, str) or not kind:
            raise LocalConfigError(
                f"{where}: backing_services[{i}] ({name}) needs a non-empty 'kind'"
            )
        version_raw = item.get("version", "")
        version = "" if version_raw is None else str(version_raw)
        out.append(BackingService(name=name, kind=kind, version=version))
    return tuple(out)


def parse_local_config(text: str) -> LocalConfigView:
    """Parse the additive LOCAL view from deploy-config YAML text.

    Reads only ``role`` + ``backing_services`` (plus ``name`` / ``tier`` for
    alignment). Unknown fields — every CORE field the floor owns — are ignored,
    which is exactly the additive-superset contract (§5.1). A YAML parse error
    or a malformed backing-service block raises ``LocalConfigError``."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise LocalConfigError(f"deploy config does not parse: {exc}") from exc
    if data is None:
        return LocalConfigView(environments=())
    if not isinstance(data, dict):
        raise LocalConfigError("deploy config top-level must be a mapping")
    envs_raw = data.get("environments")
    if envs_raw is None:
        return LocalConfigView(environments=())
    if not isinstance(envs_raw, list):
        raise LocalConfigError("'environments' must be a list")

    profiles: list[EnvProfile] = []
    for i, raw in enumerate(envs_raw):
        where = f"environments[{i}]"
        if not isinstance(raw, dict):
            raise LocalConfigError(f"{where}: must be a mapping")
        name = raw.get("name")
        if not isinstance(name, str) or not name:
            raise LocalConfigError(f"{where}: 'name' must be a non-empty string")
        tier = raw.get("tier")
        if not isinstance(tier, str) or not tier:
            raise LocalConfigError(f"{where} ({name}): 'tier' must be a non-empty string")
        role_raw = raw.get("role")
        if role_raw is not None and (not isinstance(role_raw, str) or not role_raw):
            raise LocalConfigError(
                f"{where} ({name}): 'role' must be a non-empty string if present"
            )
        backing = _parse_backing_services(raw.get("backing_services"), f"{where} ({name})")
        profiles.append(
            EnvProfile(name=name, tier=tier, role=role_raw, backing_services=backing)
        )
    return LocalConfigView(environments=tuple(profiles))


def find_config_path(workspace_root: Path) -> Path | None:
    """First existing deploy-config path under *workspace_root*, or ``None``."""
    for parts in CONFIG_RELATIVE_PATHS:
        candidate = workspace_root.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return None


def load_local_config(workspace_root: Path) -> LocalConfigView | None:
    """Load the additive LOCAL view under *workspace_root*, or ``None`` when no
    deploy config is present (the tier is inert without one)."""
    path = find_config_path(workspace_root)
    if path is None:
        return None
    return parse_local_config(path.read_text(encoding="utf-8"))

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

"""Contribution type + metadata schema.

A `Contribution` subclass declares:

  - `metadata: ClassVar[ContributionMetadata]` — name, phase, ordering
    declarations, optional required flag, plugin-contract `api_version`.
  - `contribute(host) -> None | Awaitable[None]` — the adapter body.
    Sync or async; the main loop awaits coroutines.

Metadata is Pydantic-validated with `extra="forbid"` and frozen so
authoring typos fail-closed at load.

The phase set is the minimal three-partition Eve proposed (proposal §8.1):

  - `before_orchestrator_start` — runs before the orchestrator's
    `_startup()` completes. The observability aggregator, memory
    sidecar launcher, persona loader, and declaration-only adapters
    live here.
  - `wrap_activate_scope` — runs after orchestrator `_startup()` has
    registered its `activate_scope` handler, wrapping it with the
    gate chain in dispatch order safety → reversibility → cost → orig.
  - `after_orchestrator_ready` — runs after all wraps are installed;
    self-correction subscribes, self-upgrade probes, the escape-hatch
    workspace bootstrap.py loader fires.

Plugin contract versioning (F7-PLUGIN-VERSION, v1.0-readiness):

  - `ContributionMetadata.api_version: int = 1` declares which plugin
    contract revision the contribution was authored against.
  - `SUPPORTED_API_VERSION` is the version this bootstrap accepts.
  - Mismatches are rejected by `read_metadata()` with a clear error
    naming expected vs received api_version (see `errors.py`).
  - The default of `1` preserves backward-compat with existing
    contributions written before the field existed.

Host attribute surface (`BootstrapHostProtocol`):

  - The runtime host passed to `contribute(host)` is a concrete
    `BootstrapHost` instance from `host.py`. The `BootstrapHostProtocol`
    in this module types the attribute surface that contributions are
    permitted to read; the concrete class structurally conforms.
  - Annotated as `host: BootstrapHostProtocol` so plugin authors and
    type-checkers see the documented surface, not `Any`.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, ClassVar, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Plugin contract version this bootstrap supports. Contributions that
# declare a different `api_version` are rejected at read_metadata time.
SUPPORTED_API_VERSION: int = 1


class Phase(str, Enum):
    first_run_scaffold = "first_run_scaffold"
    before_orchestrator_start = "before_orchestrator_start"
    wrap_activate_scope = "wrap_activate_scope"
    after_orchestrator_ready = "after_orchestrator_ready"


PHASE_ORDER: tuple[Phase, ...] = (
    Phase.first_run_scaffold,
    Phase.before_orchestrator_start,
    Phase.wrap_activate_scope,
    Phase.after_orchestrator_ready,
)


class ContributionMetadata(BaseModel):
    """Structured metadata for a contribution.

    `name`: unique identifier; collisions fail-closed at load.
    `phase`: one of the three `Phase` values.
    `after`: tuple of names this contribution must run after.
    `before`: tuple of names this contribution must run before.
    `required`: if True (default), a missing/erroring adapter fails the
        boot. If False, a workspace may list the contribution but
        survive its absence at import time (an erroring `contribute()`
        still fails the boot — `required=False` is only about import
        availability).
    `api_version`: plugin-contract revision this contribution was
        authored against (default `1`). Bootstrap rejects mismatches
        with a clear error naming expected vs received. The default
        preserves backward-compat with contributions written before
        the field existed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    phase: Phase
    after: tuple[str, ...] = ()
    before: tuple[str, ...] = ()
    required: bool = True
    api_version: int = Field(default=1, ge=1)

    @field_validator("after", "before", mode="before")
    @classmethod
    def _coerce_ordering_to_tuple(cls, v: Any) -> Any:
        # Accept lists coming from YAML; reject anything that is not a
        # sequence of strings. The final value is a tuple (frozen).
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        raise ValueError("after/before must be a tuple or list of names")


@runtime_checkable
class BootstrapHostProtocol(Protocol):
    """Structural protocol typing the public host-attribute surface.

    Contributions receive a host object during `contribute(host)`; this
    Protocol documents the attributes they may read/write. The concrete
    runtime host is `loam.workspace_bootstrap.host.BootstrapHost`, which
    structurally conforms — no inheritance required.

    F7-PLUGIN-VERSION (v1.0-readiness): replaces the previous `host: Any`
    annotation so plugin authors and type-checkers see the documented
    surface. The Protocol intentionally types only the attributes
    contributions are documented to use; runtime-internal helpers
    (e.g. `_enter_phase`) are deliberately omitted.

    NAME RESOLUTION NOTE: the concrete class in `host.py` is named
    `BootstrapHost` and is part of the public surface (constructed
    directly by `Bootstrapper` and by ~7 test files). To avoid a
    breaking rename, the Protocol carries the `BootstrapHostProtocol`
    suffix and the concrete class keeps its name. Structural subtyping
    means contributions remain Protocol-typed regardless of which name
    a plugin author imports.

    Attribute groups (see `host.py` docstring for full lifecycle):

      1. Framework-owned singletons (always populated):
         config_dir, workspace_root, manifest_path, tracer,
         channel_registry, current_phase.
      2. Orchestrator-linked (populated during `wrap_activate_scope`):
         orchestrator, ipc_server, scope_runtime, objective_tracker,
         monitor, dormancy.
      3. Per-adapter outputs (populated as contributions run):
         observability_provider, loaded_persona, reversibility_controller,
         safety_controller, cost_controller, self_correction_controller,
         memory_sidecar_url.

    Helpers: `require(attr)`, `register_shutdown(name, callable_)`,
    `register_channel(name, channel)`.
    """

    # Group 1 — framework-owned singletons.
    config_dir: Path
    workspace_root: Path
    manifest_path: Path
    tracer: Any  # opentelemetry tracer; typed Any to avoid opentelemetry import in spec.py
    channel_registry: dict[str, Any]

    # Group 2 — orchestrator-linked (assigned during wrap phase; may be None earlier).
    orchestrator: Any
    ipc_server: Any
    scope_runtime: Any
    objective_tracker: Any
    monitor: Any
    dormancy: Any

    # Group 3 — per-adapter outputs (assigned by individual contributions).
    observability_provider: Any
    loaded_persona: Any
    reversibility_controller: Any
    safety_controller: Any
    cost_controller: Any
    self_correction_controller: Any
    memory_sidecar_url: Optional[str]

    @property
    def current_phase(self) -> Optional[Phase]:  # pragma: no cover - structural
        ...

    def require(self, attr: str) -> Any:  # pragma: no cover - structural
        ...

    def register_shutdown(self, name: str, callable_: Any) -> None:  # pragma: no cover - structural
        ...

    def register_channel(self, name: str, channel: Any) -> None:  # pragma: no cover - structural
        ...


@runtime_checkable
class Contribution(Protocol):
    """Structural protocol every contribution satisfies.

    Subclasses set `metadata` as a class attribute and implement
    `contribute(host)`. The discovery machinery instantiates a
    contribution class with no args; therefore `__init__` must accept
    no required positional arguments.
    """

    metadata: ClassVar[ContributionMetadata]

    def contribute(self, host: "BootstrapHostProtocol") -> None | Awaitable[None]:  # pragma: no cover - structural
        ...


class BaseContribution:
    """Convenience base class. Subclasses override `metadata` and
    implement `contribute(host)`. Not required by the framework —
    anything satisfying the `Contribution` protocol works — but
    simplifies the common case.
    """

    metadata: ClassVar[ContributionMetadata]  # subclasses must set this.

    def contribute(self, host: "BootstrapHostProtocol") -> None | Awaitable[None]:  # pragma: no cover - abstract
        raise NotImplementedError

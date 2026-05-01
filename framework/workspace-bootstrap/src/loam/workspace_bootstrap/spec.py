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
    declarations, optional required flag.
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
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Awaitable, ClassVar, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    phase: Phase
    after: tuple[str, ...] = ()
    before: tuple[str, ...] = ()
    required: bool = True

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
class Contribution(Protocol):
    """Structural protocol every contribution satisfies.

    Subclasses set `metadata` as a class attribute and implement
    `contribute(host)`. The discovery machinery instantiates a
    contribution class with no args; therefore `__init__` must accept
    no required positional arguments.
    """

    metadata: ClassVar[ContributionMetadata]

    def contribute(self, host: Any) -> None | Awaitable[None]:  # pragma: no cover - structural
        ...


class BaseContribution:
    """Convenience base class. Subclasses override `metadata` and
    implement `contribute(host)`. Not required by the framework —
    anything satisfying the `Contribution` protocol works — but
    simplifies the common case.
    """

    metadata: ClassVar[ContributionMetadata]  # subclasses must set this.

    def contribute(self, host: Any) -> None | Awaitable[None]:  # pragma: no cover - abstract
        raise NotImplementedError

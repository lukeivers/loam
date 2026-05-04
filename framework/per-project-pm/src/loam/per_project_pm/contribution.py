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

"""Workspace-bootstrap contribution for per-project-pm.

Per cycle-2 plan §4 Surface #6 + AC.PPM.8:

  - :class:`PerProjectPMContribution` — registered via the
    ``loam.bootstrap.contributions`` entry-point; published as
    ``host.per_project_pm`` at the ``after_orchestrator_ready`` phase
    after ``primary_persona``.
  - :class:`PerProjectPMRuntime` — lightweight handle on the host;
    holds ``workspace_root`` + provides
    :meth:`PerProjectPMRuntime.runtime_for` factory that lazily loads
    a named PM into a :class:`~loam.per_project_pm.runtime.PMRuntime`.

Lazy resolution per F2.C: the contribution does NOT eagerly load
every PM at boot. Empty workspace = no PMs authored = the
contribution just publishes the factory; calling
``host.per_project_pm.runtime_for("eric-saas-pm")`` raises
:class:`PMNotFoundError` until a PM with that name has been authored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from loam.workspace_bootstrap.spec import (
    BaseContribution,
    ContributionMetadata,
    Phase,
)

from loam.per_project_pm.runtime import PMRuntime


@dataclass
class PerProjectPMRuntime:
    """Lightweight runtime handle published on ``host.per_project_pm``.

    Holds ``workspace_root`` so persona-side / CLI invocations agree
    on the workspace identity, and provides the lazy factory
    :meth:`runtime_for` for loading a named PM.

    Per F2.C (cycle-2 plan §2): this is the lazy-resolution surface.
    No PM is loaded at boot; PMs load on demand when the persona
    invokes ``runtime_for(pm_name)``.
    """

    workspace_root: Path
    # Cycle 2 explicitly does NOT cache PMRuntime instances — every
    # runtime_for() call re-reads from disk. This matches the
    # correctness-over-perf trade-off named in the design-note §5.
    # The reserved field is here so a future Cycle (5+) could add
    # an LRU cache without changing the API surface.
    _reserved_cache: dict[str, Any] = field(default_factory=dict, repr=False)

    def runtime_for(self, pm_name: str) -> PMRuntime:
        """Lazily load the named PM.

        Raises:
            PMNotFoundError: when no
                ``contract.yaml`` exists at
                ``<workspace_root>/workspace/.loam/pms/<pm_name>/``.
            PMStateCorruptedError: when contract.yaml or state files
                fail schema validation.
            ValueError: when ``pm_name`` is empty.
        """
        if not pm_name:
            raise ValueError("pm_name must be a non-empty string")
        return PMRuntime.from_workspace(self.workspace_root, pm_name)


class PerProjectPMContribution(BaseContribution):
    """Constructs :class:`PerProjectPMRuntime` and assigns to
    ``host.per_project_pm``.

    Phase: ``after_orchestrator_ready`` — same phase as the
    dev-sdlc plugin's contribution; runs after the orchestrator's
    boot is complete and the host attribute surface is stable.

    After: ``("primary_persona",)`` — the per-project PM composes
    against the primary-persona at the persona-side flow level
    (Cycle 4 wires); declaring the ordering keeps boot ordering
    sound when later cycles wire the composition.

    Per AC.PPM.8.
    """

    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="per_project_pm",
        phase=Phase.after_orchestrator_ready,
        after=("primary_persona",),
    )

    def contribute(self, host: Any) -> None:
        """Publish ``host.per_project_pm`` as a
        :class:`PerProjectPMRuntime` instance.

        The host's ``workspace_root`` attribute is the source of truth
        for the workspace identity; the published runtime echoes it
        so persona / CLI invocations resolve PM paths identically.
        """
        host.per_project_pm = PerProjectPMRuntime(
            workspace_root=Path(host.workspace_root),
        )

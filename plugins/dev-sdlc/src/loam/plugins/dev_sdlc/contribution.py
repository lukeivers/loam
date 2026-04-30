"""Workspace-bootstrap contribution class — DevSdlcContribution.

Per plan §4 AC.OSS-M6.1 + §10 D-build.M6.5: the plugin composes
against workspace-bootstrap's existing contribution-discovery
protocol via the `loam.bootstrap.contributions` entry-point group.

Phase = `after_orchestrator_ready` per the manifest's recommendation —
the plugin reads `host.scope_runtime` + `host.objective_tracker` at
contribute() time.

`after = ('primary_persona', 'objective_tracker', 'scope_of_work')`
ensures those host attributes are populated before the plugin
constructs its runtime.

The contribution publishes `host.dev_sdlc` (a `DevSdlcRuntime`
instance) for downstream consumers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from loam.workspace_bootstrap.spec import (
    BaseContribution,
    ContributionMetadata,
    Phase,
)


@dataclass
class DevSdlcRuntime:
    """Lightweight runtime handle published on the host.

    Holds references to the scope_runtime + objective_tracker so
    persona-side calls into `loam.plugins.dev_sdlc.api.start_project`
    (etc.) can pass them through. Holds `workspace_root` so CLI-
    invocations and persona invocations agree on the workspace.
    """

    workspace_root: Any
    scope_runtime: Any | None
    objective_tracker: Any | None


class DevSdlcContribution(BaseContribution):
    """Constructs `DevSdlcRuntime` and assigns to `host.dev_sdlc`.

    See module docstring for the metadata + ordering rationale.
    """

    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="dev_sdlc",
        phase=Phase.after_orchestrator_ready,
        after=(
            "primary_persona",
            "objective_tracker",
            "scope_of_work",
        ),
    )

    def contribute(self, host: Any) -> None:
        # Open-attribute-surface convention per BootstrapHost docstring:
        # adapters assign new attributes to the host for downstream
        # consumption. The DevSdlcRuntime exposes the workspace + the
        # composed runtimes so persona / CLI invocations can pass them
        # through to the plugin's API surface.
        host.dev_sdlc = DevSdlcRuntime(
            workspace_root=host.workspace_root,
            scope_runtime=getattr(host, "scope_runtime", None),
            objective_tracker=getattr(host, "objective_tracker", None),
        )

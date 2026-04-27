"""BootstrapHost — shared singletons + named access to
orchestrator-constructed components.

The host is constructed by the framework at boot and passed to every
contribution's `contribute(host)` callable. Contributions read and
write named attributes on the host; the host itself is a thin
container with validated accessors.

Attributes fall into three groups:

  1. Framework-owned singletons available on every phase:
     - `config_dir` (Path) — where contribution configs live.
     - `workspace_root` (Path) — the workspace directory.
     - `manifest_path` (Path) — `bootstrap.yaml` path.
     - `tracer` (opentelemetry tracer) — bootstrap's own spans.
     - `channel_registry` (dict[str, Any]) — notification channel
       registry. Bootstrap initializes it empty; adapters and
       Phase 4+ contributions register channels by name.

  2. Orchestrator-linked (populated during `wrap_activate_scope`):
     - `orchestrator` (Orchestrator) — the running instance.
     - `ipc_server` (IPCServer) — shared IPC server.
     - `scope_runtime` (ScopeRuntime) — from `orchestrator.scope_runtime`.
     - `objective_tracker` (ObjectiveTracker).
     - `monitor` (BackgroundWorkMonitor).
     - `graceful_degradation` (DegradationComponent | None).

  3. Per-adapter outputs (populated as contributions run; used by
     downstream contributions that declare `after=`):
     - `observability_provider` — (TracerProvider, BatchSpanProcessor, Exporter).
     - `loaded_persona` (LoadedPersona | None).
     - `reversibility_controller`, `safety_controller`, `cost_controller`
       (the gate controllers, after the wrap-phase adapters run).
     - `self_correction_controller`.
     - `memory_sidecar_url` (str | None) — health-verified sidecar URL.

Access discipline: reading an attribute before its producing phase
raises `HostAttributeNotYetAvailable`. Contributions are expected to
read only attributes produced by phases earlier than their own, or by
contributions named in their `after=` declaration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from opentelemetry import trace

from .spec import Phase


class HostAttributeNotYetAvailable(RuntimeError):
    """Raised when a contribution reads a host attribute before the
    phase that produces it has run."""


class BootstrapHost:
    """Shared state passed to every contribution.

    This is an explicit container rather than a dataclass because the
    `contribute(host)` contract lets adapters assign new attributes to
    the host for downstream consumption (by their name). Dataclass
    frozen= would forbid that; an open attribute surface is the
    intended pattern.
    """

    def __init__(
        self,
        *,
        config_dir: Path,
        workspace_root: Path,
        manifest_path: Path,
    ) -> None:
        self.config_dir: Path = config_dir
        self.workspace_root: Path = workspace_root
        self.manifest_path: Path = manifest_path

        # Acquire bootstrap's own tracer — A1 constraint: do NOT
        # construct a TracerProvider here. The observability_aggregator
        # contribution sets the global provider; `get_tracer` late-binds.
        self.tracer = trace.get_tracer("pos.bootstrap")

        # Channel registry — adapters register notification channels
        # by name for discoverability and reuse.
        self.channel_registry: dict[str, Any] = {}

        # Phase tracking so the host can error on too-early reads.
        self._current_phase: Optional[Phase] = None

        # Per-adapter outputs (assigned by contributions). Declared here
        # with `None` defaults so attribute probing is typed, but the
        # actual assignment happens inside the contribution body.
        self.orchestrator: Any = None
        self.ipc_server: Any = None
        self.scope_runtime: Any = None
        self.objective_tracker: Any = None
        self.monitor: Any = None
        self.graceful_degradation: Any = None
        self.observability_provider: Any = None
        self.loaded_persona: Any = None
        self.reversibility_controller: Any = None
        self.safety_controller: Any = None
        self.cost_controller: Any = None
        self.self_correction_controller: Any = None
        self.memory_sidecar_url: Optional[str] = None

        # Shutdown hooks — contributions push no-arg callables here,
        # framework calls them in reverse order at teardown.
        self._shutdown_hooks: list[tuple[str, Any]] = []

    # -- phase tracking (framework-internal) --------------------------

    def _enter_phase(self, phase: Phase) -> None:
        self._current_phase = phase

    def _exit_all_phases(self) -> None:
        self._current_phase = None

    # -- public helpers contributions use -----------------------------

    @property
    def current_phase(self) -> Optional[Phase]:
        return self._current_phase

    def require(self, attr: str) -> Any:
        """Read an attribute; raise a clear error if the attribute is
        None (i.e. its producing phase has not yet populated it).

        Adapters use this in preference to bare attribute access so
        the `before`-its-phase error is diagnostic rather than
        cryptic AttributeError-on-None downstream."""
        value = getattr(self, attr, None)
        if value is None:
            raise HostAttributeNotYetAvailable(
                f"host attribute {attr!r} not yet available "
                f"(current phase: {self._current_phase})"
            )
        return value

    def register_shutdown(self, name: str, callable_: Any) -> None:
        """Register a no-arg callable to run on teardown. Callables run
        in REVERSE registration order (last-in-first-out)."""
        self._shutdown_hooks.append((name, callable_))

    def register_channel(self, name: str, channel: Any) -> None:
        """Register a notification channel by name in the registry.
        Second registration of the same name replaces the prior entry
        (and is logged via the caller — host does not log)."""
        self.channel_registry[name] = channel

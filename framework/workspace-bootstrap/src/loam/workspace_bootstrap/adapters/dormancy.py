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

"""Adapter — dormancy (constructor + supervisor wiring).

Phase: ``before_orchestrator_start``, ``after=("primary_persona",)``.

Per amendment #86 (M5 wire-dormancy), this adapter promotes from the
declaration-only shape introduced at amendment #6 into a real
constructor that:

  1. Loads dormancy config from ``host.config_dir / dormancy-config.yaml``
     (returns defaults when absent).
  2. Builds a ``DegradationNotifier`` from non-group channels in
     ``host.channel_registry``. Empty channel list is acceptable —
     the existing notifier queues notifications in-memory until a
     channel registers (the ``telegram_interface`` adapter populates
     the registry later in ``after_orchestrator_ready``).
  3. Constructs the ``DegradationComponent`` via ``build(...)`` and
     assigns to ``host.dormancy``.
  4. Subscribes ``comp.on_scope_event`` to
     ``host.scope_runtime.subscribe_all`` per the dormancy
     architecture's "Core composition" section — closes the
     Claude-API memory-system detection blind spot.
  5. Awaits ``comp.reconcile_on_startup(...)`` for restart edge cases.
  6. When ``host.memory_sidecar_url`` is populated by the
     ``memory_system`` adapter, constructs ``MemorySupervisor`` with
     a stdlib-urlopen probe and an ``on_transition`` bridge to
     dormancy's ``record_supervisor_signal`` surface, then calls
     ``await supervisor.start()``.
  7. Registers a shutdown hook to cleanly stop the supervisor's
     probe loop at process teardown.

When ``host.memory_sidecar_url`` is ``None`` (test workspaces with
``launch: False`` skip the sidecar), the supervisor is NOT
constructed; ``host.memory_supervisor`` is ``None``. The
``DegradationComponent`` is still built so the Claude-API detection
path stays active.

AC family: AC.OSS-M5.1 .. AC.OSS-M5.7 + AC.OSS-M5.S.
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from typing import Any, ClassVar

from ..spec import BaseContribution, ContributionMetadata, Phase


_LOGGER = logging.getLogger(__name__)


def _build_probe(url: str):
    """Return an async probe callable that hits the sidecar's health
    endpoint and returns a ``ProbeResult`` per the supervisor's
    protocol.

    Mirrors the ``memory_system`` adapter's existing probe pattern —
    stdlib ``urllib.request.urlopen`` only, no third-party deps.
    """
    from loam.orchestrator.supervisor import ProbeResult

    async def _probe() -> ProbeResult:
        import time as _time

        started = _time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:  # noqa: S310 — fixed sidecar URL
                ok = resp.status == 200
                latency_ms = (_time.monotonic() - started) * 1000.0
                return ProbeResult(
                    ok=ok,
                    error_class=None if ok else f"http_{resp.status}",
                    latency_ms=latency_ms,
                )
        except (urllib.error.URLError, OSError):
            latency_ms = (_time.monotonic() - started) * 1000.0
            return ProbeResult(
                ok=False,
                error_class="refused",
                latency_ms=latency_ms,
            )

    return _probe


def _build_supervisor_bridge(comp: Any):
    """Return an ``on_transition`` callable that maps supervisor
    state edges to dormancy detector signals.

    Mapping (per plan §10 D-build.M5.4):

      to_state == degraded   → memory_sidecar_down
      to_state == escalated  → memory_sidecar_down (idempotent)
      to_state == recovering → no-op (intermediate state)
      to_state == normal     → memory_sidecar_recovered

    Resolves the asymmetric callback surface (``MemorySupervisor``
    exposes ``on_recovering`` + ``on_normal`` shorthands but no
    explicit ``on_degraded``) via uniform ``on_transition``
    subscription per plan §11 finding #2.
    """
    from loam.dormancy.errors import DegradationSignal
    from loam.orchestrator.supervisor import (
        SupervisorState,
        SupervisorTransition,
    )

    async def _on_transition(t: SupervisorTransition) -> None:
        if t.to_state in (SupervisorState.degraded, SupervisorState.escalated):
            await comp.detector.record_supervisor_signal(
                signal=DegradationSignal.memory_sidecar_down
            )
        elif t.to_state == SupervisorState.normal:
            await comp.detector.record_supervisor_signal(
                signal=DegradationSignal.memory_sidecar_recovered
            )
        # SupervisorState.recovering is an intermediate state; no
        # dormancy signal emitted (the dormancy FSM advances through
        # half_open via dwell + probe, OR via the recovered short-path
        # when the supervisor reaches normal).

    return _on_transition


class DormancyContribution(BaseContribution):
    """Promotes dormancy from declaration-only to a real constructor.

    See module docstring for full contract.
    """

    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="dormancy",
        phase=Phase.before_orchestrator_start,
        after=("primary_persona",),
    )

    async def contribute(self, host) -> None:
        from loam.dormancy.component import DegradationComponent
        from loam.dormancy.config import load_config
        from loam.dormancy.notification import DegradationNotifier

        # 1. Load dormancy config. ``load_config`` returns defaults
        #    when the file is absent.
        cfg_path = host.config_dir / "dormancy-config.yaml"
        cfg = load_config(cfg_path)

        # 2. Build the notifier from non-group channels in the host's
        #    channel registry. Empty list is acceptable — the
        #    notifier queues notifications until a channel registers
        #    (the ``telegram_interface`` adapter runs in a later phase
        #    and populates the registry).
        non_group_channels = [
            ch
            for ch in host.channel_registry.values()
            if not getattr(ch, "is_group", False)
        ]
        notifier = DegradationNotifier(channels=non_group_channels)

        # 3. Construct the component. The dispatcher inside the
        #    component already binds the orchestrator's pause/resume
        #    hooks via ``OrchestratorHooks`` Protocol — no extra
        #    wiring needed; AC.OSS-M5.2 is satisfied as a
        #    side-effect of construction.
        comp = DegradationComponent.build(
            cfg=cfg,
            orchestrator=host.orchestrator,
            scope_runtime=host.scope_runtime,
            notifier=notifier,
        )
        host.dormancy = comp

        # 4. Subscribe the component's on_scope_event handler to the
        #    scope runtime's emitter, per architecture.md §"Core
        #    composition". This closes the Claude-API memory-system
        #    detection blind spot (memory failures surface as scope
        #    failures with Claude-related reasons).
        if hasattr(host.scope_runtime, "subscribe_all"):
            host.scope_runtime.subscribe_all(comp.on_scope_event)

        # 5. Reconcile across restart. On a fresh boot both sides are
        #    empty and the call is a no-op.
        await comp.reconcile_on_startup(
            orchestrator_paused=host.orchestrator.is_paused,
        )

        # 6 + 7. Construct + start MemorySupervisor when the sidecar
        # URL is populated. When ``launch: False`` skipped the
        # sidecar, ``host.memory_sidecar_url`` is None and we
        # short-circuit cleanly per AC.OSS-M5.6.
        sidecar_url = getattr(host, "memory_sidecar_url", None)
        host.memory_supervisor = None
        if sidecar_url is not None:
            from loam.orchestrator.supervisor import MemorySupervisor

            probe = _build_probe(sidecar_url)
            bridge = _build_supervisor_bridge(comp)
            supervisor = MemorySupervisor(
                probe=probe,
                on_transition=bridge,
            )
            await supervisor.start()
            host.memory_supervisor = supervisor

            async def _shutdown() -> None:
                try:
                    await supervisor.stop()
                except Exception:
                    _LOGGER.debug(
                        "dormancy_adapter_supervisor_stop_failed",
                        exc_info=True,
                    )

            host.register_shutdown("memory_supervisor", _shutdown)

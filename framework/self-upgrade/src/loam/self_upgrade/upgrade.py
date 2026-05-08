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

"""D5 + D9 — top-level upgrade flow.

Coordinates the full sequence:

1. Load manifest (D1)
2. Pre-upgrade snapshot (D3)
3. Pre-upgrade probe run (D4)
4. orchestrator.pause_activation("upgrade:<tag>")
5. Bounded drain window
6. SIGTERM; wait for pid exit
7. Atomic symlink swap (staging → live)
8. launchctl kickstart the new tree
9. Wait for boot; no-op RPC succeeds (clause a)
10. Post-upgrade probe run (D4 surfaces again)
11. Seven-clause verification (D6)
12. Accept (D9) or rollback (D8)

This module is **injection-heavy** so tests can exercise every branch
without needing a live orchestrator. Production wiring is in
``cli.py`` which builds the default injection bundle.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from .clause_checks import ClauseBundle, run_all_clauses
from .config import UpgradeConfig
from .manifest import Manifest
from .observability import span as otel_span
from .orchestrator_control import (
    OrchestratorControlError,
    atomic_symlink_swap,
    sigterm_and_wait,
    wait_for_boot,
    wait_for_drain,
)
from .paths import Paths
from .probes import collect_pre_probe, post_upgrade_probe_hashes
from .rollback import RollbackFailed, rollback as do_rollback
from .snapshot import capture_substrate_snapshots, substrate_components


@dataclass
class UpgradeResult:
    tag: str
    accepted: bool
    clause_results: dict[str, Any]
    duration_s: float
    timings: dict[str, float]
    rolled_back: bool = False
    rollback_success: bool | None = None
    halt_reason: str | None = None


class LiveAdapters(Protocol):
    """Bundle of callables that talk to the live components.

    Tests can substitute in-memory adapters; the CLI builds a production
    bundle wiring the orchestrator IPC client, the memory harness, etc.
    """

    def pause_activation(self, reason: str) -> None: ...
    def is_drained(self) -> bool: ...
    def orchestrator_pid(self) -> int | None: ...
    def restart_orchestrator(self) -> None: ...
    def is_orchestrator_up(self) -> bool: ...
    def no_op_rpc(self) -> bool: ...
    def resume_activation(self) -> None: ...
    def post_survival_payloads(self) -> dict[str, Any]: ...
    def post_memory_drift(self) -> Any: ...
    def post_scope_drift(self) -> Any: ...
    def post_objective_drift(self) -> Any: ...


def execute_upgrade(
    *,
    manifest: Manifest,
    paths: Paths,
    config: UpgradeConfig,
    staging_dir: Path,
    prior_tag: str | None,
    adapters: LiveAdapters,
    progress: Callable[[str, str, float], None] | None = None,
) -> UpgradeResult:
    """Run the full upgrade sequence.

    ``progress(stage, verdict, elapsed_s)`` is invoked per stage so the
    CLI can render its streaming output. ``verdict`` is 'ok' | 'halt'.
    """
    t0 = time.monotonic()
    tag = manifest.release_tag
    timings: dict[str, float] = {}

    def _tick(stage: str, verdict: str, started: float) -> None:
        elapsed = time.monotonic() - started
        timings[stage] = elapsed
        if progress:
            progress(stage, verdict, elapsed)

    with otel_span(
        "loam.upgrade.started",
        {"loam.upgrade.tag": tag, "loam.upgrade.commit_sha": manifest.commit_sha},
    ):
        # 1. Pre-upgrade snapshot (D3)
        stage_start = time.monotonic()
        with otel_span(
            "loam.upgrade.pre_snapshot", {"loam.upgrade.tag": tag}
        ):
            probe_fn = lambda: post_upgrade_probe_hashes(paths)
            capture_substrate_snapshots(paths, tag, probe_fn=probe_fn)
        _tick("pre_snapshot", "ok", stage_start)

        # 2. Pre-upgrade probe (D4)
        stage_start = time.monotonic()
        with otel_span(
            "loam.upgrade.pre_probe", {"loam.upgrade.tag": tag}
        ):
            pre_bundle = collect_pre_probe(paths, tag)
            pre_bundle.save(paths.pre_probe_json(tag))
        _tick("pre_probe", "ok", stage_start)

        # 3. pause_activation
        stage_start = time.monotonic()
        with otel_span("loam.upgrade.pause_activation", {"loam.upgrade.tag": tag}):
            adapters.pause_activation(f"upgrade:{tag}")
        _tick("pause_activation", "ok", stage_start)

        # 4. Drain window
        stage_start = time.monotonic()
        try:
            with otel_span("loam.upgrade.drain", {"loam.upgrade.tag": tag}):
                wait_for_drain(
                    is_drained=adapters.is_drained,
                    timeout_s=config.drain_timeout_seconds,
                )
            _tick("drain", "ok", stage_start)
        except OrchestratorControlError as exc:
            _tick("drain", "halt", stage_start)
            return _halt_with_resume(
                paths,
                tag,
                prior_tag,
                timings,
                t0,
                halt_reason=f"drain_timeout: {exc}",
                adapters=adapters,
            )

        # 5. SIGTERM + pid exit
        stage_start = time.monotonic()
        pid = adapters.orchestrator_pid()
        try:
            if pid is not None:
                with otel_span(
                    "loam.upgrade.sigterm",
                    {"loam.upgrade.tag": tag, "loam.upgrade.pid": pid},
                ):
                    sigterm_and_wait(pid, timeout_s=config.sigterm_timeout_seconds)
            _tick("sigterm", "ok", stage_start)
        except OrchestratorControlError as exc:
            _tick("sigterm", "halt", stage_start)
            return _halt_rollback(
                paths, tag, prior_tag, timings, t0,
                halt_reason=f"sigterm_timeout: {exc}",
                failing_clauses=["a"],
                clause_details={"a": {"reason": str(exc)}},
                adapters=adapters,
            )

        # 6. Atomic symlink swap
        stage_start = time.monotonic()
        with otel_span("loam.upgrade.swap", {"loam.upgrade.tag": tag}):
            atomic_symlink_swap(paths.current_link, staging_dir)
        _tick("swap", "ok", stage_start)

        # 7. Restart orchestrator
        stage_start = time.monotonic()
        try:
            with otel_span("loam.upgrade.orchestrator_restart", {"loam.upgrade.tag": tag}):
                adapters.restart_orchestrator()
        except Exception as exc:
            _tick("orchestrator_restart", "halt", stage_start)
            return _halt_rollback(
                paths, tag, prior_tag, timings, t0,
                halt_reason=f"restart failed: {exc}",
                failing_clauses=["a"],
                clause_details={"a": {"reason": str(exc)}},
                adapters=adapters,
            )
        try:
            wait_for_boot(
                is_up=adapters.is_orchestrator_up,
                timeout_s=config.orchestrator_boot_timeout_seconds,
            )
            _tick("orchestrator_restart", "ok", stage_start)
        except OrchestratorControlError as exc:
            _tick("orchestrator_restart", "halt", stage_start)
            return _halt_rollback(
                paths, tag, prior_tag, timings, t0,
                halt_reason=f"boot_timeout: {exc}",
                failing_clauses=["a"],
                clause_details={"a": {"reason": str(exc)}},
                adapters=adapters,
            )

        # 8. Post-upgrade probe + clause verification
        stage_start = time.monotonic()
        with otel_span("loam.upgrade.post_probe", {"loam.upgrade.tag": tag}):
            bundle = run_all_clauses(
                no_op_rpc=adapters.no_op_rpc,
                survival_payloads=adapters.post_survival_payloads(),
                memory_drift_report=adapters.post_memory_drift(),
                scope_drift=adapters.post_scope_drift(),
                objective_drift=adapters.post_objective_drift(),
                manifest=manifest,
                paths=paths,
                tag=tag,
                live_root=paths.current_link.resolve(),
                snapshot_components=substrate_components(),
            )
            paths.post_probe_json(tag).write_text(
                json.dumps(bundle.to_dict(), indent=2, default=str)
            )
        _tick("post_probe", "ok", stage_start)

        # 9. Accept or rollback
        if bundle.all_passed:
            stage_start = time.monotonic()
            with otel_span(
                "loam.upgrade.accepted",
                {
                    "loam.upgrade.tag": tag,
                    "loam.upgrade.duration_s": time.monotonic() - t0,
                    "loam.upgrade.files_verified": len(manifest.files),
                },
            ):
                _write_accepted_json(paths, tag, bundle, t0, manifest)
                adapters.resume_activation()
            _tick("accept", "ok", stage_start)
            return UpgradeResult(
                tag=tag,
                accepted=True,
                clause_results=bundle.to_dict(),
                duration_s=time.monotonic() - t0,
                timings=timings,
            )

        # Rollback — at least one clause failed
        return _halt_rollback(
            paths, tag, prior_tag, timings, t0,
            halt_reason=f"clause(s) failed: {bundle.failing()}",
            failing_clauses=bundle.failing(),
            clause_details=bundle.to_dict(),
            adapters=adapters,
        )


def _write_accepted_json(
    paths: Paths,
    tag: str,
    bundle: ClauseBundle,
    t0: float,
    manifest: Manifest,
) -> None:
    target = paths.accepted_json(tag)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "release_tag": tag,
                "commit_sha": manifest.commit_sha,
                "clause_verdicts": bundle.to_dict(),
                "duration_s": time.monotonic() - t0,
                "files_verified": len(manifest.files),
                "schema_versions": [
                    {"component": s.component, "version_post": s.version_post}
                    for s in manifest.component_schemas
                ],
                "breaking_changes": [
                    {"id": bc.id, "component": bc.component}
                    for bc in manifest.breaking_changes
                ],
            },
            indent=2,
            default=str,
        )
    )


def _halt_with_resume(
    paths: Paths,
    tag: str,
    prior_tag: str | None,
    timings: dict[str, float],
    t0: float,
    *,
    halt_reason: str,
    adapters: LiveAdapters,
) -> UpgradeResult:
    """Halt before the symlink swap: just resume activation, no
    rollback needed — no state has changed in the live tree."""
    try:
        adapters.resume_activation()
    except Exception:
        pass
    return UpgradeResult(
        tag=tag,
        accepted=False,
        clause_results={},
        duration_s=time.monotonic() - t0,
        timings=timings,
        rolled_back=False,
        halt_reason=halt_reason,
    )


def _halt_rollback(
    paths: Paths,
    tag: str,
    prior_tag: str | None,
    timings: dict[str, float],
    t0: float,
    *,
    halt_reason: str,
    failing_clauses: list[str],
    clause_details: dict[str, Any],
    adapters: LiveAdapters,
) -> UpgradeResult:
    """Halt after the symlink swap: rollback required. Whether the
    rollback itself succeeds or fails is reflected in
    ``rollback_success``."""
    try:
        do_rollback(
            paths=paths,
            tag=tag,
            prior_tag=prior_tag,
            failing_clauses=failing_clauses,
            clause_details=clause_details,
            restart_orchestrator=adapters.restart_orchestrator,
        )
        rollback_success = True
    except RollbackFailed:
        rollback_success = False

    try:
        adapters.resume_activation()
    except Exception:
        pass

    return UpgradeResult(
        tag=tag,
        accepted=False,
        clause_results=clause_details,
        duration_s=time.monotonic() - t0,
        timings=timings,
        rolled_back=True,
        rollback_success=rollback_success,
        halt_reason=halt_reason,
    )

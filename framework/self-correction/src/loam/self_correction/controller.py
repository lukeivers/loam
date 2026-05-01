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

"""SelfCorrectionController — composed runtime.

Single construction site for self-correction. Composes:

  - CorrectionStore (four-table SQLite)
  - CorrectionConfig (knobs)
  - CorrectionNotifier (one-on-one channels)
  - CompletionPrecheck (deterministic four-part enforcement)
  - ScopeFailurePyeeSubscriber (wired to ScopeRuntime.emitter)
  - OTelAnomalyPoller (polls aggregator QueryAPI)
  - IPC-boundary surfaces for the three other trigger sources

Cost-refusal catch path (CR19): the activate-scope IPC raises
`ApplicationError(-32060/61/62)` when a correction scope's budget
exceeds any ceiling. We catch at this layer, mark the episode
`refused`, emit `loam.correction.cost_refusal_caught`, and dispatch a
`CorrectionChannel` notification. Silent drop is structurally refused.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from loam.orchestrator.ipc import ApplicationError

from . import observability as obs
from .bounds import depth_cap_check, same_class_cascade_check
from .completion_check import CompletionPrecheck
from .config import CorrectionConfig, default_config
from .notification import (
    CorrectionNotification,
    CorrectionNotifier,
    render_cascade_depth_text,
    render_cascade_same_class_text,
    render_cost_refusal_text,
)
from .spec import (
    CorrectionEpisode,
    CorrectionTrigger,
    EpisodeState,
    RecordType,
    TriggerSource,
    iso_now,
)
from .spec_builder import build_correction_spec
from .store import CorrectionStore


# Cost-refusal codes from cost-governance (brief §4 constraint).
_COST_REFUSAL_CODES: frozenset[int] = frozenset({-32060, -32061, -32062})


# Callable signatures for injection.
ActivateFn = Callable[[dict[str, Any]], Awaitable[Any]]
SpecResolver = Callable[[str], Any | None]  # scope_id -> ScopeSpec | None
RegisterCompensationFn = Callable[[dict[str, Any]], Awaitable[Any]]
CreateScopeFn = Callable[..., Awaitable[Any]]


@dataclass
class CorrectionOpenResult:
    episode_id: str
    state: EpisodeState
    correction_scope_id: str | None
    refusal_reason: str | None = None


@dataclass
class SelfCorrectionController:
    """Top-level self-correction runtime.

    Constructed by the workspace bootstrap; the bootstrap supplies the
    scope runtime, the IPC activate callable, the compensation-binding
    registrar, and the set of allowed primary-persona caller identifiers.
    """

    store: CorrectionStore
    config: CorrectionConfig
    notifier: CorrectionNotifier | None = None

    # Injection for the gate-flow path:
    create_scope_fn: CreateScopeFn | None = None
    activate_fn: ActivateFn | None = None
    register_compensation_fn: RegisterCompensationFn | None = None
    spec_resolver: SpecResolver | None = None

    # The set of reporter identities permitted to call correction.user_reported.
    allowed_user_report_callers: frozenset[str] = field(default_factory=frozenset)

    # In-memory correction-scope registry: correction_scope_id → episode_id.
    _scopes_to_episodes: dict[str, str] = field(default_factory=dict)

    @property
    def completion_precheck(self) -> CompletionPrecheck:
        pc = getattr(self, "_precheck_instance", None)
        if pc is None:
            pc = CompletionPrecheck(store=self.store)
            object.__setattr__(self, "_precheck_instance", pc)
        return pc

    # ---- intake ----------------------------------------------------

    async def intake(
        self,
        trigger: CorrectionTrigger,
        *,
        parent_correction_id: str | None = None,
        triggering_budget: Any | None = None,
    ) -> CorrectionOpenResult | None:
        """Main intake path. Dedups, checks bounds, opens scope, or
        records refusal. Returns None on dedup; otherwise the result.
        """
        # 1. persist the trigger (idempotent).
        self.store.insert_trigger(trigger)
        obs.trigger_received(
            trigger_id=trigger.trigger_id,
            source=trigger.source.value,
            scope_id=trigger.scope_id,
            failure_class_hint=trigger.failure_class_hint,
        )

        # 2. dedup gate (CR6).
        if trigger.dedup_key:
            reserved = self.store.try_reserve_dedup(
                trigger.dedup_key,
                trigger.trigger_id,
                self.config.dedup_ttl_seconds,
            )
            if not reserved:
                obs.trigger_deduplicated(
                    trigger_id=trigger.trigger_id,
                    dedup_key=trigger.dedup_key,
                    source=trigger.source.value,
                )
                return None

        # 3. derive failure class. Order: explicit hint, then scope_id,
        #    then source, then "unknown". The class is the key for
        #    same-class cascade detection.
        failure_class = (
            trigger.failure_class_hint
            or f"scope:{trigger.scope_id}"
            if trigger.scope_id
            else trigger.source.value
        )

        # 4. depth cap (CR15).
        depth_trip = depth_cap_check(
            parent_correction_id=parent_correction_id,
            store=self.store,
            config=self.config,
        )
        if depth_trip is not None:
            return await self._refuse_and_escalate_depth(
                trigger=trigger,
                failure_class=failure_class,
                parent_correction_id=parent_correction_id,
                depth=depth_trip.depth,
            )

        # 5. same-class cascade (CR16).
        cascade_trip = same_class_cascade_check(
            failure_class=failure_class,
            store=self.store,
            config=self.config,
        )
        if cascade_trip is not None:
            return await self._refuse_and_escalate_cascade(
                trigger=trigger,
                failure_class=failure_class,
                parent_correction_id=parent_correction_id,
                window_count=cascade_trip.window_count,
            )

        # 6. open a correction scope via standard activate path (CR14).
        return await self._open_correction_scope(
            trigger=trigger,
            failure_class=failure_class,
            parent_correction_id=parent_correction_id,
            triggering_budget=triggering_budget,
        )

    async def _open_correction_scope(
        self,
        *,
        trigger: CorrectionTrigger,
        failure_class: str,
        parent_correction_id: str | None,
        triggering_budget: Any | None,
    ) -> CorrectionOpenResult:
        episode_id = f"ep-{uuid.uuid4()}"

        # Build the spec — refuses irreversible at the builder (CR11).
        spec = build_correction_spec(
            trigger,
            failure_class=failure_class,
            triggering_budget=triggering_budget,
            config=self.config,
        )

        correction_scope_id = f"scope-correction-{uuid.uuid4()}"

        # Create the scope in the runtime BEFORE activating (so the
        # spec resolver can find it). We do this via the injected
        # create_scope_fn.
        if self.create_scope_fn is not None:
            await self.create_scope_fn(
                spec=spec,
                scope_id=correction_scope_id,
            )

        # Register compensation binding BEFORE activation (CR13). The
        # reversibility gate requires a compensatable scope to have a
        # binding; absent one the gate raises -32050.
        if self.register_compensation_fn is not None:
            await self.register_compensation_fn(
                {
                    "scope_id": correction_scope_id,
                    "handle": "self_correction.revert_structural_remedy",
                    "description": (
                        "Reverts the StructuralRemedyApplied record "
                        "from episode's correction_episode_records."
                    ),
                    "registered_by": "self_correction",
                }
            )

        # Persist episode before activation so bounds can see it if a
        # child trigger fires synchronously during the scope's life.
        ep = CorrectionEpisode(
            episode_id=episode_id,
            trigger_id=trigger.trigger_id,
            correction_scope_id=correction_scope_id,
            parent_correction_id=parent_correction_id,
            failure_class=failure_class,
            state=EpisodeState.running,
        )
        self.store.insert_episode(ep)
        self._scopes_to_episodes[correction_scope_id] = episode_id

        # Activate via the three-gate chain (CR14, CR18, CR19, CR20).
        if self.activate_fn is not None:
            try:
                await self.activate_fn({"scope_id": correction_scope_id})
            except ApplicationError as exc:
                if exc.code in _COST_REFUSAL_CODES:
                    # CR19: catch cost-refusal, mark refused, escalate.
                    return await self._refuse_and_escalate_cost(
                        episode_id=episode_id,
                        correction_scope_id=correction_scope_id,
                        error=exc,
                        failure_class=failure_class,
                    )
                # Non-cost refusals (safety -32040..-32049, reversibility
                # -32050..-32059) propagate per CR18: self-correction does
                # not bypass the gates. Mark the episode refused with the
                # structural reason; escalate via the same channel.
                self.store.update_episode_state(
                    episode_id,
                    EpisodeState.refused,
                    refusal_reason=f"gate_refused:{exc.code}:{exc}",
                )
                obs.episode_refused(
                    episode_id=episode_id,
                    reason="gate_refused",
                    code=exc.code,
                    details={"error_message": str(exc)},
                )
                raise

        obs.episode_opened(
            episode_id=episode_id,
            correction_scope_id=correction_scope_id,
            parent_correction_id=parent_correction_id,
            failure_class=failure_class,
        )
        return CorrectionOpenResult(
            episode_id=episode_id,
            state=EpisodeState.running,
            correction_scope_id=correction_scope_id,
        )

    # ---- record authoring (CR9, CR10) ------------------------------

    def record_part(
        self,
        *,
        episode_id: str,
        record_type: RecordType,
        payload: dict[str, Any],
    ) -> None:
        """Persist a record. Pydantic validation via the typed model
        happens in the IPC layer before this method sees the payload.
        """
        self.store.insert_record(
            episode_id=episode_id,
            record_type=record_type,
            payload=payload,
        )
        obs.record_part_persisted(
            episode_id=episode_id, record_type=record_type.value
        )

    # ---- completion (CR7, CR8) -------------------------------------

    async def request_complete(
        self,
        *,
        correction_scope_id: str,
        complete_fn: Callable[[str], Awaitable[Any]],
    ) -> None:
        """Run the four-part pre-check, then call `complete_fn`.

        `complete_fn` is typically `runtime.complete(scope_id)` — the
        caller injects it so this module stays decoupled from the
        runtime import.

        Raises -32070 on missing records; caller's `complete_fn` is
        NOT invoked on raise. The episode stays `running`; the caller
        may record the missing parts and retry.
        """
        self.completion_precheck.run_or_raise(
            correction_scope_id=correction_scope_id
        )
        await complete_fn(correction_scope_id)

        ep = self.store.get_episode_by_scope(correction_scope_id)
        if ep is not None:
            self.store.update_episode_state(
                ep.episode_id, EpisodeState.completed
            )
            obs.episode_closed(
                episode_id=ep.episode_id,
                correction_scope_id=correction_scope_id,
                failure_class=ep.failure_class,
                records_present=len(
                    self.store.record_types_for(ep.episode_id)
                ),
            )

    # ---- rollback compensation (CR13, CR20) -----------------------

    async def compensation_handler(
        self, *, scope_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Reverts the structural remedy from the episode's records.

        Invoked by reversibility's rollback runtime via the handler
        registered at scope construction. Deterministic — no LLM.
        """
        ep = self.store.get_episode_by_scope(scope_id)
        if ep is None:
            return {"ok": True, "scope_id": scope_id, "noop": True}
        records = self.store.list_records(ep.episode_id)
        remedy_records = [
            r
            for r in records
            if r["record_type"] == RecordType.structural_remedy.value
        ]
        # The handler's job is to describe the reversal; the actual
        # file-path reversal is performed by whoever authored the
        # remedy (they are the source of truth on what "revert" means
        # for a specific change). We return the payload so the
        # reversibility-runtime logs it in the rollback span.
        return {
            "ok": True,
            "scope_id": scope_id,
            "episode_id": ep.episode_id,
            "remedy_records": remedy_records,
        }

    # ---- refusal paths --------------------------------------------

    async def _refuse_and_escalate_depth(
        self,
        *,
        trigger: CorrectionTrigger,
        failure_class: str,
        parent_correction_id: str | None,
        depth: int,
    ) -> CorrectionOpenResult:
        episode_id = f"ep-{uuid.uuid4()}"
        ep = CorrectionEpisode(
            episode_id=episode_id,
            trigger_id=trigger.trigger_id,
            correction_scope_id=None,
            parent_correction_id=parent_correction_id,
            failure_class=failure_class,
            state=EpisodeState.escalated,
            refusal_reason="depth_cap",
        )
        self.store.insert_episode(ep)
        obs.cascade_escalated(
            kind="depth_cap",
            failure_class=failure_class,
            parent_correction_id=parent_correction_id,
            depth=depth,
            window_count=None,
        )
        if self.notifier is not None:
            await self.notifier.send(
                CorrectionNotification(
                    kind="cascade_depth",
                    text=render_cascade_depth_text(
                        episode_id=episode_id,
                        failure_class=failure_class,
                        depth=depth,
                        cap=self.config.depth_cap,
                    ),
                    episode_id=episode_id,
                    failure_class=failure_class,
                )
            )
        return CorrectionOpenResult(
            episode_id=episode_id,
            state=EpisodeState.escalated,
            correction_scope_id=None,
            refusal_reason="depth_cap",
        )

    async def _refuse_and_escalate_cascade(
        self,
        *,
        trigger: CorrectionTrigger,
        failure_class: str,
        parent_correction_id: str | None,
        window_count: int,
    ) -> CorrectionOpenResult:
        episode_id = f"ep-{uuid.uuid4()}"
        ep = CorrectionEpisode(
            episode_id=episode_id,
            trigger_id=trigger.trigger_id,
            correction_scope_id=None,
            parent_correction_id=parent_correction_id,
            failure_class=failure_class,
            state=EpisodeState.escalated,
            refusal_reason="same_class_cascade",
        )
        self.store.insert_episode(ep)
        obs.cascade_escalated(
            kind="same_class_cascade",
            failure_class=failure_class,
            parent_correction_id=parent_correction_id,
            depth=None,
            window_count=window_count,
        )
        if self.notifier is not None:
            await self.notifier.send(
                CorrectionNotification(
                    kind="cascade_same_class",
                    text=render_cascade_same_class_text(
                        failure_class=failure_class,
                        count=window_count,
                        window_seconds=self.config.cascade_window_seconds,
                    ),
                    episode_id=episode_id,
                    failure_class=failure_class,
                )
            )
        return CorrectionOpenResult(
            episode_id=episode_id,
            state=EpisodeState.escalated,
            correction_scope_id=None,
            refusal_reason="same_class_cascade",
        )

    async def _refuse_and_escalate_cost(
        self,
        *,
        episode_id: str,
        correction_scope_id: str,
        error: ApplicationError,
        failure_class: str,
    ) -> CorrectionOpenResult:
        self.store.update_episode_state(
            episode_id,
            EpisodeState.refused,
            refusal_reason=f"cost_ceiling:{error.code}:{error}",
        )
        obs.cost_refusal_caught(
            episode_id=episode_id,
            code=error.code,
            message=str(error),
        )
        if self.notifier is not None:
            await self.notifier.send(
                CorrectionNotification(
                    kind="cost_refusal",
                    text=render_cost_refusal_text(
                        episode_id=episode_id,
                        code=error.code,
                        message=str(error),
                    ),
                    episode_id=episode_id,
                    failure_class=failure_class,
                )
            )
        return CorrectionOpenResult(
            episode_id=episode_id,
            state=EpisodeState.refused,
            correction_scope_id=correction_scope_id,
            refusal_reason=f"cost_ceiling:{error.code}",
        )

    # ---- IPC gate for user_reported (ruling #4) -------------------

    def authorize_user_report_caller(self, reporter: str) -> None:
        """Caller-identity enforcement at the IPC boundary.

        Raises ApplicationError(-32602) if the reporter is not on the
        primary-persona allowlist. Empty allowlist means reject all —
        fail-closed. Workspaces wire the allowlist at bootstrap.
        """
        if reporter not in self.allowed_user_report_callers:
            raise ApplicationError(
                -32602,
                f"caller {reporter!r} is not a primary persona; "
                f"correction.user_reported is primary-persona-only "
                f"(ruling #4)",
                data={
                    "reporter": reporter,
                    "allowed": sorted(self.allowed_user_report_callers),
                },
            )

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

"""DegradationComponent — the composed runtime.

Wires:

    DegradationDetector     (FSMs + detection rubrics)  — D2 + D3
    PolicyDispatcher        (P1/P2/P3/P4)                — D4
    DegradationNotifier     (one-on-one channel)         — D5
    NarrativeRenderer       (Claude-authored / template) — D6
    ResumeManager           (auto / gated)               — D7
    DegradationStore        (SQLite)                     — D8
    OTel emission                                        — D9

The component is constructed alongside the sealed orchestrator — see
the integration notes in docs/architecture.md. It does not amend the
orchestrator; it uses only the `pause_activation` / `resume_activation`
hooks and the ScopeRuntime's public API.

Clock-injectable for time-compressed simulation; no real wall-clock
awaits anywhere.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from . import observability as obs
from .adapter import AdapterEvent, ClaudeClient
from .config import DegradationConfig
from .detection import DegradationDetector
from .errors import DegradationSignal
from .fsm import DegradationMode, FSMState, FSMTransition
from .notification import (
    DegradationNotification,
    DegradationNotifier,
    NarrativeRenderer,
    NotificationTier,
    ThresholdEvaluator,
    ThresholdTrigger,
    tier_for_mode,
)
from .policy import (
    OrchestratorHooks,
    Policy,
    PolicyDispatcher,
    ScopeRuntimeLike,
    build_defaults_from_config,
    scope_has_user_relevant_escalation,
)
from .state import (
    DegradationStore,
    FSMStateRow as FSMStateRowDB,
    ReconciliationPlan,
    reconcile,
)


# ---- active-episode in-memory record ----------------------------------


@dataclass
class ActiveEpisode:
    episode_id: str
    mode: DegradationMode
    signal: str
    policy: Policy
    started_at: float  # clock()
    paused_scope_ids: list[str] = field(default_factory=list)
    failed_scope_ids: list[str] = field(default_factory=list)
    notification_sent: bool = False
    resume_notification_sent: bool = False
    threshold_trigger: ThresholdTrigger | None = None
    last_user_relevant_check: float = 0.0

    def elapsed(self, now: float) -> float:
        return now - self.started_at


# ---- DegradationComponent ---------------------------------------------


@dataclass
class DegradationComponent:
    """Composed runtime."""

    cfg: DegradationConfig
    detector: DegradationDetector
    notifier: DegradationNotifier
    narrative: NarrativeRenderer
    dispatcher: PolicyDispatcher
    store: DegradationStore
    threshold: ThresholdEvaluator
    orchestrator: OrchestratorHooks
    scope_runtime: ScopeRuntimeLike
    clock: Callable[[], float] = field(default=time.monotonic)
    client: ClaudeClient | None = None

    active_episodes: dict[DegradationMode, ActiveEpisode] = field(default_factory=dict)
    _user_initiated_probe: dict[DegradationMode, bool] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        cfg: DegradationConfig,
        orchestrator: OrchestratorHooks,
        scope_runtime: ScopeRuntimeLike,
        notifier: DegradationNotifier,
        client: ClaudeClient | None = None,
        clock: Callable[[], float] | None = None,
        store: DegradationStore | None = None,
    ) -> "DegradationComponent":
        clk = clock or time.monotonic
        if store is None:
            store = DegradationStore(cfg.sqlite_path())
        detector = DegradationDetector.from_config(cfg, clock=clk)
        dispatcher = PolicyDispatcher(
            orchestrator=orchestrator,
            scope_runtime=scope_runtime,
            defaults=build_defaults_from_config(cfg),
        )
        narrative = NarrativeRenderer(cfg=cfg, client=client)
        threshold = ThresholdEvaluator(cfg=cfg)
        comp = cls(
            cfg=cfg,
            detector=detector,
            notifier=notifier,
            narrative=narrative,
            dispatcher=dispatcher,
            store=store,
            threshold=threshold,
            orchestrator=orchestrator,
            scope_runtime=scope_runtime,
            clock=clk,
            client=client,
        )
        # Wire the detector's transition callback to our handler.
        detector.on_transition = comp._on_transition
        if client is not None:
            client.on_event = comp._on_adapter_event
        return comp

    # ---- adapter event handler (detection feed) ----------------------

    async def _on_adapter_event(self, event: AdapterEvent) -> None:
        """Called by the ClaudeClient for every call. Records to store
        and forwards to the detector."""
        try:
            self.store.append_detection_event(
                mode=(event.signal.value if event.signal is not None else "ok"),
                signal=(event.signal.value if event.signal is not None else "ok"),
                ok=event.ok,
                call_id=event.call_id,
                prompt_name=event.prompt_name,
                latency_seconds=event.latency_seconds,
                status_code=event.status_code,
                retry_after=event.retry_after,
            )
        except Exception:
            # Persistence failures never block detection.
            pass
        await self.detector.record_event(event)

    # ---- scope-event handler (pyee subscription fallback) -----------

    async def on_scope_event(self, scope_event: Any) -> None:
        """Subscribed via ScopeRuntime.subscribe_all. Looks for
        scope_failed / trigger_fired with Claude-related reasons and
        synthesises an AdapterEvent so memory-system failures can
        still drive detection."""
        et = getattr(scope_event, "event_type", "") or type(scope_event).__name__
        # Only look at scope-failure-shaped events.
        if "fail" not in et.lower() and "fault" not in et.lower():
            return
        reason = getattr(scope_event, "reason", None) or ""
        sid = getattr(scope_event, "scope_id", "") or ""
        if not reason:
            return
        await self.detector.record_scope_fail(
            scope_id=sid, reason=reason, now=self.clock()
        )

    # ---- transition handler -----------------------------------------

    async def _on_transition(self, transition: FSMTransition) -> None:
        """Called by the detector when any FSM transitions state."""
        self._persist_fsm_state(transition.mode)
        if transition.to_state == FSMState.open:
            await self._enter_open(transition)
        elif transition.to_state == FSMState.gated:
            await self._enter_gated(transition)
        elif transition.to_state == FSMState.closed:
            await self._enter_closed(transition)
        elif transition.to_state == FSMState.half_open:
            await self._enter_half_open(transition)

    async def _enter_open(self, transition: FSMTransition) -> None:
        mode = transition.mode
        if mode in self.active_episodes:
            return
        signal = transition.trigger.split(":", 1)[1] if ":" in transition.trigger else transition.trigger
        episode_id = f"deg-{uuid.uuid4()}"
        app = await self.dispatcher.apply(
            mode=mode, episode_id=episode_id, signal=signal
        )
        self.store.create_episode(
            episode_id=episode_id,
            mode=mode.value,
            signal=signal,
            policy=app.policy.value,
            paused_scope_ids=app.paused_scope_ids,
            failed_scope_ids=app.failed_scope_ids,
        )
        ep = ActiveEpisode(
            episode_id=episode_id,
            mode=mode,
            signal=signal,
            policy=app.policy,
            started_at=self.clock(),
            paused_scope_ids=list(app.paused_scope_ids),
            failed_scope_ids=list(app.failed_scope_ids),
        )
        self.active_episodes[mode] = ep
        obs.episode_started(
            episode_id=episode_id,
            signal=signal,
            policy=app.policy.value,
            paused_scope_ids=app.paused_scope_ids,
            mode=mode.value,
        )
        # Auth-broken fires Tier 1 immediately.
        if mode == DegradationMode.auth_broken:
            await self._maybe_fire_notification(ep, force=True)

    async def _enter_gated(self, transition: FSMTransition) -> None:
        # Auth-broken goes straight to gated on trip; other modes may
        # enter gated via long-dwell or explicit request. If a new
        # episode doesn't exist yet, create one now.
        mode = transition.mode
        if mode not in self.active_episodes:
            await self._enter_open(transition)
            # Force notification if auth_broken.
            ep = self.active_episodes.get(mode)
            if ep is not None:
                await self._maybe_fire_notification(ep, force=True)

    async def _enter_half_open(self, transition: FSMTransition) -> None:
        # Probe call — only if we have a client.
        if self.client is None:
            return
        attempt = 1
        probe = await self.client.probe(timeout=self.cfg.narrative.timeout_seconds)
        obs.probe_call(
            mode=transition.mode.value,
            result="ok" if probe.ok else "fail",
            attempt_n=attempt,
            latency_seconds=probe.latency_seconds,
        )
        # Feed the probe result DIRECTLY into the specific mode's FSM.
        # Going through the detector would broadcast to all modes and
        # apply normal classification — not what we want for a probe
        # attributed to a single FSM.
        fsm = self.detector.fsms[transition.mode]
        if probe.ok:
            t = fsm.record_success(now=self.clock())
        else:
            # Feed a signal the mode accepts to invalidate the probe.
            signal_to_use: DegradationSignal | None = probe.signal
            if signal_to_use is None or signal_to_use not in fsm.accepted_signals:
                # Use the first accepted signal as a marker.
                signal_to_use = (
                    fsm.accepted_signals[0]
                    if fsm.accepted_signals
                    else DegradationSignal.connection_error
                )
            t = fsm.record_failure(signal_to_use, now=self.clock())
        if t is not None:
            await self._on_transition(t)

    async def _enter_closed(self, transition: FSMTransition) -> None:
        """Mode recovered. Apply resume policy for its active episode."""
        mode = transition.mode
        ep = self.active_episodes.get(mode)
        if ep is None:
            return
        elapsed = ep.elapsed(self.clock())
        # Gate on long-dwell: force gated instead of closed.
        # Exception: if transition's trigger is a user-initiated probe,
        # the user already confirmed — long-dwell gate is skipped.
        user_initiated = (
            "user" in (transition.trigger or "")
            or self._user_initiated_probe.get(mode, False)
        )
        if elapsed >= self.cfg.resume.user_confirm_after_seconds and not user_initiated:
            # Re-gate the FSM (closed → gated) — user must confirm.
            fsm = self.detector.fsms[mode]
            fsm.force_gated("long_dwell_gate")
            # Re-send notification to indicate gate.
            ep.threshold_trigger = ThresholdTrigger.time
            await self._maybe_fire_notification(ep, force=True)
            return
        # Auto-resume if mode qualifies OR user just confirmed.
        if (
            mode.value not in self.cfg.resume.auto_resume_modes
            and not user_initiated
        ):
            # Gated mode (auth_broken) should never reach closed
            # without user_resume; if it does via a bug, still require
            # user confirmation by keeping the episode active.
            return
        # Clear the user-initiated flag for this mode.
        self._user_initiated_probe[mode] = False
        await self._auto_resume(ep)

    async def _auto_resume(self, ep: ActiveEpisode) -> None:
        resumed = await self.dispatcher.release(
            mode=ep.mode,
            episode_id=ep.episode_id,
            paused_scope_ids=ep.paused_scope_ids,
        )
        self.store.resolve_episode(
            episode_id=ep.episode_id, resolution_kind="auto"
        )
        duration = ep.elapsed(self.clock())
        obs.episode_resolved(
            episode_id=ep.episode_id,
            duration_seconds=duration,
            resolution_kind="auto",
            resumed_scope_count=len(resumed),
        )
        # Resume notification (always, per Luke's decision).
        text = self.narrative.render_recovery(
            episode_id=ep.episode_id,
            resumed_count=len(resumed),
            duration_seconds=duration,
        )
        notif = DegradationNotification(
            episode_id=ep.episode_id,
            tier=NotificationTier.tier_2,
            threshold_triggered=ep.threshold_trigger or ThresholdTrigger.time,
            text=text,
            kind="resume",
        )
        if ep.notification_sent and not ep.resume_notification_sent:
            await self.notifier.send(notif)
            ep.resume_notification_sent = True
            self.store.set_episode_notification(
                episode_id=ep.episode_id,
                threshold=(ep.threshold_trigger.value if ep.threshold_trigger else "time"),
                kind="resume",
            )
        del self.active_episodes[ep.mode]

    async def user_confirm_resume(self, mode: DegradationMode) -> bool:
        """User explicit resume (for gated episodes)."""
        ep = self.active_episodes.get(mode)
        if ep is None:
            return False
        fsm = self.detector.fsms[mode]
        fsm.user_resume()
        self._user_initiated_probe[mode] = True
        # Probe fires through the standard half-open handler.
        await self._enter_half_open(
            FSMTransition(
                mode=mode,
                from_state=FSMState.gated,
                to_state=FSMState.half_open,
                trigger="user_resume",
                at=self.clock(),
            )
        )
        return True

    # ---- notification threshold check ------------------------------

    async def tick(self) -> None:
        """Periodic tick: advance dwelled FSMs and re-evaluate
        notification thresholds."""
        await self.detector.tick(now=self.clock())
        now = self.clock()
        for ep in list(self.active_episodes.values()):
            await self._maybe_fire_notification(ep)
        # Refresh FSM state cache on tick.
        for mode in DegradationMode:
            self._persist_fsm_state(mode)

    async def _maybe_fire_notification(
        self, ep: ActiveEpisode, *, force: bool = False
    ) -> None:
        if ep.notification_sent and not force:
            # Dedup per episode; only fire once for the "alert" kind.
            return
        now = self.clock()
        any_user_relevant = self._any_paused_scope_user_relevant(ep)
        trigger = self.threshold.evaluate(
            mode=ep.mode,
            episode_started_at=ep.started_at,
            now=now,
            paused_scope_count=len(ep.paused_scope_ids)
            + len(ep.failed_scope_ids),
            any_user_relevant_scope=any_user_relevant,
        )
        if trigger is None and not force:
            return
        if trigger is None:
            trigger = ThresholdTrigger.auth_broken
        ep.threshold_trigger = trigger
        tier = tier_for_mode(self.cfg, ep.mode)
        text = await self.narrative.render_alert(
            episode_id=ep.episode_id,
            mode=ep.mode,
            signal=ep.signal,
            policy=ep.policy.value,
            paused_scope_count=len(ep.paused_scope_ids)
            + len(ep.failed_scope_ids),
        )
        notif = DegradationNotification(
            episode_id=ep.episode_id,
            tier=tier,
            threshold_triggered=trigger,
            text=text,
            kind="alert",
        )
        delivered = await self.notifier.send(notif)
        ep.notification_sent = True
        if delivered:
            self.store.set_episode_notification(
                episode_id=ep.episode_id,
                threshold=trigger.value,
                kind="alert",
            )

    def _any_paused_scope_user_relevant(self, ep: ActiveEpisode) -> bool:
        for sid in ep.paused_scope_ids:
            scope = None
            # Amendment #20 — Site 6: replace silent continue with an
            # emitter. A lookup failure that silently drops one scope
            # from the user-relevance check could suppress notifications
            # for a user-relevant episode.
            try:
                scope = self.scope_runtime.get(sid)  # type: ignore[attr-defined]
            except Exception as e:
                obs.scope_lookup_failed(
                    episode_id=ep.episode_id,
                    scope_id=sid,
                    exception_class=type(e).__name__,
                )
                continue
            if scope is not None and scope_has_user_relevant_escalation(scope):
                return True
        return False

    # ---- fsm persistence --------------------------------------------

    def _persist_fsm_state(self, mode: DegradationMode) -> None:
        fsm = self.detector.fsms[mode]
        from datetime import datetime, timezone

        self.store.upsert_fsm_state(
            FSMStateRowDB(
                mode=mode.value,
                state=fsm.state.value,
                state_entered_at=fsm.state_entered_at,
                retry_after_until=getattr(fsm, "retry_after_until", None),
                consecutive_probe_successes=fsm.consecutive_probe_successes,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    # ---- restart reconciliation -------------------------------------

    async def reconcile_on_startup(self, *, orchestrator_paused: bool) -> ReconciliationPlan:
        """Run cross-state reconciliation. Called once at component
        startup."""
        unresolved = self.store.unresolved_episodes()
        plan = reconcile(
            orchestrator_paused=orchestrator_paused,
            unresolved_episodes=unresolved,
        )
        if plan.case == 3 and plan.should_call_resume_activation:
            self.orchestrator.resume_activation()
            # Mark the episode resolved with the restart tag.
            if plan.active_episode_id is not None:
                self.store.resolve_episode(
                    episode_id=plan.active_episode_id,
                    resolution_kind="reconciled_on_restart",
                )
        if plan.case == 2:
            # Orchestrator paused but no active episode — create a
            # recovered shell so we can probe recovery.
            episode_id = f"deg-recovered-{uuid.uuid4()}"
            self.store.create_episode(
                episode_id=episode_id,
                mode="down",
                signal="restart_detected",
                policy="pause_all",
                paused_scope_ids=[],
            )
        if plan.case == 1 and plan.active_episode_id is not None:
            # Rebuild the active-episode in-memory record from the
            # stored row.
            ep_row = self.store.get_episode(plan.active_episode_id)
            if ep_row is not None:
                # Amendment #20 — Site 7: replace silent ValueError
                # pass with an emitter. A stored mode/policy value
                # that no longer maps to an enum (schema drift across
                # restarts) is dropped from the in-memory rebuild; the
                # span surfaces the drop so an operator sees it.
                try:
                    mode = DegradationMode(ep_row.mode)
                    policy = Policy(ep_row.policy)
                    self.active_episodes[mode] = ActiveEpisode(
                        episode_id=ep_row.episode_id,
                        mode=mode,
                        signal=ep_row.signal,
                        policy=policy,
                        started_at=self.clock(),  # re-anchor to current clock
                        paused_scope_ids=list(ep_row.paused_scope_ids),
                        failed_scope_ids=list(ep_row.failed_scope_ids),
                        notification_sent=ep_row.notification_sent_at is not None,
                    )
                except ValueError as e:
                    obs.reconcile_restore_failed(
                        episode_id=ep_row.episode_id,
                        mode_value=ep_row.mode,
                        policy_value=ep_row.policy,
                        exception_class=type(e).__name__,
                    )
        return plan

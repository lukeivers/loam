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

"""Four detection surfaces normalised to CorrectionTrigger.

Sources:
  1. scope_failure   — pyee subscription on ScopeRuntime.emitter.on("*")
                        filtered to StateTransitioned(to_state=failed)
  2. otel_anomaly    — polling aggregator QueryAPI.find_spans(...)
  3. review_verdict  — IPC correction.report_review_verdict
  4. user_reported   — IPC correction.user_reported (primary-persona only)

Gate-refusal exclusion (Eve-inference #1 — CHALLENGED; kept defensive):

The three sealed gates (safety, reversibility, cost) refuse by raising
`ApplicationError` BEFORE the scope's `orig_activate` runs. A
gate-refused activation therefore never emits a
`StateTransitioned(to_state=failed)` event — the scope is still in
`proposed` state when the IPC call returns the error. The exclusion
pattern in the proposal (§4.1 CR2) is therefore defensive-only: it
handles the case where external code catches an `ApplicationError` and
manually calls `runtime.fail(scope_id, reason="safety-gate/...")`. We
keep the exclusion prefixes because:

  - the regex cost is negligible;
  - future gate integrations may emit state transitions directly;
  - absent exclusion, a manual `.fail("cost-ceiling/...")` would
    recurse the corrector on its own gate.

See `gate_refusal_prefixes.md` in the brief and the challenge notes in
the return summary.
"""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any, Awaitable, Callable

from . import observability as obs
from .dedup import make_dedup_key, normalise_reason
from .spec import CorrectionTrigger, TriggerSource


GATE_REFUSAL_REASON_PATTERN = re.compile(
    r"^(safety-gate/|cost-ceiling/|reversibility-gate/)"
)


TriggerHandler = Callable[[CorrectionTrigger], Awaitable[None]]


def build_trigger_from_state_transitioned(
    *, event: Any
) -> CorrectionTrigger | None:
    """Normalise a `StateTransitioned` event into a CorrectionTrigger.

    Returns None if the event is not an eligible failure.
    """
    # Duck-type against the scope-of-work event. We import lazily to
    # avoid a hard dependency in modules that never see events.
    from loam.scope_of_work import ScopeState

    to_state = getattr(event, "to_state", None)
    if to_state != ScopeState.failed:
        return None

    reason = getattr(event, "reason", None) or ""
    if GATE_REFUSAL_REASON_PATTERN.match(reason):
        return None

    scope_id = getattr(event, "scope_id", None)
    trace_id = getattr(event, "otel_trace_id", None)
    normalised = normalise_reason(reason)
    dedup_key = make_dedup_key(
        scope_id=scope_id,
        source=TriggerSource.scope_failure.value,
        normalised_reason=normalised,
    )
    return CorrectionTrigger(
        trigger_id=f"tr-{uuid.uuid4()}",
        source=TriggerSource.scope_failure,
        scope_id=scope_id,
        trace_id=trace_id,
        failure_class_hint=normalised or None,
        raw_payload={"reason": reason},
        dedup_key=dedup_key,
    )


def build_trigger_from_span(*, span: Any) -> CorrectionTrigger:
    """Normalise an aggregator SpanRecord into a CorrectionTrigger."""
    scope_id = None
    # Amendment #20 — Site 1: replace silent pass with an emitter. A
    # failed scope-id extraction breaks downstream dedup (two real
    # failures on the same scope would dedup as distinct triggers);
    # the emitter surfaces the degradation instead of hiding it.
    try:
        scope_id = span.attributes.get("loam.scope.id")
    except Exception as e:
        obs.span_attribute_lookup_failed(
            trigger_source=TriggerSource.otel_anomaly.value,
            attribute_name="loam.scope.id",
            exception_class=type(e).__name__,
        )
    name = getattr(span, "name", "") or ""
    status_message = getattr(span, "status_message", None) or ""
    normalised = normalise_reason(f"{name}:{status_message}")
    dedup_key = make_dedup_key(
        scope_id=scope_id,
        source=TriggerSource.otel_anomaly.value,
        normalised_reason=normalised,
    )
    return CorrectionTrigger(
        trigger_id=f"tr-{uuid.uuid4()}",
        source=TriggerSource.otel_anomaly,
        scope_id=scope_id,
        trace_id=getattr(span, "trace_id", None),
        failure_class_hint=name or None,
        raw_payload={
            "span_id": getattr(span, "span_id", None),
            "name": name,
            "status": getattr(span, "status", None),
            "status_message": status_message,
            "retention_class": (
                span.retention_class.value
                if hasattr(span, "retention_class")
                and hasattr(span.retention_class, "value")
                else None
            ),
        },
        dedup_key=dedup_key,
    )


def build_trigger_from_review_verdict(
    *,
    scope_id: str,
    verdict: str,
    reasons: list[str] | None,
    reporter: str,
) -> CorrectionTrigger | None:
    """Build a CorrectionTrigger from a review verdict.

    Per ruling #1: only `verdict == "fail"` fires a trigger.
    """
    if verdict != "fail":
        return None
    normalised = normalise_reason(";".join(reasons or []))
    dedup_key = make_dedup_key(
        scope_id=scope_id,
        source=TriggerSource.review_verdict.value,
        normalised_reason=normalised,
    )
    return CorrectionTrigger(
        trigger_id=f"tr-{uuid.uuid4()}",
        source=TriggerSource.review_verdict,
        scope_id=scope_id,
        trace_id=None,
        failure_class_hint="review_verdict_fail",
        raw_payload={
            "verdict": verdict,
            "reasons": list(reasons or []),
            "reporter": reporter,
        },
        reporter=reporter,
        dedup_key=dedup_key,
    )


def build_trigger_from_user_report(
    *,
    description: str,
    related_scope_id: str | None,
    reporter: str,
) -> CorrectionTrigger:
    """Build a CorrectionTrigger from a user-report IPC call.

    Caller identity is enforced upstream (ruling #4) — the IPC wiring
    only hands control here when `reporter` is a primary-persona
    identifier.
    """
    normalised = normalise_reason(description)
    dedup_key = make_dedup_key(
        scope_id=related_scope_id,
        source=TriggerSource.user_reported.value,
        normalised_reason=normalised,
    )
    return CorrectionTrigger(
        trigger_id=f"tr-{uuid.uuid4()}",
        source=TriggerSource.user_reported,
        scope_id=related_scope_id,
        trace_id=None,
        failure_class_hint="user_reported",
        raw_payload={"description": description, "reporter": reporter},
        reporter=reporter,
        dedup_key=dedup_key,
    )


class ScopeFailurePyeeSubscriber:
    """Subscribes to ScopeRuntime.emitter.on('*') and routes eligible
    `StateTransitioned(failed)` events to the correction controller.

    Ignores gate-refusal reason prefixes (defensive — see module docstring).
    """

    def __init__(self, *, handler: TriggerHandler) -> None:
        self._handler = handler

    def subscribe(self, scope_runtime: Any) -> None:
        scope_runtime.emitter.on("*", self._on_event)

    def _on_event(self, event: Any) -> None:
        trigger = build_trigger_from_state_transitioned(event=event)
        if trigger is None:
            return
        # pyee handlers may run sync or async; schedule the async
        # handler on the running loop when one exists, else run it
        # synchronously. Mirrors the cost-governance _fire_notification
        # pattern.
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._handler(trigger))
        except RuntimeError:
            asyncio.run(self._handler(trigger))


class OTelAnomalyPoller:
    """Polls the aggregator for anomaly spans and routes them.

    Anomaly predicate (ruling #2): `status == "ERROR"` AND
    `retention_class == NORMAL`.

    CHALLENGE to Eve-inference / ruling literal: the aggregator's
    `RetentionClass` enum is `NORMAL | DERIVED_ONLY | EPHEMERAL` —
    there is no `high` value. We map Luke's `"high"` directive to
    `NORMAL` (the full-fidelity class; lower classes are sampled /
    reduced). Documented in the return summary.
    """

    def __init__(
        self,
        *,
        query_api: Any,
        handler: TriggerHandler,
        poll_interval_seconds: int,
    ) -> None:
        self._query_api = query_api
        self._handler = handler
        self._interval = poll_interval_seconds
        self._seen_span_ids: set[str] = set()
        self._stopped = asyncio.Event()

    async def run_forever(self) -> None:
        while not self._stopped.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(
                    self._stopped.wait(), timeout=self._interval
                )
            except asyncio.TimeoutError:
                # Amendment #20 — Site 2: timeout here IS the intended
                # sleep-with-early-wake control flow (the alternate branch
                # means _stopped was set). Emit a liveness span so the
                # poll cadence is observable; keep the `continue`.
                obs.poll_tick(
                    poller_name="otel_anomaly",
                    interval_seconds=self._interval,
                )
                continue

    def stop(self) -> None:
        self._stopped.set()

    async def run_once(self) -> int:
        """Single poll pass. Returns number of triggers dispatched."""
        spans = self._find_anomaly_spans()
        dispatched = 0
        for span in spans:
            span_id = getattr(span, "span_id", None)
            if span_id and span_id in self._seen_span_ids:
                continue
            if span_id:
                self._seen_span_ids.add(span_id)
            trigger = build_trigger_from_span(span=span)
            await self._handler(trigger)
            dispatched += 1
        return dispatched

    def _find_anomaly_spans(self) -> list[Any]:
        from loam.observability_aggregator.api import SpanFilter
        from loam.observability_aggregator.schema import RetentionClass

        flt = SpanFilter(
            status="ERROR",
            retention_class=RetentionClass.NORMAL,
        )
        return self._query_api.find_spans(flt, limit=200)

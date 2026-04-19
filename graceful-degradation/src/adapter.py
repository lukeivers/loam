"""`ClaudeClient` adapter (D1).

A thin wrapper around any async Claude-calling callable. Every pOS LLM
call that can be routed through it should be — including primary-
persona authoring, the monitor's stuck-reason pass, and the graceful-
degradation component's own narrative / judge / probe calls.

The adapter does not reimplement the SDK's retry loop. Per research
§1.3, the SDK should be configured with `max_retries=1` so the
degradation layer sees real failures quickly; this adapter does not
retry at all — it classifies, observes, and re-raises.

Shape:

    async def _invoke(model: str, prompt_name: str, text: str) -> str: ...
    client = ClaudeClient(
        invoke=_invoke,
        on_event=detector.record_event,   # optional observer callback
    )
    # All pOS LLM calls:
    text = await client.call(prompt_name="memory.extraction", text="...")

The `invoke` callable is workspace-supplied. In production a workspace
wires it to `anthropic.AsyncAnthropic().messages.create(...)`. In tests
the callable is replaced with a fake that scripts success/failure.

Memory-system's Graphiti client is not routable through this adapter
(it owns its own Anthropic client internally). That is a documented
detection blind spot; the degradation component compensates by
subscribing to scope-of-work's fail events via pyee (supplementary
signal). See docs/architecture.md §"Memory-system detection blind spot".

Active-probe interface: `client.probe(timeout=)` issues a known-good
minimal prompt ("respond with exactly the word OK") for use by the
half-open FSM. Probes are attributed to `degradation-probe` per v1.1
R12.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from . import observability as obs
from .errors import (
    ClaudeAPIError,
    DegradationSignal,
    classify_exception,
    is_non_degradation_signal,
)


# ---- types -------------------------------------------------------------


class ClaudeCallable(Protocol):
    """The async callable a workspace supplies to invoke Claude.

    Signature: `invoke(model, prompt_name, text, **kwargs) -> str`. The
    adapter does not care how the callable is implemented — it only
    requires that typed Anthropic SDK exceptions (or equivalents)
    propagate unchanged so `classify_exception` can route them.
    """

    async def __call__(
        self,
        *,
        model: str,
        prompt_name: str,
        text: str,
        **kwargs: Any,
    ) -> str: ...


@dataclass(frozen=True)
class LLMResult:
    """Adapter return value for a successful call."""

    text: str
    model: str
    prompt_name: str
    latency_seconds: float
    call_id: str


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of an active probe."""

    ok: bool
    latency_seconds: float
    signal: DegradationSignal | None = None
    cause: ClaudeAPIError | None = None
    timestamp: float = 0.0


# ---- adapter event (consumed by the detector) -------------------------


@dataclass(frozen=True)
class AdapterEvent:
    """Structured event the adapter emits for every call.

    `signal` is None on success; set to the classified DegradationSignal
    on failure. Consumed by `DegradationDetector.record_event`.
    """

    call_id: str
    prompt_name: str
    model: str
    ok: bool
    signal: DegradationSignal | None
    retry_after: float | None
    latency_seconds: float
    status_code: int | None
    timestamp: float


AdapterObserver = Callable[[AdapterEvent], Any]


# ---- ClaudeClient -----------------------------------------------------


@dataclass
class ClaudeClient:
    """Adapter wrapping any Claude-calling async callable.

    `invoke` is the underlying call. `on_event` is called after every
    invocation with an `AdapterEvent` — the detector's `record_event`
    method has the right shape.

    The adapter intentionally performs NO retries. The SDK's built-in
    retry loop is controlled by the workspace (recommended
    `max_retries=1`), and the degradation FSMs manage recovery via
    `probe()` during half-open states.

    `clock` is injectable for the time-compressed simulation tests.
    """

    invoke: ClaudeCallable
    on_event: AdapterObserver | None = None
    probe_model: str = "claude-haiku-4-5"
    probe_prompt: str = "Respond with exactly the single word OK."
    probe_prompt_name: str = "degradation-probe"
    default_model: str = "claude-haiku-4-5"
    clock: Callable[[], float] = field(default=time.monotonic)

    async def call(
        self,
        *,
        prompt_name: str,
        text: str,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Issue a Claude call via the underlying invoke callable.

        On success: emits a success AdapterEvent and returns LLMResult.
        On failure: classifies the exception, emits a failure
        AdapterEvent, re-raises the classified ClaudeAPIError.
        """
        resolved_model = model or self.default_model
        call_id = f"call-{uuid.uuid4()}"
        started = self.clock()
        with obs.adapter_span(
            prompt_name=prompt_name,
            model=resolved_model,
            call_id=call_id,
        ) as span:
            try:
                out = await self.invoke(
                    model=resolved_model,
                    prompt_name=prompt_name,
                    text=text,
                    **kwargs,
                )
            except Exception as raw_exc:  # noqa: BLE001
                # Classify and emit the failure event.
                err = classify_exception(raw_exc)
                latency = self.clock() - started
                event = AdapterEvent(
                    call_id=call_id,
                    prompt_name=prompt_name,
                    model=resolved_model,
                    ok=False,
                    signal=err.signal,
                    retry_after=err.retry_after,
                    latency_seconds=latency,
                    status_code=err.status_code,
                    timestamp=self.clock(),
                )
                obs.emit_adapter_event(span, event, error=err)
                await self._notify(event)
                # Re-raise as pOS-side error (callers expect typed
                # exceptions; bad_request and everything else carries
                # the original cause for debugging).
                raise err from raw_exc

            latency = self.clock() - started
            event = AdapterEvent(
                call_id=call_id,
                prompt_name=prompt_name,
                model=resolved_model,
                ok=True,
                signal=None,
                retry_after=None,
                latency_seconds=latency,
                status_code=200,
                timestamp=self.clock(),
            )
            obs.emit_adapter_event(span, event)
            await self._notify(event)
            return LLMResult(
                text=out,
                model=resolved_model,
                prompt_name=prompt_name,
                latency_seconds=latency,
                call_id=call_id,
            )

    async def probe(self, *, timeout: float | None = 5.0) -> ProbeResult:
        """Issue a minimal known-good prompt to test liveness.

        Used by FSMs in half-open state. Attributed to
        `degradation-probe` for v1.1 R12 cost aggregation.
        """
        started = self.clock()
        try:
            coro = self.call(
                prompt_name=self.probe_prompt_name,
                text=self.probe_prompt,
                model=self.probe_model,
            )
            if timeout is not None:
                out = await asyncio.wait_for(coro, timeout=timeout)
            else:
                out = await coro
        except ClaudeAPIError as err:
            return ProbeResult(
                ok=False,
                latency_seconds=self.clock() - started,
                signal=err.signal,
                cause=err,
                timestamp=self.clock(),
            )
        except asyncio.TimeoutError:
            return ProbeResult(
                ok=False,
                latency_seconds=self.clock() - started,
                signal=DegradationSignal.timeout,
                cause=None,
                timestamp=self.clock(),
            )
        return ProbeResult(
            ok=True,
            latency_seconds=out.latency_seconds,
            signal=None,
            cause=None,
            timestamp=self.clock(),
        )

    async def _notify(self, event: AdapterEvent) -> None:
        if self.on_event is None:
            return
        result = self.on_event(event)
        if asyncio.iscoroutine(result):
            await result

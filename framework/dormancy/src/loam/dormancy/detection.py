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

"""Detection rubrics (D3).

The six detectors from the research matrix with research-recommended
thresholds, all per-workspace-tunable via DegradationConfig.

The detector consumes `AdapterEvent`s from the ClaudeClient wrapper,
feeds them into the six mode FSMs, and emits transition events for the
policy layer to act on.

Garbage detection is a three-tier pipeline:

    tier 1: pydantic schema validation (if the caller declared a shape)
    tier 2: regex refusal / empty markers
    tier 3: LLM-judge (bounded to `judge_budget_per_hour` per config)

`GarbageJudge` is a Protocol so the concrete implementation is
workspace-supplied (it needs a ClaudeClient to call). The detector
manages the budget internally.
"""

from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Deque, Protocol

from pydantic import BaseModel, ValidationError

from . import observability as obs
from .adapter import AdapterEvent, ClaudeClient
from .config import DegradationConfig
from .errors import (
    ClaudeAPIError,
    DegradationSignal,
    GarbageResponseError,
)
from .fsm import (
    DegradationMode,
    FSMState,
    FSMTransition,
    LatencyFSM,
    ModeFSM,
    build_fsms,
)


# ---- garbage pipeline --------------------------------------------------


_REFUSAL_MARKERS = (
    "i can't help",
    "i cannot help",
    "i'm sorry, but i'm unable",
    "i am unable to",
    "i won't be able to",
    "i refuse",
)


def _regex_flags_garbage(text: str, *, min_chars: int = 1) -> bool:
    """True if the response looks like structurally empty / refusal.

    `min_chars` is a per-prompt floor; callers who know their output
    should be larger can pass a higher value (wired through
    `GarbageDetectionRequest` below).
    """
    stripped = (text or "").strip()
    if len(stripped) < min_chars:
        return True
    lowered = stripped.lower()
    for marker in _REFUSAL_MARKERS:
        if lowered.startswith(marker):
            return True
    return False


@dataclass
class GarbageDetectionRequest:
    """Caller-supplied context for judging a response.

    `expected_model`: pydantic BaseModel subclass the response should
        validate against, if the caller declared one. None disables the
        schema tier.
    `min_chars`: structural minimum length for the prompt type.
    `prompt_name`: attribution for the judge call (if tier-3 fires).
    `text`: the response to evaluate.
    """

    text: str
    prompt_name: str
    expected_model: type[BaseModel] | None = None
    min_chars: int = 1


class GarbageJudge(Protocol):
    """Workspace-supplied Claude-judge. Returns True if the response is
    "bad" per the judge prompt."""

    async def __call__(self, request: GarbageDetectionRequest) -> bool: ...


@dataclass
class GarbagePipeline:
    """Three-tier garbage classifier. Tracks the per-hour judge budget."""

    judge: GarbageJudge | None = None
    judge_budget_per_hour: int = 5
    clock: Callable[[], float] = field(default=time.monotonic)
    _judge_calls: Deque[float] = field(default_factory=deque)

    async def is_garbage(self, req: GarbageDetectionRequest) -> bool:
        # Tier 1: pydantic schema
        if req.expected_model is not None:
            try:
                req.expected_model.model_validate_json(req.text)
            except ValidationError:
                return True
            except Exception:
                # Non-JSON text but a model expected → garbage.
                return True
        # Tier 2: structural / refusal
        if _regex_flags_garbage(req.text, min_chars=req.min_chars):
            return True
        # Tier 3: LLM-judge (only if budget remains)
        if self.judge is None:
            return False
        now = self.clock()
        hour_ago = now - 3600.0
        while self._judge_calls and self._judge_calls[0] < hour_ago:
            self._judge_calls.popleft()
        if len(self._judge_calls) >= self.judge_budget_per_hour:
            # Budget exhausted — assume fine and emit a log event via
            # OTel so the operator can see it happened.
            with obs.operation_span(
                "loam.dormancy.judge_budget_exhausted",
                budget=self.judge_budget_per_hour,
            ):
                pass
            return False
        self._judge_calls.append(now)
        return await self.judge(req)


class PydanticJudge:
    """Simple judge wrapper — uses a ClaudeClient to ask a fixed
    is-this-garbage prompt and returns True on a "yes" verdict.

    Exposed as a concrete utility for workspaces; not required — any
    callable of shape `GarbageJudge` is acceptable.
    """

    def __init__(
        self,
        client: ClaudeClient,
        *,
        judge_prompt_name: str = "degradation-garbage-judge",
        judge_template: str = (
            "You are evaluating whether a language-model response is "
            "a reasonable completion of its prompt.\n"
            "Prompt name: {prompt_name}\n"
            "Response:\n---\n{text}\n---\n"
            "Respond with exactly one word: 'good' or 'bad'."
        ),
    ) -> None:
        self._client = client
        self._prompt_name = judge_prompt_name
        self._template = judge_template

    async def __call__(self, request: GarbageDetectionRequest) -> bool:
        prompt = self._template.format(
            prompt_name=request.prompt_name, text=request.text[:8000]
        )
        try:
            result = await self._client.call(
                prompt_name=self._prompt_name,
                text=prompt,
            )
        except ClaudeAPIError:
            # Judge unreachable → abstain from garbage verdict.
            return False
        verdict = (result.text or "").strip().lower()
        return verdict.startswith("bad")


# ---- detector ----------------------------------------------------------


@dataclass
class DegradationDetector:
    """Routes AdapterEvents into mode FSMs; reports transitions.

    `on_transition` is a callback invoked for every state transition
    (typically the policy dispatcher). Latency observations feed the
    LatencyFSM's rolling window.
    """

    cfg: DegradationConfig
    fsms: dict[DegradationMode, ModeFSM]
    on_transition: Callable[[FSMTransition], Awaitable[None]] | None = None
    clock: Callable[[], float] = field(default=time.monotonic)

    @classmethod
    def from_config(
        cls,
        cfg: DegradationConfig,
        *,
        clock: Callable[[], float] | None = None,
        on_transition: Callable[[FSMTransition], Awaitable[None]] | None = None,
    ) -> "DegradationDetector":
        clk = clock or time.monotonic
        return cls(
            cfg=cfg,
            fsms=build_fsms(cfg, clock=clk),
            on_transition=on_transition,
            clock=clk,
        )

    async def record_event(self, event: AdapterEvent) -> None:
        """Consume one AdapterEvent. Feeds the relevant FSM and the
        latency tracker."""
        # Always feed the latency FSM (advisory).
        latency_fsm = self.fsms[DegradationMode.latency_sustained]
        assert isinstance(latency_fsm, LatencyFSM)
        advisory = latency_fsm.observe_latency(event.latency_seconds)
        if advisory is not None and self.on_transition is not None:
            await self.on_transition(advisory)

        if event.ok:
            # Success: record into each FSM whose signals overlap.
            for fsm in self.fsms.values():
                if fsm.mode == DegradationMode.latency_sustained:
                    continue
                transition = fsm.record_success(now=event.timestamp)
                if transition is not None and self.on_transition is not None:
                    await self.on_transition(transition)
            return

        # Failure: route by signal to mode FSM(s).
        if event.signal is None:
            return
        for fsm in self.fsms.values():
            if event.signal not in fsm.accepted_signals:
                continue
            transition = fsm.record_failure(
                event.signal,
                retry_after=event.retry_after,
                now=event.timestamp,
            )
            if transition is not None and self.on_transition is not None:
                await self.on_transition(transition)

    async def record_scope_fail(
        self,
        *,
        scope_id: str,
        reason: str,
        now: float | None = None,
    ) -> None:
        """Supplementary signal: scope-of-work reported a scope failure
        with a Claude-related reason. Per research §6.b, this is the
        pyee-based fallback detection path for sealed components (like
        memory-system) that don't route through the adapter.

        Heuristic: if `reason` contains any of the failure-class
        markers, synthesize an AdapterEvent and feed the detector.
        """
        # Map common phrasings to signals.
        low = reason.lower()
        signal: DegradationSignal | None = None
        if "timeout" in low:
            signal = DegradationSignal.timeout
        elif "connection" in low or "unreachable" in low:
            signal = DegradationSignal.connection_error
        elif "rate" in low and "limit" in low:
            signal = DegradationSignal.rate_limited
        elif "overload" in low or "529" in low:
            signal = DegradationSignal.overloaded
        elif "401" in low or "authentication" in low or "auth" in low:
            signal = DegradationSignal.auth_broken
        elif "5xx" in low or "server error" in low or "500" in low or "503" in low:
            signal = DegradationSignal.server_error
        if signal is None:
            return
        event = AdapterEvent(
            call_id=f"scope-fail:{scope_id}",
            prompt_name="sealed-component-fail",
            model="unknown",
            ok=False,
            signal=signal,
            retry_after=None,
            latency_seconds=0.0,
            status_code=None,
            timestamp=self.clock() if now is None else now,
        )
        await self.record_event(event)

    async def record_supervisor_signal(
        self,
        *,
        signal: DegradationSignal,
        now: float | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> FSMTransition | None:
        """Consume a supervisor-emitted signal (Amendment 3 of
        hands-off-lifecycle).

        The hands-off-lifecycle supervisor probes the memory sidecar
        directly; on classified failure it calls this method with a
        ``memory_sidecar_down`` signal. On recovery it calls this with
        ``memory_sidecar_recovered`` which is routed through
        ``record_success`` on the memory_sidecar FSM so the mode
        returns to ``closed``.

        Complementary to the existing `ClaudeClient`-adapter-based
        detection — not replacing it. This closes the memory
        detection blind spot logged in architecture.md.
        """
        t = self.clock() if now is None else now
        fsm = self.fsms.get(DegradationMode.memory_sidecar)
        if fsm is None:
            return None
        if signal is DegradationSignal.memory_sidecar_recovered:
            transition = fsm.record_success(now=t)
        elif signal is DegradationSignal.memory_sidecar_down:
            transition = fsm.record_failure(signal, now=t)
        else:
            # Ignore signals this mode does not consume.
            return None
        if transition is not None and self.on_transition is not None:
            await self.on_transition(transition)
        return transition

    async def tick(self, now: float | None = None) -> list[FSMTransition]:
        """Clock-driven pass — moves dwelled FSMs to half_open."""
        out: list[FSMTransition] = []
        for fsm in self.fsms.values():
            t = fsm.tick(now=now)
            if t is not None:
                out.append(t)
                if self.on_transition is not None:
                    await self.on_transition(t)
        return out

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

"""Test fakes for graceful-degradation tests.

FakeClaudeClient: scripted sequence of successes/failures by call index.
FakeClock: manually-advanced monotonic clock for time-compressed tests.
FakeOrchestrator: records pause_activation / resume_activation calls.
FakeScopeRuntime: minimal stand-in; records pause/resume/fail calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


# ---- clock -----------------------------------------------------------


class FakeClock:
    """Monotonic clock that advances only on explicit advance()."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self._t = start

    def now(self) -> float:
        return self._t

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


# ---- fake orchestrator ----------------------------------------------


class FakeOrchestrator:
    def __init__(self) -> None:
        self.paused: bool = False
        self.paused_reason: str | None = None
        self.pause_calls: list[str] = []
        self.resume_calls: int = 0

    def pause_activation(self, reason: str) -> None:
        self.paused = True
        self.paused_reason = reason
        self.pause_calls.append(reason)

    def resume_activation(self) -> None:
        self.paused = False
        self.paused_reason = None
        self.resume_calls += 1


# ---- fake scope runtime ---------------------------------------------


@dataclass
class FakeScope:
    scope_id: str
    constraints: tuple[str, ...] = ()
    budget: Any = None
    escalation_triggers: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if self.budget is None:
            # Default: LLM-dependent (non-zero tokens)
            self.budget = type(
                "B",
                (),
                {"tokens": 10000, "money_cents": 100, "time_seconds": 3600},
            )()


class FakeScopeRuntime:
    def __init__(self) -> None:
        self._scopes: dict[str, FakeScope] = {}
        self.pause_calls: list[tuple[str, str | None]] = []
        self.resume_calls: list[str] = []
        self.fail_calls: list[tuple[str, str]] = []
        self.completed: set[str] = set()

    def add_scope(self, scope: FakeScope) -> None:
        self._scopes[scope.scope_id] = scope

    def get(self, scope_id: str) -> FakeScope | None:
        return self._scopes.get(scope_id)

    def list(self, *, states: Sequence[Any] | None = None, **kwargs: Any) -> list[FakeScope]:
        return [
            s
            for s in self._scopes.values()
            if s.scope_id not in self.completed
            and s.scope_id not in [c[0] for c in self.fail_calls]
        ]

    async def pause(self, scope_id: str, reason: str | None = None) -> FakeScope:
        self.pause_calls.append((scope_id, reason))
        return self._scopes[scope_id]

    async def resume(self, scope_id: str) -> FakeScope:
        self.resume_calls.append(scope_id)
        return self._scopes[scope_id]

    async def fail(self, scope_id: str, reason: str) -> FakeScope:
        self.fail_calls.append((scope_id, reason))
        return self._scopes[scope_id]


# ---- fake claude client underlying callable ------------------------


class FakeInvoker:
    """Scripted invoke callable for the ClaudeClient adapter.

    Takes a sequence of responses: each element is either a str (success
    text) or an Exception instance (failure). On each call, the next
    element is consumed. Beyond the sequence, `default` is used.
    """

    def __init__(
        self,
        script: Sequence[str | Exception],
        default: str | Exception = "OK",
    ) -> None:
        self._script: list[str | Exception] = list(script)
        self._default = default
        self.call_log: list[dict[str, Any]] = []

    async def __call__(
        self,
        *,
        model: str,
        prompt_name: str,
        text: str,
        **kwargs: Any,
    ) -> str:
        self.call_log.append(
            {"model": model, "prompt_name": prompt_name, "text": text}
        )
        nxt = self._script.pop(0) if self._script else self._default
        if isinstance(nxt, Exception):
            raise nxt
        return str(nxt)


# ---- fake notification channel -------------------------------------


def make_capture_channel(name: str = "test-terminal", *, is_active: bool = True):
    from loam.primary_persona.introduction import ChannelKind
    from loam.dormancy.notification import DegradationChannel

    sent: list[str] = []

    async def send(text: str) -> None:
        sent.append(text)

    return (
        DegradationChannel(
            kind=ChannelKind.terminal,
            name=name,
            send=send,
            is_group=False,
            is_active=is_active,
        ),
        sent,
    )

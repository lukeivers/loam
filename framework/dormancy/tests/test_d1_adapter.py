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

"""D1 — ClaudeClient adapter.

Acceptance (brief):
- Every pOS LLM call routes through the adapter (memory extraction,
  primary-persona monitor's stuck-reason pass, authoring pipeline).
- Exceptions propagate to callers unchanged; `retry-after` readable.
- Active probe interface returns success/failure + timing.
- Integration test confirms sealed-component existing LLM paths
  continue to work after routing through the adapter.
"""

from __future__ import annotations

import pytest

from loam.dormancy import (
    APIConnectionError,
    AuthenticationError,
    ClaudeClient,
    DegradationSignal,
    OverloadedError,
)
from loam.dormancy.adapter import AdapterEvent

from .fakes import FakeClock, FakeInvoker


async def _capture_events(events: list[AdapterEvent]):
    async def cb(e: AdapterEvent) -> None:
        events.append(e)

    return cb


async def test_adapter_success_path_records_event() -> None:
    events: list[AdapterEvent] = []
    clock = FakeClock()
    invoker = FakeInvoker(["hello"])
    client = ClaudeClient(
        invoke=invoker, on_event=await _capture_events(events), clock=clock
    )
    result = await client.call(prompt_name="memory.extraction", text="input")
    assert result.text == "hello"
    assert result.prompt_name == "memory.extraction"
    assert len(events) == 1
    assert events[0].ok is True
    assert events[0].signal is None
    assert events[0].prompt_name == "memory.extraction"


async def test_adapter_classifies_sdk_style_exception() -> None:
    # Simulate an Anthropic SDK-style exception by shape: a class named
    # RateLimitError with `response.headers['retry-after']`.
    class _Resp:
        def __init__(self) -> None:
            self.headers = {"retry-after": "30"}
            self.status_code = 429

    class RateLimitError(Exception):
        def __init__(self) -> None:
            super().__init__("rate limited")
            self.response = _Resp()
            self.status_code = 429

    events: list[AdapterEvent] = []
    invoker = FakeInvoker([RateLimitError()])
    client = ClaudeClient(invoke=invoker, on_event=await _capture_events(events))
    with pytest.raises(Exception) as err:  # re-raised after classify
        await client.call(prompt_name="monitor.stuck_reason", text="x")
    assert events and events[0].ok is False
    assert events[0].signal == DegradationSignal.rate_limited
    assert events[0].retry_after == 30.0


async def test_adapter_connection_error_maps_to_down_signal() -> None:
    events: list[AdapterEvent] = []
    invoker = FakeInvoker([ConnectionError("network down")])
    client = ClaudeClient(invoke=invoker, on_event=await _capture_events(events))
    with pytest.raises(APIConnectionError):
        await client.call(prompt_name="authoring.pipeline", text="x")
    assert events[0].signal == DegradationSignal.connection_error


async def test_adapter_auth_401_maps_to_auth_broken() -> None:
    events: list[AdapterEvent] = []
    invoker = FakeInvoker([_make_sdk_exception("AuthenticationError", status=401)])
    client = ClaudeClient(invoke=invoker, on_event=await _capture_events(events))
    with pytest.raises(AuthenticationError):
        await client.call(prompt_name="memory.extraction", text="x")
    assert events[0].signal == DegradationSignal.auth_broken
    assert events[0].status_code == 401


async def test_adapter_529_overloaded_distinct_from_5xx() -> None:
    events: list[AdapterEvent] = []
    invoker = FakeInvoker([_make_api_status_error(status=529)])
    client = ClaudeClient(invoke=invoker, on_event=await _capture_events(events))
    with pytest.raises(OverloadedError):
        await client.call(prompt_name="memory.extraction", text="x")
    assert events[0].signal == DegradationSignal.overloaded


async def test_adapter_400_bad_request_is_not_degradation_signal() -> None:
    from loam.dormancy import BadRequestError

    events: list[AdapterEvent] = []
    invoker = FakeInvoker([_make_sdk_exception("BadRequestError", status=400)])
    client = ClaudeClient(invoke=invoker, on_event=await _capture_events(events))
    with pytest.raises(BadRequestError):
        await client.call(prompt_name="memory.extraction", text="x")
    # 400 is classified as bad_request — detector filters this out.
    assert events[0].signal == DegradationSignal.bad_request


async def test_adapter_probe_success_and_failure() -> None:
    # Probe success
    invoker = FakeInvoker(["OK"])
    client = ClaudeClient(invoke=invoker)
    probe = await client.probe()
    assert probe.ok is True
    assert probe.latency_seconds >= 0.0

    # Probe failure (connection)
    invoker2 = FakeInvoker([ConnectionError("down")])
    client2 = ClaudeClient(invoke=invoker2)
    probe2 = await client2.probe()
    assert probe2.ok is False
    assert probe2.signal == DegradationSignal.connection_error


async def test_adapter_probe_prompt_attributed_correctly() -> None:
    invoker = FakeInvoker(["OK"])
    client = ClaudeClient(invoke=invoker)
    await client.probe()
    assert invoker.call_log[0]["prompt_name"] == "degradation-probe"


async def test_adapter_preserves_injectable_llm_callable_shape() -> None:
    """Primary-persona authoring expects `LLMCallable = Callable[[str,str],Awaitable[LLMResult]]`.
    The adapter itself is not that callable, but its `.call` method can
    be wrapped into one. Verify the shape adapts cleanly."""
    invoker = FakeInvoker(["persona-authoring-output"])
    client = ClaudeClient(invoke=invoker)

    async def llm_shim(prompt_name: str, prompt: str):
        from loam.primary_persona.authoring import LLMResult

        out = await client.call(prompt_name=prompt_name, text=prompt)
        return LLMResult(text=out.text, prompt_name=prompt_name, model=out.model)

    # Sanity: the shim shape matches primary-persona's expectation.
    result = await llm_shim("persona.style_harvest", "some prompt")
    assert result.text == "persona-authoring-output"


def _make_sdk_exception(type_name: str, *, status: int) -> Exception:
    """Build a shape-matching SDK-style exception that classify_exception
    recognises by class-name."""

    class _Resp:
        def __init__(self, s: int) -> None:
            self.headers = {}
            self.status_code = s

    cls = type(
        type_name,
        (Exception,),
        {"__init__": lambda self: Exception.__init__(self, type_name)},
    )
    instance = cls()
    instance.status_code = status
    instance.response = _Resp(status)
    return instance


def _make_api_status_error(*, status: int) -> Exception:
    class _Resp:
        def __init__(self, s: int) -> None:
            self.headers = {}
            self.status_code = s

    cls = type(
        "APIStatusError",
        (Exception,),
        {"__init__": lambda self: Exception.__init__(self, "APIStatusError")},
    )
    instance = cls()
    instance.status_code = status
    instance.response = _Resp(status)
    return instance

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

"""D3 — Detection rubrics + config.

Acceptance (brief):
- Synthetic Claude-side failures produce correct FSM transitions at
  documented thresholds.
- Workspace config in YAML overrides defaults cleanly; malformed YAML
  rejects with a clear error.
- Garbage detector's pydantic → regex → LLM-judge chain respects the
  5-judge/hour budget.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from loam.dormancy import DegradationConfig, load_config
from loam.dormancy.adapter import AdapterEvent
from loam.dormancy.detection import (
    DegradationDetector,
    GarbageDetectionRequest,
    GarbagePipeline,
)
from loam.dormancy.errors import DegradationSignal
from loam.dormancy.fsm import DegradationMode, FSMState, FSMTransition

from .fakes import FakeClock


async def test_detector_routes_signal_to_correct_fsm() -> None:
    clock = FakeClock()
    cfg = DegradationConfig()
    transitions: list[FSMTransition] = []

    async def on_t(t):
        transitions.append(t)

    det = DegradationDetector.from_config(cfg, clock=clock, on_transition=on_t)
    for _ in range(3):
        await det.record_event(
            AdapterEvent(
                call_id="x",
                prompt_name="memory.extraction",
                model="claude-haiku-4-5",
                ok=False,
                signal=DegradationSignal.connection_error,
                retry_after=None,
                latency_seconds=0.1,
                status_code=None,
                timestamp=clock.now(),
            )
        )
    # Exactly one "open" transition for `down`.
    open_events = [
        t for t in transitions if t.to_state.value == "open" and t.mode.value == "down"
    ]
    assert len(open_events) == 1


async def test_detector_latency_advisory_fires() -> None:
    clock = FakeClock()
    cfg = DegradationConfig()
    transitions: list[FSMTransition] = []

    async def on_t(t):
        transitions.append(t)

    det = DegradationDetector.from_config(cfg, clock=clock, on_transition=on_t)
    for _ in range(20):
        await det.record_event(
            AdapterEvent(
                call_id=f"x{_}",
                prompt_name="authoring",
                model="claude-haiku-4-5",
                ok=True,
                signal=None,
                retry_after=None,
                latency_seconds=40.0,
                status_code=200,
                timestamp=clock.now(),
            )
        )
    advisories = [t for t in transitions if t.trigger == "latency_advisory"]
    assert len(advisories) == 1


def test_config_load_defaults_when_no_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"
    cfg = load_config(path)
    assert isinstance(cfg, DegradationConfig)
    assert cfg.modes.down.trip_threshold.failures == 3


def test_config_load_from_text_overrides_defaults() -> None:
    text = """
degradation:
  modes:
    down:
      trip_threshold:
        failures: 10
        window_seconds: 120
      half_open_dwell_seconds: 60
      probe_success_requirement: 1
      default_policy: pause_all
"""
    cfg = load_config(text=text)
    assert cfg.modes.down.trip_threshold.failures == 10
    assert cfg.modes.down.trip_threshold.window_seconds == 120


def test_config_malformed_yaml_rejects_with_clear_error() -> None:
    text = "degradation:\n  modes:\n    down:\n      trip_threshold: not_a_mapping\n"
    with pytest.raises((ValidationError, ValueError)):
        load_config(text=text)


def test_config_unknown_field_rejects() -> None:
    text = """
modes:
  down:
    trip_threshold: {failures: 3, window_seconds: 60}
    half_open_dwell_seconds: 30
    probe_success_requirement: 1
    default_policy: pause_all
    bogus_field: true
"""
    with pytest.raises(ValidationError):
        load_config(text=text)


async def test_garbage_pipeline_pydantic_tier_catches_validation() -> None:
    class Expected(BaseModel):
        name: str
        value: int

    pipe = GarbagePipeline()
    req = GarbageDetectionRequest(
        text='{"name": "x", "value": "not-an-int"}',
        prompt_name="authoring",
        expected_model=Expected,
    )
    assert await pipe.is_garbage(req) is True


async def test_garbage_pipeline_regex_catches_refusal() -> None:
    pipe = GarbagePipeline()
    req = GarbageDetectionRequest(
        text="I can't help with that request, sorry.",
        prompt_name="authoring",
    )
    assert await pipe.is_garbage(req) is True


async def test_garbage_pipeline_regex_catches_empty() -> None:
    pipe = GarbagePipeline()
    req = GarbageDetectionRequest(
        text="   ", prompt_name="authoring", min_chars=5
    )
    assert await pipe.is_garbage(req) is True


async def test_garbage_pipeline_respects_judge_budget() -> None:
    clock = FakeClock()
    call_count = {"n": 0}

    async def judge(req: GarbageDetectionRequest) -> bool:
        call_count["n"] += 1
        return True

    pipe = GarbagePipeline(judge=judge, judge_budget_per_hour=2, clock=clock)
    # 3 ambiguous responses (not empty, not refusal, no schema)
    for _ in range(3):
        req = GarbageDetectionRequest(
            text="A plausible response that's not obviously bad.",
            prompt_name="authoring",
        )
        await pipe.is_garbage(req)
    # Budget 2 — judge should have been called twice only.
    assert call_count["n"] == 2


async def test_garbage_pipeline_budget_resets_after_hour() -> None:
    clock = FakeClock()

    async def judge(req: GarbageDetectionRequest) -> bool:
        return False

    pipe = GarbagePipeline(judge=judge, judge_budget_per_hour=1, clock=clock)
    req = GarbageDetectionRequest(
        text="An ambiguous response.", prompt_name="p"
    )
    await pipe.is_garbage(req)
    # Advance > 3600s.
    clock.advance(3700)
    # Should be callable again (budget reset)
    called = {"n": 0}

    async def judge2(req: GarbageDetectionRequest) -> bool:
        called["n"] += 1
        return False

    pipe.judge = judge2
    await pipe.is_garbage(req)
    assert called["n"] == 1

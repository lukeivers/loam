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

"""D0 — `expected_duration_seconds` + stuck-detection.

Acceptance (primary-persona brief D0):
- Field exists on `ScopeSpec` as an optional float.
- Default is `None`; scopes without the field load and behave as before.
- Field flows through the event log and projection cache.
- When set and `elapsed > 2 × expected_duration_seconds` without state
  events since start, the scope is identifiable as stuck via
  `list(stuck=True)`.

These tests mutate `datetime.now()` indirectly by injecting a `now` into
the stuck helper paths where possible; the `list(stuck=True)` path is
exercised by moving `first_activated_at` into the past via direct
projection manipulation on the event log.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from loam.scope_of_work.events import ScopeCreated
from loam.scope_of_work.projection import project
from loam.scope_of_work.spec import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)
from loam.scope_of_work.triggers import is_stuck, seconds_since_first_activation
from tests.conftest import make_spec


# ---- field existence and default --------------------------------------


def test_expected_duration_seconds_defaults_to_none():
    spec = make_spec()
    assert spec.expected_duration_seconds is None


def test_expected_duration_seconds_accepts_positive_float():
    spec = make_spec(expected_duration_seconds=30.0)
    assert spec.expected_duration_seconds == 30.0


def test_expected_duration_seconds_rejects_negative():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ScopeSpec(
            goal="x",
            constraints=(),
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
            observers=(),
            escalation_triggers=(),
            expected_duration_seconds=-5.0,
        )


# ---- field flows through event log and projection --------------------


async def test_field_flows_through_scope_created_event(runtime):
    spec = make_spec(expected_duration_seconds=30.0)
    proj = await runtime.create(spec, scope_id="flows-1")
    # Public projection surfaces the field
    assert proj.expected_duration_seconds == 30.0

    # Event log round-trip: re-read the event and confirm the field
    # is serialised and de-serialised intact.
    events = runtime.store.events_for("flows-1")
    created = [e for e in events if isinstance(e, ScopeCreated)]
    assert len(created) == 1
    assert created[0].expected_duration_seconds == 30.0

    # Projection round-trip: rebuild projection from events alone.
    rebuilt = project("flows-1", events)
    assert rebuilt.expected_duration_seconds == 30.0


async def test_field_none_when_unset(runtime):
    spec = make_spec()  # expected_duration_seconds not specified
    proj = await runtime.create(spec, scope_id="unset-1")
    assert proj.expected_duration_seconds is None
    rebuilt = project("unset-1", runtime.store.events_for("unset-1"))
    assert rebuilt.expected_duration_seconds is None


# ---- stuck-detection logic (pure helper) -----------------------------


async def test_scope_without_duration_is_never_stuck(runtime):
    spec = make_spec()  # no expected_duration_seconds
    await runtime.create(spec, scope_id="never-stuck")
    await runtime.start("never-stuck")
    proj = runtime._project("never-stuck")
    assert is_stuck(proj) is False


async def test_scope_not_yet_activated_is_not_stuck(runtime):
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="not-started")
    proj = runtime._project("not-started")
    # proposed state, never activated
    assert is_stuck(proj) is False


async def test_terminal_scope_is_not_stuck(runtime):
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="terminal")
    await runtime.start("terminal")
    await runtime.complete("terminal", evaluations=[("c1", "met", None)])
    proj = runtime._project("terminal")
    assert is_stuck(proj) is False


async def test_scope_with_state_transitions_after_start_is_not_stuck(runtime):
    """A scope that had pause→resume after start is actively progressing;
    it is not stuck even if elapsed exceeds the budget."""
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="progressing")
    await runtime.start("progressing")
    await runtime.pause("progressing", reason="checkpoint")

    proj = runtime._project("progressing")
    # Simulate elapsed past 2× expected duration.
    future = datetime.now(timezone.utc) + timedelta(seconds=5)
    assert is_stuck(proj, now=future) is False


async def test_scope_stuck_after_2x_expected_duration(runtime):
    """Core D0 acceptance: when elapsed > 2× expected and no
    state events since start, the scope is stuck."""
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="stuck-1")
    await runtime.start("stuck-1")

    proj = runtime._project("stuck-1")
    # Just after start: elapsed < 2× expected → not stuck.
    assert is_stuck(proj) is False

    # Simulate 3 seconds later (> 2× 1.0 = 2.0).
    future = datetime.now(timezone.utc) + timedelta(seconds=3)
    assert is_stuck(proj, now=future) is True


async def test_scope_not_stuck_at_exactly_2x(runtime):
    """Strict `>` boundary: elapsed == 2× expected is not yet stuck."""
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="boundary")
    await runtime.start("boundary")
    proj = runtime._project("boundary")
    # Elapsed exactly 2s (== 2×1.0); rule is strict >, so not stuck.
    future_exact = datetime.fromisoformat(proj.first_activated_at) + timedelta(seconds=2)
    assert is_stuck(proj, now=future_exact) is False
    future_past = datetime.fromisoformat(proj.first_activated_at) + timedelta(
        seconds=2, microseconds=1
    )
    # Only microseconds past the boundary is still false because the
    # elapsed computation is float seconds — just above 2.0s is >2.0.
    assert is_stuck(proj, now=future_past + timedelta(milliseconds=50)) is True


# ---- list(stuck=True) — the acceptance criterion ---------------------


async def test_list_stuck_filter_identifies_stuck_scope(runtime, monkeypatch):
    """The brief's explicit acceptance: `list(stuck=True)` surfaces a
    scope whose elapsed exceeds 2× expected_duration_seconds without
    state events."""
    # One scope with opt-in, one without. Only the opt-in one should
    # ever appear in stuck=True results.
    spec_stuck = make_spec(expected_duration_seconds=0.1)
    spec_not = make_spec()

    await runtime.create(spec_stuck, scope_id="stuck-a")
    await runtime.start("stuck-a")

    await runtime.create(spec_not, scope_id="not-tracked")
    await runtime.start("not-tracked")

    # Immediately: nothing is stuck.
    assert runtime.list(stuck=True) == []

    # Advance wall-clock: patch `datetime.now` in the is_stuck /
    # elapsed helpers to simulate the scope exceeding 2× expected.
    import loam.scope_of_work.triggers as triggers_mod
    import loam.scope_of_work.projection_view as projection_view_mod

    real_now = datetime.now(timezone.utc)
    fake_now = real_now + timedelta(seconds=5)

    class _FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now if tz is None else fake_now.astimezone(tz)

    monkeypatch.setattr(triggers_mod, "datetime", _FakeDatetime)
    monkeypatch.setattr(projection_view_mod, "datetime", _FakeDatetime)

    stuck_scopes = runtime.list(stuck=True)
    stuck_ids = {s.scope_id for s in stuck_scopes}
    assert "stuck-a" in stuck_ids
    assert "not-tracked" not in stuck_ids

    # Sanity: `stuck=False` excludes the stuck scope but keeps the
    # other.
    not_stuck = runtime.list(stuck=False)
    not_stuck_ids = {s.scope_id for s in not_stuck}
    assert "not-tracked" in not_stuck_ids
    assert "stuck-a" not in not_stuck_ids


# ---- seconds_since_first_activation helper ---------------------------


async def test_seconds_since_first_activation_none_when_never_activated(runtime):
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="fresh")
    proj = runtime._project("fresh")
    assert seconds_since_first_activation(proj) is None


async def test_seconds_since_first_activation_spans_pauses(runtime):
    """first_activated_at is the clock start and does not reset on
    resume; seconds_since_first_activation includes paused time."""
    spec = make_spec(expected_duration_seconds=1.0)
    await runtime.create(spec, scope_id="paused-clock")
    await runtime.start("paused-clock")
    await runtime.pause("paused-clock")
    proj = runtime._project("paused-clock")
    future = datetime.fromisoformat(proj.first_activated_at) + timedelta(seconds=10)
    assert seconds_since_first_activation(proj, now=future) == pytest.approx(10.0, abs=1.0)

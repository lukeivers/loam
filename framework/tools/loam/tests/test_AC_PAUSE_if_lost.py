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

"""AC.PAUSE.* — pause-if-lost made structural.

  - AC.PAUSE.1 — a RESOLVED cursor surfaces the position (flow + step +
    the follow-it / pause-if-lost directive) into context.
  - AC.PAUSE.2 — an UNRESOLVED cursor (missing / stale / non-existent
    step) yields the PAUSE signal, not a silent continue.
  - AC.PAUSE.3 — positive-resolution: the check passes ONLY on a
    one-sentence restatement; an empty / corrupt / ambiguous cursor
    defaults to PAUSE. The lost state is the default.
"""

from __future__ import annotations

import pytest

from loam_cli.flows.cursor import Cursor, resolve_cursor
from loam_cli.flows.format import parse_flow_definition
from loam_cli.flows.pause import (
    FOLLOW_DIRECTIVE,
    PAUSE_DIRECTIVE,
    position_check,
)

_FLOW_TEXT = (
    "---\n"
    "flow: f\n"
    "entry: a\n"
    "steps:\n"
    "  - id: a\n    name: A\n    transitions: [b]\n"
    "  - id: b\n    name: B\n    transitions: [c]\n"
    "  - id: c\n    name: C\n    transitions: []\n"
    "---\n"
    "# f\nnarrative present.\n"
)


@pytest.fixture
def flow():
    return parse_flow_definition(_FLOW_TEXT)


def test_AC_PAUSE_1_resolved_cursor_surfaces_position(flow) -> None:
    """AC.PAUSE.1 — a resolved cursor surfaces flow + step + the
    follow-it / pause-if-lost directive."""
    res = resolve_cursor(Cursor(flow="f", step="b", branch_state="mid"), flow)
    decision = position_check(res)
    assert not decision.paused
    # Names the flow + the current step.
    assert "f" in decision.directive
    assert "B" in decision.directive  # step name.
    # Carries the follow-it / pause-if-lost directive.
    assert FOLLOW_DIRECTIVE in decision.directive


def test_AC_PAUSE_2_unresolved_cursor_emits_pause_not_continue(
    flow,
) -> None:
    """AC.PAUSE.2 — a stale / non-existent-step cursor yields the PAUSE
    signal, not a silent continue."""
    # Non-existent step (the stale-cursor shape at the pause boundary).
    res = resolve_cursor(Cursor(flow="f", step="ghost"), flow)
    decision = position_check(res)
    assert decision.paused
    assert PAUSE_DIRECTIVE in decision.directive
    assert "re-establish position" in decision.directive.lower()


def test_AC_PAUSE_2_missing_cursor_emits_pause(flow) -> None:
    """AC.PAUSE.2 — a missing cursor (None) yields PAUSE."""
    res = resolve_cursor(None, flow)
    decision = position_check(res)
    assert decision.paused
    assert PAUSE_DIRECTIVE in decision.directive


def test_AC_PAUSE_3_lost_is_the_default(flow) -> None:
    """AC.PAUSE.3 — positive-resolution: every non-positive input
    (empty / corrupt / ambiguous / no-definition) defaults to PAUSE,
    never to 'probably fine'."""
    # No cursor, no definition.
    assert position_check(resolve_cursor(None, None)).paused
    # Cursor present but no flow definition (cannot confirm position).
    assert position_check(
        resolve_cursor(Cursor(flow="f", step="b"), None)
    ).paused
    # Cursor flow-name mismatched against the loaded definition.
    assert position_check(
        resolve_cursor(Cursor(flow="other", step="b"), flow)
    ).paused
    # The ONLY non-paused path is a positive resolution.
    ok = position_check(resolve_cursor(Cursor(flow="f", step="a"), flow))
    assert not ok.paused
    assert ok.one_sentence  # the one-sentence restatement is present.

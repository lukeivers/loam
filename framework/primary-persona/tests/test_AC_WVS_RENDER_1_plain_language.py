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

"""AC.WVS-RENDER.1 — the snapshot renders to a plain-language status a
non-technical reader understands at a glance, explicitly answering the
three anxiety questions — what's happening now / what's next / is
anything stuck — in plain English.

Plan: docs/plans/work-visibility-surface.md §5.
"""

from __future__ import annotations

from loam.primary_persona.work_visibility import (
    HEALTH_OK,
    HEALTH_STUCK,
    HEALTH_UNKNOWN,
    WorkSnapshot,
    render_surface,
)


def test_AC_WVS_RENDER_1_answers_now_next_health() -> None:
    """A populated snapshot renders a now / next / health statement in
    plain prose."""
    snapshot = WorkSnapshot(
        running_now=2,
        queued=3,
        owner_pending=1,
        health=HEALTH_OK,
        health_unknown=False,
    )
    text = render_surface(snapshot)
    lower = text.lower()
    # now
    assert "right now" in lower
    assert "working on" in lower
    # next
    assert "what's next" in lower
    # health
    assert "health" in lower
    assert "no problems detected" in lower


def test_AC_WVS_RENDER_1_owner_pending_rendered_prominently() -> None:
    """The owner-pending bucket renders prominently — the 'is it waiting
    on ME?' anxiety (plan §10 F2 #2). It leads the next-line and names
    the user explicitly."""
    snapshot = WorkSnapshot(owner_pending=2, queued=1, health=HEALTH_OK)
    text = render_surface(snapshot)
    lower = text.lower()
    assert "waiting on you" in lower
    # Owner-pending precedes the queued mention in the next-line.
    assert lower.index("waiting on you") < lower.index("lined up")


def test_AC_WVS_RENDER_1_stuck_health_surfaced() -> None:
    """A stuck health renders the 'something looks stuck' answer — the
    surface answers 'is it stuck?', not merely 'what's there?'."""
    snapshot = WorkSnapshot(running_now=1, health=HEALTH_STUCK)
    text = render_surface(snapshot)
    assert "stuck" in text.lower()


def test_AC_WVS_RENDER_1_unknown_health_is_honest() -> None:
    """An unknown health renders an honest 'could not check', never a
    false 'fine' (plan §10 F2 #3)."""
    snapshot = WorkSnapshot(health=HEALTH_UNKNOWN, health_unknown=True)
    text = render_surface(snapshot).lower()
    assert "could not check" in text
    assert "everything is fine" not in text


def test_AC_WVS_RENDER_1_all_caught_up() -> None:
    """An empty, healthy snapshot renders an 'all caught up / all clear'
    plain statement."""
    snapshot = WorkSnapshot(health=HEALTH_OK)
    text = render_surface(snapshot).lower()
    assert "all caught up" in text or "nothing is in progress" in text
    assert "all clear" in text or "nothing is waiting" in text


def test_AC_WVS_RENDER_1_position_line_when_resolved() -> None:
    """A resolved position renders a plain 'where I am' line."""
    snapshot = WorkSnapshot(
        running_now=1,
        position_known=True,
        position_phrase="step first step of flow build, branch ready",
        health=HEALTH_OK,
    )
    text = render_surface(snapshot).lower()
    assert "where i am" in text
    assert "first step" in text

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

"""AC.ANL.BALANCE.1/.2/.3 — insight 3: completion-vs-intake balance.

Plan §6 AC.ANL.BALANCE.*:
  - .1 over a recent window, captured-vs-finished in ONE plain sentence,
    derived over the event log's created vs terminal-transition events;
  - .2 DERIVED OVER HISTORY not over current state — an item created AND
    finished within the window counts in BOTH (a snapshot count cannot
    reconstruct this — the load-bearing Lens-1 fact);
  - .3 an empty window -> honest "nothing captured or finished", no
    divide-by-zero theatre.

.1/.3 are pure derivations over duck-typed events; .2 rides a REAL store's
``all_events()`` to prove the history-derivation (no snapshot count could
reproduce the created-and-finished-within-window item).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from loam.primary_persona.keep_pace.analytics import compute_balance

from _wms4_store import EDGE, fresh_factory, live_store, make_open  # noqa: F401

_NOW = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeStatus:
    value: str


@dataclass(frozen=True)
class _Ev:
    kind: str
    created_at: str
    to_status: Optional[_FakeStatus] = None


def _ago(days: float) -> str:
    return (_NOW - timedelta(days=days)).isoformat()


def _created(days: float) -> _Ev:
    return _Ev(kind="objective_created", created_at=_ago(days))


def _terminal(days: float, status: str = "achieved") -> _Ev:
    return _Ev(kind="status_transitioned", created_at=_ago(days),
               to_status=_FakeStatus(status))


def _nonterminal(days: float, status: str = "active") -> _Ev:
    return _Ev(kind="status_transitioned", created_at=_ago(days),
               to_status=_FakeStatus(status))


def test_AC_ANL_BALANCE_1_capture_vs_finish_one_sentence() -> None:
    events = (
        [_created(d) for d in (1, 2, 3, 4, 5)]   # 5 captured in window
        + [_terminal(2), _terminal(3)]           # 2 finished in window
        + [_nonterminal(1)]                       # a non-terminal move: ignored
        + [_created(30), _terminal(40)]           # outside the window: ignored
    )
    bal = compute_balance(events, now=_NOW, window_days=7)
    assert bal.captured == 5
    assert bal.finished == 2
    sentence = bal.sentence()
    assert "5" in sentence
    # Plain one-sentence signal; non-judgmental orienting phrasing (RF #4).
    assert "captured" in sentence.lower()
    assert "this week" in sentence


async def test_AC_ANL_BALANCE_2_derived_over_history_not_snapshot(tmp_path) -> None:
    # The load-bearing Lens-1 proof: an item CREATED and FINISHED within the
    # window. A current-state snapshot would see one terminal item and could
    # NOT tell you it was also captured in the window. The event-log walk
    # reconstructs both — it counts in captured AND finished.
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        a = await make_open(setup, "created and finished this week")
        await setup.mark_achieved(a.objective_id, evidence="done")
        # A second item only captured (still open).
        await make_open(setup, "just captured this week")
    finally:
        setup.close()

    factory = fresh_factory(db)
    client = factory()
    try:
        events = list(client.store.all_events())
    finally:
        client.close()

    # All events are "now" (real store) -> inside a 7-day window from _real_
    # now. Use the real clock here (the store stamped real now).
    bal = compute_balance(events, window_days=7)
    # Two created (both items), one terminal (the achieved one). The achieved
    # item counts in BOTH captured and finished — the history-derivation a
    # snapshot cannot reproduce.
    assert bal.captured == 2, f"both creations in window; got {bal.captured}"
    assert bal.finished == 1, f"the achieved item in window; got {bal.finished}"


def test_AC_ANL_BALANCE_3_empty_window_honest_no_activity() -> None:
    # Activity all OUTSIDE the window.
    events = [_created(30), _terminal(40)]
    bal = compute_balance(events, now=_NOW, window_days=7)
    assert bal.captured == 0
    assert bal.finished == 0
    assert not bal.has_activity
    sentence = bal.sentence()
    assert "nothing" in sentence.lower()
    # No misleading ratio / divide-by-zero theatre.
    assert "/" not in sentence

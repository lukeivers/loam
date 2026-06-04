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

"""AC.PRI.4 — every ranked item carries a PLAIN-LANGUAGE reason, and NO
raw numeric score is surfaced.

Plan §6 AC.PRI.4. Outcome: the reason names the dominant contributing
signal in plain language, carrying NO internal identifier, lifecycle
enum, slug, path, or score (transparent-not-black-box — the Lens-2 trust
value + the zero-internal-vocab invariant).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.prioritize import prioritize

from _wms4_store import make_item


_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)

# A score / internal-id leak detector: bare floats, enum-ish tokens,
# obj-ids, dotted paths.
_SCORE_RE = re.compile(r"\b\d+\.\d+\b")
_OBJID_RE = re.compile(r"\bobj-[0-9a-f-]+\b", re.IGNORECASE)
_ENUM_TOKENS = {"owner_pending", "proposed", "blocks", "waits_on", "objectivestatus", "workedgekind"}


def _assert_clean_reason(reason: str) -> None:
    assert reason.strip(), "every ranked item must carry a non-empty reason"
    assert not _SCORE_RE.search(reason), f"no raw numeric score may surface: {reason!r}"
    assert not _OBJID_RE.search(reason), f"no internal objective-id may leak: {reason!r}"
    low = reason.lower()
    for tok in _ENUM_TOKENS:
        assert tok not in low, f"no internal enum/slug may leak: {reason!r} (token {tok!r})"
    assert "/" not in reason, f"no path may leak: {reason!r}"


def test_AC_PRI_4_every_ranked_item_carries_a_plain_language_reason() -> None:
    items = [
        make_item("obj-a", goal="independent thing", priority="active",
                  last_transition_at=(_NOW - timedelta(days=30)).isoformat()),
        make_item("obj-b", goal="the unblocker", priority="active",
                  edges_out=[("blocks", "obj-c", None)]),
        make_item("obj-c", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-b", None)]),
    ]
    ranked = prioritize(items, aligned_terms=frozenset({"unblocker"}), now=_NOW)
    assert len(ranked) == 3
    for r in ranked:
        _assert_clean_reason(r.reason)


def test_AC_PRI_4_blocking_impact_reason_is_human() -> None:
    """The unblock-many item's reason names the dependency in plain
    language ("waiting on it"), not an id or score."""
    b = make_item("obj-b", goal="the unblocker", priority="active",
                  edges_out=[("blocks", "obj-c", None)])
    c = make_item("obj-c", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-b", None)])
    ranked = prioritize([b, c], now=_NOW)
    top = ranked[0]
    assert top.item.objective_id == "obj-b"
    assert "waiting on it" in top.reason.lower()
    _assert_clean_reason(top.reason)


def test_AC_PRI_4_score_is_internal_only_never_in_reason() -> None:
    """The internal score exists on the wrapper (for verification) but
    never appears in the reason text."""
    items = [make_item("obj-a", goal="task a", priority="owner_pending")]
    r = prioritize(items, now=_NOW)[0]
    # The score is accessible internally...
    assert isinstance(r.score, float)
    # ...but the reason carries no rendering of it.
    assert str(r.score) not in r.reason
    _assert_clean_reason(r.reason)


def test_AC_PRI_4_pinned_and_deferred_reasons_are_plain() -> None:
    item = make_item("obj-p", goal="the pinned thing", priority="proposed")
    pinned = prioritize([item], pinned=frozenset({"obj-p"}), now=_NOW)[0]
    assert "pinned" in pinned.reason.lower()
    _assert_clean_reason(pinned.reason)

    deferred = prioritize([item], deferred=frozenset({"obj-p"}), now=_NOW)[0]
    assert "deferred" in deferred.reason.lower()
    _assert_clean_reason(deferred.reason)

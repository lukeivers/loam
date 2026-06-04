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

"""Legal status transitions for an objective.

Lifecycle (spec):

    proposed → active
    proposed → abandoned
    active   → achieved
    active   → abandoned
    active   → owner_pending  (session-/clear-safety R2: work shipped,
                               owner ruling pending)
    owner_pending → active    (owner ruled: resume / re-scope)
    owner_pending → achieved  (owner ruled: done)
    owner_pending → abandoned (owner ruled: drop)
    achieved → active   (re_open; mandatory rationale)
    abandoned → active  (re_open; mandatory rationale)

`owner_pending` is additive (amendment-38 additive-widening precedent):
no pre-R2 transition is removed or altered, so existing records and
every existing transition path are unchanged (AC.SCS-R2.3,
default-preserving D8 round-trip). It is NOT in `TERMINAL_STATES` —
an owner-pending objective is an open loop awaiting the owner, not a
closed record.
"""

from __future__ import annotations

from .spec import ObjectiveStatus

LEGAL_TRANSITIONS: dict[ObjectiveStatus, set[ObjectiveStatus]] = {
    ObjectiveStatus.proposed: {
        ObjectiveStatus.active,
        ObjectiveStatus.abandoned,
    },
    ObjectiveStatus.active: {
        ObjectiveStatus.achieved,
        ObjectiveStatus.abandoned,
        ObjectiveStatus.owner_pending,
        # WMS increment 2 — `active → blocked` (a blocker surfaced;
        # AC.WI.1). Additive, the `owner_pending` precedent: no existing
        # transition is removed or altered.
        ObjectiveStatus.blocked,
    },
    ObjectiveStatus.owner_pending: {
        ObjectiveStatus.active,
        ObjectiveStatus.achieved,
        ObjectiveStatus.abandoned,
    },
    # WMS increment 2 — `blocked` is a non-terminal open state; it leaves
    # back to `active` when the blocker clears, or to `abandoned` if the
    # item is dropped while blocked (AC.WI.1). NOT terminal.
    ObjectiveStatus.blocked: {
        ObjectiveStatus.active,
        ObjectiveStatus.abandoned,
    },
    ObjectiveStatus.achieved: {
        ObjectiveStatus.active,
    },
    ObjectiveStatus.abandoned: {
        ObjectiveStatus.active,
    },
}

TERMINAL_STATES = {ObjectiveStatus.achieved, ObjectiveStatus.abandoned}


def is_legal(from_status: ObjectiveStatus, to_status: ObjectiveStatus) -> bool:
    return to_status in LEGAL_TRANSITIONS.get(from_status, set())


def is_terminal(status: ObjectiveStatus) -> bool:
    return status in TERMINAL_STATES

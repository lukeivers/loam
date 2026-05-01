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
    achieved → active   (re_open; mandatory rationale)
    abandoned → active  (re_open; mandatory rationale)
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

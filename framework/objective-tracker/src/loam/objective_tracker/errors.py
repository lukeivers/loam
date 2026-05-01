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

"""Typed errors raised by the objective tracker.

These are the public exception surface consumers catch.
"""

from __future__ import annotations


class ObjectiveTrackerError(Exception):
    """Base class for tracker errors."""


class UnresolvedObjectiveError(ObjectiveTrackerError):
    """bind_scope received an objective_id that doesn't exist.

    Message always carries the offending objective id (D4 acceptance).
    """

    def __init__(self, objective_id: str) -> None:
        super().__init__(f"Unresolved objective id: {objective_id!r}")
        self.objective_id = objective_id


class OrphanRootError(ObjectiveTrackerError):
    """bind_scope received an objective whose ancestry does not
    terminate at a user-authored root (authored_by != "user").
    """

    def __init__(self, objective_id: str, terminal_root_id: str, terminal_authored_by: str) -> None:
        super().__init__(
            f"Objective {objective_id!r} traces to root {terminal_root_id!r} "
            f"authored_by={terminal_authored_by!r}; user-authored root required."
        )
        self.objective_id = objective_id
        self.terminal_root_id = terminal_root_id
        self.terminal_authored_by = terminal_authored_by


class IllegalTransitionError(ObjectiveTrackerError):
    """Status transition is not permitted."""


class MissingRationaleError(ObjectiveTrackerError):
    """re_open was called without a non-empty rationale (Luke's decision)."""


class DAGRejected(ObjectiveTrackerError):
    """Attempted to author an objective that would form a DAG or cycle."""


class ManifestRowError(ObjectiveTrackerError):
    """Refused an `objective_manifest` row insert due to a structural
    failure (empty field or invalid fnmatch pattern).

    Per the structural-enforcement A1 substrate (AC.SE.7) the
    manifest's write API refuses malformed rows at the API boundary
    rather than at SQLite-projection time. ``field`` names which
    field rejected the value; ``value`` carries the rejected literal.
    """

    def __init__(self, field: str, value: str, reason: str) -> None:
        super().__init__(
            f"objective_manifest refused row: field={field!r} "
            f"value={value!r} reason={reason!r}"
        )
        self.field = field
        self.value = value
        self.reason = reason

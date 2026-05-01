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

"""Objective tracker primitive for pOS v2.

Public surface:

    from loam.objective_tracker import (
        ObjectiveTracker, ObjectiveSpec, ObjectiveStatus,
        TimeBound, ParentClosePolicy,
        ProseCriterion, ScopeSuccessCriterion,
        ChildClosureCriterion, ExternalPredicateCriterion,
    )
    from loam.objective_tracker.errors import (
        UnresolvedObjectiveError, OrphanRootError,
        IllegalTransitionError, MissingRationaleError, DAGRejected,
    )

The tracker is constructed once per process (or per database file).
It has no hard dependencies on any other pOS component. Optional
integration with scope-of-work: call `tracker.subscribe_scope_emitter(
scope_runtime.emitter)` to enable auto-evaluation of
`ScopeSuccessCriterion` on scope state-change events.
"""

from __future__ import annotations

from .errors import (
    DAGRejected,
    IllegalTransitionError,
    ManifestRowError,
    MissingRationaleError,
    ObjectiveTrackerError,
    OrphanRootError,
    UnresolvedObjectiveError,
)
from .filter import ObjectiveFilter
from .projection_view import CriterionEvaluation, ObjectiveProjection
from .runtime import ObjectiveTracker
from .spec import (
    ChildClosureCriterion,
    Criterion,
    ExternalPredicateCriterion,
    LiftedFrom,
    ObjectiveSpec,
    ObjectiveStatus,
    ParentCloseEventKind,
    ParentClosePolicy,
    ProseCriterion,
    ScopeSuccessCriterion,
    TimeBound,
)

__all__ = [
    "ChildClosureCriterion",
    "Criterion",
    "CriterionEvaluation",
    "DAGRejected",
    "ExternalPredicateCriterion",
    "IllegalTransitionError",
    "LiftedFrom",
    "ManifestRowError",
    "MissingRationaleError",
    "ObjectiveFilter",
    "ObjectiveProjection",
    "ObjectiveSpec",
    "ObjectiveStatus",
    "ObjectiveTracker",
    "ObjectiveTrackerError",
    "OrphanRootError",
    "ParentCloseEventKind",
    "ParentClosePolicy",
    "ProseCriterion",
    "ScopeSuccessCriterion",
    "TimeBound",
    "UnresolvedObjectiveError",
]

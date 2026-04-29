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

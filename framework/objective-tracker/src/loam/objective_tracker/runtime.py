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

"""ObjectiveTracker — the public orchestrator.

Composes the EventStore, projector, pyee emitter, sidecar binding
table, and OTel tracer behind one async public API. Per-objective
`asyncio.Lock` serialises mutations.

The tracker has no hard dependencies on any other pOS component. It
optionally subscribes to scope-of-work's pyee emitter for auto-
evaluation of ScopeSuccessCriterion (Luke's decision — brief
§"Luke's decisions"); see `subscribe_scope_emitter`. Consumers can
call `bind_scope(scope_id, objective_id)` to enforce the
traceability invariant at scope activation time.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from pyee.asyncio import AsyncIOEventEmitter

from . import observability as obs
from .errors import (
    DAGRejected,
    IllegalTransitionError,
    MissingRationaleError,
    OrphanRootError,
    UnresolvedObjectiveError,
)
from .events import (
    CriterionEvaluated,
    ObjectiveCreated,
    ObjectiveEvent,
    ParentClosed,
    ScopeBound,
    StatusTransitioned,
    WorkEdge,
    WorkEdgeCleared,
)
from .filter import ObjectiveFilter
from .policies import is_legal, is_terminal
from .projection import (
    ObjectiveProjectionData,
    WorkEdgeRecord,
    project,
    projection_to_state_row,
)
from .projection_view import ObjectiveProjection, public_projection
from .spec import (
    Criterion,
    ObjectiveSpec,
    ObjectiveStatus,
    ParentCloseEventKind,
    ParentClosePolicy,
    ScopeSuccessCriterion,
    WorkEdgeKind,
)
from .store import EventStore


class ObjectiveTracker:
    """Public async orchestrator over an EventStore."""

    def __init__(self, db_path: str | Path) -> None:
        self._store = EventStore(db_path)
        self._emitter = AsyncIOEventEmitter()
        self._obj_locks: dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()
        # scope_id -> list of (objective_id, criterion_id) subscribed
        # from registered scope emitters. We track subscriptions so
        # auto-evaluation can trigger the right criterion on each
        # scope-of-work state event.
        self._scope_subscriptions: dict[str, list[tuple[str, ScopeSuccessCriterion]]] = {}
        self._scope_emitters: list[Any] = []

    @property
    def store(self) -> EventStore:
        return self._store

    @property
    def emitter(self) -> AsyncIOEventEmitter:
        return self._emitter

    def close(self) -> None:
        self._store.close()

    # -- helpers -------------------------------------------------------

    async def _lock_for(self, objective_id: str) -> asyncio.Lock:
        async with self._locks_lock:
            lock = self._obj_locks.get(objective_id)
            if lock is None:
                lock = asyncio.Lock()
                self._obj_locks[objective_id] = lock
            return lock

    def _append(self, event: ObjectiveEvent, span: Any = None) -> Any:
        trace_id, span_id = obs.span_ids(span)
        if trace_id and not event.otel_trace_id:
            event = event.model_copy(
                update={"otel_trace_id": trace_id, "otel_span_id": span_id}
            )
        return self._store.append(event).event

    def _project(self, objective_id: str) -> ObjectiveProjectionData:
        return project(objective_id, self._store.events_for(objective_id))

    def _persist(self, proj: ObjectiveProjectionData) -> None:
        self._store.upsert_state(projection_to_state_row(proj))

    def _fan_out(self, objective_id: str, event: Any) -> None:
        self._emitter.emit(f"objective:{objective_id}", event)
        self._emitter.emit("*", event)

    # ------------------------------------------------------------------
    # Public API: create / decompose
    # ------------------------------------------------------------------

    async def create(
        self,
        spec: ObjectiveSpec,
        *,
        objective_id: str | None = None,
    ) -> ObjectiveProjection:
        """Author a new objective from a validated spec.

        Raises:
          - UnresolvedObjectiveError: parent_id set but parent doesn't exist.
          - DAGRejected: parent_id is self (trivial cycle).

        Longer cycle detection is not needed — every objective has at
        most one parent, and a new objective cannot yet be an ancestor
        of its parent because it didn't exist before this call.
        """
        oid = objective_id or f"obj-{uuid.uuid4()}"
        if spec.parent_id == oid:
            raise DAGRejected(f"objective cannot be its own parent: {oid!r}")

        with obs.operation_span(
            "objective_tracker.create",
            **{
                "loam.objective.id": oid,
                "loam.objective.authored_by": spec.authored_by,
                "loam.objective.parent_id": spec.parent_id,
            },
        ) as span:
            if spec.parent_id is not None:
                parent_row = self._store.read_state(spec.parent_id)
                if parent_row is None and not self._store.events_for(spec.parent_id):
                    raise UnresolvedObjectiveError(spec.parent_id)

            async with await self._lock_for(oid):
                ev = self._append(
                    ObjectiveCreated(
                        objective_id=oid,
                        goal=spec.goal,
                        parent_id=spec.parent_id,
                        acceptance_criteria=spec.acceptance_criteria,
                        time_bound=spec.time_bound,
                        authored_by=spec.authored_by,
                        owner=spec.owner,
                        parent_close_policy=spec.parent_close_policy,
                        lifted_from=spec.lifted_from,
                        belongs_to_project=spec.belongs_to_project,
                        tagged_streams=spec.tagged_streams,
                        priority=spec.priority,
                    ),
                    span=span,
                )
                self._fan_out(oid, ev)
                proj = self._project(oid)
                self._persist(proj)
                self._register_scope_success_subscriptions(oid, spec.acceptance_criteria)
                obs.add_event(
                    span,
                    "objective.created",
                    {"loam.objective.id": oid, "loam.objective.status": proj.status.value},
                )
                return public_projection(proj)

    async def decompose_into_children(
        self,
        parent_id: str,
        child_specs: Sequence[ObjectiveSpec],
    ) -> list[ObjectiveProjection]:
        """Atomic multi-create of children under `parent_id`.

        Every child_spec must already have parent_id == parent_id
        (callers are explicit, not implicit). A parent that doesn't
        exist raises UnresolvedObjectiveError.
        """
        if self._store.read_state(parent_id) is None and not self._store.events_for(parent_id):
            raise UnresolvedObjectiveError(parent_id)
        for cs in child_specs:
            if cs.parent_id != parent_id:
                raise DAGRejected(
                    f"child spec parent_id {cs.parent_id!r} does not match "
                    f"requested parent {parent_id!r}"
                )
        out: list[ObjectiveProjection] = []
        for cs in child_specs:
            out.append(await self.create(cs))
        return out

    # ------------------------------------------------------------------
    # Public API: lifecycle transitions
    # ------------------------------------------------------------------

    async def start(
        self, objective_id: str, *, rationale: str | None = None
    ) -> ObjectiveProjection:
        return await self._transition(
            objective_id,
            ObjectiveStatus.active,
            rationale=rationale,
            operation="start",
        )

    async def mark_achieved(
        self, objective_id: str, *, evidence: str | None = None
    ) -> ObjectiveProjection:
        return await self._transition(
            objective_id,
            ObjectiveStatus.achieved,
            evidence=evidence,
            operation="mark_achieved",
        )

    async def mark_owner_pending(
        self, objective_id: str, *, evidence: str | None = None
    ) -> ObjectiveProjection:
        """Transition `active → owner_pending`: work shipped, owner
        ruling pending (session-`/clear`-safety R2).

        Distinct from `mark_achieved` (closed) and from leaving the
        objective `active` (no signal it is owner-blocked). The
        session-start digest surfaces an `owner_pending` objective as
        an open loop awaiting the owner, never as done (R2.2, in R1's
        primary-persona digest fence per D-SCS.4). `evidence` records
        what shipped — optional, mirroring `mark_achieved`; no mandatory
        rationale because this is not a terminal/corrective transition.
        """
        return await self._transition(
            objective_id,
            ObjectiveStatus.owner_pending,
            evidence=evidence,
            operation="mark_owner_pending",
        )

    async def mark_blocked(
        self, objective_id: str, *, evidence: str | None = None
    ) -> ObjectiveProjection:
        """Transition `active → blocked`: started but parked on a blocker
        (WMS increment 2, AC.WI.1).

        Distinct from `active` (in progress, unblocked) and
        `owner_pending` (shipped, owner-blocked). `evidence` records what
        the item is blocked on — optional, mirroring `mark_owner_pending`.
        The unblocked-next query (AC.WI.EDGE.2) reads the edge graph; this
        status is the lifecycle signal that an item is parked. Not
        terminal; leaves back to `active` via :meth:`unblock`."""
        return await self._transition(
            objective_id,
            ObjectiveStatus.blocked,
            evidence=evidence,
            operation="mark_blocked",
        )

    async def unblock(
        self, objective_id: str, *, evidence: str | None = None
    ) -> ObjectiveProjection:
        """Transition `blocked → active`: the blocker cleared (WMS
        increment 2, AC.WI.1)."""
        return await self._transition(
            objective_id,
            ObjectiveStatus.active,
            evidence=evidence,
            operation="unblock",
        )

    async def mark_abandoned(
        self, objective_id: str, *, rationale: str
    ) -> ObjectiveProjection:
        if not rationale or not rationale.strip():
            raise MissingRationaleError(
                "mark_abandoned requires a non-empty rationale."
            )
        return await self._transition(
            objective_id,
            ObjectiveStatus.abandoned,
            rationale=rationale,
            operation="mark_abandoned",
        )

    async def re_open(
        self, objective_id: str, *, rationale: str
    ) -> ObjectiveProjection:
        """Return a terminal objective to `active` with audit rationale.

        Luke's decision (brief §"Luke's decisions"): rationale is
        mandatory. Empty or whitespace rationale → MissingRationaleError.
        """
        if not rationale or not rationale.strip():
            raise MissingRationaleError(
                "re_open requires a non-empty rationale string."
            )
        return await self._transition(
            objective_id,
            ObjectiveStatus.active,
            rationale=rationale,
            operation="re_open",
        )

    async def _transition(
        self,
        objective_id: str,
        to_status: ObjectiveStatus,
        *,
        evidence: str | None = None,
        rationale: str | None = None,
        operation: str,
    ) -> ObjectiveProjection:
        proj = self._project(objective_id)
        if not proj.goal:
            raise UnresolvedObjectiveError(objective_id)
        with obs.operation_span(
            f"objective_tracker.{operation}",
            **{
                "loam.objective.id": objective_id,
                "loam.objective.authored_by": proj.authored_by,
                "loam.objective.status": proj.status.value,
            },
        ) as span:
            async with await self._lock_for(objective_id):
                proj = self._project(objective_id)
                if to_status == proj.status:
                    return public_projection(proj)
                if not is_legal(proj.status, to_status):
                    raise IllegalTransitionError(
                        f"Illegal transition {proj.status.value} → "
                        f"{to_status.value} on {objective_id!r}"
                    )
                ev = self._append(
                    StatusTransitioned(
                        objective_id=objective_id,
                        from_status=proj.status,
                        to_status=to_status,
                        evidence=evidence,
                        rationale=rationale,
                    ),
                    span=span,
                )
                obs.add_event(
                    span,
                    "objective.status_changed",
                    {
                        "from": proj.status.value,
                        "to": to_status.value,
                        "rationale": rationale or "",
                        "evidence": evidence or "",
                    },
                )
                self._fan_out(objective_id, ev)
                new_proj = self._project(objective_id)
                self._persist(new_proj)
                # If parent just reached a terminal state, notify children.
                if is_terminal(to_status):
                    await self._notify_children(objective_id, to_status)
                return public_projection(new_proj)

    async def _notify_children(
        self,
        parent_id: str,
        parent_status: ObjectiveStatus,
    ) -> None:
        kind = (
            ParentCloseEventKind.achieved
            if parent_status == ObjectiveStatus.achieved
            else ParentCloseEventKind.abandoned
        )
        children = self._store.list_states(parent_id=parent_id)
        for child_row in children:
            cid = child_row["objective_id"]
            policy = ParentClosePolicy(child_row["parent_close_policy"])
            async with await self._lock_for(cid):
                ev = self._append(
                    ParentClosed(
                        objective_id=cid,
                        parent_id=parent_id,
                        parent_event=kind,
                        applied_policy=policy,
                    )
                )
                self._fan_out(cid, ev)
                self._persist(self._project(cid))

            if policy == ParentClosePolicy.notify:
                continue
            if policy == ParentClosePolicy.terminate:
                # A per-child "terminate" override means the child
                # should go to the same terminal state as the parent.
                child_proj = self._project(cid)
                if is_terminal(child_proj.status):
                    continue
                # Terminate-as-abandoned by default; if parent was
                # achieved, mark child achieved only if policy author
                # said so — the abstract "terminate" in pOS semantics
                # maps to `abandoned` (safer default, per scope-of-work
                # convention).
                target = ObjectiveStatus.abandoned
                if child_proj.status == ObjectiveStatus.proposed:
                    # proposed → abandoned is legal.
                    await self._transition(
                        cid,
                        target,
                        rationale=f"parent_closed:{parent_id}",
                        operation="parent_terminate",
                    )
                elif child_proj.status == ObjectiveStatus.active:
                    await self._transition(
                        cid,
                        target,
                        rationale=f"parent_closed:{parent_id}",
                        operation="parent_terminate",
                    )
            elif policy == ParentClosePolicy.abandon:
                child_proj = self._project(cid)
                if is_terminal(child_proj.status):
                    continue
                await self._transition(
                    cid,
                    ObjectiveStatus.abandoned,
                    rationale=f"parent_closed:{parent_id}",
                    operation="parent_abandon",
                )

    # ------------------------------------------------------------------
    # Public API: criterion evaluation
    # ------------------------------------------------------------------

    async def evaluate_criterion(
        self,
        objective_id: str,
        *,
        criterion_id: str,
        result: str,
        rationale: str | None = None,
        source: str = "caller",
    ) -> ObjectiveProjection:
        if result not in ("met", "not_met"):
            raise ValueError(f"result must be 'met' or 'not_met'; got {result!r}")
        proj = self._project(objective_id)
        if not proj.goal:
            raise UnresolvedObjectiveError(objective_id)
        criterion_ids = {c.criterion_id for c in proj.criteria}
        if criterion_id not in criterion_ids:
            raise ValueError(
                f"criterion_id {criterion_id!r} is not declared on "
                f"objective {objective_id!r}"
            )
        with obs.operation_span(
            "objective_tracker.evaluate_criterion",
            **{
                "loam.objective.id": objective_id,
                "loam.objective.criterion_id": criterion_id,
                "loam.objective.status": proj.status.value,
            },
        ) as span:
            async with await self._lock_for(objective_id):
                ev = self._append(
                    CriterionEvaluated(
                        objective_id=objective_id,
                        criterion_id=criterion_id,
                        result=result,  # type: ignore[arg-type]
                        rationale=rationale,
                        source=source,
                    ),
                    span=span,
                )
                obs.add_event(
                    span,
                    "objective.criterion_evaluated",
                    {
                        "criterion_id": criterion_id,
                        "result": result,
                        "source": source,
                    },
                )
                self._fan_out(objective_id, ev)
                new_proj = self._project(objective_id)
                self._persist(new_proj)
                return public_projection(new_proj)

    def child_closure_status(
        self, objective_id: str, criterion_id: str
    ) -> tuple[int, int, bool]:
        """Compute N-of-M child_closure result on demand.

        Returns (achieved_child_count, required_count, is_met). The
        caller decides when to push an evaluation via evaluate_criterion.
        """
        proj = self._project(objective_id)
        if not proj.goal:
            raise UnresolvedObjectiveError(objective_id)
        criterion = next(
            (c for c in proj.criteria if c.criterion_id == criterion_id), None
        )
        if criterion is None or criterion.kind != "child_closure":
            raise ValueError(
                f"criterion_id {criterion_id!r} is not a child_closure on "
                f"objective {objective_id!r}"
            )
        children = self._store.list_states(
            parent_id=objective_id, status=[ObjectiveStatus.achieved.value]
        )
        achieved = len(children)
        required = criterion.required_count  # type: ignore[attr-defined]
        return achieved, required, achieved >= required

    # ------------------------------------------------------------------
    # Public API: scope binding (sidecar enforcement)
    # ------------------------------------------------------------------

    async def bind_scope(
        self, scope_id: str, objective_id: str
    ) -> dict[str, Any]:
        """Bind a scope to an objective. Enforces root-user invariant.

        Raises:
          - UnresolvedObjectiveError: objective doesn't exist.
          - OrphanRootError: ancestry does not terminate at a
            user-authored root.
        """
        with obs.operation_span(
            "objective_tracker.bind_scope",
            **{
                "loam.scope.id": scope_id,
                "loam.objective.id": objective_id,
            },
        ) as span:
            chain = self.trace_to_root(objective_id)
            terminal = chain[-1]
            if terminal.authored_by != "user":
                raise OrphanRootError(
                    objective_id=objective_id,
                    terminal_root_id=terminal.objective_id,
                    terminal_authored_by=terminal.authored_by,
                )
            async with await self._lock_for(objective_id):
                ev = self._append(
                    ScopeBound(objective_id=objective_id, scope_id=scope_id),
                    span=span,
                )
                bound_at = datetime.now(timezone.utc).isoformat()
                self._store.upsert_binding(
                    scope_id=scope_id,
                    objective_id=objective_id,
                    bound_event_id=ev.event_id,
                    bound_at=bound_at,
                )
                obs.add_event(
                    span,
                    "objective.scope_bound",
                    {"scope_id": scope_id, "objective_id": objective_id},
                )
                self._persist(self._project(objective_id))
                self._fan_out(objective_id, ev)
                return {
                    "scope_id": scope_id,
                    "objective_id": objective_id,
                    "bound_event_id": ev.event_id,
                    "bound_at": bound_at,
                }

    def get_binding(self, scope_id: str) -> dict[str, Any] | None:
        return self._store.read_binding(scope_id)

    def is_scope_bound(self, scope_id: str) -> bool:
        return self._store.read_binding(scope_id) is not None

    # ------------------------------------------------------------------
    # Public API: the relational graph (WMS increment 2 — AC.WI.EDGE.*)
    # ------------------------------------------------------------------

    async def record_edge(
        self,
        from_id: str,
        *,
        edge_kind: WorkEdgeKind,
        to_id: str | None = None,
        party: str | None = None,
    ) -> ObjectiveProjection:
        """Record a non-tree edge `from_id --edge_kind--> to_id`
        (AC.WI.EDGE.1).

        A `waits_on` edge may name an external ``party`` (with ``to_id``
        left None) — "the launch waits on Eric". An item-to-item edge
        names ``to_id``; the edge then surfaces on BOTH endpoints'
        projections (the `from`'s `edges_out`, the `to`'s `edges_in`).
        ``from_id`` must exist; an item-to-item edge's ``to_id`` must
        exist too (no edge fabrication against a non-existent item —
        AC.WI.EDGE.3). Re-recording an active edge is idempotent.

        Returns the updated projection of ``from_id``."""
        if to_id is None and party is None:
            raise ValueError(
                "record_edge requires either a to_id (item-to-item edge) "
                "or a party (external-party wait)"
            )
        if self._store.read_state(from_id) is None and not self._store.events_for(from_id):
            raise UnresolvedObjectiveError(from_id)
        if to_id is not None:
            if self._store.read_state(to_id) is None and not self._store.events_for(to_id):
                raise UnresolvedObjectiveError(to_id)
        async with await self._lock_for(from_id):
            ev = self._append(
                WorkEdge(
                    objective_id=from_id,
                    to_id=to_id,
                    edge_kind=edge_kind,
                    party=party,
                )
            )
            self._fan_out(from_id, ev)
            self._persist(self._project(from_id))
        return self.get(from_id)  # type: ignore[return-value]

    async def clear_edge(
        self,
        from_id: str,
        *,
        edge_kind: WorkEdgeKind,
        to_id: str | None = None,
        party: str | None = None,
    ) -> ObjectiveProjection:
        """Retract a previously-recorded edge (AC.WI.EDGE.1).

        Matches on (``from_id``, ``to_id``, ``edge_kind``, ``party``);
        after clearing, the edge no longer surfaces on either endpoint.
        Clearing an edge that was never recorded is a no-op (idempotent —
        AC.WI.EDGE.3). Returns the updated projection of ``from_id``."""
        async with await self._lock_for(from_id):
            ev = self._append(
                WorkEdgeCleared(
                    objective_id=from_id,
                    to_id=to_id,
                    edge_kind=edge_kind,
                    party=party,
                )
            )
            self._fan_out(from_id, ev)
            self._persist(self._project(from_id))
        return self.get(from_id)  # type: ignore[return-value]

    def _edges_in_for(self, objective_id: str) -> tuple[WorkEdgeRecord, ...]:
        """Resolve the active edges pointing AT ``objective_id`` by folding
        every item's outgoing edges (AC.WI.EDGE.1).

        Enumerates the source objective-ids from the EVENT LOG (not the
        projection cache) so incoming edges reconstruct from events alone
        after a cold rebuild — the single-source-of-truth invariant
        (AC.WI.2). A per-stream projection only sees its own outgoing
        edges; this scans every other item's stream so an edge surfaces
        on the `to` endpoint too. Cleared edges are already removed by the
        per-item fold, so only currently-active incoming edges return."""
        source_ids: set[str] = set()
        for ev in self._store.all_events():
            other_id = getattr(ev, "objective_id", None)
            if other_id is not None and other_id != objective_id:
                source_ids.add(other_id)
        incoming: list[WorkEdgeRecord] = []
        for other_id in source_ids:
            proj = self._project(other_id)
            for e in proj.edges_out:
                if e.to_id == objective_id:
                    incoming.append(e)
        return tuple(incoming)

    def unblocked_next(
        self,
        *,
        authored_by: str | None = None,
    ) -> tuple[ObjectiveProjection, ...]:
        """Return the open work items that are NOT waiting on any
        unresolved blocker — the "next unblocked thing" query
        (AC.WI.EDGE.2).

        An item is "next" iff it is OPEN (proposed / active / blocked /
        owner_pending — not terminal) AND has no active `waits_on` edge
        AND is not the `to` of an active `blocks` edge from an OPEN item.
        An item whose only outstanding wait is on an EXTERNAL party is
        reported as waiting-on-other (NOT next) — it is excluded from the
        unblocked set. Method-level note: terminal blockers do not count
        (a `waits_on` an achieved/abandoned item no longer blocks)."""
        open_states = {
            ObjectiveStatus.proposed,
            ObjectiveStatus.active,
            ObjectiveStatus.blocked,
            ObjectiveStatus.owner_pending,
        }
        rows = self._store.list_states(authored_by=authored_by)
        all_open = [
            self.get(r["objective_id"])
            for r in rows
            if (g := self.get(r["objective_id"])) is not None
            and g.status in open_states
        ]
        open_ids = {p.objective_id for p in all_open}

        def _is_unresolved_target(target_id: str | None) -> bool:
            if target_id is None:
                return False
            tgt = self.get(target_id)
            return tgt is not None and tgt.status in open_states

        out: list[ObjectiveProjection] = []
        for proj in all_open:
            waiting = False
            # The item's own waits_on edges: unresolved if the target is
            # an open item, OR if it waits on an external party.
            for e in proj.edges_out:
                if e.edge_kind == WorkEdgeKind.waits_on:
                    if e.party is not None or _is_unresolved_target(e.to_id):
                        waiting = True
                        break
            if waiting:
                continue
            # An active `blocks` edge from an OPEN item targeting this
            # item means this item is blocked (the inverse direction).
            for e in self._edges_in_for(proj.objective_id):
                if (
                    e.edge_kind == WorkEdgeKind.blocks
                    and e.from_id in open_ids
                ):
                    waiting = True
                    break
            if not waiting:
                out.append(proj)
        return tuple(out)

    def waiting_on_other(self) -> tuple[ObjectiveProjection, ...]:
        """Return the open items whose only outstanding wait is on an
        EXTERNAL party (AC.WI.EDGE.2) — reported as waiting-on-other, not
        as next. An item with a `waits_on` edge that names a ``party`` is
        in this set."""
        open_states = {
            ObjectiveStatus.proposed,
            ObjectiveStatus.active,
            ObjectiveStatus.blocked,
            ObjectiveStatus.owner_pending,
        }
        out: list[ObjectiveProjection] = []
        for r in self._store.list_states():
            proj = self.get(r["objective_id"])
            if proj is None or proj.status not in open_states:
                continue
            if any(
                e.edge_kind == WorkEdgeKind.waits_on and e.party is not None
                for e in proj.edges_out
            ):
                out.append(proj)
        return tuple(out)

    # ------------------------------------------------------------------
    # Public API: queries
    # ------------------------------------------------------------------

    def get(self, objective_id: str) -> ObjectiveProjection | None:
        events = self._store.events_for(objective_id)
        if not events:
            return None
        # WMS increment 2 — resolve the incoming edges (where this item is
        # the `to`) so an edge surfaces on BOTH endpoints (AC.WI.EDGE.1).
        # The per-stream projection only carries this item's outgoing
        # edges; incoming edges are folded from the other items' streams.
        edges_in = self._edges_in_for(objective_id)
        return public_projection(
            project(objective_id, events), edges_in=edges_in
        )

    def list(
        self,
        *,
        parent_id: str | None = None,
        status: Sequence[ObjectiveStatus] | None = None,
        authored_by: str | None = None,
        is_root: bool | None = None,
        with_unchecked_criteria: bool | None = None,
    ) -> list[ObjectiveProjection]:
        rows = self._store.list_states(
            parent_id=parent_id,
            status=[s.value for s in status] if status else None,
            authored_by=authored_by,
            is_root=is_root,
        )
        out: list[ObjectiveProjection] = []
        for r in rows:
            proj = public_projection(self._project(r["objective_id"]))
            if with_unchecked_criteria is True and not proj.unchecked_criteria():
                continue
            if with_unchecked_criteria is False and proj.unchecked_criteria():
                continue
            out.append(proj)
        return out

    def list_by_root(
        self,
        root_id: str,
        *,
        states: Sequence[ObjectiveStatus] | None = None,
        with_unchecked_criteria: bool | None = None,
    ) -> list[ObjectiveProjection]:
        """Walk the entire descendant set under `root_id`.

        The root itself IS included. Filters match `list()`.
        """
        visited: set[str] = set()
        out: list[ObjectiveProjection] = []
        stack: list[str] = [root_id]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            proj = self.get(cur)
            if proj is None:
                continue
            if states and proj.status not in states:
                pass
            else:
                if (
                    with_unchecked_criteria is True
                    and not proj.unchecked_criteria()
                ):
                    pass
                elif (
                    with_unchecked_criteria is False
                    and proj.unchecked_criteria()
                ):
                    pass
                else:
                    out.append(proj)
            for child_row in self._store.list_states(parent_id=cur):
                stack.append(child_row["objective_id"])
        return out

    def query_projection_view(
        self, filter: ObjectiveFilter | None = None
    ) -> tuple[ObjectiveProjection, ...]:
        """Return projections matching `filter` in deterministic order.

        Amendment #38: the surface every Heavy-B downstream consumer
        composes against (loam amend's `project` subcommand, primary-
        persona's tracker-context contributor). An empty / `None`
        filter returns the full record set in `last_event_id` ASC
        order — the same ordering `list_states` already exposes, so
        the ordering is stable across calls on a stable DB.

        Filter semantics: every set field is an equality match
        AND-ed together. A filter that names
        `lifted_from_source_doc` excludes records whose
        `lifted_from is None`.
        """
        flt = filter if filter is not None else ObjectiveFilter()
        rows = self._store.list_states(
            authored_by=flt.authored_by,
        )
        out: list[ObjectiveProjection] = []
        for r in rows:
            proj = public_projection(self._project(r["objective_id"]))
            if flt.lifted_from_source_doc is not None:
                if proj.lifted_from is None:
                    continue
                if proj.lifted_from.source_doc != flt.lifted_from_source_doc:
                    continue
            out.append(proj)
        return tuple(out)

    def trace_to_root(self, objective_id: str) -> list[ObjectiveProjection]:
        """Return the ordered ancestor chain, terminal root last.

        The objective itself is the first element; the terminal root
        is the last. A missing parent along the way raises
        UnresolvedObjectiveError.
        """
        chain: list[ObjectiveProjection] = []
        visited: set[str] = set()
        cur = self.get(objective_id)
        if cur is None:
            raise UnresolvedObjectiveError(objective_id)
        while cur is not None:
            if cur.objective_id in visited:
                raise DAGRejected(
                    f"cycle detected in ancestry of {objective_id!r} at "
                    f"{cur.objective_id!r}"
                )
            visited.add(cur.objective_id)
            chain.append(cur)
            if cur.parent_id is None:
                break
            nxt = self.get(cur.parent_id)
            if nxt is None:
                raise UnresolvedObjectiveError(cur.parent_id)
            cur = nxt
        return chain

    def snapshot(self, target_path: str | Path) -> Path:
        return self._store.snapshot_to(target_path)

    # ------------------------------------------------------------------
    # Public API: objective-manifest registry (structural-enforcement A1)
    # ------------------------------------------------------------------

    def register_source_binding(
        self,
        *,
        component: str,
        ac_id: str,
        source_path_glob: str,
    ) -> None:
        """Register a (component, ac_id, source_path_glob) manifest row.

        AC.SE.6 / AC.SE.7. Idempotent on duplicate. Raises
        ``ManifestRowError`` on empty fields or invalid fnmatch
        patterns. The refusal is observable to the caller without
        leaking a SQLite exception.
        """
        self._store.insert_manifest_row(
            component=component,
            ac_id=ac_id,
            source_path_glob=source_path_glob,
        )

    def manifest_rows_for_component(
        self, component: str
    ) -> list[dict[str, Any]]:
        """All manifest rows for ``component`` (AC.SE.6)."""
        return self._store.list_manifest_rows_for_component(component)

    def manifest_rows_for_ac(
        self, component: str, ac_id: str
    ) -> list[dict[str, Any]]:
        """All manifest rows for the (component, ac_id) tuple (AC.SE.6)."""
        return self._store.list_manifest_rows_for_ac(component, ac_id)

    def manifest_rows_matching_source_path(
        self, workspace_relative_path: str
    ) -> list[dict[str, Any]]:
        """Every manifest row whose glob matches the path (AC.SE.6)."""
        return self._store.list_manifest_rows_matching_source_path(
            workspace_relative_path
        )

    async def poll_external_events(self, last_event_id: int = 0) -> int:
        new_events = self._store.events_since(last_event_id)
        for ev in new_events:
            self._fan_out(ev.objective_id, ev)
        return new_events[-1].event_id if new_events else last_event_id

    # ------------------------------------------------------------------
    # pyee fan-out and scope-success subscriptions
    # ------------------------------------------------------------------

    def subscribe(
        self, objective_id: str, callback: Callable[[Any], Any]
    ) -> None:
        self._emitter.on(f"objective:{objective_id}", callback)

    def subscribe_all(self, callback: Callable[[Any], Any]) -> None:
        self._emitter.on("*", callback)

    def _register_scope_success_subscriptions(
        self, objective_id: str, criteria: Iterable[Criterion]
    ) -> None:
        for c in criteria:
            if isinstance(c, ScopeSuccessCriterion):
                subs = self._scope_subscriptions.setdefault(c.scope_id, [])
                subs.append((objective_id, c))
                # Re-bind to already-registered scope emitters.
                for emitter in self._scope_emitters:
                    self._bind_scope_success_listener(emitter, c.scope_id)

    def _bind_scope_success_listener(self, emitter: Any, scope_id: str) -> None:
        event_name = f"scope:{scope_id}"
        subs_ref = self._scope_subscriptions

        async def _handler(event: Any) -> None:
            # Scope-of-work StateTransitioned carries .to_state
            to_state = getattr(event, "to_state", None)
            if to_state is None:
                return
            state_value = getattr(to_state, "value", str(to_state))
            for oid, criterion in list(subs_ref.get(scope_id, [])):
                success_states = set(criterion.success_states)
                if state_value in success_states:
                    await self.evaluate_criterion(
                        oid,
                        criterion_id=criterion.criterion_id,
                        result="met",
                        rationale=f"scope {scope_id} → {state_value}",
                        source="scope_success_auto",
                    )
                elif state_value in {"failed", "cancelled"}:
                    await self.evaluate_criterion(
                        oid,
                        criterion_id=criterion.criterion_id,
                        result="not_met",
                        rationale=f"scope {scope_id} → {state_value}",
                        source="scope_success_auto",
                    )

        emitter.on(event_name, _handler)

    def subscribe_scope_emitter(self, scope_emitter: Any) -> None:
        """Hook a scope-of-work pyee emitter so ScopeSuccessCriterion
        auto-evaluates on scope state-change events.

        Call this once after constructing the tracker, passing
        `scope_runtime.emitter`. Brief §"Eve's inferences" flagged the
        hook shape — this is the implementation.
        """
        self._scope_emitters.append(scope_emitter)
        for scope_id in list(self._scope_subscriptions.keys()):
            self._bind_scope_success_listener(scope_emitter, scope_id)

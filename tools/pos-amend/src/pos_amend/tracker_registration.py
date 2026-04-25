"""Tracker registration helper — schema v2 ``objectives`` block bridge.

Translates the manifest-level ``ObjectiveEntry`` shape into runtime
``ObjectiveSpec`` records inside the workspace's tracker DB. Provides
two synchronous public entry points:

- ``register_objectives(manifest, repo_root)`` — called from
  ``pos-amend apply`` (non-dry-run); creates one tracker record per
  manifest entry, idempotently. Returns a ``RegistrationResult``.

- ``update_source_commits(manifest, repo_root, amendment_sha)`` —
  called from ``pos-amend seal`` after the amendment SHA is known;
  rewrites every registered record so its ``lifted_from.source_commit``
  equals ``amendment_sha``. Returns the count of records updated.

Plan: ``docs/rebuild/plans/pos-amend-tracker-integration.md``.

Method-level decisions (D-build.x) are documented in
``pos-amend-tracker-integration.builder-plan.md``.

Tracker-DB-path resolution (D-build.4 (a)): tracker DB lives at
``<repo_root>/objective_tracker.sqlite`` — same convention every
existing consumer (`workspace_bootstrap.adapters.tracker_seed`,
`primary_persona.tracker_context`) uses.

Source-commit resolution at seal time (D-build.3 (a)): caller (the
seal step) reads HEAD itself and passes ``amendment_sha`` in. This
helper does NOT call git; that responsibility lives in the seal step
that already reads HEAD for its own commit-message construction.
"""

from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# objective_tracker is an installed dep of the workspace's shared venv
# (transitive via workspace_bootstrap). The import lives at module top
# so an `objective_tracker` import failure surfaces as a structured
# tracker-unavailable diagnostic at apply time (AC.D-pa.5 path).
from objective_tracker import (
    ChildClosureCriterion,
    ExternalPredicateCriterion,
    LiftedFrom,
    ObjectiveFilter,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    ScopeSuccessCriterion,
    TimeBound,
)
from objective_tracker.spec import Criterion

from pos_amend.manifest import LiftedFromEntry, Manifest, ObjectiveEntry


TRACKER_DB_FILENAME = "objective_tracker.sqlite"
"""Filename convention. Mirrors
``workspace_bootstrap.adapters.tracker_seed.TRACKER_DB_FILENAME`` and
``primary_persona.tracker_context.TRACKER_DB_FILENAME``. Inlined so
pos-amend has no runtime dep on workspace-bootstrap or primary-persona.
"""


# ---- exceptions ------------------------------------------------------


class TrackerUnavailableError(Exception):
    """Raised when the workspace's tracker DB cannot be opened.

    Cases (per AC.D-pa.5): missing file under a fresh workspace
    (rare — first-run seeds the file), corrupt SQLite (the file
    exists but the header is malformed), permission error
    (operator-permission misconfiguration), schema-version mismatch
    (rare — the upgrader runs at first-run / startup but a stale
    file from a prior pre-#38 workspace would surface here).

    Carries a short failure-class label and an operator-readable
    detail message so callers can render a structured diagnostic.
    """

    def __init__(self, klass: str, detail: str) -> None:
        super().__init__(detail)
        self.klass = klass
        self.detail = detail


# ---- public result shape --------------------------------------------


@dataclass(frozen=True)
class RegistrationResult:
    """Outcome of one ``register_objectives`` invocation.

    ``created`` names the source_ac labels for which a fresh tracker
    record was created on this call. ``skipped`` names entries that
    were already present (idempotency case). The two together account
    for every manifest entry passed in.
    """

    created: tuple[str, ...]
    skipped: tuple[str, ...]


# ---- helpers ---------------------------------------------------------


def tracker_db_path_for(repo_root: Path | str) -> Path:
    """Resolve the tracker-DB path inside *repo_root*.

    Pure function (no I/O). Mirrors the same-named helpers in
    workspace-bootstrap and primary-persona so the three consumers
    target the same file by construction.
    """
    return Path(repo_root) / TRACKER_DB_FILENAME


def _entry_key(entry: ObjectiveEntry | LiftedFromEntry) -> tuple[str, str]:
    """Return the (source_doc, source_ac) idempotency key for an entry."""
    if isinstance(entry, ObjectiveEntry):
        return (entry.lifted_from.source_doc, entry.lifted_from.source_ac)
    return (entry.source_doc, entry.source_ac)


def _build_criterion(raw: dict[str, Any]) -> Criterion:
    """Translate a manifest-AC dict into a runtime ``Criterion``.

    Discriminator-key dispatch on ``kind`` (matches the runtime
    union's discriminator). Errors propagate to the caller as
    ``ValueError`` / ``KeyError`` from the underlying Pydantic model.
    """
    kind = raw.get("kind")
    fields = {k: v for k, v in raw.items() if k != "kind"}
    if kind == "prose":
        return ProseCriterion(**fields)
    if kind == "scope_success":
        return ScopeSuccessCriterion(**fields)
    if kind == "child_closure":
        return ChildClosureCriterion(**fields)
    if kind == "external_predicate":
        return ExternalPredicateCriterion(**fields)
    raise ValueError(
        f"unknown acceptance-criterion kind {kind!r}; expected one of "
        "'prose', 'scope_success', 'child_closure', 'external_predicate'"
    )


def _build_time_bound(raw: dict[str, Any]) -> TimeBound:
    """Translate a manifest time_bound dict into a runtime ``TimeBound``."""
    return TimeBound(**raw)


def _entry_to_spec(entry: ObjectiveEntry) -> ObjectiveSpec:
    """Translate a manifest ``ObjectiveEntry`` into ``ObjectiveSpec``.

    Method note: ``parent_root: true`` maps to ``parent_id=None``;
    a non-None ``parent_id`` is passed through. Acceptance criteria
    are translated via ``_build_criterion``. The runtime spec re-
    validates every field; this layer just shapes the call.
    """
    parent_id = None if entry.parent_root else entry.parent_id
    criteria = tuple(_build_criterion(c) for c in entry.acceptance_criteria)
    spec = ObjectiveSpec(
        goal=entry.goal,
        parent_id=parent_id,
        acceptance_criteria=criteria,
        time_bound=_build_time_bound(entry.time_bound),
        authored_by=entry.authored_by,
        lifted_from=LiftedFrom(
            source_doc=entry.lifted_from.source_doc,
            source_ac=entry.lifted_from.source_ac,
        ),
    )
    return spec


def _open_tracker(db_path: Path) -> ObjectiveTracker:
    """Open the tracker at *db_path*, raising ``TrackerUnavailableError``.

    Failure-class labels (per AC.D-pa.5):

    - ``tracker-db-missing-parent`` — the workspace dir doesn't exist
    - ``tracker-db-corrupt`` — sqlite refuses to open
    - ``tracker-db-permission`` — file/dir permission rejection
    - ``tracker-db-schema-mismatch`` — pre-amendment-#38 schema
      surfaced via the upgrader's failure mode

    Callers receive a ``TrackerUnavailableError`` with klass + detail;
    no partial state is created (``ObjectiveTracker.__init__`` either
    succeeds entirely or raises).
    """
    if not db_path.parent.exists():
        raise TrackerUnavailableError(
            klass="tracker-db-missing-parent",
            detail=(
                f"tracker DB parent directory does not exist: "
                f"{db_path.parent}\n"
                "Workspace layout suggests pos-v2 first-run did not "
                "complete on this checkout. Run first-run before "
                "invoking `pos-amend apply` against a manifest that "
                "carries an `objectives` block."
            ),
        )
    try:
        return ObjectiveTracker(db_path)
    except sqlite3.DatabaseError as exc:
        raise TrackerUnavailableError(
            klass="tracker-db-corrupt",
            detail=(
                f"tracker DB at {db_path} could not be opened "
                f"(SQLite reports: {exc}). Refusing to register "
                "objectives. Restore from snapshot or re-run "
                "first-run on this checkout."
            ),
        ) from exc
    except PermissionError as exc:
        raise TrackerUnavailableError(
            klass="tracker-db-permission",
            detail=(
                f"tracker DB at {db_path} is not readable/writable "
                f"by the current user (OS reports: {exc}). Refusing "
                "to register objectives."
            ),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        # Schema-version-mismatch errors arrive from the upgrader
        # at runtime startup; they're heterogeneous in shape so we
        # catch broadly and re-raise as a structured failure class.
        # AC.D-pa.5 names "no partial registration" — the tracker
        # constructor either succeeds or this path runs.
        raise TrackerUnavailableError(
            klass="tracker-db-schema-mismatch",
            detail=(
                f"tracker DB at {db_path} could not be opened; the "
                f"underlying error was: {exc!r}. Refusing to register "
                "objectives. Inspect the file or re-run first-run."
            ),
        ) from exc


# ---- registration: apply-time ---------------------------------------


def register_objectives(
    manifest: Manifest, repo_root: Path | str
) -> RegistrationResult:
    """Register every ``manifest.objectives`` entry in the workspace tracker.

    Idempotent (AC.D-pa.2): entries whose ``(source_doc, source_ac)``
    pair already exists in the tracker are skipped. The function is
    a no-op when ``manifest.objectives`` is empty (v1 manifests).

    Raises ``TrackerUnavailableError`` if the tracker DB is unreadable;
    the caller (apply.run) translates that into a structured exit-3
    diagnostic. AC.D-pa.5 names "no partial registration"; the
    sequencing here honours that: we open the tracker first, then
    create records one by one inside a single ``try``/``finally``
    that closes the handle. A mid-loop failure (e.g. one entry
    triggers a ValidationError) propagates without partial commits
    being possible, but those are authoring errors, not
    tracker-unavailability and not in AC.D-pa.5's scope. We let the
    pydantic ValidationError surface verbatim — the manifest author
    must fix their manifest.
    """
    if not manifest.objectives:
        return RegistrationResult(created=(), skipped=())

    repo_root_p = Path(repo_root)
    db_path = tracker_db_path_for(repo_root_p)
    tracker = _open_tracker(db_path)
    try:
        # Build the existing-record set keyed by (source_doc, source_ac).
        # The plan-doc is typically the manifest's ``plan`` field, but
        # entries may name a different ``source_doc`` (e.g. an
        # external research artefact). We query by each entry's
        # source_doc to be conservative.
        existing_keys: set[tuple[str, str]] = set()
        # Collect distinct source_docs across the manifest entries to
        # avoid one query per entry (a small optimisation; matters
        # when N is large).
        source_docs = {e.lifted_from.source_doc for e in manifest.objectives}
        for source_doc in source_docs:
            projections = tracker.query_projection_view(
                ObjectiveFilter(lifted_from_source_doc=source_doc)
            )
            for proj in projections:
                lf = getattr(proj, "lifted_from", None)
                if lf is None:
                    continue
                existing_keys.add((lf.source_doc, lf.source_ac))

        created: list[str] = []
        skipped: list[str] = []
        for entry in manifest.objectives:
            key = _entry_key(entry)
            if key in existing_keys:
                skipped.append(entry.lifted_from.source_ac)
                continue
            spec = _entry_to_spec(entry)
            asyncio.run(tracker.create(spec))
            created.append(entry.lifted_from.source_ac)
        return RegistrationResult(
            created=tuple(created), skipped=tuple(skipped)
        )
    finally:
        tracker.close()


# ---- registration: seal-time -----------------------------------------


def update_source_commits(
    manifest: Manifest,
    repo_root: Path | str,
    amendment_sha: str,
) -> int:
    """Write ``lifted_from.source_commit = amendment_sha`` on every record.

    AC.D-pa.3: after an amendment whose manifest carries an
    ``objectives`` block is sealed, every registered record carries
    the amendment SHA in its provenance pointer. Caller passes the
    SHA in (D-build.3 (a) — caller already reads HEAD for its own
    commit message).

    Returns the count of records actually rewritten. A no-op
    (``manifest.objectives`` empty, or every record already pinned)
    returns 0.

    Implementation note: ``LiftedFrom`` is a frozen Pydantic model
    and ``ObjectiveSpec`` is also frozen. The tracker has no public
    API for rewriting an existing record's ``lifted_from`` — it's
    event-sourced from the original ``ObjectiveCreated`` event. The
    seal-time write is therefore implemented as a direct SQLite
    update against the workspace's tracker DB: rewrite the
    ``lifted_from`` JSON blob inside the ``ObjectiveCreated`` event
    rows for affected objectives, then re-project to refresh the
    ``state`` row. This matches the tracker's own internal upgrade
    pattern (`objective_tracker/src/upgrade.py`) which also rewrites
    event payloads in place when a schema migration requires it.
    """
    if not manifest.objectives:
        return 0
    if not amendment_sha:
        raise ValueError(
            "amendment_sha must be a non-empty string; the seal step "
            "passes HEAD's SHA in"
        )

    repo_root_p = Path(repo_root)
    db_path = tracker_db_path_for(repo_root_p)
    if not db_path.exists():
        # Nothing to update — the apply step did not run / no tracker
        # was seeded. Treat as no-op rather than raising; the caller
        # may have used --no-finalize for a manifest that never
        # registered anything (legacy path).
        return 0

    # Match the keys we want to update.
    keys = {
        (e.lifted_from.source_doc, e.lifted_from.source_ac)
        for e in manifest.objectives
    }

    # Direct SQLite update — the tracker's own runtime has no
    # rewrite-lifted-from API for an existing record (the
    # ``lifted_from`` field was authored at create-event time and is
    # event-sourced). We mirror the store layout from
    # ``objective-tracker/src/store.py``:
    #
    #   - ``objective_events`` (event_id, objective_id, kind, payload)
    #     is the source of truth; ObjectiveCreated rows carry the
    #     authoring lifted_from in JSON payload.
    #   - ``objective_state`` carries the cached projection row;
    #     ``lifted_from_json`` is the projected JSON blob.
    #
    # Rewriting the event payload would change projection semantics
    # only on next ``query_projection_view`` call (which re-folds
    # events). To keep state and event-log in lockstep, we update
    # both: the JSON payload of the ObjectiveCreated event, and the
    # lifted_from_json column of the state row.
    import json

    updated = 0
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Collect ObjectiveCreated event rows whose payload's
        # lifted_from key matches a (source_doc, source_ac) we own.
        # ``kind`` discriminator value is "objective_created" per
        # ``objective-tracker/src/events.py:58``.
        rows = cur.execute(
            "SELECT event_id, objective_id, payload FROM "
            "objective_events WHERE kind = ?",
            ("objective_created",),
        ).fetchall()
        affected_objective_ids: list[str] = []
        for row in rows:
            payload = json.loads(row["payload"])
            lf = payload.get("lifted_from")
            if not isinstance(lf, dict):
                continue
            entry_key = (lf.get("source_doc"), lf.get("source_ac"))
            if entry_key not in keys:
                continue
            # Only write if the SHA actually changes — keeps
            # second-invocation idempotent on the same amendment.
            if lf.get("source_commit") == amendment_sha:
                continue
            lf["source_commit"] = amendment_sha
            payload["lifted_from"] = lf
            cur.execute(
                "UPDATE objective_events SET payload = ? "
                "WHERE event_id = ?",
                (json.dumps(payload), row["event_id"]),
            )
            affected_objective_ids.append(row["objective_id"])
            updated += 1

        # Refresh the state row's projected lifted_from_json so
        # ``query_projection_view`` reads the new value even before
        # a full re-projection (the runtime re-folds events on each
        # query, but the state row is the materialised view; we
        # keep them aligned).
        for oid in affected_objective_ids:
            state_row = cur.execute(
                "SELECT lifted_from_json FROM objective_state "
                "WHERE objective_id = ?",
                (oid,),
            ).fetchone()
            if state_row is None:
                continue
            lf_state = json.loads(state_row["lifted_from_json"])
            if not isinstance(lf_state, dict):
                continue
            lf_state["source_commit"] = amendment_sha
            cur.execute(
                "UPDATE objective_state "
                "SET lifted_from_json = ? "
                "WHERE objective_id = ?",
                (json.dumps(lf_state), oid),
            )

        conn.commit()
    finally:
        conn.close()

    return updated

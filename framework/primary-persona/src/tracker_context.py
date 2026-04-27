"""Tracker-context contributor for the primary-persona layer (#40).

Amendment #40 registers a session-level tracker-context contributor on
the shared ``ComposedContextPayload`` composer that D8 shipped. The
contributor surfaces "what objectives are in flight under the workspace"
in the persona's ``additionalContext`` payload at SessionStart, so the
persona reads the value-prop-rooted objective tree without the user
asking.

The composition mirrors amendment #33's memory-consumer contributor:

- ``TrackerClient``: narrow Protocol bound against the public surface
  amendments #38 (``query_projection_view`` + ``ObjectiveFilter``) and
  the long-standing ``trace_to_root`` API expose. The persona never
  imports objective-tracker source directly at module top-level; the
  Protocol is sufficient. The default factory inside
  ``register_tracker_context`` does ``import objective_tracker`` lazily
  — so production composes against the live tracker without putting the
  cross-component import on the persona-layer's import-time surface.
- ``tracker_db_path_for(workspace_root)``: pure function resolving the
  tracker DB path from the workspace identity. Mirrors workspace-
  bootstrap's ``TRACKER_DB_FILENAME = "objective_tracker.sqlite"``
  constant by convention parity (D-build.5 — method-level; AC40.6
  measures outcome not literal equality).
- ``build_tracker_context_contributor``: factory producing the callable
  the composer registers under ``TriggerKind.session``. Calls the
  client's ``query_projection_view`` + ``trace_to_root``, filters to
  in-flight descendants of the workspace's value-prop root, and
  projects them onto a structured textual block.
- ``register_tracker_context``: convenience wrapper around
  ``composer.register(...)`` matching ``register_memory_retrieval``'s
  shape.

Per amendment plan §3 + §6 the contributor degrades gracefully on
tracker unavailability (AC40.3), honours a proactive sub-cap to keep
it inside the composer's structural 10 000-char refusal (AC40.4),
contributes empty when nothing is in-flight (AC40.5), filters to the
workspace's value-prop-rooted tree (AC40.2 + AC40.6), and ships zero
workspace-content prose in source (AC40.7).

Per ODD §2.5 every code path traces back to AC40.1–AC40.7. The
graceful-degradation branch (AC40.3), the cap-guard handling
(AC40.4), and the empty-set behaviour (AC40.5) are explicitly
criterion-backed (not unbacked defensive branches).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol, Sequence

from .context_composer import TriggerKind
from . import observability as obs


# ---- exceptions ------------------------------------------------------


# No public exceptions. The contributor is fail-open under AC40.3 — any
# tracker-side error yields a structured diagnostic + an empty / marker
# contribution; the session proceeds. Method choices route through the
# graceful-degradation branch, not a raise.


# ---- workspace-identity → tracker DB path ---------------------------


# Mirrors workspace-bootstrap's
# ``adapters.tracker_seed.TRACKER_DB_FILENAME`` (amendment #39). The
# persona layer carries a private constant by convention parity rather
# than importing the workspace-bootstrap symbol — D-build.5; method-
# level; AC40.6 measures outcome (workspace A's contributor surfaces
# A's tree only) not constant equality. If workspace-bootstrap ever
# rotates its convention, the parity is verified empirically by AC40.6
# — the constant lives next to the pure-function path resolver below
# so a future amendment that reconciles the two is a one-line edit.
TRACKER_DB_FILENAME = "objective_tracker.sqlite"


# Stable objective ID for the workspace's value-prop root (amendment
# #39, ``adapters.tracker_seed.ROOT_OBJECTIVE_ID``). The contributor
# filters to this root's descendants. Convention parity, not import.
DEFAULT_VALUE_PROP_ROOT_ID = "value-prop-root"


def tracker_db_path_for(workspace_root: Path | str) -> Path:
    """Return the tracker DB path for ``workspace_root``.

    Pure function: no I/O. AC40.6 — the contributor consumes this
    path-resolver to derive its DB target from the workspace identity
    the persona already holds (the workspace_root path passed to
    ``ComposedContextPayload.on_session_start``). Two parallel
    workspaces resolve to two distinct paths; cross-workspace bleed
    is structurally impossible.
    """
    return Path(workspace_root) / TRACKER_DB_FILENAME


# ---- TrackerClient protocol -----------------------------------------


# Status vocabulary the contributor treats as "in flight" — AC40.1's
# pre-terminal set. The plan's AC40.1 names ``{started, decomposed}``;
# the tracker's actual lifecycle (per ``objective_tracker.spec.
# ObjectiveStatus``) is ``{proposed, active, achieved, abandoned}``.
# "In flight" = pre-terminal = ``{proposed, active}``. Vocabulary
# mapping is method-level (AC40.1 measures outcome: non-empty when
# in-flight objectives exist).
IN_FLIGHT_STATUSES: frozenset[str] = frozenset({"proposed", "active"})


class TrackerClient(Protocol):
    """Narrow read-only surface the persona layer calls on the tracker.

    Mirrors amendment #33's ``MemoryClient`` Protocol shape: the
    persona declares the methods it consumes and lets callers supply
    a concrete implementation. In production the implementation is
    ``objective_tracker.ObjectiveTracker`` (lazily imported by
    ``register_tracker_context``). In tests it is a fake.

    Per plan §6 constraint 8: read-only access. The Protocol exposes
    only ``query_projection_view``, ``trace_to_root``, and ``close``.
    No write or scope-binding methods are declared.
    """

    def query_projection_view(
        self, filter: Any | None = None
    ) -> tuple[Any, ...]:
        """Return projections matching ``filter`` (amendment #38)."""

    def trace_to_root(self, objective_id: str) -> list[Any]:
        """Return the ancestor chain, terminal root last."""

    def close(self) -> None:
        """Release any underlying resources (e.g. SQLite handle)."""


# ---- config + render -------------------------------------------------


@dataclass(frozen=True)
class TrackerContextConfig:
    """Per-composer config for the session-level tracker-context
    contributor.

    Decoupling from the build function simplifies test wiring and keeps
    the contributor callable captureable. Mirrors amendment #33's
    ``MemoryRetrievalConfig`` shape.
    """

    workspace_root: Path
    """Workspace identity the persona already holds; the contributor
    derives every other path from this. AC40.6."""

    value_prop_root_id: str = DEFAULT_VALUE_PROP_ROOT_ID
    """Stable ID of the workspace's value-prop root in the tracker
    (amendment #39 contract). Filters cross-tree records out (AC40.2)."""

    objective_id_cap: int = 20
    """Hard cap on the number of in-flight objectives projected. The
    sub-cap composes with ``char_cap`` to bound the contribution
    (AC40.4). Excess is replaced with a truncation marker."""

    char_cap: int = 2000
    """Soft character cap on the contributor's output. Composer's
    structural cap is 10 000 chars (``ADDITIONAL_CONTEXT_CAP``); we pin
    a sub-cap so combined contributions stay inside the structural
    refusal (AC40.4). Truncation is hard — caller-style markers are
    appended naming the elided count."""

    handle: str = "primary-persona"
    """Persona handle for diagnostics. Empty / unknown is acceptable."""


# ---- helpers (pure) -------------------------------------------------


def _is_in_flight(projection: Any) -> bool:
    """True iff ``projection.status`` is in the pre-terminal set.

    The projection is duck-typed to the public
    ``ObjectiveProjection`` shape — ``.status`` is an enum-or-string
    whose ``.value`` (or string form) we compare against
    ``IN_FLIGHT_STATUSES``.
    """
    status = getattr(projection, "status", None)
    if status is None:
        return False
    value = getattr(status, "value", str(status))
    return value in IN_FLIGHT_STATUSES


def _trace_chain_to_root_id(
    tracker: TrackerClient, objective_id: str
) -> tuple[list[Any], str | None]:
    """Return (chain, terminal_root_id).

    chain is the ancestor list (objective itself first, terminal last);
    terminal_root_id is the ``objective_id`` of the terminal element
    or None if the trace surfaces an error.

    Pure-ish: calls ``trace_to_root`` once. Errors propagate to the
    contributor's outer try/except (AC40.3).
    """
    chain = tracker.trace_to_root(objective_id)
    if not chain:
        return chain, None
    terminal = chain[-1]
    terminal_id = getattr(terminal, "objective_id", None)
    return chain, terminal_id


def _filter_to_root_descendants(
    tracker: TrackerClient,
    projections: Iterable[Any],
    root_id: str,
) -> list[Any]:
    """Filter ``projections`` to those whose trace_to_root terminates
    at ``root_id``. Pure delegation to ``trace_to_root``; AC40.2.
    """
    out: list[Any] = []
    for proj in projections:
        oid = getattr(proj, "objective_id", None)
        if oid is None:
            continue
        try:
            _chain, terminal_id = _trace_chain_to_root_id(tracker, oid)
        except Exception:
            # Stale or malformed projection — skip silently. The
            # contributor's outer fail-closed branch (AC40.3) catches
            # connection-level errors; a per-record trace failure on a
            # well-opened tracker is a record-level skip, not a
            # session-level halt.
            continue
        if terminal_id == root_id:
            out.append(proj)
    return out


def _format_projection_line(
    projection: Any,
    chain: Sequence[Any],
    *,
    root_id: str,
) -> str:
    """One-line bullet for an in-flight projection.

    Format:

        - <objective_id> [<status>]: <goal>  (<- <parent_goal> -> root)

    Parentage is the chain from the objective back to the root,
    excluding the objective itself and the root. When the chain is
    short (objective is a direct child of root), the parentage hint
    collapses to ``(<- root)``.
    """
    oid = getattr(projection, "objective_id", "?")
    status = getattr(projection, "status", "?")
    status_value = getattr(status, "value", str(status))
    goal = getattr(projection, "goal", "")
    # Parentage chain: chain[0] is the objective itself; chain[-1] is
    # the terminal root. Intermediate elements are parents.
    intermediates = list(chain[1:-1]) if len(chain) >= 2 else []
    if intermediates:
        parents = " -> ".join(getattr(p, "goal", "?")[:50] for p in intermediates)
        parentage = f"  (<- {parents} -> root)"
    else:
        parentage = "  (<- root)"
    # Single-line; truncate goal to keep the bullet short.
    short_goal = goal if len(goal) <= 100 else goal[:97] + "..."
    return f"  - {oid} [{status_value}]: {short_goal}{parentage}"


def _render_projection_block(
    *,
    in_flight: Sequence[Any],
    root_projection: Any | None,
    chains_by_id: dict[str, Sequence[Any]],
    root_id: str,
    objective_id_cap: int,
    char_cap: int,
) -> str:
    """Produce the contributor's textual block.

    Identity-anchor-style bracketed marker on the first line so the
    persona retains the structural signal through compaction. Subsequent
    lines describe the workspace's value-prop root + the in-flight set.

    Returns an empty string when ``in_flight`` is empty (AC40.5).
    """
    if not in_flight:
        return ""

    lines: list[str] = ["[primary-persona/tracker-context]"]
    # Root summary — gives the persona the workspace's prime objective
    # at the top of the block. Falls back to the root_id if the root
    # projection is None (e.g. trace_to_root never landed it; fail-soft).
    if root_projection is not None:
        root_goal = getattr(root_projection, "goal", "")
        short_root_goal = (
            root_goal if len(root_goal) <= 200 else root_goal[:197] + "..."
        )
        lines.append(f"workspace value-prop root: {short_root_goal}")
    else:
        lines.append(f"workspace value-prop root: <unresolved {root_id}>")

    # In-flight section.
    total = len(in_flight)
    capped = list(in_flight)[:objective_id_cap]
    truncated_count = total - len(capped)
    lines.append(f"in flight ({total}):")
    for proj in capped:
        oid = getattr(proj, "objective_id", "?")
        chain = chains_by_id.get(oid, [proj])
        lines.append(_format_projection_line(proj, chain, root_id=root_id))
    if truncated_count > 0:
        lines.append(
            f"  [{truncated_count} more in-flight objectives truncated]"
        )

    text = "\n".join(lines)
    if len(text) > char_cap:
        # Hard-trim on a line boundary so we don't half-emit a record.
        # Walk the lines back, dropping bullets until the total fits;
        # surface the dropped count in a final marker line so the
        # persona observes the truncation outcome.
        out: list[str] = []
        kept_bullets = 0
        total_size = 0
        # First two lines (marker + root summary + "in flight (N):")
        # are mandatory; they fit because (lines[0]+lines[1]+lines[2])
        # is well under the cap by construction (root_goal <= 200
        # chars). Defensive: if even those exceed, fall back to a hard
        # textual truncation.
        head = "\n".join(lines[:3])
        if len(head) >= char_cap:
            return head[: char_cap - 1].rstrip() + "…"
        out.extend(lines[:3])
        total_size = len(head)
        bullet_lines = [
            ln for ln in lines[3:] if not ln.startswith("  [") or ln.endswith(":")
        ]
        for ln in bullet_lines:
            if total_size + len(ln) + 1 > char_cap - 80:
                break
            out.append(ln)
            kept_bullets += 1
            total_size += len(ln) + 1
        dropped = (len(in_flight) - kept_bullets) + (
            truncated_count if truncated_count > 0 else 0
        )
        if dropped > 0:
            out.append(
                f"  [{dropped} more in-flight objectives truncated for cap]"
            )
        text = "\n".join(out)
    return text


# ---- contributor factory --------------------------------------------


def build_tracker_context_contributor(
    config: TrackerContextConfig,
    *,
    tracker_factory: Callable[[], TrackerClient],
) -> Callable[[dict[str, Any]], str]:
    """Return the callable registered on
    ``ComposedContextPayload.register(name=..., trigger_kind=
    TriggerKind.session, fn=<returned callable>)``.

    On every ``on_session_start`` the returned callable opens a tracker
    via ``tracker_factory``, queries every record, filters to in-flight
    descendants of ``config.value_prop_root_id`` (AC40.2 + AC40.6),
    renders a structured textual block, and returns it. Empty
    contribution when no in-flight objectives exist (AC40.5). Sub-cap
    enforced via ``_render_projection_block`` (AC40.4). On any
    exception during open/query/trace, returns either an empty string
    or a structured graceful-degradation marker and emits the
    ``pos.persona.tracker_context.unavailable`` event (AC40.3).
    """

    def contributor(context: dict[str, Any]) -> str:
        # AC40.3 — graceful-degradation envelope. Any tracker-side
        # exception (open failure, schema mismatch, permission error,
        # I/O error) yields a structured diagnostic + empty/marker
        # contribution; the registry's other contributors continue to
        # fire because the registry's invocation walk is per-contributor
        # try/except already (context_composer.py:367-371).
        try:
            tracker = tracker_factory()
        except Exception as exc:
            obs.tracker_context_unavailable_event(
                handle=config.handle,
                failure_class=type(exc).__name__,
                detail="tracker_open_failed",
            )
            return ""

        try:
            # Pull the full record set; downstream filter narrows to
            # in-flight descendants of the workspace's value-prop
            # root. AC40.2 — the tracker's actual surface is
            # query_projection_view (amendment #38).
            try:
                projections = tracker.query_projection_view()
            except Exception as exc:
                obs.tracker_context_unavailable_event(
                    handle=config.handle,
                    failure_class=type(exc).__name__,
                    detail="query_projection_view_failed",
                )
                return ""

            # Build chain-to-root for each candidate so the renderer can
            # surface parentage AND so we can filter to records whose
            # root is the workspace's value-prop root (AC40.2).
            chains_by_id: dict[str, Sequence[Any]] = {}
            descendants: list[Any] = []
            root_projection: Any | None = None
            for proj in projections:
                oid = getattr(proj, "objective_id", None)
                if oid is None:
                    continue
                if oid == config.value_prop_root_id:
                    root_projection = proj
                    continue
                try:
                    chain = tracker.trace_to_root(oid)
                except Exception:
                    # A single record's trace failed; skip it — the
                    # rest of the projection still composes. This is
                    # NOT a session-level halt; it's a record-level
                    # skip (the well-opened tracker yielded a stale
                    # record without an ancestor). AC40.3's outcome is
                    # measured at the session boundary.
                    continue
                if not chain:
                    continue
                terminal = chain[-1]
                terminal_id = getattr(terminal, "objective_id", None)
                if terminal_id != config.value_prop_root_id:
                    # Cross-workspace-root noise (AC40.2).
                    continue
                chains_by_id[oid] = chain
                descendants.append(proj)

            in_flight = [p for p in descendants if _is_in_flight(p)]

            # AC40.5 — empty contribution when nothing is in-flight.
            if not in_flight:
                obs.tracker_context_composed_event(
                    handle=config.handle,
                    in_flight_count=0,
                    truncated_count=0,
                )
                return ""

            text = _render_projection_block(
                in_flight=in_flight,
                root_projection=root_projection,
                chains_by_id=chains_by_id,
                root_id=config.value_prop_root_id,
                objective_id_cap=config.objective_id_cap,
                char_cap=config.char_cap,
            )

            # Truncation count for diagnostics — best-effort: derive
            # from line shape rather than threading through state.
            truncated = 1 if "truncated" in text else 0
            obs.tracker_context_composed_event(
                handle=config.handle,
                in_flight_count=len(in_flight),
                truncated_count=truncated,
            )
            return text
        finally:
            try:
                tracker.close()
            except Exception:
                # close() failure is non-load-bearing; the diagnostic
                # path above already emitted any open/query failures.
                pass

    return contributor


# ---- registration helper --------------------------------------------


def register_tracker_context(
    composer: Any,
    *,
    workspace_root: Path | str,
    value_prop_root_id: str = DEFAULT_VALUE_PROP_ROOT_ID,
    objective_id_cap: int = 20,
    char_cap: int = 2000,
    handle: str = "primary-persona",
    name: str = "tracker-context",
    tracker_factory: Callable[[], TrackerClient] | None = None,
) -> Callable[[dict[str, Any]], str]:
    """Register the tracker-context contributor against a
    ``ComposedContextPayload`` instance. Convenience wrapper around
    ``composer.register(...)`` for call sites that don't need to
    capture the contributor callable themselves.

    The default ``tracker_factory`` lazily imports
    ``objective_tracker.ObjectiveTracker`` and constructs it against
    ``tracker_db_path_for(workspace_root)``. Callers may override the
    factory (tests inject a stub; production composes against a
    long-lived shared tracker if one already exists).

    Returns the registered callable so tests can inspect / re-invoke.
    """
    config = TrackerContextConfig(
        workspace_root=Path(workspace_root),
        value_prop_root_id=value_prop_root_id,
        objective_id_cap=objective_id_cap,
        char_cap=char_cap,
        handle=handle,
    )

    if tracker_factory is None:
        # Lazy import — keeps objective-tracker off the persona layer's
        # import-time surface. The tracker is editable-installed in the
        # workspace's shared venv (see plan §6 constraint 5); this
        # import resolves at first contributor invocation, not at
        # module load.
        def _default_factory() -> TrackerClient:
            from objective_tracker import ObjectiveTracker  # noqa: WPS433

            return ObjectiveTracker(tracker_db_path_for(workspace_root))

        tracker_factory = _default_factory

    fn = build_tracker_context_contributor(config, tracker_factory=tracker_factory)
    composer.register(name=name, trigger_kind=TriggerKind.session, fn=fn)
    return fn

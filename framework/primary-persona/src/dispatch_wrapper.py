"""Agent-dispatch-as-scope wrapper (amendment #52, A8 R1-revised).

The persona-side wrapper that turns a Claude-Code Agent dispatch into
a first-class scope of work governed by the four-gate chain
(safety / reversibility / cost / orchestrator).

Public callable: :func:`dispatch_with_scope`. The single
persona-callable entry point per AC.A8.9. Takes a
:class:`DispatchShape` describing the Agent dispatch (objective,
constraints, halt conditions, expected duration, etc.) plus an
``agent_runner`` callable that actually invokes the Agent tool. The
wrapper:

  1. Builds a :class:`scope_of_work.ScopeSpec` from the shape
     (AC.A8.1).
  2. Infers the budget from the duration-estimation rubric
     (D4 — AC.A8.2).
  3. Opens an :class:`pos_orchestrator.ipc.IPCClient` against the
     workspace's orchestrator socket (D9 — AC.A8.3 / AC.A8.6).
     - Socket missing / connection refused → fail-soft fallback
       (AC.A8.6): log NDJSON diagnostic to
       ``<workspace>/.pos/dispatch-wrapper.log``, run the agent
       unwrapped, return its result.
  4. Calls ``activate_scope_with_spec(scope_id, objective_id,
     spec_payload)`` — the new IPC method per amendment #52
     AC.A8.A1 (AC.A8.3).
     - Gate-chain refusal (`ApplicationError` with `-32060` /
       `-32061` / `-32062` cost codes; safety / reversibility codes)
       → return :class:`DispatchRefusal` as a value (AC.A8.7); do
       NOT raise, do NOT invoke the agent.
  5. On approval, invokes ``agent_runner`` with the original
     dispatch payload, captures its result + reported tokens.
  6. Calls ``record_dispatch_close(scope_id, terminal_state,
     debited_tokens)`` — AC.A8.A3 — to emit ``BudgetDebited`` and
     transition the scope to ``completed`` | ``failed`` |
     ``cancelled`` (AC.A8.4 / AC.A8.5).
  7. Closes the IPC client. Returns the agent's result.

Default reversibility class is ``compensatable`` (D2 — locked
2026-04-26). Default objective_id resolves to the workspace's
ambient seed (D5 — amendment #39 tracker seed); when neither
caller-supplied nor ambient is available, the wrapper takes the
fail-soft fallback path (AC.A8.6).

Per ODD §2.5 every code path traces back to a named AC. Defensive
``if`` branches without backing AC are not introduced.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal


# ---- inline duration-estimation rubric (D4) -------------------------
#
# The six-row table from memory bullet
# `feedback_duration_estimation_rubric` §"Step 1 — Categorize by task
# shape". Each row: time_seconds_min/max + tokens_min/max bounds. The
# wrapper picks the row's tokens_max as the conservative reservation
# (cost-governance refuses the dispatch if a smaller cap would not
# fit; over-reservation does not refuse). AC.A8.2 measures the
# returned Budget falls within the rubric's documented bounds.
#
# Categories (verbatim from memory bullet):
#   trivial       — single-tool one-shot, ~1s,    50-500 tokens
#   simple        — small read/edit,      ~5s,    500-2k
#   moderate      — multi-tool sequence,  ~30s,   2k-10k
#   substantial   — research+author,      ~3min,  10k-50k
#   heavy         — multi-artefact build, ~15min, 50k-200k
#   epic          — full amendment cycle, ~60min, 200k-1M
#
# Inline because (a) calibration data, not user-tunable config; (b)
# updated with the bullet's calibration loop, not per-workspace
# (D4 alt(a) rejected); (c) self-contained within the wrapper's
# module — no YAML loader / config schema. ODD §2.5 forward
# direction: each row is consumed by AC.A8.2; reverse direction:
# every code path that reads this constant maps to AC.A8.2.

_DURATION_RUBRIC: dict[str, dict[str, int]] = {
    "trivial": {
        "time_seconds_max": 5,
        "tokens_min": 50,
        "tokens_max": 500,
    },
    "simple": {
        "time_seconds_max": 15,
        "tokens_min": 500,
        "tokens_max": 2_000,
    },
    "moderate": {
        "time_seconds_max": 60,
        "tokens_min": 2_000,
        "tokens_max": 10_000,
    },
    "substantial": {
        "time_seconds_max": 300,
        "tokens_min": 10_000,
        "tokens_max": 50_000,
    },
    "heavy": {
        "time_seconds_max": 1800,
        "tokens_min": 50_000,
        "tokens_max": 200_000,
    },
    "epic": {
        "time_seconds_max": 7200,
        "tokens_min": 200_000,
        "tokens_max": 1_000_000,
    },
}


# ---- public dataclasses ---------------------------------------------


@dataclass(frozen=True)
class DispatchShape:
    """The persona's natural-language Agent dispatch shape.

    AC.A8.1: the wrapper builds a `ScopeSpec` from these fields.
    AC.A8.9: the persona has a single callable surface taking this
    shape.
    """

    objective: str
    constraints: tuple[str, ...] = ()
    halt_conditions: tuple[str, ...] = ()
    expected_duration_seconds: float = 30.0
    task_shape_category: str = "moderate"
    reversibility_class: str = "compensatable"  # D2 default
    agent_payload: dict[str, Any] = field(default_factory=dict)
    """Caller-opaque payload passed verbatim to ``agent_runner``."""


@dataclass(frozen=True)
class DispatchRefusal:
    """Structured gate-chain refusal returned as a VALUE per AC.A8.7.

    The persona caller routes this to user narration without
    exception-handling boilerplate.
    """

    gate_code: int
    rejecting_gate: Literal["safety", "reversibility", "cost", "orchestrator"]
    reason: str
    scope_id: str


@dataclass(frozen=True)
class DispatchOutcome:
    """The successful return value of `dispatch_with_scope`.

    Carries the underlying agent's result plus the scope-of-work
    bookkeeping so the persona can route both.
    """

    scope_id: str
    objective_id: str
    agent_result: Any
    debited_tokens: int
    terminal_state: Literal["completed", "failed", "cancelled"]
    fallback: bool = False
    """True when the orchestrator was unreachable and the agent ran
    unwrapped (AC.A8.6)."""


# ---- helpers --------------------------------------------------------


def _infer_budget_from_duration(
    duration_seconds: float, category: str
) -> Any:
    """Return a `scope_of_work.Budget` per AC.A8.2.

    The wrapper declares time + tokens (D6: money axis omitted by
    default). Bounds come from the inline `_DURATION_RUBRIC`. The
    `tokens_max` row value is the reservation cap; cost-governance
    refuses the dispatch if a smaller workspace cap would not fit.
    """
    from scope_of_work import Budget  # lazy: avoids module-load cycle

    row = _DURATION_RUBRIC.get(category)
    if row is None:
        # ODD §2.5: only categories in the rubric are valid. An
        # unknown category is a programmer error (caller wrote a
        # category name not in the rubric); raise rather than guess.
        raise ValueError(
            f"unknown task_shape_category {category!r}; expected one of "
            f"{sorted(_DURATION_RUBRIC.keys())}"
        )
    # Pick max(declared duration, rubric ceiling) for the time axis
    # so a caller's pessimistic estimate is honoured.
    time_seconds = max(int(duration_seconds), row["time_seconds_max"])
    tokens = row["tokens_max"]
    return Budget(time_seconds=time_seconds, tokens=tokens)


def _build_scope_spec(
    shape: DispatchShape, *, owner_persona: str | None = None
) -> Any:
    """Construct a `ScopeSpec` from a `DispatchShape` per AC.A8.1.

    Success criteria are derived from the halt-conditions tuple; one
    `SuccessCriterion` per halt condition. (Halt conditions are
    natural-language predicates the dispatch must satisfy or
    explicitly trip; the audit-trail records each as a separate
    criterion so post-dispatch evaluation is granular.)
    """
    from scope_of_work import (
        ReversibilityClass,
        ScopeSpec,
        SuccessCriterion,
    )

    budget = _infer_budget_from_duration(
        shape.expected_duration_seconds, shape.task_shape_category
    )
    rev_class = ReversibilityClass(shape.reversibility_class)
    if shape.halt_conditions:
        criteria = tuple(
            SuccessCriterion(
                criterion_id=f"halt_{i}",
                description=cond,
            )
            for i, cond in enumerate(shape.halt_conditions)
        )
    else:
        # AC.A8.1 requires "at least one SuccessCriterion derived from
        # the halt-conditions tuple." When the caller supplies none,
        # we synthesise a single placeholder criterion naming the
        # objective itself (audit-trail still records a criterion).
        criteria = (
            SuccessCriterion(
                criterion_id="objective_completed",
                description=shape.objective,
            ),
        )
    return ScopeSpec(
        goal=shape.objective,
        constraints=tuple(shape.constraints),
        budget=budget,
        reversibility_class=rev_class,
        success_criteria=criteria,
        observers=(),
        escalation_triggers=(),
        owner_persona=owner_persona,
        expected_duration_seconds=float(shape.expected_duration_seconds),
    )


def _resolve_socket_path(workspace_root: Path) -> Path:
    """Return the orchestrator's Unix socket path for this workspace.

    Production convention post-D.2 (amendment #63):
    ``<workspace>/workspace/.pos/orchestrator.sock`` (set by
    workspace-bootstrap; verified on every active install). Tests
    pass an explicit override via the ``ipc_socket_path`` parameter
    on `dispatch_with_scope`.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "orchestrator.sock"


def _resolve_objective_id(
    workspace_root: Path, supplied: str | None
) -> str | None:
    """Resolve the objective_id per D5.

    1. If the caller supplies one, use it.
    2. Otherwise, read the ambient seed from
       ``<workspace>/workspace/.pos/ambient-objective-id`` (a single-
       line text file authored by amendment #39's workspace-bootstrap
       contributor).
    3. If neither is available, return None (AC.A8.6 fallback).
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    if supplied:
        return supplied
    seed_path = pos_subdir(workspace_root) / "ambient-objective-id"
    if not seed_path.exists():
        return None
    try:
        text = seed_path.read_text().strip()
    except OSError:
        return None
    return text or None


def _diagnostic_log_path(workspace_root: Path) -> Path:
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "dispatch-wrapper.log"


def _append_diagnostic(workspace_root: Path, record: dict[str, Any]) -> None:
    """Append a structured NDJSON diagnostic per D1 / D8.

    Mirrors amendment #48's `<workspace>/.pos/memory-writes.log`
    pattern. Failure to write the diagnostic is itself swallowed
    (the diagnostic is a fallback-pathway observable; if even the
    diagnostic write fails, the wrapper is in a workspace state
    where logging is impossible — proceeding with the dispatch is
    still preferable to raising).
    """
    log_path = _diagnostic_log_path(workspace_root)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **record,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        # Diagnostic write failure does not fail the dispatch.
        # AC.A8.6 measures the dispatch-completion outcome, not the
        # log file's append success.
        pass


# ---- gate-code → rejecting-gate mapping (AC.A8.7) -------------------
#
# Error code ranges from sealed-component public surfaces:
#   -32060 / -32061 / -32062 → cost-governance (session / rolling /
#                              scope ceiling reservation refusal)
#   -32070 .. -32079         → safety-layer
#   -32080 .. -32089         → reversibility-primitive
#   409, -32020, -32030      → orchestrator (ScopeNotPending,
#                              BindRefused, paused)
# Anything else → bubble as exception (programmer error or
# unanticipated server failure; AC.A8.7 names only the gate-chain
# refusal codes).


def _classify_gate_code(code: int) -> str | None:
    if code in (-32060, -32061, -32062):
        return "cost"
    if -32079 <= code <= -32070:
        return "safety"
    if -32089 <= code <= -32080:
        return "reversibility"
    if code in (409, -32020, -32030):
        return "orchestrator"
    return None


# ---- public callable ------------------------------------------------


async def dispatch_with_scope(
    shape: DispatchShape,
    *,
    agent_runner: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    workspace_root: Path | str,
    objective_id: str | None = None,
    owner_persona: str | None = "primary",
    ipc_socket_path: Path | str | None = None,
) -> DispatchOutcome | DispatchRefusal:
    """Wrap an Agent dispatch in a scope of work governed by the
    four-gate chain.

    Parameters
    ----------
    shape:
        The persona's dispatch shape (objective, constraints, halt
        conditions, etc.). See :class:`DispatchShape`.
    agent_runner:
        An async callable that performs the actual Agent dispatch.
        Receives ``shape.agent_payload`` and returns a dict containing
        the agent's result. The wrapper extracts an integer
        ``total_tokens`` field (default 0 if absent) for the
        BudgetDebited reservation amount on close.
    workspace_root:
        The workspace root path. Used to resolve the orchestrator
        socket and the diagnostic log location.
    objective_id:
        Optional caller-supplied objective id. Default: the ambient
        seed at ``<workspace>/.pos/ambient-objective-id`` (D5).
    owner_persona:
        Persona identifier recorded on the ScopeSpec. Default
        ``"primary"``.
    ipc_socket_path:
        Optional override for the IPC socket path (tests).

    Returns
    -------
    Either a :class:`DispatchOutcome` (success or fallback) or a
    :class:`DispatchRefusal` (gate-chain refusal, returned as value
    per AC.A8.7).
    """
    # Lazy imports — keep module load fast and avoid any
    # primary-persona ↔ pos-orchestrator import-time cycle. Tests
    # monkeypatch `pos_orchestrator.ipc.IPCClient` directly; we
    # re-resolve via `import pos_orchestrator.ipc as _ipc_mod` so
    # the swap is visible.
    import pos_orchestrator.ipc as _ipc_mod
    from pos_orchestrator.ipc import ApplicationError

    IPCClient = _ipc_mod.IPCClient

    workspace_root = Path(workspace_root)
    socket_path = (
        Path(ipc_socket_path)
        if ipc_socket_path is not None
        else _resolve_socket_path(workspace_root)
    )
    scope_id = f"scope-{uuid.uuid4()}"  # AC.A8.8: distinct per call
    spec = _build_scope_spec(shape, owner_persona=owner_persona)

    resolved_objective = _resolve_objective_id(workspace_root, objective_id)
    if resolved_objective is None or not socket_path.exists():
        # AC.A8.6 — orchestrator unreachable / no objective: log a
        # structured diagnostic, run the agent unwrapped, return a
        # DispatchOutcome with fallback=True.
        _append_diagnostic(
            workspace_root,
            {
                "event": "fallback",
                "scope_id": scope_id,
                "reason": (
                    "no_ambient_objective"
                    if resolved_objective is None
                    else "socket_missing"
                ),
                "objective": shape.objective[:200],
            },
        )
        agent_result = await agent_runner(dict(shape.agent_payload))
        debited = int(agent_result.get("total_tokens", 0) or 0)
        return DispatchOutcome(
            scope_id=scope_id,
            objective_id=resolved_objective or "<unresolved>",
            agent_result=agent_result,
            debited_tokens=debited,
            terminal_state="completed",
            fallback=True,
        )

    client = IPCClient(socket_path)
    try:
        try:
            await client.connect()
        except (FileNotFoundError, ConnectionRefusedError, OSError) as e:
            # AC.A8.6 — socket-connection failure also takes the
            # fallback path. (The path-exists check above can race;
            # this except handles the connect-time race.)
            _append_diagnostic(
                workspace_root,
                {
                    "event": "fallback",
                    "scope_id": scope_id,
                    "reason": f"connect_failed:{type(e).__name__}",
                    "objective": shape.objective[:200],
                },
            )
            agent_result = await agent_runner(dict(shape.agent_payload))
            debited = int(agent_result.get("total_tokens", 0) or 0)
            return DispatchOutcome(
                scope_id=scope_id,
                objective_id=resolved_objective,
                agent_result=agent_result,
                debited_tokens=debited,
                terminal_state="completed",
                fallback=True,
            )

        # AC.A8.3 — call activate_scope_with_spec (amendment #52
        # AC.A8.A1 IPC method).
        try:
            await client.call(
                "activate_scope_with_spec",
                {
                    "scope_id": scope_id,
                    "objective_id": resolved_objective,
                    "spec": spec.model_dump(),
                },
            )
        except ApplicationError as e:
            # AC.A8.7 — gate-chain refusal becomes a value.
            rejecting = _classify_gate_code(e.code)
            if rejecting is None:
                # Unanticipated server error — bubble.
                raise
            _append_diagnostic(
                workspace_root,
                {
                    "event": "refusal",
                    "scope_id": scope_id,
                    "gate_code": e.code,
                    "rejecting_gate": rejecting,
                    "reason": str(e),
                },
            )
            return DispatchRefusal(
                gate_code=e.code,
                rejecting_gate=rejecting,  # type: ignore[arg-type]
                reason=str(e),
                scope_id=scope_id,
            )

        # AC.A8.3 approval branch — invoke the agent.
        try:
            agent_result = await agent_runner(dict(shape.agent_payload))
            debited = int(agent_result.get("total_tokens", 0) or 0)
            terminal: Literal["completed", "failed", "cancelled"] = (
                "completed"
            )
        except Exception as e:
            # Agent raised — record close as failed.
            _append_diagnostic(
                workspace_root,
                {
                    "event": "agent_raised",
                    "scope_id": scope_id,
                    "exception_class": type(e).__name__,
                    "message": str(e),
                },
            )
            await client.call(
                "record_dispatch_close",
                {
                    "scope_id": scope_id,
                    "terminal_state": "failed",
                    "debited_tokens": 0,
                },
            )
            raise

        # AC.A8.4 + AC.A8.5 — record_dispatch_close emits BudgetDebited
        # and transitions scope to terminal state.
        await client.call(
            "record_dispatch_close",
            {
                "scope_id": scope_id,
                "terminal_state": terminal,
                "debited_tokens": debited,
            },
        )
        return DispatchOutcome(
            scope_id=scope_id,
            objective_id=resolved_objective,
            agent_result=agent_result,
            debited_tokens=debited,
            terminal_state=terminal,
            fallback=False,
        )
    finally:
        await client.close()


__all__ = [
    "DispatchOutcome",
    "DispatchRefusal",
    "DispatchShape",
    "dispatch_with_scope",
]

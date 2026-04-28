"""Agent-dispatch-as-scope wrapper (amendment #52, A8 R1-revised) +
dispatcher-side test-stub authoring (amendment #74, AC.DSA.*).

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
  4. **Setup phase (amendment #74, AC.DSA.1–AC.DSA.10).** When
     ``shape.new_acs`` is non-empty AND the workspace is in DEV MODE,
     the wrapper authors three artefacts on disk BEFORE the IPC call:
     (a) the active-scope sentinel binding the scope to the new ACs,
     (b) one manifest row per (component, ac_id, source_path_glob)
     triple via A1's ``register_source_binding`` API, (c) one
     ``pytest.skip(...)`` placeholder test file per AC at
     ``framework/<comp>/tests/test_AC_<NORM>_placeholder.py``.
     Sentinel write strictly precedes manifest registration so A3's
     ``manifest_row.created_at > sentinel.created_at`` "new AC in this
     diff" predicate is satisfied (AC.DSA.3 + D-DSA.4 — sub-second
     collisions resolved by waiting for the next ISO-second tick;
     §14 method-decision register entry).
     Setup is fail-soft (AC.DSA.5): every step's failure logs a
     structured NDJSON diagnostic and the dispatch proceeds; the gates
     (A2 / A3) provide the structural enforcement and surface the
     failure to the operator at first-edit time.
  5. Calls ``activate_scope_with_spec(scope_id, objective_id,
     spec_payload)`` — the new IPC method per amendment #52
     AC.A8.A1 (AC.A8.3).
     - Gate-chain refusal (`ApplicationError` with `-32060` /
       `-32061` / `-32062` cost codes; safety / reversibility codes)
       → return :class:`DispatchRefusal` as a value (AC.A8.7); do
       NOT raise, do NOT invoke the agent.
  6. On approval, invokes ``agent_runner`` with the original
     dispatch payload, captures its result + reported tokens.
  7. Calls ``record_dispatch_close(scope_id, terminal_state,
     debited_tokens)`` — AC.A8.A3 — to emit ``BudgetDebited`` and
     transition the scope to ``completed`` | ``failed`` |
     ``cancelled`` (AC.A8.4 / AC.A8.5).
  8. Closes the IPC client. Returns the agent's result.

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
class NewACSpec:
    """A single (component, ac_id, source_path_glob) declaration of a
    new acceptance criterion the dispatched agent will author.

    AC.DSA.1 / AC.DSA.6: the persona declares one ``NewACSpec`` per
    new AC the dispatch will introduce. The dispatcher uses each
    triple to (a) bind the scope sentinel, (b) register a manifest
    row via A1's ``register_source_binding``, and (c) author a
    ``pytest.skip(...)`` placeholder test file the agent will replace
    with a real test.

    Fields are workspace-relative-canonical: ``component`` matches the
    sealed-component name (e.g. ``"primary-persona"``); ``ac_id`` may
    be either ``"AC.X.1"`` or ``"X.1"`` (A3's ``_normalise_ac_id`` is
    case-insensitive on the leading ``AC.`` prefix); ``source_path_glob``
    is the workspace-relative fnmatch glob the new AC's source edits
    will match (e.g. ``"framework/primary-persona/src/foo.py"``).
    """

    component: str
    ac_id: str
    source_path_glob: str


@dataclass(frozen=True)
class DispatchShape:
    """The persona's natural-language Agent dispatch shape.

    AC.A8.1: the wrapper builds a `ScopeSpec` from these fields.
    AC.A8.9: the persona has a single callable surface taking this
    shape.
    AC.DSA.1: an optional ``new_acs`` tuple declares the new ACs the
    dispatch will introduce; when non-empty, the wrapper's setup
    phase authors sentinel + manifest rows + placeholder test stubs
    on disk before the IPC call. Default ``()`` preserves backwards
    compatibility with every pre-amendment-#74 caller (AC.DSA.10).
    """

    objective: str
    constraints: tuple[str, ...] = ()
    halt_conditions: tuple[str, ...] = ()
    expected_duration_seconds: float = 30.0
    task_shape_category: str = "moderate"
    reversibility_class: str = "compensatable"  # D2 default
    agent_payload: dict[str, Any] = field(default_factory=dict)
    """Caller-opaque payload passed verbatim to ``agent_runner``."""
    new_acs: tuple[NewACSpec, ...] = ()
    """Amendment #74 / AC.DSA.1: declared new ACs the dispatch will
    author. Empty tuple disables the setup phase (AC.DSA.10
    backwards-compat); research+plan dispatches pass ``()``."""


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


# ---- amendment #74 setup phase (AC.DSA.1 – AC.DSA.10) ---------------
#
# When a build dispatch declares NEW ACs via ``DispatchShape.new_acs``,
# the wrapper's setup phase authors three on-disk artefacts BEFORE the
# IPC call to ``activate_scope_with_spec`` (D-DSA.7):
#
#   1. The active-scope sentinel (A1's ``write_active_scope_sentinel``
#      surface) binding the dispatched agent to the (component, ac_id)
#      pairs.
#   2. One manifest row per ``NewACSpec`` triple via A1's
#      ``register_source_binding``.
#   3. One placeholder test stub at
#      ``framework/<comp>/tests/test_AC_<NORM>_placeholder.py``.
#
# The sentinel write is sequenced FIRST so manifest-row ``created_at``
# lands strictly after sentinel ``created_at`` (AC.DSA.3).
#
# Pre-amendment-#75 the sentinel emitted second-resolution Z-format
# while the manifest emitted microsecond-+00:00 format; lexicographic
# comparison (A3's predicate at ``tdd_guard.evaluate``) collapsed
# same-second pairs to ``False`` because ``"."`` (0x2E) sorts before
# ``"Z"`` (0x5A). Tight-loop empirical at #74 build time: 100%
# collision rate. Amendment #74 mitigated by waiting one ISO-second
# tick between writes; amendment #75 (AC.TFN.1, AC.TFN.2, AC.TFN.4)
# eliminated the failure class structurally by migrating both A1
# emitters to format γ (microsecond-Z, fixed-width 27 chars). The
# wait helper has been removed; back-to-back writes within the same
# wall-clock second now produce strictly-increasing lex-comparable
# strings via the microsecond field.

_STUB_FILENAME_TEMPLATE = "test_AC_{normalised}_placeholder.py"
_STUB_FUNCTION_TEMPLATE = "test_AC_{normalised}_placeholder"


def _normalise_ac_id(ac_id: str) -> str:
    """Match A3's normalisation (``framework/hands-off-lifecycle/hooks/
    tdd_guard.py:_normalise_ac_id``).

    Drops a leading ``AC.`` (case-insensitive); replaces every ``.``
    with ``_``; uppercases. The output keys both the test-file name
    (``test_AC_<NORM>_placeholder.py``) and the function-name prefix
    (``test_AC_<NORM>_``) — AC.DSA.2 names the byte-content shape.
    Local duplication of A3's helper avoids a hooks-package import
    cycle (the dispatch wrapper is in primary-persona, hooks live in
    hands-off-lifecycle; a sibling import would be cross-component).
    """
    s = ac_id
    if s[:3].lower() == "ac.":
        s = s[3:]
    s = s.replace(".", "_")
    return s.upper()


def _stub_path(workspace_root: Path, component: str, ac_id: str) -> Path:
    """Resolve the placeholder test file path for a (component, ac_id)
    pair (AC.DSA.2 / AC.DSA.3 — file at A3's expected glob).
    """
    norm = _normalise_ac_id(ac_id)
    return (
        workspace_root
        / "framework"
        / component
        / "tests"
        / _STUB_FILENAME_TEMPLATE.format(normalised=norm)
    )


def _render_stub_body(
    *,
    component: str,
    ac_id: str,
    scope_id: str,
    plan_path: str,
) -> str:
    """Render the placeholder test file content (AC.DSA.2).

    Body: module docstring naming the dispatcher + scope + plan;
    ``import pytest``; one function ``test_AC_<NORM>_placeholder()``
    whose body invokes ``pytest.skip(...)`` with a reason naming the
    AC ID. The function-name matches A3's
    ``^def\\s+test_AC_<NORM>_\\w*\\s*\\(`` regex (AC.DSA.2 + halt-trigger
    8 verification).
    """
    norm = _normalise_ac_id(ac_id)
    fn_name = _STUB_FUNCTION_TEMPLATE.format(normalised=norm)
    return (
        f'"""Dispatcher-authored placeholder for {ac_id} '
        f'(component {component}).\n'
        '\n'
        'This file was created by the dispatch wrapper at scope-creation\n'
        f'time (scope_id={scope_id!r}; plan={plan_path!r}) to satisfy\n'
        "A3's pinned-test predicate. The build agent is expected to\n"
        f'replace the placeholder function with a real test for {ac_id}.\n'
        '\n'
        f'A3 admits any test_AC_{norm}_* function in this file; the\n'
        'build agent may rename or augment as needed.\n'
        '"""\n'
        '\n'
        'import pytest\n'
        '\n'
        '\n'
        f'def {fn_name}() -> None:\n'
        '    pytest.skip(\n'
        f'        "stub authored by dispatcher; replace with real test '
        f'for {ac_id}"\n'
        '    )\n'
    )


def _is_dispatcher_authored_stub(
    existing: str, *, component: str, ac_id: str
) -> bool:
    """True iff ``existing`` looks byte-equivalent to the dispatcher's
    skip-with-reason stub for (component, ac_id) (AC.DSA.4).

    Tolerant to scope_id / plan_path drift across re-dispatches: the
    canonical detection is the function name + the
    ``stub authored by dispatcher`` skip reason. If those two markers
    are present AND the file imports ``pytest`` AND the function body
    calls ``pytest.skip``, treat the file as the dispatcher's
    placeholder (re-author safe). Any other content is agent-authored;
    the dispatcher does NOT overwrite (AC.DSA.4).
    """
    norm = _normalise_ac_id(ac_id)
    fn_marker = f"def test_AC_{norm}_placeholder("
    return (
        fn_marker in existing
        and "import pytest" in existing
        and "pytest.skip" in existing
        and "stub authored by dispatcher" in existing
    )


def _write_stub_idempotent(
    workspace_root: Path,
    spec: NewACSpec,
    *,
    scope_id: str,
    plan_path: str,
) -> dict[str, Any]:
    """Write one placeholder stub idempotently (AC.DSA.4).

    Outcomes (returned in the diagnostic dict for AC.DSA.9):
      - ``"written"``: file did not exist; authored fresh.
      - ``"skipped-identical"``: file existed with byte-equal content.
      - ``"skipped-agent-authored"``: file existed but content does
        NOT match the dispatcher's stub shape (the build agent has
        already authored real content; respect it — AC.DSA.4).
      - ``"failed-os-error"`` / ``"failed-permission"``: write raised;
        AC.DSA.5 fail-soft; A3 surfaces the missing-test at first
        edit time.
    """
    target = _stub_path(workspace_root, spec.component, spec.ac_id)
    rendered = _render_stub_body(
        component=spec.component,
        ac_id=spec.ac_id,
        scope_id=scope_id,
        plan_path=plan_path,
    )
    if target.exists():
        try:
            existing = target.read_text(encoding="utf-8")
        except OSError as e:
            return {
                "outcome": "failed-os-error",
                "path": str(target),
                "error_detail": f"{type(e).__name__}: {e}",
            }
        if existing == rendered:
            return {
                "outcome": "skipped-identical",
                "path": str(target),
            }
        if _is_dispatcher_authored_stub(
            existing, component=spec.component, ac_id=spec.ac_id
        ):
            # Dispatcher-authored shape with header drift (e.g.
            # different scope_id / plan_path on a re-dispatch). The
            # file already serves A3's predicate; AC.DSA.4 requires
            # idempotent skip — do not corrupt the existing header.
            return {
                "outcome": "skipped-identical",
                "path": str(target),
            }
        # Agent-authored content (or unrecognised). Per D-DSA.5, do
        # NOT overwrite — the build agent's real test takes precedence.
        return {
            "outcome": "skipped-agent-authored",
            "path": str(target),
        }
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    except PermissionError as e:
        return {
            "outcome": "failed-permission",
            "path": str(target),
            "error_detail": f"{type(e).__name__}: {e}",
        }
    except OSError as e:
        return {
            "outcome": "failed-os-error",
            "path": str(target),
            "error_detail": f"{type(e).__name__}: {e}",
        }
    return {
        "outcome": "written",
        "path": str(target),
    }


def _read_workspace_mode(workspace_root: Path) -> str:
    """Read the workspace-mode bit per AC.DSA.6.

    Lazy import of A1's ``corpus_load_sentinel.workspace_mode`` so the
    module-load cost stays bounded for non-DEV-MODE workspaces. Failure
    (module unavailable, contract unreadable) falls through to
    ``"normal-use"`` — fail-closed-to-permissive at the import boundary;
    the setup phase is gated behind ``"dev-mode"`` so a fall-through
    skips the phase entirely (matches A2/A3's mode-bit handling).
    """
    try:
        # The hooks/ dir is on sys.path inside any workspace where A1
        # ships; a stdlib-style import path-fix is unnecessary because
        # the persona's runtime context already reaches the hooks
        # directory through the shared workspace .venv.
        from corpus_load_sentinel import workspace_mode  # type: ignore[import-not-found]

        return workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return "normal-use"


def _open_tracker(workspace_root: Path) -> Any | None:
    """Open the workspace's ObjectiveTracker, or return None on failure.

    AC.DSA.5: failure to open the tracker is fail-soft — the dispatch
    proceeds; A2 surfaces the substrate failure at first-edit time.
    """
    try:
        from objective_tracker import ObjectiveTracker  # type: ignore[import-not-found]
        from workspace_bootstrap.workspace_paths import (  # type: ignore[import-not-found]
            tracker_db_path,
        )

        db_path = tracker_db_path(workspace_root)
        if not db_path.exists():
            return None
        return ObjectiveTracker(db_path)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


def _run_setup_phase(
    workspace_root: Path,
    *,
    scope_id: str,
    plan_path: str,
    new_acs: tuple[NewACSpec, ...],
) -> None:
    """Author sentinel + manifest rows + placeholder stubs (AC.DSA.1
    .. AC.DSA.10).

    Sequence (AC.DSA.3):
      1. Write the active-scope sentinel binding the new ACs.
      2. Register one manifest row per ``NewACSpec`` triple.
      3. Write one placeholder test stub per ``NewACSpec``.

    Pre-amendment-#75 there was a wall-clock wait between step 1 and
    step 2 (``_wait_until_next_iso_second``) — A1's sentinel and
    manifest emitters used incompatible timestamp formats whose
    lexicographic comparison collided on same-second writes. Amendment
    #75 (AC.TFN.1, AC.TFN.2, AC.TFN.4) migrated both A1 emitters to
    format γ (microsecond ``Z``-suffix, fixed-width); the wait became
    structurally unnecessary and was removed.

    Every step is fail-soft (AC.DSA.5): substrate failures emit a
    structured NDJSON diagnostic to ``dispatch-wrapper.log`` (AC.DSA.9
    observability) and the dispatch continues. Idempotent on repeated
    invocation (AC.DSA.4) — A1's sentinel + manifest APIs short-circuit
    on byte-equal / duplicate; ``_write_stub_idempotent`` short-circuits
    on byte-equal or agent-authored content.

    Caller is expected to gate this whole function behind
    ``new_acs != ()`` (AC.DSA.1) AND ``_read_workspace_mode(
    workspace_root) == "dev-mode"`` (AC.DSA.6). The function does NOT
    re-check those preconditions — keeping the gating at the call site
    satisfies ODD §2.5 reverse direction (no defensive ``if`` without a
    backing AC at the helper boundary).
    """
    # AC.DSA.3 — sentinel first.
    sentinel_outcome: dict[str, Any] = {
        "step": "sentinel",
        "scope_id": scope_id,
    }
    try:
        # Lazy import: avoids a primary-persona ↔ hands-off-lifecycle
        # import-time dependency. The hooks dir is reachable through
        # the workspace's shared .venv at runtime.
        from active_scope_sentinel import (  # type: ignore[import-not-found]
            ScopeBinding,
            write_active_scope_sentinel,
        )

        bindings = tuple(
            ScopeBinding(component=spec.component, ac_id=spec.ac_id)
            for spec in new_acs
        )
        result = write_active_scope_sentinel(
            workspace_root,
            scope_id=scope_id,
            plan_path=plan_path,
            bindings=bindings,
        )
        sentinel_outcome["wrote"] = bool(result.wrote)
        sentinel_outcome["reason"] = result.reason
        sentinel_outcome["path"] = str(result.path)
        if result.error_detail:
            sentinel_outcome["error_detail"] = result.error_detail
    except Exception as e:  # noqa: BLE001 — fail-soft per AC.DSA.5
        sentinel_outcome["wrote"] = False
        sentinel_outcome["reason"] = "failed-exception"
        sentinel_outcome["error_detail"] = f"{type(e).__name__}: {e}"
    _append_diagnostic(
        workspace_root,
        {"event": "setup", **sentinel_outcome},
    )

    # AC.DSA.3 — register manifest rows. Amendment #75 (AC.TFN.4)
    # removed the iso-second wait that previously sat here: A1's
    # sentinel + manifest emitters now produce microsecond-resolution
    # ``Z``-suffixed timestamps (format γ), so lexicographic order
    # follows wall-clock order without a synthetic delay.
    tracker = _open_tracker(workspace_root)
    for spec in new_acs:
        manifest_outcome: dict[str, Any] = {
            "step": "manifest",
            "scope_id": scope_id,
            "component": spec.component,
            "ac_id": spec.ac_id,
            "source_path_glob": spec.source_path_glob,
        }
        if tracker is None:
            manifest_outcome["outcome"] = "failed-tracker-unavailable"
            _append_diagnostic(
                workspace_root,
                {"event": "setup", **manifest_outcome},
            )
            continue
        try:
            tracker.register_source_binding(
                component=spec.component,
                ac_id=spec.ac_id,
                source_path_glob=spec.source_path_glob,
            )
            manifest_outcome["outcome"] = "registered"
        except Exception as e:  # noqa: BLE001 — fail-soft per AC.DSA.5
            manifest_outcome["outcome"] = "failed-exception"
            manifest_outcome["error_detail"] = f"{type(e).__name__}: {e}"
        _append_diagnostic(
            workspace_root,
            {"event": "setup", **manifest_outcome},
        )

    # AC.DSA.2 + AC.DSA.4 — write placeholder stubs.
    for spec in new_acs:
        stub_outcome = _write_stub_idempotent(
            workspace_root,
            spec,
            scope_id=scope_id,
            plan_path=plan_path,
        )
        _append_diagnostic(
            workspace_root,
            {
                "event": "setup",
                "step": "stub",
                "scope_id": scope_id,
                "component": spec.component,
                "ac_id": spec.ac_id,
                **stub_outcome,
            },
        )


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

        # AC.DSA.7 — setup phase strictly precedes
        # activate_scope_with_spec when the dispatch declares NEW ACs
        # AND the workspace is in DEV MODE. Empty ``new_acs`` ⇒ no-op
        # (AC.DSA.1 backwards-compat for amendment-#52 callers and
        # research+plan dispatches). NORMAL USE ⇒ no-op (AC.DSA.6).
        if shape.new_acs and _read_workspace_mode(workspace_root) == "dev-mode":
            # plan_path is bookkeeping on the sentinel record (gates
            # do not read it). Pull a caller-supplied
            # ``shape.agent_payload["plan_path"]`` when present;
            # fall back to a truncated form of the objective so the
            # sentinel JSON shape (A1's ``plan_path: str | non-empty``
            # validator) is satisfied without a new ``DispatchShape``
            # field.
            plan_path_value = shape.agent_payload.get("plan_path")
            plan_path = (
                plan_path_value
                if isinstance(plan_path_value, str) and plan_path_value
                else (shape.objective[:200] or "<unspecified-plan>")
            )
            _run_setup_phase(
                workspace_root,
                scope_id=scope_id,
                plan_path=plan_path,
                new_acs=shape.new_acs,
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
    "NewACSpec",
    "dispatch_with_scope",
]

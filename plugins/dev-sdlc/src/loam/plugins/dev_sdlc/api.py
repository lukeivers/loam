"""Persona-invocable Python API for the Dev/SDLC plugin.

Public surface (per plan §4 AC.OSS-M6.7 + AC.OSS-M6.2..M6.5):

  - `start_project(slug, *, methodology="odd", workspace_root=None,
    scope_runtime=None, objective_tracker=None)`
  - `advance_stage(slug, *, workspace_root=None, scope_runtime=None,
    objective_tracker=None)`
  - `project_status(slug=None, *, workspace_root=None)`
  - `list_projects(*, workspace_root=None)`
  - `gate_check(slug, *, workspace_root=None)`

Pydantic models are import-stable; signatures are stable for AC
verification (`inspect.signature`).

The optional `scope_runtime` + `objective_tracker` keyword arguments
let the persona pass live runtime instances for the scope + tracker
integration (AC.OSS-M6.5). When omitted, the API runs without those
side effects — useful for CLI invocations where the bootstrap host
hasn't constructed those runtimes (the plugin remains useful as a
file-system-only project scaffolder).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from . import stages, store
from .errors import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    StageGateFailedError,
    TerminalStageError,
    UnsupportedMethodologyError,
)
from .observability import stage_advance_span


# ---------------------------------------------------------------------
# Public Pydantic models (re-exported via package __init__).
# ---------------------------------------------------------------------


class ProjectHandle(BaseModel):
    """Returned by `start_project`. Carries the slug + paths the
    persona / CLI may want to surface to the user."""

    model_config = ConfigDict(frozen=True)

    slug: str
    methodology: str
    project_root: Path
    current_stage: str


class StageAdvanceResult(BaseModel):
    """Returned by `advance_stage`."""

    model_config = ConfigDict(frozen=True)

    slug: str
    from_stage: str
    to_stage: str
    methodology: str


class ProjectStatus(BaseModel):
    """Returned by `project_status` + `list_projects`."""

    model_config = ConfigDict(frozen=True)

    slug: str
    methodology: str
    current_stage: str
    project_root: Path


class GateResult(BaseModel):
    """Returned by `gate_check`. `passed=True` when gate satisfies;
    `reason` stable code on failure (per
    `errors.StageGateFailedError`)."""

    model_config = ConfigDict(frozen=True)

    slug: str
    stage: str
    passed: bool
    reason: str | None = None
    detail: str | None = None


# ---------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------


def _resolve_workspace_root(workspace_root: Path | None) -> Path:
    """Default to CWD when not provided. CLI explicitly passes
    --workspace-root; the persona supplies host.workspace_root."""
    if workspace_root is None:
        return Path.cwd()
    return Path(workspace_root)


def _project_root(workspace_root: Path, slug: str) -> Path:
    return workspace_root / "projects" / slug


def _odd_mirror_path(project_root: Path) -> Path:
    return project_root / ".dev-sdlc-odd-mirror.yaml"


def _yaml_mirror_path(project_root: Path) -> Path:
    return project_root / ".dev-sdlc.yaml"


def _scaffold_project_tree(project_root: Path) -> None:
    """Create the project directory + per-stage subdirectories."""
    project_root.mkdir(parents=True, exist_ok=False)
    for st in stages.STAGES:
        (project_root / st).mkdir(parents=True, exist_ok=True)


def _write_yaml_mirror(
    project_root: Path,
    *,
    slug: str,
    methodology: str,
    current_stage: str,
) -> None:
    """Author the human-readable YAML mirror at
    `<project>/.dev-sdlc.yaml` (derived view per plan §10
    D-build.M6.8 — SQLite is source of truth)."""
    payload = {
        "slug": slug,
        "methodology": methodology,
        "current_stage": current_stage,
    }
    _yaml_mirror_path(project_root).write_text(
        yaml.safe_dump(payload, sort_keys=True), encoding="utf-8"
    )


def _write_odd_mirror(
    project_root: Path, *, slug: str
) -> None:
    """Author the internal ODD mirror for non-ODD methodologies
    (per plan §4 AC.OSS-M6.3)."""
    payload = {
        "slug": slug,
        "objective": "<unset until populated>",
        "stages": list(stages.STAGES),
        "authored_at": datetime.now(timezone.utc).isoformat(),
    }
    _odd_mirror_path(project_root).write_text(
        yaml.safe_dump(payload, sort_keys=True), encoding="utf-8"
    )


def _await_if_coro(value: Any) -> Any:
    """Run a coroutine to completion synchronously. Used so the
    public API stays sync from the persona / CLI's perspective even
    when scope-of-work / objective-tracker public methods are
    async (per their respective architectures)."""
    if asyncio.iscoroutine(value):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(value)
        # Inside an async context already — return the coroutine for
        # the caller to await. The plugin's CLI / API uses this in
        # sync contexts only at v0.1.0; in-event-loop callers receive
        # the coroutine.
        return loop.run_until_complete(value)
    return value


def _build_default_scope_spec(goal: str) -> Any:
    """Construct a `ScopeSpec` with the plugin's default shape.

    Conservative defaults: 24-hour time budget, fully reversible
    class, single ProseCriterion-equivalent SuccessCriterion. The
    plugin's projects are scope-of-work scopes for tracking purposes
    only — concrete budget enforcement is the harness's job, not the
    plugin's.
    """
    from loam.scope_of_work.spec import (
        Budget,
        ReversibilityClass,
        ScopeSpec,
        SuccessCriterion,
    )

    return ScopeSpec(
        goal=goal,
        constraints=(),
        budget=Budget(time_seconds=24 * 60 * 60),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(
            SuccessCriterion(
                criterion_id="dev-sdlc.default.AC.1",
                description=goal,
            ),
        ),
        observers=(),
        escalation_triggers=(),
        owner_persona=None,
    )


def _create_project_scope(
    scope_runtime: Any | None, *, slug: str, methodology: str
) -> str | None:
    """Create the project's parent scope via scope-of-work; return
    its scope_id or None when scope_runtime is unavailable."""
    if scope_runtime is None:
        return None
    spec = _build_default_scope_spec(
        f"produce {slug} via {methodology}"
    )
    proj = _await_if_coro(scope_runtime.create(spec))
    return getattr(proj, "scope_id", None)


def _create_stage_scope(
    scope_runtime: Any | None,
    *,
    slug: str,
    stage: str,
    parent_scope_id: str | None,
) -> str | None:
    """Create a child scope under the project for *stage*."""
    if scope_runtime is None or parent_scope_id is None:
        return None
    spec = _build_default_scope_spec(
        f"produce {stage} artefact for {slug}"
    )
    proj = _await_if_coro(
        scope_runtime.create(spec, parent_scope_id=parent_scope_id)
    )
    return getattr(proj, "scope_id", None)


def _build_objective_spec(
    *, goal: str, parent_id: str | None, criterion_id: str, prose: str
) -> Any:
    """Construct an ObjectiveSpec with the plugin's default shape.

    Evergreen + weekly review cadence; single ProseCriterion. Per
    plan §10 D-build.M6.7 — the plugin's tracker integration uses
    free-text criteria; explicit AC formalisation lives in the
    project's own stage artefacts.
    """
    from loam.objective_tracker.spec import (
        ObjectiveSpec,
        ProseCriterion,
        TimeBound,
    )

    return ObjectiveSpec(
        goal=goal,
        parent_id=parent_id,
        acceptance_criteria=(
            ProseCriterion(criterion_id=criterion_id, prose=prose),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="weekly"),
        authored_by="user",
    )


def _create_project_objective(
    objective_tracker: Any | None,
    *,
    slug: str,
    methodology: str,
) -> str | None:
    """Create the root project objective via objective-tracker;
    return its objective_id or None when tracker is unavailable."""
    if objective_tracker is None:
        return None
    spec = _build_objective_spec(
        goal=f"produce {slug} via {methodology}",
        parent_id=None,
        criterion_id=f"{slug}.AC.1",
        prose=f"all five stages of {slug} reach review state",
    )
    proj = _await_if_coro(objective_tracker.create(spec))
    return getattr(proj, "objective_id", None)


def _create_stage_objective(
    objective_tracker: Any | None,
    *,
    slug: str,
    stage: str,
    parent_objective_id: str | None,
) -> str | None:
    """Create a child objective under the project's root for *stage*."""
    if objective_tracker is None or parent_objective_id is None:
        return None
    spec = _build_objective_spec(
        goal=f"produce {stage} artefact for {slug}",
        parent_id=parent_objective_id,
        criterion_id=f"{slug}.{stage}.AC.1",
        prose=(
            f"{stage} artefact exists with objective + "
            "acceptance criteria"
        ),
    )
    proj = _await_if_coro(objective_tracker.create(spec))
    return getattr(proj, "objective_id", None)


# ---------------------------------------------------------------------
# Public API surface.
# ---------------------------------------------------------------------


def start_project(
    slug: str,
    *,
    methodology: str = "odd",
    workspace_root: Path | None = None,
    scope_runtime: Any | None = None,
    objective_tracker: Any | None = None,
) -> ProjectHandle:
    """Scaffold an ODD-shaped project tree (AC.OSS-M6.2 + AC.OSS-M6.3).

    Creates:
      - `<workspace>/projects/<slug>/` with per-stage subdirectories.
      - SQLite row in `<workspace>/.loam/dev-sdlc.sqlite`.
      - YAML mirror at `<project>/.dev-sdlc.yaml`.
      - For non-ODD methodologies: ODD mirror at
        `<project>/.dev-sdlc-odd-mirror.yaml` (AC.OSS-M6.3).

    When `scope_runtime` + `objective_tracker` are supplied, the
    parent scope + project objective are created (AC.OSS-M6.5).
    """
    if methodology not in stages.METHODOLOGIES:
        raise UnsupportedMethodologyError(methodology)
    ws = _resolve_workspace_root(workspace_root)
    proj_root = _project_root(ws, slug)
    if proj_root.exists():
        raise ProjectAlreadyExistsError(slug)

    _scaffold_project_tree(proj_root)

    project_scope_id = _create_project_scope(
        scope_runtime, slug=slug, methodology=methodology
    )
    project_objective_id = _create_project_objective(
        objective_tracker, slug=slug, methodology=methodology
    )

    current_stage = stages.STAGES[0]
    with store.open_store(ws) as conn:
        store.insert_project(
            conn,
            slug=slug,
            methodology=methodology,
            current_stage=current_stage,
            project_scope_id=project_scope_id,
            project_objective_id=project_objective_id,
        )
        conn.commit()

    _write_yaml_mirror(
        proj_root,
        slug=slug,
        methodology=methodology,
        current_stage=current_stage,
    )
    if methodology != "odd":
        _write_odd_mirror(proj_root, slug=slug)

    return ProjectHandle(
        slug=slug,
        methodology=methodology,
        project_root=proj_root,
        current_stage=current_stage,
    )


def advance_stage(
    slug: str,
    *,
    workspace_root: Path | None = None,
    scope_runtime: Any | None = None,
    objective_tracker: Any | None = None,
) -> StageAdvanceResult:
    """Run the structural gate; on pass, advance the project's
    current_stage (AC.OSS-M6.4 + AC.OSS-M6.5).

    Emits `loam.dev_sdlc.stage_advance` span (AC.OSS-M6.5).
    """
    ws = _resolve_workspace_root(workspace_root)
    proj_root = _project_root(ws, slug)
    with store.open_store(ws) as conn:
        row = store.get_project(conn, slug)
        if row is None:
            raise ProjectNotFoundError(slug)
        from_stage = row.current_stage
        if stages.is_terminal_stage(from_stage):
            raise TerminalStageError(slug, from_stage)
        outcome = stages.check_gate(
            project_root=proj_root,
            slug=slug,
            stage=from_stage,
            methodology=row.methodology,
        )
        if not outcome.passed:
            assert outcome.reason is not None
            raise StageGateFailedError(
                reason=outcome.reason,
                project=slug,
                stage=from_stage,
            )
        to_stage = stages.next_stage(from_stage)
        assert to_stage is not None
        store.advance_project_stage(
            conn,
            slug=slug,
            from_stage=from_stage,
            to_stage=to_stage,
        )
        conn.commit()

    # Emit OTel span + run scope/tracker integration in one place
    # so the span captures the work.
    with stage_advance_span(
        slug=slug,
        from_stage=from_stage,
        to_stage=to_stage,
        methodology=row.methodology,
    ):
        _create_stage_scope(
            scope_runtime,
            slug=slug,
            stage=to_stage,
            parent_scope_id=row.project_scope_id,
        )
        _create_stage_objective(
            objective_tracker,
            slug=slug,
            stage=to_stage,
            parent_objective_id=row.project_objective_id,
        )

    # Update YAML mirror.
    _write_yaml_mirror(
        proj_root,
        slug=slug,
        methodology=row.methodology,
        current_stage=to_stage,
    )

    return StageAdvanceResult(
        slug=slug,
        from_stage=from_stage,
        to_stage=to_stage,
        methodology=row.methodology,
    )


def project_status(
    slug: str | None = None,
    *,
    workspace_root: Path | None = None,
) -> list[ProjectStatus]:
    """Return status for one project (`slug` set) or all projects
    (`slug=None`). Same return type either way for predictable
    persona consumption."""
    ws = _resolve_workspace_root(workspace_root)
    out: list[ProjectStatus] = []
    with store.open_store(ws) as conn:
        if slug is not None:
            row = store.get_project(conn, slug)
            if row is None:
                raise ProjectNotFoundError(slug)
            rows = [row]
        else:
            rows = store.list_all_projects(conn)
    for row in rows:
        out.append(
            ProjectStatus(
                slug=row.slug,
                methodology=row.methodology,
                current_stage=row.current_stage,
                project_root=_project_root(ws, row.slug),
            )
        )
    return out


def list_projects(
    *, workspace_root: Path | None = None
) -> list[ProjectStatus]:
    """Return status for every project in the workspace."""
    return project_status(slug=None, workspace_root=workspace_root)


def gate_check(
    slug: str,
    *,
    workspace_root: Path | None = None,
) -> GateResult:
    """Inspect the current stage's artefact + return a `GateResult`
    without advancing. Useful for the persona's pre-flight check
    before invoking `advance_stage`."""
    ws = _resolve_workspace_root(workspace_root)
    proj_root = _project_root(ws, slug)
    with store.open_store(ws) as conn:
        row = store.get_project(conn, slug)
        if row is None:
            raise ProjectNotFoundError(slug)
    outcome = stages.check_gate(
        project_root=proj_root,
        slug=slug,
        stage=row.current_stage,
        methodology=row.methodology,
    )
    return GateResult(
        slug=slug,
        stage=row.current_stage,
        passed=outcome.passed,
        reason=outcome.reason,
        detail=outcome.detail,
    )

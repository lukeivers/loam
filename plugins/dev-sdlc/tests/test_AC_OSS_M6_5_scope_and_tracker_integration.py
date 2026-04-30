"""AC.OSS-M6.5 — Stage-bound scope + objective-tracker integration.

Per plan §4 AC.OSS-M6.5: when a project is created, the plugin
creates a parent scope under scope-of-work + a root objective in
the tracker. When a stage advances, the plugin creates a child
scope + a child objective. Each stage advance emits
`loam.dev_sdlc.stage_advance` span.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.plugins.dev_sdlc import api


class _StubScopeProjection:
    def __init__(self, scope_id: str) -> None:
        self.scope_id = scope_id


class _StubScopeRuntime:
    """Minimal stub matching scope_runtime.create's contract."""

    def __init__(self) -> None:
        self.creates: list[tuple[Any, str | None]] = []
        self._next_id = 0

    async def create(
        self, spec: Any, *, parent_scope_id: str | None = None
    ) -> _StubScopeProjection:
        self._next_id += 1
        sid = f"scope-{self._next_id}"
        self.creates.append((spec, parent_scope_id))
        return _StubScopeProjection(sid)


class _StubObjectiveProjection:
    def __init__(self, objective_id: str) -> None:
        self.objective_id = objective_id


class _StubObjectiveTracker:
    """Minimal stub matching objective_tracker.create's contract."""

    def __init__(self) -> None:
        self.creates: list[Any] = []
        self._next_id = 0

    async def create(
        self, spec: Any, *, objective_id: str | None = None
    ) -> _StubObjectiveProjection:
        self._next_id += 1
        oid = f"obj-{self._next_id}"
        self.creates.append(spec)
        return _StubObjectiveProjection(oid)


def test_start_project_creates_parent_scope_and_root_objective(
    tmp_path: Path,
) -> None:
    sr = _StubScopeRuntime()
    ot = _StubObjectiveTracker()
    api.start_project(
        slug="alpha",
        workspace_root=tmp_path,
        scope_runtime=sr,
        objective_tracker=ot,
    )
    # Parent scope + root objective each created exactly once.
    assert len(sr.creates) == 1
    assert len(ot.creates) == 1
    # Parent scope has no parent_scope_id; root objective has
    # parent_id None.
    _, parent_id = sr.creates[0]
    assert parent_id is None
    assert ot.creates[0].parent_id is None


def test_advance_stage_creates_child_scope_and_child_objective(
    tmp_path: Path,
) -> None:
    sr = _StubScopeRuntime()
    ot = _StubObjectiveTracker()
    api.start_project(
        slug="alpha",
        workspace_root=tmp_path,
        scope_runtime=sr,
        objective_tracker=ot,
    )
    proj_root = tmp_path / "projects" / "alpha"
    (proj_root / "research" / "alpha.md").write_text(
        "## Objective\n\nDo a thing.\n\n"
        "## Acceptance Criteria\n\n- outcome\n",
        encoding="utf-8",
    )
    api.advance_stage(
        slug="alpha",
        workspace_root=tmp_path,
        scope_runtime=sr,
        objective_tracker=ot,
    )
    assert len(sr.creates) == 2  # parent + spec child
    assert len(ot.creates) == 2  # root + spec child
    # Spec child carries the project's parent_scope_id.
    _, child_parent = sr.creates[1]
    assert child_parent == "scope-1"
    # Spec child objective carries the project's parent_id.
    assert ot.creates[1].parent_id == "obj-1"


def test_stage_advance_works_without_runtimes(tmp_path: Path) -> None:
    """When no scope/tracker is supplied, the plugin still scaffolds +
    advances — the persona / CLI may call without those runtimes."""
    api.start_project(slug="alpha", workspace_root=tmp_path)
    proj_root = tmp_path / "projects" / "alpha"
    (proj_root / "research" / "alpha.md").write_text(
        "## Objective\n\ndo\n\n## Acceptance Criteria\n\n- ok\n",
        encoding="utf-8",
    )
    result = api.advance_stage(
        slug="alpha", workspace_root=tmp_path
    )
    assert result.to_stage == "spec"


def test_stage_advance_emits_otel_span(tmp_path: Path) -> None:
    """The OTel span fires around stage_advance; we patch
    `stage_advance_span` to confirm it's invoked with the expected
    arguments."""
    from loam.plugins.dev_sdlc import api as api_mod

    captured: list[dict[str, Any]] = []

    real_span = api_mod.stage_advance_span

    def _capture_span(**kwargs):
        captured.append(kwargs)
        return real_span(**kwargs)

    api_mod.stage_advance_span = _capture_span  # type: ignore[assignment]
    try:
        api.start_project(slug="alpha", workspace_root=tmp_path)
        proj_root = tmp_path / "projects" / "alpha"
        (proj_root / "research" / "alpha.md").write_text(
            "## Objective\n\ndo\n\n## Acceptance Criteria\n\n- ok\n",
            encoding="utf-8",
        )
        api.advance_stage(slug="alpha", workspace_root=tmp_path)
    finally:
        api_mod.stage_advance_span = real_span  # type: ignore[assignment]

    assert len(captured) == 1
    kwargs = captured[0]
    assert kwargs["slug"] == "alpha"
    assert kwargs["from_stage"] == "research"
    assert kwargs["to_stage"] == "spec"
    assert kwargs["methodology"] == "odd"

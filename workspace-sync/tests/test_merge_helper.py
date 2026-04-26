"""AC.WS.2, AC.WS.3, AC.WS.4, AC.WS.6, AC.WS.11, AC.WS.12 — merge_helper integration tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from workspace_sync.conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    INFERRED_RESOLUTIONS,
    Resolution,
)
from workspace_sync.merge_helper import (
    check_inferred_resolution_invariants,
    resolve_inferred_conflicts,
)
from workspace_sync.merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
)
from workspace_sync.state import SyncStatus, audit_yaml_path, load_state, state_yaml_path
from workspace_sync.sync_protected import default_sync_protected


class StubLLMClient:
    def __init__(self, queued: list[tuple[MergeVerdict, int]]) -> None:
        self.queued = list(queued)
        self.calls = 0

    def invoke(self, prompt: str, response_model: type[BaseModel]):
        self.calls += 1
        if not self.queued:
            raise ResolverFailure("stub: out of canned verdicts")
        v, t = self.queued.pop(0)
        return v, t


def _verdict(resolution="inferred-accept-canonical", merged_content=None, confidence=0.9) -> MergeVerdict:
    return MergeVerdict(
        resolution=resolution,
        merged_content=merged_content,
        rationale="stub rationale",
        confidence=confidence,
    )


def _make_report(*entries) -> ConflictReport:
    return ConflictReport(
        sync_ref="testref",
        detected_at="2026-04-26T00:00:00Z",
        conflicts=list(entries),
    )


def _entry(
    path: str,
    *,
    change_kind: ConflictChangeKind = ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
    resolution: Resolution = Resolution.PENDING,
    rationale: str | None = None,
    confidence: float | None = None,
    user_override: bool = False,
    override_rationale: str | None = None,
) -> ConflictEntry:
    return ConflictEntry(
        path=path,
        prior_release_sha256=None,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=change_kind,
        resolution=resolution,
        rationale=rationale,
        confidence=confidence,
        user_override=user_override,
        override_rationale=override_rationale,
    )


def test_class_a_path_resolves_keep_local_no_resolver_call(tmp_path: Path) -> None:
    """AC.WS.2: Class-A entries skip the resolver entirely."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / ".mcp.json").write_text("{}")
    (workspace_root / ".mcp.json").write_text("workspace")

    stub = StubLLMClient([])  # would ResolverFailure if invoked
    resolver = MergeResolver(stub)
    report = _make_report(_entry(".mcp.json"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    assert stub.calls == 0  # resolver NEVER called for Class A
    assert report.conflicts[0].resolution is Resolution.KEEP_LOCAL
    assert "Class A" in (report.conflicts[0].rationale or "")


def test_class_b_workspace_modified_keeps_local(tmp_path: Path) -> None:
    """AC.WS.3: Class-B + workspace-modified → KEEP_LOCAL."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "memory.yaml").write_text("canonical")
    (workspace_root / "memory.yaml").write_text("workspace")

    resolver = MergeResolver(StubLLMClient([]))
    report = _make_report(
        _entry("memory.yaml", change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED)
    )

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    assert report.conflicts[0].resolution is Resolution.KEEP_LOCAL


def test_class_c_invokes_resolver_writes_audit(tmp_path: Path) -> None:
    """AC.WS.4 + AC.WS.5: Class-C runs resolver; audit + state persist."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "framework.py").write_text("canonical")
    (workspace_root / "framework.py").write_text("workspace")

    stub = StubLLMClient([(_verdict(), 100)])
    resolver = MergeResolver(stub)
    report = _make_report(_entry("framework.py"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    assert stub.calls == 1
    assert report.conflicts[0].resolution in INFERRED_RESOLUTIONS

    # Audit + state YAML written.
    audit_p = audit_yaml_path(workspace_root, "testref")
    assert audit_p.exists()
    state_p = state_yaml_path(workspace_root)
    assert state_p.exists()
    state = load_state(workspace_root)
    assert state is not None
    assert state.status is SyncStatus.SUCCESS


def test_budget_halt_persists_partial_state(tmp_path: Path) -> None:
    """AC.WS.6 + AC.WS.12: BudgetExhausted halts; audit + state persist."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "a.py").write_text("a-canonical")
    (workspace_root / "a.py").write_text("a-workspace")
    (canonical_root / "b.py").write_text("b-canonical")
    (workspace_root / "b.py").write_text("b-workspace")

    # Budget = 5k per-conflict, cumulative 10k. After 1 call (8k used)
    # the next call's projected 13k exceeds the ceiling.
    stub = StubLLMClient([(_verdict(), 8_000), (_verdict(), 8_000)])
    resolver = MergeResolver(
        stub,
        ResolverBudget(per_conflict_token_budget=5_000, cumulative_token_budget=10_000),
    )
    report = _make_report(_entry("a.py"), _entry("b.py"))

    with pytest.raises(BudgetExhausted):
        resolve_inferred_conflicts(
            report=report,
            sync_protected=default_sync_protected(),
            canonical_root=canonical_root,
            workspace_root=workspace_root,
            resolver=resolver,
        )

    # State persisted with FAILURE.
    state = load_state(workspace_root)
    assert state is not None
    assert state.status is SyncStatus.FAILURE
    assert state.halt_reason is not None
    assert "budget_exhausted" in state.halt_reason


def test_resolver_failure_persists_state_then_raises(tmp_path: Path) -> None:
    """AC.WS.12: ResolverFailure halts; state.yaml records FAILURE."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "x.py").write_text("c")
    (workspace_root / "x.py").write_text("w")

    class ExplodingClient:
        def invoke(self, prompt, response_model):
            raise RuntimeError("network gone")

    resolver = MergeResolver(ExplodingClient())
    report = _make_report(_entry("x.py"))

    with pytest.raises(ResolverFailure):
        resolve_inferred_conflicts(
            report=report,
            sync_protected=default_sync_protected(),
            canonical_root=canonical_root,
            workspace_root=workspace_root,
            resolver=resolver,
        )

    state = load_state(workspace_root)
    assert state is not None
    assert state.status is SyncStatus.FAILURE


def test_user_override_skips_resolver(tmp_path: Path) -> None:
    """AC.WS.9: user_override=True entries bypass the resolver."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "framework.py").write_text("c")
    (workspace_root / "framework.py").write_text("w")

    stub = StubLLMClient([])  # would explode if called
    resolver = MergeResolver(stub)
    # Operator-overridden entry: resolution + override_rationale set.
    overridden = _entry(
        "framework.py",
        resolution=Resolution.KEEP_LOCAL,
        user_override=True,
        override_rationale="operator chose to keep workspace",
    )
    report = _make_report(overridden)

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    assert stub.calls == 0
    assert report.conflicts[0].resolution is Resolution.KEEP_LOCAL


def test_otel_summary_span_emitted_per_run(tmp_path: Path) -> None:
    """AC.WS.11: per-resolution + summary OTel spans emit."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "x.py").write_text("c")
    (workspace_root / "x.py").write_text("w")

    stub = StubLLMClient([(_verdict(), 100)])
    resolver = MergeResolver(stub)
    report = _make_report(_entry("x.py"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    span_names = [s.name for s in exporter.get_finished_spans()]
    assert "pos.sync.merge_gate.resolution" in span_names
    assert "pos.sync.merge_gate.summary" in span_names


def test_check_inferred_resolution_invariants_pass() -> None:
    report = _make_report(
        _entry(
            "x.py",
            resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
            rationale="r",
            confidence=0.9,
        ),
    )
    passed, reason = check_inferred_resolution_invariants(report)
    assert passed
    assert reason is None


def test_check_inferred_invariants_pending_fails() -> None:
    report = _make_report(_entry("x.py"))  # PENDING
    passed, reason = check_inferred_resolution_invariants(report)
    assert not passed
    assert "pending" in (reason or "").lower()


def test_check_inferred_invariants_no_report_passes() -> None:
    passed, _ = check_inferred_resolution_invariants(None)
    assert passed

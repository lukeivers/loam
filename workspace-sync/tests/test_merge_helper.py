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
from workspace_sync.merge_primitives import (
    MergeClassification,
    MergeVerification,
)
from workspace_sync.sync_protected import default_sync_protected


class StubLLMClient:
    """Test-double LLM client.

    Type-aware (α.2-compatible). When the resolver/helper invokes
    with ``response_model=MergeClassification`` (the α.2 classify
    call), the stub returns a canned classifier output: by default
    ``merge_class="unknown"`` so α.2 falls through to the legacy
    LLM-generator path immediately. Tests that exercise α.2 happy
    paths supply their own ``MergeClassification`` queue entry.

    When the helper invokes with ``response_model=MergeVerification``
    (α.2 verify call), the stub returns ``passed=false`` — forces
    fall-through. Same opt-in pattern: tests that want pass return
    a custom queue entry.

    When the resolver invokes with ``response_model=MergeVerdict``
    (today's generator path), the stub pops from ``queued`` (the
    legacy behaviour).
    """

    def __init__(
        self,
        queued: list[tuple[MergeVerdict, int]] | None = None,
        *,
        classify_responses: list[tuple[MergeClassification, int]] | None = None,
        verify_responses: list[tuple[MergeVerification, int]] | None = None,
    ) -> None:
        self.queued = list(queued or [])
        self.classify_responses = list(classify_responses or [])
        self.verify_responses = list(verify_responses or [])
        self.calls = 0

    def invoke(self, prompt: str, response_model: type[BaseModel]):
        self.calls += 1
        if response_model is MergeClassification:
            if self.classify_responses:
                v, t = self.classify_responses.pop(0)
                return v, t
            return MergeClassification(
                merge_class="unknown", confidence=0.0, reasoning="stub default"
            ), 50
        if response_model is MergeVerification:
            if self.verify_responses:
                v, t = self.verify_responses.pop(0)
                return v, t
            return MergeVerification(
                passed=False, class_mismatch=False, concerns="stub default", confidence=0.0
            ), 100
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
    resolved_content_path: str | None = None,
) -> ConflictEntry:
    # α-hotfix-2 #60 Bug C: when constructing an
    # INFERRED_ACCEPT_CANONICAL or ACCEPT_UPSTREAM entry without an
    # explicit resolved_content_path, supply a placeholder so the
    # validator does not reject (the test factory's intent is shape-
    # correctness; null-content-path is the bug shape the validator
    # now refuses).
    if resolved_content_path is None and resolution in (
        Resolution.INFERRED_ACCEPT_CANONICAL,
        Resolution.ACCEPT_UPSTREAM,
        Resolution.INFERRED_MERGED,
        Resolution.THREE_WAY_MERGE,
    ):
        resolved_content_path = f"/tmp/staging/{path}"
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
        resolved_content_path=resolved_content_path,
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

    # Bundle α (#57): the helper now calls classify (returns
    # unknown by default) before invoking the generator. So
    # total call count is 2 (classify + generator). What matters
    # for AC.WS.4 is that the generator IS invoked — verified by
    # consuming the queued verdict.
    assert stub.calls >= 1
    assert stub.queued == [], "queued generator verdict was consumed"
    assert report.conflicts[0].resolution in INFERRED_RESOLUTIONS

    # Audit + state YAML written.
    audit_p = audit_yaml_path(workspace_root, "testref")
    assert audit_p.exists()
    state_p = state_yaml_path(workspace_root)
    assert state_p.exists()
    state = load_state(workspace_root)
    assert state is not None
    # α-hotfix-2 #60 Bug D: the merge_helper writes NEEDS_APPLY
    # on clean-resolve (was SUCCESS pre-fix); cli.py post-apply is
    # the authoritative SUCCESS writer. This test calls
    # resolve_inferred_conflicts directly — no CLI apply path
    # runs — so the terminal status is correctly NEEDS_APPLY.
    assert state.status is SyncStatus.NEEDS_APPLY


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


# ----------------------------------------------------------------------
# Bundle α (#57) integration tests — α.2 classifier+primitive+verifier.
# ----------------------------------------------------------------------


def _classify(merge_class: str = "append-only-list", confidence: float = 0.9) -> MergeClassification:
    return MergeClassification(
        merge_class=merge_class, confidence=confidence, reasoning="t"
    )


def _verification(passed: bool = True, class_mismatch: bool = False, confidence: float = 0.9) -> MergeVerification:
    return MergeVerification(
        passed=passed,
        class_mismatch=class_mismatch,
        concerns=None,
        confidence=confidence,
    )


def test_alpha2_happy_path_accepts_deterministic_merge(tmp_path: Path) -> None:
    """AC.WSα.3 + .4 + .5: classify pass → primitive succeeds → verify pass → INFERRED_MERGED."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "list.md").write_text("- a\n- b\n")
    (workspace_root / "list.md").write_text("- a\n- b\n- c\n")

    stub = StubLLMClient(
        classify_responses=[(_classify("append-only-list"), 50)],
        verify_responses=[(_verification(passed=True), 100)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("list.md"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_MERGED
    assert e.classifier_class == "append-only-list"
    assert e.deterministic_primitive is not None
    assert "concat-dedup" in e.deterministic_primitive
    # The generator was NOT invoked — there are no queued generator verdicts.
    assert stub.queued == []
    assert e.fallback_reason is None


def test_alpha2_classifier_unknown_falls_through_to_generator(tmp_path: Path) -> None:
    """AC.WSα.6: classifier returns unknown → generator runs; fallback_reason recorded."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "binary-ish").write_text("\x00\x01\x02")
    (workspace_root / "binary-ish").write_text("\x00\x01\x03")

    stub = StubLLMClient(
        queued=[(_verdict(), 200)],
        classify_responses=[(_classify("unknown", confidence=0.0), 30)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("binary-ish"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.fallback_reason == "classifier-unknown"
    # Generator verdict was consumed.
    assert stub.queued == []


def test_alpha2_primitive_decline_falls_through_to_generator(tmp_path: Path) -> None:
    """AC.WSα.6: primitive raises MergeClassDeclined → generator runs; fallback_reason recorded."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    # Append-only-list classifier but the file has no bullets — primitive declines.
    (canonical_root / "x.md").write_text("just prose\n")
    (workspace_root / "x.md").write_text("different prose\n")

    stub = StubLLMClient(
        queued=[(_verdict(), 200)],
        classify_responses=[(_classify("append-only-list"), 30)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("x.md"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.fallback_reason is not None
    assert e.fallback_reason.startswith("primitive-failed")
    assert stub.queued == []  # generator consumed


def test_alpha2_verifier_rejects_falls_through_to_generator(tmp_path: Path) -> None:
    """AC.WSα.6: verifier returns passed=False → generator runs."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "list.md").write_text("- a\n- b\n")
    (workspace_root / "list.md").write_text("- a\n- b\n- c\n")

    stub = StubLLMClient(
        queued=[(_verdict(), 200)],
        classify_responses=[(_classify("append-only-list"), 30)],
        verify_responses=[(_verification(passed=False), 80)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("list.md"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    e = report.conflicts[0]
    assert e.fallback_reason == "verifier-rejected"
    assert stub.queued == []


def test_alpha2_otel_spans_emitted(tmp_path: Path) -> None:
    """AC.WSα.7: classify + verify spans emit under pos.sync.merge_gate.* namespace."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    # Add a processor to the EXISTING provider rather than overriding
    # (the prior test has already set one, and OTel's provider is
    # process-singleton).
    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        # First test in this process to use OTel — install a real provider.
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "list.md").write_text("- a\n- b\n")
    (workspace_root / "list.md").write_text("- a\n- b\n- c\n")

    stub = StubLLMClient(
        classify_responses=[(_classify("append-only-list"), 50)],
        verify_responses=[(_verification(passed=True), 100)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("list.md"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    span_names = [s.name for s in exporter.get_finished_spans()]
    assert "pos.sync.merge_gate.classify" in span_names
    assert "pos.sync.merge_gate.verify" in span_names
    assert "pos.sync.merge_gate.summary" in span_names


def test_alpha_backcompat_falls_through_to_existing_generator_path(tmp_path: Path) -> None:
    """Hard Constraint #4: with α.2 declines, the resolver path matches #56's behaviour byte-for-byte."""
    canonical_root = tmp_path / "canon"
    workspace_root = tmp_path / "ws"
    canonical_root.mkdir()
    workspace_root.mkdir()
    (canonical_root / "code.py").write_text("def f():\n    return 1\n")
    (workspace_root / "code.py").write_text("def f():\n    return 2\n")

    queued = [(_verdict(resolution="inferred-accept-canonical"), 250)]
    stub = StubLLMClient(
        queued=queued,
        # Classifier returns 'unknown' — α.2 falls through immediately.
        classify_responses=[(_classify("unknown"), 30)],
    )
    resolver = MergeResolver(stub)
    report = _make_report(_entry("code.py"))

    resolve_inferred_conflicts(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical_root,
        workspace_root=workspace_root,
        resolver=resolver,
    )

    e = report.conflicts[0]
    # Verdict matches what the queued #56-shape generator returned.
    assert e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert e.fallback_reason == "classifier-unknown"

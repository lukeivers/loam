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

"""Clause-(h) AC.H.7/8/9/12 — pre-stage helper + verifier integration."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from loam.self_upgrade.clause_checks import (
    check_clause_h,
    resolve_clause_h_inferred,
    run_all_clauses,
)
from loam.self_upgrade.conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    Resolution,
)
from loam.self_upgrade.merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
)
from loam.self_upgrade.sync_protected import (
    FRAMEWORK_FLOOR,
    FileClass,
    SyncProtected,
    SyncProtectedRule,
    default_sync_protected,
)


class StubLLMClient:
    def __init__(self, queued: list[tuple[MergeVerdict, int]]) -> None:
        self.queued = list(queued)

    def invoke(
        self, prompt: str, response_model: type[BaseModel]
    ) -> tuple[BaseModel, int]:
        if not self.queued:
            raise ResolverFailure("stub: out of canned verdicts")
        return self.queued.pop(0)


def _make_report(*, conflicts: list[ConflictEntry]) -> ConflictReport:
    return ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=conflicts,
    )


def _entry(
    path: str,
    *,
    resolution: Resolution = Resolution.PENDING,
    change_kind: ConflictChangeKind = ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
) -> ConflictEntry:
    return ConflictEntry(
        path=path,
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=change_kind,
        resolution=resolution,
    )


def test_clause_h_class_a_preserved(tmp_path: Path) -> None:
    """AC.H.2: Class-A path resolves to KEEP_LOCAL with high confidence."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "workspace" / ".pos").mkdir(parents=True)
    (canonical / "workspace" / ".pos" / "objective_tracker.sqlite").write_text("canonical-state")
    (workspace / "workspace" / ".pos").mkdir(parents=True)
    (workspace / "workspace" / ".pos" / "objective_tracker.sqlite").write_text("workspace-state")

    report = _make_report(
        conflicts=[_entry("workspace/.pos/objective_tracker.sqlite")]
    )
    sp = default_sync_protected()
    resolver = MergeResolver(StubLLMClient([]))  # unused for class A

    resolve_clause_h_inferred(
        report=report,
        sync_protected=sp,
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )
    e = report.conflicts[0]
    assert e.resolution is Resolution.KEEP_LOCAL
    assert e.confidence == 1.0
    assert "Class A" in (e.rationale or "")


def test_clause_h_class_c_invokes_resolver(tmp_path: Path) -> None:
    """AC.H.4: Class-C path goes through the LLM resolver."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "framework.py").write_text("canonical-content")
    (workspace / "framework.py").write_text("workspace-content")

    report = _make_report(conflicts=[_entry("framework.py")])
    sp = default_sync_protected()
    resolver = MergeResolver(
        StubLLMClient(
            [
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="canonical's update is independent of the workspace edit",
                        confidence=0.92,
                    ),
                    300,
                )
            ]
        )
    )
    resolve_clause_h_inferred(
        report=report,
        sync_protected=sp,
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert e.confidence == 0.92
    assert "canonical" in (e.rationale or "")


def test_clause_h_inferred_merged_writes_content(tmp_path: Path) -> None:
    """AC.H.4: inferred-merged persists merged_content for swap pickup."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "f.py").write_text("CANONICAL")
    (workspace / "f.py").write_text("WORKSPACE")

    report = _make_report(conflicts=[_entry("f.py")])
    resolver = MergeResolver(
        StubLLMClient(
            [
                (
                    MergeVerdict(
                        resolution="inferred-merged",
                        merged_content="MERGED-BOTH-SIDES",
                        rationale="combined intents",
                        confidence=0.78,
                    ),
                    400,
                )
            ]
        )
    )
    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )
    e = report.conflicts[0]
    assert e.resolution is Resolution.INFERRED_MERGED
    assert e.resolved_content_path is not None
    merged_text = Path(e.resolved_content_path).read_text()
    assert merged_text == "MERGED-BOTH-SIDES"


def test_clause_h_user_override_skipped(tmp_path: Path) -> None:
    """AC.H.9: user_override entries are NOT re-resolved."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "f.py").write_text("X")
    (workspace / "f.py").write_text("Y")

    overridden = ConflictEntry(
        path="f.py",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.KEEP_LOCAL,
        user_override=True,
        override_rationale="operator decision",
    )
    report = _make_report(conflicts=[overridden])
    resolver = MergeResolver(StubLLMClient([]))  # would ResolverFailure if invoked

    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )
    e = report.conflicts[0]
    assert e.resolution is Resolution.KEEP_LOCAL
    assert e.user_override is True
    assert resolver.call_count == 0


def test_clause_h_already_resolved_skipped(tmp_path: Path) -> None:
    """AC.H.8 / convergent idempotency: non-PENDING entries skipped."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "f.py").write_text("X")
    (workspace / "f.py").write_text("Y")

    report = _make_report(
        conflicts=[_entry("f.py", resolution=Resolution.ACCEPT_UPSTREAM)]
    )
    resolver = MergeResolver(StubLLMClient([]))
    resolve_clause_h_inferred(
        report=report,
        sync_protected=default_sync_protected(),
        canonical_root=canonical,
        workspace_root=workspace,
        resolver=resolver,
    )
    e = report.conflicts[0]
    assert e.resolution is Resolution.ACCEPT_UPSTREAM
    assert resolver.call_count == 0


def test_clause_h_budget_exhausted_halts(tmp_path: Path) -> None:
    """AC.H.6: budget exhaustion raises out, leaving prior entries resolved."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for f in ("a.py", "b.py", "c.py"):
        (canonical / f).write_text(f"CANON-{f}")
        (workspace / f).write_text(f"WORK-{f}")

    report = _make_report(
        conflicts=[_entry(f) for f in ("a.py", "b.py", "c.py")]
    )
    # Budget allows exactly one call at 5000 tokens; second halts.
    resolver = MergeResolver(
        StubLLMClient(
            [
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="r",
                        confidence=0.9,
                    ),
                    5_000,
                ),
                (
                    MergeVerdict(
                        resolution="inferred-accept-canonical",
                        rationale="r",
                        confidence=0.9,
                    ),
                    5_000,
                ),
            ]
        ),
        ResolverBudget(
            per_conflict_token_budget=5_000,
            cumulative_token_budget=5_000,
        ),
    )
    with pytest.raises(BudgetExhausted):
        resolve_clause_h_inferred(
            report=report,
            sync_protected=default_sync_protected(),
            canonical_root=canonical,
            workspace_root=workspace,
            resolver=resolver,
        )
    # First conflict resolved; second left PENDING.
    assert report.conflicts[0].resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert report.conflicts[1].resolution is Resolution.PENDING


def test_clause_h_resolver_failure_raises(tmp_path: Path) -> None:
    """AC.H.12: ResolverFailure surfaces (caller routes to rollback)."""
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (canonical / "f.py").write_text("X")
    (workspace / "f.py").write_text("Y")

    report = _make_report(conflicts=[_entry("f.py")])
    resolver = MergeResolver(StubLLMClient([]))  # immediate ResolverFailure

    with pytest.raises(ResolverFailure):
        resolve_clause_h_inferred(
            report=report,
            sync_protected=default_sync_protected(),
            canonical_root=canonical,
            workspace_root=workspace,
            resolver=resolver,
        )


def test_check_clause_h_passes_when_no_pending(tmp_path: Path) -> None:
    report = _make_report(
        conflicts=[
            ConflictEntry(
                path="x.py",
                prior_release_sha256=None,
                installed_sha256=None,
                new_release_sha256="c" * 64,
                change_kind=ConflictChangeKind.LOCAL_MODIFIED_ONLY,
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r",
                confidence=0.9,
            ),
        ]
    )
    res = check_clause_h(report)
    assert res.passed is True
    assert res.details["inferred_count"] == 1


def test_check_clause_h_fails_on_pending() -> None:
    report = _make_report(
        conflicts=[
            ConflictEntry(
                path="x.py",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
                resolution=Resolution.PENDING,
            )
        ]
    )
    res = check_clause_h(report)
    assert res.passed is False
    assert "pending" in (res.reason or "").lower()


def test_check_clause_h_skipped_when_no_report() -> None:
    """Legacy --staging-dir path (no clause-(h) pre-stage) → no-op pass."""
    res = check_clause_h(None)
    assert res.passed is True
    assert res.details.get("skipped") is True


def test_run_all_clauses_includes_h() -> None:
    """``h`` is part of the bundle's contract."""
    # Use the existing integration shape — minimal stub to exercise
    # the bundle's contract. Real clause-h verifier exercised above.
    from loam.self_upgrade.manifest import Manifest

    m = Manifest(
        release_tag="pos-v2-v0.2.0",
        commit_sha="abc1234",
    )
    # Use shared fixture conventions: pass live_root that won't exist,
    # which causes other clauses to fail (acceptable — we only assert "h" is present).
    from loam.self_upgrade.paths import Paths

    paths = Paths.from_env(None)
    bundle = run_all_clauses(
        no_op_rpc=lambda: True,
        survival_payloads={"loam": {"persona_identity": "x", "authority_boundary": "y", "current_scope_context": "z", "pending_decisions": [], "recent_corrections": []}},
        memory_drift_report=type("R", (), {"passed": True, "verdict_flip_fraction": 0, "mean_recall_delta": 0})(),
        scope_drift=type("R", (), {"total_drift": 0})(),
        objective_drift=type("R", (), {"total_drift": 0})(),
        manifest=m,
        paths=paths,
        tag="pos-v2-v0.2.0",
        live_root=Path("/tmp/nonexistent-root-for-this-test"),
        snapshot_components=("memory",),
        conflict_report=None,
    )
    assert "h" in bundle.results
    assert bundle.results["h"].passed is True  # None report = skipped pass

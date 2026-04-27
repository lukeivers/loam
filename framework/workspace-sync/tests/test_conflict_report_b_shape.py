"""AC.WS.4, AC.WS.5, AC.WS.9 — conflict-report B-shape tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from workspace_sync.conflict_report import (
    INFERRED_RESOLUTIONS,
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    ConflictSummary,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)


def _entry(
    *,
    path: str = "x.py",
    resolution: Resolution = Resolution.PENDING,
    rationale: str | None = None,
    confidence: float | None = None,
    user_override: bool = False,
    override_rationale: str | None = None,
    resolved_content_path: str | None = None,
    change_kind: ConflictChangeKind = ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
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
        resolved_content_path=resolved_content_path,
    )


def test_resolution_enum_includes_inferred_three() -> None:
    assert Resolution.INFERRED_ACCEPT_CANONICAL.value == "inferred-accept-canonical"
    assert Resolution.INFERRED_ACCEPT_WORKSPACE.value == "inferred-accept-workspace"
    assert Resolution.INFERRED_MERGED.value == "inferred-merged"
    assert INFERRED_RESOLUTIONS == frozenset({
        Resolution.INFERRED_ACCEPT_CANONICAL,
        Resolution.INFERRED_ACCEPT_WORKSPACE,
        Resolution.INFERRED_MERGED,
    })


def test_resolution_skipped_rejected_at_load() -> None:
    """AC.WS.5: schema rejects resolution=skipped at load (clause-g)."""
    with pytest.raises(ValueError):
        ConflictEntry.model_validate({
            "path": "x",
            "prior_release_sha256": None,
            "installed_sha256": None,
            "new_release_sha256": None,
            "change_kind": "upstream_modified_and_local_modified",
            "resolution": "skipped",
        })


def test_inferred_requires_rationale_and_confidence() -> None:
    """AC.WS.4 + AC.WS.5: INFERRED_* without rationale/confidence is invalid."""
    with pytest.raises(ValueError):
        _entry(resolution=Resolution.INFERRED_ACCEPT_CANONICAL)
    with pytest.raises(ValueError):
        _entry(resolution=Resolution.INFERRED_ACCEPT_CANONICAL, rationale="r")  # missing confidence


def test_user_override_requires_rationale() -> None:
    """AC.WS.9: user_override=True demands override_rationale."""
    with pytest.raises(ValueError):
        _entry(user_override=True)


def test_sorted_low_confidence_first() -> None:
    """AC.WS.5: ordering is low-confidence-first then path-asc."""
    # α-hotfix-2 #60 Bug C: INFERRED_ACCEPT_CANONICAL entries now
    # require resolved_content_path; supply a non-null value to
    # satisfy the validator (intent of this test is sort-order, not
    # null-content-path).
    report = ConflictReport(
        sync_ref="abc123",
        detected_at="2026-04-26T00:00:00Z",
        conflicts=[
            _entry(
                path="z.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.95,
                resolved_content_path="/tmp/staging/z.py",
            ),
            _entry(
                path="a.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.50,
                resolved_content_path="/tmp/staging/a.py",
            ),
            _entry(
                path="m.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.50,
                resolved_content_path="/tmp/staging/m.py",
            ),
            _entry(path="pending.py"),  # PENDING; no confidence; sorts last
        ],
    )
    sorted_entries = report.sorted_low_confidence_first()
    paths = [e.path for e in sorted_entries]
    assert paths == ["a.py", "m.py", "z.py", "pending.py"]


def test_sync_ref_field_replaces_upgrade_tag(tmp_path: Path) -> None:
    """ConflictReport's per-run identifier is sync_ref (not upgrade_tag)."""
    report = ConflictReport(
        sync_ref="abc123def456",
        prior_ref="prev",
        detected_at="2026-04-26T00:00:00Z",
        conflicts=[],
        summary=ConflictSummary(),
    )
    target = tmp_path / "audit.yaml"
    save_conflict_report(report, target)

    raw = yaml.safe_load(target.read_text())
    assert raw["sync_ref"] == "abc123def456"
    assert "upgrade_tag" not in raw
    assert raw["prior_ref"] == "prev"

    # round-trip
    loaded = load_conflict_report(target)
    assert loaded.sync_ref == "abc123def456"
    assert loaded.prior_ref == "prev"


# ---- α-hotfix-2 #60 (Bug C) — validator gates resolved_content_path on
# accept-canonical-flavored verdicts (structural-enforcement-default per
# ODD §5.3). Without this gate, the entire fault-class repaired by
# α-hotfix #59 + α-hotfix-2 (verdict set without canonical content
# staged → silent no-op at apply time) could re-ship on any future
# amendment that introduces a new code path producing one of these
# verdicts. -----------------------------------------------------------------


def test_alpha_hotfix_2_inferred_accept_canonical_requires_resolved_content_path() -> None:
    """AC.α-hotfix-2.3: ConflictEntry rejects INFERRED_ACCEPT_CANONICAL
    with null resolved_content_path.

    Pre-fix: the validator gated resolved_content_path only on
    INFERRED_MERGED + THREE_WAY_MERGE; INFERRED_ACCEPT_CANONICAL
    accepted null content paths and the audit YAML recorded the bug
    shape (resolved_content_path: null) without a structural
    rejection. apply_staging_atomically then silently no-op'd on the
    path while state.yaml advanced — false-success.

    Post-fix: constructing the bug shape raises ValueError. The same
    fault-class can no longer ship.
    """
    with pytest.raises(ValueError, match="resolved_content_path"):
        ConflictEntry(
            path="framework/x.py",
            prior_release_sha256=None,
            installed_sha256="b" * 64,
            new_release_sha256="c" * 64,
            change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
            resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
            rationale="LLM said accept canonical",
            confidence=0.95,
            resolved_content_path=None,  # the bug shape
        )


def test_alpha_hotfix_2_accept_upstream_requires_resolved_content_path() -> None:
    """AC.α-hotfix-2.3: ConflictEntry rejects ACCEPT_UPSTREAM with null
    resolved_content_path.

    Same shape as INFERRED_ACCEPT_CANONICAL — Class-B
    operator-prefers-canonical demands canonical's content be staged
    for apply to overwrite the workspace file. Pre-fix, the cli.py
    post-stage append-after-stage was a no-op; the entry's audit
    record showed accept-upstream with null content path and the
    workspace file silently never updated.
    """
    with pytest.raises(ValueError, match="resolved_content_path"):
        ConflictEntry(
            path="framework/x.py",
            prior_release_sha256=None,
            installed_sha256="b" * 64,
            new_release_sha256="c" * 64,
            change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
            resolution=Resolution.ACCEPT_UPSTREAM,
            resolved_content_path=None,  # the bug shape
        )


def test_alpha_hotfix_2_inferred_accept_workspace_remains_ungated() -> None:
    """AC.α-hotfix-2.3 explicit out-of-scope: INFERRED_ACCEPT_WORKSPACE
    does NOT require resolved_content_path. The workspace already
    holds the content; staging is unnecessary."""
    # Should construct without error.
    entry = ConflictEntry(
        path="framework/x.py",
        prior_release_sha256=None,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.INFERRED_ACCEPT_WORKSPACE,
        rationale="preserve workspace edits",
        confidence=0.9,
        resolved_content_path=None,  # correctly permitted
    )
    assert entry.resolution is Resolution.INFERRED_ACCEPT_WORKSPACE
    assert entry.resolved_content_path is None

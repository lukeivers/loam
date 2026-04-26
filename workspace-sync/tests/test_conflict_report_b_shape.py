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
    report = ConflictReport(
        sync_ref="abc123",
        detected_at="2026-04-26T00:00:00Z",
        conflicts=[
            _entry(
                path="z.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.95,
            ),
            _entry(
                path="a.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.50,
            ),
            _entry(
                path="m.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="r", confidence=0.50,
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

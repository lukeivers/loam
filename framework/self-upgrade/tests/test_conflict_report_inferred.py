"""Clause-(h) AC.H.4/5/9 — ConflictReport inferred-resolution tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.self_upgrade.conflict_report import (
    INFERRED_RESOLUTIONS,
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)


def _entry(
    *,
    path: str = "framework/x.py",
    resolution: Resolution = Resolution.PENDING,
    change_kind: ConflictChangeKind = ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
    rationale: str | None = None,
    confidence: float | None = None,
    user_override: bool = False,
    override_rationale: str | None = None,
    resolved_content_path: str | None = None,
) -> ConflictEntry:
    return ConflictEntry(
        path=path,
        prior_release_sha256="a" * 64,
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


def test_resolution_enum_extended() -> None:
    """AC.H.4: enum carries three INFERRED_* values."""
    assert Resolution.INFERRED_ACCEPT_CANONICAL.value == "inferred-accept-canonical"
    assert Resolution.INFERRED_ACCEPT_WORKSPACE.value == "inferred-accept-workspace"
    assert Resolution.INFERRED_MERGED.value == "inferred-merged"
    assert {
        Resolution.INFERRED_ACCEPT_CANONICAL,
        Resolution.INFERRED_ACCEPT_WORKSPACE,
        Resolution.INFERRED_MERGED,
    } == set(INFERRED_RESOLUTIONS)


def test_skipped_still_rejected() -> None:
    """clause-(g) "no silent skip" extends to clause-(h)."""
    with pytest.raises(ValueError, match="skipped"):
        ConflictEntry(
            path="x",
            prior_release_sha256=None,
            installed_sha256=None,
            new_release_sha256=None,
            change_kind=ConflictChangeKind.LOCAL_MODIFIED_ONLY,
            resolution="skipped",  # type: ignore[arg-type]
        )


def test_inferred_requires_rationale() -> None:
    """AC.H.5: INFERRED_* without rationale rejects."""
    with pytest.raises(ValueError, match="rationale"):
        _entry(resolution=Resolution.INFERRED_ACCEPT_CANONICAL, confidence=0.9)


def test_inferred_requires_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        _entry(
            resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
            rationale="canonical's change applies cleanly",
        )


def test_inferred_confidence_in_range() -> None:
    with pytest.raises(ValueError, match="confidence must be in"):
        _entry(
            resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
            rationale="ok",
            confidence=1.5,
        )


def test_inferred_merged_requires_content_path() -> None:
    """AC.H.4: INFERRED_MERGED demands resolved_content_path."""
    with pytest.raises(ValueError, match="resolved_content_path"):
        _entry(
            resolution=Resolution.INFERRED_MERGED,
            rationale="synthesised merge",
            confidence=0.85,
        )


def test_user_override_requires_rationale() -> None:
    """AC.H.9: user_override flag without override_rationale rejects."""
    with pytest.raises(ValueError, match="override_rationale"):
        _entry(
            resolution=Resolution.KEEP_LOCAL,
            user_override=True,
        )


def test_user_override_persistence_shape() -> None:
    """AC.H.9: a user-overridden entry round-trips through YAML."""
    e = _entry(
        resolution=Resolution.ACCEPT_UPSTREAM,
        user_override=True,
        override_rationale="operator decision: workspace edit was wrong",
    )
    assert e.user_override is True
    assert e.override_rationale.startswith("operator")


def test_round_trip_inferred_entry(tmp_path: Path) -> None:
    """AC.H.5: load/save round-trips inferred entries."""
    rpt = ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        detected_at="2026-04-26T00:00:00+00:00",
        conflicts=[
            _entry(
                path="a.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="redundant local edit",
                confidence=0.95,
            ),
            _entry(
                path="b.py",
                resolution=Resolution.INFERRED_MERGED,
                rationale="merged both sides",
                confidence=0.7,
                resolved_content_path="/tmp/merged/b.py",
            ),
        ],
    )
    target = tmp_path / "x-conflicts.yaml"
    save_conflict_report(rpt, target)
    loaded = load_conflict_report(target)
    assert len(loaded.conflicts) == 2
    a, b = loaded.conflicts
    assert a.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
    assert a.confidence == 0.95
    assert b.resolution is Resolution.INFERRED_MERGED
    assert b.resolved_content_path == "/tmp/merged/b.py"


def test_sorted_low_confidence_first() -> None:
    """AC.H.5: low-confidence-first ordering with deterministic tie-break."""
    rpt = ConflictReport(
        upgrade_tag="t",
        detected_at="x",
        conflicts=[
            _entry(
                path="z.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="...",
                confidence=0.95,
            ),
            _entry(
                path="a.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="...",
                confidence=0.55,
            ),
            _entry(
                path="m.py",
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="...",
                confidence=0.55,
            ),
            _entry(  # no confidence — sorts last
                path="manual.py", resolution=Resolution.KEEP_LOCAL
            ),
        ],
    )
    sorted_paths = [c.path for c in rpt.sorted_low_confidence_first()]
    # 0.55 first (a, m by path-asc), then 0.95 (z), then no-confidence (manual).
    assert sorted_paths == ["a.py", "m.py", "z.py", "manual.py"]


def test_inferred_entries_filter() -> None:
    rpt = ConflictReport(
        upgrade_tag="t",
        detected_at="x",
        conflicts=[
            _entry(
                resolution=Resolution.INFERRED_ACCEPT_CANONICAL,
                rationale="...",
                confidence=0.9,
                path="a.py",
            ),
            _entry(resolution=Resolution.KEEP_LOCAL, path="b.py"),
        ],
    )
    inferred = rpt.inferred_entries()
    assert len(inferred) == 1
    assert inferred[0].path == "a.py"

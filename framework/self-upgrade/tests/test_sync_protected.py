"""Clause-(h) AC.H.2/3/10 — sync-protected envelope tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from self_upgrade.sync_protected import (
    FRAMEWORK_FLOOR,
    FileClass,
    SyncProtected,
    SyncProtectedRule,
    classify,
    default_sync_protected,
    load_sync_protected,
    save_sync_protected,
    write_default_if_absent,
)


def test_default_envelope_carries_floor() -> None:
    """AC.H.10: default envelope ships every framework-floor rule."""
    sp = default_sync_protected()
    floor = {(r.pattern, r.klass) for r in sp.framework_floor}
    expected = {(p, k) for p, k in FRAMEWORK_FLOOR}
    assert floor == expected


def test_classify_class_a_workspace_state() -> None:
    """AC.H.2: workspace-state paths classify as A."""
    sp = default_sync_protected()
    assert classify("workspace/personas/loam/contract.yaml", sp) is FileClass.A
    assert classify("workspace/.pos/objective_tracker.sqlite", sp) is FileClass.A
    assert classify("workspace/.pos/upgrade/state.yaml", sp) is FileClass.A
    assert classify("workspace/.scratch/notes.md", sp) is FileClass.A
    assert classify("workspace/.mcp.json", sp) is FileClass.A


def test_classify_class_b_operator_pref() -> None:
    """AC.H.3: operator-pref paths classify as B."""
    sp = default_sync_protected()
    assert classify("workspace/memory.yaml", sp) is FileClass.B


def test_classify_class_c_default() -> None:
    """AC.H.4 substrate: unmatched paths default to C."""
    sp = default_sync_protected()
    assert classify("self-upgrade/src/self_upgrade/cli.py", sp) is FileClass.C
    assert classify("docs/foo.md", sp) is FileClass.C
    assert classify("some/random/file.txt", sp) is FileClass.C


def test_workspace_rules_match_first(tmp_path: Path) -> None:
    """workspace_rules win over framework_floor on first-match."""
    sp = SyncProtected(
        framework_floor=[
            SyncProtectedRule(pattern=p, klass=k)
            for p, k in FRAMEWORK_FLOOR
        ],
        workspace_rules=[
            SyncProtectedRule(pattern="docs/private/**", klass=FileClass.A),
        ],
    )
    assert classify("docs/private/secret.md", sp) is FileClass.A
    assert classify("docs/public/notes.md", sp) is FileClass.C


def test_floor_refused_on_removal() -> None:
    """AC.H.10: removing a framework-floor entry fails validation."""
    incomplete = [
        SyncProtectedRule(pattern=p, klass=k)
        for p, k in FRAMEWORK_FLOOR
        if p != "workspace/.mcp.json"  # drop one floor entry
    ]
    with pytest.raises(ValueError, match="missing framework-floor rules"):
        SyncProtected(framework_floor=incomplete, workspace_rules=[])


def test_load_save_roundtrip(tmp_path: Path) -> None:
    sp = default_sync_protected()
    target = tmp_path / "sync-protected.yaml"
    save_sync_protected(sp, target)
    loaded = load_sync_protected(target)
    assert {(r.pattern, r.klass) for r in loaded.framework_floor} == {
        (r.pattern, r.klass) for r in sp.framework_floor
    }


def test_load_rejects_floor_violation(tmp_path: Path) -> None:
    target = tmp_path / "bad.yaml"
    target.write_text(
        yaml.safe_dump(
            {
                "framework_floor": [
                    {"pattern": "workspace/.mcp.json", "klass": "A"},
                    # rest of floor missing
                ],
                "workspace_rules": [],
            }
        )
    )
    with pytest.raises(ValueError, match="missing framework-floor"):
        load_sync_protected(target)


def test_write_default_if_absent_writes_when_missing(tmp_path: Path) -> None:
    """AC.H.10: first-run writes the default envelope."""
    written = write_default_if_absent(tmp_path)
    assert written.exists()
    assert written == tmp_path / "workspace" / ".pos" / "sync-protected.yaml"
    sp = load_sync_protected(written)
    assert len(sp.framework_floor) == len(FRAMEWORK_FLOOR)


def test_write_default_if_absent_idempotent(tmp_path: Path) -> None:
    """AC.H.10: pre-existing files are not overwritten."""
    target_dir = tmp_path / "workspace" / ".pos"
    target_dir.mkdir(parents=True)
    target = target_dir / "sync-protected.yaml"
    # Build a custom envelope (still floor-valid) with a workspace rule.
    sp = SyncProtected(
        framework_floor=[
            SyncProtectedRule(pattern=p, klass=k)
            for p, k in FRAMEWORK_FLOOR
        ],
        workspace_rules=[
            SyncProtectedRule(pattern="custom/**", klass=FileClass.A),
        ],
    )
    save_sync_protected(sp, target)
    original = target.read_text()
    written = write_default_if_absent(tmp_path)
    assert written == target
    # Content unchanged.
    assert target.read_text() == original

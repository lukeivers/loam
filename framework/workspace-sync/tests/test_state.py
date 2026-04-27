"""AC.WS.5, AC.WS.8 — state.yaml + audit-path resolution tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from workspace_sync.state import (
    StateRecord,
    SyncStatus,
    audit_yaml_path,
    load_state,
    make_state_record,
    save_state,
    state_yaml_path,
)


def test_audit_path_under_pos_sync_ref(tmp_path: Path) -> None:
    """AC.WS.5: audit lands at <workspace>/.pos/sync/<ref>/audit.yaml."""
    p = audit_yaml_path(tmp_path, "abc123")
    assert p == tmp_path / "workspace" / ".pos" / "sync" / "abc123" / "audit.yaml"


def test_state_path_under_pos_sync(tmp_path: Path) -> None:
    """AC.WS.8: state.yaml lands at <workspace>/.pos/sync/state.yaml."""
    p = state_yaml_path(tmp_path)
    assert p == tmp_path / "workspace" / ".pos" / "sync" / "state.yaml"


def test_state_save_load_round_trip(tmp_path: Path) -> None:
    record = make_state_record(
        sync_ref="abc123",
        workspace_root=tmp_path,
        total_conflicts=3,
        resolved_count=3,
        deferred_count=0,
        cumulative_tokens_used=1200,
        status=SyncStatus.SUCCESS,
    )
    save_state(record, tmp_path)
    loaded = load_state(tmp_path)
    assert loaded is not None
    assert loaded.sync_ref == "abc123"
    assert loaded.status is SyncStatus.SUCCESS
    assert loaded.cumulative_tokens_used == 1200


def test_load_state_missing_returns_none(tmp_path: Path) -> None:
    assert load_state(tmp_path) is None


def test_state_record_uses_sync_ref_field(tmp_path: Path) -> None:
    """Field-level rename: sync_ref (not upgrade_tag) appears in YAML."""
    record = make_state_record(
        sync_ref="zzz",
        workspace_root=tmp_path,
        total_conflicts=0,
        resolved_count=0,
        deferred_count=0,
        cumulative_tokens_used=0,
        status=SyncStatus.SUCCESS,
    )
    save_state(record, tmp_path)
    raw = yaml.safe_load((tmp_path / "workspace" / ".pos" / "sync" / "state.yaml").read_text())
    assert raw["sync_ref"] == "zzz"
    assert "upgrade_tag" not in raw

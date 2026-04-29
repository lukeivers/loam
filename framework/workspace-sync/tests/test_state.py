"""SyncState (D-migration D.3 shape) round-trip + path resolution tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.workspace_sync.state import (
    SyncOutcome,
    SyncState,
    load_state,
    save_state,
    state_yaml_path,
)


def test_state_path_under_workspace_pos_sync(tmp_path: Path) -> None:
    """state.yaml lands at <workspace>/workspace/.pos/sync/state.yaml."""
    p = state_yaml_path(tmp_path)
    assert p == tmp_path / "workspace" / ".pos" / "sync" / "state.yaml"


def test_state_save_load_round_trip(tmp_path: Path) -> None:
    record = SyncState(
        last_synced_sha="abc123def456",
        last_synced_at="2026-04-26T13:00:00+00:00",
        last_branch="pos-v2",
        last_outcome=SyncOutcome.FAST_FORWARD,
    )
    save_state(record, tmp_path)
    loaded = load_state(tmp_path)
    assert loaded is not None
    assert loaded.last_synced_sha == "abc123def456"
    assert loaded.last_branch == "pos-v2"
    assert loaded.last_outcome is SyncOutcome.FAST_FORWARD


def test_load_state_missing_returns_none(tmp_path: Path) -> None:
    assert load_state(tmp_path) is None


def test_state_yaml_uses_d3_field_names(tmp_path: Path) -> None:
    """Field-level: D.3 fields (last_synced_sha, last_branch,
    last_outcome) appear in YAML; pre-D.3 fields (sync_ref,
    cumulative_tokens_used, status) do not."""
    record = SyncState(
        last_synced_sha="zzz",
        last_synced_at="2026-04-26T13:00:00+00:00",
        last_branch="pos-v2",
        last_outcome=SyncOutcome.UP_TO_DATE,
    )
    save_state(record, tmp_path)
    raw = yaml.safe_load(
        (tmp_path / "workspace" / ".pos" / "sync" / "state.yaml").read_text()
    )
    assert raw["last_synced_sha"] == "zzz"
    assert raw["last_branch"] == "pos-v2"
    assert raw["last_outcome"] == "up-to-date"
    assert "sync_ref" not in raw
    assert "cumulative_tokens_used" not in raw
    assert "status" not in raw


def test_all_outcomes_round_trip(tmp_path: Path) -> None:
    """Every SyncOutcome value round-trips cleanly."""
    for outcome in SyncOutcome:
        record = SyncState(
            last_synced_sha=f"sha-{outcome.value}",
            last_synced_at="2026-04-26T13:00:00+00:00",
            last_branch="pos-v2",
            last_outcome=outcome,
        )
        save_state(record, tmp_path)
        loaded = load_state(tmp_path)
        assert loaded is not None
        assert loaded.last_outcome is outcome

"""Tests for ``self_upgrade.state`` — clause-(h) state.yaml + audit-path.

Covers AC.HFX.2 (state.yaml schema + round-trip + auto-discovery
shape) and AC.HFX.3 (workspace-local audit path resolution). The
in-helper integration tests live in
``test_bb_feat_synthetic_validation.py`` (the CC synthetic-validation
file whose halt-surface markers were flipped by amendment #55).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from self_upgrade.state import (
    StateRecord,
    UpgradeStatus,
    audit_yaml_path,
    load_state,
    make_state_record,
    save_state,
    state_yaml_path,
)


def test_state_yaml_path_workspace_relative(tmp_path: Path) -> None:
    """state.yaml lives at ``<workspace>/.pos/upgrade/state.yaml``."""
    p = state_yaml_path(tmp_path)
    assert p == tmp_path / ".pos" / "upgrade" / "state.yaml"


def test_audit_yaml_path_includes_tag(tmp_path: Path) -> None:
    """audit.yaml lives at ``<workspace>/.pos/upgrade/<tag>/audit.yaml``."""
    p = audit_yaml_path(tmp_path, "pos-v2-v0.2.0")
    assert p == (
        tmp_path / ".pos" / "upgrade" / "pos-v2-v0.2.0" / "audit.yaml"
    )


def test_state_record_round_trip(tmp_path: Path) -> None:
    """StateRecord round-trips via save_state + load_state."""
    record = make_state_record(
        upgrade_tag="pos-v2-v0.2.0",
        workspace_root=tmp_path,
        total_conflicts=3,
        resolved_count=2,
        deferred_count=1,
        cumulative_tokens_used=1234,
        status=UpgradeStatus.PARTIAL,
        halt_reason=None,
    )
    save_state(record, tmp_path)
    loaded = load_state(tmp_path)
    assert loaded is not None
    assert loaded.upgrade_tag == "pos-v2-v0.2.0"
    assert loaded.status is UpgradeStatus.PARTIAL
    assert loaded.total_conflicts == 3
    assert loaded.resolved_count == 2
    assert loaded.deferred_count == 1
    assert loaded.cumulative_tokens_used == 1234
    assert loaded.halt_reason is None
    assert loaded.audit_path.endswith(
        "/.pos/upgrade/pos-v2-v0.2.0/audit.yaml"
    )


def test_load_state_returns_none_when_absent(tmp_path: Path) -> None:
    """A workspace without state.yaml returns None (no soft-fail)."""
    assert load_state(tmp_path) is None


def test_state_record_rejects_negative_counts() -> None:
    """ge=0 constraint refuses negative counts at validation time."""
    with pytest.raises(ValidationError):
        StateRecord(
            upgrade_tag="t",
            timestamp="2026-04-26T00:00:00+00:00",
            audit_path="/x/audit.yaml",
            total_conflicts=-1,
            resolved_count=0,
            deferred_count=0,
            cumulative_tokens_used=0,
            status=UpgradeStatus.SUCCESS,
        )


def test_state_record_status_enum_only() -> None:
    """status must be one of success / failure / partial."""
    with pytest.raises(ValidationError):
        StateRecord(
            upgrade_tag="t",
            timestamp="2026-04-26T00:00:00+00:00",
            audit_path="/x/audit.yaml",
            total_conflicts=0,
            resolved_count=0,
            deferred_count=0,
            cumulative_tokens_used=0,
            status="aborted",  # type: ignore[arg-type]
        )


def test_state_record_halt_reason_carries_through_yaml(tmp_path: Path) -> None:
    """halt_reason serialises + deserialises for failure paths."""
    record = make_state_record(
        upgrade_tag="t",
        workspace_root=tmp_path,
        total_conflicts=2,
        resolved_count=1,
        deferred_count=0,
        cumulative_tokens_used=5000,
        status=UpgradeStatus.FAILURE,
        halt_reason="resolver_failure: stub: out of canned verdicts",
    )
    save_state(record, tmp_path)
    p = state_yaml_path(tmp_path)
    raw = yaml.safe_load(p.read_text())
    assert raw["halt_reason"] == (
        "resolver_failure: stub: out of canned verdicts"
    )
    assert raw["status"] == "failure"

    loaded = load_state(tmp_path)
    assert loaded is not None
    assert loaded.halt_reason == (
        "resolver_failure: stub: out of canned verdicts"
    )

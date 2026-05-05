"""AC.PRGATE.6 — Audit-log per gate decision at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.PRGATE.6.

Additive payload (no schema-version bump); SOC-2 floor preserved.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_pr_safety.audit import list_entries, write_audit_entry


def test_audit_entry_carries_objective_altitude_fields(tmp_workspace):
    """Audit payload includes objective_ids_touched + objective_bands_touched
    + backing_rows_overlapped + extraction_id."""
    entry_path = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="test-repo",
        repo_sha="abc1234567890def",
        diff_range="working-tree vs HEAD",
        safety_profile="dev",
        decision="HARD_BLOCK",
        requires_ratification=True,
        touched_acs=["O.auth.1"],  # backward compat
        objective_ids_touched=["O.auth.1"],
        objective_bands_touched={"O.auth.1": "VERIFIED"},
        backing_rows_overlapped={
            "O.auth.1": ["route:app/auth.py:10-25"]
        },
        extraction_id="repo-abc123",
        novel_count=0,
        reason="HARD_BLOCK — diff touches VERIFIED objective O.auth.1",
    )
    data = yaml.safe_load(entry_path.read_text())
    assert data["event_kind"] == "gate_decision"
    assert data["objective_ids_touched"] == ["O.auth.1"]
    assert data["objective_bands_touched"] == {"O.auth.1": "VERIFIED"}
    assert data["backing_rows_overlapped"] == {
        "O.auth.1": ["route:app/auth.py:10-25"]
    }
    assert data["extraction_id"] == "repo-abc123"


def test_legacy_callers_still_work_with_minimal_args(tmp_workspace):
    """write_audit_entry without new fields → defaults to empty."""
    entry_path = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="test-repo",
        decision="PASS",
        reason="no touch",
    )
    data = yaml.safe_load(entry_path.read_text())
    assert data["objective_ids_touched"] == []
    assert data["objective_bands_touched"] == {}
    assert data["backing_rows_overlapped"] == {}
    assert data["extraction_id"] is None


def test_round_trip_through_list_entries(tmp_workspace):
    """Multiple audit entries enumerated via list_entries."""
    for i in range(3):
        write_audit_entry(
            tmp_workspace,
            event_kind="gate_decision",
            repo_id="test-repo",
            decision="PASS",
            objective_ids_touched=[f"O.x.{i + 1}"],
            extraction_id="ext",
        )
    entries = list_entries(tmp_workspace)
    assert len(entries) == 3
    for entry in entries:
        data = yaml.safe_load(entry.read_text())
        assert "objective_ids_touched" in data


def test_schema_version_unchanged(tmp_workspace):
    """AC.PRGATE.6 — additive payload; no schema-version bump."""
    entry_path = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="test-repo",
        decision="HARD_BLOCK",
        objective_ids_touched=["O.auth.1"],
        extraction_id="ext",
    )
    data = yaml.safe_load(entry_path.read_text())
    assert data["schema_version"] == 1


def test_production_stake_audit_preserves_requires_ratification(tmp_workspace):
    """SOC-2 floor (Decision P) — production-stake gate decisions
    record requires_ratification=True."""
    entry_path = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="test-repo",
        safety_profile="production-stake",
        decision="SURFACE_DECISION",
        requires_ratification=True,
        objective_ids_touched=["O.orders.1"],
        objective_bands_touched={"O.orders.1": "PLAUSIBLE"},
        extraction_id="ext",
    )
    data = yaml.safe_load(entry_path.read_text())
    assert data["safety_profile"] == "production-stake"
    assert data["requires_ratification"] is True

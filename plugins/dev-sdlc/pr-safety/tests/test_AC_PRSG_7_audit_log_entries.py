"""AC.PRSG.7 — SOC-2 audit-trail floor."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from loam_pr_safety import (
    audit_log_dir,
    list_entries,
    write_audit_entry,
)


_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}\.yaml$")


def test_audit_log_dir_path(tmp_workspace):
    p = audit_log_dir(tmp_workspace)
    assert str(p).endswith(".loam/pr-safety/audit-log")


def test_write_audit_entry_creates_file(tmp_workspace):
    p = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r-12345678",
        repo_sha="abc1234",
        diff_range="HEAD~1..HEAD",
        safety_profile="dev",
        decision="HARD_BLOCK",
        requires_ratification=True,
        touched_acs=["AC.X.1"],
        novel_count=0,
        reason="reason here",
    )
    assert p.exists()
    assert _FILENAME_RE.match(p.name)
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["event_kind"] == "gate_decision"
    assert payload["repo_id"] == "r-12345678"
    assert payload["decision"] == "HARD_BLOCK"
    assert payload["requires_ratification"] is True
    assert payload["touched_acs"] == ["AC.X.1"]


def test_write_audit_entry_each_event_kind(tmp_workspace):
    """Each named event-kind writes a distinct entry."""
    kinds = [
        "gate_decision",
        "override_proposed",
        "override_approved",
        "override_rejected",
        "dry_run",
    ]
    for k in kinds:
        write_audit_entry(
            tmp_workspace,
            event_kind=k,
            repo_id="r",
            decision="X",
        )
    entries = list_entries(tmp_workspace)
    assert len(entries) == len(kinds)
    seen_kinds = []
    for entry in entries:
        payload = yaml.safe_load(entry.read_text(encoding="utf-8"))
        seen_kinds.append(payload["event_kind"])
    assert sorted(seen_kinds) == sorted(kinds)


def test_audit_filename_monotonic_per_day(tmp_workspace):
    """Filenames increment NNNN per (date) bucket."""
    a = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-04",
    )
    b = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-04",
    )
    c = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-04",
    )
    # Filenames should sort 0001 < 0002 < 0003.
    assert a.name == "2026-05-04-0001.yaml"
    assert b.name == "2026-05-04-0002.yaml"
    assert c.name == "2026-05-04-0003.yaml"


def test_audit_per_day_resets_counter(tmp_workspace):
    """A new YYYY-MM-DD bucket starts at 0001."""
    write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-04",
    )
    write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-04",
    )
    next_day = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r",
        today_ymd="2026-05-05",
    )
    assert next_day.name == "2026-05-05-0001.yaml"


def test_audit_entry_required_fields_populated(tmp_workspace):
    p = write_audit_entry(
        tmp_workspace,
        event_kind="gate_decision",
        repo_id="r-1",
        repo_sha="def5678",
        diff_range="abc..def",
        safety_profile="production-stake",
        decision="PASS",
        requires_ratification=False,
        touched_acs=[],
        novel_count=0,
        reason="clean",
        owner="user@x",
        rationale=None,
    )
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    for field in (
        "schema_version",
        "event_kind",
        "timestamp",
        "repo_id",
        "repo_sha",
        "diff_range",
        "safety_profile",
        "decision",
        "requires_ratification",
        "touched_acs",
        "novel_count",
        "reason",
        "owner",
        "rationale",
    ):
        assert field in payload, f"missing field {field}"
    # timestamp is ISO 8601 with TZ.
    assert "T" in payload["timestamp"]
    assert (
        "+00:00" in payload["timestamp"]
        or "Z" in payload["timestamp"]
    )

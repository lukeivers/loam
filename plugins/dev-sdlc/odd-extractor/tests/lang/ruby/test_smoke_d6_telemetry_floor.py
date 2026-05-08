"""Smoke D6 — telemetry floor.

Per plan-doc §6 D6:

- Run a full extraction against the synthetic fixture.
- Assert audit log has expected event_kind sequence.
- Schema version preserved at 1; filenames monotonic.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.budget import budget_from_cents
from loam_odd_extractor.generate import generate_raw_acs
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.observability import list_entries
from loam_odd_extractor.state import compute_repo_id, extraction_dir
from loam_odd_extractor.verify import verify_contract


def test_audit_log_has_expected_event_kinds(
    synthetic_rails_repo: Path, tmp_path: Path,
) -> None:
    """Full extraction → extraction_start + 4×stage_complete +
    extraction_end at minimum.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=synthetic_rails_repo,
        workspace_root=workspace,
        budget=budget_from_cents(5000),
        dry_run=False,
    )
    plan = analyze_repo(config=config)
    raw = generate_raw_acs(config=config, plan=plan)
    verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(synthetic_rails_repo)
    ext_dir = extraction_dir(workspace, repo_id)
    entries = list_entries(ext_dir)
    assert len(entries) >= 5  # start + 4 stage_complete + end (some
                              # may coalesce)

    event_kinds = []
    for entry_path in entries:
        payload = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == 1
        event_kinds.append(payload["event_kind"])

    # extraction_start + 4 stage_complete + extraction_end.
    assert "extraction_start" in event_kinds
    assert event_kinds.count("stage_complete") == 4
    assert "extraction_end" in event_kinds


def test_audit_log_filenames_monotonic(
    synthetic_rails_repo: Path, tmp_path: Path,
) -> None:
    """Filenames are NNNN.yaml with monotonic counter."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=synthetic_rails_repo,
        workspace_root=workspace,
        budget=budget_from_cents(5000),
        dry_run=False,
    )
    plan = analyze_repo(config=config)
    raw = generate_raw_acs(config=config, plan=plan)
    verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(synthetic_rails_repo)
    ext_dir = extraction_dir(workspace, repo_id)
    entries = list_entries(ext_dir)
    nums = [int(p.stem) for p in entries]
    assert nums == sorted(nums)
    assert nums[0] == 1
    # Sequential without gaps.
    for prev, curr in zip(nums, nums[1:]):
        assert curr == prev + 1


def test_every_audit_entry_carries_required_fields(
    synthetic_rails_repo: Path, tmp_path: Path,
) -> None:
    """Each entry has schema_version, timestamp (ISO8601 with TZ),
    extraction_id, event_kind."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=synthetic_rails_repo,
        workspace_root=workspace,
        budget=budget_from_cents(5000),
        dry_run=False,
    )
    plan = analyze_repo(config=config)
    raw = generate_raw_acs(config=config, plan=plan)
    verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(synthetic_rails_repo)
    ext_dir = extraction_dir(workspace, repo_id)

    for entry_path in list_entries(ext_dir):
        payload = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
        assert "schema_version" in payload
        assert payload["schema_version"] == 1
        assert "timestamp" in payload
        # ISO 8601 with timezone — contains "+" (e.g., +00:00) or "Z".
        ts = payload["timestamp"]
        assert ts and ("+" in ts or ts.endswith("Z"))
        assert "extraction_id" in payload
        assert "event_kind" in payload

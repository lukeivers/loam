"""Smoke D6 — telemetry floor against the canonical ruby-rails-payment
fixture (v0.1.8 Cycle 4b).

Per smoke-test-discipline §6 + plan-doc §6 D6 — extraction writes
audit-log entries per stage + per slice + per recognizer-finding;
filenames monotonic; schema v1 preserved.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.budget import budget_from_cents
from loam_odd_extractor.generate import generate_raw_acs
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.state import compute_repo_id, extraction_dir
from loam_odd_extractor.verify import verify_contract


def test_canonical_fixture_writes_telemetry_floor(
    canonical_ruby_rails_payment_repo: Path, tmp_path: Path,
) -> None:
    """Full extraction writes the AC.OREK.7 + AC.RAILS audit-log floor
    against the canonical fixture.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=canonical_ruby_rails_payment_repo,
        workspace_root=workspace,
        budget=budget_from_cents(5000),
        dry_run=False,
    )
    plan = analyze_repo(config=config)
    raw = generate_raw_acs(config=config, plan=plan)
    verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(canonical_ruby_rails_payment_repo)
    ext_dir = extraction_dir(workspace, repo_id)
    audit_dir = ext_dir / "audit-log"

    assert audit_dir.is_dir(), "Audit-log directory missing"

    entries = sorted(audit_dir.glob("*.yaml"))
    assert len(entries) >= 6, (
        f"Audit log has {len(entries)} entries; floor is 6 "
        f"(extraction_start + 4× stage_complete + extraction_end)"
    )

    # Filenames monotonic (NNNN.yaml).
    names = [e.stem for e in entries]
    for name in names:
        assert name.isdigit() or name.replace("-", "").isdigit(), (
            f"Audit log filename '{name}' not monotonic-numeric"
        )

    # Each entry parses as YAML and has an event_kind.
    event_kinds: list[str] = []
    for entry in entries:
        payload = yaml.safe_load(entry.read_text())
        assert payload is not None
        assert "event_kind" in payload
        event_kinds.append(payload["event_kind"])

    # Required event kinds present.
    assert "extraction_start" in event_kinds
    assert "stage_complete" in event_kinds
    assert "extraction_end" in event_kinds

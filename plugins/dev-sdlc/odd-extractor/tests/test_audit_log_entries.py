"""D6 — operational telemetry floor smoke.

Per smoke-test-discipline §2.6 + plan-doc §6 D6: each stage writes
one audit-log entry; each run writes start + end bookend entries.
SOC-2 audit-trail floor (Decision P).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.cli import main as cli_main


def _audit_entries(extraction_dir: Path) -> list[dict]:
    audit_dir = extraction_dir / "audit-log"
    entries = []
    for entry_path in sorted(audit_dir.iterdir()):
        data = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
        entries.append(data)
    return entries


def test_audit_log_entries_per_stage_plus_bookends(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """1 extraction_start + 4 stage_complete + 1 extraction_end = 6 entries."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    entries = _audit_entries(repo_id_dir)
    assert len(entries) == 6

    kinds = [e["event_kind"] for e in entries]
    assert kinds[0] == "extraction_start"
    assert kinds[-1] == "extraction_end"
    stage_completes = [e for e in entries if e["event_kind"] == "stage_complete"]
    assert len(stage_completes) == 4
    stages = [e["stage"] for e in stage_completes]
    assert stages == ["init", "analyze", "generate", "verify"]


def test_audit_log_entry_schema(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Every entry has schema_version + ISO8601 timestamp + extraction_id +
    event_kind."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    for entry in _audit_entries(repo_id_dir):
        assert entry["schema_version"] == 1
        assert "timestamp" in entry
        # Timestamp is ISO 8601 with timezone offset.
        ts = entry["timestamp"]
        assert "T" in ts
        assert "+" in ts or ts.endswith("Z")
        assert entry["extraction_id"]
        assert entry["event_kind"] in {
            "extraction_start",
            "stage_complete",
            "extraction_end",
            "extraction_failed",
            "budget_override",
        }


def test_audit_log_filenames_monotonic_zero_padded(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Filenames follow <NNNN>.yaml with monotonic sequence."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    audit_dir = repo_id_dir / "audit-log"
    names = sorted(p.name for p in audit_dir.iterdir())
    expected = [f"{i:04d}.yaml" for i in range(1, len(names) + 1)]
    assert names == expected

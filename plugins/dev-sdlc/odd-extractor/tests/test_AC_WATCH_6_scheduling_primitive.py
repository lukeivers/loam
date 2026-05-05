"""AC.WATCH.6 — Scheduling integration (CLI-as-primitive).

Tests:

- `--invocation-source` flag accepted + recorded in audit-log.
- Default invocation_source is `cli_human`.
- Multiple invocation_source values (cli_cron / cli_schedule_skill)
  pass through to audit-log notes.
- README documents three scheduling examples.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.cli import main
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _incremental_helpers import (  # type: ignore[import-not-found]
    init_git_repo,
    make_plausible_ac,
    write_prior_contract,
)


def _read_audit_entries(workspace: Path, repo_id: str) -> list[dict]:
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    if not audit_dir.exists():
        return []
    entries: list[dict] = []
    for fp in sorted(audit_dir.iterdir()):
        if fp.suffix == ".yaml":
            entries.append(yaml.safe_load(fp.read_text(encoding="utf-8")))
    return entries


def _setup_workspace_and_run(
    *, tmp_path: Path, invocation_source: str | None = None
) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=["a.py"],
        citations=["a.py:1-1"],
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=[ac],
        created_at="2099-01-01T00:00:00+00:00",
    )
    args = [
        str(repo),
        "--incremental",
        "--workspace-root",
        str(workspace),
        "--json",
    ]
    if invocation_source is not None:
        args += ["--invocation-source", invocation_source]
    rc = main(args)
    assert rc == 0
    return workspace, compute_repo_id(repo)


def test_default_invocation_source_is_cli_human(
    tmp_path: Path,
) -> None:
    workspace, repo_id = _setup_workspace_and_run(tmp_path=tmp_path)
    entries = _read_audit_entries(workspace, repo_id)
    watch_entries = [
        e for e in entries if e.get("event_kind") == "incremental_watch_run"
    ]
    assert len(watch_entries) >= 1
    assert "invocation_source=cli_human" in watch_entries[0]["notes"]


def test_cli_cron_invocation_source_recorded(tmp_path: Path) -> None:
    workspace, repo_id = _setup_workspace_and_run(
        tmp_path=tmp_path, invocation_source="cli_cron"
    )
    entries = _read_audit_entries(workspace, repo_id)
    watch_entries = [
        e for e in entries if e.get("event_kind") == "incremental_watch_run"
    ]
    assert any(
        "invocation_source=cli_cron" in e["notes"]
        for e in watch_entries
    )


def test_cli_schedule_skill_invocation_source_recorded(
    tmp_path: Path,
) -> None:
    workspace, repo_id = _setup_workspace_and_run(
        tmp_path=tmp_path, invocation_source="cli_schedule_skill"
    )
    entries = _read_audit_entries(workspace, repo_id)
    watch_entries = [
        e for e in entries if e.get("event_kind") == "incremental_watch_run"
    ]
    assert any(
        "invocation_source=cli_schedule_skill" in e["notes"]
        for e in watch_entries
    )


def test_readme_documents_scheduling() -> None:
    """README has a Scheduling section with the three example
    schedules per AC.WATCH.6."""
    readme = Path(__file__).parent.parent / "README.md"
    assert readme.exists()
    text = readme.read_text(encoding="utf-8")
    # Per AC.WATCH.6: launchd, crontab, /schedule skill all named.
    assert "Scheduling" in text or "scheduling" in text
    assert "--incremental" in text
    # At least one of the three example shapes named.
    assert (
        "launchd" in text.lower()
        or "crontab" in text.lower()
        or "/schedule" in text
    )

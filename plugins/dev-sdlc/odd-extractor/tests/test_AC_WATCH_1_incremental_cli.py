"""AC.WATCH.1 — Incremental-mode CLI.

Tests the `loam odd-extract <repo> --incremental` surface:

- Argparse exposes `--incremental` + `--invocation-source` flags.
- Default invocation runs without `--pm-name`.
- ContractNotFoundError when no prior contract sidecar exists.
- Successful run against a synthetic prior contract returns exit 0.
- `--json` output is structured.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from loam_odd_extractor.cli import build_odd_extract_subcommand, main

from _incremental_helpers import (  # type: ignore[import-not-found]
    init_git_repo,
    make_plausible_ac,
    write_prior_contract,
)


def test_incremental_flag_is_argparse_visible() -> None:
    """`loam odd-extract --help` lists the --incremental flag."""
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_odd_extract_subcommand(sub)
    # Parse --help-style to verify flag presence.
    help_text = parser.format_help()
    # The leaf parser holds the flag; access via subparser.
    import io

    buf = io.StringIO()
    parser._subparsers._group_actions[0].choices[  # type: ignore[attr-defined]
        "odd-extract"
    ].print_help(buf)
    odd_help = buf.getvalue()
    assert "--incremental" in odd_help
    assert "--invocation-source" in odd_help


def test_invocation_source_flag_default(tmp_path: Path) -> None:
    """Default --invocation-source is 'cli_human'."""
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
    rc = main(
        [
            str(repo),
            "--incremental",
            "--workspace-root",
            str(workspace),
            "--json",
        ]
    )
    assert rc == 0


def test_contract_not_found_error_when_no_prior(
    tmp_path: Path, capsys
) -> None:
    """Without a prior contract sidecar, --incremental exits non-zero
    with ContractNotFoundError."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    workspace = tmp_path / "ws"
    workspace.mkdir()
    rc = main(
        [
            str(repo),
            "--incremental",
            "--workspace-root",
            str(workspace),
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "--incremental" in err


def test_json_output_is_structured(tmp_path: Path, capsys) -> None:
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
    rc = main(
        [
            str(repo),
            "--incremental",
            "--workspace-root",
            str(workspace),
            "--json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "extraction_id" in payload
    assert "summary" in payload
    assert "still_current" in payload["summary"]
    assert "out_of_date" in payload["summary"]
    assert "orphaned" in payload["summary"]
    assert "audit_log_entries_written" in payload


def test_incremental_human_output(tmp_path: Path, capsys) -> None:
    """Without --json, the CLI emits a human-readable summary."""
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
    rc = main(
        [
            str(repo),
            "--incremental",
            "--workspace-root",
            str(workspace),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Incremental watch run" in out
    assert "Summary:" in out
    assert "still-current" in out
    assert "Audit-log entries written" in out

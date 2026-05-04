"""AC.OREK.2 — `loam odd-extract <repo-path>` CLI invocable.

- Argparse surface: --live, --budget-cents N, --budget-override,
  --workspace-root, --stage, --status, --resume, --json.
- Dry-run by default per Decision D.
- Runs end-to-end against a tmp fixture without invoking any LLM.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam_odd_extractor.cli import (
    build_odd_extract_subcommand,
    main as cli_main,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loam-test")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)
    return parser


def test_subcommand_registers() -> None:
    """`build_odd_extract_subcommand` adds an `odd-extract` parser."""
    parser = _build_parser()
    # Probe by parsing --help (which raises SystemExit but we
    # short-circuit by inspecting the parser tree).
    actions = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    assert len(actions) == 1
    assert "odd-extract" in actions[0].choices


def test_argparse_surface_includes_required_flags() -> None:
    """All AC-named flags are accepted."""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "odd-extract",
            "/tmp/fake",
            "--live",
            "--budget-cents",
            "500",
            "--budget-override",
            "--workspace-root",
            "/tmp/ws",
            "--stage",
            "init",
            "--json",
        ]
    )
    assert args.live is True
    assert args.budget_cents == 500
    assert args.budget_override is True
    assert args.workspace_root == Path("/tmp/ws")
    assert args.stage == "init"
    assert args.json is True


def test_status_and_resume_flags_present() -> None:
    parser = _build_parser()
    a = parser.parse_args(
        ["odd-extract", "/tmp/fake", "--status"]
    )
    assert a.status is True
    assert a.resume is False
    b = parser.parse_args(
        ["odd-extract", "/tmp/fake", "--resume"]
    )
    assert b.resume is True
    assert b.status is False


def test_dry_run_is_default(fixture_repo: Path, workspace_root: Path) -> None:
    """No --live flag → dry-run path runs end-to-end without LLM
    invocation. Exit status 0."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    # Verify dry_run flag landed in config.yaml
    import yaml

    repo_id_dirs = list(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    assert len(repo_id_dirs) == 1
    config_path = repo_id_dirs[0] / "config.yaml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg["dry_run"] is True


def test_cli_runs_end_to_end_against_fixture(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Full four-stage workflow lands four artefacts."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    for fname in (
        "config.yaml",
        "plan.yaml",
        "raw-acs.yaml",
        "contract-draft.md",
        "contract-draft.yaml",
        "state.yaml",
    ):
        assert (repo_id_dir / fname).exists(), f"missing {fname}"


def test_repo_path_must_exist(workspace_root: Path) -> None:
    """Non-existent repo path → exit 2 + stderr message."""
    rc = cli_main(
        [
            "/this/path/does/not/exist",
            "--workspace-root",
            str(workspace_root),
        ]
    )
    assert rc == 2

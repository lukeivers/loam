"""AC.PERSONA-PULL.1 — CLI flag ``--build-next``.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.PERSONA-PULL.1:

- Additive in ``_cmd_dispatch`` alongside ``--interview`` and ``--gaps``.
- Handler ``_cmd_build_next(args)`` mirrors ``_cmd_gaps`` shape.
- Halts exit code 2 + actionable message when predecessors missing.
- Idempotent re-run (per AC.BLDNXT.4).
- Stdout summary; exit codes correct.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.cli import main as cli_main
from loam_odd_extractor.state import compute_repo_id, extraction_dir


def _setup_workspace_with_predecessors(
    tmp_path: Path,
    *,
    repo_name: str = "fixture-repo",
    fixture: str = "no-survey-context",
) -> tuple[Path, Path, str]:
    """Create fixture repo + workspace with augmented + gap-inventory files."""
    repo = tmp_path / repo_name
    repo.mkdir()
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)

    # Copy fixture's augmented-objectives.yaml + gap-inventory.yaml
    # into the workspace's extraction-dir.
    fdir = (
        Path(__file__).parent
        / "fixtures"
        / "build-next"
        / fixture
    )
    aug_payload = yaml.safe_load(
        (fdir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    )
    # Re-key extraction_id to match the workspace's repo_id (else
    # round-trip / load uses wrong id).
    aug_payload["extraction_id"] = repo_id
    (ext_dir / "augmented-objectives.yaml").write_text(
        yaml.safe_dump(aug_payload, sort_keys=False), encoding="utf-8"
    )
    inv_payload = yaml.safe_load(
        (fdir / "gap-inventory.yaml").read_text(encoding="utf-8")
    )
    inv_payload["extraction_id"] = repo_id
    (ext_dir / "gap-inventory.yaml").write_text(
        yaml.safe_dump(inv_payload, sort_keys=False), encoding="utf-8"
    )
    return repo, workspace, repo_id


def test_flag_invocation_full_path(tmp_path: Path, capsys):
    repo, workspace, repo_id = _setup_workspace_with_predecessors(tmp_path)
    rc = cli_main([
        str(repo),
        "--build-next",
        "--workspace-root",
        str(workspace),
    ])
    assert rc == 0
    ext_dir = extraction_dir(workspace, repo_id)
    assert (ext_dir / "build-next.yaml").exists()
    assert (ext_dir / "build-next.md").exists()
    out = capsys.readouterr().out
    assert "Build-next recommendation" in out


def test_missing_predecessor_halts_with_exit_2(tmp_path: Path, capsys):
    """No augmented-objectives.yaml + no gap-inventory.yaml → exit 2."""
    repo = tmp_path / "fixture-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    rc = cli_main([
        str(repo),
        "--build-next",
        "--workspace-root",
        str(workspace),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "no prior extraction" in err or "gap-inventory.yaml" in err
    assert "--gaps" in err  # actionable message


def test_missing_gap_inventory_halts(tmp_path: Path, capsys):
    """Augmented-objectives.yaml present but gap-inventory.yaml missing."""
    repo, workspace, repo_id = _setup_workspace_with_predecessors(tmp_path)
    # Remove gap-inventory; keep augmented.
    ext_dir = extraction_dir(workspace, repo_id)
    (ext_dir / "gap-inventory.yaml").unlink()
    rc = cli_main([
        str(repo),
        "--build-next",
        "--workspace-root",
        str(workspace),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "gap-inventory.yaml" in err


def test_idempotent_rerun_does_not_rewrite(tmp_path: Path, capsys):
    repo, workspace, repo_id = _setup_workspace_with_predecessors(tmp_path)
    rc1 = cli_main([str(repo), "--build-next", "--workspace-root", str(workspace)])
    assert rc1 == 0
    capsys.readouterr()
    rc2 = cli_main([str(repo), "--build-next", "--workspace-root", str(workspace)])
    assert rc2 == 0
    out = capsys.readouterr().out
    assert "Wrote:" in out
    assert "False" in out  # skip-write fired


def test_limit_flag_truncates(tmp_path: Path, capsys):
    repo, workspace, repo_id = _setup_workspace_with_predecessors(
        tmp_path, fixture="orphan-only"
    )
    rc = cli_main([
        str(repo),
        "--build-next",
        "--limit", "1",
        "--workspace-root",
        str(workspace),
    ])
    assert rc == 0
    ext_dir = extraction_dir(workspace, repo_id)
    yaml_p = ext_dir / "build-next.yaml"
    raw = yaml.safe_load(yaml_p.read_text(encoding="utf-8"))
    assert len(raw["candidates"]) == 1
    assert raw["truncated_count"] == 2


def test_json_mode_emits_structured_payload(tmp_path: Path, capsys):
    repo, workspace, repo_id = _setup_workspace_with_predecessors(tmp_path)
    rc = cli_main([
        str(repo),
        "--build-next",
        "--json",
        "--workspace-root",
        str(workspace),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    import json
    payload = json.loads(out)
    assert payload["extraction_id"] == repo_id
    assert "build_next_yaml_path" in payload
    assert "build_next_md_path" in payload
    assert "candidate_count" in payload

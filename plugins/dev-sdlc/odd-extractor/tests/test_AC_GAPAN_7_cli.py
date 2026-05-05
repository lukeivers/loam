"""AC.GAPAN.7 — CLI subcommand `loam odd-extract --gaps`.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.7:

- Reads augmented-objectives.yaml + backing-map.yaml + evidence-rows.yaml.
- Invokes analyze_gaps → persists gap-inventory.yaml.
- Emits stdout summary (per-category counts, per-confidence counts,
  top-3 example gap_ids per category).
- Idempotent on re-run.
- Halts with exit code 2 + actionable message on missing predecessor.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    save_augmented_objectives,
    save_backing_map,
)
from loam_odd_extractor.cli import main
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _gapan_helpers import make_aug_set, make_backing_map, make_objective, make_raw_dict


def _setup_workspace(workspace_root: Path, repo_path: Path) -> Path:
    """Build a minimal workspace with all three predecessor artefacts."""
    repo_path.mkdir(parents=True, exist_ok=True)
    repo_id = compute_repo_id(repo_path)
    ext_dir = extraction_dir(workspace_root, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)

    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    aug = make_aug_set([obj], extraction_id=repo_id, audit_path=str(ext_dir / "audit-log"))
    save_augmented_objectives(aug, ext_dir)

    bm = make_backing_map(
        [BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[])],
        extraction_id=repo_id,
    )
    save_backing_map(ext_dir, bm)

    # evidence-rows.yaml — RawACs.model_dump shape.
    evidence_rows = [
        make_raw_dict(path="src/orphan.js", kind="route"),
    ]
    (ext_dir / "evidence-rows.yaml").write_text(
        yaml.safe_dump(
            {
                "extraction_id": repo_id,
                "acs": evidence_rows,
                "unhandled_paths": [],
                "per_slice_costs": {},
                "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return ext_dir


def test_cli_happy_path(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    ext_dir = _setup_workspace(workspace, repo)

    rc = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    assert rc == 0
    captured = capsys.readouterr()
    out = captured.out
    assert "Gap inventory" in out
    assert "Total gaps" in out
    assert "STRONG" in out
    assert "WEAK" in out
    assert "Inventory:" in out
    # File written.
    assert (ext_dir / "gap-inventory.yaml").exists()


def test_cli_missing_extraction_dir_halts(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    rc = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "no prior extraction" in err.lower()


def test_cli_missing_augmented_halts(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True)
    # Don't write augmented-objectives.yaml.

    rc = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "augmented-objectives.yaml" in err.lower() or "interview" in err.lower()


def test_cli_missing_backing_map_halts(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True)
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    save_augmented_objectives(
        make_aug_set([obj], extraction_id=repo_id, audit_path=str(ext_dir / "audit-log")),
        ext_dir,
    )
    rc = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "backing-map.yaml" in err.lower()


def test_cli_missing_evidence_rows_halts(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True)
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    save_augmented_objectives(
        make_aug_set([obj], extraction_id=repo_id, audit_path=str(ext_dir / "audit-log")),
        ext_dir,
    )
    save_backing_map(
        ext_dir,
        make_backing_map(
            [BackingMapEntry(objective_id=obj.objective_id, evidence_rows=[])],
            extraction_id=repo_id,
        ),
    )
    rc = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "evidence-rows.yaml" in err.lower()


def test_cli_idempotent_re_run(tmp_path: Path, capsys) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    ext_dir = _setup_workspace(workspace, repo)

    rc1 = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    capsys.readouterr()
    assert rc1 == 0
    p = ext_dir / "gap-inventory.yaml"
    first_mtime = p.stat().st_mtime_ns

    rc2 = main([str(repo), "--gaps", "--workspace-root", str(workspace)])
    out = capsys.readouterr().out
    assert rc2 == 0
    # Skip-write fired (analyzed_at differs but content-hash matches).
    assert p.stat().st_mtime_ns == first_mtime
    assert "Wrote:      False" in out


def test_cli_json_mode(tmp_path: Path, capsys) -> None:
    import json

    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    _setup_workspace(workspace, repo)

    rc = main([str(repo), "--gaps", "--json", "--workspace-root", str(workspace)])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "gap_inventory_path" in payload
    assert "summary" in payload

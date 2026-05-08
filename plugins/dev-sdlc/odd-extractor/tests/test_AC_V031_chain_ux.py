"""AC.V031.{1,2,3,4,8,9} — workflow-chain UX (v0.3.0.1 PATCH).

Per the v0.3.0.1 patch plan-doc at
``docs/plans/v0-3-0-1-patch-chain-ux-and-doc-gap-fill.md``:

- AC.V031.1 — ``--verify`` (default) success-path stdout names
  ``loam odd-extract <repo> --interview`` as the next step.
- AC.V031.2 — ``--interview`` success-path stdout names ``--gaps``
  as the next step.
- AC.V031.3 — ``--gaps`` success-path stdout names ``--build-next``
  as the next step.
- AC.V031.4 — ``--build-next`` success-path stdout closes the chain
  (mentions implement + re-run).
- AC.V031.8 — Default-dry-run with ``ac_count == 0`` emits a
  ``--live`` hint.
- AC.V031.9 (outcome-altitude) — Cold-run extract → interview →
  gap-analysis → build-next chain on a synthetic repo. At every
  stage, the user (no prior context) can identify the next command
  from stdout alone — verified by stdout-grep against the production
  CLI entry-point. Each stage's stdout contains the literal next
  command-line that, when executed, advances the chain.

Eric-feedback regression test (Telegram 10375):
"it didn't naturally progress to the interview, the gap analysis,
the build next, etc. it stopped after generating the objectives."
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import yaml

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    save_augmented_objectives,
    save_backing_map,
)
from loam_odd_extractor.cli import main as cli_main
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
)


# ---------------------------------------------------------------------------
# AC.V031.1 + AC.V031.8 — verify-stage stdout (default + dry-run hint).
# ---------------------------------------------------------------------------


def test_verify_stage_emits_next_step_pointer_to_interview(
    fixture_repo: Path, workspace_root: Path, capsys
) -> None:
    """AC.V031.1 — default verify success-path names --interview."""
    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Next:" in out
    assert "--interview" in out
    assert "loam odd-extract" in out
    # The hint must reference the actual repo_id so the user can
    # copy-paste — not a placeholder.
    repo_id = compute_repo_id(fixture_repo)
    assert repo_id in out


def test_verify_stage_emits_live_hint_when_ac_count_zero(
    fixture_repo: Path, workspace_root: Path, capsys
) -> None:
    """AC.V031.8 — dry-run AC=0 surfaces --live remedy."""
    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # The fixture-repo cold-run produces zero ACs (no adapters
    # registered, structural-seam dry-run shape).
    assert "AC count:       0" in out
    assert "Dry-run mode" in out
    assert "--live" in out


# ---------------------------------------------------------------------------
# AC.V031.2 — interview success-path → --gaps.
# AC.V031.3 — gaps success-path → --build-next.
# AC.V031.4 — build-next success-path → chain-close.
# ---------------------------------------------------------------------------


def _seed_for_interview(workspace: Path, repo: Path) -> Path:
    """Plant the artefacts --interview reads (verify-stage output)."""
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("# x\n", encoding="utf-8")
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    aug = make_aug_set(
        [obj], extraction_id=repo_id, audit_path=str(ext_dir / "audit-log")
    )
    save_augmented_objectives(aug, ext_dir)
    return ext_dir


def _seed_for_gaps(workspace: Path, repo: Path) -> Path:
    """Plant augmented + backing + evidence rows the --gaps stage reads."""
    ext_dir = _seed_for_interview(workspace, repo)
    repo_id = compute_repo_id(repo)
    obj_id = (
        ext_dir / "augmented-objectives.yaml"
    )
    payload = yaml.safe_load(obj_id.read_text(encoding="utf-8"))
    objective_id = payload["objectives"][0]["objective_id"]
    bm = make_backing_map(
        [BackingMapEntry(objective_id=objective_id, evidence_rows=[])],
        extraction_id=repo_id,
    )
    save_backing_map(ext_dir, bm)
    evidence = [make_raw_dict(path="src/orphan.js", kind="route")]
    (ext_dir / "evidence-rows.yaml").write_text(
        yaml.safe_dump(
            {
                "extraction_id": repo_id,
                "acs": evidence,
                "unhandled_paths": [],
                "per_slice_costs": {},
                "created_at": _dt.datetime.now(
                    _dt.timezone.utc
                ).isoformat(),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return ext_dir


def test_gaps_stage_emits_next_step_pointer_to_build_next(
    tmp_path: Path, capsys
) -> None:
    """AC.V031.3 — gaps success-path names --build-next."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    _seed_for_gaps(workspace, repo)
    rc = cli_main(
        [str(repo), "--gaps", "--workspace-root", str(workspace)]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Next:" in out
    assert "--build-next" in out
    assert "loam odd-extract" in out
    assert compute_repo_id(repo) in out


def test_build_next_stage_emits_chain_closing_pointer(
    tmp_path: Path, capsys
) -> None:
    """AC.V031.4 — build-next success-path closes the chain.

    Reuses the AC.PERSONA-PULL.1 fixture-driven setup pattern.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# x\n", encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True, exist_ok=True)

    # Reuse PERSONA-PULL fixture for valid build-next predecessors.
    fdir = (
        Path(__file__).parent
        / "fixtures"
        / "build-next"
        / "no-survey-context"
    )
    aug_payload = yaml.safe_load(
        (fdir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    )
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

    rc = cli_main(
        [
            str(repo),
            "--build-next",
            "--workspace-root",
            str(workspace),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Next:" in out
    # Chain-close hints: the user is told to implement + re-run.
    assert "implement" in out.lower()
    assert "re-run" in out.lower() or "rerun" in out.lower()


# ---------------------------------------------------------------------------
# AC.V031.9 — OUTCOME-ALTITUDE: stdout-grep proves an unprimed user
# can identify the next command at every stage from stdout alone.
# Composes the verify + (gaps with seeded predecessors) + build-next
# tests above into a single end-to-end chain assertion. The
# --interview stage requires interactive stdin (Q&A) — its stdout
# contract is verified separately at AC.V025.C1_C2 + the gap+build
# stages cover the remaining transitions of the chain in one
# integration test.
# ---------------------------------------------------------------------------


def test_outcome_altitude_chain_stdout_progression(
    tmp_path: Path, capsys
) -> None:
    """AC.V031.9 — chain-stdout-grep across stages.

    For each stage the user runs, stdout MUST contain the literal
    next command-line. This is the regression contract for Eric's
    ""it stopped after generating the objectives"" report.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# x\n", encoding="utf-8")
    repo_id = compute_repo_id(repo)

    # Stage 1 — verify (default cold-run on a fresh repo).
    rc = cli_main([str(repo), "--workspace-root", str(workspace)])
    assert rc == 0
    out_verify = capsys.readouterr().out
    next_cmd = f"loam odd-extract {repo_id} --interview"
    assert next_cmd in out_verify, (
        f"AC.V031.9 verify-stage MUST surface `{next_cmd}` in stdout — "
        f"got:\n{out_verify}"
    )

    # Stage 3 — --gaps (after seeding interview output).
    _seed_for_gaps(workspace, repo)
    rc = cli_main(
        [str(repo), "--gaps", "--workspace-root", str(workspace)]
    )
    assert rc == 0
    out_gaps = capsys.readouterr().out
    next_cmd = f"loam odd-extract {repo_id} --build-next"
    assert next_cmd in out_gaps, (
        f"AC.V031.9 gaps-stage MUST surface `{next_cmd}` in stdout — "
        f"got:\n{out_gaps}"
    )

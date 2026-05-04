"""D2 idempotency variant — repeated runs produce stable artefacts.

Per plan-doc §6 D2: the extractor is one-shot (D2 daemon-style
n/a structurally); the master plan dispatch's "5+ init/analyze runs
idempotent" wording is satisfied here. Five repeated runs against
the same fixture with fixed timestamps produce byte-identical
content artefacts (config.yaml / plan.yaml / raw-acs.yaml /
contract-draft.md / contract-draft.yaml).

Audit-log entries grow on each run (each run writes a fresh set of
6 entries — start + 4 stages + end); we don't assert audit-log
byte-identity since growth is intended.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor import (
    analyze_repo,
    default_budget,
    generate_raw_acs,
    init_extraction,
    verify_contract,
)


FIXED_TS = "2026-05-04T12:00:00+00:00"


def _run_once(repo: Path, ws: Path) -> dict[str, str]:
    """Run all four stages with FIXED_TS; return artefact contents."""
    config = init_extraction(
        repo_path=repo,
        workspace_root=ws,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    plan = analyze_repo(config=config, timestamp=FIXED_TS)
    raw = generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)
    draft = verify_contract(config=config, raw=raw, timestamp=FIXED_TS)
    ext_dir = (
        ws.resolve() / ".loam" / "extractions" / config.repo_id
    )
    return {
        "config.yaml": (ext_dir / "config.yaml").read_text(encoding="utf-8"),
        "plan.yaml": (ext_dir / "plan.yaml").read_text(encoding="utf-8"),
        "raw-acs.yaml": (ext_dir / "raw-acs.yaml").read_text(encoding="utf-8"),
        "contract-draft.md": (ext_dir / "contract-draft.md").read_text(
            encoding="utf-8"
        ),
        "contract-draft.yaml": (ext_dir / "contract-draft.yaml").read_text(
            encoding="utf-8"
        ),
    }


def test_five_repeated_runs_produce_byte_identical_artefacts(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """5+ runs idempotent at the artefact-content level."""
    runs = [_run_once(fixture_repo, workspace_root) for _ in range(5)]
    baseline = runs[0]
    for run_idx, run in enumerate(runs[1:], start=2):
        for fname, content in run.items():
            assert content == baseline[fname], (
                f"run {run_idx}: {fname} drifted from baseline. "
                f"This is a non-determinism bug in stage {fname}."
            )


def test_repeated_runs_walk_produces_stable_path_order(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """The walk in analyze.py sorts paths lexicographically;
    repeated runs see the same order."""
    runs = [_run_once(fixture_repo, workspace_root) for _ in range(3)]
    plan_a = runs[0]["plan.yaml"]
    plan_b = runs[1]["plan.yaml"]
    plan_c = runs[2]["plan.yaml"]
    assert plan_a == plan_b == plan_c

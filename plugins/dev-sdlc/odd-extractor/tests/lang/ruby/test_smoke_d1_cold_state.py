"""Smoke D1 — cold-state (fresh canonical workspace + synthetic
fixture).

Per AC.RAILS smoke + plan-doc §6 D1:

- Tmp workspace + synthetic fixture as target repo.
- Run ``loam odd-extract <fixture> --live --budget-cents 5000`` end
  to end.
- All four stage artefacts land at expected paths.
- Contract draft is well-formed markdown with band-tagged AC table.
- ≥1 VERIFIED, ≥3 PLAUSIBLE, ≥1 HYPOTHESISED AC.
- ``RawACs.acs`` round-trips through ``BandedAC.model_validate()``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.bands import BandedAC, ConfidenceBand
from loam_odd_extractor.budget import default_budget, budget_from_cents
from loam_odd_extractor.generate import generate_raw_acs
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.state import (
    compute_repo_id,
    extraction_dir,
    load_state,
)
from loam_odd_extractor.verify import verify_contract


def test_d1_cold_state_full_workflow(
    synthetic_rails_repo: Path, tmp_path: Path,
) -> None:
    """End-to-end four-stage workflow against the synthetic fixture."""
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
    draft = verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(synthetic_rails_repo)
    ext_dir = extraction_dir(workspace, repo_id)

    # All four stage artefacts present.
    assert (ext_dir / "config.yaml").exists()
    assert (ext_dir / "plan.yaml").exists()
    assert (ext_dir / "raw-acs.yaml").exists()
    assert (ext_dir / "contract-draft.md").exists()
    assert (ext_dir / "contract-draft.yaml").exists()

    # state.yaml shows all four stages complete.
    state = load_state(ext_dir)
    assert state is not None
    assert state.all_stages_complete

    # RawACs has populated content.
    raw_payload = yaml.safe_load(
        (ext_dir / "raw-acs.yaml").read_text(encoding="utf-8")
    )
    assert raw_payload["acs"]
    assert len(raw_payload["acs"]) >= 10

    # Every AC round-trips through BandedAC.
    for ac in raw_payload["acs"]:
        BandedAC.model_validate(ac)

    # Band distribution per AC.RAILS.5.
    from collections import Counter
    bands = Counter(ac["confidence"] for ac in raw_payload["acs"])
    assert bands[ConfidenceBand.VERIFIED.value] >= 1
    assert bands[ConfidenceBand.PLAUSIBLE.value] >= 3
    assert bands[ConfidenceBand.HYPOTHESISED.value] >= 1

    # Contract draft is well-formed markdown with anchors.
    md = (ext_dir / "contract-draft.md").read_text(encoding="utf-8")
    assert "<!-- ACS_TABLE_HERE -->" in md
    assert "| AC | Band | Evidence kind | Citations |" in md
    assert "VERIFIED" in md
    assert "PLAUSIBLE" in md
    assert "HYPOTHESISED" in md


def test_d1_dry_run_produces_estimate_only(
    synthetic_rails_repo: Path, tmp_path: Path,
) -> None:
    """Dry-run mode emits an estimate; live extraction does not run."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    config = init_extraction(
        repo_path=synthetic_rails_repo,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=True,
    )
    plan = analyze_repo(config=config)
    raw = generate_raw_acs(config=config, plan=plan)

    # In dry-run mode, generate stage short-circuits to empty acs
    # per Cycle 1 AC.OREK.5 + Decision D.
    repo_id = compute_repo_id(synthetic_rails_repo)
    ext_dir = extraction_dir(workspace, repo_id)
    raw_payload = yaml.safe_load(
        (ext_dir / "raw-acs.yaml").read_text(encoding="utf-8")
    )
    # Dry-run produces 0 ACs (live extraction skipped).
    assert raw_payload["acs"] == []

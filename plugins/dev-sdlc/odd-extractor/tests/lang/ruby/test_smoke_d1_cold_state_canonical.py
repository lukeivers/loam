"""Smoke D1 — cold-state against the canonical ruby-rails-payment
fixture (v0.1.8 Cycle 4b).

Mirror of ``test_smoke_d1_cold_state.py`` (Cycle 3, synthetic-rails-
bound) bound to the canonical fixture instead. The canonical
fixture is shape-richer; the band-distribution floor is tighter
(AC.FIXTURES.3 floor: ≥3 VERIFIED + ≥5 PLAUSIBLE + ≥2 HYPOTHESISED).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.bands import BandedAC, ConfidenceBand
from loam_odd_extractor.budget import budget_from_cents
from loam_odd_extractor.generate import generate_raw_acs
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.state import (
    compute_repo_id,
    extraction_dir,
    load_state,
)
from loam_odd_extractor.verify import verify_contract


def test_d1_cold_state_full_workflow_canonical(
    canonical_ruby_rails_payment_repo: Path, tmp_path: Path,
) -> None:
    """End-to-end four-stage workflow against the canonical fixture."""
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
    draft = verify_contract(config=config, raw=raw)

    repo_id = compute_repo_id(canonical_ruby_rails_payment_repo)
    ext_dir = extraction_dir(workspace, repo_id)

    # All four stage artefacts present.
    assert (ext_dir / "config.yaml").exists()
    assert (ext_dir / "plan.yaml").exists()
    assert (ext_dir / "raw-acs.yaml").exists()
    assert (ext_dir / "contract-draft.md").exists()
    assert (ext_dir / "contract-draft.yaml").exists()

    state = load_state(ext_dir)
    assert state is not None
    assert state.all_stages_complete

    raw_payload = yaml.safe_load(
        (ext_dir / "raw-acs.yaml").read_text(encoding="utf-8")
    )
    assert raw_payload["acs"]
    # Canonical fixture is shape-richer; AC.FIXTURES.2 implies ≥10
    # ACs comfortably.
    assert len(raw_payload["acs"]) >= 20

    for ac in raw_payload["acs"]:
        BandedAC.model_validate(ac)

    # AC.FIXTURES.3 floor — TIGHTER than Cycle 3's smoke.
    bands = Counter(ac["confidence"] for ac in raw_payload["acs"])
    assert bands[ConfidenceBand.VERIFIED.value] >= 3, (
        f"VERIFIED count {bands[ConfidenceBand.VERIFIED.value]} < 3"
    )
    assert bands[ConfidenceBand.PLAUSIBLE.value] >= 5, (
        f"PLAUSIBLE count {bands[ConfidenceBand.PLAUSIBLE.value]} < 5"
    )
    assert bands[ConfidenceBand.HYPOTHESISED.value] >= 2, (
        f"HYPOTHESISED count {bands[ConfidenceBand.HYPOTHESISED.value]} < 2"
    )

    md = (ext_dir / "contract-draft.md").read_text(encoding="utf-8")
    assert "<!-- ACS_TABLE_HERE -->" in md
    assert "| AC | Band | Evidence kind | Citations |" in md
    assert "VERIFIED" in md
    assert "PLAUSIBLE" in md
    assert "HYPOTHESISED" in md

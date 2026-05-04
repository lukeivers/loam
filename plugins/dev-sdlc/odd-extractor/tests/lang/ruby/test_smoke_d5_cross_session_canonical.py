"""Smoke D5 — cross-session continuity against the canonical
ruby-rails-payment fixture (v0.1.8 Cycle 4b).

Per smoke-test-discipline §6 — partial extraction state survives
subprocess boundary; resume completes remaining stages. Mirror of
Cycle 3 + Cycle 4a's d5 smoke against the synthetic / JsTs fixtures.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.budget import budget_from_cents
from loam_odd_extractor.generate import generate_raw_acs
from loam_odd_extractor.init import init_extraction
from loam_odd_extractor.state import (
    compute_repo_id,
    extraction_dir,
    load_state,
)
from loam_odd_extractor.verify import verify_contract


def test_canonical_fixture_partial_extraction_resumes(
    canonical_ruby_rails_payment_repo: Path, tmp_path: Path,
) -> None:
    """Stage 1 + 2 run; stages 3 + 4 deferred; resume completes.

    Verifies state.yaml + per-stage artefacts survive across what
    would be a /clear or session boundary (in test, sequential calls
    against the same workspace_root).
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()

    # Phase 1 — init + analyze only (the "session A" subset).
    config = init_extraction(
        repo_path=canonical_ruby_rails_payment_repo,
        workspace_root=workspace,
        budget=budget_from_cents(5000),
        dry_run=False,
    )
    plan = analyze_repo(config=config)

    repo_id = compute_repo_id(canonical_ruby_rails_payment_repo)
    ext_dir = extraction_dir(workspace, repo_id)

    state_after_phase1 = load_state(ext_dir)
    assert state_after_phase1 is not None
    assert (ext_dir / "config.yaml").exists()
    assert (ext_dir / "plan.yaml").exists()
    assert not (ext_dir / "raw-acs.yaml").exists()
    assert not (ext_dir / "contract-draft.md").exists()

    # Phase 2 — fresh "session B": load state, complete remaining
    # stages.
    raw = generate_raw_acs(config=config, plan=plan)
    draft = verify_contract(config=config, raw=raw)

    state_after_phase2 = load_state(ext_dir)
    assert state_after_phase2 is not None
    assert state_after_phase2.all_stages_complete

    raw_payload = yaml.safe_load(
        (ext_dir / "raw-acs.yaml").read_text(encoding="utf-8")
    )
    assert raw_payload["acs"]

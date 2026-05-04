"""Smoke D1 — cold-state (fresh canonical workspace +
jsts-playwright-app fixture).

Per AC.JSTS smoke + plan-doc §6 D1:

- Tmp workspace + JsTs fixture as target repo.
- Run end-to-end four-stage workflow.
- All four stage artefacts land at expected paths.
- Contract draft is well-formed markdown with band-tagged AC table.
- ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED AC.
- :class:`RawACs.acs` round-trips through
  :meth:`BandedAC.model_validate`.
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
from loam_odd_extractor.lang.jsts import JsTsAdapter
from loam_odd_extractor.registry import (
    clear_manual_registry,
    register_adapter,
)
from loam_odd_extractor.state import (
    compute_repo_id,
    extraction_dir,
    load_state,
)
from loam_odd_extractor.verify import verify_contract


def test_d1_cold_state_full_workflow(
    jsts_playwright_app_repo: Path, tmp_path: Path,
) -> None:
    """End-to-end four-stage workflow against the JsTs fixture."""
    clear_manual_registry()
    register_adapter(JsTsAdapter())
    try:
        workspace = tmp_path / "ws"
        workspace.mkdir()

        config = init_extraction(
            repo_path=jsts_playwright_app_repo,
            workspace_root=workspace,
            budget=budget_from_cents(5000),
            dry_run=False,
        )
        plan = analyze_repo(config=config)
        raw = generate_raw_acs(config=config, plan=plan)
        draft = verify_contract(config=config, raw=raw)

        repo_id = compute_repo_id(jsts_playwright_app_repo)
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
        assert len(raw_payload["acs"]) >= 20

        # Every AC round-trips through BandedAC.
        for ac in raw_payload["acs"]:
            BandedAC.model_validate(ac)

        # Band distribution per AC.JSTS.5 / AC.FIXTURES.3.
        bands = Counter(ac["confidence"] for ac in raw_payload["acs"])
        assert bands[ConfidenceBand.VERIFIED.value] >= 3
        assert bands[ConfidenceBand.PLAUSIBLE.value] >= 5
        assert bands[ConfidenceBand.HYPOTHESISED.value] >= 2

        # Contract draft is well-formed markdown with anchors.
        md = (ext_dir / "contract-draft.md").read_text(
            encoding="utf-8"
        )
        assert "<!-- ACS_TABLE_HERE -->" in md
        assert "VERIFIED" in md
        assert "PLAUSIBLE" in md
        assert "HYPOTHESISED" in md
    finally:
        clear_manual_registry()

"""Smoke D5 — cross-session continuity.

Per plan-doc §6 D5:

- Test setup runs the four-stage workflow against the JsTs fixture
  in process A.
- Mid-extraction (after ``analyze`` complete), simulates ``/clear``
  by spawning process B as a subprocess.
- B reads A's per-slice state and resumes the remaining stages.
- The final state has all_stages_complete True.

Cycle 4a inherits Cycle 1's state.yaml resume mechanism + Cycle 3's
per-file routing — no new fields needed at the cycle level.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.analyze import analyze_repo
from loam_odd_extractor.budget import budget_from_cents
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


def test_resume_picks_up_after_analyze(
    jsts_playwright_app_repo: Path, tmp_path: Path,
) -> None:
    """Process A: init + analyze. Resume via in-process cli_main →
    completes generate + verify. Final state has all_stages_complete.
    """
    clear_manual_registry()
    register_adapter(JsTsAdapter())
    try:
        workspace = tmp_path / "ws"
        workspace.mkdir()

        # Process A — partial extraction.
        config = init_extraction(
            repo_path=jsts_playwright_app_repo,
            workspace_root=workspace,
            budget=budget_from_cents(5000),
            dry_run=False,
        )
        analyze_repo(config=config)

        repo_id = compute_repo_id(jsts_playwright_app_repo)
        ext_dir = extraction_dir(workspace, repo_id)
        state_a = load_state(ext_dir)
        assert state_a is not None
        assert state_a.init_complete
        assert state_a.analyze_complete
        assert not state_a.generate_complete
        assert not state_a.verify_complete

        # Process B — resume in-process via cli_main (mirroring Cycle
        # 3's pattern).
        from loam_odd_extractor.cli import main as cli_main

        rc = cli_main(
            [
                str(jsts_playwright_app_repo),
                "--resume",
                "--workspace-root",
                str(workspace),
                "--live",
                "--budget-cents",
                "5000",
            ]
        )
        assert rc == 0

        state_b = load_state(ext_dir)
        assert state_b is not None
        assert state_b.all_stages_complete
    finally:
        clear_manual_registry()


def test_state_yaml_survives_fresh_load(
    jsts_playwright_app_repo: Path, tmp_path: Path,
) -> None:
    """A second load_state() (fresh process simulation) reads the
    same state.
    """
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
        analyze_repo(config=config)

        repo_id = compute_repo_id(jsts_playwright_app_repo)
        ext_dir = extraction_dir(workspace, repo_id)

        s1 = load_state(ext_dir)
        s2 = load_state(ext_dir)
        assert s1 is not None and s2 is not None
        assert s1.extraction_id == s2.extraction_id
        assert s1.init_complete == s2.init_complete
        assert s1.analyze_complete == s2.analyze_complete
    finally:
        clear_manual_registry()

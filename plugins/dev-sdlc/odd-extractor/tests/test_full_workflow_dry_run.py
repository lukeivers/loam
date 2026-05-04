"""D1 — cold-state functional smoke.

Per smoke-test-discipline §2.1 + plan-doc §6 D1: from a fresh
workspace, a single representative invocation produces the expected
output and side-effects.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.cli import main as cli_main


def test_full_workflow_dry_run_against_fixture(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """End-to-end init → analyze → generate → verify."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0

    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )

    # All four stage artefacts present.
    for fname in (
        "config.yaml",
        "plan.yaml",
        "raw-acs.yaml",
        "contract-draft.md",
        "contract-draft.yaml",
        "state.yaml",
    ):
        assert (repo_id_dir / fname).exists(), f"missing {fname}"

    # contract-draft.md parses (well-formed markdown shape).
    md_text = (repo_id_dir / "contract-draft.md").read_text(
        encoding="utf-8"
    )
    assert md_text.startswith("# Contract draft —")
    assert "## Acceptance criteria" in md_text
    assert "## Unhandled paths" in md_text

    # Sidecar parses as YAML.
    sidecar = yaml.safe_load(
        (repo_id_dir / "contract-draft.yaml").read_text(encoding="utf-8")
    )
    assert sidecar["schema_version"] == 1
    assert sidecar["ac_count"] == 0
    assert sidecar["unhandled_count"] >= 1

    # State.yaml records all four stages complete.
    state = yaml.safe_load(
        (repo_id_dir / "state.yaml").read_text(encoding="utf-8")
    )
    assert state["init_complete"] is True
    assert state["analyze_complete"] is True
    assert state["generate_complete"] is True
    assert state["verify_complete"] is True


def test_unhandled_paths_section_lists_fixture_files(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Cycle 1: every fixture path is unhandled (zero adapters)."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    md_text = (repo_id_dir / "contract-draft.md").read_text(
        encoding="utf-8"
    )
    # Fixture files: README.md, main.py, src/lib.py.
    assert "README.md" in md_text
    assert "main.py" in md_text
    assert "lib.py" in md_text
    # .git and __pycache__ should NOT appear (skipped by the walker).
    assert ".git/HEAD" not in md_text
    assert "__pycache__" not in md_text

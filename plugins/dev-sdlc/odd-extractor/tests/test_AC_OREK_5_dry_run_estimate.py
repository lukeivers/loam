"""AC.OREK.5 — Dry-run cost estimate via cost-governance primitive.

- estimate_for_extraction(scope_id, recent_actuals) wraps
  loam.cost_governance.dry_run_estimate.
- Cold-start (no actuals) returns LOW band + non-empty reason.
- CLI surfaces the estimate before any extraction work.
- Dry-run mode (default) outputs only the estimate + scaffold
  artefacts; no LLM calls.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from loam.cost_governance import ConfidenceBand

from loam_odd_extractor import estimate_for_extraction
from loam_odd_extractor.cli import main as cli_main


def test_estimate_for_extraction_cold_start_returns_low_band() -> None:
    estimate = estimate_for_extraction(
        scope_id="test:cold-start", recent_actuals=[]
    )
    assert estimate.confidence_band == ConfidenceBand.LOW
    assert estimate.estimated_money_cents == 0
    assert estimate.estimated_tokens == 0
    assert estimate.estimated_time_seconds == 0
    assert estimate.reason is not None
    assert "cold-start" in estimate.reason


def test_estimate_for_extraction_with_actuals_returns_higher_band() -> None:
    actuals = [
        {"money_cents": 100, "tokens": 1000, "time_seconds": 5}
        for _ in range(5)
    ]
    estimate = estimate_for_extraction(
        scope_id="test:with-actuals", recent_actuals=actuals
    )
    assert estimate.confidence_band == ConfidenceBand.HIGH
    assert estimate.estimated_money_cents == 100
    assert estimate.estimated_tokens == 1000


def test_cli_surfaces_estimate_block_in_stdout(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """`loam odd-extract <repo>` outputs an Estimate block first."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(
            [str(fixture_repo), "--workspace-root", str(workspace_root)]
        )
    assert rc == 0
    out = buf.getvalue()
    assert "Estimate" in out
    assert "estimated_money_cents" in out
    assert "confidence_band" in out


def test_cli_surfaces_estimate_in_json_mode(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """`--json` surfaces the estimate in JSON shape."""
    import json

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(
            [
                str(fixture_repo),
                "--workspace-root",
                str(workspace_root),
                "--json",
            ]
        )
    assert rc == 0
    # The JSON estimate block is one of several stdout writes; pull
    # the first complete JSON object.
    out = buf.getvalue()
    # Find first '{' / matching '}'.
    start = out.index("{")
    depth = 0
    end = start
    for i, c in enumerate(out[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    payload = json.loads(out[start:end])
    assert "estimate" in payload
    e = payload["estimate"]
    assert "estimated_money_cents" in e
    assert "estimated_tokens" in e
    assert "estimated_time_seconds" in e
    assert "confidence_band" in e


def test_dry_run_default_no_extraction_work_runs(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Default invocation runs scaffold without any LLM/adapter
    extraction (Cycle 1 has zero adapters; this verifies the
    short-circuit in generate_raw_acs)."""
    rc = cli_main(
        [str(fixture_repo), "--workspace-root", str(workspace_root)]
    )
    assert rc == 0
    # raw-acs.yaml has acs=[]; no adapter was called (none exist).
    import yaml

    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    raw = yaml.safe_load(
        (repo_id_dir / "raw-acs.yaml").read_text(encoding="utf-8")
    )
    assert raw["acs"] == []

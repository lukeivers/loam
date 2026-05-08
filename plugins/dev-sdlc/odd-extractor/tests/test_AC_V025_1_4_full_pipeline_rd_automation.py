"""AC.V025-1.4 — Outcome-altitude full pipeline GREEN against rd-automation.

**outcome-altitude: true** (per ``docs/odd-llm-grounding.lean.md``
§"Outcome-altitude AC requirement" + ``plugins/dev-sdlc/skills/
odd-test-altitude-discipline/SKILL.md``).

Per v0.2.5.1 corrective: the canonical jsts-playwright-app fixture is
synthetic. Eric's actual install of v0.2.5 against rd-automation
(real-world Playwright app with html-captures/ + screenshots/ +
public/uploads/ + customer CSV data) excavated F-LEAK + F-TIMEOUT +
F-VERIFY-ORPHAN. This test runs the production CLI surface against
the local stale copy of rd-automation at
``/Users/lukeivers/pos3/workspace/rd-automation`` and asserts:

1. All four stages (extract --live → --interview → --gaps → --build-next)
   exit 0.
2. Four artefacts produced + non-empty: objectives.yaml,
   augmented-objectives.yaml, gap-inventory.yaml, build-next.yaml.
3. gap-inventory.yaml parses to ≥1 gap entry.
4. build-next.yaml parses to ≥1 ranked candidate.
5. F-LEAK regression: no ``html-captures/``- or ``screenshots/``-
   prefixed paths appear in plan.yaml or evidence-rows.yaml.
6. F-VERIFY-ORPHAN regression: stage 1 (which runs verify internally)
   exited 0 — no orphan-capability halt occurred.

Skips cleanly if:

- ``claude`` binary not in PATH.
- ``loam`` binary not in PATH.
- ``/Users/lukeivers/pos3/workspace/rd-automation`` absent or empty.

Mirrors the AC.V025-C6.1 outcome-altitude pattern but against the
real-world fixture.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


_RD_AUTOMATION_PATH = Path("/Users/lukeivers/pos3/workspace/rd-automation")


def _author_stub_pm(workspace: Path, pm_handle: str) -> None:
    """Author a minimum-valid PM at
    ``<workspace>/workspace/.loam/pms/<handle>/contract.yaml``.

    Mirrors the AC.V025-C6.1 pattern.
    """
    pm_dir = workspace / "workspace" / ".loam" / "pms" / pm_handle
    pm_dir.mkdir(parents=True)
    contract = {
        "schema_version": 1,
        "handle": pm_handle,
        "project_name": "rd-automation-smoke",
        "project_kind": "general",
        "owner_name": "Smoke Operator",
        "workspace_root": str(workspace),
        "decision_surfacing_policy": {
            "onboarding_mode": False,
            "max_questions_per_turn": 1,
            "cool_down_seconds": 0,
            "require_owner_response": False,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))


def _run_loam(
    args: list[str],
    *,
    stdin: str | None = None,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    """Run ``loam <args>`` via subprocess; return (rc, stdout, stderr)."""
    proc = subprocess.run(
        ["loam", *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_AC_V025_1_4_full_pipeline_rd_automation(tmp_path: Path) -> None:
    """End-to-end OUTCOME-altitude probe against rd-automation real-world.

    Skips on missing claude / loam / rd-automation. Runs all four
    stages + asserts F-LEAK + F-VERIFY-ORPHAN regressions are absent.
    """
    if shutil.which("claude") is None:
        pytest.skip(
            "outcome-altitude AC.V025-1.4 requires the `claude` CLI on "
            "PATH (subscription-routed auth via `claude -p`)."
        )
    if shutil.which("loam") is None:
        pytest.skip(
            "outcome-altitude AC.V025-1.4 requires the `loam` CLI on "
            "PATH (workstation-installed via install-from-source.txt)."
        )
    if not _RD_AUTOMATION_PATH.exists():
        pytest.skip(
            f"outcome-altitude AC.V025-1.4 requires rd-automation at "
            f"{_RD_AUTOMATION_PATH}. Skipping when absent so this test "
            f"runs cleanly in any build environment."
        )
    # Sanity-check: rd-automation must be non-empty.
    if not any(_RD_AUTOMATION_PATH.iterdir()):
        pytest.skip(
            f"rd-automation path {_RD_AUTOMATION_PATH} is empty"
        )

    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()
    pm_handle = "smoke-pm"
    _author_stub_pm(workspace, pm_handle)

    # ---- Stage 1 — extraction (real claude -p) ---------------------
    rc1, out1, err1 = _run_loam(
        [
            "odd-extract",
            str(_RD_AUTOMATION_PATH),
            "--live",
            "--budget-cents",
            "500",
            "--budget-override",
            "--workspace-root",
            str(workspace),
            "--synthesis-timeout",
            "1200",
        ],
    )
    assert rc1 == 0, (
        f"Stage 1 (extraction) must exit 0; got rc={rc1}.\n"
        f"stdout: {out1[-2000:]}\n"
        f"stderr: {err1[-2000:]}"
    )
    # F-VERIFY-ORPHAN regression: stage 1 runs verify internally; if it
    # exited 0 we had no orphan-capability halt.

    # Locate the extraction directory.
    ext_root = workspace / ".loam" / "extractions"
    ext_dirs = [p for p in ext_root.iterdir() if p.is_dir()]
    assert len(ext_dirs) == 1, (
        f"Stage 1 should leave exactly 1 extraction-dir; got "
        f"{len(ext_dirs)}: {ext_dirs!r}"
    )
    ext_dir = ext_dirs[0]
    objectives_path = ext_dir / "objectives.yaml"
    assert objectives_path.exists(), (
        f"Stage 1 must produce objectives.yaml at {objectives_path}"
    )
    assert objectives_path.stat().st_size > 0, (
        "Stage 1 objectives.yaml must be non-empty"
    )

    # F-LEAK regression assertion: walk plan.yaml + evidence-rows.yaml
    # and assert NO file path beginning with html-captures/ or
    # screenshots/ appears.
    plan_path = ext_dir / "plan.yaml"
    if plan_path.exists():
        plan_text = plan_path.read_text(encoding="utf-8")
        assert "html-captures/" not in plan_text, (
            "F-LEAK regression: plan.yaml contains html-captures/ "
            "filenames; analyze step must skip off-limits dirs."
        )
        assert "screenshots/" not in plan_text, (
            "F-LEAK regression: plan.yaml contains screenshots/ "
            "filenames; analyze step must skip off-limits dirs."
        )
    evidence_path = ext_dir / "evidence-rows.yaml"
    if evidence_path.exists():
        evidence_text = evidence_path.read_text(encoding="utf-8")
        assert "html-captures/" not in evidence_text, (
            "F-LEAK regression: evidence-rows.yaml contains "
            "html-captures/ filenames."
        )
        assert "screenshots/" not in evidence_text, (
            "F-LEAK regression: evidence-rows.yaml contains "
            "screenshots/ filenames."
        )

    # ---- Stage 2 — interview (no claude -p) ------------------------
    stdin_pipe = ("1\n" * 30) + "no\n"
    rc2, out2, err2 = _run_loam(
        [
            "odd-extract",
            str(_RD_AUTOMATION_PATH),
            "--interview",
            "--workspace-root",
            str(workspace),
            "--pm-name",
            pm_handle,
        ],
        stdin=stdin_pipe,
    )
    assert rc2 == 0, (
        f"Stage 2 (--interview) must exit 0; got rc={rc2}.\n"
        f"stderr: {err2[-2000:]}"
    )
    augmented_path = ext_dir / "augmented-objectives.yaml"
    assert augmented_path.exists(), (
        f"Stage 2 must produce augmented-objectives.yaml"
    )
    assert augmented_path.stat().st_size > 0

    # ---- Stage 3 — gaps -------------------------------------------
    rc3, out3, err3 = _run_loam(
        [
            "odd-extract",
            str(_RD_AUTOMATION_PATH),
            "--gaps",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc3 == 0, (
        f"Stage 3 (--gaps) must exit 0; got rc={rc3}.\n"
        f"stderr: {err3[-2000:]}"
    )
    gap_inventory_path = ext_dir / "gap-inventory.yaml"
    assert gap_inventory_path.exists()
    gap_data = yaml.safe_load(
        gap_inventory_path.read_text(encoding="utf-8")
    )
    # Per the GapInventory pydantic model serialisation shape:
    # the file carries a top-level ``gaps:`` list (each entry tagged
    # with ``category``), plus a ``summary:`` block. Verify the file
    # is well-formed and produced ≥1 gap entry on rd-automation
    # (real-world fixture; rd-automation has known PLAUSIBLE objectives
    # without STRONG backing — the production code identifies them).
    assert isinstance(gap_data, dict), (
        f"gap-inventory.yaml must parse to a dict; got {type(gap_data)}"
    )
    gaps_list = gap_data.get("gaps") or []
    assert isinstance(gaps_list, list), (
        f"gap-inventory.yaml ``gaps`` field must be a list; got "
        f"{type(gaps_list)}"
    )
    assert len(gaps_list) >= 1, (
        f"gap-inventory.yaml must list ≥1 gap entry on rd-automation; "
        f"got len(gaps)={len(gaps_list)}; gap_data={gap_data!r}"
    )

    # ---- Stage 4 — build-next -------------------------------------
    rc4, out4, err4 = _run_loam(
        [
            "odd-extract",
            str(_RD_AUTOMATION_PATH),
            "--build-next",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc4 == 0, (
        f"Stage 4 (--build-next) must exit 0; got rc={rc4}.\n"
        f"stderr: {err4[-2000:]}"
    )
    build_next_path = ext_dir / "build-next.yaml"
    assert build_next_path.exists()
    bn_data = yaml.safe_load(
        build_next_path.read_text(encoding="utf-8")
    )
    if isinstance(bn_data, dict):
        candidates = bn_data.get("candidates") or []
    else:
        candidates = bn_data or []
    assert len(candidates) >= 1, (
        f"build-next.yaml must rank ≥1 candidate; got "
        f"{len(candidates)}"
    )

"""AC.V025-C6.1 — Outcome-altitude smoke fixture authors PM and exercises
the full 4-stage CLI pipeline end-to-end.

**outcome-altitude: true** (per ``docs/odd-llm-grounding.lean.md`` §"Outcome-altitude AC requirement"
+ ``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``).

Per v0.2.5 corrective C6 (HARD-smoke F-DESIGN-1): the dispatcher's manual
HARD smoke against rd-automation failed stages 2/3/4 because no PM was
authored under ``<workspace>/workspace/.loam/pms/``. The dependency chain
forces clean-exit-2 through stages 2/3/4 in the no-PM state. The
operationally-correct fix (per the dispatch brief) is the smoke fixture:
author a stub PM BEFORE running the pipeline.

This test is the durable mechanization of that fixture. It:

  1. Copies the canonical ``jsts-playwright-app`` fixture into a tmp dir
     and ``git init``s it.
  2. Authors a stub PM at
     ``<workspace>/workspace/.loam/pms/smoke-pm/contract.yaml`` —
     mirrors the per-project-pm conftest pattern at
     ``framework/per-project-pm/tests/conftest.py``.
  3. Runs Stage 1 — ``loam odd-extract <repo> --live --workspace-root <ws>``
     — via subprocess (real ``claude -p`` call; skips on missing binary).
  4. Runs Stage 2 — ``loam odd-extract <repo> --interview --workspace-root <ws>``
     — via subprocess with stdin pipe of confirm-1 responses + ``no`` for
     free-form-add. (No claude -p call in --interview; PM batching is
     local heuristic.)
  5. Runs Stage 3 — ``loam odd-extract <repo> --gaps --workspace-root <ws>``
     — via subprocess.
  6. Runs Stage 4 — ``loam odd-extract <repo> --build-next --workspace-root <ws>``
     — via subprocess.
  7. Asserts all four stages exit 0.
  8. Asserts the four stage-output artefacts exist:
     ``objectives.yaml`` + ``augmented-objectives.yaml`` + ``gap-inventory.yaml``
     + ``build-next.yaml``.

This is OUTCOME-class per the SKILL's classifier:

  - Production entry-point invoked? YES — ``loam odd-extract ...`` via
    subprocess.run.
  - No state pre-arranged that production would produce? YES — only
    fixture files + workspace + PM contract.yaml are pre-arranged. PM
    contract.yaml is NOT something the production code under test
    produces; it is user-authored prerequisite state.
  - Asserts on production-produced artefacts? YES — objectives.yaml,
    augmented-objectives.yaml, gap-inventory.yaml,
    build-next.yaml.
  - No SDK / client / subprocess mocking? YES — no monkeypatch of the
    synthesis client / subprocess.run / claude binary. Stdin is piped
    via subprocess (real I/O channel).

**Stochasticity tolerance:** stage 1 invokes the live LLM via ``claude -p``;
stochastic. Per dispatch brief, the operator re-runs 3x; ≥2 of 3 must pass.
The test itself is single-invocation; the operator re-runs to verify
stochastic stability.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "jsts-playwright-app"


def _setup_jsts_repo(tmp_path: Path) -> Path:
    """Copy canonical jsts-playwright-app fixture + git-init.

    Mirrors ``test_AC_V025_C4_3_*._setup_jsts_repo``.
    """
    repo = tmp_path / "jsts-app"
    shutil.copytree(_FIXTURE_PATH, repo)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@e.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "T"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "commit",
            "-q",
            "-m",
            "initial fixture",
        ],
        check=True,
    )
    return repo


def _author_stub_pm(workspace: Path, pm_handle: str) -> None:
    """Author a minimum-valid PM at
    ``<workspace>/workspace/.loam/pms/<handle>/contract.yaml``.

    Mirrors the existing test pattern across 5+ test files
    (``framework/per-project-pm/tests/conftest.py`` + ``test_ratification_*.py``
    + ``test_QSURF_*``). PM contract authoring is user-prerequisite state,
    not something the production CLI produces — so writing it BEFORE
    invocation is OUTCOME-class-compatible (per the
    odd-test-altitude-discipline SKILL: "PM authoring is the user's
    setup step, not pre-arranged production output").
    """
    pm_dir = workspace / "workspace" / ".loam" / "pms" / pm_handle
    pm_dir.mkdir(parents=True)
    contract = {
        "schema_version": 1,
        "handle": pm_handle,
        "project_name": "smoke-test",
        "project_kind": "general",
        "owner_name": "Smoke Operator",
        "workspace_root": str(workspace),
        "decision_surfacing_policy": {
            "onboarding_mode": False,
            # Surface 1 question at a time (matches stdin-pipe pattern).
            "max_questions_per_turn": 1,
            "cool_down_seconds": 0,
            # The interview's response_producer feeds responses
            # synchronously, so require_owner_response=False keeps the
            # surface non-blocking.
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


def test_AC_V025_C6_1_full_pipeline_with_authored_pm(
    tmp_path: Path,
) -> None:
    """End-to-end OUTCOME-altitude probe: fixture-with-PM authored + four
    pipeline stages all exit 0 + four named artefacts exist.

    Skips cleanly if ``claude`` or ``loam`` is not on PATH.

    Failure of this test post-C6 indicates EITHER:

    1. The PM-fixture-authoring pattern is wrong (PM not discovered).
    2. The CLI pipeline has a stage-to-stage handoff bug (an artefact
       isn't produced even when its predecessor exists).
    3. The default workspace-root resolution (C6.3) regresses some
       sealed AC.
    """
    if shutil.which("claude") is None:
        pytest.skip(
            "outcome-altitude AC.V025-C6.1 requires the `claude` CLI on "
            "PATH (subscription-routed auth via `claude -p`). Install "
            "Claude Code per https://docs.anthropic.com/claude-code "
            "and run `claude /login` once."
        )
    if shutil.which("loam") is None:
        pytest.skip(
            "outcome-altitude AC.V025-C6.1 requires the `loam` CLI on "
            "PATH (workstation-installed via install-from-source.txt)."
        )

    # ---- Setup -----------------------------------------------------
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()
    pm_handle = "smoke-pm"
    _author_stub_pm(workspace, pm_handle)

    repo = _setup_jsts_repo(tmp_path)

    # ---- Stage 1 — extraction (real claude -p) ---------------------
    rc1, out1, err1 = _run_loam(
        [
            "odd-extract",
            str(repo),
            "--live",
            "--budget-cents",
            "500",
            "--budget-override",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc1 == 0, (
        f"Stage 1 (extraction) must exit 0; got rc={rc1}.\n"
        f"stdout: {out1[-2000:]}\n"
        f"stderr: {err1[-2000:]}"
    )

    # Locate the extraction directory (compute_repo_id is private; we
    # inspect ``<workspace>/.loam/extractions/`` for the single subdir).
    ext_root = workspace / ".loam" / "extractions"
    ext_dirs = [p for p in ext_root.iterdir() if p.is_dir()]
    assert len(ext_dirs) == 1, (
        f"Stage 1 should leave exactly 1 extraction-dir; got "
        f"{len(ext_dirs)}: {ext_dirs!r}"
    )
    ext_dir = ext_dirs[0]
    objectives_path = ext_dir / "objectives.yaml"
    assert objectives_path.exists(), (
        f"Stage 1 must produce objectives.yaml; absent at "
        f"{objectives_path}.\nstderr: {err1[-2000:]}"
    )

    # ---- Stage 2 — interview (no claude -p; stdin-fed responses) ---
    # Generous stdin pipe: confirm-1 responses for every confirm question
    # + ``no`` for the trailing free-form-add. With at most 4-5 extracted
    # objectives the pipe carries enough.
    stdin_pipe = ("1\n" * 20) + "no\n"
    rc2, out2, err2 = _run_loam(
        [
            "odd-extract",
            str(repo),
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
        f"stdout: {out2[-2000:]}\n"
        f"stderr: {err2[-2000:]}"
    )
    augmented_path = ext_dir / "augmented-objectives.yaml"
    assert augmented_path.exists(), (
        f"Stage 2 must produce augmented-objectives.yaml; absent at "
        f"{augmented_path}.\nstderr: {err2[-2000:]}"
    )

    # ---- Stage 3 — gaps -------------------------------------------
    rc3, out3, err3 = _run_loam(
        [
            "odd-extract",
            str(repo),
            "--gaps",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc3 == 0, (
        f"Stage 3 (--gaps) must exit 0; got rc={rc3}.\n"
        f"stdout: {out3[-2000:]}\n"
        f"stderr: {err3[-2000:]}"
    )
    gap_inventory_path = ext_dir / "gap-inventory.yaml"
    assert gap_inventory_path.exists(), (
        f"Stage 3 must produce gap-inventory.yaml; absent at "
        f"{gap_inventory_path}.\nstderr: {err3[-2000:]}"
    )

    # ---- Stage 4 — build-next -------------------------------------
    rc4, out4, err4 = _run_loam(
        [
            "odd-extract",
            str(repo),
            "--build-next",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc4 == 0, (
        f"Stage 4 (--build-next) must exit 0; got rc={rc4}.\n"
        f"stdout: {out4[-2000:]}\n"
        f"stderr: {err4[-2000:]}"
    )
    build_next_path = ext_dir / "build-next.yaml"
    assert build_next_path.exists(), (
        f"Stage 4 must produce build-next.yaml; absent "
        f"at {build_next_path}.\nstderr: {err4[-2000:]}"
    )

    # ---- All four artefacts present + non-empty -------------------
    for name in (
        "objectives.yaml",
        "augmented-objectives.yaml",
        "gap-inventory.yaml",
        "build-next.yaml",
    ):
        path = ext_dir / name
        assert path.stat().st_size > 0, (
            f"{name} must be non-empty; got size 0 at {path}"
        )

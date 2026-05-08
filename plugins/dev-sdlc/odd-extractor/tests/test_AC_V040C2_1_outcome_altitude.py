"""AC.V040C2.1 — Outcome-altitude probe for code-gen-from-objectives.

**outcome-altitude: true** (per
``docs/odd-llm-grounding.lean.md`` §"Outcome-altitude AC requirement"
+ ``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``).

Per v0.4.0 Cycle 2 plan-doc §4 AC.V040C2.{1,2,3,4,6}: this test
invokes the full production chain on a real clone of
``jsts-playwright-app``:

    loam odd-extract <repo> --live          # Stage 1
    loam odd-extract <repo> --interview     # Stage 2 (stdin-fed)
    loam odd-extract <repo> --gaps          # Stage 3
    loam odd-extract <repo> --build-next    # Stage 4
    loam odd-extract <repo> --code-gen      # Stage 5 (NEW at v0.4.0)

Every LLM-routed stage executes the real ``claude -p`` subprocess
through ``ClaudePrintAnthropicShimClient`` —
NO ``ANTHROPIC_API_KEY``, NO ``import anthropic``,
NO monkey-patch / mock of ``messages.create()`` /
``subprocess.run`` / the ``claude`` binary, NO pre-arrangement of
state the production code under test would itself produce.

Asserts (per v0.4.0 Cycle 2 plan-doc §4):

1. AC.V040C2.1 — Stage 5 (--code-gen) exits 0; produces
   ``<extraction_dir>/code-gen/{diff.patch,manifest.json}``.
2. AC.V040C2.1 — manifest.json round-trips through
   :class:`CodeGenDiff.model_validate`; ≥1 commit; commit's
   ``diff_text`` contains unified-diff structural markers.
3. AC.V040C2.1 — commit message rendered via
   :func:`render_full_message` carries the ``---objectives---``
   delimited block; ``extract_objectives_block`` round-trips it
   back to a valid :class:`LiftedFrom`.
4. AC.V040C2.4 — ``lifted_from.source_doc`` references the
   originating ``objective_id`` (``O.<…>`` shape); F3 closure.
5. AC.V040C2.3 — multi-commit case: if real output produced ≥2
   commits, each has a populated ``lifted_from``; if 1 commit,
   single-commit verification passes and multi-commit defers to
   C3-or-later per plan-doc §13 D-V040C2.3.

Skip semantics: cleanly skip when ``claude`` or ``loam`` is not on
PATH. Pattern matches v0.2.5 outcome-altitude tests
(``test_AC_V025_C6_1_*``).

Stochasticity: ``claude -p`` is stochastic. The test asserts on
structural properties stable across stochastic variation —
parseable unified-diff markers, populated ``LiftedFrom``,
referenced objective_id. The test does NOT assert on commit
subject text or specific diff hunks.

Cost: per `claude_print_synthesis_client` invariants and the
v0.2.5 ``--budget-cents 500`` precedent, a full chain costs
typically 4-8 LLM calls; on Max subscription
``total_cost_usd=0.0`` is the billing-floor sentinel.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from loam.objective_tracker.spec import LiftedFrom
from loam_odd_extractor.code_gen import extract_objectives_block
from loam_odd_extractor.code_gen_spec import CodeGenDiff


_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "jsts-playwright-app"
)


def _setup_jsts_repo(tmp_path: Path) -> Path:
    """Copy canonical jsts-playwright-app fixture + git-init.

    Mirrors ``test_AC_V025_C6_1_*._setup_jsts_repo``. Pre-arrangement
    rubric (per ``odd-test-altitude-discipline`` SKILL): copying the
    static fixture + git-init is user-prerequisite-state, NOT
    pre-arrangement of artefacts the production code would produce.
    The production code produces ``objectives.yaml`` /
    ``backing-map.yaml`` / ``synthesis.yaml`` / etc. — none of which
    this helper writes.
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

    Mirrors ``test_AC_V025_C6_1_*._author_stub_pm``. PM contract
    authoring is user-prerequisite state, not production output —
    OUTCOME-class-compatible per the SKILL's pre-arrangement rubric.
    """
    import yaml as _yaml

    pm_dir = workspace / "workspace" / ".loam" / "pms" / pm_handle
    pm_dir.mkdir(parents=True)
    contract = {
        "schema_version": 1,
        "handle": pm_handle,
        "project_name": "v040c2-outcome-altitude",
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
    (pm_dir / "contract.yaml").write_text(_yaml.safe_dump(contract))


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


def test_AC_V040C2_1_outcome_altitude_full_chain_jsts_playwright_app(
    tmp_path: Path,
) -> None:
    """Full chain ``--live → --interview → --gaps → --build-next →
    --code-gen`` against a clone of jsts-playwright-app produces a
    valid CodeGenDiff with populated per-commit ``lifted_from``.

    NO monkeypatch of LLM dispatch. NO subprocess / claude-binary
    mocking. NO pre-arrangement of objectives.yaml / backing-map.yaml /
    augmented-objectives.yaml / gap-inventory.yaml / build-next.yaml /
    code-gen/manifest.json — every artefact is produced by a
    production CLI invocation under test.
    """
    if shutil.which("claude") is None:
        pytest.skip(
            "outcome-altitude AC.V040C2.1 requires the `claude` CLI on "
            "PATH (subscription-routed auth via `claude -p`). Install "
            "Claude Code per https://docs.anthropic.com/claude-code "
            "and run `claude /login` once."
        )
    if shutil.which("loam") is None:
        pytest.skip(
            "outcome-altitude AC.V040C2.1 requires the `loam` CLI on "
            "PATH (workstation-installed via install-from-source.txt)."
        )

    # ---- Setup -----------------------------------------------------
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()
    pm_handle = "v040c2-pm"
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

    # Locate the extraction directory (compute_repo_id is private).
    ext_root = workspace / ".loam" / "extractions"
    ext_dirs = [p for p in ext_root.iterdir() if p.is_dir()]
    assert len(ext_dirs) == 1, (
        f"Stage 1 should leave exactly 1 extraction-dir; got "
        f"{len(ext_dirs)}: {ext_dirs!r}"
    )
    ext_dir = ext_dirs[0]
    assert (ext_dir / "objectives.yaml").exists(), (
        f"Stage 1 must produce objectives.yaml; absent.\n"
        f"stderr: {err1[-2000:]}"
    )

    # ---- Stage 2 — interview (no claude -p; stdin-fed) -------------
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
    assert (ext_dir / "augmented-objectives.yaml").exists(), (
        f"Stage 2 must produce augmented-objectives.yaml; absent.\n"
        f"stderr: {err2[-2000:]}"
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
    assert (ext_dir / "gap-inventory.yaml").exists(), (
        f"Stage 3 must produce gap-inventory.yaml; absent.\n"
        f"stderr: {err3[-2000:]}"
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
    assert (ext_dir / "build-next.yaml").exists(), (
        f"Stage 4 must produce build-next.yaml; absent.\n"
        f"stderr: {err4[-2000:]}"
    )

    # ---- Stage 5 — code-gen (real claude -p; the C2 outcome AC) ---
    rc5, out5, err5 = _run_loam(
        [
            "odd-extract",
            str(repo),
            "--code-gen",
            "--workspace-root",
            str(workspace),
        ],
    )
    assert rc5 == 0, (
        f"AC.V040C2.1 — Stage 5 (--code-gen) must exit 0; got "
        f"rc={rc5}.\n"
        f"stdout: {out5[-2000:]}\n"
        f"stderr: {err5[-2000:]}"
    )

    # ---- AC.V040C2.1 — manifest.json + diff.patch produced --------
    manifest_path = ext_dir / "code-gen" / "manifest.json"
    diff_path = ext_dir / "code-gen" / "diff.patch"
    assert manifest_path.exists(), (
        f"AC.V040C2.1 — Stage 5 must produce manifest.json; absent at "
        f"{manifest_path}.\nstderr: {err5[-2000:]}"
    )
    assert diff_path.exists(), (
        f"AC.V040C2.1 — Stage 5 must produce diff.patch; absent at "
        f"{diff_path}.\nstderr: {err5[-2000:]}"
    )
    assert manifest_path.stat().st_size > 0, (
        f"manifest.json must be non-empty; got size 0"
    )
    assert diff_path.stat().st_size > 0, (
        f"diff.patch must be non-empty; got size 0"
    )

    # ---- AC.V040C2.1 — manifest round-trips through CodeGenDiff ---
    payload = json.loads(manifest_path.read_text())
    diff = CodeGenDiff.model_validate(payload)
    assert len(diff.commits) >= 1, (
        f"AC.V040C2.1 — code-gen must produce at least one commit; "
        f"got {len(diff.commits)}"
    )

    # ---- AC.V040C2.1 — commit diff_text contains unified-diff -----
    # Structural shape only (per D-V040C2.6 stochasticity tolerance):
    # at least one of ``--- a/`` / ``+++ b/`` / ``@@`` markers must
    # be present, OR the diff text contains diff-friendly patch
    # syntax. ``claude -p`` is stochastic; structural markers are
    # stable.
    first_commit = diff.commits[0]
    diff_text = first_commit.diff_text
    assert diff_text.strip(), (
        f"AC.V040C2.1 — first commit's diff_text must be non-empty"
    )
    has_unified_marker = (
        "@@" in diff_text
        or ("--- " in diff_text and "+++ " in diff_text)
    )
    assert has_unified_marker, (
        f"AC.V040C2.1 — first commit's diff_text must contain "
        f"unified-diff structural markers (`@@` or `--- `/`+++ `); "
        f"got first 1000 chars:\n{diff_text[:1000]}"
    )

    # ---- AC.V040C2.1 — `objectives:` block round-trips ------------
    rendered = first_commit.render_full_message()
    parsed = extract_objectives_block(rendered)
    assert isinstance(parsed, LiftedFrom)
    assert parsed == first_commit.lifted_from, (
        "AC.V040C2.1 — render_full_message → extract_objectives_block "
        "round-trip must preserve LiftedFrom"
    )

    # ---- AC.V040C2.4 — `source_doc` references objective_id -------
    # F3 closure: the `_resolve_source_doc` fallback produces a
    # meaningful pointer that contains the `O.<...>` objective_id.
    # Format per code_gen._resolve_source_doc:
    #   `objectives.yaml#<objective_id>::<source>` (with source) or
    #   `objectives.yaml#<objective_id>` (without source).
    source_doc = first_commit.lifted_from.source_doc
    assert source_doc.startswith("objectives.yaml#O."), (
        f"AC.V040C2.4 — source_doc must reference an objective_id "
        f"(format `objectives.yaml#O.<…>` per _resolve_source_doc); "
        f"got {source_doc!r}"
    )

    # ---- AC.V040C2.4 — `source_ac` populated from gap_id ----------
    # Format per code_gen._resolve_source_ac: gap_id directly.
    # gap_ids on real fixture follow `G.<CATEGORY>.<…>` shape.
    source_ac = first_commit.lifted_from.source_ac
    assert source_ac.startswith("G."), (
        f"AC.V040C2.4 — source_ac must equal a real gap_id (format "
        f"`G.<CATEGORY>.<…>` per gap-inventory.yaml); got "
        f"{source_ac!r}"
    )

    # ---- AC.V040C2.3 — multi-commit verification (closes C1 F1) ---
    # If real claude -p produced ≥2 commits, each must carry a
    # populated lifted_from. If 1 commit, single-commit shape passes
    # and multi-commit verification defers per plan-doc §13
    # D-V040C2.3 (one build-next candidate → one commit is the
    # v0.4.0 baseline; multi-commit prompt is a separate methodology
    # question).
    for idx, commit in enumerate(diff.commits):
        assert commit.lifted_from is not None, (
            f"AC.V040C2.3 — every commit must carry lifted_from; "
            f"commit[{idx}] missing it"
        )
        assert commit.lifted_from.source_doc.startswith(
            "objectives.yaml#O."
        ), (
            f"AC.V040C2.3 — every commit's lifted_from.source_doc "
            f"must reference an objective_id; commit[{idx}] got "
            f"{commit.lifted_from.source_doc!r}"
        )
        assert commit.lifted_from.source_ac.startswith("G."), (
            f"AC.V040C2.3 — every commit's lifted_from.source_ac "
            f"must equal a real gap_id; commit[{idx}] got "
            f"{commit.lifted_from.source_ac!r}"
        )
        # D-build.2: source_commit is None at code-gen time.
        assert commit.lifted_from.source_commit is None, (
            f"AC.V040C2.3 — D-build.2 invariant: source_commit must "
            f"be None at code-gen time; commit[{idx}] got "
            f"{commit.lifted_from.source_commit!r}"
        )

    # ---- AC.V040C3.5 (folded F2-from-C2) — stage-count print ------
    # Print the produced commit count so future log-readers can
    # classify single-commit vs multi-commit baselines without
    # re-running the test. Per v0.4.0 C2 build report F2 #2 +
    # v0.4.0 C3 plan-doc §4 AC.V040C3.5. Cosmetic; no assertion.
    print(
        f"AC.V040C3.5 stage-count: code-gen produced "
        f"{len(diff.commits)} commit(s); shape = "
        f"{'single-commit' if len(diff.commits) == 1 else 'multi-commit'}"
    )

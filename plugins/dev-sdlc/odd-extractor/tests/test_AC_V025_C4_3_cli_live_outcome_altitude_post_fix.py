"""AC.V025-C4.3 — outcome-altitude AC test for CLI ``--live`` post-F8-fix.

**outcome-altitude: true** (per ``docs/odd-llm-grounding.lean.md`` §"Outcome-altitude AC requirement"
+ ``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``).

Per v0.2.5 corrective C4 plan-doc §2 AC.V025-C4.3 + corrective C4-pivot
(2026-05-05) — pivoted to ``claude -p`` subscription auth:

This test is the post-fix verification probe for the F8 BLOCKER closed by
the C4 corrective. It mirrors the AC.V025-C3.3 test (the OUTCOME-class
probe that surfaced F8) but verifies the GREEN path post-fix — the full
happy path of the synthesis pipeline against the live subscription via
``claude -p``.

**Pre-fix verification:** with the C3 outcome (no prompt-strengthening,
no demotion-guard), the LLM produces VERIFIED-banded objectives without
two-source evidence; the validator raises ``ValidationError``; ``rc != 0``;
``objectives.yaml`` is empty. C3.3 caught this.

**Post-fix expectation:** with the strengthened prompt + demotion-guard,
the synthesis pass completes — either the LLM produces compliant rows
(VERIFIED with two sources, or PLAUSIBLE), OR the demotion-guard rewrites
malformed VERIFIED rows to PLAUSIBLE before validation. Either way,
``rc == 0``, ``objectives.yaml`` populated, ``backing-map.yaml`` exists.

Skip semantics (per the SKILL's "skip-by-default-locally + run-on-demand
by humans" pattern): mirrors C3.3 post-pivot (skip cleanly when the
``claude`` CLI is absent from PATH).

**Pre-arrangement detection rubric** (per the SKILL):

- Production entry-point invoked? YES — ``cli.main()`` with ``--live``.
- No state pre-arranged that production would produce? YES — only the
  workspace dir + the fixture clone are set up; no objectives.yaml /
  backing-map.yaml / synthesis.yaml are pre-written.
- Asserts on production-produced artefacts? YES — objectives.yaml content,
  backing-map.yaml existence, synthesis.yaml model_id.
- No SDK / client / subprocess mocking? YES — no monkeypatch / mock of
  ``synthesis.build_default_anthropic_client`` or
  ``claude_print_synthesis_client.build_default_synthesis_client`` or
  ``subprocess.run`` / ``subprocess.Popen`` / the ``claude`` binary.

This test is **OUTCOME-class** per the SKILL's classifier.

**Stochasticity tolerance:** per dispatch brief, the operator re-runs
this test 3x; ≥2 of 3 must pass cleanly. The test itself is single-
invocation; the human/operator re-runs to verify stochastic stability.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.cli import main
from loam_odd_extractor.state import compute_repo_id, extraction_dir


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "jsts-playwright-app"


def _setup_jsts_repo(tmp_path: Path) -> Path:
    """Copy canonical jsts-playwright-app fixture + git-init.

    Mirrors ``test_AC_V025_C3_3_*._setup_jsts_repo``.
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


def test_AC_V025_C4_3_cli_live_outcome_altitude_post_fix(
    tmp_path: Path,
) -> None:
    """End-to-end OUTCOME-altitude probe (post-F8-fix): ``loam odd-extract
    <repo> --live`` against the REAL ``claude -p`` subprocess produces
    clean extraction output — the full happy path post-corrective-C4
    (and post-C4-pivot subscription-routing).

    NO monkey-patching of ``synthesis.build_default_anthropic_client`` or
    ``claude_print_synthesis_client.build_default_synthesis_client``.
    NO subprocess / claude-binary mocking.
    NO pre-arrangement of objectives.yaml / backing-map.yaml.

    Skips cleanly if ``claude`` is not on PATH.

    Failure of this test post-C4 indicates EITHER:

    1. The prompt-strengthening (AC.V025-C4.1) was insufficient AND the
       demotion-guard (AC.V025-C4.2) failed to handle the LLM's actual
       output shape.
    2. The LLM produces objectives that fail OTHER validators beyond the
       VERIFIED two-source rule (means F8 was just one symptom of a
       deeper synthesis-quality problem; halt-and-surface per dispatch
       brief).
    3. The C4-pivot shim's prompt-flattening or response-parsing
       diverges from claude -p's actual response shape (means the pivot
       transport itself has a bug; halt-and-surface).

    This is the prevention test for F8 staying closed. Per the
    ``odd-test-altitude-discipline`` SKILL: this test is the OUTCOME-class
    verification for AC.V025-C4.3. STUB-class probes (e.g., AC.V025-C4.2's
    unit test) verify the guard's behavior against synthetic payloads;
    only the OUTCOME-class probe verifies the full pipeline against the
    live LLM.
    """
    # Precondition — `claude` binary on PATH (v0.2.5 corrective C4-pivot:
    # subscription auth via OAuth keychain, no API key).
    if shutil.which("claude") is None:
        pytest.skip(
            "outcome-altitude AC.V025-C4.3 requires the `claude` CLI on "
            "PATH (v0.2.5 corrective C4-pivot: subscription-routed auth "
            "via `claude -p`). Install Claude Code per "
            "https://docs.anthropic.com/claude-code and run "
            "`claude /login` once."
        )

    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = _setup_jsts_repo(tmp_path)

    # Invoke the production CLI surface — NO monkeypatch, NO mocks.
    rc = main(
        [
            str(repo),
            "--live",
            "--budget-cents",
            "500",
            "--budget-override",
            "--workspace-root",
            str(workspace),
        ]
    )

    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)

    # 1. Clean exit. If rc != 0 post-C4, the F8 fix is incomplete.
    assert rc == 0, (
        f"CLI must exit cleanly with --live + real SDK post-C4-fix; "
        f"got rc={rc}. Indicates either: (a) prompt-strengthening "
        f"insufficient AND demotion-guard failed to cover the LLM's "
        f"actual output shape; (b) LLM produces objectives that fail "
        f"OTHER validators beyond F8's two-source rule (deeper "
        f"synthesis-quality problem; halt-and-surface)."
    )

    # 2. Production produced objectives.yaml — outcome-altitude artefact.
    objectives_path = ext_dir / "objectives.yaml"
    assert objectives_path.exists(), (
        f"objectives.yaml must be written by the production CLI; "
        f"absent at {objectives_path}. Indicates synthesis pass did not "
        f"complete (would mean rc != 0 above; defensive assertion)."
    )
    objectives_payload = (
        yaml.safe_load(objectives_path.read_text(encoding="utf-8")) or {}
    )
    objectives_list = objectives_payload.get("objectives") or []
    # ANY band is acceptable post-fix. The fix is "no validator error";
    # the band can be VERIFIED (LLM cooperates with tightened prompt),
    # PLAUSIBLE (LLM had only single-source, OR demotion-guard demoted
    # a malformed VERIFIED), or HYPOTHESISED.
    assert len(objectives_list) >= 1, (
        f"objectives.yaml must contain >=1 objective on jsts-playwright-app "
        f"post-C4-fix (canonical fixture has README + tests + code "
        f"patterns sufficient for >=1 objective at SOME band per v0.2.4 "
        f"Cycle 3 SOFT smoke evidence); got {len(objectives_list)}."
    )

    # 3. Production produced backing-map.yaml — outcome-altitude artefact.
    backing_map_path = ext_dir / "backing-map.yaml"
    assert backing_map_path.exists(), (
        f"backing-map.yaml must be written by the production CLI; "
        f"absent at {backing_map_path}. Indicates backing-map population "
        f"step did not run (gated on non-empty objectives per "
        f"generate.py)."
    )

    # 4. synthesis.yaml shows real model_id (not the "(none)" sentinel).
    synthesis_path = ext_dir / "synthesis.yaml"
    assert synthesis_path.exists(), (
        f"synthesis.yaml must be written by the production CLI; "
        f"absent at {synthesis_path}."
    )
    synthesis_payload = (
        yaml.safe_load(synthesis_path.read_text(encoding="utf-8")) or {}
    )
    model_id = synthesis_payload.get("model_id", "(none)")
    assert model_id != "(none)", (
        f"synthesis.yaml model_id must reflect a real synthesis pass against "
        f"the live API; got {model_id!r}."
    )
    assert model_id.startswith("claude-"), (
        f"synthesis.yaml model_id must match a real Anthropic model "
        f"identifier (starts with `claude-`); got {model_id!r}."
    )

"""AC.V025-C3.3 — outcome-altitude AC test for the CLI ``--live`` synthesis path.

**outcome-altitude: true** (per ``docs/odd-llm-grounding.lean.md`` §"Outcome-altitude AC requirement"
+ ``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``).

This is the FIRST WORKED INSTANCE of the ``odd-test-altitude-discipline`` SKILL's
"HARD per-cycle required" classifier path applied to a production-facing surface
(``install-from-source.txt`` + the CLI ``--live`` flow against the real ``anthropic``
SDK).

The test exists to close the procedural gap behind v0.2.5 BLOCKER F5 — the C1
verification test monkey-patched the import boundary, so the real-world install
path was never exercised end-to-end. This test exercises the production CLI
surface against:

- the REAL ``anthropic`` SDK (no ``monkeypatch.setattr`` of
  ``synthesis.build_default_anthropic_client``; no ``mock.patch`` of the SDK);
- the REAL Anthropic API (requires ``ANTHROPIC_API_KEY`` env var; skips cleanly
  if not set);
- a REAL fixture (``jsts-playwright-app`` per the canonical pattern); and
- NO pre-arrangement of ``objectives.yaml`` / ``backing-map.yaml`` — the
  production code must produce them.

Skip semantics (per the SKILL's "skip-by-default-locally + run-on-demand by
humans" pattern):

- Skips with explicit reason if ``ANTHROPIC_API_KEY`` is not set in the
  environment.
- Skips with explicit reason if the ``anthropic`` SDK cannot be imported
  (the F5 condition pre-fix).

When BOTH preconditions are present, the test runs against the live API and
asserts the production outcome (objectives + backing-map + real model_id).

**Pre-arrangement detection rubric** (per the SKILL):

- ☐ Production entry-point invoked? YES — ``cli.main()`` with ``--live``.
- ☐ No state pre-arranged that production would produce? YES — only the
  workspace dir + the fixture clone are set up; no objectives.yaml /
  backing-map.yaml / synthesis.yaml are pre-written.
- ☐ Asserts on production-produced artefacts? YES — objectives.yaml content,
  backing-map.yaml existence, synthesis.yaml model_id.
- ☐ No SDK / client mocking? YES — no monkeypatch / mock of the synthesis
  module's build_default_anthropic_client.

This test is **OUTCOME-class** per the SKILL's classifier.

**Cost note** — live synthesis on the jsts-playwright-app fixture per v0.2.4
Cycle 3 SOFT smoke evidence consumed under 1¢. ``--budget-cents 500`` is
generous; ``--budget-override`` set so the test exits cleanly even if the
foreign-codebase budget envelope gates kick in.
"""

from __future__ import annotations

import os
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

    Mirrors ``test_AC_V025_C1_C2_*._setup_jsts_repo``.
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


def test_AC_V025_C3_3_cli_live_outcome_altitude(tmp_path: Path) -> None:
    """End-to-end OUTCOME-altitude probe: ``loam odd-extract <repo> --live``
    against the REAL Anthropic SDK + API produces real synthesis output.

    NO monkey-patching of ``anthropic`` or
    ``synthesis.build_default_anthropic_client``.
    NO pre-arrangement of objectives.yaml / backing-map.yaml.

    Skips cleanly if ``ANTHROPIC_API_KEY`` is unset OR ``anthropic`` SDK
    is not importable (the F5 pre-fix condition).

    Failure of this test indicates EITHER:

    1. The CLI synthesis wire-through is broken (the F1 condition the v0.2.5
       C1 corrective fixed); OR
    2. The ``[synthesis]`` extra install path is broken (the F5 condition the
       v0.2.5 C3 corrective fixed); OR
    3. Real-world live synthesis returns malformed responses that the
       production parser can't handle (a regression in the synthesis layer
       not caught by stub-based tests).

    Per the ``odd-test-altitude-discipline`` SKILL: this test is the
    OUTCOME-class verification for AC.V025-C3.3. STUB-class probes (e.g.,
    ``test_AC_V025_C1_C2_*``) satisfy implementation-altitude ACs but
    cannot satisfy outcome-altitude ACs.
    """
    # Precondition 1 — anthropic SDK importable. Pre-C3 (and on any system
    # without [synthesis] extra installed) this fails; pytest.importorskip
    # is the canonical pattern.
    pytest.importorskip(
        "anthropic",
        reason=(
            "outcome-altitude AC.V025-C3.3 requires the real anthropic SDK; "
            "install with `pip install -r install-from-source.txt` (which now "
            "includes the [synthesis] extra per v0.2.5 corrective C3) or "
            "`pip install anthropic>=0.40` directly."
        ),
    )

    # Precondition 2 — ANTHROPIC_API_KEY set. The production CLI's
    # build_default_anthropic_client constructs anthropic.Anthropic() which
    # reads the key from env; absent env, the constructor either raises or
    # the API call fails. Skip cleanly if absent.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip(
            "ANTHROPIC_API_KEY env var not set; outcome-altitude "
            "AC.V025-C3.3 requires real-API access. To run locally: "
            "`export ANTHROPIC_API_KEY=$(security find-generic-password "
            "-s ANTHROPIC_API_KEY -w)` (macOS keychain) before pytest."
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

    # 1. Clean exit. If the CLI fails (F5 install gap, F1 wire-through gap,
    #    or any new regression), rc != 0 and the assertion below names which
    #    of the three failure paths is in play.
    assert rc == 0, (
        f"CLI must exit cleanly with --live + real SDK; got rc={rc}. "
        f"This indicates one of: (a) F5 — anthropic SDK missing despite "
        f"install path; (b) F1 — CLI synthesis wire-through broken; (c) a "
        f"new regression in the synthesis layer. Check stderr for the "
        f"OddExtractorError carrier message."
    )

    # 2. Production produced objectives.yaml — outcome-altitude artefact.
    objectives_path = ext_dir / "objectives.yaml"
    assert objectives_path.exists(), (
        f"objectives.yaml must be written by the production CLI; "
        f"absent at {objectives_path}. Indicates synthesis pass did not "
        f"complete (F1 condition or upstream regression)."
    )
    objectives_payload = (
        yaml.safe_load(objectives_path.read_text(encoding="utf-8")) or {}
    )
    objectives_list = objectives_payload.get("objectives") or []
    assert len(objectives_list) >= 1, (
        f"objectives.yaml must contain ≥1 objective on jsts-playwright-app "
        f"(canonical fixture has README + tests + code patterns sufficient "
        f"for ≥1 PLAUSIBLE objective per v0.2.4 SOFT smoke evidence); "
        f"got {len(objectives_list)}. Indicates synthesis returned empty "
        f"or production parser stripped the response."
    )

    # 3. Production produced backing-map.yaml — outcome-altitude artefact.
    backing_map_path = ext_dir / "backing-map.yaml"
    assert backing_map_path.exists(), (
        f"backing-map.yaml must be written by the production CLI; "
        f"absent at {backing_map_path}. Indicates backing-map population "
        f"step did not run (gated on non-empty objectives per generate.py:229)."
    )

    # 4. synthesis.yaml shows real model_id (not "(none)" sentinel + matches
    #    a canonical Anthropic model name shape — starts with "claude-").
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
        f"the live API; got {model_id!r}. Indicates the synthesis pass fell "
        f"into the empty-result fallback path (the F1 silent no-op)."
    )
    # A real Anthropic model_id starts with `claude-` per the SDK's model
    # catalogue. This guards against a regression where some sentinel other
    # than "(none)" leaks through (e.g., "stub-model" from a coupled test).
    assert model_id.startswith("claude-"), (
        f"synthesis.yaml model_id must match a real Anthropic model "
        f"identifier (starts with `claude-`); got {model_id!r}. Indicates "
        f"a stub or sentinel model_id leaked from a non-production code "
        f"path."
    )

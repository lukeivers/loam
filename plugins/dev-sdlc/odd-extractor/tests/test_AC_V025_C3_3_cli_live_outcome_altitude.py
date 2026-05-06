"""AC.V025-C3.3 — outcome-altitude AC test for the CLI ``--live`` synthesis path.

**outcome-altitude: true** (per ``docs/odd-llm-grounding.lean.md`` §"Outcome-altitude AC requirement"
+ ``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``).

This is the FIRST WORKED INSTANCE of the ``odd-test-altitude-discipline`` SKILL's
"HARD per-cycle required" classifier path applied to a production-facing surface
(``install-from-source.txt`` + the CLI ``--live`` flow against the production
``claude -p`` subprocess transport).

The test exists to close the procedural gap behind v0.2.5 BLOCKER F5 — the C1
verification test monkey-patched the import boundary, so the real-world install
path was never exercised end-to-end. **v0.2.5 corrective C4-pivot 2026-05-05:
the test was rewired from the Anthropic SDK + ``ANTHROPIC_API_KEY`` precondition
to the ``claude`` binary on PATH precondition** (subscription-routed auth via
``claude -p`` per owner ruling Telegram 10194: "we absolutely will not be using
an Anthropic api key of any kind. We only use the subscription").

The test exercises the production CLI surface against:

- the REAL ``claude -p`` subprocess (no ``monkeypatch.setattr`` of
  ``synthesis.build_default_anthropic_client`` or
  ``claude_print_synthesis_client.build_default_synthesis_client``;
  no ``mock.patch`` of subprocess.run / subprocess.Popen);
- the REAL Claude Max subscription via OAuth keychain (no API key reads);
- a REAL fixture (``jsts-playwright-app`` per the canonical pattern); and
- NO pre-arrangement of ``objectives.yaml`` / ``backing-map.yaml`` — the
  production code must produce them.

Skip semantics (per the SKILL's "skip-by-default-locally + run-on-demand by
humans" pattern):

- Skips with explicit reason if ``claude`` binary is not on PATH (out-of-band
  install per https://docs.anthropic.com/claude-code).

When the ``claude`` binary resolves on PATH and OAuth state is present, the
test runs against the live subscription and asserts the production outcome
(objectives + backing-map + real model_id). If OAuth is absent, the synthesis
client surfaces a "Not logged in" error which the test treats as a real
failure (instructions to run ``claude /login``).

**Pre-arrangement detection rubric** (per the SKILL):

- ☐ Production entry-point invoked? YES — ``cli.main()`` with ``--live``.
- ☐ No state pre-arranged that production would produce? YES — only the
  workspace dir + the fixture clone are set up; no objectives.yaml /
  backing-map.yaml / synthesis.yaml are pre-written.
- ☐ Asserts on production-produced artefacts? YES — objectives.yaml content,
  backing-map.yaml existence, synthesis.yaml model_id.
- ☐ No SDK / client / subprocess mocking? YES — no monkeypatch / mock of
  ``synthesis.build_default_anthropic_client`` or
  ``claude_print_synthesis_client.build_default_synthesis_client`` or
  ``subprocess.run`` / ``subprocess.Popen`` / the ``claude`` binary.

This test is **OUTCOME-class** per the SKILL's classifier.

**Cost note** — live synthesis on the jsts-playwright-app fixture per v0.2.4
Cycle 3 SOFT smoke evidence consumed under 1¢ on the metered API; on Max
subscription via ``claude -p`` the per-call billing is 0 (subscription-flat).
``--budget-cents 500`` is generous; ``--budget-override`` set so the test
exits cleanly even if the foreign-codebase budget envelope gates kick in.
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
    against the REAL ``claude -p`` subprocess produces real synthesis output.

    NO monkey-patching of ``synthesis.build_default_anthropic_client`` or
    ``claude_print_synthesis_client.build_default_synthesis_client``.
    NO ``subprocess`` / ``claude`` binary mocking.
    NO pre-arrangement of objectives.yaml / backing-map.yaml.

    Skips cleanly if the ``claude`` binary is not on PATH (out-of-band
    install per https://docs.anthropic.com/claude-code).

    Failure of this test indicates EITHER:

    1. The CLI synthesis wire-through is broken (the F1 condition the v0.2.5
       C1 corrective fixed); OR
    2. The ``claude`` binary is on PATH but OAuth is absent (run
       ``claude /login`` interactively); OR
    3. Real-world live synthesis returns malformed responses that the
       production parser can't handle (a regression in the synthesis layer
       not caught by stub-based tests); OR
    4. The C4-pivot shim's prompt flattening / response parsing diverges
       from the LLM's actual response shape.

    Per the ``odd-test-altitude-discipline`` SKILL: this test is the
    OUTCOME-class verification for AC.V025-C3.3. STUB-class probes (e.g.,
    ``test_AC_V025_C1_C2_*``) satisfy implementation-altitude ACs but
    cannot satisfy outcome-altitude ACs.
    """
    # Precondition — `claude` binary on PATH.
    # Pre-C4-pivot this required ANTHROPIC_API_KEY + anthropic SDK;
    # post-pivot it requires the `claude` Code CLI installed
    # (https://docs.anthropic.com/claude-code) with OAuth state already
    # written to the system keychain via `claude /login`.
    if shutil.which("claude") is None:
        pytest.skip(
            "outcome-altitude AC.V025-C3.3 requires the `claude` CLI on "
            "PATH (v0.2.5 corrective C4-pivot: subscription-routed auth "
            "via `claude -p`). Install Claude Code per "
            "https://docs.anthropic.com/claude-code and run "
            "`claude /login` once to write OAuth state to the system "
            "keychain."
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
    #    of the failure paths is in play.
    assert rc == 0, (
        f"CLI must exit cleanly with --live + claude -p; got rc={rc}. "
        f"This indicates one of: (a) `claude` binary on PATH but OAuth "
        f"absent (run `claude /login`); (b) F1 — CLI synthesis wire-"
        f"through broken; (c) C4-pivot shim's prompt-flattening or "
        f"response parsing diverges from claude -p's actual shape; (d) a "
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

"""AC.V025-C1 + AC.V025-C2 — v0.2.5 corrective tests.

Per v0.2.5 corrective C1+C2 plan-doc + dispatch brief:

- AC.V025-C1: ``loam odd-extract <repo> --live`` runs the full synthesis
  pass through the CLI surface (end-to-end, no canned-fixture bypass).
  Stub client injected via monkeypatch on ``synthesis.build_default_anthropic_client``.
  Pre-fix: this test FAILS (objectives empty; backing-map missing).
  Post-fix: passes — objectives.yaml populated, backing-map.yaml written,
  synthesis.yaml shows non-``(none)`` model_id.

- AC.V025-C2: ``loam odd-extract <repo> --interview`` against a repo
  with no PM authored produces a clean exit-2 + actionable error
  message; NO Python traceback.
  Pre-fix: FAILS (uncaught ``ValueError`` from ``resolve_pm_handle``).
  Post-fix: passes — error converted to ``OddExtractorError``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from loam_odd_extractor.cli import main
from loam_odd_extractor.state import compute_repo_id, extraction_dir


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "jsts-playwright-app"


# ---- stub client harness ------------------------------------------


class _StubBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(
        self,
        text: str,
        *,
        input_tokens: int = 100,
        output_tokens: int = 50,
    ) -> None:
        self.content = [_StubBlock(text)]
        self.usage = type(
            "Usage",
            (),
            {"input_tokens": input_tokens, "output_tokens": output_tokens},
        )()


class _MultiShotMessages:
    """Returns successive canned responses based on call counter.

    Synthesis pass (1st call) returns the objectives JSON shape;
    backing-map pass (2nd call) returns the verdict-array shape.
    """

    def __init__(
        self,
        synthesis_payload: dict[str, Any],
        backing_map_payload: list[dict[str, Any]],
    ) -> None:
        self._synthesis = synthesis_payload
        self._backing_map = backing_map_payload
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _StubResponse:
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return _StubResponse(json.dumps(self._synthesis))
        # All subsequent calls (backing-map; potentially additional).
        return _StubResponse(json.dumps(self._backing_map))


class _StubAnthropicClient:
    def __init__(
        self,
        synthesis_payload: dict[str, Any],
        backing_map_payload: list[dict[str, Any]],
    ) -> None:
        self.messages = _MultiShotMessages(
            synthesis_payload, backing_map_payload
        )


def _canned_synthesis_response() -> dict[str, Any]:
    """Mirrors ``test_AC_OBJX_5_llm_pass_synthesis._good_response``."""
    return {
        "objectives": [
            {
                "objective_id": "O.dispute-flow.1",
                "text": (
                    "Operators file refund disputes against merchant "
                    "portals at scale, replacing manual portal clickwork."
                ),
                "confidence": "VERIFIED",
                "domain": "dispute-flow",
                "evidence": {
                    "test_name_refs": ["tests/x.spec.ts::it files"],
                    "readme_excerpts": ["File refunds at scale"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.dispute-flow.2",
                "text": "Auditors trace each dispute back to operator + timestamp.",
                "confidence": "PLAUSIBLE",
                "domain": "audit",
                "evidence": {
                    "test_name_refs": [],
                    "readme_excerpts": ["audit"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.dispute-flow.3",
                "text": "Operators upload bulk dispute CSVs without portal clickwork.",
                "confidence": "PLAUSIBLE",
                "domain": "csv-upload",
                "evidence": {
                    "test_name_refs": [],
                    "readme_excerpts": ["csv"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
        ],
        "constraints": [],
        "capabilities": [],
    }


def _canned_backing_map_verdicts() -> list[dict[str, Any]]:
    """Empty verdict list — population proceeds; orphans get classified.

    The backing-map phase only runs an LLM call when there are
    narrowed pairs. The jsts fixture has dozens of evidence rows;
    pre-filter top-K narrows. Returning an empty verdict list is
    valid: every row classifies as orphan (``no-objective-match``).
    """
    return []


def _setup_jsts_repo(tmp_path: Path) -> Path:
    """Copy canonical jsts-playwright-app fixture + git-init.

    Mirrors ``test_AC_PERSONA_PULL_4_release_smoke._setup_jsts_repo``.
    """
    repo = tmp_path / "jsts-app"
    shutil.copytree(_FIXTURE_PATH, repo)
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@e.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "T"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "add", "."], check=True
    )
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


# ---- AC.V025-C1 — CLI synthesis wire-through -----------------------


def test_AC_V025_C1_cli_live_produces_real_objectives_via_synthesis(
    tmp_path: Path, monkeypatch
) -> None:
    """End-to-end: ``loam odd-extract <repo> --live`` produces real
    objectives + backing-map via the CLI surface.

    Pre-fix behaviour: ``_cmd_extract`` never constructs an Anthropic
    client; ``synthesis.build_default_anthropic_client`` is never
    called; objectives.yaml ends up empty; backing-map.yaml is never
    written; synthesis.yaml shows ``model_id: (none)``.

    Post-fix behaviour: ``_cmd_extract`` constructs a client via
    ``build_default_anthropic_client`` (monkeypatched to a stub here);
    threads it into ``generate_raw_acs`` with ``synthesis_required=True``;
    synthesis runs; backing-map populates; objectives.yaml carries
    ≥1 objective; backing-map.yaml exists; synthesis.yaml's model_id
    is non-``(none)``.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = _setup_jsts_repo(tmp_path)

    stub_client = _StubAnthropicClient(
        _canned_synthesis_response(),
        _canned_backing_map_verdicts(),
    )

    # Monkeypatch the default-client builder so --live picks up the
    # stub instead of trying to instantiate a real anthropic.Anthropic.
    from loam_odd_extractor import synthesis as _synthesis_mod

    monkeypatch.setattr(
        _synthesis_mod,
        "build_default_anthropic_client",
        lambda: stub_client,
    )

    rc = main(
        [
            str(repo),
            "--live",
            "--budget-cents",
            "100",
            "--budget-override",
            "--workspace-root",
            str(workspace),
        ]
    )
    assert rc == 0, "CLI must exit cleanly with --live + stub client"

    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)

    # 1. objectives.yaml is non-empty.
    objectives_path = ext_dir / "objectives.yaml"
    assert objectives_path.exists(), "objectives.yaml must be written"
    objectives_payload = (
        yaml.safe_load(objectives_path.read_text(encoding="utf-8")) or {}
    )
    objectives_list = objectives_payload.get("objectives") or []
    assert len(objectives_list) >= 1, (
        f"objectives.yaml must contain ≥1 objective; got {len(objectives_list)}"
    )

    # 2. backing-map.yaml exists.
    backing_map_path = ext_dir / "backing-map.yaml"
    assert backing_map_path.exists(), "backing-map.yaml must be written"

    # 3. synthesis.yaml shows non-(none) model_id.
    synthesis_path = ext_dir / "synthesis.yaml"
    assert synthesis_path.exists()
    synthesis_payload = (
        yaml.safe_load(synthesis_path.read_text(encoding="utf-8")) or {}
    )
    model_id = synthesis_payload.get("model_id", "(none)")
    assert model_id != "(none)", (
        f"synthesis.yaml model_id must reflect a real synthesis pass; "
        f"got {model_id!r}"
    )

    # 4. The stub was invoked at least once (synthesis pass).
    assert len(stub_client.messages.calls) >= 1, (
        "stub Anthropic client must receive at least the synthesis call"
    )


# ---- AC.V025-C2 — interview ValueError leak ------------------------


def test_AC_V025_C2_interview_no_pm_emits_clean_error_no_traceback(
    tmp_path: Path, capsys
) -> None:
    """``loam odd-extract <repo> --interview`` against a workspace
    with no PM authored emits actionable error + non-zero exit; NOT
    a Python traceback.

    Pre-fix: ``resolve_pm_handle`` raises Python builtin ``ValueError``;
    ``_cmd_interview``'s ``except OddExtractorError`` doesn't catch
    it; user sees a Python traceback.

    Post-fix: ``resolve_pm_handle`` raises ``OddExtractorError``; the
    CLI catches it; emits actionable message; exits non-zero.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()

    # Pre-author the extraction dir + objectives.yaml so we get past
    # the pre-PM-resolution checks (we want the PM-resolution path
    # specifically).
    repo_id = compute_repo_id(repo)
    ext_dir = extraction_dir(workspace, repo_id)
    ext_dir.mkdir(parents=True)
    objectives_path = ext_dir / "objectives.yaml"
    objectives_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "extraction_id": repo_id,
                "repo_path": str(repo),
                "created_at": "2026-05-05T00:00:00+00:00",
                "objectives": [],
                "constraints": [],
                "capabilities": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    # No PM authored under workspace/.loam/pms/ — this is the
    # smoke's exact condition.
    rc = main(
        [
            str(repo),
            "--interview",
            "--workspace-root",
            str(workspace),
        ]
    )

    captured = capsys.readouterr()
    err = captured.err

    # 1. Non-zero exit.
    assert rc != 0, f"--interview without PM must exit non-zero; got {rc}"

    # 2. Actionable phrase present. Per v0.2.5 corrective C6 (HARD-smoke
    # F-DESIGN-2): the error message no longer references the
    # nonexistent ``loam project init`` subcommand. Actionable guidance
    # = workspace path + ``--pm-handle`` flag.
    err_lower = err.lower()
    assert (
        "no pm authored" in err_lower or "--pm-handle" in err_lower
    ), f"stderr must carry actionable phrase; got: {err!r}"
    assert "loam project init" not in err_lower, (
        f"stderr must NOT reference the nonexistent `loam project "
        f"init` subcommand (v0.2.5 corrective C6 F-DESIGN-2 fix); "
        f"got: {err!r}"
    )

    # 3. NO Python traceback.
    combined = err + captured.out
    assert "Traceback (most recent call last)" not in combined, (
        f"CLI must convert ValueError → OddExtractorError, NOT leak a "
        f"traceback; got: {combined!r}"
    )

"""AC.BANDS.4 — `loam odd-extract <draft> --ratify` CLI invocable;
PM-mediated batch.

- The CLI loads the contract-draft + sidecar YAML;
- constructs the BandedAC list;
- invokes enqueue_ratification_batch via the PM;
- reports the count of pending decisions.

Test flow: tmp workspace + authored PM → copy fixture into expected
extraction-dir layout → invoke CLI → assert decision-queue.yaml has
3 entries with provenance strings matching odd-extract:*:AC.SYNTH.{1,2,3}.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.cli import main as odd_main


_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def tmp_workspace_with_pm(tmp_path: Path) -> tuple[Path, str]:
    """Tmp workspace with a fresh PM authored under
    ``<workspace>/workspace/.loam/pms/<pm-name>/``.

    Mirrors the per-project-pm tests' ``authored_pm`` fixture pattern,
    but constructed locally so the odd-extractor tests don't depend
    on the PM-side conftest.
    """
    ws = tmp_path / "test-workspace"
    ws.mkdir()
    (ws / "workspace").mkdir()

    pm_name = "ratify-test-pm"
    pm_dir = ws / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    contract = {
        "schema_version": 1,
        "handle": pm_name,
        "project_name": "test-project",
        "project_kind": "general",
        "owner_name": "Tester",
        "workspace_root": str(ws),
        "decision_surfacing_policy": {
            "onboarding_mode": False,
            "max_questions_per_turn": 1,
            "cool_down_seconds": 0,
            "require_owner_response": False,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))
    return ws, pm_name


def _stage_fixture_into_extraction_dir(
    workspace_root: Path,
    extraction_id: str,
) -> Path:
    """Copy the synthetic banded fixture into
    ``<workspace>/.loam/extractions/<repo-id>/`` so the CLI loads it
    from the canonical extraction-dir layout.
    """
    ext_dir = workspace_root / ".loam" / "extractions" / extraction_id
    ext_dir.mkdir(parents=True)
    md_src = _FIXTURES_DIR / "synthetic-banded-contract.md"
    yml_src = _FIXTURES_DIR / "synthetic-banded-contract.yaml"
    md_target = ext_dir / "contract-draft.md"
    yml_target = ext_dir / "contract-draft.yaml"
    shutil.copy(md_src, md_target)
    shutil.copy(yml_src, yml_target)
    return md_target


def test_ratify_cli_enqueues_three_decisions(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    extraction_id = "synthetic-fixture-v0-1-8-c2"
    draft_md = _stage_fixture_into_extraction_dir(ws, extraction_id)

    rc = odd_main(
        [
            str(draft_md),
            "--ratify",
            "--pm-name",
            pm_name,
            "--workspace-root",
            str(ws),
        ]
    )
    assert rc == 0

    pm_queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    assert pm_queue_path.exists()
    queue_payload = yaml.safe_load(pm_queue_path.read_text(encoding="utf-8"))
    queue = queue_payload["queue"]
    assert len(queue) == 3
    provenances = [entry["provenance"] for entry in queue]
    assert any(f"odd-extract:{extraction_id}:AC.SYNTH.1" == p for p in provenances)
    assert any(f"odd-extract:{extraction_id}:AC.SYNTH.2" == p for p in provenances)
    assert any(f"odd-extract:{extraction_id}:AC.SYNTH.3" == p for p in provenances)


def test_ratify_cli_creates_ratification_state(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    extraction_id = "synthetic-fixture-v0-1-8-c2"
    draft_md = _stage_fixture_into_extraction_dir(ws, extraction_id)

    rc = odd_main(
        [
            str(draft_md),
            "--ratify",
            "--pm-name",
            pm_name,
            "--workspace-root",
            str(ws),
        ]
    )
    assert rc == 0

    rstate_path = (
        ws / ".loam" / "extractions" / extraction_id / "ratification-state.yaml"
    )
    assert rstate_path.exists()
    payload = yaml.safe_load(rstate_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["extraction_id"] == extraction_id
    assert payload["pm_handle"] == pm_name
    assert set(payload["pending_acs"]) == {
        "AC.SYNTH.1",
        "AC.SYNTH.2",
        "AC.SYNTH.3",
    }
    assert payload["completed_actions"] == []
    assert payload["in_flight_action"] is None


def test_ratify_cli_first_surfacing_returns_one_question(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """After the CLI enqueues, the PM's batch surface returns one
    question (max_questions_per_turn=1; FIFO head)."""
    from loam.per_project_pm import PMRuntime

    ws, pm_name = tmp_workspace_with_pm
    extraction_id = "synthetic-fixture-v0-1-8-c2"
    draft_md = _stage_fixture_into_extraction_dir(ws, extraction_id)

    rc = odd_main(
        [
            str(draft_md),
            "--ratify",
            "--pm-name",
            pm_name,
            "--workspace-root",
            str(ws),
        ]
    )
    assert rc == 0

    runtime = PMRuntime.from_workspace(ws, pm_name)
    batch = runtime.surface_next_questions_batch()
    assert len(batch) == 1
    sq = batch[0]
    # First-enqueued AC is AC.SYNTH.1 (FIFO)
    assert "AC.SYNTH.1" in sq.text
    assert "VERIFIED" in sq.text  # the AC's current band
    assert sq.provenance == f"odd-extract:{extraction_id}:AC.SYNTH.1"


def test_ratify_cli_missing_pm_name_exits_nonzero(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, _ = tmp_workspace_with_pm
    extraction_id = "synthetic-fixture-v0-1-8-c2"
    draft_md = _stage_fixture_into_extraction_dir(ws, extraction_id)

    rc = odd_main(
        [
            str(draft_md),
            "--ratify",
            # --pm-name omitted
            "--workspace-root",
            str(ws),
        ]
    )
    assert rc != 0


def test_ratify_cli_missing_draft_path_exits_nonzero(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm

    rc = odd_main(
        [
            "/nonexistent/path/to/draft.md",
            "--ratify",
            "--pm-name",
            pm_name,
            "--workspace-root",
            str(ws),
        ]
    )
    assert rc != 0


def test_ratify_cli_json_mode(
    tmp_workspace_with_pm: tuple[Path, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json mode emits machine-readable output."""
    import json as _json
    ws, pm_name = tmp_workspace_with_pm
    extraction_id = "synthetic-fixture-v0-1-8-c2"
    draft_md = _stage_fixture_into_extraction_dir(ws, extraction_id)

    rc = odd_main(
        [
            str(draft_md),
            "--ratify",
            "--pm-name",
            pm_name,
            "--workspace-root",
            str(ws),
            "--json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = _json.loads(out)
    assert payload["ratification"]["enqueued_count"] == 3
    assert payload["ratification"]["pm_handle"] == pm_name
    assert payload["ratification"]["extraction_id"] == extraction_id
    assert payload["ratification"]["total_acs"] == 3

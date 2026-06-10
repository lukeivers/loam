"""AC.GEN.1 (pipeline half) + AC.PRG.1/.2 wiring — deterministic e2e.

Drives `run_build_from_intent` end to end with injected deterministic
doubles (model dispatch, URL probe, build dispatcher) and pins:

  * the gate is authored DURING the run and hash-pinned BEFORE any
    build agent sees work (the build dispatcher asserts the frozen
    file already exists on disk when the first sub-agent runs, and
    that its brief carries neither the gate text nor a gate path);
  * tool, gate, and objective all come into existence during the run
    (the workspace starts empty; afterwards the gate dir, work dir,
    frozen pin, and run record all exist with content);
  * the stage updates flow in pipeline order with zero unverifiable
    narration claims (the after-the-fact audit passes);
  * the honest negative terminal flows through the same path.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import generative, grounding, request_intent  # noqa: E402
from handsoff_loop.build_from_intent import (  # noqa: E402
    run_build_from_intent,
)
from handsoff_loop.orchestrator import (  # noqa: E402
    clear_swarm_in_session_dispatcher,
    set_swarm_in_session_dispatcher,
)

_ASK = "tidy up the club's signup sheet so nobody is on it twice"


def _fake_llm(prompt, *, model="sonnet", timeout=0):
    if "intent-understanding" in prompt or "user typed\nthis ask" in prompt \
            or "intent-understanding step" in prompt \
            or "build pipeline. A user typed" in prompt:
        return {"result": json.dumps({
            "inferred_intent": "You want the signup sheet cleaned so "
                               "each person appears once.",
            "objective": f"derived in-run from: {_ASK}",
            "questions": [],
            "form_factor": "cli",
            "form_factor_plain": "A small command you run on the sheet.",
        })}
    if "domain-research step" in prompt:
        return {"result": json.dumps({
            "summary": "List hygiene is done with stable rules.",
            "norms": [{"norm": "Removed rows are reported, not "
                               "silently discarded.",
                       "source_url": "https://example.org/hygiene",
                       "source_title": "List Hygiene"}],
            "expert_gate_flags": [],
        })}
    if "design-generation step" in prompt:
        return {"result": json.dumps({
            "tool_plan": "A small script that cleans the sheet.",
            "data_shape": "Reads sheet.csv, writes sheet_clean.csv.",
            "gate_plain": "Done when the cleaned sheet lists each "
                          "person exactly once.",
            "gate_criteria": [
                {"criterion": "Removed rows are reported.",
                 "traceable_to": "N1"}],
            "gate_files": {
                "gate_zq.sh": "test -f cleaned.txt && grep -q ok "
                            "cleaned.txt\n",
                "held_out/marker.txt": "held out\n"},
            "check_command": "sh {gate_dir}/gate_zq.sh",
            "held_out_command": "sh {gate_dir}/gate_zq.sh",
            "sub_tasks": [{
                "name": "clean-sheet",
                "brief": "Create cleaned.txt containing the word ok "
                         "in the working directory.",
                "tighter_acceptance": "cleaned.txt exists"}],
            "judge_scope": "Checks the sample only.",
        })}
    raise AssertionError(f"unexpected dispatch: {prompt[:80]}")


@pytest.fixture()
def _doubles(monkeypatch, tmp_path):
    monkeypatch.setattr(request_intent, "_claude_json", _fake_llm)
    monkeypatch.setattr(grounding, "_claude_json", _fake_llm)
    monkeypatch.setattr(grounding, "_probe_url", lambda url: 200)
    monkeypatch.setattr(generative, "_claude_json", _fake_llm)
    yield tmp_path
    clear_swarm_in_session_dispatcher()


def test_freeze_lands_before_any_build_agent_and_all_born_in_run(_doubles):
    ws = _doubles / "fresh-ws"
    ws.mkdir()
    assert list(ws.iterdir()) == []  # nothing exists before the run

    observed = {}

    def _builder(prompt, *, timeout):
        run_dir = next((ws / "runs").iterdir())
        frozen = run_dir / "_frozen" / "bfi-gate.frozen"
        # The gate was frozen + hash-pinned BEFORE this first build
        # agent ran (AC.GEN.1).
        observed["frozen_existed_at_dispatch"] = frozen.exists()
        observed["sha_existed_at_dispatch"] = (
            run_dir / "_frozen" / "bfi-gate.sha256").exists()
        # The brief carries neither the gate text nor a gate path.
        observed["gate_unseen_by_brief"] = (
            "lists each person exactly once" not in prompt
            and "gate_zq.sh" not in prompt
            and "_frozen" not in prompt)
        (run_dir / "work" / "cleaned.txt").write_text("ok\n",
                                                      encoding="utf-8")
        return "built"

    set_swarm_in_session_dispatcher(_builder)
    said = []
    result = run_build_from_intent(
        _ASK, workspace_dir=ws, say=said.append,
        heartbeat_interval_s=0.05)

    assert observed == {"frozen_existed_at_dispatch": True,
                        "sha_existed_at_dispatch": True,
                        "gate_unseen_by_brief": True}
    assert result.terminal == "done"
    # Tool, gate, and objective all born during the run, on disk.
    run_dir = Path(result.run_dir)
    assert (run_dir / "work" / "cleaned.txt").exists()
    assert (run_dir / "gate" / "gate_zq.sh").exists()
    assert _ASK in result.intent.objective  # objective from THIS ask
    assert (run_dir / "run_summary.json").exists()


def test_stage_updates_flow_in_order_with_zero_unverifiable_claims(_doubles):
    ws = _doubles / "ws2"
    ws.mkdir()

    def _builder(prompt, *, timeout):
        run_dir = next((ws / "runs").iterdir())
        (run_dir / "work" / "cleaned.txt").write_text("ok\n",
                                                      encoding="utf-8")
        return "built"

    set_swarm_in_session_dispatcher(_builder)
    result = run_build_from_intent(
        _ASK, workspace_dir=ws, say=lambda s: None,
        heartbeat_interval_s=0.05)

    record = (Path(result.run_dir) / "run_record.jsonl").read_text(
        encoding="utf-8")
    events = [json.loads(ln) for ln in record.splitlines() if ln.strip()]
    stages = [e["stage"] for e in events if e.get("user_visible")]
    # Pipeline order, heartbeats aside.
    core = [s for s in stages if s != "heartbeat"]
    assert core[0] == "understanding"
    for a, b in (("understanding", "researching"),
                 ("researching", "planning"),
                 ("planning", "building"),
                 ("building", "checking"),
                 ("checking", "verdict")):
        assert core.index(a) < core.index(b)
    # AC.PRG.2: the audit found nothing unverifiable.
    assert result.progress_audit["unverifiable_claims"] == []
    assert result.progress_audit["n_user_visible"] >= 6


def test_honest_negative_flows_through_the_same_path(_doubles):
    ws = _doubles / "ws3"
    ws.mkdir()

    def _never_builds(prompt, *, timeout):
        return "tried"

    set_swarm_in_session_dispatcher(_never_builds)
    result = run_build_from_intent(
        _ASK, workspace_dir=ws, say=lambda s: None,
        max_refine_attempts=1, heartbeat_interval_s=0.05)
    assert result.terminal == "honest-negative"
    assert result.verdict_text.startswith("Not done")
    assert "What was checked, honestly" in result.verdict_text

"""AC.SMK.3 (+ the AC.SMK.2 identical-path structure) — the run log.

  * the run log is a room-ready artifact: every number carries its
    run-of-origin (the entry names the ask verbatim, the archetype,
    the workspace, the loam commit, the timestamp), and every entry
    embeds the one documented command that reproduces it;
  * an honest negative is logged exactly like a pass (fails-included
    is the format's contract, not an editorial choice);
  * AC.SMK.2's structural half: the harness has NO per-archetype
    branching — back-office trio and off-vertical probes flow through
    the IDENTICAL underlying command (the archetype is a label, never
    a code path), so the documented "one more case" command serves a
    prompt no builder has seen.

The executed-run halves of AC.SMK.1/.2 are the logged runs themselves
(smoke/RUN_LOG.md), produced by this harness.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

_SMOKE = Path(__file__).resolve().parents[1] / "smoke"
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_spec = importlib.util.spec_from_file_location(
    "run_smoke", _SMOKE / "run_smoke.py")
run_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_smoke)


def _entry(terminal="done"):
    return run_smoke.format_log_entry(
        archetype="app1-class",
        ask="match the things up for me",
        workspace="/tmp/ws-xyz",
        loam_commit="abc1234",
        started="2026-06-09 21:00:00",
        wall_clock_s=812.4,
        terminal=terminal,
        summary={
            "grounding": {"grounded": True, "norms": [1, 2, 3],
                          "dropped_citations": [],
                          "expert_gate_flags": ["needs an expert"]},
            "design": {"gate_criteria": [
                {"criterion": "a", "traceable_to": "N1"},
                {"criterion": "b", "traceable_to": ""}]},
            "convergence": {"stop_reason": terminal == "done" and "done"
                            or "attempt-bound",
                            "refine_attempts": 1, "timed_out": False,
                            "timeout_retries": 0},
            "progress_audit": {"n_user_visible": 14, "max_gap_s": 61.0,
                               "gap_within_bound": True,
                               "unverifiable_claims": []},
            "intent": {"questions": ["which column?"]},
            "answers": {},
        },
        entry_command="PYTHONPATH=/x python3.13 -m handsoff_loop.cli "
                      "build-from-intent --ask 'match the things up "
                      "for me' --workspace /tmp/ws-xyz --yes",
    )


def test_every_number_carries_run_of_origin():
    entry = _entry()
    # The entry header IS the run of origin: archetype, commit,
    # workspace, timestamp, verbatim ask.
    assert "app1-class" in entry
    assert "loam commit `abc1234`" in entry
    assert "workspace `/tmp/ws-xyz`" in entry
    assert "ask (verbatim): match the things up for me" in entry
    # Numbers are explicitly scoped to this run.
    assert "wall-clock: 812.4s [this run]" in entry
    assert entry.count("[this run]") >= 4


def test_reproduce_command_is_embedded_verbatim():
    entry = _entry()
    assert "reproduce this run:" in entry
    assert "build-from-intent --ask 'match the things up" in entry


def test_honest_negative_logged_like_a_pass():
    neg = _entry(terminal="honest-negative")
    assert "terminal: **honest-negative**" in neg
    assert "fails included by contract" in neg
    # Same fields, same format — no softening, no omission.
    pos = _entry()
    assert neg.count("[this run]") == pos.count("[this run]")


def test_human_gates_are_named_per_run():
    entry = _entry()
    assert "question (unanswered): which column?" in entry
    assert "expert-gate flag: needs an expert" in entry


def test_no_per_archetype_branching_in_the_harness():
    """AC.SMK.2 structure: the archetype is a LABEL — no code path in
    the harness conditions on it (AST sweep: no If/While/comparison
    touches the archetype value)."""
    tree = ast.parse((_SMOKE / "run_smoke.py").read_text(
        encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While)):
            for sub in ast.walk(node.test):
                if isinstance(sub, ast.Name) and sub.id == "archetype":
                    offenders.append(ast.dump(node.test))
                if (isinstance(sub, ast.Attribute)
                        and sub.attr == "archetype"):
                    offenders.append(ast.dump(node.test))
    assert offenders == [], (
        f"harness branches on the archetype: {offenders}")


def test_trio_and_off_vertical_prompts_present_and_plain():
    # The trio prompt files exist (the executed runs log against them)
    for name in ("app1-reconciliation", "app3-customer-dedupe",
                 "app2-books-migration"):
        p = _SMOKE / "prompts" / f"{name}.txt"
        assert p.exists(), f"missing trio prompt {name}"
        text = p.read_text(encoding="utf-8")
        assert len(text.split()) > 20  # a real ask, not a stub

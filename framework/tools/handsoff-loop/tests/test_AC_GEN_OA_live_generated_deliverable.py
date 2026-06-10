"""AC.GEN.OA (outcome-altitude: true) — the corrected June-8 demo.

On a FRESH workspace through the production entry point with NO
pre-arranged state, an unseen vague ask yields a working generated
deliverable that passes its own loam-authored frozen gate — with
on-disk evidence (mtimes against the run-start clock) that tool,
gate, and objective all came into existence DURING the run — or a
definite, evidence-named honest negative.

Shares the single session live run (conftest.live_bfi_run; env-gated
BFI_REAL_CLAUDE=1).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_deliverable_gate_and_objective_born_during_the_run(live_bfi_run):
    result = live_bfi_run["result"]
    t_start = live_bfi_run["t_start"]
    run_dir = Path(result.run_dir)

    # Terminal is one of the two honest terminals only.
    assert result.terminal in ("done", "honest-negative"), (
        f"pipeline failure, not an honest terminal: {result.terminal}")

    # The objective derives from THIS run's ask (echoes its specifics).
    lowered = result.intent.objective.lower()
    assert any(t in lowered for t in ("schedul", "team", "league")), (
        f"objective does not carry the ask's specifics: {lowered!r}")

    # Born-in-run evidence: the frozen gate pin and every gate
    # artifact have mtimes AFTER the run started on a workspace that
    # did not exist before it.
    frozen = run_dir / "_frozen" / "bfi-gate.frozen"
    assert frozen.exists()
    assert frozen.stat().st_mtime >= t_start - 1
    gate_files = [p for p in (run_dir / "gate").rglob("*") if p.is_file()]
    assert gate_files, "no generated gate artifacts on disk"
    assert all(p.stat().st_mtime >= t_start - 1 for p in gate_files)

    if result.terminal == "done":
        # A working generated deliverable exists in the work dir,
        # born in-run, and it passed the loam-authored frozen gate.
        work_files = [p for p in (run_dir / "work").rglob("*")
                      if p.is_file()]
        assert work_files, "done verdict but no deliverable on disk"
        assert all(p.stat().st_mtime >= t_start - 1
                   for p in work_files)
        assert result.convergence.result.final_verify.done is True
    else:
        # The honest negative is definite and evidence-named.
        assert result.convergence is not None
        assert result.convergence.stop_reason in (
            "attempt-bound", "cost-ceiling", "wall-ceiling",
            "leg-timeout")
        assert "Not done" in result.verdict_text

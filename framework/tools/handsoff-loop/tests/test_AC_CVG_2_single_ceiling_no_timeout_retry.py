"""AC.CVG.2 — single generous leg ceiling; timeout terminal; NO retry.

The #111 empirical lesson, binding:

  * each agent leg runs under a single named generous ceiling (the
    ceiling value is a named tunable: DEFAULT_LEG_CEILING_S);
  * a timeout is TERMINAL for that leg with the state honestly
    recorded — the forced-timeout probe counts dispatch attempts and
    requires EXACTLY ONE (zero retries);
  * the no-retry evidence is observable in every result
    (timeout_retries is structurally 0, recorded, never silent).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.convergence import (  # noqa: E402
    DEFAULT_LEG_CEILING_S,
    run_to_convergence,
)
from handsoff_loop.orchestrator import (  # noqa: E402
    SubTask,
    clear_swarm_in_session_dispatcher,
    set_swarm_in_session_dispatcher,
)
from handsoff_loop.verify import freeze_acceptance  # noqa: E402


def test_ceiling_is_a_named_generous_tunable():
    # ~1200s-class (the empirically proven band) and tunable per call.
    assert DEFAULT_LEG_CEILING_S >= 1200


def test_forced_timeout_terminates_leg_with_zero_retries(tmp_path):
    (tmp_path / "work").mkdir()
    attempts = []

    def _slow_agent(prompt, *, timeout):
        attempts.append(1)
        raise subprocess.TimeoutExpired(cmd=["fake-leg"], timeout=timeout)

    frozen = freeze_acceptance(
        acceptance_id="t", content="done content",
        check_argv=["/bin/sh", "-c", "false"],
        freeze_dir=tmp_path / "_frozen")

    set_swarm_in_session_dispatcher(_slow_agent)
    try:
        res = run_to_convergence(
            objective="anything",
            sub_tasks=[SubTask(name="t", brief="b",
                               tighter_acceptance="a",
                               check_command="true")],
            frozen=frozen,
            work_dir=tmp_path / "work",
            artifact_dir=tmp_path / "artifacts",
            leg_ceiling_s=7.0,
            max_refine_attempts=5,  # bound present — yet NOT spent on timeout
            behavioral_done=False,
        )
    finally:
        clear_swarm_in_session_dispatcher()

    # EXACTLY one dispatch attempt: timeout is terminal, never retried
    # (even with refine attempts available).
    assert attempts == [1]
    assert res.timed_out is True
    assert res.reached_done is False
    assert res.stop_reason == "leg-timeout"
    assert res.timeout_retries == 0
    # The state is honestly recorded, ceiling named.
    assert res.timeout_state["ceiling_s"] == 7.0
    assert "never auto-retried" in res.timeout_state["note"]
    ev = res.as_evidence()
    assert ev["timed_out"] is True and ev["timeout_retries"] == 0


def test_no_retry_on_timeout_path_exists_in_source():
    """Structural sweep: the convergence module's timeout handler
    contains no dispatch loop — `run_handsoff_loop` is called exactly
    once in the module source, and the TimeoutExpired handler returns
    directly."""
    src = (Path(_SRC) / "handsoff_loop" / "convergence.py").read_text(
        encoding="utf-8")
    assert src.count("run_handsoff_loop(") == 1  # exactly one call site
    handler = src.split("except subprocess.TimeoutExpired", 1)[1]
    assert "run_handsoff_loop" not in handler.split("return ConvergenceResult")[0]

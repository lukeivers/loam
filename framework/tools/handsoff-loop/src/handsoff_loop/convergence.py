"""Build-to-convergence as canonical default (S4 — AC.CVG.*).

The sealed bounded re-drive (``orchestrator.run_handsoff_loop`` with
``max_refine_attempts``) IS convergence machinery already in canonical
loam.  This module makes it the DEFAULT behavior of the general
build-from-intent path and adds the two empirically-learned
disciplines the prior art proved binding:

  * **Single generous leg ceiling, NO retry-on-timeout** (AC.CVG.2 —
    the #111 lesson): each agent leg runs under one named generous
    ceiling (:data:`DEFAULT_LEG_CEILING_S`, a named tunable); a
    timeout is TERMINAL for the run with the state honestly recorded —
    retrying a slow-but-working agent doubles the wait, so no retry
    path exists here, structurally.
  * **Own-the-wait** (AC.CVG.3): while a build leg is in flight the
    dispatching side tracks liveness from RUN ARTIFACTS (newest
    artifact mtime — artifact-probe-class evidence, never
    poller-cadence inference); :func:`probe_liveness` is the probe and
    its results feed the S5 progress surface.

Convergence terminals (AC.CVG.1): gate-pass and definite honest
negative ONLY.  A failed check re-drives bounded refinement carrying
the failure context (the sealed spine's contract); there is no
retry-to-green and no retry-on-timeout.  The honest negative is
first-class, never softened.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .orchestrator import HandsoffResult, SubTask, run_handsoff_loop
from .verify import FrozenAcceptance

# The single generous per-leg wall-clock ceiling (seconds) — the #111
# empirical lesson: one generous ceiling, terminal on expiry, NEVER an
# automatic retry. A named tunable (callers may widen it for genuinely
# long builds); the NO-RETRY rule is not tunable.
DEFAULT_LEG_CEILING_S = 1200

# Convergence is the default: the bounded re-drive runs unless a
# caller explicitly narrows it. Finite by construction.
DEFAULT_MAX_REFINE_ATTEMPTS = 3


@dataclass(frozen=True)
class ConvergenceResult:
    """One converged (or honestly-terminal) build leg outcome.

    ``timed_out`` True means the leg hit the single ceiling and the
    run ended THERE: ``timeout_retries`` is structurally always 0 —
    the field exists so the no-retry discipline is observable in
    every run record, not a silent property.  ``result`` is the
    underlying spine outcome when the run completed (None on
    timeout).  ``stop_reason`` ∈ {"done", "attempt-bound",
    "cost-ceiling", "wall-ceiling", "leg-timeout"}.
    """

    reached_done: bool
    stop_reason: str
    timed_out: bool = False
    timeout_retries: int = 0  # ALWAYS 0 — observable no-retry evidence
    leg_ceiling_s: float = DEFAULT_LEG_CEILING_S
    wall_clock_s: float = 0.0
    timeout_state: dict = field(default_factory=dict)
    result: HandsoffResult | None = None

    def as_evidence(self) -> dict:
        return {
            "reached_done": self.reached_done,
            "stop_reason": self.stop_reason,
            "timed_out": self.timed_out,
            "timeout_retries": self.timeout_retries,
            "leg_ceiling_s": self.leg_ceiling_s,
            "wall_clock_s": self.wall_clock_s,
            "timeout_state": dict(self.timeout_state),
            "refine_attempts": (
                self.result.refine_attempts if self.result else 0),
            "refine_log": (
                list(self.result.refine_log) if self.result else []),
        }


def run_to_convergence(
    *,
    objective: str,
    sub_tasks: list[SubTask],
    frozen: FrozenAcceptance,
    work_dir: Path,
    artifact_dir: Path,
    leg_ceiling_s: float = DEFAULT_LEG_CEILING_S,
    max_refine_attempts: int = DEFAULT_MAX_REFINE_ATTEMPTS,
    behavioral_done: bool = True,
    verify_timeout: int = 120,
    wall_ceiling_s: float | None = None,
    cost_ceiling_usd: float | None = None,
) -> ConvergenceResult:
    """Drive a build leg to convergence — the canonical default (AC.CVG.1).

    Composes the sealed spine: bounded verification-gated re-drive ON
    by default (``max_refine_attempts`` defaults > 0), behavioural
    self-check ON by default, gate-pass / honest-negative the only
    terminals.  AC.CVG.2: a leg timeout under the single ceiling is
    caught HERE, recorded honestly, and is TERMINAL — this function
    contains no loop, no recursion, and no second dispatch on the
    timeout path (the forced-timeout AC test counts dispatch attempts).
    """
    t0 = time.monotonic()
    try:
        result = run_handsoff_loop(
            objective=objective,
            sub_tasks=sub_tasks,
            frozen=frozen,
            work_dir=work_dir,
            artifact_dir=artifact_dir,
            per_subtask_timeout=int(leg_ceiling_s),
            verify_timeout=verify_timeout,
            behavioral_done=behavioral_done,
            max_refine_attempts=max_refine_attempts,
            wall_ceiling_s=wall_ceiling_s,
            cost_ceiling_usd=cost_ceiling_usd,
        )
    except subprocess.TimeoutExpired as exc:
        # The #111 discipline: terminal, honest, ZERO retries.
        return ConvergenceResult(
            reached_done=False,
            stop_reason="leg-timeout",
            timed_out=True,
            timeout_retries=0,
            leg_ceiling_s=leg_ceiling_s,
            wall_clock_s=round(time.monotonic() - t0, 2),
            timeout_state={
                "ceiling_s": leg_ceiling_s,
                "cmd": " ".join(str(c) for c in (exc.cmd or []))[:300]
                if isinstance(exc.cmd, (list, tuple)) else str(exc.cmd)[:300],
                "note": (
                    "leg hit the single generous ceiling; per the "
                    "no-retry-on-timeout discipline this run ends here "
                    "with its state recorded — it is never auto-retried"
                ),
            },
        )
    return ConvergenceResult(
        reached_done=result.reached_done,
        stop_reason=result.refine_stop_reason,
        timed_out=False,
        timeout_retries=0,
        leg_ceiling_s=leg_ceiling_s,
        wall_clock_s=round(time.monotonic() - t0, 2),
        result=result,
    )


def probe_liveness(run_dir: Path, *, stale_after_s: float = 300.0) -> dict:
    """Own-the-wait liveness from run ARTIFACTS (AC.CVG.3).

    Artifact-probe-class evidence: scans the run dir for the newest
    file mtime and reports how long ago real work last touched disk.
    Never infers liveness from poller cadence or self-reports.  The
    returned dict is a progress state the S5 surface consumes.
    """
    run_dir = Path(run_dir)
    newest: tuple[float, str] | None = None
    if run_dir.exists():
        for p in run_dir.rglob("*"):
            if p.is_file():
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if newest is None or mt > newest[0]:
                    newest = (mt, str(p))
    now = time.time()
    if newest is None:
        return {"alive": False, "evidence": "no run artifacts on disk",
                "newest_artifact": "", "artifact_age_s": None,
                "probed_at": now}
    age = now - newest[0]
    return {
        "alive": age <= stale_after_s,
        "evidence": f"newest artifact mtime {round(age, 1)}s ago",
        "newest_artifact": newest[1],
        "artifact_age_s": round(age, 1),
        "probed_at": now,
    }

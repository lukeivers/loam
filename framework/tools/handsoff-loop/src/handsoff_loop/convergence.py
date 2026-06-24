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

import json
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
        "newest_mtime": newest[0],
        "probed_at": now,
    }


def probe_progress(
    run_dir: Path,
    *,
    prev: dict | None = None,
    run_record_path: Path | None = None,
    stale_after_s: float = 300.0,
) -> dict:
    """Cross-beat PROGRESS (not bare liveness) from run ARTIFACTS (AC.HB.2).

    ``probe_liveness`` answers "is anything fresh?" (LIVENESS — newest
    artifact age).  This answers the distinct question "did something
    NEW land since the last time I looked?" (PROGRESS), which is what
    the heartbeat needs to tell "moving" from "stuck" (SAL-HB-2).

    Progress is the DELTA between consecutive probes, measured two ways
    (D-5 — either is sufficient): the newest-artifact mtime ADVANCED, OR
    the run record gained ≥1 line.  ``prev`` is the prior return of this
    function (None on the first beat — the first beat reports
    ``progressed_since_last=None``, neither progress nor stall, since
    there is no prior state to delta against).  ``run_record_path`` is
    the run record whose line-count growth is the second progress
    signal; when omitted, only the mtime-advance signal is used.

    Honors ``feedback_dead_agent_detection_via_artifact_probe`` by
    construction: the delta is computed from disk artifacts (mtime,
    run-record line count), never from poller cadence or a self-report.

    Self-narration is NOT progress.  The heartbeat writes its own beats
    to the run record inside ``run_dir``; counting that churn as build
    progress would mask every stall (the beat that asks "did anything
    move?" would itself look like movement).  So the newest-artifact
    scan EXCLUDES ``run_record_path``, and the run-record line signal
    counts only build-meaningful events — ``heartbeat``-stage lines (the
    beats themselves) are excluded.
    """
    run_dir = Path(run_dir)
    record_path = Path(run_record_path) if run_record_path is not None else None
    state = probe_liveness(run_dir, stale_after_s=stale_after_s)

    # Newest BUILD-ARTIFACT mtime, excluding the run record's own churn.
    newest_mt: float | None = None
    newest_name = ""
    if run_dir.exists():
        for p in run_dir.rglob("*"):
            if not p.is_file():
                continue
            if record_path is not None and p.resolve() == record_path.resolve():
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if newest_mt is None or mt > newest_mt:
                newest_mt = mt
                newest_name = str(p)
    state["progress_mtime"] = newest_mt
    state["progress_artifact"] = newest_name

    # Build-meaningful run-record lines (heartbeat beats excluded).
    record_lines = 0
    if record_path is not None and record_path.exists():
        try:
            for ln in record_path.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    ev = json.loads(ln)
                except ValueError:
                    record_lines += 1
                    continue
                if ev.get("stage") != "heartbeat":
                    record_lines += 1
        except OSError:
            record_lines = 0
    state["record_lines"] = record_lines

    if prev is None:
        state["progressed_since_last"] = None
        state["stall_beats"] = 0
        state["progress_evidence"] = "first probe — no prior state to compare"
        return state

    prev_mt = prev.get("progress_mtime")
    # Progress on the artifact axis: the newest build artifact's mtime
    # advanced, OR a build artifact appeared where there was none.
    mtime_advanced = (
        newest_mt is not None
        and (prev_mt is None or newest_mt > prev_mt))
    record_grew = record_lines > prev.get("record_lines", 0)
    progressed = bool(mtime_advanced or record_grew)
    state["progressed_since_last"] = progressed
    # Consecutive non-progressing beats accrue toward a stall; any
    # progress resets the counter.
    state["stall_beats"] = 0 if progressed else prev.get("stall_beats", 0) + 1
    if progressed:
        bits = []
        if mtime_advanced:
            bits.append("a newer artifact landed")
        if record_grew:
            bits.append("the run record gained a line")
        state["progress_evidence"] = " and ".join(bits)
    else:
        state["progress_evidence"] = (
            "no new artifact and no new run-record line since the last "
            f"check ({state['stall_beats']} consecutive)")
    return state

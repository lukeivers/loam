"""The packaged orchestrator (AC.A.1) — composes the proven loop.

AC.FOUND.0 (fence guard): the decompose -> scoped-dispatch ->
independent-judge -> frozen-verify loop is taken as ESTABLISHED by
the Tier-0 probe.  This module COMPOSES that mechanism into a
packaged, persona-invocable capability.  It contains NO step that
re-proves the core loop at unit scale — the only things it adds are
the PACKAGING (so the persona invokes one capability, not a
hand-driven orchestrator) and the structural carry-through of the
honesty controls (frozen-unseen done + independent + anti-overfit
verify) that the probe hand-added.

AC.A.1 — invocable by the persona as one capability: `run_handsoff_loop`
         is the single entry point; `cli.py` exposes it; the SKILL
         bundle delegates to it.  No human hand-drives decompose /
         dispatch / judge.

AC.A.4 / AC.B.5 — `PhaseVerdict` is the per-dimension verdict-table
         structure.  A definite NEGATIVE verdict is a first-class
         valid outcome: `PhaseVerdict.passed_as_deliverable` is True
         whenever the table is DEFINITE and evidence-backed,
         regardless of whether the dimensions came back positive or
         negative.  There is deliberately no retry-to-green path.

NO Anthropic API key — sub-agents are real `claude -p` subprocesses
via goal_drive.build_goal_drive_argv, default Sonnet.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .goal_drive import (
    DONE_SENTINEL,
    GoalDriveSpec,
    build_goal_drive_argv,
)
from .verify import FrozenAcceptance, VerifyResult, verify


@dataclass(frozen=True)
class SubTask:
    """One scoped sub-task with a strictly-tighter acceptance.

    The probe-validated unit shape (NOT re-defined here — AC.FOUND.0;
    D-UNIT keeps the USER-facing unit the whole objective, sub-tasks
    internal).  `brief` never contains the frozen acceptance (the
    isolation is asserted in `run_handsoff_loop`).
    """

    name: str
    brief: str
    tighter_acceptance: str
    check_command: str


@dataclass
class PhaseVerdict:
    """A definite per-dimension verdict table (AC.A.4 / AC.B.5).

    `dimensions` maps a named orthogonal dimension to
    (verdict: bool, evidence: str).  `passed_as_deliverable` is True
    iff the table is DEFINITE and evidence-backed — true for EITHER
    polarity.  `polarity` is "positive" (all dims true) or "negative"
    (>=1 dim false); a negative is plan-success, reported straight,
    never retried.  `failure_class` is set on negative (D-NEG-DEPTH:
    class + evidence only, no root-cause / fix).
    """

    phase: str
    dimensions: dict[str, tuple[bool, str]] = field(default_factory=dict)
    definite: bool = False
    failure_class: str = ""

    @property
    def polarity(self) -> str:
        if not self.dimensions:
            return "indeterminate"
        return ("positive"
                if all(v for v, _ in self.dimensions.values())
                else "negative")

    @property
    def passed_as_deliverable(self) -> bool:
        # A definite, evidence-backed table is a plan deliverable for
        # EITHER polarity.  This property is intentionally polarity-
        # blind: there is no green-only success path.
        return self.definite and bool(self.dimensions) and all(
            isinstance(e, str) and e.strip()
            for _, e in self.dimensions.values()
        )

    def as_table(self) -> dict:
        return {
            "phase": self.phase,
            "polarity": self.polarity,
            "definite": self.definite,
            "passed_as_deliverable": self.passed_as_deliverable,
            "failure_class": self.failure_class,
            "dimensions": {
                k: {"verdict": v, "evidence": e}
                for k, (v, e) in self.dimensions.items()
            },
        }


@dataclass
class HandsoffResult:
    """Outcome of one packaged hands-off loop run."""

    reached_done: bool
    sub_task_results: list[dict]
    final_verify: VerifyResult | None
    cost_usd: float | None
    wall_clock_s: float
    human_loop_driving: bool  # MUST be False for AC.A.4(i)
    transcript_paths: list[str] = field(default_factory=list)


def _dispatch_subagent(
    spec: GoalDriveSpec,
    *,
    work_dir: Path,
    timeout: int,
) -> tuple[str, float, float | None]:
    """Run ONE real /goal-driven `claude -p` sub-agent.

    No human drives the loop — `/goal` (inside the prompt) keeps
    Claude taking turns until the surfaced-exit-code condition holds.
    Returns (transcript, wall_clock_s, cost_usd|None).  Cost is
    MEASURED from the --output-format json envelope (D-COST-BAND).
    """
    argv = build_goal_drive_argv(spec, cost_json=True)
    t0 = time.monotonic()
    proc = subprocess.run(
        argv, cwd=str(work_dir),
        capture_output=True, text=True, timeout=timeout,
    )
    dt = time.monotonic() - t0
    out = proc.stdout or ""
    cost: float | None = None
    try:
        env = json.loads(out)
        if isinstance(env, dict):
            cost = env.get("total_cost_usd")
    except json.JSONDecodeError:
        pass
    return out + "\n" + (proc.stderr or ""), dt, cost


def run_handsoff_loop(
    *,
    objective: str,
    sub_tasks: list[SubTask],
    frozen: FrozenAcceptance,
    work_dir: Path,
    artifact_dir: Path,
    per_subtask_timeout: int = 1200,
    verify_timeout: int = 120,
) -> HandsoffResult:
    """Drive the packaged loop on a real task (AC.A.1).

    Composes the probe-proven decompose->dispatch->judge mechanism
    (AC.FOUND.0 — NOT re-proved): each scoped sub-task is dispatched
    to a real /goal-driven `claude -p` sub-agent (no human driving
    the loop); after the loop, loam's INDEPENDENT tool-executing
    check + anti-overfit check (verify.py) decides "done" — the
    sub-agents' self-reports are never trusted.

    AC.A.2 isolation is asserted up front: the frozen acceptance must
    not appear in ANY sub-task brief.  A breach raises (refusing is
    honest; silently continuing destroys the Tier-0 control).
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # AC.A.2 structural guard: frozen acceptance unseen by any brief.
    frozen.assert_unseen_by(*[st.brief for st in sub_tasks],
                            *[st.tighter_acceptance for st in sub_tasks])

    t0 = time.monotonic()
    total_cost: float | None = 0.0
    results: list[dict] = []
    transcript_paths: list[str] = []

    for i, st in enumerate(sub_tasks):
        spec = GoalDriveSpec(
            directive=(
                f"Scoped sub-task {st.name} of objective: {objective}\n\n"
                f"{st.brief}\n\n"
                f"Acceptance for THIS sub-task (tighter than the whole): "
                f"{st.tighter_acceptance}"
            ),
            check_command=st.check_command,
        )
        transcript, dt, cost = _dispatch_subagent(
            spec, work_dir=work_dir, timeout=per_subtask_timeout
        )
        tp = artifact_dir / f"sub_{i}_{st.name}.transcript"
        tp.write_text(transcript, encoding="utf-8")
        transcript_paths.append(str(tp))
        if cost is not None and total_cost is not None:
            total_cost += cost
        elif cost is None:
            total_cost = None  # measurement gap -> honest None
        results.append({
            "name": st.name,
            "wall_clock_s": round(dt, 2),
            "cost_usd": cost,
            "self_report_done": DONE_SENTINEL in transcript,
        })

    # loam's INDEPENDENT check decides — NOT the self-reports above.
    final = verify(frozen, work_dir=work_dir, timeout=verify_timeout)
    (artifact_dir / "final_verify.json").write_text(
        json.dumps(final.as_evidence(), indent=2), encoding="utf-8"
    )

    return HandsoffResult(
        reached_done=final.done,
        sub_task_results=results,
        final_verify=final,
        cost_usd=total_cost,
        wall_clock_s=round(time.monotonic() - t0, 2),
        human_loop_driving=False,  # /goal drove; no human in the loop
        transcript_paths=transcript_paths,
    )

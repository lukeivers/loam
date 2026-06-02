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

NO Anthropic API key — sub-agents stay subscription-routed (the host
session's own auth for the in-session path; the keychain-stored
subscription credential for the residual `claude -p` path).

IN-SESSION SUBAGENT CONVERSION (AC.SWARM.* — in-session-subagent-
migration minor, Slice 2). The leaf dispatch (`_dispatch_subagent`)
fans out the per-sub-task `/goal`-driven work as an IN-SESSION subagent
(the Task primitive) through a host-session-registered dispatcher
callable (`set_swarm_in_session_dispatcher`), NOT a detached
`claude -p` subprocess. In-session subagents are accounted against the
subscription plan limits — NOT the post-June-15 metered Agent SDK
credit a detached `claude -p` would draw from — and share the parent's
MCP, so they never re-load the Telegram plugin and cannot SIGTERM-steal
the operator's bot-poller slot. The RESIDUAL `claude -p` path (via
goal_drive.build_goal_drive_argv + `_isolation`) STAYS for the
launchd-sessionless case that has no living parent session to fan an
in-session subagent from; `loam_spawn_isolation`'s scope narrows to
residual-only (do NOT delete it — the residual path still needs it).
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ._isolation import isolated_env
from .behavioral_selfcheck import (
    BehavioralCheckSpec,
    build_behavioral_check_command,
)
from .goal_drive import (
    DONE_SENTINEL,
    GoalDriveSpec,
    build_goal_drive_argv,
)
from .verify import FrozenAcceptance, VerifyResult, verify


# === In-session subagent dispatch seam (AC.SWARM.1) ==========================
#
# The standalone Python orchestrator is NOT itself a Claude session — it cannot
# import the Task primitive directly. The LIVE host session that invokes the
# handsoff loop (the only context with the Task tool) registers a dispatcher
# callable here; `_dispatch_subagent` resolves it at call time. A registry (vs
# threading a dispatcher arg through run_handsoff_loop -> _run_subtask_pass ->
# _dispatch_subagent) keeps every pre-existing caller/test byte-behaviour-
# unchanged. A registered dispatcher is accounted against the subscription plan
# limits (in-session subagent billing), NOT the post-June-15 metered Agent SDK
# credit a detached `claude -p` would draw from — the whole motive of this
# slice. Mirrors Slice 1's deep_role_research_provider seam.
#
# The dispatcher takes the `/goal`-driven sub-task prompt (`spec.prompt()`) +
# the per-sub-task timeout and returns the in-session subagent's raw transcript
# TEXT (the same text the residual `-p` path's stdout+stderr would carry — the
# DONE_SENTINEL detection downstream is unchanged). No dispatcher registered ->
# the orchestrator falls through to the residual `-p` path (the natural degrade,
# preserving the sealed behaviour for the launchd-sessionless case).

SwarmInSessionDispatcher = Callable[..., str]

_swarm_in_session_dispatcher: SwarmInSessionDispatcher | None = None


def set_swarm_in_session_dispatcher(dispatcher: SwarmInSessionDispatcher) -> None:
    """Register the live host session's in-session swarm-subagent dispatcher.

    Called by the live Claude Code session that invokes the handsoff loop: it
    passes a callable ``(prompt: str, *, timeout: int) -> str`` that fans out an
    in-session subagent (the Task primitive) with that prompt and returns the
    subagent's raw transcript text. ``_dispatch_subagent`` resolves this at call
    time so no orchestrator call site has to thread the dispatcher through.
    """
    global _swarm_in_session_dispatcher
    _swarm_in_session_dispatcher = dispatcher


def get_swarm_in_session_dispatcher() -> SwarmInSessionDispatcher | None:
    """Return the registered in-session swarm dispatcher, or ``None`` if none."""
    return _swarm_in_session_dispatcher


def clear_swarm_in_session_dispatcher() -> None:
    """Unregister the swarm dispatcher (test hygiene + session teardown)."""
    global _swarm_in_session_dispatcher
    _swarm_in_session_dispatcher = None


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
    # AC.BRC.2/.3/.5 — the bounded behavioural-refine cycle's
    # observable evidence.  `refine_attempts` is how many EXTRA
    # re-drives ran after the first dispatch (0 == done on the first
    # pass, no re-drive needed — a healthy outcome, NOT a failure).
    # `refine_bound` is the explicit finite attempt cap.
    # `refine_stop_reason` ∈ {"done", "attempt-bound", "cost-ceiling",
    # "wall-ceiling"} names WHY the cycle stopped (honest-negative on
    # any non-"done" — a first-class plan-success outcome, NEVER
    # retried-to-green).  `refine_log` carries each iteration's
    # verification result so progress was accepted ONLY on a check
    # result, never on a sub-agent self-report (AC.BRC.3 anti-erosion
    # — the gate is observable in this log, not a footnote).
    refine_attempts: int = 0
    refine_bound: int = 0
    refine_stop_reason: str = "done"
    refine_log: list[dict] = field(default_factory=list)
    behavioral_gated: bool = False


def _dispatch_subagent(
    spec: GoalDriveSpec,
    *,
    work_dir: Path,
    timeout: int,
) -> tuple[str, float, float | None]:
    """Run ONE /goal-driven sub-agent — in-session by default (AC.SWARM.1).

    No human drives the loop — `/goal` (inside the prompt) keeps
    Claude taking turns until the surfaced-exit-code condition holds.
    Returns (transcript, wall_clock_s, cost_usd|None).

    IN-SESSION PATH (the production default — AC.SWARM.1). When the live
    host session has registered a swarm dispatcher
    (`set_swarm_in_session_dispatcher`), the per-sub-task `/goal`-driven
    prompt (`spec.prompt()`) is dispatched as an IN-SESSION subagent (the
    Task primitive) and its raw transcript returned.  This path spawns NO
    detached `claude -p` subprocess, touches NEITHER `subprocess.run` NOR
    the `_isolation` chokepoint (there is no subprocess argv to isolate —
    in-session subagents share the parent's MCP, so the Telegram kill
    vector the isolation guards does not exist here), and reaches no
    Anthropic SDK / `ANTHROPIC_API_KEY` (the host session is subscription-
    routed).  `cost_usd` is an honest `None` on this path: in-session
    subagents have no per-call `claude -p --output-format json` envelope to
    read `total_cost_usd` from — the plan-level cost signal moves to the
    `/usage` read (AC.SWARM.4; the honest-None fold is already in the spine
    via `_run_subtask_pass`).  This is NOT a regression — fabricating a
    per-call cost would be the dishonesty.

    RESIDUAL `claude -p` PATH (no dispatcher registered — the launchd-
    sessionless case with no living parent session to fan an in-session
    subagent from).  `build_goal_drive_argv` returns an argv already
    carrying the empty-strict-MCP isolation (AC.TPI.3); this consumer owns
    the spawn env and scrubs the bot-token / API-key spellings via
    `_isolation` (so this sub-agent `claude` can neither load the telegram
    plugin nor steal the operator's single-consumer poller slot — closing
    both halves of the verified kill vector).  `loam_spawn_isolation`'s
    scope is RESIDUAL-ONLY now; it is NOT deleted (the residual path still
    needs it — do NOT "clean up" a still-load-bearing guard).  Cost is
    MEASURED from the `--output-format json` envelope (D-COST-BAND).
    """
    dispatcher = get_swarm_in_session_dispatcher()
    if dispatcher is not None:
        # In-session subagent fan-out (AC.SWARM.1): the SAME `/goal`-driven
        # prompt the residual path would build, dispatched through the host-
        # registered Task-primitive callable.  No subprocess; no `-p`
        # envelope -> honest cost_usd=None (AC.SWARM.4).
        t0 = time.monotonic()
        transcript = dispatcher(spec.prompt(), timeout=timeout)
        dt = time.monotonic() - t0
        return transcript, dt, None

    # --- Residual `claude -p` path (launchd-sessionless; isolation-guarded).
    argv = build_goal_drive_argv(spec, cost_json=True)
    t0 = time.monotonic()
    proc = subprocess.run(
        argv, cwd=str(work_dir),
        capture_output=True, text=True, timeout=timeout,
        env=isolated_env(),
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


def _run_subtask_pass(
    *,
    objective: str,
    sub_tasks: list[SubTask],
    work_dir: Path,
    artifact_dir: Path,
    per_subtask_timeout: int,
    pass_tag: str,
    extra_directive: str = "",
) -> tuple[list[dict], list[str], float | None]:
    """One decompose->dispatch pass (AC.FOUND.0 — NOT re-proved).

    Factored out of the original single-pass body UNCHANGED in
    substance so the bounded re-drive (AC.BRC.2) can invoke it again
    carrying ``extra_directive`` (the surfaced behavioural-failure
    context).  ``pass_tag`` namespaces the transcript files so a
    re-drive's transcripts do not clobber the first pass's (the
    re-dispatch stays observable — AC.BRC.5).  No new spawn machinery:
    each sub-task still dispatches through ``_dispatch_subagent`` ->
    ``build_goal_drive_argv`` -> the sealed isolation surface.
    """
    results: list[dict] = []
    transcript_paths: list[str] = []
    pass_cost: float | None = 0.0
    for i, st in enumerate(sub_tasks):
        directive = (
            f"Scoped sub-task {st.name} of objective: {objective}\n\n"
            f"{st.brief}\n\n"
            f"Acceptance for THIS sub-task (tighter than the whole): "
            f"{st.tighter_acceptance}"
        )
        if extra_directive:
            directive += f"\n\n{extra_directive}"
        spec = GoalDriveSpec(
            directive=directive,
            check_command=st.check_command,
        )
        transcript, dt, cost = _dispatch_subagent(
            spec, work_dir=work_dir, timeout=per_subtask_timeout
        )
        tp = artifact_dir / f"sub_{pass_tag}_{i}_{st.name}.transcript"
        tp.write_text(transcript, encoding="utf-8")
        transcript_paths.append(str(tp))
        if cost is not None and pass_cost is not None:
            pass_cost += cost
        elif cost is None:
            pass_cost = None  # measurement gap -> honest None
        results.append({
            "name": st.name,
            "pass": pass_tag,
            "wall_clock_s": round(dt, 2),
            "cost_usd": cost,
            "self_report_done": DONE_SENTINEL in transcript,
        })
    return results, transcript_paths, pass_cost


def _behavioralize(
    sub_tasks: list[SubTask],
    *,
    objective: str,
    work_dir: Path,
    reference_artifact: str | None,
) -> tuple[list[SubTask], BehavioralCheckSpec]:
    """Replace each sub-task's in-loop ``check_command`` GENERICALLY

    with the loop's OWN behavioural self-check (AC.BRC.1 / AC.BRC.6).

    The structural-presence / ``"true"`` (arms.py:200) signal is
    replaced by the generic construct — NOT a realpb-specific hack and
    NOT another no-op.  The construct imports no scorer/judge
    (AC.BRC.4 — provable by the import test); the frozen graded
    acceptance is never consumed here.
    """
    bspec = build_behavioral_check_command(
        objective=objective,
        work_dir=str(work_dir),
        reference_artifact=reference_artifact,
    )
    cmd = bspec.command()
    return (
        [
            SubTask(
                name=st.name,
                brief=st.brief + "\n\n" + bspec.directive(),
                tighter_acceptance=st.tighter_acceptance,
                check_command=cmd,
            )
            for st in sub_tasks
        ],
        bspec,
    )


def run_handsoff_loop(
    *,
    objective: str,
    sub_tasks: list[SubTask],
    frozen: FrozenAcceptance,
    work_dir: Path,
    artifact_dir: Path,
    per_subtask_timeout: int = 1200,
    verify_timeout: int = 120,
    behavioral_done: bool = False,
    reference_artifact: str | None = None,
    max_refine_attempts: int = 0,
    cost_ceiling_usd: float | None = None,
    wall_ceiling_s: float | None = None,
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

    The behavioural feedback-and-refine cycle (default OFF — every
    pre-existing caller/test is byte-behaviour-unchanged when the new
    params are unset):

      * ``behavioral_done=True`` (AC.BRC.1) — the in-loop
        ``check_command`` is replaced GENERICALLY by the loop's OWN
        behavioural self-check (behavioral_selfcheck.py): a
        self-constructed functional check derived from the plain-
        language ``objective`` that EXERCISES the produced artefact,
        so a structurally-present-but-behaviourally-wrong submission
        (or a ``"true"`` no-op — AC.BRC.6) is NOT reported done.  The
        construct imports no scorer/judge (AC.BRC.4 — the frozen
        graded ``verify`` authority + ``assert_unseen_by`` freeze-
        isolation spine are preserved by construction).

      * ``max_refine_attempts > 0`` (AC.BRC.2) — on a NOT-done
        ``verify`` the loop RE-DRIVES: it re-dispatches carrying the
        surfaced behavioural-failure context (expected vs what the
        artefact did) into the next pass, BOUNDED by
        ``max_refine_attempts`` AND ``cost_ceiling_usd`` /
        ``wall_ceiling_s`` (whichever binds first — no unbounded
        turn-burn).  Each iteration is VERIFICATION-GATED (AC.BRC.3
        anti-erosion): the loop advances ONLY on a fresh ``verify``
        result, NEVER on a sub-agent self-report; the gate is recorded
        in ``refine_log``.  On bound exhaustion the loop returns a
        definite evidence-backed honest-negative (``reached_done`` is
        the real ``verify`` verdict; ``refine_stop_reason`` names why)
        — a first-class plan-success outcome, NEVER retried-to-green
        and the bound NEVER weakened (AC.BRC.5).

    The bounded re-drive is a CONTAINED control-flow evolution of this
    one function (the single ``for``+single ``verify`` becomes a
    bounded re-drive around ``verify``) — NOT a loop re-architecture
    and NOT a new orchestrator phase; AC.FOUND.0 is consumed, NOT
    re-proved.  It composes the ALREADY-PRESENT Claude-native
    primitives only (``/goal`` turn-iteration + ``_dispatch_subagent``
    re-dispatch + the existing ``verify`` spine) — no external agent
    framework (Lens 1).  ORTHOGONAL to the sealed
    ``loop-goal-refinement`` intake construct (``intake.py``
    ``derive_acceptance_from_intent``), which is NOT touched —
    composing alongside it, not modifying it (plan §3.3 / §8.4).
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    drive_tasks = sub_tasks
    bspec: BehavioralCheckSpec | None = None
    if behavioral_done:
        drive_tasks, bspec = _behavioralize(
            sub_tasks,
            objective=objective,
            work_dir=work_dir,
            reference_artifact=reference_artifact,
        )

    # AC.A.2 structural guard: frozen acceptance unseen by any brief.
    # (Behavioural self-check is the loop's OWN check — it never
    # carries the frozen graded acceptance, so this guard still holds
    # on the behavioralised briefs; AC.BRC.4 freeze-isolation
    # preserved.)
    frozen.assert_unseen_by(*[st.brief for st in drive_tasks],
                            *[st.tighter_acceptance for st in drive_tasks])

    t0 = time.monotonic()
    total_cost: float | None = 0.0
    results: list[dict] = []
    transcript_paths: list[str] = []
    refine_log: list[dict] = []

    def _within_budget() -> tuple[bool, str]:
        if (cost_ceiling_usd is not None and total_cost is not None
                and total_cost >= cost_ceiling_usd):
            return False, "cost-ceiling"
        if (wall_ceiling_s is not None
                and (time.monotonic() - t0) >= wall_ceiling_s):
            return False, "wall-ceiling"
        return True, ""

    # --- Pass 0: the original decompose->dispatch pass (AC.FOUND.0).
    p_results, p_tps, p_cost = _run_subtask_pass(
        objective=objective, sub_tasks=drive_tasks,
        work_dir=work_dir, artifact_dir=artifact_dir,
        per_subtask_timeout=per_subtask_timeout, pass_tag="0",
    )
    results += p_results
    transcript_paths += p_tps
    if p_cost is None or total_cost is None:
        total_cost = None
    else:
        total_cost += p_cost

    # loam's INDEPENDENT check decides — NOT the self-reports above.
    final = verify(frozen, work_dir=work_dir, timeout=verify_timeout)
    (artifact_dir / "final_verify.json").write_text(
        json.dumps(final.as_evidence(), indent=2), encoding="utf-8"
    )
    refine_log.append({
        "attempt": 0, "verify_done": final.done,
        "primary_exit": final.primary_exit,
        "held_out_exit": final.held_out_exit,
        # AC.BRC.3 — the gate is the VERIFY result, never the
        # sub-agent self-report.  Recorded so anti-erosion is
        # observable, not a footnote.
        "gated_on": "independent-verify",
    })

    # --- AC.BRC.2/.3/.5: bounded, verification-gated re-drive.
    attempt = 0
    stop_reason = "done" if final.done else "attempt-bound"
    while (not final.done and attempt < max_refine_attempts):
        ok, why = _within_budget()
        if not ok:
            stop_reason = why
            break
        attempt += 1
        # AC.BRC.2 — carry the surfaced behavioural-failure context
        # (expected vs what the artefact did) into the re-dispatch.
        failure_ctx = (
            "PRIOR ATTEMPT DID NOT PASS THE BEHAVIOURAL SELF-CHECK. "
            "The independent check reported NOT-DONE (primary exit "
            f"{final.primary_exit}"
            + (f", held-out exit {final.held_out_exit}"
               if final.held_out_exit is not None else "")
            + "). What the artefact did vs what the objective "
            "requires:\n"
            f"{(final.primary_tail or '').strip()[-1200:]}\n"
            f"{(final.held_out_tail or '').strip()[-600:]}\n"
            "Refine the produced artefact so it ACTUALLY BEHAVES as "
            "the objective describes (structural presence / a no-op "
            "is NOT done), then re-run the behavioural self-check and "
            "surface its full output."
        )
        if bspec is not None:
            failure_ctx += "\n\n" + bspec.directive()
        p_results, p_tps, p_cost = _run_subtask_pass(
            objective=objective, sub_tasks=drive_tasks,
            work_dir=work_dir, artifact_dir=artifact_dir,
            per_subtask_timeout=per_subtask_timeout,
            pass_tag=f"r{attempt}", extra_directive=failure_ctx,
        )
        results += p_results
        transcript_paths += p_tps
        if p_cost is None or total_cost is None:
            total_cost = None
        else:
            total_cost += p_cost
        # AC.BRC.3 — the iteration advances ONLY on a fresh
        # independent verify, NEVER on the sub-agent's "I fixed it"
        # self-report.  A pass that does not improve the verifiable
        # outcome does not silently accumulate (anti-erosion).
        final = verify(
            frozen, work_dir=work_dir, timeout=verify_timeout
        )
        (artifact_dir / "final_verify.json").write_text(
            json.dumps(final.as_evidence(), indent=2), encoding="utf-8"
        )
        refine_log.append({
            "attempt": attempt, "verify_done": final.done,
            "primary_exit": final.primary_exit,
            "held_out_exit": final.held_out_exit,
            "gated_on": "independent-verify",
        })
        if final.done:
            stop_reason = "done"
            break
        stop_reason = "attempt-bound"

    return HandsoffResult(
        reached_done=final.done,
        sub_task_results=results,
        final_verify=final,
        cost_usd=total_cost,
        wall_clock_s=round(time.monotonic() - t0, 2),
        human_loop_driving=False,  # /goal drove; no human in the loop
        transcript_paths=transcript_paths,
        refine_attempts=attempt,
        refine_bound=max_refine_attempts,
        refine_stop_reason=stop_reason,
        refine_log=refine_log,
        behavioral_gated=behavioral_done,
    )

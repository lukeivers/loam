"""The general build-from-intent pipeline (S1→S5 assembled).

ONE code path from a stranger's vague plain-language ask on a fresh
workspace to an honestly-scored generated deliverable:

  understanding (live per-request intent + confirm, AC.REQ.*)
  → asking (meaningful questions iff a build-shaping decision is open)
  → researching (bounded in-run web research → durable grounding
    record, AC.DGR.*)
  → planning (the generative middle: tool + data shape + gate born
    THIS run, AC.GEN.*)
  → freeze (the sealed verify.freeze_acceptance, untouched in
    contract: hash-pinned before any build agent, seen by none)
  → building (convergence as default with the no-retry timeout
    discipline, AC.CVG.*)
  → checking → verdict (judge-scope honesty, honest negative
    first-class)

with plain-language stage updates + heartbeats the whole way
(AC.PRG.*), every claim written to the run record before it is shown.

This module is domain-blind (AC.GEN.2): the domain enters only
through the live ask.  There is no pre-built deliverable, no canned
objective, and no vertical branch — the S6 proof runs and the
off-vertical anti-rigging probe all flow through this exact path.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .convergence import (
    DEFAULT_LEG_CEILING_S,
    DEFAULT_MAX_REFINE_ATTEMPTS,
    ConvergenceResult,
    run_to_convergence,
)
from .generative import (
    GeneratedDesign,
    GenerationUnavailable,
    generate_design,
    render_verdict,
    resolve_command,
    write_gate_files,
)
from .grounding import GroundingOutcome, research_domain
from .orchestrator import SubTask
from .progress import (
    HEARTBEAT_INTERVAL_S,
    RunRecord,
    audit_progress,
    start_heartbeat,
)
from .request_intent import (
    RequestIntent,
    RequestUnderstandingUnavailable,
    build_confirm_text,
    understand_request,
)
from .verify import freeze_acceptance


def interactive_approve(confirm_text: str) -> bool:
    """The interactive form of the SINGLE plain-language approval gate.

    Intake-surface machinery (the sealed AC.B.3 one-approval contract),
    NOT loop-driving: it fires once, before any build, and never steps
    decompose/dispatch/judge.  Lives here (not in the CLI) because the
    approval gate belongs to the intake surface; the CLI must carry no
    interactive surface at all (the sealed AC.HL.A1 guarantee).
    """
    return input("\nProceed? [y/N] ").strip().lower() in ("y", "yes")


def interactive_answer(question: str) -> str:
    """Interactive answers to the bounded meaningful questions
    (AC.REQ.2) — intake-surface, fired before the confirm, never
    inside the build loop."""
    return input(f"\n{question}\n> ").strip()


@dataclass
class BuildFromIntentResult:
    """The end-to-end run outcome, evidence-first."""

    terminal: str  # "done" | "honest-negative" | "not-approved" |
    #               "understanding-failed" | "generation-failed"
    run_dir: str
    verdict_text: str = ""
    intent: RequestIntent | None = None
    answers: dict = field(default_factory=dict)
    grounding: GroundingOutcome | None = None
    design: GeneratedDesign | None = None
    convergence: ConvergenceResult | None = None
    narration: list[str] = field(default_factory=list)
    progress_audit: dict = field(default_factory=dict)
    wall_clock_s: float = 0.0

    def as_evidence(self) -> dict:
        return {
            "terminal": self.terminal,
            "run_dir": self.run_dir,
            "verdict_text": self.verdict_text,
            "intent": self.intent.as_evidence() if self.intent else None,
            "answers": dict(self.answers),
            "grounding": (self.grounding.as_evidence()
                          if self.grounding else None),
            "design": self.design.as_evidence() if self.design else None,
            "convergence": (self.convergence.as_evidence()
                            if self.convergence else None),
            "progress_audit": dict(self.progress_audit),
            "wall_clock_s": self.wall_clock_s,
        }


def _finish(record: RunRecord, result: BuildFromIntentResult,
            t0: float) -> BuildFromIntentResult:
    result.wall_clock_s = round(time.monotonic() - t0, 1)
    result.progress_audit = audit_progress(record.path, result.narration)
    summary = Path(result.run_dir) / "run_summary.json"
    summary.write_text(json.dumps(result.as_evidence(), indent=2),
                       encoding="utf-8")
    return result


def run_build_from_intent(
    ask: str,
    *,
    workspace_dir: Path,
    approve_fn=None,
    answer_fn=None,
    say=print,
    model: str = "sonnet",
    leg_ceiling_s: float = DEFAULT_LEG_CEILING_S,
    max_refine_attempts: int = DEFAULT_MAX_REFINE_ATTEMPTS,
    heartbeat_interval_s: float = HEARTBEAT_INTERVAL_S,
    wall_ceiling_s: float | None = None,
) -> BuildFromIntentResult:
    """Run the whole general path on one ask (the S6 entry point).

    ``approve_fn(confirm_text) -> bool`` is the single plain-language
    approval gate (None = standing hands-off agreement, recorded as
    such).  ``answer_fn(question) -> str`` answers meaningful
    questions when a live user is reachable; when None, surfaced
    questions are recorded as an un-answered human gate and the run
    proceeds on the plain reading of the ask — honestly noted.
    """
    t0 = time.monotonic()
    workspace_dir = Path(workspace_dir)
    run_dir = workspace_dir / "runs" / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    record = RunRecord(run_dir)
    narration: list[str] = []

    def _say(line: str) -> None:
        narration.append(line)
        say(line)

    result = BuildFromIntentResult(terminal="", run_dir=str(run_dir),
                                   narration=narration)

    # --- understanding (S1) -----------------------------------------
    record.narrate(
        "understanding",
        "Reading your ask to make sure I build the right thing.",
        say=_say, next_step="I'll confirm what I understood with you.")
    try:
        intent = understand_request(ask, model=model)
    except RequestUnderstandingUnavailable as exc:
        record.narrate(
            "verdict",
            f"I couldn't get a reliable read of this ask ({exc}). "
            "Nothing was built.", say=_say)
        result.terminal = "understanding-failed"
        return _finish(record, result, t0)
    result.intent = intent
    record.emit("understanding", "intent extracted",
                intent=intent.as_evidence())

    # --- asking (S1: questions iff a decision is open) ----------------
    answers: dict[str, str] = {}
    if intent.questions:
        record.narrate(
            "asking",
            "Before I start, a couple of things genuinely change what "
            "gets built:", say=_say)
        for q in intent.questions:
            record.narrate("asking", q, say=_say)
            if answer_fn is not None:
                answers[q] = str(answer_fn(q))
                record.emit("asking", "answer received",
                            question=q, answer=answers[q])
            else:
                record.emit(
                    "asking", "no live user to answer — proceeding on "
                    "the plain reading of the ask (noted honestly)",
                    question=q, human_gate_unanswered=True)
    result.answers = answers

    # --- the single plain-language approval gate ----------------------
    confirm = build_confirm_text(intent, answers)
    record.narrate("understanding", confirm, say=_say)
    if approve_fn is not None:
        approved = bool(approve_fn(confirm))
        record.emit("understanding", "approval gate",
                    approved=approved)
        if not approved:
            record.narrate(
                "verdict", "Understood — I won't build this. Nothing "
                "was changed.", say=_say)
            result.terminal = "not-approved"
            return _finish(record, result, t0)
    else:
        record.emit("understanding", "approval gate",
                    approved=True, standing_hands_off_agreement=True)

    # --- researching (S2) ---------------------------------------------
    record.narrate(
        "researching",
        "Checking how people who do this work professionally actually "
        "do it, so the finished tool is checked against real practice.",
        say=_say, next_step="I'll plan the build around what I find.",
        expected_wait_plain="usually a minute or two")
    # AC.PRG.1: the research leg can run long — heartbeats cover it
    # (no user-visible silence beyond the bound while work is active).
    beat_stop = start_heartbeat(
        record, watch_dir=run_dir, say=_say,
        interval_s=heartbeat_interval_s)
    try:
        grounding = research_domain(
            intent.objective, workspace_dir=workspace_dir, model=model)
    finally:
        beat_stop.set()
    if grounding.grounded:
        record.narrate(
            "researching",
            f"Found {len(grounding.norms)} relevant practices from "
            "real sources (each checked live just now). The finished "
            "tool's acceptance check will reflect them.", say=_say,
            grounding_record=grounding.record_path)
        if grounding.expert_gate_flags:
            for flag in grounding.expert_gate_flags:
                record.narrate(
                    "researching",
                    f"One thing research can't settle (a human expert "
                    f"should): {flag}", say=_say, expert_gate=True)
    else:
        record.narrate("researching", grounding.ungrounded_reason,
                       say=_say, ungrounded=True)
    result.grounding = grounding

    # --- planning: the generative middle (S3) --------------------------
    record.narrate(
        "planning",
        "Designing the tool, its data layout, and the pass/fail check "
        "it will have to satisfy — all from your ask, none of it "
        "pre-made.", say=_say,
        next_step="I'll lock the check in before any building starts.",
        expected_wait_plain="a few minutes")
    # AC.PRG.1: the generation leg runs long too — heartbeats cover it.
    beat_stop = start_heartbeat(
        record, watch_dir=run_dir, say=_say,
        interval_s=heartbeat_interval_s)
    try:
        design = generate_design(intent, grounding, answers=answers,
                                 model=model)
    except GenerationUnavailable as exc:
        record.narrate(
            "verdict",
            f"I couldn't produce a sound design for this ({exc}). "
            "Nothing was built — reported straight rather than built "
            "on a broken plan.", say=_say)
        result.terminal = "generation-failed"
        return _finish(record, result, t0)
    finally:
        beat_stop.set()
    result.design = design

    gate_dir = run_dir / "gate"
    work_dir = run_dir / "work"
    artifact_dir = run_dir / "artifacts"
    work_dir.mkdir(parents=True, exist_ok=True)
    write_gate_files(design, gate_dir=gate_dir)
    check_cmd = resolve_command(design.check_command,
                                gate_dir=gate_dir, work_dir=work_dir)
    held_out_cmd = (resolve_command(design.held_out_command,
                                    gate_dir=gate_dir, work_dir=work_dir)
                    if design.held_out_command else None)
    criteria_text = "\n".join(
        f"- {c.criterion}"
        + (f" [per practitioner norm {c.traceable_to}]"
           if c.traceable_to else "")
        for c in design.gate_criteria)
    frozen = freeze_acceptance(
        acceptance_id="bfi-gate",
        content=f"{design.gate_plain}\n\n{criteria_text}",
        check_argv=["/bin/sh", "-c", check_cmd],
        held_out_argv=(["/bin/sh", "-c", held_out_cmd]
                       if held_out_cmd else None),
        freeze_dir=run_dir / "_frozen",
    )
    record.emit("planning", "acceptance gate frozen + hash-pinned "
                "before any build agent sees work",
                gate_sha256=frozen.content_sha256,
                criteria=[vars(c) for c in design.gate_criteria])

    # --- building to convergence (S4) with heartbeats (S5) -------------
    record.narrate(
        "building",
        "Building now. I'll check in while it runs so you can see "
        "it's moving.", say=_say,
        next_step="An independent check decides when it's done — not "
                  "the builder's word.",
        expected_wait_plain="builds like this often take 10-40 minutes")
    sub_tasks = [SubTask(name=st["name"], brief=st["brief"],
                         tighter_acceptance=st["tighter_acceptance"],
                         check_command="true")
                 for st in design.sub_tasks]
    beat_stop = start_heartbeat(
        record, watch_dir=run_dir, say=_say,
        interval_s=heartbeat_interval_s)
    try:
        convergence = run_to_convergence(
            objective=intent.objective,
            sub_tasks=sub_tasks,
            frozen=frozen,
            work_dir=work_dir,
            artifact_dir=artifact_dir,
            leg_ceiling_s=leg_ceiling_s,
            max_refine_attempts=max_refine_attempts,
            wall_ceiling_s=wall_ceiling_s,
        )
    finally:
        beat_stop.set()
    result.convergence = convergence

    # --- checking + verdict (S5/AC.GEN.3 honesty) -----------------------
    record.narrate(
        "checking",
        "Build finished — running the locked-in acceptance check "
        "(the builder never saw it).", say=_say)
    tail = ""
    if convergence.result and convergence.result.final_verify:
        tail = (convergence.result.final_verify.primary_tail or "")[-300:]
    verdict = render_verdict(
        design, reached_done=convergence.reached_done,
        stop_reason=convergence.stop_reason, evidence_tail=tail)
    record.narrate("verdict", verdict, say=_say)
    result.verdict_text = verdict
    result.terminal = ("done" if convergence.reached_done
                       else "honest-negative")
    return _finish(record, result, t0)

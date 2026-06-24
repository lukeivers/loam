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
    CandidateDesign,
    GateCriterion,
    GeneratedDesign,
    GenerationUnavailable,
    generate_candidate_designs,
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
class ChosenDesign:
    """The user's settled choice from the candidate designs (AC.DF.2/.3).

    The intake-surface ``choose_design_fn(candidates)`` returns one of
    these (or ``None`` for "declined / abandoned" — a distinct
    non-built terminal).  ``index`` selects the candidate; the optional
    tweak fields carry the user's edits, which are folded into the
    chosen :class:`GeneratedDesign` BEFORE the (untouched) freeze
    (AC.DF.3):

      * ``objective`` — a changed objective sentence;
      * ``add_criteria`` — gate criteria the user added;
      * ``remove_criteria`` — substrings of gate criteria to drop;
      * ``gate_plain`` — a changed plain "done-when" statement.

    A tweak is a property of the chosen design; the choice UI (numbered
    terminal prompt, a channel reply, a test double) is the caller's —
    this carrier is the contract between the surface and the freeze."""

    index: int = 0
    objective: str | None = None
    gate_plain: str | None = None
    add_criteria: list[str] = field(default_factory=list)
    remove_criteria: list[str] = field(default_factory=list)


def apply_design_tweaks(
    design: GeneratedDesign, chosen: ChosenDesign,
) -> GeneratedDesign:
    """Fold the user's tweaks into the buildable design (AC.DF.3).

    ``design`` is the full buildable design generated for the chosen
    direction.  Returns a new :class:`GeneratedDesign` reflecting the
    EDITED design (the frozen gate + build briefs are derived from this,
    not the raw machine output).  No tweak fields => the design is
    returned unchanged."""
    import dataclasses as _dc

    new_objective = chosen.objective or design.objective
    new_gate_plain = chosen.gate_plain or design.gate_plain
    criteria = [
        c for c in design.gate_criteria
        if not any(rm and rm.lower() in c.criterion.lower()
                   for rm in chosen.remove_criteria)
    ]
    for added in chosen.add_criteria:
        text = str(added).strip()
        if text:
            criteria.append(GateCriterion(criterion=text, traceable_to=""))
    if (new_objective == design.objective
            and new_gate_plain == design.gate_plain
            and criteria == list(design.gate_criteria)):
        return design
    return _dc.replace(
        design, objective=new_objective, gate_plain=new_gate_plain,
        gate_criteria=criteria)


@dataclass
class BuildFromIntentResult:
    """The end-to-end run outcome, evidence-first."""

    terminal: str  # "done" | "honest-negative" | "not-approved" |
    #               "understanding-failed" | "generation-failed" |
    #               "design-not-chosen" (AC.DF.2: user declined a design)
    run_dir: str
    verdict_text: str = ""
    intent: RequestIntent | None = None
    answers: dict = field(default_factory=dict)
    grounding: GroundingOutcome | None = None
    candidates: list[CandidateDesign] = field(default_factory=list)
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
            "candidates": [c.as_evidence() for c in self.candidates],
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
    choose_design_fn=None,
    n_candidates: int = 3,
    say=print,
    notify_fn=None,
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

    ``choose_design_fn(candidates) -> ChosenDesign | None`` is the
    design-first front stage (AC.DF.*): when provided, the pipeline
    generates ``n_candidates`` materially-distinct candidate designs
    AFTER research and surfaces them for the user to review / tweak /
    SELECT before any build starts.  Returning ``None`` (declined /
    abandoned) terminates the run with the distinct ``design-not-chosen``
    terminal — NO gate is frozen and NO build dispatches (AC.DF.2).  A
    returned :class:`ChosenDesign` proceeds the build on exactly the
    chosen (optionally tweaked) design (AC.DF.3).  When ``choose_design_fn
    is None`` (standing hands-off — the sealed non-interactive S6 path)
    the single-design ``generate_design`` path runs UNCHANGED and the
    build proceeds on it byte-for-byte as before this slice (AC.DF.4).

    ``notify_fn(text)`` is the channel-aware heartbeat seam (Slice HB,
    AC.HB.*): when wired (the workspace passes a closure over the shared
    channel module), the long build leg posts periodic plain-language
    progress + a distinct stall surface to the user's ACTIVE channel
    (Discord/Telegram) at the calmer channel cadence; loam imports NO
    workspace channel file — the channel surface enters ONLY through this
    injected callable (SAL-HB-1 / H-3).  When ``notify_fn is None`` the
    heartbeat surfaces on the main thread (terminal) exactly as before
    this slice — byte-behaviour-preserved (AC.HB.4).
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
        if choose_design_fn is None:
            # AC.DF.4 — the sealed non-interactive S6 path: the
            # single-design generate_design runs UNCHANGED, byte-for-byte
            # as before this slice. No candidate generation, no choice
            # gate; standing hands-off auto-builds on the one design.
            design = generate_design(intent, grounding, answers=answers,
                                     model=model)
        else:
            # AC.DF.1 — the design-first front stage: N materially-
            # distinct candidate designs, surfaced for review BEFORE the
            # freeze + any build dispatch.
            candidates = generate_candidate_designs(
                intent, grounding, n=n_candidates, answers=answers,
                model=model)
            result.candidates = candidates
            record.emit(
                "planning", "candidate designs generated for review",
                candidate_count=len(candidates),
                form_factors=[c.form_factor for c in candidates])
            record.narrate(
                "planning",
                f"I came up with {len(candidates)} different ways to "
                "build this. Pick the one that fits — you can tweak it "
                "before I start:", say=_say)
            for i, cand in enumerate(candidates):
                record.narrate(
                    "planning",
                    f"  {i + 1}. {cand.form_factor} — {cand.tool_plan}",
                    say=_say)
            # AC.DF.2 — the build loop does NOT start until the user
            # settles a design. choose_design_fn is the intake surface
            # (numbered prompt / channel reply / test double — the
            # caller's, mirroring approve_fn). None back = declined.
            chosen = choose_design_fn(candidates)
            if chosen is None:
                design = None
            else:
                idx = max(0, min(int(getattr(chosen, "index", 0)),
                                 len(candidates) - 1))
                picked = candidates[idx]
                # The full buildable design (gate_files, verification
                # scripts, sub-task briefs) is generated for the CHOSEN
                # direction only — the chosen candidate's direction
                # conditions the single-design generation through the
                # existing clarifications seam (no new generate_design
                # contract). This is the budget-safe split (D-build.2).
                direction_answers = dict(answers)
                direction_answers["Chosen design direction to build"] = (
                    picked.as_direction_brief())
                base_design = generate_design(
                    intent, grounding, answers=direction_answers,
                    model=model)
                # AC.DF.3 — the user's tweaks propagate into the frozen
                # gate + build briefs (the EDITED design, not the raw
                # machine output).
                design = apply_design_tweaks(base_design, chosen)
                record.emit(
                    "planning", "design chosen + buildable gate generated",
                    chosen_index=idx, form_factor=picked.form_factor,
                    tweaked=(design is not base_design))
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

    # AC.DF.2 — the user declined / abandoned: NO gate is frozen and NO
    # build sub-task dispatches; a distinct non-built terminal.
    if design is None:
        record.narrate(
            "verdict",
            "Understood — none of those designs were what you wanted, so "
            "I didn't build anything. Nothing was changed.", say=_say)
        result.terminal = "design-not-chosen"
        return _finish(record, result, t0)
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
    # AC.HB.1–.3 — the build leg is the long async leg (10-40 min); its
    # heartbeat is channel-aware via the injected notify_fn (Slice HB).
    # notify_fn=None keeps the sealed terminal-only behaviour (AC.HB.4).
    beat_stop = start_heartbeat(
        record, watch_dir=run_dir, say=_say,
        interval_s=heartbeat_interval_s,
        notify_fn=notify_fn)
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

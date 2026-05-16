"""Persona-invocable CLI entry point (AC.A.1).

`handsoff-loop run --objective ... --frozen ...` is the single
capability the primary persona invokes; the SKILL bundle
(`plugins/loam-skills/skills/handsoff-loop/`) delegates here.  No
human hand-drives decompose / dispatch / judge — the orchestrator
composes the probe-proven loop and `/goal` drives the keep-going leg.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_describe(_args: argparse.Namespace) -> int:
    """Emit the capability contract as JSON (what the persona invokes)."""
    print(json.dumps({
        "capability": "handsoff-loop",
        "unit": ("one user-approved plain-language objective with one "
                 "frozen machine-checkable acceptance set; sub-tasks "
                 "internal (D-UNIT ratified)"),
        "composes": ["probe-proven decompose->dispatch->judge "
                     "(AC.FOUND.0 — not re-proved)",
                     "/goal drive/stop leg (binary 2.1.143)",
                     "loam independent tool-executing judge decides"],
        "phases": {
            "A": "packaged-skill orchestration fidelity (AC.A.1-.4)",
            "B": "intent->checkable-done intake (AC.B.1-.5)",
            "C": "end-to-end hands-off, gated on A+B both positive",
        },
        "honest_negative": ("a definite negative phase verdict is a "
                            "valid plan-success outcome; never retried "
                            "to green"),
        "no_api_key": "real claude binary, default Sonnet",
    }, indent=2))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    """Run the packaged loop on a real frozen-acceptance task.

    Two freeze sources, mutually exclusive:

      * ``--frozen <spec.json>`` — the pre-existing hand-authored
        frozen-acceptance + sub_tasks JSON (unchanged path).
      * ``--from-intake <intake-outcome.json>`` — AC.GR.6: the seam
        read-path.  The frozen `check_argv` the loop EXECUTES is
        provably DERIVED (via `freeze_input_from_outcome`) from the
        `IntakeOutcome.machine_checkable` the user AGREED to at the
        single approval gate — NOT a separately hand-authored command
        unrelated to intake.  This closes the §3b disconnected-halves
        gap so "you agreed to milestone M and the loop verified
        exactly M" is structurally true, not coincidental.  The
        milestone leg's honesty depends on this; it is a read-path
        connection ONLY (it feeds `freeze_acceptance`; it does NOT
        change how `verify` decides done and does NOT touch
        decompose/dispatch/judge — AC.FOUND.0 untouched).  `sub_tasks`
        still come from the spec file (the intake unit is the
        whole-objective unit; decomposition stays internal — D-UNIT).
    """
    from .intake import IntakeOutcome, freeze_input_from_outcome
    from .orchestrator import SubTask, run_handsoff_loop
    from .verify import freeze_acceptance

    spec = json.loads(Path(args.frozen).read_text())
    if getattr(args, "from_intake", None):
        # AC.GR.6 — freeze the AGREED command, provably.
        evidence = json.loads(Path(args.from_intake).read_text())
        outcome = IntakeOutcome(
            original_intent=evidence.get("original_intent", ""),
            under_specification=evidence.get("under_specification", []),
            elicited_questions=evidence.get("elicited_questions", []),
            elicited_answers=evidence.get("elicited_answers", {}),
            plain_language_acceptance=evidence.get(
                "plain_language_acceptance", ""),
            machine_checkable=evidence.get("machine_checkable", {}),
            approved=evidence.get("approved", False),
            faithful=evidence.get("faithful", False),
            faithfulness_reason=evidence.get("faithfulness_reason", ""),
            is_milestone=evidence.get("is_milestone", False),
            milestone_toward=evidence.get("milestone_toward", ""),
            check_in_pending=evidence.get("check_in_pending", False),
            refinement_attempts=evidence.get("refinement_attempts", 0),
            refinement_outcome=evidence.get("refinement_outcome", "none"),
        )
        fi = freeze_input_from_outcome(outcome)
        frozen = freeze_acceptance(
            acceptance_id=fi["acceptance_id"],
            content=fi["content"],
            check_argv=fi["check_argv"],
            held_out_argv=fi["held_out_argv"],
            freeze_dir=Path(args.work_dir).parent / "_frozen",
        )
    else:
        frozen = freeze_acceptance(
            acceptance_id=spec["acceptance_id"],
            content=spec["content"],
            check_argv=spec["check_argv"],
            held_out_argv=spec.get("held_out_argv"),
            freeze_dir=Path(args.work_dir).parent / "_frozen",
        )
    sub_tasks = [SubTask(**st) for st in spec["sub_tasks"]]
    result = run_handsoff_loop(
        objective=args.objective,
        sub_tasks=sub_tasks,
        frozen=frozen,
        work_dir=Path(args.work_dir),
        artifact_dir=Path(args.artifact_dir),
        # AC.BRC.1/.2/.6 — opt into the loop's OWN behavioural self-
        # check + the bounded verification-gated re-drive.  Defaults
        # OFF so every pre-existing caller is byte-behaviour-unchanged.
        behavioral_done=bool(getattr(args, "behavioral_done", False)),
        reference_artifact=getattr(args, "reference_artifact", None),
        max_refine_attempts=int(
            getattr(args, "max_refine_attempts", 0) or 0),
        cost_ceiling_usd=(
            float(args.cost_ceiling_usd)
            if getattr(args, "cost_ceiling_usd", None) is not None
            else None),
        wall_ceiling_s=(
            float(args.wall_ceiling_s)
            if getattr(args, "wall_ceiling_s", None) is not None
            else None),
    )
    print(json.dumps({
        "reached_done": result.reached_done,
        "human_loop_driving": result.human_loop_driving,
        "cost_usd": result.cost_usd,
        "wall_clock_s": result.wall_clock_s,
        "sub_tasks": result.sub_task_results,
        # AC.BRC.2/.3/.5 — the bounded behavioural-refine cycle's
        # observable evidence (honest-negative is first-class:
        # reached_done False with a definite refine_stop_reason is a
        # plan-success outcome, never retried-to-green).  Read
        # defensively: a pre-existing caller / test double that
        # predates these fields stays byte-behaviour-unchanged (the
        # AC.GR.6 seam double is intentionally narrow — AC.FOUND.0:
        # the seam is NOT re-proved by this cycle).
        "behavioral_gated": getattr(
            result, "behavioral_gated", False),
        "refine_attempts": getattr(result, "refine_attempts", 0),
        "refine_bound": getattr(result, "refine_bound", 0),
        "refine_stop_reason": getattr(
            result, "refine_stop_reason", "done"),
        "refine_log": getattr(result, "refine_log", []),
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="handsoff-loop")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("describe").set_defaults(fn=_cmd_describe)

    r = sub.add_parser("run")
    r.add_argument("--objective", required=True)
    r.add_argument("--frozen", required=True,
                   help="JSON: frozen acceptance + sub_tasks")
    r.add_argument(
        "--from-intake", default=None,
        help=("AC.GR.6 seam: JSON of an IntakeOutcome.as_evidence(); "
              "the frozen check the loop executes is provably derived "
              "from the user-agreed machine_checkable (not the "
              "hand-authored --frozen check_argv). sub_tasks still "
              "come from --frozen (D-UNIT)."))
    r.add_argument("--work-dir", required=True)
    r.add_argument("--artifact-dir", required=True)
    r.add_argument(
        "--behavioral-done", dest="behavioral_done",
        action="store_true",
        help=("AC.BRC.1/.6: replace the in-loop check_command "
              "GENERICALLY with the loop's OWN behavioural self-check "
              "derived from --objective (a structurally-present-but-"
              "behaviourally-wrong artefact, or a `true` no-op, is "
              "NOT reported done). The construct imports no scorer/"
              "judge (AC.BRC.4)."))
    r.add_argument(
        "--reference-artifact", dest="reference_artifact",
        default=None,
        help=("AC.BRC.5 / D-BRC-5 (permitted, NOT mandated): a "
              "runnable reference artefact the behavioural self-check "
              "MAY probe/diff observable behaviour against."))
    r.add_argument(
        "--max-refine-attempts", dest="max_refine_attempts",
        type=int, default=0,
        help=("AC.BRC.2: on a NOT-done independent verify, RE-DRIVE "
              "carrying the surfaced behavioural-failure context, "
              "bounded by THIS finite attempt count AND the cost/wall "
              "ceiling (whichever binds first). 0 == no re-drive "
              "(byte-behaviour-unchanged)."))
    r.add_argument(
        "--cost-ceiling-usd", dest="cost_ceiling_usd",
        type=float, default=None,
        help=("AC.BRC.2: the existing cost ceiling — the re-drive "
              "stops when MEASURED cost reaches it (no unbounded "
              "turn-burn)."))
    r.add_argument(
        "--wall-ceiling-s", dest="wall_ceiling_s",
        type=float, default=None,
        help=("AC.BRC.2: the existing wall-clock ceiling — the "
              "re-drive stops when wall time reaches it."))
    r.set_defaults(fn=_cmd_run)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

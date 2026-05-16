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
    """Run the packaged loop on a real frozen-acceptance task."""
    from .orchestrator import SubTask, run_handsoff_loop
    from .verify import freeze_acceptance

    spec = json.loads(Path(args.frozen).read_text())
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
    )
    print(json.dumps({
        "reached_done": result.reached_done,
        "human_loop_driving": result.human_loop_driving,
        "cost_usd": result.cost_usd,
        "wall_clock_s": result.wall_clock_s,
        "sub_tasks": result.sub_task_results,
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
    r.add_argument("--work-dir", required=True)
    r.add_argument("--artifact-dir", required=True)
    r.set_defaults(fn=_cmd_run)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

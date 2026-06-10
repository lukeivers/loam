#!/usr/bin/env python3.13
"""The honest smoke harness (S6 — AC.SMK.1/.2/.3).

Runs ONE archetype ask through the documented general-path command on
a FRESH workspace and appends an unfiltered, room-ready entry to the
run log: result (fails included), wall-clock, where human gates
fired, gate traceability, citations — every number carrying its
run-of-origin (this entry IS the run of origin: ask verbatim,
workspace, loam commit, timestamp).

THE DOCUMENTED REPRODUCIBLE COMMAND (any logged run, and the "one
more case" a dispatcher runs with a prompt no builder ever saw —
AC.SMK.2/.OA):

    python3.13 framework/tools/handsoff-loop/smoke/run_smoke.py \
        --archetype <name> --prompt-file <file-with-the-ask>
    # or --ask "<the ask verbatim>"

Every archetype — back-office trio and off-vertical alike — flows
through the IDENTICAL underlying command (printed in each log entry);
the harness contains no per-archetype branching.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent / "src"
_REPO = _HERE.parents[3]
DEFAULT_LOG = _HERE / "RUN_LOG.md"

# The one underlying command every archetype runs (placeholders are
# substituted per run; nothing else varies by archetype).
ENTRY_COMMAND = (
    "PYTHONPATH={src} python3.13 -m handsoff_loop.cli "
    "build-from-intent --ask {ask!r} --workspace {workspace} --yes"
)


def _loam_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(_REPO), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def format_log_entry(
    *,
    archetype: str,
    ask: str,
    workspace: str,
    loam_commit: str,
    started: str,
    wall_clock_s: float,
    terminal: str,
    summary: dict,
    entry_command: str,
) -> str:
    """One unfiltered, self-contained, room-ready log entry (AC.SMK.3).

    Every number in the entry is scoped to THIS run (run-of-origin is
    the entry header: archetype + ask verbatim + workspace + commit +
    timestamp); the reproduce command is included verbatim."""
    grounding = summary.get("grounding") or {}
    design = summary.get("design") or {}
    convergence = summary.get("convergence") or {}
    audit = summary.get("progress_audit") or {}
    intent = summary.get("intent") or {}

    human_gates = []
    if intent.get("questions"):
        answered = set((summary.get("answers") or {}))
        for q in intent["questions"]:
            state = "answered" if q in answered else "unanswered"
            human_gates.append(f"question ({state}): {q}")
    if not grounding.get("grounded", False):
        human_gates.append("ungrounded build flagged to the user")
    for flag in (grounding.get("expert_gate_flags") or []):
        human_gates.append(f"expert-gate flag: {flag}")

    traced = [c for c in (design.get("gate_criteria") or [])
              if c.get("traceable_to")]
    lines = [
        f"## {started} — {archetype} — terminal: **{terminal}**",
        "",
        f"- run-of-origin: this entry (loam commit `{loam_commit}`, "
        f"workspace `{workspace}`, started {started})",
        f"- ask (verbatim): {ask}",
        f"- wall-clock: {wall_clock_s}s [this run]",
        f"- result: {terminal} — fails included by contract; an "
        f"honest negative is logged exactly like a pass",
        f"- grounding: grounded={grounding.get('grounded')} | "
        f"live-verified citations={len(grounding.get('norms') or [])} "
        f"| dropped={len(grounding.get('dropped_citations') or [])} "
        f"[this run]",
        f"- gate criteria: {len(design.get('gate_criteria') or [])} "
        f"total, {len(traced)} traceable to practitioner norms "
        f"[this run]",
        f"- convergence: stop_reason={convergence.get('stop_reason')} "
        f"| refine_attempts={convergence.get('refine_attempts')} | "
        f"timed_out={convergence.get('timed_out')} | "
        f"timeout_retries={convergence.get('timeout_retries')} "
        f"[this run]",
        f"- progress audit: user-visible updates="
        f"{audit.get('n_user_visible')} | max gap={audit.get('max_gap_s')}s "
        f"| within heartbeat bound={audit.get('gap_within_bound')} | "
        f"unverifiable claims="
        f"{len(audit.get('unverifiable_claims') or [])} [this run]",
        "- human gates fired this run:" if human_gates else
        "- human gates fired this run: none",
    ]
    lines += [f"  - {g}" for g in human_gates]
    lines += [
        "- reproduce this run:",
        "  ```",
        f"  {entry_command}",
        "  ```",
        "",
    ]
    return "\n".join(lines)


def run_one(archetype: str, ask: str, *, workspace: str | None,
            log_path: Path, wall_ceiling_s: float) -> dict:
    ws = workspace or tempfile.mkdtemp(prefix=f"bfi-smoke-{archetype}-")
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    cmd = ENTRY_COMMAND.format(src=_SRC, ask=ask, workspace=ws)
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-m", "handsoff_loop.cli", "build-from-intent",
         "--ask", ask, "--workspace", ws, "--yes",
         "--wall-ceiling-s", str(wall_ceiling_s)],
        capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(_SRC)},
    )
    wall = round(time.monotonic() - t0, 1)

    terminal = "pipeline-error"
    summary: dict = {}
    for line in reversed(proc.stdout.strip().splitlines()):
        try:
            tail = json.loads(line)
            if "terminal" in tail:
                terminal = tail["terminal"]
                sp = Path(tail["run_summary"])
                if sp.exists():
                    summary = json.loads(sp.read_text(encoding="utf-8"))
                break
        except (json.JSONDecodeError, ValueError):
            continue
    if terminal == "pipeline-error":
        summary = {"stderr_tail": proc.stderr[-800:],
                   "stdout_tail": proc.stdout[-800:]}

    entry = format_log_entry(
        archetype=archetype, ask=ask, workspace=ws,
        loam_commit=_loam_commit(), started=started,
        wall_clock_s=wall, terminal=terminal, summary=summary,
        entry_command=cmd)
    with Path(log_path).open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")
    print(json.dumps({"archetype": archetype, "terminal": terminal,
                      "wall_clock_s": wall, "workspace": ws,
                      "log": str(log_path)}))
    return {"terminal": terminal, "wall_clock_s": wall,
            "workspace": ws, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--archetype", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ask")
    g.add_argument("--prompt-file",
                   help="file whose full contents are the ask verbatim "
                        "(how a dispatcher runs a prompt no builder saw)")
    p.add_argument("--workspace", default=None,
                   help="default: a fresh temp dir")
    p.add_argument("--log", default=str(DEFAULT_LOG))
    p.add_argument("--wall-ceiling-s", type=float, default=3000.0)
    args = p.parse_args(argv)
    ask = args.ask if args.ask else Path(
        args.prompt_file).read_text(encoding="utf-8").strip()
    out = run_one(args.archetype, ask, workspace=args.workspace,
                  log_path=Path(args.log),
                  wall_ceiling_s=args.wall_ceiling_s)
    return 0 if out["terminal"] in ("done", "honest-negative") else 1


if __name__ == "__main__":
    sys.exit(main())

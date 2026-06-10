"""In-loop progress surface (S5 — AC.PRG.*).

The user is kept in the loop through plain-language STAGE UPDATES
(understanding → asking → researching → planning → building →
checking → verdict), each saying what is happening and what comes
next, with HEARTBEATS during long legs so no user-visible silence
exceeds the named bound while work is active (AC.PRG.1).

Narration honesty (AC.PRG.2 — narration-is-not-action, enforced on
this surface):

  * write-then-say: every user-visible line is appended to the
    on-disk run record BEFORE it is shown — a narrated claim with no
    run-record state cannot exist by construction;
  * heartbeats carry artifact-probe liveness evidence (the S4
    ``probe_liveness`` dict), never bare "still working" assertions;
  * waits are stated honestly with rough plain-language time
    expectations;
  * :func:`audit_progress` replays a finished run's record against
    its narration after the fact: unverifiable claims and
    over-the-bound silence gaps are named, not waved through
    (AC.PRG.OA's audit half).

Claude-primitive composition (Lens 1, per the plan's placement): the
build legs run as in-session Task subagents or residual spawn-isolated
agents; the dispatcher-side wait is owned via the artifact probe; the
persona's narration is the user-facing voice (channel reply/edit when
a channel is connected; terminal narration on a fresh workspace) —
this module is the run-record + heartbeat substrate all of those
consume.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

# AC.PRG.1 — the named heartbeat bound: while work is active, the gap
# between user-visible updates never exceeds this.
HEARTBEAT_INTERVAL_S = 120.0

# The ordered stage vocabulary of the general build-from-intent path.
STAGES = ("understanding", "asking", "researching", "planning",
          "building", "checking", "verdict", "heartbeat")

RUN_RECORD_NAME = "run_record.jsonl"


class RunRecord:
    """The append-only on-disk run record narration is audited against.

    Every event is one JSON line: ``{"ts", "stage", "message", ...}``.
    ``narrate`` is the ONLY intended path to the user's eyes: it
    appends the event FIRST, then hands the rendered line to ``say``
    (AC.PRG.2 write-then-say, structural)."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / RUN_RECORD_NAME
        self._lock = threading.Lock()

    def emit(self, stage: str, message: str, **fields) -> dict:
        """Append one verifiable progress event (no user surface)."""
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage!r} — the stage "
                             f"vocabulary is {STAGES}")
        event = {"ts": time.time(), "stage": stage,
                 "message": str(message), **fields}
        line = json.dumps(event)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return event

    def narrate(self, stage: str, message: str, *, say=print,
                next_step: str = "", expected_wait_plain: str = "",
                **fields) -> dict:
        """Write-then-say: the record carries the claim BEFORE the
        user sees it (AC.PRG.2).  ``next_step`` is the "what comes
        next" half of AC.PRG.1; ``expected_wait_plain`` states a wait
        honestly in plain language when one is coming."""
        rendered = message
        if expected_wait_plain:
            rendered += f" ({expected_wait_plain})"
        if next_step:
            rendered += f" Next: {next_step}"
        event = self.emit(stage, rendered, user_visible=True,
                          next_step=next_step,
                          expected_wait_plain=expected_wait_plain,
                          **fields)
        say(rendered)
        return event

    def events(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out


def start_heartbeat(
    record: RunRecord,
    *,
    watch_dir: Path,
    say=print,
    interval_s: float = HEARTBEAT_INTERVAL_S,
    probe_fn=None,
) -> "threading.Event":
    """Keep the user-visible surface alive during a long leg.

    Every ``interval_s`` while the returned stop-event is unset, emit
    + say a heartbeat whose message carries artifact-probe liveness
    EVIDENCE (AC.PRG.2 — a heartbeat is a verified claim, not a vibe).
    Returns the stop event; callers set it when the leg completes.
    """
    from .convergence import probe_liveness

    probe = probe_fn if probe_fn is not None else probe_liveness
    stop = threading.Event()

    def _beat() -> None:
        while not stop.wait(interval_s):
            state = probe(Path(watch_dir))
            if state.get("alive"):
                msg = ("Still working — progress is actively landing "
                       f"on disk ({state['evidence']}).")
            else:
                msg = ("Still here — the current step is running and "
                       "hasn't written new files yet "
                       f"({state['evidence']}).")
            record.narrate("heartbeat", msg, say=say,
                           liveness=state)

    t = threading.Thread(target=_beat, name="bfi-heartbeat", daemon=True)
    t.start()
    return stop


def audit_progress(
    record_path: Path,
    narrated_lines: list[str],
    *,
    heartbeat_bound_s: float = HEARTBEAT_INTERVAL_S,
) -> dict:
    """After-the-fact audit of a finished run (AC.PRG.2 / AC.PRG.OA).

    Returns ``{"unverifiable_claims": [...], "max_gap_s": float,
    "gap_within_bound": bool, "n_user_visible": int}``:

      * every narrated line must exist verbatim as a user-visible
        run-record event (a said-but-never-recorded line is a
        fabricated progress claim);
      * the max gap between consecutive user-visible events across
        the active window (first event → verdict event) must stay
        within the heartbeat bound (a small grace factor covers
        scheduler jitter, not silence).
    """
    record_path = Path(record_path)
    events = []
    if record_path.exists():
        for line in record_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
    visible = [e for e in events if e.get("user_visible")]
    recorded_messages = {e["message"] for e in visible}
    unverifiable = [ln for ln in narrated_lines
                    if ln not in recorded_messages]

    max_gap = 0.0
    if len(visible) >= 2:
        ts = sorted(e["ts"] for e in visible)
        max_gap = max(b - a for a, b in zip(ts, ts[1:]))
    return {
        "unverifiable_claims": unverifiable,
        "max_gap_s": round(max_gap, 1),
        "gap_within_bound": max_gap <= heartbeat_bound_s * 1.25,
        "n_user_visible": len(visible),
    }

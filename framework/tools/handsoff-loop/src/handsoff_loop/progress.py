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
        event = {"ts": time.time(), "ts_mono": time.monotonic(),
                 "stage": stage, "message": str(message), **fields}
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


# Slice HB — the channel-post cadence: the run record keeps the
# HEARTBEAT_INTERVAL_S audit-grade fidelity, but channel posts (the
# Discord/Telegram ping) are throttled to this calmer interval to avoid
# notification fatigue (D-4) — with an IMMEDIATE post on stall onset and
# on the done surface, regardless of this throttle.
CHANNEL_INTERVAL_S = 300.0

# Slice HB — a stall is alive-but-not-progressing for this many
# consecutive beats (D-5; ~6 min at the 120s probe).
STALL_AFTER_BEATS = 3


def channel_say(notify_fn=print, *, prefix: str = ""):
    """The injection seam (D-6 / SAL-HB-1 / AC.HB.4): wrap an injected
    channel-post callable as a ``say``-shaped callable.

    ``notify_fn(text)`` is the workspace-wired channel post (the pos3
    workspace passes a closure over the shared channel module's
    ``post_to_active_channel``; loam ships the terminal default
    ``print``).  loam source NEVER imports a workspace channel file —
    the channel surface enters ONLY through this injected callable, so
    the framework stays general-purpose (H-3: a hard import of a
    workspace channel module is a fence violation).
    """
    notify = notify_fn if notify_fn is not None else print

    def _say(line: str) -> None:
        notify(f"{prefix}{line}" if prefix else line)

    return _say


def start_heartbeat(
    record: RunRecord,
    *,
    watch_dir: Path,
    say=print,
    interval_s: float = HEARTBEAT_INTERVAL_S,
    probe_fn=None,
    notify_fn=None,
    channel_interval_s: float = CHANNEL_INTERVAL_S,
    stall_after_beats: int = STALL_AFTER_BEATS,
    run_record_path: Path | None = None,
) -> "threading.Event":
    """Keep the user-visible surface alive during a long leg.

    Sealed substrate (AC.PRG.1 / AC.PRG.2 — UNCHANGED by default): every
    ``interval_s`` while the returned stop-event is unset, write-then-say
    a heartbeat to the run record + ``say`` whose message carries
    artifact-probe EVIDENCE (a heartbeat is a verified claim, not a
    vibe).  With the Slice-HB params at their defaults
    (``notify_fn=None``) this is byte-behaviour-identical to the sealed
    heartbeat — the AC.PRG suites stay green (AC.HB.4).

    Slice HB (AC.HB.1–.3) — additive, engaged ONLY when ``notify_fn`` is
    wired:

      * the probe is the cross-beat :func:`convergence.probe_progress`
        delta, so each beat carries PROGRESS evidence (did new work land
        since the last beat?), not bare liveness (AC.HB.2 / SAL-HB-2);
      * a periodic plain-language status is posted to the user's ACTIVE
        channel via ``notify_fn`` at the calmer ``channel_interval_s``
        cadence (D-4) — the run record keeps the full ``interval_s``
        fidelity, the channel gets a calmer ping (AC.HB.1).  With no
        ``notify_fn`` wired the status surfaces only on the main thread
        (the ``say`` terminal), which is the fallback AC.HB.1 names;
      * when progress flatlines for ``stall_after_beats`` consecutive
        beats the heartbeat surfaces a DISTINCT stall message (different
        from the normal progress beat) so the user can tell "moving"
        from "stuck" (AC.HB.3) — the stall post fires IMMEDIATELY on
        onset, bypassing the channel throttle.

    Returns the stop event; callers set it when the leg completes.
    """
    from .convergence import probe_liveness, probe_progress

    stop = threading.Event()
    record_path = (Path(run_record_path) if run_record_path is not None
                   else record.path)

    def _beat() -> None:
        prev: dict | None = None
        last_channel_post = 0.0
        stalled = False  # tracks stall ONSET so it posts once, distinctly
        while not stop.wait(interval_s):
            if probe_fn is not None:
                state = probe_fn(Path(watch_dir))
                progressed = state.get("progressed_since_last")
                stall_beats = state.get("stall_beats", 0)
            elif notify_fn is not None:
                state = probe_progress(
                    Path(watch_dir), prev=prev,
                    run_record_path=record_path)
                progressed = state.get("progressed_since_last")
                stall_beats = state.get("stall_beats", 0)
                prev = state
            else:
                # Sealed default path (AC.PRG.* byte-preserved).
                state = probe_liveness(Path(watch_dir))
                progressed = None
                stall_beats = 0

            is_stall = stall_beats >= stall_after_beats
            if is_stall:
                msg = ("Heads up — the build is still alive but hasn't "
                       "written anything new for a while "
                       f"({state.get('progress_evidence', state['evidence'])}). "
                       "Watching; I'll say so the moment it moves again.")
            elif progressed:
                msg = ("Still working — new progress just landed on disk "
                       f"({state.get('progress_evidence', state['evidence'])}).")
            elif state.get("alive"):
                msg = ("Still working — progress is actively landing "
                       f"on disk ({state['evidence']}).")
            else:
                msg = ("Still here — the current step is running and "
                       "hasn't written new files yet "
                       f"({state['evidence']}).")
            # Write-then-say: the run record carries the claim before the
            # user sees it (AC.PRG.2 / AC.HB.4 — intact for every line,
            # channel-posted or not).
            record.narrate("heartbeat", msg, say=say, liveness=state,
                           is_stall=is_stall,
                           progressed_since_last=progressed)

            # AC.HB.1/.3 — the channel surface (injected): throttled
            # periodic post, but an IMMEDIATE post on stall onset.
            if notify_fn is not None:
                now = time.monotonic()
                stall_onset = is_stall and not stalled
                due = (now - last_channel_post) >= channel_interval_s
                if stall_onset or due or last_channel_post == 0.0:
                    notify_fn(msg)
                    last_channel_post = now
                stalled = is_stall

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
    "max_gap_wall_s": float, "gap_clock": str,
    "gap_within_bound": bool, "n_user_visible": int}``:

      * every narrated line must exist verbatim as a user-visible
        run-record event (a said-but-never-recorded line is a
        fabricated progress claim);
      * the max gap between consecutive user-visible events across
        the active window (first event → verdict event) must stay
        within the heartbeat bound (a small grace factor covers
        scheduler jitter, not silence).

    AC.PRG.1's bound covers ACTIVE work, so the bound is checked on
    the MONOTONIC clock (``ts_mono``) when the record carries it —
    the same clock the heartbeat scheduler runs on, and one that does
    not advance while the OS has the whole process suspended (system
    sleep).  Wall-clock counts suspension as silence and manufactures
    breaches no watching human experienced and no emitter could
    physically have prevented (OA live run 2's 415.1s "gap" was 355s
    of pmset-verified macOS maintenance sleep).  The wall-clock max
    gap is still reported (``max_gap_wall_s``) so suspension is
    visible, never hidden; records without ``ts_mono`` (older runs)
    fall back to wall-clock and say so via ``gap_clock``.
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
    max_wall_gap = 0.0
    gap_clock = "wall"
    if len(visible) >= 2:
        wall = sorted(e["ts"] for e in visible)
        max_wall_gap = max(b - a for a, b in zip(wall, wall[1:]))
        if all("ts_mono" in e for e in visible):
            mono = sorted(e["ts_mono"] for e in visible)
            max_gap = max(b - a for a, b in zip(mono, mono[1:]))
            gap_clock = "monotonic"
        else:
            max_gap = max_wall_gap
    return {
        "unverifiable_claims": unverifiable,
        "max_gap_s": round(max_gap, 1),
        "max_gap_wall_s": round(max_wall_gap, 1),
        "gap_clock": gap_clock,
        "gap_within_bound": max_gap <= heartbeat_bound_s * 1.25,
        "n_user_visible": len(visible),
    }

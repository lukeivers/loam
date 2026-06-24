"""AC.HB.3 — a stall (alive-but-not-progressing) is detected and
surfaced distinctly.

When the build process is alive but no new artifact / run-record line
has landed for >= K consecutive probes, the heartbeat surfaces a
DISTINCT stall message (different from the normal progress beat), so
the user can tell "moving" from "stuck."  The stall post fires
IMMEDIATELY on onset, bypassing the channel throttle.

Outcome, not method: asserts a distinct stall surface on flatlined
progress; does not prescribe the threshold mechanism.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.progress import (  # noqa: E402
    STALL_AFTER_BEATS,
    RunRecord,
    start_heartbeat,
)


def test_stall_threshold_is_a_named_constant():
    assert STALL_AFTER_BEATS >= 1


def test_stall_is_surfaced_distinctly_after_flatline(tmp_path):
    # A run dir whose artifacts NEVER change: the process is "alive"
    # (a fresh-enough file exists) but nothing new lands. After K beats
    # of no progress the heartbeat must surface a DISTINCT stall message.
    said = []
    channel = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "frozen.txt").write_text("never changes", encoding="utf-8")

    stop = start_heartbeat(
        rec, watch_dir=watch, say=said.append,
        interval_s=0.02, channel_interval_s=100.0,
        stall_after_beats=2, notify_fn=channel.append)
    try:
        # Wait for enough beats that a stall must have been detected.
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if any(e.get("is_stall")
                   for e in rec.events() if e.get("stage") == "heartbeat"):
                break
            time.sleep(0.02)
    finally:
        stop.set()

    hb_events = [e for e in rec.events() if e.get("stage") == "heartbeat"]
    stall_events = [e for e in hb_events if e.get("is_stall")]
    normal_events = [e for e in hb_events if not e.get("is_stall")]
    assert stall_events, "no stall was detected on a flatlined run"
    # The stall message is DISTINCT from a normal beat (different text).
    stall_text = stall_events[0]["message"]
    assert stall_text not in {e["message"] for e in normal_events}
    assert "hasn't written anything new" in stall_text

    # AC.HB.3 + AC.HB.1: the stall fired an IMMEDIATE channel post even
    # though the channel throttle (100s) had not elapsed — the user is
    # told they are stuck without waiting for the next cadence window.
    assert any("hasn't written anything new" in p for p in channel), (
        "stall onset did not bypass the channel throttle")


def test_progress_resets_the_stall_counter(tmp_path):
    # If new work lands after a partial flatline, the stall counter
    # resets — the user is told "moving again," not "still stuck."
    from handsoff_loop.convergence import probe_progress

    run = tmp_path / "run"
    run.mkdir()
    p = probe_progress(run, prev=None)
    p = probe_progress(run, prev=p)   # no progress → stall_beats 1
    p = probe_progress(run, prev=p)   # still none → stall_beats 2
    assert p["stall_beats"] == 2
    time.sleep(0.02)
    (run / "new.txt").write_text("moved", encoding="utf-8")
    p = probe_progress(run, prev=p)   # progress → reset
    assert p["progressed_since_last"] is True
    assert p["stall_beats"] == 0

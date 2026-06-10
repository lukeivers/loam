"""AC.PRG.1 — plain-language stage updates + the heartbeat bound (S5).

  * throughout a run the user receives plain-language stage updates
    (understanding → asking → researching → planning → building →
    checking → verdict), each saying what is happening AND what comes
    next;
  * during long legs, no user-visible silence exceeds the NAMED
    heartbeat interval while work is active (the bound is a named
    constant; the heartbeat emitter fires within it and keeps firing
    until stopped).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.progress import (  # noqa: E402
    HEARTBEAT_INTERVAL_S,
    STAGES,
    RunRecord,
    start_heartbeat,
)


def test_stage_vocabulary_covers_the_whole_path():
    for stage in ("understanding", "asking", "researching", "planning",
                  "building", "checking", "verdict"):
        assert stage in STAGES


def test_updates_say_what_is_happening_and_what_comes_next(tmp_path):
    said = []
    rec = RunRecord(tmp_path)
    rec.narrate("understanding",
                "Reading your ask to make sure I build the right thing.",
                say=said.append,
                next_step="I'll check how this work is usually done.")
    assert len(said) == 1
    assert "Reading your ask" in said[0]
    assert "Next: I'll check how this work is usually done." in said[0]


def test_heartbeat_bound_is_named_and_heartbeats_fire_within_it(tmp_path):
    assert HEARTBEAT_INTERVAL_S > 0
    said = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "artifacts"
    watch.mkdir()
    (watch / "work.log").write_text("active", encoding="utf-8")
    stop = start_heartbeat(
        rec, watch_dir=watch, say=said.append, interval_s=0.05)
    try:
        deadline = time.monotonic() + 2.0
        while len(said) < 3 and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        stop.set()
    # >=3 beats well within 2s at a 0.05s interval: the emitter fires
    # within the configured bound and KEEPS firing until stopped.
    assert len(said) >= 3
    assert all("disk" in s for s in said)  # evidence-carrying, not vibes
    n_before = len(said)
    time.sleep(0.2)
    assert len(said) == n_before  # stopped means stopped


def test_unknown_stage_is_refused(tmp_path):
    rec = RunRecord(tmp_path)
    try:
        rec.emit("vibing", "nope")
    except ValueError as exc:
        assert "stage vocabulary" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown stage accepted")

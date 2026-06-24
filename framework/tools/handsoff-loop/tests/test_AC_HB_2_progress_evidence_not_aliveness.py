"""AC.HB.2 — heartbeats carry artifact-probe PROGRESS evidence, not
bare aliveness.

Every surfaced heartbeat message carries evidence derived from the
artifact probe (newest-artifact age + whether new work landed since
the last beat) — never a bare "still working" with no probe state
behind it.  Honors ``feedback_dead_agent_detection_via_artifact_probe``
(probe the disk artifacts, never the poller's "still running") and
makes the SAL-HB-2 distinction concrete: liveness ("is anything
fresh?") vs PROGRESS ("did something NEW land since I last looked?").

Outcome, not method: any probe that reads disk artifacts (mtime, size,
line-count) passes; the test never prescribes the probe internals.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.convergence import probe_progress  # noqa: E402
from handsoff_loop.progress import RunRecord, start_heartbeat  # noqa: E402


def test_progress_is_the_cross_beat_delta_not_bare_liveness(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    rec = run / "run_record.jsonl"
    rec.write_text("", encoding="utf-8")

    # First probe: no prior state → progressed is None (neither progress
    # nor stall — there is nothing to delta against yet).
    p0 = probe_progress(run, prev=None, run_record_path=rec)
    assert p0["progressed_since_last"] is None
    assert p0["stall_beats"] == 0

    # A new artifact lands → the next probe reports PROGRESS (mtime
    # advanced), distinct from liveness.
    time.sleep(0.02)
    (run / "step1.txt").write_text("work", encoding="utf-8")
    p1 = probe_progress(run, prev=p0, run_record_path=rec)
    assert p1["progressed_since_last"] is True
    assert p1["stall_beats"] == 0
    assert "landed" in p1["progress_evidence"]

    # Nothing new lands → NOT progress even though the process is alive;
    # the stall counter accrues.
    p2 = probe_progress(run, prev=p1, run_record_path=rec)
    assert p2["progressed_since_last"] is False
    assert p2["stall_beats"] == 1


def test_run_record_growth_counts_as_progress(tmp_path):
    # D-5's OTHER progress signal: the run record gaining a line is
    # progress even if no new artifact file appears.
    run = tmp_path / "run"
    run.mkdir()
    rec = run / "run_record.jsonl"
    rec.write_text("line1\n", encoding="utf-8")
    p0 = probe_progress(run, prev=None, run_record_path=rec)
    rec.write_text("line1\nline2\n", encoding="utf-8")
    p1 = probe_progress(run, prev=p0, run_record_path=rec)
    assert p1["progressed_since_last"] is True
    assert "run record gained a line" in p1["progress_evidence"]


def test_every_surfaced_beat_carries_probe_evidence(tmp_path):
    # No heartbeat message is a bare "still working" — each carries the
    # probe state behind it (evidence string), and the event records the
    # full liveness/progress dict.
    said = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "seed.txt").write_text("x", encoding="utf-8")
    stop = start_heartbeat(
        rec, watch_dir=watch, say=said.append,
        interval_s=0.03, channel_interval_s=0.0,
        notify_fn=lambda s: None)
    try:
        deadline = time.monotonic() + 2.0
        while len(said) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        stop.set()
    assert len(said) >= 2
    # Evidence-carrying, not vibes: every line references disk state.
    assert all(("disk" in s or "run-record" in s or "artifact" in s)
               for s in said)
    events = [e for e in rec.events()
              if e.get("stage") == "heartbeat" and e.get("user_visible")]
    assert events, "no heartbeat events recorded"
    assert all("liveness" in e for e in events)

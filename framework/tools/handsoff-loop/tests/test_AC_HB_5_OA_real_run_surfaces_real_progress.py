"""AC.HB.5 (outcome-altitude: true) — a real build run surfaces a real
progress signal end-to-end.

Invoking the production heartbeat entry point on a real run dir with
real artifacts landing on disk (NO pre-arranged run-record state), with
a capturing ``notify_fn``, yields >= 1 captured progress post whose
evidence reflects an actual artifact that landed DURING the run, AND
the post-run ``audit_progress`` reports ``gap_within_bound: true``.

Outcome-altitude: the production entry point (``start_heartbeat``) runs
against a live run with no pre-arranged state — a real worker thread
writes real files to a real run dir while the heartbeat watches, and a
real ``notify_fn`` captures the channel surface.  Nothing is staged in
the run record beforehand; the captured progress post is a genuine
end-to-end signal off real disk activity, not a fixture.  The held-out
verifier is ``audit_progress`` (the sealed AC.PRG.OA auditor) — it never
saw the heartbeat's emission, it only replays the run record after the
fact.

Per docs/plans/handsoff-design-first-and-build-heartbeat.md §5.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.progress import (  # noqa: E402
    HEARTBEAT_INTERVAL_S,
    RunRecord,
    audit_progress,
    start_heartbeat,
)


def test_real_run_surfaces_real_artifact_progress_end_to_end(tmp_path):
    run_dir = tmp_path / "runs" / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True)
    record = RunRecord(run_dir)  # NO pre-arranged run-record events

    channel_posts: list[str] = []
    say_lines: list[str] = []

    def notify_fn(text: str) -> None:
        channel_posts.append(text)

    def say(line: str) -> None:
        say_lines.append(line)

    # A real worker thread that writes real files to the run dir over
    # time — the genuine "artifacts landing during the run" the heartbeat
    # must catch as progress (not a pre-staged fixture).
    worker_done = threading.Event()
    landed: list[str] = []

    def _worker() -> None:
        for i in range(5):
            if worker_done.wait(0.04):
                return
            p = run_dir / f"artifact_{i}.txt"
            p.write_text(f"real work unit {i}\n", encoding="utf-8")
            landed.append(str(p))

    # Production heartbeat entry point against the live run dir.
    stop = start_heartbeat(
        record, watch_dir=run_dir, say=say,
        interval_s=0.03, channel_interval_s=0.0,
        notify_fn=notify_fn)
    worker = threading.Thread(target=_worker, name="hb5-worker", daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            # Stop once we have both real artifacts on disk and a captured
            # progress post that reflects one.
            if len(landed) >= 3 and any(
                "landed on disk" in p for p in channel_posts):
                break
            time.sleep(0.02)
    finally:
        worker_done.set()
        stop.set()
        worker.join(timeout=1.0)

    # >= 1 captured progress post reflecting an ACTUAL artifact that
    # landed during the run.
    progress_posts = [p for p in channel_posts if "landed on disk" in p]
    assert progress_posts, (
        "no captured progress post reflected a real artifact landing "
        f"during the run; posts={channel_posts}")
    assert landed, "the worker never wrote a real artifact"

    # The post-run audit (held-out verifier) reports gap_within_bound.
    audit = audit_progress(
        record.path, say_lines, heartbeat_bound_s=HEARTBEAT_INTERVAL_S)
    assert audit["gap_within_bound"] is True, (
        f"post-run audit gap exceeded the bound: {audit}")
    assert audit["unverifiable_claims"] == [], (
        "a surfaced line was never recorded (write-then-say breach): "
        f"{audit['unverifiable_claims']}")
    assert audit["n_user_visible"] >= 1

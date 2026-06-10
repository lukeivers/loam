"""AC.PRG.2 — every progress claim verifies against run-record state.

Narration-is-not-action, enforced on this surface:

  * write-then-say is STRUCTURAL: the run record carries the event
    before the ``say`` callback ever sees the line (verified by a
    callback that reads the record from inside the say);
  * a narrated line with no run-record event is a fabricated claim —
    the after-the-fact audit names it;
  * heartbeats carry artifact-probe liveness evidence in the event;
  * waits are stated honestly with rough plain-language time
    expectations.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.progress import (  # noqa: E402
    RunRecord,
    audit_progress,
    start_heartbeat,
)


def test_write_then_say_is_structural(tmp_path):
    rec = RunRecord(tmp_path)
    seen_in_record_at_say_time = []

    def _say(line):
        on_disk = rec.path.read_text(encoding="utf-8")
        seen_in_record_at_say_time.append(line in on_disk)

    rec.narrate("building", "Starting the build now.", say=_say,
                expected_wait_plain="this usually takes a few minutes")
    assert seen_in_record_at_say_time == [True]


def test_honest_wait_expectation_is_carried(tmp_path):
    said = []
    rec = RunRecord(tmp_path)
    rec.narrate("researching",
                "Looking up how practitioners handle this.",
                say=said.append,
                expected_wait_plain="usually a minute or two")
    assert "(usually a minute or two)" in said[0]
    ev = rec.events()[0]
    assert ev["expected_wait_plain"] == "usually a minute or two"


def test_audit_names_fabricated_claims(tmp_path):
    said = []
    rec = RunRecord(tmp_path)
    rec.narrate("building", "Real progress line.", say=said.append)
    said.append("Fabricated line the record never carried.")
    audit = audit_progress(rec.path, said)
    assert audit["unverifiable_claims"] == [
        "Fabricated line the record never carried."]


def test_audit_passes_a_fully_recorded_narration(tmp_path):
    said = []
    rec = RunRecord(tmp_path)
    rec.narrate("understanding", "Reading the ask.", say=said.append)
    rec.narrate("verdict", "Done, honestly.", say=said.append)
    audit = audit_progress(rec.path, said)
    assert audit["unverifiable_claims"] == []
    assert audit["n_user_visible"] == 2
    assert audit["gap_within_bound"] is True


def test_audit_flags_over_the_bound_silence(tmp_path):
    rec = RunRecord(tmp_path)
    rec.emit("understanding", "start", user_visible=True)
    # Forge a record with a 10-minute silent gap.
    ev = {"ts": time.time() + 600, "stage": "verdict",
          "message": "end", "user_visible": True}
    with rec.path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev) + "\n")
    audit = audit_progress(rec.path, [], heartbeat_bound_s=120.0)
    assert audit["max_gap_s"] >= 599
    assert audit["gap_within_bound"] is False


def test_heartbeat_events_carry_liveness_evidence(tmp_path):
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "w"
    watch.mkdir()
    (watch / "a.log").write_text("x", encoding="utf-8")
    stop = start_heartbeat(rec, watch_dir=watch, say=lambda s: None,
                           interval_s=0.05)
    try:
        deadline = time.monotonic() + 2.0
        while not rec.events() and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        stop.set()
    beats = [e for e in rec.events() if e["stage"] == "heartbeat"]
    assert beats
    assert beats[0]["liveness"]["alive"] is True
    assert "newest_artifact" in beats[0]["liveness"]

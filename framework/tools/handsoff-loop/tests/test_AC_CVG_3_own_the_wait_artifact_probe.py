"""AC.CVG.3 — own-the-wait: liveness from run artifacts (S4).

While a build leg is in flight, the dispatching session tracks
liveness from RUN ARTIFACTS (artifact-probe-class evidence — newest
artifact mtime), never from poller-cadence inference or self-reports;
the probe result is a progress state the S5 surface consumes.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.convergence import probe_liveness  # noqa: E402


def test_no_artifacts_is_honestly_not_alive(tmp_path):
    state = probe_liveness(tmp_path / "nothing-here")
    assert state["alive"] is False
    assert state["evidence"] == "no run artifacts on disk"


def test_fresh_artifact_is_alive_with_named_evidence(tmp_path):
    sub = tmp_path / "artifacts" / "deep"
    sub.mkdir(parents=True)
    f = sub / "sub_0_build.transcript"
    f.write_text("working...", encoding="utf-8")
    state = probe_liveness(tmp_path)
    assert state["alive"] is True
    # The evidence NAMES the artifact and its mtime age — Tier-0
    # artifact-probe evidence, not an inference.
    assert state["newest_artifact"] == str(f)
    assert state["artifact_age_s"] is not None
    assert "mtime" in state["evidence"]


def test_stale_artifacts_are_not_alive(tmp_path):
    f = tmp_path / "old.transcript"
    f.write_text("long ago", encoding="utf-8")
    old = time.time() - 4000
    os.utime(f, (old, old))
    state = probe_liveness(tmp_path, stale_after_s=300.0)
    assert state["alive"] is False
    assert state["artifact_age_s"] > 3000


def test_probe_is_consumable_as_a_progress_state(tmp_path):
    (tmp_path / "x.log").write_text("x", encoding="utf-8")
    state = probe_liveness(tmp_path)
    # The S5 contract: a dict with alive/evidence/probed_at fields.
    assert {"alive", "evidence", "newest_artifact",
            "artifact_age_s", "probed_at"} <= set(state)

"""AC.HB.4 — the heartbeat composes the existing alerting infra via an
injected notify_fn; no sealed honesty control weakens.

Three properties:

  * the channel surface enters ONLY through the injected ``notify_fn``
    (SAL-HB-1 / H-3) — loam source imports NO workspace channel module
    (``channel_notify``, ``stopfailure_alert``, ``refusal_watchdog``);
  * the sealed AC.PRG.2 write-then-say contract is intact: every
    channel-surfaced line exists in the run record BEFORE it is shown
    (a said-but-never-recorded line is a fabricated progress claim);
  * the sealed non-interactive heartbeat path is byte-behaviour-
    preserved: with ``notify_fn=None`` (the sealed default) the
    heartbeat behaves exactly as the AC.PRG suites pin it.

Outcome, not method: asserts composition-via-injection + zero honesty
regression; does not prescribe the channel module.

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
    HEARTBEAT_INTERVAL_S,
    RunRecord,
    audit_progress,
    channel_say,
    start_heartbeat,
)

# Workspace-only channel modules (3db9360 — "do not port from here"):
# loam source must NEVER import any of these (H-3 / SAL-HB-1).
_FORBIDDEN_WORKSPACE_IMPORTS = (
    "channel_notify",
    "stopfailure_alert",
    "refusal_watchdog",
    "post_to_active_channel",
    "_detect_active_channel",
)


def test_loam_source_imports_no_workspace_channel_module():
    # The channel surface is injection-only: no loam source file under
    # handsoff_loop references the pos3-only channel modules. A hard
    # import would be the H-3 fence violation.
    src_root = _SRC / "handsoff_loop"
    offenders = []
    for py in src_root.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for token in _FORBIDDEN_WORKSPACE_IMPORTS:
            # "import <token>" / "from ... import <token>" — an actual
            # dependency, not a mention in a comment/docstring naming the
            # seam. We scan for import-statement shapes specifically.
            for line in text.splitlines():
                stripped = line.strip()
                if not (stripped.startswith("import ")
                        or stripped.startswith("from ")):
                    continue
                if token in stripped:
                    offenders.append(f"{py.name}: {stripped}")
    assert not offenders, (
        "loam source hard-imports a workspace channel module "
        f"(H-3 violation): {offenders}")


def test_write_then_say_holds_for_channel_surfaced_lines(tmp_path):
    # AC.PRG.2 intact under the channel-aware heartbeat: every channel
    # post also exists in the run record (write-then-say). We capture the
    # channel surface and replay it through audit_progress.
    channel = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "seed.txt").write_text("x", encoding="utf-8")
    say = channel_say(channel.append)
    stop = start_heartbeat(
        rec, watch_dir=watch, say=say,
        interval_s=0.03, channel_interval_s=0.0,
        notify_fn=channel.append)
    try:
        deadline = time.monotonic() + 2.0
        while len(channel) < 4 and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        stop.set()
    assert channel, "no channel-surfaced lines to audit"
    # Every line shown on the channel exists verbatim in the run record.
    audit = audit_progress(rec.path, channel,
                           heartbeat_bound_s=HEARTBEAT_INTERVAL_S)
    assert audit["unverifiable_claims"] == [], (
        "a channel-surfaced line was never written to the run record "
        f"(fabricated claim): {audit['unverifiable_claims']}")


def test_non_interactive_default_is_byte_preserved(tmp_path):
    # notify_fn=None (the sealed default): the heartbeat behaves exactly
    # as the AC.PRG suites pin it — evidence-carrying beats to the say
    # terminal, no channel surface, no stall/progress fields driving the
    # message. (The AC.PRG suites themselves are the regression gate;
    # here we assert the default path still fires evidence-carrying beats
    # with no notify_fn wired.)
    said = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "work.log").write_text("active", encoding="utf-8")
    stop = start_heartbeat(rec, watch_dir=watch, say=said.append,
                           interval_s=0.05)
    try:
        deadline = time.monotonic() + 2.0
        while len(said) < 3 and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        stop.set()
    assert len(said) >= 3
    assert all("disk" in s for s in said)  # the sealed AC.PRG.1 shape

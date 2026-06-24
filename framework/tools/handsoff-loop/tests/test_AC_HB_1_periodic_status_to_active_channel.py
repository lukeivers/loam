"""AC.HB.1 — the build leg surfaces periodic progress to the user's
active channel, with a terminal fallback when no channel is wired.

During a long build leg, with a ``notify_fn`` wired to a channel, the
user receives periodic plain-language status posts on the channel they
are actually on (the injected ``notify_fn`` IS the active-channel
surface — the workspace wires it to ``post_to_active_channel``).  With
NO ``notify_fn`` wired, the status surfaces on the main thread (the
``say`` terminal) — the fallback.

Outcome, not method: asserts the user sees periodic status on the right
surface; does not prescribe the post mechanism (the channel surface is
an injected callable — a Discord post, a Telegram post, or a test
double all pass).

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
    RunRecord,
    channel_say,
    start_heartbeat,
)


def _spin_until(predicate, *, timeout_s=2.0, step_s=0.02):
    deadline = time.monotonic() + timeout_s
    while not predicate() and time.monotonic() < deadline:
        time.sleep(step_s)


def test_channel_say_routes_through_the_injected_notify_fn():
    # The injection seam (D-6): channel_say wraps an injected callable;
    # loam ships print as the terminal default, the workspace passes its
    # own channel-post closure. No workspace import anywhere.
    posted = []
    say = channel_say(posted.append, prefix="[build] ")
    say("progress landed")
    assert posted == ["[build] progress landed"]
    # Default is the terminal print (no channel wired) — does not raise.
    channel_say()("terminal fallback ok")


def test_periodic_status_posts_to_the_channel_when_wired(tmp_path):
    # With notify_fn wired, the heartbeat posts periodic status to the
    # channel surface (here a capturing list standing in for the active
    # Discord/Telegram channel).
    channel_posts = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "seed.txt").write_text("start", encoding="utf-8")
    stop = start_heartbeat(
        rec, watch_dir=watch, say=lambda s: None,
        interval_s=0.03, channel_interval_s=0.0,
        notify_fn=channel_posts.append)
    try:
        _spin_until(lambda: len(channel_posts) >= 2)
    finally:
        stop.set()
    assert len(channel_posts) >= 2, "no periodic channel status posted"
    assert all(isinstance(p, str) and p for p in channel_posts)


def test_terminal_fallback_when_no_channel_is_wired(tmp_path):
    # No notify_fn → status surfaces on the main-thread say terminal,
    # never on a channel (there is none). This is the AC.HB.1 fallback.
    said = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "seed.txt").write_text("start", encoding="utf-8")
    stop = start_heartbeat(
        rec, watch_dir=watch, say=said.append,
        interval_s=0.03, notify_fn=None)
    try:
        _spin_until(lambda: len(said) >= 2)
    finally:
        stop.set()
    assert len(said) >= 2, "no terminal status surfaced on the fallback"


def test_channel_cadence_is_calmer_than_the_record_cadence(tmp_path):
    # D-4: the run record keeps the full interval_s fidelity, but channel
    # posts are throttled to the calmer channel_interval_s — fewer channel
    # pings than run-record beats over the same window.
    record_beats = []
    channel_posts = []
    rec = RunRecord(tmp_path / "run")
    watch = tmp_path / "run"
    (watch / "seed.txt").write_text("start", encoding="utf-8")
    stop = start_heartbeat(
        rec, watch_dir=watch, say=record_beats.append,
        interval_s=0.02, channel_interval_s=10.0,
        notify_fn=channel_posts.append)
    try:
        _spin_until(lambda: len(record_beats) >= 5, timeout_s=2.0)
    finally:
        stop.set()
    # Many record beats (audit-grade fidelity) but the channel got only
    # the single immediate post (the 10s throttle never elapsed).
    assert len(record_beats) >= 5
    assert len(channel_posts) < len(record_beats)
    assert len(channel_posts) >= 1  # the immediate first post still fires

"""D5 — Notification threshold.

Acceptance (brief):
- Synthetic episodes hitting each of the four threshold conditions
  produce notifications at the correct moment.
- Duplicate-threshold-crossings within a single episode are suppressed
  (UUID dedup).
- Auth-broken fires Tier 1 immediately on detection; all other modes
  fire Tier 2 on threshold.
- Resume fires a second notification per episode.
- Notification channel is the primary-persona layer's one-on-one
  surface. Group channels rejected at construction per v1.2 R15.
"""

from __future__ import annotations

import pytest

from loam.graceful_degradation import (
    DegradationConfig,
    DegradationMode,
    DegradationNotification,
    DegradationNotifier,
    NotificationTier,
)
from loam.graceful_degradation.notification import (
    DegradationChannel,
    NarrativeRenderer,
    ThresholdEvaluator,
    ThresholdTrigger,
    tier_for_mode,
)
from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel

from .fakes import make_capture_channel


def test_degradation_channel_rejects_group_at_construction() -> None:
    async def send(text: str) -> None:
        pass

    with pytest.raises(ValueError):
        DegradationChannel(
            kind=ChannelKind.terminal,
            name="group-chat",
            send=send,
            is_group=True,
        )


def test_notifier_rejects_group_channel_at_construction() -> None:
    async def send(text: str) -> None:
        pass

    # `is_group` must be False for construction to succeed; trying to
    # sneak a group in requires constructing OneOnOneChannel directly
    # with is_group=True, which itself raises. We verify the notifier
    # guard wouldn't accept even a hypothetical group channel.
    # Here we patch the channel's is_group after construction; the
    # notifier's __post_init__ rejects.
    ch = DegradationChannel(
        kind=ChannelKind.terminal,
        name="c",
        send=send,
        is_group=False,
    )
    # Direct mutation is hard on a frozen dataclass; but the notifier
    # also guards at construction. Simulate by building a custom
    # sequence that falsely claims is_group=True.
    class _G:
        is_group = True
        name = "g"

    with pytest.raises(ValueError):
        DegradationNotifier(channels=[_G()])  # type: ignore[arg-type]


async def test_threshold_fires_on_time() -> None:
    cfg = DegradationConfig()
    ev = ThresholdEvaluator(cfg)
    trigger = ev.evaluate(
        mode=DegradationMode.down,
        episode_started_at=0.0,
        now=400.0,  # > 300s default
        paused_scope_count=1,
        any_user_relevant_scope=False,
    )
    assert trigger == ThresholdTrigger.time


async def test_threshold_fires_on_count() -> None:
    cfg = DegradationConfig()
    ev = ThresholdEvaluator(cfg)
    trigger = ev.evaluate(
        mode=DegradationMode.down,
        episode_started_at=0.0,
        now=10.0,  # too early on time
        paused_scope_count=3,
        any_user_relevant_scope=False,
    )
    assert trigger == ThresholdTrigger.count


async def test_threshold_fires_on_criticality() -> None:
    cfg = DegradationConfig()
    ev = ThresholdEvaluator(cfg)
    trigger = ev.evaluate(
        mode=DegradationMode.down,
        episode_started_at=0.0,
        now=5.0,
        paused_scope_count=1,
        any_user_relevant_scope=True,
    )
    assert trigger == ThresholdTrigger.criticality


async def test_threshold_auth_broken_always_fires() -> None:
    cfg = DegradationConfig()
    ev = ThresholdEvaluator(cfg)
    trigger = ev.evaluate(
        mode=DegradationMode.auth_broken,
        episode_started_at=0.0,
        now=0.0,
        paused_scope_count=0,
        any_user_relevant_scope=False,
    )
    assert trigger == ThresholdTrigger.auth_broken


async def test_threshold_none_below_all_conditions() -> None:
    cfg = DegradationConfig()
    ev = ThresholdEvaluator(cfg)
    trigger = ev.evaluate(
        mode=DegradationMode.down,
        episode_started_at=0.0,
        now=10.0,
        paused_scope_count=1,
        any_user_relevant_scope=False,
    )
    assert trigger is None


def test_tier_for_mode_auth_broken_is_tier_1() -> None:
    cfg = DegradationConfig()
    assert tier_for_mode(cfg, DegradationMode.auth_broken) == NotificationTier.tier_1


def test_tier_for_mode_default_is_tier_2() -> None:
    cfg = DegradationConfig()
    assert tier_for_mode(cfg, DegradationMode.down) == NotificationTier.tier_2
    assert tier_for_mode(cfg, DegradationMode.rate_limited) == NotificationTier.tier_2


async def test_notifier_delivers_to_first_active_channel() -> None:
    ch, sent = make_capture_channel("terminal", is_active=True)
    notifier = DegradationNotifier(channels=[ch])
    notif = DegradationNotification(
        episode_id="ep-1",
        tier=NotificationTier.tier_2,
        threshold_triggered=ThresholdTrigger.time,
        text="degraded",
        kind="alert",
    )
    delivered = await notifier.send(notif)
    assert delivered is True
    assert sent == ["degraded"]


async def test_notifier_queues_if_no_active_channel() -> None:
    ch, sent = make_capture_channel("terminal", is_active=False)
    notifier = DegradationNotifier(channels=[ch])
    notif = DegradationNotification(
        episode_id="ep-1",
        tier=NotificationTier.tier_2,
        threshold_triggered=ThresholdTrigger.time,
        text="degraded",
        kind="alert",
    )
    delivered = await notifier.send(notif)
    assert delivered is False
    assert notifier._pending_queue
    assert sent == []


async def test_narrative_uses_template_for_down_mode() -> None:
    cfg = DegradationConfig()
    renderer = NarrativeRenderer(cfg=cfg, client=None)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.down,
        signal="connection_error",
        policy="pause_all",
        paused_scope_count=2,
    )
    # Template fields present
    assert "claude upstream degraded" in text.lower() or "pos" in text.lower()
    assert "connection_error" in text
    assert "pause_all" in text


async def test_narrative_recovery_template() -> None:
    cfg = DegradationConfig()
    renderer = NarrativeRenderer(cfg=cfg, client=None)
    text = renderer.render_recovery(
        episode_id="ep",
        resumed_count=3,
        duration_seconds=120.0,
    )
    assert "3 scope" in text or "3 scope(s)" in text
    assert "120" in text

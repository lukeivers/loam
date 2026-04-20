"""Throttle / 80% warning — C14, C15."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from cost_governance import (
    CostConfig,
    CostLedger,
    CostNotifier,
    CostStore,
    RollingCeiling,
    SessionCeiling,
)

from .conftest import build_config, make_fake_channel, make_spec


def test_C14_warning_fires_once_per_crossing(store: CostStore) -> None:
    """Reservation at 85% triggers one warning; a second reservation at
    87% does NOT trigger a second (warning already fired for this
    (kind, axis, window) crossing until reset)."""
    ch, received = make_fake_channel()
    notifier = CostNotifier(channels=[ch])
    config = build_config(session_money=1000, warning_fraction=0.8)

    captured_notifs: list = []

    async def dispatch(notif) -> None:
        captured_notifs.append(notif)

    ledger = CostLedger(
        store=store, config=config, notifier=notifier, dispatch_fn=dispatch
    )

    # First reservation pushes to 850/1000 = 85% → warning.
    spec1 = make_spec(money_cents=850)
    asyncio.run(_reserve(ledger, spec1, "s1"))
    assert len(captured_notifs) == 1
    assert captured_notifs[0].kind == "ceiling_warning"

    # Second reservation would push to 850+50=900/1000 = 90% — still in
    # warning band, but warning already fired; should NOT fire again.
    # But this reservation would also succeed (900 < 1000).
    # Wait — first reservation is active; math is: committed 0 +
    # reserved 850 + declared 50 = 900.
    spec2 = make_spec(money_cents=50)
    asyncio.run(_reserve(ledger, spec2, "s2"))
    assert len(captured_notifs) == 1, (
        "warning fired more than once for the same crossing"
    )


def test_C14_warning_on_zero_pre_existing_spend(store: CostStore) -> None:
    """A scope that activates directly at >= 80% (cold start) still
    produces a warning — the rule is 'at the crossing', and going
    from 0 to >=80 IS a crossing.
    """
    ch, received = make_fake_channel()
    notifier = CostNotifier(channels=[ch])
    config = build_config(session_money=1000, warning_fraction=0.8)

    captured: list = []

    async def dispatch(notif) -> None:
        captured.append(notif)

    ledger = CostLedger(
        store=store, config=config, notifier=notifier, dispatch_fn=dispatch
    )
    spec = make_spec(money_cents=900)  # 90% from cold start
    asyncio.run(_reserve(ledger, spec, "s1"))
    assert len(captured) == 1


def test_C15_warning_fraction_configurable(store: CostStore) -> None:
    """Default is 0.8; user-set 0.5 fires earlier."""
    ch, received = make_fake_channel()
    notifier = CostNotifier(channels=[ch])
    config = build_config(session_money=1000, warning_fraction=0.5)

    captured: list = []

    async def dispatch(notif) -> None:
        captured.append(notif)

    ledger = CostLedger(
        store=store, config=config, notifier=notifier, dispatch_fn=dispatch
    )
    spec = make_spec(money_cents=600)  # 60% — above 0.5 cutoff
    asyncio.run(_reserve(ledger, spec, "s1"))
    assert len(captured) == 1


def test_C15_warning_fraction_refuses_invalid() -> None:
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=0.0)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=1.0)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=-0.5)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=1.5)
    # Valid values accepted.
    CostConfig(warning_fraction=0.5)


async def _reserve(ledger, spec, scope_id):
    """Reserve inside an async context so dispatch_fn's create_task fires."""
    ledger.reserve_or_refuse(spec, scope_id=scope_id)
    # Yield so scheduled tasks run.
    await asyncio.sleep(0)

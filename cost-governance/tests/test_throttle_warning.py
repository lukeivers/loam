"""Throttle / 80% warning — C14, C15."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from pydantic import ValidationError

from primary_persona.introduction import ChannelKind
from scope_of_work.events import BudgetDebited

from cost_governance import (
    CostChannel,
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


def test_C14_warning_emits_before_reservation_row_written(tmp_path: Path) -> None:
    """C14 ordering sub-behaviour: the `pos.cost.ceiling_warning`
    event is emitted BEFORE the `reservations` row is written.

    The assertion is a shared ordered trace across two documented
    public collaborators on `CostLedger`'s constructor surface: the
    injected `CostStore` (whose `insert_reservation` method is the
    ledger-row-write call-point) and the injected `dispatch_fn` sink
    (whose invocation marks the point at which the warning has been
    emitted into the outside world). Neither spy inspects a private
    attribute; the test observes the relative order in which the two
    public call-sites are exercised.

    Per odd-in-pos.md §5.2: "The emission precedes the ledger write.
    A test has to check both 'the warning was emitted' and 'the
    warning happened before the row appeared in `reservations`' —
    a sequencing assertion."
    """
    trace: list[str] = []

    class TracingStore(CostStore):
        def insert_reservation(self, r):  # type: ignore[override]
            trace.append("insert")
            super().insert_reservation(r)

    store = TracingStore(tmp_path / "cost.sqlite")
    try:
        config = build_config(session_money=1000, warning_fraction=0.8)

        # Capture the warning emission through the notifier surface.
        # Run `reserve_or_refuse` OUTSIDE a running event loop: under
        # that path `_fire_notification` invokes
        # `asyncio.run(notifier.send(notif))` synchronously (ledger.py
        # lines 350-355), so the send() completes before control
        # returns to `reserve_or_refuse`. The trace order then reflects
        # the ledger's ordering choice, not asyncio task scheduling.
        async def _send(_text: str) -> None:
            trace.append("warning")

        channel = CostChannel(
            kind=ChannelKind.personal_telegram,
            name="ordering-probe",
            send=_send,
            is_group=False,
            is_active=True,
        )
        notifier = CostNotifier(channels=[channel])

        ledger = CostLedger(store=store, config=config, notifier=notifier)
        # Cold-start scope activating at 85% of cap — triggers warning.
        spec = make_spec(money_cents=850)
        ledger.reserve_or_refuse(spec, scope_id="s1")

        assert trace == ["warning", "insert"], (
            f"expected warning emission before reservation row write, "
            f"got trace={trace!r}"
        )
    finally:
        store.close()


def test_C14_warning_fires_once_across_multiple_debits_in_same_scope(
    store: CostStore,
) -> None:
    """C14 "not repeatedly per debit" sub-behaviour: a scope that
    activates in the warning band and then accrues multiple debits
    which keep it in the warning band produces exactly ONE warning,
    not one warning per BudgetDebited event.

    The existing `test_C14_warning_fires_once_per_crossing` exercises
    the fire-once semantics across multiple *reservations* on the same
    crossing. This test exercises the `BudgetDebited` path — the
    failure mode C14's criterion text names explicitly — which the
    reservation-only test cannot reach.
    """
    ch, _received = make_fake_channel()
    notifier = CostNotifier(channels=[ch])
    config = build_config(session_money=1000, warning_fraction=0.8)

    captured: list = []

    async def dispatch(notif) -> None:
        captured.append(notif)

    ledger = CostLedger(
        store=store, config=config, notifier=notifier, dispatch_fn=dispatch
    )

    # Reserve at 85% of cap — one warning dispatched.
    spec = make_spec(money_cents=850, tokens=10_000)
    asyncio.run(_reserve(ledger, spec, "s1"))
    assert len(captured) == 1
    assert captured[0].kind == "ceiling_warning"

    # Now fire a stream of debits that keep the scope in the warning
    # band (80-100% of cap). An obvious buggy implementation would
    # re-check the threshold on every BudgetDebited and re-emit the
    # warning — C14 forbids that.
    for call_id in ("c1", "c2", "c3", "c4", "c5"):
        ledger._on_event(
            BudgetDebited(
                scope_id="s1",
                input_tokens=10,
                output_tokens=20,
                money_cents=10,
                call_id=call_id,
            )
        )

    warnings = [n for n in captured if n.kind == "ceiling_warning"]
    assert len(warnings) == 1, (
        f"warning fired {len(warnings)} times across 5 debits; "
        f"C14 requires exactly one per crossing, not per debit"
    )


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

# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""WS-A4 — subscription cap-% into the cost-governance ledger.

AC.CAPC.1 (★ outcome-altitude): three-region gate through the real
    `CostLedger.reserve_or_refuse` entry point — refuse / warn / silent.
AC.CAPC.2: `UsageUnavailable` fails open; the ledger record carries the
    categorical reason and NO numeric utilization.
AC.CAPC.3: default-OFF — no cap configured ⇒ the probe is never called
    (no regression to the existing time/token/money ceilings).
AC.CAPC.4: production-stake floor clamps the cap `warn_fraction` to 0.6
    at runtime without mutating the config source.
AC.CAPC.5: the TTL cache is what the gate consults — N reserves within
    the TTL trigger exactly one probe invocation.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from loam.orchestrator.ipc import ApplicationError
from loam.usage_window_guard import (
    UnavailableReason,
    UsageUnavailable,
    UsageWindows,
    Window,
)

from loam.cost_governance import (
    IPC_COST_CAP_CEILING_EXCEEDED,
    CachedCapProbe,
    CapCeiling,
    CostConfig,
    CostLedger,
    CostStore,
    SessionCeiling,
    apply_safety_profile_floor,
)

from .conftest import make_spec


# ---- helpers --------------------------------------------------------


def _windows(seven_day_pct: float) -> UsageWindows:
    """A successful probe reading with the given seven_day utilization
    (in the endpoint's native [0, 100] percentage scale)."""
    resets = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return UsageWindows(
        five_hour=Window(utilization=0.0, resets_at=resets),
        seven_day=Window(utilization=seven_day_pct, resets_at=resets),
    )


def _cap_config(
    *,
    warn_fraction: float,
    refuse_fraction: float,
    action: str = "refuse",
) -> CostConfig:
    """A config with NO session/rolling caps so only the cap ceiling gates."""
    return CostConfig(
        session=SessionCeiling(),
        rolling=[],
        cap_ceiling=CapCeiling(
            warn_fraction=warn_fraction,
            refuse_fraction=refuse_fraction,
            action=action,  # type: ignore[arg-type]
        ),
    )


def _fixed_probe(result) -> CachedCapProbe:
    return CachedCapProbe(reader=lambda: result)


# ---- AC.CAPC.1 — outcome-altitude: three-region gate ----------------


def test_AC_CAPC_1_above_refuse_is_refused(store: CostStore) -> None:
    """★ outcome-altitude. utilization above the refuse fraction refuses a
    dispatch through the production reserve path with the typed error, and
    NO reservation is written."""
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    ledger = CostLedger(
        store=store, config=config, cap_probe=_fixed_probe(_windows(90.0))
    )
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(make_spec(), scope_id="s1")
    assert exc.value.code == IPC_COST_CAP_CEILING_EXCEEDED
    assert exc.value.data["ceiling_kind"] == "cap"
    assert store.get_reservation("s1") is None
    assert ledger.last_cap_check is not None
    assert ledger.last_cap_check.outcome == "refuse"


def test_AC_CAPC_1_below_warn_proceeds_silently(store: CostStore) -> None:
    """★ outcome-altitude. Below the warn fraction the dispatch proceeds and
    the reservation lands; the recorded outcome is silent."""
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    ledger = CostLedger(
        store=store, config=config, cap_probe=_fixed_probe(_windows(30.0))
    )
    reservation = ledger.reserve_or_refuse(make_spec(), scope_id="s2")
    assert reservation is not None
    assert store.get_reservation("s2") is not None
    assert ledger.last_cap_check.outcome == "silent"


def test_AC_CAPC_1_between_proceeds_with_warning(store: CostStore) -> None:
    """★ outcome-altitude. Between warn and refuse the dispatch proceeds
    (reservation lands) but the recorded outcome is a warning."""
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    ledger = CostLedger(
        store=store, config=config, cap_probe=_fixed_probe(_windows(65.0))
    )
    reservation = ledger.reserve_or_refuse(make_spec(), scope_id="s3")
    assert reservation is not None
    assert store.get_reservation("s3") is not None
    assert ledger.last_cap_check.outcome == "warn"
    assert ledger.last_cap_check.utilization_fraction == pytest.approx(0.65)


def test_AC_CAPC_1_action_warn_never_refuses(store: CostStore) -> None:
    """With action='warn', utilization above the refuse fraction still
    proceeds — the configured softer posture."""
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8, action="warn")
    ledger = CostLedger(
        store=store, config=config, cap_probe=_fixed_probe(_windows(95.0))
    )
    reservation = ledger.reserve_or_refuse(make_spec(), scope_id="s4")
    assert reservation is not None
    assert ledger.last_cap_check.outcome == "warn"


# ---- AC.CAPC.2 — fail-open, no fabricated number --------------------


def test_AC_CAPC_2_unavailable_fails_open_with_no_number(store: CostStore) -> None:
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    unavailable = UsageUnavailable(reason=UnavailableReason.UNREACHABLE)
    ledger = CostLedger(
        store=store, config=config, cap_probe=_fixed_probe(unavailable)
    )
    # Fail OPEN: dispatch proceeds, reservation lands.
    reservation = ledger.reserve_or_refuse(make_spec(), scope_id="s5")
    assert reservation is not None
    assert store.get_reservation("s5") is not None
    # The record carries the categorical reason and NO utilization number.
    status = ledger.last_cap_check
    assert status.outcome == "unavailable"
    assert status.reason == "unreachable"
    assert status.utilization_fraction is None
    # No numeric utilization anywhere in the record's rendered form.
    assert not any(ch.isdigit() for ch in repr(status))


# ---- AC.CAPC.3 — default-OFF, no probe call, no regression ----------


def test_AC_CAPC_3_unconfigured_never_probes(store: CostStore) -> None:
    calls = {"n": 0}

    def counting_reader():
        calls["n"] += 1
        return _windows(99.0)

    # No cap_ceiling configured; inject a probe that MUST NOT be consulted.
    config = CostConfig(session=SessionCeiling(), rolling=[])
    ledger = CostLedger(
        store=store,
        config=config,
        cap_probe=CachedCapProbe(reader=counting_reader),
    )
    reservation = ledger.reserve_or_refuse(make_spec(), scope_id="s6")
    assert reservation is not None
    assert calls["n"] == 0
    assert ledger.last_cap_check.outcome == "off"


# ---- AC.CAPC.4 — production-stake floor on the cap warn fraction -----


def test_AC_CAPC_4_production_stake_clamps_cap_warn_fraction() -> None:
    config = _cap_config(warn_fraction=0.9, refuse_fraction=0.95)
    floored = apply_safety_profile_floor(config, safety_profile="production-stake")
    # Clamped at runtime to the 0.6 floor.
    assert floored.cap_ceiling.warn_fraction == 0.6
    # refuse_fraction + action untouched.
    assert floored.cap_ceiling.refuse_fraction == 0.95
    assert floored.cap_ceiling.action == "refuse"
    # Source config is NOT mutated.
    assert config.cap_ceiling.warn_fraction == 0.9


def test_AC_CAPC_4_dev_profile_is_noop() -> None:
    config = _cap_config(warn_fraction=0.9, refuse_fraction=0.95)
    out = apply_safety_profile_floor(config, safety_profile="dev")
    assert out.cap_ceiling.warn_fraction == 0.9


def test_AC_CAPC_4_below_floor_unchanged() -> None:
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    out = apply_safety_profile_floor(config, safety_profile="production-stake")
    assert out.cap_ceiling.warn_fraction == 0.5


# ---- AC.CAPC.5 — TTL cache: N reserves, one probe -------------------


def test_AC_CAPC_5_ttl_cache_coalesces_probes(store: CostStore) -> None:
    calls = {"n": 0}
    now = {"t": 1000.0}

    def counting_reader():
        calls["n"] += 1
        return _windows(30.0)

    probe = CachedCapProbe(
        reader=counting_reader, ttl_seconds=30.0, clock=lambda: now["t"]
    )
    config = _cap_config(warn_fraction=0.5, refuse_fraction=0.8)
    ledger = CostLedger(store=store, config=config, cap_probe=probe)

    for i in range(5):
        ledger.reserve_or_refuse(make_spec(), scope_id=f"cap-{i}")
    # Five gate checks within the TTL → exactly one probe invocation.
    assert calls["n"] == 1

    # Advance past the TTL → the next check re-probes.
    now["t"] += 31.0
    ledger.reserve_or_refuse(make_spec(), scope_id="cap-after-ttl")
    assert calls["n"] == 2

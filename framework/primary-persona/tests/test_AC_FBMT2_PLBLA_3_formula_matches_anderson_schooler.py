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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.FBMT2.PLBLA.3 — activation formula matches Anderson & Schooler 1991.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.PLBLA.3:

    For synthetic access patterns the computed activation equals the
    expected ``B_i = ln(Σ_j (now − t_j)^(−d))`` to within floating-
    point tolerance. Bands at least the single-access case, the
    two-access case (frequency-pattern observable), and the zero-
    access case (returns the floor / epsilon).

§14 D-T2.1.DECAY pins ``d = 0.5``; D-T2.1.FLOOR pins
``epsilon = 1.0 second``.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

from loam.primary_persona.access_log import (
    ACTIVATION_DECAY_D,
    ACTIVATION_FLOOR_EPSILON_SECONDS,
    compute_activation,
)


def test_AC_FBMT2_PLBLA_3_zero_access_returns_neg_inf() -> None:
    """Empty timestamp list returns ``-inf`` (the empty-sum case;
    ``ln(0)`` is the sentinel)."""
    now = datetime.now(timezone.utc)
    assert compute_activation([], now=now) == -math.inf


def test_AC_FBMT2_PLBLA_3_single_access_matches_formula() -> None:
    """One access ``Δ`` seconds ago → ``B = ln(Δ^(-d))``."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    delta_sec = 100.0
    t1 = now - timedelta(seconds=delta_sec)
    expected = math.log(delta_sec ** (-ACTIVATION_DECAY_D))
    actual = compute_activation([t1], now=now)
    assert abs(actual - expected) < 1e-9, (actual, expected)


def test_AC_FBMT2_PLBLA_3_two_access_matches_formula() -> None:
    """Two accesses at Δ_1 and Δ_2 → ``B = ln(Δ_1^(-d) + Δ_2^(-d))``.

    Demonstrates the frequency-pattern observable: a second access
    increases B above the single-access value."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    t1 = now - timedelta(seconds=100)
    t2 = now - timedelta(seconds=200)
    d = ACTIVATION_DECAY_D
    expected = math.log(100.0 ** (-d) + 200.0 ** (-d))
    actual = compute_activation([t1, t2], now=now)
    assert abs(actual - expected) < 1e-9
    # Frequency observable: two accesses > one access.
    single = compute_activation([t1], now=now)
    assert actual > single


def test_AC_FBMT2_PLBLA_3_floor_when_just_now() -> None:
    """A ``t_j == now`` touch (zero duration) floors at ``epsilon``
    per D-T2.1.FLOOR; the activation contribution for a single such
    touch is ``epsilon^(-d) = 1.0`` for the default values."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    actual = compute_activation([now], now=now)
    expected = math.log(
        ACTIVATION_FLOOR_EPSILON_SECONDS ** (-ACTIVATION_DECAY_D)
    )
    assert abs(actual - expected) < 1e-9
    # With default epsilon=1.0s and d=0.5, the activation is ln(1) = 0.
    assert abs(actual - 0.0) < 1e-9


def test_AC_FBMT2_PLBLA_3_future_dated_touch_floored() -> None:
    """A future-dated touch (clock skew / test setup) is floored at
    ``epsilon`` so the formula stays well-defined (D-T2.1.FLOOR)."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    future = now + timedelta(seconds=60)
    actual = compute_activation([future], now=now)
    expected = math.log(
        ACTIVATION_FLOOR_EPSILON_SECONDS ** (-ACTIVATION_DECAY_D)
    )
    assert abs(actual - expected) < 1e-9

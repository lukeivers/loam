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

"""★ AC.USG.S — outcome-altitude (real probe, NO pre-arranged state).

Invokes the PRODUCTION entry-point ``read()`` with NO injected transport, NO
fixture credential, NO monkeypatch — the call reads the real macOS keychain
and hits the real ``https://api.anthropic.com/api/oauth/usage``. The outcome
is one of exactly two REAL-code-path results:

  1. ``UsageWindows`` — real floats in [0, 100] with parsed reset timestamps
     (live endpoint reachable + token valid); OR
  2. ``UsageUnavailable`` — a categorical reason with NO number (the genuine
     fail-open path, through the SAME real code, never a stub).

Either PASSES. A fabricated number or an uncaught exception FAILS. A
STUB-class test (pre-seeded response) does NOT satisfy this AC
(feedback_test_outcome_altitude_required).
"""

from __future__ import annotations

from datetime import datetime

from loam.usage_window_guard import (
    UnavailableReason,
    UsageUnavailable,
    UsageWindows,
    read,
)


def test_real_probe_returns_real_windows_or_fails_open() -> None:
    # NO pre-arranged state: defaults => real keychain read + real HTTPS GET.
    result = read()

    if isinstance(result, UsageWindows):
        # Live success branch — assert the values are REAL, not fabricated.
        for window in (result.five_hour, result.seven_day):
            assert isinstance(window.utilization, float)
            assert 0.0 <= window.utilization <= 100.0
            assert isinstance(window.resets_at, datetime)
            # A real reset timestamp is in the future relative to the epoch
            # year of the windows (sanity — never the unix epoch / zero).
            assert window.resets_at.year >= 2026
    elif isinstance(result, UsageUnavailable):
        # Genuine fail-open branch — categorical reason, NO number.
        assert isinstance(result.reason, UnavailableReason)
        # The fail-open value carries no utilization attribute at all.
        assert not hasattr(result, "utilization")
        assert not hasattr(result, "five_hour")
        assert not hasattr(result, "seven_day")
    else:  # pragma: no cover - the sum type admits no third member.
        raise AssertionError(
            f"read() returned an unexpected type: {type(result)!r}"
        )

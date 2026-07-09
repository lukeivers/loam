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

"""AC.CAP.2 — UsageUnavailable FIRES the categorical reason, never a number.

D-A1-1: an unreadable cap is not silence. WS-A4's cap guard fails open on
UsageUnavailable *because this alert covers the blind window*, so the alert must
fire with the categorical reason — and, structurally, with NO fabricated
utilization percentage (the assertion is against a percentage shape, since a
correct message may legitimately carry non-percentage digits).
"""

from __future__ import annotations

import re

import pytest
from conftest import CapturingNotify, probe_returning, unavailable

from loam.usage_window_guard import UnavailableReason
from loam.weekly_cap_alert import run_alert
from loam.weekly_cap_alert.alert import KIND_UNAVAILABLE

_PERCENT = re.compile(r"\d+(?:\.\d+)?\s*%")


@pytest.mark.parametrize("reason", list(UnavailableReason))
def test_unavailable_fires_reason_and_never_a_percentage(reason):
    notify = CapturingNotify()
    # A detail that itself contains digits ("HTTP 401") — proving the alert does
    # NOT interpolate detail onto the message, so no digit-bearing HTTP status
    # can masquerade as a reading, and no percentage appears at all.
    decision = run_alert(
        probe=probe_returning(unavailable(reason, detail="token rejected (HTTP 401)")),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert decision.kind == KIND_UNAVAILABLE
    assert decision.notify is True
    # The alert fired (covers WS-A4's blind window).
    assert notify.called
    message = notify.messages[0]
    # The categorical reason is present...
    assert reason.value in message
    # ...and no utilization percentage was fabricated anywhere in the message.
    assert not _PERCENT.search(message)
    # The HTTP-status detail was not leaked onto the alert message.
    assert "401" not in message


def test_unavailable_message_names_no_threshold_percentage_either():
    # Even the threshold (a percentage) must not appear on the unavailable path:
    # there is no number to compare against, so surfacing "threshold 60.0%"
    # would imply a reading occurred. The unavailable message is number-free.
    notify = CapturingNotify()
    run_alert(
        probe=probe_returning(unavailable(UnavailableReason.UNREACHABLE)),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert not _PERCENT.search(notify.messages[0])

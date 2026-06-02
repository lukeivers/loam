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

"""AC.USG.1 — real-window read (source-identity).

``read()`` against a fixture HTTP 200 body (the live nested shape) returns a
``UsageWindows`` carrying BOTH windows' utilization (float %) AND resets_at,
each sourced from that window's ``utilization`` field — NOT a token count.
"""

from __future__ import annotations

import json
from datetime import datetime

from loam.usage_window_guard import UsageWindows, read
from loam.usage_window_guard.probe import _HttpResult

from .conftest import LIVE_200_BODY


def _ok_transport(body: str):
    def transport(token: str, endpoint: str) -> _HttpResult:
        return _HttpResult(200, body)

    return transport


def test_both_windows_parsed_from_live_shape() -> None:
    result = read(
        credential_reader=lambda: "fixture-token",
        transport=_ok_transport(LIVE_200_BODY),
    )
    assert isinstance(result, UsageWindows)

    # five_hour window parsed with the endpoint's exact utilization + reset.
    assert result.five_hour.utilization == 18.0
    assert isinstance(result.five_hour.resets_at, datetime)
    assert result.five_hour.resets_at.year == 2026
    assert result.five_hour.resets_at.month == 6
    assert result.five_hour.resets_at.day == 3

    # seven_day window parsed likewise.
    assert result.seven_day.utilization == 11.0
    assert isinstance(result.seven_day.resets_at, datetime)
    assert result.seven_day.resets_at.day == 5


def test_value_is_sourced_from_the_endpoint_utilization_field() -> None:
    """Source-identity: the number is the named window's ``utilization``
    field, not any derived/aggregated/token quantity. Changing only that
    field changes only that window's reading."""
    payload = json.loads(LIVE_200_BODY)
    payload["five_hour"]["utilization"] = 73.5
    body = json.dumps(payload)

    result = read(
        credential_reader=lambda: "fixture-token",
        transport=_ok_transport(body),
    )
    assert isinstance(result, UsageWindows)
    assert result.five_hour.utilization == 73.5
    # seven_day untouched — proves per-window field sourcing.
    assert result.seven_day.utilization == 11.0

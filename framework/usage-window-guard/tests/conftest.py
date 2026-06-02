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

"""Shared fixtures for the usage-window-guard tests.

``LIVE_200_BODY`` is the REAL nested shape captured from
``GET /api/oauth/usage`` at build time (HTTP 200) — the ground-truth shape
the probe parses (plan §3 SAL-1). It is recorded verbatim (minus any secret;
the response carries no secret) so AC.USG.1 verifies the parser against the
actual endpoint contract, not an invented one.
"""

from __future__ import annotations

import json

import pytest

# Verbatim live capture (build time, HTTP 200). Nested
# ``{window: {utilization, resets_at}}`` shape.
LIVE_200_BODY = json.dumps(
    {
        "five_hour": {
            "utilization": 18.0,
            "resets_at": "2026-06-03T00:40:00.958044+00:00",
        },
        "seven_day": {
            "utilization": 11.0,
            "resets_at": "2026-06-05T05:59:59.958068+00:00",
        },
        "seven_day_oauth_apps": None,
        "seven_day_opus": None,
        "seven_day_sonnet": {
            "utilization": 2.0,
            "resets_at": "2026-06-05T05:59:59.958078+00:00",
        },
        "extra_usage": {
            "is_enabled": False,
            "monthly_limit": None,
            "used_credits": None,
            "utilization": None,
            "currency": None,
            "disabled_reason": None,
        },
    }
)


@pytest.fixture
def live_200_body() -> str:
    return LIVE_200_BODY

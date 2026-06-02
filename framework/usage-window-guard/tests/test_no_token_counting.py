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

"""Source-identity guard: the reading is the endpoint's enforced cap
utilization, NOT token-counting / cost-estimation / a tool-call tally.

The owner constraint (Luke 13492): read the REAL Anthropic-side rolling
windows, never token-counting. These tests pin that the foundation reads the
OAuth usage endpoint and sources the value from the response field — there is
no token summing, no session-JSONL read, no cost arithmetic anywhere in the
component.
"""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "loam" / "usage_window_guard"


def test_probe_targets_the_oauth_usage_endpoint() -> None:
    from loam.usage_window_guard import USAGE_ENDPOINT

    assert USAGE_ENDPOINT == "https://api.anthropic.com/api/oauth/usage"


def test_no_token_counting_machinery_in_source() -> None:
    """The component never reads session JSONLs, never sums message.usage
    tokens, never estimates cost. Grep the source for the forbidden shapes."""
    forbidden = [
        "message.usage",
        "input_tokens",
        "output_tokens",
        "usage_tally",
        ".jsonl",
        "cost_usd",
        "session.jsonl",
    ]
    for py in SRC.glob("*.py"):
        text = py.read_text()
        for needle in forbidden:
            assert needle not in text, (
                f"{py.name} contains token-counting/cost shape {needle!r} — "
                f"the foundation must read the enforced cap utilization only."
            )


def test_utilization_is_read_not_computed() -> None:
    """The window utilization equals the endpoint field verbatim — the
    component does not derive/scale/aggregate it."""
    import json

    from loam.usage_window_guard import UsageWindows, read
    from loam.usage_window_guard.probe import _HttpResult

    body = json.dumps(
        {
            "five_hour": {"utilization": 42.0, "resets_at": "2026-06-03T00:40:00+00:00"},
            "seven_day": {"utilization": 7.0, "resets_at": "2026-06-05T05:59:59+00:00"},
        }
    )
    result = read(
        credential_reader=lambda: "tok",
        transport=lambda t, e: _HttpResult(200, body),
    )
    assert isinstance(result, UsageWindows)
    # Verbatim — no token math applied.
    assert result.five_hour.utilization == 42.0
    assert result.seven_day.utilization == 7.0

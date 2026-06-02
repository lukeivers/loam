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

"""loam usage-window guard (foundation slice).

Reads the user's REAL Anthropic-side rolling-window utilization — the rolling
5-hour window and the 7-day weekly window — directly from the OAuth usage
endpoint, and fails open (never fabricates a percentage) when it cannot.

Public surface:

    from loam.usage_window_guard import read, UsageWindows, UsageUnavailable

    result = read()
    if isinstance(result, UsageWindows):
        print(result.five_hour.utilization, result.seven_day.utilization)
    else:
        # result is UsageUnavailable — usage is unknown right now; do NOT
        # guess a number, do NOT block work.
        print("usage unavailable:", result.reason.value)

This is the foundation slice: probe + parse + fail-open. Thresholds, the
plain-language surfacing contract, and hook wiring are a follow-on slice.
"""

from __future__ import annotations

from .model import (
    UnavailableReason,
    UsageUnavailable,
    UsageWindows,
    Window,
)
from .probe import USAGE_ENDPOINT, read

__all__ = [
    "read",
    "UsageWindows",
    "UsageUnavailable",
    "UnavailableReason",
    "Window",
    "USAGE_ENDPOINT",
]

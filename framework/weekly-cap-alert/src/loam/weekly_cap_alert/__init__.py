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

"""loam weekly-cap alert (WS-A1).

Reads the SEALED usage-window-guard's REAL ``seven_day`` (weekly) Anthropic cap
utilization and fires a channel notification when it crosses the owner-ratified
threshold (60%, backplane D5); stays silent below it; and, on ``UsageUnavailable``,
fires the categorical failure reason and NEVER a fabricated number.

    from loam.weekly_cap_alert import run_alert
    run_alert()  # real sealed probe + stdout delivery

Channel-agnostic (H-3): the delivery surface is an injected ``notify_fn``. The
launchd job bridges to a workspace poster via ``--notify-cmd``. Threshold lives
in config, not code.
"""

from __future__ import annotations

from .alert import (
    AlertDecision,
    evaluate,
    run_alert,
)
from .config import DEFAULT_THRESHOLD_PCT, load_threshold
from .notify import NotifyFn, command_notify, stdout_notify

__all__ = [
    "AlertDecision",
    "evaluate",
    "run_alert",
    "DEFAULT_THRESHOLD_PCT",
    "load_threshold",
    "NotifyFn",
    "command_notify",
    "stdout_notify",
]

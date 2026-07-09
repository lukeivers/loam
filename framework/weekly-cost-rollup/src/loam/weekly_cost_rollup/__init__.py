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

"""loam weekly cost roll-up (WS-A5).

Once a week, one channel message in three sections: this machine's weekly Claude
cap % (from the SEALED usage-window-guard), the top-3 projects by Claude tokens
(a PROXY ranked from the local ``~/.claude/projects`` transcripts, never dollars),
and metered-model spend month-to-date (Vercel AI Gateway, a named absence until
D1). Missing sources are NAMED, never silently omitted.

    from loam.weekly_cost_rollup import run_rollup
    run_rollup()  # real sealed probe + real transcript parser + stdout delivery

Channel-agnostic (H-3): the delivery surface is an injected ``notify_fn`` (reused
from WS-A1). Runs as a weekly launchd job that survives a session ending.
"""

from __future__ import annotations

from .gateway import GatewaySpend, GatewayUnavailable, read_gateway_spend
from .rollup import build_message, run_rollup
from .tokens import (
    ProjectTokens,
    TokenUsageUnavailable,
    read_project_tokens,
)

__all__ = [
    "run_rollup",
    "build_message",
    "ProjectTokens",
    "TokenUsageUnavailable",
    "read_project_tokens",
    "GatewaySpend",
    "GatewayUnavailable",
    "read_gateway_spend",
]

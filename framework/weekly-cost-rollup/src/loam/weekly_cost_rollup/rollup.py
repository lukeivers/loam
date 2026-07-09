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

"""The weekly cost roll-up: assemble the three-section message + deliver it.

One weekly channel message in three sections (BACKPLANE §5 WS-A5):

1. **This machine's weekly Claude cap %** — from the SEALED usage-window-guard
   ``seven_day`` window. On ``UsageUnavailable`` the section names the categorical
   reason and carries **no** number (a fabricated % is impossible off the probe's
   sum type; D-A5-5).
2. **Top-3 projects by Claude tokens** — a PROXY (ranks consumption, never
   dollars; stream 04 §1c). The proxy label is mandatory (D-A5-4).
3. **Metered-model spend month-to-date** — Vercel AI Gateway; a named absence
   until D1 is signed up (D-A5-2).

A missing source is a NAMED section, never a dropped one (D-A5-5). Unlike the
WS-A1 alert (conditional), the roll-up **always** delivers (D-A5-3).
"""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional

from loam.usage_window_guard import UsageUnavailable, UsageWindows, read
from loam.weekly_cap_alert.notify import NotifyFn, stdout_notify

from .gateway import GatewaySpend, GatewayUnavailable, read_gateway_spend
from .tokens import ProjectTokens, TokenUsageUnavailable, read_project_tokens

# Injectable seams so the AC tests drive deterministic inputs while the default
# arguments exercise the full production path.
ProbeFn = Callable[[], "UsageWindows | UsageUnavailable"]
TokenSourceFn = Callable[[], "list[ProjectTokens] | TokenUsageUnavailable"]
GatewaySourceFn = Callable[[], "GatewaySpend | GatewayUnavailable"]

# The mandatory proxy disclaimer (D-A5-4 / stream 04 §1c) — asserted by AC.RUP.1.
_PROXY_LABEL = "proxy — ranks consumption, not billing-grade"


def _cap_section(result: "UsageWindows | UsageUnavailable") -> str:
    if isinstance(result, UsageUnavailable):
        # Named absence, categorical reason, NO number (D-A5-5).
        return (
            "Claude weekly cap (this machine): unavailable "
            f"(reason: {result.reason.value}); no number this run."
        )
    utilization = result.seven_day.utilization
    return (
        f"Claude weekly cap (this machine): {utilization:.1f}% of the "
        "enforced limit."
    )


def _tokens_section(
    result: "list[ProjectTokens] | TokenUsageUnavailable",
    top_n: int,
) -> str:
    if isinstance(result, TokenUsageUnavailable):
        # Named absence — the section is present, never silently dropped.
        return (
            f"Top Claude-token projects ({_PROXY_LABEL}): unavailable "
            f"(reason: {result.reason})."
        )
    lines = [f"Top Claude-token projects ({_PROXY_LABEL}):"]
    for rank, entry in enumerate(result[:top_n], start=1):
        lines.append(f"  {rank}. {entry.project} — {entry.tokens:,} tokens")
    return "\n".join(lines)


def _gateway_section(result: "GatewaySpend | GatewayUnavailable") -> str:
    if isinstance(result, GatewayUnavailable):
        phrase = result.detail or f"source unavailable (reason: {result.reason})"
        return f"Metered-model spend (month-to-date): {phrase}."
    return (
        f"Metered-model spend (month-to-date, {result.period}): "
        f"${result.amount_usd:.2f}."
    )


def build_message(
    *,
    cap_result: "UsageWindows | UsageUnavailable",
    token_result: "list[ProjectTokens] | TokenUsageUnavailable",
    gateway_result: "GatewaySpend | GatewayUnavailable",
    top_n: int = 3,
    today: Optional[date] = None,
) -> str:
    """Assemble the three-section roll-up message (≤ ~15 lines; D-A5-7)."""
    header_date = (today or date.today()).isoformat()
    sections = [
        f"Weekly cost roll-up ({header_date})",
        _cap_section(cap_result),
        _tokens_section(token_result, top_n),
        _gateway_section(gateway_result),
    ]
    return "\n\n".join(sections)


def run_rollup(
    *,
    probe: ProbeFn = read,
    token_source: TokenSourceFn = read_project_tokens,
    gateway_source: GatewaySourceFn = read_gateway_spend,
    notify_fn: NotifyFn = stdout_notify,
    top_n: int = 3,
) -> str:
    """Production entry point: read all three sources → assemble → deliver.

    Called with no arguments this exercises the full production path: the real
    sealed usage probe, the real transcript token parser, the (not-yet-configured)
    gateway source, and the stdout delivery default. Always delivers (D-A5-3) and
    returns the message so the launchd job log can capture it.
    """
    message = build_message(
        cap_result=probe(),
        token_result=token_source(),
        gateway_result=gateway_source(),
        top_n=top_n,
    )
    notify_fn(message)
    return message

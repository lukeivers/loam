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

"""The metered-model spend section: Vercel AI Gateway month-to-date (D-A5-2).

The gateway is owner decision **D1**, not yet signed up. Rather than silently
drop the section, the default source returns a NAMED absence
(:class:`GatewayUnavailable` with ``reason="not_configured"``), so the roll-up
renders "source unavailable — Vercel AI Gateway not configured yet (D1 pending)"
— the plan's "degrades … plus a named absence", not a silent two-section message.

The source is a seam: when D1 lands, a real provider (querying the gateway's
per-tag spend report) is configured here and returns a :class:`GatewaySpend`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewaySpend:
    """Real metered-model spend (exact dollars — the one honest $ in the shop)."""

    amount_usd: float
    period: str


@dataclass(frozen=True)
class GatewayUnavailable:
    """The gateway spend could not be read — a NAMED absence.

    ``reason`` is a categorical token (``not_configured`` before D1,
    ``unreachable`` when the gateway is signed up but the request fails);
    ``detail`` is an optional human phrase the message renders verbatim.
    """

    reason: str
    detail: str = ""


def read_gateway_spend() -> "GatewaySpend | GatewayUnavailable":
    """Default source: the gateway is not configured yet (D1 pending)."""
    return GatewayUnavailable(
        reason="not_configured",
        detail="Vercel AI Gateway not configured yet (D1 pending)",
    )

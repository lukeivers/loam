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

"""Result types for the usage-window probe.

The probe returns a **sum type** — :class:`UsageWindows` on success,
:class:`UsageUnavailable` on any failure. This is deliberate
(plan §5 D-build.3): a fabricated number is structurally impossible to
read off the failure value because :class:`UsageUnavailable` carries NO
numeric utilization field at all. The caller can never mistake a fail-open
for a real reading (AC.USG.5 — never confabulate a usage number).

These types are **parse-only**. They carry no thresholds, no warning copy,
no de-duplication state — that is the follow-on slice (design
AC.USG.{2,3,4}).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UnavailableReason(str, Enum):
    """Categorical fail-open reasons (plan §5 D-build.4).

    None of these implies a utilization value; each names *why* the real
    windows could not be read so a later surfacing slice can say "usage
    unavailable" honestly. The string values are stable diagnostic tokens.
    """

    MISSING_CREDENTIAL = "missing_credential"
    """No OAuth credential could be read from the keychain (absent/empty)."""

    AUTH_REJECTED = "auth_rejected"
    """The endpoint rejected the token (HTTP 401/403) — typically a rotated
    token Claude Code has not yet refreshed. Transient; the next probe after
    any Claude activity should succeed."""

    ENDPOINT_ERROR = "endpoint_error"
    """The endpoint returned a non-200 that is not an auth rejection
    (e.g. 5xx)."""

    UNREACHABLE = "unreachable"
    """The endpoint could not be reached (network error / timeout)."""

    MALFORMED_RESPONSE = "malformed_response"
    """A 200 was returned but the body was not parseable into both
    windows (non-JSON, or missing the expected window fields)."""


@dataclass(frozen=True)
class Window:
    """One rolling window's REAL Anthropic-side cap utilization.

    ``utilization`` is the server-side percentage of the enforced cap (a
    float in ``[0, 100]``) — Anthropic's own accounting, read straight from
    the ``utilization`` field of the named window object in
    ``/api/oauth/usage``. It is **not** a token count, a cost estimate, or a
    tool-call tally.
    """

    utilization: float
    resets_at: datetime


@dataclass(frozen=True)
class UsageWindows:
    """A successful read of both REAL rolling windows.

    ``five_hour`` — the rolling 5-hour window (the one that bites mid-work).
    ``seven_day`` — the 7-day weekly window.
    """

    five_hour: Window
    seven_day: Window


@dataclass(frozen=True)
class UsageUnavailable:
    """The fail-open value (AC.USG.5).

    Carries a categorical ``reason`` and an optional human-readable
    ``detail`` for diagnostics — and, by construction, **NO** utilization
    number. A fail-open can never be misread as a real percentage.
    """

    reason: UnavailableReason
    detail: str = ""


# The probe's return type is one of the two above.
UsageResult = "UsageWindows | UsageUnavailable"

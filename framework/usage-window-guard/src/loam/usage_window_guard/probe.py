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

"""The production entry-point: :func:`read`.

Reads the user's REAL Anthropic-side rolling-window utilization from
``GET https://api.anthropic.com/api/oauth/usage`` and returns a
:class:`~loam.usage_window_guard.model.UsageWindows` on success or a
:class:`~loam.usage_window_guard.model.UsageUnavailable` on ANY failure
(fail-open — AC.USG.5). It never raises for an expected failure mode and
never fabricates a utilization number.

This is Anthropic's enforced cap utilization — the same numbers ``/usage``
renders. It is NOT token-counting, NOT cost-estimation, NOT a tool-call
tally; the value for each window is read straight from that window's
``utilization`` field in the endpoint response (AC.USG.1 source-identity).

The credential read and the HTTP transport are injectable so the AC.USG.1 /
AC.USG.5 fixture tests can drive deterministic responses, but the DEFAULTS
are the real keychain read and a real HTTPS GET — so the outcome-altitude
test (AC.USG.S) exercises the production path with NO pre-arranged state.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Callable, Optional

from .credential import read_access_token
from .model import (
    UnavailableReason,
    UsageUnavailable,
    UsageWindows,
    Window,
)

USAGE_ENDPOINT = "https://api.anthropic.com/api/oauth/usage"

# Headers replicated verbatim from the verified-working recipe
# (``usage_cap.sh`` / feedback_real_claude_usage_oauth_endpoint.md). The
# ``anthropic-beta`` header is optional per the design's Tier-0 check, but we
# send it to match the proven recipe exactly (plan §3 SAL-2) and avoid
# inventing a deviation.
_BASE_HEADERS = {
    "anthropic-beta": "oauth-2025-04-20",
    "User-Agent": "claude-cli",
}

_DEFAULT_TIMEOUT_S = 10.0


class _HttpResult:
    """A minimal transport result the parser consumes.

    A transport returns one of these (status + body text) or raises a
    transport error the probe maps to ``UNREACHABLE``.
    """

    __slots__ = ("status", "body")

    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body


# A transport takes the bearer token + endpoint and returns an _HttpResult.
# Injectable for tests; the default is the real urllib GET.
Transport = Callable[[str, str], _HttpResult]

# A credential reader returns the token string or None (missing).
CredentialReader = Callable[[], Optional[str]]


def _real_transport(token: str, endpoint: str) -> _HttpResult:
    """Perform the real HTTPS GET. Raises on a network/timeout error."""
    request = urllib.request.Request(endpoint, method="GET")
    request.add_header("Authorization", f"Bearer {token}")
    for key, value in _BASE_HEADERS.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=_DEFAULT_TIMEOUT_S) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
            return _HttpResult(status, body)
    except urllib.error.HTTPError as exc:
        # A non-2xx status is delivered as HTTPError; capture status + body so
        # the probe can distinguish 401/403 (auth) from other non-200s.
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # pragma: no cover - body read best-effort
            body = ""
        return _HttpResult(exc.code, body)


def _parse_window(obj: object) -> Optional[Window]:
    """Parse one window object ``{"utilization": float, "resets_at": iso}``.

    Returns ``None`` if the shape is not the expected nested struct — the
    caller maps that to ``MALFORMED_RESPONSE``. The utilization is read from
    the ``utilization`` field (source-identity: the value is the endpoint's,
    never a token count).
    """
    if not isinstance(obj, dict):
        return None
    util = obj.get("utilization")
    resets_raw = obj.get("resets_at")
    if not isinstance(util, (int, float)) or not isinstance(resets_raw, str):
        return None
    try:
        resets_at = datetime.fromisoformat(resets_raw)
    except (ValueError, TypeError):
        return None
    return Window(utilization=float(util), resets_at=resets_at)


def read(
    *,
    credential_reader: CredentialReader = read_access_token,
    transport: Transport = _real_transport,
) -> "UsageWindows | UsageUnavailable":
    """Read the REAL rolling-window utilization, or fail open.

    Returns :class:`UsageWindows` (both windows parsed) on a clean HTTP 200,
    or :class:`UsageUnavailable` (with a categorical reason and NO number) on
    a missing credential, a 401/403, any other non-200, an unreachable
    endpoint/timeout, or a malformed body. Never raises for these modes;
    never fabricates a utilization (AC.USG.5).

    The defaults read the real macOS keychain and perform a real HTTPS GET —
    so calling ``read()`` with no arguments exercises the full production path
    (AC.USG.S outcome-altitude).
    """
    # 1. Transient credential read (fresh every call — never cached).
    token = credential_reader()
    if not token:
        return UsageUnavailable(
            reason=UnavailableReason.MISSING_CREDENTIAL,
            detail="no OAuth credential available from the keychain",
        )

    # 2. The HTTP GET — transport errors are unreachable (fail-open).
    try:
        result = transport(token, USAGE_ENDPOINT)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return UsageUnavailable(
            reason=UnavailableReason.UNREACHABLE,
            detail=f"endpoint unreachable: {type(exc).__name__}",
        )

    # 3. Status discrimination.
    if result.status in (401, 403):
        return UsageUnavailable(
            reason=UnavailableReason.AUTH_REJECTED,
            detail=f"token rejected (HTTP {result.status}) — likely rotated",
        )
    if result.status != 200:
        return UsageUnavailable(
            reason=UnavailableReason.ENDPOINT_ERROR,
            detail=f"unexpected HTTP {result.status}",
        )

    # 4. Parse the nested body (live ground-truth shape; plan §3 SAL-1).
    try:
        payload = json.loads(result.body)
    except (json.JSONDecodeError, ValueError):
        return UsageUnavailable(
            reason=UnavailableReason.MALFORMED_RESPONSE,
            detail="200 body was not valid JSON",
        )

    if not isinstance(payload, dict):
        return UsageUnavailable(
            reason=UnavailableReason.MALFORMED_RESPONSE,
            detail="200 body was not a JSON object",
        )

    five_hour = _parse_window(payload.get("five_hour"))
    seven_day = _parse_window(payload.get("seven_day"))
    if five_hour is None or seven_day is None:
        return UsageUnavailable(
            reason=UnavailableReason.MALFORMED_RESPONSE,
            detail="five_hour/seven_day window missing or malformed",
        )

    return UsageWindows(five_hour=five_hour, seven_day=seven_day)

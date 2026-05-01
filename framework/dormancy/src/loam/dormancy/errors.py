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

"""Claude-API error taxonomy and classification.

pOS cannot assume the Anthropic SDK is installed (memory-system uses it
through Graphiti; scope-of-work and friends do not call Claude at all).
Rather than make a hard dependency, the adapter defines its own typed
exception hierarchy that mirrors the Anthropic SDK's public names:

    anthropic.APIConnectionError    → APIConnectionError
    anthropic.APITimeoutError       → APITimeoutError
    anthropic.RateLimitError        → RateLimitError        (429)
    anthropic.APIStatusError (5xx)  → InternalServerError
    anthropic.APIStatusError (529)  → OverloadedError
    anthropic.AuthenticationError   → AuthenticationError   (401)
    anthropic.BadRequestError       → BadRequestError       (400)

`classify_exception()` maps any exception to the pOS-side class. It first
checks `isinstance` against the pOS hierarchy (for callers that raise the
pOS types directly), then matches against the Anthropic SDK types by
attribute shape (type name + `status_code` attribute) so we don't need to
import the SDK. This keeps the adapter SDK-optional while still detecting
real SDK exceptions cleanly when the SDK is installed.

`GarbageResponseError` is a pOS-only shape — the Anthropic SDK does not
raise this; the garbage detector raises it when a response fails the
pydantic → regex → LLM-judge chain.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


# ---- signal enum (used for event logging + metric tags) ----------------


class DegradationSignal(str, Enum):
    """Observed-failure class, one per Claude-side failure mode.

    ``memory_sidecar_down`` / ``memory_sidecar_recovered`` are consumed
    by the hands-off-lifecycle supervisor integration (Amendment 3 of
    hands-off-lifecycle). They enter the detection pipeline via
    :meth:`DegradationDetector.record_supervisor_signal`, not via the
    Claude-adapter path.
    """

    connection_error = "connection_error"
    timeout = "timeout"
    server_error = "server_error"  # 5xx other than 529
    overloaded = "overloaded"  # 529
    rate_limited = "rate_limited"  # 429
    auth_broken = "auth_broken"  # 401
    bad_request = "bad_request"  # 400 — NOT a degradation signal
    garbage = "garbage"  # pOS detector
    latency_high = "latency_high"  # advisory
    memory_sidecar_down = "memory_sidecar_down"  # supervisor signal
    memory_sidecar_recovered = "memory_sidecar_recovered"  # supervisor signal


# ---- pOS-side exception hierarchy --------------------------------------


class ClaudeAPIError(Exception):
    """Base for all Claude-upstream errors surfaced from the adapter.

    Carries the raw exception the Anthropic SDK raised (if any) so
    callers can still inspect SDK-specific metadata. `retry_after` is
    populated from the `retry-after` header when the adapter can read
    it from the SDK exception's response headers.
    """

    signal: DegradationSignal = DegradationSignal.server_error

    def __init__(
        self,
        message: str = "",
        *,
        cause: BaseException | None = None,
        retry_after: float | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message or self.__class__.__name__)
        self.cause = cause
        self.retry_after = retry_after
        self.status_code = status_code


class APIConnectionError(ClaudeAPIError):
    signal = DegradationSignal.connection_error


class APITimeoutError(ClaudeAPIError):
    signal = DegradationSignal.timeout


class InternalServerError(ClaudeAPIError):
    signal = DegradationSignal.server_error


class OverloadedError(ClaudeAPIError):
    """Anthropic's 529 — shed-load signal. Distinct from generic 5xx."""

    signal = DegradationSignal.overloaded


class RateLimitError(ClaudeAPIError):
    """429 rate-limit. `retry_after` populated from SDK header."""

    signal = DegradationSignal.rate_limited


class AuthenticationError(ClaudeAPIError):
    """401 — terminal until user fixes credentials."""

    signal = DegradationSignal.auth_broken


class BadRequestError(ClaudeAPIError):
    """400 — client-side. Not a degradation signal; re-raised to caller."""

    signal = DegradationSignal.bad_request


class GarbageResponseError(ClaudeAPIError):
    """pOS-only — response failed the pydantic → regex → judge chain."""

    signal = DegradationSignal.garbage


# ---- classification ----------------------------------------------------


_ANTHROPIC_TYPE_MAP: dict[str, type[ClaudeAPIError]] = {
    "APIConnectionError": APIConnectionError,
    "APITimeoutError": APITimeoutError,
    "RateLimitError": RateLimitError,
    "AuthenticationError": AuthenticationError,
    "BadRequestError": BadRequestError,
}


def _retry_after_from(exc: BaseException) -> float | None:
    """Pull `retry-after` header out of an Anthropic SDK exception.

    Accepts either integer seconds or HTTP-date in the header; falls
    back to None if neither shape matches.
    """
    response = getattr(exc, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    raw = None
    try:
        raw = headers.get("retry-after")
    except Exception:
        # Some response types only expose headers via dict-key access.
        try:
            raw = headers["retry-after"]
        except Exception:
            return None
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        # Could be an HTTP-date; we don't parse that here.
        return None


def _status_code_from(exc: BaseException) -> int | None:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    # Newer SDK shapes nest under .status / .response.status_code.
    for attr in ("status", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    response = getattr(exc, "response", None)
    if response is not None:
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return code
    return None


def classify_exception(exc: BaseException) -> ClaudeAPIError:
    """Map any exception to a pOS-side `ClaudeAPIError` subclass.

    - pOS-side types pass through unchanged.
    - Anthropic SDK types are detected by class-name (avoids importing
      the SDK when it is absent); `retry-after` header and status code
      are pulled into the pOS-side exception.
    - Generic OSError / TimeoutError map to APIConnectionError /
      APITimeoutError.
    - Anything else becomes an InternalServerError with the cause set.
    """
    if isinstance(exc, ClaudeAPIError):
        return exc

    type_name = type(exc).__name__

    # Anthropic SDK detection by class name.
    cls = _ANTHROPIC_TYPE_MAP.get(type_name)
    if cls is not None:
        status = _status_code_from(exc)
        return cls(
            str(exc),
            cause=exc,
            retry_after=_retry_after_from(exc),
            status_code=status,
        )

    # APIStatusError differentiates 529 (overloaded) from other 5xx.
    if type_name == "APIStatusError":
        status = _status_code_from(exc)
        if status == 529:
            return OverloadedError(
                str(exc),
                cause=exc,
                retry_after=_retry_after_from(exc),
                status_code=status,
            )
        return InternalServerError(str(exc), cause=exc, status_code=status)

    # Generic Python exceptions that map to connection / timeout.
    if isinstance(exc, TimeoutError):
        return APITimeoutError(str(exc), cause=exc)
    if isinstance(exc, (ConnectionError, OSError)):
        return APIConnectionError(str(exc), cause=exc)

    # Unknown — classify as internal error so degradation treats it as a
    # "Down" signal rather than silently swallowing it.
    return InternalServerError(str(exc), cause=exc)


# ---- handy utilities ---------------------------------------------------


def is_non_degradation_signal(err: ClaudeAPIError) -> bool:
    """True if this error should NOT trigger degradation.

    Only 400 (bad_request) is excluded; every other class counts.
    """
    return err.signal == DegradationSignal.bad_request


def signal_to_mode(signal: DegradationSignal) -> "str | None":
    """Map a signal to the ModeFSM name that consumes it.

    Returns None for signals that don't feed any mode (bad_request).
    """
    mapping = {
        DegradationSignal.connection_error: "down",
        DegradationSignal.timeout: "down",
        DegradationSignal.server_error: "down",
        DegradationSignal.overloaded: "overloaded",
        DegradationSignal.rate_limited: "rate_limited",
        DegradationSignal.auth_broken: "auth_broken",
        DegradationSignal.garbage: "garbage",
        DegradationSignal.latency_high: "latency_sustained",
        DegradationSignal.bad_request: None,
        DegradationSignal.memory_sidecar_down: "memory_sidecar",
        DegradationSignal.memory_sidecar_recovered: "memory_sidecar",
    }
    return mapping.get(signal)

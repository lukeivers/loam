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

"""AC.USG.5 — fail-open on unreadable usage.

For every failure mode — missing credential, 401/403, other non-200,
unreachable/timeout, malformed-200 — ``read()`` returns a ``UsageUnavailable``
that carries NO utilization number, does not raise, and names a categorical
reason. Never confabulate a usage number (information-trust-ordering).
"""

from __future__ import annotations

import urllib.error
from dataclasses import fields

import pytest

from loam.usage_window_guard import (
    UnavailableReason,
    UsageUnavailable,
    read,
)
from loam.usage_window_guard.probe import _HttpResult

from .conftest import LIVE_200_BODY


def _transport_returning(status: int, body: str = ""):
    def transport(token: str, endpoint: str) -> _HttpResult:
        return _HttpResult(status, body)

    return transport


def _assert_no_number(result: UsageUnavailable) -> None:
    """UsageUnavailable must carry no numeric utilization field by
    construction — verified structurally, not just by value."""
    assert isinstance(result, UsageUnavailable)
    field_names = {f.name for f in fields(result)}
    assert "utilization" not in field_names
    assert "five_hour" not in field_names
    assert "seven_day" not in field_names
    # And no numeric attribute leaked in.
    for f in fields(result):
        assert not isinstance(getattr(result, f.name), (int, float))


def test_missing_credential_fails_open() -> None:
    result = read(
        credential_reader=lambda: None,
        transport=_transport_returning(200, LIVE_200_BODY),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.MISSING_CREDENTIAL
    _assert_no_number(result)


def test_empty_credential_fails_open() -> None:
    result = read(
        credential_reader=lambda: "",
        transport=_transport_returning(200, LIVE_200_BODY),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.MISSING_CREDENTIAL
    _assert_no_number(result)


@pytest.mark.parametrize("status", [401, 403])
def test_auth_rejected_fails_open(status: int) -> None:
    result = read(
        credential_reader=lambda: "rotated-token",
        transport=_transport_returning(status),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.AUTH_REJECTED
    _assert_no_number(result)


@pytest.mark.parametrize("status", [400, 429, 500, 503])
def test_other_non_200_fails_open(status: int) -> None:
    result = read(
        credential_reader=lambda: "tok",
        transport=_transport_returning(status),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.ENDPOINT_ERROR
    _assert_no_number(result)


def test_unreachable_endpoint_fails_open() -> None:
    def raising_transport(token: str, endpoint: str) -> _HttpResult:
        raise urllib.error.URLError("connection refused")

    result = read(
        credential_reader=lambda: "tok",
        transport=raising_transport,
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.UNREACHABLE
    _assert_no_number(result)


def test_timeout_fails_open() -> None:
    def timing_out(token: str, endpoint: str) -> _HttpResult:
        raise TimeoutError("read timed out")

    result = read(credential_reader=lambda: "tok", transport=timing_out)
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.UNREACHABLE
    _assert_no_number(result)


def test_malformed_non_json_200_fails_open() -> None:
    result = read(
        credential_reader=lambda: "tok",
        transport=_transport_returning(200, "not json at all <<<"),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.MALFORMED_RESPONSE
    _assert_no_number(result)


def test_200_missing_window_fields_fails_open() -> None:
    result = read(
        credential_reader=lambda: "tok",
        transport=_transport_returning(200, '{"five_hour": {"utilization": 5.0}}'),
    )
    assert isinstance(result, UsageUnavailable)
    assert result.reason is UnavailableReason.MALFORMED_RESPONSE
    _assert_no_number(result)


def test_no_failure_mode_raises() -> None:
    """No expected failure mode escapes as an exception (never crash work)."""
    for reader, transport in [
        (lambda: None, _transport_returning(200, LIVE_200_BODY)),
        (lambda: "tok", _transport_returning(401)),
        (lambda: "tok", _transport_returning(500)),
        (lambda: "tok", _transport_returning(200, "garbage")),
    ]:
        # Must not raise.
        result = read(credential_reader=reader, transport=transport)
        assert isinstance(result, UsageUnavailable)

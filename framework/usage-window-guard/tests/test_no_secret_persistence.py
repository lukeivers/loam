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

"""No-secrets discipline (the env-scrub fence).

The OAuth token is read transiently per probe and must NEVER be returned to a
caller, stored on the result, or written into a log. These tests prove the
token does not leak out of the probe via its return value or via the source's
shape.
"""

from __future__ import annotations

from dataclasses import fields

from loam.usage_window_guard import UsageUnavailable, UsageWindows, read
from loam.usage_window_guard.probe import _HttpResult

from .conftest import LIVE_200_BODY

SENTINEL_TOKEN = "sk-ant-oat01-SECRET-SENTINEL-DO-NOT-LEAK"


def _capturing_transport(seen: dict):
    def transport(token: str, endpoint: str) -> _HttpResult:
        seen["token"] = token
        return _HttpResult(200, LIVE_200_BODY)

    return transport


def test_token_reaches_transport_but_not_the_result() -> None:
    seen: dict = {}
    result = read(
        credential_reader=lambda: SENTINEL_TOKEN,
        transport=_capturing_transport(seen),
    )
    # The token DID reach the request layer (it must, to authenticate)...
    assert seen["token"] == SENTINEL_TOKEN
    # ...but it must NOT appear anywhere on the returned value.
    assert isinstance(result, UsageWindows)
    for f in fields(result):
        assert SENTINEL_TOKEN not in repr(getattr(result, f.name))
    assert SENTINEL_TOKEN not in repr(result)


def test_fail_open_value_carries_no_token() -> None:
    result = read(
        credential_reader=lambda: SENTINEL_TOKEN,
        transport=lambda t, e: _HttpResult(401, ""),
    )
    assert isinstance(result, UsageUnavailable)
    assert SENTINEL_TOKEN not in repr(result)
    assert SENTINEL_TOKEN not in result.detail


def test_source_does_not_persist_the_token_at_module_scope() -> None:
    """No module-level cache holds the token across calls (it rotates ~hourly;
    a cached token would 401 and is a no-secrets violation)."""
    import loam.usage_window_guard.credential as cred
    import loam.usage_window_guard.probe as probe

    for module in (cred, probe):
        for name in dir(module):
            val = getattr(module, name)
            assert SENTINEL_TOKEN != val
            if isinstance(val, str):
                assert "sk-ant-oat01" not in val

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

"""TTL-cached wrapper around the sealed usage-window-guard probe (WS-A4).

`reserve_or_refuse` is a synchronous, deterministic gate on a hot path;
`usage_window_guard.read()` hits the OAuth usage endpoint. Calling the
live endpoint per reservation would (a) make the gate non-deterministic
and slow, and (b) hammer the endpoint when N parallel dispatches gate at
once. This cache is the layer the gate consults: within `ttl_seconds`,
the first `read()` invokes the underlying probe and every subsequent
call returns the cached sum-type value (AC.CAPC.5 — one probe per TTL).

Both arms of the probe's sum type are cached — a `UsageUnavailable`
fail-open is cached exactly like a `UsageWindows` success, so a transient
outage does not trigger a probe storm either. The WS-A1 weekly-cap alert
covers the blind window while the cap guard fails open (AC.CAPC.2).
"""

from __future__ import annotations

import time
from typing import Callable

from loam.usage_window_guard import UsageUnavailable, UsageWindows, read as _default_read


# A zero-arg reader returning the probe's sum type. The default binds the
# sealed probe with its own default credential/transport; tests inject a
# stub to drive utilization deterministically with no network.
CapReader = Callable[[], "UsageWindows | UsageUnavailable"]


def _default_reader() -> "UsageWindows | UsageUnavailable":
    return _default_read()


class CachedCapProbe:
    """Short-TTL cache over a `CapReader`.

    `ttl_seconds` defaults to 30s — long enough that a burst of parallel
    dispatches shares one reading, short enough that the ledger reacts to
    a rising weekly cap within a window that matters for cost. `clock`
    is injectable so tests advance time without sleeping.
    """

    def __init__(
        self,
        *,
        reader: CapReader = _default_reader,
        ttl_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._reader = reader
        self._ttl = ttl_seconds
        self._clock = clock
        self._cached: "UsageWindows | UsageUnavailable | None" = None
        self._cached_at: float = 0.0

    def read(self) -> "UsageWindows | UsageUnavailable":
        now = self._clock()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            return self._cached
        result = self._reader()
        self._cached = result
        self._cached_at = now
        return result

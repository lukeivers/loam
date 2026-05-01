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

"""Trigger dedup — hash + TTL logic (CR6).

The dedup key is SHA-256 of `(scope_id, source, normalised_reason)`.
Two identical triggers within the TTL produce exactly one episode; the
second emits `loam.correction.trigger_deduplicated` and persists to the
dedup table.

`normalised_reason` is a lowercased, trimmed, whitespace-collapsed
version of the reason-bearing field on the raw payload. This handles
the common case where two emitters describe the same failure with
minor whitespace differences.
"""

from __future__ import annotations

import hashlib
import re


def normalise_reason(raw: str | None) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().lower()
    return re.sub(r"\s+", " ", s)


def make_dedup_key(
    *, scope_id: str | None, source: str, normalised_reason: str
) -> str:
    parts = f"{scope_id or ''}|{source}|{normalised_reason}"
    return hashlib.sha256(parts.encode("utf-8")).hexdigest()

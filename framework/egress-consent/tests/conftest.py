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

"""Shared fixtures for the egress-consent tests.

``recording_transport`` is a real, deterministic send transport that records
exactly what bytes were handed to it — so a test can assert NOTHING was sent
(the never-leak guarantee) or that EXACTLY the approved set was sent. It is NOT
a stub of the gate; the gate runs in full and either refuses (transport never
called) or passes (transport called once with the real payload).
"""

from __future__ import annotations

import pytest


class RecordingTransport:
    """Records (endpoint, payload) for every send. Egress is observable."""

    def __init__(self) -> None:
        self.sends: list[tuple[str, tuple[bytes, ...]]] = []

    def __call__(self, endpoint: str, payload: tuple[bytes, ...]) -> None:
        self.sends.append((endpoint, payload))

    @property
    def egress_occurred(self) -> bool:
        return bool(self.sends)

    @property
    def last_payload_bytes(self) -> bytes:
        if not self.sends:
            return b""
        return b"".join(self.sends[-1][1])


@pytest.fixture
def transport() -> RecordingTransport:
    return RecordingTransport()

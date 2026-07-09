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

"""AC.LEASE.6 — the README documents the known blind spot (leases catch
textual collisions only; semantic collisions are the merge queue's catch,
WS-B2) and presents the pair rather than overselling the lease.  It also
names the deferred mandatory-path wiring and the conservative-overlap
approximation.
"""

from __future__ import annotations

from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_AC_LEASE_6_readme_documents_blind_spot_and_pairing():
    text = README.read_text().lower()
    # textual-only + semantic-is-merge-queue pairing
    assert "textual" in text
    assert "semantic" in text
    assert "merge queue" in text
    assert "ws-b2" in text
    assert "neither alone" in text
    # deferred mandatory-path wiring named
    assert "follow-up" in text
    assert "mandatory dispatch path" in text
    # conservative-overlap approximation named
    assert "conservative" in text

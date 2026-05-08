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

"""Test fixtures for telegram-interface.

Most tests use in-memory fakes — no real Telegram API calls, no real
MCP connection. The availability probe is driven by fake ``getme``
and ``mcp_tool_probe`` callables.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.telegram_interface.allowlist import AccessFile, AuthorityClass


@pytest.fixture
def tmp_access(tmp_path: Path) -> AccessFile:
    path = tmp_path / "access.json"
    a = AccessFile(path=path, data={
        "dmPolicy": "allowlist",
        "allowFrom": [],
        "groups": {},
        "pending": {},
        "pos_identities": {},
    })
    a.save()
    return a


@pytest.fixture
def tmp_access_with_owner(tmp_path: Path) -> AccessFile:
    path = tmp_path / "access.json"
    a = AccessFile(path=path, data={
        "dmPolicy": "allowlist",
        "allowFrom": ["111111"],
        "groups": {},
        "pending": {},
        "pos_identities": {
            "111111": {
                "user_id": "111111",
                "display_name": "Luke",
                "relationship": "owner",
                "authority_class": AuthorityClass.OWNER,
                "added_at": "2026-04-22T00:00:00+00:00",
            }
        },
    })
    a.save()
    return a


@pytest.fixture
def tmp_access_with_spouse(tmp_path: Path) -> AccessFile:
    path = tmp_path / "access.json"
    a = AccessFile(path=path, data={
        "dmPolicy": "allowlist",
        "allowFrom": ["111111", "222222"],
        "groups": {},
        "pending": {},
        "pos_identities": {
            "111111": {
                "user_id": "111111",
                "display_name": "Luke",
                "relationship": "owner",
                "authority_class": AuthorityClass.OWNER,
                "added_at": "2026-04-22T00:00:00+00:00",
            },
            "222222": {
                "user_id": "222222",
                "display_name": "Partner",
                "relationship": "spouse",
                "authority_class": AuthorityClass.REDUCED_BOUND,
                "added_at": "2026-04-22T01:00:00+00:00",
            },
        },
    })
    a.save()
    return a

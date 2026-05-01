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

"""Shared pytest fixtures for self-upgrade tests."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

# Add src/ to path for editable imports when running against tree
_HERE = Path(__file__).parent
sys.path.insert(0, str((_HERE.parent / "src").resolve()))


@pytest.fixture
def tmp_history(tmp_path: Path) -> Path:
    d = tmp_path / "framework" / "history"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def sample_manifest_dict() -> dict:
    return {
        "release_tag": "pos-v2-v0.2.0",
        "commit_sha": "abcdef1234567",
        "files": [
            {
                "path": "framework/self_upgrade/cli.py",
                "expected_pre_sha": "a" * 64,
                "expected_post_sha": "b" * 64,
                "change_kind": "modified",
            },
            {
                "path": "framework/self_upgrade/fresh.py",
                "expected_pre_sha": None,
                "expected_post_sha": "c" * 64,
                "change_kind": "new",
            },
            {
                "path": "framework/self_upgrade/old.py",
                "expected_pre_sha": "d" * 64,
                "expected_post_sha": None,
                "change_kind": "deleted",
            },
            {
                "path": "framework/self_upgrade/same.py",
                "expected_pre_sha": "e" * 64,
                "expected_post_sha": "e" * 64,
                "change_kind": "unchanged",
            },
        ],
        "component_schemas": [
            {"component": "memory", "version_pre": 3, "version_post": 3},
            {"component": "scope_of_work", "version_pre": 5, "version_post": 5},
        ],
        "breaking_changes": [],
        "migrations": [],
        "generated_at": "2026-04-19T12:00:00Z",
    }


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def write_file_sha():
    """Return a helper: writes content and returns its sha256."""

    def _w(p: Path, content: bytes) -> str:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return _sha(content)

    return _w

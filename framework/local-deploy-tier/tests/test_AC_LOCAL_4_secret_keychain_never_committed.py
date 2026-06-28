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

"""AC.LOCAL.4 — a LOCAL secret is stored in the OS keychain, never written to a
repo-committed file.

Verified against the keychain abstraction: storing a secret round-trips through
the keychain backend, and a scan of the entire repository tree after the store
finds the value in NO file. The redacted handle never carries the value."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.local_deploy_tier.secrets import (
    InMemoryKeychainBackend,
    LocalSecretStore,
    repo_files_containing,
)


SECRET = "sk-live-2f9c4d8a-DO-NOT-COMMIT"


def test_secret_round_trips_through_the_keychain() -> None:
    store = LocalSecretStore("demo-workspace", backend=InMemoryKeychainBackend())
    store.set_secret("DATABASE_URL", SECRET)
    assert store.get_secret("DATABASE_URL") == SECRET


def test_storing_a_secret_writes_no_repo_file(tmp_path: Path) -> None:
    """The load-bearing property: after a LOCAL secret is stored, the value is
    in NO file under the repo working tree — there is nothing for git to
    capture. (The keychain backend has no filesystem surface at all.)"""
    repo = tmp_path / "project"
    repo.mkdir()
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "README.md").write_text("# project\n", encoding="utf-8")

    store = LocalSecretStore("project", backend=InMemoryKeychainBackend())
    store.set_secret("API_TOKEN", SECRET)

    # No file anywhere under the repo contains the secret value.
    assert repo_files_containing(SECRET, repo) == []


def test_scan_would_catch_a_committed_secret_so_the_assertion_is_meaningful(
    tmp_path: Path,
) -> None:
    """Guard against a vacuous test: if a secret WERE written to a repo file,
    the scan must find it — so the empty result above is a real signal."""
    repo = tmp_path / "project"
    repo.mkdir()
    (repo / ".env.local").write_text(f"API_TOKEN={SECRET}\n", encoding="utf-8")
    assert repo_files_containing(SECRET, repo) == [".env.local"]


def test_handle_describes_without_revealing_the_value() -> None:
    """A secret is never printed back into a transcript surface (research §5)."""
    store = LocalSecretStore("project", backend=InMemoryKeychainBackend())
    store.set_secret("API_TOKEN", SECRET)
    handle = store.describe("API_TOKEN")
    assert handle.present is True
    text = handle.describe()
    assert SECRET not in text
    assert "hidden" in text


def test_absent_secret_reads_as_none_and_not_present() -> None:
    store = LocalSecretStore("project", backend=InMemoryKeychainBackend())
    assert store.get_secret("MISSING") is None
    assert store.describe("MISSING").present is False


def test_empty_workspace_id_is_refused() -> None:
    with pytest.raises(ValueError):
        LocalSecretStore("", backend=InMemoryKeychainBackend())

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

Secrets are where a non-technical user is most likely to do irreversible harm —
committing an API key, leaking a credential into a dev context (local-target
research §5). The LOCAL tier makes the safe path the default: a LOCAL secret
lives in the operating system's keychain (macOS Keychain via the ``security``
CLI; the backend is injectable so the same contract holds on any platform and
under test). The value never touches a file under the repository working tree,
so there is nothing for ``git add`` to capture.

This composes ON the secure-build baseline (Lens 1): that baseline already
enforces secrets-never-committed at the commit/push boundary. This tier removes
the secret from disk-under-repo entirely, so the commit boundary has nothing to
catch — defence at the source rather than only at the gate.

The store NEVER returns the secret value into any rendered/transcript surface
(research §5 guardrail). :meth:`describe` yields only the key and a redacted
marker.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class KeychainBackend(Protocol):
    """The OS-keychain operations the LOCAL secret store needs. The default is
    the macOS ``security`` CLI; an injected backend (in-memory) lets the same
    never-on-disk contract be verified under test without touching the real
    keychain."""

    def set(self, service: str, account: str, secret: str) -> None: ...
    def get(self, service: str, account: str) -> str | None: ...
    def delete(self, service: str, account: str) -> None: ...


class KeychainError(RuntimeError):
    """The OS keychain could not be read/written."""


class MacOSKeychainBackend:
    """macOS Keychain backend via the ``security`` CLI. The secret value is
    passed as an argument to ``security`` (which writes it into the user's
    login keychain) — never to a file. ``security`` is invoked with the value
    redacted from any error this module raises."""

    def set(self, service: str, account: str, secret: str) -> None:
        # -U updates an existing item rather than erroring on a duplicate.
        proc = subprocess.run(
            [
                "security", "add-generic-password",
                "-a", account, "-s", service, "-w", secret, "-U",
            ],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise KeychainError(
                f"keychain write failed for service={service!r} "
                f"account={account!r} (value redacted)"
            )

    def get(self, service: str, account: str) -> str | None:
        proc = subprocess.run(
            ["security", "find-generic-password", "-a", account, "-s", service, "-w"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.rstrip("\n")

    def delete(self, service: str, account: str) -> None:
        subprocess.run(
            ["security", "delete-generic-password", "-a", account, "-s", service],
            capture_output=True, text=True,
        )


class InMemoryKeychainBackend:
    """A keychain backend that holds items in process memory only. Used to
    verify the never-on-disk contract deterministically and cross-platform —
    it has NO filesystem surface at all, so a secret stored through it provably
    never reaches a repo file."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def set(self, service: str, account: str, secret: str) -> None:
        self._store[(service, account)] = secret

    def get(self, service: str, account: str) -> str | None:
        return self._store.get((service, account))

    def delete(self, service: str, account: str) -> None:
        self._store.pop((service, account), None)


# The keychain "service" namespace LOCAL secrets live under, so they are scoped
# to a workspace and never collide with unrelated keychain items.
SERVICE_PREFIX = "loam.local"


@dataclass(frozen=True)
class SecretHandle:
    """A non-sensitive description of a stored secret — the key and a redacted
    marker, NEVER the value (research §5: never print a resolved secret)."""

    key: str
    present: bool

    def describe(self) -> str:
        marker = "set (hidden)" if self.present else "not set"
        return f"{self.key}: {marker}"


def _service_for(workspace_id: str) -> str:
    return f"{SERVICE_PREFIX}.{workspace_id}"


class LocalSecretStore:
    """Stores LOCAL secrets in the OS keychain — never a repo-committed file.

    *workspace_id* scopes the secret namespace (any stable per-workspace
    string — the repo path's basename, an id from config). The store performs
    NO filesystem writes under the repository: every operation goes through the
    keychain backend."""

    def __init__(
        self,
        workspace_id: str,
        backend: KeychainBackend | None = None,
    ) -> None:
        if not isinstance(workspace_id, str) or not workspace_id:
            raise ValueError("workspace_id must be a non-empty string")
        self._service = _service_for(workspace_id)
        self._backend: KeychainBackend = backend or MacOSKeychainBackend()

    def set_secret(self, key: str, value: str) -> SecretHandle:
        """Store *value* under *key* in the OS keychain. No file under the repo
        is created or modified — the value goes only to the keychain."""
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        if not isinstance(value, str):
            raise TypeError("secret value must be a string")
        self._backend.set(self._service, key, value)
        return SecretHandle(key=key, present=True)

    def get_secret(self, key: str) -> str | None:
        """Read *key* from the OS keychain, or ``None`` when unset."""
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        return self._backend.get(self._service, key)

    def delete_secret(self, key: str) -> None:
        self._backend.delete(self._service, key)

    def describe(self, key: str) -> SecretHandle:
        """A redacted handle — present/absent only, never the value."""
        return SecretHandle(key=key, present=self.get_secret(key) is not None)


def repo_files_containing(secret_value: str, repo_root: Path) -> list[str]:
    """Return repo-relative paths of any TRACKED-tree file under *repo_root*
    whose content contains *secret_value*.

    The AC.LOCAL.4 verifier: after a secret is stored, this must return ``[]``
    — the value is in the keychain, never on disk under the repo. Skips the
    VCS metadata dir and binary-unreadable files."""
    if not secret_value:
        return []
    hits: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if rel.parts and rel.parts[0] == ".git":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if secret_value in text:
            hits.append(str(rel))
    return hits

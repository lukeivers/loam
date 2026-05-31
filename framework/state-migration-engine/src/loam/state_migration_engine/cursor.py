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

"""The per-workspace applied-migration CURSOR (AC.MIG-REPLAY.3).

The cursor is USER-STATE: ``<workspace>/.loam/migrations/.cursor`` (gitignored;
home established by P1.2's ``establish_loam_layout``; see
``docs/state-migrations/README.md``). It is the authoritative record of which
declared migrations THIS workspace has applied.

Per D1 the replay-order key is the RELEASE-VERSION (stamped at release time),
so the cursor records (a) the last-applied resolved version and (b) the ordered
list of applied slugs (the audit trail). The cursor is append-only in spirit:
``advance`` only ever moves it forward to a later version + appends the slug.

Format: a small YAML document so a human browsing user-state can read it. A
missing cursor means "nothing applied yet" (a fresh instance) — the engine
treats absent as the empty cursor, never an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


CURSOR_FILENAME = ".cursor"


def cursor_path(workspace_root: str | Path) -> Path:
    """Resolve the cursor path under a workspace root.

    ``<workspace>/.loam/migrations/.cursor`` — the home P1.2 declared.
    """
    return Path(workspace_root) / ".loam" / "migrations" / CURSOR_FILENAME


@dataclass
class AppliedCursor:
    """The applied-migration cursor for one workspace.

    ``applied_version`` is the last resolved release-version applied (``None``
    on a fresh instance). ``applied_slugs`` is the ordered audit trail of every
    applied migration slug.
    """

    applied_version: str | None = None
    applied_slugs: list[str] = field(default_factory=list)

    def has_applied(self, slug: str) -> bool:
        return slug in self.applied_slugs

    def advance(self, *, version: str, slug: str) -> None:
        """Record one migration as applied — appends slug, moves the version.

        Idempotent on slug: a slug already recorded is not appended twice
        (supports a re-run / interrupted-and-restarted replay — AC.MIG-SAFE.3).
        """
        if slug not in self.applied_slugs:
            self.applied_slugs.append(slug)
        self.applied_version = version


def read_cursor(workspace_root: str | Path) -> AppliedCursor:
    """Read the cursor for *workspace_root*; absent → empty cursor.

    A fresh instance (no ``.cursor`` yet) reads as the empty cursor — never an
    error. A malformed cursor is also tolerated as empty (the safest reading:
    re-deriving the pending set against a fresh cursor re-applies idempotent
    migrations rather than corrupting state).
    """
    path = cursor_path(workspace_root)
    if not path.exists():
        return AppliedCursor()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return AppliedCursor()
    if not isinstance(data, dict):
        return AppliedCursor()
    slugs = data.get("applied_slugs") or []
    if not isinstance(slugs, list):
        slugs = []
    version = data.get("applied_version")
    if version is not None and not isinstance(version, str):
        version = None
    return AppliedCursor(
        applied_version=version,
        applied_slugs=[str(s) for s in slugs],
    )


def write_cursor(workspace_root: str | Path, cursor: AppliedCursor) -> Path:
    """Persist *cursor* under *workspace_root*; returns the cursor path.

    Ensures the ``.loam/migrations/`` home exists (P1.2 establishes it on a
    bootstrapped workspace; the engine is defensive for a hand-seeded one).
    """
    path = cursor_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "applied_version": cursor.applied_version,
        "applied_slugs": list(cursor.applied_slugs),
    }
    path.write_text(
        yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return path

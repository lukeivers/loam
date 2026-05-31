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

"""The REPLAY engine (AC.MIG-REPLAY.* + AC.MIG-SAFE.*).

Read the per-instance applied cursor -> enumerate pending declared migrations
in RELEASE-VERSION order (D1) -> apply each declarative step IN ORDER through
intermediates (never jumping) -> advance the cursor. The whole replay is
WRAPPED in the reversibility-primitive safety envelope (``envelope.py``):
backup-first, protection-floor gate, rollback-on-failure.

Declarative-only (D2): a migration's *apply* is interpreted from its declared
``operation`` token. The current closed vocabulary is wholly non-destructive,
so applying is idempotent and forward-additive:

  * ``structural-only`` -> ensure the declared ``creates:`` paths exist
    (additive; never overwrites). This is the only operation that touches the
    filesystem at apply time.
  * ``no-op`` / ``none-code-only`` / ``schema-add-forward-additive`` -> no
    on-disk apply step (the new field appears lazily on NEW writes; code-only
    changes nothing). The engine still records the cursor advance so the
    migration is accounted as applied.

There is NO embedded-script execution path (D2 defers it to a later slice).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .cursor import AppliedCursor, read_cursor, write_cursor
from .envelope import MigrationSafetyEnvelope
from .schema import DeclaredMigration, load_migration_dir


class MigrationOrderError(ValueError):
    """A migration lacks the release-version stamp needed to order replay.

    Per D1 the replay-order key is the release-version (stamped at release
    time by the release-gate). A pending migration with no ``version`` cannot
    be ordered into the total replay sequence; this is a build/release-time
    error, surfaced rather than guessed (guessing the order risks corrupting
    user-state -- plan §8 #1).
    """


def _version_sort_key(version: str) -> tuple:
    """SemVer-ish sort key. ``v0.6.0`` -> (0, 6, 0); a 4th hot-patch segment
    (``v0.2.5.1``) is supported. Non-numeric tails sort after numeric so a
    pre-release suffix never outranks its base."""
    raw = version.lstrip("v")
    parts = raw.split(".")
    key: list = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p))
    return tuple(key)


def enumerate_pending(
    cursor: AppliedCursor,
    migrations: list[DeclaredMigration],
    *,
    target_version: str | None = None,
) -> list[DeclaredMigration]:
    """Compute the pending set in release-version order (AC.MIG-REPLAY.1/.2).

    Pending = every migration NOT already in the cursor's applied-slug set,
    ordered by its release-version stamp. When *target_version* is given, the
    set is bounded above by it (migrations beyond the target are excluded) --
    so an N->N+k upgrade applies exactly N+1..N+k through the intermediates,
    not only the target (AC.MIG-REPLAY.2, through-not-jump).

    Raises ``MigrationOrderError`` if a pending migration carries no version
    stamp (D1: the order key must exist for the pending set).
    """
    pending = [m for m in migrations if not cursor.has_applied(m.slug)]

    unstamped = [m.slug for m in pending if m.version is None]
    if unstamped:
        raise MigrationOrderError(
            "pending migration(s) carry no release-version stamp and cannot "
            "be ordered: " + ", ".join(sorted(unstamped)) + ". Per D1 the "
            "release-gate stamps `version:` at release time; an unstamped "
            "pending migration is a release-time gap."
        )

    if cursor.applied_version is not None:
        cur_key = _version_sort_key(cursor.applied_version)
        pending = [
            m for m in pending if _version_sort_key(m.version) > cur_key
        ]

    if target_version is not None:
        tgt_key = _version_sort_key(target_version)
        pending = [
            m for m in pending if _version_sort_key(m.version) <= tgt_key
        ]

    pending.sort(key=lambda m: _version_sort_key(m.version))
    return pending


def _apply_declarative_step(
    migration: DeclaredMigration, workspace_root: Path
) -> None:
    """Apply one migration's declarative step (D2 declarative-only).

    Only ``structural-only`` touches the filesystem -- it ensures the declared
    ``creates:`` paths exist (additive, idempotent; never overwrites). Every
    other operation in the closed vocabulary has no on-disk apply step.
    """
    if migration.operation == "structural-only":
        for rel in migration.creates:
            # `creates:` entries are declared relative to the workspace root
            # (e.g. `.loam/migrations/`). A trailing slash marks a directory;
            # the authored files use directory paths for structural-only.
            target = workspace_root / rel
            if rel.endswith("/") or not target.suffix:
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_text("", encoding="utf-8")
    # no-op / none-code-only / schema-add-forward-additive: no apply step.


@dataclass
class ReplayResult:
    """Outcome of a replay run.

    ``applied`` is the ordered list of slugs applied THIS run; ``cursor`` is
    the post-replay cursor; ``rolled_back`` is True when a failure triggered a
    restore (cursor then reflects the pre-replay state).
    """

    applied: list[str] = field(default_factory=list)
    cursor: AppliedCursor | None = None
    rolled_back: bool = False
    failure: str | None = None


def replay(
    workspace_root: str | Path,
    *,
    migrations_dir: str | Path,
    envelope: MigrationSafetyEnvelope,
    target_version: str | None = None,
) -> ReplayResult:
    """Run the wrapped, ordered, through-not-jump replay.

    Sequence (the manual care-flow this slice automates):
      1. read the cursor (absent -> fresh instance);
      2. load + validate the declared migrations;
      3. enumerate the pending set in release-version order;
      4. SNAPSHOT ``.loam/`` (backup-first, AC.MIG-SAFE.1);
      5. for each pending migration IN ORDER: GUARD (protection floor,
         AC.MIG-SAFE.4) -> apply the declarative step -> advance the cursor;
      6. on ANY failure: RESTORE from the snapshot (rollback-on-failure,
         AC.MIG-SAFE.2) and DO NOT persist an advanced cursor;
      7. on success: persist the advanced cursor (AC.MIG-REPLAY.3).

    Re-running after a clean completion is a no-op (the pending set is empty --
    AC.MIG-REPLAY.3, AC.MIG-SAFE.3 idempotent).
    """
    workspace_root = Path(workspace_root)
    cursor = read_cursor(workspace_root)
    migrations = load_migration_dir(migrations_dir)
    pending = enumerate_pending(
        cursor, migrations, target_version=target_version
    )

    result = ReplayResult(cursor=cursor)
    if not pending:
        # Clean no-op: nothing to do, cursor unchanged.
        return result

    snapshot = envelope.snapshot(workspace_root)
    try:
        for migration in pending:
            scope_id = f"migration-{migration.slug}"
            envelope.guard(migration, scope_id=scope_id)
            _apply_declarative_step(migration, workspace_root)
            cursor.advance(version=migration.version, slug=migration.slug)
            result.applied.append(migration.slug)
    except Exception as exc:  # noqa: BLE001 -- any failure rolls back
        envelope.restore(snapshot, workspace_root)
        # Re-read the pre-replay cursor from disk (the restore brought back the
        # snapshot's .cursor); the in-memory advance is discarded.
        result.cursor = read_cursor(workspace_root)
        result.rolled_back = True
        result.applied = []
        result.failure = str(exc)
        return result

    write_cursor(workspace_root, cursor)
    result.cursor = cursor
    return result

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

"""``loam migrate`` -- the real upgrade entry-point (D4 / AC.MIG-UPGRADE.1).

Registers through the unified loam CLI dispatcher's ``loam.cli.subcommands``
entry-point group (the same pattern as ``loam release`` / ``loam amend``).
This verb IS the production entry-point the outcome-altitude AC drives -- a
real, testable surface, not an inner function (today's lesson,
``feedback_test_outcome_altitude_required``).

    loam migrate [--workspace <root>] [--migrations-dir <dir>]
                 [--target-version <v>] [--dry-run]

The session-start auto-detect hook (D4 option B) is a fast-follow OUT of this
slice -- a thin consumer that invokes this verb when the cursor is behind.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from loam.reversibility_primitive import ReversibilityStore

from .envelope import MigrationSafetyEnvelope
from .replay import enumerate_pending, replay
from .cursor import read_cursor
from .schema import load_migration_dir


def _default_migrations_dir(repo_root: Path) -> Path:
    """The tracked declared-migration contract home (``docs/state-migrations/``).

    Defaults relative to *repo_root*; production invocations run from the loam
    repo, where the contract ships + versions with the framework.
    """
    return repo_root / "docs" / "state-migrations"


def build_migrate_subcommand(sub: argparse._SubParsersAction) -> None:
    """Register the ``migrate`` subcommand on *sub* (builder contract)."""
    p = sub.add_parser(
        "migrate",
        help=(
            "upgrade this workspace's .loam/ user-state: replay pending "
            "declared migrations in release-version order, wrapped in the "
            "reversibility safety envelope (backup-first, rollback-on-failure)"
        ),
        description=(
            "Read the per-workspace applied-migration cursor, enumerate the "
            "pending declared migrations in release-version order, and replay "
            "them through intermediates inside a backup -> apply -> "
            "rollback-on-failure envelope. Safe to re-run (a fully-migrated "
            "workspace is a no-op). A non-technical user can run this without "
            "risk -- a failed upgrade rolls the workspace back to its "
            "pre-upgrade state."
        ),
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="workspace root to migrate (default: current directory)",
    )
    p.add_argument(
        "--migrations-dir",
        type=Path,
        default=None,
        help=(
            "declared-migration contract dir (default: "
            "<repo-root>/docs/state-migrations relative to the workspace)"
        ),
    )
    p.add_argument(
        "--target-version",
        default=None,
        help=(
            "upgrade only up to this release-version (default: latest "
            "declared). Applies every intermediate up to and including it."
        ),
    )
    p.add_argument(
        "--snapshot-root",
        type=Path,
        default=None,
        help=(
            "where to write the pre-replay .loam/ backup (default: a temp dir)"
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="report the pending set + order without applying anything",
    )
    p.set_defaults(func=dispatch)


def dispatch(args: argparse.Namespace) -> int:
    """Run the matched ``loam migrate`` invocation. Returns an exit code."""
    workspace = (args.workspace or Path.cwd()).resolve()
    migrations_dir = (
        args.migrations_dir
        if args.migrations_dir is not None
        else _default_migrations_dir(workspace)
    ).resolve()

    if not migrations_dir.is_dir():
        print(
            f"loam migrate: declared-migration dir not found at "
            f"{migrations_dir}. Pass --migrations-dir or run from the loam "
            f"repo root."
        )
        return 2

    if args.dry_run:
        cursor = read_cursor(workspace)
        migrations = load_migration_dir(migrations_dir)
        pending = enumerate_pending(
            cursor, migrations, target_version=args.target_version
        )
        if not pending:
            print(
                f"loam migrate (dry-run): {workspace} is up to date "
                f"(cursor at {cursor.applied_version or 'fresh'}); nothing "
                f"pending."
            )
            return 0
        print(
            f"loam migrate (dry-run): {len(pending)} migration(s) pending "
            f"for {workspace} (cursor at {cursor.applied_version or 'fresh'}):"
        )
        for m in pending:
            print(f"  - {m.version}  {m.slug}  [{m.operation}]")
        return 0

    snapshot_root = (
        args.snapshot_root
        if args.snapshot_root is not None
        else Path(tempfile.mkdtemp(prefix="loam-migrate-snapshot-"))
    )
    store = ReversibilityStore(snapshot_root / "reversibility.sqlite")
    envelope = MigrationSafetyEnvelope(
        store=store, snapshot_root=snapshot_root
    )

    result = replay(
        workspace,
        migrations_dir=migrations_dir,
        envelope=envelope,
        target_version=args.target_version,
    )

    if result.rolled_back:
        print(
            f"loam migrate: FAILED and ROLLED BACK -- {workspace} restored to "
            f"its pre-upgrade state. Reason: {result.failure}"
        )
        return 1

    if not result.applied:
        cur = result.cursor.applied_version if result.cursor else None
        print(
            f"loam migrate: {workspace} is up to date "
            f"(cursor at {cur or 'fresh'}); nothing applied."
        )
        return 0

    cur = result.cursor.applied_version if result.cursor else None
    print(
        f"loam migrate: applied {len(result.applied)} migration(s); "
        f"{workspace} is now at {cur}:"
    )
    for slug in result.applied:
        print(f"  + {slug}")
    return 0

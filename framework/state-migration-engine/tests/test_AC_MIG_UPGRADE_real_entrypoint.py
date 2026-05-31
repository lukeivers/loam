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

"""AC.MIG-UPGRADE.1 — OUTCOME-ALTITUDE: a real N->N+k upgrade at the TRUE
entry-point.

This AC may NOT be satisfied by a unit test of the inner replay function. It
seeds a genuinely SEPARATE workspace instance (a temp ``.loam/`` at a real
prior cursor version, with real seeded user-state) and drives the PRODUCTION
``loam migrate`` entry-point — the unified ``loam`` CLI dispatcher
(``loam_cli.cli.main(["migrate", ...])``) resolving the ``migrate`` verb through
the same entry-point group a real shell invocation uses. No pre-arranged
internal replay state. (Today's lesson: ACs hit the real entry-point, not just
the inner function — feedback_test_outcome_altitude_required.)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_cli.cli import main as loam_main

from loam.state_migration_engine import read_cursor

from .conftest import seed_workspace, write_migration


def test_AC_MIG_UPGRADE_1_separate_instance_N_to_Nplusk_via_loam_migrate(
    tmp_path: Path,
) -> None:
    """A separate seeded instance at version N is upgraded to N+k by invoking
    the REAL `loam migrate` verb through the unified CLI dispatcher, replaying
    the intermediates in order; afterward the cursor reads the target, the
    seeded user-state survives intact, and the store is consistent."""
    # --- a genuinely separate workspace instance, seeded with real state ---
    ws = tmp_path / "separate-instance"
    seed_workspace(
        ws,
        episodes={
            "ep-001.md": "real user episode one — must survive the upgrade",
            "ep-002.md": "real user episode two — must survive the upgrade",
        },
    )

    # Seed the cursor at a real prior version N (= v0.1.0): the instance has
    # already applied m1 and sits behind the rest of the chain.
    cursor_file = ws / ".loam" / "migrations" / ".cursor"
    cursor_file.write_text(
        yaml.safe_dump(
            {"applied_version": "v0.1.0", "applied_slugs": ["m1"]},
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    # --- the declared-migration contract: a chain N .. N+k ---
    md = tmp_path / "docs" / "state-migrations"
    write_migration(md, slug="m1", version="v0.1.0", operation="no-op")  # already applied
    write_migration(md, slug="m2", version="v0.2.0", operation="structural-only", creates=[".loam/user-model/"])
    write_migration(md, slug="m3", version="v0.3.0", operation="schema-add-forward-additive")
    write_migration(md, slug="m4", version="v0.4.0", operation="structural-only", creates=[".loam/session-model/"])

    snapshot_root = tmp_path / "snap"

    # --- drive the REAL `loam migrate` entry-point (no inner-function call) ---
    rc = loam_main(
        [
            "migrate",
            "--workspace", str(ws),
            "--migrations-dir", str(md),
            "--target-version", "v0.4.0",
            "--snapshot-root", str(snapshot_root),
        ]
    )
    assert rc == 0

    # --- verify at the true entry-point's observable effects ---
    # The cursor reads the target version N+k, with every intermediate applied
    # in order (m1 was pre-applied; m2..m4 added this run — through-not-jump).
    cursor = read_cursor(ws)
    assert cursor.applied_version == "v0.4.0"
    assert cursor.applied_slugs == ["m1", "m2", "m3", "m4"]

    # The structural-only intermediates created their declared paths.
    assert (ws / ".loam" / "user-model").is_dir()
    assert (ws / ".loam" / "session-model").is_dir()

    # The seeded user-state survived intact — no episode rewritten or lost.
    assert (
        ws / ".loam" / "memory" / "episodes" / "ep-001.md"
    ).read_text() == "real user episode one — must survive the upgrade"
    assert (
        ws / ".loam" / "memory" / "episodes" / "ep-002.md"
    ).read_text() == "real user episode two — must survive the upgrade"

    # Re-running the real entry-point is a clean no-op (idempotent at the true
    # surface, not just the inner function).
    rc2 = loam_main(
        [
            "migrate",
            "--workspace", str(ws),
            "--migrations-dir", str(md),
            "--snapshot-root", str(snapshot_root),
        ]
    )
    assert rc2 == 0
    assert read_cursor(ws).applied_slugs == ["m1", "m2", "m3", "m4"]

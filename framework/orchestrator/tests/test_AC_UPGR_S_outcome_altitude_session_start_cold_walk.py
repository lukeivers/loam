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

"""★ AC.UPGR.S (outcome-altitude: true) — the cold-walk.

A genuinely SEPARATE instance (a temp ``.loam/`` workspace seeded at a real
prior cursor version with real seeded user-state) reaches the SessionStart
auto-upgrade entry-point with NO pre-arranged trigger state; the auto-detect
fires, the wrapped replay runs THROUGH the intermediate migrations, the cursor
reads the target version, the seeded user-state SURVIVES intact, and the
plain-language surface reports it.

This AC may NOT be satisfied by a unit test of the trigger function. It drives
``emit_auto_upgrade_surface`` — the live-shaped SessionStart contributor
entry-point the (owner-gated) ``pos_session_start.py:main()`` wiring would call
— and captures the additionalContext line it emits, exactly as the live hook
would (feedback_test_outcome_altitude_required).

COLD-WALK DISCIPLINE (plan §8.6): the instance is a SEPARATE temp root seeded
with real user-state; the live pos3 store is NEVER written. The auto-detect is
pointed at the temp instance + a temp declared-migration contract by
redirecting the module's workspace-root resolver to the temp root (the same
``_loam_root`` resolution production uses) — there is NO pre-arranged
trigger/replay state; detection + replay run end-to-end from the entry-point.
"""

from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCH_SCRIPTS = REPO_ROOT / "framework" / "orchestrator" / "scripts"
if str(ORCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ORCH_SCRIPTS))

import auto_upgrade  # noqa: E402
from auto_upgrade import emit_auto_upgrade_surface  # noqa: E402

from loam.state_migration_engine.cursor import read_cursor  # noqa: E402


_VERSION_RE = re.compile(r"\bv?\d+\.\d+(\.\d+)?\b")
_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
_FORBIDDEN = ("cursor", "migration", "slug", "replay", ".loam", "AC.")


def _write_migration(directory: Path, *, slug: str, version: str, operation: str = "structural-only", creates=None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = {
        "slug": slug,
        "operation": operation,
        "reversible": True,
        "removes_user_state": False,
        "idempotent": True,
        "version": version,
    }
    if creates is not None:
        doc["creates"] = creates
    (directory / f"{slug}.migration.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )


def test_AC_UPGR_S_cold_walk_session_start_auto_upgrade(
    tmp_path: Path, monkeypatch
) -> None:
    # --- a genuinely SEPARATE temp instance with REAL seeded user-state ------
    # (a synthetic real instance — the live pos3 store is never touched).
    temp_root = tmp_path / "separate-loam-root"
    ws = temp_root  # the workspace IS the loam root for this instance
    episodes = ws / ".loam" / "memory" / "episodes"
    episodes.mkdir(parents=True, exist_ok=True)
    (episodes / "ep-001.md").write_text(
        "real user episode one — must survive the auto-upgrade", encoding="utf-8"
    )
    (episodes / "ep-002.md").write_text(
        "real user episode two — must survive the auto-upgrade", encoding="utf-8"
    )

    # Seed the cursor at a real prior version N (= v0.1.0): m1 applied, behind
    # the rest of the shipped chain. This is the ONLY pre-state — there is no
    # pre-arranged trigger/replay artefact.
    cursor_file = ws / ".loam" / "migrations" / ".cursor"
    cursor_file.parent.mkdir(parents=True, exist_ok=True)
    cursor_file.write_text(
        yaml.safe_dump(
            {"applied_version": "v0.1.0", "applied_slugs": ["m1"]}, sort_keys=False
        ),
        encoding="utf-8",
    )

    # The declared-migration contract ships under <loam-root>/docs/state-
    # migrations — exactly where production resolves it. A chain N..N+k.
    md = temp_root / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0", operation="no-op")  # already applied
    _write_migration(md, slug="m2", version="v0.2.0", creates=[".loam/user-model/"])
    _write_migration(md, slug="m3", version="v0.3.0", operation="schema-add-forward-additive")
    _write_migration(md, slug="m4", version="v0.4.0", creates=[".loam/session-model/"])

    # Redirect the module's loam-root resolver to the temp instance — the SAME
    # resolution production uses (parents[3]); the live entry-point then reads
    # the temp cursor + the temp contract with NO migrations-dir override.
    monkeypatch.setattr(auto_upgrade, "_loam_root", lambda: temp_root)

    # --- drive the LIVE-shaped SessionStart entry-point, capture its emit ----
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit_auto_upgrade_surface(workspace_root=ws)
    surface = buf.getvalue().strip()

    # --- the entry-point's observable effects -------------------------------
    # 1) The auto-detect fired + the wrapped replay ran through the
    #    intermediates: the cursor reads the TARGET version, every step applied
    #    in order (m1 pre-applied; m2..m4 this run — through-not-jump).
    cursor = read_cursor(ws)
    assert cursor.applied_version == "v0.4.0"
    assert cursor.applied_slugs == ["m1", "m2", "m3", "m4"]

    # 2) The structural intermediates created their declared paths.
    assert (ws / ".loam" / "user-model").is_dir()
    assert (ws / ".loam" / "session-model").is_dir()

    # 3) The seeded user-state survived intact — no episode rewritten or lost.
    assert (episodes / "ep-001.md").read_text() == (
        "real user episode one — must survive the auto-upgrade"
    )
    assert (episodes / "ep-002.md").read_text() == (
        "real user episode two — must survive the auto-upgrade"
    )

    # 4) The plain-language surface was EMITTED (the live additionalContext
    #    line) and reports the upgrade — with NO internal vocabulary.
    assert surface, "the live entry-point emitted no surface for a real upgrade"
    low = surface.lower()
    assert "up to date" in low or "preserved" in low
    assert "3 updates" in surface  # m2, m3, m4
    for tok in _FORBIDDEN:
        assert tok.lower() not in low, f"internal token {tok!r} leaked: {surface!r}"
    assert not _VERSION_RE.search(surface), f"version string leaked: {surface!r}"
    assert not _SHA_RE.search(low), f"SHA-like token leaked: {surface!r}"

    # 5) Re-reaching the entry-point is a quiet no-op (idempotent at the true
    #    surface): the now-current instance emits nothing.
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        emit_auto_upgrade_surface(workspace_root=ws)
    assert buf2.getvalue().strip() == ""
    assert read_cursor(ws).applied_slugs == ["m1", "m2", "m3", "m4"]

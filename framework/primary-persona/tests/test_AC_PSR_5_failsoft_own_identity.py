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

"""AC.PSR.5 — fail-soft on the reader's OWN identity-resolution error.

Outcome (plan §4 AC.PSR.5, D1/D2): if the reader cannot resolve ITS OWN
session_key (env missing/garbled at read time), it degrades to today's
workspace-global behavior — never an empty/blank resume. Distinct from
AC.PSR.3 (an old episode with no key); this is the reader failing to
resolve its own key.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loam.primary_persona.active_thread import (
    ACTIVE_THREAD_MARKER,
    build_active_thread_contributor,
)
from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.session_identity import resolve_session_key

_SLUG = "pos3"


def test_AC_PSR_5_garbled_env_resolves_to_none() -> None:
    """A garbled/missing env resolves to None (→ workspace-global), not
    a spurious key that would filter everything out."""
    assert resolve_session_key({}) is None
    assert resolve_session_key({"CLAUDE_PERSONA": "   "}) is None
    assert resolve_session_key({"DISCORD_STATE_DIR": ""}) is None


def test_AC_PSR_5_none_key_sees_tagged_episodes_global(tmp_path: Path) -> None:
    """A reader that could not resolve its key (session_key None) still
    sees persona-tagged episodes — workspace-global, never blank."""
    store = FileMemoryStore(
        memory_dir=tmp_path / "workspace" / ".loam" / "memory"
    )
    for i in range(3):
        store.write_episode(
            name=f"turn/t-{i}",
            body=f"TAGGED episode {i} on the aurora thread",
            source_description="t",
            reference_time=datetime.now(timezone.utc),
            source="message",
            group_id=_SLUG,
            session_key="master-control",
        )
    fn = build_active_thread_contributor(
        store, workspace_root=tmp_path, workspace_slug=_SLUG, session_key=None
    )
    block = fn({})
    assert ACTIVE_THREAD_MARKER in block and "TAGGED episode" in block, (
        "a reader with no resolvable key must degrade to workspace-global "
        "(see everything), never a blank resume"
    )


def test_AC_PSR_5_store_that_rejects_filter_falls_back(tmp_path: Path) -> None:
    """If the store cannot honor the session_key filter (older signature
    / any error), the contributor degrades to a session-key-less scan
    rather than blanking (AC.PSR.5 fail-soft, defence-in-depth)."""

    class _LegacyStore:
        """A store whose recent_episodes predates the session_key kwarg."""

        def recent_episodes(
            self, *, group_ids: Any, limit: int
        ) -> list[dict[str, Any]]:
            return [
                {
                    "name": "turn/legacy",
                    "content": "LEGACY episode still resumes",
                    "path": "/x",
                    "group_id": _SLUG,
                    "valid_at": "",
                }
            ]

    fn = build_active_thread_contributor(
        _LegacyStore(),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert "LEGACY episode still resumes" in block, (
        "a store that rejects the session_key kwarg must fall back to the "
        "session-key-less scan, never blank"
    )

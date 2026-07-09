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

"""AC.PSR.3 — single-session no-op + old untagged episodes age out.

Outcome (plan §4 AC.PSR.3, D1/D5): a workspace with no ``CLAUDE_PERSONA``
(single-session / non-channel) resumes exactly as today; pre-migration
episodes that carry no ``session_key`` still surface (they are not
hidden by the new filter).

Two guarantees:
  1. session_key None => the recency scan is byte-identical to the
     pre-amendment path (single-session no-op).
  2. absent-key-inclusive => an UNTAGGED episode surfaces to a session
     that DOES carry a key (the D5 age-out contract — old episodes are
     never hidden merely for lacking a key).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.active_thread import (
    ACTIVE_THREAD_MARKER,
    build_active_thread_contributor,
)
from loam.primary_persona.file_memory import FileMemoryStore

_SLUG = "pos3"


def _store(root: Path) -> FileMemoryStore:
    return FileMemoryStore(memory_dir=root / "workspace" / ".loam" / "memory")


def _seed_untagged(root: Path, n: int = 4) -> None:
    store = _store(root)
    now = datetime.now(timezone.utc)
    for i in range(n):
        store.write_episode(
            name=f"turn/u-{i}",
            body=f"UNTAGGED legacy episode {i} on the migration thread",
            source_description="t",
            reference_time=now - timedelta(minutes=i + 1),
            source="message",
            group_id=_SLUG,
            # session_key omitted -> untagged (pre-amendment shape).
        )


def test_AC_PSR_3_single_session_surfaces_untagged(tmp_path: Path) -> None:
    """No CLAUDE_PERSONA (session_key None) resumes untagged episodes as
    today."""
    _seed_untagged(tmp_path)
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key=None,
    )
    block = fn({})
    assert ACTIVE_THREAD_MARKER in block
    assert "UNTAGGED legacy episode" in block, (
        "a single-session workspace must resume its (untagged) episodes"
    )


def test_AC_PSR_3_no_session_path_is_byte_identical(tmp_path: Path) -> None:
    """session_key None must produce the SAME digest the pre-amendment
    call produced — the store's no-session path is byte-identical."""
    _seed_untagged(tmp_path)
    store = _store(tmp_path)
    with_none = store.recent_episodes(group_ids=[_SLUG], limit=8, session_key=None)
    # The pre-amendment call did not pass session_key at all.
    without = store.recent_episodes(group_ids=[_SLUG], limit=8)
    assert with_none == without, (
        "passing session_key=None must be byte-identical to the "
        "pre-amendment no-arg recency scan"
    )


def test_AC_PSR_3_untagged_surfaces_to_a_keyed_session(tmp_path: Path) -> None:
    """A session that DOES carry a key still sees untagged (pre-migration)
    episodes — absent-key-inclusive age-out (D5), never hidden."""
    _seed_untagged(tmp_path)
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert "UNTAGGED legacy episode" in block, (
        "pre-migration untagged episodes must not be hidden by the new "
        "filter (D5 age-out is inclusive of absent keys)"
    )

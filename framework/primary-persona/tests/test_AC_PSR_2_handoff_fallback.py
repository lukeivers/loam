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

"""AC.PSR.2 — handoff-file fallback resume (D4, SECONDARY).

Outcome (plan §4 AC.PSR.2): a persona P with no episodes yet but a
``workspace/.loam/handoffs/P.md`` present resumes from that named file
at session-start; a ``handoffs/Q.md`` for another persona is NOT
surfaced in P's session (the read is persona-filtered by construction).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.active_thread import build_active_thread_contributor
from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.handoffs import write_handoff

_SLUG = "pos3"


def _store(root: Path) -> FileMemoryStore:
    return FileMemoryStore(memory_dir=root / "workspace" / ".loam" / "memory")


def test_AC_PSR_2_empty_store_resumes_from_handoff(tmp_path: Path) -> None:
    """No episodes, but a handoffs/master-control.md is present → P's
    session-start surfaces the handoff content."""
    write_handoff(
        tmp_path,
        persona="master-control",
        content="HANDOFF: resume the aurora migration; step 4 pending.",
    )
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert "aurora migration" in block, (
        "a persona with no episodes but a handoff file must resume from it"
    )


def test_AC_PSR_2_other_personas_handoff_not_surfaced(tmp_path: Path) -> None:
    """A handoffs/loam-dev.md is NOT surfaced in master-control's
    session (persona-filtered read)."""
    write_handoff(
        tmp_path,
        persona="loam-dev",
        content="OTHERHANDOFF: loam-dev private note.",
    )
    fn = build_active_thread_contributor(
        _store(tmp_path),
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert "OTHERHANDOFF" not in block, (
        "persona P must never surface another persona's handoff file"
    )
    # With no episodes and no own handoff, master-control's block is empty.
    assert block == "", "no own episodes or handoff => empty block"


def test_AC_PSR_2_handoff_secondary_to_episodes(tmp_path: Path) -> None:
    """The handoff is SECONDARY: when episodes exist they lead; the
    handoff appears after them (never promoted above the crash-robust
    episodes)."""
    from datetime import datetime, timezone

    store = _store(tmp_path)
    store.write_episode(
        name="turn/live",
        body="LIVE EPISODE aurora migration active thread",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id=_SLUG,
        session_key="master-control",
    )
    write_handoff(
        tmp_path, persona="master-control", content="SECONDARYHANDOFF note."
    )
    fn = build_active_thread_contributor(
        store,
        workspace_root=tmp_path,
        workspace_slug=_SLUG,
        session_key="master-control",
    )
    block = fn({})
    assert "LIVE EPISODE" in block and "SECONDARYHANDOFF" in block
    assert block.index("LIVE EPISODE") < block.index("SECONDARYHANDOFF"), (
        "episodes (primary) must precede the handoff (secondary)"
    )

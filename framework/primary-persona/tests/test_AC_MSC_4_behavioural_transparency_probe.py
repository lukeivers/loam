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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.MSC.4 — behavioural-transparency probe (the prime outcome,
end-to-end). The §10 HARD smoke: cold session-start cross-session
continuity.

Outcome (plan §4 AC.MSC.4): in a workspace whose most-recent
durably-stored memory is a known active thread with a pending owner
ruling, a cold session-start (simulating a session restart) produces
session context from which the active thread + its pending ruling are
recoverable, with no in-session state and no session-end hook having
run. The before-restart and after-restart context are not byte-for-
byte identical, but the active-thread + pending-ruling facts are
present in both.

This is the outcome-altitude AC; AC.MSC.1–3 are the mechanism ACs
that ladder into it. Ladders to AC.PO.1 (translation-burden —
session-amnesia is the maximal per-session-boundary burden) +
AC.PO.2 (toolkit — recency-aware session-start read is a reusable
persona primitive).

Method-in-AC test (plan §4): PASS — pure outcome (active thread
recoverable post-restart); every method that achieves it satisfies
it. This test asserts only the outcome.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.session_start_emitter import (
    cli_session_start,
    emit_session_start_context,
)


# The known active thread + its pending owner ruling. These are the
# facts that must survive a session restart.
_ACTIVE_TOPIC = "v0.11.0 ODD-paper corrective and KilnBench v2"
_PENDING_MARKER = "owner ruling pending"


def _seed_restart_workspace(root: Path) -> None:
    """A workspace whose most-recent durable memory is a known active
    thread with a pending owner ruling — and a named-thread durable
    surface recording the same. No in-session state; no session-end
    hook artefacts."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "# ws\n\n"
        "## Session-start discipline\n\n"
        "Read:\n\n"
        "- `docs/STATE.md`\n"
        "- `docs/FUTURE_IDEAS_DRAFT.md`\n"
        "\n---\n\n"
    )
    docs = root / "docs"
    docs.mkdir()
    (docs / "STATE.md").write_text("state")
    (docs / "FUTURE_IDEAS_DRAFT.md").write_text(
        "# FIDRAFT\n\n"
        f"- **F-INVERTED-FRAME — {_ACTIVE_TOPIC}; corrective experiment "
        f"needed.** Captured 2026-05-14. Status: OPEN; {_PENDING_MARKER} "
        "on the corrective shape (pos3 task seventy-five).\n"
    )
    pos = root / "workspace" / ".pos"
    pos.mkdir(parents=True)
    (pos / "first-run.state").write_text(
        json.dumps({"completed_at": "2026-04-25T00:00:00Z"})
    )
    (pos / "cost-headroom.json").write_text(
        json.dumps({"mtd_spend_usd": "1.00", "ceiling_usd": "500.00"})
    )

    store = FileMemoryStore(
        memory_dir=root / "workspace" / ".loam" / "memory"
    )
    slug = root.name.lower().replace("_", "-")
    now = datetime.now(timezone.utc)
    # Older episodes (the lexically-strong-but-stale distractors).
    for i in range(5):
        store.write_episode(
            name=f"turn/old-{i}",
            body="earlier work on memory pivot scaffolding and logs",
            source_description="t",
            reference_time=now - timedelta(days=15 + i),
            source="t",
            group_id=slug,
        )
    # The most-recent episodes ARE the active thread.
    store.write_episode(
        name="turn/active-1",
        body=(
            f"working the {_ACTIVE_TOPIC}: discussing the paper "
            "inversion and the v2 experiment design"
        ),
        source_description="t",
        reference_time=now - timedelta(minutes=40),
        source="t",
        group_id=slug,
    )
    store.write_episode(
        name="turn/active-2",
        body=(
            f"{_ACTIVE_TOPIC}: {_PENDING_MARKER} on the corrective "
            "shape — surfaced to owner, awaiting the ruling."
        ),
        source_description="t",
        reference_time=now - timedelta(minutes=8),
        source="t",
        group_id=slug,
    )


def test_AC_MSC_4_cold_session_start_recovers_active_thread(
    tmp_path: Path,
) -> None:
    """A cold session-start (no in-session state, no session-end hook)
    produces session context from which the active thread + its
    pending ruling are recoverable."""
    _seed_restart_workspace(tmp_path)

    # Cold session-start — exactly the post-restart entry point.
    post_restart = emit_session_start_context(tmp_path)
    assert post_restart, "cold session-start produced empty context"

    # The active-thread topic is recoverable.
    assert "KilnBench" in post_restart or "v0.11.0" in post_restart, (
        "post-restart session context must name the active thread; "
        f"head={post_restart[:200]!r}"
    )
    # The pending owner ruling is recoverable.
    assert "pending" in post_restart.lower(), (
        "post-restart session context must surface the pending owner "
        "ruling"
    )


def test_AC_MSC_4_before_and_after_restart_carry_same_facts(
    tmp_path: Path,
) -> None:
    """Before-restart and after-restart context are not byte-for-byte
    identical, but the active-thread + pending-ruling facts are
    present in both (the behavioural-transparency bar)."""
    _seed_restart_workspace(tmp_path)
    before = emit_session_start_context(tmp_path)
    # Simulate a restart: a brand-new emit with zero carried state.
    after = emit_session_start_context(tmp_path)

    def _has_facts(text: str) -> bool:
        t = text.lower()
        return (
            ("kilnbench" in t or "v0.11.0" in t)
            and "pending" in t
        )

    assert _has_facts(before), "pre-restart context missing the facts"
    assert _has_facts(after), "post-restart context missing the facts"
    # Behaviourally transparent: the load-bearing facts survive even
    # though the rendered text is regenerated each session.


def test_AC_MSC_4_cli_cold_start_emits_recoverable_context(
    tmp_path: Path, capsys
) -> None:
    """The session-start CLI (the real cold-start entry point Claude
    Code invokes on SessionStart) writes recoverable active-thread
    context to stdout and exits 0."""
    _seed_restart_workspace(tmp_path)
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert out, "cli_session_start produced no stdout"
    assert "KilnBench" in out or "v0.11.0" in out, (
        "the cold-start CLI payload must name the active thread"
    )
    assert "pending" in out.lower(), (
        "the cold-start CLI payload must surface the pending ruling"
    )


def test_AC_MSC_4_no_session_end_state_required(tmp_path: Path) -> None:
    """The recovery requires NO session-end / Stop artefact. Assert no
    Stop-hook state file exists in the seeded workspace yet the active
    thread is still recovered (capture is the continuous passive
    worker only; this path reads the episode store + named surface
    alone)."""
    _seed_restart_workspace(tmp_path)
    pos = tmp_path / "workspace" / ".pos"
    # No session-end capture artefacts seeded.
    assert not (pos / "last-turn-id").exists()
    assert not (pos / "memory-writes.log").exists()
    text = emit_session_start_context(tmp_path)
    assert "pending" in text.lower() and (
        "KilnBench" in text or "v0.11.0" in text
    ), (
        "active thread must be recoverable with zero session-end "
        "state — capture is continuous/passive, not session-end-gated"
    )

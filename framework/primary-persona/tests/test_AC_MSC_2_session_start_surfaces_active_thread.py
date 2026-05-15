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

"""AC.MSC.2 — session-start surfaces the active thread without a
session-end hook (Gap A part b closed).

Outcome (plan §4 AC.MSC.2): a fresh session (no prior in-session
state, no session-end hook having run) receives, in its session-start
``additionalContext``, a bounded digest of the most-recent active
working thread reconstructed from the durably-stored episodes. The
digest names the live topic and any pending owner ruling. No
session-end / Stop-hook capture is required — capture is the
already-existing continuous passive worker only.

Verification (plan §4): seed a workspace's episode store with a known
active-thread sequence; run the session-start path cold; assert the
emitted ``additionalContext`` contains the active-thread topic marker.
Separately assert no Stop / session-end hook is invoked or required
(the contributor reads only the episode store + named-thread
surfaces).

Method-in-AC test (plan §4): PASS — the AC pins the outcome (active
thread present at session-start, no session-end hook required); this
cycle's method is the deterministic recency scan (D-MSC.4) but the
test asserts the outcome, not the scan.
"""

from __future__ import annotations

import json
import inspect
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona import active_thread as active_thread_mod
from loam.primary_persona.active_thread import (
    ACTIVE_THREAD_BLOCK_CAP,
    ACTIVE_THREAD_MARKER,
    build_active_thread_contributor,
)
from loam.primary_persona.context_composer import TriggerKind
from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.session_start_emitter import (
    build_session_composer,
    emit_session_start_context,
)


def _seed_workspace(root: Path) -> None:
    """A fully-scaffolded baseline workspace (mirrors the AC46.1
    fixture shape) with NO persona-state and NO session-end hook
    artefacts."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(
        "# test workspace\n\n"
        "## Session-start discipline\n\n"
        "Before acting, read:\n\n"
        "- `docs/odd-methodology.md`\n"
        "- `docs/STATE.md`\n"
        "\n---\n\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "odd-methodology.md").write_text("odd")
    (root / "docs" / "STATE.md").write_text("state")
    pos = root / "workspace" / ".pos"
    pos.mkdir(parents=True)
    (pos / "first-run.state").write_text(
        json.dumps({"completed_at": "2026-04-25T00:00:00Z"})
    )
    (pos / "cost-headroom.json").write_text(
        json.dumps({"mtd_spend_usd": "1.00", "ceiling_usd": "500.00"})
    )


def _memory_dir(root: Path) -> Path:
    return root / "workspace" / ".loam" / "memory"


def _seed_active_thread(root: Path) -> None:
    """Write a known active-thread episode sequence — the newest
    episode names the live topic + a pending owner ruling."""
    store = FileMemoryStore(memory_dir=_memory_dir(root))
    slug = root.name.lower().replace("_", "-")
    now = datetime.now(timezone.utc)
    # Older background episodes.
    for i in range(3):
        store.write_episode(
            name=f"turn/bg-{i}",
            body="earlier background work on unrelated scaffolding",
            source_description="t",
            reference_time=now - timedelta(days=10 + i),
            source="t",
            group_id=slug,
        )
    # The ACTIVE THREAD — newest, names topic + pending ruling.
    store.write_episode(
        name="turn/active",
        body=(
            "ACTIVE: the v0.11.0 ODD-paper corrective and ProgramBench "
            "v2 experiment. Owner ruling is pending on the corrective "
            "shape (pos3 task seventy-five)."
        ),
        source_description="t",
        reference_time=now - timedelta(minutes=15),
        source="t",
        group_id=slug,
    )


def test_AC_MSC_2_contributor_registered_at_session_trigger(
    tmp_path: Path,
) -> None:
    """The active-thread contributor is registered at
    ``TriggerKind.session`` (so ``on_session_start`` invokes it —
    ``on_session_start`` skips every non-session-trigger
    contributor)."""
    _seed_workspace(tmp_path)
    _seed_active_thread(tmp_path)
    composer = build_session_composer(tmp_path)
    session_contribs = composer.contributors(TriggerKind.session)
    names = {c.name for c in session_contribs}
    assert "active-thread" in names, (
        "active-thread contributor must register at "
        f"TriggerKind.session; session contributors = {names}"
    )


def test_AC_MSC_2_session_start_payload_carries_active_thread(
    tmp_path: Path,
) -> None:
    """A cold session-start emits additionalContext naming the active
    thread + its pending owner ruling — no in-session state, no
    session-end hook run."""
    _seed_workspace(tmp_path)
    _seed_active_thread(tmp_path)
    text = emit_session_start_context(tmp_path)
    assert text, "session-start emitted empty payload"
    assert ACTIVE_THREAD_MARKER in text, (
        "session-start payload must carry the active-thread marker"
    )
    # The live topic + pending-ruling facts are recoverable.
    assert "v0.11.0" in text or "ProgramBench" in text, (
        "the active-thread digest must name the live topic"
    )
    assert "pending" in text.lower(), (
        "the active-thread digest must surface the pending owner ruling"
    )


def test_AC_MSC_2_no_session_end_hook_referenced_by_path(
    tmp_path: Path,
) -> None:
    """The active-thread module reads only the episode store + the
    named-thread surface; it neither invokes nor requires a Stop /
    SessionEnd hook (§12 halt trigger 1 / plan §10 risk 2).

    Structural assertion on the executable surface (NOT the docstring,
    which legitimately *names* the constraint to explain why none is
    added): no Stop/SessionEnd hook-registration or -builder symbol is
    referenced by any non-comment, non-docstring line. The contributor
    is also invoked with a context dict that carries NO session-end
    signal and still produces the active-thread digest from the
    episode store alone — proving the path does not require a
    session-end hook to have run."""
    src = inspect.getsource(active_thread_mod)
    # Strip comments + the module docstring; what remains is executable
    # code. The constraint is "no session-end hook machinery in the
    # code path", not "the word never appears in prose explaining the
    # constraint".
    code_lines = []
    in_module_doc = False
    for ln in src.splitlines():
        stripped = ln.strip()
        if stripped.startswith('"""') and not in_module_doc:
            in_module_doc = True
            if stripped.count('"""') == 2:
                in_module_doc = False
            continue
        if in_module_doc:
            if stripped.endswith('"""'):
                in_module_doc = False
            continue
        if stripped.startswith("#"):
            continue
        code_lines.append(ln)
    code = "\n".join(code_lines)
    forbidden = (
        "register_stop",
        "build_persona_stop",
        "SessionEnd",
        "on_session_end",
        "TriggerKind.stop",
    )
    hits = [tok for tok in forbidden if tok in code]
    assert hits == [], (
        "active-thread contributor must not introduce any session-end "
        f"hook machinery in its code path (owner constraint); found {hits}"
    )

    # Behavioural proof: the contributor produces the active-thread
    # digest from the episode store with a context dict carrying no
    # session-end signal whatsoever.
    _seed_active_thread(tmp_path)
    slug = tmp_path.name.lower().replace("_", "-")
    store = FileMemoryStore(memory_dir=_memory_dir(tmp_path))
    fn = build_active_thread_contributor(
        store, workspace_root=tmp_path, workspace_slug=slug
    )
    block = fn({})  # no session-end state in the context
    assert ACTIVE_THREAD_MARKER in block, (
        "active thread must be reconstructable with zero session-end "
        "input"
    )


def test_AC_MSC_2_empty_workspace_yields_no_block(tmp_path: Path) -> None:
    """A genuinely-empty workspace (zero episodes, no named-thread
    surface) yields the empty string — no active thread to surface is
    AC-shape-correct, not a failure."""
    _seed_workspace(tmp_path)
    # No episodes seeded; no docs/FUTURE_IDEAS_DRAFT.md.
    store = FileMemoryStore(memory_dir=_memory_dir(tmp_path))
    fn = build_active_thread_contributor(
        store, workspace_root=tmp_path, workspace_slug="ws"
    )
    assert fn({}) == "", (
        "empty workspace must yield an empty active-thread block"
    )


def test_AC_MSC_2_digest_is_bounded(tmp_path: Path) -> None:
    """The active-thread block is bounded (§12 halt trigger 3) — even
    with many large episodes the block stays within its per-contributor
    cap."""
    _seed_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=_memory_dir(tmp_path))
    now = datetime.now(timezone.utc)
    for i in range(30):
        store.write_episode(
            name=f"turn/big-{i}",
            body="X" * 5000,
            source_description="t",
            reference_time=now - timedelta(minutes=i),
            source="t",
            group_id="ws",
        )
    fn = build_active_thread_contributor(
        store, workspace_root=tmp_path, workspace_slug="ws"
    )
    block = fn({})
    assert block, "expected a non-empty block with episodes present"
    assert len(block) <= ACTIVE_THREAD_BLOCK_CAP, (
        f"active-thread block {len(block)} exceeds cap "
        f"{ACTIVE_THREAD_BLOCK_CAP}"
    )

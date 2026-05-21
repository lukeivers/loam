"""AC.FBMT1.ENCC.1 — encoding-context block emits exactly four fields.

The memory-write worker's drain path emits a ``context:`` frontmatter
block containing EXACTLY the four named fields: ``triggering_msg_id``,
``active_task_id``, ``cwd``, ``active_files``. No more, no less.

A fifth field on the written-out file IS a test failure — this
structurally enforces the TG 11805 schema-minimal directive against
accidental schema expansion.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.ENCC family + §16 finding #2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    ENCODING_CONTEXT_FIELDS,
    _split_frontmatter,
    build_file_backed_memory_client,
    memory_dir_for_workspace,
)


def _workspace_with_queue(tmp_path: Path) -> Path:
    """Build a minimal workspace shell so the queue dir resolves."""
    ws_root = tmp_path / "ws"
    (ws_root / "workspace" / ".pos").mkdir(parents=True)
    (ws_root / "workspace" / ".loam" / "memory").mkdir(parents=True)
    return ws_root


def test_AC_FBMT1_ENCC_1_exactly_four_fields(tmp_path: Path):
    """The on-disk frontmatter ``context:`` block carries exactly
    the four named fields — no more, no less."""
    ws_root = _workspace_with_queue(tmp_path)
    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="testturn1",
        session_id="testsess",
        user_message="hello",
        assistant_reply="hi there",
        triggering_msg_id="msg-123",
        active_task_id="task-7",
        cwd="/Users/me/proj",
        active_files=["a.py", "b.py"],
    )
    counters = mww.drain_once(
        workspace_root=ws_root,
        client_factory=build_file_backed_memory_client,
        workspace_slug="testslug",
    )
    assert counters["ok"] == 1, counters
    # Read the written-out file.
    memory_dir = memory_dir_for_workspace(ws_root)
    files = list((memory_dir / "episodes" / "testslug").rglob("*.md"))
    assert len(files) == 1, [str(f) for f in files]
    content = files[0].read_text(encoding="utf-8")
    front, _ = _split_frontmatter(content)
    # ``context`` is a dict.
    assert "context" in front, f"missing context block; front={front!r}"
    ctx = front["context"]
    assert isinstance(ctx, dict), f"context not a dict: {ctx!r}"
    # EXACTLY four keys — same set as ENCODING_CONTEXT_FIELDS.
    assert set(ctx.keys()) == set(ENCODING_CONTEXT_FIELDS), (
        f"context schema drift; "
        f"got {set(ctx.keys())} vs expected {set(ENCODING_CONTEXT_FIELDS)}"
    )
    # Order: rendered in declaration order (verified by re-reading
    # the raw text rather than the dict, since dict iteration is
    # insertion-ordered).
    raw_ctx_block = content.split("context:\n", 1)[1].split("\n---", 1)[0]
    rendered_keys = [
        ln.strip().split(":", 1)[0]
        for ln in raw_ctx_block.splitlines()
        if ln.strip() and ":" in ln
    ]
    assert rendered_keys == list(ENCODING_CONTEXT_FIELDS), (
        f"context fields out of order; got {rendered_keys}"
    )


def test_AC_FBMT1_ENCC_1_no_fifth_field_creeps_in(tmp_path: Path):
    """A queue record carrying speculative extra fields does NOT
    leak them into the on-disk frontmatter — the schema is bounded
    at the writer."""
    ws_root = _workspace_with_queue(tmp_path)
    # Manually craft a queue entry with a speculative 5th field.
    import json
    qdir = mwq.queue_dir(ws_root)
    qdir.mkdir(parents=True, exist_ok=True)
    record = {
        "turn_id": "testturn2",
        "session_id": "testsess",
        "user_message": "u",
        "assistant_reply": "a",
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
        "retry_count": 0,
        "triggering_msg_id": "msg-1",
        "active_task_id": "task-1",
        "cwd": "/p",
        "active_files": ["x.py"],
        # Speculative — not in the schema; must NOT appear on disk.
        "session_id_alt": "should-not-render",
        "parent_task_id": "also-should-not-render",
    }
    entry_path = qdir / "testturn2.json"
    entry_path.write_text(
        json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    counters = mww.drain_once(
        workspace_root=ws_root,
        client_factory=build_file_backed_memory_client,
        workspace_slug="testslug",
    )
    assert counters["ok"] == 1, counters
    memory_dir = memory_dir_for_workspace(ws_root)
    files = list((memory_dir / "episodes" / "testslug").rglob("*.md"))
    assert files
    content = files[0].read_text(encoding="utf-8")
    assert "session_id_alt" not in content, (
        "speculative extra field leaked into frontmatter"
    )
    assert "parent_task_id" not in content, (
        "speculative extra field leaked into frontmatter"
    )

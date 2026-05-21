"""AC.FBMT1.ENCC.2 — fields render null when input is absent.

The four context fields carry values when the worker's input
carries them; carry ``null`` (and the YAML field is still present)
when the input does not. The block schema is always present; only
the values vary.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.ENCC family.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    _split_frontmatter,
    build_file_backed_memory_client,
    memory_dir_for_workspace,
)


def _workspace_with_queue(tmp_path: Path) -> Path:
    ws_root = tmp_path / "ws"
    (ws_root / "workspace" / ".pos").mkdir(parents=True)
    (ws_root / "workspace" / ".loam" / "memory").mkdir(parents=True)
    return ws_root


def test_AC_FBMT1_ENCC_2_all_null_when_no_input(tmp_path: Path):
    """A queue entry without any context fields produces a
    ``context:`` block where every value is ``null`` (active_files
    is ``[]`` which is its null-equivalent for a list field)."""
    ws_root = _workspace_with_queue(tmp_path)
    # enqueue without the context fields — they default to None
    # / empty list per the queue's signature.
    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="testturn1",
        session_id="testsess",
        user_message="hi",
        assistant_reply="hello",
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
    front, _ = _split_frontmatter(content)
    ctx = front.get("context")
    assert ctx is not None
    # All scalar fields are None; active_files is the empty list.
    assert ctx["triggering_msg_id"] is None
    assert ctx["active_task_id"] is None
    assert ctx["cwd"] is None
    assert ctx["active_files"] == []
    # The raw on-disk shape carries ``null`` literals for the
    # scalar nones (not ``None`` Python-repr, not missing keys).
    assert "  triggering_msg_id: null" in content
    assert "  active_task_id: null" in content
    assert "  cwd: null" in content
    assert "  active_files: []" in content


def test_AC_FBMT1_ENCC_2_mixed_input_renders_per_field(tmp_path: Path):
    """A queue entry with SOME context fields set renders set
    values for those fields and ``null`` for the unset ones."""
    ws_root = _workspace_with_queue(tmp_path)
    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="testturn2",
        session_id="testsess",
        user_message="hi",
        assistant_reply="hello",
        triggering_msg_id="msg-99",
        # active_task_id, cwd intentionally absent
        active_files=["only-one.py"],
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
    front, _ = _split_frontmatter(content)
    ctx = front.get("context")
    assert ctx is not None
    assert ctx["triggering_msg_id"] == "msg-99"
    assert ctx["active_task_id"] is None
    assert ctx["cwd"] is None
    assert ctx["active_files"] == ["only-one.py"]

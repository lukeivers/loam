"""AC.FBMT1.ENCC.3 — active_files is a list of relative paths.

The schema rejects non-list inputs; the worker coerces a string
input to a single-element list (builder's call per the AC's "coerces
to a single-element list or surfaces the validation failure"
disjunction).

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.ENCC family.
"""

from __future__ import annotations

import json
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


def test_AC_FBMT1_ENCC_3_list_input_renders_as_list(tmp_path: Path):
    """A list input lands as a bracketed list on disk; the parser
    reads it back as a Python list."""
    ws_root = _workspace_with_queue(tmp_path)
    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="testturn1",
        session_id="testsess",
        user_message="hi",
        assistant_reply="hello",
        active_files=["a.py", "b.py", "c.py"],
    )
    mww.drain_once(
        workspace_root=ws_root,
        client_factory=build_file_backed_memory_client,
        workspace_slug="testslug",
    )
    memory_dir = memory_dir_for_workspace(ws_root)
    files = list((memory_dir / "episodes" / "testslug").rglob("*.md"))
    content = files[0].read_text(encoding="utf-8")
    assert "active_files: [a.py, b.py, c.py]" in content
    front, _ = _split_frontmatter(content)
    assert front["context"]["active_files"] == ["a.py", "b.py", "c.py"]


def test_AC_FBMT1_ENCC_3_string_input_coerced_to_single_element_list(tmp_path: Path):
    """A non-list input (a bare string) is coerced to a single-
    element list rather than raising. The schema-validation
    failure mode the AC names is therefore the coercion path."""
    ws_root = _workspace_with_queue(tmp_path)
    # Manually craft a queue entry with active_files as a string.
    qdir = mwq.queue_dir(ws_root)
    qdir.mkdir(parents=True, exist_ok=True)
    record = {
        "turn_id": "testturn2",
        "session_id": "testsess",
        "user_message": "u",
        "assistant_reply": "a",
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
        "retry_count": 0,
        "triggering_msg_id": None,
        "active_task_id": None,
        "cwd": None,
        # NON-LIST input — a single string.
        "active_files": "single-file-string.py",
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
    content = files[0].read_text(encoding="utf-8")
    # The string was coerced to a single-element list.
    assert "active_files: [single-file-string.py]" in content
    front, _ = _split_frontmatter(content)
    assert front["context"]["active_files"] == ["single-file-string.py"]


def test_AC_FBMT1_ENCC_3_empty_list_renders_as_empty_brackets(tmp_path: Path):
    """An empty list (or no input) renders as ``[]``, not as a
    bare ``null`` — list fields stay typed even when empty."""
    ws_root = _workspace_with_queue(tmp_path)
    mwq.enqueue(
        workspace_root=ws_root,
        turn_id="testturn3",
        session_id="testsess",
        user_message="hi",
        assistant_reply="hello",
        active_files=[],
    )
    mww.drain_once(
        workspace_root=ws_root,
        client_factory=build_file_backed_memory_client,
        workspace_slug="testslug",
    )
    memory_dir = memory_dir_for_workspace(ws_root)
    files = list((memory_dir / "episodes" / "testslug").rglob("*.md"))
    content = files[0].read_text(encoding="utf-8")
    assert "active_files: []" in content

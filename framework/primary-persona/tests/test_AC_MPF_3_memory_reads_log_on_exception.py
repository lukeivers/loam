"""AC.MPF.3 — retrieval exception path appends to memory-reads.log.

Outcome (per locked plan §4 AC.MPF.3): when the contributor's
``search`` boundary raises any exception, the contributor still
returns ``""`` (fail-closed contract from AC-D7.7 preserved) AND
additionally appends one NDJSON line to
``<workspace>/.pos/memory-reads.log`` with exception type, message,
slug, and query preview.

Pre-amendment-#95 the exception path swallowed silently (``return
""``) — leaving operators no way to distinguish "memory boundary
failed" from "no results" or "group_id mismatch" without inspecting
the sidecar logs.

Post-amendment-#95 the exception emits one observable line per the
M6c graceful-fallthrough-with-detection CDC.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona.memory_consumer import (
    MemoryRetrievalConfig,
    build_memory_retrieval_contributor,
)


class _RaisingMemoryClient:
    """Fake MemoryClient whose ``search`` raises a specified exception."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def add_episode(self, **kwargs):  # pragma: no cover — unused
        raise NotImplementedError

    async def search(self, **kwargs):
        raise self._exc


def _build_contributor(
    workspace_root: Path, *, exc: BaseException
) -> tuple[object, Path]:
    config = MemoryRetrievalConfig(
        memory_client=_RaisingMemoryClient(exc),
        workspace_slug="test-slug",
        num_results=5,
    )
    fn = build_memory_retrieval_contributor(
        config, workspace_root=workspace_root
    )
    return fn, workspace_root / ".pos" / "memory-reads.log"


def test_AC_MPF_3_connection_error_logs_one_line(tmp_path: Path) -> None:
    """ConnectionError boundary fails — log appends one NDJSON line
    carrying exception_type=ConnectionError + slug + query preview.
    """
    fn, log_path = _build_contributor(
        tmp_path, exc=ConnectionError("ECONNREFUSED 127.0.0.1:8765")
    )
    out = fn({"prompt": "what is the meaning of life"})
    # Fail-closed contract preserved.
    assert out == ""
    # Diagnostic surfaced.
    assert log_path.exists(), (
        "memory-reads.log should be created on first exception"
    )
    lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["exception_type"] == "ConnectionError"
    assert "ECONNREFUSED" in rec["exception_message"]
    assert rec["workspace_slug"] == "test-slug"
    assert rec["query_preview"] == "what is the meaning of life"
    # ISO-8601-ish timestamp present (don't pin format too tight).
    assert "T" in rec["timestamp"]


def test_AC_MPF_3_log_appends_across_invocations(tmp_path: Path) -> None:
    """Multiple exception-raising invocations append; previous lines
    are preserved.
    """
    fn, log_path = _build_contributor(tmp_path, exc=RuntimeError("boom"))
    fn({"prompt": "first"})
    fn({"prompt": "second"})
    fn({"prompt": "third"})
    lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 3
    previews = [json.loads(ln)["query_preview"] for ln in lines]
    assert previews == ["first", "second", "third"]


def test_AC_MPF_3_query_preview_truncates_to_80_chars(
    tmp_path: Path,
) -> None:
    """Long queries truncate to the first 80 chars — log shape stays
    bounded under heavy-prompt sessions.
    """
    fn, log_path = _build_contributor(tmp_path, exc=ValueError("v"))
    long_q = "x" * 200
    fn({"prompt": long_q})
    rec = json.loads(log_path.read_text().splitlines()[0])
    assert rec["query_preview"] == "x" * 80
    assert len(rec["query_preview"]) == 80


def test_AC_MPF_3_no_workspace_root_skips_log(tmp_path: Path) -> None:
    """When ``workspace_root`` is None (e.g. test fixture without a
    workspace path), the contributor's exception path returns ""
    cleanly and does NOT attempt to write a log file. Backwards-compat
    for pre-amendment-#95 callers.
    """
    config = MemoryRetrievalConfig(
        memory_client=_RaisingMemoryClient(RuntimeError("boom")),
        workspace_slug="test-slug",
        num_results=5,
    )
    # Note: workspace_root not threaded through.
    fn = build_memory_retrieval_contributor(config)
    out = fn({"prompt": "anything"})
    assert out == ""
    # No log file should have been created anywhere we'd find it.
    assert not (tmp_path / ".pos" / "memory-reads.log").exists()


def test_AC_MPF_3_missing_pos_dir_is_created(tmp_path: Path) -> None:
    """When ``<workspace>/.pos/`` doesn't pre-exist, the helper
    creates it. Workspace-bootstrap normally creates it; this is
    defence-in-depth for early-init / test paths.
    """
    # tmp_path has no .pos/ subdirectory.
    assert not (tmp_path / ".pos").exists()
    fn, log_path = _build_contributor(tmp_path, exc=OSError("hmm"))
    fn({"prompt": "test"})
    assert (tmp_path / ".pos").is_dir()
    assert log_path.exists()

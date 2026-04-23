"""Amendment #21 — S3 silent-except bundle — memory-system surface.

Covers Site 6:
  * ``src/observability.py::_read_jsonl`` — a malformed JSONL line was
    previously skipped silently, so ``read_spans`` / ``read_tokens`` /
    ``read_audit`` (and transitively ``per_prompt_cost`` — R12's cost-
    attribution query) under-reported. The fix surfaces each drop via
    ``record_audit(operation="observability.jsonl_line_malformed", ...)``
    while keeping the ``continue`` so robust read is preserved.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import observability
from src.observability import Emitter, reset_default_emitter


@pytest.fixture
def emitter(tmp_path) -> observability.Emitter:
    em = Emitter(sink_dir=tmp_path)
    reset_default_emitter(em)
    return em


def test_read_jsonl_surfaces_malformed_line_in_audit(
    emitter: observability.Emitter,
) -> None:
    # Write a spans.jsonl with two valid records and one malformed
    # line between them.
    spans_file = emitter.sink_dir / "spans.jsonl"
    spans_file.write_text(
        '{"trace_id":"a","span_id":"1","parent_span_id":null,'
        '"name":"x","start_time_unix_nano":0,"end_time_unix_nano":1,'
        '"attributes":{},"status":"OK","error":null}\n'
        '{broken-not-json\n'
        '{"trace_id":"b","span_id":"2","parent_span_id":null,'
        '"name":"y","start_time_unix_nano":2,"end_time_unix_nano":3,'
        '"attributes":{},"status":"OK","error":null}\n',
        encoding="utf-8",
    )

    # Existing-behaviour preservation: two valid records returned; the
    # malformed line does not raise and does not appear.
    rows = emitter.read_spans()
    assert len(rows) == 2
    assert rows[0]["trace_id"] == "a"
    assert rows[1]["trace_id"] == "b"

    # Observable surface: one audit entry for the malformed line.
    audit = emitter.read_audit()
    malformed_entries = [
        e for e in audit
        if e.get("operation") == "observability.jsonl_line_malformed"
    ]
    assert len(malformed_entries) == 1, (
        f"expected one malformed-line audit entry; got {malformed_entries}"
    )
    entry = malformed_entries[0]
    assert entry["actor"] == "memory-system"
    extras = entry.get("extras") or {}
    assert extras["line_no"] == 2
    assert extras["exception_class"] == "JSONDecodeError"
    assert Path(extras["path"]).name == "spans.jsonl"

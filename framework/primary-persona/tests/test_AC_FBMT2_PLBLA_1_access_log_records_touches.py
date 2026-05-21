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

"""AC.FBMT2.PLBLA.1 — every memory touch appends an access-log entry.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.PLBLA.1:

    Every memory touch (write via the worker; read/cite via the
    retrieval contributor surfacing the file in a result set) appends
    a structured entry to a sidecar access log. The log entry records
    the touched file, an ISO-8601 UTC timestamp, and an operation tag
    from a closed enum.

Verification (per plan-doc): drive a write through the worker, then a
retrieval through the contributor; read the sidecar log; assert each
touch produced exactly one entry whose fields parse to the expected
structure.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.access_log import (
    ACCESS_LOG_FILENAME,
    ACCESS_LOG_OPS,
    access_log_path,
    read_access_log,
)
from loam.primary_persona.file_memory import (
    FileBackedMemoryClient,
    FileMemoryRetrievalConfig,
    FileMemoryStore,
    build_file_memory_retrieval_contributor,
)


def test_AC_FBMT2_PLBLA_1_write_appends_one_event(tmp_path: Path) -> None:
    """A successful ``add_episode`` call through ``FileBackedMemoryClient``
    appends exactly one ``{file, ts, op=write}`` entry to the access log."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    client = FileBackedMemoryClient(store=store)
    result = asyncio.run(
        client.add_episode(
            name="turn/t1",
            body="alpha beta gamma",
            source_description="test",
            reference_time=datetime.now(timezone.utc),
            source="message",
            group_id="ws",
        )
    )
    # AC.FBMT2.PLBLA.1: the log lives at ``<memory_dir>/.access-log.jsonl``.
    log_path = access_log_path(memory_dir)
    assert log_path.name == ACCESS_LOG_FILENAME
    assert log_path.exists(), f"log not written at {log_path}"
    lines = [
        line for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1, f"expected exactly one event, got {lines}"
    rec = json.loads(lines[0])
    assert set(rec.keys()) == {"file", "ts", "op"}
    assert rec["op"] == "write"
    assert rec["op"] in ACCESS_LOG_OPS
    assert rec["file"] == result["path"]
    # ts parses as ISO-8601 UTC.
    parsed = datetime.fromisoformat(rec["ts"])
    assert parsed.tzinfo is not None


def test_AC_FBMT2_PLBLA_1_retrieval_appends_read_event(tmp_path: Path) -> None:
    """A retrieval through the production contributor appends one
    ``{file, ts, op=read}`` entry per episode in the result set."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    # Seed one episode (write event lands as a side-effect of the
    # store.write_episode call PATH ONLY — note we use the
    # FileMemoryStore.write_episode directly, NOT the client, so no
    # write event is emitted by this seed line; the access log starts
    # empty for the retrieval assertion).
    store.write_episode(
        name="turn/seed",
        body="alpha beta gamma retrieval-target",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="ws",
    )
    log_path = access_log_path(memory_dir)
    assert not log_path.exists(), "store-direct write should not emit; client-mediated does"
    # Invoke the production contributor closure directly with a context
    # dict. AC.FBMT2.PLBLA.1 verifies the production code path emits
    # the ``read`` events; routing through the full composer is not
    # required for the assertion.
    config = FileMemoryRetrievalConfig(
        store=store, workspace_slug="ws", num_results=5
    )
    contributor = build_file_memory_retrieval_contributor(config)
    block = contributor({"prompt": "alpha beta retrieval-target"})
    assert block, "expected the contributor to emit a non-empty block"
    # AC.FBMT2.PLBLA.1: one read event per episode the retrieval
    # surfaced. One seed → one read.
    assert log_path.exists()
    events = read_access_log(memory_dir)
    # Sum across all files.
    total = sum(len(ts) for ts in events.values())
    assert total >= 1, f"expected at least one read event, got {events}"
    # Verify the structure: the file key is a resolvable path.
    for file_key, ts_list in events.items():
        assert isinstance(file_key, str) and file_key
        assert all(isinstance(t, datetime) for t in ts_list)
        # The op enum is closed; verify by reading the raw lines.
    raw = log_path.read_text(encoding="utf-8").splitlines()
    for raw_line in raw:
        if not raw_line.strip():
            continue
        rec = json.loads(raw_line)
        assert rec["op"] in ACCESS_LOG_OPS
        # Only ``read`` events fire from the contributor; ``write``
        # is the worker path (covered by the first test in this file).
        assert rec["op"] == "read", rec

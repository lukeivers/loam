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

"""AC.FBMT2.COCG.3 — retroactive seed pass is idempotent.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.COCG.3:

    The one-shot retroactive seed pass populates the graph from
    existing memory-write log entries + agent-transcript JSONL files
    at amendment-apply time (Q3-ratified). The seed pass is
    idempotent (running it twice does not double-count).

Verification (per plan-doc): run the seed pass against a synthetic
corpus of existing log + transcript files with known co-occurrences;
assert the resulting graph has the expected edge weights; run the
seed pass a second time against the same corpus; assert the graph is
byte-identical to the first-pass result (idempotency).
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona.access_log import (
    access_log_path,
    read_access_log,
)
from loam.primary_persona.cocitation_graph import (
    build_cocitation_graph,
    seed_from_transcripts,
)


def _write_transcript(
    projects_root: Path, slug: str, session: str, lines: list[dict]
) -> Path:
    """Write a synthetic Claude Code transcript JSONL file."""
    target_dir = projects_root / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{session}.jsonl"
    with target.open("w", encoding="utf-8") as fp:
        for rec in lines:
            fp.write(json.dumps(rec) + "\n")
    return target


def test_AC_FBMT2_COCG_3_seed_populates_access_log(tmp_path: Path) -> None:
    """The seed pass mines transcript files for memory-file references
    and appends synthetic ``read`` events to the access log."""
    memory_dir = tmp_path / "mem"
    memory_dir.mkdir(parents=True)
    projects_root = tmp_path / "projects"
    _write_transcript(
        projects_root,
        slug="ws-main",
        session="2026-05-20T10-00-00",
        lines=[
            {
                "timestamp": "2026-05-20T10:00:00Z",
                "text": "looked at episodes/ws/2026-05-19/turn-x.md",
            },
            {
                "timestamp": "2026-05-20T10:00:10Z",
                "text": "and episodes/ws/2026-05-19/turn-y.md",
            },
        ],
    )
    written = seed_from_transcripts(
        memory_dir=memory_dir, projects_root=projects_root
    )
    assert written >= 2, f"seed must write at least 2 events; got {written}"
    log = read_access_log(memory_dir)
    # The synthetic events reference these two memory files.
    assert "episodes/ws/2026-05-19/turn-x.md" in log
    assert "episodes/ws/2026-05-19/turn-y.md" in log


def test_AC_FBMT2_COCG_3_second_invocation_is_no_op(tmp_path: Path) -> None:
    """Running the seed pass a second time produces zero new events —
    the marker file prevents double-counting. The access log is
    byte-identical to the first pass."""
    memory_dir = tmp_path / "mem"
    memory_dir.mkdir(parents=True)
    projects_root = tmp_path / "projects"
    _write_transcript(
        projects_root,
        slug="ws-main",
        session="2026-05-20T10-00-00",
        lines=[
            {
                "timestamp": "2026-05-20T10:00:00Z",
                "text": "looked at episodes/ws/2026-05-19/turn-x.md",
            },
            {
                "timestamp": "2026-05-20T10:00:10Z",
                "text": "and episodes/ws/2026-05-19/turn-y.md",
            },
        ],
    )

    first_written = seed_from_transcripts(
        memory_dir=memory_dir, projects_root=projects_root
    )
    log_path = access_log_path(memory_dir)
    first_bytes = log_path.read_bytes()

    # AC.FBMT2.COCG.3: second invocation is a no-op.
    second_written = seed_from_transcripts(
        memory_dir=memory_dir, projects_root=projects_root
    )
    assert second_written == 0, (
        f"second seed invocation must be a no-op; "
        f"wrote {second_written} additional events"
    )
    second_bytes = log_path.read_bytes()
    # The access log must be byte-identical.
    assert first_bytes == second_bytes, (
        "access log must be byte-identical after second seed invocation; "
        "the marker file prevents re-running"
    )
    assert first_written > 0  # sanity: first pass actually did something


def test_AC_FBMT2_COCG_3_graph_built_from_seeded_log(tmp_path: Path) -> None:
    """After the seed pass, the access log contains the synthetic
    events, and :func:`build_cocitation_graph` produces the expected
    edges between co-mentioned files. Realistic Claude-Code transcript
    shape: separate JSONL lines per tool-use event (one file
    referenced per record)."""
    memory_dir = tmp_path / "mem"
    memory_dir.mkdir(parents=True)
    projects_root = tmp_path / "projects"
    _write_transcript(
        projects_root,
        slug="ws-main",
        session="s1",
        lines=[
            {
                "timestamp": "2026-05-20T10:00:00Z",
                "tool_use": {"path": "episodes/ws/2026-05-19/turn-x.md"},
            },
            {
                "timestamp": "2026-05-20T10:00:30Z",
                "tool_use": {"path": "episodes/ws/2026-05-19/turn-y.md"},
            },
        ],
    )
    seed_from_transcripts(
        memory_dir=memory_dir, projects_root=projects_root
    )
    log = read_access_log(memory_dir)
    graph = build_cocitation_graph(log)
    # Both files were referenced in transcript lines within the
    # co-occurrence window → co-occur.
    assert "episodes/ws/2026-05-19/turn-x.md" in graph, (
        f"x.md must appear as a graph vertex; log={list(log.keys())}"
    )
    assert (
        "episodes/ws/2026-05-19/turn-y.md"
        in graph["episodes/ws/2026-05-19/turn-x.md"]
    )

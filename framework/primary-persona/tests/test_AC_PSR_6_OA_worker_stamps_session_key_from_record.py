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

"""AC.PSR.6 (outcome-altitude) — a real turn-close write stamps
``session_key`` FROM THE RECORD, never the worker's own env.

Outcome (plan §4 AC.PSR.6, D3): a real enqueue→worker turn-close write
in persona P yields an episode whose frontmatter carries
``session_key=P`` — EVEN when the worker's OWN ``CLAUDE_PERSONA`` is
unset or set to a DIFFERENT value. This is the AC that catches a worker
reading its own env instead of the record.

Outcome-altitude: the write runs through the PRODUCTION enqueue→worker
path against the real file-backed client (no injected store), with the
worker's own env deliberately wrong; the assertion reads the ACTUAL
on-disk ``.md`` frontmatter.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    build_file_backed_memory_client,
    memory_dir_for_workspace,
)


def _config_no_sleep() -> dict:
    return {
        "max_retries": 5,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
    }


def _written_episodes(root: Path) -> list[Path]:
    mem = memory_dir_for_workspace(root)
    return sorted(mem.glob("episodes/**/*.md"))


def test_AC_PSR_6_worker_stamps_session_key_from_record_not_env(
    tmp_path: Path, monkeypatch
) -> None:
    """Enqueue a record carrying session_key=P; drain the REAL file
    worker with its own CLAUDE_PERSONA set to a WRONG value; assert the
    written frontmatter carries session_key=P (from the record)."""
    # The record carries the enqueuing session's identity.
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:t0",
        session_id="s1",
        user_message="what is the kilnbench telemetry status",
        assistant_reply="the kilnbench telemetry run is green",
        session_key="master-control",
    )

    # The worker's OWN env is deliberately wrong — a worker that reads
    # its env instead of the record would stamp WRONG.
    monkeypatch.setenv("CLAUDE_PERSONA", "WRONG-OTHER-PERSONA")

    rc = mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda root: build_file_backed_memory_client(root),
        workspace_slug="pos3",
        sleep_fn=lambda _s: None,
        max_iterations=2,
    )
    assert rc == 0

    episodes = _written_episodes(tmp_path)
    assert len(episodes) == 1, f"expected one episode, got {episodes}"
    front = episodes[0].read_text(encoding="utf-8")
    assert "session_key: master-control" in front, (
        "the written frontmatter must carry the RECORD's session_key "
        f"(master-control), not the worker's env; frontmatter:\n{front}"
    )
    assert "WRONG-OTHER-PERSONA" not in front, (
        "the worker must not read its own CLAUDE_PERSONA env"
    )
    # group_id is untouched (the session dimension is additive).
    assert "group_id: pos3" in front


def test_AC_PSR_6_worker_env_unset_still_stamps_from_record(
    tmp_path: Path, monkeypatch
) -> None:
    """Same, with the worker's own CLAUDE_PERSONA UNSET — the record is
    still the source of truth."""
    monkeypatch.delenv("CLAUDE_PERSONA", raising=False)
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:t1",
        session_id="s1",
        user_message="kilnbench telemetry question two",
        assistant_reply="kilnbench telemetry answer two",
        session_key="loam-dev",
    )
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda root: build_file_backed_memory_client(root),
        workspace_slug="pos3",
        sleep_fn=lambda _s: None,
        max_iterations=2,
    )
    episodes = _written_episodes(tmp_path)
    assert len(episodes) == 1
    front = episodes[0].read_text(encoding="utf-8")
    assert "session_key: loam-dev" in front, front


def test_AC_PSR_6_single_session_write_is_untagged(
    tmp_path: Path, monkeypatch
) -> None:
    """A record with no session_key (single-session / no channel
    identity) writes an UNTAGGED episode — no session_key line (D5
    age-out; the read-side filter is absent-key-inclusive)."""
    monkeypatch.delenv("CLAUDE_PERSONA", raising=False)
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:t2",
        session_id="s1",
        user_message="kilnbench telemetry question three",
        assistant_reply="kilnbench telemetry answer three",
        # session_key omitted -> None on the record.
    )
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda root: build_file_backed_memory_client(root),
        workspace_slug="pos3",
        sleep_fn=lambda _s: None,
        max_iterations=2,
    )
    episodes = _written_episodes(tmp_path)
    assert len(episodes) == 1
    front = episodes[0].read_text(encoding="utf-8")
    assert "session_key:" not in front, (
        "a single-session write must omit the session_key line (untagged)"
    )

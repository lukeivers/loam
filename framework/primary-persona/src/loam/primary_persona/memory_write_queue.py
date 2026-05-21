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

"""Disk-backed memory-write queue (amendment J / D-4 / AC.J.2 / AC.J.3).

Fire-and-forget primitive consumed by the Stop-hook to enqueue
turn-close memory writes; the long-running worker (see
``memory_write_worker``) drains entries from this queue.

Per the locked plan §11 D-4: NDJSON-shaped one-record-per-file
under ``<workspace>/.pos/memory-write-queue/<turn-id>.json``.
Atomic enqueue via tmp-file + ``os.replace``; readers walk by
oldest mtime first (FIFO).

Per ODD §2.5 every code path traces back to AC.J.2 / AC.J.3 /
AC.J.4 / AC.J.7. The retry-counter + dead-letter routing live
in :mod:`memory_write_worker`; this module owns the durable
on-disk queue surface only.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---- public layout ---------------------------------------------------


QUEUE_DIRNAME = ".pos/memory-write-queue"
DEADLETTER_FILENAME = ".pos/memory-write-deadletter.log"
WORKER_CONFIG_FILENAME = ".pos/memory-worker.yaml"
PREWARM_RECOMMEND_FILENAME = ".pos/ollama-prewarm-recommended.txt"
PREWARM_LOG_FILENAME = ".pos/memory-prewarm.log"


def queue_dir(workspace_root: Path | str) -> Path:
    """Return the workspace-local queue directory path.

    AC.J.2: each enqueued turn record lives at
    ``<workspace>/workspace/.pos/memory-write-queue/<turn-id>.json``
    post-D.2 (amendment #63). The legacy constant ``QUEUE_DIRNAME``
    is preserved as ``.pos/memory-write-queue`` for backwards-compat
    with operator scripts that compose it manually; the production
    consumer uses this helper which delegates to the canonical
    workspace_paths helper.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "memory-write-queue"


def deadletter_path(workspace_root: Path | str) -> Path:
    """Return the workspace-local dead-letter log path (AC.J.4).

    D-migration D.2 (amendment #63): now under
    ``<workspace>/workspace/.pos/memory-write-deadletter.log``.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "memory-write-deadletter.log"


# ---- enqueue (AC.J.2 / AC.J.3 / Hard Constraint 7) -------------------


# Per Hard Constraint 7: enqueue is atomic — tmp-file write +
# ``os.replace`` rename. A crash mid-enqueue leaves either nothing or
# the fully-written file; never a partial.

_TURN_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_turn_filename(turn_id: str) -> str:
    """Sanitise a turn id for use as a filename.

    Turn ids are ``<session_id>:<12-hex>`` — the colon is
    filesystem-safe on macOS but not all platforms; sanitise to
    underscore so the filename round-trips across environments.
    Idempotent: running twice yields the same output.
    """
    return _TURN_ID_SAFE_RE.sub("_", turn_id) + ".json"


def enqueue(
    *,
    workspace_root: Path,
    turn_id: str,
    session_id: str,
    user_message: str,
    assistant_reply: str,
    triggering_msg_id: str | None = None,
    active_task_id: str | None = None,
    cwd: str | None = None,
    active_files: list[str] | None = None,
) -> Path:
    """Write a queue entry to disk via atomic tmp+rename.

    AC.J.2: returns in milliseconds — the only blocking work is
    the file write + atomic rename on the local filesystem.

    AC.J.3: durability guarantee — if the function returns, the
    entry is on disk and survives session-end + reboot. Hard
    Constraint 7 makes this structural: tmp-file + ``os.replace``.

    AC.J.7 idempotency: enqueueing the same ``turn_id`` twice
    is harmless — the second ``os.replace`` overwrites the first
    file atomically, and the worker's drain layer carries a
    second-line dedupe (the on-disk filename is keyed on turn_id,
    so a duplicate enqueue yields exactly one queue entry, not
    two).

    The record's ``enqueued_at`` timestamp is the worker's
    FIFO-ordering hint when filesystem mtime granularity is
    coarse (HFS+ stored 1-second resolution; APFS stores ns).

    AC.FBMT1.ENCC.1: the four encoding-context fields
    (``triggering_msg_id``, ``active_task_id``, ``cwd``,
    ``active_files``) are durable per-queue-entry per the TG 11805
    schema-minimal directive. The worker reads these on drain and
    threads them into the writer's frontmatter ``context:`` block.
    All four are optional; missing values map to ``null`` on the
    written-out file (the block schema is always present).
    """
    qdir = queue_dir(workspace_root)
    qdir.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "turn_id": turn_id,
        "session_id": session_id,
        "user_message": user_message,
        "assistant_reply": assistant_reply,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
        "retry_count": 0,
        # AC.FBMT1.ENCC.1 — encoding-context capture at write-time.
        # Stored on the queue entry so the worker (which may run
        # post-session-end) has the values the original turn carried.
        "triggering_msg_id": triggering_msg_id,
        "active_task_id": active_task_id,
        "cwd": cwd,
        "active_files": list(active_files) if active_files else [],
    }
    final = qdir / _safe_turn_filename(turn_id)
    tmp = final.with_suffix(final.suffix + ".tmp")
    payload = json.dumps(record, ensure_ascii=False) + "\n"
    # Write tmp first; flush + fsync the data so the rename is
    # observed-after-write even on a power-loss timeline.
    with tmp.open("w", encoding="utf-8") as fp:
        fp.write(payload)
        fp.flush()
        try:
            os.fsync(fp.fileno())
        except OSError:
            # Best-effort; some filesystems (network mounts) refuse
            # fsync. Atomic rename still gives all-or-nothing.
            pass
    os.replace(tmp, final)
    return final


# ---- drain (AC.J.2 / AC.J.3 / AC.J.4 / AC.J.7) -----------------------


def list_queue_entries_oldest_first(workspace_root: Path) -> list[Path]:
    """Return queue entries sorted oldest-mtime-first (FIFO).

    AC.J.2: drain order matches enqueue order — the worker
    processes turns in the sequence the user produced them.

    Skips ``*.tmp`` files (in-flight enqueues whose
    ``os.replace`` has not yet committed). A ``.tmp`` file
    visible to the walker is a never-completed enqueue;
    ignoring it is safe — the writer either finishes the rename
    (the entry then re-enters the walk), or the writer crashed
    and the tmp will be cleaned by ``cleanup_stale_tmp``.
    """
    qdir = queue_dir(workspace_root)
    if not qdir.exists():
        return []
    entries: list[tuple[float, Path]] = []
    for path in qdir.iterdir():
        if not path.is_file():
            continue
        if path.suffix == ".tmp":
            continue
        if path.suffix != ".json":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        entries.append((mtime, path))
    entries.sort(key=lambda t: (t[0], t[1].name))
    return [p for _, p in entries]


def read_queue_entry(path: Path) -> dict[str, Any] | None:
    """Load a queue entry's NDJSON record.

    Returns ``None`` on unreadable / malformed files; caller
    routes those to dead-letter (AC.J.4) so the queue does not
    block on a corrupted entry.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    text = text.strip()
    if not text:
        return None
    try:
        record = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(record, dict):
        return None
    return record


def delete_entry(path: Path) -> None:
    """Remove a successfully-drained queue entry (AC.J.2)."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def update_retry_count(
    path: Path, *, retry_count: int, last_error: str
) -> None:
    """Bump the retry counter on disk (AC.J.4).

    Atomic via tmp+rename so a crash mid-update leaves the
    pre-update record intact; the worker re-reads on restart.
    """
    record = read_queue_entry(path)
    if record is None:
        return
    record["retry_count"] = retry_count
    record["last_error"] = last_error
    record["last_attempt_at"] = datetime.now(timezone.utc).isoformat()
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(record, ensure_ascii=False) + "\n"
    with tmp.open("w", encoding="utf-8") as fp:
        fp.write(payload)
        fp.flush()
        try:
            os.fsync(fp.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def move_to_deadletter(
    *,
    workspace_root: Path,
    path: Path,
    last_error: str,
    retry_count: int,
) -> None:
    """Append the failed entry to the dead-letter log + delete (AC.J.4).

    The dead-letter log is NDJSON; one line per failed turn record
    carrying turn_id, payload, retry-history, last-error. The file
    is human-readable; the operator can re-queue an entry by moving
    its payload back to the queue directory under the original
    filename.
    """
    record = read_queue_entry(path) or {}
    deadletter_record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "turn_id": record.get("turn_id"),
        "session_id": record.get("session_id"),
        "user_message": record.get("user_message"),
        "assistant_reply": record.get("assistant_reply"),
        "enqueued_at": record.get("enqueued_at"),
        "retry_count": retry_count,
        "last_error": last_error,
    }
    dl_path = deadletter_path(workspace_root)
    dl_path.parent.mkdir(parents=True, exist_ok=True)
    with dl_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(deadletter_record, ensure_ascii=False) + "\n")
    delete_entry(path)


def cleanup_stale_tmp(workspace_root: Path, *, age_seconds: float = 3600.0) -> int:
    """Remove orphaned ``*.tmp`` enqueue artefacts older than ``age_seconds``.

    A tmp file older than the threshold is necessarily abandoned
    (a real enqueue completes its ``os.replace`` in milliseconds).
    The worker calls this periodically to keep the queue dir
    clean. Returns the count removed.
    """
    qdir = queue_dir(workspace_root)
    if not qdir.exists():
        return 0
    now = datetime.now(timezone.utc).timestamp()
    removed = 0
    for path in qdir.iterdir():
        if path.suffix != ".tmp":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if (now - mtime) >= age_seconds:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
    return removed


# ---- worker config (AC.J.4 — workspace-tunable retry policy) --------


DEFAULT_WORKER_CONFIG: dict[str, Any] = {
    "max_retries": 5,
    "backoff_initial_s": 2.0,
    "backoff_max_s": 60.0,
    "poll_interval_s": 1.0,
    "tmp_cleanup_age_s": 3600.0,
    # AC.MFBM-OPS.6 — emit a `worker-heartbeat` NDJSON entry every
    # N drain-loop iterations so an empty queue still produces a
    # liveness signal in memory-writes.log. At the default poll
    # interval (1.0s) this is ~60s wall-clock between heartbeats —
    # enough fidelity to detect a hung worker without flooding the
    # log. Operators can lower the value for diagnostics or raise
    # it (e.g., 600) to quiet the log on cold workspaces.
    "heartbeat_interval_iterations": 60,
}


def load_worker_config(workspace_root: Path) -> dict[str, Any]:
    """Read ``<workspace>/workspace/.pos/memory-worker.yaml`` with
    defaults.

    Per locked D-3: workspace-tunable retry policy. Missing /
    malformed config → defaults silently. The worker NEVER
    crashes on config — it logs at startup and uses defaults.

    D-migration D.2 (amendment #63): config now under
    ``<workspace>/workspace/.pos/`` post-D.2.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    config = dict(DEFAULT_WORKER_CONFIG)
    path = pos_subdir(workspace_root) / "memory-worker.yaml"
    if not path.exists():
        return config
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return config
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return config
    if not isinstance(loaded, dict):
        return config
    for key, default_value in DEFAULT_WORKER_CONFIG.items():
        if key in loaded:
            value = loaded[key]
            if isinstance(value, (int, float)) and value > 0:
                config[key] = type(default_value)(value)
    return config

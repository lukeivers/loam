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

"""Long-running memory-write worker (amendment J / AC.J.5 / AC.J.4 / AC.J.7).

Drains the disk-backed queue at
``<workspace>/.pos/memory-write-queue/`` by driving each entry's
``add_episode`` to completion against the live MCP memory client.

Per the locked plan §11 + Hard Constraint 9: the queue is the
source of truth, the worker is stateless. Killing and restarting
the worker (launchd-mediated; AC.J.5) loses no enqueued entries
and produces no duplicates.

Per locked D-2: single worker per workspace. Per locked D-3:
5 retries with exponential backoff 2s→60s, then dead-letter at
``<workspace>/.pos/memory-write-deadletter.log``.

Per ODD §2.5 every code path traces back to AC.J.2 / AC.J.3 /
AC.J.4 / AC.J.5 / AC.J.7. The retry curve, dead-letter routing,
and per-turn dedupe live here; the durable on-disk surface
lives in :mod:`memory_write_queue`.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import memory_write_queue as mwq


# ---- diagnostic log (AC.J.4 / AC.J.6 — worker observability) --------


def _diag_log_path(workspace_root: Path) -> Path:
    """Workspace-local NDJSON diagnostic log shared with the
    Stop-hook's existing diagnostic surface (#48 D8 / AC.M.10).

    Same path used by ``stop_emitter._diag_log_path`` so the
    operator reads one log to see Stop-hook + worker activity.
    The schema is shared (NDJSON ``kind:`` discriminator); the
    worker adds new ``kind`` values without changing existing
    semantics (#48 backward-compat per Hard Constraint 4).

    D-migration D.2 (amendment #63): now under
    ``<workspace>/workspace/.pos/``.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "memory-writes.log"


def _append_diag(workspace_root: Path, entry: dict[str, Any]) -> None:
    """Append one NDJSON entry; best-effort (matches #48 contract)."""
    try:
        log_path = _diag_log_path(workspace_root)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return


# ---- backoff curve ---------------------------------------------------


def compute_backoff_seconds(
    *,
    retry_count: int,
    initial_s: float,
    max_s: float,
) -> float:
    """Exponential backoff: ``initial_s * 2^(retry_count-1)``, capped
    at ``max_s``.

    AC.J.4: locked D-3 default is 2s→60s curve (2, 4, 8, 16, 32, 60).
    """
    if retry_count <= 0:
        return initial_s
    delay = initial_s * (2 ** (retry_count - 1))
    if delay > max_s:
        return max_s
    return delay


# ---- single-entry drain (AC.J.4 / AC.J.7) ---------------------------


def _build_episode_args(
    *,
    record: dict[str, Any],
    workspace_slug: str,
) -> dict[str, Any]:
    """Construct ``add_episode`` arguments from a queue record.

    Matches the #48 ``cli_memory_write`` body composition shape
    byte-identically so AC.M.6 invariants survive (turn_id-encoded
    name, group_id=workspace_slug, source="message", body carries
    both halves under labelled blocks).
    """
    user_message = str(record.get("user_message", ""))
    assistant_reply = str(record.get("assistant_reply", ""))
    turn_id = str(record.get("turn_id", ""))
    body = (
        "[user]\n"
        f"{user_message}\n"
        "\n"
        "[assistant]\n"
        f"{assistant_reply}\n"
    )
    enqueued_at_iso = record.get("enqueued_at")
    if isinstance(enqueued_at_iso, str):
        try:
            reference_time = datetime.fromisoformat(enqueued_at_iso)
        except ValueError:
            reference_time = datetime.now(timezone.utc)
    else:
        reference_time = datetime.now(timezone.utc)
    return {
        "name": f"turn:{turn_id}",
        "body": body,
        "source_description": "primary-persona Stop-hook turn-close write",
        "reference_time": reference_time,
        "source": "message",
        "group_id": workspace_slug,
    }


async def _call_add_episode(
    *,
    client: Any,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Drive one ``add_episode`` call against the MemoryClient.

    Per plan §13 verify-then-proceed: the worker uses the same
    ``LiveMCPMemoryClient`` per-call session shape as #48 — open
    the session, call the tool, close. No held session across
    drain cycles.
    """
    result = await client.add_episode(**arguments)
    return result if isinstance(result, dict) else {}


def _process_one_entry(
    *,
    workspace_root: Path,
    entry_path: Path,
    config: dict[str, Any],
    client_factory: Callable[[Path], Any | None],
    workspace_slug: str,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> str:
    """Drain a single queue entry to completion, retry, or dead-letter.

    Returns one of:
      - ``"ok"`` — write succeeded, entry deleted.
      - ``"retry"`` — transient failure; retry count bumped on disk.
      - ``"deadletter"`` — terminal failure; entry moved to dead-letter.
      - ``"skipped-no-client"`` — live client unavailable; entry left
        in place for the next worker iteration to retry (substrate
        not ready is not a retry-counter event).
      - ``"corrupt"`` — entry unreadable; moved to dead-letter.

    AC.J.4: bounded retries + dead-letter on terminal failure.
    AC.J.7: turn-id is the on-disk filename (sanitised), so a
    repeated enqueue overwrites in place — no double-write.
    """
    record = mwq.read_queue_entry(entry_path)
    if record is None:
        # Corrupt entry: move to dead-letter so the queue does not
        # block on a malformed file.
        mwq.move_to_deadletter(
            workspace_root=workspace_root,
            path=entry_path,
            last_error="record-unreadable-or-malformed",
            retry_count=0,
        )
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "worker-deadletter",
                "reason": "record-corrupt",
                "path": str(entry_path),
            },
        )
        return "corrupt"

    client = client_factory(workspace_root)
    if client is None:
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "worker-skip",
                "reason": "no-live-client",
                "turn_id": record.get("turn_id"),
            },
        )
        return "skipped-no-client"

    arguments = _build_episode_args(
        record=record, workspace_slug=workspace_slug
    )
    try:
        result = asyncio.run(
            _call_add_episode(client=client, arguments=arguments)
        )
    except Exception as exc:  # noqa: BLE001 — bounded by retry policy
        retry_count = int(record.get("retry_count", 0)) + 1
        max_retries = int(config["max_retries"])
        last_error = f"{type(exc).__name__}: {exc}"
        if retry_count >= max_retries:
            mwq.move_to_deadletter(
                workspace_root=workspace_root,
                path=entry_path,
                last_error=last_error,
                retry_count=retry_count,
            )
            _append_diag(
                workspace_root,
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "worker-deadletter",
                    "reason": "max-retries-exhausted",
                    "turn_id": record.get("turn_id"),
                    "retry_count": retry_count,
                    "last_error": last_error,
                },
            )
            return "deadletter"
        mwq.update_retry_count(
            entry_path,
            retry_count=retry_count,
            last_error=last_error,
        )
        delay = compute_backoff_seconds(
            retry_count=retry_count,
            initial_s=float(config["backoff_initial_s"]),
            max_s=float(config["backoff_max_s"]),
        )
        _append_diag(
            workspace_root,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": "worker-retry",
                "turn_id": record.get("turn_id"),
                "retry_count": retry_count,
                "next_delay_s": delay,
                "last_error": last_error,
            },
        )
        sleep_fn(delay)
        return "retry"

    mwq.delete_entry(entry_path)
    _append_diag(
        workspace_root,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "worker-ok",
            "turn_id": record.get("turn_id"),
            "session_id": record.get("session_id"),
            "episode_uuid": result.get("episode_uuid")
            if isinstance(result, dict) else None,
        },
    )
    return "ok"


# ---- drain loop (AC.J.5 — long-running worker) ----------------------


def drain_once(
    *,
    workspace_root: Path,
    config: dict[str, Any] | None = None,
    client_factory: Callable[[Path], Any | None] | None = None,
    workspace_slug: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, int]:
    """Walk the queue once, processing each entry to terminal state.

    Used by tests to drive deterministic single-pass behaviour and
    by the long-running worker as its inner loop.

    Returns counters keyed by per-entry result (``ok`` / ``retry`` /
    ``deadletter`` / ``skipped-no-client`` / ``corrupt``).
    """
    config = config if config is not None else mwq.load_worker_config(workspace_root)
    if client_factory is None:
        # M-FBM (memory-substrate pivot, 2026-05-01) — AC.MFBM.5: the
        # default substrate is the file-based store; MCP retires from
        # the runtime path. Tests that need MCP semantics pass an
        # explicit ``client_factory=build_live_mcp_memory_client``;
        # M-GMP (post-v0.1.0) reintroduces the MCP factory inside the
        # graphiti plugin.
        from .file_memory import build_file_backed_memory_client  # noqa: WPS433
        client_factory = build_file_backed_memory_client
    if workspace_slug is None:
        from .memory_consumer import resolve_workspace_slug  # noqa: WPS433
        workspace_slug = resolve_workspace_slug(workspace_root)

    counters: dict[str, int] = {
        "ok": 0,
        "retry": 0,
        "deadletter": 0,
        "skipped-no-client": 0,
        "corrupt": 0,
    }
    for entry_path in mwq.list_queue_entries_oldest_first(workspace_root):
        outcome = _process_one_entry(
            workspace_root=workspace_root,
            entry_path=entry_path,
            config=config,
            client_factory=client_factory,
            workspace_slug=workspace_slug,
            sleep_fn=sleep_fn,
        )
        counters[outcome] = counters.get(outcome, 0) + 1
        # If the live client wasn't ready, abort the walk — every
        # subsequent entry would also skip. The launchd
        # ThrottleInterval gives us a natural retry cadence.
        if outcome == "skipped-no-client":
            break
    return counters


# Module-level flag toggled by signal handlers; the long-running
# worker checks it between drain passes so SIGTERM / SIGINT exit
# cleanly without aborting an in-flight ``add_episode`` call.
_should_exit = False


def _install_signal_handlers() -> None:
    """Wire SIGTERM + SIGINT to the cooperative-exit flag.

    AC.J.5 + Hard Constraint 9: launchd may send SIGTERM during a
    KeepAlive bounce or a workspace teardown. The worker exits at
    the next drain-pass boundary; entries mid-flight either complete
    (and get deleted) or get retried on the next worker startup
    (the queue is the source of truth).
    """
    def _handler(signum: int, frame: Any) -> None:  # noqa: ARG001
        global _should_exit  # noqa: PLW0603
        _should_exit = True

    try:
        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)
    except (ValueError, OSError):
        # Some embedded contexts (e.g., a non-main thread) refuse
        # signal-handler installation. The worker is always main-
        # thread under launchd; the guard keeps test injection
        # straightforward.
        pass


def run_worker_loop(
    *,
    workspace_root: Path,
    config: dict[str, Any] | None = None,
    client_factory: Callable[[Path], Any | None] | None = None,
    workspace_slug: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
) -> int:
    """Drive the long-running drain loop.

    AC.J.5: launchd's ``KeepAlive=true`` + ``RunAtLoad=true`` make
    this a supervised process. The function blocks until SIGTERM /
    SIGINT (cooperative exit) or ``max_iterations`` is reached
    (test-only bound).

    Each iteration: drain the queue once, sleep for the configured
    poll interval, repeat. The launchd plist's ``ThrottleInterval``
    bounds restart-on-crash; the worker's poll interval bounds
    drain latency.

    Returns 0 on cooperative exit. Failures inside ``drain_once``
    are absorbed by the per-entry retry/dead-letter logic; a
    raised exception here would crash the worker and trigger
    launchd's KeepAlive restart (the queue survives intact).
    """
    global _should_exit  # noqa: PLW0603
    _should_exit = False
    _install_signal_handlers()

    config = config if config is not None else mwq.load_worker_config(workspace_root)
    poll_interval = float(config.get("poll_interval_s", 1.0))
    tmp_cleanup_age = float(config.get("tmp_cleanup_age_s", 3600.0))
    # AC.MFBM-OPS.6 — heartbeat emission cadence; default 60 iterations.
    # Cast through int to tolerate YAML-loaded floats that survive
    # ``load_worker_config``'s type coercion intact.
    heartbeat_interval_iterations = max(
        1, int(config.get("heartbeat_interval_iterations", 60))
    )

    _append_diag(
        workspace_root,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "worker-start",
            "pid": os.getpid(),
            "config": config,
        },
    )

    iteration = 0
    while not _should_exit:
        if max_iterations is not None and iteration >= max_iterations:
            break
        iteration += 1
        drain_once(
            workspace_root=workspace_root,
            config=config,
            client_factory=client_factory,
            workspace_slug=workspace_slug,
            sleep_fn=sleep_fn,
        )
        # AC.MFBM-OPS.6 — periodic worker-heartbeat emission. An empty
        # queue produces no per-entry log lines; without this, a long-
        # idle worker is indistinguishable from a dead one (the failure
        # mode on 2026-05-01: 5 lines / 3 days of memory-writes.log).
        # Best-effort queue-depth read; a transient OS error here must
        # not bring down the loop.
        if iteration % heartbeat_interval_iterations == 0:
            qdir = mwq.queue_dir(workspace_root)
            if qdir.exists():
                try:
                    queue_depth = sum(1 for _ in qdir.iterdir())
                except OSError:
                    # Transient FS error: report -1 sentinel so an
                    # operator can correlate heartbeat anomalies with
                    # the OS error in the surrounding stderr stream.
                    queue_depth = -1
            else:
                # Empty workspace (queue dir not yet materialised) —
                # depth is structurally 0; the writer creates the
                # dir lazily on first enqueue.
                queue_depth = 0
            _append_diag(
                workspace_root,
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "worker-heartbeat",
                    "pid": os.getpid(),
                    "iteration": iteration,
                    "queue_depth": queue_depth,
                },
            )
        # Periodic stale-tmp cleanup keeps the queue dir tidy.
        if iteration % 60 == 0:
            mwq.cleanup_stale_tmp(
                workspace_root, age_seconds=tmp_cleanup_age
            )
        if _should_exit:
            break
        sleep_fn(poll_interval)

    _append_diag(
        workspace_root,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "worker-exit",
            "pid": os.getpid(),
            "iterations": iteration,
        },
    )
    return 0


# ---- CLI entry point (invoked by launchd) ----------------------------


def cli_memory_worker(
    *,
    workspace_root: Path,
) -> int:
    """CLI entry point for the long-running worker.

    Invoked by the workspace-local launchd service
    ``com.loam.<slug>.memory-write-worker``. The plist's
    ``KeepAlive=true`` means a clean exit triggers a restart;
    the worker is intended to run forever in normal operation.

    Returns 0 on cooperative exit (SIGTERM / SIGINT). Other
    failure modes raise — letting launchd see a crash + restart.
    """
    workspace_root = Path(workspace_root).resolve()
    return run_worker_loop(workspace_root=workspace_root)


if __name__ == "__main__":  # pragma: no cover - launchd entry
    if len(sys.argv) < 2:
        sys.exit(2)
    sys.exit(cli_memory_worker(workspace_root=Path(sys.argv[1])))

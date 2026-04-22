"""State-file machinery for the detached first-run worker.

Added by the 2026-04-22 session-start-detachment amendment.

## Failure class closed by this module

SessionStart hook is the wrong container for multi-minute first-run.
Claude Code's hook ceiling (120s default, but the real killer is the
user's own patience) is shorter than a cold-cache pip install of
graphiti-core + neo4j + kuzu + fastapi. When the hook times out the
Python helper is SIGKILL'd mid-Phase-3, leaves ``~/.pos/`` partially
scaffolded and the venv partially populated, and the next session
hits ``partial-scaffold-detected`` or duplicates the partial install.

## Systemic cause

Synchronous blocking bootstrap inside a hook with tight timeout
semantics. The hook is a notification + handoff surface; it was being
used as the execution surface.

## Structural remedy

Hook becomes a thin status-report-and-handoff. Heavy work detaches to
a separate process in its own session group. Progress surfaces to
``~/.pos/first-run.log`` (a file the user is told about in the hook's
plain-language output). The process's outcome is recorded in
``~/.pos/first-run.state`` (JSON). The next session's hook reads the
state, not the running process.

## Contract

One state file per host: ``~/.pos/first-run.state``. The file is
written atomically via ``.tmp`` sibling + rename, so concurrent
readers always see a valid snapshot. The state machine transitions
monotonically forward: ``absent`` -> ``starting`` -> ``running`` ->
``completed`` (happy path) or ``failed`` (any halt). ``completed`` and
``failed`` are terminal. A ``starting`` that never advances past the first write is
treated as ``failed`` by the hook side after the grace window expires.

Stdlib only. No third-party deps.
"""

from __future__ import annotations

import json
import os
import signal
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# Canonical file locations. ``~/.pos/`` is the per-host config dir;
# tests override via ``pos_root`` parameters rather than env vars so
# the production paths are not mockable at runtime.
DEFAULT_POS_ROOT = Path.home() / ".pos"


STATE_FILE = "first-run.state"
LOG_FILE = "first-run.log"


# Terminal states.
TERMINAL_STATES = frozenset({"completed", "failed"})

# Non-terminal states the hook may still see a live process for.
LIVE_STATES = frozenset({"starting", "running"})


@dataclass
class FirstRunState:
    """Snapshot of the detached worker's progress.

    ``status`` is one of: ``starting`` (worker just spawned, no phase
    has started), ``running`` (worker made at least one phase write),
    ``completed`` (worker finished all phases), ``failed`` (worker hit
    a halt or was observed dead by the hook).

    ``pid`` is the OS process id of the worker at spawn time. The hook
    uses it to detect silent death (worker process gone but state
    still says ``running`` — a crash Claude Code may not have logged).

    ``started_at`` / ``updated_at`` are UTC Unix timestamps (floats).

    ``phase`` is a short label identifying the current work ("phase-3b-shared-deps"
    etc). It is what the user sees in the hook's additionalContext line.

    ``detail`` is free-form plain-language detail (one line). Optional.

    ``error_code`` is populated only when status=failed; it matches
    the first_run_helper error codes (-32091..-32099).

    ``remediation`` is populated only when status=failed; it is the
    plain-language text the hook surfaces to the user.
    """

    status: str = "starting"
    pid: int = 0
    started_at: float = 0.0
    updated_at: float = 0.0
    phase: str = ""
    detail: str = ""
    error_code: int = 0
    remediation: str = ""
    # Spawn generation counter — incremented each time the hook decides
    # to respawn the worker (e.g. after a silent death on a previous
    # session). Lets the log file distinguish between runs without
    # rotating on every hook fire.
    generation: int = 1

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True) + "\n"


def state_path(pos_root: Path = DEFAULT_POS_ROOT) -> Path:
    return Path(pos_root).expanduser() / STATE_FILE


def log_path(pos_root: Path = DEFAULT_POS_ROOT) -> Path:
    return Path(pos_root).expanduser() / LOG_FILE


def read_state(pos_root: Path = DEFAULT_POS_ROOT) -> FirstRunState | None:
    """Read and parse the state file. Returns None if absent/corrupt."""
    p = state_path(pos_root)
    if not p.exists():
        return None
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    # Accept only the fields we know about; extras are dropped.
    known = {f: data.get(f) for f in FirstRunState.__dataclass_fields__}
    try:
        state = FirstRunState()
        for k, v in known.items():
            if v is None:
                continue
            setattr(state, k, v)
        return state
    except (TypeError, ValueError):
        return None


def write_state(
    state: FirstRunState,
    pos_root: Path = DEFAULT_POS_ROOT,
) -> None:
    """Atomically persist ``state`` to the state file.

    Writes to a ``.tmp`` sibling then ``rename()`` — POSIX rename is
    atomic within a filesystem, so concurrent readers always see a
    complete snapshot (not a half-written file).
    """
    p = state_path(pos_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state.updated_at = time.time()
    if state.started_at == 0.0:
        state.started_at = state.updated_at
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(state.to_json(), encoding="utf-8")
    os.replace(tmp, p)


def append_log(
    message: str,
    pos_root: Path = DEFAULT_POS_ROOT,
    *,
    generation: int = 1,
) -> None:
    """Append a timestamped line to ``~/.pos/first-run.log``.

    The log is the user's live progress surface — the hook tells them
    to tail it while first-run runs. ``generation`` is embedded in the
    line so the user (or a future diagnostic) can tell one spawn's
    output apart from another after a respawn.
    """
    p = log_path(pos_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] [gen{generation}] {message}\n"
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line)


def process_alive(pid: int) -> bool:
    """Best-effort liveness check for the detached worker.

    ``os.kill(pid, 0)`` raises ``ProcessLookupError`` if the process
    does not exist, ``PermissionError`` if it does but we don't own
    it (still counts as alive for our purposes). Returns False for
    pid==0 (pre-spawn placeholder).
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it — treat as alive.
        return True
    except OSError:
        return False
    return True


def is_stale_live_state(
    state: FirstRunState,
    *,
    stale_after_s: float = 180.0,
) -> bool:
    """Detect a "live" state whose process is gone (silent death).

    The hook uses this to decide whether to respawn. A state in
    ``starting`` or ``running`` whose pid is not alive is stale — the
    worker was SIGKILL'd (hook timeout, OOM, user ctrl-C) before it
    could write a terminal state. ``stale_after_s`` adds a grace
    window so a genuinely-alive worker mid-phase is not mis-diagnosed
    as dead on a slow system.
    """
    if state.status not in LIVE_STATES:
        return False
    if process_alive(state.pid):
        return False
    # Process gone, but we still give the state one grace window in
    # case the pid was recycled or the kernel is slow. The updated_at
    # clock gives us a second signal.
    age = time.time() - state.updated_at
    return age >= stale_after_s


def mark_failed_silently(
    state: FirstRunState,
    pos_root: Path = DEFAULT_POS_ROOT,
) -> FirstRunState:
    """Flip a stale live state to failed and persist.

    Called by the hook when it detects ``is_stale_live_state(state)``.
    The failure mode is named ``worker-died-silently`` so it surfaces
    differently in diagnostics from a worker-reported failure.
    """
    state.status = "failed"
    state.error_code = -32099
    state.detail = (
        f"worker-died-silently: pid {state.pid} no longer running, "
        f"state was {state.status!r}"
    )
    state.remediation = (
        "first-run worker exited without writing a terminal state. "
        "The next claude session will automatically retry. "
        "If this repeats, check ~/.pos/first-run.log for the last "
        "recorded phase."
    )
    write_state(state, pos_root)
    return state

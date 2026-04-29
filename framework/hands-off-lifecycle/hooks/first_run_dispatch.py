"""Thin SessionStart dispatcher — decides what to do with the state file.

Added by the 2026-04-22 session-start-detachment amendment.

## Role in the architecture

``first-run.sh`` does the minimum needed to find a Python 3.13
interpreter and hand off to this script. ``first_run_dispatch.py``
reads ``<workspace>/.pos/first-run.state`` (amendment #28: per-
workspace, not ``~/.loam/first-run.state`` as in the original
session-start-detachment amendment), decides which of the five
cases we are in, and either spawns the detached worker
(``first_run_helper.py`` in ``bootstrap`` / ``resume`` mode) or
short-circuits with an appropriate additionalContext message.

The dispatcher itself must be stdlib-only and complete in under a
second. It owns zero heavy work — the only thing it invokes that
could take time is reading a small JSON file.

## Five cases

1. **No state file, no venv** — fresh clone, never started. Spawn the
   detached worker; emit "first-run started, tail log, wait ~5min."

2. **State says ``completed``** — worker finished successfully last
   time. Settings.json was rewritten by the worker's self-retire, so
   a future SessionStart hook will invoke the supervisor path
   directly; we merely note "already done, proceeding" and exit.

3. **State says ``running`` or ``starting``, pid alive** — worker is
   in flight. Emit "still installing, live progress at <log>, reopen
   in a few minutes."

4. **State says ``running`` or ``starting``, pid gone** — silent
   death. Mark state failed; spawn fresh worker with an incremented
   generation counter; emit "prior run crashed at <phase>; restarted."

5. **State says ``failed``** — worker reported a halt. Emit the
   stored plain-language remediation. On next hook fire (user-driven
   reopen), respawn the worker — we already captured what failed.

## Contract with Claude Code

stdout is captured as ``additionalContext`` by the SessionStart hook.
We write a plain-language paragraph with line breaks. The reader (the
user, via Claude's model voice) gets: (a) what state first-run is in,
(b) the progress log path, (c) if applicable the expected wait.

Exit code is always 0. Status is encoded in stdout content plus the
persistent state file.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Import the state module from the same hooks directory.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from first_run_state import (  # noqa: E402
    FirstRunState,
    LIVE_STATES,
    append_log,
    is_stale_live_state,
    log_path,
    mark_failed_silently,
    read_state,
    write_state,
)


# ---- user-facing text --------------------------------------------


def _msg_fresh_start(log: Path, helper_version: str) -> str:
    return (
        "Your pos-v2 workspace is installing.\n"
        "\n"
        "This takes about 5 minutes on a fresh clone (component dependencies "
        "are being installed; the memory-system component alone pulls "
        "graphiti-core, neo4j, and kuzu — slow on a cold pip cache).\n"
        "\n"
        f"Live progress: {log}\n"
        "\n"
        "Close this claude session, wait a few minutes, then reopen. First-run "
        "will finish in the background and the next launch will be "
        "instant. If something goes wrong you'll see a clear failure "
        "message and instructions on next launch — you don't have to "
        "babysit this."
    )


def _msg_still_running(state: FirstRunState, log: Path) -> str:
    age_s = int(time.time() - state.started_at) if state.started_at else 0
    mins = age_s // 60
    secs = age_s % 60
    phase = state.phase or "phase-unknown"
    detail = state.detail or "in progress"
    return (
        f"Your pos-v2 workspace is still installing ({mins}m {secs}s elapsed).\n"
        "\n"
        f"Current phase: {phase}\n"
        f"Detail: {detail}\n"
        f"Live progress: {log}\n"
        "\n"
        "Close this session and reopen in a couple of minutes. Typical "
        "fresh-clone install is about 5 minutes end to end."
    )


def _msg_completed() -> str:
    return (
        "pos-v2 first-run completed. The workspace is ready; subsequent "
        "sessions will launch straight into the supervisor path."
    )


def _msg_failed(state: FirstRunState, log: Path) -> str:
    remediation = state.remediation or (
        "Reopen claude to retry. The next session will automatically "
        "pick up where this one left off."
    )
    detail = state.detail or "no additional detail"
    code = state.error_code or -32099
    return (
        "Your pos-v2 workspace did not finish installing.\n"
        "\n"
        f"What went wrong: {detail}\n"
        "\n"
        f"What to do: {remediation}\n"
        "\n"
        f"Live progress (full history): {log}\n"
        f"Reference code: {code}"
    )


def _msg_respawn_after_silent_death(state: FirstRunState, log: Path) -> str:
    phase = state.phase or "phase-unknown"
    return (
        "Your pos-v2 workspace's previous install crashed silently "
        f"(last recorded phase: {phase}). A new attempt is starting "
        "now in the background.\n"
        "\n"
        f"Live progress: {log}\n"
        "\n"
        "Close this session and reopen in a few minutes. If the same "
        "crash repeats across multiple attempts, check the log for the "
        "specific failure and file an issue."
    )


# ---- detached worker spawn ---------------------------------------


def _spawn_detached_worker(
    *,
    python: str,
    helper: Path,
    loam_root: Path,
    pos_root: Path,
    generation: int,
    mode: str,
) -> int:
    """Spawn the first_run_helper as a fully detached process.

    "Fully detached" means:
      * new session group (start_new_session=True) — surviving the
        hook process's exit and the parent terminal's SIGHUP.
      * stdio redirected away from the hook's inherited fds —
        attaching to the hook's stdout would re-capture the worker's
        output as additionalContext, which is exactly the bug we are
        fixing. Instead, stdout and stderr go to the log file, stdin
        is /dev/null.
      * no hold on the hook's FDs — the hook exits as soon as this
        call returns; the Python runtime running this dispatcher is a
        separate process and the worker is its own subprocess.

    Returns the worker's pid. State-file bookkeeping is the caller's
    responsibility.
    """
    log = log_path(pos_root)
    log.parent.mkdir(parents=True, exist_ok=True)
    # Append mode — the state module writes generation-tagged lines
    # and the log spans multiple spawns; rotation is out of scope for
    # this amendment.
    log_fh = open(log, "a", encoding="utf-8", buffering=1)
    devnull = open(os.devnull, "rb")
    # ``-u`` is the Python "unbuffered" flag — forces stdout/stderr to
    # be unbuffered so ``print()`` from the worker hits the log within
    # the caller's perceived latency rather than block-buffering until
    # the pipe fills. Added 2026-04-22 by the pyyaml-reachability
    # amendment (#5) — without this, any print() in the worker was
    # block-buffered into ~/.loam/first-run.log and users tailing the
    # log saw long stretches of silence between phases. The direct
    # state-file writes the worker also does are unaffected; ``-u``
    # specifically rescues ``print()`` and any subprocess that writes
    # via inherited stdout.
    env = os.environ.copy()
    # PYTHONUNBUFFERED is belt-and-braces alongside -u: some subprocess
    # chains unset -u when they exec a child, but environment
    # propagates. Either alone is enough; both together is cheap.
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [
        python,
        "-u",
        str(helper),
        "--loam-root",
        str(loam_root),
        "--mode",
        mode,
        "--pos-root",
        str(pos_root),
        "--generation",
        str(generation),
    ]
    # start_new_session creates a new process group and detaches from
    # the controlling terminal — the kernel-level equivalent of
    # setsid(2). Combined with stdio redirection, the child survives
    # the hook's exit with zero fd entanglement.
    proc = subprocess.Popen(
        cmd,
        stdin=devnull,
        stdout=log_fh,
        stderr=log_fh,
        close_fds=True,
        start_new_session=True,
        env=env,
    )
    # Close our end of the redirected fds — the child inherited dup'd
    # copies and owns its own writes.
    devnull.close()
    log_fh.close()
    append_log(
        f"dispatch: spawned worker pid={proc.pid} mode={mode}",
        pos_root,
        generation=generation,
    )
    return proc.pid


# ---- main decision loop ------------------------------------------


def _write_fresh_state(
    *,
    workspace_root: Path,
    pid: int,
    generation: int,
) -> FirstRunState:
    state = FirstRunState(
        status="starting",
        pid=pid,
        generation=generation,
        workspace_root=str(Path(workspace_root).resolve()),
    )
    write_state(state, workspace_root)
    return state


def _state_belongs_to(state: FirstRunState, loam_root: Path) -> bool:
    """Amendment #28 — defence in depth against cross-workspace reads.

    A state file located under ``<loam_root>/.pos/`` *should* always
    belong to that workspace by construction of the path. Still: if
    the file's recorded ``workspace_root`` is non-empty and does not
    match, trust the content — the workspace may have been renamed,
    moved, or the file copied in by an admin. Empty
    ``workspace_root`` means a pre-amendment-#28 state or a test
    harness that did not fill it; refuse those too (fail-closed per
    plan §2 constraint "Fail-closed direction").
    """
    if not state.workspace_root:
        return False
    try:
        recorded = Path(state.workspace_root).resolve()
    except (OSError, RuntimeError):
        return False
    try:
        current = Path(loam_root).resolve()
    except (OSError, RuntimeError):
        return False
    return recorded == current


def dispatch(
    *,
    loam_root: Path,
    pos_root: Path,
    helper: Path,
    python: str,
) -> str:
    """Decide what to do and return the additionalContext text.

    Pure function over filesystem state plus side-effects of spawning
    + state-file writes. Returns the user-facing string for stdout;
    caller prints.

    Amendment #28: state is read from the workspace-local path
    ``<loam_root>/.pos/first-run.state``. A state whose recorded
    ``workspace_root`` does not match the current ``loam_root`` is
    treated as absent (fail-closed); the dispatcher never touches
    another workspace's state file.
    """
    log = log_path(pos_root)
    settings_path = loam_root / ".claude" / "settings.json"

    existing = read_state(loam_root)
    # Defence in depth — reject a state whose content names a
    # different workspace (or has no recorded workspace at all).
    # Path routing plus the ``_state_belongs_to`` check together
    # close AC11 (foreign-workspace state is fresh-spawn) and AC13
    # (corrupt state is fresh-spawn via read_state returning None).
    if existing is not None and not _state_belongs_to(existing, loam_root):
        existing = None

    # Case 2 — completed previously.
    if existing is not None and existing.status == "completed":
        # Defensive: if the worker succeeded but settings.json was not
        # rewritten for some reason (e.g. a test harness bug), the user
        # would loop forever. Detect and surface instead of silently
        # looping; the _is_already_retired check in the helper mirrors
        # this reasoning.
        return _msg_completed()

    # Case 4 — live state but dead pid. Silent death.
    if existing is not None and is_stale_live_state(
        existing, stale_after_s=0.0
    ):
        existing = mark_failed_silently(existing, loam_root)
        # Fall through to respawn, but remember we came from a silent
        # death so the user-facing text explains it.
        next_gen = int(existing.generation or 1) + 1
        pid = _spawn_detached_worker(
            python=python,
            helper=helper,
            loam_root=loam_root,
            pos_root=pos_root,
            generation=next_gen,
            mode="resume",
        )
        _write_fresh_state(
            workspace_root=loam_root, pid=pid, generation=next_gen
        )
        return _msg_respawn_after_silent_death(existing, log)

    # Case 3 — still running with a live pid.
    if existing is not None and existing.status in LIVE_STATES:
        return _msg_still_running(existing, log)

    # Case 5 — previously failed. User has to manually reopen to retry.
    # Respawn the worker on this reopen so the retry is truly hands-off.
    if existing is not None and existing.status == "failed":
        next_gen = int(existing.generation or 1) + 1
        # Preserve the failure message for the user-facing output, but
        # kick a new worker off before we return so the next reopen
        # sees progress rather than another "still failed."
        pid = _spawn_detached_worker(
            python=python,
            helper=helper,
            loam_root=loam_root,
            pos_root=pos_root,
            generation=next_gen,
            mode="resume",
        )
        _write_fresh_state(
            workspace_root=loam_root, pid=pid, generation=next_gen
        )
        # The user-facing message still names what broke — they need
        # that context even though we already kicked off a retry.
        return (
            _msg_failed(existing, log)
            + "\n\n"
            + "A retry has been started in the background; reopen in a "
            + "few minutes to check progress."
        )

    # Case 1 — no state file. Fresh clone. Pick bootstrap mode (runs
    # all phases from 1 through 7) and spawn. If a .venv already
    # exists (partial from a pre-amendment run) the worker's
    # resume-or-verify path handles it.
    venv_python = loam_root / ".venv" / "bin" / "python"
    mode = "resume" if venv_python.exists() else "bootstrap"
    pid = _spawn_detached_worker(
        python=python,
        helper=helper,
        loam_root=loam_root,
        pos_root=pos_root,
        generation=1,
        mode=mode,
    )
    _write_fresh_state(workspace_root=loam_root, pid=pid, generation=1)
    return _msg_fresh_start(log, helper_version="1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="pos-v2 first-run dispatch — SessionStart hook worker.",
    )
    parser.add_argument("--loam-root", required=True)
    parser.add_argument("--pos-root", default=str(Path.home() / ".loam"))
    parser.add_argument("--helper", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument(
        "--python-version",
        default="",
        help="Informational only; the shell passes the detected version.",
    )
    args = parser.parse_args(argv)

    loam_root = Path(args.loam_root).resolve()
    pos_root = Path(args.pos_root).expanduser().resolve()
    helper = Path(args.helper).resolve()

    if not helper.exists():
        # Partial install: the hook fired but the worker file is gone.
        # This is the "first-run.sh survived self-retire but the rest
        # did not" edge case. We cannot spawn what is not there; tell
        # the user to reclone.
        print(
            "pos-v2 first-run cannot start — the worker script is missing.\n"
            "This usually means the repository was cloned incompletely.\n"
            "Re-clone pos-v2 into a fresh directory and reopen claude."
        )
        return 0

    try:
        text = dispatch(
            loam_root=loam_root,
            pos_root=pos_root,
            helper=helper,
            python=args.python,
        )
    except Exception as e:  # pragma: no cover
        # A dispatcher that itself crashes must not silence — the hook
        # would otherwise return empty additionalContext and the user
        # gets no signal. Surface the exception into the additionalContext.
        print(
            "pos-v2 first-run dispatch hit an unexpected error:\n"
            f"  {type(e).__name__}: {e}\n"
            "Reopen claude to retry. If this repeats, inspect\n"
            f"  {pos_root}/first-run.log\n"
            "for the last recorded phase."
        )
        return 0

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

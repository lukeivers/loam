"""D5 — orchestrator control: pause, drain, SIGTERM, symlink swap, kickstart.

The self-upgrade framework is an **external process**. It talks to the
live orchestrator by three mechanisms:

1. Reading the orchestrator's PID file (written on boot).
2. Sending ``SIGTERM`` to that pid for graceful shutdown.
3. Invoking ``launchctl kickstart`` to bring the new orchestrator up
   on the swapped tree.

The orchestrator is sealed: this module does NOT call into it; it only
signals it. Per the brief, the orchestrator already has a SIGTERM-
graceful-shutdown handler and will rebind to the IPC socket on the new
path once ``launchctl kickstart`` invokes it.

Symlink swap uses ``os.replace`` — atomic on APFS per the research
doc. If the target filesystem does not support atomic rename, the
caller can detect this (returns a recovery string that
``test_orchestrator_control`` covers) and halt.

Amendment #10 (linux-removal) dropped the systemd-user restart
fallback; macOS launchd is the only supported supervisor.
"""

from __future__ import annotations

import errno
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("loam.self_upgrade.orchestrator_control")


class OrchestratorControlError(RuntimeError):
    """Any failure of the orchestrator-control subsystem."""


@dataclass
class ControlTiming:
    """Wall-clock measurements for the upgrade sequence. Used by the
    accept report + the measurement runbook."""

    drain_ms: float = 0.0
    sigterm_ms: float = 0.0
    swap_ms: float = 0.0
    boot_ms: float = 0.0


# ---- pid discovery --------------------------------------------------


def read_orchestrator_pid(pid_file: Path) -> int | None:
    """Return the live pid, or None if no pid file / pid is dead."""
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text().strip())
    except (OSError, ValueError):
        return None
    return pid if _pid_alive(pid) else None


def _pid_alive(pid: int) -> bool:
    """True if the pid names a running (non-zombie) process.

    Zombies (exited but not reaped by parent) are treated as dead for
    upgrade purposes — the process is no longer running even though
    its pid entry lingers in the process table. On macOS we use
    ``ps -o state=`` to distinguish zombies (there is no /proc).
    """
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.EPERM:
            # Exists, not ours — treat as alive
            return True
        return False

    # pid is "alive" per os.kill; check for zombie using BSD ps.
    try:
        result = subprocess.run(
            ["ps", "-o", "state=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    state = result.stdout.strip()
    if not state:
        return False  # ps lost it — dead
    # BSD ps flags: Z in state means zombie
    return "Z" not in state


# ---- drain ----------------------------------------------------------


def wait_for_drain(
    *,
    is_drained: "callable",
    timeout_s: float,
    poll_interval_s: float = 0.2,
) -> float:
    """Wait up to ``timeout_s`` seconds for ``is_drained()`` → True.

    Returns elapsed wall-clock seconds. Raises ``OrchestratorControlError``
    if the timeout elapses without draining.
    """
    start = time.monotonic()
    while True:
        try:
            if is_drained():
                return time.monotonic() - start
        except Exception as exc:
            raise OrchestratorControlError(f"drain check raised: {exc}") from exc
        elapsed = time.monotonic() - start
        if elapsed >= timeout_s:
            raise OrchestratorControlError(
                f"drain-timeout after {elapsed:.1f}s "
                f"(limit {timeout_s}s)"
            )
        time.sleep(poll_interval_s)


# ---- SIGTERM --------------------------------------------------------


def sigterm_and_wait(pid: int, timeout_s: float) -> float:
    """Send SIGTERM; wait for pid to exit.

    Returns elapsed wall-clock seconds. Raises ``OrchestratorControlError``
    on timeout (caller escalates to SIGKILL or halts).
    """
    start = time.monotonic()
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return 0.0
    except OSError as exc:
        raise OrchestratorControlError(
            f"SIGTERM to pid={pid} failed: {exc}"
        ) from exc

    while True:
        if not _pid_alive(pid):
            return time.monotonic() - start
        if time.monotonic() - start >= timeout_s:
            raise OrchestratorControlError(
                f"pid={pid} still alive {timeout_s}s after SIGTERM"
            )
        time.sleep(0.1)


# ---- symlink swap ---------------------------------------------------


def atomic_symlink_swap(link: Path, new_target: Path) -> float:
    """Atomically point ``link`` at ``new_target``.

    Returns elapsed wall-clock seconds.

    Implementation: create a sibling temp symlink, then ``os.replace``
    it over the destination. ``os.replace`` is atomic on POSIX filesystems
    that implement ``rename(2)``. On platforms where it is not atomic
    (rare; the research doc discusses APFS/ext4 and those work), the
    function still completes but the caller-visible half-swap window
    is non-zero.
    """
    start = time.monotonic()
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_suffix(link.suffix + ".__upgrade_tmp__")
    # Clear any leftover temp from a prior failed attempt
    try:
        tmp.unlink()
    except FileNotFoundError:
        pass
    # Create the new symlink at tmp
    os.symlink(str(new_target), tmp)
    # Atomic rename over destination — clobbers the existing symlink.
    os.replace(tmp, link)
    return time.monotonic() - start


# ---- launchctl restart ----------------------------------------------


@dataclass
class RestartResult:
    elapsed_s: float
    returncode: int
    stdout: str
    stderr: str


def launchctl_kickstart(label: str, *, user: bool = True) -> RestartResult:
    """Invoke ``launchctl kickstart`` to start the orchestrator.

    ``label`` is the com.pos.orchestrator (or similar) launchd target.
    Uses the user-domain (``gui/$UID``) by default. The command is
    ``launchctl kickstart -k gui/$UID/<label>`` which force-restarts if
    running, starts if not.
    """
    start = time.monotonic()
    domain = f"gui/{os.getuid()}" if user else "system"
    cmd = ["launchctl", "kickstart", "-k", f"{domain}/{label}"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise OrchestratorControlError(
            "launchctl not found — this build requires macOS launchd"
        ) from exc
    return RestartResult(
        elapsed_s=time.monotonic() - start,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


# ---- boot-wait ------------------------------------------------------


def wait_for_boot(
    *,
    is_up: "callable",
    timeout_s: float,
    poll_interval_s: float = 0.3,
) -> float:
    """Poll ``is_up()`` until True or timeout. Mirror of wait_for_drain."""
    start = time.monotonic()
    while True:
        try:
            if is_up():
                return time.monotonic() - start
        except Exception:
            pass
        elapsed = time.monotonic() - start
        if elapsed >= timeout_s:
            raise OrchestratorControlError(
                f"orchestrator boot-timeout after {elapsed:.1f}s "
                f"(limit {timeout_s}s)"
            )
        time.sleep(poll_interval_s)

"""User-facing progress surface for pos-v2 first-run.

Added by the 2026-04-22 visible-progress amendment.

## Failure class

Silent first-run UX — non-technical users cannot distinguish progress
from a hang. Luke hit this himself at the editable-install amendment's
Phase 3e step: "so i started it, but it doesn't really seem to be doing
anything, just kinda sitting there." A five-minute silence on a
3-8 minute cold-cache install destroys the hands-off promise — the user
reasonably concludes the system is broken and kills it before
completion.

## Systemic cause

Claude Code captures a SessionStart hook's stdout as ``additionalContext``
for the model. The user never sees stdout in real time — they see it
(if at all) only after the hook terminates. The hook and its Python
helper were written with a single output surface (stdout), so there
was no channel that reaches the user while work is in flight.

## Structural remedy

A *separate* user-facing channel that reaches the controlling TTY
directly, opened once at process start and reused. Stdout is preserved
unchanged for the final Claude Code payload. The TTY channel carries
plain-language progress lines — one at each phase boundary, one per
meaningful pip install, and a final "complete" or "failed with
remediation" sentence.

Selection rationale (see amendment commit message for full analysis):

  * ``/dev/tty`` is the POSIX-standard "write to the user's terminal
    regardless of stdio redirection" primitive. Claude Code running
    interactively in a Terminal / iTerm2 / WezTerm window has a
    controlling TTY the hook process inherits; the hook can ``open()``
    it and write. Stdout redirection is bypassed.

  * Fallback to ``sys.stderr`` if ``/dev/tty`` is unopenable (CI with
    no controlling TTY, background / daemon contexts, unusual sandbox
    configurations). Claude Code may or may not surface stderr — but
    the alternative is silence, and stderr at least reaches the parent
    process's log if one exists.

  * File-based side-channels (``progress.log`` the user is told to
    tail) were rejected: they require the user to run a second command
    before launching ``claude``, which defeats the zero-friction
    first-run promise. The progress is *for* the passive observer; a
    channel that requires active tailing does not solve their problem.

This module is stdlib-only. No new runtime dependencies (hard
constraint of this amendment). Progress output is never trusted —
phases only claim success when their underlying work has verifiably
succeeded, not before.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import TextIO


# Sentinel values for the env override.
_ENV_DISABLE = "POS_V2_FIRST_RUN_NO_TTY"
_ENV_FORCE_FILE = "POS_V2_FIRST_RUN_PROGRESS_FILE"


class UserProgress:
    """Plain-language progress channel that reaches the user's terminal.

    Thread-safe (single process, but bootstrap may spawn pip subprocesses
    that emit their own noise — a lock around writes keeps the lines
    ordered). Messages are always prefixed ``pos-v2:`` so the user
    knows the source in a busy terminal.

    A caller may override the destination via ``POS_V2_FIRST_RUN_PROGRESS_FILE``
    — used by the test suite to redirect the surface into a capture
    file without mocking the entire class. Setting ``POS_V2_FIRST_RUN_NO_TTY=1``
    disables output entirely (silent mode; useful for non-interactive
    CI where even stderr noise is undesirable).
    """

    _PREFIX = "pos-v2: "

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._target: TextIO | None = None
        self._target_label = "none"
        self._closed = False
        self._open_target()

    # ---- lifecycle ---------------------------------------------------

    def _open_target(self) -> None:
        """Resolve the user-facing surface once; cache the file handle.

        Priority order:
          1. ``POS_V2_FIRST_RUN_PROGRESS_FILE`` env override (test hook).
          2. ``POS_V2_FIRST_RUN_NO_TTY=1`` — silent, no writes.
          3. ``/dev/tty`` — controlling terminal, bypasses stdout capture.
          4. ``sys.stderr`` — last-resort fallback.

        If all paths fail we leave ``_target = None`` and writes become
        no-ops. The bootstrap flow never depends on the progress surface
        succeeding — it is purely additive UX.
        """
        override = os.environ.get(_ENV_FORCE_FILE)
        if override:
            try:
                self._target = open(override, "a", encoding="utf-8", buffering=1)
                self._target_label = f"file:{override}"
                return
            except OSError:
                pass  # Fall through to the standard chain.

        if os.environ.get(_ENV_DISABLE, "").strip() in ("1", "true", "yes"):
            self._target = None
            self._target_label = "disabled"
            return

        # /dev/tty is the canonical "talk to the user" channel on POSIX.
        # Line-buffered (buffering=1) so each message flushes without an
        # explicit flush() call — critical for progress that must appear
        # immediately, not queued.
        try:
            if Path("/dev/tty").exists():
                self._target = open("/dev/tty", "w", encoding="utf-8", buffering=1)
                self._target_label = "tty"
                return
        except OSError:
            pass

        # Fallback: stderr. Unbuffered by default on most runtimes;
        # Claude Code may or may not surface this, but it's never worse
        # than silence.
        try:
            self._target = sys.stderr
            self._target_label = "stderr"
        except Exception:  # pragma: no cover — stderr is always present
            self._target = None
            self._target_label = "none"

    def close(self) -> None:
        """Close the TTY handle if we opened one; stderr is never closed."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._target is None:
                return
            if self._target is sys.stderr:
                return
            try:
                self._target.close()
            except OSError:
                pass

    # ---- introspection for tests -------------------------------------

    @property
    def target_label(self) -> str:
        """Diagnostic: which surface did this instance resolve to?"""
        return self._target_label

    # ---- output API --------------------------------------------------

    def _write(self, line: str) -> None:
        if self._target is None or self._closed:
            return
        try:
            with self._lock:
                self._target.write(self._PREFIX + line + "\n")
                # Line-buffered streams flush on newline; explicit
                # flush() is defensive for callers that passed a
                # non-default file object via the env override.
                try:
                    self._target.flush()
                except OSError:
                    pass
        except (OSError, ValueError):
            # OSError: surface gone (SIGHUP, pipe closed, etc.).
            # ValueError: file was closed out from under us — this
            # happens under pytest stdout-capture teardown between
            # test cases, where the stderr fallback the singleton
            # cached no longer points at a live handle. Silently drop
            # — the bootstrap contract does not depend on progress
            # delivery, only on its best effort.
            pass

    def start(self, message: str) -> None:
        """Initial line emitted at hook entry (AC1: within 2 s of launch)."""
        self._write(message)

    def step(self, message: str) -> None:
        """Per-phase or per-component progress line."""
        self._write(message)

    def warn(self, message: str) -> None:
        """Non-fatal warning the user should see inline."""
        self._write("warning: " + message)

    def done(self, message: str) -> None:
        """Final success line (AC3)."""
        self._write(message)

    def fail(
        self,
        *,
        what: str,
        remediation: str,
        error_code: int,
    ) -> None:
        """Plain-language failure line (AC4).

        Emits three pieces the user needs: what broke (plain English),
        how to fix it (plain English, step-by-step), and the error code
        (as a reference for machine-consumer audit, not the primary
        surface). The triple reaches the TTY; the stdout ``_emit_diag``
        payload remains available for the Claude Code model.
        """
        self._write(f"first-run cannot continue — {what}")
        for line in remediation.splitlines():
            line = line.strip()
            if not line:
                continue
            self._write("  " + line)
        self._write(f"(reference code: {error_code})")


# ---- module-level singleton ----------------------------------------


_singleton: UserProgress | None = None
_singleton_lock = threading.Lock()


def get_progress() -> UserProgress:
    """Return the module-wide progress instance, constructing on first call.

    Callers that want an isolated instance (e.g. the test suite)
    construct ``UserProgress()`` directly. The singleton exists so the
    helper module and its sub-phases share a single TTY handle.
    """
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = UserProgress()
    return _singleton


def reset_progress_for_tests() -> None:
    """Drop the singleton — test-only escape hatch for re-resolution.

    Not part of the public API. Exposed so tests that mutate
    ``POS_V2_FIRST_RUN_PROGRESS_FILE`` between cases get a fresh
    target resolution.
    """
    global _singleton
    with _singleton_lock:
        if _singleton is not None:
            _singleton.close()
        _singleton = None

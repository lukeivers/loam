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

"""Claude-Code subagent-file authoring (amendment #37).

Stdlib-only writer for ``<workspace>/.claude/agents/<handle>.md`` —
Claude Code's documented subagent-file surface
(https://docs.claude.com/en/docs/claude-code/sub-agents). The body is
provided by the caller (rendered by amendment #35's ``to_agent_md()``
under the shared venv via ``agent_file_runner.py``); this module owns
only the on-disk write contract.

Per amendment #37 plan §11 D-build.2 + D-build.4, the writer:

  - writes atomically via a ``.tmp`` sibling + ``os.replace`` (so an
    interrupted write never leaves Claude Code with a partial file to
    parse), and
  - skips the write entirely when the existing file's bytes equal the
    rendered body (write-only-if-different — preserves mtime stability
    across re-runs per AC37.3).

Failures are returned via the ``AgentFileWriteResult`` dataclass; the
caller (the first-run helper) inspects the dataclass and routes the
diagnostic via the existing ``_advance_state`` surface. Exceptions
escape only when the failure class is structurally a programmer error
(e.g., the ``handle`` parameter is empty); environmental failures
(unwritable directory, permission denied) are caught here so the
amendment's graceful-degradation contract (AC37.4) is never bypassed
by an unhandled exception.

ODD §2.5: every code path traces back to AC37.2 (write the file),
AC37.3 (write-only-if-different), or AC37.4 (graceful failure).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


# ---- result dataclass -----------------------------------------------


@dataclass(frozen=True)
class AgentFileWriteResult:
    """Outcome of a single ``write_agent_file`` invocation.

    Attributes:
      wrote: True iff this call created or overwrote the file. False
        when the file already held identical bytes (no-op skip per
        AC37.3) OR when an environmental failure prevented the write
        (graceful degradation per AC37.4).
      reason: short structural label naming the outcome class. One of:
        ``written-new``, ``written-update``, ``skipped-identical``,
        ``failed-permission``, ``failed-os-error``,
        ``failed-empty-handle``. Stable enough for the caller to route
        diagnostics on.
      path: the absolute target path the call resolved to (whether or
        not the write succeeded — useful for diagnostic output).
      error_detail: short string carrying ``type(exc).__name__: str(exc)``
        when the result is a ``failed-*`` reason; empty otherwise.
    """

    wrote: bool
    reason: str
    path: Path
    error_detail: str = ""


# ---- write contract -------------------------------------------------


def agent_file_path(workspace_root: Path, handle: str) -> Path:
    """Return the absolute path to ``<workspace>/.claude/agents/<handle>.md``.

    Pure helper — no I/O. Refuses an empty handle structurally (an
    empty handle would resolve to ``<workspace>/.claude/agents/.md``,
    which is not a stable subagent-file shape). AC37.2 measures the
    target shape; this helper enforces the precondition.
    """
    if not handle:
        raise ValueError("agent_file_path: handle must be non-empty")
    return Path(workspace_root) / ".claude" / "agents" / f"{handle}.md"


def write_agent_file(
    *, workspace_root: Path, handle: str, body: str
) -> AgentFileWriteResult:
    """Write ``<workspace>/.claude/agents/<handle>.md`` with ``body``.

    Behaviour:
      - When the target file does not exist: write atomically and
        return ``reason="written-new"``.
      - When the target file exists and its bytes equal the encoded
        ``body``: skip the write and return
        ``reason="skipped-identical"``. The file's mtime stays
        unchanged (AC37.3).
      - When the target file exists with different content: write
        atomically (``.tmp`` sibling + ``os.replace``) and return
        ``reason="written-update"``.
      - When the parent directory cannot be created or the file cannot
        be written (permission denied, OSError on the rename, etc.):
        return ``reason="failed-permission"`` (or ``failed-os-error``
        for non-permission OS errors). The exception is caught and
        recorded in ``error_detail``; no exception escapes (AC37.4).

    Atomic write contract: the file is either (a) absent, (b) the
    pre-existing content, or (c) the new ``body`` — never a partial
    write. Achieved via writing ``body`` into a sibling ``.tmp`` path
    first and then ``os.replace`` to the target, mirroring the
    existing settings-merge pattern.
    """
    if not handle:
        return AgentFileWriteResult(
            wrote=False,
            reason="failed-empty-handle",
            path=Path(workspace_root),
            error_detail="handle is empty",
        )

    target = agent_file_path(workspace_root, handle)
    encoded = body.encode("utf-8")

    # Read-and-compare for the write-only-if-different policy. Any
    # read failure (missing file, permission denied) falls through to
    # the write path; the read is best-effort.
    if target.exists():
        try:
            existing = target.read_bytes()
        except OSError:
            existing = None
        if existing is not None and existing == encoded:
            return AgentFileWriteResult(
                wrote=False, reason="skipped-identical", path=target
            )
        will_overwrite = True
    else:
        will_overwrite = False

    # Ensure the parent directory exists. The .claude/agents/ path is
    # entirely under hands-off-lifecycle's first-run authority; the
    # mkdir is structurally additive.
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        return AgentFileWriteResult(
            wrote=False,
            reason="failed-permission",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )
    except OSError as e:
        return AgentFileWriteResult(
            wrote=False,
            reason="failed-os-error",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )

    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp.write_bytes(encoded)
        os.replace(tmp, target)
    except PermissionError as e:
        # Best-effort cleanup — ignore secondary failure of unlink.
        try:
            tmp.unlink()
        except OSError:
            pass
        return AgentFileWriteResult(
            wrote=False,
            reason="failed-permission",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )
    except OSError as e:
        try:
            tmp.unlink()
        except OSError:
            pass
        return AgentFileWriteResult(
            wrote=False,
            reason="failed-os-error",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )

    return AgentFileWriteResult(
        wrote=True,
        reason="written-update" if will_overwrite else "written-new",
        path=target,
    )

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

"""Work-visibility presenters — the self-maintaining surfaces over the
shared aggregator (AC.WVS-FRESH.1 / .2; FORK F-1 ruling (d): (a)+(c)).

Owner/dispatcher ruled FORK F-1 = (d): a shared aggregator with two
load-bearing presenters and an on-demand render as a thin free wrapper:

  * (a) ``regenerate_status_file`` — the always-openable generated
    status artifact (``<workspace>/.loam/status.txt``). The durable
    surface a non-technical user away from a terminal (or Luke beyond
    Telegram) opens. Self-maintaining: regenerated on the events that
    change work-state, not pulled by the user.

  * (c) ``in_context_block`` — the hook-driven live in-context status
    block (``additionalContext``). The proactive persona-awareness
    surface: because the persona always HOLDS current work-state, it
    can say "still running X, Y is next" without being asked — the
    prime-objective "without asking" test (plan §3 F-1 reasoning).

  * (b) ``render_on_demand`` — the on-demand render. A thin wrapper over
    the SAME entry-point, falling out for free (FORK F-1 (b)). The
    user-facing ``/status`` SKILL that would invoke it is OWNER-GATED
    instance-config (out of cycle, per the dispatch); this function is
    the framework-tracked entry-point it would call.

THE SHARED-AGGREGATOR INVARIANT (plan §7 / §8 halt #4): every presenter
calls ``render_work_visibility`` — one snapshot, many thin presenters.
No presenter reads its own divergent state.

Per AC.WVS-FRESH.2 the refresh is persona-owned: it is driven by
work-state-change / lifecycle events (a hook path), never by a command
the user must run. The hook entry-points live in ``scripts/`` /
``hooks/``; wiring them into a live ``.claude/settings.json`` is
owner-gated instance-config (surfaced, not self-wired).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .work_visibility import render_work_visibility


#: The always-openable generated status artifact, under the gitignored
#: per-workspace ``.loam/`` user-state home (the same home the position
#: cursor's user-state instances use — ``cursor.user_state_cursor_path``
#: lives under ``.loam/``). User-state, not a committed artifact.
STATUS_FILE_RELPATH = Path(".loam") / "status.txt"


def status_file_path(workspace_root: Path | str) -> Path:
    """Resolve the generated status-file path for a workspace (a)."""
    return Path(workspace_root) / STATUS_FILE_RELPATH


def regenerate_status_file(
    workspace_root: Path | str,
    *,
    tracker_factory: Callable[[], Any] | None = None,
    cursor_path: Path | str | None = None,
    flow_loader: Callable[[str], Any] | None = None,
    stall_watchdog: Any | None = None,
) -> Path:
    """(a) Regenerate the always-openable status file from live state.

    Recomputes the surface via the shared aggregator and writes it to
    ``<workspace>/.loam/status.txt``, creating parent directories.
    Returns the written path. Self-maintaining (AC.WVS-FRESH.1): each
    call reflects the CURRENT work-state, so firing this on a work-
    state-change event refreshes the openable artifact with no user
    pull.

    This is the durable, beyond-Telegram-ready surface (plan §3 F-1
    non-tech signal): a file an attachment can carry, openable any time
    on any surface.
    """
    text = render_work_visibility(
        workspace_root,
        tracker_factory=tracker_factory,
        cursor_path=cursor_path,
        flow_loader=flow_loader,
        stall_watchdog=stall_watchdog,
    )
    path = status_file_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    return path


#: Identity-anchor-style bracketed marker so the persona retains the
#: structural signal through compaction (mirrors tracker_context's
#: ``[primary-persona/tracker-context]`` lead-in). This marker is an
#: INTERNAL framing token shown only to the persona in-context — it is
#: NOT part of the user-facing rendered surface (which is leak-free per
#: AC.WVS-RENDER.2); the marker line is stripped before any user-facing
#: file render.
IN_CONTEXT_MARKER = "[primary-persona/work-visibility]"


def in_context_block(
    workspace_root: Path | str,
    *,
    tracker_factory: Callable[[], Any] | None = None,
    cursor_path: Path | str | None = None,
    flow_loader: Callable[[str], Any] | None = None,
    stall_watchdog: Any | None = None,
) -> str:
    """(c) The live in-context status block for ``additionalContext``.

    Returns the rendered surface prefixed with the persona-only
    structural marker, so the persona always HOLDS current work-state
    and can surface it conversationally without being asked
    (AC.WVS-FRESH.2 persona-owned; the prime-objective "without asking"
    test). Thin by design (plan §10 F2 #4 — the in-context cost is
    bounded by keeping it to now/next/health).

    Rides the reinject carrier's events (SessionStart / PreCompact /
    UserPromptSubmit) in production — the registration is owner-gated
    instance-config (surfaced, not self-wired).
    """
    text = render_work_visibility(
        workspace_root,
        tracker_factory=tracker_factory,
        cursor_path=cursor_path,
        flow_loader=flow_loader,
        stall_watchdog=stall_watchdog,
    )
    return f"{IN_CONTEXT_MARKER}\n{text}"


def render_on_demand(
    workspace_root: Path | str,
    *,
    tracker_factory: Callable[[], Any] | None = None,
    cursor_path: Path | str | None = None,
    flow_loader: Callable[[str], Any] | None = None,
    stall_watchdog: Any | None = None,
) -> str:
    """(b) The on-demand render — a thin wrapper over the shared entry-
    point (FORK F-1 (b), falls out free).

    The user-facing ``/status`` SKILL that invokes this is owner-gated
    instance-config (out of cycle per the dispatch); this is the
    framework-tracked entry-point it calls. Returns the plain-language
    surface (no persona-only marker — this is user-facing).
    """
    return render_work_visibility(
        workspace_root,
        tracker_factory=tracker_factory,
        cursor_path=cursor_path,
        flow_loader=flow_loader,
        stall_watchdog=stall_watchdog,
    )

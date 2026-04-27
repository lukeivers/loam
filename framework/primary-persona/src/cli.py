"""``primary-persona`` CLI entry point.

Subcommands:
  - ``session-start`` — emit the SessionStart additionalContext for the
    current workspace (AC46.1). Always exits 0 (AC46.4 fail-soft).
  - ``user-prompt-submit`` — read Claude Code's UserPromptSubmit JSON
    envelope from stdin, extract ``prompt``, and emit per-turn memory-
    retrieval additionalContext (AC46.2). Always exits 0.
  - ``stop`` — read Claude Code's Stop envelope from stdin, recover
    the user message + assistant reply from the envelope's
    ``transcript_path``, derive a stable per-turn id, deduplicate on
    re-firing Stops, and detach the actual ``add_episode`` write to
    a background subprocess (amendment #48 / AC.M.4 / AC.M.7).
    Always exits 0.
  - ``memory-write`` — internal entry point for the detached
    background subprocess that ``stop`` spawns. Drives one
    ``add_episode`` synchronously to completion against the live
    MCP memory client (AC.M.6 / AC.M.10). Always exits 0.

Invoked from Claude Code's ``hooks.SessionStart``,
``hooks.UserPromptSubmit``, and ``hooks.Stop`` arrays via the
inner-hook entries ``hands-off-lifecycle`` registers in
``.claude/settings.json``.

Mirrors ``loam_mode.cli`` (amendment #45) shape.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .session_start_emitter import (
    cli_session_start,
    cli_user_prompt_submit,
)
from .stop_emitter import (
    cli_memory_write,
    cli_stop,
)
from .memory_write_worker import cli_memory_worker


def _resolve_workspace(workspace: Path | None) -> Path:
    if workspace is not None:
        return workspace.resolve()
    return Path.cwd().resolve()


def _cmd_session_start(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_session_start(workspace_root=workspace_root)


def _cmd_user_prompt_submit(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_user_prompt_submit(workspace_root=workspace_root)


def _cmd_stop(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_stop(workspace_root=workspace_root)


def _cmd_memory_write(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_memory_write(
        workspace_root=workspace_root,
        turn_id=args.turn_id,
        session_id=args.session_id,
        user_message=args.user_message,
        assistant_reply=args.assistant_reply,
    )


def _cmd_memory_worker(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_memory_worker(workspace_root=workspace_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="primary-persona",
        description=(
            "primary-persona hook + emitter CLI."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ss = sub.add_parser(
        "session-start",
        help=(
            "Emit the SessionStart additionalContext for the current "
            "workspace (AC46.1). Always exits 0 per AC46.4 fail-soft."
        ),
    )
    p_ss.add_argument("--workspace", type=Path, default=None)
    p_ss.set_defaults(func=_cmd_session_start)

    p_ups = sub.add_parser(
        "user-prompt-submit",
        help=(
            "Read Claude Code's UserPromptSubmit JSON envelope from "
            "stdin, extract ``prompt``, and emit per-turn memory-"
            "retrieval additionalContext (AC46.2). Always exits 0."
        ),
    )
    p_ups.add_argument("--workspace", type=Path, default=None)
    p_ups.set_defaults(func=_cmd_user_prompt_submit)

    p_stop = sub.add_parser(
        "stop",
        help=(
            "Read Claude Code's Stop envelope from stdin, recover the "
            "turn content, dedupe on re-firing Stops, and detach the "
            "actual add_episode write (amendment #48 / AC.M.4 / "
            "AC.M.7). Always exits 0."
        ),
    )
    p_stop.add_argument("--workspace", type=Path, default=None)
    p_stop.set_defaults(func=_cmd_stop)

    p_mw = sub.add_parser(
        "memory-write",
        help=(
            "Internal entry point for the detached background "
            "subprocess spawned by `stop`. Drives one add_episode "
            "synchronously (AC.M.6 / AC.M.10). Always exits 0."
        ),
    )
    p_mw.add_argument("--workspace", type=Path, default=None)
    p_mw.add_argument("--turn-id", type=str, required=True)
    p_mw.add_argument("--session-id", type=str, required=True)
    p_mw.add_argument("--user-message", type=str, required=True)
    p_mw.add_argument("--assistant-reply", type=str, required=True)
    p_mw.set_defaults(func=_cmd_memory_write)

    p_worker = sub.add_parser(
        "memory-worker",
        help=(
            "Long-running memory-write worker (amendment J / "
            "AC.J.5). Drains the disk-backed queue at "
            "<workspace>/.pos/memory-write-queue/ by driving each "
            "entry's add_episode against the live MCP memory client. "
            "Invoked by the workspace-local launchd service "
            "com.pos-v2.<slug>.memory-write-worker; runs forever in "
            "normal operation. Returns 0 on cooperative exit "
            "(SIGTERM / SIGINT)."
        ),
    )
    p_worker.add_argument("--workspace", type=Path, default=None)
    p_worker.set_defaults(func=_cmd_memory_worker)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

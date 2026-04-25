"""``primary-persona`` CLI entry point (amendment #46).

Subcommands:
  - ``session-start`` — emit the SessionStart additionalContext for the
    current workspace (AC46.1). Always exits 0 (AC46.4 fail-soft).
  - ``user-prompt-submit`` — read Claude Code's UserPromptSubmit JSON
    envelope from stdin, extract ``prompt``, and emit per-turn memory-
    retrieval additionalContext (AC46.2). Always exits 0.

Invoked from Claude Code's ``hooks.SessionStart`` and
``hooks.UserPromptSubmit`` arrays via the inner-hook entries
``hands-off-lifecycle`` registers in ``.claude/settings.json``.

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="primary-persona",
        description=(
            "primary-persona session-start + user-prompt-submit emitter "
            "CLI (amendment #46)."
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

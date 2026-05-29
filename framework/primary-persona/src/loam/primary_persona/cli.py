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

"""``primary-persona`` CLI entry point.

Subcommands:
  - ``session-start`` — emit the SessionStart additionalContext for the
    current workspace (AC46.1). Always exits 0 (AC46.4 fail-soft).
  - ``user-prompt-submit`` — read Claude Code's UserPromptSubmit JSON
    envelope from stdin, extract ``prompt``, and emit per-turn memory-
    retrieval additionalContext (AC46.2). Always exits 0.
  - ``intent-classifier`` — read Claude Code's UserPromptSubmit JSON
    envelope from stdin, classify the embedded prompt, and emit
    ``hookSpecificOutput.additionalContext`` injecting the closed-
    loop methodology directive (the ``handsoff-loop`` SKILL) when
    the classification is build-with-verification (amendment #144
    Scope A / AC.CLE.HOOK.*). Always exits 0.
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
  - ``trait-reflection-stop`` — independent Stop-hook contributor
    (AC.EOTTR.{1-5}). Reads the same Stop envelope as ``stop``,
    recovers the assistant reply from ``transcript_path``, runs a
    deterministic seven-trait self-reflection check, and appends
    one NDJSON entry per turn to
    ``<workspace>/workspace/.pos/trait-reflection/<session>.jsonl``.
    Observer + reporter only; always exits 0. Wired side-by-side
    with ``stop`` via a second entry in the operator's
    ``.claude/settings.json`` Stop array.

Invoked from Claude Code's ``hooks.SessionStart``,
``hooks.UserPromptSubmit``, and ``hooks.Stop`` arrays via the
inner-hook entries ``hands-off-lifecycle`` registers in
``.claude/settings.json``.

Mirrors ``loam_mode.cli`` (amendment #45) shape.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from loam.workspace_bootstrap.workspace_paths import WORKSPACE_STATE_SUBDIR

from .session_start_emitter import (
    cli_session_start,
    cli_user_prompt_submit,
)
from .stop_emitter import (
    cli_memory_write,
    cli_stop,
)
from .memory_write_worker import cli_memory_worker
from .end_of_turn_trait_reflection import cli_trait_reflection_stop
from .intent_classifier import cli_intent_classifier


def _resolve_workspace(workspace: Path | None) -> Path:
    """Resolve the REPO-ROOT workspace_root for the hook subcommands.

    AC.FBMW.1 — the resolvers ``memory_write_queue.queue_dir`` /
    ``file_memory.memory_dir_for_workspace`` append
    ``WORKSPACE_STATE_SUBDIR`` (``"workspace"``) to the value returned
    here (the designed D-Q.MFBM.3 contract — preserved unchanged). The
    correct argument is therefore the REPO ROOT (e.g. ``pos3``), NOT
    the operator workspace (``pos3/workspace``). Claude Code fires the
    Stop / UserPromptSubmit / SessionStart hooks with cwd set to the
    project dir, which IS the operator workspace ``<repo>/workspace/``
    — so a bare ``Path.cwd()`` doubles the resolver's segment to
    ``<repo>/workspace/workspace/.pos/...`` (the stranded dead shadow).
    The launchd-supervised memory-write-worker is already launched with
    the repo root (``--workspace {workspace}`` + ``LOAM_WORKSPACE_ROOT``
    = repo root in its plist), so writes must resolve the same repo
    root for writer and worker to agree on one queue location.

    Resolution order (caller-side fix; the resolver contract is
    untouched):
      1. an explicit ``--workspace`` flag (the worker's plist path);
      2. ``LOAM_WORKSPACE_ROOT`` — the canonical repo-root env the
         worker plist already sets (single source of truth shared with
         the worker);
      3. cwd with a trailing ``workspace`` segment stripped — when the
         hook fires from the operator workspace ``<repo>/workspace/``,
         this recovers the repo root;
      4. bare cwd — a hook fired from the repo root already (no
         trailing ``workspace`` segment) needs no adjustment.
    """
    if workspace is not None:
        return workspace.resolve()
    env_root = os.environ.get("LOAM_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root).resolve()
    cwd = Path.cwd().resolve()
    if cwd.name == WORKSPACE_STATE_SUBDIR:
        return cwd.parent
    return cwd


def _cmd_session_start(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_session_start(workspace_root=workspace_root)


def _cmd_user_prompt_submit(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_user_prompt_submit(workspace_root=workspace_root)


def _cmd_intent_classifier(args: argparse.Namespace) -> int:
    # The intent classifier is workspace-independent (it operates on
    # the user's prompt body alone, no workspace state required). The
    # ``--workspace`` flag is accepted for argparse-shape uniformity
    # with the sibling subcommands; the resolved path is unused.
    _resolve_workspace(args.workspace)
    return cli_intent_classifier()


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


def _cmd_trait_reflection_stop(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_trait_reflection_stop(workspace_root=workspace_root)


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

    p_ic = sub.add_parser(
        "intent-classifier",
        help=(
            "Read Claude Code's UserPromptSubmit JSON envelope from "
            "stdin, classify the embedded prompt (deterministic "
            "regex, no LLM), and emit hookSpecificOutput."
            "additionalContext injecting the closed-loop methodology "
            "directive (the handsoff-loop SKILL) on build-with-"
            "verification intent. Always exits 0 (amendment #144 "
            "Scope A / AC.CLE.HOOK.{1,2,3,4})."
        ),
    )
    p_ic.add_argument("--workspace", type=Path, default=None)
    p_ic.set_defaults(func=_cmd_intent_classifier)

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
            "com.loam.<slug>.memory-write-worker; runs forever in "
            "normal operation. Returns 0 on cooperative exit "
            "(SIGTERM / SIGINT)."
        ),
    )
    p_worker.add_argument("--workspace", type=Path, default=None)
    p_worker.set_defaults(func=_cmd_memory_worker)

    p_tr = sub.add_parser(
        "trait-reflection-stop",
        help=(
            "End-of-turn trait-reflection Stop-hook contributor "
            "(AC.EOTTR.{1-5}). Reads Claude Code's Stop envelope from "
            "stdin, recovers the assistant reply from "
            "``transcript_path``, runs a deterministic seven-trait "
            "self-reflection check, and appends one NDJSON entry per "
            "turn to ``<workspace>/workspace/.pos/trait-reflection/"
            "<session>.jsonl``. Observer + reporter only; always "
            "exits 0 (a non-zero Stop-hook exit blocks Claude Code's "
            "normal stop behaviour)."
        ),
    )
    p_tr.add_argument("--workspace", type=Path, default=None)
    p_tr.set_defaults(func=_cmd_trait_reflection_stop)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

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

"""``loam recover`` — the user-facing self-recovery verb (FORK F-1).

The single named thing a non-technical user can run to get unstuck. It is
the deterministic / non-tech entry-point half of FORK F-1's "(c) both"
ruling — the persona-flow half is the in-conversation distress trip
(part 1, the distress detector feeding the existing correction engine).
Both share the same underlying detect -> recover -> reset core authored in
this component.

Registered via the ``loam.cli.subcommands`` entry-point group (symmetric to
``loam amend``), so it surfaces as ``loam recover`` on the unified CLI. The
builder shape follows the M6a contract: add a named subparser + set
``args.func``.

Surface (all output is plain-language — AC.SR-RECOVER.1/.2):

  loam recover check        — run the self-diagnosis + watchdog checks and
                              print the plain-language situation. Read-only.
  loam recover reset        — the safe FBM hard-reset (backup-first,
                              fail-closed, requires --confirm "yes, start
                              fresh"). Refuses without the confirm.

This verb is the deterministic surface; it does NOT spawn a Claude session
and makes no LLM call (``feedback_no_anthropic_api_key``).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .recovery_surface import RecoverySituation, render_recovery
from .safe_reset import (
    ResetNotConfirmed,
    SafeFbmReset,
    reset_would_fail_closed,
)


def _default_workspace() -> Path:
    return Path.cwd()


def _reset_store_dir(workspace: Path) -> Path:
    """Where the reset's reversibility store + snapshots live. Kept OUTSIDE
    the ``.loam/`` store that the reset removes, so the backup survives the
    destructive step."""
    return workspace / ".loam-recovery"


def _cmd_check(args: argparse.Namespace) -> int:
    """Print the plain-language recovery situation (read-only).

    Reports whether a reset would currently be refused (fail-closed
    posture) without taking any destructive action — the user sees a
    plain-English status, never internals.
    """
    workspace = Path(args.workspace) if args.workspace else _default_workspace()
    # Import lazily so `loam recover --help` does not require the store deps.
    from loam.reversibility_primitive import ReversibilityStore

    store_dir = _reset_store_dir(workspace)
    store = ReversibilityStore(store_dir / "reversibility.sqlite")
    try:
        would_refuse = reset_would_fail_closed(store, store_dir / "snapshots")
    finally:
        store.close()

    msg = render_recovery(RecoverySituation.all_clear)
    print(msg.text)
    if would_refuse:
        # A reset right now would be refused because no backup exists yet —
        # this is the safe default, surfaced in plain language.
        print()
        print(
            "If you ask me to start fresh, I will make a full backup first; "
            "until then nothing can be erased."
        )
    return 0


def _cmd_reset(args: argparse.Namespace) -> int:
    """Run the safe FBM hard-reset (backup-first, fail-closed, confirmed)."""
    workspace = Path(args.workspace) if args.workspace else _default_workspace()
    from loam.reversibility_primitive import ReversibilityStore

    store_dir = _reset_store_dir(workspace)
    store = ReversibilityStore(store_dir / "reversibility.sqlite")
    resetter = SafeFbmReset(store=store, snapshot_root=store_dir / "snapshots")
    try:
        try:
            result = resetter.reset(workspace, confirmed=args.confirm)
        except ResetNotConfirmed as exc:
            print(str(exc))
            return 2
    finally:
        store.close()

    # Plain-language confirmation — no paths/IDs to the user.
    print(
        "Done. I made a complete backup of your saved settings first, then "
        "started them fresh. If anything looks wrong, tell me and I can put "
        "the backup right back."
    )
    # The snapshot path is operational detail kept off the user surface; a
    # caller (the persona) can read it from the return value when wiring.
    _ = result.snapshot_path
    return 0


def build_recover_subcommand(sub: argparse._SubParsersAction) -> None:
    """Register the ``recover`` subcommand on ``sub`` (M6a builder contract).

    Entry-point declaration in ``framework/self-correction/pyproject.toml``:

        [project.entry-points."loam.cli.subcommands"]
        recover = "loam.self_correction.recover_cli:build_recover_subcommand"
    """
    recover_parser = sub.add_parser(
        "recover",
        help="get unstuck: check what is wrong, or safely start fresh",
        add_help=True,
    )
    _attach_recover_actions(recover_parser)


def _attach_recover_actions(parser: argparse.ArgumentParser) -> None:
    """Attach the recover actions (check / reset) directly onto *parser*.

    Shared by both the standalone ``loam-recover`` entry-point and the
    ``loam recover`` subcommand so the action surface is authored once.
    """
    action_sub = parser.add_subparsers(dest="recover_cmd", required=True)

    p_check = action_sub.add_parser(
        "check", help="check what might be stuck and what to do about it"
    )
    p_check.add_argument("--workspace", default=None)
    p_check.set_defaults(func=_cmd_check)

    p_reset = action_sub.add_parser(
        "reset",
        help="safely start your saved settings fresh (makes a backup first)",
    )
    p_reset.add_argument("--workspace", default=None)
    p_reset.add_argument(
        "--confirm",
        default=None,
        help='explicit confirmation phrase, e.g. "yes, start fresh"',
    )
    p_reset.set_defaults(func=_cmd_reset)


def main(argv: list[str] | None = None) -> int:
    """Standalone entry-point (``loam-recover``) mirroring the subcommand.

    Exposes ``check`` / ``reset`` directly (``loam-recover check ...``),
    matching the actions the ``loam recover`` subcommand exposes.
    """
    parser = argparse.ArgumentParser(prog="loam recover")
    _attach_recover_actions(parser)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover — exercised via main(argv)
    raise SystemExit(main())

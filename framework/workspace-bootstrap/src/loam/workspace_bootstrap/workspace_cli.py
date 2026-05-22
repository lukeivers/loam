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

"""``loam workspace`` CLI verb — operator-facing surface for
post-scaffold workspace maintenance.

Registered via the ``loam.cli.subcommands`` entry-point group
(mirrors ``loam.workspace_bootstrap.onboarding_cli.build_onboard_subcommand``).
The top-level verb is ``workspace``; sub-verbs hang off it:

  - ``rescaffold-skills`` — re-run ``_symlink_plugin_skills`` against
    an existing workspace. Operator recovery path for workspaces
    scaffolded before v0.1.7 (and therefore missing plugin-shipped
    SKILL symlinks). Idempotent + collision-aware: existing correct
    symlinks are left alone; non-symlink targets (workspace-local
    operator overrides) raise ``PluginSkillCollisionError`` per
    AC.LAYERED.3 (operator resolves explicitly); cross-plugin name
    collisions raise per AC.LAYERED.4. Composes on top of the
    existing fresh-workspace symlinker without semantic change.

Amendment #144 Scope C / AC.CLE.SCAFFOLD-AUDIT.2 — closes the
operator-recovery gap for pre-v0.1.7 workspaces (the pos3 case:
pos3 was scaffolded before v0.1.7 and the first-run scaffolder is
idempotent, so pos3's ``.claude/skills/`` carries only the manual
``handsoff-loop`` symlink it added today, NOT the 21 plugin-shipped
SKILLs canonical loam now ships).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    PluginSkillCollisionError,
    _symlink_plugin_skills,
)


def rescaffold_skills(workspace_root: Path) -> tuple[str, ...]:
    """Re-run plugin-SKILL symlinking against an existing workspace.

    Pure function — testable without stdio. The CLI command wrapper
    (:func:`_cmd_rescaffold_skills`) adds the stdout reporting +
    PluginSkillCollisionError-to-exit-code mapping.

    Returns the tuple of newly-written relative paths (matches
    ``_symlink_plugin_skills``'s return shape). An empty tuple means
    either no plugins were resolvable from the workspace OR every
    plugin-shipped SKILL was already symlinked (idempotent re-run).
    """
    return _symlink_plugin_skills(Path(workspace_root))


def _cmd_rescaffold_skills(args: argparse.Namespace) -> int:
    """CLI handler for ``loam workspace rescaffold-skills``.

    Exit codes:

      - 0 — symlinking completed (possibly a no-op on idempotent
        re-runs); newly-written paths reported to stdout.
      - 2 — a ``PluginSkillCollisionError`` was raised (workspace-
        local override at a target path OR cross-plugin name
        collision). The operator resolves explicitly; we never
        overwrite operator artefacts.
    """
    workspace_root: Path = (
        args.path if args.path is not None else Path.cwd()
    ).resolve()
    if not workspace_root.is_dir():
        print(
            f"loam workspace rescaffold-skills: workspace path is not a "
            f"directory: {workspace_root}",
            file=sys.stderr,
        )
        return 2
    try:
        written = rescaffold_skills(workspace_root)
    except PluginSkillCollisionError as exc:
        print(
            f"loam workspace rescaffold-skills: collision halted the "
            f"operation; resolve and re-run.\n  {exc}",
            file=sys.stderr,
        )
        return 2
    if not written:
        print(
            "loam workspace rescaffold-skills: nothing to do (every "
            "plugin-shipped SKILL is already symlinked, or no plugins "
            "are reachable from this workspace).",
        )
        return 0
    print(
        "loam workspace rescaffold-skills: registered "
        f"{len(written)} plugin SKILL symlink(s):"
    )
    for rel in written:
        print(f"  {rel}")
    return 0


def build_workspace_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register ``loam workspace`` on the unified loam CLI.

    Builder contract per ``loam_cli`` M6a (mirrors
    ``build_onboard_subcommand``). The ``workspace`` verb itself is
    a parent parser with its own sub-verbs; ``rescaffold-skills`` is
    the first sub-verb. Future amendments can attach additional
    workspace-maintenance verbs here (e.g. an upgrade verb, a
    diagnostics verb) without re-shaping the discovery contract.
    """
    parser = sub.add_parser(
        "workspace",
        help=(
            "Operator-facing post-scaffold workspace maintenance "
            "verbs (rescaffold-skills for now)."
        ),
        description=(
            "loam workspace — operator maintenance verbs for an "
            "already-bootstrapped workspace. See `loam workspace "
            "--help` for the available sub-verbs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    workspace_sub = parser.add_subparsers(
        dest="workspace_command",
        required=True,
    )

    p_rs = workspace_sub.add_parser(
        "rescaffold-skills",
        help=(
            "Re-run plugin-SKILL symlinking against an existing "
            "workspace. Operator recovery path for workspaces "
            "scaffolded before v0.1.7 (missing plugin-shipped SKILL "
            "symlinks). Idempotent + collision-aware."
        ),
        description=(
            "loam workspace rescaffold-skills — re-runs "
            "_symlink_plugin_skills (v0.1.7 AC.LAYERED.2) against "
            "an existing workspace. Existing correct symlinks are "
            "left alone; non-symlink operator overrides at target "
            "paths raise (operator resolves); cross-plugin name "
            "collisions raise.\n\n"
            "Use this after upgrading from a pre-v0.1.7 loam install "
            "to retrofit the SKILL discovery into your workspace's "
            "`.claude/skills/` directory. The first-run scaffold is "
            "idempotent and won't re-run on an already-bootstrapped "
            "workspace; this verb is the recovery path."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rs.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=None,
        help=(
            "Workspace root (default: cwd). Must be a previously-"
            "bootstrapped workspace."
        ),
    )
    p_rs.set_defaults(func=_cmd_rescaffold_skills)

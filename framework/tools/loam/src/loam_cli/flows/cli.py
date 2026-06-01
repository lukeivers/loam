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

"""``loam flow`` argparse builder + dispatcher (the production verb).

Registered with the unified ``loam`` CLI dispatcher's
``loam.cli.subcommands`` entry-point group (sibling to ``release`` /
``audit``). This is the operator-facing surface over the
defined-workflow system: validate a flow definition, and resolve /
surface the active position cursor (the same positive-resolution check
the re-injection hook runs).

Surface::

    loam flow validate <flow-definition.flow.md>
    loam flow position [--repo-root <path>] [--flow <name>]

  * ``validate`` — parse + validate a flow definition; exit non-zero
    with a corrective message on a malformed / not-a-flow input
    (AC.FLOWDEF.3 / AC.FLOWDEF.4 surfaced through the real verb).
  * ``position`` — resolve the active flow's cursor against its
    definition and print the position block, or the PAUSE directive if
    position is UNRESOLVED (AC.PAUSE.1 / AC.PAUSE.2 through the real
    verb). Exit code 0 when resolved, 2 when PAUSED.

Exit codes: 0 = ok (valid / resolved); 1 = invalid flow definition;
2 = position UNRESOLVED (pause condition).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam_cli.flows.cursor import (
    methodology_cursor_path,
    read_cursor,
    resolve_cursor,
)
from loam_cli.flows.format import FlowParseError, parse_flow_definition
from loam_cli.flows.pause import position_check

_FLOWS_DIR = "docs/flows"


def build_flow_subcommand(sub: argparse._SubParsersAction) -> None:
    """Register the ``flow`` subcommand on *sub*."""
    p = sub.add_parser(
        "flow",
        help=(
            "defined-workflow system: validate a flow definition + "
            "resolve the active position cursor (pause-if-lost)"
        ),
        description=(
            "Validate a flow definition (machine graph + human "
            "narrative) and resolve the active flow's position cursor "
            "against it. The positive-resolution check is the same one "
            "the re-injection hook runs: a resolved cursor surfaces the "
            "position + follow-it directive; an unresolved cursor "
            "(missing / stale / vanished step) surfaces the PAUSE "
            "directive."
        ),
    )
    flow_sub = p.add_subparsers(dest="flow_command", required=True)

    v = flow_sub.add_parser(
        "validate",
        help="parse + validate a flow definition; reject malformed.",
    )
    v.add_argument(
        "path",
        type=Path,
        metavar="<flow-definition>",
        help="path to a <flow>.flow.md flow definition.",
    )
    v.set_defaults(func=_dispatch_validate)

    pos = flow_sub.add_parser(
        "position",
        help="resolve + surface the active flow's position cursor.",
    )
    pos.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root override (default: cwd).",
    )
    pos.add_argument(
        "--flow",
        type=str,
        default=None,
        metavar="<name>",
        help=(
            "the active flow name (default: the single methodology flow "
            "cursor present under docs/flows/)."
        ),
    )
    pos.set_defaults(func=_dispatch_position)

    p.set_defaults(func=_dispatch_help)


def _dispatch_help(args: argparse.Namespace) -> int:
    print(
        "loam flow: specify a subcommand — 'validate <flow.md>' or "
        "'position'."
    )
    return 0


def _dispatch_validate(args: argparse.Namespace) -> int:
    """Run ``loam flow validate``. Returns the exit code."""
    path: Path = args.path
    if not path.is_file():
        print(f"ERROR: flow definition not found: {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    try:
        definition = parse_flow_definition(text)
    except FlowParseError as exc:
        print(f"== flow definition INVALID ==\n  {exc}")
        return 1
    print(
        f"== flow definition VALID ==\n"
        f"  flow: {definition.flow}\n"
        f"  steps: {len(definition.steps)}  "
        f"gates: {len(definition.gates)}\n"
        f"  entry: {definition.entry}"
    )
    return 0


def _find_active_flow(repo_root: Path, flow: str | None) -> str | None:
    if flow:
        return flow
    flows_dir = repo_root / _FLOWS_DIR
    if not flows_dir.is_dir():
        return None
    cursors = sorted(flows_dir.glob("*.cursor.yaml"))
    if len(cursors) == 1:
        # `<flow>.cursor.yaml` -> `<flow>`.
        return cursors[0].name[: -len(".cursor.yaml")]
    return None


def _dispatch_position(args: argparse.Namespace) -> int:
    """Run ``loam flow position``. Returns the exit code (2 == PAUSED)."""
    repo_root = (args.repo_root or Path.cwd()).resolve()
    flow = _find_active_flow(repo_root, args.flow)
    if flow is None:
        decision = position_check(
            resolve_cursor(None, None)
        )
        print(decision.directive)
        return 2

    cursor_path = methodology_cursor_path(repo_root, flow)
    cursor = read_cursor(cursor_path)
    definition = None
    if cursor is not None:
        flow_def_path = repo_root / _FLOWS_DIR / f"{cursor.flow}.flow.md"
        if flow_def_path.is_file():
            try:
                definition = parse_flow_definition(
                    flow_def_path.read_text(encoding="utf-8")
                )
            except FlowParseError:
                definition = None
    resolution = resolve_cursor(cursor, definition)
    decision = position_check(resolution)
    print(decision.directive)
    return 2 if decision.paused else 0

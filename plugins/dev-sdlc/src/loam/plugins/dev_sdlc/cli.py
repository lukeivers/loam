"""`loam project ...` subcommand builder.

Per plan §4 AC.OSS-M6.6 + §10 D-build.M6.5: the unified `loam` CLI
discovers this builder via the NEW entry-point group
`loam.cli.subcommands` (introduced at M6a). The plugin's
`pyproject.toml` ships
`project = "loam.plugins.dev_sdlc.cli:build_project_subcommand"`.

`loam_cli.cli.main` iterates the entry-point group at startup and
invokes each builder with the parent argparse subparsers handle
to register the subcommand.

Builder contract:

    def build_project_subcommand(
        sub: argparse._SubParsersAction,
    ) -> None:
        ...

The builder MUST set `func` on each leaf-parser via `set_defaults`
so the unified CLI's main() can dispatch via `args.func(args)`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import api
from .errors import (
    DevSdlcError,
    StageGateFailedError,
)


def _add_workspace_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help=(
            "workspace root (default: cwd). The plugin's per-project "
            "state lives in <workspace>/.loam/dev-sdlc.sqlite."
        ),
    )


def _cmd_new(args: argparse.Namespace) -> int:
    try:
        handle = api.start_project(
            slug=args.slug,
            methodology=args.methodology,
            workspace_root=args.workspace_root,
        )
    except DevSdlcError as exc:
        print(f"loam project new: {exc}", file=sys.stderr)
        return 2
    print(
        f"created project {handle.slug!r} at "
        f"{handle.project_root.as_posix()} "
        f"(methodology={handle.methodology}, "
        f"current_stage={handle.current_stage})"
    )
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    try:
        rows = api.project_status(
            slug=args.slug,
            workspace_root=args.workspace_root,
        )
    except DevSdlcError as exc:
        print(f"loam project status: {exc}", file=sys.stderr)
        return 2
    if args.json:
        out = [r.model_dump(mode="json") for r in rows]
        print(json.dumps(out, indent=2, default=str))
        return 0
    if not rows:
        print("(no projects)")
        return 0
    for r in rows:
        print(
            f"{r.slug}\tmethodology={r.methodology}\t"
            f"current_stage={r.current_stage}\t"
            f"root={r.project_root.as_posix()}"
        )
    return 0


def _cmd_advance(args: argparse.Namespace) -> int:
    try:
        result = api.advance_stage(
            slug=args.slug,
            workspace_root=args.workspace_root,
        )
    except StageGateFailedError as exc:
        # Render the structured halt-and-surface signal per plan §4
        # AC.OSS-M6.4 — the persona's exception handler receives the
        # same shape via the API; the CLI surface mirrors it for
        # operator-callable use.
        print(
            f"loam project advance: gate failed at stage "
            f"{exc.stage!r}: reason={exc.reason}",
            file=sys.stderr,
        )
        return 3
    except DevSdlcError as exc:
        print(f"loam project advance: {exc}", file=sys.stderr)
        return 2
    print(
        f"advanced project {result.slug!r}: "
        f"{result.from_stage} → {result.to_stage} "
        f"(methodology={result.methodology})"
    )
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    try:
        rows = api.list_projects(workspace_root=args.workspace_root)
    except DevSdlcError as exc:
        print(f"loam project list: {exc}", file=sys.stderr)
        return 2
    if args.json:
        out = [r.model_dump(mode="json") for r in rows]
        print(json.dumps(out, indent=2, default=str))
        return 0
    if not rows:
        print("(no projects)")
        return 0
    for r in rows:
        print(f"{r.slug}\t{r.methodology}\t{r.current_stage}")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    try:
        result = api.gate_check(
            slug=args.slug,
            workspace_root=args.workspace_root,
        )
    except DevSdlcError as exc:
        print(f"loam project gate: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        return 0 if result.passed else 3
    if result.passed:
        print(
            f"gate passed for {result.slug!r} at stage {result.stage!r}"
        )
        return 0
    print(
        f"gate FAILED for {result.slug!r} at stage {result.stage!r}: "
        f"reason={result.reason}"
    )
    if result.detail:
        print(f"  {result.detail}")
    return 3


def build_project_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the `loam project ...` subcommand surface.

    Five operator verbs per plan §1 capability #4 + AC.OSS-M6.6:
    `new`, `status`, `advance`, `list`, `gate`.
    """
    project_parser = sub.add_parser(
        "project",
        help=(
            "Dev/SDLC project lifecycle — methodology-shaped 5-stage "
            "workflow with structural gate enforcement"
        ),
        description=(
            "loam project ... — Dev/SDLC plugin's operator surface. "
            "Five verbs: new, status, advance, list, gate."
        ),
    )
    project_sub = project_parser.add_subparsers(
        dest="project_verb", required=True
    )

    # new
    p_new = project_sub.add_parser(
        "new",
        help="scaffold a new project tree",
        description=(
            "Scaffold an ODD-shaped (or methodology-specified) project "
            "tree under <workspace>/projects/<slug>/. Records the "
            "project in <workspace>/.loam/dev-sdlc.sqlite."
        ),
    )
    p_new.add_argument("slug", help="project slug (directory name)")
    p_new.add_argument(
        "--methodology",
        choices=("odd", "tdd", "bdd", "adhoc"),
        default="odd",
        help=(
            "methodology shape (default: odd). Non-ODD methodologies "
            "preserve an internal ODD mirror at "
            "<project>/.dev-sdlc-odd-mirror.yaml."
        ),
    )
    _add_workspace_root_arg(p_new)
    p_new.set_defaults(func=_cmd_new)

    # status
    p_status = project_sub.add_parser(
        "status",
        help="report current stage + methodology",
        description=(
            "Report current stage + methodology. Without a slug, "
            "report every project."
        ),
    )
    p_status.add_argument(
        "slug",
        nargs="?",
        default=None,
        help="project slug (optional; default: every project)",
    )
    p_status.add_argument(
        "--json", action="store_true", help="emit JSON output"
    )
    _add_workspace_root_arg(p_status)
    p_status.set_defaults(func=_cmd_status)

    # advance
    p_advance = project_sub.add_parser(
        "advance",
        help="advance to next stage (gate-enforced)",
        description=(
            "Run the structural gate against the current stage's "
            "artefact; on pass, advance the project's current_stage."
        ),
    )
    p_advance.add_argument("slug", help="project slug")
    _add_workspace_root_arg(p_advance)
    p_advance.set_defaults(func=_cmd_advance)

    # list
    p_list = project_sub.add_parser(
        "list",
        help="list every project",
        description="List every project in the workspace.",
    )
    p_list.add_argument(
        "--json", action="store_true", help="emit JSON output"
    )
    _add_workspace_root_arg(p_list)
    p_list.set_defaults(func=_cmd_list)

    # gate
    p_gate = project_sub.add_parser(
        "gate",
        help="check current stage's gate without advancing",
        description=(
            "Inspect the current stage's artefact + report whether "
            "the gate passes. Does not advance."
        ),
    )
    p_gate.add_argument("slug", help="project slug")
    p_gate.add_argument(
        "--json", action="store_true", help="emit JSON output"
    )
    _add_workspace_root_arg(p_gate)
    p_gate.set_defaults(func=_cmd_gate)

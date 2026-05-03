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

"""``loam init`` subcommand builder.

Per FBE.1 sub-plan §6 + parent plan AC.FBE.1.1..1.6: registers the
`loam init <path> [--from <canonical-source>]` argparse parser whose
action wraps the existing
``loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace``
function. Per FBE.9 (AC.FBE.9.1): ``--from`` is optional; when
omitted, the resolver defaults to the current working directory if it
is a git tree (the typical pattern when ``loam init`` runs from inside
a cloned loam tree).

The builder follows the M6a contract — `loam_cli/cli.py` discovers
this builder via the `loam.cli.subcommands` entry-point group and
invokes it with the parent argparse `_SubParsersAction`. The builder
adds its own subparser + `set_defaults(func=<callable>)` so the
unified CLI's `main` dispatches via `args.func(args)`.

Composition contract (AC.FBE.1.6 — negative AC):

  - Zero edits to ``framework/tools/loam/src/loam_cli/cli.py`` (entry-
    point discovery is the contract).
  - Zero edits to ``loam.workspace_bootstrap.new_workspace.
    bootstrap_new_workspace``'s signature or behaviour. The wrapper
    composes on the existing public function as-is.

Exit code mapping (mirrors ``new_workspace.cli_main``):

  - 0 — bootstrap succeeded.
  - 1 — target not empty (``TargetNotEmptyError``).
  - 2 — canonical source invalid (``CanonicalSourceInvalidError``).
  - 3 — clone failed (``CloneFailedError``).
  - 4 — scaffold failed (``ScaffoldFailedError``).
  - 5 — other ``NewWorkspaceError`` (catch-all for the few halt
        conditions outside the named subclasses).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _cmd_init(args: argparse.Namespace) -> int:
    """Action callable for ``loam init`` — wraps bootstrap_new_workspace.

    Lazy-imports ``loam.workspace_bootstrap.new_workspace`` so that
    the loam-init subcommand registration (entry-point group discovery)
    does not fail-load when workspace-bootstrap isn't installed in the
    same environment. The dispatcher's discovery loop swallows load
    failures + emits a WARNING per `loam_cli/cli.py:84-89` (M6c
    graceful-fallthrough-with-detection); a lazy import shifts the
    failure to invocation-time where the user gets a clearer error.
    """
    try:
        from loam.workspace_bootstrap.new_workspace import (
            bootstrap_new_workspace,
            CanonicalSourceInvalidError,
            CloneFailedError,
            NewWorkspaceError,
            ScaffoldFailedError,
            TargetNotEmptyError,
        )
    except ImportError as exc:
        print(
            f"[loam init] loam-workspace-bootstrap is not installed in "
            f"this environment ({exc}). Install it alongside loam-init: "
            f"`pip install -e framework/workspace-bootstrap`.",
            file=sys.stderr,
        )
        return 6

    # FBE.9 (AC.FBE.9.1) — resolve `--from` smart-default. When omitted
    # via the CLI, default to the current working directory if it is a
    # git tree (the typical pattern when `loam init` runs from inside a
    # cloned loam tree). Otherwise raise a structured error so the
    # existing CanonicalSourceInvalidError handler returns exit 2.
    canonical_source = args.canonical_source
    if canonical_source is None:
        cwd = Path.cwd().resolve()
        if (cwd / ".git").exists():
            canonical_source = str(cwd)
        else:
            print(
                f"[loam init] --from omitted AND current working directory "
                f"{cwd!s} is not a git tree (missing .git/). Pass --from "
                f"with an absolute POSIX path to a local git working tree "
                f"or an http(s)/git@ URL, or run `loam init` from inside "
                f"a cloned loam tree.",
                file=sys.stderr,
            )
            return 2

    try:
        result = bootstrap_new_workspace(
            new_ws_path=args.path,
            canonical_source=canonical_source,
            init_existing=args.init_existing,
            persona_handle=args.persona_handle,
        )
    except TargetNotEmptyError as exc:
        print(f"[loam init] {exc}", file=sys.stderr)
        return 1
    except CanonicalSourceInvalidError as exc:
        print(f"[loam init] {exc}", file=sys.stderr)
        return 2
    except CloneFailedError as exc:
        print(f"[loam init] {exc}", file=sys.stderr)
        return 3
    except ScaffoldFailedError as exc:
        print(f"[loam init] {exc}", file=sys.stderr)
        return 4
    except NewWorkspaceError as exc:
        # Catch-all for halt conditions outside the named subclasses
        # (e.g. --init-existing with no framework/).
        print(f"[loam init] {exc}", file=sys.stderr)
        return 5

    # Success summary — operator-actionable next-step guidance, mirrors
    # cli_main's prose so users get the same shape regardless of which
    # entry point they invoked.
    print(
        f"[loam init] bootstrapped {result.new_ws_path!s}",
        file=sys.stderr,
    )
    print(
        f"  framework/  ← clone of {result.canonical_source} "
        f"({result.canonical_source_kind})",
        file=sys.stderr,
    )
    print(
        f"  workspace/  ← scaffolded "
        f"(persona={args.persona_handle}, "
        f"reason={result.scaffold_result.reason})",
        file=sys.stderr,
    )
    print(
        "  .claude/    ← scaffolded (Claude Code expects this here)",
        file=sys.stderr,
    )
    return 0


def build_init_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the ``loam init`` subcommand on the unified loam CLI.

    Builder contract (per loam_cli M6a discovery loop):

        def build_init_subcommand(
            sub: argparse._SubParsersAction,
        ) -> None:
            ...

    The builder MUST call ``set_defaults(func=<callable>)`` on the
    leaf parser so ``loam_cli.cli.main`` can dispatch via
    ``args.func(args)``.

    Argparse surface mirrors ``pos-new-workspace`` (the existing
    console-script for the same primitive) but with the operator-
    facing positional named ``path`` (rather than ``new_ws_path``)
    for ergonomics under the ``loam init <path>`` invocation form.
    """
    parser = sub.add_parser(
        "init",
        help=(
            "Bootstrap a fresh loam workspace from a canonical source"
        ),
        description=(
            "loam init — bootstrap a fresh workspace at <path>. "
            "Creates <path>/framework/ (cloned from <canonical-source>), "
            "<path>/workspace/ (scaffolded with .pos/, personas/, "
            ".mcp.json), and <path>/.claude/ (Claude Code's expected "
            "location at workspace root). Subsequent `pos-sync` "
            "invocations from inside the workspace work no-args."
        ),
        epilog=(
            "Examples:\n"
            "  loam init ~/my-ws --from /Users/.../loam\n"
            "  loam init ~/my-ws --from https://github.com/lukeivers/loam\n"
            "  loam init ~/existing-ws --from /Users/.../loam --init-existing\n"
            "  loam init ~/my-ws       (run from inside a cloned loam tree;\n"
            "                          --from defaults to cwd)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        type=Path,
        help=(
            "Target path for the new workspace. Must be empty or "
            "non-existent (use --init-existing to re-scaffold an "
            "already-bootstrapped workspace)."
        ),
    )
    parser.add_argument(
        "--from",
        dest="canonical_source",
        required=False,
        default=None,
        type=str,
        help=(
            "Canonical loam source: an absolute POSIX path to a local "
            "git working tree, or an http(s)/git@ URL. URL form clones "
            "to ~/.loam/canonical-cache/<repo-id>/ first; the original "
            "URL is recorded in the new workspace's sync-config.yaml so "
            "subsequent pos-sync runs resolve it the same way. Optional "
            "(per FBE.9 / AC.FBE.9.1); if omitted, defaults to the "
            "current working directory when it is a git tree (the "
            "typical pattern when `loam init` runs from inside a cloned "
            "loam tree). Errors with exit-2 if omitted AND cwd is not a "
            "git tree."
        ),
    )
    parser.add_argument(
        "--init-existing",
        action="store_true",
        help=(
            "Skip the clone step; assume <path>/framework/ already "
            "exists as a git working tree. Runs only the scaffold + "
            "sync-config write. Idempotent: re-invocation on a complete "
            "workspace produces no further changes."
        ),
    )
    # Persona-handle default mirrors workspace_bootstrap's
    # ``DEFAULT_PERSONA_HANDLE = "primary"`` (verified at
    # workspace_bootstrap/adapters/first_run_scaffold.py:169). Inlined
    # as a string literal rather than imported so the entry-point
    # builder loads even when workspace-bootstrap isn't yet installed
    # in the venv (the dispatcher's discovery loop swallows load
    # failures, hiding the cause); the import-failure path lives in
    # ``_cmd_init`` where the user gets a clear actionable message.
    parser.add_argument(
        "--persona-handle",
        default="primary",
        help=(
            "Workspace primary-persona handle (default: 'primary'). "
            "Passed through to the first-run scaffold."
        ),
    )
    parser.set_defaults(func=_cmd_init)

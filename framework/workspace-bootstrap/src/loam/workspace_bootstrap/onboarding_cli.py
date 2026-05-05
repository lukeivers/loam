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

"""``loam onboard`` subcommand builder.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.1: registers ``loam
onboard`` via the ``loam.cli.subcommands`` entry-point group (M6a
contract; mirrors loam-init's wiring at
``framework/loam-init/pyproject.toml`` line 23).

Optional invocation; idempotent (re-run on already-onboarded
workspace re-uses prior config + offers per-question re-ask).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _cmd_onboard(args: argparse.Namespace) -> int:
    """Action callable for ``loam onboard`` — runs the ritual.

    Lazy-imports the orchestrator + audit emitter so the entry-point
    discovery loop in ``loam_cli/cli.py`` doesn't fail when one of
    the optional helpers is missing in a constrained environment.
    """
    try:
        from .onboarding import run_onboarding, SKIP_ENV_VAR
    except ImportError as exc:
        print(
            f"[loam onboard] onboarding ritual unavailable ({exc}). "
            f"Reinstall workspace-bootstrap.",
            file=sys.stderr,
        )
        return 1

    workspace_root: Path = args.path.resolve()
    if not workspace_root.is_dir():
        print(
            f"[loam onboard] workspace path does not exist: "
            f"{workspace_root!s}. Run `loam init <path>` first.",
            file=sys.stderr,
        )
        return 2

    if os.environ.get(SKIP_ENV_VAR) == "1":
        print(
            "[loam onboard] LOAM_ONBOARDING_SKIP=1 — ritual skipped.",
            file=sys.stderr,
        )
        return 0

    answerer = _stdin_answerer

    result = run_onboarding(
        workspace_root,
        answerer=answerer,
    )
    if result.skipped:
        return 0

    print(
        f"[loam onboard] completed; summary at "
        f"{result.completion_summary_path!s}",
        file=sys.stderr,
    )
    return 0


def _stdin_answerer(slug: str, prompt: str) -> str:
    """Stdin-driven answerer for the production CLI."""
    print(prompt, file=sys.stderr)
    print("> ", end="", file=sys.stderr, flush=True)
    line = sys.stdin.readline()
    return line.strip()


def build_onboard_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register ``loam onboard`` on the unified loam CLI.

    Builder contract per loam_cli M6a (mirrors loam-init's
    ``build_init_subcommand``).
    """
    parser = sub.add_parser(
        "onboard",
        help=(
            "Run the install-time onboarding ritual on a workspace"
        ),
        description=(
            "loam onboard — six-question one-at-a-time install-time "
            "onboarding ritual. Auto-detects project language, asks "
            "channel + safety-profile + extractor + watch + auto-skill-"
            "capture preferences via the per-project-pm batch API, "
            "fires opt-in activations, and writes a SOC-2-floor audit-"
            "log per Decision P. LOAM_ONBOARDING_SKIP=1 disables the "
            "ritual (CI-friendly). LOAM_ONBOARDING_SURVEY=<path> reads "
            "pre-filled defaults from a survey file (AC.ONBOARD.15)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help=(
            "Workspace root (default: cwd). Must be a previously-"
            "bootstrapped workspace (use `loam init` first)."
        ),
    )
    parser.set_defaults(func=_cmd_onboard)

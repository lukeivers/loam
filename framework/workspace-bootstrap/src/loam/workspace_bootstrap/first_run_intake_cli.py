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

"""``loam init-intake`` subcommand builder — the translate-in first-run intake
orchestrator's CLI entry-point (slice N3 / AC.ONFIRE.1).

Registers ``loam init-intake [path]`` via the ``loam.cli.subcommands``
entry-point group (M6a contract; mirrors ``onboarding_cli``'s wiring). The
action drives ``first_run_intake.run_first_run_intake`` — the real production
orchestrator — with a stdin-driven answerer.

The verb is named ``init-intake`` (NOT ``init``) to avoid shadowing the
existing sealed ``loam init`` tree-bootstrap verb (``framework/loam-init/``);
see the plan §11 collision resolution. This is the REAL entry-point the
outcome-altitude AC.ONFIRE.3 walks on an empty instance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _stdin_answerer(slug: str, prompt: str) -> str:
    """Stdin-driven answerer for the production CLI (mirrors onboarding_cli)."""
    print(prompt, file=sys.stderr)
    print("> ", end="", file=sys.stderr, flush=True)
    line = sys.stdin.readline()
    return line.strip()


def _cmd_init_intake(args: argparse.Namespace) -> int:
    """Action callable for ``loam init-intake`` — runs the orchestrator.

    Lazy-imports the orchestrator so the entry-point discovery loop in
    ``loam_cli/cli.py`` doesn't fail-load in a constrained environment.
    """
    try:
        from .first_run_intake import run_first_run_intake
    except ImportError as exc:
        print(
            f"[loam init-intake] first-run intake unavailable ({exc}). "
            f"Reinstall workspace-bootstrap.",
            file=sys.stderr,
        )
        return 1

    workspace_root: Path = args.path.resolve()
    if not workspace_root.is_dir():
        print(
            f"[loam init-intake] workspace path does not exist: "
            f"{workspace_root!s}. Run `loam init <path>` first.",
            file=sys.stderr,
        )
        return 2

    result = run_first_run_intake(
        workspace_root,
        answerer=_stdin_answerer,
        capability_answerer=_stdin_answerer if args.with_capability_ritual else None,
        run_capability_ritual=args.with_capability_ritual,
    )

    if result.already_seeded:
        print(
            f"[loam init-intake] instance already onboarded "
            f"(seed present at {result.global_home!s}); nothing changed "
            f"(idempotent / non-destructive).",
            file=sys.stderr,
        )
        return 0

    for idea in result.intake.leverage_ideas:
        print(f"\n  >> {idea.text}", file=sys.stderr)
    if result.seed is not None:
        print(
            f"\n[loam init-intake] seeded user-state under "
            f"{result.global_home!s} "
            f"(created: {', '.join(result.seed.created) or 'nothing new'}).",
            file=sys.stderr,
        )
    return 0


def build_init_intake_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register ``loam init-intake`` on the unified loam CLI (M6a contract)."""
    parser = sub.add_parser(
        "init-intake",
        help=(
            "Run the translate-in first-run intake on a brand-new instance"
        ),
        description=(
            "loam init-intake — the translate-in first-run intake. Runs "
            "loam's operating loop (infer -> propose -> verify -> learn) on a "
            "brand-new user: leads to ONE concrete stop/start thing, falls "
            "back gracefully when the user is stuck (describe-your-work -> "
            "mine-the-role -> opt-in deep role-research), proposes an "
            "inferred end-intent, confirms it before seeding, and ends on a "
            "person-specific leverage idea. Seeds the D-2 minimum prior "
            "(confirmed objective + openness-biased interaction-model at "
            "confidence:prior) into ~/.claude/ + the workspace .loam/ home. "
            "Idempotent: a re-run on an already-onboarded instance changes "
            "nothing."
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
    parser.add_argument(
        "--with-capability-ritual",
        action="store_true",
        help=(
            "Also run the existing six-question capability-activation ritual "
            "(language / channel / safety-profile / extractor / watch / "
            "auto-skill-capture) before the intake. Off by default so the "
            "intake stays the featherlight focus; `loam onboard` runs the "
            "capability ritual standalone."
        ),
    )
    parser.set_defaults(func=_cmd_init_intake)

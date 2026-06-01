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

"""``loam guards`` — the protection-pillar coverage-check verb.

The REAL production entry-point the ★ outcome-altitude AC (AC.FMG-S.1)
drives: load the catalogue, derive the live guard set from ground truth,
reconcile, and NAME the gaps. Registers through the unified loam CLI
dispatcher's ``loam.cli.subcommands`` entry-point group (sibling to
``loam audit`` / ``loam release`` / ``loam migrate``) — the same composition
``loam audit`` uses; zero new CLI plumbing (Lens 1).

    loam guards [--catalogue <path>] [--repo-root <path>]
                [--refresh [--out <path>]]

Exit code (FORK F-2 ruling): **0 with the gap report** — gaps are the normal,
honest reporting state, not an error; a non-zero default would punish honesty
by making every run "fail" until every known gap is closed. (The deferred
release-gate arm — FORK F-4 — would reserve non-zero; it is OUT of this
cycle's scope.)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .check import (
    companion_doc_path,
    render_companion_doc,
    render_report,
    run_coverage_check,
)
from .derive import find_repo_root


def build_guards_subcommand(sub: argparse._SubParsersAction) -> None:
    """Register the ``guards`` subcommand on *sub* (builder contract)."""
    p = sub.add_parser(
        "guards",
        help=(
            "report loam's protection-pillar coverage: every known way an "
            "AI betrays a user x loam's actual guard x default-on? x "
            "floor-vs-proportional, and NAME the gaps (floor-class failure "
            "modes with no default-on guard)"
        ),
        description=(
            "Load the failure-mode-guard catalogue, derive the live guard "
            "set from GROUND TRUTH (resolve each guard against the real "
            "tree, confirm release-gate membership), reconcile the two, and "
            "emit the coverage report + a distinct GAP section naming the "
            "floor-class failure modes guarded today only by persona "
            "discipline. The gaps are the actionable output — the check "
            "exits 0 even with gaps (gaps are the normal reporting state). "
            "--refresh regenerates the human-readable companion doc, "
            "composing on loam's existing recurring maintenance/pruning "
            "cadence (no net-new scheduler)."
        ),
    )
    p.add_argument(
        "--catalogue",
        type=Path,
        default=None,
        help=(
            "catalogue YAML path (default: the shipped "
            "framework/protection-matrix/data/failure-mode-guard-matrix.yaml)"
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="loam repo root override (default: auto-detected from the tree)",
    )
    p.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "regenerate the human-readable companion at "
            "docs/design/protection-matrix.md from the catalogue + the live "
            "coverage verdict (the recurring-maintenance refresh item)"
        ),
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "with --refresh: write the companion to this path instead of the "
            "default docs/design/protection-matrix.md"
        ),
    )
    p.set_defaults(func=dispatch)


def dispatch(args: argparse.Namespace) -> int:
    """Run ``loam guards``. Returns 0 (FORK F-2 — reporter, not a gate)."""
    report = run_coverage_check(
        catalogue_path=args.catalogue,
        repo_root=args.repo_root,
    )

    if args.refresh:
        root = args.repo_root or find_repo_root()
        out = args.out or companion_doc_path(root)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_companion_doc(report) + "\n", encoding="utf-8")
        print(
            f"loam guards: refreshed the protection-matrix companion at "
            f"{out} ({len(report.gaps)} floor-class gap(s) named)."
        )
        return 0

    print(render_report(report))
    return 0

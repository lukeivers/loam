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

"""``loam report`` — the user-facing privacy-safe bug-report verb (plan §6).

The deterministic / non-tech entry-point: a single named thing a
non-technical user can run to report a problem. Symmetric to ``loam recover``
(self-recovery's verb). Registered via the ``loam.cli.subcommands``
entry-point group, so it surfaces as ``loam report`` on the unified CLI.

Surface (all output is plain-language; ZERO internal vocabulary):

  loam report          — start a problem report. Asks a couple of plain
                         questions, shows what it would send, and either saves
                         the report on your own computer (default) or sends it
                         to the loam team after you approve each piece.

This verb makes NO LLM call and spawns NO Claude session
(``feedback_no_anthropic_api_key``). In a real interactive run the persona
conducts the interview + drives the review surface; this CLI is the
deterministic shell that, absent supplied answers, takes the safe default
(save locally — zero egress) so a bare ``loam report`` NEVER sends anything
without explicit per-item approval.
"""

from __future__ import annotations

import argparse
import platform
from pathlib import Path

from .bug_report import ReportInterview, run_bug_report


def _default_out_path() -> Path:
    return Path.home() / "loam-report.txt"


def _cmd_report(args: argparse.Namespace) -> int:
    """Run the bug-report flow. Default choice is the local-only fallback.

    A bare ``loam report`` (no interview answers, no ``--send``) takes the
    safe path: it saves a starter report on the user's own disk with ZERO
    egress and tells them where it is — never sends without explicit approval.
    The interactive interview + per-item review are conducted by the persona
    in conversation; this CLI is the deterministic, fail-safe shell.
    """
    interview = ReportInterview(
        what_doing=args.what_doing or "(not described)",
        expected=args.expected or "(not described)",
        happened=args.happened or "(not described)",
    )
    out_path = Path(args.out) if args.out else _default_out_path()

    # The CLI NEVER sends without an explicit --send AND a wired transport.
    # Absent that, it always lands on the local fallback (zero egress).
    outcome = run_bug_report(
        interview=interview,
        loam_version=args.loam_version or "unknown",
        os_name=platform.system() or "unknown",
        choice="local",
        out_path=out_path,
    )
    print(
        "No problem — I've saved your report on your own computer at "
        f"{outcome.local_path}.\n"
        "It's yours: open it, read it, send it whenever you like, or never. "
        "Nothing left your computer."
    )
    return 0


def _attach_report_actions(parser: argparse.ArgumentParser) -> None:
    """Attach the report flow onto *parser*.

    Shared by the standalone ``loam-report`` entry-point and the ``loam
    report`` subcommand so the surface is authored once.
    """
    parser.add_argument("--what-doing", dest="what_doing", default=None)
    parser.add_argument("--expected", dest="expected", default=None)
    parser.add_argument("--happened", dest="happened", default=None)
    parser.add_argument("--loam-version", dest="loam_version", default=None)
    parser.add_argument(
        "--out",
        dest="out",
        default=None,
        help="where to save the report on your computer",
    )
    parser.set_defaults(func=_cmd_report)


def build_report_subcommand(sub: "argparse._SubParsersAction") -> None:
    """Register the ``report`` subcommand on ``sub`` (M6a builder contract).

    Entry-point declaration in ``framework/egress-consent/pyproject.toml``:

        [project.entry-points."loam.cli.subcommands"]
        report = "loam.egress_consent.report_cli:build_report_subcommand"
    """
    report_parser = sub.add_parser(
        "report",
        help="report a problem safely — nothing leaves your computer unless "
        "you approve it",
        add_help=True,
    )
    _attach_report_actions(report_parser)


def main(argv: list[str] | None = None) -> int:
    """Standalone ``loam-report`` entry-point."""
    parser = argparse.ArgumentParser(
        prog="loam-report",
        description="Report a problem safely — nothing leaves your computer "
        "unless you approve it.",
    )
    _attach_report_actions(parser)
    args = parser.parse_args(argv)
    return args.func(args)

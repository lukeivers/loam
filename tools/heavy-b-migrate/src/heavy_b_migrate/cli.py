"""``heavy-b-migrate`` CLI entry.

Subcommands:

- ``run`` — invoke the phase runner (default: alpha + beta + gamma).
  Exits 0 on success; non-zero on phase-ordering error or runner
  failure. Honours ``--phases`` (comma-separated subset of α/β/γ;
  must be a contiguous prefix per the runner's enforcement).
- ``project`` — alias for ``run`` retained for symmetry with the
  research-§D.1 vocabulary; identical behaviour.
- ``verify-continuous`` — run the AC.D-mig.4 continuous-registration
  verifier inside an isolated tmpfs tracker. Exits 0 if the fixture
  amendment registers + source_commit propagates cleanly; non-zero
  with a structured diagnostic otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from heavy_b_migrate.runner import (
    PhaseOrderingError,
    VALID_PHASES,
    run_phases,
)
from heavy_b_migrate.trigger import TRACKER_DB_FILENAME
from heavy_b_migrate.verify import verify_continuous_registration


def _resolve_workspace(arg: Path | None) -> Path:
    if arg is not None:
        return arg.resolve()
    return Path.cwd().resolve()


def _cmd_run(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    tracker_db = (
        args.tracker_db.resolve()
        if args.tracker_db is not None
        else workspace_root / TRACKER_DB_FILENAME
    )
    phases: tuple[str, ...] = tuple(args.phases) if args.phases else VALID_PHASES
    try:
        report = run_phases(workspace_root, tracker_db, phases=phases)
    except PhaseOrderingError as exc:
        sys.stderr.write(f"phase-ordering error: {exc}\n")
        return 2
    payload: dict = {"phases_run": list(report.phases_run)}
    if report.alpha is not None:
        payload["alpha"] = {
            "created": list(report.alpha.created),
            "skipped": list(report.alpha.skipped),
            "missing_proposal": list(report.alpha.missing_proposal),
        }
    if report.beta is not None:
        payload["beta"] = {
            "created_count": len(report.beta.created),
            "skipped_count": len(report.beta.skipped),
            "placeholders": list(report.beta.placeholders_seeded),
        }
    if report.gamma is not None:
        payload["gamma"] = {
            "created_count": len(report.gamma.created),
            "skipped_count": len(report.gamma.skipped),
            "placeholders": list(report.gamma.placeholders_seeded),
            "plans_visited": report.gamma.plans_visited,
        }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def _cmd_verify(_args: argparse.Namespace) -> int:
    report = verify_continuous_registration()
    payload = {
        "registered_count": report.registered_count,
        "source_commit_updated_count": report.source_commit_updated_count,
        "fixture_amendment_id": report.fixture_amendment_id,
        "contributor_surfaces_record": report.contributor_surfaces_record,
        "failure_reason": report.failure_reason,
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if report.failure_reason is None else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="heavy-b-migrate",
        description=(
            "Heavy-B Phase α/β/γ data-migration tooling. Dev-discipline; "
            "composes against #38/#39/#40 + pos-amend tracker integration."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser(
        "run",
        help="Run the phase migration (default: α + β + γ).",
    )
    p_run.add_argument("--workspace", type=Path, default=None)
    p_run.add_argument(
        "--tracker-db", type=Path, default=None,
        help=(
            "Override the tracker DB path. Default: "
            "<workspace>/objective_tracker.sqlite (mirrors #39's seed path)."
        ),
    )
    p_run.add_argument(
        "--phases",
        nargs="+",
        choices=list(VALID_PHASES),
        default=None,
        help="Subset of phases to run; must be contiguous prefix of α/β/γ.",
    )
    p_run.set_defaults(func=_cmd_run)

    p_project = sub.add_parser(
        "project",
        help=(
            "Alias for `run` — research-§D.1 vocabulary; identical "
            "behaviour."
        ),
    )
    p_project.add_argument("--workspace", type=Path, default=None)
    p_project.add_argument("--tracker-db", type=Path, default=None)
    p_project.add_argument(
        "--phases", nargs="+", choices=list(VALID_PHASES), default=None,
    )
    p_project.set_defaults(func=_cmd_run)

    p_verify = sub.add_parser(
        "verify-continuous",
        help="AC.D-mig.4 continuous-registration end-to-end verifier.",
    )
    p_verify.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

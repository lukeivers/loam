"""CLI builder for ``loam odd-extract``.

Per AC.OREK.2 — registered with the unified ``loam`` CLI via the
``loam.cli.subcommands`` entry-point group (declared in pyproject.toml).
``loam_cli.cli.main`` discovers this builder + invokes it with the
parent argparse subparsers handle.

Builder contract (per loam_cli convention):

    def build_odd_extract_subcommand(
        sub: argparse._SubParsersAction,
    ) -> None:
        ...

Sets ``func`` on the leaf parser via ``set_defaults`` so ``main``
dispatches via ``args.func(args)``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .analyze import analyze_repo
from .budget import (
    budget_from_cents,
    default_budget,
    enforce_budget,
    estimate_for_extraction,
)
from .errors import BudgetExceededError, OddExtractorError
from .generate import generate_raw_acs
from .init import init_extraction
from .observability import write_audit_entry
from .spec import ExtractionConfig
from .state import compute_repo_id, extraction_dir, load_state
from .verify import verify_contract


_EXIT_OK = 0
_EXIT_ERR = 2
_EXIT_BUDGET = 3


# ---- helpers --------------------------------------------------------


def _resolve_workspace_root(arg: Path | None) -> Path:
    return (arg if arg is not None else Path.cwd()).expanduser().resolve()


def _resolve_repo_path(arg: Path) -> Path:
    p = arg.expanduser().resolve()
    if not p.exists():
        raise OddExtractorError(f"repo path does not exist: {p}")
    return p


def _print_estimate(estimate, *, json_mode: bool) -> None:
    payload = {
        "estimated_money_cents": estimate.estimated_money_cents,
        "estimated_tokens": estimate.estimated_tokens,
        "estimated_time_seconds": estimate.estimated_time_seconds,
        "confidence_band": estimate.confidence_band.value,
        "reason": estimate.reason,
    }
    if json_mode:
        print(json.dumps({"estimate": payload}, indent=2))
    else:
        print("Estimate:")
        print(f"  estimated_money_cents:  {payload['estimated_money_cents']}")
        print(f"  estimated_tokens:       {payload['estimated_tokens']}")
        print(f"  estimated_time_seconds: {payload['estimated_time_seconds']}")
        print(f"  confidence_band:        {payload['confidence_band']}")
        if payload["reason"]:
            print(f"  reason:                 {payload['reason']}")


# ---- subcommand handlers -------------------------------------------


def _cmd_extract(args: argparse.Namespace) -> int:
    """Default verb — runs the full four-stage workflow."""
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root)

        # Budget envelope
        if args.budget_cents is not None:
            envelope = budget_from_cents(args.budget_cents)
        else:
            envelope = default_budget()

        # Pre-extraction estimate (always)
        repo_id = compute_repo_id(repo_path)
        scope_id = f"odd-extract:{repo_id}"
        estimate = estimate_for_extraction(
            scope_id=scope_id,
            recent_actuals=[],  # Cycle 1: cold-start always.
        )
        _print_estimate(estimate, json_mode=args.json)

        # Live + budget check
        dry_run = not args.live
        if args.live:
            try:
                enforce_budget(
                    estimate=estimate,
                    envelope=envelope,
                    override=args.budget_override,
                )
            except BudgetExceededError as exc:
                print(f"loam odd-extract: {exc}", file=sys.stderr)
                # If we have an extraction directory in flight, log
                # the rejection. Otherwise just exit.
                ext_dir = extraction_dir(workspace_root, repo_id)
                if ext_dir.exists():
                    write_audit_entry(
                        ext_dir,
                        event_kind="extraction_failed",
                        extraction_id=repo_id,
                        notes=f"budget_exceeded: {exc}",
                    )
                return _EXIT_BUDGET

        if args.live and args.budget_override:
            # Audit-log the override BEFORE any extraction work.
            ext_dir = extraction_dir(workspace_root, repo_id)
            ext_dir.mkdir(parents=True, exist_ok=True)
            write_audit_entry(
                ext_dir,
                event_kind="budget_override",
                extraction_id=repo_id,
                estimate={
                    "estimated_money_cents": estimate.estimated_money_cents,
                    "confidence_band": estimate.confidence_band.value,
                },
                notes=(
                    f"--budget-override; envelope hard_cap_cents="
                    f"{envelope.hard_cap_money_cents}"
                ),
            )

        # Per-stage selection (None = run all four)
        target_stage: str | None = args.stage

        config: ExtractionConfig | None = None

        if target_stage in (None, "init"):
            config = init_extraction(
                repo_path=repo_path,
                workspace_root=workspace_root,
                budget=envelope,
                dry_run=dry_run,
            )

        if target_stage in (None, "analyze"):
            if config is None:
                config = _load_config(workspace_root, repo_id)
            plan = analyze_repo(config=config)

        if target_stage in (None, "generate"):
            if config is None:
                config = _load_config(workspace_root, repo_id)
            plan = _load_plan(workspace_root, repo_id)
            raw = generate_raw_acs(config=config, plan=plan)

        if target_stage in (None, "verify"):
            if config is None:
                config = _load_config(workspace_root, repo_id)
            raw = _load_raw_acs(workspace_root, repo_id)
            draft = verify_contract(config=config, raw=raw)
            print(f"Contract draft: {draft.markdown_path}")
            print(f"Sidecar:        {draft.sidecar_path}")
            print(f"AC count:       {draft.ac_count}")
            print(f"Unhandled:      {draft.unhandled_count}")

        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract: {exc}", file=sys.stderr)
        return _EXIT_ERR


def _cmd_status(args: argparse.Namespace) -> int:
    """Report extraction status without running."""
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root)
        repo_id = compute_repo_id(repo_path)
        ext_dir = extraction_dir(workspace_root, repo_id)
        state = load_state(ext_dir)
        if state is None:
            print(f"No prior extraction at {ext_dir}")
            return _EXIT_OK
        payload = {
            "extraction_id": state.extraction_id,
            "repo_path": state.repo_path,
            "workspace_root": state.workspace_root,
            "init_complete": state.init_complete,
            "analyze_complete": state.analyze_complete,
            "generate_complete": state.generate_complete,
            "verify_complete": state.verify_complete,
            "all_stages_complete": state.all_stages_complete,
            "last_updated_at": state.last_updated_at,
            "artefacts": state.artefacts,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Extraction: {state.extraction_id}")
            print(f"  repo_path:           {state.repo_path}")
            print(f"  workspace_root:      {state.workspace_root}")
            print(f"  init_complete:       {state.init_complete}")
            print(f"  analyze_complete:    {state.analyze_complete}")
            print(f"  generate_complete:   {state.generate_complete}")
            print(f"  verify_complete:     {state.verify_complete}")
            print(f"  all_stages_complete: {state.all_stages_complete}")
            print(f"  last_updated_at:     {state.last_updated_at}")
        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract status: {exc}", file=sys.stderr)
        return _EXIT_ERR


def _cmd_resume(args: argparse.Namespace) -> int:
    """Resume an interrupted extraction.

    Cycle 1 stub-shape per F2 RF gap #5: since extractions are nearly
    free in dry-run mode, "resume" reads the state and either reports
    "already complete" or re-runs the stages that haven't completed.
    """
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root)
        repo_id = compute_repo_id(repo_path)
        ext_dir = extraction_dir(workspace_root, repo_id)
        state = load_state(ext_dir)
        if state is None:
            print(
                f"No prior extraction at {ext_dir} — nothing to resume."
            )
            return _EXIT_OK
        if state.all_stages_complete:
            print(
                f"Extraction {state.extraction_id} already complete; "
                "nothing to resume."
            )
            return _EXIT_OK
        # Re-run pending stages by delegating to _cmd_extract with
        # the original config (re-load from config.yaml).
        config = _load_config(workspace_root, repo_id)
        if not state.analyze_complete:
            analyze_repo(config=config)
        if not state.generate_complete:
            plan = _load_plan(workspace_root, repo_id)
            generate_raw_acs(config=config, plan=plan)
        if not state.verify_complete:
            raw = _load_raw_acs(workspace_root, repo_id)
            verify_contract(config=config, raw=raw)
        print(f"Resumed extraction {state.extraction_id} to completion.")
        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract resume: {exc}", file=sys.stderr)
        return _EXIT_ERR


# ---- artefact loaders ----------------------------------------------


def _load_config(workspace_root: Path, repo_id: str) -> ExtractionConfig:
    ext_dir = extraction_dir(workspace_root, repo_id)
    config_path = ext_dir / "config.yaml"
    if not config_path.exists():
        raise OddExtractorError(
            f"config.yaml not found at {config_path} — run 'init' first"
        )
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return ExtractionConfig.model_validate(data)


def _load_plan(workspace_root: Path, repo_id: str):
    from .spec import AnalysisPlan

    ext_dir = extraction_dir(workspace_root, repo_id)
    plan_path = ext_dir / "plan.yaml"
    if not plan_path.exists():
        raise OddExtractorError(
            f"plan.yaml not found at {plan_path} — run 'analyze' first"
        )
    data = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    return AnalysisPlan.model_validate(data)


def _load_raw_acs(workspace_root: Path, repo_id: str):
    from .spec import RawACs

    ext_dir = extraction_dir(workspace_root, repo_id)
    raw_path = ext_dir / "raw-acs.yaml"
    if not raw_path.exists():
        raise OddExtractorError(
            f"raw-acs.yaml not found at {raw_path} — run 'generate' first"
        )
    data = yaml.safe_load(raw_path.read_text(encoding="utf-8")) or {}
    return RawACs.model_validate(data)


# ---- subcommand builder --------------------------------------------


def _add_workspace_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help=(
            "workspace root (default: cwd). Per-extraction state "
            "lives under <workspace>/.loam/extractions/<repo-id>/."
        ),
    )


def _cmd_dispatch(args: argparse.Namespace) -> int:
    """Dispatch handler for ``loam odd-extract``.

    Routes between extract / status / resume based on the
    ``--status`` / ``--resume`` flags. Default action is extract.
    """
    if getattr(args, "status", False):
        return _cmd_status(args)
    if getattr(args, "resume", False):
        return _cmd_resume(args)
    return _cmd_extract(args)


def build_odd_extract_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the ``loam odd-extract ...`` subcommand surface.

    Per AC.OREK.2 — single-verb subcommand. ``loam odd-extract
    <repo>`` runs the four-stage workflow; ``--status`` reports;
    ``--resume`` continues a paused run. Dry-run by default;
    ``--live`` is opt-in; ``--budget-cents N`` configures the
    envelope; ``--budget-override`` opts out of the foreign-codebase
    ceiling check; ``--workspace-root`` overrides the cwd-derived
    workspace.

    Single-verb shape (no sub-verbs) avoids argparse ambiguity
    between a positional ``repo_path`` and a subparser dest.
    """
    odd_parser = sub.add_parser(
        "odd-extract",
        help=(
            "ODD reverse-engineering — read a target repo and emit a "
            "confidence-banded contract draft. Cycle 1: scaffold."
        ),
        description=(
            "loam odd-extract ... — Cartographer-style ODD reverse-"
            "engineering. v0.1.8 Cycle 1 ships the four-stage workflow "
            "shape (init/analyze/generate/verify) + language-adapter "
            "registry (zero adapters) + dry-run cost estimate + "
            "foreign-codebase budget envelope."
        ),
    )
    odd_parser.add_argument(
        "repo_path",
        type=Path,
        help="path to the target repo to extract from",
    )
    odd_parser.add_argument(
        "--live",
        action="store_true",
        help="run live (default: dry-run, per Decision D)",
    )
    odd_parser.add_argument(
        "--budget-cents",
        type=int,
        default=None,
        help=(
            "override the foreign-codebase budget ceiling (cents). "
            f"Default: {1000} hard / {500} soft (AC.OREK.6)."
        ),
    )
    odd_parser.add_argument(
        "--budget-override",
        action="store_true",
        help=(
            "opt out of the budget ceiling check; allows live runs "
            "that exceed the envelope (audit-logged)."
        ),
    )
    odd_parser.add_argument(
        "--stage",
        choices=("init", "analyze", "generate", "verify"),
        default=None,
        help=(
            "run only the named stage (default: all four). Useful "
            "for testing + scriptability."
        ),
    )
    odd_parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON output where applicable.",
    )
    odd_parser.add_argument(
        "--status",
        action="store_true",
        help=(
            "report extraction status without running. Reads "
            "<workspace>/.loam/extractions/<repo-id>/state.yaml."
        ),
    )
    odd_parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "resume an interrupted extraction (re-runs only the "
            "stages that did not complete)."
        ),
    )
    _add_workspace_root_arg(odd_parser)
    odd_parser.set_defaults(func=_cmd_dispatch)


# ---- direct-invocation main (for tests + ad-hoc) -------------------


def main(argv: list[str] | None = None) -> int:
    """Stand-alone entry point that mirrors the unified-CLI dispatch.

    Tests can import this and call directly without going through
    the unified ``loam`` binary. The unified binary's ``loam
    odd-extract ...`` route lands at the same handlers via the
    builder above.

    Note: the standalone form prepends ``odd-extract`` so tests
    can pass argv as ``[<repo-path>, ...]`` matching the unified
    CLI shape.
    """
    parser = argparse.ArgumentParser(prog="loam-odd-extract")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(["odd-extract", *argv])
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

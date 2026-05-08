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


def _resolve_workspace_root(arg: Path | None, repo_path: Path) -> Path:
    """Resolve the workspace-root from --workspace-root or default.

    Per v0.2.5 corrective C6 (HARD-smoke F-DESIGN-3): the default is
    the target ``<repo>`` positional arg, NOT ``Path.cwd()``. The
    cwd-default semantics surprised callers running
    ``loam odd-extract <some-other-repo>`` from inside a loam tree —
    extraction artefacts landed in the loam tree rather than under
    the target. Pre-C6 default was ``Path.cwd()``; existing tests
    pass ``--workspace-root`` explicitly so the default-shift is
    backward-compatible against the test surface.
    """
    if arg is not None:
        return arg.expanduser().resolve()
    return repo_path.expanduser().resolve()


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
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)

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

        # Per v0.2.5 corrective C1 (HARD-smoke RED finding F1) +
        # corrective C4-pivot: construct the default subscription-routed
        # synthesis client when ``--live`` is set so the synthesis pass
        # + backing-map population actually run end-to-end through the
        # CLI surface. Pre-C1 the CLI silently fell into
        # ``_empty_synthesis_result`` with ``model_id="(none)"`` even
        # with ``--live`` because it never threaded a client into
        # ``generate_raw_acs``. Pre-C4-pivot the constructed client was
        # an ``anthropic.Anthropic()`` instance reading
        # ``ANTHROPIC_API_KEY``; post-C4-pivot the client is a
        # :class:`ClaudePrintAnthropicShimClient` that routes every call
        # through ``claude -p`` against the user's Claude Max
        # subscription via OAuth keychain — NO API key.
        llm_client: Any | None = None
        if args.live and target_stage in (None, "generate"):
            from .claude_print_synthesis_client import (
                build_default_synthesis_client,
            )

            # Per v0.2.5.1 AC.V025-1.2 (F-TIMEOUT closure): thread the
            # ``--synthesis-timeout`` operator override into the
            # subscription-routed shim. ``None`` (no flag passed)
            # accepts the shim's own default (600s post-corrective).
            synthesis_timeout: float | None = getattr(
                args, "synthesis_timeout", None
            )
            try:
                llm_client = build_default_synthesis_client(
                    timeout_seconds=synthesis_timeout,
                )
            except OddExtractorError:
                # ``StageError`` / ``ClaudeBinaryMissingError`` from
                # ``build_default_synthesis_client`` (claude binary
                # missing); the surrounding ``except OddExtractorError``
                # catch below converts it to actionable stderr + exit 2,
                # NOT a Python traceback.
                raise

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
            raw = generate_raw_acs(
                config=config,
                plan=plan,
                anthropic_client=llm_client,
                synthesis_required=args.live,
            )

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
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)
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
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)
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
            "workspace root (default: target <repo> positional arg). "
            "Per-extraction state lives under "
            "<workspace>/.loam/extractions/<repo-id>/. Per v0.2.5 "
            "corrective C6: the default tracks the target repo so "
            "artefacts land alongside it, not in the invoker's cwd."
        ),
    )


def _cmd_dispatch(args: argparse.Namespace) -> int:
    """Dispatch handler for ``loam odd-extract``.

    Routes between extract / status / resume / ratify / incremental
    based on the ``--status`` / ``--resume`` / ``--ratify`` /
    ``--incremental`` flags. Default action is extract.

    The ratify-flag form (``loam odd-extract <draft-md-path> --ratify``)
    treats the positional ``repo_path`` as a contract-draft markdown
    path; the ``ratify`` sub-verb in :func:`build_odd_extract_subcommand`
    is the canonical entry. Per AC.BANDS.4 + plan-doc §5 Surface #3.

    The incremental-flag form (``loam odd-extract <repo> --incremental``)
    is v0.2.0 Cycle 1 AC.WATCH.1 — reads the prior contract sidecar,
    classifies evidence, generates proposals, enqueues domain-batched
    PM questions.
    """
    if getattr(args, "status", False):
        return _cmd_status(args)
    if getattr(args, "resume", False):
        return _cmd_resume(args)
    if getattr(args, "ratify", False):
        return _cmd_ratify(args)
    if getattr(args, "incremental", False):
        return _cmd_incremental(args)
    if getattr(args, "interview", False):
        return _cmd_interview(args)
    if getattr(args, "gaps", False):
        return _cmd_gaps(args)
    if getattr(args, "build_next", False):
        return _cmd_build_next(args)
    return _cmd_extract(args)


def _cmd_interview(args: argparse.Namespace) -> int:
    """Handle ``loam odd-extract <workspace> --interview``.

    Per v0.2.4 Cycle 1 AC.COMPINT.4 + AC.COMPINT.11 — runs the
    completeness interview against the prior extraction's
    objectives.yaml. Loads existing objectives → optionally calls
    flag_missing_objectives → runs run_interview → persists augmented
    set at <workspace>/.loam/extractions/<repo-id>/augmented-
    objectives.yaml.

    Default response producer is a stdin-based interactive prompt;
    tests inject via direct call to :func:`loam_odd_extractor.run_interview`.
    """
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)
        repo_id = compute_repo_id(repo_path)
        ext_dir = extraction_dir(workspace_root, repo_id)
        if not ext_dir.exists():
            raise OddExtractorError(
                f"no prior extraction at {ext_dir} — run "
                "`loam odd-extract <repo>` first to produce "
                "objectives.yaml + multi-source bundle."
            )

        # Load extracted objectives from objectives.yaml (v0.2.3 output).
        objectives_path = ext_dir / "objectives.yaml"
        if not objectives_path.exists():
            raise OddExtractorError(
                f"no objectives.yaml at {objectives_path} — v0.2.3 "
                "synthesis pass has not been run."
            )
        from .spec import (
            AugmentedObjectiveSet,
            Objective,
        )
        import datetime as _dt
        raw = yaml.safe_load(objectives_path.read_text(encoding="utf-8")) or {}
        if isinstance(raw, dict):
            objs_raw = raw.get("objectives") or []
        elif isinstance(raw, list):
            objs_raw = raw
        else:
            objs_raw = []
        objectives = [Objective.model_validate(d) for d in objs_raw]

        # Resolve PM handle.
        from .interview import resolve_pm_handle, run_interview
        pm_handle = resolve_pm_handle(workspace_root, args.pm_name)

        from loam.per_project_pm import PMRuntime
        pm_runtime = PMRuntime.from_workspace(workspace_root, pm_handle)

        flagged: list = []  # CLI-time: skip LLM-judge when --no-llm; tests use direct call.
        baseline = AugmentedObjectiveSet(
            extraction_id=repo_id,
            augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
            interview_audit_path=str(ext_dir / "audit-log"),
            objectives=objectives,
        )

        def _stdin_producer(sq) -> str:  # pragma: no cover (interactive)
            text = getattr(sq, "text", "")
            print(f"\n{text}\n")
            print("> ", end="", flush=True)
            try:
                return input()
            except EOFError:
                return ""

        result = run_interview(
            workspace_root=workspace_root,
            extraction_dir_=ext_dir,
            extraction_id=repo_id,
            pm=pm_runtime,
            augmented_set_in=baseline,
            flagged_missing=flagged,
            response_producer=_stdin_producer,
        )

        if args.json:
            print(json.dumps({
                "augmented_set_path": str(ext_dir / "augmented-objectives.yaml"),
                "objective_count_post": len(result.objectives),
                "extraction_id": result.extraction_id,
            }, indent=2))
        else:
            print(f"Completeness interview complete for {repo_id}.")
            print(f"  Augmented set:    {ext_dir / 'augmented-objectives.yaml'}")
            print(f"  Objective count:  {len(result.objectives)}")
        return _EXIT_OK
    except OddExtractorError as exc:
        print(
            f"loam odd-extract --interview: {exc}", file=sys.stderr
        )
        return _EXIT_ERR


def _cmd_gaps(args: argparse.Namespace) -> int:
    """Handle ``loam odd-extract <repo> --gaps``.

    Per v0.2.4 Cycle 2 AC.GAPAN.7 — runs the gap analysis against
    the prior extraction's augmented-objectives.yaml + backing-map.yaml
    + evidence-rows.yaml; writes gap-inventory.yaml; emits stdout
    summary.

    Halts with exit code 2 + actionable message when any predecessor
    artefact is missing.
    """
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)
        repo_id = compute_repo_id(repo_path)
        ext_dir = extraction_dir(workspace_root, repo_id)
        if not ext_dir.exists():
            raise OddExtractorError(
                f"no prior extraction at {ext_dir} — run "
                "`loam odd-extract <repo> --interview` first to "
                "produce augmented-objectives.yaml."
            )

        # Predecessor: augmented-objectives.yaml (Cycle 1 output).
        from .interview import load_augmented_objectives

        augmented = load_augmented_objectives(ext_dir)
        if augmented is None:
            raise OddExtractorError(
                f"no augmented-objectives.yaml at {ext_dir} — run "
                "`loam odd-extract <repo> --interview` first to "
                "produce the augmented objective set."
            )

        # Predecessor: backing-map.yaml (v0.2.3 substrate).
        from .backing_map import load_backing_map

        bm = load_backing_map(ext_dir)
        if bm is None:
            raise OddExtractorError(
                f"no backing-map.yaml at {ext_dir} — run "
                "`loam odd-extract <repo>` first to produce the "
                "backing-map."
            )

        # Predecessor: evidence-rows.yaml (v0.2.3 substrate).
        evidence_path = ext_dir / "evidence-rows.yaml"
        if not evidence_path.exists():
            raise OddExtractorError(
                f"no evidence-rows.yaml at {evidence_path} — run "
                "`loam odd-extract <repo>` first to produce evidence "
                "rows."
            )
        evidence_payload = (
            yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
            or {}
        )
        evidence_rows = (
            evidence_payload.get("acs", [])
            if isinstance(evidence_payload, dict)
            else []
        )
        if not isinstance(evidence_rows, list):
            evidence_rows = []

        from .gap_analysis import (
            analyze_gaps,
            emit_end_audit,
            emit_persisted_audit,
            emit_start_audit,
            render_stdout_summary,
            save_gap_inventory,
        )
        import time as _time

        # Audit: start.
        emit_start_audit(
            ext_dir,
            extraction_id=repo_id,
            augmented_objective_count=len(augmented.objectives),
            backing_map_objective_count=len(bm.entries),
            evidence_row_count=len(evidence_rows),
        )

        t0 = _time.monotonic()
        inventory = analyze_gaps(
            augmented_objectives=augmented,
            backing_map=bm,
            evidence_rows=evidence_rows,
            extraction_id=repo_id,
            audit_path=str(ext_dir / "audit-log"),
        )

        # Persist (idempotent on no-change).
        path, wrote = save_gap_inventory(inventory, ext_dir)

        # Audit: persisted.
        emit_persisted_audit(
            ext_dir,
            extraction_id=repo_id,
            inventory=inventory,
            gap_inventory_path_str=str(path),
        )

        # Audit: end.
        duration_ms = int((_time.monotonic() - t0) * 1000)
        emit_end_audit(
            ext_dir,
            extraction_id=repo_id,
            duration_ms=duration_ms,
        )

        if args.json:
            print(
                json.dumps(
                    {
                        "extraction_id": repo_id,
                        "gap_inventory_path": str(path),
                        "wrote": wrote,
                        "summary": inventory.summary.model_dump(),
                    },
                    indent=2,
                )
            )
        else:
            print(render_stdout_summary(inventory))
            print()
            print(f"  Inventory:  {path}")
            print(f"  Wrote:      {wrote} (False = no-change skip)")
        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract --gaps: {exc}", file=sys.stderr)
        return _EXIT_ERR


def _cmd_build_next(args: argparse.Namespace) -> int:
    """Handle ``loam odd-extract <repo> --build-next``.

    Per v0.2.4 Cycle 3 AC.PERSONA-PULL.1 — runs the build-next
    ranking against the prior extraction's gap-inventory.yaml +
    augmented-objectives.yaml + (optional) onboarding-survey context.
    Persists build-next.yaml + build-next.md; emits stdout summary +
    audit-log entries.

    Persona invokes via `loam odd-extract <repo> --build-next` on
    user-question-trigger such as 'what should I build next?'.

    Halts with exit code 2 + actionable message when any predecessor
    artefact is missing.
    """
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)
        repo_id = compute_repo_id(repo_path)
        ext_dir = extraction_dir(workspace_root, repo_id)
        if not ext_dir.exists():
            raise OddExtractorError(
                f"no prior extraction at {ext_dir} — run "
                "`loam odd-extract <repo> --gaps` first to produce "
                "gap-inventory.yaml + augmented-objectives.yaml."
            )

        # Predecessor: gap-inventory.yaml (Cycle 2 output).
        from .gap_analysis import load_gap_inventory

        inventory = load_gap_inventory(ext_dir)
        if inventory is None:
            raise OddExtractorError(
                f"no gap-inventory.yaml at {ext_dir} — run "
                "`loam odd-extract <repo> --gaps` first to produce "
                "the gap inventory."
            )

        # Predecessor: augmented-objectives.yaml (Cycle 1 output).
        from .interview import load_augmented_objectives

        augmented = load_augmented_objectives(ext_dir)
        if augmented is None:
            raise OddExtractorError(
                f"no augmented-objectives.yaml at {ext_dir} — run "
                "`loam odd-extract <repo> --interview` first to "
                "produce the augmented objective set."
            )

        # Optional: survey-context via lazy-imported multi_source helper.
        from .multi_source import _read_user_survey

        survey_bundle = _read_user_survey(repo_path, workspace_root)
        survey_text: str | None = None
        if survey_bundle is not None:
            survey_text = survey_bundle.get("raw_text") or None

        # Optional: interview-added objective-ids from audit-log.
        from .build_next import (
            DEFAULT_LIMIT,
            DEFAULT_LLM_JUDGE_BUDGET_CENTS,
            _read_interview_added_objective_ids,
            check_build_next_cost_band,
            emit_build_next_end_audit,
            emit_build_next_persisted_audit,
            emit_build_next_start_audit,
            estimate_build_next_cost_cents,
            render_stdout_summary as _bn_stdout_summary,
            save_recommendation,
            score_candidates,
        )
        from .gap_analysis import render_stdout_summary as _gap_stdout_summary
        import time as _time

        audit_dir = ext_dir / "audit-log"
        interview_ids = _read_interview_added_objective_ids(audit_dir)
        survey_present = bool(survey_text)

        # Pre-flight cost-band check (AC.BLDNXT.7).
        budget_cents = (
            float(args.budget_cents)
            if getattr(args, "budget_cents", None) is not None
            else float(DEFAULT_LLM_JUDGE_BUDGET_CENTS)
        )
        estimated = estimate_build_next_cost_cents(
            gap_count=len(inventory.gaps),
            survey_present=survey_present,
        )
        check_build_next_cost_band(
            estimated_cost_cents=estimated,
            budget_cents=budget_cents,
        )

        # Audit: start.
        emit_build_next_start_audit(
            ext_dir,
            extraction_id=repo_id,
            gap_count=len(inventory.gaps),
            survey_present=survey_present,
            interview_priority_count=len(interview_ids),
            llm_judge_budget_cents=int(budget_cents),
        )

        limit = int(getattr(args, "limit", None) or DEFAULT_LIMIT)
        t0 = _time.monotonic()

        # Ranking — anthropic_client=None means deterministic only
        # (no LLM-judge tier). The CLI handler does NOT construct a
        # real Anthropic client; tests inject via direct call to
        # :func:`score_candidates`.
        rec = score_candidates(
            gap_inventory=inventory,
            augmented_objectives=augmented,
            survey_text=survey_text,
            extraction_id=repo_id,
            audit_path=str(audit_dir),
            limit=limit,
            interview_added_objective_ids=interview_ids,
            anthropic_client=None,
        )

        # Inventory summary text — for the markdown header.
        inv_summary = _gap_stdout_summary(inventory)
        yaml_p, md_p, wrote = save_recommendation(
            rec, ext_dir, inventory_summary_text=inv_summary
        )

        # Audit: persisted.
        emit_build_next_persisted_audit(
            ext_dir,
            extraction_id=repo_id,
            rec=rec,
            build_next_md_path_str=str(md_p),
            build_next_yaml_path_str=str(yaml_p),
        )

        # Audit: end.
        duration_ms = int((_time.monotonic() - t0) * 1000)
        emit_build_next_end_audit(
            ext_dir,
            extraction_id=repo_id,
            duration_ms=duration_ms,
            total_cost_cents=0.0,
        )

        if args.json:
            print(
                json.dumps(
                    {
                        "extraction_id": repo_id,
                        "build_next_yaml_path": str(yaml_p),
                        "build_next_md_path": str(md_p),
                        "wrote": wrote,
                        "candidate_count": len(rec.candidates),
                        "truncated_count": rec.truncated_count,
                        "llm_judge_invocations": rec.llm_judge_invocations,
                        "degenerate_survey": rec.degenerate_survey,
                    },
                    indent=2,
                )
            )
        else:
            print(_bn_stdout_summary(rec))
            print()
            print(f"  Recommendation YAML:  {yaml_p}")
            print(f"  Recommendation MD:    {md_p}")
            print(f"  Wrote:                {wrote} (False = no-change skip)")
        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract --build-next: {exc}", file=sys.stderr)
        return _EXIT_ERR


def _cmd_incremental(args: argparse.Namespace) -> int:
    """Handle ``loam odd-extract <repo> --incremental``.

    Per AC.WATCH.1 (v0.2.0 Cycle 1) — invokes
    :func:`loam_odd_extractor.incremental.run_incremental` against
    the resolved (repo_path, workspace_root) pair; optionally
    composes through :class:`loam.per_project_pm.PMRuntime` if
    ``--pm-name`` is supplied.

    Exit codes:

    - ``0`` — success (proposals enqueued OR no drift detected).
    - ``2`` — :class:`OddExtractorError` (incl. ContractNotFoundError,
      IncrementalRefusedError).
    - ``3`` — :class:`BudgetExceededError` (existing budget envelope
      inherited; not currently exercised by Cycle 1's path).
    """
    try:
        repo_path = _resolve_repo_path(args.repo_path)
        workspace_root = _resolve_workspace_root(args.workspace_root, repo_path)

        # Optionally resolve PM. Without --pm-name, the watch runs
        # without enqueueing through PM; useful for dry-runs +
        # tests.
        pm_runtime = None
        pm_handle: str | None = args.pm_name
        if pm_handle:
            try:
                from loam.per_project_pm import PMRuntime
            except ImportError as exc:
                raise OddExtractorError(
                    "loam.per_project_pm not importable; install "
                    "loam-per-project-pm to use the incremental "
                    f"workflow with --pm-name ({exc})"
                ) from exc
            pm_runtime = PMRuntime.from_workspace(
                workspace_root, pm_handle
            )

        from .incremental import run_incremental

        # `--live` opts into PM enqueue (mirrors full-mode
        # behaviour). Default = dry-run; production-stake forces
        # dry-run regardless.
        explicit_dry_run = not args.live

        result = run_incremental(
            repo_path=repo_path,
            workspace_root=workspace_root,
            pm_runtime=pm_runtime,
            pm_handle=pm_handle,
            invocation_source=args.invocation_source,
            dry_run=explicit_dry_run,
        )

        if args.json:
            print(json.dumps(result.to_json_dict(), indent=2))
        else:
            print(f"Incremental watch run for {result.extraction_id}")
            print(f"  Summary: {result.summary_line()}")
            print(
                f"  Safety profile:    {result.safety_profile} "
                f"(dry_run={result.dry_run})"
            )
            print(f"  Prior repo SHA:    {result.prior_contract_sha}")
            print(f"  Current repo SHA:  {result.current_repo_sha}")
            print(
                f"  PM enqueued:       "
                f"{result.enqueue_result.enqueued_count} "
                f"domain-batches"
            )
            if result.enqueue_result.skipped_count:
                print(
                    f"  PM skipped (dup):  "
                    f"{result.enqueue_result.skipped_count} "
                    f"domain-batches"
                )
            print(
                f"  Audit-log entries written: "
                f"{result.audit_log_entries_written}"
            )
        return _EXIT_OK
    except OddExtractorError as exc:
        print(
            f"loam odd-extract --incremental: {exc}", file=sys.stderr
        )
        return _EXIT_ERR


def _cmd_ratify(args: argparse.Namespace) -> int:
    """Handle ``loam odd-extract <contract-draft-md> --ratify``.

    Per AC.BANDS.4 — loads the contract-draft + sidecar YAML;
    constructs the BandedAC list; resolves the named PM via
    PMRuntime; calls enqueue_ratification_batch; reports the count
    of pending decisions + the next surfaced question (if PM has a
    decision policy that surfaces immediately).

    Per plan-doc §5 Surface #7 — the CLI handler does the parsing +
    constructs the BandedAC list; the helper consumes typed objects.
    """
    try:
        # Treat repo_path as the contract-draft markdown path.
        draft_md_path = args.repo_path.expanduser().resolve()
        if not draft_md_path.exists():
            raise OddExtractorError(
                f"contract-draft path does not exist: {draft_md_path}"
            )
        # Sidecar — same basename, .yaml extension.
        sidecar_path = draft_md_path.with_suffix(".yaml")
        if not sidecar_path.exists():
            raise OddExtractorError(
                f"contract-draft sidecar (.yaml) not found at "
                f"{sidecar_path}"
            )

        # Load sidecar → BandedAC list.
        from .bands import BandedAC
        sidecar_payload = (
            yaml.safe_load(sidecar_path.read_text(encoding="utf-8"))
            or {}
        )
        raw_acs = sidecar_payload.get("acs") or []
        if not isinstance(raw_acs, list):
            raise OddExtractorError(
                f"contract-draft sidecar at {sidecar_path}: 'acs' must "
                f"be a list; got {type(raw_acs).__name__}"
            )
        banded_acs = [BandedAC.model_validate(d) for d in raw_acs]

        if not banded_acs:
            print("No banded ACs in contract draft; nothing to ratify.")
            return _EXIT_OK

        # Resolve PM. Lazy import to keep odd-extractor → per-project-pm
        # dep direction one-way.
        try:
            from loam.per_project_pm import PMRuntime
        except ImportError as exc:
            raise OddExtractorError(
                "loam.per_project_pm not importable; install "
                "loam-per-project-pm to use the ratification "
                f"workflow ({exc})"
            ) from exc

        # For --ratify, the positional arg is a contract-draft.md file,
        # not a repo directory. Default workspace-root to the file's
        # parent (preserves the C6 default-shift intent: artefacts live
        # alongside the input target, not in CWD).
        workspace_root = _resolve_workspace_root(
            args.workspace_root, draft_md_path.parent
        )
        pm_name = args.pm_name
        if not pm_name:
            raise OddExtractorError(
                "ratify: --pm-name is required (the PM mediating "
                "ratification batches; see "
                "framework/per-project-pm/ for PM authoring)"
            )
        pm_runtime = PMRuntime.from_workspace(workspace_root, pm_name)

        extraction_id = sidecar_payload.get("extraction_id")
        if not extraction_id:
            raise OddExtractorError(
                f"contract-draft sidecar at {sidecar_path}: missing "
                f"required 'extraction_id' field"
            )

        from .ratify import enqueue_ratification_batch

        # Compute draft path relative to extraction-dir for the
        # ratification-state record.
        ext_dir = extraction_dir(workspace_root, extraction_id)
        try:
            draft_relative = str(
                draft_md_path.relative_to(ext_dir)
            )
        except ValueError:
            draft_relative = str(draft_md_path)

        enqueued = enqueue_ratification_batch(
            extraction_id=extraction_id,
            banded_acs=banded_acs,
            workspace_root=workspace_root,
            pm_runtime=pm_runtime,
            pm_handle=pm_name,
            draft_path=draft_relative,
        )

        if args.json:
            payload = {
                "ratification": {
                    "extraction_id": extraction_id,
                    "enqueued_count": enqueued,
                    "pm_handle": pm_name,
                    "draft_path": draft_relative,
                    "total_acs": len(banded_acs),
                }
            }
            print(json.dumps(payload, indent=2))
        else:
            print(f"Ratification batch enqueued for {extraction_id}.")
            print(f"  PM handle:        {pm_name}")
            print(f"  Draft:            {draft_relative}")
            print(f"  ACs in draft:     {len(banded_acs)}")
            print(f"  Newly enqueued:   {enqueued}")
            print(
                "  Next: persona surfaces one question via "
                "PM.surface_next_questions_batch + relays + records "
                "response."
            )
        return _EXIT_OK
    except OddExtractorError as exc:
        print(f"loam odd-extract ratify: {exc}", file=sys.stderr)
        return _EXIT_ERR


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
    # AC.V025-1.2 — synthesis-timeout flag. v0.2.5.1 corrective.
    odd_parser.add_argument(
        "--synthesis-timeout",
        type=float,
        default=None,
        dest="synthesis_timeout",
        help=(
            "v0.2.5.1 corrective AC.V025-1.2 — synthesis subprocess "
            "timeout in seconds. Threads through to the claude -p "
            "subprocess wrapping the synthesis LLM-pass. Default: "
            "600s (raised from 180s after Eric's rd-automation run "
            "hit the 180s ceiling). Operator override for large "
            "repos with big synthesis prompts."
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
    # AC.BANDS.4 — ratification CLI sub-mode. The positional
    # ``repo_path`` is reused: when ``--ratify`` is set, it is treated
    # as the contract-draft markdown path. Single-positional shape
    # avoids argparse subparser conflict; the flag form keeps this
    # backward-compatible with Cycle 1's CLI surface.
    odd_parser.add_argument(
        "--ratify",
        action="store_true",
        help=(
            "ratify a confidence-banded contract draft. Treats the "
            "positional argument as the contract-draft markdown path "
            "(its sidecar .yaml is loaded automatically). Requires "
            "--pm-name (the PM mediating the ratification batch). "
            "Per AC.BANDS.4 (v0.1.8 Cycle 2)."
        ),
    )
    odd_parser.add_argument(
        "--pm-name",
        type=str,
        default=None,
        help=(
            "name of the PM (handle) mediating the ratification "
            "batch. Required with --ratify; optional with "
            "--incremental (when omitted, --incremental runs the "
            "classifier + generates proposals but does not enqueue)."
        ),
    )
    # AC.WATCH.1 — incremental-mode flag. v0.2.0 Cycle 1.
    odd_parser.add_argument(
        "--incremental",
        action="store_true",
        help=(
            "v0.2.0 Cycle 1 — incremental-mode watch. Reads the "
            "prior contract sidecar at <workspace>/.loam/extractions/"
            "<repo-id>/contract-draft.yaml; classifies each AC's "
            "evidence as still-current / out-of-date / orphaned; "
            "generates re-extraction proposals; enqueues domain-"
            "batched PM questions when --pm-name is supplied. "
            "Per AC.WATCH.{1,2,3,4,7,8}."
        ),
    )
    # AC.COMPINT.4 — completeness-interview flag. v0.2.4 Cycle 1.
    odd_parser.add_argument(
        "--interview",
        action="store_true",
        help=(
            "v0.2.4 Cycle 1 — completeness interview. Loads "
            "<workspace>/.loam/extractions/<repo-id>/objectives.yaml; "
            "runs the PM-batch one-question-at-a-time interview "
            "(confirm-existing / flag-missing-candidate / free-form-"
            "add); writes <workspace>/.loam/extractions/<repo-id>/"
            "augmented-objectives.yaml. Per AC.COMPINT.{4,5,6,7,8}."
        ),
    )
    # AC.GAPAN.7 — gap-analysis flag. v0.2.4 Cycle 2.
    odd_parser.add_argument(
        "--gaps",
        action="store_true",
        help=(
            "v0.2.4 Cycle 2 — gap analysis. Loads "
            "<workspace>/.loam/extractions/<repo-id>/{augmented-"
            "objectives,backing-map,evidence-rows}.yaml; produces "
            "two-category GapInventory (objectives without verified "
            "backing + implementation orphans) at "
            "<workspace>/.loam/extractions/<repo-id>/gap-inventory.yaml; "
            "emits stdout summary + audit-log entries. Idempotent "
            "on unchanged inputs. Per AC.GAPAN.{3,4,5,6,7}."
        ),
    )
    # AC.PERSONA-PULL.1 — build-next flag. v0.2.4 Cycle 3.
    odd_parser.add_argument(
        "--build-next",
        action="store_true",
        dest="build_next",
        help=(
            "v0.2.4 Cycle 3 — build-next ranking. Loads "
            "<workspace>/.loam/extractions/<repo-id>/{augmented-"
            "objectives,gap-inventory}.yaml + (optional) onboarding-"
            "survey context; produces ranked candidate list at "
            "<workspace>/.loam/extractions/<repo-id>/build-next."
            "{md,yaml}; emits stdout summary + audit-log entries. "
            "Idempotent on unchanged inputs. Output is informative "
            "(not prescriptive) — operator chooses what to build. "
            "Persona invokes on user-question-trigger such as 'what "
            "should I build next?'. Per AC.BLDNXT.{1..9} + "
            "AC.PERSONA-PULL.{1..4}."
        ),
    )
    odd_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "(--build-next) cap the ranked candidate list at top-N. "
            f"Default {10}. Per AC.BLDNXT.5."
        ),
    )
    # AC.WATCH.6 — invocation-source flag. v0.2.0 Cycle 1.
    odd_parser.add_argument(
        "--invocation-source",
        type=str,
        default="cli_human",
        help=(
            "trigger-source slug recorded in audit-log "
            "(`incremental_watch_run` event_kind notes). Default "
            "`cli_human`; schedulers can pass `cli_cron`, "
            "`cli_schedule_skill`, etc. Per AC.WATCH.6."
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

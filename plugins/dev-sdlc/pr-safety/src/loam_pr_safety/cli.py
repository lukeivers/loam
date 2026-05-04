"""CLI builder for ``loam pr-safety``.

Per AC.PRSG.6 — registered with the unified ``loam`` CLI via the
``loam.cli.subcommands`` entry-point group (declared in pyproject.toml).
``loam_cli.cli.main`` discovers this builder + invokes it with the
parent argparse subparsers handle.

Builder contract (per loam_cli convention):

    def build_pr_safety_subcommand(
        sub: argparse._SubParsersAction,
    ) -> None:
        ...

Sets ``func`` on each leaf parser via ``set_defaults`` so ``main``
dispatches via ``args.func(args)``.

Sub-subcommands shipped this cycle: ``gate``. Cycle 2 adds
``install`` (hook + CI installer).

Exit codes:

  0 — PASS
  2 — HARD-BLOCK
  3 — SURFACE-DECISION
  4 — OVERRIDE-REJECTED
  5 — ContractMissingError / ClassifierAccuracyError / GateError
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loam_pr_safety.audit import write_audit_entry
from loam_pr_safety.classifier import classify
from loam_pr_safety.contract import read_contract
from loam_pr_safety.diff import parse_diff
from loam_pr_safety.errors import (
    ContractMissingError,
    GateError,
    OverrideRejectedError,
    PRSafetyError,
)
from loam_pr_safety.gate import decide
from loam_pr_safety.override import (
    build_override_request,
    read_commit_message,
    read_commit_owner,
    recognise_override,
)
from loam_pr_safety.profile import (
    is_production_stake,
    read_safety_profile,
)
from loam_pr_safety.state import compute_repo_id
from loam_pr_safety.spec import GateAction


_EXIT_PASS = 0
_EXIT_HARD_BLOCK = 2
_EXIT_SURFACE_DECISION = 3
_EXIT_OVERRIDE_REJECTED = 4
_EXIT_ERR = 5


def build_pr_safety_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the ``loam pr-safety`` subcommand group.

    Per the loam_cli convention, this is invoked once at CLI build
    time. Sub-subcommands attach via ``add_parser`` on the inner
    subparsers.
    """
    parser = sub.add_parser(
        "pr-safety",
        help=(
            "PR-safety gate — read banded contract + classify diff "
            "+ decide per the 3-band × 4-shape × 3-profile matrix"
        ),
        description=(
            "loam pr-safety — gates PRs against the v0.1.8-authored "
            "banded ODD contract. Cycle 1 (v0.1.9): engine without "
            "delivery wrapping. Cycle 2 ships hooks + CI templates "
            "+ PR description template."
        ),
    )
    inner = parser.add_subparsers(dest="pr_safety_subcommand", required=True)

    # ---- gate sub-subcommand --------------------------------------

    p_gate = inner.add_parser(
        "gate",
        help="run gate against a repo's PR diff",
        description=(
            "Reads the banded contract from "
            "<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml; "
            "diffs the repo (default: HEAD vs origin/main); classifies "
            "the diff against the contract; decides per the 3×4×3 "
            "decision matrix; records to audit log."
        ),
    )
    p_gate.add_argument(
        "repo",
        type=Path,
        help="path to the target repo",
    )
    p_gate.add_argument(
        "--diff",
        dest="diff_range",
        default=None,
        help="diff range as <sha1>..<sha2>; default = HEAD vs origin/main",
    )
    p_gate.add_argument(
        "--override",
        action="store_true",
        help=(
            "opt into override-flow recognition (Decision I default-no). "
            "Required to honour `contract-update:` prefix or "
            "`Loam-Override:` trailer."
        ),
    )
    p_gate.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help=(
            "do not enqueue PM ratification or write contract-overrides; "
            "audit-log entry still written. Default under "
            "production-stake; off under dev/research."
        ),
    )
    p_gate.add_argument(
        "--require-ratification",
        action="store_true",
        help=(
            "force requires_ratification=True under dev/research "
            "for SURFACE-DECISION (overrides default proceed-with-warning)"
        ),
    )
    p_gate.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="workspace root (default: cwd)",
    )
    p_gate.add_argument(
        "--repo-id",
        default=None,
        help=(
            "override automatic repo-id derivation (default: "
            "<basename>-<8-char-sha256-hex-of-abs-path>)"
        ),
    )
    p_gate.add_argument(
        "--json",
        action="store_true",
        help="emit structured JSON output instead of human-readable",
    )
    p_gate.set_defaults(func=_run_gate)


def _resolve_workspace_root(arg: Path | None) -> Path:
    return (arg if arg is not None else Path.cwd()).expanduser().resolve()


def _resolve_repo_path(arg: Path) -> Path:
    p = arg.expanduser().resolve()
    if not p.exists():
        raise GateError(f"repo path does not exist: {p}")
    return p


def _parse_diff_range(arg: str | None) -> tuple[str | None, str | None]:
    """Parse ``--diff <sha1>..<sha2>`` into (sha1, sha2)."""
    if arg is None:
        # Default: HEAD vs origin/main when invoked without --diff.
        # The `parse_diff` call below resolves this — we surface
        # this default here so the audit-log carries the resolved
        # range. To keep Cycle 1 simple, we let `parse_diff` handle
        # the None/None default (working-tree-vs-HEAD); the
        # "HEAD vs origin/main" default is named in CLI help but the
        # default invocation diffs working-tree-vs-HEAD which is the
        # safer default for the gate (working-tree captures the
        # author's in-progress commit before push).
        return (None, None)
    if ".." not in arg:
        raise GateError(
            f"--diff must be of the form <sha1>..<sha2>; got {arg!r}"
        )
    sha1, _, sha2 = arg.partition("..")
    return (sha1.strip() or None, sha2.strip() or None)


def _emit_decision(decision, *, json_mode: bool) -> None:
    if json_mode:
        payload = {
            "action": decision.action.value,
            "requires_ratification": decision.requires_ratification,
            "safety_profile": decision.safety_profile,
            "reason": decision.reason,
            "touched_ac_ids": [
                t.ac.ac_id for t in decision.touched_acs
            ],
            "novel_count": len(decision.novel),
            "pm_batch_pairs": [
                {"question": q, "provenance": p}
                for q, p in decision.pm_batch_pairs
            ],
        }
        print(json.dumps(payload, indent=2))
        return
    print(f"action: {decision.action.value}")
    print(f"requires_ratification: {decision.requires_ratification}")
    print(f"safety_profile: {decision.safety_profile}")
    print(f"reason: {decision.reason}")
    if decision.touched_acs:
        print("touched ACs:")
        for t in decision.touched_acs:
            print(
                f"  - {t.ac.ac_id} ({t.ac.confidence.value}, "
                f"touch={t.touch_kind})"
            )
    if decision.novel:
        print(f"novel candidates: {len(decision.novel)}")
        for c in decision.novel:
            print(
                f"  - {c.file_path!s} ({len(c.hunks)} hunk(s))"
            )
    if decision.pm_batch_pairs:
        print(f"PM batch ({len(decision.pm_batch_pairs)} questions):")
        for idx, (q, p) in enumerate(decision.pm_batch_pairs, start=1):
            print(f"  [{idx}] provenance={p}")
            print(f"      {q}")


def _action_to_exit_code(action: GateAction) -> int:
    if action is GateAction.PASS:
        return _EXIT_PASS
    if action is GateAction.HARD_BLOCK:
        return _EXIT_HARD_BLOCK
    if action is GateAction.SURFACE_DECISION:
        return _EXIT_SURFACE_DECISION
    return _EXIT_PASS  # DOCS_ONLY = 0


def _run_gate(args: argparse.Namespace) -> int:
    """Execute the ``loam pr-safety gate`` invocation.

    Per AC.PRSG.6.
    """
    try:
        repo_path = _resolve_repo_path(args.repo)
        workspace_root = _resolve_workspace_root(args.workspace_root)
        repo_id = (
            args.repo_id
            if args.repo_id
            else compute_repo_id(repo_path)
        )

        # Resolve safety_profile + dry-run default.
        prodstake = is_production_stake(workspace_root)
        if args.dry_run is None:
            dry_run = prodstake  # production-stake → dry by default
        else:
            dry_run = args.dry_run
        safety_profile = read_safety_profile(workspace_root)

        # Read contract.
        contract = read_contract(repo_id, workspace_root)

        # Parse diff.
        from_sha, to_sha = _parse_diff_range(args.diff_range)
        diff = parse_diff(repo_path, from_sha=from_sha, to_sha=to_sha)
        diff_range_str = (
            args.diff_range
            if args.diff_range
            else "(working-tree vs HEAD)"
        )

        # Classify.
        classification = classify(diff, contract)

        # Decide.
        decision = decide(
            classification,
            safety_profile=safety_profile,
            extraction_id=contract.extraction_id,
            require_ratification=args.require_ratification,
        )

        # Override-flow detection (only when --override is set AND
        # decision is HARD_BLOCK and dry_run is False).
        override_recognised = False
        if args.override and decision.action is GateAction.HARD_BLOCK:
            commit_msg = read_commit_message(repo_path, "HEAD")
            override_recognised, rationale = recognise_override(
                commit_msg, override_flag=True
            )
            if override_recognised and not dry_run:
                # Build override request + audit override_proposed.
                owner = read_commit_owner(repo_path, "HEAD")
                request = build_override_request(
                    classification,
                    rationale=rationale,
                    owner=owner,
                    commit_sha=to_sha or "HEAD",
                    repo_sha=contract.repo_sha or "",
                )
                write_audit_entry(
                    workspace_root,
                    event_kind="override_proposed",
                    repo_id=repo_id,
                    repo_sha=contract.repo_sha or "",
                    diff_range=diff_range_str,
                    safety_profile=safety_profile,
                    decision="OVERRIDE_PROPOSED",
                    requires_ratification=True,
                    touched_acs=[ac.ac_id for ac in request.original_acs],
                    novel_count=len(classification.novel),
                    reason=(
                        "Override recognised; ratification flow not "
                        "auto-run from CLI in Cycle 1 — caller "
                        "should invoke the override flow programmatically "
                        "or via Cycle 2's hook installer surface."
                    ),
                    owner=owner,
                    rationale=rationale,
                )

        # Audit the gate decision.
        write_audit_entry(
            workspace_root,
            event_kind="dry_run" if dry_run else "gate_decision",
            repo_id=repo_id,
            repo_sha=contract.repo_sha or "",
            diff_range=diff_range_str,
            safety_profile=safety_profile,
            decision=decision.action.value,
            requires_ratification=decision.requires_ratification,
            touched_acs=[
                t.ac.ac_id for t in decision.touched_acs
            ],
            novel_count=len(decision.novel),
            reason=decision.reason,
        )

        # Emit decision.
        _emit_decision(decision, json_mode=args.json)

        return _action_to_exit_code(decision.action)
    except OverrideRejectedError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return _EXIT_OVERRIDE_REJECTED
    except ContractMissingError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return _EXIT_ERR
    except PRSafetyError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return _EXIT_ERR

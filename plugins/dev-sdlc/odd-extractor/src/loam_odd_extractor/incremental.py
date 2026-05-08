"""Incremental-mode entry-point for the watch.

Per AC.WATCH.{1,2,3,4,7,8} (v0.2.0 Cycle 1) — the incremental
engine glues together the diff_classifier + proposals +
incremental_ratify + audit-log floor + production-stake honour-flow.

Public surface:

  - :func:`run_incremental` — the main engine; reads prior contract,
    classifies evidence, generates proposals, enqueues PM domain-
    batches, writes audit-log entries.
  - :class:`IncrementalRunResult` — typed result of the run.
  - :class:`ContractNotFoundError` — raised when no prior contract
    exists for `--incremental` to read.
  - :class:`IncrementalRefusedError` — raised when production-stake
    constraints are violated structurally.

Per F2 RF gap #6 (plan-doc §10): defense-in-depth — `run_incremental`
NEVER mutates the contract sidecar regardless of `safety_profile`.
The watch only enqueues proposals through PM; sidecar updates flow
through the existing v0.1.8 Cycle 2 `apply_ratification_action`
flow, which this cycle does NOT invoke.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path

import yaml

from .backing_map import load_backing_map
from .diff_classifier import (
    EvidenceClassification,
    classify_evidence,
)
from .errors import OddExtractorError
from .incremental_ratify import (
    EnqueueResult,
    enqueue_incremental_proposals,
)
from .observability import write_audit_entry
from .proposals import IncrementalProposalSet, generate_proposals
from .spec import BackingMap, Objective
from .state import compute_repo_id, extraction_dir


# ---- errors ---------------------------------------------------------


class ContractNotFoundError(OddExtractorError):
    """No prior contract sidecar exists; --incremental requires one."""


class IncrementalRefusedError(OddExtractorError):
    """Structural refusal — production-stake constraint violated."""


# ---- result type ----------------------------------------------------


@dataclass(frozen=True)
class IncrementalRunResult:
    """Typed result of `run_incremental`.

    Captured for observability + test assertion. Includes the
    classification + proposal-set + enqueue-result so callers can
    inspect without re-walking the workspace.
    """

    extraction_id: str
    classification: EvidenceClassification
    proposal_set: IncrementalProposalSet
    enqueue_result: EnqueueResult
    safety_profile: str
    dry_run: bool
    invocation_source: str
    prior_contract_sha: str | None
    current_repo_sha: str
    audit_log_entries_written: int

    def summary_line(self) -> str:
        """Single-line human-readable summary for CLI output."""
        c = self.classification
        return (
            f"{c.still_current_count} still-current / "
            f"{c.out_of_date_count} out-of-date / "
            f"{c.orphaned_count} orphaned across "
            f"{self.enqueue_result.enqueued_count + self.enqueue_result.skipped_count} "
            f"domain{'s' if (self.enqueue_result.enqueued_count + self.enqueue_result.skipped_count) != 1 else ''}"
        )

    def to_json_dict(self) -> dict:
        """JSON-serializable dict for `--json` CLI output."""
        c = self.classification
        e = self.enqueue_result
        return {
            "extraction_id": self.extraction_id,
            "summary": {
                "still_current": c.still_current_count,
                "out_of_date": c.out_of_date_count,
                "orphaned": c.orphaned_count,
            },
            "enqueue": {
                "enqueued_domains": list(e.enqueued_domains),
                "skipped_duplicates": list(e.skipped_duplicates),
                "total_proposals": e.total_proposals,
            },
            "safety_profile": self.safety_profile,
            "dry_run": self.dry_run,
            "invocation_source": self.invocation_source,
            "prior_contract_sha": self.prior_contract_sha,
            "current_repo_sha": self.current_repo_sha,
            "audit_log_entries_written": self.audit_log_entries_written,
        }


# ---- helpers --------------------------------------------------------


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _load_prior_objectives(
    *, ext_dir: Path
) -> tuple[list[Objective], BackingMap, str, Path, Path]:
    """Read prior objectives.yaml + backing-map.yaml and reconstruct
    typed lists.

    Returns ``(prior_objectives, prior_backing_map, contract_created_at,
    objectives_path, backing_map_path)``. Raises
    :class:`ContractNotFoundError` if either source file is missing.

    Per AC.WATCHOBJ.4 — Cycle 3 reads objectives.yaml + backing-map.yaml
    directly (Cycles 1+2 outputs); legacy contract-draft.yaml.acs:
    retired per master plan §6.2.
    """
    objectives_path = ext_dir / "objectives.yaml"
    backing_map_path = ext_dir / "backing-map.yaml"

    if not objectives_path.exists():
        raise ContractNotFoundError(
            f"--incremental requires prior objectives at "
            f"{objectives_path}. Run `loam odd-extract <repo>` "
            f"(full mode) first to synthesize objectives + "
            f"populate the backing-map."
        )

    payload = yaml.safe_load(objectives_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractNotFoundError(
            f"prior objectives.yaml at {objectives_path} is malformed "
            f"(expected mapping, got {type(payload).__name__})"
        )
    raw_objs = payload.get("objectives") or []
    if not isinstance(raw_objs, list):
        raise ContractNotFoundError(
            f"prior objectives.yaml at {objectives_path}: 'objectives' "
            f"must be a list; got {type(raw_objs).__name__}"
        )
    objectives: list[Objective] = []
    for d in raw_objs:
        objectives.append(Objective.model_validate(d))

    bm = load_backing_map(ext_dir)
    if bm is None:
        raise ContractNotFoundError(
            f"--incremental requires prior backing-map at "
            f"{backing_map_path}. Run Cycle 2 backing-map population "
            f"(part of `loam odd-extract` post-synthesis pipeline) first."
        )

    contract_created_at = str(
        payload.get("created_at") or "1970-01-01T00:00:00+00:00"
    )

    return (
        objectives,
        bm,
        contract_created_at,
        objectives_path,
        backing_map_path,
    )


def _resolve_safety_profile(workspace_root: Path) -> str:
    """Read the workspace manifest at ``<workspace>/loam.yaml`` and
    return `safety_profile`.

    Mirrors the resolution order in
    :mod:`loam_pr_safety.profile.read_safety_profile`:

      1. ``<workspace_root>/loam.yaml`` — canonical location.
      2. Manifest absent → ``"dev"`` (DEFAULT_SAFETY_PROFILE).
      3. Manifest present but malformed → ``"dev"`` (graceful
         degradation; defense-in-depth).

    Defaults to `"dev"` per AC.WATCH.7 fallback contract.
    """
    try:
        from loam.workspace_bootstrap import load_manifest  # type: ignore
    except ImportError:
        return "dev"
    manifest_path = workspace_root.expanduser().resolve() / "loam.yaml"
    if not manifest_path.exists():
        return "dev"
    try:
        manifest = load_manifest(manifest_path)
    except Exception:
        return "dev"
    sp = getattr(manifest, "safety_profile", None)
    if not sp:
        return "dev"
    return str(sp)


def _is_production_stake(safety_profile: str) -> bool:
    return safety_profile == "production-stake"


def _prior_repo_sha(prior_objectives: list[Objective]) -> str | None:
    """Pick a representative prior repo SHA from the prior objectives.

    Returns the first non-null evidence.repo_sha across the objective
    list; ``None`` if no objective pinned a SHA (e.g., all-PLAUSIBLE
    extraction).
    """
    for o in prior_objectives:
        if o.evidence.repo_sha:
            return o.evidence.repo_sha
    return None


# ---- main engine ----------------------------------------------------


def run_incremental(
    *,
    repo_path: Path,
    workspace_root: Path,
    pm_runtime=None,  # PMRuntime — None disables PM enqueue
    pm_handle: str | None = None,
    invocation_source: str = "cli_human",
    dry_run: bool | None = None,
    timestamp: str | None = None,
) -> IncrementalRunResult:
    """Run the watch in incremental mode against `repo_path`.

    Per AC.WATCH.{1,2,3,4,7,8}:

      1. Resolve `extraction_id` via `compute_repo_id(repo_path)`.
      2. Load prior contract sidecar from
         ``<workspace>/.loam/extractions/<id>/contract-draft.yaml``.
         Raise :class:`ContractNotFoundError` if missing.
      3. Read `safety_profile` from workspace manifest. Under
         `production-stake`, force `dry_run=True` regardless of
         caller's `dry_run` argument.
      4. Run `classify_evidence(...)` against the current repo state.
      5. Run `generate_proposals(...)` over the classification.
      6. Run `enqueue_incremental_proposals(...)` if `pm_runtime` is
         supplied AND `dry_run is False`. Under dry-run, skip enqueue
         (still write proposal audit entries so the dry-run is
         observable).
      7. Write audit-log entries throughout per AC.WATCH.8.

    Returns :class:`IncrementalRunResult`.

    `pm_runtime=None` is permitted — used by tests + dry-run paths
    that exercise classification + proposal-generation without PM
    interaction.
    """
    extraction_id = compute_repo_id(repo_path)
    ext_dir = extraction_dir(workspace_root, extraction_id)

    (
        prior_objectives,
        prior_backing_map,
        contract_created_at,
        objectives_path,
        backing_map_path,
    ) = _load_prior_objectives(ext_dir=ext_dir)

    safety_profile = _resolve_safety_profile(workspace_root)
    is_prod = _is_production_stake(safety_profile)
    # Production-stake forces dry-run.
    effective_dry_run: bool
    if is_prod:
        effective_dry_run = True
    elif dry_run is None:
        effective_dry_run = False
    else:
        effective_dry_run = dry_run

    ts = timestamp if timestamp is not None else _now_iso()
    audit_count = 0

    # --- Audit: incremental_watch_run -------------------------------
    notes_run_parts = [
        f"prior_objectives_path={objectives_path}",
        f"prior_backing_map_path={backing_map_path}",
        f"safety_profile={safety_profile}",
        f"dry_run={str(effective_dry_run).lower()}",
        f"invocation_source={invocation_source}",
    ]
    if is_prod and dry_run is False:
        notes_run_parts.append("production_stake_dry_run_downgrade")
    write_audit_entry(
        ext_dir,
        event_kind="incremental_watch_run",
        extraction_id=extraction_id,
        notes=" ".join(notes_run_parts),
        timestamp=ts,
    )
    audit_count += 1

    # --- Classify ---------------------------------------------------
    classification = classify_evidence(
        prior_objectives=prior_objectives,
        prior_backing_map=prior_backing_map,
        repo_path=repo_path,
        contract_created_at=contract_created_at,
    )

    # --- Audit: incremental_classification --------------------------
    notes_class = (
        f"still_current_count={classification.still_current_count} "
        f"out_of_date_count={classification.out_of_date_count} "
        f"orphaned_count={classification.orphaned_count}"
    )
    write_audit_entry(
        ext_dir,
        event_kind="incremental_classification",
        extraction_id=extraction_id,
        notes=notes_class,
        timestamp=ts,
    )
    audit_count += 1

    # --- Generate proposals -----------------------------------------
    prior_sha = _prior_repo_sha(prior_objectives)
    # Current repo SHA — best-effort; classifier helper will have
    # used the same one. We re-derive here to avoid leaking it
    # across module boundaries.
    from .diff_classifier import (
        _current_head_sha as _current_head,
        _is_git_repo,
    )

    if _is_git_repo(repo_path):
        current_sha = _current_head(repo_path) or "<no-sha>"
    else:
        current_sha = "<no-sha>"

    proposal_set = generate_proposals(
        classification,
        extraction_id=extraction_id,
        prior_repo_sha=prior_sha,
        current_repo_sha=current_sha,
        generated_at=ts,
    )

    # --- Enqueue (or skip under dry-run) ----------------------------
    if pm_runtime is None or effective_dry_run:
        enqueue_result = EnqueueResult(
            enqueued_domains=(),
            skipped_duplicates=(),
            total_proposals=proposal_set.proposal_count,
        )
        # Even under dry-run, emit a per-domain audit entry so the
        # dry-run is observable per AC.WATCH.8 (event_kind=
        # incremental_proposal w/ enqueued=false).
        from .domain_batching import group_proposals_by_domain

        for domain, props in group_proposals_by_domain(
            list(proposal_set.proposals)
        ).items():
            write_audit_entry(
                ext_dir,
                event_kind="incremental_proposal",
                extraction_id=extraction_id,
                notes=(
                    f"domain={domain} objective_count={len(props)} "
                    f"provenance_string=odd-extract:incremental:"
                    f"{extraction_id}:objective:{domain} enqueued=false "
                    f"reason={'dry_run' if effective_dry_run else 'no_pm_runtime'}"
                ),
                timestamp=ts,
            )
            audit_count += 1
    else:
        if pm_handle is None:
            raise IncrementalRefusedError(
                "pm_runtime supplied but pm_handle is None; "
                "callers must pass both"
            )
        enqueue_result = enqueue_incremental_proposals(
            proposal_set=proposal_set,
            workspace_root=workspace_root,
            pm_runtime=pm_runtime,
            pm_handle=pm_handle,
        )
        # Per-domain audit entries.
        for domain in enqueue_result.enqueued_domains:
            write_audit_entry(
                ext_dir,
                event_kind="incremental_proposal",
                extraction_id=extraction_id,
                notes=(
                    f"domain={domain} "
                    f"provenance_string=odd-extract:incremental:"
                    f"{extraction_id}:objective:{domain} enqueued=true"
                ),
                timestamp=ts,
            )
            audit_count += 1
        for domain in enqueue_result.skipped_duplicates:
            write_audit_entry(
                ext_dir,
                event_kind="incremental_enqueue_skip_duplicate",
                extraction_id=extraction_id,
                notes=(
                    f"domain={domain} "
                    f"provenance_string=odd-extract:incremental:"
                    f"{extraction_id}:objective:{domain}"
                ),
                timestamp=ts,
            )
            audit_count += 1

    # --- AC.WATCHOBJ.5 — incremental_run_complete (objective-altitude
    #     telemetry; additive payload; SOC-2 floor preserved). -------
    objectives_by_domain: dict[str, int] = {}
    for objective in prior_objectives:
        from .domain_batching import infer_domain
        d = infer_domain(objective)
        objectives_by_domain[d] = objectives_by_domain.get(d, 0) + 1
    backing_map_staleness = (
        classification.out_of_date_count > 0
        or classification.orphaned_count > 0
    )
    write_audit_entry(
        ext_dir,
        event_kind="incremental_run_complete",
        extraction_id=extraction_id,
        notes=(
            f"still_current_objective_count={classification.still_current_count} "
            f"out_of_date_objective_count={classification.out_of_date_count} "
            f"orphaned_objective_count={classification.orphaned_count} "
            f"backing_map_staleness_detected={str(backing_map_staleness).lower()} "
            f"domain_batches_enqueued={enqueue_result.enqueued_count} "
            f"objectives_by_domain={','.join(f'{k}={v}' for k, v in sorted(objectives_by_domain.items()))} "
            f"prior_repo_sha={prior_sha or '<no-sha>'} "
            f"current_repo_sha={current_sha}"
        ),
        timestamp=ts,
    )
    audit_count += 1

    return IncrementalRunResult(
        extraction_id=extraction_id,
        classification=classification,
        proposal_set=proposal_set,
        enqueue_result=enqueue_result,
        safety_profile=safety_profile,
        dry_run=effective_dry_run,
        invocation_source=invocation_source,
        prior_contract_sha=prior_sha,
        current_repo_sha=current_sha,
        audit_log_entries_written=audit_count,
    )

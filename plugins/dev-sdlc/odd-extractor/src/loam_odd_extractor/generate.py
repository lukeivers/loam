"""Stage 3 — generate.

Per AC.OREK.3 — input :class:`AnalysisPlan` → output :class:`RawACs`
written to ``<workspace>/.loam/extractions/<repo-id>/raw-acs.yaml``.

Cycle 1 ships zero language adapters, so this stage iterates the
plan's slices (zero in Cycle 1) and dispatches to each adapter's
:meth:`LanguageAdapter.extract`. With no slices, the output is empty
``acs: []`` plus :attr:`AnalysisPlan.unhandled_paths` carried forward
into :attr:`RawACs.unhandled_paths`.

Per Surface #2 (plan-doc §5) — the adapter contract is intentionally
loose; Cycles 3+4 tighten as Ruby + Python adapters land. This stage
trusts the adapter to honour the contract.
"""

from __future__ import annotations

import datetime as _dt

import yaml

from .observability import write_audit_entry
from .registry import discover_adapters
from .spec import AnalysisPlan, ExtractionConfig, RawACs
from .state import extraction_dir, load_state, save_state


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def generate_raw_acs(
    *,
    config: ExtractionConfig,
    plan: AnalysisPlan,
    timestamp: str | None = None,
) -> RawACs:
    """Run Stage 3 — generate.

    Returns :class:`RawACs`; writes ``raw-acs.yaml`` artefact;
    appends a ``stage_complete`` audit-log entry; updates
    ``state.yaml``.

    Cycle 1 dispatch logic: for each slice in ``plan.slices``, look
    up the adapter by name and call ``adapter.extract(repo, plan)``.
    Aggregate the resulting :class:`RawACs.acs` lists. Aggregate
    per-slice cost dicts. Carry plan.unhandled_paths into the output
    plus any paths returned by adapters as unhandled.

    ``timestamp`` is injectable for deterministic tests.
    """
    ext_dir = extraction_dir(config.workspace_root, config.repo_id)
    ts = timestamp if timestamp is not None else _now_iso()

    adapters_by_name = {a.name: a for a in discover_adapters()}

    aggregated_acs: list[dict] = []
    aggregated_unhandled = list(plan.unhandled_paths)
    per_slice_costs: dict[str, dict] = {}

    if config.dry_run:
        # Per AC.OREK.5 + Decision D — dry-run mode never invokes
        # adapter extract(); it short-circuits to an empty result
        # plus the plan's unhandled paths. The cost-estimate is the
        # only meaningful output in dry-run.
        pass
    else:
        for slice_ in plan.slices:
            adapter = adapters_by_name.get(slice_.adapter_name)
            if adapter is None:
                # The plan references an adapter that's no longer
                # discoverable — record as unhandled and continue.
                aggregated_unhandled.extend(slice_.paths)
                per_slice_costs[slice_.slice_id] = {
                    "status": "adapter_missing",
                    "adapter_name": slice_.adapter_name,
                }
                continue
            try:
                slice_acs = adapter.extract(config.repo_path, plan)
            except Exception as exc:
                aggregated_unhandled.extend(slice_.paths)
                per_slice_costs[slice_.slice_id] = {
                    "status": "extract_failed",
                    "adapter_name": slice_.adapter_name,
                    "error": str(exc),
                }
                continue
            aggregated_acs.extend(slice_acs.acs)
            aggregated_unhandled.extend(slice_acs.unhandled_paths)
            per_slice_costs[slice_.slice_id] = {
                "status": "extracted",
                "adapter_name": slice_.adapter_name,
                "ac_count": len(slice_acs.acs),
            }

    raw = RawACs(
        extraction_id=config.repo_id,
        acs=aggregated_acs,
        unhandled_paths=aggregated_unhandled,
        per_slice_costs=per_slice_costs,
        created_at=ts,
    )

    raw_path = ext_dir / "raw-acs.yaml"
    raw_payload = raw.model_dump(mode="json")
    raw_path.write_text(
        yaml.safe_dump(raw_payload, sort_keys=False),
        encoding="utf-8",
    )

    state = load_state(ext_dir)
    if state is None:
        from .state import ExtractionState

        state = ExtractionState(
            extraction_id=config.repo_id,
            repo_path=str(config.repo_path),
            workspace_root=str(config.workspace_root),
            init_complete=True,
            analyze_complete=True,
        )
    state.generate_complete = True
    state.last_updated_at = ts
    state.artefacts["raw_acs"] = raw_path.relative_to(ext_dir).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=config.repo_id,
        stage="generate",
        artefact_path=raw_path.relative_to(ext_dir).as_posix(),
        notes=(
            f"acs={len(aggregated_acs)} "
            f"unhandled={len(aggregated_unhandled)} "
            f"dry_run={config.dry_run}"
        ),
        timestamp=ts,
    )

    return raw

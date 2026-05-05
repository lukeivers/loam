"""Stage 3 — generate.

Per v0.2.3 Cycle 1 (sub-plan-doc §3 AC.OBJX.7) — the generate stage
is rewired:

1. Adapter outputs (``BandedAC`` rows from Ruby + JS/TS adapters) are
   collected into ``evidence-rows.yaml`` (renamed from
   ``raw-acs.yaml`` per master plan §6.3 + sub-plan-doc §7).
2. The multi-source input collector (:mod:`multi_source`) reads
   README + design docs + tests + survey + code patterns from the
   adapter rows.
3. The LLM-pass synthesis layer (:mod:`synthesis`) emits banded
   :class:`Objective` + :class:`Constraint` + :class:`Capability`
   rows.
4. The altitude validator (:mod:`altitude_validator`) runs §self-
   checks 1-5; drift-halt at >30% fail rate.
5. ``contract-draft.yaml acs:`` (legacy v0.1.9 PR-safety field)
   carries typed :class:`Objective` rows transitionally; full drop
   is Cycle 3 per master plan §6.2.

Test-mode + dry-run + adapter-only paths: when ``anthropic_client``
is ``None`` and ``synthesis_required=False``, the stage runs only
the evidence-rows path — :class:`SynthesisResult` is empty. This
preserves v0.1.8 substrate behaviour for tests that don't exercise
the LLM-pass.

The four-stage workflow shape + adapter Protocol + audit-log
substrate are PRESERVED unchanged — Cycle 1's rewire is additive.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml

from .multi_source import collect_multi_source_inputs
from .observability import write_audit_entry
from .registry import discover_adapters
from .spec import (
    AnalysisPlan,
    ExtractionConfig,
    RawACs,
    SynthesisResult,
)
from .state import extraction_dir, load_state, save_state


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _empty_synthesis_result(
    *, extraction_id: str, ts: str
) -> SynthesisResult:
    return SynthesisResult(
        extraction_id=extraction_id,
        objectives=[],
        constraints=[],
        capabilities=[],
        raw_response=None,
        token_count_input=0,
        token_count_output=0,
        cost_actual_cents=0.0,
        model_id="(none)",
        created_at=ts,
    )


# Per v0.2.3 Cycle 3 + master plan §6.2 — `_objectives_as_legacy_acs`
# retired. The legacy `acs:` field in `contract-draft.yaml` is no
# longer rendered. PR-safety reads `objectives.yaml` +
# `backing-map.yaml` directly per AC.PRGATE.1.


def generate_raw_acs(
    *,
    config: ExtractionConfig,
    plan: AnalysisPlan,
    timestamp: str | None = None,
    anthropic_client: Any | None = None,
    synthesis_required: bool = False,
) -> RawACs:
    """Run Stage 3 — generate (v0.2.3 rewire).

    Returns :class:`RawACs` (the evidence-rows shape — symbol-
    altitude adapter output); writes ``evidence-rows.yaml``;
    optionally invokes the synthesis pass and persists
    :class:`SynthesisResult` to ``synthesis.yaml``; appends
    ``stage_complete`` + (when synthesis runs)
    ``synthesis_complete`` audit-log entries; updates
    ``state.yaml``.

    Synthesis pass invariants (per AC.OBJX.5 + AC.OBJX.6):

    - When ``anthropic_client`` is provided, the synthesis pass
      runs unconditionally and produces banded objectives.
    - When ``synthesis_required=True`` and no client is given, raise
      :class:`StageError` (production path).
    - Otherwise the synthesis result is empty (test / dry-run
      preservation path).

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
        # plus the plan's unhandled paths. Cost-estimate is the
        # only meaningful output in dry-run.
        pass
    else:
        for slice_ in plan.slices:
            adapter = adapters_by_name.get(slice_.adapter_name)
            if adapter is None:
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

    # Per AC.OBJX.7: rename to evidence-rows.yaml. Preserves the
    # exact RawACs.model_dump shape — adapters round-trip through
    # this file unchanged. v0.2.3 also writes raw-acs.yaml as a
    # transitional alias (same content) for v0.1.9 PR-safety smoke
    # + the v0.1.8 test substrate; full retirement is Cycle 3 per
    # master plan §6.3 + sub-plan-doc §6.5 ("rename is structural-
    # cleanup with zero consumer break"). Both names point at the
    # SAME serialized payload — the new name is authoritative.
    evidence_path = ext_dir / "evidence-rows.yaml"
    raw_payload = raw.model_dump(mode="json")
    serialized = yaml.safe_dump(raw_payload, sort_keys=False)
    evidence_path.write_text(serialized, encoding="utf-8")
    # Transitional alias.
    legacy_raw_path = ext_dir / "raw-acs.yaml"
    legacy_raw_path.write_text(serialized, encoding="utf-8")

    # Per sub-plan-doc §3 AC.OBJX.5 + AC.OBJX.7: multi-source bundle
    # + synthesis pass. The synthesis result lands in
    # ``synthesis.yaml``; the typed-Objective transitional shape
    # lands in legacy ``acs:`` via the verify-stage.
    bundle = collect_multi_source_inputs(
        config.repo_path,
        config.workspace_root,
        repo_id=config.repo_id,
        evidence_rows=aggregated_acs,
    )

    synthesis_result: SynthesisResult
    if anthropic_client is not None:
        # Lazy import to avoid circular import at module load.
        from .synthesis import synthesize_objectives

        synthesis_result = synthesize_objectives(
            bundle,
            extraction_id=config.repo_id,
            repo_sha=bundle.repo_sha,
            anthropic_client=anthropic_client,
            extraction_dir=ext_dir,
            timestamp=ts,
        )
    elif synthesis_required:
        from .errors import StageError

        raise StageError(
            "generate: synthesis_required=True but anthropic_client=None; "
            "supply a client (or stub for tests) per AC.OBJX.5"
        )
    else:
        synthesis_result = _empty_synthesis_result(
            extraction_id=config.repo_id, ts=ts
        )

    synthesis_path = ext_dir / "synthesis.yaml"
    synthesis_payload = synthesis_result.model_dump(mode="json")
    synthesis_path.write_text(
        yaml.safe_dump(synthesis_payload, sort_keys=False),
        encoding="utf-8",
    )

    # Persist multi-source bundle for downstream rendering / debug.
    bundle_path = ext_dir / "multi-source-bundle.yaml"
    bundle_path.write_text(
        yaml.safe_dump(bundle.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    # v0.2.3 Cycle 2 — backing-map population post-synthesis.
    # Per AC.BACKMAP.{2,3,7}: populate via heuristic pre-filter +
    # LLM-pass classifier, persist, audit-log. D2 idempotent skip when
    # the prior backing-map's counts match the current run.
    backing_map_persisted_path: Path | None = None
    if synthesis_result.objectives and not config.dry_run:
        from .backing_map import (
            is_idempotent_skip,
            load_backing_map,
            populate_backing_map,
            save_backing_map,
        )

        existing_bm = load_backing_map(ext_dir)
        if anthropic_client is not None and not is_idempotent_skip(
            existing_bm,
            objective_count=len(synthesis_result.objectives),
            total_evidence_rows=len(aggregated_acs),
        ):
            backing_map = populate_backing_map(
                synthesis_result.objectives,
                aggregated_acs,
                extraction_id=config.repo_id,
                anthropic_client=anthropic_client,
                repo_sha=bundle.repo_sha,
                extraction_dir=ext_dir,
                timestamp=ts,
            )
            backing_map_persisted_path = save_backing_map(
                ext_dir, backing_map
            )
        elif existing_bm is not None:
            backing_map_persisted_path = ext_dir / "backing-map.yaml"

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
    # Per AC.OBJX.7: rename artefact key to evidence_rows; keep
    # raw_acs as alias for backward compat readers.
    state.artefacts["evidence_rows"] = evidence_path.relative_to(
        ext_dir
    ).as_posix()
    state.artefacts["raw_acs"] = state.artefacts["evidence_rows"]
    state.artefacts["synthesis"] = synthesis_path.relative_to(
        ext_dir
    ).as_posix()
    state.artefacts["multi_source_bundle"] = bundle_path.relative_to(
        ext_dir
    ).as_posix()
    if backing_map_persisted_path is not None:
        state.artefacts["backing_map"] = backing_map_persisted_path.relative_to(
            ext_dir
        ).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=config.repo_id,
        stage="generate",
        artefact_path=evidence_path.relative_to(ext_dir).as_posix(),
        notes=(
            f"evidence_rows={len(aggregated_acs)} "
            f"unhandled={len(aggregated_unhandled)} "
            f"objectives={len(synthesis_result.objectives)} "
            f"constraints={len(synthesis_result.constraints)} "
            f"capabilities={len(synthesis_result.capabilities)} "
            f"dry_run={config.dry_run}"
        ),
        timestamp=ts,
    )

    return raw


def load_synthesis_result(
    workspace_root: Path, repo_id: str
) -> SynthesisResult:
    """Read the persisted :class:`SynthesisResult` for the verify stage.

    Returns an empty result if the file doesn't exist (preserves the
    test path that runs generate without synthesis).
    """
    ext_dir = extraction_dir(workspace_root, repo_id)
    p = ext_dir / "synthesis.yaml"
    if not p.exists():
        return _empty_synthesis_result(
            extraction_id=repo_id, ts=_now_iso()
        )
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return SynthesisResult.model_validate(data)

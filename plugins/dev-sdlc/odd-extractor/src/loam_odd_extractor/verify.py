"""Stage 4 — verify (v0.2.3 Cycle 1 outcome-altitude rendering).

Per AC.OBJX.10 (sub-plan-doc §3) — Stage 4 reads the
:class:`SynthesisResult` produced by Stage 3 and renders:

- ``contract-draft.md`` with sections per altitude (Objectives →
  Constraints → Capabilities → Evidence-rows summary →
  §self-checks audit table).
- ``contract-draft.yaml`` sidecar carrying typed lists
  (``objectives:`` / ``constraints:`` / ``capabilities:``) AND the
  legacy ``acs:`` field populated with typed Objective rows
  (transitional v0.1.9 PR-safety compat per master plan §6.2).

Cross-reference validation: every ``Capability.serves`` ID must
resolve to a present Objective; raises :class:`StageError` on
dangling reference.

The §self-checks audit table is sourced from
:func:`altitude_validator.validate_altitude` invoked at verify-time
on the synthesis rows. Rows failing checks have their decision
applied and surfaced.

The legacy v0.1.8 markdown shape (used by tests with empty/symbol-
altitude content) is preserved as a fallback for the no-synthesis
test path.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import yaml

from .altitude_validator import validate_altitude
from .backing_map import load_backing_map
from .errors import StageError
from .generate import load_synthesis_result
from .observability import write_audit_entry
from .spec import (
    BackingMap,
    ContractDraft,
    ExtractionConfig,
    RawACs,
    SynthesisResult,
)
from .state import extraction_dir, load_state, save_state


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# ====================================================================
# Cross-reference validation
# ====================================================================


def _check_capability_references(synthesis: SynthesisResult) -> None:
    """Per AC.OBJX.10 — every ``Capability.serves`` ID must resolve.

    Raises :class:`StageError` on dangling reference.
    """
    objective_ids = {o.objective_id for o in synthesis.objectives}
    for c in synthesis.capabilities:
        for ref in c.serves:
            if ref not in objective_ids:
                raise StageError(
                    f"verify: Capability {c.capability_id!r} references "
                    f"unknown objective {ref!r}; known objectives: "
                    f"{sorted(objective_ids)}"
                )


# ====================================================================
# Markdown rendering
# ====================================================================


def _render_legacy_evidence_summary(ev: dict) -> str:
    """Tiny inline summary for an evidence dict in the markdown table."""
    cites = ev.get("citations") or []
    if cites:
        return f"{len(cites)} citation(s)"
    return "(none)"


def _render_backing_map_section(bm: BackingMap | None) -> list[str]:
    """v0.2.3 Cycle 2 (AC.BACKMAP.4) — backing-implementation map section.

    Renders per-objective row counts (STRONG / WEAK / total) + first-3
    path:line previews; orphan section with first-10 paths annotated by
    reason; HYPOTHESISED objectives' empty backing rendered as
    ``(none)``.
    """
    lines: list[str] = []
    lines.append("## Backing-implementation map")
    lines.append("")
    if bm is None:
        lines.append(
            "_No backing-map persisted (population skipped or run "
            "predates v0.2.3 Cycle 2)._"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines
    lines.append(
        f"**Total evidence rows:** {bm.total_evidence_rows} | "
        f"**Objectives:** {bm.objective_count} | "
        f"**Orphans:** {len(bm.orphan_rows)} | "
        f"**Unmatched objectives:** {len(bm.unmatched_objective_ids)}"
    )
    lines.append("")
    lines.append(
        f"**Cost:** {bm.cost_actual_cents:.4f} cents (model "
        f"`{bm.model_id}`)"
    )
    lines.append("")
    if bm.entries:
        lines.append("| objective_id | STRONG | WEAK | total | preview |")
        lines.append("|--------------|--------|------|-------|---------|")
        for entry in bm.entries:
            strong = sum(
                1 for r in entry.evidence_rows if r.confidence == "STRONG"
            )
            weak = sum(
                1 for r in entry.evidence_rows if r.confidence == "WEAK"
            )
            total = len(entry.evidence_rows)
            preview_parts: list[str] = []
            for ref in entry.evidence_rows[:3]:
                if ref.line_range and ref.line_range[0] != ref.line_range[1]:
                    preview_parts.append(
                        f"`{ref.path}:{ref.line_range[0]}-{ref.line_range[1]}`"
                    )
                elif ref.line_range:
                    preview_parts.append(
                        f"`{ref.path}:{ref.line_range[0]}`"
                    )
                else:
                    preview_parts.append(f"`{ref.path}`")
            preview = ", ".join(preview_parts) if preview_parts else "(none)"
            lines.append(
                f"| `{entry.objective_id}` | {strong} | {weak} | {total} | "
                f"{preview} |"
            )
        lines.append("")
    if bm.unmatched_objective_ids:
        lines.append(
            "**Unmatched objectives** (non-HYPOTHESISED with empty "
            "backing — gap-analysis input for v0.2.4):"
        )
        for oid in bm.unmatched_objective_ids:
            lines.append(f"- `{oid}`")
        lines.append("")
    if bm.orphan_rows:
        lines.append(
            f"**Orphan evidence rows** ({len(bm.orphan_rows)}; first 10):"
        )
        lines.append("")
        lines.append("| evidence_row_id | reason | path |")
        lines.append("|-----------------|--------|------|")
        for orow in bm.orphan_rows[:10]:
            lines.append(
                f"| `{orow.evidence_row_id}` | {orow.reason} | "
                f"`{orow.path}` |"
            )
        lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def _render_outcome_altitude_markdown(
    *,
    config: ExtractionConfig,
    raw: RawACs,
    synthesis: SynthesisResult,
    altitude_report: Any,
    backing_map: BackingMap | None = None,
) -> str:
    """Render the v0.2.3 outcome-altitude contract draft.

    Sections per AC.OBJX.10: Objectives → Constraints → Capabilities
    → Evidence-rows summary → §self-checks audit table.
    """
    lines: list[str] = []
    lines.append(f"# Contract draft — {config.repo_path.name}")
    lines.append("")
    lines.append(
        "**Status:** DRAFT — auto-generated by `loam odd-extract` "
        "v0.2.3 (multi-source objective synthesis)."
    )
    lines.append("")
    lines.append(f"**Repo path:** `{config.repo_path}`")
    lines.append(f"**Repo ID:** `{config.repo_id}`")
    lines.append(f"**Generated at:** {raw.created_at}")
    lines.append(f"**Dry run:** {config.dry_run}")
    lines.append(f"**Synthesis model:** `{synthesis.model_id}`")
    lines.append(
        f"**Synthesis cost:** {synthesis.cost_actual_cents:.4f} cents "
        f"({synthesis.token_count_input} input + "
        f"{synthesis.token_count_output} output tokens)"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Objectives section
    lines.append("## Objectives (outcome altitude)")
    lines.append("")
    lines.append("<!-- OBJECTIVES_TABLE_HERE -->")
    lines.append("")
    if synthesis.objectives:
        lines.append("| ID | Domain | Band | Text |")
        lines.append("|----|--------|------|------|")
        for o in synthesis.objectives:
            txt = o.text.replace("|", "\\|")
            lines.append(
                f"| `{o.objective_id}` | {o.domain} | {o.confidence.value} | {txt} |"
            )
        lines.append("")
        for o in synthesis.objectives:
            lines.append(f"### {o.objective_id} — {o.confidence.value}")
            lines.append("")
            lines.append(f"**Domain:** {o.domain}")
            lines.append("")
            lines.append(f"**Text:** {o.text}")
            lines.append("")
            ev = o.evidence
            if ev.test_name_refs:
                lines.append("- **Test refs:**")
                for r in ev.test_name_refs:
                    lines.append(f"  - `{r}`")
            if ev.readme_excerpts:
                lines.append("- **README excerpts:**")
                for r in ev.readme_excerpts:
                    excerpt = r if len(r) <= 200 else r[:200] + "…"
                    lines.append(f"  - {excerpt!r}")
            if ev.design_doc_refs:
                lines.append("- **Design doc refs:**")
                for r in ev.design_doc_refs:
                    lines.append(f"  - `{r}`")
            if ev.survey_line_refs:
                lines.append("- **Survey lines:**")
                for r in ev.survey_line_refs:
                    lines.append(f"  - {r}")
            if ev.code_pattern_refs:
                lines.append("- **Code pattern refs:**")
                for r in ev.code_pattern_refs:
                    lines.append(f"  - `{r}`")
            if ev.repo_sha:
                lines.append(f"- **Repo SHA:** `{ev.repo_sha}`")
            if ev.rationale:
                lines.append(f"- **Rationale:** {ev.rationale}")
            lines.append("")
    else:
        lines.append(
            "_No objectives synthesized in this run._"
        )
        lines.append("")
    lines.append("---")
    lines.append("")

    # Constraints section
    lines.append("## Constraints")
    lines.append("")
    if synthesis.constraints:
        lines.append("| ID | Bounds | Text |")
        lines.append("|----|--------|------|")
        for k in synthesis.constraints:
            txt = k.text.replace("|", "\\|")
            lines.append(
                f"| `{k.constraint_id}` | {k.bounds_kind} | {txt} |"
            )
        lines.append("")
    else:
        lines.append("_No constraints synthesized._")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Capabilities section
    lines.append("## Capabilities")
    lines.append("")
    if synthesis.capabilities:
        lines.append("| ID | Serves | Text |")
        lines.append("|----|--------|------|")
        for c in synthesis.capabilities:
            txt = c.text.replace("|", "\\|")
            serves = ", ".join(f"`{s}`" for s in c.serves)
            lines.append(f"| `{c.capability_id}` | {serves} | {txt} |")
        lines.append("")
    else:
        lines.append("_No capabilities synthesized._")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Evidence-rows summary
    lines.append("## Evidence rows (symbol-altitude)")
    lines.append("")
    lines.append(
        f"**Count:** {len(raw.acs)} adapter-emitted rows in "
        f"`evidence-rows.yaml` (Cycle 2 backing-map population)."
    )
    lines.append("")
    if raw.acs:
        # Show first 10 + count for huge sets.
        first_n = raw.acs[:10]
        lines.append("| ac_id | band | evidence kind |")
        lines.append("|-------|------|---------------|")
        for ac in first_n:
            ac_id = ac.get("ac_id", "(unnamed)")
            band = ac.get("confidence", "?")
            ev = ac.get("evidence", {}) or {}
            kind = ev.get("kind", "?")
            lines.append(f"| `{ac_id}` | {band} | {kind} |")
        if len(raw.acs) > 10:
            lines.append("")
            lines.append(
                f"_… {len(raw.acs) - 10} more rows in `evidence-rows.yaml`._"
            )
        lines.append("")
    lines.append("---")
    lines.append("")

    # v0.2.3 Cycle 2 — Backing-implementation map (AC.BACKMAP.4).
    lines.extend(_render_backing_map_section(backing_map))

    # §self-checks audit table
    lines.append("## §self-checks audit (altitude validator)")
    lines.append("")
    if altitude_report is not None:
        lines.append(
            f"**Total rows:** {altitude_report.total_rows} | "
            f"**Pass:** {altitude_report.pass_count} | "
            f"**Fail:** {altitude_report.fail_count} | "
            f"**Borderline:** {altitude_report.borderline_count}"
        )
        lines.append("")
        lines.append(
            f"**Pass rate:** {altitude_report.pass_rate:.2%} "
            f"(threshold {altitude_report.fail_threshold:.0%}; "
            f"drift halt: {altitude_report.drift_halt_triggered})"
        )
        lines.append("")
        if altitude_report.results:
            lines.append("| row_id | kind | classification | failed | decision | reason |")
            lines.append("|--------|------|----------------|--------|----------|--------|")
            for r in altitude_report.results:
                lines.append(
                    f"| `{r.row_id}` | {r.row_kind} | "
                    f"{r.classification} | "
                    f"{'-' if r.failed_check is None else r.failed_check} | "
                    f"{r.decision} | "
                    f"{r.rationale.replace('|', '\\|') if r.rationale else ''} |"
                )
            lines.append("")
    else:
        lines.append("_Altitude validator not invoked (no synthesis)._")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Unhandled paths
    lines.append("## Unhandled paths")
    lines.append("")
    if raw.unhandled_paths:
        lines.append(
            f"_{len(raw.unhandled_paths)} path(s) had no language "
            "adapter coverage:_"
        )
        lines.append("")
        for p in raw.unhandled_paths[:50]:
            lines.append(f"- `{p}`")
        if len(raw.unhandled_paths) > 50:
            lines.append(
                f"- _… {len(raw.unhandled_paths) - 50} more in sidecar._"
            )
        lines.append("")
    else:
        lines.append("_No unhandled paths._")
        lines.append("")
    lines.append("---")
    lines.append("")

    # Provenance
    lines.append("## Provenance")
    lines.append("")
    lines.append(
        "- v0.2.3 sub-plan-doc: "
        "`docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`"
    )
    lines.append(
        "- ODD lean grounding: `docs/odd-llm-grounding.lean.md`"
    )
    lines.append(
        "- Per-extraction artefacts: `<workspace>/.loam/extractions/"
        f"{config.repo_id}/`"
    )
    lines.append("")
    return "\n".join(lines)


def _render_legacy_markdown(
    *,
    config: ExtractionConfig,
    raw: RawACs,
) -> str:
    """v0.1.8 fallback rendering for tests that don't run synthesis.

    Preserved unchanged from the v0.1.8 substrate — empty / symbol-
    altitude content paths used by the existing test suite.
    """
    lines: list[str] = []
    lines.append(f"# Contract draft — {config.repo_path.name}")
    lines.append("")
    lines.append(
        "**Status:** DRAFT — auto-generated by `loam odd-extract` "
        "v0.2.3 (legacy-fallback no-synthesis path)."
    )
    lines.append("")
    lines.append(f"**Repo path:** `{config.repo_path}`")
    lines.append(f"**Repo ID:** `{config.repo_id}`")
    lines.append(f"**Generated at:** {raw.created_at}")
    lines.append(f"**Dry run:** {config.dry_run}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("")
    lines.append("<!-- ACS_TABLE_HERE -->")
    lines.append("")
    if raw.acs:
        all_banded = all(
            isinstance(ac, dict) and "confidence" in ac
            for ac in raw.acs
        )
        if all_banded:
            lines.append("| AC | Band | Evidence kind | Citations |")
            lines.append("|----|------|---------------|-----------|")
            for ac in raw.acs:
                ac_id = ac.get("ac_id", "(unnamed)")
                band = ac.get("confidence", "?")
                ev = ac.get("evidence", {}) or {}
                kind = ev.get("kind", "?")
                cites_summary = _render_legacy_evidence_summary(ev)
                lines.append(
                    f"| {ac_id} | {band} | {kind} | {cites_summary} |"
                )
            lines.append("")
            for ac in raw.acs:
                ac_id = ac.get("ac_id", "(unnamed)")
                band = ac.get("confidence", "?")
                lines.append(f"### {ac_id} — {band}")
                lines.append("")
                lines.append(f"**Text:** {ac.get('text', '')}")
                lines.append("")
                ev = ac.get("evidence", {}) or {}
                lines.append(f"- **Evidence kind:** {ev.get('kind', '?')}")
                cites = ev.get("citations") or []
                if cites:
                    lines.append(f"- **Citations:** {len(cites)} entries")
                    for c in cites:
                        lines.append(f"  - `{c}`")
                if ev.get("repo_sha"):
                    lines.append(f"- **Repo SHA:** `{ev['repo_sha']}`")
                if ev.get("rationale"):
                    lines.append(f"- **Rationale:** {ev['rationale']}")
                if ac.get("backing_files"):
                    lines.append(
                        f"- **Backing files:** "
                        f"{len(ac['backing_files'])} file(s)"
                    )
                lines.append("")
        else:
            lines.append("(Cycle 1 raw shape — bands not yet attached.)")
            lines.append("")
            for idx, ac in enumerate(raw.acs, 1):
                lines.append(f"### AC.{idx}")
                lines.append("")
                for k, v in ac.items():
                    lines.append(f"- **{k}:** {v}")
                lines.append("")
    else:
        lines.append(
            "_No ACs extracted in this run._"
        )
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Unhandled paths")
    lines.append("")
    lines.append("<!-- COVERAGE_GAPS_HERE -->")
    lines.append("")
    if raw.unhandled_paths:
        lines.append(
            f"_{len(raw.unhandled_paths)} path(s) had no language "
            "adapter coverage:_"
        )
        lines.append("")
        for p in raw.unhandled_paths:
            lines.append(f"- `{p}`")
        lines.append("")
    else:
        lines.append("_No unhandled paths._")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(
        "- Plan-doc: "
        "`docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`"
    )
    lines.append(
        "- Per-stage artefacts: `<workspace>/.loam/extractions/"
        f"{config.repo_id}/`"
    )
    lines.append("")
    return "\n".join(lines)


# ====================================================================
# Verify entry-point
# ====================================================================


def verify_contract(
    *,
    config: ExtractionConfig,
    raw: RawACs,
    timestamp: str | None = None,
    synthesis: SynthesisResult | None = None,
) -> ContractDraft:
    """Run Stage 4 — verify (v0.2.3 outcome-altitude rendering).

    Returns :class:`ContractDraft`; writes ``contract-draft.md`` and
    ``contract-draft.yaml`` artefacts; appends ``stage_complete``,
    ``altitude_check_complete`` (when synthesis present), +
    ``extraction_end`` audit-log entries; updates ``state.yaml``.

    When ``synthesis`` is ``None``, attempts to load
    ``synthesis.yaml`` from the extraction-dir (Stage 3 output);
    falls back to an empty synthesis result if missing — preserves
    the v0.1.8 test path that runs verify in isolation without a
    synthesis call.

    Per AC.OBJX.10: Capability cross-references resolved against
    Objective IDs; dangling references raise :class:`StageError`.
    Per AC.OBJX.8: altitude validator runs at verify-time and
    surfaces drift halts.

    ``timestamp`` is injectable for deterministic tests.
    """
    ext_dir = extraction_dir(config.workspace_root, config.repo_id)
    ts = timestamp if timestamp is not None else _now_iso()

    # Backing-paths shape check (preserved from v0.1.8).
    backed_paths: set[str] = set()
    for ac in raw.acs:
        for p in ac.get("backing_files", []) or []:
            backed_paths.add(str(p))
    if not isinstance(raw.unhandled_paths, list):
        raise StageError(
            "verify: raw-acs.unhandled_paths is not a list — "
            "extraction state is malformed"
        )

    # Resolve synthesis result.
    if synthesis is None:
        synthesis = load_synthesis_result(
            config.workspace_root, config.repo_id
        )

    altitude_report = None
    if (
        synthesis.objectives
        or synthesis.constraints
        or synthesis.capabilities
    ):
        # AC.OBJX.10 — cross-reference integrity.
        _check_capability_references(synthesis)
        # AC.OBJX.8 — altitude validation at verify-time.
        altitude_report = validate_altitude(
            extraction_id=config.repo_id,
            objectives=synthesis.objectives,
            constraints=synthesis.constraints,
            capabilities=synthesis.capabilities,
        )
        # AC.OBJX.12 — audit-log entry.
        write_audit_entry(
            ext_dir,
            event_kind="altitude_check_complete",
            extraction_id=config.repo_id,
            stage="generate",
            estimate={
                "total_rows": altitude_report.total_rows,
                "pass_count": altitude_report.pass_count,
                "fail_count": altitude_report.fail_count,
                "borderline_count": altitude_report.borderline_count,
                "pass_rate": altitude_report.pass_rate,
                "dropped_count": altitude_report.dropped_count,
                "downgraded_count": altitude_report.downgraded_count,
                "drift_halt_triggered": altitude_report.drift_halt_triggered,
            },
            timestamp=ts,
        )

    # v0.2.3 Cycle 2 (AC.BACKMAP.4) — load backing-map for rendering.
    backing_map = load_backing_map(ext_dir)

    # Render markdown.
    if (
        synthesis.objectives
        or synthesis.constraints
        or synthesis.capabilities
    ):
        markdown = _render_outcome_altitude_markdown(
            config=config,
            raw=raw,
            synthesis=synthesis,
            altitude_report=altitude_report,
            backing_map=backing_map,
        )
    else:
        # Test path / empty-synthesis path: v0.1.8 fallback.
        markdown = _render_legacy_markdown(config=config, raw=raw)

    md_path = ext_dir / "contract-draft.md"
    md_path.write_text(markdown, encoding="utf-8")

    # Per v0.2.3 Cycle 3 + master plan §6.2 — legacy ``acs:`` field
    # retired. PR-safety reads ``objectives.yaml`` + ``backing-map.yaml``
    # directly. ``contract-draft.yaml`` shrinks to a top-level
    # summary; ``objectives.yaml`` is the canonical authority for
    # downstream consumers.

    # Top-level contract-draft.yaml summary (canonical handle).
    sidecar_payload: dict[str, Any] = {
        "schema_version": 2,  # bumped: legacy `acs:` field retired.
        "extraction_id": config.repo_id,
        "repo_path": str(config.repo_path),
        "ac_count": len(synthesis.objectives),
        "objective_count": len(synthesis.objectives),
        "constraint_count": len(synthesis.constraints),
        "capability_count": len(synthesis.capabilities),
        "unhandled_count": len(raw.unhandled_paths),
        "dry_run": config.dry_run,
        "created_at": ts,
        "synthesis_model_id": synthesis.model_id,
        "synthesis_cost_actual_cents": synthesis.cost_actual_cents,
    }
    if altitude_report is not None:
        sidecar_payload["altitude_report_summary"] = {
            "total_rows": altitude_report.total_rows,
            "pass_count": altitude_report.pass_count,
            "fail_count": altitude_report.fail_count,
            "pass_rate": altitude_report.pass_rate,
            "drift_halt_triggered": altitude_report.drift_halt_triggered,
        }

    yaml_path = ext_dir / "contract-draft.yaml"
    yaml_path.write_text(
        yaml.safe_dump(sidecar_payload, sort_keys=False),
        encoding="utf-8",
    )

    # Canonical objectives.yaml (PR-safety + watch read this directly).
    objectives_path = ext_dir / "objectives.yaml"
    objectives_payload = {
        "schema_version": 1,
        "extraction_id": config.repo_id,
        "repo_path": str(config.repo_path),
        "created_at": ts,
        "objectives": [
            o.model_dump(mode="json") for o in synthesis.objectives
        ],
        "constraints": [
            k.model_dump(mode="json") for k in synthesis.constraints
        ],
        "capabilities": [
            c.model_dump(mode="json") for c in synthesis.capabilities
        ],
    }
    objectives_path.write_text(
        yaml.safe_dump(objectives_payload, sort_keys=False),
        encoding="utf-8",
    )

    draft = ContractDraft(
        extraction_id=config.repo_id,
        markdown_path=md_path,
        sidecar_path=yaml_path,
        ac_count=len(synthesis.objectives),
        unhandled_count=len(raw.unhandled_paths),
        created_at=ts,
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
            generate_complete=True,
        )
    state.verify_complete = True
    state.last_updated_at = ts
    state.artefacts["contract_md"] = md_path.relative_to(ext_dir).as_posix()
    state.artefacts["contract_yaml"] = yaml_path.relative_to(ext_dir).as_posix()
    state.artefacts["objectives"] = objectives_path.relative_to(
        ext_dir
    ).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=config.repo_id,
        stage="verify",
        artefact_path=md_path.relative_to(ext_dir).as_posix(),
        notes=(
            f"objective_count={len(synthesis.objectives)} "
            f"constraint_count={len(synthesis.constraints)} "
            f"capability_count={len(synthesis.capabilities)} "
            f"unhandled_count={len(raw.unhandled_paths)}"
        ),
        timestamp=ts,
    )
    write_audit_entry(
        ext_dir,
        event_kind="extraction_end",
        extraction_id=config.repo_id,
        notes=f"dry_run={config.dry_run}",
        timestamp=ts,
    )

    return draft

# v0.1.8 Cycle 2 — Confidence bands + ratification workflow

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** Cycle 1 sealed at `c1abda1` (odd-extractor scaffolding). Master plan `docs/rebuild/plans/v0-1-8-master-plan.md` sealed at `1c2c478`; §9 backfilled at `774d465`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-1-8-master-plan.md` §3 + §4 Cycle 2.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-2-status-2026-05-04.md`.

**Quality bar (load-bearing):** "WOW Eric. No partial features. No excuses." — Luke 2026-05-04. The bands schema + ratification workflow ship COMPLETE; if any AC ships partial we halt and surface.

**Dispatch path divergence (recorded).** The master plan §4 Cycle 2 dispatch brief names sub-plan path `v0-1-8-cycle-2-bands-and-ratification.md`; the live dispatch from the parent agent names `v0-1-8-cycle-2-confidence-bands-and-ratification.md`. The parent agent's path is canonical for this build (longer slug; matches the dispatch authored 2026-05-04). The manifest and §14 backfill use the same canonical slug.

---

## §1 — Outcome shape (the "why")

v0.1.8 Cycle 1 shipped the extractor's shape without content — four-stage workflow, language-adapter registry (zero adapters), dry-run cost estimate, foreign-codebase budget envelope. Contract drafts ship with a skeleton markdown carrying named anchor comments (`<!-- ACS_TABLE_HERE -->`, `<!-- COVERAGE_GAPS_HERE -->`) for Cycle 2 to inject into.

Cycle 2 lands the **bands shape and the ratification workflow** — every AC in a contract draft carries a `confidence: VERIFIED | PLAUSIBLE | HYPOTHESISED` field with a structured `evidence:` block; every band promotion is mediated by the per-project PM's one-question-at-a-time decision queue from v0.1.7 Cycle 4; every ratification action lands in the SOC-2 audit-trail floor established in v0.1.6 production-stake mode. The master plan calls these out as `AC.BANDS.{1..7}`.

Cycle 2's release-note promise: a synthetic banded contract draft (built by a stubbed test source, since adapters land in Cycles 3+4) can be ratified end-to-end via `loam odd-extract ratify <contract-draft>`; the ratification surfaces one AC's promotion question at a time through the PM's decision queue; PLAUSIBLE→VERIFIED promotion requires owner explicit yes (default-no per Decision I); every promote/demote/edit/reject action writes an audit-log entry; partial batches resume across `/clear`.

The shape is the deliverable. The content (Ruby/Python adapters that *populate* bands from real codebases) is explicitly not in this cycle's fence — Cycle 1's ContractDraft skeleton plus Cycle 2's banded schema plus a stubbed banded fixture is sufficient to test the ratification flow end-to-end.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

Cycle 2 composes on top of Claude-native primitives + already-shipped loam machinery:

- **`framework/per-project-pm/` (v0.1.7 Cycles 2 + 4).** The PM's `decision-queue.yaml` + `surface_next_questions_batch()` + `record_response()` are the substrate the ratification workflow rides on. No re-implementation of question-batching, audit-log entry shape, or response-recording. Ratification batches enqueue questions with provenance pointing back to the contract-draft's AC; the PM surfaces them one at a time per `onboarding_mode` / `max_questions_per_turn` policy; `record_response()` closes the loop and flips the AC's band.
- **Cycle 1's audit-log primitive.** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/observability.py:write_audit_entry()` already writes per-stage / per-run entries; Cycle 2 extends with new `event_kind` values (`ratification_promote`, `ratification_demote`, `ratification_edit`, `ratification_reject`, `ratification_resume`) without changing the schema or filename pattern.
- **Cycle 1's state machine + extraction directory layout.** `<workspace>/.loam/extractions/<repo-id>/` already exists; Cycle 2 adds two artefacts (`ratification-state.yaml` for resume, plus the `audit-log/` extension is already in place). No new top-level workspace root.
- **v0.1.6 cost-governance dry-run.** Ratification is text-only and free; no cost-governance call is needed at the ratification call site. Cited for completeness.

The required research question — **"What Claude capability does this lean on or extend?"** — answer: per-project-PM's one-question-at-a-time + audit-log primitives + Cycle 1's extraction-state directory + audit-log writer. All four are composed; no re-implementation.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops materially because the persona no longer has to author + sequence the user's ratification questions itself — the PM's queue + one-at-a-time discipline handles it. The persona's job becomes "relay one question at a time, capture the user's reply, call `record_response()`, repeat." Cycle 2 ships the toolkit; persona-side wiring lands at v0.2.0+ per parent plan (PM persona-side flow integration is out of v0.1.7 Cycle 4 scope).
- **Harness test:** every persona that wants to ratify a banded contract draft can call `loam.odd_extractor.ratify.enqueue_ratification_batch(contract_draft, pm_runtime)` — a public API that converts a `ContractDraft`'s pending-band ACs into PM decision-queue entries. The toolkit composes; nothing is hand-rolled per persona.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§8) + acceptance smoke (§6). Method (CLI verb shape, schema field naming, ratification-state file path) stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 + §4 Cycle 2 names every AC with explicit field semantics and the PM-mediated batch contract. Tight scope: extend the odd-extractor with band schema + ratify subpackage; extend per-project-pm with a thin ratification-batch helper that enqueues from a ContractDraft. Halt-and-surface if the master plan's named contract turns out unimplementable.

Outcome confidence is **MEDIUM** on three points (recorded as halt-surfaces in §5):

1. The ratification CLI's exact verb / flag shape — master plan names `loam odd-extract ratify <contract-draft>` but the flag surface for promote/demote/edit/reject is the builder's call. Method stays inferable from constraints.
2. The "stubbed test source" for banded ACs — Cycle 2 needs a fixture-banded contract to exercise ratification, but the master plan doesn't constrain whether that's a hand-authored YAML, a test helper, or both. Builder picks the cheapest shape that satisfies all 7 ACs (see Surface #2 in §5).
3. The ratification-state file format — Cycle 1's state.yaml is per-run; Cycle 2's ratification-state may extend that file or live separately. Builder picks (see Surface #4).

The Pydantic models for `ConfidenceBand` and `Evidence` ship LOOSE — strict on the band enum (literal three values), looser on the evidence block (Cycles 3+4 will need richer fields per language). Schema versions if necessary.

### Lens 5 — Swarming

Two-component fence (per master plan + dispatch). Within the cycle, decomposition options:

- (a) per-component (odd-extractor schema + ratify package; per-project-pm ratification-batch helper). Each component has its own seal-test + own AC-test files; meets stopping criterion.
- (b) per-AC-family (band schema + ratification CLI + PM integration + audit-log + workflow + idempotency + cross-session). Tighter decomposition — but the AC families overlap heavily on shared infrastructure (the audit-log primitive is used by 4 of 7 ACs; the PM helper is used by 3 of 7), so (b) introduces coordination overhead without tightening any subtask's scope. Stopping criterion fires.

Builder picks (a) — per-component decomposition matches the two-component fence + gives the right granularity for two parallel-readable test surfaces. `max_planner_depth: 1` (no sub-planners; per-component organization is the right granularity already). No further decomposition adds value.

---

## §3 — Two-component fence (serialized per `feedback_serialize_amendment_builds`)

**Primary fence:** `plugins/dev-sdlc/odd-extractor/` (the band schema + ratify subpackage; new files + minor edits to existing `verify.py` to band-tag the contract-draft template).

**Secondary fence:** `framework/per-project-pm/` (a thin ratification-batch helper that takes a `ContractDraft` + a `PMRuntime` and enqueues per-AC questions through `enqueue_decision`). The PM's runtime + state.yaml + decision-queue.yaml schemas don't change — Cycle 2 only adds a helper module and re-exports.

**Manifest names both** (single manifest, two `components:` entries, single seal commit).

**New paths (this cycle):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` — Pydantic models (`ConfidenceBand` enum literal `VERIFIED|PLAUSIBLE|HYPOTHESISED`; `Evidence` block; `BandedAC` extending the dict-typed AC shape).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/ratify.py` — ratification subpackage: `enqueue_ratification_batch(draft, pm_runtime)`, `apply_ratification_action(draft, action)`, plus the per-action verb functions (`promote`, `demote`, `edit`, `reject`).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/ratification_state.py` — separate state file at `<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml` for resume across `/clear` (see §5 Surface #4 for the rationale).
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_1_band_schema.py` — band field + evidence block on each AC.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_2_band_evidence_rules.py` — VERIFIED/PLAUSIBLE/HYPOTHESISED evidence requirements.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_3_methodology_doc_extension.py` — `docs/odd-methodology.md` carries the band semantics extension (loaded via `pathlib`, content-asserted).
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_4_ratification_cli.py` — `loam odd-extract ratify <contract-draft>` invocable; PM-mediated batch.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_5_promotion_default_no.py` — PLAUSIBLE→VERIFIED requires explicit yes; silent promotion refused.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_6_audit_log_per_action.py` — every ratification action writes an audit-log entry.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_BANDS_7_pm_integration.py` — ratification batches surface through PM's decision-queue; one-question-at-a-time per Decision Q.
- `plugins/dev-sdlc/odd-extractor/tests/test_ratification_resume_cross_session.py` — D5 cross-session smoke (partial batch resumable).
- `plugins/dev-sdlc/odd-extractor/tests/test_ratification_steady_state.py` — D2 steady-state-variant: 5+ promotions in sequence are idempotent; queue depth bounded.
- `plugins/dev-sdlc/odd-extractor/tests/fixtures/synthetic-banded-contract.md` — hand-authored fixture drafting a banded contract with 1 VERIFIED + 1 PLAUSIBLE + 1 HYPOTHESISED AC (and matching `synthetic-banded-contract.yaml` sidecar).
- `framework/per-project-pm/src/loam/per_project_pm/ratification.py` — `RatificationBatch` builder helper that converts `(ContractDraft, list[BandedAC])` into PM decision-queue entries with structured provenance.
- `framework/per-project-pm/tests/test_AC_BANDS_PM_integration.py` — programmatic test that the helper round-trips through the PM queue + audit-log.

**Edits to existing dev-sdlc paths (universal-admitted within fence):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py` — extend `RawACs.acs` doc-comment to reference the `BandedAC` shape; add `BandedAC` re-export from `bands.py`. (No schema migration — Cycle 1's `acs: list[dict]` already accommodates band fields additively.)
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/verify.py` — extend `_render_contract_markdown()` to inject band-tagged AC rows when `raw.acs` carries `confidence` keys (replaces the "Cycle 2+ will band-tag these ACs" stub at line 67). Anchor `<!-- ACS_TABLE_HERE -->` becomes the injection point per Cycle 1 plan §10 RF gap #3.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — re-export `ConfidenceBand`, `Evidence`, `BandedAC`, `enqueue_ratification_batch`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — add `ratify` sub-verb under the existing `loam odd-extract` parser; routes to `_cmd_ratify`.
- `plugins/dev-sdlc/odd-extractor/README.md` — add a "Ratification workflow" subsection naming the new public API.
- `plugins/dev-sdlc/docs/odd-methodology.md` — append §11 "Confidence bands for derived ACs" (the universal-admitted doc edit per AC.BANDS.3; the manifest's universal_paths.files admits this path explicitly).

**Edits to existing per-project-pm paths (within fence):**

- `framework/per-project-pm/src/loam/per_project_pm/__init__.py` — re-export `RatificationBatch`.
- `framework/per-project-pm/README.md` — add a "Ratification batches (Cycle 2 of v0.1.8 odd-extractor)" subsection.

**Composition (read-only, no edit):**

- `framework/cost-governance/` — no changes; ratification is text-only + free.

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/rebuild/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md` (top-level), `docs/rebuild/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any `framework/` component edit other than `framework/per-project-pm/` (and read-only imports of cost-governance).
- Any other `plugins/` component edit (e.g., `plugins/loam-skills/`).
- Any actual language-adapter implementation (Cycles 3+4).
- Any change to v0.1.7 Cycle 4's PM contract (the runtime + state.yaml + decision-queue.yaml schemas) — Cycle 2 only adds a helper module on top.

**Serialization rule.** Per `feedback_serialize_amendment_builds`, two-component fence builds in one working tree must serialize: the build agent edits both components in one pass (one feature commit covering both), then runs the manifest+apply (single commit per AC.DPS1.6 v3 schema), then seals (single seal commit covering both components). No parallel build agents.

---

## §4 — AC family — `AC.BANDS.*` (locked)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.BANDS.1 — Banded AC schema.**
  - `bands.py` exposes `ConfidenceBand` (str enum literal `VERIFIED|PLAUSIBLE|HYPOTHESISED`) and `Evidence` Pydantic model with `ConfigDict(extra="forbid")`.
  - `BandedAC` Pydantic model carries: `ac_id: str` (required, non-empty), `text: str` (required, non-empty, the AC's prose), `confidence: ConfidenceBand` (required), `evidence: Evidence` (required), plus `backing_files: list[Path] = []` (preserves Cycle 1's coverage-check field shape).
  - `Evidence` carries: `kind: Literal["test", "source", "inference"]` matching the band (VERIFIED → test; PLAUSIBLE → source; HYPOTHESISED → inference); `citations: list[str]` (file paths + line numbers + test names); `repo_sha: str | None` (non-null for VERIFIED — pinned at extraction time); `rationale: str | None` (non-null for HYPOTHESISED — LLM-derived explanation).
  - `BandedAC.model_dump()` produces a dict that round-trips through `RawACs.acs` (Cycle 1's `list[dict]`) without schema migration.
  - Test: instantiate each band variant; round-trip via `model_dump()` / `model_validate()`; reject malformed (missing required fields).

- **AC.BANDS.2 — Per-band evidence requirements (structural enforcement).**
  - Pydantic `model_validator(mode="after")` on `BandedAC` rejects: VERIFIED without `repo_sha` set; VERIFIED with `Evidence.kind != "test"`; PLAUSIBLE with `Evidence.kind != "source"`; HYPOTHESISED without non-empty `rationale`; HYPOTHESISED with `Evidence.kind != "inference"`.
  - Citations list non-empty for VERIFIED + PLAUSIBLE (HYPOTHESISED may legitimately have no citations — pure inference).
  - Test: each rejection path raises `pydantic.ValidationError` with a message naming the offending field; happy-path constructions pass for all three bands.

- **AC.BANDS.3 — Methodology doc extension.**
  - `plugins/dev-sdlc/docs/odd-methodology.md` carries a new §11 "Confidence bands for derived ACs" (or a new top-level section — builder picks naming) covering: what each band means; what evidence is required for each; when promotion (band-up) is appropriate; when demotion (band-down) is appropriate; when re-extension applies (composes with §4 re-extension pattern).
  - The section names the three bands by exact spelling; names `evidence:` block with `kind` / `citations` / `repo_sha` / `rationale` field names verbatim; cross-references the ratification workflow's CLI verb (`loam odd-extract ratify`) by exact spelling.
  - Test: load the doc; assert every required content marker is present (band names; field names; CLI verb; cross-reference back to §4 re-extension pattern). Content-grep test, not prose-quality test.

- **AC.BANDS.4 — Ratification CLI invocable + PM-mediated batch.**
  - `loam odd-extract ratify <contract-draft-path>` is a new sub-verb under the existing `loam odd-extract` parser. Flags: `--pm-name <handle>` (required when the workspace has multiple PMs; auto-resolved to the only PM if exactly one is authored); `--workspace-root <path>`; `--auto-promote` (advisory; rejected unless explicit `--allow-auto` per Decision I — see AC.BANDS.5); `--json` for machine-readable output.
  - The CLI loads the contract-draft (markdown + sidecar YAML; the sidecar carries the `BandedAC` list); invokes `enqueue_ratification_batch(draft, pm_runtime)`; reports the count of pending decisions + the next surfaced question; exits with status 0.
  - When the PM has `onboarding_mode=True`, exactly 1 question surfaces per call; the CLI exits and the persona resumes via `loam odd-extract ratify --resume <draft>` after the user responds (which the PM records via `record_response()`).
  - Test: CLI invocation with a synthetic banded contract enqueues 3 decisions (matching the fixture's 3 ACs); first surfacing returns the expected text; subsequent surfacings respect `onboarding_mode` / `max_questions_per_turn`. End-to-end with a real `PMRuntime` constructed against a tmp workspace.

- **AC.BANDS.5 — PLAUSIBLE → VERIFIED requires explicit yes (default-no per Decision I).**
  - `apply_ratification_action(draft, action)` where `action.kind="promote" and action.from_band="PLAUSIBLE" and action.to_band="VERIFIED"` requires `action.explicit_yes=True`; otherwise raises `RatificationRefusedError` with a message naming the AC + the missing-explicit-yes condition.
  - Silent promotion shapes (e.g., "promote all PLAUSIBLE without per-AC review") are refused at the action-construction layer (`promote()` factory rejects `from_band="PLAUSIBLE"` + `to_band="VERIFIED"` without `explicit_yes=True`).
  - All other promotions (HYPOTHESISED→PLAUSIBLE, HYPOTHESISED→VERIFIED, etc.) and demotions remain default-allow.
  - Test: each rejection path raises `RatificationRefusedError`; happy-path with `explicit_yes=True` succeeds; demotion VERIFIED→PLAUSIBLE requires no explicit-yes (Decision I is asymmetric — only PLAUSIBLE→VERIFIED is gated).

- **AC.BANDS.6 — Audit log per ratification action (SOC-2 floor per Decision P).**
  - Every `apply_ratification_action(draft, action)` call writes one audit-log entry under `<workspace>/.loam/extractions/<repo-id>/audit-log/` via the existing `write_audit_entry` primitive.
  - `event_kind` enum extended with: `ratification_promote`, `ratification_demote`, `ratification_edit`, `ratification_reject`, `ratification_resume`.
  - Each entry carries: standard fields (schema_version, timestamp, extraction_id) + `ac_id` + `from_band` + `to_band` (where applicable) + `actor` (`user` | `system`; system-actor for PLAUSIBLE→VERIFIED is impossible per AC.BANDS.5) + `pm_audit_path` (relative path to the PM-side `record_response` audit entry that backs this action; `None` when the action is system-internal).
  - Test: every action variant writes one entry; entries parse as YAML; sequence is monotonic (filename `<NNNN>.yaml`); schema_version=1 preserved.

- **AC.BANDS.7 — PM integration: ratification batches surface through PM's decision-queue (one-question-at-a-time per Decision Q).**
  - `framework/per-project-pm/src/loam/per_project_pm/ratification.py` exposes `RatificationBatch.from_contract_draft(draft: ContractDraft, banded_acs: list[BandedAC]) -> RatificationBatch` which produces a list of `(question_text, provenance)` pairs.
  - `enqueue(pm_runtime: PMRuntime) -> int` calls `pm_runtime.enqueue_decision(...)` for each pair and returns the count.
  - Provenance shape: `f"odd-extract:{extraction_id}:{ac_id}"` so the persona can route a recorded response back to the correct AC.
  - The persona-side flow is: `enqueue_ratification_batch(draft, pm)` → `pm.surface_next_questions_batch(n=1)` (respecting `onboarding_mode`) → relay question → user responds → `pm.record_response(audit_path, response_text)` → `apply_ratification_action(draft, parse_action(response_text, surfaced_question))`.
  - Test: end-to-end round-trip with a synthetic banded contract + a tmp `PMRuntime` against a tmp workspace; queue-depth advances by N (one per banded AC needing ratification); first surfacing's `question_text` matches the AC's text; `record_response()` clears the blocking flag.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — `BandedAC` as Pydantic vs dict (no halt — recorded)

**Decision (autonomous):** `BandedAC` is a Pydantic model with `model_config = ConfigDict(extra="forbid")`. Cycle 1's `RawACs.acs: list[dict]` accommodates band fields additively (each dict has a `confidence:` key + `evidence:` block); Cycle 2 introduces the strict `BandedAC` model as the typed in-memory representation, with `model_dump()` round-tripping through the dict shape so Cycle 1 callers / Cycle 3+4 adapters can still produce dicts before the typed model is constructed.

Rationale: dict-shape preserved at the persistence layer (forward-compat with Cycle 3+4 adapter outputs that may need extra-language-specific fields not yet typed); Pydantic validation exists at the in-memory layer (catches malformed bands at construction time per AC.BANDS.2). Mirrors the cost-governance + per-project-pm convention of `extra="forbid"` Pydantic models for runtime types.

### Surface #2 — Stubbed banded fixture vs adapter-produced banded ACs (no halt — recorded)

**Decision (autonomous):** Cycle 2 ships a hand-authored synthetic banded fixture at `tests/fixtures/synthetic-banded-contract.{md,yaml}` with 1 VERIFIED + 1 PLAUSIBLE + 1 HYPOTHESISED AC. The fixture exercises every band variant + every ratification action variant. Cycles 3+4 will produce real banded ACs from real adapters; until then the fixture is sufficient.

Rationale: cheapest shape that satisfies all 7 ACs; deterministic (hand-authored, byte-stable, no LLM in the loop); matches Cycle 1's pattern of using tmp/synthetic fixtures for test workflows. The fixture lives under `tests/fixtures/` so it's clearly test-scoped (not exposed in the public API surface).

### Surface #3 — Ratification CLI verb shape (no halt — recorded)

**Decision (autonomous):** `loam odd-extract ratify <contract-draft-path>` is a sub-verb routed through `argparse`'s subparsers under the existing `odd-extract` parser. Flags per AC.BANDS.4. Per-action verbs (`promote`, `demote`, `edit`, `reject`) are NOT exposed as separate CLI verbs in Cycle 2 — they are programmatic API only; the CLI's mediator role is "surface the next pending decision to the PM and exit." The persona drives the action via `record_response()` parsing.

Rationale: the master plan dispatch wording is "ratification CLI: `loam odd-extract ratify <contract-draft>`; PM-mediated batch" — singular verb. Per-action sub-verbs are persona-level concerns (the persona converts the user's natural-language response into a structured `RatificationAction`); exposing them as CLI verbs would force the persona to know an extra layer of CLI prose, increasing the translation burden Lens 2 says we're trying to reduce.

### Surface #4 — Ratification-state file: separate vs extend Cycle 1's state.yaml (no halt — recorded)

**Decision (autonomous):** ratification state lives in a separate file at `<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml`. NOT extending Cycle 1's `state.yaml`.

Rationale: separation-of-concerns — Cycle 1's `state.yaml` tracks the four-stage extraction's stage-completion flags (`init_complete`, `analyze_complete`, etc.); ratification is a post-extraction phase and conceptually separate. Two reasons make a separate file cleaner: (a) the extraction may be re-run (re-extract → new draft → new ratification cycle); a separate file clearly delineates "ratification state for THIS draft" vs "extraction state, persistent across draft refreshes"; (b) Cycle 1's state.yaml schema doesn't carry pending-action / partial-batch fields, and extending it would require schema-migration discipline. A new file with its own schema_version=1 sidesteps that. Both files coexist under the same extraction-dir; the audit-log is shared.

`ratification-state.yaml` schema:

```yaml
schema_version: 1
extraction_id: <repo-id>
draft_path: <relative path to contract-draft.md under .loam/extractions/<repo-id>/>
created_at: <ISO 8601>
last_updated_at: <ISO 8601>
pending_acs: [<ac_id>, ...]    # ACs awaiting ratification
in_flight_action: <ac_id | null>  # ACs surfaced through PM but not yet record_response()'d
completed_actions: [{ac_id: ..., action_kind: ..., applied_at: ...}, ...]
pm_handle: <pm name being used for ratification>
```

D5 cross-session resume reads this file, identifies `in_flight_action` + `pending_acs`, and re-surfaces the next pending question via the PM.

### Surface #5 — `RatificationAction` shape + factory functions (no halt — recorded)

**Decision (autonomous):** `RatificationAction` is a frozen dataclass (NOT Pydantic — no persistence; in-memory only) with fields: `kind: Literal["promote", "demote", "edit", "reject"]`, `ac_id: str`, `from_band: ConfidenceBand | None`, `to_band: ConfidenceBand | None`, `edit_text: str | None`, `reject_reason: str | None`, `explicit_yes: bool = False`. Factory functions `promote(...)`, `demote(...)`, `edit(...)`, `reject(...)` enforce per-action invariants at construction time (e.g., `promote(...)` requires `from_band` + `to_band` + raises if `from_band="PLAUSIBLE"` and `to_band="VERIFIED"` without `explicit_yes=True`).

Rationale: dataclass for in-memory construction (matches `SurfacedQuestion` / `RecordedResponse` precedent in `framework/per-project-pm/src/loam/per_project_pm/state.py`); factory functions make the structural enforcement (AC.BANDS.5) impossible-to-bypass at the action-construction layer (Pydantic + `model_validator` would also work but adds persistence-layer machinery for an in-memory-only type — the dataclass-factory shape is lighter).

### Surface #6 — `event_kind` extension vs new audit-log file (no halt — recorded)

**Decision (autonomous):** the existing `audit-log/<NNNN>.yaml` file pattern from Cycle 1 is extended with new `event_kind` values (`ratification_*`). NO new audit-log directory or file pattern.

Rationale: SOC-2 audit-trail floor is satisfied by ANY audit log under the SOC-2-compliant shape — the `event_kind` field discriminates between extraction events and ratification events; readers iterate the directory and dispatch on `event_kind`. Cycle 1's writer (`write_audit_entry`) accepts an arbitrary string for `event_kind`, so no schema change is required. Filenames remain `<NNNN>.yaml` with monotonic counter; ratification entries simply continue the counter from where Cycle 1's stage-complete entries leave off.

The `pm_audit_path` field cross-references the PM-side audit-log entry (under `<workspace>/workspace/.loam/pms/<pm-name>/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`) so a SOC-2 audit reader can join the two trails. Path is relative to the workspace root for portability (mirrors Cycle 4 `record_response`'s relative-path convention per v0.1.7 Cycle 4 plan §5 Surface #2).

### Surface #7 — `RatificationBatch.from_contract_draft` input shape (no halt — recorded)

**Decision (autonomous):** the helper takes `(draft: ContractDraft, banded_acs: list[BandedAC])` rather than re-parsing the markdown contract-draft file. The caller is responsible for loading the sidecar YAML + constructing the `BandedAC` list; the helper consumes typed objects.

Rationale: separation of concerns — `RatificationBatch` is the PM-integration helper; markdown/YAML parsing is the odd-extractor's responsibility. The CLI handler in `cli.py:_cmd_ratify` does the parsing + constructs the `BandedAC` list + calls the helper. Tests can construct `BandedAC`s directly without round-tripping through markdown.

### Surface #8 — `enqueue_ratification_batch` provenance string format (no halt — recorded)

**Decision (autonomous):** provenance format `f"odd-extract:{extraction_id}:{ac_id}"`. The persona-side flow parses this format to route a `record_response()` call back to the correct AC (which becomes the input to `apply_ratification_action`).

Rationale: deterministic + greppable + human-readable; matches the existing PM provenance-string convention (free-form caller tag); composes with the PM's `question_provenance` field which is already plumbed through `surface_question` audit-log entries.

### Surface #9 — Methodology doc extension placement (no halt — recorded)

**Decision (autonomous):** new section §11 "Confidence bands for derived ACs" appended to `plugins/dev-sdlc/docs/odd-methodology.md`. Numbered §11 (continues the existing 1-10 numbering); subsections 11.1 band semantics, 11.2 evidence requirements, 11.3 promotion rules, 11.4 ratification workflow. NOT a separate `odd-methodology-confidence.md` file — keeps the methodology doc as the single canonical source.

Rationale: master plan dispatch wording is "extend `docs/odd-methodology.md` (or create `docs/odd-methodology-confidence.md` if cleaner)" — extension is the cleaner choice because (a) bands are an extension of the existing methodology, not a separate methodology; (b) one canonical doc means readers don't have to discover both files; (c) future cycles (3+4) will likely cross-reference the band semantics from per-language adapter docs, and a single anchor point is easier to maintain.

### Surface #10 — Smoke-dimensions D2/D3/D4 applicability (no halt — recorded)

**Decision (autonomous):** the ratification workflow inherits Cycle 1's smoke-dimension applicability — the extractor + ratifier are invoked-on-demand (one-shot CLI), not long-running daemons. Per smoke-test-discipline §6 quick-reference, D2 (steady-state durability), D3 (restart resilience under signal), and D4 (full reboot) are structurally n/a.

But: the master plan dispatch asks all 6 dimensions exercised at cycle level (where applicable). Resolution per Cycle 1 plan §5 Surface #10 (already-applied precedent):

- **D1 (cold-state):** synthetic banded contract → ratify → audit log entries observable. Exercised by `test_AC_BANDS_4_*.py` + `test_AC_BANDS_7_*.py`.
- **D2 (steady-state, idempotency variant):** 5+ promotions in sequence are idempotent; queue depth bounded. Exercised by `test_ratification_steady_state.py`.
- **D3 (restart):** n/a structurally.
- **D4 (reboot):** n/a structurally.
- **D5 (cross-session):** partial ratification batch resumable across `/clear`. Exercised by `test_ratification_resume_cross_session.py`.
- **D6 (telemetry-floor):** every ratification action writes an audit-log entry. Exercised by `test_AC_BANDS_6_*.py`.

### Surface #11 — Release-note promise mapping (no halt — recorded)

**Decision (autonomous):** every release-note promise from the master plan §4 Cycle 2 dispatch corresponds to a tested + reliable AC.

| Promise | Backing AC | Test |
|---|---|---|
| "every derived AC has a `confidence:` field" | AC.BANDS.1 | `test_AC_BANDS_1_*.py` |
| "VERIFIED requires passing test pinned; PLAUSIBLE requires source citation; HYPOTHESISED requires LLM rationale" | AC.BANDS.2 | `test_AC_BANDS_2_*.py` |
| "schema documented in odd-methodology" | AC.BANDS.3 | `test_AC_BANDS_3_*.py` |
| "ratification CLI: `loam odd-extract ratify`; PM-mediated" | AC.BANDS.4 + AC.BANDS.7 | `test_AC_BANDS_4_*.py` + `test_AC_BANDS_7_*.py` |
| "PLAUSIBLE→VERIFIED requires explicit yes" | AC.BANDS.5 | `test_AC_BANDS_5_*.py` |
| "every ratification action audit-logged" | AC.BANDS.6 | `test_AC_BANDS_6_*.py` |
| "partial batch resumable across `/clear`" | D5 smoke | `test_ratification_resume_cross_session.py` |

If any test in the right column FAILs at build time, the corresponding promise gets de-shipped (not partially-shipped) — halt-and-surface to dispatcher.

---

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level HARD gate at v0.1.8 close (master plan §5 + Decision R), not this cycle.

### D1 — cold-state (fresh canonical workspace)

**Pattern.** Tmp workspace root; load the synthetic banded fixture as the contract draft; invoke `loam odd-extract ratify <fixture-md>` against a freshly-authored `PMRuntime` (with `onboarding_mode=False`, `max_questions_per_turn=1`). Assert: (a) `<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml` lands with all 3 fixture ACs in `pending_acs`; (b) PM `decision-queue.yaml` has 3 entries with provenance strings matching `odd-extract:*:AC1` / `:AC2` / `:AC3`; (c) first surfacing returns the first AC's question text; (d) audit-log carries one `extraction_start`-equivalent + 3 surface entries (PM-side); (e) exit status 0.

**Test:** `test_AC_BANDS_4_ratification_cli.py` + `test_AC_BANDS_7_pm_integration.py`.

### D2 — steady-state durability (n/a structurally; idempotency variant exercised)

**Structural rationale.** The ratifier is a one-shot CLI / library, not a long-running daemon. Smoke-test-discipline §6 quick-reference: one-shot CLI doesn't engage D2.

**Idempotency variant exercised.** `test_ratification_steady_state.py` runs 5 promotions in sequence (HYPOTHESISED → PLAUSIBLE for the same AC, then PLAUSIBLE → VERIFIED with explicit_yes, then a series of edit-actions on different ACs); asserts each action writes exactly one audit-log entry; asserts the queue depth on the PM side returns to 0 after every batch is processed; asserts the ratification-state.yaml's `completed_actions` grows monotonically with no duplicates.

### D3 — restart resilience (n/a)

**Structural rationale.** No long-running process. Cycle 1 plan §6 D3 reasoning applies verbatim.

### D4 — reboot resilience (n/a)

**Structural rationale.** Same as D3 — no daemon.

### D5 — cross-session continuity

**Pattern.** Test setup invokes ratification through stage 1 (enqueue + first surface) in process A (pytest worker). Then constructs a fresh `PMRuntime` + ratifier in process B (subprocess invocation of the CLI). Asserts: (a) `ratification-state.yaml` from A's run is readable by B; (b) B's `loam odd-extract ratify --resume <draft>` reads A's state and surfaces the second pending question (not the first — the first was already surfaced); (c) audit-log entries from A are visible in B's read.

**Test:** `test_ratification_resume_cross_session.py`.

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly (subprocess vs in-process).

### D6 — telemetry floor

**Pattern.** Run a full ratification cycle with all 4 action variants exercised (promote / demote / edit / reject); assert: (a) per ratification action, exactly one audit-log entry under `<workspace>/.loam/extractions/<repo-id>/audit-log/`; (b) entries carry `event_kind: ratification_*` matching the action; (c) entries carry `ac_id` + `from_band`/`to_band` (where applicable); (d) `pm_audit_path` cross-references a real PM-side audit entry under `<workspace>/workspace/.loam/pms/<pm-name>/audit-log/`; (e) entry sequence is monotonic.

**Test:** `test_AC_BANDS_6_audit_log_per_action.py`.

---

## §7 — Out of scope

Explicit deferrals (master plan §3 Cycle 2 + per-cycle dispatch):

- **Real-language extraction.** Ruby/Rails adapter → Cycle 3; Python adapter → Cycle 4. Cycle 2 uses a synthetic hand-authored fixture.
- **Test-first extraction priority.** The "every passing RSpec/Minitest test → candidate VERIFIED AC" rule lands when adapters land (Cycles 3+4). Cycle 2's fixture has VERIFIED ACs but they're hand-authored.
- **Persona-side auto-routing.** The persona's natural-language → `RatificationAction` parser is persona-level work; Cycle 2 ships the typed action layer + the CLI surface; persona-side wiring lands at v0.2.0+ alongside auto-creation per parent plan §7.
- **PR-safety gate using bands.** v0.1.9 — high-confidence (VERIFIED) ACs gate PRs strictly; HYPOTHESISED requires explicit user review. Cycle 2 establishes the bands; the gate consumes them.
- **6 dev-sdlc SKILLs.** Cycle 5.
- **Continuous codebase-watch.** v0.2.0+.

---

## §8 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **Plan-doc not authored before code.** This document IS that plan-doc. If code lands before this is committed, halt.
- **Cycle 1 not sealed.** Predecessor required; should be `c1abda1`. If `git log --oneline | grep c1abda1` returns nothing, halt.
- **Any AC ships partial.** If `test_AC_BANDS_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe before sealing.
- **Two-component fence breaks `feedback_serialize_amendment_builds`.** If a concurrent build agent is running on either component, halt.
- **D5 cross-session smoke fails.** Ship-test for cross-session continuity; halt unconditionally on red.
- **Cycle exceeds 5 hours wall-clock.** Halt with partial findings; consider further decomposition.
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **Confidence-band schema design surfaces a contradiction with Cycle 1's AC structure.** E.g., if `BandedAC.model_dump()` round-trip through `RawACs.acs: list[dict]` is found broken — halt + surface.
- **PM-mediated promotion workflow surfaces a contradiction with v0.1.7 Cycle 4's question-batching contract.** E.g., if `RatificationBatch.enqueue` is found incompatible with `PMRuntime.enqueue_decision`'s API — halt + surface.
- **Audit-log shape conflicts with M-FBM convention.** Halt + RF the conflict.
- **More than 3 in-build decisions need Luke escalation.** Master plan recommends 5; this dispatch tightens to 3.

---

## §9 — Bookkeeping

- **Manifest:** `docs/rebuild/plans/v0-1-8-cycle-2-confidence-bands-and-ratification.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 7. smoke_outcome: "D1 + D2 idempotency-variant + D5 + D6 exercised; D3/D4 n/a per smoke-test-discipline §6".
- **Apply:** `loam amend apply` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema).
- **Seal:** `loam amend seal --plan-doc docs/rebuild/plans/v0-1-8-cycle-2-confidence-bands-and-ratification.md` — synthesizes 5–15 line narrative body per AC.DPS2.{1,4} into seal target file (see §10 below for path).
- **§14 backfill:** master plan `docs/rebuild/plans/v0-1-8-master-plan.md` §9 method-decision register row for v0.1.8 Cycle 2 — doc-only commit after seal. Plus the `--plan-doc` flag on `loam amend seal` will append a `### Commit SHAs` subsection under THIS plan-doc's `## 14.` heading (see §14 below) per AC.D-sa.7 lint.
- **No tag push.** v0.1.8 tag waits on Cycles 3–5 + release-level HARD gate (Decision R).

---

## §10 — Seal narrative target

Two-component fence raises the question of where the seal narrative lives. Per `loam amend seal` convention, the narrative target is one path on a sealed component's tree.

**Decision (autonomous):** seal narrative lives at `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-8-cycle-2-confidence-bands-and-ratification` (the odd-extractor side — the primary fence). The per-project-pm side is a thin helper module + tests; the meaningful component-of-the-cycle is the band schema + ratify package on the dev-sdlc side. The master-plan §4 Cycle 2 brief's narrative-target convention also names dev-sdlc as the natural anchor (single seal commit; two `components:` entries in the manifest, but one narrative file).

The per-project-pm seal-test sidecar still advances (the seal commit pins both components' seal-test sidecars per `loam amend seal` convention) — only the narrative file is single-anchored.

---

## §11 — F2 Ruthless Feedback (gaps named this turn)

1. **Synthetic-fixture validity.** AC.BANDS.4 + AC.BANDS.7 + AC.BANDS.5 are exercised against a hand-authored fixture. Fixture-based tests can drift from real-language adapter outputs. Mitigation: Cycle 3's first real Ruby/Rails adapter run will exercise the band schema end-to-end with real evidence; if the schema turns out wrong-shaped (e.g., missing a field that real Rails RSpec evidence needs), Cycle 3 surfaces the gap + a doc-only schema migration lands. Honest framing.

2. **PM persona-side wiring is not in scope.** The persona that converts a user's natural-language reply ("yes, promote that one") into a structured `RatificationAction` is persona-level work; Cycle 2 ships the typed action layer + the round-trip via `record_response()` audit linkage. The CLI returns the next surfaced question; the persona drives the action. If a persona implementation never lands, the ratification workflow is technically usable but practically tedious. Mitigation: v0.2.0+ ships the persona. Cycle 2's surface is the substrate; the user-facing experience hinges on v0.2.0.

3. **`pm_audit_path` cross-reference is best-effort.** The persona-side flow correlates the PM's `record_response` audit entry with the odd-extractor's `ratification_*` entry via the path. If the persona drives `record_response()` AFTER `apply_ratification_action()` (out-of-order), the cross-reference breaks. Mitigation: enforced ordering in the helper API — the Cycle 2 docstring + tests assert "always `record_response()` first; then `apply_ratification_action(pm_audit_path=...)`." The persona-side flow that doesn't follow this ordering is a persona bug, not a Cycle 2 contract bug.

4. **Two-component fence + serialization rule.** Per `feedback_serialize_amendment_builds`, the two components must be edited in one pass by one agent in one working tree. This is the second multi-component fence in v0.1.8 (Cycle 1 was single-component); the seal-test for both components must pass the cross-component sweep. Honest framing: if the per-project-pm seal-test sweep fails because the dev-sdlc edit changed something the PM seal-test diff-window catches, halt + surface. The dev-sdlc side's universal-admitted prefixes already include `framework/per-project-pm/` (per the existing manifest pattern's universal admission) so this should not happen, but verify post-build.

5. **`RatificationAction` factory enforcement is impossible-to-bypass at construction.** Per AC.BANDS.5, the `promote()` factory rejects PLAUSIBLE→VERIFIED without `explicit_yes=True`. Direct `RatificationAction(...)` construction with field values would bypass the factory. Mitigation: the `RatificationAction` dataclass is documented as "construct via factories, not directly"; tests exercise both the factory rejection AND the dataclass-direct construction (which we DO want to allow for, e.g., test fixtures that pre-construct rejected actions for testing the rejection path). The structural enforcement lives at the factory layer; programmatic API users follow the convention. ODD violation if a future caller bypasses the factory in production code.

6. **Ratification-state.yaml schema vs Cycle 1's state.yaml schema.** Two state files in the same extraction-dir is a small surface area for confusion. Mitigation: each file's schema_version is explicit; each is loaded by its own loader function; the audit-log primitive doesn't read either (it's append-only). If a Cycle 5+ change wants to consolidate them, it'll be an explicit schema migration.

7. **Cycle 2 second-multi-component-fence-build precedent.** This is the third "two-component manifest" build in the v0.1.x series (after foldback FBE.6 patterns and a couple of v0.1.0 oss-publish ladders). v3 manifest schema's two-`components:` entry handling is exercised in DPS1+DPS2 (single-component each) but multi-component v3 has no precedent yet. Builder watches for any v3-tooling defects in the `loam amend seal` cross-component-sweep step (the sweep iterates all sealed components by default; with two components in the manifest, the sweep runs both seal-tests and verifies neither's diff window contains foreign paths). If the sweep surfaces a tooling defect, halt + surface.

---

## §12 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`. Composition substrate; no direct call in Cycle 2.
- v0.1.7 per-project-pm Cycle 2 — sealed at `73505f0`. Provides `PMRuntime.enqueue_decision` + `decision-queue.yaml` shape.
- v0.1.7 per-project-pm Cycle 4 — sealed at `122a7c8`. Provides `surface_next_questions_batch` + `record_response` + `pending_response_for` blocking + `is_audit_block_trigger` composition.
- v0.1.8 master plan — sealed at `1c2c478`; §9 backfilled at `774d465`.
- v0.1.8 Cycle 1 — sealed at `c1abda1` (predecessor; provides extractor scaffold + ContractDraft skeleton + audit-log primitive).
- ODD-RE research at `<pos3>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` — D-Q.RE.{1..8} sub-decisions. Method-level guidance for band schema + audit-log shape.
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D2/D3/D4 marked n/a per quick-reference card §6.
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — extended at AC.BANDS.3 with §11 confidence-band semantics.
- Eric synthesis Decision I (PLAUSIBLE→VERIFIED default-no), Decision P (SOC-2 floor), Decision Q (one-question-at-a-time) — locked at master plan time.

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 7 AC.BANDS.* families named with explicit pytest paths (§4) ✓
2. Two-component fence named (§3) ✓
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) ✓
4. Halt triggers named (§8) ✓
5. Bookkeeping path named (§9) + Seal narrative target named (§10) ✓
6. F2 gaps named (§11) ✓
7. §14 method-decision-record heading present per AC.D-sa.7 lint (§14) ✓

Build proceeds.

---

## 14. Method-decision record

Per AC.D-sa.7 — `loam amend seal --plan-doc <path>` appends a `### Commit SHAs` subsection under this heading at seal time, naming the source-edit commit + manifest-apply commit + seal commit + this plan-doc's authoring commit. The follow-up `docs(plans): record amendment ... commit SHAs ...` doc-only commit lands automatically.

Method-level decisions made during this build (a record for future cycles + audits):

1. **Banded AC schema as Pydantic + dict round-trip** (Surface #1) — strict in-memory typing via `BandedAC` Pydantic model with `extra="forbid"`; dict-shape preserved at the `RawACs.acs: list[dict]` persistence layer for forward-compat with Cycle 3+4 adapter outputs. `model_dump()` round-trips.
2. **Synthetic banded fixture vs adapter-produced** (Surface #2) — hand-authored fixture under `tests/fixtures/synthetic-banded-contract.{md,yaml}` covers all three bands + all four action variants; cheapest deterministic shape that satisfies all 7 ACs.
3. **Ratification CLI verb shape** (Surface #3) — `loam odd-extract ratify <draft>` is a single sub-verb; per-action verbs (promote/demote/edit/reject) are programmatic API only.
4. **Ratification-state file separate from Cycle 1's state.yaml** (Surface #4) — `<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml` keeps separation-of-concerns; each schema versioned independently.
5. **`RatificationAction` as frozen dataclass** (Surface #5) — in-memory only, factory-function-enforced invariants; matches `SurfacedQuestion` precedent.
6. **`event_kind` extension on existing audit-log** (Surface #6) — no new audit-log file pattern; `event_kind: ratification_*` discriminates ratification events.
7. **`RatificationBatch.from_contract_draft` takes typed `BandedAC` list** (Surface #7) — caller parses markdown/YAML; helper consumes typed objects.
8. **Provenance string format** (Surface #8) — `f"odd-extract:{extraction_id}:{ac_id}"`.
9. **Methodology doc extended in place at §11** (Surface #9) — single canonical file; not a separate `odd-methodology-confidence.md`.
10. **Smoke dimensions D3/D4 n/a** (Surface #10) — one-shot CLI; D2 idempotency-variant exercised; D1/D5/D6 exercised per AC tests.

### Commit SHAs

- Amendment commit: `96bacfeefd48c7688018488ae3b0a694c7cec20f` —
  `chore(amend): v0-1-8-cycle-2-confidence-bands-and-ratification manifest+apply — dev-sdlc+per-project-pm BASELINE+sidecar bump to 08256cf`
- Seal commit: `4865028d144b3b5c5a480913719376a258515891` —
  `chore(seals): v0-1-8-cycle-2-confidence-bands-and-ratification — dev-sdlc+per-project-pm at 96bacfe`

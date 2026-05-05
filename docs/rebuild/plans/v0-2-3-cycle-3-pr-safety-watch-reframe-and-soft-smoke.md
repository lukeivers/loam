# v0.2.3 Cycle 3 — PR-safety + continuous-watch reframe + release SOFT smoke

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.3 Cycle 2 SHIPPED — apply `716da0a`, seal `857749c`, master plan §9 backfill `06779c4`. Cycle 1 SHIPPED — apply `1e20037`, seal `9b9f87c`, §14 backfill `66de327`. Master plan committed at `35155fd`. Lean grounding doc `d37c623`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-2-3-master-plan.md` §3 Cycle 3 + §4 Cycle 3 dispatch brief + §5 release-level SOFT smoke + §9 method-decision register.

**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2). The §self-checks (§5 of that doc) were applied to every "objective" / "AC" / "constraint" / "capability" named in this plan-doc; §11 below records the audit.

**Quality bar (Luke directive 2026-05-04, carried verbatim from master plan):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 3 closes the v0.2.3 release. The producers (Cycles 1 + 2) emit objective-altitude + backing-map outputs; Cycle 3 reshapes the consumers to operate at that altitude. Two-component fence (pr-safety + odd-extractor incremental engine) under shared dev-sdlc parent; single seal. Gate decision matrix fully reframed (not partial). Override flow reframed (objectives + backing-map, not symbol-altitude ACs). PR description template renders objective text. Watch incremental engine consults backing-map. Pre-emption order preserved per v0.1.9. Audit-log preserved per v0.1.6 SOC-2 floor. Legacy `acs:` consumers retire per master plan §6.2. Release-level SOFT smoke runs against the canonical jsts-playwright-app fixture. **No partial features.** Self-checks pass on every example AC named in this plan-doc per §11.

---

## §1 — Outcome shape

Cycle 3 ships three tightly-coupled mechanisms above Cycles 1 + 2's substrate:

1. **PR-safety reframed at objective altitude.** `BandedContract` + `read_contract` (pr-safety) swap from reading legacy `contract-draft.yaml.acs:` to reading `objectives.yaml` + `backing-map.yaml` directly. Classifier consumes the backing-map (objective_id → evidence rows with file + line ranges) instead of `BandedAC.evidence.citations` + `backing_files`. Decision matrix: VERIFIED-objective-backing-touched → HARD_BLOCK; PLAUSIBLE-touched or novel hunks → SURFACE_DECISION; HYPOTHESISED-only → DOCS_ONLY. Override flow carries `original_objectives` + `proposed_objectives` (Cycle 1's `Objective` type). PR description template renders objective text + per-objective band + backing rows touched + ratification SHAs. Hooks (`pre-commit`, `pre-push`) install-shape unchanged.

2. **Continuous-watch reframed at objective altitude.** v0.2.0's `diff_classifier.py` (odd-extractor) classified `BandedAC` evidence at symbol altitude. Cycle 3 reshapes to consult `backing-map.yaml`: each `BackingMapEntry.evidence_rows` walked; rows with stale path/line-range flag backing-row drift on the objective. Output: `OutOfDateObjective` / `OrphanedObjective` replace `OutOfDateAC` / `OrphanedAC`. `IncrementalProposalSet` carries objective-altitude proposals. Domain-batching groups by `O.<domain>.<n>` regex from `objective_id`.

3. **Legacy `acs:` consumer retirement (per master plan §6.2 default).** Cycle 1+2 preserved `acs:` as transitional alias via `_objectives_as_legacy_acs` in `generate.py`. Cycle 3 retires: `generate.py` stops rendering; `verify.py` legacy-AC rendering retires; pr-safety's `read_contract` consumes `objectives.yaml`. Halt + surface if non-trivial consumer found beyond pr-safety + verify.

**Fence reality.** Two-component under shared `plugins/dev-sdlc/` parent; single seal. PRIMARY edits to `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/{contract,classifier,gate,override,spec,audit,cli,templates/pr/}.py` + secondary edits to `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/{diff_classifier,proposals,incremental,incremental_ratify,domain_batching,generate,verify,observability}.py`.

**Release-note promise.** After Cycle 3 seals, fresh canonical workspace runs `loam odd-extract <fixture>` + `ratify` + `loam pr-safety check` end-to-end on objective altitude. Synthetic VERIFIED-objective-touching diff → HARD_BLOCK with objective text + backing row cited inline. Synthetic external commit affecting objective backing → watch flags coverage shift via PM domain-batched proposal. PR description renders objective prose, not symbol-AC IDs. v0.2.3 SHIPPED rollup commit lands when SOFT smoke green on canonical jsts-playwright-app fixture.

**Discipline.** v0.1.9 four-stage pipeline (read → parse-diff → classify → decide → act) preserved. v0.2.0 incremental engine shape preserved (production-stake refusal; PM-only enqueue; never-mutate-sidecar). Pre-emption order preserved. Audit-log floor preserved. Override `Loam-Override:` trailer preserved. Hooks + CI templates preserved (invoke same gate CLI).

---

## §2 — Lens checks (per CLAUDE.md design lenses)

**Lens 1 — Claude-leverage-first.** Reuses Cycle 1's `Objective`/`Capability`/`Constraint` Pydantic models; Cycle 2's `BackingMap`/`BackingMapEntry`/`EvidenceRowRef`; v0.1.9's gate engine + classifier + override-flow + audit-log; v0.2.0's incremental engine + `IncrementalProposalSet` + `domain_batching.py` + production-stake refusal; `framework/per-project-pm/`'s `PMRuntime` (zero PM-side schema edits — provenance carries altitude tag); `observability.py` audit-log. No LLM-pass at this cycle (deterministic backing-map lookup). Zero new dependencies.

**Lens 2 — Harness + primary-persona value.** Primary-persona test ✓ — Eric pushes a commit touching `src/routes/disputeRoutes.js`; gate fires HARD_BLOCK with "diff touches VERIFIED objective O.dispute-flow.1: 'operators file refund disputes against DoorDash + Uber Eats merchant portals at scale'; backing rows: src/routes/disputeRoutes.js:42-58." Eric reads outcome prose, not `AC.JSTS.express.get.all_orders...`. Harness test ✓ — objective-altitude gate + watch are reusable consumer layers; v0.2.5 negative-alignment composes (gate adds LLM-judge against objective text); v0.2.4 completeness-interview composes on backing-map orphan list.

**Lens 3 — ODD authoring.** Outcome + named ACs (§3) + halt triggers (§5 + §6) + acceptance smoke (§4 + §5). Method-loose per builder: classifier evidence-row-overlap algorithm; orphan-row presentation; incremental drift detection logic; legacy-`acs:` retirement strategy.

**Lens 4 — Prompt scope ↔ confidence.** HIGH for shape (master plan names all 14 ACs; Cycles 1+2 shipped + verified; v0.1.9 + v0.2.0 substrates verified-working; backing-map shape directly addresses watch's coverage-detection need). MEDIUM for legacy-`acs:` retirement scope — primary consumers identified; halt if non-pr-safety/non-verify consumer surfaces. MEDIUM for override `proposed_objectives` shape — Cycle 1 `Objective` reused; VERIFIED→PLAUSIBLE conversion preserves text + demotes confidence + records override commit SHA. MEDIUM for watch reframe — backing-map shape sufficient; engine needs minimal change. HIGH for substrate preservation.

**Lens 5 — Swarming.** Two-component fence under shared dev-sdlc parent; single seal per `feedback_serialize_amendment_builds`. Per-concern module decomposition matches master plan's named-mechanism naming. `max_planner_depth: 1` — further split adds only coordination overhead. Model: Sonnet default (no LLM-pass design; pure consumer-swap + output-type reshape).

---

## §3 — AC enumeration (locked, 14 ACs across three families)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, branch, test maps to a named AC. AC.PRGATE.1 → AC.PRGATE.6 + AC.WATCHOBJ.1 → AC.WATCHOBJ.5 + AC.RELSMOKE.1 → AC.RELSMOKE.3 inherited from master plan §3 Cycle 3 (renamed AC.PRSGOBJ → AC.PRGATE for consistency with the dispatcher's family naming). §self-checks 1-5 ran on every example outcome / capability / constraint named in this plan-doc; §11 records the audit.

### AC.PRGATE.* — PR-safety reframed at objective altitude (6 ACs)

- **AC.PRGATE.1 — Contract reader consumes `objectives.yaml` + `backing-map.yaml`.** `read_contract` (pr-safety/contract.py) reads `<workspace>/.loam/extractions/<repo-id>/{objectives.yaml,backing-map.yaml}` (Cycle 1+2 outputs); legacy `contract-draft.yaml.acs:` retired. New `BandedContract` (pr-safety/spec.py): `objectives: list[Objective]` + `backing_map: BackingMap` + preserves `extraction_id` + `repo_path` + `repo_sha` + `created_at` + `override_count`. Imports `Objective`/`BackingMap` from `loam_odd_extractor.spec`. Override-overlay composition preserved structurally (now operates on `Objective` rows). Test: synthetic objectives.yaml + backing-map.yaml → BandedContract.objectives populated; missing-file raises ContractMissingError; round-trip.

- **AC.PRGATE.2 — Classifier consumes backing-map.** `classify` (pr-safety/classifier.py) walks `contract.backing_map.entries`; per evidence row's `path` + `line_range`, checks diff-hunk intersection via existing `_hunk_intersects_range`; emits `TouchedObjective` (new spec type: `objective` + `touch_kind: Literal["evidence_line","evidence_file"]` + `touched_evidence_rows: list[EvidenceRowRef]` + `touched_hunks: list[Hunk]`). Diff hunks not overlapping any backing-row → `NovelDiff` (`file_path` + `hunks`). `ClassificationResult` reshapes: `touched_objectives` + `novel` + `untouched`. Test: hunk-in-range → TouchedObjective; unmapped file → NovelDiff; no overlap → untouched=True; edge cases (hunk fully inside; hunk on range end; pure-addition hunk).

- **AC.PRGATE.3 — Gate decision matrix at objective altitude.** `decide` (pr-safety/gate.py): VERIFIED objective touched → HARD_BLOCK; PLAUSIBLE → SURFACE_DECISION; HYPOTHESISED → DOCS_ONLY; novel-diff → SURFACE_DECISION (consolidated with PLAUSIBLE). Pre-emption HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS preserved per v0.1.9 AC.PRSG.4. `GateDecision` carries `touched_objectives` + `novel` + existing fields. Production-stake `requires_ratification=True` on every SURFACE_DECISION preserved per v0.1.9 AC.PRSG.8. PM provenance: `pr-safety:plausible-objective:{ext}:{obj_id}` + `pr-safety:novel-diff:{ext}` (additive). Test: V-only → HARD_BLOCK + objective_ids cited in reason text; P-only → SURFACE_DECISION + PM pairs; H-only → DOCS_ONLY; novel-only → SURFACE_DECISION; mixed V+P → HARD_BLOCK pre-empts; production-stake forces requires_ratification=True.

- **AC.PRGATE.4 — Override flow at objective altitude.** `OverrideRequest` (pr-safety/spec.py): `original_objectives` + `proposed_objectives: list[Objective]` + existing fields (`rationale`, `owner`, `commit_sha`, `repo_sha`, `created_at`). `build_override_request` (pr-safety/override.py): VERIFIED-objective-touched → propose conversion to PLAUSIBLE preserving `objective_id` + `text` + `domain` + multi-source evidence; novel-diff → no objective creation (v0.2.4 gap-analysis owns; Cycle 3 records audit-only). `Loam-Override:` trailer parser preserved. Overlay shape at `<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml`: `kind: replace_verified_objective` + `original_objective_id` + `replacement_objective: <Objective dict>`. v0.1.9 overlay v1→v2 migration on read with `.v1.bak` (mirrors Cycle 2 RatificationStateV2 pattern). Test: V-objective → proposed_objectives downgrade to P; trailer parser unchanged; overlay round-trip; novel-diff records audit-only.

- **AC.PRGATE.5 — PR description template at objective altitude.** `pr-safety/templates/pr/pr_description.md.template` sections: "Touched objectives" (per-objective: `objective_id` + band + `text` + `domain` + backing rows path:line); "Novel diff" (file + hunks); "Override audit trail" (override SHAs + rationale chain). Template variables driven by `GateDecision`. v0.1.9 string-replace machinery preserved per AC.PRSI.7. Test: synthetic GateDecision → rendered output contains objective text + band + backing rows; no AC.* IDs present (regression guard against legacy leak); overflow handling (>50 objectives truncated per v0.1.9 AC.PRSI.7 precedent).

- **AC.PRGATE.6 — Audit-log per gate decision at objective altitude.** `pr-safety/audit.py` `gate_decision_recorded` payload extends additively: `objective_ids_touched` + `objective_bands_touched` (per-id band) + `backing_rows_overlapped` (per-objective list of `evidence_row_id`) + existing fields (`decision_action` + `requires_ratification` + `safety_profile` + `novel_count` + `extraction_id` + `repo_sha` + `commit_sha`). No schema-version bump. Test: gate decision → audit entry with objective-altitude payload; round-trip; SOC-2 floor (Decision P) preserved; production-stake honour preserved per v0.1.9 AC.PRSG.8.

### AC.WATCHOBJ.* — Continuous-watch reframed at objective altitude (5 ACs)

- **AC.WATCHOBJ.1 — `diff_classifier.py` consults backing-map.** `classify_evidence` (odd-extractor/diff_classifier.py) signature: `(prior_objectives: list[Objective], prior_backing_map: BackingMap, repo_path: Path)`. Per objective: walks `prior_backing_map.entries[objective_id].evidence_rows`; per row's `path`, checks file-existence (missing → `OrphanedObjective`: `objective` + `missing_evidence_rows`); if `line_range` set, uses existing `_git_log_range` to detect changes between prior `repo_sha` and HEAD (changed → `OutOfDateObjective`: `objective` + `drift_kind: Literal["evidence_row_path_missing","evidence_row_line_changed","evidence_row_file_changed"]` + `affected_rows` + `from_sha` + `to_sha`). `EvidenceClassification` reshapes: `still_current: tuple[Objective,...]` + `out_of_date: tuple[OutOfDateObjective,...]` + `orphaned: tuple[OrphanedObjective,...]`. Test: path-missing → orphaned; line-changed → out_of_date; unrelated diff → still_current; SHA-pinned vs unpinned paths.

- **AC.WATCHOBJ.2 — `IncrementalProposalSet` at objective altitude.** `proposals.py`: new `IncrementalProposal` dataclass parallel to v0.2.0 `Proposal`: `objective_id` + `current_evidence: Objective.Evidence` (Cycle 1 multi-source evidence preserved) + `proposed_new_evidence: Objective.Evidence | None` (None for orphaned; refreshed `repo_sha` + line-range for out_of_date) + `confidence_band` (preserved per Decision I default-no) + `drift_kind` + `affected_rows`. `IncrementalProposalSet.proposals: list[IncrementalProposal]` + existing fields. v0.2.0 `Proposal` dataclass preserved for legacy callers (additive shape). Test: out_of_date → IncrementalProposal with proposed_new_evidence; orphaned → proposed_new_evidence=None; band preservation; round-trip.

- **AC.WATCHOBJ.3 — `domain_batching.py` groups by objective domain.** `group_proposals_by_domain` parses `O.<domain>.<n>` regex from `objective_id`; one PM batch per domain per v0.2.0 precedent. PM provenance: `odd-watch:incremental:{ext}:objective:{obj_id}` (additive). Test: 5 proposals across 3 domains → 3 batches; one-question-at-a-time within batch preserved; provenance carries altitude.

- **AC.WATCHOBJ.4 — `incremental.py` engine reshape.** `run_incremental` reads `prior_objectives` from `objectives.yaml` + `prior_backing_map` from `backing-map.yaml`; calls `classify_evidence` (AC.WATCHOBJ.1) → `generate_proposals` (AC.WATCHOBJ.2) → `enqueue_incremental_proposals` (AC.WATCHOBJ.3). `IncrementalRunResult.classification` reshapes; existing fields preserved. Production-stake refusal (`IncrementalRefusedError`) preserved. Sidecar-never-mutated invariant preserved per v0.2.0 F2 RF gap #6. ContractNotFoundError messaging at objective altitude. Test: full run on synthetic prior objectives + backing-map → IncrementalRunResult with objective-altitude classification; production-stake refusal preserved; ContractNotFoundError on missing objectives.yaml.

- **AC.WATCHOBJ.5 — Audit-log per incremental run at objective altitude.** `observability.py` `incremental_run_complete` payload extends additively: `still_current_objective_count` + `out_of_date_objective_count` + `orphaned_objective_count` + `backing_map_staleness_detected: bool` + `domain_batches_enqueued` + `objectives_by_domain` (count per domain). No schema-version bump. Test: incremental run → audit entry with objective-altitude payload; SOC-2 floor preserved.

### AC.RELSMOKE.* — Release-level SOFT smoke (3 ACs)

- **AC.RELSMOKE.1 — Cold-state SOFT smoke on canonical jsts-playwright-app fixture.** Integration test at `plugins/dev-sdlc/odd-extractor/tests/test_v0_2_3_release_soft_smoke.py` (smoke spans both components; consolidate in odd-extractor). Stub Anthropic with canned objectives + backing-map. Steps: (1) `loam odd-extract <fixture>` → `objectives.yaml` + `backing-map.yaml`; (2) ratify one objective P→V with backing cited; (3) PR-safety `read_contract` loads typed BandedContract; (4) synthetic diff overlapping VERIFIED backing → HARD_BLOCK with objective text in reason; (5) synthetic diff overlapping PLAUSIBLE backing → SURFACE_DECISION + PM pair; (6) synthetic external commit modifying VERIFIED backing-row line range → watch flags via OutOfDateObjective. Each step asserts typed output + audit entry. D1 exercised. Evidence at `<pos3>/workspace/.scratch/claude-output/v0-2-3-soft-smoke-2026-05-05.md` per master plan §5.

- **AC.RELSMOKE.2 — Idempotent re-run smoke.** Re-run extract / gate / watch on unchanged repo → byte-identical output (modulo timestamps); identical GateDecision; empty watch proposals. Cross-cycle assertion (Cycle 1+2+3 idempotent in sequence). D2 exercised.

- **AC.RELSMOKE.3 — Cross-session SOFT smoke + telemetry-floor.** Session A extracts + ratifies + caches; Session B (post-`/clear`) reads cached state + gate fires + watch detects drift. Audit entries across sessions: `synthesis_complete` + `backing_map_populated` + `ratification_objective_promote` + `gate_decision_recorded` + `incremental_run_complete`. All carry `extraction_id` + `repo_sha` + `timestamp`. SOC-2 floor preserved. D5 + D6 exercised.

---

## §4 — Component & file layout

**PRIMARY:** `plugins/dev-sdlc/pr-safety/`. **SECONDARY:** `plugins/dev-sdlc/odd-extractor/` (incremental engine reframe + legacy `acs:` retirement). **TERTIARY:** `docs/rebuild/plans/` (plan-doc paper trail). Single-seal under shared dev-sdlc parent per v0.1.8 + Cycle 2 precedent.

**Existing paths (extend in-place; consumer-swap inside):**

PR-safety:

- `src/loam_pr_safety/spec.py` — replace `BandedContract.acs` with `objectives` + `backing_map`; replace `TouchedAC`/`CandidateAC` with `TouchedObjective`/`NovelDiff`; replace `ClassificationResult.touched_acs/.novel` with `.touched_objectives/.novel`; replace `OverrideRequest.original_acs/.proposed_acs` with `.original_objectives/.proposed_objectives`. Imports `Objective`/`BackingMap`/`EvidenceRowRef` from `loam_odd_extractor.spec`.
- `src/loam_pr_safety/contract.py` — `read_contract` swaps source files; overlay composition reshapes to operate on `Objective` rows.
- `src/loam_pr_safety/classifier.py` — `classify` consumes `contract.backing_map.entries`; line-overlap helpers (`_hunk_intersects_range`, `_normalise_path`) preserved; novel detection logic preserved structurally.
- `src/loam_pr_safety/gate.py` — `decide` consumes `.touched_objectives`; `_has_band` reshapes input type; pre-emption + production-stake honour preserved.
- `src/loam_pr_safety/override.py` — `build_override_request` + `_proposed_objectives_from_classification` (renamed); VERIFIED-objective conversion preserved; novel-diff records audit-only.
- `src/loam_pr_safety/audit.py` — `gate_decision_recorded` payload extended additively.
- `src/loam_pr_safety/cli.py` — flag/arg surface unchanged; internal call sites swap types.
- `src/loam_pr_safety/templates/pr/pr_description.md.template` — sections reshape; AC.* IDs removed.

Odd-extractor (secondary):

- `src/loam_odd_extractor/diff_classifier.py` — `classify_evidence` signature reshape; `OutOfDateObjective`/`OrphanedObjective` replace `OutOfDateAC`/`OrphanedAC`; `_git_log_range` + line-citation regex preserved.
- `src/loam_odd_extractor/proposals.py` — new `IncrementalProposal` dataclass; `IncrementalProposalSet.proposals` reshape.
- `src/loam_odd_extractor/incremental.py` — `run_incremental` reads `objectives.yaml` + `backing-map.yaml`; `IncrementalRunResult.classification` reshape; production-stake refusal preserved.
- `src/loam_odd_extractor/incremental_ratify.py` — `enqueue_incremental_proposals` accepts `IncrementalProposal`; PM-side schema unchanged.
- `src/loam_odd_extractor/domain_batching.py` — `group_proposals_by_domain` parses `O.<domain>.<n>` regex; one batch per domain.
- `src/loam_odd_extractor/generate.py` — retire `_objectives_as_legacy_acs`; `aggregated_acs` empty in `RawACs`.
- `src/loam_odd_extractor/verify.py` — retire legacy `acs:` rendering paths (~lines 310, 437, 445, 455, 564); render `Objective` rows directly from `objectives.yaml`; `contract-draft.yaml` shrinks to top-level summary.
- `src/loam_odd_extractor/observability.py` — `incremental_run_complete` payload extends additively per AC.WATCHOBJ.5.
- `src/loam_odd_extractor/__init__.py` — additive exports.

**New paths (this cycle):**

- Tests pr-safety: `tests/test_AC_PRGATE_{1..6}_*.py` (6).
- Tests odd-extractor: `tests/test_AC_WATCHOBJ_{1..5}_*.py` (5) + `tests/test_AC_RELSMOKE_{1..3}_*.py` (3) + `tests/test_v0_2_3_release_soft_smoke.py` (full integration).
- Fixtures odd-extractor: `tests/fixtures/release-smoke/jsts-playwright-app/` may extend the existing canonical fixture with synthetic diff + synthetic external commit + synthetic objectives.yaml + backing-map.yaml stubs (build agent verifies fixture path; halt + surface if canonical fixture lacks needed shape).

**Smoke dimensions (per master plan §3 Cycle 3 + §5):**

- **D1 cold-state** ✓ — full release-level SOFT smoke per AC.RELSMOKE.1.
- **D2 steady-state** ✓ — idempotent re-run per AC.RELSMOKE.2.
- **D3 restart** inherited from v0.1.9 + v0.2.0 substrate (mid-gate Ctrl-C; mid-watch kill -TERM); no new D3-specific code.
- **D5 cross-session** ✓ — AC.RELSMOKE.3 + per-component v0.1.9/v0.2.0 D5 inherited.
- **D6 telemetry-floor** ✓ — per AC.PRGATE.6 + AC.WATCHOBJ.5 + AC.RELSMOKE.3.
- **D4 reboot** — n/a structurally (gate + watch both invoked-on-demand; filesystem state survives reboot trivially per v0.1.9 + v0.2.0 precedent).

Plus full-suite green sweep — pre-Cycle-3 `plugins/dev-sdlc/{pr-safety,odd-extractor}/` + `framework/cost-governance/` + `framework/per-project-pm/` tests at HEAD all pass post-Cycle-3; halt + surface on any regression.

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.3 Cycle 3 BUILD dispatch — PR-safety + watch reframe + release SOFT smoke

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

LOAD `docs/odd-llm-grounding.lean.md` FIRST. Gate + watch must consume
objective-altitude shape; legacy symbol-altitude rendering retires.

Authority: build the 6 AC.PRGATE.* + 5 AC.WATCHOBJ.* + 3 AC.RELSMOKE.*
families (14 ACs) per sub-plan-doc §3. Two-component fence (pr-safety
PRIMARY + odd-extractor SECONDARY) under shared dev-sdlc parent; single seal.
Tertiary: docs/rebuild/plans/.

Principles at turn-start: AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-
NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / OUTPUT-TO-DISK /
WD-IN-DISPATCHES / NO --amend / NO push / NO FALSE FAULT / PRINCIPLE-
APPLICATION DISCIPLINE / TEST-AGAINST-OPERATIONAL-OBJECTIVE-BEFORE-ESCALATING.

Quality bar (Luke directive 2026-05-04, carried verbatim): every AC ships
complete + tested. Gate decision matrix fully reframed. Override flow
reframed. PR description template renders objective text. Watch reframed.
Pre-emption order preserved per v0.1.9. Audit-log preserved per v0.1.6
SOC-2 floor. Legacy `acs:` consumers retired per master plan §6.2 default.
SOFT smoke green on canonical jsts-playwright-app fixture. No partial features.

Source pointers (READ FIRST):
  - THIS sub-plan-doc at
    docs/rebuild/plans/v0-2-3-cycle-3-pr-safety-watch-reframe-and-soft-smoke.md
  - master plan §3 Cycle 3 + §4 + §5 + §9 at
    docs/rebuild/plans/v0-2-3-master-plan.md (commit 35155fd)
  - Cycle 1 sub-plan-doc (sealed 9b9f87c) + Cycle 2 sub-plan-doc (sealed 857749c)
  - Lean grounding doc at docs/odd-llm-grounding.lean.md (d37c623)
  - v0.1.9 PR-safety substrate: pr-safety/{contract,classifier,gate,override,
    audit,spec,cli,templates/pr/}.py + tests/test_AC_PRSG_*.py
  - v0.2.0 watch substrate: odd-extractor/{diff_classifier,proposals,
    incremental,incremental_ratify,domain_batching}.py + tests/test_AC_WATCH_*.py
  - Cycle 1 Objective + Cycle 2 BackingMap models: odd-extractor/spec.py
  - canonical jsts-playwright-app fixture at
    plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/
  - rd-automation extraction artefact at /Users/lukeivers/pos3/workspace/
    rd-automation/.loam/extractions/rd-automation-5f656bad/ — RESERVED for
    v0.2.5 HARD gate; do NOT touch.

Fence + ACs + smoke + out-of-scope: per sub-plan-doc §3 + §4.

Halt triggers — sub-plan-doc §6 + below; halt-and-surface, do NOT work around:
  - WD drifts to pos3.
  - PR-safety gate-logic full rewrite needed (not consumer-swap; master plan §7.4).
  - Watch reframe needs richer backing-map than Cycle 2 ships (master plan §7.5).
  - Legacy `acs:` consumer beyond pr-safety + verify/generate.
  - jsts-playwright-app fixture lacks shape needed for SOFT smoke.
  - SOFT smoke surfaces v0.2.0 watch breakage beyond reframe scope.
  - Override-overlay v0.1.9 → v0.2.3 migration non-trivial.
  - ODD §2.5 violations in surrounding code OR Cycles 1/2 substrate.
  - Cycle wall-clock >6 h with no progress.
  - >3 escalations needed.

Bookkeeping:
  - pos-amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit: feat(dev-sdlc): v0.2.3 Cycle 3 — PR-safety + watch
    reframe + release SOFT smoke.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §9 per-cycle SHA backfill row updates with apply + seal SHAs.
  - v0.2.3 SHIPPED rollup commit AFTER seal + smoke green: updates STATE.md
    + roadmap §8 + odd-rebuild master plan §3 v0.2.3 row + master plan §9
    register. Tag deferred until v0.2.5 ship gate.

Model rationale: Sonnet default (no Opus tier; pure consumer-swap + output-
type reshape; no LLM-pass design — backing-map lookup deterministic).
```

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — PR-safety consumer-swap may surface deeper coupling than expected.** Master plan §7.4 named this risk. *Mitigation:* halt-trigger explicit in §5; cycle-count growing to 4 (split PR-safety from watch) is the corrective path. Risk is low — Cycle 2 already round-tripped Objective/BackingMap; spec.py is the sole heavy-coupling site.

**6.2 — Watch reframe may need richer backing-map than Cycle 2 ships.** Master plan §7.5. `EvidenceRowRef` (`path` + `line_range` + `symbol_name` + `language` + `confidence`) is structurally sufficient — `line_range` + `path` is exactly what `_git_log_range` consumes. *Mitigation:* halt if shape insufficient mid-cycle. Risk low post-Cycle-2.

**6.3 — Legacy `acs:` retirement scope.** Primary consumers identified: pr-safety/contract.py + odd-extractor/verify.py (~5 paths) + odd-extractor/generate.py (`_objectives_as_legacy_acs`). *Mitigation:* halt if third consumer surfaces (e.g., ratify.py legacy callback or hooks/objective_binding_gate.py); expand scope or transitional alias.

**6.4 — Override-overlay v0.1.9 → v0.2.3 migration.** v0.1.9 overlays use `kind: replace_verified` + `original_ac_id` + `replacement_ac` (BandedAC dict). *Mitigation:* if no v0.1.9 overlays exist in canonical workspace (likely; v0.1.9 just demoed), retirement clean. Else read-time v1→v2 migration with `.v1.bak` (mirrors Cycle 2 RatificationStateV2); halt if non-trivial.

**6.5 — Canonical jsts-playwright-app fixture readiness.** Smoke needs synthetic diffs + commits + objectives.yaml + backing-map.yaml. *Mitigation:* AC.RELSMOKE.1 stub-Anthropic approach reuses Cycle 1 stub-mode pattern; halt if fixture extension non-trivial.

**6.6 — TouchedObjective vs TouchedAC test-coverage parity.** v0.1.9 has 30+ tests on TouchedAC pathways. *Mitigation:* AC.PRGATE.2 + AC.PRGATE.3 enumerate edge cases; build agent ports v0.1.9 test patterns to objective altitude; halt if any pathway lacks analog.

**6.7 — Novel-diff handling regression.** v0.1.9 promotes novel to PLAUSIBLE (`AC.NOVEL.<n>` IDs); v0.2.3 defers to v0.2.4 gap-analysis, records audit-only. Reviewer experience changes. *Mitigation:* document explicitly in AC.PRGATE.4; v0.2.4 plan-doc carries novel-diff promotion.

**6.8 — Cycle wall-clock band 4–6 h may be optimistic.** 14 ACs + two-component fence + ~10 module reshape + 14 tests + integration test + fixture work. *Mitigation:* halt at 6h-no-progress; agent may serialise internally (pass 1: pr-safety; pass 2: watch; pass 3: retirement + smoke); single-commit still required.

**6.9 — SOFT smoke fixture-driven nature.** Per v0.2.0 F2 RF gap #10 + Cycle 1 actuals, full-mode adapter ships zero real-AC production for non-fixture cases; smoke uses stub-Anthropic + canned objectives. *Mitigation:* correct shape for SOFT (HARD against rd-automation deferred to v0.2.5); fixture-driven smoke validates wiring + altitude shape; honest framing per AC.RELSMOKE.1 evidence document.

**6.10 — Two-component single-seal raises seal-narrative breadth.** *Mitigation:* mirror Cycle 2's manifest pattern (single dev-sdlc component sweep); seal_test covers both since dev-sdlc parent is the seal granularity per v0.1.8 + Cycle 2 precedent.

---

## §7 — Method-decision register (Cycle-3-specific)

| Decision | Choice | Rationale |
|---|---|---|
| Component fence | Two-component (pr-safety + odd-extractor) under shared dev-sdlc parent; single seal | Master plan §9 + Cycle 2 precedent. |
| AC family naming | AC.PRGATE.* + AC.WATCHOBJ.* + AC.RELSMOKE.* | Dispatcher-named; PRGATE shorter than master plan's PRSGOBJ. |
| `BandedContract` reshape | Replace `acs: list[BandedAC]` with `objectives: list[Objective]` + `backing_map: BackingMap` | Master plan §6.2 + Cycle 1+2 model reuse. |
| `read_contract` source | `objectives.yaml` + `backing-map.yaml` | Cycle 1+2 outputs are canonical. |
| `TouchedObjective` shape | `objective` + `touch_kind: Literal["evidence_line","evidence_file"]` + `touched_evidence_rows` + `touched_hunks` | Mirrors v0.1.9 TouchedAC; altitude-adapted. |
| `NovelDiff` shape | `file_path` + `hunks` (no objective creation) | v0.2.4 owns novel→objective promotion. |
| Decision matrix | Pre-emption HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS preserved verbatim | v0.1.9 AC.PRSG.4. |
| Production-stake honour | `requires_ratification=True` on every SURFACE_DECISION preserved | v0.1.9 AC.PRSG.8. |
| Override flow | `original_objectives` + `proposed_objectives: list[Objective]`; novel records audit-only | §6.7. |
| Override overlay | `kind: replace_verified_objective` + `original_objective_id` + `replacement_objective` | Altitude-adapted from v0.1.9. |
| Override v1→v2 migration | Read-time auto-migration with `.v1.bak`; halt if non-trivial | §6.4; mirrors Cycle 2 RatificationStateV2 pattern. |
| PR description template | String-replace; sections: Touched objectives + Novel diff + Override audit trail; AC.* IDs removed | v0.1.9 AC.PRSI.7 substrate; master plan §6.2. |
| Watch signature | `classify_evidence(prior_objectives, prior_backing_map, repo_path)` | Cycle 1+2 model reuse. |
| Watch output types | `OutOfDateObjective` + `OrphanedObjective` dataclasses | Mirrors v0.2.0 at altitude. |
| `IncrementalProposal` | `objective_id` + `current_evidence` + `proposed_new_evidence | None` + `confidence_band` + `drift_kind` + `affected_rows` | Cycle 1 evidence reuse. |
| Domain-batching | Group by `O.<domain>.<n>` regex from `objective_id` | Cycle 1 ID convention. |
| PM provenance | Additive: `pr-safety:plausible-objective:{ext}:{obj_id}` + `pr-safety:novel-diff:{ext}` + `odd-watch:incremental:{ext}:objective:{obj_id}` | PM-side schema unchanged. |
| Legacy `acs:` retirement | Full removal | Master plan §6.2 default; halt if third consumer surfaces. |
| `_objectives_as_legacy_acs` | Delete | Clean removal. |
| `RawACs.acs` field | Render empty (preserve type signature) | Type-signature stability for any v0.1.8 callers. |
| `verify.py` rendering | Render `Objective` rows directly from `objectives.yaml`; legacy `raw.acs` paths retire | Cycle 1 authoritative. |
| `contract-draft.yaml` shape | Shrink to top-level summary (extraction_id + repo_path + objective_count + created_at); `objectives.yaml` is canonical | Halt if any consumer needs full legacy shape. |
| Audit-log payload | Additive only; no schema-version bump | SOC-2 floor preserved. |
| Smoke fixture | Canonical jsts-playwright-app (NOT rd-automation) | Master plan §5; rd-automation is v0.2.5 HARD-gate target. |
| Smoke approach | Stub-Anthropic + canned objectives + canned backing-map | Cycle 1 stub-mode precedent. |
| Smoke evidence path | `<pos3>/workspace/.scratch/claude-output/v0-2-3-soft-smoke-2026-05-05.md` | Output-to-disk discipline. |
| Test granularity | 1-per-AC (14) + 1 integration | Mirrors Cycle 1+2+v0.1.9+v0.2.0 conventions. |
| Manifest schema | v3 with plan_doc_ref + ac_count + smoke_outcome | Cycle 1+2 precedent. |
| v0.2.3 SHIPPED rollup | Post-seal + smoke green; updates STATE.md + roadmap §8 + ODD-rebuild master plan §3 v0.2.3 row + master plan §9 register; tag deferred until v0.2.5 ship gate | Master plan §5; Eric paused. |

---

## §8 — Provenance trail

- **Master plan:** `docs/rebuild/plans/v0-2-3-master-plan.md` §3 Cycle 3 + §4 + §5 + §6 + §9 (`35155fd`).
- **Cycle 1 sub-plan-doc:** `docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md`. Sealed `9b9f87c`.
- **Cycle 2 sub-plan-doc:** `docs/rebuild/plans/v0-2-3-cycle-2-backing-map-and-ratification-reframe.md`. Apply `716da0a`; seal `857749c`; master §9 backfill `06779c4`.
- **Lean grounding (auto-loaded):** `docs/odd-llm-grounding.lean.md` at `d37c623`.
- **v0.1.9 PR-safety substrate:** Cycle 1 gate engine `790807d`; Cycle 2 hooks+templates `0dc557e`; Cycle 3 SKILLs+cleanup `3284087`. Local rollup `9022df1`.
- **v0.2.0 watch substrate:** Cycle 1 watch `6fef2f1`; Cycle 2 skill-capture `549fe88`; rollup `bbc93a7`.
- **v0.1.7 PM batch API (provenance contract):** Cycle 4 `122a7c8`. `framework/per-project-pm/`.
- **v0.1.6 production-safety + cost-governance:** `3f1d237` / `88674cb`.
- **rd-automation extraction artefact:** `/Users/lukeivers/pos3/workspace/rd-automation/.loam/extractions/rd-automation-5f656bad/` — RESERVED for v0.2.5 HARD gate; do NOT touch at Cycle 3.
- **Canonical jsts-playwright-app fixture:** `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/`.
- **Lens 5 swarming + AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_{swarming_recursive_decomposition,duration_estimation_rubric}.md`.
- **Quality bar:** Luke directive 2026-05-04 (master plan §1 verbatim).

---

## §11 — §self-checks audit (per AC.OGP discipline + master plan §11 precedent)

Every "objective" / "AC" / "constraint" / "capability" named or exemplified in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed audit rows:

| Element | Classified-as | Pass |
|---|---|---|
| "operators file refund disputes against DoorDash + Uber Eats merchant portals at scale" | objective (outcome ✓ / rewrite-survives ✓ / method-loose ✓ / observable ✓ / user-purpose ✓) | ✓ |
| "diff touches VERIFIED objective O.dispute-flow.1; backing rows src/routes/disputeRoutes.js:42-58" | gate output: objective at outcome altitude + implementation-altitude evidence correctly distinguished | ✓ |
| "src/routes/disputeRoutes.js:42-58" | implementation citation (file/line specific) | ✓ |
| "AC.JSTS.express.get.all_orders.src_routes_exportroutes_js" | implementation — v0.1.8 failure-mode the rebuild fixes | ✓ |
| SOC-2 audit-trail floor | constraint (bounds HOW) | ✓ |
| Production-stake `requires_ratification=True` | promotion-gate constraint | ✓ |
| Pre-emption HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS | classification-rule constraint | ✓ |
| Decision I default-no-silent-promotion | promotion-rule constraint | ✓ |
| AC.PRGATE.* + AC.WATCHOBJ.* + AC.RELSMOKE.* | tool-implementation contracts (ladder up to v0.2.5 user-objective) | ✓ |
| "Gate triggers on VERIFIED-objective backing" / "Watch flags coverage shifts" | tool-internal capabilities | ✓ |
| `objective_id` regex `^O\.[a-z][a-z0-9-]*\.\d+$` | structural format constraint | ✓ |
| "STRONG/WEAK" signal-strength | classification labels (orthogonal to banding) | ✓ |
| "Eric reads outcome prose" (Lens 2) | primary-persona-test outcome | ✓ |
| "two-source verification" (Lens 4) | banding-rule constraint | ✓ |

**Drift-mode check** (each recognised + avoided):

- **Symbol-as-AC** ✓ — backing-row citations named as backing-implementation evidence; objective text + implementation evidence kept distinct.
- **Function-name-as-AC** ✓ — `classify_evidence` / `_proposed_objectives_from_classification` named as functions; ACs are AC.PRGATE.*/AC.WATCHOBJ.*/AC.RELSMOKE.* families.
- **Feature-as-objective** ✓ — gate/watch/smoke named as tool capabilities.
- **Test-name-as-implementation** ✓ — AC.RELSMOKE.1 distinguishes outcome-shape (HARD_BLOCK with objective text) from implementation-shape tests.
- **Gap-as-objective** ✓ — `NovelDiff` carries gap signal forward to v0.2.4.
- **Constraint-as-objective** ✓ — Decision I + production-stake + pre-emption-order classified as constraints.
- **Implementation-detail-as-constraint** ✓ — STRONG/WEAK classification, not constraint.

§self-checks pass on every "objective" / "AC" / "constraint" / "capability" named in this plan-doc. ✓

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-3 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/rebuild/plans/v0-2-3-master-plan.md`). Cycle 1 method decisions at `docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md` §7. Cycle 2 method decisions at `docs/rebuild/plans/v0-2-3-cycle-2-backing-map-and-ratification-reframe.md` §7.

### Commit SHAs

- Amendment commit: `e277c274f6b120ac5fe68c76a7e425a53ea1bcd5` —
  `chore(amend): v0-2-3-cycle-3-pr-safety-watch-reframe-and-soft-smoke manifest+apply — dev-sdlc BASELINE+sidecar bump to 4157092`
- Seal commit: `f78bb362931e0e7b7a64782c1c407c812a941533` —
  `chore(seals): v0-2-3-cycle-3-pr-safety-watch-reframe-and-soft-smoke — dev-sdlc at e277c27`

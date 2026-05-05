# v0.2.4 Cycle 1 — Completeness interview (augmented objective set via PM batch interview)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Predecessor:** v0.2.4 master plan committed at `f230333` (parent §3 Cycle 1 + §6.1 + §9 method-decision register; trim discipline applied).
**Parent plan:** `docs/rebuild/plans/v0-2-4-master-plan.md` §3 Cycle 1 + §9.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md` (`d37c623`); auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2. The §self-checks (§8 of that doc) were applied to every "objective" / "AC" / "constraint" / "capability" named here; §11 records the audit pass.
**BASELINE (pre-build tip):** to be set by build agent to the source-edit commit when source lands.

**Quality bar (Luke directive 2026-05-04, carried verbatim):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 1 IS the v0.2.4 substrate. Missing-objective detection fully implemented (heuristic pre-pass + LLM-as-judge cap 5; not a stub). PM batch API consumption is read-only — zero edits to `framework/per-project-pm/`. One-question-at-a-time enforced structurally via `surface_next_questions_batch(n=1)`. Augmented objective set persists at workspace-local YAML mirroring v0.2.3 backing-map path conventions. Audit-log per interview action (Decision P SOC-2 floor). Cost band $0.20 default, $0.05–$0.50 halt-and-surface. **No partial features.** Self-checks pass on every example named per §11.

---

## §1 — Outcome shape

Cycle 1 ships the **completeness interview** that turns v0.2.3's read-only objectives.yaml output into an **augmented objective set** the user has confirmed (or adjusted, or extended). The persona presents extracted objectives back to the user, flags missing-but-expected objectives the synthesis pass didn't surface (heuristic pre-pass + LLM-as-judge), and runs a one-question-at-a-time interview via the v0.1.7 PM batch API. User responses (confirm, adjust-text, flag-as-out-of-scope, free-form-add) flow through `record_response` and re-shape the augmented set on disk.

**Pin (outcome 1):** A user invoking `loam odd-extract` on a fresh workspace, then `loam odd-extract interview`, sees the persona present the extracted objectives one at a time + present any heuristic/LLM-flagged missing-objective candidates one at a time, and the augmented set lands at `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml`. Verified by `test_AC_COMPINT_4_pm_batch_consumer.py` + `test_AC_COMPINT_11_integration.py`.

**Pin (outcome 2):** An interview interrupted mid-flow (`/clear`, kill -TERM, restart) resumes from the next un-answered question without re-asking already-answered ones. Augmented-set persistence is the source of truth; in-flight state is reconstructed from `state.yaml` + audit-log entries. Verified by `test_AC_COMPINT_10_resume.py`.

**Pin (outcome 3):** Every interview action emits an audit-log event_kind so SOC-2 floor is preserved (`completeness_interview_start`, `objective_confirmed`, `objective_adjusted`, `objective_flagged_missing`, `objective_added_by_user`, `completeness_interview_end`). Verified by `test_AC_COMPINT_8_audit_log.py`.

**Pin (outcome 4):** Cost band stays under $0.20 default for the LLM-as-judge missing-objective pass on the canonical jsts-playwright-app fixture; halt-and-surface fires if calibrated cost lands outside $0.05–$0.50 (parent master plan §9 envelope). Verified by `test_AC_COMPINT_9_cost_band.py`.

**Pin (Eric-relevance):** On Eric's rd-automation fixture (Q4=Yes production-stake; Q5 SOC-2 CC6 + auth-bypass finding; no security-shape objective in v0.2.3 extracted set), the missing-objective detection flags "audit trail identifies who initiated each dispute" as a high-confidence missing candidate. Eric confirms via question-shape (b)(1) → augmented set carries it as PLAUSIBLE → Cycle 2 surfaces backing gap. Verified structurally by synthetic-Eric fixture in AC.COMPINT.11.

---

## §2 — Lens checks (per CLAUDE.md design lenses; abbreviated where obviously satisfied)

**Lens 1 — Claude-leverage-first.** Composes on Anthropic Messages API + prompt caching for the LLM-as-judge missing-objective pass (claude-api SKILL conventions inherited from v0.2.3 Cycle 1). Reuses v0.1.7 `PMRuntime.enqueue_decision` / `surface_next_questions_batch(n=1)` / `record_response` verbatim — zero PM-side edits. Reuses v0.1.6 `BudgetEnvelope` + `BudgetExceededError`. Reuses v0.2.3 `Objective` Pydantic model + `ConfidenceBand`. Reuses v0.2.3 `observability.write_audit_entry`. Pass.

**Lens 2 — Harness + primary-persona value.** Primary-persona test: translation burden drops from "user manually re-reads objectives.yaml + cross-references README to spot gaps" to "persona presents one Q at a time; user answers in plain English; augmented set updates." Pass. Harness test: `interview.py` + `completeness.py` are reusable harness primitives (Cycle 2 gap-analysis consumes augmented-objectives.yaml; Cycle 3 build-next consumes it; v0.2.0 auto-skill-capture composes structurally). Pass.

**Lens 3 — ODD authoring.** Outcome + 11 named ACs (§3) + halt triggers (§5 + §6) + smoke (§4) + method-loose. Method-loose holds: heuristic pre-pass details (regex patterns, keyword sets) are builder's call; LLM-judge prompt body is builder's call; question-shape rendering prose is builder's call; YAML field-names within the `AugmentedObjectiveSet` schema constraint are builder's call. Constraints pin WHAT (one-question-at-a-time, PLAUSIBLE-default for added objectives, persistence path, cost band, audit-log floor); HOW is the builder's. Pass.

**Lens 4 — Prompt scope ↔ confidence.** **HIGH** for shape: master plan §3 Cycle 1 names the 8 load-bearing concerns (augmented-set Pydantic; missing-objective LLM-judge; heuristic pre-pass; PM-batch consumer; question-shape design; promotion-rules; persistence; audit-log + cost + resumability + tests); v0.2.3 substrate verified-working; v0.1.7 PM batch API verified-working. Tight scope: extension to existing `plugins/dev-sdlc/odd-extractor/` component, additive Pydantic models in `spec.py`, two new modules (`completeness.py` + `interview.py`), AC-shaped tests. **MEDIUM** for missing-objective LLM-judge prompt design (master plan §6.1 + §7.1 names this risk); commitments at AC.COMPINT.2 + AC.COMPINT.3. **MEDIUM** for question-shape ergonomics under PM batch API (one-question-at-a-time means three render shapes — confirm-existing / flag-missing-candidate / free-form-add — must each fit a single `enqueue_decision` text payload); commitments at AC.COMPINT.5. **HIGH** for substrate preservation. Pass overall.

**Lens 5 — Swarming.** Single-component fence under `plugins/dev-sdlc/odd-extractor/`. Per-concern module decomposition (`completeness.py` for missing-objective detection + `interview.py` for PM-batch interview-loop) gives the tightest AC-per-module mapping. `max_planner_depth: 1` — sub-planning the LLM-judge prompt is coordination overhead with no tighter AC. Model rationale: Sonnet default; Opus permitted for missing-objective LLM-judge prompt design specifically with mandatory `model-rationale:` line if depth exceeds Sonnet's reach. Pass.

---

## §3 — AC enumeration — `AC.COMPINT.*` (locked, 11 ACs)

Each AC has at least one explicit pytest. ODD §2.5: every line of code, branch, test maps to a named AC. §self-checks 1-5 ran on every example outcome / capability / constraint named in this plan-doc; §11 records the audit.

- **AC.COMPINT.1 — Augmented-set Pydantic shape.** Additive `Objective.source: Literal["extracted","added_by_user","flagged_by_persona"]` with default `"extracted"` (round-trip safe). New container `AugmentedObjectiveSet` carrying `objectives: list[Objective]` + `extraction_id: str` + `augmented_at: datetime` + `interview_audit_path: str`. `model_validator` enforces no duplicate `objective_id`. Fence: `spec.py` extension. Test: `test_AC_COMPINT_1_augmented_set.py` — round-trip; ValidationError on duplicate ID; default `source` on legacy objectives; explicit `source` on new instances.

- **AC.COMPINT.2 — Missing-objective LLM-as-judge.** New module `completeness.py`; function `flag_missing_objectives(objectives, *, multi_source_bundle, anthropic_client) -> list[FlaggedMissing]`. Invoked AFTER heuristic pre-pass; consumes priors. System prompt injects lean grounding doc §altitudes + §self-checks verbatim. User prompt: existing objectives YAML + heuristic priors + multi-source bundle. Response: structured JSON `{flagged: [{candidate_text, reasoning, evidence_refs, priority}]}`. **Cap of 5 candidates** per run (prompt-side + post-validation truncation). `FlaggedMissing` carries `candidate_text` (≥20 chars), `reasoning`, `evidence_refs`, `priority: Literal["high","medium","low"]`. Test: `test_AC_COMPINT_2_llm_judge.py` — stub Anthropic with canned responses; cap-of-5 enforced on 8-candidate response; ValidationError on malformed; prompt-structure verified.

- **AC.COMPINT.3 — Heuristic pre-pass.** In `completeness.py`; function `heuristic_priors(objectives, *, multi_source_bundle) -> list[HeuristicPrior]`. Runs BEFORE LLM-judge. Baseline patterns (builder iterates within scope):
    1. **Production-stake-without-security-objective** — survey `production_use=Yes` AND no objective with `domain in {"auth","security","audit"}` → priority=high.
    2. **Survey-mentions-compliance-without-compliance-objective** — survey body contains `{"SOC-2","HIPAA","PCI","GDPR","compliance","audit trail"}` AND no objective with `domain in {"compliance","audit"}` → priority=high.
    3. **Data-modify-routes-without-persistence-objective** — evidence rows include `POST|PUT|DELETE` route shapes AND no objective with `domain in {"persistence","data-write"}` → priority=medium.
  Returns `list[HeuristicPrior]` with `prior_text`, `priority`, `evidence_refs`. LLM-judge consumes; may augment, downgrade, filter. Test: `test_AC_COMPINT_3_heuristic_priors.py` — fixtures per heuristic; assert priors + no false-positives on clean fixture.

- **AC.COMPINT.4 — PM batch API consumer.** New module `interview.py`; function `run_interview(workspace_root, *, pm_handle, augmented_set_in, flagged_missing) -> AugmentedObjectiveSet`. Read-only PM consumer — zero PM-side edits. Flow: (1) `PMRuntime.from_workspace(workspace_root, pm_handle)`; (2) `enqueue_decision(question_text, provenance="completeness_interview:<key>")` for each existing-objective + flagged-missing candidate; (3) loop `surface_next_questions_batch(n=1)` → render → `record_response`. `n=1` enforced per-call (not via `onboarding_mode`); provenance prefix is response-routing key. Test: `test_AC_COMPINT_4_pm_batch_consumer.py` — synthetic PM contract; assert one-at-a-time; assert all responses recorded; `pending_response_for` clears between batches.

- **AC.COMPINT.5 — Question-shape design (3 shapes).** Each `enqueue_decision` text follows one of:
    - **(a) confirm-existing-objective.** "Does this objective accurately describe what you want? `<O.<id>>: <text>` — (1) yes-keep, (2) yes-but-adjust-text [paste], (3) no-flag-out-of-scope, (4) skip."
    - **(b) flag-missing-candidate.** "Persona-flagged missing: `<candidate_text>` (priority=`<H/M/L>`; reasoning: `<reasoning>`). Add? — (1) yes-add-as-PLAUSIBLE, (2) yes-but-rewrite [paste], (3) no-skip, (4) defer."
    - **(c) free-form-add.** Surfaced ONCE at end: "Any objectives we missed? — answer with one or more outcome statements (or 'no')."
  Response-parser matches numeric prefix + free-text branches. Malformed → one re-ask cap; second malformed → defer slot + flag for human review. Test: `test_AC_COMPINT_5_question_shapes.py` — payload format per shape; parser handles each branch; malformed fallback.

- **AC.COMPINT.6 — Promotion rules + interview-added defaults.** User-added objectives (Shape (b)(1)/(b)(2)/(c)) default to `confidence=PLAUSIBLE`, `source="added_by_user"`, `evidence.survey_line_refs` populated from question-provenance audit-log entry (satisfies PLAUSIBLE invariant without faux test/README evidence) + `evidence.rationale="user-added via completeness interview"`. User-flagged-out-of-scope (Shape (a)(3)) → removed from set + audit-log records rationale. User-adjusted text (Shape (a)(2)) → in-place text update, `source` preserved (text-edit ≠ re-source). Persona-flagged accepted (Shape (b)(1)) → `source="flagged_by_persona"`. v0.2.3 ratify path handles P→V; no new ratify surface. Test: `test_AC_COMPINT_6_promotion_rules.py` — each branch path; assert resulting shape + source + PLAUSIBLE invariants.

- **AC.COMPINT.7 — Persistence at canonical workspace path.** Augmented set at `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml` (mirrors v0.2.3 `backing-map.yaml` convention; atomic tmp+rename). Schema: `{schema_version: 1, extraction_id, augmented_at, interview_audit_path, objectives: [...]}`. Round-trip via `AugmentedObjectiveSet.model_dump` / `model_validate`. Idempotent on no-change. Test: `test_AC_COMPINT_7_persistence.py` — file written at expected path; round-trip; tmp cleanup; idempotent.

- **AC.COMPINT.8 — Audit-log event_kinds.** Additive 7 new kinds: `completeness_interview_start`, `objective_confirmed`, `objective_adjusted`, `objective_flagged_out_of_scope`, `objective_added_by_user`, `objective_flagged_by_persona`, `completeness_interview_end`. Structured payload via existing `estimate` field (no schema-version bump). Start payload: `{extraction_id, objective_count_pre, flagged_missing_count}`. Per-objective: `{objective_id, response_audit_path, response_text_hash}`. End: `{extraction_id, objective_count_post, added_count, removed_count, adjusted_count}`. Test: `test_AC_COMPINT_8_audit_log.py` — full run; all kinds present; payload round-trip.

- **AC.COMPINT.9 — Cost band for LLM-as-judge.** Default ceiling $0.20 per interview-run; halt band $0.05–$0.50. Pre-call dry-run estimate via SDK `messages.count_tokens` if available, else 4-chars-per-token (v0.2.3 Cycle 1 precedent). Live mode: `enforce_budget(estimate, BudgetEnvelope(ceiling_cents=20))` raises `BudgetExceededError`. Build agent halts-and-surfaces if calibrated cost on canonical fixture lands outside band. Heuristic pre-pass is zero-LLM-cost. Test: `test_AC_COMPINT_9_cost_band.py` — estimate within ±10%; `BudgetExceededError` on overrun; `--budget-override` allows.

- **AC.COMPINT.10 — Resumability across `/clear` + restart.** Mid-interview interrupt → re-invoking reads `state.yaml` + `decision-queue.yaml` + audit-log; reconstructs from PM's crash-safe surface. Already-answered questions are no longer in the FIFO queue (consume-on-surface contract). Augmented set updated AFTER each `record_response` (per-response, not per batch end) → partial state durable. Mid-LLM-judge interrupt re-runs LLM call (heuristic priors cached via audit-log; LLM call fresh). Test: `test_AC_COMPINT_10_resume.py` — kill at three breakpoints (after Q2 / after Q4 / mid-LLM-judge); re-invoke; final set matches no-interrupt baseline.

- **AC.COMPINT.11 — Component tests on 3+ synthetic fixtures.** Fixtures under `plugins/dev-sdlc/odd-extractor/tests/fixtures/completeness-interview/`:
    1. `clean-codebase/` — extracted set "complete"; 0 heuristic priors; 0 LLM-flagged; user confirms all. Augmented == extracted + `source="extracted"`.
    2. `eric-shape/` — set lacks security objective; `production_use=Yes` + SOC-2 mention. Heuristic-1 fires; LLM-judge promotes to flagged; user adds → `O.security.audit_trail.1` PLAUSIBLE `source="added_by_user"`.
    3. `persona-flagged/` — set lacks data-persistence objective; POST/DELETE evidence rows. Heuristic-3 fires; LLM-judge confirms; user accepts → `source="flagged_by_persona"`.
  Each exercises full path: heuristic pre-pass → LLM-judge → PM-batch interview (response-stub) → persistence → audit-log. Test: `test_AC_COMPINT_11_integration.py` — three sub-tests; per-fixture source-distribution; full pipeline e2e.

---

## §4 — Component & file layout

**PRIMARY scope:** `plugins/dev-sdlc/odd-extractor/` (the existing component's sealed fence; new modules + tests + Pydantic-model extensions land under it).

**TERTIARY admission:** `docs/rebuild/plans/` (universal-paths admission for plan-doc paper trail).

### Existing paths (extend in-place; sealed-content unchanged)

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py` — extend with `Objective.source` enum field (additive, default `"extracted"`); new `AugmentedObjectiveSet` container model. Existing `Objective`/`Constraint`/`Capability`/etc unchanged at type level.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/observability.py` — extend event_kinds (7 new kinds per AC.COMPINT.8); structured payload uses existing `estimate` field (no schema-version bump).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — additive subcommand `loam odd-extract interview <workspace>` + `--budget-cents N` integration with cost band per AC.COMPINT.9.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — additive exports.

### New paths (this cycle)

Source modules (under `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/`):

- `completeness.py` — heuristic pre-pass + LLM-as-judge missing-objective detection. Function `flag_missing_objectives(objectives, *, multi_source_bundle, anthropic_client) -> list[FlaggedMissing]`; helper `heuristic_priors(...) -> list[HeuristicPrior]`. Hosts heuristic patterns + LLM-judge prompt body + cap-of-5 enforcement + cost-budget integration.
- `interview.py` — PM batch API consumer + question-shape rendering + response-parser + augmented-set persistence + resume-state reconstruction. Function `run_interview(workspace_root, *, pm_handle, augmented_set_in, flagged_missing) -> AugmentedObjectiveSet`.

Tests (under `plugins/dev-sdlc/odd-extractor/tests/`):

- `test_AC_COMPINT_1_augmented_set.py`
- `test_AC_COMPINT_2_llm_judge.py`
- `test_AC_COMPINT_3_heuristic_priors.py`
- `test_AC_COMPINT_4_pm_batch_consumer.py`
- `test_AC_COMPINT_5_question_shapes.py`
- `test_AC_COMPINT_6_promotion_rules.py`
- `test_AC_COMPINT_7_persistence.py`
- `test_AC_COMPINT_8_audit_log.py`
- `test_AC_COMPINT_9_cost_band.py`
- `test_AC_COMPINT_10_resume.py`
- `test_AC_COMPINT_11_integration.py`

Fixtures (under `plugins/dev-sdlc/odd-extractor/tests/fixtures/completeness-interview/`):

- `clean-codebase/` — synthetic v0.2.3 extraction artefacts (extraction-dir layout, objectives.yaml + multi-source bundle stub) where heuristics produce 0 priors and LLM-judge returns 0 flagged.
- `eric-shape/` — extraction artefacts lacking security objective + survey snippet with `production_use=Yes` + SOC-2 substring; heuristic-1 fires.
- `persona-flagged/` — extraction artefacts lacking data-persistence objective + evidence rows showing POST/DELETE routes; heuristic-3 fires.

### Smoke dimensions (per master plan §3 Cycle 1)

- **D1 (cold-state)** ✓ — `loam odd-extract interview <fresh-workspace>` against canonical fixture produces `augmented-objectives.yaml` + audit-log entries. Verified by `test_AC_COMPINT_11_integration.py`.
- **D5 (cross-session)** ✓ — augmented-set + audit-log persist at `<workspace>/.loam/extractions/<repo-id>/`; survive `/clear`. Subsequent session reads them; resume verified. Verified by `test_AC_COMPINT_10_resume.py` + `test_AC_COMPINT_7_persistence.py`.
- **D6 (telemetry-floor)** ✓ — per AC.COMPINT.8. Verified by `test_AC_COMPINT_8_audit_log.py`.
- **D2 (steady-state)** inherited — re-run interview on completed augmented set is no-op (FIFO queue empty; nothing to surface).
- **D3 (restart)** inherited — PM's existing crash-safe surface (per v0.1.7 Cycle 4 + Cycle 2 contract) handles mid-interview kill; this cycle adds resume-state reconstruction (AC.COMPINT.10) on top.
- **D4 (reboot)** n/a structurally — odd-extract is invoked-on-demand, not a daemon; filesystem state survives reboot trivially per existing v0.1.8 / v0.2.3 precedent.

**Pre-cycle baseline (full-suite green sweep):** 96 test files in `plugins/dev-sdlc/odd-extractor/tests/` at HEAD (master plan committed at `f230333`); test-count must remain non-decreasing post-Cycle-1 (96 + 11 new files → 107 expected). Baseline test count is a guess — build agent verifies via `pytest --collect-only` pre-edit and reports actual count.

---

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL. Source-of-truth for fence + ACs + smoke + AI-time + out-of-scope lives at §3 above + master plan §3 Cycle 1.

---

## §6 — Honest doubts (F2 RF on this decomposition)

**6.1 — Heuristic false-positive rate.** Heuristic-1 fires whenever survey `production_use=Yes` + no security-domain objective; mis-domained objectives (e.g., `domain="auth_layer"` not `"auth"`) trigger spuriously. *Mitigation:* priors feed LLM-judge (not direct flags); cap-of-5 + Shape (b)(3) "no-skip" bound user cost. Residual ~15% acceptable.

**6.2 — LLM-judge under-flag on novel domains.** Real-time / ML / embedded domains may not match heuristic baseline. *Mitigation:* free-form-add Shape (c) is the structural catch-all.

**6.3 — One-question-at-a-time fatigue at 20+ objectives.** 20 confirmed + 5 flagged = 26 sequential questions. *Mitigation:* (a)(4) "skip" + resume across sessions (AC.COMPINT.10). Optional batched-confirm shape deferred to v0.2.5+.

**6.4 — `Objective.source` extends sealed spec.py.** Additive default-valued field is round-trip-safe; existing tests pass on new shape (AC.COMPINT.1). *Mitigation:* build agent verifies full v0.2.3 test suite green pre-Cycle-1 commit.

**6.5 — `pm_handle` resolution.** AC.COMPINT.4 takes `pm_handle`; persona must know it. *Mitigation:* CLI `--pm-handle` flag; default via `<workspace>/workspace/.loam/pms/` directory scan (zero→halt; one→use; >1→explicit-required). Recorded at §7.

**6.6 — Cost band $0.20 default may be optimistic.** Rich bundle (full README + 5 design docs + 50 tests + 100 evidence rows + survey) ~25K input + 2K output ≈ $0.105 Sonnet — within band but close. *Mitigation:* AC.COMPINT.9 dry-run + halt-and-surface band has 2.5× headroom.

**6.7 — Resume relies on audit-log integrity.** Corrupted / partial-write audit-log could miss `record_response` entries. *Mitigation:* PM's existing tmp+rename (v0.1.7 Cycle 4) prevents partial writes; tmp-rename interrupted → resume re-asks (conservative direction; no silent data loss).

**6.8 — Cycle wall-clock band 12-20 min may be optimistic.** v0.2.3 Cycle 1 actuals (~30 min / 95 calls) suggest underestimate. *Mitigation:* halt-trigger at >3 escalations OR cost-band breach; actuals logged for forward calibration.

---

## §7 — Method-decision register (Cycle-1-specific)

| Decision | Choice | Rationale |
|---|---|---|
| `Objective.source` shape | enum `extracted`/`added_by_user`/`flagged_by_persona`; default `"extracted"` | Master plan §9; Cycle 2/3 provenance routing; round-trip safety. |
| Augmented-set container | `AugmentedObjectiveSet` Pydantic | Symmetric with v0.2.3 `BackingMap`; structural cross-cycle pattern. |
| Persistence path | `<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml` | Mirrors `backing-map.yaml`; co-located with extraction artefacts. |
| Missing-objective detection | Hybrid: heuristic pre-pass + LLM-as-judge (cap 5) | Master plan §6.1; heuristic-only misses domain gaps; LLM-only over-flags. |
| Heuristic baseline patterns | 3 (production-stake-no-security; survey-compliance-no-compliance; data-modify-routes-no-persistence) | Builder iterates within scope; load-bearing patterns named. |
| PM consumption | Read-only — zero PM edits; `n=1` per-call | Master plan §6; v0.1.7 surface complete; structural one-at-a-time. |
| Question shapes | 3 (confirm-existing / flag-missing / free-form-add); free-form-add ONCE at end | AC.COMPINT.5; minimal complete coverage; bounds user fatigue. |
| Malformed-response handling | One re-ask cap; second → defer slot + flag for human review | Bounds frustration; preserves audit-log. |
| User-added defaults | PLAUSIBLE; `survey_line_refs` from interview audit-log | Master plan §9; satisfies PLAUSIBLE invariant cleanly. |
| User-flagged-out-of-scope | Remove from set; rationale in audit-log | Clean removal; provenance preserved for Cycle 2/3. |
| User-adjusted text | In-place; `source` preserved | Text-edit is not re-source. |
| Cost band | $0.20 default; $0.05–$0.50 halt band | Master plan §9 envelope. |
| Token estimation | SDK `count_tokens` if available, else 4-chars-per-token | v0.2.3 Cycle 1 precedent. |
| Resume source | PM audit-log + decision-queue + state.yaml; per-response augmented-set write | AC.COMPINT.10; inherits PM crash-safety contract. |
| Mid-LLM-judge interrupt | Re-run LLM on resume; heuristic priors cached via audit-log | Atomic-call; streaming buffer complexity unjustified. |
| `pm_handle` resolution | CLI `--pm-handle` flag; default via workspace PM-dir scan; halt on zero / explicit on >1 | §6.5 mitigation. |
| Anthropic SDK invocation | Reuses v0.2.3 `synthesis.py` lazy-import + cost-governance pattern | Substrate-preservation; no new dependency. |
| Test stub strategy | Stub Anthropic with fixture-tuned canned responses; no real API in CI | v0.2.3 Cycle 1 precedent. |
| Plan-doc shape | v0.2.3 Cycle 1 + trim discipline (§5 stub) | Luke 2026-05-05; verified at master plan f230333. |

---

## §8 — Provenance trail

- **Master plan:** `docs/rebuild/plans/v0-2-4-master-plan.md` §3 Cycle 1 + §6.1 + §9 (commit `f230333`).
- **Lean grounding doc (auto-loaded):** `docs/odd-llm-grounding.lean.md` at `d37c623`. §self-checks + §drift-modes + §altitudes held in working memory throughout authoring.
- **Sub-plan-doc shape precedent:** `docs/rebuild/plans/v0-2-3-cycle-1-multi-source-objective-synthesis.md` (388 lines pre-trim — this plan is shorter under trim discipline).
- **Trim discipline ratification:** master plan §3 light-entry shape (`f230333`) + plan-before-code-author + plan-docs-author SKILLs (Luke 2026-05-05).
- **v0.2.3 substrate (load-bearing):** Cycle 1 seal `9b9f87c` (Objective/Constraint/Capability + synthesis.py + multi_source.py + altitude_validator.py); Cycle 2 seal `857749c` (BackingMap + ratify); Cycle 3 seal `f78bb36` (PR-safety + watch). v0.2.3 SHIPPED rollup `50b5385`.
- **v0.1.7 PM batch API:** Cycle 4 seal `122a7c8`. `framework/per-project-pm/src/loam/per_project_pm/runtime.py:118/240/313/405` (`PMRuntime` / `enqueue_decision` / `surface_next_questions_batch` / `record_response`).
- **v0.1.6 cost-governance:** `3f1d237` / `88674cb`. `framework/cost-governance/`.
- **v0.2.1 survey-file path (AC.ONBOARD.15):** `~/loam-onboarding-survey.md` shape.
- **Eric survey response:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md` (Q4 production-stake, Q5 SOC-2 + auth-bypass; multi-source synthesis input precedent).
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Lens 5 swarming patterns:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.

---

## §9 — Bookkeeping

Per `loam-amend-cycle` SKILL + master plan §3 Cycle 1:

- **pos-amend apply** (NOT `--amend`); manifest schema v3 (`plan_doc_ref:` + no `amendment.number`).
- **Single semantic commit on apply:** `feat(odd-extractor): v0.2.4 Cycle 1 — completeness interview`.
- **Short-form seal commit** per AC.DPS2 schema-v3.
- **§14 backfill** as separate post-seal commit per AC.D-sa.7.
- **Master plan §9** per-cycle SHA backfill row updates with apply + seal SHAs (master plan §9 is canonical SHA register; this sub-plan §14 is cycle-local audit trail per trim discipline).
- **Tag policy:** v0.2.4 SHIPPED rollup tags after Cycle 3 seals + SOFT smoke green; tag NOT pushed until v0.2.5 ship per master plan §3.
- **Status file:** master plan §9 per-cycle SHA register row + STATE.md SHIPPED entry summary (per trim discipline).

---

## §10 — Halt triggers (in-flight)

Standard set + Cycle-1-specific:

- WD drifts to pos3 (canonical pos-v2 only).
- Plan-before-code violation (any source-edit before plan-doc commit).
- Fence breach (edits outside `plugins/dev-sdlc/odd-extractor/` + universal admissions).
- Heuristic pre-pass discovers a domain pattern not in the baseline 3 → halt + surface (may need master plan §9 amendment).
- LLM-judge cost calibration on canonical fixture lands outside $0.05–$0.50 band → halt.
- LLM-judge prompt design demands Opus → halt-and-surface with `model-rationale:` line.
- PM batch API surface needs non-trivial extension (master plan said read-only consumer) → halt + surface (escalate to master plan amendment).
- `Objective.source` enum extension breaks v0.2.3 test suite → halt + surface (substrate-preservation fail).
- Question-shape ergonomics demand more than 3 shapes → halt + surface.
- Resumability test (AC.COMPINT.10) reveals PM crash-safety gap → halt + surface (escalate to v0.1.7 amendment).
- Cycle wall-clock >40 min (2× upper band) with no progress → halt.
- More than 3 escalations needed → halt.
- ODD §2.5 violations in plan-doc OR surrounding code → halt + surface.

---

## §11 — §self-checks audit (per AC.OGP discipline)

Every "objective" / "AC" / "constraint" / "capability" named in this plan-doc was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed:

| Element | Classified-as | Pass |
|---|---|---|
| "augmented objective set persisted" (Pin 1) | tool-altitude capability output | ✓ derivative artefact serving v0.2.5 user-objective |
| "audit trail identifies who initiated each dispute" (Eric example) | objective | ✓ outcome / survives rewrite / observable / user-purpose (SOC-2 CC6) |
| "completeness interview" / "missing-objective detection" / "augmented set" | tool capabilities | ✓ tool-altitude; serve user-objective at v0.2.5 |
| "production-stake" / "SOC-2 CC6" (Eric heuristic) | constraints | ✓ bound solution-space; NOT outcomes |
| "POST/DELETE adapter route shapes" (heuristic-3) | implementation evidence | ✓ correctly named as evidence, NOT objective |
| "one-question-at-a-time" / "Cost band $0.20" | constraints on interview-shape / resource-use | ✓ bound HOW; NOT outcomes |
| AC.COMPINT.1-11 (the ACs of THIS plan-doc) | tool-internal implementation contracts | ✓ ladder up to v0.2.5 user-objective |

**Drift-mode check:** Symbol-as-AC ✓; Function-name-as-AC ✓; Feature-as-objective ✓ (interview/detection named as capabilities); Test-name-as-implementation ✓ (tests assert OUTCOMES); Gap-as-objective ✓ (this cycle produces FLAGS that become objectives only on user ratify; gaps are Cycle 2); Constraint-as-objective ✓; Implementation-detail-as-constraint ✓.

§self-checks pass on every element named. ✓

---

## §12 — Acceptance gate

Plan-doc is gate-ready when:

1. ✓ §1 Outcome shape pinned to verification surfaces.
2. ✓ §2 Lens checks all pass.
3. ✓ §3 AC family enumerated (11 ACs locked; each with pytest path).
4. ✓ §4 Component & file layout enumerated; smoke dimensions named.
5. ✓ §5 stub paragraph (trim discipline applied).
6. ✓ §6 F2 RF gaps named with mitigations.
7. ✓ §7 Method-decision register populated.
8. ✓ §8 Provenance trail cited with SHAs.
9. ✓ §9 Bookkeeping aligned with `loam-amend-cycle` SKILL.
10. ✓ §10 Halt triggers (in-flight) enumerated.
11. ✓ §11 §self-checks audit pass on every named element.
12. ✓ §14 method-decision record heading present (per AC.D-sa.7 lint).
13. ✓ Manifest companion authored at `docs/rebuild/plans/v0-2-4-cycle-1-completeness-interview.manifest.yaml`.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-1 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/rebuild/plans/v0-2-4-master-plan.md`).

### Commit SHAs

- Amendment commit: `e1a4239a3d814c2d9bb9536ffb145445e8422802` —
  `chore(amend): v0-2-4-cycle-1-completeness-interview manifest+apply — dev-sdlc BASELINE+sidecar bump to 89f3933`
- Seal commit: `d42ace940c6d594f4d0fdf1e86afed7509c7b2be` —
  `chore(seals): v0-2-4-cycle-1-completeness-interview — dev-sdlc at e1a4239`

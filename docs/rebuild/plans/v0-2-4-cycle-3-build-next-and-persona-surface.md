# v0.2.4 Cycle 3 — Build-next ranking + persona pull-point + release-level SOFT smoke

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.
**Predecessors:** v0.2.4 Cycle 1 (completeness interview) sealed at `d42ace9`; Cycle 2 (gap analysis) sealed at `9d15333`.
**Parent plan:** `docs/rebuild/plans/v0-2-4-master-plan.md` §3 Cycle 3 + §5 release-smoke gate + §9.
**Always-load grounding:** `docs/odd-llm-grounding.lean.md`; auto-loaded structurally per v0.2.2 AC.OGP.1/AC.OGP.2. The §self-checks 1-5 + §drift-modes ran on every "objective" / "AC" / "constraint" / "capability" named here; §11 records the audit.
**BASELINE (pre-build tip):** to be set by build agent to the source-edit commit when source lands.

**Quality bar (Luke directive 2026-05-04, carried verbatim):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

Cycle 3 closes v0.2.4 — gap inventory turned into a ranked candidate list with rationale, persona invokes via CLI, release-level SOFT integration smoke green on canonical jsts-playwright-app. Informative not prescriptive (denylist enforced). Negative-alignment carved to v0.2.6+. After Cycle 3 seal + the v0.2.4 SHIPPED rollup commit, v0.2.4 is locked-and-shipped (local; Eric ship at v0.2.5). **No partial features.** §self-checks pass on every example named per §11.

---

## §1 — Outcome shape

Cycle 3 ships the **build-next ranking** that consumes Cycle 2's `gap-inventory.yaml` + (optionally) onboarding-survey priorities + interview-added objectives, and produces a ranked `BuildNextRecommendation` persisted at `<workspace>/.loam/extractions/<repo-id>/build-next.md` (human-readable Markdown) with companion `build-next.yaml` (typed YAML). Persona invokes via CLI flag `loam odd-extract <repo> --build-next` (mirrors Cycle 2's `--gaps` precedent). Release-level SOFT smoke verifies the full path on canonical jsts-playwright-app.

**Pin (outcome 1):** Invoking `loam odd-extract <repo> --build-next` after Cycle 2 produces a top-N candidate list (default 10; `--limit` configurable) at `build-next.md` + `build-next.yaml` + stdout summary, where each candidate carries `gap_id`, composite score, gap-confidence × priority-match × estimated-impact factors, and a 2-4 sentence rationale naming which gap surfaced + which user-priority signal matched. Verified by `test_AC_BLDNXT_9_integration.py`.

**Pin (outcome 2):** Output prose is **informative, not prescriptive** — denylist at output-emit blocks "you should…", "you must…", "we recommend…", "the next step is…" and similar. Rationale phrases findings as "this gap matches your stated priority X / impact Y / backing-confidence WEAK in Z." Verified by `test_AC_BLDNXT_6_denylist.py`.

**Pin (outcome 3):** When survey-context is absent (canonical fixture has no survey at either canonical path), priority-match degenerates to NONE; ranking falls back to gap-confidence × estimated-impact; stdout + `build-next.md` flag the degenerate explicitly. Verified by `test_AC_BLDNXT_3_priority_match.py` + `no-survey-context/` fixture.

**Pin (outcome 4):** Re-running on unchanged inputs produces content-identical recommendation (LLM-judge variance bounded by structured-JSON + temperature=0). Audit-log per stage (`build_next_start` / `build_next_persisted` / `build_next_end`); cost band ≤$0.10 default ($0.02–$0.30 halt). Verified by `test_AC_BLDNXT_4_idempotence.py` + `test_AC_BLDNXT_8_audit_log.py`.

**Pin (outcome 5; release SOFT smoke):** End-to-end on jsts-playwright-app: extraction → `--interview` (PM-mock; 1 missing objective added) → `--gaps` (both categories populated) → `--build-next` (top-N ranked with rationale); D1/D2/D3/D5/D6 ✓; D4 n/a; §self-checks pass-rate ≥90% over augmented objectives + capabilities + constraints. Verified by `test_AC_PERSONA_PULL_4_release_smoke.py`.

---

## §2 — Lens checks (abbreviated)

**Lens 1 — Claude-leverage-first.** Reuses v0.2.3 Anthropic-client pattern (`synthesis.py`) for priority-match LLM-judge on borderline only; deterministic explicit-formula owns the main path. Reuses `observability.write_audit_entry` (additive kinds), Cycle 1 `AugmentedObjectiveSet`, Cycle 2 `GapInventory`, framework `cost-governance`, `workspace-bootstrap.survey_parser` (lazy-import) — all read-only. No new SKILL.md per master plan §6.3. Pass.

**Lens 2 — Harness + primary-persona value.** Primary-persona: translation drops from "user manually compares gap-inventory.yaml against survey priorities" to "persona invokes one CLI; ranked options with rationale." Harness: `build_next.py` reusable; v0.2.5 HARD-gate ship calls same surface; v0.2.6+ negative-alignment composes via Cycle 2 `Gap.negative_alignment_evidence` forward-compat seam (third category surfaces without ranking-API change). Pass.

**Lens 3 — ODD authoring.** Outcome (§1) + 13 named ACs (§4) + halt triggers (§8) + smoke (§6) + method-loose. Method-loose: weight tuning, denylist phrase growth, rationale template, stdout format, LLM-judge prompt design — all builder's call within AC scope. Constraints pin WHAT; HOW is builder's. Pass.

**Lens 4 — Prompt scope ↔ confidence.** **HIGH** for shape: master plan §3 Cycle 3 names 13 load-bearing concerns; Cycle 2 sealed yesterday with `GapInventory` substrate this consumes. Tight: existing component extension, additive Pydantic, one new module, CLI flag matching `--gaps`. **MEDIUM** for ranking-formula weights (master plan §6.2; halt-on-collapse on `mixed/` fixture). **MEDIUM** for denylist phrase set (~15% slip-past acceptable per master plan §7.3). **HIGH** for substrate preservation + SOFT smoke gate shape. Pass.

**Lens 5 — Swarming.** Single-component fence; one new module + CLI flag. Two AC families kept separate (BLDNXT = core; PERSONA-PULL = surface + smoke gate); further decomposition is coordination overhead. `max_planner_depth: 1` — leaf cycle. Model rationale: Sonnet default; Opus only if LLM-judge prompt design requires (build agent surfaces). Pass.

---

## §3 — Single-component fence

**PRIMARY scope:** `plugins/dev-sdlc/odd-extractor/` (existing component's sealed fence; new module + tests + Pydantic-model extensions + CLI flag land under it).

**TERTIARY admission:** `docs/rebuild/plans/` (universal-paths admission for plan-doc paper trail).

**Read-only compose-points:**
- `gap_analysis.py` (consumes `GapInventory` + `Gap`).
- `spec.py` (consumes `Objective` + `AugmentedObjectiveSet` + `Gap` + `GapInventory` + `ConfidenceBand`).
- `interview.py` (consumes `load_augmented_objectives` for interview-derived priorities).
- `multi_source._read_user_survey` (lazy-import; consumes survey-context per AC.OBJX.9 read-order: `<repo>/.loam/onboarding-survey.md` then `~/loam-onboarding-survey.md`).
- `synthesis.py` (Anthropic-client construction pattern reused — no edits).
- `framework/cost-governance/` (LLM-judge budget; existing surface).
- `framework/workspace-bootstrap.survey_parser` (lazy-import; existing AC.ONBOARD.15 parser).

**Explicit exclusions:** zero edits to `framework/per-project-pm/`, `framework/cost-governance/`, `framework/workspace-bootstrap/`, `framework/loam-amend/`, `plugins/dev-sdlc/seals/`, `plugins/dev-sdlc/SEAL_COMMIT*`. Zero edits to v0.2.3 sealed surfaces (`backing_map.py`, `ratify.py`, `synthesis.py`, `multi_source.py`). Zero edits to Cycle 1+2 sealed surfaces (`completeness.py`, `interview.py`, `gap_analysis.py`) — read-only consumption only. No new SKILL.md (per master plan §6.3 ruling).

---

## §4 — AC enumeration — `AC.BLDNXT.*` + `AC.PERSONA-PULL.*` (locked, 13 ACs)

Each AC has at least one explicit pytest. ODD §2.5: every line of code, branch, test maps to a named AC. §self-checks ran on every named outcome / capability / constraint; §11 records the audit.

### AC.BLDNXT.* — build-next ranking core (9 ACs)

- **AC.BLDNXT.1 — `BuildNextCandidate` Pydantic.** New in `spec.py`: `gap_id: str` (regex per Cycle 2 AC.GAPAN.1); `composite_score: float` ∈ [0.0, 1.0]; `gap_confidence_factor: float`; `priority_match_factor: float | None` (None on degenerate); `estimated_impact_factor: float`; `priority_match_signal: Literal["survey","interview","keyword","llm_judge","none"]`; `rationale: str` ≥40 chars; `category: Literal[...]` mirrored from source `Gap`; `objective_id: str | None` mirrored. `model_validator` enforces range + factor-product-matches-composite (rounding tolerance documented). Test: `test_AC_BLDNXT_1_candidate_model.py` — round-trip; out-of-range ValidationError; factor/composite consistency; rationale-min-length.

- **AC.BLDNXT.2 — Composite ranking + tie-break.** Helper `_score_candidate` in `build_next.py` computes `composite_score = gap_confidence_factor × priority_match_factor × estimated_impact_factor` (priority_match_factor=1.0 when None → degenerate falls back to gap-confidence × estimated-impact). gap-confidence-factor: STRONG=1.0, WEAK=0.5. estimated-impact-factor (deterministic, no LLM): category-a base 0.8, category-b base 0.5; +0.1 if mapped objective.source `added_by_user`; +0.1 if orphan cluster size ≥3. Tie-break: (1) category-a > category-b; (2) STRONG > WEAK; (3) lex `gap_id`. Test: `test_AC_BLDNXT_2_score_and_tiebreak.py` — table-driven; deterministic ordering; stability.

- **AC.BLDNXT.3 — Priority-match + LLM-judge for borderline.** Helper `_compute_priority_match` in `build_next.py`. Read survey-context via lazy-imported `multi_source._read_user_survey` + interview-added objectives via `objective_added_by_user` audit entries. Returns `(factor ∈ {0.0, 0.5, 1.0}, signal)`. Signal hierarchy: `survey` (Q11/Q12 keyword overlap ≥2 → 1.0; ≥1 → 0.5) > `interview` (gap touches interview-added objective → 1.0) > `keyword` (rationale tokens overlap extracted-objective keywords ≥3 → 0.5) > `llm_judge` (only on borderline: ≥1 < 2 overlap with budget remaining; structured-JSON `{factor, rationale_phrase}`; lean grounding inject; temperature=0) > `none`. LLM-judge cap ≤5/run (per AC.BLDNXT.7). Halt-and-surface if every candidate `none` AND survey file exists. Test: `test_AC_BLDNXT_3_priority_match.py` — survey-present + survey-absent; signal table; LLM-judge mock; halt-on-collapse.

- **AC.BLDNXT.4 — Idempotence semantics.** Re-run on unchanged inputs produces content-identical outputs (excluding `analyzed_at`; LLM-judge structured-JSON at temperature=0 expected stable; halt-trigger if 3 dry-run variance observed). Skip-write on no-change (mirrors AC.GAPAN.5). Test: `test_AC_BLDNXT_4_idempotence.py` — three sequential runs against `no-survey-context/` byte-identical sans `analyzed_at`; LLM-judge case verifies shape stability + deterministic composite given fixed factors.

- **AC.BLDNXT.5 — Output cap + dual output.** Default top-N=10; `--limit N` overrides. (1) `build-next.md` — human-readable Markdown at `<extraction_dir>/build-next.md` (header with analyzed_at + degenerate flag + summary; per-candidate `### Rank K — <gap_id>` with score + factor breakdown + rationale; closing "informative not prescriptive" line). (2) `build-next.yaml` — typed YAML carrying `BuildNextRecommendation` (schema_version=1; extraction_id; analyzed_at; audit_path; degenerate_survey: bool; candidates; truncated_count when underlying-list > limit). Atomic tmp+rename per Cycle 2. Test: `test_AC_BLDNXT_5_dual_output.py` — `--limit` round-trip; truncation accuracy; both files; Markdown heading-ladder parseable; YAML round-trip.

- **AC.BLDNXT.6 — Informative-not-prescriptive denylist.** Module-level seed `_PRESCRIPTIVE_DENYLIST` = `["you should", "you must", "we recommend", "the next step is", "i suggest", "you need to", "must implement", "should implement", "build this next", "do this first"]` (case-insensitive; word-boundary). Helper `_assert_informative_not_prescriptive(text)` raises `OddExtractorError` on hit; checks rendered rationale + stdout + `build-next.md`. Opt-in LLM-judge pass via `LOAM_BUILD_NEXT_LLM_DENYLIST=1` (~$0.02; default off; v0.2.5 calibration may flip). Test: `test_AC_BLDNXT_6_denylist.py` — each phrase flagged; clean rationale passes; LLM-judge mock.

- **AC.BLDNXT.7 — Cost band.** $0.10 default ceiling; $0.02–$0.30 halt band. Pre-flight via `framework/cost-governance` `dry_run` (mirrors AC.COMPINT.9). Per-LLM-judge call ledger record. `--budget-cents` overrides. Halt on pre-flight or mid-run breach. Test: `test_AC_BLDNXT_7_cost_band.py` — default ceiling; override; upper-band halt; lower-band halt sanity.

- **AC.BLDNXT.8 — Audit-log event_kinds.** Additive 3 in `observability.py`: `build_next_start` / `build_next_persisted` / `build_next_end`. Payloads via existing `estimate` field (no schema-version bump). Start: `{extraction_id, gap_count, survey_present, interview_priority_count, llm_judge_budget_cents}`. Persisted: `{extraction_id, candidate_count, truncated_count, llm_judge_invocations, degenerate_survey, build_next_md_path, build_next_yaml_path}`. End: `{extraction_id, duration_ms, total_cost_cents}`. Test: `test_AC_BLDNXT_8_audit_log.py` — full run; 3 kinds in order; round-trip; degenerate + LLM-judge cases.

- **AC.BLDNXT.9 — Component tests on 3 synthetic fixtures.** Under `plugins/dev-sdlc/odd-extractor/tests/fixtures/build-next/`:
    1. `high-priority-match/` — augmented + gap-inventory + synthetic onboarding-survey.md (H2-section per AC.ONBOARD.15; Q11/Q12 keywords intersecting category-a STRONG gap rationale tokens) → top rank-1 has signal `survey` + factor 1.0; rationale names matched keyword.
    2. `no-survey-context/` — same gap-inventory; no survey at either path; interview-priorities empty → all candidates factor None + signal `none`; degenerate flag set; stdout flags degenerate.
    3. `orphan-only/` — gap-inventory with only category-b orphans → top-N entirely orphan candidates; tie-break lex `gap_id`.
  Each fixture: full `build-next.md` + `build-next.yaml` + audit-log + stdout; e2e via `_cmd_build_next`. Test: `test_AC_BLDNXT_9_integration.py` — 3 sub-tests; rank-list + factors + audit + denylist-clean.

### AC.PERSONA-PULL.* — persona surface + release SOFT smoke (4 ACs)

- **AC.PERSONA-PULL.1 — CLI flag `--build-next`.** Additive in `cli.py` `_cmd_dispatch` alongside `--interview` and `--gaps` (master plan §3 prose says "subcommand" loosely; actual is flag-form for symmetry — see §14). Handler `_cmd_build_next(args)` mirrors `_cmd_gaps` shape: resolves repo + workspace + extraction_dir; halts exit code 2 + actionable message if any predecessor missing ("run `loam odd-extract <repo> --gaps` first"). Idempotent (per AC.BLDNXT.4). Test: `test_AC_PERSONA_PULL_1_cli.py` — flag registration; missing-predecessor halt; idempotent; exit codes; stdout format.

- **AC.PERSONA-PULL.2 — Persona pull-point contract (documentation-only).** No new SKILL.md per master plan §6.3 ruling. Documentation lives in module docstring + `loam odd-extract --help` text + `build-next.md` closing line ("Persona invokes via `loam odd-extract <repo> --build-next` on user-question-trigger such as 'what should I build next?'"). Test: `test_AC_PERSONA_PULL_2_contract.py` — docstring contains invocation line; `--help` contains `--build-next`; `build-next.md` carries closing line.

- **AC.PERSONA-PULL.3 — Composition with v0.2.3 ratification.** HYPOTHESISED objectives flagged in rationale prefix ("backing-confidence reflects HYPOTHESISED band — ratify via interview before treating as final priority signal"); not blocked. PLAUSIBLE / VERIFIED ranked normally. Source: `Objective.band` from `AugmentedObjectiveSet`. Test: `test_AC_PERSONA_PULL_3_ratification.py` — mixed-band fixture; flag fires only on HYPOTHESISED-derived candidates; ordering preserved.

- **AC.PERSONA-PULL.4 — Release-level SOFT integration smoke on jsts-playwright-app.** End-to-end against `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/`: extraction → `--interview` (PM-mock; confirm-3 + flag-missing-1-add) → `--gaps` → `--build-next`. D1 ✓ (fresh extraction-dir); D2 ✓ (re-run idempotence); D3 ✓ (mid-stage `kill -TERM` + re-invoke; interview resumes per AC.COMPINT.10; gap + build-next re-run pure); D5 ✓ (Session A persists; Session B reads + invokes); D6 ✓ (≥13 audit entries: 7 completeness + 3 gap + 3 build-next); D4 n/a (invoked-on-demand). §self-checks gate: programmatic + LLM-as-judge double-pass; ≥90% pass §self-checks 1-5. <90% → halt + surface. Test: `test_AC_PERSONA_PULL_4_release_smoke.py` — six sub-tests (per dimension + §self-checks-rate); D4 skip-marker.

---

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL. Source-of-truth for fence + ACs + smoke + AI-time + out-of-scope lives at §3 + §4 + §6 above + master plan §3 Cycle 3 + §5.

---

## §6 — Smoke (REALISTIC CONDITION — release-level SOFT integration smoke)

Per master plan §3 Cycle 3 + §5:

- **D1 cold-state ✓** — fresh extraction-dir; `--build-next` runs full predecessor chain (`--interview` + `--gaps`) producing `build-next.md` + `build-next.yaml` + audit-log + stdout. Verified by AC.PERSONA-PULL.4 + AC.BLDNXT.9.
- **D2 steady-state ✓** — re-run idempotent on byte-identical inputs; LLM-judge variance bounded per AC.BLDNXT.4. Verified by AC.BLDNXT.4 + AC.PERSONA-PULL.4.
- **D3 restart ✓** — mid-run `kill -TERM` → re-invoke clean. `build_next` is pure (Cycle 2 AC.GAPAN.5 pattern); LLM-judge resume re-runs the call (master plan §7.8 precedent). Verified by AC.PERSONA-PULL.4.
- **D4 reboot — n/a** — invoked-on-demand, not daemon; filesystem state survives trivially per Cycle 1+2 precedent.
- **D5 cross-session ✓** — Session A persists; Session B reads + invokes. Verified by AC.PERSONA-PULL.4.
- **D6 telemetry-floor ✓** — ≥13 audit entries (7 completeness + 3 gap + 3 build-next); SOC-2 floor (Decision P) honored. Verified by AC.BLDNXT.8 + AC.PERSONA-PULL.4.

**§self-checks pass-rate gate:** programmatic + LLM-as-judge double-pass over augmented objectives + capabilities + constraints from canonical jsts-playwright-app run; ≥90% pass §self-checks 1-5. <90% → halt + surface. Verified by AC.PERSONA-PULL.4.

**Full-suite green sweep** — pre-Cycle-3 odd-extractor + cost-governance + per-project-pm + workspace-bootstrap tests at HEAD (Cycle 2 seal `9d15333` or successor; ≈456 odd-extractor test functions counted via grep at HEAD — full-suite count requires editable install, NOT empirically verified by this session) all pass post-Cycle-3; halt on regression.

**HARD gate deferred to v0.2.5** — rd-automation HARD-gate is v0.2.5's ship target per master plan §3 v0.2.5.

---

## §7 — Out of scope (this cycle)

- HARD smoke gate against rd-automation → v0.2.5.
- Negative-alignment in build-next ranking → v0.2.6+ (forward-compat seam exists at `Gap.negative_alignment_evidence` from Cycle 2 AC.GAPAN.8; build-next will surface third-category candidates without ranking-API change once v0.2.6+ populates the field).
- Watch / PR-safety composition (auto-trigger build-next on commit / PR open) → post-v0.2.5.
- New SKILL.md for "what to build next?" pattern → never at v0.2.4 per master plan §6.3 (v0.2.0 auto-skill-capture composes if recurs).
- Auto-promotion of build-next candidates to PRs / branches / issues → never (informative not prescriptive per AC.BLDNXT.6).
- Composite-score weight tuning / rationale-prose template polish beyond AC scope → builder's call within named ACs; revisit after Eric calibration data at v0.2.5.
- Eric ship → v0.2.5 (paused per Luke 2026-05-05).

---

## §8 — Halt triggers (in-flight)

Standard set + Cycle-3-specific:

- WD drifts to pos3 (canonical pos-v2 only).
- Plan-before-code violation (any source-edit before plan-doc commit).
- Fence breach (edits outside `plugins/dev-sdlc/odd-extractor/` + universal admissions).
- AC.BLDNXT.3 priority-match collapses to `none` for every candidate when survey file exists at either canonical path → halt + surface (signal-detection broken).
- AC.BLDNXT.4 idempotence test fails on LLM-judge variance across 3 sequential dry-runs → halt + surface (ranking-shape unstable).
- AC.BLDNXT.6 denylist seed misses ≥1 of the explicit named test phrases → halt + surface (denylist incomplete).
- AC.BLDNXT.7 cost-band breach (pre-flight estimate >$0.30 OR mid-run actuals exceed override) → halt + surface.
- AC.PERSONA-PULL.4 §self-checks pass-rate <90% on canonical jsts-playwright-app run → halt + surface (release-gate breach per master plan §3 Cycle 3).
- LLM-judge invocation count exceeds AC.BLDNXT.3 cap of 5 per run → halt + surface (heuristic borderline-detection too loose).
- Cycle wall-clock >36 min (2× upper band 18 min) with no progress → halt.
- More than 3 escalations needed → halt.
- ODD §2.5 violations in plan-doc OR surrounding code → halt + surface.
- §self-checks fail on any "objective" / "AC" / "constraint" / "capability" introduced this cycle → halt + restate before commit.

---

## §9 — Bookkeeping

Per `loam-amend-cycle` SKILL + master plan §3 Cycle 3:

- **pos-amend apply** (NOT `--amend`); manifest schema v3 (`plan_doc_ref:` + no `amendment.number`).
- **Single semantic commit on apply:** `feat(odd-extractor): v0.2.4 Cycle 3 — build-next + persona surface + SOFT smoke`.
- **Short-form seal commit** per AC.DPS2 schema-v3.
- **§14 backfill** as separate post-seal commit per AC.D-sa.7.
- **Master plan §9** per-cycle SHA backfill row updates Cycle 3 apply + seal SHAs (master plan §9 is canonical SHA register; this sub-plan §14 is cycle-local audit trail per trim discipline ratified Luke 2026-05-05).
- **STATE.md SHIPPED entry** + roadmap §8 update + ODD-rebuild master plan §3 v0.2.4 row update at v0.2.4 SHIPPED rollup commit (post-Cycle-3-seal + post-SOFT-smoke-green).
- **Tag policy:** v0.2.4 SHIPPED rollup tags `v0.2.4` after Cycle 3 seals + SOFT smoke green; tag NOT pushed until v0.2.5 ship per master plan §3.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

**10.1 — CLI form-mismatch with master plan prose.** Master plan §3 Cycle 3 calls `loam odd-extract build-next <workspace>` a "subcommand"; actual implementation uses flag-form `--build-next` for symmetry with Cycle 2's `--gaps`. *Mitigation:* recorded as method-decision §14; CLI behavior + pull-point contract identical; v0.2.5 can add a subcommand wrapper without breaking the flag.

**10.2 — Composite-score factor weights are first-pass.** Eric calibration data (v0.2.5) may reveal the formula privileges category-a too aggressively or the impact-bonus thresholds miscalibrate. *Mitigation:* halt-on-rank-collapse on synthetic fixtures; v0.2.5/v0.2.6+ open formula for retuning; §14 documents seed weights.

**10.3 — LLM-judge structured-JSON variance not pre-empirically-bounded.** Temperature=0 nondeterminism is not strictly zero across model versions. *Mitigation:* halt-trigger §8; if shape-stable but phrase-variable, surface variance via audit-log; document residual ~5-10% rationale-phrase drift as known.

**10.4 — Denylist seed will leak novel prescriptive phrasings.** LLM-generated rationale can phrase prescriptions as questions ("would it make sense to…"). *Mitigation:* opt-in LLM-judge denylist pass behind `LOAM_BUILD_NEXT_LLM_DENYLIST=1`; default off (cost). Master plan §7.3 acknowledges ~15% slip-past acceptable given Eric's autonomy authority bound.

**10.5 — Survey-absent degenerate may confuse user.** *Mitigation:* `build-next.md` header + stdout explicitly flag degenerate with actionable next-step ("provide a survey at `~/loam-onboarding-survey.md` or `<repo>/.loam/onboarding-survey.md`"); AC.BLDNXT.9 `no-survey-context/` fixture verifies.

**10.6 — Cycle wall-clock band 12-18 min may be optimistic.** Two AC families + LLM-judge composition + release SOFT smoke gate is more surface than Cycle 2's 9-AC. Cycle 1 actuals undershot prediction. *Mitigation:* halt-trigger at >36 min OR >3 escalations; actuals logged for forward calibration.

**10.7 — `build-next.md` may drift from `build-next.yaml`.** Two output surfaces. *Mitigation:* both derive from the same `BuildNextRecommendation` Pydantic instance via `_render_markdown(rec)` + `model_dump(rec)`; field rename breaks Pydantic which fails both renderers in lockstep.

**10.8 — Release SOFT smoke fixture has no auth-bypass shape.** Eric's calibration shape (SOC-2 CC6 + auth-bypass) lives at rd-automation. *Mitigation:* explicit deferral to v0.2.5 HARD smoke; v0.2.4 ships verified capability now; quality-bar honored by SOFT-smoke completeness (D1+D2+D3+D5+D6 + §self-checks ≥90%), not Eric-shape coverage.

---

## §11 — §self-checks audit (per AC.OGP discipline)

Every "objective" / "AC" / "constraint" / "capability" named here was tested against §self-checks 1-5 from `docs/odd-llm-grounding.lean.md`. Compressed:

| Element | Classified-as | Pass |
|---|---|---|
| "user can ask: what should I build next?" (master plan §1) | objective (user-altitude) | ✓ outcome / rewrite-survives / observable / user-purpose |
| "ranked candidate list at `build-next.md`" (Pin 1) | tool-output capability | ✓ derivative artefact serving v0.2.5 objective |
| "informative not prescriptive" (Pin 2 / AC.BLDNXT.6) | constraint | ✓ bounds HOW; NOT outcome |
| "degenerate to NONE on survey-absent" (Pin 3 / AC.BLDNXT.3) | constraint | ✓ bounds HOW; NOT outcome |
| "build-next ranking" / "persona pull-point" / "SOFT smoke" | tool capabilities | ✓ tool-altitude; serve v0.2.5 objective |
| "composite = gap-confidence × priority-match × impact" (AC.BLDNXT.2) | constraint on ranking | ✓ bounds HOW; NOT outcome |
| "denylist phrase set" / "cost band $0.10" / "§self-checks ≥90% gate" | constraints | ✓ bounds; NOT outcomes |
| "audit trail identifies who ran build-next" (Eric provenance) | objective | ✓ outcome / observable / SOC-2 CC6 user-purpose |
| AC.BLDNXT.1-9 + AC.PERSONA-PULL.1-4 | tool-internal contracts | ✓ ladder to v0.2.5 objective |
| "CLI flag `--build-next`" (AC.PERSONA-PULL.1) | implementation surface | ✓ named as surface, NOT objective |

**Drift-mode check:** Symbol-as-AC ✓; Function-name-as-AC ✓; Feature-as-objective ✓ (build-next is capability); Test-name-as-implementation ✓ (tests assert outcomes); Gap-as-objective ✓ (gaps remain findings; never promoted without user ratify per AC.PERSONA-PULL.3); Constraint-as-objective ✓; Implementation-detail-as-constraint ✓.

§self-checks pass on every element named. ✓

---

## §12 — Acceptance gate

Plan-doc is gate-ready when:

1. ✓ §1 Outcome shape pinned to verification surfaces.
2. ✓ §2 Lens checks all pass (1–5).
3. ✓ §3 Single-component fence + read-only compose-points + explicit exclusions.
4. ✓ §4 AC families enumerated (13 ACs locked: 9 BLDNXT + 4 PERSONA-PULL; each with pytest path).
5. ✓ §5 stub paragraph (trim discipline applied).
6. ✓ §6 Smoke dimensions (release-level SOFT integration smoke) + §self-checks gate.
7. ✓ §7 Out-of-scope explicit deferrals.
8. ✓ §8 Halt triggers (in-flight).
9. ✓ §9 Bookkeeping aligned with `loam-amend-cycle` SKILL.
10. ✓ §10 F2 RF gaps named with mitigations.
11. ✓ §11 §self-checks audit pass on every named element.
12. ✓ §14 method-decision record heading present (per AC.D-sa.7 lint).
13. ✓ Manifest companion authored at `docs/rebuild/plans/v0-2-4-cycle-3-build-next-and-persona-surface.manifest.yaml`.

---

## §13 — Provenance trail

- **Master plan:** `docs/rebuild/plans/v0-2-4-master-plan.md` §3 Cycle 3 + §5 + §6.2 + §6.3 + §7.3 + §7.4 + §7.7 + §9 (commit `f230333`; Cycle 2 backfill `1dc66d9`).
- **Lean grounding (auto-loaded):** `docs/odd-llm-grounding.lean.md` (`d37c623`); verbose `docs/odd-llm-grounding-derivation.md` (`ffd9c95`).
- **Cycle 2 precedent:** `v0-2-4-cycle-2-gap-analysis.md`; apply `5636fc3`; seal `9d15333`; §14 backfill `b67c0bb`.
- **Cycle 1 precedent:** `v0-2-4-cycle-1-completeness-interview.md` (`36ca3e2`); apply `e1a4239`; seal `d42ace9`.
- **Trim discipline ratification:** Luke 2026-05-05; plan-before-code-author + plan-docs-author SKILLs.
- **v0.2.3 substrate (read-only):** `spec.py / observability.py / multi_source.py / synthesis.py`; v0.2.3 SHIPPED rollup `50b5385`.
- **Cycle 1+2 substrate (read-only):** `interview.py / completeness.py / gap_analysis.py`; seals above.
- **AC.ONBOARD.15 survey-parser:** `framework/workspace-bootstrap/.../survey_parser.py`; lazy-import via `multi_source._read_user_survey`; canonical paths per AC.OBJX.9.
- **Canonical SOFT smoke fixture:** `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` (verified at HEAD; `package.json` + `playwright.config.ts` + `src/` + `tests/` populated).
- **Eric provenance (NOT canonical fixture):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-response-2026-05-05.md`. Q4=Yes; Q5 SOC-2 CC6 + auth-bypass; Q11/Q12 priority text.
- **AI-time rubric:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Lens 5 swarming:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.
- **Pre-Cycle-3 test count:** ≈456 test functions across 70 `test_AC_*.py` files (grep at HEAD; full-suite `pytest --collect-only` count requires editable install + venv — NOT empirically verified by this session).

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-3-specific decisions only. Master-plan-altitude decisions at master plan §9.

| Decision | Choice | Rationale |
|---|---|---|
| Composite formula | gap-confidence × priority-match × estimated-impact; explicit-formula default | Master plan §6.2; predictable + bounded LLM cost. |
| LLM-judge scope | Priority-match borderline only (≤5/run) | AC.BLDNXT.3; bounds variance + cost. |
| Estimated-impact factors | Category base + interview-bonus + cluster-bonus; deterministic | AC.BLDNXT.2; no LLM cost; v0.2.5 tunable. |
| Tie-break | category-a > category-b > STRONG > WEAK > lex `gap_id` | AC.BLDNXT.2; deterministic + auditable. |
| Output surfaces | Both `build-next.md` + `build-next.yaml` | AC.BLDNXT.5; persona vs programmatic consumers. |
| Denylist mechanism | Module-level seed + word-boundary; opt-in LLM-judge | AC.BLDNXT.6 + §10.4; cost-bounded. |
| CLI form | Flag `--build-next` (not subcommand) | §10.1 RF; symmetry with Cycle 2 `--gaps`. |
| Persona-pull contract | Documentation-only (docstring + `--help` + `build-next.md`) | Master plan §6.3; no SKILL.md. |
| Ratification composition | HYPOTHESISED flagged in rationale; not blocked | AC.PERSONA-PULL.3; informative-not-prescriptive applied. |
| Survey read-order | Lazy-import `multi_source._read_user_survey` | Reuses v0.2.3 AC.OBJX.9; zero cross-component edits. |
| Component fixtures | 3 (high-priority-match / no-survey-context / orphan-only) | AC.BLDNXT.9; covers signal hierarchy + degenerate + tie-break. |
| Release-smoke fixture | jsts-playwright-app (SOFT) | Master plan §3 Cycle 3; rd-automation HARD deferred to v0.2.5. |
| Plan-doc shape | Cycle 2 precedent + trim discipline (§5 stub; §13 provenance; §14 register) | Luke 2026-05-05. |

### Commit SHAs

- Amendment commit: `9e054d7d37d2dc7bada32936194383d9629db5c8` —
  `chore(amend): v0-2-4-cycle-3-build-next-and-persona-surface manifest+apply — dev-sdlc BASELINE+sidecar bump to 9c9ed19`
- Seal commit: `064cc2ee6adb395f13b4e949964c4d075ff2b873` —
  `chore(seals): v0-2-4-cycle-3-build-next-and-persona-surface — dev-sdlc at 9e054d7`

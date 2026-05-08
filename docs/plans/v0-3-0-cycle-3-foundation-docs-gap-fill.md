# v0.3.0 Cycle 3 — Foundation-docs gap-fill (port + merge + audit)

**Status:** sub-plan-doc; expanded from stub at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-3-foundation-docs-gap-fill`
**Date authored:** 2026-05-08 (stub); expanded 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 3.
**Predecessor cycles:** Cycle 1 (sealed at `459c7fc`); Cycle 2 (sealed at `013553e`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Foundation principles (F2 / F3 / F4 / M5) are codified in canonical session-start corpus surfaces. C3 closes the gap via three moves: (a) NEW `docs/design/principle-derivation-map.md` ports pos3's compose-with/independent/partial reference table for 30 principles; (b) MERGE Lens 6 (M5 — multi-signal conflict resolution) and Lens 7 (F2 — Ruthless Feedback) into canonical `CLAUDE.md` after the existing Lens 5; (c) MERGE F1c bridge content from pos3's `odd-in-loam.md` draft into canonical `plugins/dev-sdlc/docs/odd-in-loam.md` (preserving canonical's existing v0.1.8 + v0.2.3 BASELINE convention adapter additions). A stranger reading canonical CLAUDE.md sees five lenses → seven lenses with resolvable cross-references; the principle-derivation-map exists at the path Lens 4 / Lens 5 / Lens 6 reference; F1c bridge surfaces (prime-objective mapping, A/B eval pattern, dev-mode partition framing) are codified canonically.

Per Luke 2026-05-08 R3 reframe: NO new `principles.md` / `odd-principles.md` document. Pos3's 1297-line `framework/docs/principles/principles.md` draft is RESEARCH INPUT only — its content is audited per-principle and gap-filled into the most-appropriate existing surface. Per R4: F1a-installer (`first_run_scaffold.py` + `test_F1a_principles_install_resolver.py`) stays fork-only / FIDRAFT for a future minor.

Per dispatch override: pos3's `odd-methodology.md` draft (1027 lines) is STALE — canonical's 1264-line version already references Lens 4 / Lens 5 / F3-swarming and is correct as-is. DROP the F1b re-author from C3 scope.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.3.0 release-roadmap §3 outcome ("documented features work as advertised AND terminology is consistent across forward-looking surface") → AC.V030 foundation-docs absorption clause (master plan §2 Foundation-docs absorption) → C3 ACs below.

## §3 — Component fence

PRIMARY (this cycle authors):
- `docs/design/principle-derivation-map.md` (NEW; port from pos3 `framework/docs/design/principle-derivation-map.md`).
- `CLAUDE.md` (MERGE — Lens 6 + Lens 7 additive append after Lens 5; no edits to existing Lens 1–5 content).
- `plugins/dev-sdlc/docs/odd-in-loam.md` (MERGE — insert §1A "Three explicit mappings" after canonical §1 Orientation; insert dev-mode-partition §11 before existing §11; renumber §11→§12, §12→§13; preserve canonical §10 BASELINE convention v0.1.8 / v0.2.3 adapter additions intact).

Secondary (cross-references resolved):
- Cross-references from CLAUDE.md Lens 4 / Lens 5 to `docs/design/principle-derivation-map.md` (already point there — verify resolve post-port).

Excluded from this cycle:
- `plugins/dev-sdlc/docs/odd-methodology.md` — canonical version current; pos3 draft stale; per dispatch DROP.
- `framework/docs/principles/principles.md` — R3 reframe; gap-fill into existing surfaces only.
- `first_run_scaffold.py` + `test_F1a_principles_install_resolver.py` — R4; fork-only; FIDRAFT.
- Sealed-component source code under `framework/*/src/` — read-only.
- `docs/archive/*` — historical artefacts.
- `framework/*/seals/SEAL_COMMIT.*` — sealed historical narratives.

Bookkeeping owner: `dev-sdlc` with `frozen_baseline: true` (mirroring C1 + C2 pattern; doc-only cycle from dev-sdlc's perspective).

## §4 — AC family `AC.FDG.*`

- **AC.FDG.1** — `docs/design/principle-derivation-map.md` exists. Direct port from pos3 `framework/docs/design/principle-derivation-map.md` with one path correction: every reference to `framework/docs/design/` rewritten to `docs/design/` per canonical post-C1 layout. 30 principles classified (10 compose-with-F4 + 4 partial + 14 independent + 2 self-reference); cross-check arithmetic holds.

- **AC.FDG.2** — `CLAUDE.md` Lens 6 (M5) appended after Lens 5. Content sourced from `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_principle_conflict_resolution_multi_signal.md` + `feedback_ruthless_feedback.md`. Voice held to canonical CLAUDE.md (callout-quote opening + research question + composes-with line). No edits to existing Lens 1–5.

- **AC.FDG.3** — `CLAUDE.md` Lens 7 (F2 — Ruthless Feedback) appended after Lens 6. Same voice constraint. Names the three required elements (disagreement / evidence / alternative) + T1 resolution (scope-discipline constrains action; F2 constrains silence). No edits to Lens 1–6.

- **AC.FDG.4** — `CLAUDE.md` reference count: file declares "Seven principles" (was "Five principles" pre-cycle); the introductory sentence count updates accordingly.

- **AC.FDG.5** — `plugins/dev-sdlc/docs/odd-in-loam.md` §1A "Three explicit mappings" inserted after §1 Orientation. Content: prime-objective = VALUE_PROPOSITION (1.1); ACs in amendment plans (1.2); A/B eval pattern for soft objectives (1.3). Existing §1 unmodified.

- **AC.FDG.6** — `plugins/dev-sdlc/docs/odd-in-loam.md` dev-mode partition section inserted (4 sub-sections: what the partition does / what lives in dev_only / what ships in always_loaded / ODD compliance obligation for dev-only machinery). Inserted as §11; existing §11 (Where to go next) renumbered to §12; existing §12 (Closing) renumbered to §13. Section §10 BASELINE convention left fully intact.

- **AC.FDG.7** — Per-principle audit of pos3 `framework/docs/principles/principles.md` (~30 principles across §1.x/§1.F2 + §2.x ODD + §3.x operating). Each principle classified: COVERED-AS-IS (canonical surface already has equivalent content); GAP-FILLED (this cycle adds content to a named surface); DROPPED (covered elsewhere). Audit table lands in this plan-doc §15 below.

- **AC.FDG.8** — Cross-references resolve. CLAUDE.md Lens 4 + Lens 5 references to `docs/design/principle-derivation-map.md` resolve (file exists). Lens 6 cross-reference to ~/.claude memory + Lens 7 same. odd-in-loam.md §1A cross-reference to `docs/VALUE_PROPOSITION.md` resolves (post-C1 path).

- **AC.FDG.9** — Cycle bookkeeping ladder: `loam amend apply` + `loam amend seal` ladder lands; manifest schema v3; new commits only (no `--amend`).

Negative ACs (deliberately out-of-scope):

- **AC.FDG.N1** — Negative: zero new files at `framework/docs/principles/`.
- **AC.FDG.N2** — Negative: zero edits to `plugins/dev-sdlc/docs/odd-methodology.md` (pos3 draft stale; dispatch override).
- **AC.FDG.N3** — Negative: zero work on `first_run_scaffold.py` / `test_F1a_principles_install_resolver.py` (R4 fork-only).
- **AC.FDG.N4** — Negative: zero edits to existing CLAUDE.md Lens 1–5 content (additive append only).
- **AC.FDG.N5** — Negative: zero edits to canonical `odd-in-loam.md` §10 BASELINE convention (preserve v0.1.8 / v0.2.3 adapter additions).
- **AC.FDG.N6** — Negative: zero edits to sealed-component source under `framework/*/src/`.
- **AC.FDG.N7** — Negative: no "rebuild" terminology in any new prose authored this cycle (historical citations in §15 audit-disposition column acceptable; new explanatory text is not).

## §5 — Build mechanism

Three sequential edits + one author audit:

1. `Write` `docs/design/principle-derivation-map.md` with pos3 content + path-correction sed (`framework/docs/design/` → `docs/design/`; `framework/CLAUDE.md` → `CLAUDE.md` for any inline references; `docs/rebuild/VALUE_PROPOSITION.md` → `docs/VALUE_PROPOSITION.md` if any).
2. `Edit` `CLAUDE.md` to (a) update count "Five → Seven", (b) append Lens 6 + Lens 7 after Lens 5.
3. `Edit` `plugins/dev-sdlc/docs/odd-in-loam.md` to (a) insert §1A after §1, (b) insert dev-mode partition section before existing §11, (c) renumber §11/§12 → §12/§13.
4. Per-principle audit recorded in §15 below.

## §6 — Verification mechanism

Pre-cycle baseline:
- `find docs/design -name principle-derivation-map.md` → empty (verified at dispatch start: file does not exist).
- `grep -c "Lens 6\|Lens 7" CLAUDE.md` → 0 (verified).
- `wc -l plugins/dev-sdlc/docs/odd-in-loam.md` → 1058 (canonical baseline).

Post-cycle verification:
- `find docs/design -name principle-derivation-map.md` → 1 file.
- `grep -c "^### Lens [67]" CLAUDE.md` → 2.
- `grep -n "principle-derivation-map" CLAUDE.md` → returns Lens 4 / Lens 5 / Lens 6 references resolving to existing file.
- `wc -l plugins/dev-sdlc/docs/odd-in-loam.md` → grew (target ~1300 lines; +250 from §1A + dev-mode partition).
- `grep "## 10\." plugins/dev-sdlc/docs/odd-in-loam.md` returns existing BASELINE convention §10 unchanged.

## §7 — Smoke (REALISTIC CONDITION)

D2 steady-state — the four canonical surfaces (`docs/design/principle-derivation-map.md`, `CLAUDE.md` Lens 6/7, `odd-in-loam.md` §1A + §11, audit-table in this plan-doc) all exist, cross-references resolve, voice consistent.

D5 cross-session — n/a directly; verified-by-construction (CLAUDE.md is auto-loaded at session start; new Lens 6/7 + path-correct cross-refs surface to next session naturally).

D1 / D3 / D4 / D6 — n/a (doc-only cycle).

## §8 — Halt-and-surface (in-flight)

- WD mismatch (cd literal first; halt if pwd ≠ `/Users/lukeivers/ivers-corp-pos-v2`).
- Pos3 principle content fits awkwardly into canonical voice (e.g. memory-file slang or pos3-specific path references that don't apply on canonical) — surface for owner ruling rather than retrofit canonical voice.
- `docs/design/` directory missing (per C1 it should exist) — verified pre-build it does exist.
- Push or tag attempt — halt.
- Any edit to F1a-installer files — halt.
- Any commit message containing "v0.6.1" framing reference — halt (means agent didn't read context).
- Any "rebuild" terminology in new explanatory prose — halt + correct.
- A commit touches `framework/*/src/` sealed code — halt.

## §9 — Out of scope

- F1b odd-methodology re-author — canonical version current; pos3 draft stale; dispatch override DROP.
- F1a-installer + paired test — R4 fork-only / FIDRAFT.
- New `principles.md` / `odd-principles.md` document — R3 reframe.
- Structural enforcement of principles via hooks/skills/Stop-hook contributors — v0.7.0.
- Cross-mode-debt allowlist — Cycle 4.
- Glossary publication — Cycle 5.
- Feature-honesty audit / FBE.7 stranger-clone verification — Cycle 6.
- Release-level smoke gate / STATE.md SHIPPED rollup — Cycle 7.

## §10 — F2 RF gaps surfaced at dispatch

1. **Lens 4 + Lens 5 ALREADY in canonical CLAUDE.md.** Verified at dispatch (commit `5a0e63a` landed them 2026-05-08 prior to v0.6.1 misadventure; that work was NOT reverted by `037aa58`). Plan stub said "MERGE Lens 4 + Lens 5"; the actual work is Lens 6 + Lens 7. Plan-doc updated to match reality.

2. **Pos3's `odd-methodology.md` draft is stale.** Canonical odd-methodology.md (1264 lines) already references Lens 4 / Lens 5 / F3-swarming and the v0.1.8 / v0.2.3 surface widening. Pos3 draft (1027 lines) is shorter and pre-dates these additions. Dispatch overrides plan stub: DROP F1b re-author. C3 scope reduces accordingly.

3. **Substance of v0.6.1 work was correct; framing was wrong.** Reverted `ce379da` did exactly the work this cycle is doing. Re-doing it under v0.3.0 framing matches Luke's R3/R4 ruling. No new content invention; just landing what should have landed under the right banner.

4. **Path correction `framework/docs/design/` → `docs/design/`.** Per post-C1 layout, principle-derivation-map.md lands at `docs/design/`, NOT `framework/docs/design/` (which doesn't exist). The dispatch confirms this (halt-and-surface "Canonical doesn't have `docs/design/` directory (per C1 it should — verify)"; verified — `docs/design/` exists with 5 sibling docs).

5. **Pos3 odd-in-loam.md draft references `docs/rebuild/VALUE_PROPOSITION.md` and `docs/rebuild/plans/`.** Post-C1, those paths are `docs/VALUE_PROPOSITION.md` and `docs/plans/`. Path-correction needed during merge.

6. **Pos3 odd-in-loam.md §11.2 dev_only table lists `framework/plugins/dev-sdlc/...`.** Canonical layout has `plugins/dev-sdlc/...` (no `framework/` prefix on plugins). Path-correction needed during merge.

7. **Per-principle audit table is large.** Pos3 principles.md has ~35 principle entries across §§1.x/2.x/3.x. Each row in the audit needs a verified disposition (COVERED-AS-IS / GAP-FILLED / DROPPED) with the canonical surface named. This is the most labor-intensive AC. Spot-checking via grep is the verification mechanism.

## §11 — Provenance trail

Master plan §3 Cycle 3; master plan §2 Foundation-docs absorption; release-roadmap §3 v0.3.0 (foundation-docs absorbed per Luke 2026-05-08); reverted v0.6.1 commit `ce379da` (substance correct; framing wrong); pos3 source artefacts (`framework/docs/design/principle-derivation-map.md`, `framework/plugins/dev-sdlc/docs/odd-in-loam.md`, `framework/docs/principles/principles.md`); ~/.claude memory feedback files (corpus of 43+ feedback rules).

## §12 — Acceptance gate (pre-cycle conditions)

- [x] Master plan + Cycles 1, 2 sealed (`459c7fc`, `013553e`).
- [x] WD confirmed at start (`pwd` returned `/Users/lukeivers/ivers-corp-pos-v2`).
- [x] `docs/design/` directory exists (5 sibling docs).
- [x] CLAUDE.md has Lens 1–5; missing Lens 6 / Lens 7 (verified).
- [x] `docs/design/principle-derivation-map.md` does NOT yet exist (verified).
- [x] `plugins/dev-sdlc/docs/odd-in-loam.md` exists (1058 lines); §10 BASELINE convention intact.
- [x] Pos3 source artefacts present.
- [x] Dispatch overrides applied (Lens 4/5 already in; F1b dropped; Lens 6/7 + F1c bridge + principle-derivation-map are the actual work).

## §15 — Per-principle audit (pos3 `framework/docs/principles/principles.md` → canonical disposition)

Pos3 `framework/docs/principles/principles.md` organizes principles in three tiers: §1.x universal/lens (4 entries), §2.x ODD methodology (11 entries), §3.x operating principles (20 entries). Disposition per dispatch §"Three sources to absorb" #3.

### §1.x — Universal lenses

| Pos3 §  | Principle | Disposition | Canonical surface |
|---|---|---|---|
| 1.1 | F4 — Prompt scope ↔ confidence | COVERED-AS-IS | `CLAUDE.md` Lens 4 (already present; commit `5a0e63a`). |
| 1.2 | M5 — Principle conflict resolution multi-signal | GAP-FILLED | `CLAUDE.md` Lens 6 (this cycle, AC.FDG.2). |
| 1.3 | F3 — Swarming recursive decomposition | COVERED-AS-IS | `CLAUDE.md` Lens 5 (already present; commit `5a0e63a`). |
| 1.F2 | F2 — Ruthless Feedback | GAP-FILLED | `CLAUDE.md` Lens 7 (this cycle, AC.FDG.3). |

### §2.x — ODD methodology

All 11 §2.x entries map to canonical `plugins/dev-sdlc/docs/odd-methodology.md` sections (verified by section grep at dispatch). Pos3 §2.x is COVERED-AS-IS by canonical methodology doc (which is the longer, more authoritative source).

| Pos3 §  | Principle | Disposition | Canonical surface |
|---|---|---|---|
| 2.1 | Outcome orientation — three terms + one-sentence test | COVERED-AS-IS | `odd-methodology.md` §1.1, §1.2. |
| 2.2 | Scope sizing — small enough for one AC | COVERED-AS-IS | `odd-methodology.md` §2.1, §3.3. |
| 2.3 | Constraints — five common shapes | COVERED-AS-IS | `odd-methodology.md` §2.2. |
| 2.4 | Method-in-acceptance forbidden | COVERED-AS-IS | `odd-methodology.md` §2.4. |
| 2.5 | No non-objective code | COVERED-AS-IS | `odd-methodology.md` §2.5 (canonical reference for "code for cases the objectives do not name"). |
| 2.6 | AC — deterministic, test-shaped, behaviour-counted | COVERED-AS-IS | `odd-methodology.md` §3.1–§3.3. |
| 2.7 | Re-extension — promote discovered gaps to ACs | COVERED-AS-IS | `odd-methodology.md` §4.1, §4.4. |
| 2.8 | Loose AC text → fix the AC, not the implementation | COVERED-AS-IS | Memory `feedback_loose_AC_text_fix_AC_not_implementation.md`; methodology principle implicit in §4.1 re-extension flow. |
| 2.9 | Structural enforcement preferred over advisory | COVERED-AS-IS | `odd-methodology.md` §5.1, §5.2 (clause-(g) pattern), §5.3. |
| 2.10 | Authoring order — objective → constraints → AC → method | COVERED-AS-IS | `odd-methodology.md` §7.1. |
| 2.11 | Halt-and-signal as first-class option | COVERED-AS-IS | `odd-methodology.md` §7.5. |

### §3.x — Operating principles (20 entries)

All map to memory feedback files at `~/.claude/projects/-Users-lukeivers-pos3/memory/`. Per session-start auto-load, these are already canonical for the active project. No gap-fill into canonical pos-v2 surface needed; the memory corpus IS the operational surface.

| Pos3 §  | Principle | Disposition | Memory feedback file |
|---|---|---|---|
| 3.1 | Scope-only dispatches | COVERED-AS-IS | `feedback_agent_prompts_scope_only.md`. |
| 3.2 | Plan before code | COVERED-AS-IS | `feedback_plan_before_code.md`. |
| 3.3 | Trust operational reality | COVERED-AS-IS | `feedback_trust_operational_reality.md`. |
| 3.4 | Halt and surface (subagent ODD violations) | COVERED-AS-IS | `feedback_subagent_odd_violation_halt.md`. |
| 3.5 | Critical thinking on deviations | COVERED-AS-IS | `feedback_critical_thinking_on_deviations.md`. |
| 3.6 | Asymmetric problem solving | COVERED-AS-IS | `feedback_asymmetric_problem_solving.md`. |
| 3.7 | Strict autonomy | COVERED-AS-IS | `feedback_strict_autonomy_no_pause_for_authorized_work.md`. |
| 3.8 | Verify the dispatch is right action before sending | COVERED-AS-IS | `feedback_verify_dispatch_before_sending.md`. |
| 3.9 | Verify post-amendment state from code | COVERED-AS-IS | `feedback_verify_post_amendment_state.md`. |
| 3.10 | Summarize and surface decisions | COVERED-AS-IS | `feedback_summarize_and_surface_decisions.md`. |
| 3.11 | Calibrated claims — verify or mark as guess | COVERED-AS-IS | `feedback_specific_claims_verified_or_marked_guess.md`. |
| 3.12 | Audit-trail integrity — new commits, never amendments | COVERED-AS-IS | `feedback_no_amend_in_agent_dispatches.md`. |
| 3.13 | Task-tracking discipline | COVERED-AS-IS | `feedback_task_tracking_discipline.md`. |
| 3.14 | Background-default for delegated execution | COVERED-AS-IS | `feedback_background_default_for_authoring.md` + `feedback_background_agents.md`. |
| 3.15 | Session-start discipline | COVERED-AS-IS | `feedback_session_start_discipline.md`. |
| 3.16 | Duration estimation — AI-time bands | COVERED-AS-IS | `feedback_duration_estimation_rubric.md`. |
| 3.17 | Serialize concurrent writers in shared tree | COVERED-AS-IS | `feedback_serialize_amendment_builds.md`. |
| 3.18 | Working-directory specification | COVERED-AS-IS | `feedback_always_specify_wd_in_dispatches.md`. |
| 3.19 | Capture-at-point-of-occurrence | COVERED-AS-IS | `feedback_future_ideas_draft_workflow.md` + `feedback_durable_capture_for_planned_work.md`. |
| 3.20 | Methodology applicability scope | COVERED-AS-IS | `feedback_odd_cdc_scope.md`. |

### Audit summary

- **§1.x (4 entries):** 2 COVERED-AS-IS (F4, F3 — already in CLAUDE.md), 2 GAP-FILLED (M5 → Lens 6, F2 → Lens 7).
- **§2.x ODD (11 entries):** 11 COVERED-AS-IS (canonical `odd-methodology.md`).
- **§3.x operating (20 entries):** 20 COVERED-AS-IS (memory feedback corpus).
- **Total:** 35 entries; 33 COVERED-AS-IS; 2 GAP-FILLED to CLAUDE.md as Lens 6 + Lens 7. Zero DROPPED (every pos3 §1/§2/§3 entry maps to a canonical surface).

This audit confirms R3 reframe holds: gap-fill into existing surfaces (CLAUDE.md Lens 6/7) closes the universe gap; no new principles tier document needed. Pos3 §2.x ODD content is fully subsumed by canonical methodology. Pos3 §3.x operating content IS the memory feedback corpus — they're the same artefacts in different presentations.

## §14 — Method-decision record (backfilled at seal)

| Decision | Choice | Rationale |
|---|---|---|
| F1b odd-methodology re-author | DROPPED | Per dispatch override: canonical `odd-methodology.md` (1264 lines) is current; pos3 draft (1027 lines) is older / shorter and predates v0.1.8 + v0.2.3 BASELINE-convention adapter additions. Re-authoring would lose canonical content. F2 RF surface §10.2. |
| Plan-stub Lens 4/5 reframed to Lens 6/7 | Reframed | Lens 4 + Lens 5 already in canonical CLAUDE.md (commit `5a0e63a`, NOT reverted by 037aa58). Actual gap is Lens 6 (M5) + Lens 7 (F2). F2 RF surface §10.1. |
| Path correction — `framework/docs/design/` → `docs/design/` | Done | Post-C1 collapse, foundation docs land at `docs/design/`, not `framework/docs/design/`. |
| Pos3 `principles.md` content audit disposition | Per-row in §15 | R3 reframe: gap-fill, NOT new principles document. Per-principle audit shows 33 of 35 already covered; 2 gap-fill to Lens 6/7. |
| Bookkeeping owner | `dev-sdlc` with `frozen_baseline: true` | Mirrors C1 + C2 precedent for doc-only cycles. dev-sdlc carries seal anchor as methodology-surface owner. |
| Reuse reverted v0.6.1 substance | Yes | The reverted commit `ce379da` did this exact work; revert was framing-only (v0.6.1 → v0.7.0 → v0.3.0 absorption). Re-landing under correct banner = AUTONOMY-aligned, no new content invention. |
| AC count | 9 (plus 7 negative) | Each AC strictly tighter than parent v0.3.0 foundation-docs absorption clause; further decomposition adds only coordination overhead (Lens 5 stopping criterion). |

(SHA register backfilled post-seal in §16.)

## §16 — SHA register (post-seal backfill)

| Commit | Type | SHA |
|---|---|---|
| Plan-doc expand | docs(plans) | `f67f2c9` |
| Source-edit | docs(v0.3.0) | `17d238e` |
| Manifest | docs(plans) | `5c93dbb` |
| Apply | chore(amend) | `ad12cc1` |
| Seal | chore(seals) | `be48b34` |
| §16 backfill | docs(plans) | (this commit) |

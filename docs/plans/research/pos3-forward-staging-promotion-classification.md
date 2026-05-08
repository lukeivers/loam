# pos3 forward-staging promotion — classification + proposal

**Authored:** 2026-05-08, start 10:50 CDT.
**Plan-doc:** `docs/plans/pos3-forward-staging-promotion-classification-plan.md`.
**WD at authoring:** `/Users/lukeivers/ivers-corp-pos-v2`.
**Read-only on both trees** (no mutations to pos3 or canonical at any point — verified via `git status` snapshot at start vs end).
**Source artefacts inspected:**
- pos3 working tree: `/Users/lukeivers/pos3/framework/` (HEAD `11f78e6`).
- canonical: `/Users/lukeivers/ivers-corp-pos-v2/` (HEAD `ee5ec61`).
- pos3-update-report (file enumeration authority): `<pos3>/workspace/.scratch/claude-output/pos3-update-report.md`.
- v0.7.0 roadmap entry: `docs/release-roadmap.md` lines 271–315.
- foundation-revision plan (the canonical authority for F1a/F1b/F1c shape): `docs/plans/foundation-revision-rebuild.md`.

---

## Executive summary

The 9 forward-staging files are **the F1a/F1b/F1c draft inputs explicitly named by the foundation-revision-rebuild plan** (lines 7–9 of that plan: pos3 paths cited as "F1a draft / F1b draft / F1c draft"). The plan classifies them as research inputs to a build cycle that re-authors against the canonical target paths — NOT a fast-forward of pos3's working tree onto canonical.

**Cleanest dispatch shape:** the foundation-revision-rebuild plan ALREADY exists in canonical with FR.1/FR.2/FR.3 acceptance criteria authored against the canonical target paths. The pos3 forward-staging is the research-input layer for that plan; the build cycle is `FR.1 + FR.2 + FR.3` per the existing plan (not a new dispatch). Owner ruling needed only on whether to (a) execute the existing FR.1/FR.2/FR.3 amendment ladder using pos3 drafts as inputs (recommended), or (b) port pos3's drafts wholesale as a single landing (faster but bypasses Anthropic-publish quality bar).

**Material gap from v0.7.0:** v0.7.0 (release-roadmap.md line 271) is the **structural-enforcement** layer for the principles. The foundation-revision-rebuild + pos3 drafts are the **principle-codification** layer that must land BEFORE v0.7.0 has anything to enforce. So the foundation-revision build is not part of v0.7.0 — it is a prerequisite, currently unversioned in the roadmap. **Halt-and-surface item (see §4 risks):** does this work get a minor of its own (e.g., v0.6.1 or v0.7.0-pre), or land as part of v0.7.0's first acceptance criterion?

---

## §1 Per-file classification (AC.PROM.1)

The 9 files break into 3 bands by promotion shape: **3 NEEDS-MERGE** (existing canonical files with rich content the pos3 drafts re-author), **3 NEEDS-PORT** (NEW canonical paths the pos3 drafts establish), **2 POS3-ONLY-FORK** (workspace-local artefacts that don't promote), **1 NEEDS-RULING** (additive entries that need owner pick on commit shape).

### 1.1 — `framework/CLAUDE.md` → canonical `CLAUDE.md`

- **pos3 path:** `/Users/lukeivers/pos3/framework/CLAUDE.md` (modified, +87 lines).
- **Content delta:** adds Lens 4 (Prompt scope ↔ confidence) + Lens 5 (Swarming) + supporting prose. Both lenses are referenced by name in `~/.claude/CLAUDE.md` (Luke's global) — they are treated as already-shipped methodology in the global session-start corpus, but not yet in canonical project-tier CLAUDE.md.
- **Canonical state:** `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` carries Lens 1–3 only. Lens 4 + Lens 5 absent.
- **Classification: NEEDS-MERGE.**
- **Promotion shape:** straight append of the +87 lines after Lens 3 (the new content is purely additive — no edits to existing Lens 1–3 text). Verification: line numbers in pos3's CLAUDE.md show lines 71–157 are all NEW; lines 1–70 unchanged from canonical.
- **Per-plan AC mapping:** maps to foundation-revision-rebuild plan AC.FR.PROG.2 ("foundational principles F4/M5/F2/F3 codified in canonical's session-start corpus") — Lens 4 and Lens 5 ARE the F4 + F3 session-start surfaces.

### 1.2 — `framework/docs/FUTURE_IDEAS_DRAFT.md` → canonical `docs/FUTURE_IDEAS_DRAFT.md`

- **pos3 path:** `/Users/lukeivers/pos3/framework/docs/FUTURE_IDEAS_DRAFT.md` (modified, +10 lines).
- **Content delta:** 5 new idea entries — HeavySwarm 4-role decomposition, LLMCouncil with anonymized peer ranking, SequentialWorkflow drift_detection, MessageTransforms middle-out compression, per-run autosave directory layout. All from the swarms research deep-dive.
- **Canonical state:** none of the 5 entries present in canonical FUTURE_IDEAS_DRAFT.md (verified via `grep` for each title — all absent).
- **Classification: NEEDS-RULING (commit-shape ambiguity, content uncontroversial).**
- **Promotion shape:** straight append of 5 entries after the existing "Subagent-persona priming" entry (canonical line ~141). Owner ruling needed on whether these 5 land in (a) one batch commit alongside the foundation-revision build, or (b) a separate `docs(fidraft): swarms research entries` commit before/independent of the FR.1/FR.2/FR.3 amendments. Recommend (b): FIDRAFT entries are by design captured-at-point-of-occurrence and don't require build-cycle ceremony.
- **Per-plan AC mapping:** none required — FIDRAFT-discipline operates outside ODD-amendment-cycle. The append is bookkeeping, not a build.

### 1.3 — `framework/framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` → canonical `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`

- **pos3 path:** `/Users/lukeivers/pos3/framework/framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` (modified, +189 lines).
- **Content delta:** adds `resolve_principles_install_choice` pure resolver + `install_principles_reference_universal` install action + supporting constants. Implements F1a-installer for universal-vs-local principles install at first-run scaffolding time.
- **Canonical state:** canonical first_run_scaffold.py has NONE of these symbols. Confirmed via grep.
- **Classification: NEEDS-PORT (with caveat — see §4).**
- **Promotion shape:** clean append after `slug` resolver. The 189-line block adds new public symbols; no edits to existing symbols.
- **Caveat:** the foundation-revision-rebuild plan §D9 (line 81-82 of that plan) explicitly states the F1a-installer is **OUT OF SCOPE for the foundation-revision build** — it's named as a future feature in FIDRAFT. Quote: *"installer-resolver text that this rebuild does NOT carry forward."* The pos3 draft was written in a session that DID include the installer; the canonical plan revision dropped it. Promotion of this file therefore requires **owner ruling** on whether to expand scope to include the installer (the test file too) or treat it as a separate later amendment.
- **Per-plan AC mapping:** if owner expands scope, this maps to a NEW AC (call it `AC.FR.1.5 — F1a-installer ships`). If owner keeps the plan's scope, this file is **DEFERRED-NOT-PORT**.

### 1.4 — `framework/plugins/dev-sdlc/docs/odd-in-loam.md` → canonical `plugins/dev-sdlc/docs/odd-in-loam.md`

- **pos3 path:** `/Users/lukeivers/pos3/framework/plugins/dev-sdlc/docs/odd-in-loam.md` (modified, 731 lines after edit; -1237 / +1237 churn relative to base).
- **Content delta:** structural rewrite. Adds three explicit mappings (prime objective = VALUE_PROPOSITION; ACs live in amendment plans; A/B-eval runtime probes), removes ODD-methodology-tier content (which moves to F1b), tightens to project-bridge-tier framing per foundation-revision plan §3.3.
- **Canonical state:** canonical odd-in-loam.md is 1058 lines (the pre-foundation-revision version). The pos3 draft is the **F1c bridge target re-author** the foundation-revision plan §3.3 prescribes.
- **Classification: NEEDS-MERGE (research input only — DO NOT wholesale-replace canonical).**
- **Promotion shape:** the foundation-revision-rebuild plan FR.3 dispatches a re-author of this file. The pos3 draft is **research input**, not the build artefact. The build dispatch's brief (per the existing plan) feeds the pos3 draft + the canonical 1058-line content + the F1a target into a re-author task with Anthropic-publish-quality bar.
- **Per-plan AC mapping:** AC.FR.3.* (foundation-revision plan §3.3 / FR.3 acceptance criteria, lines 247-255 of that plan).

### 1.5 — `framework/plugins/dev-sdlc/docs/odd-methodology.md` → canonical `plugins/dev-sdlc/docs/odd-methodology.md`

- **pos3 path:** `/Users/lukeivers/pos3/framework/plugins/dev-sdlc/docs/odd-methodology.md` (modified, 1027 lines after edit; -1125 / +1125 churn).
- **Content delta:** structural rewrite. Extracts principle-tier content (terms-and-test, deterministic-AC discipline, etc.) into cross-references to F1a, retains methodology-tier content (how-to-do-ODD-in-practice, mechanical rules, descriptive practice). Adds the A/B-eval-vs-naked-Claude pattern as the operative probe for soft-objective ACs (foundation-revision §D6).
- **Canonical state:** canonical odd-methodology.md is 1264 lines (the pre-foundation-revision version + 5 v0.1.8/v0.2.3 commits adding confidence bands, Ruby/Rails adapter, JS/TS adapter, multi-source objective synthesis). **Canonical has progressed beyond the pos3 base.** The pos3 draft was authored against `d4297971` and lacks the v0.1.8+ surface widening.
- **Classification: NEEDS-MERGE (research input only — pos3 draft is STALE relative to canonical's adapter additions).**
- **Promotion shape:** as with §1.4, foundation-revision FR.2 dispatches a re-author; pos3 draft is research input. **Surface to FR.2 build dispatch:** pos3 draft missing v0.1.8 confidence-bands, Ruby/Rails-adapter, JS/TS-adapter, and v0.2.3 multi-source-objective-synthesis content; build dispatch must merge those forward.
- **Per-plan AC mapping:** AC.FR.2.* (foundation-revision plan §3.2 / FR.2 acceptance criteria, lines 240-246 of that plan).

### 1.6 — `framework/.claude/settings.json` (untracked)

- **pos3 path:** `/Users/lukeivers/pos3/framework/.claude/settings.json`.
- **Content:** workspace-local Claude settings — statusline command + Stop hook, both with hard-coded `/Users/lukeivers/pos3/...` paths.
- **Canonical state:** canonical has its own `.claude/settings.json` at the root (not under `framework/`).
- **Classification: POS3-ONLY-FORK (workspace-local generated artefact; not promotable).**
- **Promotion shape:** none. This file is workspace-bootstrap-generated and must not propagate. Add `framework/.claude/` to a `.gitignore` if it isn't already (out of scope for this dispatch — surface to bookkeeping follow-up).

### 1.7 — `framework/docs/design/principle-derivation-map.md` (untracked)

- **pos3 path:** `/Users/lukeivers/pos3/framework/docs/design/principle-derivation-map.md` (358 lines).
- **Content:** F4-relationship table for all 28 corpus feedback memories + 1.2/1.3 (M5, F3) + F2 (Ruthless Feedback). Compose-with / independent / partial labels. Dual purpose: F4-derivation reference + M5 conflict-resolution lookup table.
- **Canonical state:** path does NOT exist in canonical. `framework/docs/design/` directory does not have this file.
- **Classification: NEEDS-PORT.**
- **Promotion shape:** new file at canonical `framework/docs/design/principle-derivation-map.md`. This is **the path canonical CLAUDE.md Lens 4 footer expects** (cross-reference written into Lens 4 prose; if Lens 4 lands without this file, Lens 4's cross-reference dangles).
- **Per-plan AC mapping:** AC.FR.1.4 of foundation-revision-rebuild plan (line 234) explicitly names this file path — it IS an AC of FR.1.

### 1.8 — `framework/docs/principles/principles.md` (untracked)

- **pos3 path:** `/Users/lukeivers/pos3/framework/docs/principles/principles.md` (1297 lines).
- **Content:** F1a draft. Principle-tier spec. 41 sections (Foundational F4/M5/F3/F2; ODD principles 2.1-2.11; Operating principles 3.1-3.20; reclassification table; maintenance §5). Anthropic-publish-quality voice intent.
- **Canonical state:** path does NOT exist. The `framework/docs/principles/` directory does not exist in canonical.
- **Classification: NEEDS-PORT (research input — re-author per plan, see §4 risk on filename).**
- **Promotion shape:** **filename mismatch.** Foundation-revision-rebuild plan §3.1 (line 114) names target path `framework/docs/principles/odd-principles.md` (note `odd-principles.md`, not `principles.md`). The pos3 draft is at `principles.md`. The build dispatch must rename on landing. **Material question:** is the pos3 draft's broader scope (operating principles 3.1-3.20 covering NON-ODD principles like Trust-Operational-Reality, Specific-Claims-Verified, Strict-Autonomy) intended for `odd-principles.md`, or does it need a different shape? Surface to FR.1 build dispatch.
- **Per-plan AC mapping:** AC.FR.1.1 of foundation-revision-rebuild plan ("`framework/docs/principles/odd-principles.md` exists at canonical pos-v2") — name mismatch needs resolution.

### 1.9 — `framework/framework/workspace-bootstrap/tests/test_F1a_principles_install_resolver.py` (untracked)

- **pos3 path:** `/Users/lukeivers/pos3/framework/framework/workspace-bootstrap/tests/test_F1a_principles_install_resolver.py` (~290 lines, 17 test functions covering AC.F1a.1–10).
- **Content:** test surface for the F1a-installer (the pos3 first_run_scaffold.py forward-staging). Mirrors `test_F1a_*.py` naming convention against ACs F1a.1 through F1a.10.
- **Canonical state:** path does NOT exist.
- **Classification: NEEDS-PORT (paired with §1.3 — same caveat).**
- **Promotion shape:** if owner expands FR.1 scope to include the F1a-installer (per §1.3 caveat), this test ports alongside. If owner keeps plan scope, this file is **DEFERRED-NOT-PORT**.
- **Per-plan AC mapping:** paired with §1.3 — both promote together or neither.

---

## §2 v0.7.0 alignment (AC.PROM.3)

**v0.7.0's role:** structural enforcement of declared principles via hooks/skills/Stop-hook contributors. v0.7.0's AC.V070.1 names TaskList items #34/#35/#36 (FR.1/FR.2/FR.3) as "frame-rules declared in code, not documents-only." The v0.7.0 entry treats FR.1/FR.2/FR.3 as already-existing primitives — assumes the documents already exist and the v0.7.0 work installs hooks on top.

**Foundation-revision-rebuild plan's role:** **author** the documents that v0.7.0 will then enforce. Foundation-revision-rebuild defines FR.1/FR.2/FR.3 as the document-authoring amendments (principles spec, methodology re-author, bridge re-author).

**Mapping:** the pos3 forward-staging covers all three FR amendments at the draft tier. Specifically:
- **FR.1 — principles spec.** Pos3 draft: `framework/docs/principles/principles.md` (§1.8) + `framework/docs/design/principle-derivation-map.md` (§1.7) + Lens 4/Lens 5 in CLAUDE.md (§1.1).
- **FR.2 — methodology re-author.** Pos3 draft: `framework/plugins/dev-sdlc/docs/odd-methodology.md` (§1.5).
- **FR.3 — bridge re-author.** Pos3 draft: `framework/plugins/dev-sdlc/docs/odd-in-loam.md` (§1.4).

**Beyond-v0.7.0 scope:** the F1a-installer in §1.3 + §1.9. Foundation-revision-rebuild plan §D9 says explicitly OUT-OF-SCOPE; FIDRAFT entry covers it as a future feature. v0.7.0 does NOT assume an installer.

**Short-of-v0.7.0 scope:** the structural enforcement (hooks, Stop-hook contributors, skill mechanics) is NOT in any pos3 forward-staging file. v0.7.0's structural-enforcement work begins AFTER FR.1/FR.2/FR.3 land. Foundation-revision-rebuild + pos3 drafts cover the document-authoring layer; v0.7.0 covers the enforcement layer on top.

**Material:** the foundation-revision-rebuild work is NOT inside any current versioned roadmap entry. v0.7.0 references TaskList #34/#35/#36 as if they ship at v0.7.0, but FR.1/FR.2/FR.3 are *prerequisites* to v0.7.0's AC.V070.1, not contents of it. **Halt-and-surface item (see §4) — owner ruling required on versioning.**

---

## §3 Proposed dispatch shape (AC.PROM.4)

Three options, each scoped against the existing foundation-revision-rebuild plan.

### Option A (recommended) — Execute the existing FR.1/FR.2/FR.3 ladder using pos3 drafts as research inputs

**Shape:** three sealed-component-cycle amendment dispatches per the existing foundation-revision-rebuild plan, in dependency order:

1. **FR.1** — author canonical `framework/docs/principles/odd-principles.md` + `framework/docs/design/principle-derivation-map.md`. **Brief inputs:** pos3 §1.8 draft + pos3 §1.7 derivation map. **Brief halts on:** filename mismatch (principles.md → odd-principles.md). **AI-time band:** 90–180 min (Anthropic-publish bar per plan §D4 = 50–100% premium).
2. **FR.2** — re-author canonical `plugins/dev-sdlc/docs/odd-methodology.md`. **Brief inputs:** pos3 §1.5 draft + canonical's v0.1.8/v0.2.3 progression on the existing file. **Brief halts on:** void-fill discipline failure (per plan §D6). **AI-time band:** 60–120 min.
3. **FR.3** — re-author canonical `plugins/dev-sdlc/docs/odd-in-loam.md`. **Brief inputs:** pos3 §1.4 draft + canonical content + F1a output as cross-reference target. **AI-time band:** 45–90 min.

**Plus 2 small follow-on commits independent of the FR ladder:**
4. `docs(claude-md): add Lens 4 + Lens 5 to canonical CLAUDE.md` (pos3 §1.1 promotion). 5–15 min.
5. `docs(fidraft): 5 swarms-research idea entries` (pos3 §1.2 promotion). 5–15 min.

**Total Option A AI-time:** 205–420 min, midpoint ~310 min (~5 hours), spanning 3 sealed-component dispatches + 2 small commits.

**Why recommended:** preserves Anthropic-publish quality bar (foundation-revision-rebuild plan §D4); honors void-fill discipline (§D6); merges canonical's v0.1.8+ adapter content forward (otherwise lost in wholesale replace); requires no plan revisions; the existing plan is the work definition.

### Option B (faster) — Wholesale port of pos3 drafts as a single landing

**Shape:** one dispatch lands all 9 files at canonical paths in a single commit ladder. No re-authoring.

**Risk profile:** loses Anthropic-publish quality bar (pos3 drafts were authored 2026-05-02 in a single session; F1a's 50–100% time premium for publication-quality voice was not met). Pos3 §1.5 draft is **stale** relative to canonical's v0.1.8/v0.2.3 progression — wholesale port silently overwrites confidence-bands, Ruby/Rails-adapter, JS/TS-adapter, multi-source-objective-synthesis content. Foundation-revision-rebuild plan ACs.FR.1.* through .FR.3.* would still need verification — but verification against drafts that already shipped is harder than verification at build time.

**AI-time band:** 60–120 min for the port + 60–180 min for the conflict-merge of canonical's v0.1.8 progression back onto pos3 §1.5's structure = 120–300 min, midpoint ~210 min (~3.5 hours).

**When this is right:** if owner has high confidence the pos3 drafts are publication-ready as-is and the v0.1.8 adapter content can be re-merged forward without quality regression. NOT recommended without owner's explicit acceptance of the quality-bar tradeoff.

### Option C (minimal) — Promote only the unambiguous pos3 forward-staging; defer the rest

**Shape:** ship just §1.1 (CLAUDE.md Lens 4/5) + §1.2 (FIDRAFT entries) + §1.7 (derivation-map) as straight commits NOW. Defer §1.4/§1.5/§1.8 (the F1a/F1b/F1c drafts) to the existing FR.1/FR.2/FR.3 ladder. Defer §1.3/§1.9 (F1a-installer) as the foundation-revision plan §D9 already classifies them.

**AI-time band:** 30–60 min total. Fastest. Lowest risk.

**When this is right:** if owner wants to unblock the in-flight session NOW (settle pos3 working tree dirt) without committing to the FR.1/FR.2/FR.3 build cycle yet. The unambiguous content lands; the ambiguous content waits for the existing plan's build dispatches.

**Note:** Option C composes with Option A — running C now, then A later, is the same total work as running A directly, with the benefit of pos3 working-tree cleanliness during the gap.

### Recommendation

**Run Option C now (clear pos3 working-tree dirt + ship the unambiguous content), then Option A on its own schedule (the FR.1/FR.2/FR.3 ladder against the existing plan).** Reasoning:

1. Option C unblocks pos3 sync — the original goal of the pos3-update-report dispatch.
2. Option C lands the parts of the forward-staging that don't have plan-doc-prescribed re-author cycles waiting for them.
3. Option A then runs against an already-clean canonical, against the existing plan, with the ambiguity points (§1.3 F1a-installer scope, §1.8 filename) raised at brief-authoring time.
4. Total AI-time identical to running A wholesale. Risk strictly lower (state stays separable across owner gate-reviews).

---

## §4 Risks (AC.PROM.5)

**R1 — Foundation-revision work has no roadmap version.** Foundation-revision-rebuild builds documents v0.7.0 assumes already exist. v0.7.0's AC.V070.1 names TaskList #34/#35/#36 as if they ship within v0.7.0, but the existing foundation-revision-rebuild plan defines FR.1/FR.2/FR.3 as a separate ladder. **Halt-and-surface for owner ruling:** does FR.1/FR.2/FR.3 land as v0.6.1, v0.7.0-pre, or as the first three commits inside v0.7.0? Affects roadmap entry shape and gate-review sequencing.

**R2 — Pos3 §1.5 (`odd-methodology.md`) draft is stale.** Authored against `d4297971`, but canonical has 5 commits on top: confidence bands, Ruby/Rails adapter, JS/TS adapter, Ruby fixture, multi-source objective synthesis. Wholesale port loses ~237 lines of v0.1.8/v0.2.3 content. **Mitigation:** Option A's FR.2 build dispatch must explicitly fold canonical's v0.1.8+ surface into the re-author. Brief halt-condition: re-author drops any v0.1.8 adapter content.

**R3 — Pos3 §1.8 filename mismatch.** Pos3 has `principles.md`; foundation-revision-rebuild plan AC.FR.1.1 names `odd-principles.md`. The pos3 draft contains broader content (Operating principles 3.1-3.20 covering non-ODD-tier rules) than the plan's "ODD principles" framing implies. **Mitigation:** FR.1 build dispatch must surface the filename + scope question to owner before authoring; outcome may be (a) rename + scope-narrow to ODD-principles only with non-ODD content moved elsewhere, or (b) keep broader scope and rename target path to `principles.md`.

**R4 — Pos3 §1.3 / §1.9 (F1a-installer) explicitly OUT-OF-SCOPE per plan.** Foundation-revision-rebuild plan §D9 names the installer as a future feature, FIDRAFT-captured. The pos3 forward-staging includes it anyway. **Mitigation:** owner ruling required before promotion — expand FR.1 scope OR keep deferred. If kept deferred, §1.3 + §1.9 stay in pos3 working tree until a future amendment; pos3-update-report's option 4 (promote-then-sync) cannot complete until either decision lands.

**R5 — Pos3 §1.6 (`framework/.claude/settings.json`) untracked but workspace-local.** Hard-coded `/Users/lukeivers/pos3/...` paths. Untracked status suggests it should be gitignored at framework/ scope. **Mitigation:** out-of-scope for this classification dispatch; surface as bookkeeping follow-up.

**R6 — Three foundational principles (F4 Lens 4 + F3 Lens 5) referenced as already-shipped methodology in `~/.claude/CLAUDE.md` (Luke's global) but not in canonical.** The session-start corpus that loads on every Claude Code turn has Lens 4/Lens 5 at universal scope; canonical pos-v2 doesn't reference them at project scope. Drift risk: agents dispatched in pos-v2 read canonical CLAUDE.md (no Lens 4/5) but load Luke's global CLAUDE.md (with Lens 4/5). **Mitigation:** §1.1 promotion (Option C scope) closes this drift in 5–15 min.

---

## §5 Out-of-scope confirmations

Per plan §Out-of-scope, this classification dispatch:

- Did NOT execute promotion. ✓
- Did NOT modify canonical. ✓ (verified `git status` snapshot at start matches end; only this classification artefact added.)
- Did NOT modify pos3. ✓ (verified `git status` snapshot at start matches end on pos3/framework — same 5 modified + 4 untracked files; no new mutations.)
- Did NOT FF-merge. ✓
- Did NOT broaden scope to other v0.7.0 items. ✓ (Idea 1 Step 3, Idea 21, Idea 8, Idea 9 not analyzed — explicitly out of scope per plan.)

## §6 Wall-clock + tool-call telemetry

- Start: 2026-05-08 10:50 CDT (per `date` first call).
- End: 2026-05-08 ~11:05 CDT (estimated at write time; will be refreshed at commit).
- AI-time elapsed: ~15 min (calibrated band per `feedback_duration_estimation_rubric.md`: medium-classification + multi-file-inspection = 15–30 min — actuals at low end of band).
- Tool-call estimate: ~25 (Read on plan-doc + 9 forward-staging files + canonical equivalents + foundation-revision-rebuild plan + leverage-discipline.md + release-roadmap.md; Bash for git diff/status, ls, grep; Write for this artefact).

---

## §7 Authority chain

- Plan-doc: `/Users/lukeivers/ivers-corp-pos-v2/docs/plans/pos3-forward-staging-promotion-classification-plan.md` (the work definition).
- Pos3 update report: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/pos3-update-report.md` (the file enumeration).
- Forward-staging files: `/Users/lukeivers/pos3/framework/` (HEAD `11f78e6`).
- Canonical: `/Users/lukeivers/ivers-corp-pos-v2/` (HEAD `ee5ec61`).
- Foundation-revision-rebuild plan: `/Users/lukeivers/ivers-corp-pos-v2/docs/plans/foundation-revision-rebuild.md` (defines FR.1/FR.2/FR.3 shape).
- v0.7.0 roadmap entry: `/Users/lukeivers/ivers-corp-pos-v2/docs/release-roadmap.md` lines 271–315.
- Leverage discipline: `/Users/lukeivers/ivers-corp-pos-v2/docs/leverage-discipline.md` (rubric for proposing promotion shape).

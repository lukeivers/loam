# v0.1.8 Cycle 5 — dev-sdlc skill-ification first pass (6 SKILLs)

**Status:** plan-author phase — sub-plan authored 2026-05-04, predecessor: Cycle 4b sealed at `c648cf9`.

This is the **final cycle of v0.1.8**. After this seals, the v0.1.8 release-level smoke gate runs (master plan §5). Cycle 5 ships six SKILL.md packages at `plugins/dev-sdlc/skills/<name>/SKILL.md` capturing dev-SDLC-specific rituals. The layered-skill discovery mechanism (v0.1.7 Cycle 3 sealed at `bcf699a`) auto-symlinks them into `<workspace>/.claude/skills/<name>/` at first-run, so they appear in Claude Code's `/` menu without bootstrap-time wiring.

---

## §0 — Scope decision (autonomous, F2 surface)

**Decision (no halt — authorized by master plan §4 Cycle 5 dispatch brief):** Ship all 6 SKILLs named in the master plan first-pass list:

1. `loam-amend-cycle`
2. `dispatch-brief-authoring`
3. `plan-before-code-author`
4. `fidraft-capture`
5. `front-load-principle-walk`
6. `audit-finding-triage`

**Re-evaluation per master plan §7.4 (mandated):** After Cycles 1–4 actual ritual usage, the first-six list still represents the highest-leverage rituals encountered in this v0.1.8 cycle. Specifically:

- `loam-amend-cycle` was exercised 5× across Cycles 1, 2, 3, 4a, 4b — every cycle invokes it. **Critical.**
- `dispatch-brief-authoring` is the shape every Cycle's dispatch followed — codifying it is leverage. **Critical.**
- `plan-before-code-author` was exercised 5× (one plan-doc per cycle). **Critical.**
- `fidraft-capture` was exercised throughout (multiple FUTURE_IDEAS_DRAFT.md additions per cycle). **Critical.**
- `front-load-principle-walk` corresponds to the turn-start "Principles to apply" sections in every dispatch brief. **Critical.**
- `audit-finding-triage` corresponds to halt-and-surface routing decisions made every cycle. **Critical.**

No swap warranted. The first-six list ships intact.

**Independent fence:** single-component fence on `plugins/dev-sdlc/`. No edits to `framework/`. No edits to other plugins. The 6 SKILL.md files land at `plugins/dev-sdlc/skills/<name>/SKILL.md`.

---

## §1 — Outcome shape (the "why")

**Pin:** Six dev-SDLC-specific ritual SKILLs are auto-discovered in canonical pos-v2's `/` menu from session-zero, via the v0.1.7 Cycle 3 layered-skill discovery mechanism (auto-symlink at first-run scaffold).

**Pin:** Each SKILL body is the FULL ritual shape — not a stub. Frontmatter `description` field is non-empty + ≤1536 chars (Anthropic combined-cap). Body covers (a) what the skill captures, (b) when to use, (c) how the persona applies it, (d) graceful degradation for raw Claude Code, (e) composition with other skills/principles, (f) what's out of scope.

**Pin:** Each SKILL has at least one regression test asserting frontmatter validity + body non-emptiness, mirroring the `loam-skills` plugin's `test_AC_LSK_1_skill_packages_present.py` test pattern.

**Pin:** All 6 SKILLs survive `/clear` (D5 cross-session — the ship-test) because they're filesystem-discovered by Claude Code's native walk, not session-state.

**Pin:** The release-level v0.1.8 smoke gate (master plan §5) is unblocked once Cycle 5 seals. After release-level smoke passes, v0.1.8 is locally tagged but not pushed (per dispatch).

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The SKILLs compose on top of Anthropic's native SKILL.md primitive (per `https://code.claude.com/docs/en/skills`), discovered via Claude Code's `<workspace>/.claude/skills/<name>/SKILL.md` walk. The v0.1.7 Cycle 3 auto-symlink mechanism handles registration. No new Claude capability is added — this cycle composes on extant primitives only.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** the persona uses these SKILLs natively when their `description` matches the turn intent. The persona's CLAUDE.md no longer needs to re-derive the rituals (they live in the SKILL.md files); reduces translation burden when "how do I do an amend cycle?" arises in a dev-mode workspace. **PASS.**
- **Harness test:** plugin-shipped dev-SDLC SKILLs become a reusable toolkit. A stranger running `claude` with `dev-sdlc` plugin enabled inherits 6 named rituals without committing to the full loam harness. Adds to harness toolkit. **PASS.**

Both pass.

### Lens 3 — ODD authoring

Outcome (above) + named ACs (§4 below) + halt-trigger constraints (§5 below) + acceptance gate (§12 below). Method (skill body length, exact section ordering, examples count) stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

**Confidence in outcome shape:** HIGH. The SKILL.md shape is verified-working (8 SKILLs in `plugins/loam-skills/` ship via the same mechanism). The 6 ritual targets are well-known (each was exercised ≥5× across Cycles 1–4b). Tight scope: 6 SKILLs at named paths; frontmatter must validate; body must cover the 6 sections; method-level decisions (exact prose, examples chosen) remain the builder's call.

**Failure-mode guard:** the over-tight risk is "the dispatch dictates the exact prose"; this plan-doc never names prose, only structure. The over-loose risk is "agent ships stub bodies with placeholder text"; halt-trigger §8 catches this (any stub body → halt + RF).

### Lens 5 — Swarming

**Decomposition assessment:** the cycle has 6 loosely-coupled SKILL packages. Each SKILL is independent (different ritual, different composition, different "when to use"). In principle each is a tighter-AC subtask.

**Stopping criterion:** at single-cycle granularity, decomposing 6 SKILLs into 6 sub-dispatches adds coordination overhead (manifest, plan-doc, seal commit, status reporting) without tightening any subtask's AC enough to justify the overhead. Sealed-component-build serialization (`feedback_serialize_amendment_builds`) also forbids parallel builds in the same git tree without worktree isolation.

Single-agent serial execution is correct shape. `max_planner_depth` not invoked.

---

## §3 — Single-component fence

**Component fence (manifest names this exactly):**

- `plugins/dev-sdlc/` — single component; six new SKILL.md packages land at `plugins/dev-sdlc/skills/<name>/SKILL.md`. New regression tests land at `plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_*.py`.

**Universal admissions:**

- `docs/rebuild/plans/` — the plan-doc paper trail.

**Cross-component edits:** NONE. No edits to `framework/`, other plugins, or root-level paths beyond plan-doc admission.

**Plan-doc + manifest live at:**

- Plan-doc: `docs/rebuild/plans/v0-1-8-cycle-5-dev-sdlc-skills.md` (this file).
- Manifest: `docs/rebuild/plans/v0-1-8-cycle-5-dev-sdlc-skills.manifest.yaml` (schema v3 — `plan_doc_ref` + `ac_count` + `smoke_outcome`).

---

## §4 — AC family — `AC.SKILLS-DSDLC1.*`

Each AC has at least one explicit pytest under `plugins/dev-sdlc/tests/`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

### AC.SKILLS-DSDLC1.1 — `loam-amend-cycle` SKILL.md

- File at `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md`.
- Valid YAML frontmatter delimited by `---` lines; `description` field present, non-empty, ≤1536 chars.
- Body (post-frontmatter) covers the sealed-component amendment workflow:
  - **What captures:** plan-doc → manifest (v3 schema) → BASELINE source-edit feat commit → `loam amend apply --plan-doc` (single semantic commit) → `loam amend seal --plan-doc` (deterministic short-form seal commit) → §14 method-decision register backfill (post-seal commit).
  - **When to use:** any sealed-component amendment cycle in a loam dev-mode workspace.
  - **How persona applies it:** ordered ritual steps the persona walks through.
  - **Graceful degradation:** raw Claude Code without loam (manual git-commit ladder).
  - **Composition:** with `dispatch-with-gates`, `plan-before-code-author`, `feedback_no_amend_in_agent_dispatches`.
  - **Out of scope:** dev-pattern-simplifications mechanics, schema-version migration internals.
- **Test:** `tests/test_AC_SKILLS_DSDLC1_1_loam_amend_cycle_skill_present.py` — file exists; frontmatter parses; description non-empty + ≤1536 chars; body non-empty; body mentions key terms (`plan-doc`, `manifest`, `apply`, `seal`).

### AC.SKILLS-DSDLC1.2 — `dispatch-brief-authoring` SKILL.md

- File at `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`.
- Valid frontmatter; description non-empty + ≤1536 chars.
- Body covers the dispatch-brief shape used in every Cycle's dispatch:
  - **What captures:** the structural shape — Working directory + Principles to apply at turn-start + QUALITY BAR + Source pointers + Sub-plan path + Fence + Acceptance criteria + Smoke + Halt triggers + Out of scope + Bookkeeping + Model rationale.
  - **When to use:** authoring any sealed-component or sub-task dispatch brief for a build / research / authoring agent.
  - **How persona applies it:** ordered ritual + the surface-when-meaningful checks.
  - **Graceful degradation:** raw Claude Code Task-tool dispatches without the loam corpus — keep objective + scope + halt triggers + ODD-check ONLY.
  - **Composition:** with `dispatch-with-gates`, `plan-before-code-author`, `front-load-principle-walk`, `audit-finding-triage`.
  - **Out of scope:** specific principle text (lives in CLAUDE.md), specific ODD methodology (lives in odd-methodology.md).
- **Test:** `tests/test_AC_SKILLS_DSDLC1_2_dispatch_brief_authoring_skill_present.py` — file exists; frontmatter valid; description constraints; body mentions key terms (`Working directory`, `Halt triggers`, `Acceptance criteria`).

### AC.SKILLS-DSDLC1.3 — `plan-before-code-author` SKILL.md

- File at `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md`.
- Valid frontmatter; description non-empty + ≤1536 chars.
- Body covers the ODD-shaped plan-doc skeleton:
  - **What captures:** plan-doc structure — Outcome shape (the "why") + Lens checks + Single-component fence + AC family + Halt triggers + Smoke + Bookkeeping + F2 RF + Provenance + Acceptance gate + §14 method-decision register.
  - **When to use:** before any source code is written for a sealed-component amendment cycle.
  - **How persona applies it:** ordered authoring walk.
  - **Graceful degradation:** raw Claude Code without loam — write a `plan.md` covering objective + ACs + halt triggers + done-condition.
  - **Composition:** with `dispatch-brief-authoring`, `loam-amend-cycle`, `feedback_plan_before_code`.
  - **Out of scope:** the actual code (this skill is plan-time-only).
- **Test:** `tests/test_AC_SKILLS_DSDLC1_3_plan_before_code_author_skill_present.py` — file exists; frontmatter valid; description constraints; body mentions key terms (`Outcome shape`, `Acceptance criteria`, `method-decision`).

### AC.SKILLS-DSDLC1.4 — `fidraft-capture` SKILL.md

- File at `plugins/dev-sdlc/skills/fidraft-capture/SKILL.md`.
- Valid frontmatter; description non-empty + ≤1536 chars.
- Body covers the FUTURE_IDEAS_DRAFT.md capture pattern:
  - **What captures:** entry shape — when-occurred timestamp + named idea + provenance (cycle / context / file) + composes-with + recommended next step (graduate / merge / discard).
  - **When to use:** any time a future-idea, deferred-feature, RF-surface, or improvement-opportunity is encountered mid-flow.
  - **How persona applies it:** capture at point-of-occurrence; never delegate to "I'll remember"; daily-rigor review graduates entries to FUTURE_IDEAS.md.
  - **Graceful degradation:** raw Claude Code without loam — append to a `TODO.md` or `IDEAS.md` file at the workspace root.
  - **Composition:** with `feedback_future_ideas_draft_workflow`, `feedback_durable_capture_for_planned_work`, `session-handoff`.
  - **Out of scope:** the graduation rubric (lives in the dev-mode CLAUDE.md fragment).
- **Test:** `tests/test_AC_SKILLS_DSDLC1_4_fidraft_capture_skill_present.py` — file exists; frontmatter valid; description constraints; body mentions key terms (`FUTURE_IDEAS_DRAFT`, `provenance`, `graduate`).

### AC.SKILLS-DSDLC1.5 — `front-load-principle-walk` SKILL.md

- File at `plugins/dev-sdlc/skills/front-load-principle-walk/SKILL.md`.
- Valid frontmatter; description non-empty + ≤1536 chars.
- Body covers the persona's turn-start principle re-citation ritual:
  - **What captures:** the turn-start re-cite — name the active principles (CHANNEL / AUTONOMY / F2 RF / LOCKED-DESIGN-NOT-LICENSE / ODD §2.5 / WD-IN-DISPATCHES / etc.) before the first non-trivial tool call.
  - **When to use:** every turn opening in a dev-mode loam workspace; mandatory for any sealed-component build.
  - **How persona applies it:** ordered checklist; refresh attention pointer; surface in dispatch brief when delegating.
  - **Graceful degradation:** raw Claude Code without loam — apply a generic "principles before tools" walk (objective / fence / halt triggers).
  - **Composition:** with `feedback_principle_self_reminder_at_end_of_turn`, `feedback_session_start_discipline`, `dispatch-brief-authoring`.
  - **Out of scope:** the per-principle bodies (live in CLAUDE.md / memory feedback files); this skill is the ritual, not the corpus.
- **Test:** `tests/test_AC_SKILLS_DSDLC1_5_front_load_principle_walk_skill_present.py` — file exists; frontmatter valid; description constraints; body mentions key terms (`turn-start`, `principle`, `re-cite`).

### AC.SKILLS-DSDLC1.6 — `audit-finding-triage` SKILL.md

- File at `plugins/dev-sdlc/skills/audit-finding-triage/SKILL.md`.
- Valid frontmatter; description non-empty + ≤1536 chars.
- Body covers handling of agent halt-and-surface findings:
  - **What captures:** the triage walk — receive halt-and-surface from a dispatched agent → test against operational objective → categorise (in-scope-resolve / in-scope-defer / out-of-scope-FIDRAFT / owner-escalate) → route → close the loop with the agent's status file.
  - **When to use:** when any dispatched agent returns a halt-and-surface finding (ODD violation, fence breach, schema mismatch, novel ambiguity).
  - **How persona applies it:** the four-bucket categoriser + the autonomous-vs-escalate signal weights.
  - **Graceful degradation:** raw Claude Code without loam — same four-bucket triage applied to any sub-agent output that surfaces a question or constraint conflict.
  - **Composition:** with `feedback_subagent_odd_violation_halt`, `feedback_critical_thinking_on_deviations`, `feedback_principle_conflict_resolution_multi_signal`, `dispatch-brief-authoring`.
  - **Out of scope:** the dispatch mechanics (lives in `dispatch-with-gates`); the principle-conflict resolution four-step process (lives in M5).
- **Test:** `tests/test_AC_SKILLS_DSDLC1_6_audit_finding_triage_skill_present.py` — file exists; frontmatter valid; description constraints; body mentions key terms (`halt-and-surface`, `triage`, `escalate`).

### AC.SKILLS-DSDLC1.7 — All 6 auto-discoverable via layered-skill mechanism

- After running the v0.1.7 Cycle 3 first-run scaffold (`_symlink_plugin_skills`) against a fresh canonical workspace, `<workspace>/.claude/skills/<skill-name>/` symlinks exist for all 6 dev-sdlc SKILLs (in addition to the 8 base loam-skills SKILLs). Each symlink points at the absolute path of the `plugins/dev-sdlc/skills/<name>/` directory.
- **Test:** `tests/test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py` — walks `plugins/dev-sdlc/skills/` and asserts the 6 directories each contain a valid `SKILL.md`; cross-checks against an `EXPECTED_SKILLS` constant.

### AC.SKILLS-DSDLC1.8 — Regression-test floor (per AC named above)

- AC.SKILLS-DSDLC1.{1..6} each have a per-skill regression test asserting the file's structural validity (frontmatter shape + description constraints + body non-emptiness + key-term presence).
- AC.SKILLS-DSDLC1.7 has the discovery cross-check test.
- **Test floor:** ≥7 new test functions across ≥7 new test files (one per AC + one cross-check); the test_AC_LSK_1 pattern from loam-skills is the structural reference.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

**Decision A:** v0.1.7 Cycle 3 (layered-skill discovery) is sealed at `bcf699a` (verified via `git log` at plan-author time). The auto-symlink mechanism is live in `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:_symlink_plugin_skills`. **Halt-trigger satisfied.**

**Decision B:** Frontmatter shape — Anthropic SKILL.md schema requires `description` field (string, ≤1536 chars combined-cap). The loam-skills plugin's existing pattern uses ONLY `description` (no `name` field; the directory name IS the skill name). **Adopted same pattern.** Verified at `plugins/loam-skills/skills/dispatch-with-gates/SKILL.md:1-3` and the 7 sibling SKILLs.

**Decision C:** SKILL body section ordering — the loam-skills plugin uses `What captures → When to use → How persona applies it → Graceful degradation → Composition → Out of scope`. **Adopted same ordering** for cross-plugin shape consistency. Per Lens 4 (high confidence), the established pattern wins.

**Decision D:** Test pattern — mirror `plugins/loam-skills/tests/test_AC_LSK_1_skill_packages_present.py`'s structure. **Adopted.** Each AC gets its own test file (per-AC granularity from the dev-sdlc test suite's existing convention, e.g., `test_AC_OSS_M6_9_start_project_skill_shipped.py`).

**Decision E:** No new dev-mode-manifest.yaml entry needed — `plugins/dev-sdlc/skills/` is already implicitly under `plugins/dev-sdlc/**` if the manifest gates it; verify at build-time. (Manifest gates by plugin-root, not by sub-directory; the SKILLs ship with the plugin.)

**Decision F:** No edits to `odd-methodology.md` required — Cycle 5 ships SKILLs, not extractor / methodology changes. Universal admissions reduced to `docs/rebuild/plans/` only.

No halt-and-surface conditions trigger. Proceed to build.

---

## §6 — Smoke (REALISTIC CONDITION — all 6 dimensions per smoke-test-discipline.md §6)

**D1 — cold-state.** Fresh canonical pos-v2 workspace clone; `loam init` (or equivalent first-run-scaffold invocation); verify `<workspace>/.claude/skills/loam-amend-cycle/SKILL.md`, `dispatch-brief-authoring/SKILL.md`, `plan-before-code-author/SKILL.md`, `fidraft-capture/SKILL.md`, `front-load-principle-walk/SKILL.md`, `audit-finding-triage/SKILL.md` are all symlinks pointing at the dev-sdlc plugin paths. Verified by `tests/test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py` (file-system walk against fixture).

**D2 — steady-state.** Re-run scaffold against the same workspace; symlinks unchanged (idempotent; verified by `_symlink_plugin_skills`'s extant idempotency check at lines 1277-1284). No queue/log growth (n/a — one-shot scaffold, no daemon).

**D3 — restart.** n/a structurally — SKILLs are filesystem artefacts, no long-running process. Inherited from layered-skill discovery's D3 (Cycle 3 of v0.1.7).

**D4 — reboot.** n/a structurally — symlinks survive reboot trivially (filesystem state).

**D5 — cross-session.** **THE ship-test.** SKILLs visible after `/clear` or fresh `claude` session. Verified by re-walking the `<workspace>/.claude/skills/` directory in the next session and asserting all 6 dev-sdlc SKILLs still resolve. Inherited from Anthropic's native discovery primitive.

**D6 — telemetry-floor.** Inherited from layered-skill discovery's audit-trail floor (v0.1.7 Cycle 3); `_symlink_plugin_skills` returns the tuple of relative paths written, which the scaffold logs. No new audit surface required for Cycle 5.

**Per-cycle smoke exercise:**

- D1: run pytest on the 7 new test files; all pass green.
- D2: idempotent re-scaffold smoke (verified by AC.LAYERED.2's existing idempotency test).
- D3/D4: documented n/a.
- D5: post-`/clear` directory walk (verified by D1 test in fresh session).
- D6: inherited.

**PLUS: full-suite green sweep — pre-existing tests must pass post-amendment.** 463 dev-sdlc parent tests at HEAD `c648cf9` (Cycle 4b seal) all pass post-Cycle-5; halt + surface on any regression. Cycle 5 adds ~7 new test functions; expected post-cycle test count ≥ 470.

**Release-level smoke gate (master plan §5 — runs AFTER Cycle 5 seals):**

- All four-stage codebase-reader extractions (Ruby + JS/TS) produce expected band distributions on canonical fixtures (per master plan §5 D1).
- All 6 dev-sdlc SKILLs discoverable in canonical pos-v2's `/` menu (per master plan §5 D1).
- Path 1 (JS/TS) + Path 2 (Rails) end-to-end smokes both pass (per master plan §5).
- HARD gate per Decision R — if release-level smoke fails on any dimension, halt + surface; do NOT mark v0.1.8 SHIPPED.

---

## §7 — Out of scope (Cycle 5)

- **Six second-pass dev-sdlc SKILLs** (`seal-narrative-writer`, `hook-violation-recovery`, etc.) — DEFERRED to v0.1.9.
- **Auto-creation mechanism** (the persona authors a new SKILL.md on the fly when a missing-ritual surface is detected) — DEFERRED to v0.2.0.
- **Promotion rubric** (workspace-local SKILL → plugin-shipped SKILL graduation) — DEFERRED to v0.2.1.
- **Real OSS Rails-payment + JS/TS-Playwright fixtures** for v0.2.1 release-level — explicitly out of scope per dispatch.
- **Python adapter** — DEFERRED to v0.2.2+ post-Eric per dispatch.
- **`v0.1.9+ work** (PR-safety gate + 6 more dev-sdlc SKILLs) — out of scope per dispatch.

---

## §8 — Halt triggers (in-flight)

- **WD drifts** to a non-canonical-pos-v2 path → halt + surface.
- **Plan-doc not authored before code** → halt + reframe (this plan-doc satisfies the trigger; subsequent edits to the cycle's source are admissible only after this doc commits).
- **Any SKILL ships partial** (missing required sections; frontmatter invalid; body is a stub or aspirational placeholder) → halt + RF.
- **Live `/` menu fails to show any of the 6** in canonical pos-v2 → halt (this is the ship-test).
- **Release-level smoke fails on any dimension** after Cycle 5 seals → halt + surface; do NOT mark v0.1.8 shipped.
- **More than 5 in-build decisions need Luke escalation** → halt + describe.
- **Wall-clock exceeds 5 hours total** for the cycle → halt with partial findings.

---

## §9 — Bookkeeping

Per `feedback_dispatch_explicit_pos_amend_apply` + `feedback_no_amend_in_agent_dispatches`:

- Plan-doc commits FIRST (this commit).
- Source-edit feat commit lands SECOND (the 6 SKILL.md files + ≥7 new test files).
- `loam amend apply --plan-doc <abs path>` lands the manifest+apply commit (single semantic commit per schema v3 AC.DPS1.6).
- `loam amend seal --plan-doc <abs path>` lands the deterministic short-form seal commit per AC.DPS2.{1,4,6}.
- `git commit --amend` is **forbidden** — if a file is missed, create a NEW corrective commit.
- Single-component manifest:
  - `name: dev-sdlc`
  - `seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py`
  - `sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT`
  - `frozen_baseline: false`
  - `extra_allowed_prefixes: []`
- Universal admissions: `docs/rebuild/plans/` only.
- Backfill master plan §9 method-decision register Cycle 5 row with apply + seal SHAs (separate post-seal commit per Cycle 1–4b precedent).
- Backfill v0.1.8 release-level rows (STATE.md + roadmap §8 + eric-final-delivery-plan §2) with all 5 cycle SHAs + SHIPPED status — ONLY after release-level smoke passes.
- DO NOT push tags. v0.1.8 sits as a local release.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-5-status-2026-05-04.md` — build agent writes per-AC status + smoke outcome + halt-and-surface findings here.

**Release-summary file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-release-status-2026-05-04.md` — stitches all 5 cycles + release-level smoke results.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **The 6 SKILLs codify rituals already exercised in v0.1.8 Cycles 1–4b.** This is a documentation-shape cycle — no new mechanism, no new behaviour. The leverage is reuse + cross-workspace portability + reduce CLAUDE.md re-derivation. RF: low novelty risk; high portability win. Acceptable.

2. **Body section ordering is copied from loam-skills.** The shape (`What captures → When → How → Degradation → Composition → Out of scope`) is verified-working in 8 sealed SKILLs. RF: monoculture risk if the ordering is wrong; mitigated by the existing 8-SKILL precedent (any flaw would have surfaced by now).

3. **No SKILL describes the `loam-amend-cycle` failure modes** (e.g., what to do when `loam amend apply` fails halfway). RF: failure-mode coverage is shallow. **Mitigation:** the SKILL points at `feedback_no_amend_in_agent_dispatches` for the corrective-commit pattern, and `loam amend seal --no-finalize` for the partial-seal escape. Future v0.1.9 SKILL `hook-violation-recovery` can codify the recovery walks formally.

4. **`dispatch-brief-authoring` codifies the SHAPE but not the QUALITY BAR.** The QUALITY BAR section (e.g., "It can't be half-assed") is dispatcher-authored content, not boilerplate. RF: the SKILL teaches the structure but won't generate the right intensity of QUALITY BAR text per cycle. **Mitigation:** explicit acknowledgement in the SKILL that QUALITY BAR is per-dispatch content; the SKILL ships the slot, not the slot's body.

5. **`fidraft-capture` and `feedback_future_ideas_draft_workflow` overlap.** The feedback memory file already covers the workflow; the SKILL is structurally redundant. RF: yes — but the SKILL surfaces in the `/` menu and auto-loads; the feedback memory only loads on session-start. The SKILL is the "this turn, capture this idea" call-out; the feedback memory is the persistent cross-session principle. Both compose; both retained.

6. **`front-load-principle-walk` SKILL is functionally similar to `feedback_principle_self_reminder_at_end_of_turn`.** The feedback memory is end-of-turn re-cite; this SKILL is start-of-turn re-cite. They're complementary (start + end book-end the turn). RF: the naming distinction must be crisp — this SKILL is **start**, the feedback file is **end**. Body explicitly references the pair.

7. **`audit-finding-triage` overlaps with `feedback_subagent_odd_violation_halt`.** The feedback memory says "agents must halt-and-surface ODD violations"; this SKILL is the dispatcher-side response to that surface. RF: the agent-side discipline (halt) and the dispatcher-side discipline (triage) are different surfaces; both retained. SKILL composes with the feedback memory.

8. **No SKILL explicitly captures the `--scoped-sweep` vs full-sweep tradeoff** for `loam amend seal`. RF: the `loam-amend-cycle` SKILL mentions `seal` but does not enumerate flags. **Mitigation:** the SKILL's body points at `loam amend seal --help` for flag exhaustive list; the cycle pattern handles the common case.

9. **`plan-before-code-author` SKILL is functionally similar to `feedback_plan_before_code`.** The feedback memory is the principle; the SKILL is the structural authoring walk (the plan-doc skeleton). RF: complementary; SKILL provides the template, feedback memory provides the rule.

10. **Test count target (~7 new test functions across ≥7 new files) is a guess.** Actual count may land at 8–10 depending on whether the cross-check test (AC.SKILLS-DSDLC1.7) doubles as a parametrised test of all 6 frontmatter validations vs separate per-AC tests. Marked as estimate per `feedback_specific_claims_verified_or_marked_guess`.

11. **Plan-doc length** — this plan-doc is ~430 lines. Output-to-disk convention satisfied; the dispatcher reads the summary section + decisions, not the full doc.

---

## §11 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`.
- v0.1.7 per-project-pm + layered-skill discovery — sealed at `3aa20dd` + `73505f0` + `bcf699a` + `122a7c8`.
- Dev-pattern-simplifications #1 + #2 — sealed at `019cfca` + `df3f50f`.
- v0.1.8 master plan — sealed at `1c2c478`; rerouted at `17f32a9`.
- v0.1.8 Cycle 1 — sealed at `c1abda1`. Provides scaffold + adapter Protocol + audit-log primitive.
- v0.1.8 Cycle 2 — sealed at `4865028`. Provides `BandedAC` + `Evidence` + `ConfidenceBand` + ratification.
- v0.1.8 Cycle 3 — sealed at `6711dd7`. Provides Ruby/Rails first-class adapter.
- v0.1.8 Cycle 4a — sealed at `67dd302`. Provides JS/TS/Playwright adapter.
- v0.1.8 Cycle 4b — sealed at `c648cf9`. Provides canonical Ruby fixture + Ruby e2e + DRY refactor.
- Master plan §4 Cycle 5 dispatch brief — locked at `1c2c478`; this plan-doc operationalises it.
- Master plan §5 release-level smoke gate — runs after Cycle 5 seals.
- v0.1.7 Cycle 3 layered-skill discovery (`bcf699a`) — the auto-symlink mechanism this cycle composes on.
- loam-skills plugin (`plugins/loam-skills/`) — 8 SKILLs at v0.1.6 sealing; the structural reference for SKILL.md shape and test pattern.
- Anthropic SKILL.md schema — `https://code.claude.com/docs/en/skills` (description ≤1536 chars combined-cap).
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — Cycle 5 makes no edit.
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions.
- Pre-cycle baseline: 463 dev-sdlc parent tests at HEAD `c648cf9` (verified at plan-author time via `git log`; full pytest run deferred to build-time).

---

## §12 — Acceptance gate

This plan-doc is gate-ready when:

1. All 8 ACs (AC.SKILLS-DSDLC1.{1..8}) named with explicit pytest paths (§4) — done.
2. Single-component fence named (§3) — done.
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) — done.
4. Halt triggers named (§8) — done.
5. Bookkeeping path named (§9) — done.
6. F2 gaps named (§10) — done.
7. Method-decision record named per AC.D-sa.7 (§14) — done below.
8. Pre-cycle baseline named (§11) — done (463 tests at `c648cf9`).
9. Release-level smoke gate named (§6) — done.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Per AC.D-sa.7, every plan-doc that selects non-default methods records the decision + rationale. This cycle's method-level decisions:

| Decision | Choice | Rationale |
|---|---|---|
| SKILL frontmatter shape | `description`-only (no `name` field) | Mirrors the 8 sealed loam-skills SKILLs; Anthropic's schema treats the directory name as the skill identifier (verified at `plugins/loam-skills/skills/*/SKILL.md`). Adding `name` would create cross-plugin shape inconsistency. |
| SKILL body section ordering | `What captures / When to use / How persona applies it / Graceful degradation / Composition / Out of scope` | Verified-working pattern across 8 sealed SKILLs in `plugins/loam-skills/`. Lens 4 (high confidence) → adopt the established pattern; deviation would be over-loose at high confidence. |
| Test file granularity | One test file per AC (7 new test files) | Mirrors dev-sdlc plugin's existing convention (e.g., `test_AC_OSS_M6_9_*.py`). Per-AC granularity makes test failures map cleanly to ACs without parametrize-induced coupling. |
| AC.SKILLS-DSDLC1.7 cross-check shape | Single test file walking the directory + cross-checking `EXPECTED_SKILLS` constant | Mirrors `plugins/loam-skills/tests/test_AC_LSK_1_skill_packages_present.py:test_all_skills_discovered`. Direct precedent. |
| Universal admissions | `docs/rebuild/plans/` only | No `odd-methodology.md` edit needed (Cycle 5 ships SKILLs, not methodology); no `STATE.md` edit at cycle-time (release-level rollup happens post-smoke-gate). Minimum fence per ODD discipline. |
| `_common/`-style sub-package for SKILLs? | NO | Each SKILL is self-contained; no cross-skill helper code. The `lang/_common/` precedent (Cycle 4b) was for shared adapter helpers; SKILLs are reference-content packages with no shared code. |
| Dispatch model tier | Sonnet (default) | Master plan §4 Cycle 5 brief explicitly says "(none — Sonnet default)" — this plan-doc inherits. No model-rationale line required. |
| Decomposition into 6 sub-dispatches? | NO | Per Lens 5: 6 SKILLs each have similar shape and similar acceptance criterion shape (frontmatter + body). Sub-dispatching adds coordination overhead without tightening any subtask's AC. Sealed-component-build serialization also forbids parallel builds without worktree isolation. |
| Skip release-level smoke? | NO — HARD gate per Decision R | Master plan §5 Decision R locks v0.1.8 release-level smoke as HARD; if it fails, do NOT mark v0.1.8 SHIPPED. |

---

### Commit SHAs

(to be appended by `loam amend seal --plan-doc` per AC.D-sa.7)

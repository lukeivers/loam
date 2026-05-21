# v0.2.1 Cycle 2 — Promotion rubric mechanism

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.1 Cycle 1 SEALED — apply `f6b5047`, seal `55640b1`, §14 backfill `d7c5b2d`, master plan §9 backfill `4c4a1d3`. v0.2.0 SHIPPED rollup at `bbc93a7`. Master plan committed at `2ff444e` / patched at `2ba7fcd` / swept at `9355ef2` / FIDRAFT entry at `df447bc`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-2-1-master-plan.md` §3 Cycle 2 + §4 Cycle 2 dispatch brief.

**Status file (to be authored by build agent):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-1-cycle-2-status-2026-05-04.md`.

**Quality bar (Luke directive 2026-05-04, load-bearing):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.1 Cycle 2 is the disciplined evaluation surface for workspace-local SKILLs accumulated by auto-skill-capture (v0.2.0 Cycle 2). The 3-signal MVP (Decision L) is intentional — not 6-signal-half-implemented; the SKILL body covers the FULL ritual (not stub); decision matrix encodes all 10 row classes from layered-skills §4.2; owner ratification default-to-no per Decision G; quarterly trigger composes cleanly with `framework/scope-of-work/` OR falls back to on-demand `/skill-promotion-review`. **No partial features.**

---

## §1 — Outcome shape (the "why")

v0.2.1 Cycle 2 ships the **`skill-promotion-review` SKILL** under `plugins/dev-sdlc/skills/skill-promotion-review/` — a workflow SKILL that walks the persona through evaluating workspace-local SKILLs (the artefacts auto-skill-capture has been depositing under `<workspace>/.claude/skills/` per v0.2.0 Cycle 2) and producing a structured graduation recommendation. The SKILL is dev-scoped per the three-tier gating: only dev-mode workspaces get the promotion-review surface; non-dev users (Eric, writers, lawyers) accumulate workspace-local SKILLs but the graduation pipeline runs on Luke's side after Eric's accumulated patterns have surfaced.

**Fence reality.** The SKILL package layout is well-precedented: 12 `plugins/dev-sdlc/skills/<name>/SKILL.md` packages exist at HEAD `4c4a1d3` (sealed across v0.1.8 Cycle 5 + v0.1.9 Cycle 3). 9 more `plugins/loam-skills/skills/<name>/SKILL.md` packages exist (universal-tier). The SKILL test convention is `plugins/dev-sdlc/tests/test_AC_SKILLS_*_<name>_skill_present.py` with frontmatter + body + key-terms checks. The `loam-amend-cycle` SKILL is the closest precedent: workflow-shaped (vs categoriser-shaped); composes on `plan-before-code-author` + `dispatch-brief-authoring` + `audit-finding-triage`; this SKILL composes on `loam-amend-cycle` + `audit-finding-triage` + `owner-decision-summary` + `dispatch-brief-authoring`.

**`framework/scope-of-work/` reality (compose-point READ-ONLY).** scope-of-work is an event-sourced FSM over SQLite WAL with three-axis budgeting + escalation triggers. It is foundational infrastructure, not a cron scheduler. There is no "schedule a quarterly review" API; integration would require either (a) authoring a new "calendar-trigger" surface in scope-of-work itself (NON-trivial; out of Cycle 2 scope per master plan halt-trigger), or (b) authoring a workspace-local convention that scope-of-work scopes are created with a 90-day reversibility window + a `quarterly-skill-review` escalation trigger. **The MVP fallback per master plan halt-trigger is on-demand `/skill-promotion-review` invocation only** — no cron, no calendar plumbing. This plan-doc commits to the fallback shape: AC.PROMOTE.10 ships the on-demand invocation path; the SKILL body documents the 90-day cadence as an *owner-self-discipline cadence* (the persona surfaces "it's been 90 days since the last review" if the workspace's last-review timestamp is older than 90d, but does not auto-fire). Quarterly auto-trigger via scope-of-work integration deferred to v0.2.x.

**Cycle 2's release-note promise:** invoking `/skill-promotion-review` (or the persona auto-recognising the trigger phrase per layered-skill discovery from v0.1.7 Cycle 3 `bcf699a`) walks the workspace's `.claude/skills/` directory, evaluates each workspace-local SKILL across the 3-signal MVP (Categorization + Quality + Conflict), produces a structured table per-SKILL with the matched decision-matrix row class + recommended action, surfaces each promotion candidate one-at-a-time through the PM batch API per Decision Q (composes on v0.1.7 Cycle 4 `122a7c8`), records owner ratification (default-to-no per Decision G), and for each ratified promotion guides the persona through the graduation amendment cycle (composes on `loam-amend-cycle` SKILL): author tests → move SKILL.md to `plugins/loam-skills/skills/` (HARNESS-GENERAL) or `plugins/dev-sdlc/skills/` (DEV-SPECIFIC) → loam amend apply → loam amend seal → remove workspace-local copy (replaced with `pointer.md` line). The SKILL body also surfaces the demotion path per layered-skills §4.4: "skill X has fired N times since promotion; demote/retire?" framing with corrective amendment cycle as the resolution.

**Discipline-shaped gating per workspace-local-SKILL absence.** When the workspace has zero SKILLs under `<workspace>/.claude/skills/`, the SKILL surfaces "no workspace-local SKILLs found; auto-skill-capture has not produced candidates yet" and exits cleanly. No false-positive promotions; no error path.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The SKILL composes on existing primitives:

- **Anthropic SKILL filesystem-discovery + v0.1.7 Cycle 3 layered-skill discovery (`bcf699a`).** The `skill-promotion-review` SKILL itself becomes discoverable + slash-invokable.
- **`<workspace>/.claude/skills/` directory walk via Anthropic `Read`/`ls`.** No custom file-discovery API needed.
- **`framework/per-project-pm/`'s `enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response`.** Owner ratification one-at-a-time per Decision Q. Zero PM-side edits.
- **`plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md`.** Graduation (move + manifest + apply + seal) delegates wholesale; Cycle 2 does NOT re-implement.
- **`plugins/loam-skills/skills/owner-decision-summary/` + `dispatch-with-gates/`.** Promotion-summary format + sub-agent dispatch shape.
- **`plugins/dev-sdlc/skills/audit-finding-triage/`.** Four-bucket triage on NEEDS-REVISION / DUPLICATE findings.

Answer to **"What Claude capability does this lean on or extend?"** — every load-bearing primitive composes on v0.1.7 → v0.2.0 surfaces. The SKILL is the orchestration layer.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops. Owner's natural-language intent ("which of my workspace SKILLs are real toolkit additions vs workspace-junk?") translates to AI-effective execution ("walk every SKILL, evaluate against the 3 primary signals, surface each promotion candidate one-at-a-time"). The persona doesn't ask "how should I categorise reusability?" or "what's the conflict-detection threshold?" — those are pinned by the SKILL body. Pass.
- **Harness test:** every dev-mode loam workspace gets the same promotion-review shape from `/skill-promotion-review`. Eric's accumulated Rails patterns (when his auto-skill-capture fires on recurring patterns post-30-days) become input to a Luke-side review where they graduate to `plugins/dev-sdlc/skills/`. The mechanism is what makes per-workspace SKILL accumulation compound into harness-level value. Pass.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§3) + halt triggers (§5) + acceptance smoke (§4 smoke dimensions). Method (signal-evaluation algorithm specifics, body section content beyond the 6-section convention, fixture shape, quarterly-trigger fallback path message wording, decision-matrix table rendering format) stays the builder's call within constraints (12 ACs locked; 3-signal MVP; 10 decision-matrix rows; one-at-a-time PM ratification; default-to-no; on-demand fallback for quarterly trigger; SKILL package convention from 21 sealed precedents).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 Cycle 2 names all 12 ACs; layered-skills §4 names all 6 signals + 10 decision-matrix rows + 6-step graduation workflow + demotion path; 21 sealed SKILL precedents pin the package convention; PM batch API verified.

Outcome confidence is **MEDIUM-HIGH** for the signal-evaluation algorithm. The signal categories are pinned; the heuristics inside each are method-level. Plan-doc commits: **Quality** uses the existing structural-test convention (frontmatter parses + description present + ≤1536 chars + body non-empty + body mentions key terms); **Conflict** uses literal-name-match against `plugins/dev-sdlc/skills/` + `plugins/loam-skills/skills/` plus a description-keyword-overlap heuristic for non-literal duplicates; **Categorization** uses a keyword-allowlist (HARNESS-GENERAL = universal concepts; DEV-SPECIFIC = mentions loam-amend / plan-before-code / sealed-component; PROJECT-SPECIFIC = workspace business-domain identifiers). All three have explicit "halt-and-surface to owner if ambiguous" fallbacks; never silent miscategorisation.

Outcome confidence is **MEDIUM** for quarterly-trigger fallback — plan-doc commits to on-demand-only; 90-day cadence as owner-self-discipline; scope-of-work auto-fire deferred to v0.2.x.

Outcome confidence is **HIGH** for PM batch API one-at-a-time + graduation amendment-cycle delegation. v0.1.7 Cycle 4 + `loam-amend-cycle` SKILL exercised across every v0.1.x cycle.

### Lens 5 — Swarming

Single-component fence under `plugins/dev-sdlc/skills/skill-promotion-review/` (PRIMARY) + tertiary admission for the SKILL test under `plugins/dev-sdlc/tests/`. Within the cycle, decomposition options:

- (a) one SKILL package + one structural test file (frontmatter + body + key-terms) following the existing `test_AC_SKILLS_DSDLC1_*` convention. Each AC mapped to a single test or a sub-section of the structural test. Mirrors the 12 sealed SKILLs precedent.
- (b) split SKILL package + signal-evaluation harness test (a Python module that exercises the signal-evaluation algorithm against synthetic workspace-local SKILL fixtures) + PM-flow integration test. More tests, more granularity, but the signal-evaluation logic lives in the SKILL body (instructions to the persona) NOT in Python — a Python harness for what the persona reads conceptually is type-mismatched.

The builder picks **(a)** — the SKILL is a workflow body the persona reads; tests verify the body is well-formed + covers the 12 named AC concerns. Synthetic workspace-local SKILL fixtures (3+ shapes per AC.PROMOTE.11) validate the SKILL body covers the right paths textually (key-terms presence) rather than executing a signal-evaluation Python function. `max_planner_depth: 1` (no sub-planners; single SKILL + structural test is the right granularity). No further decomposition adds value.

---

## §3 — AC enumeration — `AC.PROMOTE.*` (locked, 12 ACs)

Each AC has at least one explicit pytest. ODD §2.5 — every line of SKILL body content + every test branch maps to a named AC. AC.PROMOTE.1 → AC.PROMOTE.12 inherited verbatim from master plan §3 Cycle 2.

- **AC.PROMOTE.1 — `skill-promotion-review` SKILL package with valid SKILL.md.**
  - Path: `plugins/dev-sdlc/skills/skill-promotion-review/SKILL.md`.
  - Frontmatter: YAML mapping with `description` field (string, non-empty, ≤1536 chars per Anthropic combined-cap). NO `name` field (mirrors 21 sealed SKILL precedents).
  - Body: 6-section shape per dev-sdlc convention (v0.1.8 Cycle 5 + v0.1.9 Cycle 3 + v0.2.0 verified): What this skill captures / When to use / How the persona applies it / Graceful degradation / Composition / Out of scope.
  - Fence component: `plugins/dev-sdlc/`.
  - Test: `test_AC_PROMOTE_1_skill_package.py` — file exists; frontmatter parses; description present + non-empty + ≤1536 chars; body non-empty; all 6 section headings present.

- **AC.PROMOTE.2 — 3-signal MVP body specifies primary gates per Decision L.**
  - SKILL body §"What this skill captures" enumerates 3 primary signals: **Categorization** (HARNESS-GENERAL → `plugins/loam-skills/` / DEV-SPECIFIC → `plugins/dev-sdlc/skills/` / PROJECT-SPECIFIC → stay-workspace-local), **Quality** (PASS / FAIL / NEEDS-REVISION; structural-test equivalent), **Conflict** (NO-CONFLICT / DUPLICATE / WIDER / NARROWER / ADJACENT; literal-name + keyword-overlap heuristic).
  - Body also discusses 3 secondary signals (Reusability + Tests + Usage) as non-blocking inputs; body explicitly states they "do not block a promotion recommendation that the 3 primary signals pass."
  - Test: `test_AC_PROMOTE_2_three_signal_mvp.py` — body mentions all three primary signal names + all category values + secondary-non-blocking framing.

- **AC.PROMOTE.3 — Decision matrix encoded in SKILL body covering all 10 row classes from layered-skills §4.2.**
  - SKILL body §"How the persona applies it" includes a markdown table mirroring layered-skills §4.2 with 10 rows: (1) Promote-to-base, (2) Promote-to-plugin (Reusability=STRONG, DEV-SPECIFIC), (3) Promote-to-plugin (Reusability=MEDIUM, DEV-SPECIFIC), (4) Stay-workspace-local, (5) Author-time-fix (Quality=FAIL), (6) Author-tests (Tests=NEEDS-TESTS), (7) Defer (Usage=NONE/WEAK), (8) Deprecate (Conflict=DUPLICATE), (9) Promote-with-deprecation-pointer (Conflict=WIDER), (10) Fold-into-existing-or-keep-workspace-specific (Conflict=NARROWER).
  - Each row has explicit signal-combination + recommended action. Body explicitly states "the matrix is human-readable; the persona walks it during the review and surfaces the matched row + recommendation per candidate SKILL."
  - Fence component: `plugins/dev-sdlc/`.
  - Test: `test_AC_PROMOTE_3_decision_matrix.py` — body contains a markdown table with at least 10 rows; body mentions each of the 10 row-class action labels (Promote-to-base, Promote-to-plugin, Stay-workspace-local, Author-time-fix, Author-tests, Defer, Deprecate, Promote-with-deprecation-pointer, Fold-into-existing).

- **AC.PROMOTE.4 — Walk-workspace logic specified in SKILL body.**
  - SKILL body §"How the persona applies it" instructs: read `<workspace>/.claude/skills/` (use Anthropic's `Read`/`ls` primitives); for each subdirectory containing a `SKILL.md`, treat as a candidate; per candidate, compute the 3-signal evaluation; render a structured markdown table to a status file at `<workspace>/.scratch/claude-output/skill-promotion-review-<date>.md` and surface a summary line in chat.
  - Body explicitly handles the empty-workspace case: "If `<workspace>/.claude/skills/` is empty or absent, surface 'no workspace-local SKILLs found; auto-skill-capture has not produced candidates yet' and exit cleanly."
  - Fence component: `plugins/dev-sdlc/`.
  - Test: `test_AC_PROMOTE_4_walk_workspace_logic.py` — body mentions reading `.claude/skills/`; body mentions the empty-workspace case + exit-cleanly behavior; body mentions producing a structured table at the canonical scratch path.

- **AC.PROMOTE.5 — Owner-ratification via PM batch API one-at-a-time per Decision Q.**
  - SKILL body §"How the persona applies it" instructs: for each non-stay-workspace-local candidate, call `PMRuntime.enqueue_decision(question_text, provenance=f"skill-promotion-review:{skill_name}")` + `surface_next_questions_batch(n=1)` + await `record_response` before moving on.
  - Question text: "Promote `<skill_name>` to `<target>`? (1) No (default) (2) Yes — author tests + run amendment cycle (3) Defer to next review."
  - Body disclaims bundled-question shape; PM blocks per-candidate.
  - Test: `test_AC_PROMOTE_5_owner_ratification.py` — body mentions `enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response` + default-to-no + bundled-question disclaimer.

- **AC.PROMOTE.6 — Author-tests-for-promotions sub-flow per layered-skills §4.3 step 4.**
  - On owner-Y AND candidate Tests=NEEDS-TESTS (no test file under `plugins/<target>/tests/test_AC_SKILLS_*`), persona dispatches sub-agent for the AC-shaped test (frontmatter parse + body non-empty + key-terms presence per `test_AC_SKILLS_DSDLC1_*_skill_present.py` precedent). Dispatch follows `dispatch-brief-authoring` shape.
  - Test: `test_AC_PROMOTE_6_author_tests_subflow.py` — body mentions sub-agent dispatch + structural-test convention + test-file path convention.

- **AC.PROMOTE.7 — Land-in-target via amendment cycle (composes with `loam-amend-cycle` SKILL).**
  - Once tests are authored, invoke `loam-amend-cycle` SKILL. Graduation-specific source-edit: (1) move SKILL.md from `<workspace>/.claude/skills/<name>/` to target plugin's `skills/<name>/` (HARNESS-GENERAL → `plugins/loam-skills/skills/`; DEV-SPECIFIC → `plugins/dev-sdlc/skills/`); (2) include additional package files in the move; (3) commit as `feat(<plugin>): promote <skill_name> from workspace-local`; (4) `loam amend apply` + seal per the cycle SKILL.
  - Body explicitly delegates: "do NOT re-implement the amendment ladder."
  - Test: `test_AC_PROMOTE_7_amendment_cycle_composition.py` — body mentions `loam-amend-cycle` SKILL + move + feat-commit + apply + seal sequence.

- **AC.PROMOTE.8 — Remove workspace-local copy post-promotion.**
  - After graduation seals, replace `<workspace>/.claude/skills/<name>/SKILL.md` with single-line `pointer.md`: `"This skill graduated to <target-plugin>/skills/<name>/ at <commit-SHA>; auto-discovery now loads it from the plugin."`. Original SKILL.md deleted (no duplicate auto-load).
  - Body disclaims: "do NOT leave the workspace-local SKILL.md in place; Anthropic discovery would auto-load both copies."
  - Test: `test_AC_PROMOTE_8_remove_workspace_local.py` — body mentions delete + pointer.md replacement + duplicate-auto-load disclaimer.

- **AC.PROMOTE.9 — Demotion path per layered-skills §4.4.**
  - SKILL body §"How the persona applies it" includes §"Demotion path" sub-section: persona surfaces "skill X has fired N times since promotion at `<commit-SHA>`; demote or retire?". On demote: corrective amendment cycle moves SKILL.md back to workspace-local; on retire: deletes entirely. Commit as `feat(<plugin>): demote <skill_name>` or `feat(<plugin>): retire <skill_name>`.
  - Body explicitly states: "demotion is rare; treated as explicit visible amendment; mirror the M5 multi-signal conflict-resolution discipline when ruling demote-vs-retire."
  - Test: `test_AC_PROMOTE_9_demotion_path.py` — body mentions "demote" + "retire" + corrective amendment + rare/explicit framing.

- **AC.PROMOTE.10 — Quarterly-review trigger via on-demand `/skill-promotion-review` (MVP fallback).**
  - SKILL body §"When to use" enumerates two triggers: **on-demand** (`/skill-promotion-review` invocation by the owner; or persona auto-recognition of trigger phrases like "review my workspace skills" / "what skills should I promote" via Anthropic's native description-match) — primary; **owner-self-discipline 90-day cadence** — the SKILL body documents this as a recommendation (every 90 days, owner runs `/skill-promotion-review`); the SKILL itself surfaces "it's been >90 days since the last `<workspace>/.scratch/claude-output/skill-promotion-review-*.md` artefact" if invoked AND the workspace has prior reviews. NO auto-fire from `framework/scope-of-work/` at MVP.
  - Body explicitly disclaims: "automatic quarterly auto-fire via scope-of-work is deferred to v0.2.x. Cycle 2 ships on-demand-only with cadence as owner-self-discipline."
  - Fence component: `plugins/dev-sdlc/`. (No edits to `framework/scope-of-work/`.)
  - Test: `test_AC_PROMOTE_10_quarterly_trigger.py` — body mentions both the on-demand trigger and the 90-day owner-self-discipline framing; body mentions the v0.2.x deferral of auto-fire.

- **AC.PROMOTE.11 — Component-level tests against synthetic workspace-local SKILL fixtures (3+ shapes).**
  - Fixtures under `plugins/dev-sdlc/tests/fixtures/skill-promotion-review/`:
    - `synthetic-skills/well-formed-harness-general/` — a workspace-local SKILL with valid frontmatter + 6-section body + body mentions universal concepts (translation / channels) → expected category=HARNESS-GENERAL, quality=PASS, conflict=NO-CONFLICT, recommendation=Promote-to-base.
    - `synthetic-skills/well-formed-dev-specific/` — a workspace-local SKILL with valid frontmatter + 6-section body + body mentions loam-amend / plan-before-code → expected category=DEV-SPECIFIC, quality=PASS, conflict=NO-CONFLICT, recommendation=Promote-to-plugin.
    - `synthetic-skills/duplicate-of-existing/` — a workspace-local SKILL whose description-keywords overlap >70% with an existing dev-sdlc SKILL (e.g., a workspace-local "amend-runner" overlapping `loam-amend-cycle`) → expected category=DEV-SPECIFIC, quality=PASS, conflict=DUPLICATE, recommendation=Deprecate.
    - `synthetic-skills/quality-fail/` — a workspace-local SKILL with malformed frontmatter (missing description) OR body missing a required section → expected quality=FAIL, recommendation=Author-time-fix.
  - Test: `test_AC_PROMOTE_11_synthetic_fixtures.py` — assert each fixture exists; assert each fixture's SKILL.md has the expected shape (this is a fixture-validation test, not an algorithm-execution test, since the algorithm lives in the SKILL body the persona reads).
  - Body of the SKILL itself references these fixtures by path so a session-fresh persona can use them as worked examples when reviewing real workspace SKILLs.
  - Fence component: `plugins/dev-sdlc/`.

- **AC.PROMOTE.12 — Discoverable in canonical pos-v2.**
  - The SKILL is invokable via `/skill-promotion-review` (Anthropic's native filesystem-discovery mechanism + the v0.1.7 Cycle 3 layered-skill discovery at `bcf699a`).
  - The SKILL appears in the discovered-skills listing produced by the layered-skill-discovery harness (per v0.1.7 Cycle 3 AC.LSK.* tests).
  - Fence component: `plugins/dev-sdlc/`.
  - Test: `test_AC_PROMOTE_12_discoverable.py` — assert the SKILL.md is present at the canonical path; assert the layered-skill-discovery harness (or its test fixture) lists the SKILL when run against `plugins/dev-sdlc/skills/`. (Concrete check: parse `plugins/dev-sdlc/skills/` directory, assert `skill-promotion-review/SKILL.md` is in the discovered set.)

---

## §4 — Component & file layout

**PRIMARY scope:** `plugins/dev-sdlc/skills/skill-promotion-review/` (NEW SKILL package; sealed-content remains under `plugins/dev-sdlc/`'s existing fence).

**TERTIARY admission:** `plugins/dev-sdlc/tests/` (new structural tests + fixtures, additive; existing tests unchanged).

### Existing paths (extend in-place; sealed-content unchanged)

- `plugins/dev-sdlc/tests/` — extend with new test files per AC; existing 12 SKILL-present tests unchanged.

### New paths (this cycle)

SKILL package (under `plugins/dev-sdlc/skills/skill-promotion-review/`):

- `SKILL.md` — frontmatter (description-only, ≤1536 chars, no `name`) + 6-section body. Estimated body length: ~250–320 lines (matches average across 12 sealed dev-sdlc SKILLs at HEAD). Body sections:
  - **What this skill captures.** The 3-signal MVP (Categorization + Quality + Conflict primary; Reusability + Tests + Usage secondary non-blocking) + the 10-row decision matrix + the 6-step graduation workflow + the demotion path.
  - **When to use.** On-demand (`/skill-promotion-review` invocation; persona auto-recognition); owner-self-discipline 90-day cadence (NOT auto-fire at MVP).
  - **How the persona applies it.** 7-step walk: (1) verify WD; (2) walk `<workspace>/.claude/skills/`; (3) per-candidate 3-signal evaluation against the matrix; (4) render structured table to scratch; (5) surface each non-trivial candidate one-at-a-time via PM batch API with default-to-no framing; (6) on owner-Y, dispatch sub-agent for tests if NEEDS-TESTS, then invoke `loam-amend-cycle`; (7) post-seal, replace workspace-local SKILL.md with pointer.md.
  - **Graceful degradation.** When raw Claude Code without loam-amend tooling: collapse to manual git-cycle (move + commit + push as a single change); the 3-signal evaluation + decision matrix + PM-mediation pieces still apply; the M5 multi-signal conflict-resolution discipline still applies for ambiguous-categorisation cases.
  - **Composition.** Lists composing SKILLs by name: `loam-amend-cycle`, `audit-finding-triage`, `owner-decision-summary`, `dispatch-brief-authoring`, `dispatch-with-gates`, `plan-before-code-author`. Lists composing feedback memories: `feedback_subagent_odd_violation_halt`, `feedback_principle_conflict_resolution_multi_signal`, `feedback_no_amend_in_agent_dispatches`.
  - **Out of scope.** Auto-promotion without owner ratification (never on roadmap); demotion-by-disuse-trigger (v0.2.x); cross-workspace skill sharing (not on roadmap); 6-signal full evaluation (v0.2.x); auto-fire quarterly trigger via scope-of-work (v0.2.x).

Tests (under `plugins/dev-sdlc/tests/`):

- `test_AC_PROMOTE_1_skill_package.py` — frontmatter validity + 6-section body presence.
- `test_AC_PROMOTE_2_three_signal_mvp.py` — body mentions all 3 primary signals + secondary-non-blocking framing.
- `test_AC_PROMOTE_3_decision_matrix.py` — body contains markdown table with 10 row-class labels.
- `test_AC_PROMOTE_4_walk_workspace_logic.py` — body mentions walk-workspace + empty-workspace handling + scratch-output path.
- `test_AC_PROMOTE_5_owner_ratification.py` — body mentions PM batch API (n=1) + default-to-no framing.
- `test_AC_PROMOTE_6_author_tests_subflow.py` — body mentions sub-agent dispatch for tests + structural-test convention.
- `test_AC_PROMOTE_7_amendment_cycle_composition.py` — body mentions `loam-amend-cycle` SKILL + move + feat + apply + seal sequence.
- `test_AC_PROMOTE_8_remove_workspace_local.py` — body mentions delete + pointer.md replacement + duplicate-auto-load disclaimer.
- `test_AC_PROMOTE_9_demotion_path.py` — body mentions demote/retire + corrective amendment + rare/explicit framing.
- `test_AC_PROMOTE_10_quarterly_trigger.py` — body mentions on-demand + 90-day self-discipline + v0.2.x auto-fire deferral.
- `test_AC_PROMOTE_11_synthetic_fixtures.py` — fixture-validation test for 4 fixtures.
- `test_AC_PROMOTE_12_discoverable.py` — directory-scan asserts SKILL is in `plugins/dev-sdlc/skills/`.

Fixtures (under `plugins/dev-sdlc/tests/fixtures/skill-promotion-review/synthetic-skills/`):

- `well-formed-harness-general/SKILL.md` — minimal valid SKILL describing a universal harness pattern (e.g., a translation-discipline-flavoured candidate); ~30–50 lines.
- `well-formed-dev-specific/SKILL.md` — minimal valid SKILL describing a dev-flavoured pattern mentioning loam-amend / plan-before-code; ~30–50 lines.
- `duplicate-of-existing/SKILL.md` — minimal SKILL with description-keywords overlapping `loam-amend-cycle`; ~30–50 lines.
- `quality-fail/SKILL.md` — malformed SKILL (missing frontmatter description OR missing required body section); ~10–30 lines.

### Smoke dimensions (per master plan §3 Cycle 2)

- **D1 (cold-state)** ✓ — fresh workspace + synthetic skills under `<workspace>/.claude/skills/` → `/skill-promotion-review` invocation → walk → 3-signal evaluation per candidate → structured table → ratification → graduation amendment cycle. Verified by `test_AC_PROMOTE_1_*` through `test_AC_PROMOTE_12_*` collectively + a meta-walk dispatched by the build agent post-seal as part of the cycle's HARD-smoke (master plan Cycle 3).
- **D2 (steady-state)** ✓ — re-run on a workspace where one SKILL graduated previously: the SKILL recognises the pointer.md replacement (no double-evaluation) and skips graduated entries. Verified by `test_AC_PROMOTE_8_*` (pointer.md disclaimer) + `test_AC_PROMOTE_4_*` (walk-workspace logic mentions handling pointer.md as "already-graduated, skip").
- **D5 (cross-session)** ✓ — promoted SKILL discoverable via Anthropic's filesystem-discovery in the next session. Verified by `test_AC_PROMOTE_12_*` (directory-scan); actual cross-session behavior verified during master plan Cycle 3 HARD smoke.
- **D6 (telemetry-floor)** ✓ — owner ratification audit-trail: each PM enqueue + record_response writes to the per-project-pm audit log per Decision P (existing v0.1.7 Cycle 4 surface; Cycle 2 inherits). Verified structurally — Cycle 2 does NOT modify per-project-pm; the existing audit-log shape covers ratification events.
- **D3 (restart)** ✓ inherited — mid-review `kill -TERM` is recoverable from the PM's existing decision-queue state (a queued-but-unanswered question persists across kill); on restart, persona re-invokes `/skill-promotion-review` and PM surfaces the pending question. Verified structurally.
- **D4 (reboot)** inherited from filesystem persistence of the PM's decision-queue + the SKILL's stateless body.

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.1 Cycle 2 BUILD dispatch — Promotion rubric mechanism

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Authority: build the 12 AC.PROMOTE.* family per sub-plan-doc §3. Single-component fence on plugins/dev-sdlc/skills/skill-promotion-review/. Tertiary admission: plugins/dev-sdlc/tests/ (new structural tests + fixtures only; existing tests unchanged).

Principles to apply at turn-start:
  AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / OUTPUT-TO-DISK / WD-IN-DISPATCHES / NO --amend / NO push / NO FALSE FAULT / PRINCIPLE-APPLICATION DISCIPLINE.

Quality bar (Luke directive 2026-05-04): every AC ships complete + tested. SKILL body covers the FULL ritual (not stub). 3-signal MVP intentional (not 6-signal half-implemented). Decision matrix complete (all 10 row classes). Owner-default-to-no per Decision G. Quarterly trigger composes cleanly via on-demand + 90-day self-discipline (NO scope-of-work auto-fire at MVP). Tests cover all 12 AC concerns. THE Eric ship — no partial features.

Source pointers (READ FIRST):
  - sub-plan-doc (THIS file's predecessor) at docs/plans/v0-2-1-cycle-2-promotion-rubric.md
  - master plan §3 Cycle 2 + §4 Cycle 2 dispatch brief at docs/plans/v0-2-1-master-plan.md
  - layered-skills §4 (lines 261-323) at docs/plans/layered-skill-story-research-2026-05-04.md
  - Decisions L + G + Q at parent docs/plans/eric-final-delivery-plan-2026-05-04.md §3
  - v0.1.7 Cycle 3 layered-skill discovery at bcf699a
  - v0.1.7 Cycle 4 PM batch API at 122a7c8 (framework/per-project-pm/runtime.py: enqueue_decision @ line 240; surface_next_questions_batch @ line 313; record_response @ line 405)
  - v0.1.8 Cycle 5 + v0.1.9 Cycle 3 SKILLs precedent: 12 sealed skills under plugins/dev-sdlc/skills/
  - 9 universal-tier skills under plugins/loam-skills/skills/
  - `loam-amend-cycle` SKILL at plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md (compose-target for AC.PROMOTE.7)
  - SKILL test convention at plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_1_loam_amend_cycle_skill_present.py (template for AC.PROMOTE.1)
  - v0.2.1 Cycle 1 sealed at apply f6b5047 / seal 55640b1
  - smoke discipline at plugins/dev-sdlc/docs/smoke-test-discipline.md

Fence + ACs + smoke + AI-time + out-of-scope: per sub-plan-doc §3 + §4.

Halt triggers — enumerated at sub-plan-doc §6 + below; halt-and-surface, do NOT silently work around:
  - WD drifts to pos3.
  - Cycle 1 not sealed at HEAD predecessor (pre-flight: HEAD includes 4c4a1d3 master plan §9 backfill).
  - PM-side edits needed (any framework/per-project-pm/ surface change).
  - framework/scope-of-work/ extension turns out to be required (master plan halt-trigger; on-demand fallback is the locked path).
  - SKILL frontmatter convention diverges from sealed-precedent shape (description-only, ≤1536 chars, no `name`).
  - SKILL body misses any of the 6 required sections (What/When/How/Graceful/Composition/Out-of-scope).
  - Decision matrix table misses any of the 10 row classes from layered-skills §4.2.
  - Synthetic fixtures cannot exercise the named signal-evaluation paths (Quality FAIL, Conflict DUPLICATE, Categorization HARNESS-GENERAL/DEV-SPECIFIC).
  - Cycle wall-clock >5 h with no progress.
  - ODD §2.5 violations in surrounding code OR master plan itself.
  - >3 escalations needed.

Bookkeeping:
  - pos-amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit on apply: feat(dev-sdlc): v0.2.1 Cycle 2 — Promotion rubric mechanism.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §9 per-cycle SHA backfill row updates with apply + seal SHAs.

Model rationale: (none — Sonnet default).
```

---

## §6 — Honest doubts (F2 RF on this Cycle 2 decomposition)

The places this plan-doc is least confident.

### 6.1 — Quarterly-trigger via scope-of-work integration may be trivial after build agent inspects the API

Plan-doc commits to on-demand-only at MVP per master plan halt-trigger. *Mitigation:* build agent does a pre-flight read of `framework/scope-of-work/src/` to confirm there is no existing "calendar-trigger" or "schedule-by-cadence" surface. If a 5-minute integration turns out feasible (e.g., a `ScopeSpec` with a `reversibility_class=fully_reversible` + a `90d` budget axis + a "calendar-elapsed" escalation trigger), build agent surfaces a halt-and-RF — Cycle 2 may quietly upgrade to auto-fire. Conservative path remains the locked default.

### 6.2 — Conflict-detection description-keyword-overlap heuristic is fuzzy

The 70% threshold is method-level. *Mitigation:* `synthetic-skills/duplicate-of-existing/` fixture exercises the threshold; build agent picks the threshold value within the SKILL body; halt-and-surface only if the heuristic mis-categorises any fixture.

### 6.3 — Categorization keyword-allowlist may misclassify edge cases

A workspace-local SKILL describing both translation-discipline AND loam-amend would split between HARNESS-GENERAL + DEV-SPECIFIC. *Mitigation:* SKILL body explicitly handles ambiguous-categorisation by halting + surfacing to owner ("ambiguous category for `<skill_name>`; classify as (1) HARNESS-GENERAL (2) DEV-SPECIFIC (3) PROJECT-SPECIFIC"); never silent miscategorisation.

### 6.4 — Synthetic fixture coverage is structural, not algorithmic

The signal-evaluation algorithm lives in the SKILL body the persona reads, NOT in a Python function the test executes. AC.PROMOTE.11 ships fixture-validation tests rather than execute-and-assert tests. *Mitigation:* per-design — SKILL is a workflow body, not a Python harness; master plan Cycle 3 HARD smoke validates the algorithm end-to-end.

### 6.5 — 90-day timestamp lookup risks pulling in scope-of-work

*Mitigation:* timestamp lookup uses filesystem mtime on `<workspace>/.scratch/claude-output/skill-promotion-review-*.md` artefacts (no scope-of-work read); SKILL body documents this pattern.

### 6.6 — Cycle 1 onboarding context dependency

Cycle 1 sealed Q6 auto-skill-capture opt-in. Workspaces with Q6=N will be empty for Cycle 2 review. *Mitigation:* SKILL body §"When to use" mentions the dependency: "if your workspace has `enable_auto_skill_capture: false`, this SKILL has nothing to evaluate; consider re-running `loam onboard`."

### 6.7 — Cycle wall-clock band 4–8 h optimistic/pessimistic

Body authoring + 12 tests + 4 fixtures. SKILL authoring well-rehearsed at 12 sealed precedents. *Mitigation:* halt-trigger at 5 h with no progress; AI-time rubric calibration logged on completion.

### 6.8 — Test-file granularity matches AC count exactly (12 tests, no integration test)

Cycle 1 used 15 + 1 integration + 1 meta. Cycle 2 collapses to 12 structural tests; HARD smoke at master plan Cycle 3 IS the integration. *Mitigation:* per-design — SKILL is workflow-shaped, no orchestrator code to integration-test.

### 6.9 — Conflict-detection requires reading every existing SKILL's description

Per-evaluation cost: 21 file reads per candidate. *Mitigation:* trivially fast via Anthropic's `Read`; SKILL body documents the cost explicitly.

### 6.10 — AC.PROMOTE.11 interpretation as structural-only

AC.PROMOTE.11 master plan text mentions "covering signal-evaluation + decision-matrix + PM ratification flow." Structural tests AC.PROMOTE.2/3/4/5 cover those *in the SKILL body*; AC.PROMOTE.11 covers fixture existence + correctness. *Mitigation:* if owner prefers literal "execute-and-assert" interpretation, halt-and-surface — but structural matches the SKILL-as-workflow-body design + 12 sealed-SKILL precedent. Build agent halts + RF on interpretation difference.

---

## §7 — Method-decision register (Cycle-2-specific)

| Decision | Choice | Rationale |
|---|---|---|
| SKILL package path | `plugins/dev-sdlc/skills/skill-promotion-review/` | Master plan §3 Cycle 2 fence; dev-scoped per three-tier gating. |
| SKILL frontmatter shape | `description`-only (≤1536 chars), no `name` field | Mirrors 21 sealed SKILL precedents (12 dev-sdlc + 9 universal). |
| SKILL body section ordering | What / When / How / Graceful degradation / Composition / Out of scope | Verified across 12 sealed dev-sdlc SKILLs. |
| Test convention | `test_AC_PROMOTE_<n>_<slug>.py` per AC; structural (frontmatter + body + key-terms) | Mirrors `test_AC_SKILLS_DSDLC1_*` shape from v0.1.8 Cycle 5. |
| Test count | 12 structural tests (one per AC); NO integration test | SKILL is workflow-shaped; HARD smoke at master plan Cycle 3 IS integration. |
| Fixture coverage | 4 synthetic-skill shapes (HARNESS-GENERAL well-formed / DEV-SPECIFIC well-formed / DUPLICATE / Quality FAIL) | Covers Categorization + Quality + Conflict primary signal paths. |
| 3-signal MVP primary gates | Categorization + Quality + Conflict | Decision L + master plan §9 + layered-skills §4.1. |
| Secondary signals framing | Reusability + Tests + Usage discussed in body, non-blocking | Decision L. Mitigates §6.x overall fuzziness. |
| Decision matrix row count | 10 (per layered-skills §4.2 verbatim) | Master plan AC.PROMOTE.3. |
| Owner-ratification API | PM batch API one-at-a-time (`enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response`) | Decision Q + v0.1.7 Cycle 4 `122a7c8`; zero PM-side edits. |
| Owner-ratification default | Default-to-no per Decision G | Mirrors Eric Decision I. |
| Question framing | "Promote `<skill_name>` to `<target>`? (1) No (default) (2) Yes — author tests + run amendment cycle (3) Defer to next review." | Default-to-no explicit + matches PM batch API multi-choice shape. |
| Quarterly-trigger MVP | On-demand `/skill-promotion-review` only; 90-day cadence as owner-self-discipline; auto-fire deferred to v0.2.x | Master plan halt-trigger; mitigates §6.1. |
| 90-day timestamp lookup | Filesystem mtime on `<workspace>/.scratch/claude-output/skill-promotion-review-*.md` | Avoids scope-of-work read; mitigates §6.5. |
| Graduation amendment cycle | Delegate wholesale to `loam-amend-cycle` SKILL | Composition over re-implementation; mitigates ladder duplication. |
| Workspace-local removal post-graduation | Replace SKILL.md with single-line pointer.md | Avoids duplicate auto-load (Anthropic discovery). |
| Demotion path framing | Rare/explicit; corrective amendment cycle; mirrors Decision F | Matches layered-skills §4.4. |
| Conflict-detection literal-name match | Walk `plugins/dev-sdlc/skills/` + `plugins/loam-skills/skills/` for exact name match first | Cheap fast-path before the keyword-overlap heuristic. |
| Conflict-detection keyword-overlap heuristic | Description-keyword overlap >70% triggers candidate-DUPLICATE for owner ratification | Mitigates §6.2; threshold is method-level, builder picks. |
| Categorization keyword-allowlist | HARNESS-GENERAL = universal concepts only; DEV-SPECIFIC = mentions loam-amend / plan-before-code / sealed-component / dispatch-brief; PROJECT-SPECIFIC = mentions workspace business-domain identifiers | Mitigates §6.3; halt-and-surface on ambiguous. |
| Quality-evaluation criteria | Frontmatter validity + 6-section body + key-term presence (mirrors `test_AC_SKILLS_DSDLC1_*` checks) | Reuses sealed-precedent test shape; consistent. |
| Empty-workspace handling | Surface "no workspace-local SKILLs found" + exit cleanly | Per AC.PROMOTE.4; no false-positive promotions. |
| Status-output path | `<workspace>/.scratch/claude-output/skill-promotion-review-<date>.md` | Mirrors odd-extractor + onboarding scratch-path convention. |
| Audit-log inheritance | PM batch API's existing audit-log shape covers ratification events; Cycle 2 adds NO new audit-log surface | Per-project-pm v0.1.7 Cycle 4 shape; SOC-2 floor inherited. |
| Body length target | ~250–320 lines | Average across 12 sealed dev-sdlc SKILLs; consistent surface. |
| Body inclusion of fixture references | Body mentions fixture paths so persona can use as worked examples | Mitigates fixture-validation-only critique (§6.10) — body teaches the algorithm; fixtures are reference instances. |

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-2 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/plans/v0-2-1-master-plan.md`). Cycle 1 method decisions at `docs/plans/v0-2-1-cycle-1-eric-onboarding-hardening.md` §7.

### Commit SHAs

- Amendment commit: `c48aa686ee696555e1b810d4f64279055f892e3c` —
  `chore(amend): v0-2-1-cycle-2-promotion-rubric manifest+apply — dev-sdlc BASELINE+sidecar bump to c01f50e`
- Seal commit: `298172e9a99d73ad807074c81289407677a396ed` —
  `chore(seals): v0-2-1-cycle-2-promotion-rubric — dev-sdlc at c48aa68`

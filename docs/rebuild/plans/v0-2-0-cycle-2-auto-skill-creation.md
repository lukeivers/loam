# v0.2.0 Cycle 2 — Persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.0 master plan `7c0f87b`. Cycle 1 sealed at `6fef2f1` (apply `faff84e`). v0.1.9 SHIPPED-locally at `9022df1`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-2-0-master-plan.md` §3 Cycle 2 + §4 Cycle 2 dispatch brief.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-0-cycle-2-status-2026-05-04.md`.

**Quality bar (load-bearing):** "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses." — Luke 2026-05-04. The auto-creation MVP is the **Eric-patterns-captured** half of v0.2.0; the persona detects three named triggers, drafts SKILL.md, gates on user-ratification via PM, and on `Y` writes the file to the Anthropic-native discovery path. Three triggers ship complete (3-of-6 lock); user-ratification gate is structural defence against silent skill-write; cool-down + budget + hard-cap defend against fatigue + bloat. If any trigger ships partial we halt and surface.

---

## §1 — Outcome shape (the "why")

v0.2.0 Cycle 2 ships the **persona-driven skill-capture MVP** — a discipline-shaped (not runtime-detector-shaped) mechanism that lets the persona detect a recurring pattern, draft a workspace-local SKILL.md, surface a one-line ratification question through PM, and on user `Y` write the SKILL.md to `<workspace>/.claude/skills/<name>/SKILL.md` (Anthropic-native discovery path verified at v0.1.7 Cycle 3 `bcf699a`). The mechanism is universal-tier (any loam user; not gated on dev-mode) per Luke's 2026-05-04 universal-scope clarification.

**The shape (six artefacts in a single-component fence + co-shipping fence-extension on workspace-bootstrap):**

1. **`skill-capture-proposal` SKILL** at `plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` — codifies the persona's auto-capture workflow. Frontmatter `description` ≤1536 chars; body the standard 6-section shape (What captures / When to use / How the persona applies it / Graceful degradation / Composition / Out of scope). Section content names the 3 MVP triggers, the proposal-draft-ratify workflow, the user-ratification gate, and the audit-log discipline.
2. **Three trigger detectors** as discipline embedded in the SKILL body — explicit-request (phrase-list match), repeated-invocation (same multi-step procedure 3+ times within a session), ask-and-answer (user asks the persona how to do X; persona answers; user does X; pattern is captured-as-skill candidate). MVP detectors do NOT require a runtime daemon — the persona reads them from the SKILL when the SKILL auto-loads.
3. **`enable_auto_skill_capture` workspace-config flag** in `framework/workspace-bootstrap/manifest.py` — boolean, default `false`, parses + validates with the same fail-closed shape used for `safety_profile` (v0.1.6 Cycle 1 precedent). When `false`, the SKILL's "When to use" gate explicitly turns the persona off (graceful degradation: persona simply doesn't propose).
4. **Capture workflow** in the SKILL body — persona detects trigger → drafts SKILL.md to `<workspace>/.scratch/claude-output/skill-draft-<slug>.md` → presents to user via PM (single question via existing `PMRuntime.enqueue_decision` + one-question-at-a-time per v0.1.7 Cycle 4) → user ratifies (Y/N/R) → on Y, persona moves the draft to `<workspace>/.claude/skills/<slug>/SKILL.md`; on R, iterates; on N, audit-logs + 14-day cool-down.
5. **Design note** at `docs/design/auto-skill-capture-shape.md` — explains the universal-tier scope, the trigger philosophy, the user-ratifies-not-persona-decides framing, the cool-down + budget + hard-cap discipline, the v0.2.x trigger expansion forward path.
6. **Audit-log entries** for every capture event — every trigger fire (detected) + every proposal (drafted) + every ratification (Y/N/R) writes one entry per the SOC-2 audit-trail floor. The SKILL body names the audit-log shape; `framework/per-project-pm/`'s existing audit-log primitive carries the ratification entries via the standard `surface_question` + `record_response` path. Per-trigger-fire entries write to `<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml` (component-local; mirrors per-project-pm's audit-log shape).

**Cycle 2's release-note promise:** with `enable_auto_skill_capture: true`, when the user explicitly says "remember this" or asks the same procedural question 3+ times in a session, the persona drafts a workspace-local SKILL.md, surfaces a one-line ratification question through PM, and on `Y` writes the SKILL.md so Claude Code's native discovery auto-loads it on the next relevant turn. With the flag at default `false`, no proposals fire (graceful degradation: persona behaves identically to pre-Cycle-2). Three triggers complete; deferred 3 named in the design note's v0.2.x roadmap.

**Discipline-shaped vs runtime-shaped (Lens 4 confidence note):** Cycle 2 ships the SKILL.md as the persona's discipline reference, NOT a Python runtime detector. Trigger detection happens in-loop when the persona's reasoning matches the SKILL's "When to use" clauses. This mirrors `dispatch-with-gates`, `scope-decompose`, `session-handoff` — all reference SKILLs that codify discipline rather than wire up a Python daemon. M-FBM episode-store reads (master plan §7.3 risk) are deferred via this choice — Triggers 2 (repeated-invocation) and 3 (ask-and-answer) detect within-session via the persona's own conversation memory, not via M-FBM API calls. This honors Lens 1 (lean on Claude's session-memory primitive) and Lens 4 (HIGH-confidence shape — no novel detector code).

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The auto-skill-capture mechanism composes on top of existing primitives rather than re-implementing:

- **Anthropic's SKILL.md schema + Anthropic-native discovery.** The persona writes to `<workspace>/.claude/skills/<slug>/SKILL.md`; Claude Code's native filesystem-walk auto-loads it on next relevant turn. No `/load-skill` API exists (per layered-skill research §1.4); registration IS the file write. v0.1.7 Cycle 3 `bcf699a` already verified workspace-local discovery works.
- **Claude's `Write` tool.** The persona materializes the SKILL.md via the standard `Write` tool — no new capture API.
- **`framework/per-project-pm/`'s ratification primitives (v0.1.7 Cycle 4 `122a7c8`).** `PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)` (one-question-at-a-time per Decision Q + AC.QSURF.1) + `record_response` is the entire ratification surface. Cycle 2 makes ZERO PM-side edits; the persona uses the existing batch API verbatim.
- **`framework/workspace-bootstrap/manifest.py`'s pattern for boolean flags.** `safety_profile` (v0.1.6 Cycle 1) is the reference shape for how new manifest fields land — frozenset of legal values, fail-closed `MissingConfigError` on invalid values, default literal, `Manifest` dataclass field. `enable_auto_skill_capture` follows the exact same shape (boolean default false; legal values `True`/`False`).
- **Existing 8 SKILLs at `plugins/loam-skills/skills/`.** The 6-section body shape (What captures / When to use / How / Graceful degradation / Composition / Out of scope) is verified-working across all 8 sealed SKILLs; `skill-capture-proposal` adopts the same shape verbatim.
- **`docs/design/`'s authored-doc convention.** v0.1.7 Cycle 3 published `docs/design/layered-skill-architecture.md`; Cycle 2 publishes `docs/design/auto-skill-capture-shape.md` to the same surface.
- **PM audit-log primitive (`audit-log/<YYYY-MM-DD>-<NNNN>.yaml`).** The skill-capture audit-log under `<workspace>/.loam/skill-capture/audit-log/` mirrors this exact shape. Cycle 2 documents the format in the SKILL body; the persona writes entries via `Write` (no helper module needed for MVP).

The required research question — **"What Claude capability does this lean on or extend?"** — answer: every load-bearing primitive is composed (SKILL discovery from Anthropic, Write tool from Claude, ratification from per-project-pm, manifest schema from workspace-bootstrap, body-shape from existing loam-skills, audit shape from per-project-pm). Cycle 2 ships four artefacts (SKILL package + manifest field + design note + tests) that wire these primitives together for the auto-capture use case.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the user no longer has to hand-craft SKILL.md files — they say "remember this" (or repeat the same procedure 3 times) and the persona drafts the SKILL, surfaces it for ratification, and writes it on `Y`. Natural-language intent ("capture this pattern so we don't redo it") translates to AI-effective execution ("draft → PM → ratify → write → auto-load"). Pass.
- **Harness test:** the persona-side discipline is now invokable from any loam-driven workflow — Eric's onboarding, Luke's loam-of-loam, a hypothetical writer's research workspace — by enabling the flag. The persona reads the SKILL when relevant; no per-workspace re-derivation. Pass — the SKILL is a reusable harness primitive.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§9) + acceptance smoke (§7). Method (which phrase-list for explicit-request, which similarity heuristic for repeated-invocation, which Q&A-overlap heuristic for ask-and-answer) stays the persona's call within the constraints (3 triggers complete, structural ratification gate, 14-day cool-down, 3/week budget, 20-skill hard-cap).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: the deliverable is well-precedented (8 sealed SKILLs use the same body shape; v0.1.7 Cycle 3 verified workspace-local discovery; v0.1.6 Cycle 1 is the reference for boolean manifest fields). Tight scope: extension to `plugins/loam-skills/skills/`, additive field on `Manifest`, new design-note file, AC-shaped tests. Halt-and-surface if any named primitive turns out unimplementable.

Outcome confidence is **MEDIUM** for the trigger-detection precision: master plan §7.2 + §7.3 name this as the residual risk. Cycle 2's response is to ship the triggers as **persona-side discipline** rather than runtime-detector code. The SKILL body names the heuristic (explicit-request: phrase-list match including "remember this", "make this a thing", "let's codify this", "capture this", "save this as a skill"; repeated-invocation: same multi-step tool-call sequence ≥3 times in a session, ≥70% structural overlap; ask-and-answer: same shape of question + same answer text in 3+ user-persona exchanges). The persona applies these heuristics in-loop reading its own session memory; no Python detector to under/over-fit.

Outcome confidence is **HIGH** for the ratification surface: PM batch API + `enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response` is verified-working at v0.1.7 Cycle 4.

Outcome confidence is **HIGH** for the workspace-config flag: identical shape to `safety_profile`.

### Lens 5 — Swarming

Single-component fence under `plugins/loam-skills/` (PRIMARY) + co-shipping `framework/workspace-bootstrap/` extension (manifest field). Within the cycle, decomposition options:

- (a) one artefact per concern (SKILL.md authored separately from manifest-flag separately from design-note separately from tests) — natural decomposition; each with its own AC test.
- (b) collapse SKILL + design-note authoring into one pass (both prose; co-author) — denser but tightly coupled in subject matter.

The builder picks **(a)** at AC granularity (per-AC tests) but **(b)** at authoring stride (SKILL body and design note share content; co-authoring keeps them aligned). `max_planner_depth: 1` (no sub-planners). Two-component fence (loam-skills primary + workspace-bootstrap secondary) is intentional — the manifest flag must co-ship with the SKILL it gates; splitting them across cycles would ship a SKILL nobody can enable. No further decomposition adds value.

---

## §3 — Two-component fence (primary + secondary co-shipping)

**PRIMARY scope:** `plugins/loam-skills/` (the existing loam-skills plugin's sealed fence; the new SKILL package + extended tests land under it).

**SECONDARY co-shipping scope:** `framework/workspace-bootstrap/` (the manifest gets one new boolean field with the same shape as `safety_profile`).

**TERTIARY admission:** `docs/design/` (universal_paths admission for the authored design note).

This is a **two-component fence**. Both components must seal in the same `loam amend apply` to keep the gate working — a SKILL nobody can enable is half-assed. Per-cycle plan-doc convention is single-component fence; this cycle's deliberate exception is master-plan-locked at §3 Cycle 2 fence ("PRIMARY `plugins/loam-skills/`" + "Compose-points: `framework/workspace-bootstrap/` (config flag — likely thin extension)") and the Lens 5 audit above.

**Existing paths (extend in-place; sealed-content unchanged):**

- `plugins/loam-skills/tests/test_AC_LSK_1_skill_packages_present.py` — extend `EXPECTED_SKILLS` list from 8 to 9 (additive — adds `skill-capture-proposal` to the parametrize set; existing 8 unchanged).
- `plugins/loam-skills/tests/test_AC_LSK_2_frontmatter_well_formed.py` — same extension (additive).
- `plugins/loam-skills/tests/test_AC_LSK_3_body_content_shape.py` — same extension (additive).
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — add new field `enable_auto_skill_capture: bool = False` to `Manifest` dataclass; add validation in `load_manifest` (additive — fail-closed on invalid type).

**New paths (this cycle):**

- `plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` — the new SKILL package.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_1_skill_package.py` — SKILL.md presence + structural validation (description-trigger phrases for 3 triggers; body 6-section shape; description ≤1536 chars; named loam pattern reference).
- `plugins/loam-skills/tests/test_AC_SKILLCAP_2_explicit_request_trigger.py` — body names explicit-request trigger + phrase-list + workflow.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_3_repeated_invocation_trigger.py` — body names repeated-invocation trigger + ≥3-times threshold + workflow.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_4_ask_and_answer_trigger.py` — body names ask-and-answer trigger + 3+ exchanges + workflow.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_5_proposal_draft_workflow.py` — body names draft path (`<workspace>/.scratch/claude-output/skill-draft-<slug>.md`), 6-section template requirement, evidence header.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_6_pm_ratification_gate.py` — body names PM enqueue path, single-question shape, Y/N/R response semantics, write-on-Y, file-move semantics to `<workspace>/.claude/skills/<slug>/SKILL.md`.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_8_cooldown_semantics.py` — body names 14-day cool-down on N response + per-trigger-pattern suppression.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_9_per_week_budget.py` — body names ≤3 proposals/week per workspace + roll-over semantics.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_10_hard_cap.py` — body names 20-skill hard-cap + promotion-rubric forward pointer.
- `plugins/loam-skills/tests/test_AC_SKILLCAP_11_design_note_present.py` — `docs/design/auto-skill-capture-shape.md` exists + has required sections (Architecture / Triggers / Workflow / Cool-down + budget + hard-cap / Failure modes / Composition / Forward path).
- `plugins/loam-skills/tests/test_AC_SKILLCAP_12_audit_log_shape.py` — body names audit-log entry shape (`<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`) + named event-kinds (`skill_capture_trigger_fired` / `skill_capture_proposal_drafted` / `skill_capture_ratified` / `skill_capture_rejected` / `skill_capture_revised` / `skill_capture_cooldown_active`).
- `framework/workspace-bootstrap/tests/test_AC_SKILLCAP_7_enable_flag_default_false.py` — `Manifest.enable_auto_skill_capture` defaults to `False`; legal values `True`/`False`; non-bool fails-closed via `MissingConfigError`; existing fields unaffected.
- `framework/workspace-bootstrap/tests/test_AC_SKILLCAP_7_enable_flag_field_pinned.py` — pin the field shape so accidental widening (e.g., string `enabled`/`disabled`) gets caught.
- `docs/design/auto-skill-capture-shape.md` — the authored design note.

**No PM-side edits.** Master plan §3 Cycle 2 says "compose-points include `framework/per-project-pm/` (ratification via existing v0.1.7 Cycle 4 PM API; no PM-side edits expected)." Cycle 2 commits to that — no new batch-type, no schema change, no API edit. The persona uses the existing batch API verbatim.

---

## §4 — AC family — `AC.SKILLCAP.*` (locked)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.SKILLCAP.1 — `skill-capture-proposal` SKILL package present + well-formed.**
  - File at `plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` exists; valid YAML frontmatter; `description` ≤1536 chars; body non-empty; directory name kebab-case ≤64 chars.
  - Frontmatter `description` carries trigger-phrase clause (one of: `use when`, `use this`, `before`, `after`, `when ` per existing `WHEN_CLAUSE_MARKERS`).
  - Body has all 6 required sections (case-insensitive substring match): `## what this skill captures`, `## when to use`, `## how the persona applies it`, `## graceful degradation`, `## composition`, `## out of scope`.
  - Body references at least one named loam pattern (CLAUDE.md, F3, F4, ODD, M-FBM, M5, FIDRAFT, Lens 1/2/3, loam).
  - Graceful-degradation section names raw-Claude-Code path explicitly ("claude code" or "raw claude").
  - Test: extends `test_AC_LSK_1_skill_packages_present.py` parametrize set from 8 to 9; new file `test_AC_SKILLCAP_1_skill_package.py` adds the trigger-phrase + body-section + loam-pattern + graceful-degradation checks specific to this SKILL.

- **AC.SKILLCAP.2 — Trigger 1: explicit-request detection (named in SKILL body).**
  - Body's "When to use" or "How the persona applies it" section names the explicit-request trigger explicitly (substring `explicit request` or `explicit-request`).
  - Body names a phrase-list with at least 3 example phrases. Required examples: `"remember this"`, `"make this a thing"` (or close variant: `"make this a skill"`), `"let's codify this"` OR `"capture this as a skill"`.
  - Body names "On match → proposal-draft mode immediately" or equivalent semantic (substring containing `immediately` near the explicit-request section).
  - Test: parses body; locates the explicit-request section; asserts ≥3 phrase-list entries + immediate-draft semantic.

- **AC.SKILLCAP.3 — Trigger 2: repeated-invocation detection (named in SKILL body).**
  - Body names the repeated-invocation trigger (substring `repeated invocation` or `repeated-invocation`).
  - Body names threshold: same multi-step procedure ≥3 times within a session window.
  - Body names matching heuristic: tool-call sequence + structural overlap (≥70% threshold OR equivalent semantic).
  - Body explicitly states this is **session-scoped** (within-session conversation memory; NOT M-FBM episode-store reads — defers M-FBM dependency to v0.2.x per master plan §7.3).
  - Test: locates the repeated-invocation section; asserts ≥3 threshold + structural-overlap heuristic + session-scoped framing.

- **AC.SKILLCAP.4 — Trigger 3: ask-and-answer pattern detection (named in SKILL body).**
  - Body names the ask-and-answer trigger (substring `ask and answer` or `ask-and-answer`).
  - Body names threshold: same shape of question 3+ times within a session AND answer text stabilizes (substring or equivalent semantic).
  - Body explicitly states this is especially valuable for non-dev users (mirrors layered-skill research §3.2 #5 framing).
  - Body explicitly states this is **session-scoped** (M-FBM read deferred to v0.2.x).
  - Test: locates the ask-and-answer section; asserts threshold + non-dev-emphasis + session-scoped framing.

- **AC.SKILLCAP.5 — Proposal draft workflow.**
  - Body names the draft path: `<workspace>/.scratch/claude-output/skill-draft-<slug>.md` (or workspace-relative equivalent).
  - Body names the 6-section template the draft must follow (matches the body shape every existing SKILL uses).
  - Body names a "draft header" requirement: which trigger fired + evidence (e.g., 3 instances + timestamps or in-session reference points).
  - Body explicitly states the draft path is `.scratch/`-based (NOT yet in `.claude/skills/`) so the persona doesn't accidentally bypass ratification.
  - Test: locates the draft-workflow section; asserts the path pattern + 6-section reference + evidence-header semantic.

- **AC.SKILLCAP.6 — User-ratification via PM (Y/N/R gate).**
  - Body names the ratification surface as PM (`PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)`).
  - Body names the one-line decision-question shape: e.g., `"I noticed [pattern] N times. Capture as workspace-local skill? Y / N / R(evise)."`
  - Body names Y/N/R semantics: Y → file move from `.scratch/` draft to `<workspace>/.claude/skills/<slug>/SKILL.md`; R → iterate on user feedback; N → audit-log + 14-day cool-down (per AC.SKILLCAP.8).
  - Body explicitly references the one-question-at-a-time discipline (Decision Q + AC.QSURF.1 from v0.1.7 Cycle 4).
  - Test: locates the ratification section; asserts PM-API references + Y/N/R semantics + one-question-at-a-time reference.

- **AC.SKILLCAP.7 — `enable_auto_skill_capture` workspace-config flag.**
  - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`'s `Manifest` dataclass gains field `enable_auto_skill_capture: bool = False`.
  - `load_manifest` reads `raw.get("enable_auto_skill_capture")`; absent → default `False`; present-and-bool → use that value; present-and-not-bool → raise `MissingConfigError` (matches `safety_profile`'s fail-closed shape).
  - Field is documented in the module docstring's `bootstrap.yaml` example (additive, near `safety_profile` block).
  - SKILL body's "When to use" section explicitly names this flag: when `false` (default), the persona MUST NOT propose; when `true`, the persona MAY propose per the trigger heuristics.
  - Test 1 (`test_AC_SKILLCAP_7_enable_flag_default_false.py`): manifest without the field → `Manifest.enable_auto_skill_capture is False`; manifest with `true` → `True`; manifest with `false` → `False`; manifest with `enabled` (string) → `MissingConfigError`; manifest with `1` (int) → `MissingConfigError`.
  - Test 2 (`test_AC_SKILLCAP_7_enable_flag_field_pinned.py`): the `Manifest` dataclass has the field; default value is `False` (boolean literal, not a string).

- **AC.SKILLCAP.8 — Cool-down semantics (14 days post-rejection).**
  - Body names the cool-down: 14 days after `N` response, the same trigger-pattern is suppressed.
  - Body names the cool-down state path: `<workspace>/.loam/skill-capture/cooldowns.yaml` (mirrors per-project-pm's per-component state convention).
  - Body documents the cool-down state shape (YAML mapping: `{trigger_pattern_hash: rejection_iso_timestamp}` or equivalent named structure).
  - Body documents the cool-down check: persona reads the file before proposing; on hit and `(now - rejection_ts) < 14d`, no-op.
  - Test: locates the cool-down section; asserts 14-day duration + path + state-shape + check-semantic.

- **AC.SKILLCAP.9 — Per-week budget (≤3 proposals/week per workspace).**
  - Body names the budget: ≤3 proposals/workspace/rolling-7-day-window. Configurable via `skill_capture_weekly_budget` (forward-pointer; not implemented at MVP — default 3 is hardcoded).
  - Body names the budget state path: `<workspace>/.loam/skill-capture/budget.yaml`.
  - Body documents budget state shape (YAML list of timestamped proposal events with rolling window calculation).
  - Body names the gate: budget exceeded → no-op until rolling 7-day window resets (next-oldest entry ages out).
  - Test: locates the budget section; asserts ≤3 + 7-day-window + path + reset-semantic.

- **AC.SKILLCAP.10 — Hard-cap (20 workspace-local SKILLs).**
  - Body names the hard-cap: 20 SKILLs at `<workspace>/.claude/skills/`.
  - Body names the gate: cap reached → no-op + persona surfaces a note about promotion via `skill-promotion-review` (forward-pointer to v0.2.1).
  - Body names the count source: walking `<workspace>/.claude/skills/<*>/SKILL.md` (filesystem-discovery; same as Anthropic's discovery primitive).
  - Test: locates the hard-cap section; asserts 20 + workspace-local-path + promotion-pointer.

- **AC.SKILLCAP.11 — Design note present.**
  - File at `docs/design/auto-skill-capture-shape.md` exists.
  - Has required sections (case-insensitive substring match): `## architecture`, `## triggers`, `## workflow`, `## cool-down`, `## failure modes`, `## composition`, `## forward path`.
  - Names the universal-tier framing (substring `universal` near `architecture` or top-level intro).
  - Names the user-ratifies-not-persona-decides framing (substring `user-ratif` or `ratification gate` near workflow).
  - Names the v0.2.x deferred trigger expansion (substring `CLAUDE.md drift` + `memory-recall` + `hook-trigger` in the forward path section).
  - Names Eric's use case (substring `Eric` once — concrete grounding for the universal-tier framing).
  - Test: parses the file; asserts presence + section list + framing markers.

- **AC.SKILLCAP.12 — Audit-log shape.**
  - SKILL body names the audit-log directory: `<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`.
  - SKILL body names the event-kinds: `skill_capture_trigger_fired`, `skill_capture_proposal_drafted`, `skill_capture_ratified`, `skill_capture_rejected`, `skill_capture_revised`, `skill_capture_cooldown_active`.
  - SKILL body names the SOC-2 audit-trail floor (Decision P) as the discipline source.
  - Body documents that ratification audit entries are ALSO recorded in PM's audit-log via the standard `surface_question` + `record_response` path (cross-reference, not duplication).
  - Test: locates the audit-log section; asserts directory + 6 event-kinds + SOC-2 reference.

- **AC.SKILLCAP.13 — End-to-end smoke against fixture (component-level).**
  - Component-level smoke (Cycle-level): the SKILL.md is well-formed enough that the persona reading it can apply the workflow without referring back to this plan-doc — i.e., the SKILL is self-contained instruction.
  - Verified by: a parametrized "self-contained" check that reads the SKILL.md body and asserts every named workflow step (detect → draft path → PM enqueue → Y-write to `.claude/skills/<slug>/`) is present + named with concrete file paths.
  - Release-level smoke (master plan §5): exercised at v0.2.0 release-level SOFT smoke gate after Cycle 2 seals; covered separately in this plan-doc §7's release-level smoke notes.
  - Test: `test_AC_SKILLCAP_13_self_contained.py` reads the SKILL.md; locates each required workflow step; asserts named paths + named PM API calls + named ratification semantics.

---

## §5 — Surfaces (decisions made by this plan-doc, beyond bare ACs)

**Surface #1 — Triggers ship as persona-side discipline, NOT runtime-detector code.** Master plan §3 Cycle 2 + §7.2 + §7.3 named the precision risk for triggers 2 (repeated-invocation) and 3 (ask-and-answer). This plan-doc commits to encoding them in the SKILL body — the persona detects in-loop reading its own session memory, NOT via a Python detector reading M-FBM. Defers the M-FBM dependency to v0.2.x. Honors Lens 1 (Claude session-memory primitive) and Lens 4 (HIGH-confidence shape).

**Surface #2 — Trigger 2 + Trigger 3 are session-scoped at MVP.** Detection happens within a single session's conversation memory. Cross-session trigger detection (e.g., "user asked this 3 times across 5 sessions") requires M-FBM episode-store reads and is the v0.2.x deferred path. The SKILL body explicitly names this scope; the design note's forward-path section names cross-session detection as the v0.2.x extension.

**Surface #3 — `enable_auto_skill_capture` is a top-level manifest field, NOT nested.** Mirrors `safety_profile`'s flat shape. A future settings-bag refactor (deferred) could nest both under a `policies:` mapping; for MVP, flat is precedented and minimal.

**Surface #4 — Cool-down + budget + hard-cap state files live at `<workspace>/.loam/skill-capture/`.** Component-local namespace (not under `<workspace>/.loam/pms/`). Persona writes via `Write` tool; no helper module needed for MVP. State-file shapes documented in SKILL body + design note. v0.2.x may extract into a `loam_skill_capture` Python module if utility emerges.

**Surface #5 — Audit-log entries live at `<workspace>/.loam/skill-capture/audit-log/`.** Persona writes via `Write` tool. Mirrors the per-project-pm audit-log filename convention (`<YYYY-MM-DD>-<NNNN>.yaml`) so a future audit aggregator can walk both with the same parser. Six event-kinds named in SKILL body (per AC.SKILLCAP.12).

**Surface #6 — Design note co-ships with the SKILL.** Design note + SKILL share content; co-authoring ensures alignment (per Lens 5 audit). Design note is the architectural reference for v0.2.1 promotion-rubric authoring + v0.2.x trigger expansion.

**Surface #7 — Tests live in TWO test directories** (one per fence component). `plugins/loam-skills/tests/` for SKILL-related ACs; `framework/workspace-bootstrap/tests/` for the manifest-flag ACs. Both directories have existing `test_no_sealed_amendments.py` seal-fence tests — they enforce the diff-window discipline at seal time.

**Surface #8 — `loam.yaml` (manifest) co-evolution is documented but unmodified.** No workspace's actual `bootstrap.yaml` is touched by this cycle. The flag is added to the `Manifest` dataclass (default false), the loader honors it, and any workspace that wants to opt in adds the line manually. Pos-v2's own `bootstrap.yaml` (under `workspace/.pos/`) does NOT auto-flip — it stays at default `false` per layered-skill research §3.6 Decision E.

**Surface #9 — Existing `EXPECTED_SKILLS` list in 3 test files is the same list (drift defence).** All three test files (`test_AC_LSK_1`, `test_AC_LSK_2`, `test_AC_LSK_3`) define `EXPECTED_SKILLS = [...]` with the same contents. Cycle 2 extends each in the same edit pass (8 → 9, adding `skill-capture-proposal`). A drift-defence subtask: a one-line check confirming all three lists are equal would be a v0.2.x cleanup; for Cycle 2, the visual diff at code-review is sufficient.

**Surface #10 — The 3 deferred triggers (CLAUDE.md drift, memory-recall hit, hook-trigger pattern) are named in the design note's forward path, NOT in the SKILL body.** Keeps the SKILL focused on what ships. Design note carries the v0.2.x roadmap.

---

## §6 — Method-decision register (cycle-specific)

Per the §14 lint requirement. Per-cycle method decisions; master-plan-level decisions live at master plan §9.

| Decision | Choice | Rationale |
|---|---|---|
| Triggers ship as discipline (SKILL body) vs runtime detector (Python module) | Discipline-only at MVP | Defers M-FBM API dependency; honors Lens 1 (Claude session-memory primitive); HIGH-confidence shape (mirrors 8 existing reference SKILLs); v0.2.x can layer in a Python detector if utility emerges. |
| Trigger session-scope (within-session vs cross-session) | Session-scoped at MVP | Detection in conversation memory; cross-session requires M-FBM reads (master plan §7.3 risk); v0.2.x extension. |
| Manifest field shape (flat vs nested) | Flat (top-level `enable_auto_skill_capture`) | Mirrors `safety_profile` precedent; minimal. |
| Manifest field default | `False` | Per layered-skill research §3.6 Decision E + master plan §3 Cycle 2; fresh workspace shouldn't auto-propose. |
| Cool-down storage | `<workspace>/.loam/skill-capture/cooldowns.yaml` | Component-local namespace; YAML matches per-project-pm convention. |
| Budget storage | `<workspace>/.loam/skill-capture/budget.yaml` | Same convention. |
| Audit-log storage | `<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml` | Mirrors per-project-pm filename convention; future aggregator parses both. |
| Audit-log writer | Persona via `Write` tool | No helper module at MVP; v0.2.x can extract `loam_skill_capture` if reuse pressure emerges. |
| Two-component fence (loam-skills + workspace-bootstrap) vs single-component | Two-component (intentional exception) | A SKILL nobody can enable is half-assed; flag must co-ship; master plan §3 Cycle 2 fence is locked. |
| Test extension shape (extend `EXPECTED_SKILLS` 8→9 vs new test file) | BOTH | Extend existing 3 LSK tests to validate new SKILL with the existing checks; new `test_AC_SKILLCAP_*` files for SKILLCAP-specific ACs. |
| Design note co-ship vs separate cycle | Co-ship | Lens 5 stopping-criterion: separate cycle would be coordination overhead. |
| Design note placement | `docs/design/auto-skill-capture-shape.md` | Mirrors `docs/design/layered-skill-architecture.md` precedent (v0.1.7 Cycle 3). |
| Trigger phrase examples | "remember this" + "make this a thing"/"make this a skill" + "let's codify this"/"capture this as a skill" | High-precision phrases per layered-skill research §3.2 #2; non-overlapping with normal request phrasing. |
| Smoke fixture | Component-level self-containment + release-level fixture-driven | Component-level: SKILL is self-contained instruction; release-level: master plan §5 covers fixture-driven end-to-end. |
| Dispatch model tier | Sonnet (default) | No model-rationale line per swarming-discipline. |

---

## §7 — Acceptance smoke (D1 / D2 / D5 / D6 — D3 / D4 inherited)

Cycle-level smoke against the SKILL artefact + manifest field. Release-level smoke at v0.2.0 release-level SOFT gate (master plan §5).

**D1 cold-state (component-level):** fresh checkout; pytest in `plugins/loam-skills/tests/` and `framework/workspace-bootstrap/tests/` both green. Verifies SKILL.md presence + body shape + manifest-field presence + default-false.

**D2 idempotency (component-level):** running pytest twice produces identical results (no side effects; no test pollution). Manifest reload: `load_manifest` on the same file twice produces equal `Manifest` objects.

**D3 restart:** n/a structurally — Cycle 2 ships static artefacts (SKILL.md + manifest field + design note); no long-running process.

**D4 reboot:** n/a structurally — filesystem state survives reboot trivially.

**D5 cross-session (most-load-bearing):** the SKILL is the persona's instruction reference; cross-session means "the SKILL auto-loads when the persona's reasoning matches its description." Verified at v0.1.7 Cycle 3 `bcf699a` for workspace-local SKILLs; this cycle's SKILL is base-loam (under `plugins/loam-skills/skills/`), so Anthropic-native plugin discovery applies. Component-level check: `/` menu exposes 9 SKILLs after Cycle 2 lands. Release-level check: master plan §5 D5 covers the workspace-local-write side (persona drafts → user ratifies → SKILL writes to `<workspace>/.claude/skills/` → next session auto-loads).

**D6 telemetry-floor:** SKILL body names 6 event-kinds + audit-log directory. Component-level test (AC.SKILLCAP.12) asserts the body documents them. Release-level smoke (master plan §5 D6) verifies one fires end-to-end.

**Halt-trigger from master plan + applied here:** Anthropic SKILL.md workspace-local discovery doesn't actually work post-write (verified at v0.1.7) → halt + surface. v0.1.7 Cycle 3 sealed `bcf699a` with a passing discovery test (`test_AC_LAYERED_2_skill_symlink_registration.py`); pre-flight check at build time confirms test still passes; otherwise halt.

**Full-suite green sweep:** pre-Cycle-2 `loam-skills` + `workspace-bootstrap` tests at HEAD `6fef2f1` all pass post-Cycle-2; halt + surface on any regression.

---

## §8 — Out-of-scope (explicit, what this cycle does NOT ship)

- **Cross-session trigger detection.** Triggers fire within-session at MVP; cross-session requires M-FBM API extension; v0.2.x.
- **Python runtime detector module.** Triggers ship as persona-side discipline; if utility emerges, a `loam_skill_capture` module lands at v0.2.x.
- **Promotion rubric for workspace-local → plugin / base.** Per master plan §3 Cycle 2; v0.2.1 deliverable.
- **Demotion path for retired skills.** v0.2.1 deliverable.
- **3 deferred triggers (CLAUDE.md drift, memory-recall hit, hook-trigger pattern).** Named in design note forward path; v0.2.x.
- **Mode 2 structured fill-in-blanks UI.** Per Decision D + layered-skill research §3.4; MVP uses Mode 1 (persona drafts; user reviews); v0.2.x.
- **Cross-workspace skill sharing.** Not on roadmap.
- **Eric onboarding hardening.** Per master plan §1 + parent §3; v0.2.1 deliverable.

---

## §9 — Halt triggers

- **WD drifts.** Confirm `pwd` at turn-start is `/Users/lukeivers/ivers-corp-pos-v2/`. If pos3 → halt.
- **Plan-doc not authored before code.** This plan-doc IS the plan-before-code; build proceeds only after plan-doc + manifest YAML commit. If a code-edit lands before plan-doc commit → halt.
- **Anthropic SKILL.md workspace-local discovery doesn't work post-write.** Pre-flight check: `pytest framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py` passes. If fail → halt + surface (v0.1.7 Cycle 3 broke).
- **`enable_auto_skill_capture` flag conflicts with existing manifest field.** Pre-flight check: `grep "enable_auto_skill_capture" framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` returns nothing. If hit → halt.
- **Three triggers can't all ship complete.** If any one trigger turns out incomplete (per AC requirements), halt + reframe (per Decision N's 3-of-6 lock; can't ship 2.5 of 3).
- **Two-component fence proves substantial cross-component churn.** If `framework/workspace-bootstrap/manifest.py` requires more than the additive field + validator + docstring update, halt + reframe.
- **PM extension turns out needed.** Per master plan §3 Cycle 2 halt-trigger + this plan's Surface #2: if the PM batch API can't carry the ratification question through `enqueue_decision` + `surface_next_questions_batch(n=1)` shape, halt + reframe.
- **Cycle exceeds 5 hours wall-clock.** Master plan halt-trigger.
- **ODD violations in surrounding code.** Subagent dispatches + this build agent halt on ODD violations.
- **>3 escalations needed to Luke.** Halt + describe.
- **Smoke fails post-build.** Component-level pytest red on any AC → halt + surface; full-suite sweep red on any pre-existing test → halt + surface.

---

## §10 — Bookkeeping (per master plan §4 Cycle 2 dispatch brief)

- **`loam amend apply`** (NOT `git commit --amend`). Schema v3 manifest. Single semantic commit (manifest+apply merged per AC.DPS1.6).
- **`loam amend seal --plan-doc <abs-path>`** for the deterministic seal commit (AC.DPS2.{1,4,6}).
- **Schema v3 fields exercised:** `plan_doc_ref` + `ac_count` + `smoke_outcome` at manifest level; cross-component sweep at seal time.
- **Components in manifest:**
  - `loam-skills` (PRIMARY) — `seal_test: plugins/loam-skills/tests/test_no_sealed_amendments.py`; `sidecar: plugins/loam-skills/tests/SEAL_COMMIT`.
  - `workspace-bootstrap` (SECONDARY) — `seal_test: framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`; `sidecar: framework/workspace-bootstrap/tests/SEAL_COMMIT`.
- **Universal admissions:** `docs/rebuild/plans/` + `docs/design/` + `CLAUDE.md` + `docs/odd-in-loam.md` + `docs/odd-methodology.md` + `docs/rebuild/STATE.md` (only the ones touched).
- **Post-seal commit** backfills this plan-doc's §14 + master plan §9 SHA backfill table per AC.D-sa.7 (`loam amend seal --plan-doc` does this automatically).
- **DO NOT push tags.** v0.2.0 release-level smoke (master plan §5) gates the SHIPPED rollup; tag push waits on Luke.
- **Master plan §9 backfill** with Cycle 2 SHAs (apply + seal) lands as a separate post-seal commit (NOT part of the seal commit).
- **Release-level rows backfill** (STATE.md + roadmap §8 + eric-final-delivery §2) lands ONLY AFTER release-level smoke green per master plan §5.

---

## §11 — Provenance trail

- v0.2.0 master plan: `docs/rebuild/plans/v0-2-0-master-plan.md` (committed `7c0f87b`).
- v0.2.0 Cycle 1 sub-plan: `docs/rebuild/plans/v0-2-0-cycle-1-continuous-watch.md` (sealed `6fef2f1`, apply `faff84e`).
- Layered-skill story research (auto-creation reference): `docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` §3 + §3.6 universal-tier.
- Eric synthesis (v0.2.0 row authority): `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.2.0.
- v0.1.7 layered-skill discovery (workspace-local SKILL discovery): `bcf699a`. Plan-doc `docs/rebuild/plans/v0-1-7-cycle-3-layered-skill-discovery.md`.
- v0.1.7 PM batch API (one-question-at-a-time + record_response): `122a7c8`. Plan-doc `docs/rebuild/plans/v0-1-7-cycle-4-one-question-pm-flow.md`.
- v0.1.6 production-safety (manifest field shape precedent): `3f1d237`. Plan-doc `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md`.
- 8 sealed SKILLs (body-shape verified-working): `f04e925` (v0.1.3 5-pack) + `88674cb` (v0.1.6 3-pack).
- Smoke-test discipline: `plugins/dev-sdlc/docs/smoke-test-discipline.md`.
- Schema v3 + seal-narrative compression: `019cfca` + `df3f50f`.
- Quality bar: Luke directive 2026-05-04 (parent §1).
- Universal-tier framing: layered-skill research §3.6 + Luke 2026-05-04 messages 9951+9953.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-2 method-level decisions are recorded at §6 above. The `## 14.` heading exists per AC.D-sa.7 lint requirement; content lives at §6 to avoid duplication. The `### Commit SHAs` subsection below is appended by `loam amend seal --plan-doc` post-seal per AC.D-sa.7.

### Commit SHAs

(populated by `loam amend seal --plan-doc` post-seal)

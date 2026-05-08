# v0.2.2 — ODD grounding propagation + dispatch-brief template hardening

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-05 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.1 SHIPPED rollup at `6d66a2e` (Eric ship paused per Luke 2026-05-05). ODD grounding lean doc at `d37c623`; verbose at `ffd9c95`. Master plan v0.2.2→v0.2.5 at `5974103`.

**Parent plan:** `docs/plans/odd-rebuild-master-plan-2026-05-05.md` §3 v0.2.2.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Status file (to be authored by build agent):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-2-grounding-propagation-status-2026-05-05.md`.

**Always-load grounding:** `docs/odd-llm-grounding.lean.md`. The build agent loads it FIRST and runs §self-checks on every output declared "objective," "AC," "constraint," or "capability."

---

## §1 — Outcome shape (the "why")

v0.2.2 ships the **structural foundation** for the v0.2.3 → v0.2.5 rebuild path: the lean ODD grounding prime auto-loads on every session-start (no discipline dependency), and the dispatch-brief template propagates the hardened propagation set to every sub-agent.

Without this foundation, every subsequent dispatch in the path will drift back to implementation-altitude on contact with the v0.1.8 substrate (the failure mode the lean doc exists to prevent). The work is structural — file additions + skill extension + manifest entries — not behavioral. The agent doing v0.2.3 work simply has the doc in `additionalContext` and the discipline references in the dispatch brief.

**Two AC families ship together** because they're tightly coupled: the corpus-load propagation puts the doc in context structurally; the dispatch-brief propagation ensures sub-agents inherit the load when invoked from a session that already has it. Decoupling would mean shipping AC.OGP.* and then re-opening the same files at v0.2.2.5 for AC.DBT.*.

**Fence reality:** plan-doc is plan-only; code lands in v0.2.2-build (separate dispatch). This plan-doc identifies fences and authors the build dispatch brief; no code edits in this commit.

---

## §2 — Lens checks

### Lens 1 — Claude-leverage-first

The grounding-propagation work composes on existing Claude Code primitives:

- **SessionStart hook surface** — `corpus_inline_session_start.py` already emits `additionalContext` via stdout per Anthropic's documented hook contract. v0.2.2 extends the static `_ALWAYS_LOAD` (or `_ON_DEMAND`) tuple, not the hook mechanism.
- **dev-mode-manifest selector** — `loam_mode.select_corpus` already partitions paths into NORMAL USE vs DEV MODE sets. v0.2.2 adds an entry to the existing `dev_only:` block.
- **A1 corpus-load sentinel** — `corpus_load_sentinel.compute_corpus_paths_required` already pulls from the manifest. v0.2.2 inherits the sentinel update for free; the new path appears in `corpus_paths_required` automatically.
- **`dispatch-brief-authoring` skill** — the canonical structural shape for sub-agent dispatches already exists at `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`. v0.2.2 extends the skill's "Principles to apply at turn-start" enumeration + adds the lean-grounding-load reference; does not re-implement the skill.

**Required research question — "What Claude capability does this lean on or extend?"** Answer: SessionStart hooks + the dev-mode-manifest selector + the corpus-load sentinel + the existing dispatch-brief skill. Every load-bearing primitive is in place; v0.2.2 is additive entries + skill extension.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** the persona's drift back to implementation-altitude is the documented v0.1.8 failure. Auto-loading the lean grounding doc reduces translation burden — the persona doesn't have to remember to load it, and sub-agents don't have to be reminded each dispatch. Pass.
- **Harness test:** the dispatch-brief template is an existing harness primitive every dev-mode dispatcher draws from. Adding propagated items to the template extends the toolkit (every future dispatch inherits the propagation set). Pass.

Both pass.

### Lens 3 — ODD authoring

§1 outcome shape + §3 named ACs + §6 halt triggers + §4 smoke dimensions. Method (which exact location in the inline hook gets the new entry; whether to extend the skill SKILL.md vs author a new sibling doc; specific propagation-line wording) stays the builder's call within constraints (auto-load is structural; manifest entry goes in `dev_only:`; sentinel reflects new entry; sub-agent inheritance verified by reading recent dispatches).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for AC.OGP.* shape: both corpus-load surfaces are well-mapped (manifest + inline-hook); the precedent (the `plugins/dev-sdlc/docs/odd-methodology.md` entry shipped pre-M6b.0) shows exactly what an auto-loaded ODD doc looks like. Tight scope: one manifest entry + one inline-hook tuple entry + one CLAUDE.dev.md reference.

Outcome confidence is **MEDIUM** for AC.DBT.* propagation mechanism. Six candidate items + an open question (memory rule vs template file vs skill extension vs CLAUDE.dev.md). The plan-doc commits to extending the existing `dispatch-brief-authoring` skill (rationale at §7) rather than authoring a new file — the skill is the verified-working canonical surface; extending it composes; authoring a new file forks the surface.

Outcome confidence is **MEDIUM-LOW** for AC.DBT.* structural verification. AC.DBT.7 (telemetry of dispatch briefs DO carry the propagated items) is genuinely hard to test structurally without a corpus of dispatch-brief artefacts. Plan-doc surfaces this honestly (§6 honest doubt 6.3) and commits to verifying-by-construction (test that the skill's SKILL.md contains the propagated items; do not attempt to verify across all historical dispatch briefs).

### Lens 5 — Swarming

Single-component fence on `plugins/dev-sdlc/` (PRIMARY for skill + manifest) + tertiary additive on `framework/hands-off-lifecycle/hooks/` (the inline hook tuple) + tertiary additive on `CLAUDE.dev.md` (universal-paths). Within the cycle, decomposition options:

- (a) one dispatch covers all three surfaces (manifest + inline hook + skill SKILL.md + CLAUDE.dev.md). Single-build agent.
- (b) split into two: AC.OGP.* (corpus-load wiring) as one dispatch; AC.DBT.* (skill extension) as a second dispatch.

The builder picks **(a)** — the surfaces are structurally tightly coupled (the skill propagates the lean-grounding load that the corpus-load wiring makes structural); splitting introduces only coordination overhead without tightening any subtask's scope. `max_planner_depth: 1`. No further decomposition adds value.

---

## §3 — AC enumeration — `AC.OGP.*` + `AC.DBT.*` (locked)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, every branch, every test maps to a named AC. Self-checks per `docs/odd-llm-grounding.lean.md` §self-checks run over each AC text below.

### AC.OGP.* family — ODD grounding propagation

- **AC.OGP.1 — Lean grounding doc auto-loads in DEV MODE corpus-required set.**
  - `docs/odd-llm-grounding.lean.md` is added to `plugins/dev-sdlc/dev-mode-manifest.yaml` `dev_only:` block (the section where the existing ODD docs live).
  - On session-start in a DEV MODE pos-v2 workspace, `compute_corpus_paths_required(workspace_root, "dev-mode")` returns a list that includes the new path.
  - Self-check pass: this is an OUTCOME (the doc enters the required set), implementation-swap survives (rewriting in any mechanism that reads a manifest still satisfies it), observable from outside (sentinel reflects the entry).
  - Fence component: `plugins/dev-sdlc/` (manifest is the data file; the consuming code in `framework/hands-off-lifecycle/` is unchanged).
  - Test: `test_AC_OGP_1_lean_grounding_in_required_set.py` — invoke `compute_corpus_paths_required` on a DEV MODE fixture; assert the lean grounding path is present.

- **AC.OGP.2 — Lean grounding doc inlined into `additionalContext` on DEV MODE session-start.**
  - `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py`'s `_ALWAYS_LOAD` (or `_ON_DEMAND`, builder's call) tuple includes `docs/odd-llm-grounding.lean.md`.
  - The build-agent picks the tier — RECOMMENDED `_ALWAYS_LOAD` (per master plan §3 v0.2.2 "auto-load before every ODD-shaped agent task"); if size budget pressure (the ~6.8k token current budget) makes inline emission expensive, falls back to `_ON_DEMAND` and surfaces the choice in §14.
  - On hook fire, the doc's content (or its pointer per `_ON_DEMAND` semantics) appears in stdout; Claude Code captures this as `additionalContext`.
  - Fence component: `framework/hands-off-lifecycle/`.
  - Test: `test_AC_OGP_2_lean_grounding_inlined.py` — synthetic SessionStart envelope; capture stdout; assert lean grounding content (or pointer) present in the rendered block.

- **AC.OGP.3 — `CLAUDE.dev.md` references the lean grounding doc as session-start required reading.**
  - `CLAUDE.dev.md`'s "Session-start discipline" bulleted list adds an explicit reference to `docs/odd-llm-grounding.lean.md` as load-FIRST (above the `odd-methodology.md` reference, since the lean doc is the prime + the methodology is the depth).
  - The reference text names the load-first ordering + the §self-checks discipline.
  - Fence component: universal-paths (`CLAUDE.dev.md` in dev-mode workspaces; rooted at workspace root).
  - Test: `test_AC_OGP_3_claudedev_references_lean_grounding.py` — string-match assertion; CLAUDE.dev.md contains the lean grounding path + the "load FIRST" semantics.

- **AC.OGP.4 — Pos-v2 itself is classified DEV mode (verification AC; no edit).**
  - The plan-doc commits that pos-v2's primary-persona contract resolves to DEV MODE via `loam_mode.compute_session_mode`. The build agent verifies pre-edit; halt + surface if pos-v2 is misclassified.
  - This is a structural sanity check — the ODD docs already live in `dev_only:` and load on session-start, so the classification is verified by the existing fact that ODD methodology auto-loads. AC.OGP.4 makes the verification explicit.
  - Fence component: verification only (no edit surface).
  - Test: `test_AC_OGP_4_pos_v2_dev_mode_classification.py` — invoke `workspace_mode(pos_v2_root)`; assert `"dev-mode"`.

### AC.DBT.* family — dispatch-brief template hardening

The 6 candidates from the brief are evaluated below; each is classified as **PROMOTE-TO-AC** (universal template-shaped) or **DISCIPLINE-NOTE** (situation-specific; lives in skill prose but not as a structural AC). The propagation mechanism for the promoted items is **extending `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md`** (rationale at §7 method-decision register).

- **AC.DBT.1 — `dispatch-brief-authoring` SKILL.md enumerates the propagated principle set.**
  - The SKILL.md "Principles to apply at turn-start" section (item 3 in the canonical structural shape) is extended to enumerate the propagated principles by name. The existing list (CHANNEL / AUTONOMY / F2 RF / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / WD-IN-DISPATCHES / etc.) gains the propagated items per below ACs.
  - Fence component: `plugins/dev-sdlc/skills/dispatch-brief-authoring/`.
  - Test: `test_AC_DBT_1_skill_principle_enumeration.py` — string-match assertion; SKILL.md contains each promoted principle name.

- **AC.DBT.2 — Lean ODD grounding load reference in the skill (PROMOTE).**
  - SKILL.md adds a load-first directive: "When work is ODD-shaped (extraction, ratification, plan-authoring, AC-tightening, gap-analysis), load `docs/odd-llm-grounding.lean.md` FIRST and run §self-checks on every output declared 'objective,' 'AC,' 'constraint,' or 'capability.'"
  - **Classification: PROMOTE.** Universal for ODD-shaped sub-agent work; the v0.2.3 → v0.2.5 path is entirely ODD-shaped, so every sub-agent in the path inherits the load.
  - The dispatcher-side rule: if the task is ODD-shaped, the dispatch brief carries the load directive in its "Principles to apply at turn-start" block. Non-ODD work omits.
  - Test: `test_AC_DBT_2_lean_grounding_in_skill.py` — string-match; SKILL.md contains the load directive + the ODD-shaped condition.

- **AC.DBT.3 — No-closing-line-permission-asks reference in the skill (PROMOTE).**
  - SKILL.md adds: "Sub-agent post-task reports must not close with 'want me to...' on in-scope authorized work. Recommendation IS the decision per `feedback_no_closing_line_permission_asks`."
  - **Classification: PROMOTE.** Universal — applies to every sub-agent dispatch; not ODD-specific.
  - Test: `test_AC_DBT_3_no_closing_line_in_skill.py` — string-match.

- **AC.DBT.4 — Specific-claims-verified reference in the skill (PROMOTE).**
  - SKILL.md adds: "Every fact in the post-task report (line counts, cost estimates, SHAs, durations, tool-call counts) is empirically verified OR explicitly marked as guess/estimate/band per `feedback_specific_claims_verified_or_marked_guess`."
  - **Classification: PROMOTE.** Universal — applies to every post-task report regardless of task shape.
  - Test: `test_AC_DBT_4_specific_claims_in_skill.py` — string-match.

- **AC.DBT.5 — Test-against-operational-objective-before-escalating reference in the skill (PROMOTE).**
  - SKILL.md adds: "Sub-agent runs the operational-objective test before treating any decision as dispatcher-escalation. State the operational objective; test if it implies a clear answer; if yes, decide autonomously; only escalate on critical-call / public-action / financial decisions per `feedback_test_against_operational_objective_before_escalating`."
  - **Classification: PROMOTE.** Universal — applies to every sub-agent's escalation/non-escalation calls.
  - Test: `test_AC_DBT_5_operational_objective_test_in_skill.py` — string-match.

- **AC.DBT.6 — No-false-fault-admission reference in the skill (PROMOTE).**
  - SKILL.md adds: "Sub-agent does not manufacture audit ✗ when no real miss occurred. Apply the four-test before writing ✗: (1) was upstream input clear? (2) over-anticipation? (3) ignored prior signals? (4) third-party-reviewer attribution? All no → ship forward without retroactive blame per `feedback_no_false_fault_admission`."
  - **Classification: PROMOTE.** Universal — applies to every audit-block output.
  - Test: `test_AC_DBT_6_no_false_fault_in_skill.py` — string-match.

- **AC.DBT.7 — Audit-block-when-meaningful reference in the skill (DISCIPLINE-NOTE not promoted to test-AC; surface as prose).**
  - SKILL.md mentions: "Apply minimal audit per `feedback_principle_application_front_load_and_audit` — surface ✓ on clean turns; surface ✗ + course-correction only on real misses."
  - **Classification: DISCIPLINE-NOTE (NOT promoted to a separate test-AC).** Rationale: this rule is BEHAVIORAL (governs how the post-task report shape looks), not STRUCTURAL (governs what gets emitted at all). AC.DBT.6 already pins the negative case (no false ✗); the positive case (when to surface ✓) is harder to structurally test (is it surfaced enough? too much? when?). The skill prose carries it; structural test would be over-engineering.
  - The discipline note IS still mentioned in the skill prose to keep the principle visible; it's just not gated by a separate AC. **One-line note in the skill suffices.**
  - Fence: same as AC.DBT.1 (skill prose).
  - Test: covered structurally by AC.DBT.1 (the skill enumerates it as a referenced principle); no separate test file.

### Smoke dimensions

Per master plan §3 v0.2.2 + smoke-test-discipline.

- **D1 (cold-state)** ✓ — fresh session-start in DEV MODE pos-v2 workspace; sentinel reflects new path; inline hook emits new content. Verified by `test_AC_OGP_1` + `test_AC_OGP_2`.
- **D2 (idempotent re-load)** ✓ — re-fire session-start; sentinel idempotent (existing-content check); inline emission deterministic. Verified by sentinel write contract (existing AC.SE.4 / amendment 73 idempotency tests cover this) + integration test re-fire.
- **D3 (restart)** n/a — no daemon process; session-start is one-shot per session.
- **D4 (reboot)** inherited from filesystem persistence; n/a structurally.
- **D5 (cross-session)** ✓ — post-`/clear`, the next session-start re-loads the doc structurally (the manifest + inline-hook entries are the load source-of-truth). Verified by integration test re-invocation across simulated session boundaries.
- **D6 (telemetry-floor)** ✓ — corpus-load sentinel emits an audit-log-equivalent entry per session (the sentinel itself IS the audit surface for "what corpus was required + what was loaded"). Verified by sentinel-content assertion in integration test.

---

## §4 — Component & file layout

**PRIMARY scope:** `plugins/dev-sdlc/` (manifest + skill).

**TERTIARY admissions:** `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` (additive tuple entry) + `CLAUDE.dev.md` (universal-paths admission).

### Existing paths (extend in-place; sealed-content unchanged)

- `plugins/dev-sdlc/dev-mode-manifest.yaml` — additive entry under `dev_only:` for `docs/odd-llm-grounding.lean.md`. Existing entries unchanged.
- `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` — additive entry to `_ALWAYS_LOAD` (recommended) or `_ON_DEMAND` (fallback if size pressure). Builder's call per AC.OGP.2.
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — extend the "Principles to apply at turn-start" section + composition section per AC.DBT.1 → AC.DBT.6.
- `CLAUDE.dev.md` — extend "Session-start discipline" list per AC.OGP.3.

### New paths (this cycle)

Tests (under `framework/hands-off-lifecycle/tests/` for AC.OGP.* + `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/` for AC.DBT.*):

- `framework/hands-off-lifecycle/tests/test_AC_OGP_1_lean_grounding_in_required_set.py`
- `framework/hands-off-lifecycle/tests/test_AC_OGP_2_lean_grounding_inlined.py`
- `framework/hands-off-lifecycle/tests/test_AC_OGP_3_claudedev_references_lean_grounding.py`
- `framework/hands-off-lifecycle/tests/test_AC_OGP_4_pos_v2_dev_mode_classification.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_1_skill_principle_enumeration.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_2_lean_grounding_in_skill.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_3_no_closing_line_in_skill.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_4_specific_claims_in_skill.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_5_operational_objective_test_in_skill.py`
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/test_AC_DBT_6_no_false_fault_in_skill.py`

The test directory under the skill may not exist; build agent creates per existing dev-sdlc skill conventions (or co-locates under `plugins/dev-sdlc/tests/` if that's the established home; halt + surface on path uncertainty).

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.2 BUILD dispatch — ODD grounding propagation + dispatch-brief template hardening

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Authority: build the AC.OGP.* (4 ACs) + AC.DBT.* (6 ACs; AC.DBT.7 is discipline-note prose only) families per sub-plan-doc §3. Single-component fence on plugins/dev-sdlc/ (PRIMARY). Tertiary admissions: framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py (additive tuple entry) + CLAUDE.dev.md (universal-paths).

Principles to apply at turn-start:
  CHANNEL — telegram-only for user-visible comms.
  AUTONOMY — make method-level calls within scope.
  F2 RUTHLESS FEEDBACK — surface every disagreement with the plan-doc + every place the brief is ambiguous.
  LOCKED-DESIGN-NOT-LICENSE — plan-doc ACs are the locked design; bad-outcome shapes get surfaced.
  PROMISES > IN-MOMENT JUDGMENT — finish the build + tests + commit fully.
  ODD §2.5 — every line of code/test maps to a named AC.
  OUTPUT-TO-DISK — status report to disk per output conventions.
  WD-IN-DISPATCHES — /Users/lukeivers/ivers-corp-pos-v2/ always.
  NO --amend, NO push, NO FALSE FAULT.
  TIGHT-VS-LOOSE SCOPE — fence + AC count + smoke dimensions are tight; specific edit shape is loose.
  NO CLOSING-LINE PERMISSION-ASKS — recommendation IS the decision; no "want me to..." closes.
  SPECIFIC-CLAIMS-VERIFIED — every fact in the post-task report verified or marked guess.
  LEAN-GROUNDING-LOAD — load docs/odd-llm-grounding.lean.md FIRST; run §self-checks on every AC text.

QUALITY BAR (Luke directive 2026-05-05): every AC ships complete + tested. Lean grounding doc auto-loads structurally (sentinel + inline). Skill SKILL.md contains every promoted reference (AC.DBT.1–6). pos-v2 DEV-MODE classification verified before any edit.

Source pointers (READ FIRST):
  - sub-plan-doc at docs/plans/v0-2-2-grounding-propagation.md (THIS file's predecessor)
  - master plan at docs/plans/odd-rebuild-master-plan-2026-05-05.md §3 v0.2.2
  - lean grounding doc at docs/odd-llm-grounding.lean.md (load FIRST)
  - verbose grounding doc at docs/odd-llm-grounding-derivation.md (depth as needed)
  - corpus-load sentinel at framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py
  - corpus-inline hook at framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py
  - dev-mode-manifest at plugins/dev-sdlc/dev-mode-manifest.yaml
  - dispatch-brief-authoring skill at plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md
  - CLAUDE.dev.md at workspace root

Sub-plan path: docs/plans/v0-2-2-grounding-propagation.md (this plan-doc).
Manifest path: docs/plans/v0-2-2-grounding-propagation.manifest.yaml.
Status file: /Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-2-grounding-propagation-status-2026-05-05.md.

Fence: plugins/dev-sdlc/ (PRIMARY) + tertiary additive on framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py + CLAUDE.dev.md.

Acceptance criteria: AC.OGP.1 → AC.OGP.4 + AC.DBT.1 → AC.DBT.6 (10 test-ACs total) + AC.DBT.7 prose-only. Per sub-plan-doc §3 + §4.

Smoke: D1 + D2 + D5 + D6 exercised; D3 + D4 n/a structurally. Per sub-plan-doc §3.

Halt triggers — enumerated at sub-plan-doc §6 + below:
  - WD drifts to pos3.
  - Corpus-load hook script structure doesn't accept simple list-append edit.
  - CLAUDE.dev.md / dev-mode-manifest reveal that pos-v2 isn't classified DEV MODE.
  - Skill SKILL.md edit > 100 lines added.
  - `_ALWAYS_LOAD` size budget pressure forces `_ON_DEMAND` fallback (decision documented in §14).
  - ODD §2.5 violations in surrounding code OR plan-doc itself.
  - >3 escalations needed.

Out of scope:
  - v0.2.3 extractor rebuild (next release).
  - SessionStart hook mechanism changes (use existing surfaces only).
  - Updating historical dispatch briefs to retroactively include the propagation set (forward-only; new dispatches inherit).

Bookkeeping:
  - loam amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit on apply: feat(grounding): v0.2.2 — ODD grounding propagation + dispatch-brief template hardening.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §3 v0.2.2 backfill row updates with apply + seal SHAs.

Reply contract:
  - Seal SHA + apply SHA + plan-doc SHA.
  - 10 ACs satisfied (4 OGP + 6 DBT).
  - Smoke outcome (D1 + D2 + D5 + D6 results).
  - Status file path.
  - Halt-and-surface findings (pos-v2 DEV MODE verified; size budget decision; etc.).

Model rationale: (none — Sonnet default).
```

---

## §6 — Honest doubts (F2 RF on this v0.2.2 decomposition)

The places this plan-doc is least confident.

### 6.1 — `_ALWAYS_LOAD` vs `_ON_DEMAND` tier choice for AC.OGP.2

The lean grounding doc is 72 lines / ~4-5k tokens (verified — `wc -l`). The current `_ALWAYS_LOAD` tier emits ~6.8k tokens (per the inline hook docstring) + the per-file ceiling is 50k chars (~12.5k tokens). The lean grounding doc fits comfortably under the per-file ceiling.

**However**, adding the doc to `_ALWAYS_LOAD` increases the always-emitted token cost by ~50-70%. The tradeoff:

- `_ALWAYS_LOAD` → doc enters context every DEV-MODE session (structural; the master plan's intent).
- `_ON_DEMAND` → pointer block + persona-loads-when-relevant. Lower baseline cost; but discipline-dependent (the failure mode this v0.2.2 exists to prevent).

*Resolution (recorded autonomously per AUTONOMY):* default to `_ALWAYS_LOAD`. The master plan §3 v0.2.2 explicitly says "auto-load before every ODD-shaped agent task"; `_ALWAYS_LOAD` is structural; `_ON_DEMAND` is discipline. Build agent surfaces the size delta in the status report; if Luke gates on cost, AC.OGP.2 supports the fallback to `_ON_DEMAND` without re-opening the plan-doc.

### 6.2 — AC.DBT.7 not promoted; review the call

AC.DBT.7 (audit-block-when-meaningful) was demoted to prose-only because the negative case is covered by AC.DBT.6 (no false fault) and the positive case is hard to structurally test. *Risk:* the prose may be skimmed and the discipline-rule effectively ignored. *Mitigation:* the AC.DBT.6 structural test pins the negative case (no manufactured ✗); the positive case is reinforced by `feedback_principle_application_front_load_and_audit` which sub-agents already see in their feedback memory load. The prose in SKILL.md is sufficient.

### 6.3 — AC.DBT.* structural verification is shallow

The AC.DBT.* tests are string-match assertions on SKILL.md. They verify the skill DOCUMENTS the propagated items; they do NOT verify that dispatchers ACTUALLY include the items in their dispatch briefs. *Risk:* skill says one thing; dispatchers do another. *Mitigation:* the skill is the canonical source the dispatcher copy-pastes from per the existing precedent; if dispatchers stop using the skill, the failure surfaces independently. Structural verification of "every dispatch brief in the wild contains the propagated set" would require a brief-corpus + a separate audit pass; that's a v0.2.x follow-on, not v0.2.2 scope.

### 6.4 — `loam_mode.select_corpus` may treat `dev_only:` entries as path-shaped

The dev-mode-manifest's `dev_only:` block accepts both `path:` and `glob:` entries. The lean grounding doc is at `docs/odd-llm-grounding.lean.md` — a single file — so a `path:` entry is correct. Build agent verifies the schema validation accepts the new entry; halt + surface on schema-fail.

### 6.5 — The skill's existing principle list may not have a clean insertion point

The current SKILL.md "Principles to apply at turn-start" section enumerates 10+ principles. AC.DBT.* adds 5 more to the enumeration. *Risk:* the section becomes unwieldy; principles drift from "always-applicable" to "sometimes-applicable" without clear demarcation. *Mitigation:* the build agent groups the additions under a "Propagated principles for sub-agents" sub-section if the section length crosses 30 lines; the structural shape stays intact, the readability improves.

### 6.6 — Test-file homes for AC.DBT.* are uncertain

The brief commits to `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/` for AC.DBT.* tests, but skill-co-located tests may not be the established convention in dev-sdlc. *Mitigation:* build agent verifies pre-edit by checking sibling skills (`plan-before-code-author`, `loam-amend-cycle`, etc.); if the convention is `plugins/dev-sdlc/tests/test_skill_*.py`, builder follows that; halt + surface only on path-uncertainty that's not resolvable by precedent.

### 6.7 — Wall-clock band

Master plan §3 v0.2.2 says 2-4 h AI-time. Plan-doc commits to that band: 4 manifest/hook/skill/CLAUDE.dev.md edits + 10 test files + verification = 30-50 tool calls; per the duration rubric (~0.1-0.15 min per call), that's 3-7.5 min build + verification. The 2-4 h band assumed broader scope; this scope is tighter. Honest revision: 30 min - 90 min wall-clock (midpoint 60 min). Build agent logs actuals on completion.

---

## §7 — Method-decision register (v0.2.2-specific)

| Decision | Choice | Rationale |
|---|---|---|
| Propagation mechanism for AC.DBT.* | Extend existing `dispatch-brief-authoring` SKILL.md | Skill is the verified-working canonical surface; extension composes; alternative (new file / memory rule / CLAUDE.dev.md) forks the surface. |
| Skill insertion location | "Principles to apply at turn-start" section + composition section | Existing structural shape; adds to the canonical principle enumeration. |
| AC.DBT.7 promotion | DISCIPLINE-NOTE only (not test-AC) | Behavioral, not structural; AC.DBT.6 covers negative case; positive case hard to test. |
| Lean grounding tier | `_ALWAYS_LOAD` (default); `_ON_DEMAND` fallback if size pressure | Master plan §3 v0.2.2 says "auto-load"; `_ALWAYS_LOAD` is structural. |
| Manifest entry shape | `path: docs/odd-llm-grounding.lean.md` under `dev_only:` | Single file → path entry; `dev_only:` matches existing ODD docs. |
| CLAUDE.dev.md insertion | Top of "Session-start discipline" bulleted list | Lean grounding is the prime; loads FIRST; methodology is depth-as-needed. |
| Test-file location for AC.OGP.* | `framework/hands-off-lifecycle/tests/` | Tests sentinel + inline-hook behavior; component-local. |
| Test-file location for AC.DBT.* | `plugins/dev-sdlc/skills/dispatch-brief-authoring/tests/` (default; verify precedent) | Skill-co-located; halt + surface if convention differs. |
| AC count | 10 (4 OGP + 6 DBT) + 1 prose-only (DBT.7) | Within Sonnet-tractable scope; under the 11+ AC threshold for an Opus dispatch. |
| Fence shape | Single-component PRIMARY (plugins/dev-sdlc/) + 2 tertiary additives | Mirrors v0.2.1 Cycle 1 precedent; minimal cross-component surface. |
| Universal-paths admissions | `docs/plans/` + `CLAUDE.dev.md` + the inline-hook file path | Per amendment #22 ruling #3 + Cycle 3 + v0.1.9 + v0.2.0 + v0.2.1 precedent. |
| AC.DBT.* structural verification depth | String-match on SKILL.md | Verifies the skill DOCUMENTS the propagation; cross-dispatch verification is v0.2.x follow-on. |

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

v0.2.2 method decisions at §7. Master-plan method decisions at master plan §7 (`docs/plans/odd-rebuild-master-plan-2026-05-05.md`).

### Commit SHAs

- Amendment commit: `ada74e195559b67803da8f5c0aaf2128016bac34` —
  `chore(amend): v0-2-2-grounding-propagation manifest+apply — dev-sdlc BASELINE+sidecar bump to da58ad8`
- Seal commit: `5eda09d28806741387aa145fa20644e0a682ce5d` —
  `chore(seals): v0-2-2-grounding-propagation — dev-sdlc at ada74e1`

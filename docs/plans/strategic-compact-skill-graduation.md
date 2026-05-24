# strategic-compact-skill-graduation — Graduate the compact/clear decision-heuristic memory rule to a discoverable loam SKILL

**Status:** plan-doc, plan-before-code, **RATIFIED 2026-05-24** per maintainer recommendation-bundle implicit-yes (Telegrams 12310 + 12311). All 4 named decisions (D-COMPACT.PATH / .BODY-SOURCE / .TRIGGER / .MEMORY-FATE) ratified per plan-author recommendation. Build dispatch awaits separate owner go-ahead. Authored 2026-05-24 by `loam-plan-author` subagent (Wave 1 ECC absorption; parallel-dispatched with security-hooks-bundle / token-defaults / README-restructure).
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent capture:** Master plan §3.1 P1 + §4 D-COMPACT.SKILL + §5 WI-1 in `docs/plans/drafts/everything-claude-code-absorption-master-plan.md`. Maintainer ruling D-COMPACT.SKILL ratified per Telegram 12301 ("B" = approve graduate).
**Source-of-substance:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_clear_decision_heuristic.md` (memory rule; 112 lines; stable since 2026-05-14).
**ECC reference (informative-not-load-bearing):** `https://github.com/affaan-m/everything-claude-code/tree/main/skills/strategic-compact` — sibling implementation of the same discipline; absorption is concept-level, not file-port.
**Predecessor (load-bearing for shape):** `docs/plans/sealed/loam-skills-start-project-discoverable.md` (recent SKILL-discoverability plan-doc exemplar; AC.SPDISC pattern mirrored for AC.COMPACT family below).
**Sibling SKILLs (load-bearing for composition):** `plugins/loam-skills/skills/precompact-hook/SKILL.md` (structural enforcement of state-protection-at-compact) — this graduation adds the DECISION-DISCIPLINE companion (when to compact at all) that precompact-hook references at line 58–60.
**Quality bar:** PATCH-class graduation; load-bearing structural addition (one new SKILL directory + frontmatter + body) + one outcome-altitude AC + three supporting ACs + backlink in the originating memory file (memory-becomes-index, SKILL-becomes-operative per `feedback_durable_capture_for_planned_work` graduation pattern).

---

## Principles applied this turn

- **PLAN-BEFORE-CODE** — load-bearing; no source touched. SKILL.md authoring is a build step covered by per-work-item dispatch, not this plan-author run.
- **AGENT-PROMPTS-SCOPE-ONLY** — this plan-doc names objectives + ACs + fence; method (SKILL body wording, frontmatter trigger language) is the builder's call.
- **ODD §2.5** — every section maps to a named objective in §1; defensive sections cut. Every AC ladders up to a named objective.
- **SCOPE-DESCRIPTIVE AC IDs** — AC.COMPACT.* (NOT AC.V0XX.* per `feedback_scope_descriptive_ac_ids`).
- **OUTCOME-ALTITUDE REQUIRED** — AC.COMPACT.S is the outcome-altitude AC per `feedback_test_outcome_altitude_required.md`; production discovery + invocation path with no pre-arranged state.
- **CLAIM-OR-CITE** — every claim cites a file path, doc section, or memory file; ECC source is informative-not-load-bearing (sibling implementation, not file-port).
- **OUTPUT-TO-DISK** — plan-doc lives on disk at canonical path; dispatcher gets inline summary + path.
- **PROMPT SCOPE ↔ CONFIDENCE (F4)** — tight scope: high confidence the outcome is "memory rule graduates to subdirectory-shape SKILL discoverable in fresh workspaces with backlink in original memory"; method (SKILL prose density, trigger-phrase list, ratification approach) loose-by-design.
- **LOCKED-DESIGN-NOT-LICENSE** — D-COMPACT.SKILL is locked (maintainer ratified); this plan executes; if the SKILL turns out noisy/dormant post-ship, revisit per the rule, not silently accept.
- **VERSION-NUMBERS-AT-RELEASE-TIME** — scope-descriptive slug, no v0.X.Y pre-allocation.
- **WD-IN-DISPATCHES** — confirmed canonical loam (`/Users/lukeivers/loam/`).
- **F2 RUTHLESS FEEDBACK** — §10 surfaces honest doubts (graduation-vs-status-quo gap, ECC-vs-loam content choice).
- **NO sub-agents** in this plan-authoring turn.

---

## §0. Executive summary + named decisions

### TL;DR (4 bullets)

1. **What ships:** a new auto-discoverable SKILL at `plugins/loam-skills/skills/strategic-compact/SKILL.md` (subdirectory shape per the v0.1.7 AC.LAYERED.2 contract — flat-file shapes are silently undiscovered per the start-project regression closed at amendment 25308cf). Body derives from `feedback_compact_clear_decision_heuristic.md` (the stable memory rule) — three options + cost profiles + decision rule + trigger conditions — with frontmatter that auto-loads when the persona detects context-pressure or owner-class compact/clear questions.
2. **What the memory rule becomes:** a one-paragraph backlink to the SKILL. The memory file is RETAINED (not deleted) per the dispatcher brief; it becomes an index-pointer ("graduated to SKILL at `<path>`; see SKILL for operative content"). This mirrors `feedback_durable_capture_for_planned_work` graduation discipline (memory-becomes-index, SKILL-becomes-operative).
3. **Why this is Wave 1:** zero dependencies, ≤4 h AI-time, universal-frame surviving (non-tech users have no mental model of context windows and benefit MORE from persona-driven compaction discipline than dev users do per master plan §3.1 P1 verdict). Compositional pair with the existing `precompact-hook` SKILL (precompact = structural-enforcement-of-state-preservation; strategic-compact = decision-discipline-of-WHEN-to-compact).
4. **Recommended ruling on the four named decisions below:** D-COMPACT.PATH (subdirectory shape — discoverable), D-COMPACT.BODY-SOURCE (memory rule as primary + ECC content as cross-check additive), D-COMPACT.TRIGGER (owner-class only — never autonomous-agent), D-COMPACT.MEMORY-FATE (backlink-only; retain file). All four are autonomously rule-able from existing corpus + ratified D-COMPACT.SKILL; surfaced for transparency, not blocking.

### Named decisions with recommendations (maintainer-facing)

| ID | Decision | Recommendation | Rationale (short) | Reversibility | Blast radius |
|---|---|---|---|---|---|
| **D-COMPACT.PATH** | SKILL location: `plugins/loam-skills/skills/strategic-compact/SKILL.md` (subdirectory shape) vs `plugins/loam-skills/skills/strategic-compact.md` (flat-file shape). | **Subdirectory shape.** | The auto-symlinker `_symlink_plugin_skills` (per `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310` verified Tier-0 in amendment 25308cf §10 D-SPDISC.MECHANISM) walks per-directory only; flat-file shapes are silently undiscovered. Subdirectory is the discoverable contract. | High | Low |
| **D-COMPACT.BODY-SOURCE** | SKILL body content: memory-rule-verbatim port vs memory-rule-as-primary-+-ECC-additive vs ECC-verbatim port. | **Memory-rule-as-primary; ECC content additive only where it adds value not present in memory rule.** | Memory rule is loam-native, stable, already cites loam compositions (`feedback_durable_capture_for_planned_work`, `feedback_session_start_discipline`, etc.). ECC's `skills/strategic-compact/` is the sibling absorbtion frame — its content may strengthen the trigger-list or the activation criteria, but loam's rule already carries the cost-shape analysis ECC lacks. Use ECC as cross-check, not source. | High | Low |
| **D-COMPACT.TRIGGER** | SKILL invocation trigger surface: owner-class only (persona invokes on owner-question or proactive owner-surface) vs autonomous-agent (any agent can invoke). | **Owner-class only.** | Per memory-rule §"Composes with the autonomy directive" (lines 106–111): "manual /compact and /clear are owner-discretion moves, not autonomous-agent moves." Autonomous compact violates the rubric's own constraint. The SKILL's frontmatter must encode this. | Medium (trigger-list editable but the discipline ships baked in) | Low |
| **D-COMPACT.MEMORY-FATE** | Memory rule disposition post-graduation: delete vs backlink-only (retain as index) vs split (operative content moves; backlink stays). | **Backlink-only — retain as index.** Per dispatcher brief explicit instruction. | Memory file retains its existing role as a discovery surface for the persona via memory-recall; the backlink makes the SKILL the operative source-of-truth. Mirrors the durable-capture graduation pattern (memory becomes index after graduation). Avoids breaking any existing memory-load mechanism that depends on the file existing. | High | Low |

---

## §1. Objective + scope

### Objective

Graduate the compact/clear decision-heuristic from session-scoped memory-rule discovery (loads via the memory-recall mechanism on a per-session basis) to auto-discoverable workspace-level SKILL (loads via Claude Code's filesystem-walk discovery at session-start in every loam-installed workspace). The graduation makes the discipline auto-available to derived workspaces (including non-tech-user workspaces where the user has no mental model of context windows and the persona absorbs the technical detail).

Net effect:

1. New SKILL at canonical discoverable subdirectory path with frontmatter that fires on owner-class compact/clear questions and on persona-detected context-pressure.
2. Memory rule retained as a one-paragraph backlink (memory-as-index).
3. Outcome-altitude smoke verifying the SKILL is discoverable via Claude Code's native walk against a fresh workspace.
4. The discipline becomes part of the loam toolkit (Lens 2 harness test) and the translation layer (Lens 2 primary-persona test) — the persona consults the SKILL instead of relying on memory-rule recall.

### In-scope (sealed-component fence per §3)

- `plugins/loam-skills/skills/strategic-compact/SKILL.md` — NEW; subdirectory shape; body derived primarily from the memory rule with ECC cross-check additive content; frontmatter encodes owner-class triggers.
- Outcome-altitude smoke test asserting the SKILL is discoverable + invocable via the production discovery path in a fresh workspace.
- Backlink edit to the memory rule (one paragraph at top: "graduated to SKILL at `plugins/loam-skills/skills/strategic-compact/SKILL.md`; this file retained as index").
- Universal admissions: this plan-doc + manifest YAML.

### Out-of-scope (deferred)

- **Autonomous-agent compact/clear invocation.** Explicitly out per D-COMPACT.TRIGGER (memory rule lines 106–111 lock owner-class only). Any "persona autonomously fires /compact" surface is a separate amendment with its own design review.
- **Modifying `/compact` or `/clear` Claude Code built-in behavior.** Out of scope; the SKILL is decision-guidance, not behavior-modification.
- **PreCompact hook integration.** The existing `plugins/loam-skills/skills/precompact-hook/SKILL.md` covers state-preservation-at-compact-time (the structural-enforcement companion); composing the two operationally is a future enhancement, not in fence here. The SKILL body should NAME precompact-hook as a sibling but not depend on changes to it.
- **Auto-firing of token-usage telemetry to invoke the SKILL.** Context-window utilization is not directly exposed (per memory rule lines 86–88); the SKILL must continue to operate on heuristic + owner-trigger inputs.
- **Migration of OTHER memory rules to SKILLs.** This graduation is one-off per D-COMPACT.SKILL. The broader instinct-graduation tooling (D-INSTINCT.GRADUATION per master plan §4) is the Wave 2/3 architecture decision — separate dispatch.
- **Body-content edits to the memory rule beyond the backlink paragraph.** The rule's existing content stays byte-identical except for the prepended backlink. Any wording revision is a separate dispatch.
- **Cross-loam-workspace skill sharing.** Out of scope per `skill-capture-proposal` SKILL §"Out of scope" — workspace-local-only by definition; this SKILL is plugin-shipped (different surface).

### Objective ladder-up (per ODD §2.5)

AC.COMPACT.* → master plan §4 D-COMPACT.SKILL ratification → master plan §3.1 P1 (universal-frame absorption) → AC.PO.1 (primary-persona test — reduce translation burden; non-tech users get coherent compaction without understanding the mechanism) + AC.PO.2 (harness toolkit — the SKILL adds to what the persona can invoke).

---

## §2. Acceptance criteria

### AC.COMPACT.* family

| AC ID | Outcome (deterministic) | Verification |
|---|---|---|
| **AC.COMPACT.PATH** | `plugins/loam-skills/skills/strategic-compact/SKILL.md` exists (subdirectory shape); the path is a regular file readable by Claude Code's discovery walk. | Test: `test_AC_COMPACT_PATH_skill_at_canonical_path.py` asserts `(plugins/loam-skills/skills/strategic-compact/SKILL.md).is_file()` AND parent is a directory matching the discoverable-shape contract enforced by `_symlink_plugin_skills` per the start-project regression closure. |
| **AC.COMPACT.FRONTMATTER** | SKILL.md has valid YAML frontmatter with `description:` field present + non-empty + naming the triggers (owner-class compact/clear question, persona-detected context-pressure) + encoding the owner-class-only constraint per D-COMPACT.TRIGGER. | Test: `test_AC_COMPACT_FRONTMATTER_valid_and_constraints_named.py` parses the frontmatter via the same parser the discovery walk uses; asserts `description` exists + is ≤1536 chars (per the Anthropic SKILL spec) + substring matches for trigger keywords AND for "owner" or "owner-class" / "not autonomous" constraint. |
| **AC.COMPACT.BODY** | SKILL body carries the three-options decision rubric from the memory rule: (a) continue, (b) /compact, (c) /clear, each with cost-shape + when-to-pick. Plus the decision-rule pseudocode (or equivalent prose). Plus the activation triggers section. Plus the composition section naming `precompact-hook` + `session-handoff` siblings + the source memory rule. | Test: `test_AC_COMPACT_BODY_substantive_sections_present.py` reads the body; asserts section-header substrings for the three options + decision rule + activation + composition; asserts the source memory file is named in the composition section as the substance-source. |
| **AC.COMPACT.BACKLINK** | The source memory file (`feedback_compact_clear_decision_heuristic.md`) prepends a one-paragraph backlink at the top of the file naming the SKILL's canonical path; remainder of file is byte-identical to pre-graduation. | Test: `test_AC_COMPACT_BACKLINK_memory_indexed.py` reads the memory file; asserts the prepended paragraph naming the SKILL path; asserts the rest of the file matches the pre-graduation byte-content via a stored hash or substring assertions for the original section headers (`## The three options`, `## The decision rule`, etc.). |
| **AC.COMPACT.S** | OUTCOME-ALTITUDE: A fresh loam workspace (produced via the production `run_first_run_scaffold` entry-point or moral equivalent invoked through `loam init`) carries the `strategic-compact` SKILL discoverable + invocable. Smoke test invokes the production discovery path against a tmpfs workspace with no pre-arranged `.claude/skills/` state. Per `feedback_test_outcome_altitude_required.md`. | Test: `test_AC_COMPACT_S_fresh_workspace_discoverability.py` constructs a tmpfs workspace, invokes the canonical fresh-scaffold entry-point, asserts `<workspace>/.claude/skills/strategic-compact/SKILL.md` exists + is reachable as a readable file (symlink-resolved per the AC.LAYERED.2 mechanism). RED-on-mutation: temporarily revert the SKILL move and assert the test fails — the test must FAIL if the SKILL is absent or in the flat-file shape. |

### AC ladder-up summary

- **AC.COMPACT.PATH** + **AC.COMPACT.FRONTMATTER** + **AC.COMPACT.BODY** + **AC.COMPACT.BACKLINK** are the structural ACs (the SKILL exists in the right shape with the right content + the memory rule indexes it).
- **AC.COMPACT.S** is the outcome-altitude AC (the SKILL is actually reachable via production discovery in a fresh workspace, not just present in the canonical tree).
- All five ladder up to D-COMPACT.SKILL ratification → master plan §3.1 P1 verdict → AC.PO.1 + AC.PO.2 prime objectives per `docs/VALUE_PROPOSITION.md`.

### Method-in-AC test

Each AC tested:

- **AC.COMPACT.PATH** — "SKILL exists at canonical subdirectory path." Method-agnostic: could be created by `Write`, `git mv` from an existing flat-shape, copy from ECC's tree, or any other tool. The AC pins outcome (file at path); the method is the builder's call. PASS.
- **AC.COMPACT.FRONTMATTER** — "valid frontmatter with named triggers + owner-class constraint." Method-agnostic: frontmatter could be authored in any text editor, derived from a template, or generated from a script. The AC pins outcome (frontmatter shape + content), not method. PASS.
- **AC.COMPACT.BODY** — "three-options rubric + decision rule + activation + composition sections present." Method-agnostic: the content could be ported from the memory rule, paraphrased, derived from ECC's sibling SKILL, or co-authored. AC pins outcome (sections + content topics); the prose-density and wording is builder's call. PASS.
- **AC.COMPACT.BACKLINK** — "backlink paragraph at top of memory file; rest byte-identical." Method-agnostic: backlink could be inserted by `Edit` tool, manual editing, or any other approach. PASS.
- **AC.COMPACT.S** — "fresh workspace via production scaffold carries the SKILL discoverable + invocable." Method-agnostic: the SKILL could ship via subdirectory-shape (recommended per D-COMPACT.PATH), via a plugin-metadata mechanism, or via any other discovery surface that resolves to the same outcome (SKILL reachable in fresh workspace). PASS.

All ACs are outcome-shape per ODD §2.5; method is the builder's call.

---

## §3. Sealed-component fence

Single-cycle, single-component-pair fence:

- **`plugins/loam-skills/`** — load-bearing component (the new `skills/strategic-compact/SKILL.md` subdirectory + body + frontmatter).
- **`framework/workspace-bootstrap/`** — verification-secondary (the AC.COMPACT.S outcome-altitude smoke invokes the existing `_symlink_plugin_skills` mechanism; no code change to that component, only test exercise).

Universal admissions:

- The source memory file at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_clear_decision_heuristic.md` (the backlink edit). NOTE: this file lives in the maintainer's home-directory memory tree, not in the loam canonical repo. The build dispatch must handle this carefully (the file is not under loam's git history; the edit is to a runtime memory file that the maintainer's session loads — graceful degradation: if the file is absent in the build environment, the AC.COMPACT.BACKLINK test runs against the canonical loam-shipped equivalent if one exists, OR halts and surfaces for ruling). Surfaced as a halt-trigger in §5.
- `docs/plans/drafts/strategic-compact-skill-graduation.md` (this plan-doc) — drafts location pending maintainer ratification; promotes to `docs/plans/` on dispatch.
- `docs/plans/drafts/strategic-compact-skill-graduation.manifest.yaml` (this amendment's manifest; authored at build dispatch time).

---

## §4. Work decomposition (per-cycle build steps; method-level guidance, builder's call per ODD §1.1)

Single cycle, single seal ladder. No sub-amendment ladder.

1. **Plan-doc ratification commit.** Move plan-doc from `drafts/` to `docs/plans/strategic-compact-skill-graduation.md`; author manifest YAML. Single commit.
2. **Source-edit commit.** Create `plugins/loam-skills/skills/strategic-compact/` directory; author `SKILL.md` (frontmatter + body per AC.COMPACT.FRONTMATTER + AC.COMPACT.BODY); edit the source memory file to prepend the backlink paragraph (or, if that file isn't accessible in the build environment, halt per §5 and surface). Author the five tests per §2.
3. **`loam amend apply` auto-commit.** Per `feedback_dispatch_explicit_loam_amend_apply.md` — explicit invocation in the dispatch brief.
4. **`loam amend seal` deterministic seal commit.** Closes the cycle.

Method-level guidance (builder's call):

- **SKILL body sourcing.** D-COMPACT.BODY-SOURCE recommends memory-rule-as-primary; the builder may also fetch ECC's `skills/strategic-compact/` via WebFetch for cross-check (the dispatcher brief notes the URL is informative-not-load-bearing). If ECC's content adds substantive value (e.g., a trigger-condition not in the memory rule), the builder absorbs it; if it duplicates the memory rule, the builder doesn't. Surfaced as a build-time judgment call.
- **Frontmatter prose density.** The `description:` field is the auto-discovery hook — Claude Code matches it against turn-context to decide which SKILLs to load. The frontmatter must name explicit trigger phrases ("should I /compact?", "should I /clear?", context-pressure-detected) + the owner-class constraint. The exact phrasing is the builder's call; reference siblings: `precompact-hook` (line 2), `session-handoff` (verify shape at build-time).
- **Backlink paragraph wording.** Brief one-paragraph: "Graduated to SKILL at `plugins/loam-skills/skills/strategic-compact/SKILL.md` per amendment <slug>. This file retained as index; operative content lives in the SKILL." Exact wording builder's call.

---

## §5. Halt triggers (in-flight; if any fire during build, halt the offending work-item)

1. **WD drifts from canonical loam.** Per `feedback_always_specify_wd_in_dispatches.md` + `feedback_dispatch_cd_literal_first_action.md` — halt + surface.
2. **The source memory file is not accessible in the build environment.** Per §3 universal admission caveat — the file lives at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_clear_decision_heuristic.md` which is outside the loam canonical repo. If the build environment is a clean clone without the maintainer's home-directory memory tree, the AC.COMPACT.BACKLINK edit cannot land. Halt + surface for maintainer ruling: (a) maintainer manually applies the backlink edit in their home tree; (b) skip the AC.COMPACT.BACKLINK requirement for this graduation; (c) other resolution.
3. **`_symlink_plugin_skills` discovery contract has changed between plan-author time and build time.** Per amendment 25308cf §10 D-SPDISC.MECHANISM verified Tier-0 at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310` — walks `plugins/*/skills/*/SKILL.md` only. If the builder finds this has changed (e.g., now walks flat-files too, or requires plugin-metadata declaration), halt + RF.
4. **`strategic-compact` slug collision.** Per amendment 25308cf §6 halt-trigger pattern — if any other plugin's `skills/` carries a `strategic-compact` SKILL, `_symlink_plugin_skills` will raise `PluginSkillCollisionError`. Verified at plan-author time: `find plugins -name "strategic-compact*"` returns no matches in canonical loam. If collision discovered at build-time (e.g., a recent amendment added one), halt + surface.
5. **AC.COMPACT.S test fails RED-on-mutation.** Per `feedback_test_outcome_altitude_required.md` — if reverting the SKILL move/create doesn't break the test, the test is not at outcome-altitude (probably stubbed or pre-arranged). Halt + redesign.
6. **ECC WebFetch contradicts the maintainer ruling on D-COMPACT.BODY-SOURCE.** Unlikely (ECC is informative-not-load-bearing), but if ECC's `skills/strategic-compact/` carries a constraint that contradicts memory-rule content (e.g., autonomous-fire trigger), halt + surface so the maintainer can rule on the divergence.
7. **Outcome-altitude test exists but the production fresh-scaffold entry-point doesn't symlink loam-skills SKILLs.** Per the start-project regression: only the dev-sdlc plugin's skills got auto-symlinked at v0.1.7 ship; loam-skills SKILLs may use a different mechanism (verify at build-time). If `_symlink_plugin_skills` only walks `plugins/dev-sdlc/skills/` and not `plugins/loam-skills/skills/`, the AC.COMPACT.S smoke needs adjustment. Halt + surface for ruling.

---

## §6. Dependencies

**None.** Wave 1 leaf per master plan §6.

The SKILL graduation has zero load-bearing dependencies on:

- D-INSTINCT.GRADUATION (master plan Q2 — still pending maintainer ruling); the strategic-compact graduation is a MANUAL one-off (not via auto-graduation tooling). When/if D-INSTINCT.GRADUATION ratifies and Phase 2 tooling ships, the strategic-compact graduation will have been the seed of the manual pattern the tooling automates.
- D-SEC.HOOKS (master plan Q1); independent component.
- D-MARKETPLACE (master plan Q3); the SKILL ships via the existing plugin-content distribution, not via marketplace.json.

**Soft compositional pair (not dependency):**

- `plugins/loam-skills/skills/precompact-hook/SKILL.md` already names `feedback_compact_clear_decision_heuristic.md` at lines 58–60. After this graduation, the precompact-hook SKILL could optionally update its composition reference to name the new SKILL instead of (or in addition to) the memory rule. This update is OUT OF FENCE for this graduation; surfaced as a future-enhancement-only.

---

## §7. Cost estimate + go-order

### Cost band

**sm** per master plan §5 WI-1 + this plan's analysis. ~2–4 h AI-time per the `feedback_duration_estimation_rubric.md`:

- Plan-doc ratification commit: ~5 min.
- Source-edit commit (SKILL.md + frontmatter + body + 5 tests + backlink edit): ~30–60 min (substantive content; not boilerplate; outcome-altitude smoke requires the careful synthetic-workspace setup pattern from amendment 25308cf AC.SPDISC.S).
- `loam amend apply` + test runs + iteration on any failures: ~30–60 min.
- `loam amend seal`: ~5 min.
- Total: ~70–130 min AI-time wall-clock per the formula `tool_calls × 0.1–0.15`; band 2–4 h with buffer for unexpected halts.

### Go-order

This is a Wave 1 work-item per master plan §6. Parallel-safe at the plan-authoring tier (already in-flight per dispatch brief: parallel with security-hooks-bundle / token-defaults / README-restructure). Build phase serializes per `feedback_serialize_amendment_builds.md` (single working tree; index.lock + loam-amend races). The four Wave 1 plan-docs land in parallel; the four builds queue sequentially.

Recommended build order WITHIN Wave 1 (per master plan §6 parallelization note):

1. README restructure (no test surface; fastest).
2. Strategic-compact SKILL graduation (this; small test surface; low risk).
3. Token-defaults docs + SKILL (similar shape; small test surface).
4. Security hooks bundle (largest test surface; most risk; runs last so prior simpler builds catch any cycle-infrastructure regressions first).

Maintainer-time gate: none (no architecture decision needed beyond the four §0 named decisions which are autonomously rule-able).

---

## §8. Open questions

### Q1 (LOW) — D-COMPACT.BODY-SOURCE: how much ECC content to absorb?

**Question:** When the builder fetches ECC's `skills/strategic-compact/` for cross-check, how aggressive should absorption be? Memory-rule-only is the recommended default; ECC-additive-only-where-it-adds-novel-value is the relaxed default.

**Recommendation:** Builder judgment at build-time. The dispatch brief should pass the URL `https://github.com/affaan-m/everything-claude-code/tree/main/skills/strategic-compact` + the discipline: fetch + cross-check + absorb-if-additive. If ECC's content is materially better in any specific subsection, absorb; if duplicative, skip. The build's seal narrative names what was absorbed and what was not.

**Why not escalate:** Per `feedback_test_against_operational_objective_before_escalating.md` — the operational objective is "loam-discoverable SKILL with stable substantive content"; the source choice between two near-equivalent options is autonomously rule-able by the builder against the objective. NO escalation needed.

### Q2 (LOW) — D-COMPACT.PATH: should the SKILL ship under `plugins/loam-skills/` or `plugins/dev-sdlc/`?

**Question:** loam-skills is the universal plugin; dev-sdlc is the dev-mode-only plugin. The strategic-compact discipline is universal per master plan §3.1 P1 (non-tech users benefit MORE, not less). Recommendation: `loam-skills/`.

**Recommendation:** `plugins/loam-skills/skills/strategic-compact/SKILL.md`. Universal partition is correct per the universal-frame verdict.

**Open sub-question for maintainer awareness:** does the `_symlink_plugin_skills` mechanism walk `plugins/loam-skills/skills/` as well as `plugins/dev-sdlc/skills/`? Verified at plan-author time via the existing presence of `plugins/loam-skills/skills/` with 21 subdirectory-shape SKILLs (per `ls`). If the mechanism only walks dev-sdlc, the §5 halt-trigger #7 fires at build-time and surfaces for ruling.

### Q3 (LOW) — D-COMPACT.MEMORY-FATE: should the backlink edit happen at all, given the memory file is outside the loam repo?

**Question:** The memory file at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_clear_decision_heuristic.md` is in the maintainer's home directory, not in the loam canonical tree. Editing it from a build agent in canonical loam may not be possible (build agents typically work against the loam repo, not the maintainer's home tree).

**Options:**
- (a) Skip the backlink edit; rely on the maintainer to apply it post-build (one-paragraph manual edit; trivial).
- (b) Have the build agent attempt the edit if the file exists in the build environment; halt + surface if not.
- (c) Drop AC.COMPACT.BACKLINK from the AC family entirely; memory file stays as-is.

**Recommendation:** (b) attempt + halt-if-not-accessible (per §5 halt-trigger #2). The backlink edit is one-paragraph and trivial; if the build environment is a clean loam clone without the maintainer's memory tree, the maintainer can apply the backlink manually post-build per option (a) as fallback. Drop-the-AC option (c) is RF-incorrect because the AC is the right outcome — the question is mechanism, not desirability.

**Reversibility:** High either way.

### Q4 (LOW) — should `precompact-hook` SKILL's composition reference update to name the new SKILL?

**Question:** `plugins/loam-skills/skills/precompact-hook/SKILL.md:58-60` currently names `feedback_compact_clear_decision_heuristic.md` (the memory rule). Post-graduation, that reference is still valid (the memory file becomes an index pointing to the new SKILL) — but it could optionally update to name the new SKILL directly.

**Recommendation:** OUT OF FENCE for this graduation. Surfaced as a future-enhancement; the reference works as-is (memory-as-index resolves via the backlink). If the maintainer wants the update now, it's a one-line touch and could be folded in — surfaced for awareness, not blocking.

---

## §9. Bookkeeping

- **`docs/plans/` move:** plan-doc moves from `docs/plans/drafts/` to `docs/plans/` at ratification commit (per the recent convention).
- **STATE.md / roadmap entries:** no roadmap update needed (this is a Wave 1 absorption from the master plan; the master plan §5 WI-1 entry tracks it). Post-seal: add a one-line entry to the master plan §3.1 P1 "Recommendation" row updating to "ABSORBED — seal SHA <X>" per the canonical master-plan convention.
- **Sidecars:** advance per `loam amend seal` standard flow; per amendment 25308cf §11 convention.

---

## §10. F2 Ruthless Feedback (honest doubts)

1. **The graduation might be cosmetic.** The memory rule has been stable for 10 days and the persona (me) loads it via memory-recall every session. The question: does upgrading the discovery surface from memory-recall to SKILL-discovery materially change behavior, or does it just relocate the same content? The substantive case: SKILL-discovery is DERIVED-WORKSPACE-VISIBLE (non-tech users get the discipline without the memory tree); memory-recall is MAINTAINER-WORKSPACE-ONLY (the file path is under the maintainer's home directory). So the graduation IS materially valuable — but only for derived-workspace users. If derived workspaces don't actually use the strategic-compact discipline (e.g., they /clear instead of /compact, or rely on auto-compact), the graduation is dormant infrastructure. **Recommendation:** ship the graduation (low cost; high reversibility); add a post-ship usage-audit on a future cadence (FIDRAFT?) to verify derived workspaces actually invoke the SKILL.

2. **The ECC content might be substantively better than the memory rule, in which case "memory-rule-as-primary" is the wrong default.** Without fetching ECC's actual content, I'm recommending memory-rule-primary by analogy (loam-native content for loam SKILLs). If ECC's `skills/strategic-compact/` has materially sharper trigger criteria or a better cost-shape table, the memory-rule-primary default may produce an inferior SKILL. **Recommendation:** the builder dispatch brief carries the WebFetch + cross-check discipline (per §4 method-level guidance) so the actual comparison happens at build-time, not at plan-author-time. If ECC is sharper, the builder absorbs it (D-COMPACT.BODY-SOURCE recommendation allows additive ECC content).

3. **AC.COMPACT.S outcome-altitude smoke might be hard to author correctly.** Per amendment 25308cf §13 doubt #2: outcome-altitude tests for skill-discoverability require the synthetic-workspace setup pattern (real `_symlink_plugin_skills` invocation; no pre-arranged `.claude/skills/` state; RED-on-mutation verification). The builder dispatch brief MUST reinforce this; a stub-style test asserting the symlink directly via `os.symlink` is method-shaped, not outcome-shaped, and fails the outcome-altitude requirement. **Recommendation:** dispatch brief explicitly cites amendment 25308cf AC.SPDISC.S as the shape exemplar.

4. **The "owner-class only" constraint is encoded in frontmatter but not structurally enforced.** Per D-COMPACT.TRIGGER recommendation, the SKILL frontmatter encodes "owner-class only / never autonomous." But the constraint is documentation-shaped, not structural-shaped — a future agent could invoke the SKILL autonomously and the SKILL would surface without protest. The structural enforcement would be a hook (per `feedback_structural_enforcement_on_recurrence.md`). **Recommendation:** ship the documentation-shaped constraint now; if violations are observed post-ship, promote to structural enforcement (PreToolUse hook checking for autonomous-agent /compact invocations) per the recurrence-promotion-pattern. Surfaced as FIDRAFT in §11.

5. **The backlink-in-memory-file approach may not survive memory-file regeneration.** The memory file is auto-loaded by the loam memory-system from `~/.claude/projects/-Users-lukeivers-pos3/memory/`. If the memory-system ever regenerates or auto-rotates that file (e.g., via the M-FBM system), the backlink paragraph could be overwritten. Verified at plan-author time: the memory file's content is manually-authored (not auto-generated) per its captured-2026-05-14 header, so regeneration risk is low. **Recommendation:** accept the risk; if/when memory-system auto-rotates user-authored memory files, the backlink-fate becomes a known issue and gets re-addressed.

6. **The plan-doc covers content that the SKILL body itself should cover — is this duplication?** Section AC.COMPACT.BODY enumerates what the SKILL body must contain (three options + decision rule + activation + composition). The plan-doc names these as ACs; the SKILL body actually contains them. Some duplication is unavoidable (the plan-doc names the outcome; the SKILL body IS the outcome). The risk: at build-time, the builder might either over-source-from-the-plan-doc (sterile, plan-flavored prose) or under-source (missing AC.COMPACT.BODY substance). **Recommendation:** the dispatch brief instructs the builder to use the memory rule as the primary substance source (per D-COMPACT.BODY-SOURCE), not this plan-doc. The plan-doc is the AC contract; the memory rule is the source-of-substance.

7. **F4 calibration for this plan-doc itself.** Inventory of decisions (§0 table) is TIGHT-scope — each row has a recommendation + rationale + reversibility. Acceptance criteria (§2) are TIGHT-scope per AC — outcome-shape pinned, method left to builder. Method guidance (§4) is LOOSE-scope intentionally — builder's call per ODD §1.1. Open questions (§8) are tagged LOW criticality and autonomously rule-able. Overall: HIGH-confidence shape; matches the F4 prescription. The plan-doc itself is short by loam standards (~430 lines per draft) because the scope is small (one SKILL + one backlink); the shape matches the amendment 25308cf single-cycle PATCH exemplar.

---

## §11. FIDRAFT capture (for the maintainer to graduate or discard)

- **F-COMPACT-AUTONOMOUS-INVOCATION-STRUCTURAL-GUARD** — §10 doubt #4. If post-ship audit shows autonomous-agent /compact invocations occurring despite the SKILL's documentation-shaped owner-class-only constraint, promote to structural enforcement via PreToolUse hook. Per `feedback_structural_enforcement_on_recurrence.md` recurrence-promotion-pattern.
- **F-COMPACT-DERIVED-WORKSPACE-USAGE-AUDIT** — §10 doubt #1. Post-ship, audit on cadence whether derived workspaces (non-tech-user / writer / etc.) actually invoke the strategic-compact SKILL. If dormant, the graduation is cosmetic and a re-think is warranted. Possibly a quarterly SKILL/loop.
- **F-COMPACT-PRECOMPACT-COMPOSITION-UPDATE** — §8 Q4. Update `plugins/loam-skills/skills/precompact-hook/SKILL.md:58-60` composition reference to name the new SKILL directly. One-line touch; foldable into a future small dispatch or this graduation if the maintainer rules it in-fence.

---

## §12. Provenance trail

All citations verified Tier-0 (file-read) or Tier-1 (named source) at plan-author time 2026-05-24.

| Claim | Source | Tier |
|---|---|---|
| Memory rule exists at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_clear_decision_heuristic.md`; 112 lines; stable since 2026-05-14 | Read of file this turn | Tier-0 |
| Memory rule prescribes owner-class-only invocation | Lines 106–111 of memory file | Tier-0 |
| Memory rule's three-options + cost-shape rubric | Lines 10–66 of memory file | Tier-0 |
| Master plan D-COMPACT.SKILL ratification = approve graduate | `docs/plans/drafts/everything-claude-code-absorption-master-plan.md:540` (D-COMPACT.SKILL recommendation row) | Tier-0 |
| Master plan WI-1 scope sketch | `docs/plans/drafts/everything-claude-code-absorption-master-plan.md:602-613` | Tier-0 |
| Maintainer ruling on D-COMPACT.SKILL ratified per Telegram 12301 ("B" = approve graduate) | Dispatcher brief (passed in this dispatch); not independently Tier-0-verifiable from plan-author tree | Tier-1 |
| `_symlink_plugin_skills` walks subdirectory shape only | Amendment 25308cf §10 D-SPDISC.MECHANISM Tier-0 verification of `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py:1224-1310` | Tier-0 (transitive via sealed amendment) |
| 21 subdirectory-shape SKILLs exist in `plugins/loam-skills/skills/` | `ls plugins/loam-skills/skills/` this turn | Tier-0 |
| `plugins/loam-skills/skills/precompact-hook/SKILL.md:58-60` references the memory rule | Read of file this turn | Tier-0 |
| ECC `skills/strategic-compact/` exists as a sibling SKILL | Master plan §3.1 P1 + ECC README citations + dispatcher-brief URL | Tier-1 (cited by master plan + dispatcher; not WebFetched this turn) |
| No `strategic-compact*` slug collision in canonical loam | `find plugins -name "strategic-compact*"` this turn (no matches) | Tier-0 |
| Plan-doc shape exemplar: `loam-skills-start-project-discoverable.md` | Read of file this turn | Tier-0 |
| `feedback_durable_capture_for_planned_work.md` graduation-pattern source | Read of file this turn | Tier-0 |

**Sibling SKILL exemplars read this turn:**
- `plugins/loam-skills/skills/skill-capture-proposal/SKILL.md` (workspace-local SKILL capture; multi-page reference)
- `plugins/loam-skills/skills/handsoff-loop/SKILL.md` (single-capability SKILL; tight body)
- `plugins/loam-skills/skills/translation-discipline/SKILL.md` (discipline-as-SKILL; closest shape to this graduation's target)
- `plugins/loam-skills/skills/precompact-hook/SKILL.md` (compositional sibling)

**Memory rules referenced:**
- `feedback_compact_clear_decision_heuristic.md` — source of substance for the SKILL
- `feedback_durable_capture_for_planned_work.md` — graduation pattern (memory-becomes-index, SKILL-becomes-operative)
- `feedback_scope_descriptive_ac_ids.md` — AC.COMPACT.* naming
- `feedback_test_outcome_altitude_required.md` — AC.COMPACT.S shape
- `feedback_structural_enforcement_on_recurrence.md` — §11 F-COMPACT-AUTONOMOUS-INVOCATION-STRUCTURAL-GUARD framing
- `feedback_dispatch_explicit_loam_amend_apply.md` — §4 ladder step naming
- `feedback_serialize_amendment_builds.md` — §7 build-phase serialization note
- `feedback_duration_estimation_rubric.md` — §7 AI-time band

**Lens references (verified against `/Users/lukeivers/loam/CLAUDE.md`):**
- L1 Claude-leverage-first — SKILL discovery primitive (filesystem-walk) is the leveraged Claude capability
- L2 Harness + primary-persona value — non-tech user benefits via persona invocation; SKILL adds to toolkit
- L3 ODD authoring — every AC outcome-shape; method builder's call
- L4 Prompt scope ↔ confidence — tight outcome scope, loose method (matches HIGH-confidence-on-outcome shape)

---

## §13. Authoring trail

Authored 2026-05-24 by `loam-plan-author` subagent. Dispatched per maintainer Telegram 12301 ratifying D-COMPACT.SKILL ("B" = approve graduate). Wave 1 ECC absorption work-item WI-1 per master plan §5. Parallel-dispatched with security-hooks-bundle / token-defaults-skill / readme-decision-doc-restructure plan-author dispatches.

Plan-doc ratification: pending. Per-work-item build dispatch lands on maintainer ruling per §8 questions (all Q1–Q4 LOW-criticality and autonomously rule-able by the builder; ratification likely implicit).

---

## §14. Method-decision register (populated at build time)

Placeholders for builder narration; SHAs backfilled by `loam amend seal --plan-doc`:

- **D-COMPACT.PATH** — subdirectory shape at `plugins/loam-skills/skills/strategic-compact/SKILL.md`. **Recommended at plan-author time: SUBDIRECTORY** (per §0 + verified mechanism per amendment 25308cf).
- **D-COMPACT.BODY-SOURCE** — memory-rule primary + ECC additive only. **Recommended at plan-author time: MEMORY-RULE-PRIMARY; ECC CROSS-CHECK ADDITIVE** (per §0).
- **D-COMPACT.TRIGGER** — owner-class only encoded in frontmatter. **Recommended at plan-author time: OWNER-CLASS ONLY** (per §0 + memory rule lines 106–111).
- **D-COMPACT.MEMORY-FATE** — backlink-only; retain file. **Recommended at plan-author time: BACKLINK-ONLY** (per §0 + dispatcher brief explicit).
- **D-COMPACT.BACKLINK-METHOD** — file-edit access path: build-environment-direct-edit if accessible, else maintainer-manual-post-build. **VERIFICATION DEFERRED to builder** at apply-time (per §5 halt-trigger #2 + §8 Q3).
- **D-COMPACT.ECC-ABSORPTION-DEGREE** — how much ECC content to absorb. **DEFERRED to builder** judgment at build-time per §4 method-level guidance + §8 Q1.

---

## §15. Plan-doc convention compliance footer

This plan-doc follows the canonical shape per `plugins/dev-sdlc/docs/conventions/plan-docs.md`:

- AC IDs scope-descriptive (AC.COMPACT.*) NOT version-packed. Per `feedback_scope_descriptive_ac_ids`.
- §14 method-decision register placeholder for build-time backfill.
- §10 F2 Ruthless Feedback (honest doubts) with named alternatives + evidence per `feedback_ruthless_feedback.md`.
- §0 named decisions with recommendations per `feedback_summarize_and_surface_decisions.md` (maintainer rules from summary, not by reading the full doc).
- Provenance trail (§12) with Tier-tagged citations per `feedback_information_trust_ordering.md`.
- §11 FIDRAFT capture for durable post-ship items per `feedback_future_ideas_draft_workflow.md`.
- Outcome-altitude AC (AC.COMPACT.S) named per `feedback_test_outcome_altitude_required.md`.
- Halt triggers (§5) with named in-flight conditions per the plan-doc convention.
- Single-cycle PATCH-class amendment shape mirrors `loam-skills-start-project-discoverable.md` (sealed exemplar).

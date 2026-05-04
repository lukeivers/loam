# Layered skill story — base + plugin + workspace-local + auto-creation + promotion rubric

**Authored:** 2026-05-04. **Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Doc class:** planning + analysis (pre-build, doc-only). **Trigger:** Luke directive 2026-05-04 on layered-skill story (auto-creation + promotion rubric + dev-sdlc skill-ification, dev-only). **Length target band:** 4000–8000 words.

**Anchor sources cited inline:** `docs/rebuild/VALUE_PROPOSITION.md`; `docs/rebuild/STATE.md`; `docs/rebuild/plans/v0-1-x-roadmap.md`; `docs/rebuild/plans/value-prop-vs-actual-shape-audit-2026-05-04.md`; `docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md`; `docs/rebuild/FUTURE_IDEAS_DRAFT.md`; `plugins/loam-skills/skills/`; `plugins/dev-sdlc/skills/start-project.md`; `plugins/dev-sdlc/dev-mode-manifest.yaml`; `plugins/dev-sdlc/docs/conventions/fidraft-pattern.md`; `CLAUDE.md` (top-level loam Lens 1–5); Anthropic SKILL.md schema at https://code.claude.com/docs/en/skills (fetched 2026-05-04).

---

## Principles applied this turn (per session-start discipline)

- **CHANNEL** — reply lands at the dispatcher (main session); no Telegram in this dispatch context.
- **AUTONOMY** — research broadly within scope; surface findings; recommend.
- **F2 RUTHLESS FEEDBACK** — name disagreements with Luke's framing where evidence supports them. Specifically: the term "auto-creation" is examined against the actual Anthropic SKILL.md primitive — if the primitive doesn't support persona-driven authoring of new SKILL.md files mid-session, the recommendation must reshape, not paper over.
- **LOCKED-DESIGN-NOT-LICENSE** — the v0.1.3 5-package skill bundle is locked-but-incomplete; revisit and propose extensions without violating the seal.
- **ODD §2.5** — every recommendation maps to a named source.
- **OUTPUT-TO-DISK** — full plan to disk; reply summary inline.
- **DURABLE-CAPTURE** — this plan-doc IS the durable surface; it informs but does not replace FIDRAFT entries that may emerge.
- **WD-IN-DISPATCHES** — confirmed `/Users/lukeivers/ivers-corp-pos-v2/`.
- **TRANSLATION RULE** — executive summary readable by non-technical reader.
- **PARTITION RULE (Luke directive 2026-05-04)** — anything dev-related goes into `plugins/dev-sdlc/`, NOT into core `framework/`. The auto-creation + promotion-rubric behavior IS dev-specific (per Luke's verbatim directive); the layered-skill ARCHITECTURE itself (base / plugin / workspace-local) is harness-general.

---

## Executive summary (non-technical)

Skills are what Claude Code calls a small reusable instruction file (a "SKILL.md") that Claude pulls into a conversation when it's relevant to what the user is doing. Loam already ships five of these — they capture loam's load-bearing translation patterns (memory recall, dispatch shape, scope decomposition, session greeting, session handoff). Five is a starting point, not the destination.

Luke's directive opens four extensions:

1. **A layered architecture for skills.** Today loam puts skills in two places (a `loam-skills` plugin and a stray `dev-sdlc/skills/` directory). The layered architecture has three tiers: **base skills** that every loam install gets (today's `loam-skills`), **plugin skills** that ship with optional plugins (today's `dev-sdlc`), and **workspace-local skills** that exist only in one user's workspace and capture project-specific patterns. Claude Code already supports all three tiers natively — this work is mostly about disciplined placement, not new mechanism.

2. **Dev-SDLC skill-ification audit.** The dev-sdlc plugin is currently mostly docs + tools + hooks + templates. A lot of behaviors that *should* be SKILL-shaped (so Claude auto-loads them when relevant) currently live as long-form docs or rely on Luke remembering to invoke a tool. This document audits dev-sdlc and names ~12 candidate SKILLs.

3. **Persona-driven auto-creation of skills.** When Luke asks the persona to "remember this pattern", or when the persona detects it's done the same multi-step thing three times, the persona should propose codifying it as a workspace-local SKILL.md. The persona drafts; the user reviews and ratifies; the SKILL ships into the workspace's `.claude/skills/` directory and Claude auto-loads it from then on. This is dev-only — Eric (the SaaS user) doesn't get auto-creation.

4. **Promotion rubric.** Workspace-local skills accumulate. Some are workspace-junk (only useful here). Some are pattern-junk (a coincidence of three repeats). And some are real toolkit additions that deserve promotion to a plugin or to base loam. The rubric names six signals (reusability, quality, test coverage, usage count, conflict with existing skills, dev-vs-general categorization) and a six-step promotion workflow that ends in either ratification, deferral, or retirement.

This is **dev-only behavior**. A non-dev loam user (Eric, a hypothetical writer, anyone using loam-as-product) gets the layered architecture (which is harness-general) but does not get auto-creation or the promotion rubric (which are dev-mode-only per Luke's verbatim directive). The dev-mode partition primitive that already exists handles this gating cleanly.

The rest of this document is the technical version.

---

## §1 — Current state of skills in loam

### 1.1 — What's shipped today

**The five loam-skills packages (sealed `f04e925`, 2026-05-04, amendment #124).** Living at `plugins/loam-skills/skills/<name>/SKILL.md`:

| Skill | What it captures | Source |
|---|---|---|
| `memory-recall` | Read M-FBM episodes before answering when prior context is needed | `plugins/loam-skills/skills/memory-recall/SKILL.md` |
| `scope-decompose` | F3 swarming stopping criterion — decompose when subtasks have tighter ACs | `plugins/loam-skills/skills/scope-decompose/SKILL.md` |
| `dispatch-with-gates` | Scope-only sub-agent dispatches (objective + scope + constraints + halt + ODD-check) | `plugins/loam-skills/skills/dispatch-with-gates/SKILL.md` |
| `onboarding-conversation` | Session-start context-restoration greeting | `plugins/loam-skills/skills/onboarding-conversation/SKILL.md` |
| `session-handoff` | Durable-capture before session close | `plugins/loam-skills/skills/session-handoff/SKILL.md` |

Each is well-formed against the Anthropic SKILL.md schema (verified by `test_AC_LSK_2_frontmatter_well_formed.py`, 20 tests pass). Each carries a body shape: *What this skill captures / When to use / How the persona applies it / Graceful degradation / Composition / Out of scope*. This shape is a template the rest of this plan re-uses.

**The `dev-sdlc/skills/start-project.md` flat-shape package.** A single `.md` file (not a directory-shaped SKILL package; the difference is captured as Surface in the v0.1.3 SKILL bundle status file: "migration of flat-shape skills to modern directory-per-skill shape — out of fence; v0.2+ if Anthropic discovery requires it"). The `start-project` skill is the user-facing entry-point for the dev-sdlc plugin's project-scaffolding workflow.

**Two stray skills inside `framework/primary-persona/skills/`** — `memory-search.md` and `memory-archive.md`, both flat-shape. These should arguably move to `plugins/loam-skills/` post-promotion (covered in §4).

**Bundled skills at the Claude Code layer** (not loam's): `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/init`, `/review`, `/security-review`, `/update-config`, `/keybindings-help`, `/fewer-permission-prompts`, `/schedule`, `/telegram:access`, `/telegram:configure`. These ship with Claude Code itself; loam does not own them but composes with them.

### 1.2 — What's planned but not shipped

**Six persona-behavior SKILL packages (FIDRAFT, 2026-05-04, `FUTURE_IDEAS_DRAFT.md` line 23).** Captured under the entry "Persona-behavior SKILL packages — promote operational implicit behaviors to explicit playbooks." Six concrete candidates:

1. **translation-discipline** — anti-pattern checklist (no commit SHAs / AC IDs / abbreviations / doc-section refs without summary) + before-send pass.
2. **audit-block-on-telegram** — structural template (Executed / Deferred-to-owner / Missed enumerations) preventing one-liner regression.
3. **front-load-principle-walk** — turn-start playbook for the 12-principle walk.
4. **dispatch-brief-authoring** — template (objective / scope / constraints / halt triggers / principles propagation / model rationale).
5. **sealed-component-amendment-ship** — wraps existing pos-publish-framework-only + tag + dual-ref push + gh release create ritual.
6. **owner-decision-summary** — recommendation-with-rationale shape, prevents doc-section-pointer regression.

The FIDRAFT entry names placement as `plugins/loam-skills/skills/<name>/` (general harness patterns; not dev-specific). It also names sequencing options (own release / fold into Eric sequence / bundle into v0.1.4). This document re-evaluates that placement against the partition rule in §10 — net finding: candidates 3, 4, 5 are dev-specific and should land in dev-sdlc; 1, 2, 6 are harness-general and stay in loam-skills.

**ODD-RE V11.C heavy** — (`FUTURE_IDEAS_DRAFT.md:29` — `framework/odd-extractor/` per the original FIDRAFT, reclassified to `plugins/dev-sdlc/odd-extractor/` per the partition rule and the Eric sequence research, `eric-saas-app-use-case-version-sequence-2026-05-04.md` §3 G1). The "lightweight V11.C" (thin SKILL.md) was deferred 2026-05-04 because M-FBM operational-health amendment obviates the workaround value. The heavy version retains value for foreign-codebase comprehension. SKILL-shape exists as a question: does ODD-RE ship as a SKILL invokable mid-session, or as a CLI tool, or as a service? This plan addresses that in §5.

### 1.3 — What's drift

Three drift items, each captured as a sub-action:

1. **`plugins/loam-skills/` is not enrolled in any workspace's `bootstrap.yaml` `contributions:`.** The 5 SKILLs ship pip-installable but Claude Code's plugin discovery requires the plugin be enabled in the workspace's bootstrap. Today they're dormant. Decision A in §8.
2. **`framework/primary-persona/skills/memory-search.md` and `memory-archive.md`** are flat-shape inside a sealed component (legacy command pattern, still works per Anthropic's "commands have been merged into skills" note). Migration to directory-per-skill shape is out-of-fence per v0.1.3 status; revisit at v0.2+. Captured in §4.
3. **`plugins/loam-skills/`** missing from `dev-mode-manifest.yaml` `roots:` and `always_loaded:`. v0.1.3 SKILL bundle status file flags this. Sub-action of v0.1.7.

### 1.4 — Anthropic SKILL.md primitive (verified 2026-05-04)

Discovery locations (precedence: enterprise > personal > project; plugin in its own `plugin-name:skill-name` namespace):

| Location | Path |
|---|---|
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `<workspace>/.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` |

Live change detection picks up adds/edits within the session — *but creating the top-level skills directory mid-session requires Claude Code restart.* Frontmatter fields (all optional except `description` recommended): `name`, `description`, `when_to_use`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context: fork`, `agent`, `hooks`, `paths`, `shell`, `arguments`. Skills can `context: fork` to run in isolated subagent contexts. Description budget caps at 1,536 chars per skill in listings.

**Critical for §3 (auto-creation):** Anthropic ships *no* "auto-create-skill" API — skills are plain markdown files. The primary persona can author one mid-session via the `Write` tool into `<workspace>/.claude/skills/<name>/SKILL.md`. Registration *is* the file write. Anthropic explicitly endorses this pattern: *"Create a skill when you keep pasting the same instructions, checklist, or multi-step procedure into chat."* This shapes §3 substantially — "auto-creation" is implementable today; what's missing is the discipline.

---

## §2 — Three-layer skill architecture

### 2.1 — The three layers (formal definitions)

**Base loam skills** — skills that ship with the harness's core skill plugin. Today: `plugins/loam-skills/`. Available to every loam user when the plugin is enabled in `bootstrap.yaml`. Discoverable via Claude Code's plugin discovery (`<plugin>/skills/<name>/SKILL.md`). These capture loam's load-bearing translation patterns that aren't dev-specific (memory recall, dispatch shape, session-handoff, etc.).

**Plugin skills** — skills that ship with optional plugins. Today: `plugins/dev-sdlc/skills/start-project.md` (and post-§5 audit, ~12 more candidates). Available only when the plugin is enabled. Same Claude Code discovery mechanism. These capture domain-specific patterns (dev-sdlc patterns, Slack-workflow patterns when a Slack plugin lands, legal-research patterns when a legal plugin lands per Lens 1's example).

**Workspace-local skills** — skills authored in a specific user's workspace, persisted under `<workspace>/.claude/skills/<name>/SKILL.md`. Available only in that workspace. Discoverable via Claude Code's project-skill discovery (`.claude/skills/`). These capture project-specific patterns the user has accumulated through actual usage (e.g., "when working on Eric's SaaS app, run `bundle exec rspec spec/integration/payments/` not `rspec`" — workspace-local, useless to other workspaces).

### 2.2 — Discovery precedence

Per Anthropic spec (§1.4 above): *enterprise overrides personal, personal overrides project; plugin skills are namespaced and cannot conflict.*

Translated to loam terms:
- A workspace-local skill named `dispatch-with-gates` would override a personal skill of the same name (Anthropic's rule).
- The plugin's `loam-skills:dispatch-with-gates` would NOT conflict — it's namespaced. To invoke specifically, the user types `/loam-skills:dispatch-with-gates`; the bare `/dispatch-with-gates` could resolve to either a workspace-local override or to a personal/enterprise variant.
- For loam discipline, **workspace-local skills should not deliberately shadow plugin/base skills**. The promotion rubric in §4 detects shadowing and either flags for owner ruling or names a different skill name.

### 2.3 — Override semantics

Three cases. Each named with example:

**Case A — Workspace extends a base skill.** A workspace-local `dispatch-with-gates` file extends the base loam-skills `dispatch-with-gates` with project-specific extras (e.g., "for Eric's SaaS, dispatches must include the production-safety profile flag"). Two implementation shapes possible:

1. **Shadow with full-replacement.** Workspace authors a complete SKILL.md that overrides the base. Risk: workspace drifts from base when base updates; workspace's copy is stale; the user gets unexpectedly old behavior.
2. **Reference + extend.** Workspace authors a thin `dispatch-with-gates-eric` skill that references the base. Recommended: workspace-local skills should rename to avoid shadowing; explicit composition is more legible than implicit override.

**Case B — Plugin shadows base.** Almost never correct. If `dev-sdlc` ships a `dispatch-with-gates`, it should be named `dev-sdlc-dispatch` or similar. Plugin-namespacing protects but doesn't enforce semantic discipline.

**Case C — Workspace extends a plugin skill.** Same shape as Case A — recommend rename rather than shadow. Promotion rubric in §4 enforces this.

### 2.4 — Lifecycle (when added, when garbage-collected)

**Base skills.** Authored as part of a sealed-component amendment cycle (the v0.1.3 SKILL bundle being the precedent). Garbage-collection is a deliberate amendment cycle (deprecation → removal). Cannot be removed mid-session.

**Plugin skills.** Same as base, scoped to a plugin's own seal cycles.

**Workspace-local skills.** Created at any moment, including mid-session via the persona's `Write` tool. Garbage-collected via:

1. **Manual.** User deletes the file.
2. **Stale-detection.** A daily/weekly review skill (proposed in §3.5) walks workspace-local skills, surfaces ones that haven't fired in N days, recommends review.
3. **Promotion-driven.** Promoted skill is removed from the workspace once it lands in a plugin or base.

Live change detection (Anthropic spec, §1.4 above) means *creating a new top-level skills directory requires session restart*. So the *first* workspace-local skill ever authored in a workspace requires the user to restart Claude Code; subsequent additions/edits are picked up live. Mitigation: workspace-bootstrap should pre-create an empty `<workspace>/.claude/skills/.gitkeep` so the directory exists from session-zero. Captured as Decision B in §8.

### 2.5 — Examples of what belongs in each layer

**Base loam skills (harness-general; today + planned):**
- `memory-recall` — every loam user benefits from cross-session memory.
- `scope-decompose` — F3 is harness-wide.
- `dispatch-with-gates` — applies to any sub-agent dispatch.
- `onboarding-conversation` — session-start is universal.
- `session-handoff` — session-end is universal.
- `translation-discipline` (planned, FIDRAFT 2026-05-04) — harness-general anti-pattern checklist.
- `audit-block-on-telegram` (planned) — channel-discipline output shape; harness-general.
- `owner-decision-summary` (planned) — decision-summary format; harness-general.

**Plugin skills (`dev-sdlc/skills/`; today + planned per §5 audit):**
- `start-project` (today) — dev-sdlc workflow entry-point.
- `front-load-principle-walk` (planned, was originally proposed for loam-skills) — dev-mode behavioural; the 12-principle walk is dev-discipline.
- `dispatch-brief-authoring` (planned) — dev-mode dispatch ritual.
- `sealed-component-amendment-ship` (planned) — dev-mode shipping ritual.
- `loam-amend-cycle` (proposed §5) — wraps `loam amend apply` / `loam amend seal` / `loam amend status` discipline.
- `plan-before-code-author` (proposed §5) — turns the CDC into an invokable workflow.
- `fidraft-capture` (proposed §5) — wraps the FIDRAFT capture-at-point-of-occurrence pattern.
- `seal-narrative-writer` (proposed §5) — wraps SEAL_COMMIT.notes authoring.
- `cdc-violation-triage` (proposed §5) — when an agent surfaces a CDC violation, this skill walks the triage.
- And more per §5 below.

**Workspace-local skills (per-workspace; user-grown):**
- Pos3-local (loam-of-loam workspace) — `pos-amend-status-quick`, `pos-publish-loam-only`, `pos3-fidraft-capture` (pos3 spelling of the dev-sdlc one).
- Eric's-SaaS workspace — `eric-payment-test-quick`, `eric-staging-deploy-checklist`, `eric-pr-author-with-payments-context`.
- Hypothetical writer's workspace — `weekly-newsletter-format`, `interview-source-organize`.

The split is specific: harness primitives → base; domain primitives (where domain == "doing dev work") → plugin; project primitives → workspace.

---

## §3 — Auto-creation mechanism

This section is the most architecturally consequential and the place F2 RF must apply hardest. Luke's framing names "auto-creation"; the question is whether that's the right primitive given Claude's actual SKILL mechanism.

### 3.1 — F2 RF — "auto-creation" as Luke framed it

Luke's directive uses "auto creation of skills by primary persona within workspaces in support of the end user." The connotation is the persona detects a pattern and *autonomously* writes the SKILL.md file. Two challenges:

1. **Anthropic ships no "auto-create" API.** Per §1.4, skill registration *is* the file write. The persona authoring a SKILL.md is mechanically straightforward (the `Write` tool exists). What's missing is the *discipline* — when to author, what shape, when to commit, when to ratify. The primitive is fine; the discipline doesn't exist yet.

2. **Silent skill-creation is a known anti-pattern.** A persona that silently authors SKILLs every time the user does something twice will bloat workspace-local skills until the discovery surface becomes noisy and Claude's auto-load misfires. The promotion rubric in §4 partly handles bloat, but the auto-creation discipline must include user-ratification as a hard gate, not an after-the-fact review.

**Reframe.** "Auto-creation" should be read as **persona-proposed, user-ratified skill capture** — the persona detects the pattern, drafts the SKILL.md, and surfaces a one-line decision-question to the user ("I notice you've asked for this 3 times this week. Want me to capture it as a workspace-local skill so I auto-load it when relevant? [Y/N/show-draft]"). The user's "Y" triggers the file write. This is consistent with Luke's framing intent (the persona helps with capture) but realistic about the primitive (registration is a file write; ratification gates the write). F2 RF: name this distinction explicitly so silent-write doesn't become the failure mode.

### 3.2 — Trigger detection

When does the persona propose capturing a behavior as a skill? Six trigger signals (open list; tunable per workspace):

1. **Repeated invocation.** The persona has invoked the same multi-step procedure three or more times in N days. Concrete example: Luke has asked the persona to "run `pos pull` then `pos publish` then `git tag` then `git push --tags`" four times in a week — that's a `pos-release-tag` workspace-local skill candidate.
2. **Explicit user request.** Luke says "remember this", "make this a thing", "let's codify this". Strong signal — propose immediately.
3. **CLAUDE.md drift detection.** A CLAUDE.md section has grown to look like a procedure (Anthropic's own auto-prompt: *"a section of CLAUDE.md has grown into a procedure rather than a fact"*). Extract the procedure as a skill; thin the CLAUDE.md.
4. **Memory-recall hit pattern.** When the persona's M-FBM retrieval lands the same prior-turn episode three times in a week as relevant prior context, the pattern in that episode is a skill candidate.
5. **Dispatch-prompt scaffolding repetition.** When the same dispatch prompt scaffold appears in 3+ dispatches with only project-specific values changing, it's a skill template candidate.
6. **Hook-trigger pattern.** When a hook fires the same warning (e.g., "you didn't run plan-before-code") repeatedly across sessions, the corrective behavior is a skill candidate.

These signals are imperfect — false-positives are inevitable. The user-ratification gate (§3.3) is the structural defense.

### 3.3 — Capture workflow (proposed)

1. **Detect + draft.** Persona writes draft to `<workspace>/.scratch/claude-output/skill-draft-<name>.md` (not yet `.claude/skills/`). Draft uses the 6-section template (What / When / How / Graceful degradation / Composition / Out of scope).
2. **Surface decision-question.** "I noticed [pattern] N times in M days. Capture as workspace-local skill? Draft at `<path>`. Y / N / R(evise)."
3. **Ratify.** Y → move draft to `<workspace>/.claude/skills/<name>/SKILL.md`. R → iterate on user feedback. N → drop + record rejection (cool-down so same trigger doesn't re-propose for 14 days).
4. **First-skill restart hint** (if `.claude/skills/` didn't pre-exist) — see Decision B for pre-create mitigation.
5. **Persona auto-loads** in next relevant turn via Claude Code's native discovery.
6. **Quarterly review** per §4 rubric.

Workflow gated on dev-mode partition + opt-in flag (Decision C).

### 3.4 — Skill-content authoring — generated vs structured fill-in-blanks

Two modes:

**Mode 1 — Generated.** Persona drafts the full SKILL.md autonomously, modeling on the 6-section template + the trigger-pattern observed. Pro: low friction. Con: persona may misframe the pattern; user catches it at review.

**Mode 2 — Structured fill-in-blanks.** Persona presents a template with named sections; user fills in (potentially via short Q&A — "what's the trigger phrase you want this to fire on?"). Pro: user-precision. Con: more friction; user may give up.

**Recommendation.** **Mode 1 with explicit "this draft may be wrong; review it" framing.** The user reviews the draft anyway; making them author it primary is unnecessary friction. The persona's drafts will improve over time as it accumulates patterns of which trigger-types map to which body shapes. Captured as Decision D in §8.

### 3.5 — Failure modes

| # | Failure | Mitigation |
|---|---|---|
| 1 | Skill bloat (auto-load misfires; description budget exceeded) | Cool-down (14d post-rejection); quarterly rubric retirement; hard-cap at 20 |
| 2 | Domain-noise mistaken for pattern | Trigger requires text+structural overlap; user-ratification gate; bad skills demoted via rubric |
| 3 | User-ratification fatigue | Threshold tunable; cool-down; "decline-all-this-session"; per-week budget (3 default) |
| 4 | Workspace-local shadows future plugin name | Convention: workspace-prefix (`pos3-`, `eric-`); rubric review catches; namespace defense partial (Decision K) |
| 5 | Method-in-skill smuggling | Template checklist "pattern or instance?"; rubric quality signal catches |
| 6 | Auto-creation fires before user is ready | Single gate: `enable_auto_skill_capture` flag default false; user opts in when ready (Decision C, E). Universal availability across workflows is correct per Luke's 2026-05-04 clarification. |

### 3.6 — Three-tier gating (auto-creation universal, promotion dev-scoped)

Luke's framing was clarified across two same-day corrections (2026-05-04 messages 9951, 9953). Final gating model:

- **Auto-creation:** UNIVERSAL — any loam user, dev or non-dev. Especially valuable for non-devs whose patterns rarely fit the dev-tooling shape (writers capturing reusable rhetorical structures; researchers capturing methodology checklists; ops people capturing runbooks). Auto-creation is the persona's bidirectional translation extended to "this pattern recurs; make it explicit and invokable."
- **Promotion to a plugin:** plugin-dev-only — only the dev who owns the plugin can graduate workspace-local skills into it (or refuse). Eric's workspace-local skills don't promote unless Eric owns a loam plugin, which he doesn't.
- **Promotion to base loam:** loam-dev-only — only Luke (canonical loam owner) can graduate skills into the base set.

A single workflow-level gate refines this: even though auto-creation is universal, it remains **opt-in via a workspace-config flag** (`enable_auto_skill_capture: true`, default false). Reasoning: a fresh workspace shouldn't immediately start proposing skills — the user turns it on when they're ready. Captured as Decision E.

This satisfies the partition rule with the corrected placement:
- The auto-creation **mechanism** lives in `framework/` (every loam user benefits, including non-dev users — auto-creation is harness-general).
- The auto-creation **config flag** lives in `framework/workspace-bootstrap/` (config primitive co-located with the mechanism it gates).
- The **layered architecture** (base / plugin / workspace-local skill discovery) lives in `framework/` (every loam user benefits from layered discovery).
- The **promotion rubric** lives in `plugins/dev-sdlc/skills/skill-promotion-review/` (dev-scoped — only loam-devs and plugin-devs need to promote workspace-locals upward).

---

## §4 — Promotion rubric (workspace-local → plugin / base)

Workspace-local skills accumulate. Some are workspace-junk. Some are real toolkit additions that deserve graduation. The rubric is the disciplined evaluation surface.

### 4.1 — The six signals

For each candidate workspace-local skill being evaluated for promotion:

**Signal 1 — Reusability.** Does this skill describe a pattern that applies beyond this specific workspace? Concrete test: can the skill's body be re-read with this workspace's specifics removed and still convey a meaningful pattern? If yes → reusability signal: STRONG. If "but only for dev workspaces" → reusability signal: MEDIUM (graduate to plugin, not base). If "only useful in this workspace" → reusability signal: WEAK (stays workspace-local).

**Signal 2 — Quality.** Is the SKILL.md well-formed? Does it match the 6-section body shape (What / When / How / Graceful degradation / Composition / Out of scope)? Does it pass `test_AC_LSK_2_frontmatter_well_formed.py`-equivalent checks? Does the description carry a trigger phrase? Quality signal: PASS / FAIL / NEEDS-REVISION.

**Signal 3 — Test coverage.** Does the skill have AC-shaped tests proving it does what it claims? For graduated-to-plugin/base skills, this is a hard requirement — every base/plugin skill must carry tests (the 5 sealed at f04e925 do; the 3 test files cover frontmatter, body shape, and presence). Workspace-local skills don't need tests. *Promotion requires authoring tests.* Test-coverage signal: HAS-TESTS / NEEDS-TESTS.

**Signal 4 — Usage.** Has the skill actually fired N times in actual use? Concrete metrics:
- Auto-load by Claude (persona's description matched user intent): ≥ 5 fires in last 30 days.
- User-invoked (`/<skill-name>`): ≥ 2 fires in last 30 days.
- Total fires across all loam users (post-promotion-eligible if applicable): ≥ 10 fires aggregate.
Usage signal: STRONG / MEDIUM / WEAK / NONE.

**Signal 5 — Conflict.** Does this skill overlap with an existing plugin or base skill? If yes:
- *Same scope.* Skill is a duplicate; deprecate the workspace-local in favor of the existing.
- *Wider scope (workspace-local subsumes existing).* Promote the new one with a deprecation pointer to the older one.
- *Narrower scope (existing subsumes workspace-local).* Workspace-local is a refinement; consider folding into the existing or keeping workspace-specific.
- *Adjacent scope (overlapping but distinct).* Both stay; clarify the boundary.
Conflict signal: NO-CONFLICT / DUPLICATE / WIDER / NARROWER / ADJACENT.

**Signal 6 — Categorization.** Per the partition rule: is this skill dev-specific (→ plugin) or harness-general (→ base)? Test: would a non-dev loam user (Eric, a writer, anyone using loam-as-product) benefit from this skill? Categorization signal: HARNESS-GENERAL / DEV-SPECIFIC / PROJECT-SPECIFIC.

### 4.2 — Promotion-decision matrix

Combining the signals:

| Reusability | Categorization | Quality | Tests | Usage | Conflict | Recommendation |
|---|---|---|---|---|---|---|
| STRONG | HARNESS-GEN | PASS | YES or AUTHOR | STRONG | NO-CONFLICT | **Promote to base** (`plugins/loam-skills/`) |
| STRONG | DEV-SPECIFIC | PASS | YES or AUTHOR | STRONG | NO-CONFLICT | **Promote to plugin** (`plugins/dev-sdlc/skills/`) |
| MEDIUM | DEV-SPECIFIC | PASS | YES or AUTHOR | MEDIUM+ | NO-CONFLICT | **Promote to plugin** |
| WEAK | PROJECT-SPECIFIC | (any) | (any) | (any) | NO-CONFLICT | **Stay workspace-local** |
| (any) | (any) | FAIL | (any) | (any) | (any) | **Author-time fix** before any promotion |
| (any) | (any) | (any) | NEEDS-TESTS | (any) | (any) | **Author tests** before promotion |
| (any) | (any) | (any) | (any) | NONE / WEAK | (any) | **Defer** — not enough usage data |
| (any) | (any) | (any) | (any) | (any) | DUPLICATE | **Deprecate** workspace-local |
| (any) | (any) | (any) | (any) | (any) | WIDER | **Promote with deprecation pointer** |
| (any) | (any) | (any) | (any) | (any) | NARROWER | **Fold into existing** or keep workspace-specific |

The matrix is human-readable; the persona walks it during the quarterly (or on-demand) review.

### 4.3 — Graduation workflow

1. **Trigger.** Quarterly review (every 90 days) OR on-demand ("review my workspace skills"). The reviewer skill (proposed: `plugins/dev-sdlc/skills/skill-promotion-review/`) walks the workspace's `.claude/skills/` directory.
2. **Evaluate each.** For each workspace-local skill, the persona computes the six signals (some are auto-detectable, others need owner judgment). Output: a structured table with recommendations.
3. **Owner reviews.** Owner walks the table, accepts/rejects each recommendation. Default-to-no for promotion (per the Eric-sequence Decision I pattern — explicit ratification at production-stake-equivalent decisions).
4. **Author tests for promotions.** For each accepted promotion, dispatch a sub-agent to author the AC-shaped tests (per the precedent of the 5 sealed packages' `test_AC_LSK_*.py` files).
5. **Land in target plugin/base.** Move the SKILL.md from `<workspace>/.claude/skills/<name>/` to `plugins/loam-skills/skills/<name>/` (base) or `plugins/dev-sdlc/skills/<name>/` (plugin). Author the manifest. Run the loam-amend cycle. Seal.
6. **Remove workspace-local copy.** The promoted skill is now available via the plugin; the workspace-local copy is removed (or replaced with a single-line "moved-to-plugin" pointer).

### 4.4 — Demotion + approval

**Demotion path.** Persona surfaces "skill X fired N times since promotion; demote or retire?"; owner rules; demotion = corrective amendment cycle (skill returns to workspace-local OR retires entirely with narrative captured). Rare; treated as explicit visible amendment, not routine. Decision F in §8.

**Approval gate.** Owner-only, default-to-no for promotions. Persona auto-recommends; owner ratifies. Promotions are contract-binding (other users inherit). Mirrors Eric-sequence Decision I + amendment-cycle gate-review precedent. Decision G in §8.

---

## §5 — Dev-sdlc skill-ification analysis

This section audits `plugins/dev-sdlc/` for behaviors that should be SKILL-shaped but currently aren't. For each candidate: behavior, why SKILL vs left as tooling/doc, frontmatter + body outline, AI-time, composition.

### 5.1 — Inventory of dev-sdlc surfaces

Per `ls plugins/dev-sdlc/`:

```
docs/         (cdcs/ + conventions/ + ODD methodology + smoke-test-discipline + duration-rubric)
hooks/        (agent_guard, bash_guard, dispatch_setup_hook, objective_binding_gate, tdd_guard)
skills/       (start-project.md — flat-shape, 1 skill)
src/          (loam plugin Python source)
templates/    (component, dispatch, plan)
tests/
tools/        (loam-amend, loam-mode)
dev-mode-manifest.yaml
```

Skills are 1; the rest is docs / hooks / tools / templates.

### 5.2 — Candidate SKILLs derived from each surface

Below: 12 candidates with placement, source, and one-line trigger description (full frontmatter authored at SKILL-build time per `feedback_agent_prompts_scope_only`).

**From `docs/cdcs/`** (the CDCs that describe behaviors, not just principles):

1. **`plan-before-code-author`** (dev-sdlc) — Before writing any source code for a build, author a plan-doc at `docs/rebuild/plans/<name>.md` naming objective, scope, ACs, fence, named decisions. Source: `cdcs/plan-before-code.md`.
2. **`audit-finding-triage`** (dev-sdlc) — When persona or sub-agent discovers an unexpected finding (out-of-fence drift, ODD violation, stale convention), classify by four-bucket triage (in-band fix / FIDRAFT / halt-and-surface / retire). Source: `cdcs/audit-finding-triage.md`.
3. **`graceful-fallthrough-with-detection`** (dev-sdlc) — When authoring fallback paths (try/except, default-value, graceful-degrade), include detection + surface so fallback is observable. Source: `cdcs/graceful-fallthrough-with-detection.md`.

**From `docs/conventions/`:**

4. **`loam-amend-cycle`** (dev-sdlc) — Run the loam amendment cycle: sub-plan → manifest → `loam amend apply` → `loam amend seal` → record SHA in roadmap §8. Replaces FIDRAFT 2026-05-04 entry "sealed-component-amendment-ship". Source: `conventions/amendment-cycle.md`.
5. **`fidraft-capture`** (dev-sdlc) — Capture improvement idea/observation/follow-up to `FUTURE_IDEAS_DRAFT.md` at point-of-occurrence. Source: `conventions/fidraft-pattern.md`.
6. **`seal-narrative-writer`** (dev-sdlc) — Author `SEAL_COMMIT.notes` capturing what shipped/deferred/surfaced. Composes with `loam-amend-cycle`. Source: `conventions/sealed-component-invariants.md`.
7. **`plan-docs-author`** (dev-sdlc) — Author plan-doc in loam's standard shape (objective / scope / principles / exec summary / decisions / version sequence / partition audit / honest doubts). Source: `conventions/plan-docs.md`.

**From `hooks/`** (hooks enforce structurally; the *user behavior on fire* is SKILL-shaped):

8. **`hook-violation-recovery`** (dev-sdlc) — When a loam hook fires (agent_guard / tdd_guard / objective_binding_gate / bash_guard refuses), read the hook's message, identify the violation, fix, retry. Source: `hooks/*`.

**From `templates/`:**

9. **`dispatch-brief-authoring`** (dev-sdlc; reclassified from FIDRAFT 2026-05-04 loam-skills placement per partition rule) — Author dispatch brief using loam's template shape (objective + scope + constraints + halt + ODD-check + principles propagation + model rationale). Source: `templates/dispatch/`.
10. **`component-scaffold-author`** (dev-sdlc) — Scaffold a new sealed-component using `templates/component/` (rare; for new `framework/<comp>/` or `plugins/<plugin>/`). Source: `templates/component/`.

**From `tools/loam-amend/`:**

11. **`loam-amend-status-quick`** (dev-sdlc) — Interpret `loam amend status` output: identify next step (apply / seal / wait), surface halt conditions, recommend next command. Source: `tools/loam-amend/`.

**Cross-cutting from FIDRAFT 2026-05-04 (reclassified):**

12. **`front-load-principle-walk`** (dev-sdlc; reclassified from FIDRAFT loam-skills placement) — At start of every non-trivial turn, walk active principles by name and surface application. The 12-principle walk is dev-mode discipline (non-dev users have a thinner stack). Source: FIDRAFT 2026-05-04.

`tools/loam-mode/` (admin tooling) — skipped; SKILL wrapping is low-value for partition-selector CLI.

### 5.3 — Summary of candidates + AI-time

| # | Candidate | Placement | AI-time | Source |
|---|---|---|---|---|
| 1 | `plan-before-code-author` | dev-sdlc | 1–2 h | CDC |
| 2 | `audit-finding-triage` | dev-sdlc | 1–2 h | CDC |
| 3 | `graceful-fallthrough-with-detection` | dev-sdlc | 1–2 h | CDC |
| 4 | `loam-amend-cycle` | dev-sdlc | 2–3 h | Convention + FIDRAFT (was "sealed-component-amendment-ship") |
| 5 | `fidraft-capture` | dev-sdlc | 1–2 h | Convention |
| 6 | `seal-narrative-writer` | dev-sdlc | 1 h | Convention |
| 7 | `plan-docs-author` | dev-sdlc | 1–2 h | Convention |
| 8 | `hook-violation-recovery` | dev-sdlc | 1–2 h | Hooks behavior |
| 9 | `dispatch-brief-authoring` | dev-sdlc | 1–2 h | Templates + FIDRAFT 2026-05-04 |
| 10 | `component-scaffold-author` | dev-sdlc | 1–2 h | Templates |
| 11 | `loam-amend-status-quick` | dev-sdlc | 1 h | Tools |
| 12 | `front-load-principle-walk` | dev-sdlc | 1–2 h | FIDRAFT 2026-05-04 (reclassified from loam-skills per partition rule) |

**Total dev-sdlc SKILL-ification AI-time band:** 13–24 h for all 12 candidates.

Plus from FIDRAFT 2026-05-04 (the persona-behavior bundle), the harness-general candidates that stay in loam-skills:
- `translation-discipline` — base loam-skills, ~1–2 h.
- `audit-block-on-telegram` — base loam-skills, ~1 h.
- `owner-decision-summary` — base loam-skills, ~1 h.

**Total base-loam-skills additions AI-time band:** 3–5 h for these three.

### 5.4 — What's NOT a SKILL candidate from dev-sdlc

Important to flag (over-shipping is its own risk):

- **`docs/odd-methodology.md` (~500 lines)** — too long for a skill body (Anthropic note: keep SKILL.md under 500 lines). It's reference content. The SKILLs that REFERENCE odd-methodology are appropriate; the doc itself stays a doc.
- **`docs/odd-in-loam.md`** — same.
- **`docs/duration-estimation-rubric.md`** — reference; tables don't need skill-ification.
- **`hooks/<each>.py`** — Python hooks; deterministic enforcement, not skill-shaped.
- **`src/loam/plugins/`** — Python source; not skill-shaped.
- **`tests/`** — tests; not skill-shaped.

### 5.5 — Composition with existing surface

For each SKILL candidate, name what it composes with:

- Candidates 1, 2, 3, 4, 5, 6, 7, 9, 10 — compose with the corresponding doc/CDC/convention as primary reference; the SKILL is the *invokable workflow*, the doc is the *deep reference*.
- Candidate 8 (hook-violation-recovery) — composes with all 5 hooks as the user-side handler.
- Candidate 11 (loam-amend-status-quick) — composes with the `loam-amend` CLI as a wrapper.
- Candidate 12 (front-load-principle-walk) — composes with `~/.claude/CLAUDE.md` global principles + the per-workspace persona prompt.

**Net pattern.** Every SKILL has a primary reference (doc, tool, hook, template). The SKILL is the *invokable trigger* + *condensed checklist*; the reference is the *full detail*. This matches Anthropic's framing: *"Unlike CLAUDE.md content, a skill's body loads only when it's used, so long reference material costs almost nothing until you need it."*

---

## §6 — Connection to existing work + Eric sequence

### 6.1 — The persona-behavior FIDRAFT bundle (2026-05-04)

Six candidates. Per the partition rule:

| # | Candidate | Original placement (FIDRAFT) | Reclassified (this plan) |
|---|---|---|---|
| 1 | translation-discipline | loam-skills | **loam-skills** (harness-general) |
| 2 | audit-block-on-telegram | loam-skills | **loam-skills** (harness-general) |
| 3 | front-load-principle-walk | loam-skills | **dev-sdlc/skills/** (dev-mode discipline) |
| 4 | dispatch-brief-authoring | loam-skills | **dev-sdlc/skills/** (dev-mode dispatch ritual) |
| 5 | sealed-component-amendment-ship | loam-skills | **dev-sdlc/skills/** (renamed `loam-amend-cycle`; dev-only) |
| 6 | owner-decision-summary | loam-skills | **loam-skills** (harness-general) |

Net: 3 stay in loam-skills (base); 3 move to dev-sdlc (plugin). The FIDRAFT entry's original placement should be updated. Captured as a sub-action in §7 implementation plan.

### 6.2 — Eric SaaS-app sequence connection

Per `eric-saas-app-use-case-version-sequence-2026-05-04.md` (just landed at `ab98fb2`). The Eric path includes:

- **v0.1.7 — subagent personas + PM** (G4 + G5): subagents are dev-specific (per partition rule, `plugins/dev-sdlc/agents/`); PM is harness-general (`framework/per-project-pm/`).
- **v0.1.8 — ODD-RE heavy** (G1 + G6 + G9): all dev-specific (`plugins/dev-sdlc/odd-extractor/`).
- **v0.1.9 — PR-safety gate** (G2 + G8): all dev-specific (`plugins/dev-sdlc/pr-safety/`).
- **v0.2.0 — codebase-watch** (G10): mostly dev-specific.
- **v0.2.1 — Eric-deliverable smoke + onboarding hardening**.

**Where layered-skills fit in the Eric sequence:**

- **The base/plugin/workspace-local architecture (§2)** is harness-general — it's a prerequisite for the Eric path's subagent personas (a workspace's `.claude/agents/` for subagents and `.claude/skills/` for workspace-local skills compose as a discovery-surface pair). Should land BEFORE v0.1.7.
- **Dev-sdlc skill-ification (§5)** is dev-only — composes with v0.1.7 (subagent personas reference these skills) and v0.1.8 (ODD-RE invokes some of them). Should land BEFORE v0.1.7 OR as part of v0.1.7's preparation.
- **Auto-creation + promotion rubric (§3 + §4)** is dev-only — useful for the Luke-loam-of-loam workspace and for Eric's workspace ONLY if Eric explicitly enables (default off). Sequenced AFTER the core dev-sdlc skill-ification lands (the rubric needs the existing skill set to evaluate against).
- **The vertical-swarming FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md` per-project-PM scoping)** — the per-project PM might own the workspace-skill set (workspace-local skills are project-state, PM is project-coordinator). Auto-creation could plausibly be PM-driven rather than primary-persona-driven. Surface as Decision H in §8.

### 6.3 — Vertical-swarming + per-project-PM composition

Per `FUTURE_IDEAS_DRAFT.md` entries on per-project PM (line 25) and vertical-swarming. The PM lives in `<workspace>/.loam/pms/<pm-name>/`. The per-project PM's responsibilities include "the in-flight change list" and "Eric's preferences" and "the audit trail of past changes."

**Workspace-local skills compose with per-project PM.** When a PM exists in a workspace, workspace-local skills could plausibly live under the PM's directory rather than `<workspace>/.claude/skills/`. Two shapes:

1. **Workspace-skills under `<workspace>/.claude/skills/`** (Anthropic-native discovery). PM references the skill set; PM does not own.
2. **Workspace-skills under `<workspace>/.loam/pms/<pm-name>/skills/`** (PM-owned). Custom discovery — Claude Code wouldn't find them natively; loam would need to symlink to `.claude/skills/` or use `--add-dir` to surface.

**Recommendation.** Option 1 (Anthropic-native location). PM references the workspace-skill set; doesn't own it. Reasoning: Lens 1 (Claude-leverage-first) prefers native discovery; PM ownership creates a custom surface that doesn't compose. Captured as Decision I in §8.

---

## §7 — Implementation plan (version sequence)

Sequenced post-v0.1.5 (the current roadmap horizon). Some items can fold into existing roadmapped releases; others warrant new versions.

### 7.1 — Sequence

**v0.1.6 — base-skills harness-general additions (3 SKILLs).** Ships the 3 reclassified loam-skills additions (`translation-discipline`, `audit-block-on-telegram`, `owner-decision-summary`). Single sealed-component amendment cycle on `plugins/loam-skills/`. AI-time: 3–5 h. Composes cleanly with v0.1.6 from the Eric sequence (production-safety mode); both are small surface additions.

**v0.1.7 — layered-skill architecture mechanism.** Ships:
- Workspace-bootstrap pre-creates `<workspace>/.claude/skills/.gitkeep` to enable live-discovery (per Decision B). `framework/workspace-bootstrap/` amendment.
- `plugins/loam-skills/` enrolled in `bootstrap.yaml` `contributions:` list (this is the bug from §1.3 — the plugin doesn't auto-enable in workspaces today). `framework/workspace-bootstrap/` amendment.
- `plugins/loam-skills/` admitted to `dev-mode-manifest.yaml` `roots:` and `always_loaded:`. `plugins/dev-sdlc/` amendment.
- Design-note `docs/design/layered-skill-architecture.md` articulating the three layers, override semantics, lifecycle. Doc-only.
AI-time: 4–6 h.

**v0.1.8 — dev-sdlc skill-ification first pass (6 SKILLs).** Ship the 6 highest-value dev-sdlc candidates from §5 — choose by AI-time + dependency on existing CDCs/conventions:
- `loam-amend-cycle` (highest leverage; ritual-dense)
- `dispatch-brief-authoring` (highest fire-rate; replaces every dispatch-prompt's scaffold)
- `plan-before-code-author` (high CDC-anchor)
- `fidraft-capture` (frequent use)
- `front-load-principle-walk` (turn-start)
- `audit-finding-triage` (medium fire-rate)

Single sealed-component amendment cycle on `plugins/dev-sdlc/`. AI-time: 8–12 h. Composes with the Eric-sequence v0.1.7 (subagent personas) — these SKILLs are referenced by subagent personas.

**v0.1.9 — dev-sdlc skill-ification second pass (6 SKILLs).** Ship the remaining 6 candidates from §5:
- `seal-narrative-writer`
- `plan-docs-author`
- `hook-violation-recovery`
- `component-scaffold-author`
- `graceful-fallthrough-with-detection`
- `loam-amend-status-quick`

Single sealed-component amendment cycle on `plugins/dev-sdlc/`. AI-time: 5–10 h. Lower-priority than v0.1.8's 6.

**v0.2.0 — auto-creation mechanism (UNIVERSAL — any workflow).** Ship the auto-creation skill capture workflow as a SKILL itself + the supporting workspace-config flag. Lives in `plugins/loam-skills/skills/skill-capture-proposal/` (harness-general; not dev-only per Luke's 2026-05-04 clarification — auto-creation benefits non-devs especially). AI-time: 6–10 h. Includes:
- The `skill-capture-proposal` SKILL — the workflow from §3.3.
- The `enable_auto_skill_capture` workspace-config flag in `framework/workspace-bootstrap/`.
- The 6 trigger-detection signals from §3.2 implemented as detection logic.
- Tests covering the proposal-draft workflow.
- Design note `docs/design/persona-driven-skill-capture.md`.

**v0.2.1 — promotion rubric mechanism (DEV-ONLY).** Ship the promotion rubric as a SKILL — `plugins/dev-sdlc/skills/skill-promotion-review/`. AI-time: 4–8 h. Includes:
- The 6-signal evaluation logic from §4.1.
- The promotion-decision matrix from §4.2.
- The graduation workflow from §4.3.
- The demotion path from §4.4.
- Quarterly-review trigger (composes with scheduled-scope primitive).

### 7.2 — Total AI-time

| Version | What | AI-time |
|---|---|---|
| v0.1.6 | 3 base-skills additions | 3–5 h |
| v0.1.7 | layered-skill architecture mechanism | 4–6 h |
| v0.1.8 | dev-sdlc 6 SKILLs (first pass) | 8–12 h |
| v0.1.9 | dev-sdlc 6 SKILLs (second pass) | 5–10 h |
| v0.2.0 | auto-creation mechanism | 6–10 h |
| v0.2.1 | promotion rubric mechanism | 4–8 h |
| **Total** | | **30–51 h** |

This is mostly skill authoring (each SKILL is ~1–2 h plus tests). The mechanism work (auto-creation + promotion) is the higher-uncertainty part.

### 7.3 — Sequencing dependencies

```
v0.1.5 (current roadmap end)
  │
  ▼
v0.1.6 — base-skills additions ──┐
  │                               │ (parallel-safe)
  ▼                               │
v0.1.7 — layered-skill arch ◄─────┘
  │
  ▼
v0.1.8 — dev-sdlc skill-ification 1 ──┐
  │                                    │ (parallel-safe at plan-author stage)
  ▼                                    │
v0.1.9 — dev-sdlc skill-ification 2 ◄──┘
  │
  ▼
v0.2.0 — auto-creation (needs critical-mass of skills to be useful)
  │
  ▼
v0.2.1 — promotion rubric (needs accumulated workspace-locals to evaluate)
```

Internal-to-release dependencies handled per existing `feedback_serialize_amendment_builds` (no two amendment builds in the same working tree).

### 7.4 — Eric-sequence interleave

The Eric sequence has its own version path (v0.1.6–v0.2.2 in the Eric research doc). Two sequences are not the same numbering — they collide on v0.1.6+. Reconciliation options:

1. **Renumber.** The Eric sequence uses v0.1.6–v0.2.2; this layered-skill sequence uses v0.1.6–v0.2.1. Shift one of them to avoid collision.
2. **Interleave.** Each version number bundles items from both sequences (e.g., v0.1.6 = production-safety mode FROM Eric + 3 base-skills FROM this plan).

**Recommendation.** Interleave. Both sequences derive from the same overall capability roadmap; treating them as parallel versions creates a confusing release cadence. The Eric sequence's v0.1.6 (production-safety mode) and this plan's v0.1.6 (3 base-skills) are both small (~3–10 h each); bundle them into a single v0.1.6 release. Subsequent versions interleave similarly. Captured as Decision J in §8.

---

## §8 — Decisions Luke needs to rule on

Tight list. Each: question + recommendation + brief reasoning.

**Decision A — Enroll `plugins/loam-skills/` in `bootstrap.yaml` `contributions:` at v0.1.7?** *Recommendation:* **Yes.** v0.1.3 SKILLs aren't actually discovered today (v0.1.0-shipper-tripping bug). Fix at next mechanism touch.

**Decision B — Workspace-bootstrap pre-creates `<workspace>/.claude/skills/.gitkeep`?** *Recommendation:* **Yes.** Anthropic's live-change-detection requires the dir exist at session-start; pre-creating eliminates the session-restart UX cost on first skill capture.

**Decision C — Auto-creation gating: workflow-flag-only or also dev-mode?** *Recommendation:* **Workflow-flag only, default false.** Per Luke's 2026-05-04 clarification (messages 9951, 9953), auto-creation is universal — any loam user, dev or non-dev; non-devs especially benefit. Dev-mode gate REMOVED from earlier draft. Single gate is the `enable_auto_skill_capture` workspace-config flag (default false; user opts in when ready). Mitigate discoverability via first-run-inventory hint.

**Decision D — Skill drafting: Mode 1 (persona drafts full) or Mode 2 (fill-in-blanks)?** *Recommendation:* **Mode 1 with explicit "review carefully" framing.** Lower friction; review catches misframing. Switch to Mode 2 if user fatigue surfaces in practice.

**Decision E — Per-week proposal budget on auto-creation?** *Recommendation:* **3/week, tunable.** Without cap, fatigue is the failure mode. Explicit user-request bypasses the cap.

**Decision F — Demotion path: explicit amendment cycle or lighter-weight?** *Recommendation:* **Explicit amendment cycle.** Demotion changes sealed components; should be visible. Low frequency means friction is a non-issue.

**Decision G — Promotion approval: owner-only or persona-auto?** *Recommendation:* **Owner-only, default-to-no.** Promotions are contract-binding; auto-promote is the silent-precedent failure. Quarterly batches keep owner-review tractable.

**Decision H — Per-project PM as auto-creation driver?** *Recommendation:* **Primary persona for now; revisit when PM ships (Eric-sequence v0.1.7).** Designing against an unbuilt component is premature.

**Decision I — Workspace-local skill location: `<workspace>/.claude/skills/` or `<workspace>/.loam/pms/<pm>/skills/`?** *Recommendation:* **`<workspace>/.claude/skills/`** (Anthropic-native). Lens 1 favors native discovery; PM-owned creates custom surface. Migration is low-friction if revisited later.

**Decision J — Reconcile this sequence with Eric sequence: renumber or interleave?** *Recommendation:* **Interleave.** Both derive from same roadmap; parallel sequences = confusing cadence. v0.1.6 = production-safety + 3 base-skills; v0.1.7 = subagent personas + PM + layered-skill mechanism; etc.

**Decision K — Workspace-local skill auto-prefix convention (pos3-* / eric-*)?** *Recommendation:* **Convention-suggested first; structural-enforce at v0.2.x if collisions observed.** Auto-prefix has UX cost; rubric review catches shadowing.

**Decision L — Promotion rubric: ship full 6-signal or start with 3?** *Recommendation:* **Start with 3** (Categorization + Quality + Conflict) at v0.2.1; add Reusability + Usage + Tests later when telemetry supports measured Usage.

**Decision M — Auto-creation proposes SKILL or feedback-file or both?** (Per §9.1.) *Recommendation:* **Both options surfaced; persona suggests default by pattern shape (SKILL for trigger-shaped, feedback-file for principle-shaped); user overrides.**

**Decision N — Auto-creation v0.2.0 scope: MVP or full §3?** *Recommendation:* **MVP at v0.2.0** (explicit-request + ask-and-answer + dev-only gate). Layer in passive triggers + cool-down + budget at v0.2.x follow-ons based on observed usage.

---

## §9 — Honest doubts + F2 RF

The places this plan is least confident.

### 9.1 — Is "auto-creation" actually a skill-shaped operation, or a memory-feedback-file-shaped one?

This is the strongest F2 RF question. The persona could:

1. **Author a SKILL.md** (this plan's recommendation).
2. **Write a memory-feedback-file** (the global CLAUDE.md pattern — `feedback_<name>.md` files in `~/.claude/projects/<project>/memory/`).
3. **Both.**

Shape comparison:

- **SKILL.md** advantages: invokable as `/<name>`, auto-loaded by Claude when description matches, lives in workspace-state, namespaced, supports subagent forking + dynamic context injection.
- **Memory-feedback-file** advantages: lighter-weight (no schema), already a pattern Luke uses (~30 feedback files in his memory), composes with cross-session memory, doesn't bloat skill discovery surface.

When does each fit?

- **SKILL.md** for behaviors with clear trigger phrases + bounded execution shape (the 6 candidates from FIDRAFT 2026-05-04 fit).
- **Memory-feedback-file** for principles + discipline rules + observation-derived patterns that should ALWAYS apply (most of Luke's existing 30 feedback files).

The honest answer: *both, with a discrimination test.* The persona's auto-creation workflow should propose the right shape:
- "I notice you've asked for [pattern] N times — want me to capture as: [a] SKILL (invokable when relevant), [b] feedback-file (always-applied principle), [c] both?"

This adds a sub-decision to the §3.3 capture workflow. Captured as Decision M (added).

**Decision M — Auto-creation proposes SKILL or feedback-file or both?**

**Question.** Per §9.1.

**Recommendation.** **Both options surfaced; user picks.** Default: SKILL for trigger-shaped patterns, feedback for principle-shaped patterns; let user override.

**Risk if wrong.** Adds friction to the proposal step. Mitigation: persona suggests a default based on pattern shape; user accepts default 80% of the time.

### 9.2 — Does the promotion rubric work in practice?

No precedent in loam history. Concerns: Signal 4 (usage count) requires telemetry that doesn't exist yet (Claude Code doesn't track per-skill fires natively); Signal 1 (reusability) is judgment-heavy; 6-signal matrix may collapse to "looks-good / needs-work" in practice.

**Decision L — Ship full 6-signal rubric or start with 3?** **Start with 3** (Categorization + Quality + Conflict) at v0.2.1; add Reusability + Usage + Tests at later versions when cost-governance telemetry can support measured Usage.

### 9.3 — Workspace-local skill discovery: empirically verified?

Anthropic spec confirms `.claude/skills/<name>/SKILL.md` discovery. Loam has not tested project-shape (only plugin-shape via the 5 sealed at `f04e925`). v0.1.7 implementation must include a smoke: create `<workspace>/.claude/skills/test-discovery/SKILL.md` in pos3, verify it appears in `/` menu. Halt-and-surface if discovery fails.

### 9.4 — Are 12 dev-sdlc SKILLs too many?

Description-budget cap (1,536 chars/skill; 1% context window total) = ~25+ skills total may exceed budget. Mitigation: ship in two waves (v0.1.8 = 6, v0.1.9 = 6); measure after wave 1; merge or deprioritize if degradation observed. F4 — uncertainty justifies incremental shipping.

### 9.5 — Auto-creation might be over-engineered

Simplest version: persona detects pattern, asks "want a skill?". Three options: yes/no/edit. No detection signals, no cool-down, no per-week budget.

The §3 design layers in 6 triggers, cool-down, per-week budget, 6 failure modes. F2 RF: this mechanism is justified IF auto-creation fires often (multiple times/week); overkill if rare.

**Decision N — Auto-creation v0.2.0 scope: MVP or full §3?** **MVP at v0.2.0** (explicit-request trigger + ask-and-answer + dev-only gate). Layer in passive triggers, cool-down, budget at v0.2.x follow-ons based on observed usage.

---

## §10 — Partition-rule placement audit

| Capability | Placement | Reasoning |
|---|---|---|
| Layered-skill architecture mechanism | `framework/workspace-bootstrap/` | Harness-general — every loam user benefits from layered discovery |
| Base loam-skills additions (3 SKILLs: translation-discipline, audit-block-on-telegram, owner-decision-summary) | `plugins/loam-skills/skills/` | Harness-general patterns |
| Dev-sdlc skill-ification (12 SKILLs from §5) | `plugins/dev-sdlc/skills/` | Dev-mode-only |
| Workspace-local skill directory | `<workspace>/.claude/skills/` (Anthropic-native) | Harness-general (Claude Code surface) |
| Auto-creation mechanism | `plugins/loam-skills/skills/skill-capture-proposal/` | UNIVERSAL per Luke 2026-05-04 clarification — any loam user; non-devs especially benefit |
| Auto-creation config flag (`enable_auto_skill_capture`) | `framework/workspace-bootstrap/` | Config primitive is harness-general; co-located with mechanism it gates |
| Promotion rubric | `plugins/dev-sdlc/skills/skill-promotion-review/` | Dev-only — Eric doesn't promote skills |
| Design-note `layered-skill-architecture.md` | `docs/design/` | Mode-agnostic |

The **architecture** (discovery, layering, lifecycle) is harness-general — `framework/`. The **dev-specific behaviors** (auto-creation, promotion, dev-sdlc skill bodies) are plugin-confined — `plugins/dev-sdlc/`. The auto-creation **config flag** is the carefully-partitioned exception: it's a harness-general primitive (workspace-config) gating a dev-specific mechanism, so the flag lives in `framework/` while the mechanism it gates lives in `plugins/dev-sdlc/`. Partition rule satisfied throughout.

The FIDRAFT 2026-05-04 persona-behavior bundle's original 6-candidate placement (all loam-skills) is reclassified per partition rule: 3 stay in loam-skills (translation, audit-block, owner-decision); 3 move to dev-sdlc (front-load-principle-walk, dispatch-brief-authoring, sealed-component-amendment-ship → `loam-amend-cycle`). FIDRAFT entry should be updated as a sub-action of v0.1.6.

---

## §11 — Composition with Lens 1–5

- **Lens 1.** Composes on Claude Code's native skill discovery throughout — no re-implementation of registration, invocation, or auto-load. Auto-creation uses native `Write` + live change detection. Subagent-fork composes with Eric-sequence v0.1.7 subagent personas.
- **Lens 2.** Primary-persona test passes: every dev-sdlc SKILL reduces translation burden ("ship V11.A" → invoke `loam-amend-cycle`). Harness test passes: every SKILL is persona-invokable; auto-creation extends toolkit; rubric maintains hygiene.
- **Lens 3.** Each SKILL is ODD-shaped: description = objective; tests = ACs; body = method (builder's call).
- **Lens 4.** F4 applied at Decision N (auto-creation MVP, medium confidence); Decision L (incremental rubric, medium confidence); v0.1.7 mechanism (high confidence, full scope).
- **Lens 5.** SKILL-authoring decomposes per §7 (each SKILL has tighter AC than parent); `max_planner_depth = 1`; SKILL authoring is Sonnet-default.

---

## §12 — Provenance trail

- **Luke directive (verbatim, 2026-05-04):** quoted in §1 of dispatch.
- **`docs/rebuild/VALUE_PROPOSITION.md:60,66`** — the two prime-objective tests; Lens 2 anchor.
- **`CLAUDE.md` (top-level)** — Lens 1–5 always-on.
- **`docs/rebuild/STATE.md`** — sealed-component history; v0.1.0 ship status.
- **`docs/rebuild/plans/v0-1-x-roadmap.md`** — current 5-release roadmap; v0.1.5 horizon.
- **`docs/rebuild/plans/value-prop-vs-actual-shape-audit-2026-05-04.md`** — persona-as-translator framing; coordination-token-spend tension.
- **`docs/rebuild/plans/eric-saas-app-use-case-version-sequence-2026-05-04.md`** — companion plan; reconciliation captured in §7.4 + Decision J.
- **`docs/rebuild/FUTURE_IDEAS_DRAFT.md`** — persona-behavior SKILL bundle (line 23), V11.C heavy entry (line 29), per-project PM (line 25), vertical-swarming, channel-violation-hook (line 125).
- **`plugins/loam-skills/`** — the 5 sealed packages (`f04e925`, amendment #124).
- **`plugins/dev-sdlc/skills/start-project.md`** — current dev-sdlc skill (1 file).
- **`plugins/dev-sdlc/dev-mode-manifest.yaml`** — partition primitive used to gate auto-creation.
- **`plugins/dev-sdlc/docs/cdcs/`** + **`plugins/dev-sdlc/docs/conventions/`** — source of dev-sdlc skill candidates §5.
- **`plugins/dev-sdlc/docs/conventions/fidraft-pattern.md`** — capture pattern referenced in `fidraft-capture` SKILL candidate.
- **Anthropic SKILL.md spec** (https://code.claude.com/docs/en/skills) — fetched 2026-05-04; frontmatter schema, discovery locations, live change detection, override semantics, namespace rules.
- **`docs/rebuild/plans/v0-1-3-skill-packages.md`** — the v0.1.3 SKILL bundle plan-doc; provides shape-precedent.
- **`workspace/.scratch/claude-output/v0-1-3-skill-packages-status-2026-05-04.md`** — status file with surfaces "dev-mode-manifest update for plugins/loam-skills" + "migration of flat-shape skills" + "live discovery smoke" — all referenced inline.

---

*End of layered-skill-story plan-doc. ~30–51 h AI-time across 6 versions, dev-only auto-creation gated on dev-mode partition + opt-in flag.*

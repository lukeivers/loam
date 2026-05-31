# everything-claude-code absorption master plan

**Status:** master plan-doc, plan-before-code, DRAFT — pending owner ratification per pattern. Authored 2026-05-24 by `loam-plan-author` subagent.
**Working directory:** `/Users/lukeivers/loam/` (canonical loam tree).
**Parent capture:** Telegram 12235 (research ask), 12240 (absorb-the-useful), 12242 (non-tech-user audience + drop AGENTS.md).
**Companion research (load-bearing):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/everything-claude-code-research-2026-05-24.md` (ECC + hackathon synthesis, 2026-05-24).
**Predecessor plan-doc shape exemplar:** `docs/plans/v0-1-9-master-plan.md` (three-cycle decomposition; AC family seeds; Eric-relevance audit).
**Quality bar:** decision-doc. Maintainer ratifies the per-pattern and architecture-level recommendations BEFORE any build dispatches. No code work in this plan.

---

## Principles applied this turn

- **CHANNEL** — reports inline to dispatcher; dispatcher surfaces to maintainer.
- **F2 RUTHLESS FEEDBACK** — every pattern carries a "non-tech-frame survives?" verdict; "obvious win" + "obvious-reject-even-in-dev" findings named.
- **ODD §2.5** — every plan-doc section maps to a named objective in §1; defensive sections cut.
- **PLAN-BEFORE-CODE** — load-bearing; no source touched.
- **AGENT-PROMPTS-SCOPE-ONLY** — per-work-item plan-docs (to be authored later, on owner ratification) carry method; this plan-doc names objectives + scope only.
- **OUTPUT-TO-DISK** — plan-doc to disk; inline report = path + executive summary + named-decisions-table + go-order.
- **CLAIM-OR-CITE** — every ECC claim cites file path or URL; every loam claim cites a `docs/` path; bib-class claims cite by author/title/venue.
- **PROMPT SCOPE ↔ CONFIDENCE (F4)** — §3 inventory rows tight (specific source + specific recommendation); §4 architecture decisions loose with options.
- **LOCKED-DESIGN-NOT-LICENSE** — applied to revisitable design (e.g., should loam adopt selective install?); NOT applied to cross-tool (maintainer ruled per TG 12242).
- **VERSION-NUMBERS-AT-RELEASE-TIME** — work-items use scope-descriptive slugs; no v0.X.Y pre-allocation.
- **SCOPE-DESCRIPTIVE AC IDs** — AC family seeds use scope abbreviations.
- **WD-IN-DISPATCHES** — confirmed canonical loam (`/Users/lukeivers/loam/`).
- **NO sub-agents.**

---

## §1 — Executive summary (read this first)

### TL;DR (5 bullets)

1. **The right framing is "absorb the harness craft, not the dev catalog."** ECC ships ~20 useful harness-level patterns (selective install, hook-based security, strategic-compact SKILL, instinct→skill graduation, marketplace, token defaults, README-as-decision-doc, etc.) and ~200 dev-domain skills (Django-TDD, SpringBoot-Security, Rust-Reviewer, etc.). The harness-level patterns survive the non-tech-user frame; the dev-domain catalog mostly belongs in the existing `plugins/dev-sdlc/` partition or doesn't survive at all.
2. **Biggest-leverage absorption: hook-based input-layer security guards** — secret-pattern detection (sk-/ghp_/AKIA), dangerous-flag blocking (--no-verify), config-file write-protection. Universal value (every loam workspace benefits regardless of user technicality); low cost (single PreToolUse hook bundle); composes with the existing loam hooks pattern; closes a real safety gap the primary persona currently has no structural defense against.
3. **Biggest-conflict absorption: continuous-learning-v2 (instinct→skill graduation tooling).** ECC's `/evolve` clusters 3+ instincts into reusable skills. Loam has the same concept informally (feedback memories graduate to SKILLs by hand). The conflict is with ODD: ECC's instinct system has no objective-binding gate — patterns get extracted whether or not they ladder up to a named objective. Adopting the tooling without the binding gate would create a parallel non-objective surface inside loam. Decision needed: build a binding gate at extraction time, OR keep manual graduation only.
4. **Decision points the maintainer must rule on (5):** D-SEC.HOOKS (security-hook bundle: core or dev-plugin or new plugin), D-INSTINCT.GRADUATION (build graduation tooling with objective-binding gate / manual only / defer), D-MARKETPLACE (adopt `.claude-plugin/marketplace.json` or keep PyPI-only path), D-INSTALL.SELECTIVE (component-level install selectivity or whole-plugin), D-TOKEN.ENFORCE (enforce token-optimization defaults in `~/.claude/settings.json` writer or document only).
5. **Recommended go-order:** Wave 1 (high-leverage low-cost universal): security hooks + strategic-compact as SKILL + token-defaults documenter. Wave 2 (architecture decisions, owner-gated): marketplace + selective install + instinct-graduation. Wave 3 (dev-plugin absorptions, conditional): TDD-guide / planner / build-resolver patterns folded into `dev-sdlc/`. Wave 4 (likely reject or defer): language-specific reviewer catalog, AgentShield-scope-loam-port, dashboard GUI.

### Named decisions with recommendations (maintainer-facing summary table)

| ID | Decision | Recommendation | Rationale (short) | Reversibility | Blast radius |
|---|---|---|---|---|---|
| **D-SEC.HOOKS** | Where do hook-based security guards live? Core loam (always-on) / `dev-sdlc/` plugin (dev-mode-only) / new `safety` plugin (opt-in). | **Core loam — always-on.** | Secret-leak / dangerous-flag blast radius is independent of workspace type; non-tech users benefit AS MUCH as devs (probably more — they don't recognise dangerous flags). | High (toggle-off via env var) | Low (hooks fail-open by default) |
| **D-INSTINCT.GRADUATION** | Build instinct→SKILL graduation tooling? With or without ODD objective-binding gate? | **Build it, WITH binding gate. Phase 1 = capture; Phase 2 = graduation with required objective-link.** | Manual graduation works for one-maintainer phase but won't scale; binding-gate prevents non-objective surface. Conflict with ODD is real and gate resolves it. | Medium (tool can be retired; captured instincts persist) | Medium (changes how feedback memories become SKILLs) |
| **D-MARKETPLACE** | Adopt `.claude-plugin/marketplace.json` for one-line plugin install? | **Yes — phase-in alongside current PyPI-eventual path.** | One-line `/plugin install loam@loam` is a translation-burden reducer (primary-persona test) and a harness toolkit addition (harness test). Doesn't conflict with the future PyPI shipping path; the two compose. | High (marketplace.json is metadata; remove anytime) | Low (additive surface) |
| **D-INSTALL.SELECTIVE** | Component-level selective install (à la ECC's install-plan.js + SQLite state)? | **Defer.** Adopt the manifest shape; defer SQLite state machinery. | Loam ships 18 components; selective install is real value AT SCALE but loam-at-current-size doesn't have the inventory-size pain ECC has. Premature to build the full SQLite state pipeline; manifest-shape adoption costs little and prepares for later. | Medium | Low |
| **D-TOKEN.ENFORCE** | Enforce token-optimization defaults (Sonnet default, MAX_THINKING=10000, auto-compact %, MCP cap) by writing to `~/.claude/settings.json`? Or document and let users set? | **Document + offer an opt-in writer SKILL.** Reject auto-write. | Loam shouldn't silently mutate `~/.claude/settings.json` on install — that's user-config territory; non-tech users would not understand the mutation. A SKILL the persona can invoke ("set my Claude to cost-optimised defaults?") satisfies the harness test without violating user-config-sovereignty. | High | Low (opt-in) |
| **D-COMPACT.SKILL** | Formalize strategic-compact as a loam SKILL (existing memory rule `feedback_compact_clear_decision_heuristic.md` graduates)? | **Yes — graduate.** | Already on the corpus path; the memory rule has been stable for weeks; SKILL surface makes it discoverable to derived workspaces (non-tech users get the discipline without reading the memory file). Direct application of `feedback_durable_capture_for_planned_work` graduation pattern. | High | Low |
| **D-AGENTSHIELD** | Port a version of AgentShield (102 static-analysis rules + adversarial scanner) into loam? | **Reject for core. Defer for dev-sdlc.** | AgentShield's value-axis is "scan code for vulnerabilities." Non-tech-user workspaces don't have code to scan; in dev-mode workspaces this overlaps with the existing PR-safety gate at `plugins/dev-sdlc/pr-safety/` (v0.1.9). Building it standalone is cost without unique value; folding patterns into pr-safety is a v0.2-class consideration, not v0.1. | Medium | Medium |
| **D-LANG-REVIEWERS** | Adopt ECC's 8 language-specific reviewer agents (TypeScript / Python / Go / Rust / Java / Kotlin / C++ / F#)? | **Reject as catalog. Adopt the PATTERN — language-specialised reviewer slot in `dev-sdlc/agents/`.** | The catalog itself is dev-workspace-only and 8-language enumeration is dispatch-time overhead (the catalog's value is real but ECC pays it on every session). Loam can carry a single `code-reviewer` agent + a per-language prompt-pack that the persona loads on demand. | High | Low |

---

## §2 — Plan objective + scope

### Objective

Produce a decision-doc the maintainer ratifies pattern-by-pattern. Output is a per-pattern absorption recommendation grounded in two filters:

1. **Mechanism-without-objectives analysis.** ECC has no ODD; by what mechanism does each pattern deliver value? Answer determines whether the pattern is portable into loam's ODD-discipline-bound architecture.
2. **Primary-persona-on-behalf-of-non-tech-user filter.** Does this pattern survive when the loam persona is operating on behalf of a non-tech user, in service of natural-language intent? (Per `docs/VALUE_PROPOSITION.md` + Lens 2 + TG 12242.)

### In-scope

- §3 pattern inventory with the two filters per row.
- §4 architecture-level decisions the maintainer rules on.
- §5 per-pattern absorption work-item sketches (objective + scope + AC ladder seed — NO method, NO build).
- §6 prioritization + sequencing (waves + critical path).
- §7 explicit out-of-scope with one-sentence rationales (including cross-tool / AGENTS.md per TG 12242).
- §8 open questions ranked by criticality (one-question-at-a-time discipline).

### Out-of-scope

- Any code or scaffold work — this plan does not author any.
- Pre-deciding the architectural decisions for the maintainer — surface as decisions with recommendations; maintainer rules.
- Cross-tool / `AGENTS.md` / multi-platform adapters — maintainer ruled out per TG 12242.
- Comparison-experiment authoring (loam-vs-ECC benchmark) — that is a separate dispatch per the research artifact §3.6 recommendation.
- Hackathon-emulation work — same.

---

## §3 — Pattern inventory

Every pattern row carries: ECC source, mechanism, **mechanism-without-objectives analysis**, **non-tech-user-frame verdict**, loam integration shape, lens-conflict check, priority, cost band, recommendation.

Cost bands: **sm** = single SKILL or hook (≤ 4 h AI-time per the duration rubric); **md** = plugin or new persona (4–18 h); **lg** = architectural change (18+ h or owner-level decision).

### §3.1 — Universal-value harness patterns (survive non-tech frame)

#### P1 — Strategic-compact as discoverable SKILL

| Field | Detail |
|---|---|
| **ECC source** | `skills/strategic-compact/` (`hooks/scripts/suggest-compact.js` companion) |
| **Mechanism** | A SKILL Claude can invoke that guides WHEN to /compact (logical breakpoint, milestone, research-complete) vs WHEN NOT (mid-task, dependency unresolved). Replaces blind auto-compact at 95%. |
| **Mechanism-without-objectives analysis** | Pure harness discipline — has nothing to do with ODD. Value comes from "right context preserved at right moment," which is true regardless of whether the work is objective-bound. |
| **Non-tech-user-frame verdict** | **YES — universal.** Non-tech users have NO mental model of context windows; they need the persona to make the compaction call for them. A SKILL the persona consults is exactly the translation surface VALUE_PROPOSITION names. |
| **Loam integration shape** | New SKILL `loam-skills/skills/strategic-compact/SKILL.md`. Graduate the content from `feedback_compact_clear_decision_heuristic.md` (memory) → SKILL (auto-discoverable). |
| **Lens conflict** | None. Composes with L1 (uses Claude /compact primitive), L2 (reduces translation burden), L4 (loose-when-mid-task / tight-at-breakpoint maps directly to confidence). |
| **Priority** | **HIGH-leverage / HIGH-confidence.** |
| **Cost band** | **sm.** |
| **Recommendation** | **ABSORB — Wave 1.** D-COMPACT.SKILL approves; see §4. |

#### P2 — Hook-based input-layer security guards

| Field | Detail |
|---|---|
| **ECC source** | `hooks/hooks.json` + `hooks/scripts/` — secret-pattern detection (14 patterns per ECC README; e.g., `sk-`, `ghp_`, `AKIA`), `--no-verify` git flag blocker, config-file (`.eslintrc`, `biome.json`) write-protection, pre-commit quality check. AgentShield's smaller cousin lives here. |
| **Mechanism** | PreToolUse hooks intercept Bash + Edit + Write tool calls. Pattern-match the proposed command/content; exit 2 to block + emit structured diagnostic. Independent of ODD; pure structural defense. |
| **Mechanism-without-objectives analysis** | Blast-radius reduction — the value is the BLOCK, not any objective the agent was pursuing. Mechanism survives in any methodology because it predates methodology (it operates at the tool boundary). |
| **Non-tech-user-frame verdict** | **YES — universal, possibly MORE valuable for non-tech users.** A non-tech user can't recognise `--no-verify` as dangerous; a non-tech user can't recognise `sk-...` as a secret leak in a paste they're about to commit. The hook IS the safety the primary persona structurally provides. |
| **Loam integration shape** | New hook bundle at `framework/safety-layer/hooks/` (composes with existing `safety-layer` component). Three hooks minimum: secret-detector, dangerous-flag blocker, config-write-protector. Installed as part of the always-on hook layer. |
| **Lens conflict** | None. Composes with L1 (Claude PreToolUse primitive), L2 (translation burden absorbed by structural defense), L7 (RF — hook surfaces the blocked attempt with named evidence). |
| **Priority** | **HIGH-leverage / HIGH-confidence.** |
| **Cost band** | **sm-md.** Three hooks + tests + diagnostic shape; ECC's pattern set is mostly portable. |
| **Recommendation** | **ABSORB — Wave 1.** D-SEC.HOOKS approves core placement; see §4. |

#### P3 — Token-optimization defaults (as documented preset + opt-in writer)

| Field | Detail |
|---|---|
| **ECC source** | ECC README "Token Optimization & Cost Management" section: Sonnet default, `MAX_THINKING_TOKENS=10000`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`, <10 active MCP servers, <80 active tools, `/cost` / `/clear` / `/compact` awareness. |
| **Mechanism** | Settings + discipline. The savings (60% cost via Sonnet default, 70% via thinking cap, etc.) are real. ECC sets these via `~/.claude/settings.json` + documentation. |
| **Mechanism-without-objectives analysis** | Independent of methodology — token economics apply to every Claude session. The "default Sonnet" and "cap thinking" knobs reduce cost without changing what gets done. |
| **Non-tech-user-frame verdict** | **YES — universal, with a caveat.** Non-tech users SHOULDN'T have to know what `MAX_THINKING_TOKENS` is. The defaults must be applied FOR them — but not silently mutating `~/.claude/settings.json` on install (that's user-config sovereignty territory). A persona-invoked SKILL ("set my Claude to cost-optimised defaults? — yes/no") satisfies both constraints. |
| **Loam integration shape** | (a) Document the recommended settings in `docs/getting-started.md` (small section); (b) author SKILL `loam-skills/skills/cost-optimised-defaults/SKILL.md` — the persona offers to write the settings on user approval. (c) Loam's own dispatch briefs already prefer Sonnet (per CLAUDE.md) — no change there. |
| **Lens conflict** | Mild L2 tension if auto-applied (mutating ~/.claude/settings.json without user awareness is translation-burden-on-the-user-after-the-fact, when they discover their Claude behaviour changed). Resolved by opt-in shape. |
| **Priority** | **MEDIUM-leverage / HIGH-confidence.** |
| **Cost band** | **sm.** |
| **Recommendation** | **ABSORB — Wave 1, opt-in shape only.** D-TOKEN.ENFORCE rules opt-in not auto-mutate; see §4. |

#### P4 — README-as-decision-doc framing

| Field | Detail |
|---|---|
| **ECC source** | ECC README — leads with philosophy ("harness-native operator system"), then statistics, then architecture, then per-subsystem philosophy. Reads like a manifesto, not a manual. |
| **Mechanism** | Audience-routing. A decision-doc README sorts the reader on first read: "is this for me? what does it do? what's the philosophy?" before "how do I install it." Reduces "install + don't understand" failure mode. |
| **Mechanism-without-objectives analysis** | Pure documentation craft. Methodology-independent. The mechanism is reader sorting; it works whether the underlying system is ODD-bound or not. |
| **Non-tech-user-frame verdict** | **YES — strongly.** Non-tech users especially benefit from "is this for me?" routing; they're more likely to bounce on a manual-shaped README. |
| **Loam integration shape** | Restructure `README.md` to lead with positioning (Why → What → For whom → How). Loam's current README is mostly this shape already (`## Why` is line 19); minor revision: hoist the positioning summary higher; add a "is this for you?" subsection. |
| **Lens conflict** | None. Composes with L2 (translation-burden reduced at first-touch). |
| **Priority** | **MEDIUM-leverage / HIGH-confidence.** Quick win. |
| **Cost band** | **sm.** |
| **Recommendation** | **ABSORB — Wave 1.** Low-risk doc work. |
| **Build status (Wave 1 first build)** | **SEALED LOCAL 2026-05-24.** Plan-doc: `docs/plans/sealed/readme-restructure-decision-doc-positioning.md`. Source-edit batch `cf5b0c1`; seal `a39d5ce`; §14 backfill `ea86916`; STATE.md backfill `9146ea4`. All 4 named decisions (D-README.LEAD/.AUDIENCE-SEGMENTS/.SECTION-ORDER/.LENGTH-DELTA) ratified per Telegrams 12310+12311. README at 194 lines (exactly at D-README.LENGTH-DELTA hard ceiling). AC.README.{1,2} structural tests 5/5 GREEN; AC.README.3 outcome-altitude smoke 4/4 OPERATIONALLY MET (test wrapper synonym list over-narrow for `claude -p` phrasing variance — 1/4 wrapper PASS; corrective cycle recommended per D-build.README.2). LOCAL SEAL ONLY — not pushed, not published. |

#### P5 — Observer-loop prevention (5-layer guard against agent self-delegation)

| Field | Detail |
|---|---|
| **ECC source** | ECC README v1.8.0 release notes — "5-layer guard preventing infinite agent self-delegation"; companion to `/harness-audit`. |
| **Mechanism** | Re-entrancy guard in orchestration: detect when an agent is about to delegate to itself (or to a parent chain) and halt. Prevents runaway cost from accidental loops. |
| **Mechanism-without-objectives analysis** | Pure structural-safety. Independent of methodology — the failure mode (agent delegates to itself, burns tokens until limit) is methodology-agnostic. |
| **Non-tech-user-frame verdict** | **YES — universal.** Non-tech users have no mechanism to detect runaway cost mid-loop; the structural guard absorbs the risk. |
| **Loam integration shape** | Extends `framework/cost-governance/` — already has token/time/money ceilings + drift detection per loam README §80. Add a "re-entrancy guard" companion that detects subagent-spawn-chains that re-enter the same persona. |
| **Lens conflict** | None. Composes with L1 (Claude subagent primitive), existing safety-layer. |
| **Priority** | **MEDIUM-leverage / MEDIUM-confidence.** (Confidence not high because loam's current swarming pattern uses `max_planner_depth=1` default per Lens 5 — the loop risk is structurally bounded already.) |
| **Cost band** | **sm.** |
| **Recommendation** | **ABSORB — Wave 2.** Less urgent than P1-P4 because loam's `max_planner_depth=1` default already bounds the risk; the guard is belt-and-suspenders. |

#### P6 — Two-tier agent permission model (orchestrator vs specialist)

| Field | Detail |
|---|---|
| **ECC source** | ECC AGENTS.md (verified per WebFetch 2026-05-24): orchestrators (Planner, Architect, Security-Reviewer) have broad tool access; specialists (language-specific reviewers) have tool subsets relevant to their role. |
| **Mechanism** | Declared in agent frontmatter — `tools:` field constrains what an agent can invoke. Limits blast radius per agent class. |
| **Mechanism-without-objectives analysis** | Methodology-independent. The mechanism (tool-allowlist per agent) is a Claude Code primitive (per L1); ECC just uses it consistently. |
| **Non-tech-user-frame verdict** | **YES — universal, but indirect.** Non-tech users don't pick agents; the primary persona does. But the persona benefits from sharper tool-allowlists when dispatching (the reviewer agent doesn't need Bash; the researcher doesn't need Write). |
| **Loam integration shape** | LOAM ALREADY HAS THIS. `/Users/lukeivers/loam/.claude/agents/loam-*.md` — researcher = read-only, builder = full, reviewer = read-only, etc. (Verified via `ls` 2026-05-24.) This row is a confirmation that loam's existing pattern is the right shape; no absorption needed. |
| **Lens conflict** | None. |
| **Priority** | N/A (already present). |
| **Cost band** | N/A. |
| **Recommendation** | **CONFIRM — no new work.** Note in §10 that loam's persona-as-bounded-agent pattern matches ECC's two-tier model; this is independent convergent design, not a gap. |

### §3.2 — Architectural-decision patterns (require ratification)

#### P7 — Plugin marketplace via `.claude-plugin/marketplace.json`

| Field | Detail |
|---|---|
| **ECC source** | `marketplace.json` at repo root + `.claude-plugin/plugin.json`. Enables one-line install: `/plugin marketplace add https://github.com/affaan-m/ECC` then `/plugin install ecc@ecc`. |
| **Mechanism** | Claude Code's native plugin marketplace primitive (per L1). ECC self-hosts a marketplace from its own GitHub repo; users install via Claude Code's `/plugin` command. |
| **Mechanism-without-objectives analysis** | Pure distribution. The pattern is "publish in a Claude-native format so user runs one command not seven." |
| **Non-tech-user-frame verdict** | **YES — strongly.** Loam's current install is a 4-step shell sequence (clone, venv, pip install, loam init); the README at line 67–78 acknowledges "two copies on disk" pain. A non-tech user is significantly more likely to install via `/plugin install loam@loam` than via four shell commands. |
| **Loam integration shape** | Author `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` for loam. Phase-in alongside the existing source-install path (per README line 76: "A future minor will ship the CLI from PyPI directly"). Marketplace install can ship BEFORE PyPI; not in conflict. |
| **Lens conflict** | None. Composes with L1 (Claude marketplace primitive), L2 (translation-burden absorbed by one-line install). |
| **Priority** | **HIGH-leverage / MEDIUM-confidence.** Need to verify Claude Code's marketplace primitive composes with loam's two-tree shape (clone-tree + workspace-tree). |
| **Cost band** | **md.** Requires research into the marketplace.json shape, plugin metadata, and whether loam's `loam init` workspace-bootstrap composes with `/plugin install` flow. |
| **Recommendation** | **ABSORB — Wave 2 (architecture decision).** D-MARKETPLACE; see §4. |

#### P8 — Selective install via manifest-driven pipeline + SQLite state

| Field | Detail |
|---|---|
| **ECC source** | `install-plan.js` + `install-apply.js` + state-store (SQLite). Manifest-driven; profile-based (`minimal | core | full`); per-component selectivity (`--without`, `--modules`); state tracking prevents duplicate install. |
| **Mechanism** | Two-phase install: PLAN (read manifest, compute install graph, present user with diff) → APPLY (execute, record state). State store enables idempotent updates and per-component uninstall. |
| **Mechanism-without-objectives analysis** | Pure installer craft. The value is "users install what they need, not 232 skills they don't"; that value scales with catalog size. |
| **Non-tech-user-frame verdict** | **CONDITIONAL.** For loam (18 components), the per-component selectivity offers little to non-tech users (who don't choose components). The MANIFEST SHAPE benefits everyone (idempotent installs, structured updates); the SQLite state-store layer is overkill at loam's current inventory size. |
| **Loam integration shape** | Phase 1: adopt the manifest-shape (a single manifest.yaml describing component graph) + idempotent install — already partially present at `install-from-source.txt`. Phase 2: SQLite state store deferred until loam's component count makes it worth the complexity. |
| **Lens conflict** | None for the manifest-shape phase. The state-store phase is a complexity-not-now decision (asymmetric problem solving per `feedback_asymmetric_problem_solving`: leverage at current scale doesn't justify build cost). |
| **Priority** | **MEDIUM-leverage / MEDIUM-confidence.** |
| **Cost band** | **md** (manifest-shape phase) / **lg** (full state-store phase, deferred). |
| **Recommendation** | **ABSORB Phase 1 — Wave 2. DEFER Phase 2.** D-INSTALL.SELECTIVE; see §4. |

#### P9 — Continuous-learning v2 / instinct → skill graduation

| Field | Detail |
|---|---|
| **ECC source** | `skills/continuous-learning-v2/` + `/instinct-status` / `/instinct-import` / `/instinct-export` / `/evolve` / `/promote` / `/prune` commands. Patterns get extracted at SessionEnd; tagged with confidence (0.3–0.9); aggregated when 3+ related instincts exist; user runs `/evolve` to cluster them into a reusable SKILL. |
| **Mechanism** | Captured patterns → graduate to durable SKILLs. Replaces "the user remembers the pattern" with "the system captures + suggests graduation." |
| **Mechanism-without-objectives analysis** | **LOAD-BEARING CONFLICT.** ECC's instinct system has no objective-binding gate — patterns get extracted whether or not they ladder up to a named objective. This conflicts with ODD §2.5 (no non-objective surface). Adopting the tooling without a binding gate would create a non-objective surface inside loam. |
| **Non-tech-user-frame verdict** | **YES universally — IF the binding gate is built.** Non-tech users benefit MORE from auto-captured patterns because they don't author memory rules manually. Without the gate, non-tech-user workspaces would accumulate non-objective skills the persona doesn't know how to use. |
| **Loam integration shape** | Build a graduation tool that REQUIRES every candidate SKILL to bind to a named loam objective (per `docs/spec/`) OR carry an explicit "no objective; expressed as discipline" tag. Composes with the existing memory→SKILL graduation pattern (per `feedback_durable_capture_for_planned_work` + the recent SKILL-promotion-review SKILL at `.claude/skills/skill-promotion-review/`). |
| **Lens conflict** | L3 ODD (resolved by binding gate); L2 (binding gate ALSO reduces non-tech-user translation burden — every SKILL the persona invokes has a known purpose). |
| **Priority** | **HIGH-leverage (long-term) / MEDIUM-confidence (depends on binding-gate design).** |
| **Cost band** | **md-lg.** Capture surface (small) + graduation tool (medium) + binding-gate (medium-large, requires objective-spec read). |
| **Recommendation** | **ABSORB Phase 1 (capture only) — Wave 2. ABSORB Phase 2 (graduation with binding gate) — Wave 3.** D-INSTINCT.GRADUATION; see §4. |

### §3.3 — Dev-velocity patterns (survive non-tech frame ONLY in dev workspace; absorb into `dev-sdlc/`)

#### P10 — TDD-guide SKILL / agent

| Field | Detail |
|---|---|
| **ECC source** | `skills/tdd-workflow/` (Red-Green-Improve) + `agents/tdd-guide` (per AGENTS.md). |
| **Mechanism** | A SKILL the persona invokes when the task is code-shaped: enforces test-first ordering, helps the user (or the builder agent) author failing tests before implementation. |
| **Mechanism-without-objectives analysis** | Methodology-bound but compatible with ODD: TDD is methodology AT THE BUILDER tier; ODD is methodology AT THE OBJECTIVE tier. They compose — ODD names the AC, TDD writes the failing test that pins the AC, then implementation. Loam's existing `tdd_guard.py` hook (`plugins/dev-sdlc/hooks/tdd_guard.py`) is the structural enforcement of this; the SKILL would be the methodology layer. |
| **Non-tech-user-frame verdict** | **YES IN DEV WORKSPACE ONLY.** Non-tech users not writing code don't need a TDD SKILL. In a dev workspace (where the persona is operating on behalf of a user who is shipping code), TDD discipline is one of the highest-leverage absorptions. |
| **Loam integration shape** | Author SKILL `plugins/dev-sdlc/skills/tdd-workflow/SKILL.md`. Composes with existing `tdd_guard.py` hook. Adopts ECC's Red-Green-Improve loop content. |
| **Lens conflict** | None within dev-workspace partition. Per `feedback_odd_cdc_scope.md`, dev-CDCs scope to dev work only; this absorption respects that. |
| **Priority** | **HIGH-leverage in dev workspace / HIGH-confidence.** |
| **Cost band** | **sm.** |
| **Recommendation** | **ABSORB — Wave 3 (into dev-sdlc plugin).** |

#### P11 — Planner / Architect orchestrator agents

| Field | Detail |
|---|---|
| **ECC source** | `agents/planner.md` + `agents/architect.md`. Planner does phased feature implementation planning; Architect does system-design decisions. |
| **Mechanism** | Specialised agents that the user (in ECC's frame) invokes when planning/design is needed. In loam, planning is `loam-plan-author` (already present at `plugins/dev-sdlc/agents/loam-plan-author.md`). |
| **Mechanism-without-objectives analysis** | ECC's Planner outputs a phased plan with no ODD shape; loam's plan-author outputs an ODD-bound plan-doc. Methodologically different. |
| **Non-tech-user-frame verdict** | **CONFIRMED — loam already has this.** Verified: `plugins/dev-sdlc/agents/loam-plan-author.md` is the loam equivalent. No absorption needed; possibly worth a cross-check to see if any ECC Planner patterns are absent from `loam-plan-author`. |
| **Loam integration shape** | No new agent. Possibly a one-time review of `plugins/dev-sdlc/agents/loam-plan-author.md` against ECC's `agents/planner.md` to surface gaps (separate small dispatch). |
| **Lens conflict** | None. |
| **Priority** | LOW (mostly confirmation). |
| **Cost band** | **sm** if cross-check dispatched; **0** otherwise. |
| **Recommendation** | **CONFIRM — no new work. Optional small cross-check dispatch in Wave 3.** |

#### P12 — Code-reviewer + Security-reviewer agents (generic, not language-specific)

| Field | Detail |
|---|---|
| **ECC source** | `agents/code-reviewer.md` + `agents/security-reviewer.md`. Standalone review agents the user invokes after code changes. |
| **Mechanism** | Dedicated agent class; bounded tool access (read-only); produces structured review output. |
| **Mechanism-without-objectives analysis** | Methodology-independent in shape; ODD-compatible in content (a review can check "does this satisfy the AC?" rather than "does this look right?"). |
| **Non-tech-user-frame verdict** | **YES IN DEV WORKSPACE ONLY.** Same reasoning as P10. |
| **Loam integration shape** | LOAM ALREADY HAS: `plugins/dev-sdlc/agents/loam-reviewer.md`. Verified via `ls`. Check whether ECC's code-reviewer.md content adds anything loam-reviewer.md lacks (review-checklist depth, security-axis explicit). Possible small content absorption. |
| **Lens conflict** | None. |
| **Priority** | LOW. |
| **Cost band** | **sm** (review-content absorption if any gap surfaces). |
| **Recommendation** | **CONFIRM — no new agent. Optional content absorption in Wave 3.** |

#### P13 — Build-error-resolver agent + language-specific build-resolvers

| Field | Detail |
|---|---|
| **ECC source** | `agents/build-error-resolver.md` + `agents/go-build-resolver`, `java-build-resolver`, `kotlin-build-resolver`, `c++-build-resolver`, `rust-build-resolver`, `pytorch-build-resolver` (6 specialised). |
| **Mechanism** | When CI / build fails, agent investigates the failure log, identifies root cause, proposes fix. |
| **Mechanism-without-objectives analysis** | Methodology-independent; loop is "read error → hypothesise → patch → verify." |
| **Non-tech-user-frame verdict** | **YES IN DEV WORKSPACE.** No useful in writer/research workspaces. |
| **Loam integration shape** | Generic build-error-resolver as `plugins/dev-sdlc/agents/loam-build-resolver.md`. REJECT the 6 language-specific variants as catalog (per D-LANG-REVIEWERS reasoning). Loam's generic agent + per-language prompt-pack loaded on demand satisfies the value without catalog overhead. |
| **Lens conflict** | None. |
| **Priority** | **MEDIUM-leverage in dev workspace.** |
| **Cost band** | **sm-md** (generic agent + light prompt-packs). |
| **Recommendation** | **ABSORB GENERIC — Wave 3. REJECT language-specific catalog.** |

#### P14 — Refactor-cleaner + Doc-updater + Docs-lookup agents

| Field | Detail |
|---|---|
| **ECC source** | `agents/refactor-cleaner.md` (dead code removal), `agents/doc-updater.md` (doc sync), `agents/docs-lookup.md` (real-time API docs retrieval). |
| **Mechanism** | Single-purpose specialists. |
| **Mechanism-without-objectives analysis** | Each is methodology-independent. Refactor-cleaner could violate ODD §2.5 ("touched code outside named AC") unless scoped to closing-named-AC-debt. |
| **Non-tech-user-frame verdict** | **CONDITIONAL.** Refactor-cleaner = dev-only; doc-updater = dev-only-ish; docs-lookup = potentially universal (any persona looking up framework docs benefits). |
| **Loam integration shape** | `docs-lookup` could be a SKILL not an agent; refactor-cleaner deferred (ODD conflict needs design); doc-updater deferred (overlaps with loam's `documenter` persona at `plugins/dev-sdlc/agents/loam-documenter.md`). |
| **Lens conflict** | Refactor-cleaner — L3 ODD §2.5 (unless ACs-debt-scoped). |
| **Priority** | LOW. |
| **Cost band** | **sm** each. |
| **Recommendation** | **DEFER all three to Wave 3 or later. Re-evaluate after Wave 1/2 absorptions ship.** |

### §3.4 — Patterns that conditionally survive (analyze case-by-case)

#### P15 — Harness-optimizer agent (auto-tunes the harness itself)

| Field | Detail |
|---|---|
| **ECC source** | `agents/harness-optimizer.md`. Per ECC README: "Harness configuration tuning and reliability." |
| **Mechanism** | Meta-agent that profiles the harness, surfaces issues, proposes tuning. |
| **Mechanism-without-objectives analysis** | The pattern is "the harness optimises itself"; in loam this overlaps with self-upgrade-bb (the existing self-upgrade workflow at `docs/plans/sealed/self-upgrade-*`). |
| **Non-tech-user-frame verdict** | **YES — universal.** A non-tech user benefits from a persona that proactively flags "your loam workspace has 3 stale memory rules; want me to retire them?" — that's persona-as-translation-layer at its purest. |
| **Loam integration shape** | A new SKILL `loam-skills/skills/harness-health-audit/` that the persona invokes on cadence (composable with `/loop` or scheduled). Composes with the existing self-upgrade pattern. |
| **Lens conflict** | Mild L4 (scope-confidence — "what counts as a harness issue?" is loose; the SKILL must enumerate criteria before action). |
| **Priority** | **MEDIUM-leverage / MEDIUM-confidence.** |
| **Cost band** | **md.** |
| **Recommendation** | **DEFER to Wave 3.** Useful but not urgent; ECC pattern is informative more than prescriptive (their actual implementation is closed-pro-tier per README). |

#### P16 — Loop-operator agent (autonomous loop execution + checkpointing)

| Field | Detail |
|---|---|
| **ECC source** | `agents/loop-operator.md`. Per ECC README: "Autonomous loop execution and checkpointing." |
| **Mechanism** | Agent that runs a defined loop (sequential pipeline, PR loop, DAG) with checkpoints. |
| **Mechanism-without-objectives analysis** | Methodology-independent; loop shape is a structural primitive. Loam's `/loop` and `/goal` commands cover this (SKILLs at `loam-skills/skills/loop-command/` and `/goal-command/`). |
| **Non-tech-user-frame verdict** | LOAM ALREADY HAS — confirmation, not absorption. |
| **Loam integration shape** | No new agent. Possible content-cross-check on what ECC's loop-operator does that loam's `/loop` doesn't (e.g., checkpointing format). |
| **Priority** | LOW. |
| **Cost band** | **0–sm.** |
| **Recommendation** | **CONFIRM — no new work; optional cross-check.** |

#### P17 — MCP server configurations bundle

| Field | Detail |
|---|---|
| **ECC source** | `mcp-configs/mcp-servers.json` — 9+ bundled MCP server definitions (GitHub, Supabase, Vercel, Railway, Context7, Exa, Playwright, Sequential Thinking, Memory). |
| **Mechanism** | Pre-canned MCP configs the user enables via `/mcp`. |
| **Mechanism-without-objectives analysis** | Pure capability-expansion. Each MCP added to a workspace gives the persona a new tool to invoke. |
| **Non-tech-user-frame verdict** | **CONDITIONAL.** Each MCP is useful only if the user's workflow needs it (GitHub MCP useless to a writer; Memory MCP universal). The pattern of bundling configs IS useful (lowers the install bar); the specific bundle isn't loam's call to make — depends on workspace. |
| **Loam integration shape** | LOAM ALREADY HAS the per-workspace `.mcp.json` mechanism. A SKILL that catalogues common MCPs with one-line enable ("loam, set up the GitHub MCP for this workspace") is the loam-shaped version. |
| **Lens conflict** | Mild — ECC's "keep under 10 active MCPs" warning is real; loam needs the same discipline. |
| **Priority** | **LOW-MEDIUM.** |
| **Cost band** | **sm.** |
| **Recommendation** | **DEFER.** Author a SKILL when there's user demand; not urgent. |

#### P18 — Iterative-retrieval / search-first / verification-loop SKILLs

| Field | Detail |
|---|---|
| **ECC source** | `skills/iterative-retrieval/`, `skills/search-first/`, `skills/verification-loop/`, `skills/eval-harness/`. |
| **Mechanism** | Each codifies a discipline: progressive context refinement; search-before-coding; continuous build/test/lint/typecheck/security; checkpoint-vs-continuous evaluation. |
| **Mechanism-without-objectives analysis** | Methodology-near; each codifies a discipline loam already practices (research-first-dispatch, scope-only-dispatch, halt-and-surface). The mechanism is "make the discipline auto-discoverable as a SKILL." |
| **Non-tech-user-frame verdict** | **PARTIAL.** Search-first / iterative-retrieval / verification-loop survive (persona uses them on user's behalf); eval-harness is dev-only. |
| **Loam integration shape** | Author `loam-skills/skills/search-first/`, `loam-skills/skills/iterative-retrieval/` graduated from existing dispatch discipline. `verification-loop` lives in `dev-sdlc/` (already present-ish via `audit-finding-triage` + smoke-test-discipline). |
| **Lens conflict** | None — direct alignment with loam discipline. |
| **Priority** | **MEDIUM-leverage / HIGH-confidence.** |
| **Cost band** | **sm** each. |
| **Recommendation** | **ABSORB SELECTIVELY — Wave 2.** Two SKILLs in core (search-first, iterative-retrieval); eval-harness deferred to dev-sdlc revisit. |

#### P19 — Cost-aware-LLM-pipeline + regex-vs-LLM-structured-text SKILLs

| Field | Detail |
|---|---|
| **ECC source** | `skills/cost-aware-llm-pipeline/`, `skills/regex-vs-llm-structured-text/`. |
| **Mechanism** | Decision-framework SKILLs the persona invokes when designing LLM pipelines / parsing structured text. Same kind of discipline as loam's existing `tool-selection-rubric`. |
| **Mechanism-without-objectives analysis** | Pure decision-aid; methodology-independent. |
| **Non-tech-user-frame verdict** | **YES — universal but indirect.** Persona uses them; user doesn't see them; user benefits from cheaper/correcter executions. |
| **Loam integration shape** | Graduate concepts into existing loam SKILLs (`tool-selection-rubric` already exists at `loam-skills/skills/`; could be extended with the regex-vs-LLM decision flow). |
| **Lens conflict** | None. |
| **Priority** | LOW-MEDIUM. |
| **Cost band** | **sm.** |
| **Recommendation** | **DEFER to Wave 3 / SKILL-extension pass.** |

### §3.5 — Patterns to reject or defer indefinitely

#### P20 — Language-specific reviewer catalog (8 reviewer agents)

| Field | Detail |
|---|---|
| **ECC source** | `agents/typescript-reviewer.md`, `python-reviewer.md`, `go-reviewer.md`, `rust-reviewer.md`, `java-reviewer.md`, `kotlin-reviewer.md`, `c++-reviewer.md`, `f#-reviewer.md`. |
| **Recommendation** | **REJECT AS CATALOG. Pattern = single generic reviewer + on-demand language prompt-pack.** Per D-LANG-REVIEWERS. ECC's 8-agent catalog is dispatch-time overhead loam doesn't need. |

#### P21 — AgentShield (1,282 tests + 102 static-analysis rules + adversarial scanner)

| Field | Detail |
|---|---|
| **ECC source** | Separate npm package `ecc-agentshield`; integration via `/security-scan` skill; supports `--opus` spawning three Opus 4.6 adversarial agents. |
| **Recommendation** | **REJECT FOR LOAM CORE. DEFER FOR DEV-SDLC.** Per D-AGENTSHIELD. AgentShield's value-axis is "scan code for vulnerabilities"; non-tech-user workspaces have no code to scan; in dev workspaces it overlaps with loam's existing PR-safety gate at `plugins/dev-sdlc/pr-safety/` (v0.1.9 contract-enforcement). Folding select static-analysis patterns into pr-safety is a v0.2-class consideration; building a standalone scanner is cost without unique value. |

#### P22 — Tkinter dashboard GUI (ecc_dashboard.py)

| Field | Detail |
|---|---|
| **ECC source** | `ecc_dashboard.py`. Per ECC README: "Convenience feature for discovery." |
| **Recommendation** | **REJECT.** Loam is Claude-Code-attached; the persona IS the dashboard. A Tkinter GUI cuts AGAINST L1 (Claude-leverage-first) and L2 (translation-burden — adds a separate UI for the user to learn). |

#### P23 — Cross-tool support (.cursor/, .codex/, .opencode/, .github/, .zed/) + AGENTS.md

| Field | Detail |
|---|---|
| **ECC source** | `AGENTS.md` at root; tool-specific dirs. |
| **Recommendation** | **REJECT.** Per maintainer ruling TG 12242 ("As to agents.md, I'm not asking you to adopt his entire approach...if something isn't useful for us, then don't take it") and per L1 (loam is Claude-only by lens). Closed for further discussion. |

#### P24 — ECC operator agents (brand-voice / billing-ops / google-workspace-ops / etc., 8 from v2.0.0-rc.1)

| Field | Detail |
|---|---|
| **ECC source** | v2.0.0-rc.1 operator suite. |
| **Recommendation** | **REJECT WHOLESALE; absorb the PATTERN.** The pattern (domain-specialised operator personas the primary persona dispatches) is useful and aligns with loam's persona architecture. The specific suite is ECC's roadmap, not loam's; loam's domain-personas should emerge from user demand, not ECC catalog adoption. |

#### P25 — ECC 2.0 alpha Rust control-plane

| Field | Detail |
|---|---|
| **ECC source** | `ecc2/` directory; Rust control plane prototype. |
| **Recommendation** | **REJECT.** Cuts against L1 (loam is Python + Claude-attached); cuts against the "Claude is the runtime" framing. Not applicable. |

---

### §3.6 — Inventory summary

25 patterns inventoried. Distribution:

- **Absorb — Wave 1 (universal, low-cost, high-leverage):** P1 (strategic-compact SKILL), P2 (security hooks), P3 (token defaults opt-in), P4 (README restructure). 4 items.
- **Absorb — Wave 2 (architecture decisions or medium cost):** P5 (observer-loop guard), P7 (marketplace), P8 Phase 1 (manifest-shape selective install), P9 Phase 1 (instinct capture), P18 (search-first + iterative-retrieval SKILLs). 5 items.
- **Absorb — Wave 3 (dev-plugin or post-Wave-2 reassessment):** P10 (TDD SKILL into dev-sdlc), P9 Phase 2 (instinct graduation with binding gate), P13 (generic build-resolver), P15 (harness-optimizer SKILL). 4 items.
- **Confirm (loam already has):** P6 (two-tier agent permissions), P11 (planner/architect), P12 (code-reviewer), P16 (loop-operator). 4 items.
- **Defer (re-evaluate after Wave 1/2):** P14 (refactor-cleaner / doc-updater / docs-lookup), P17 (MCP bundle), P19 (cost-aware-LLM-pipeline). 3 items.
- **Reject:** P20 (lang-reviewer catalog), P21 (AgentShield port), P22 (Tkinter GUI), P23 (cross-tool + AGENTS.md), P24 (ECC operator suite), P25 (Rust control-plane). 6 items.

---

## §4 — Architecture-level decisions (maintainer rules)

Each decision: alternatives + recommendation + rationale + downstream consequences + non-tech-user-usefulness audit + reversibility.

### D-SEC.HOOKS — Where do hook-based security guards live?

**Alternatives:**
- (a) **Core loam, always-on** — hooks installed in every workspace via `framework/safety-layer/hooks/`.
- (b) **`dev-sdlc/` plugin, dev-mode-only** — secrets / dangerous flags / config-write protection only fire when dev-mode is loaded.
- (c) **New opt-in `safety` plugin** — user explicitly installs.

**Recommendation:** (a) Core loam, always-on.

**Rationale:** The failure mode (secret leak / `--no-verify` accident / `.eslintrc` clobber) is independent of workspace type. A writer-workspace user pasting an API key into a message they're committing to a side repo benefits equally from the secret-detection hook. The non-tech-user frame strengthens this — non-tech users are LESS likely to recognise the dangerous patterns themselves, so they need MORE structural defense, not less. Per L2 (harness test): hooks add to the persona's toolkit (the persona can refer to "the safety-layer blocked that" instead of trying to detect it itself).

**Downstream consequences:** `framework/safety-layer/` gets a new `hooks/` subdirectory; existing safety-layer's refusal-chain composes with the PreToolUse hook layer (hooks fire first; refusal-chain handles what hooks let through). Bootstrap installer must wire the hooks at first run.

**Non-tech-user-usefulness:** HIGH — see rationale.

**Reversibility:** High. Toggle off via `LOAM_SAFETY_HOOKS=off` env var; each hook can be individually disabled. Per `feedback_locked_design_not_license`, the choice is revisitable if hooks turn out noisy.

**Blast radius:** Low. Hooks fail-open by default (any exception in hook → allow the operation, log the failure). Real security is structural-defense-in-depth; loam's hooks are belt to suspenders the user already has in place.

---

### D-INSTINCT.GRADUATION — Build instinct → SKILL graduation tooling? With or without ODD binding gate?

**Alternatives:**
- (a) **Build capture + graduation tooling, WITH ODD objective-binding gate.** Two phases: Phase 1 captures patterns at SessionEnd; Phase 2 surfaces graduation candidates that must bind to a named loam objective (or carry an explicit "no objective" tag) before becoming a SKILL.
- (b) **Manual graduation only** (status quo). Maintainer reviews feedback memories, authors SKILLs by hand.
- (c) **Defer indefinitely.** Wait for empirical proof the manual path doesn't scale.

**Recommendation:** (a) Build it WITH binding gate. Phase 1 = capture; Phase 2 = graduation with required objective-link.

**Rationale:** Manual graduation has worked for the current one-maintainer phase; it won't scale once the corpus exceeds maintainer recall (the MEMORY.md already exceeds its limit at 26.4KB per the system reminder). The binding gate resolves the ODD conflict: every graduated SKILL ladders up to a named objective OR is explicitly tagged as discipline-not-objective. This forces the maintainer to KEEP non-objective surface, not silently accumulate it.

**Downstream consequences:** Requires reading `docs/spec/` (objective spec) at graduation time to validate the binding. New tooling at `framework/instinct-system/` (mirrors `framework/memory-system/` shape). Composes with existing `feedback_durable_capture_for_planned_work` discipline and the `.claude/skills/skill-promotion-review/` SKILL.

**Non-tech-user-usefulness:** HIGH (long-term). Non-tech users benefit from auto-captured patterns because they don't author memory rules manually; the binding gate ensures captured patterns are KNOWN by the persona.

**Reversibility:** Medium. Tool can be retired; captured patterns persist as data; SKILLs created by graduation are durable.

**Blast radius:** Medium. Changes how feedback memories become SKILLs; affects long-term corpus shape.

**Honest doubt:** The "binding gate" might be loose enough to not actually solve the ODD conflict. If every candidate just gets the "discipline-not-objective" tag, the gate is decorative. Phase 2 design needs to harden the gate — possibly require the tag carry a Lens-Compose-With reference (e.g., "discipline; composes with L2 by reducing burden in X situation").

---

### D-MARKETPLACE — Adopt `.claude-plugin/marketplace.json` for one-line plugin install?

**Alternatives:**
- (a) **Adopt marketplace.json, phase-in alongside current source-install path.** Both shipping methods work; users pick.
- (b) **Wait for PyPI shipping path (per README line 76).** Skip marketplace.json; deliver one-line install via `pip install loam` when ready.
- (c) **Both — marketplace.json AND eventual PyPI.** They're not mutually exclusive.

**Recommendation:** (c) Adopt marketplace.json now AND keep PyPI eventual path. They compose.

**Rationale:** Marketplace.json is metadata; it costs little to author and gives users an immediate Claude-native install path (`/plugin marketplace add ...` + `/plugin install loam@loam`). The PyPI path is the CLI distribution; the marketplace path is the plugin-content distribution. The two ship to different surfaces and don't conflict. Non-tech-user-frame strongly favors this: the current 4-step source install is a translation-burden the persona can't absorb (the user is at the shell BEFORE the persona is running).

**Downstream consequences:** Author `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` at the loam repo root. Define which components/skills/agents ship in the plugin. Workspace-bootstrap composition needs to detect "installed via marketplace" vs "installed via source" — possibly trivial (both result in the same on-disk layout once `/plugin install` runs).

**Non-tech-user-usefulness:** HIGH. One-line install removes the highest current barrier.

**Reversibility:** High. marketplace.json is just metadata; remove anytime.

**Blast radius:** Low. Additive surface; existing source-install path continues working.

**Open sub-question:** Does Claude Code's marketplace install path compose with loam's two-tree workspace shape (clone-tree + workspace-tree)? Research needed before build; possibly handled by a different sequence than `loam init`. Surfaced in §8 Q3.

---

### D-INSTALL.SELECTIVE — Component-level selective install?

**Alternatives:**
- (a) **Phase 1 only: adopt manifest shape; defer SQLite state.** Single manifest.yaml describing component graph; idempotent install.
- (b) **Full Phase 1 + Phase 2 (manifest + SQLite state + per-component uninstall).** ECC-equivalent.
- (c) **Skip entirely.** Loam at 18 components doesn't need selectivity.

**Recommendation:** (a) Phase 1 only.

**Rationale:** Loam's 18 components vs ECC's ~340 catalog items — the cost-per-component-of-selectivity scales with catalog size. At loam's current size, per-component uninstall is overkill. The MANIFEST SHAPE is valuable regardless (idempotent installs, structured updates, machine-readable component graph). SQLite state-store complexity isn't justified at current inventory.

**Downstream consequences:** Replaces `install-from-source.txt`'s ordered-list shape with manifest.yaml. Installer reads manifest, computes graph, executes. Reversion of partial installs handled by re-running installer (idempotent).

**Non-tech-user-usefulness:** Indirect — manifest-shape benefits the persona (which can introspect "what's installed" without grepping files) and the installer-author (deterministic behavior).

**Reversibility:** Medium. Manifest-shape adoption is a one-time installer rewrite.

**Blast radius:** Low. Installer surface; user-visible behavior unchanged.

---

### D-TOKEN.ENFORCE — How are token-optimization defaults applied?

**Alternatives:**
- (a) **Document only** in `docs/getting-started.md`. User sets manually.
- (b) **Opt-in SKILL** that writes settings on user approval. Persona offers ("set your Claude to cost-optimised defaults? — Sonnet default, thinking-cap, etc.").
- (c) **Auto-mutate** `~/.claude/settings.json` on install. ECC-equivalent.

**Recommendation:** (a) + (b). Document AND offer an opt-in SKILL. Reject (c).

**Rationale:** Loam shouldn't silently mutate `~/.claude/settings.json` on install — that's user-config sovereignty territory; non-tech users would not understand the mutation if they later wonder "why does my Claude behave differently?" The SKILL satisfies L2 (the persona offers the optimization, reducing translation burden) without violating sovereignty (the user explicitly approves the mutation).

**Downstream consequences:** Docs section + SKILL (~50 lines). The persona can invoke the SKILL when the user signals cost-awareness ("loam costs are too high").

**Non-tech-user-usefulness:** HIGH via the opt-in SKILL (persona absorbs the technical detail); LOW via the docs section (non-tech users don't read getting-started.md for token-tuning).

**Reversibility:** High. Opt-in.

**Blast radius:** Low.

---

### D-COMPACT.SKILL — Graduate `feedback_compact_clear_decision_heuristic.md` to a SKILL?

**Alternatives:**
- (a) **Graduate.** Author `loam-skills/skills/strategic-compact/SKILL.md` derived from the memory rule.
- (b) **Status quo.** Memory rule only.

**Recommendation:** (a) Graduate.

**Rationale:** The memory rule has been stable for weeks. SKILL surface makes it auto-discoverable in derived workspaces (non-tech users get the discipline without reading the memory file). Direct application of `feedback_durable_capture_for_planned_work` graduation pattern. Composes with the D-INSTINCT.GRADUATION binding gate (this graduation is a manual instance of what the tool will eventually automate).

**Downstream consequences:** New SKILL file; reference in the memory rule pointing to the SKILL (so memory becomes index, SKILL becomes operative).

**Non-tech-user-usefulness:** HIGH. Persona invokes the SKILL when context is mid-task; non-tech user sees coherent compaction behavior without understanding the mechanism.

**Reversibility:** High.

**Blast radius:** Low.

---

### D-AGENTSHIELD — Port AgentShield to loam?

**Alternatives:**
- (a) **Port to loam core.** Standalone scanner.
- (b) **Port select patterns into `plugins/dev-sdlc/pr-safety/`.** Compose with existing v0.1.9 contract-enforcement.
- (c) **Reject.** No port.

**Recommendation:** (c) for core. Defer (b) to v0.2-class consideration.

**Rationale:** AgentShield's value-axis is "scan CODE for vulnerabilities." Non-tech-user workspaces have no code. In dev workspaces, the overlap with loam's existing pr-safety gate is substantial (per-band contract enforcement, override workflow, audit trail — see v0-1-9-master-plan.md §1). The folding-into-pr-safety question is real but v0.2-class and not in the current absorption scope.

**Downstream consequences:** None for core. v0.2-class consideration captured to FUTURE_IDEAS_DRAFT for later.

**Non-tech-user-usefulness:** NONE in core. CONDITIONAL in dev-sdlc.

**Reversibility:** Medium.

**Blast radius:** Medium (a port would be substantial code).

---

### D-LANG-REVIEWERS — Adopt 8 language-specific reviewer agents?

**Alternatives:**
- (a) **Adopt all 8.** ECC-equivalent catalog.
- (b) **Adopt PATTERN: single generic code-reviewer + on-demand language prompt-pack.** Loam-shaped.
- (c) **Reject entirely.**

**Recommendation:** (b) Adopt pattern, reject catalog.

**Rationale:** ECC's 8-agent catalog is dispatch-time overhead (catalog discovery + per-agent context). Loam's `loam-reviewer.md` already exists; extending it with a per-language prompt-pack that the persona loads on demand satisfies the value without catalog overhead. The catalog itself is dev-workspace-only and 8-language enumeration doesn't scale (the next ask is Swift, Erlang, Elixir, Lua, ...).

**Downstream consequences:** New SKILL or sub-SKILL bundle at `plugins/dev-sdlc/skills/language-review-prompts/` with per-language prompt-packs. `loam-reviewer.md` loads the relevant pack when dispatched.

**Non-tech-user-usefulness:** N/A (dev-workspace-only).

**Reversibility:** High.

**Blast radius:** Low (small extension to existing reviewer).

---

## §5 — Per-pattern absorption work-items (Wave 1 + Wave 2 sketches)

Each work-item: slug, objective, scope (in/out), dependencies, cost band, AC ladder sketch (≥1 outcome-altitude AC per `feedback_test_outcome_altitude_required.md`). NO method, NO build. Per-work-item plan-docs authored on owner ratification.

### Wave 1 work-items

#### WI-1 — Strategic-compact SKILL graduation

- **Slug:** `strategic-compact-skill-graduation`
- **Objective:** Graduate `feedback_compact_clear_decision_heuristic.md` from a memory rule into an auto-discoverable SKILL at `plugins/loam-skills/skills/strategic-compact/SKILL.md`, with content derived from the memory rule + ECC's `skills/strategic-compact/` content where additive.
- **Scope in:** New SKILL.md; SKILL frontmatter; reference in the memory rule pointing to the SKILL; one outcome-altitude smoke that the persona discovers + invokes the SKILL during a mid-session breakpoint scenario.
- **Scope out:** Auto-firing of /compact (the SKILL guides; doesn't trigger); changes to existing /compact behavior; new hook surface.
- **Dependencies:** None.
- **Cost band:** sm (≤ 4 h AI-time).
- **AC ladder sketch:**
  - **AC.SCG.1** — SKILL.md exists at canonical path with valid frontmatter (description, trigger criteria).
  - **AC.SCG.2** — SKILL discoverable via `claude-agents-view` SKILL OR `/` menu (auto-discovered, not manually loaded).
  - **AC.SCG.S** (outcome-altitude) — synthetic session: a fresh loam workspace, simulated mid-task context-pressure breakpoint, the persona invokes the strategic-compact SKILL and emits the SKILL's prescribed decision-text (compact / don't compact / clear). Test calls the production persona dispatch path with no pre-arranged state.

#### WI-2 — Hook-based input-layer security guards

- **Slug:** `safety-layer-input-hooks`
- **Objective:** Install three PreToolUse hooks in `framework/safety-layer/hooks/` blocking (a) secret-pattern leaks (sk-/ghp_/AKIA + ~10 more), (b) dangerous git flags (--no-verify, --force-with-lease alternates per safety policy), (c) writes to known-protected config files (.eslintrc, biome.json, .git/config). Diagnostics surface structured failure messages naming the blocked pattern + suggested alternative.
- **Scope in:** Three new hook scripts; hooks.json wiring; tests per hook + integration tests; toggle-off env var.
- **Scope out:** Refusal-chain extensions (composes with existing safety-layer; doesn't replace); content-deep secret scanning (this is pattern-class only); PostToolUse cleanup hooks.
- **Dependencies:** None (composes with existing `framework/safety-layer/`).
- **Cost band:** sm-md (4–8 h).
- **AC ladder sketch:**
  - **AC.SLIH.1** — Secret-pattern hook fires on Bash + Edit + Write tool calls; blocks 14 named patterns; emits structured diagnostic.
  - **AC.SLIH.2** — Dangerous-flag hook blocks `git push --no-verify`, `git commit --no-verify` (per `feedback_no_amend_in_agent_dispatches` discipline already in corpus + extension).
  - **AC.SLIH.3** — Config-write hook blocks writes to .eslintrc / biome.json / .git/config / .pre-commit-config.yaml.
  - **AC.SLIH.4** — Toggle-off via `LOAM_SAFETY_HOOKS=off` env var disables all three.
  - **AC.SLIH.S** (outcome-altitude) — synthetic session: a fresh loam workspace, agent attempts each blocked operation in turn (secret paste, --no-verify push, .eslintrc edit), all three blocked, each diagnostic emitted. Test invokes production hook dispatch path with no pre-arranged state.

#### WI-3 — Token-optimization defaults documenter + opt-in SKILL

- **Slug:** `token-defaults-docs-and-skill`
- **Objective:** (a) Add token-optimization defaults section to `docs/getting-started.md`. (b) Author SKILL `plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md` that, when invoked by the persona, presents the user with the recommended settings, awaits explicit approval, then writes them to `~/.claude/settings.json` (preserving existing keys).
- **Scope in:** Docs section; SKILL.md; settings-merge logic (non-destructive); outcome-altitude smoke (persona invokes SKILL; user approves; settings written; existing keys preserved).
- **Scope out:** Auto-mutate on install; changes to loam's own dispatch token discipline (already Sonnet-default).
- **Dependencies:** None.
- **Cost band:** sm.
- **AC ladder sketch:**
  - **AC.TDDS.1** — Docs section exists in `docs/getting-started.md` listing the 4 recommended settings with savings rationales.
  - **AC.TDDS.2** — SKILL.md exists; describes invocation criteria + user-approval flow.
  - **AC.TDDS.3** — Settings-merge preserves existing keys when writing recommended values.
  - **AC.TDDS.S** (outcome-altitude) — synthetic session: persona detects user cost-concern signal, invokes SKILL, presents defaults, user approves, settings.json updated, existing user keys preserved.

#### WI-4 — README restructure (decision-doc framing)

- **Slug:** `readme-decision-doc-restructure`
- **Objective:** Restructure `README.md` to lead with audience-routing ("is this for you?") + positioning before installation. Hoist the philosophy summary; ensure first-screen reader sees positioning, not commands.
- **Scope in:** README.md edits only.
- **Scope out:** New documentation files; positioning.md edits (separate doc); marketing copy changes outside README.
- **Dependencies:** None.
- **Cost band:** sm (≤ 2 h).
- **AC ladder sketch:**
  - **AC.RDR.1** — README opens with positioning summary + "is this for you?" subsection BEFORE the Quickstart command block.
  - **AC.RDR.2** — All current README content preserved (no removals; reordering only).
  - **AC.RDR.S** (outcome-altitude) — out-of-band reader review (could be a second agent dispatch authored as a verification step): first-screen scan answers "what is loam?" "is this for me?" "what does it cost?" in 30 seconds.

### Wave 2 work-items (sketches only — author full plan-docs at ratification)

- **WI-5: observer-loop guard extension** — `framework/cost-governance/observer-loop-guard.py` + tests + AC.OLG.* family + outcome-altitude smoke spawning a synthetic re-entrant subagent chain.
- **WI-6: marketplace.json + plugin.json authoring** — `.claude-plugin/` directory + manifest content + verification of `/plugin install loam@loam` flow against fresh Claude Code instance + AC.MPL.* family. Dependency: D-MARKETPLACE ratified.
- **WI-7: install manifest-shape Phase 1** — convert `install-from-source.txt` → `install-manifest.yaml`; installer reads manifest; idempotent install verified; AC.IMS1.* family. Dependency: D-INSTALL.SELECTIVE ratified.
- **WI-8: instinct capture Phase 1** — `framework/instinct-system/` capture-only mode (SessionEnd hook writes candidate patterns to `<workspace>/.loam/instincts/`); no graduation tooling yet; AC.IC1.* family. Dependency: D-INSTINCT.GRADUATION Phase 1 ratified.
- **WI-9: search-first + iterative-retrieval SKILLs** — two SKILL.md files; graduated from existing dispatch discipline; AC.SFI.* + AC.IR.* families.

### Wave 3+ sketches

- **WI-10: TDD-workflow SKILL into dev-sdlc** — `plugins/dev-sdlc/skills/tdd-workflow/`; composes with existing `tdd_guard.py` hook.
- **WI-11: instinct graduation Phase 2 with binding gate** — graduation tool reading objective spec at graduation time; dispatch decision against D-INSTINCT.GRADUATION Phase 2.
- **WI-12: generic build-error-resolver agent** — `plugins/dev-sdlc/agents/loam-build-resolver.md` + per-language prompt-pack mechanism.
- **WI-13: harness-health-audit SKILL** — `plugins/loam-skills/skills/harness-health-audit/`; persona invokes on cadence or owner request.

---

## §6 — Prioritization + sequencing

### Waves

**Wave 1 — universal low-cost high-leverage. Total: 4 work-items.**
- WI-1 (strategic-compact SKILL)
- WI-2 (security hooks)
- WI-3 (token defaults docs + opt-in SKILL)
- WI-4 (README restructure)

Parallelization: WI-1, WI-3, WI-4 are mutually independent and can dispatch in parallel as plan-authoring jobs. WI-2 (hooks) is independent. All four can build in parallel research-wise; build phase serializes per `feedback_serialize_amendment_builds` (or uses worktree isolation if owner approves parallel builds — separate dispatch).

Cost band totals: ~12–18 h AI-time wave-total.

**Wave 2 — architecture decisions + medium-cost. Total: 5 work-items.**
- WI-5 (observer-loop guard)
- WI-6 (marketplace.json) — DEPENDS on D-MARKETPLACE ratified
- WI-7 (install manifest Phase 1) — DEPENDS on D-INSTALL.SELECTIVE ratified
- WI-8 (instinct capture Phase 1) — DEPENDS on D-INSTINCT.GRADUATION Phase 1 ratified
- WI-9 (search-first + iterative-retrieval SKILLs)

Parallelization: WI-5 + WI-9 independent. WI-6/7/8 sequence after owner ratification.

Cost band totals: ~25–40 h AI-time wave-total.

**Wave 3 — dev-plugin absorptions + Phase-2 work. Total: ~4 work-items.**
- WI-10 (TDD-workflow SKILL into dev-sdlc)
- WI-11 (instinct graduation Phase 2) — DEPENDS on D-INSTINCT.GRADUATION Phase 2 ratified + WI-8 sealed
- WI-12 (generic build-error-resolver)
- WI-13 (harness-health-audit SKILL)

Cost band totals: ~15–30 h AI-time wave-total.

### Critical path

Wave 1 → Wave 2 ratification round → Wave 2 builds → Wave 2 ratification of Phase-2 decisions → Wave 3.

Maintainer-availability-bound: ratification rounds need maintainer time (probably 2–4 hours of focused review per round across the 8 named decisions). AI-time is the gate for build work; maintainer-time is the gate for decision work.

### High-leverage low-cost first, architecture decisions second, high-cost low-leverage last

Wave 1 follows this exactly. Wave 2 mixes architecture decisions (P7, P8, P9) with one low-cost SKILL pair (P18) — the low-cost work CAN ship without the architecture decisions; if maintainer-availability for ratification is the bottleneck, dispatch WI-5 + WI-9 first.

---

## §7 — Out-of-scope (explicit rejections)

| Item | Rationale |
|---|---|
| **Cross-tool support / `AGENTS.md` / .cursor/ / .codex/ / .opencode/ / .github/ / .zed/** | Per maintainer ruling TG 12242 + L1 (loam is Claude-only by lens). No further analysis. |
| **Language-specific reviewer catalog (8 agents)** | Per D-LANG-REVIEWERS — dispatch-time overhead; pattern-not-catalog approach absorbed instead. |
| **AgentShield port to loam core** | Per D-AGENTSHIELD — non-tech-user workspaces have no code to scan; dev-workspace overlap with existing pr-safety. |
| **Tkinter dashboard GUI** | Per P22 — cuts against L1 (Claude-leverage) and L2 (translation burden adds, not reduces). |
| **ECC operator suite (brand-voice / billing-ops / google-workspace-ops / etc.)** | Per P24 — adopt PATTERN (domain-specialised personas) not catalog; specific suite is ECC's roadmap not loam's. |
| **ECC 2.0 Rust control-plane** | Per P25 — incompatible with loam's Python + Claude-attached runtime framing. |
| **Continuous-learning v1 (legacy Stop-hook pattern extraction)** | Per ECC README — v1 maintained for compatibility only; v2 is the recommended pattern. Loam absorbs v2-shape (with binding gate) only. |
| **Comparison experiment (loam-vs-ECC head-to-head)** | Out of this plan's scope — separate dispatch per research artifact §3.6. |
| **Hackathon emulation** | Same — separate dispatch. |
| **Auto-mutation of `~/.claude/settings.json` on install** | Per D-TOKEN.ENFORCE — user-config sovereignty + non-tech-user surprise. |

---

## §8 — Open questions for maintainer (one-question-at-a-time, ranked by criticality)

### Q1 (CRITICAL) — D-SEC.HOOKS placement: core or dev-sdlc or new plugin?

**Question:** Where should the hook-based input-layer security guards (secret-detection, dangerous-flag-block, config-write-protect) live?

**Options:**
- (a) Core loam, always-on — `framework/safety-layer/hooks/`
- (b) `dev-sdlc/` plugin, dev-mode-only
- (c) New opt-in `safety` plugin

**Recommendation:** (a). See D-SEC.HOOKS §4.

**Rationale:** Failure mode is workspace-agnostic; non-tech users benefit more, not less.

**Blast radius:** Low (hooks fail-open).

**Reversibility:** High (toggle via env var).

### Q2 (CRITICAL) — D-INSTINCT.GRADUATION: build with binding gate, manual only, or defer?

**Question:** Build instinct → SKILL graduation tooling now (with ODD objective-binding gate), keep manual graduation only, or defer indefinitely?

**Options:**
- (a) Build with binding gate, two phases (capture then graduate)
- (b) Manual only (status quo)
- (c) Defer

**Recommendation:** (a). See D-INSTINCT.GRADUATION §4.

**Rationale:** Manual won't scale past current corpus size (MEMORY.md already at limit); binding gate resolves the ODD conflict.

**Blast radius:** Medium (changes how corpus evolves).

**Reversibility:** Medium.

**Honest doubt:** Binding gate design might be decorative if every candidate just gets the "discipline-not-objective" tag. Design needs Phase-2-level rigor.

### Q3 (IMPORTANT) — D-MARKETPLACE: adopt marketplace.json now or wait for PyPI?

**Question:** Author `.claude-plugin/marketplace.json` for one-line `/plugin install loam@loam` install now, or wait for the eventual PyPI shipping path?

**Options:**
- (a) Marketplace now + PyPI eventual (compose)
- (b) PyPI only
- (c) Both not now

**Recommendation:** (a). See D-MARKETPLACE §4.

**Rationale:** Different surfaces; non-conflicting; marketplace removes the highest current install barrier for non-tech users.

**Open sub-question:** Does Claude Code's marketplace install compose with loam's two-tree workspace shape? Needs research before build.

**Blast radius:** Low (additive).

**Reversibility:** High.

### Q4 (IMPORTANT) — D-INSTALL.SELECTIVE: Phase 1 only, full Phase 1+2, or skip?

**Question:** Adopt the manifest-shape selective install (Phase 1), the full SQLite-state version (Phase 1+2), or skip entirely?

**Options:**
- (a) Phase 1 only
- (b) Full Phase 1 + 2
- (c) Skip

**Recommendation:** (a). See D-INSTALL.SELECTIVE §4.

**Rationale:** 18 components don't justify SQLite-state complexity; manifest-shape gives most of the value.

**Blast radius:** Low (installer surface).

**Reversibility:** Medium.

### Q5 (IMPORTANT) — D-TOKEN.ENFORCE: docs + opt-in SKILL, or auto-mutate?

**Question:** How should token-optimization defaults be applied — documented + offered via opt-in SKILL, or auto-mutated on install?

**Options:**
- (a) Document + opt-in SKILL
- (b) Auto-mutate on install
- (c) Document only

**Recommendation:** (a). See D-TOKEN.ENFORCE §4.

**Rationale:** User-config sovereignty + non-tech-user surprise; SKILL satisfies translation burden without violation.

**Blast radius:** Low.

**Reversibility:** High.

### Q6 (NORMAL) — D-COMPACT.SKILL: graduate the memory rule to a SKILL?

**Recommendation:** Yes. See D-COMPACT.SKILL §4. Lowest-controversy decision in the set; could be implicit-yes unless maintainer objects.

### Q7 (NORMAL) — D-AGENTSHIELD: confirm reject-for-core / defer-for-dev?

**Recommendation:** Confirm. See D-AGENTSHIELD §4.

### Q8 (NORMAL) — D-LANG-REVIEWERS: confirm pattern-not-catalog?

**Recommendation:** Confirm. See D-LANG-REVIEWERS §4.

---

## §9 — Halt triggers (in-flight; if any fire during build, halt the offending work-item)

1. **Wave 1 hook bundle (WI-2) creates a hook that fires on legitimate operations** at a rate exceeding ~1 false-positive per session. Halt and tighten patterns; do not ship a noisy hook.
2. **Wave 2 marketplace.json (WI-6) discovers Claude Code's `/plugin install` flow incompatible with loam's two-tree shape.** Halt and surface; research a different install path.
3. **Wave 2 instinct-capture (WI-8) writes patterns to `<workspace>/.loam/instincts/` faster than the persona can review them.** Halt; redesign capture criteria.
4. **Any Wave 1+ work-item's outcome-altitude smoke fails to invoke production entry-point with no pre-arranged state** (test is pre-arranged or mock-laden) — halt per `feedback_test_outcome_altitude_required.md`.
5. **A pattern recommended ABSORB-WAVE-N turns out to require dev-mode partition compliance** that the work-item didn't anticipate. Halt and re-classify; re-author per `feedback_odd_cdc_scope.md`.

---

## §10 — F2 Ruthless Feedback (honest doubts)

1. **"Continuous-learning v2 with binding gate" might be wishful design.** The binding gate is the resolution mechanism for the ODD conflict; if every captured pattern gets the "discipline-not-objective" tag, the gate is decorative and the ODD violation ships unresolved. Phase 2 design needs to prove the gate is real (e.g., gate-fail rate > 30% on a sample of candidate captures, demonstrating it actually rejects bad candidates).

2. **The "non-tech user is the audience" frame may be aspirational at current loam maturity.** Loam's current install is 4 shell commands; the current onboarding ritual assumes user can answer 6 questions about goals/preferences; the current persona output sometimes uses internal jargon (SHAs, AC IDs, agent names) per `feedback_translate_outbound_too`. Saying "non-tech users are the audience" is correct positioning per L2, but the current product gap is substantial. This plan absorbs patterns that help close the gap (marketplace, token-defaults SKILL, README restructure, security hooks); it does NOT pretend the gap is closed. Maintainer should be aware that absorbing ECC patterns doesn't automatically make loam non-tech-friendly — those are separate axes.

3. **The "everything ECC does is conditional on having no ODD" frame is too clean.** ECC has REAL methodology — TDD enforcement, planner-architect orchestration, strategic-compact, verification loops. The methodology isn't ODD-shaped but it isn't absent. Loam absorbing ECC's patterns while keeping ODD discipline is a real engineering task; the per-pattern analysis above tries to surface where the methodologies compose vs conflict, but the depth of analysis varies by pattern. WI-9 (search-first + iterative-retrieval SKILLs) is the lowest-conflict; WI-11 (instinct graduation Phase 2) is the highest-conflict; the others are between.

4. **The Wave 1 absorptions are "obvious wins" that risk being TOO obvious — i.e., why hasn't loam built them already?** Possible answers: (a) maintainer time-bounded; (b) absorption-from-ECC frame is itself new (this dispatch); (c) the patterns are obvious in retrospect but weren't on the priority list. F2 self-check: WI-1 (strategic-compact SKILL graduation) and WI-4 (README restructure) are ~2-hour absorptions that arguably should have shipped weeks ago. The fact they didn't suggests there are absorption-vs-other-work prioritization questions outside this plan's scope. Maintainer should consider whether the Wave 1 work is genuinely time-best-spent now vs deferred to free attention for other backlog.

5. **The 25-pattern inventory is exhaustive of ECC's CURRENT surface but ECC is shipping weekly per the research artifact §1.3.** New ECC patterns may land before loam ships Wave 1. Recommendation: capture the absorption frame as durable discipline (a SKILL?) so subsequent ECC pattern surfaces can be evaluated against the same two filters without re-authoring this whole plan. Captured as FIDRAFT in §11.

6. **The "loam already has this" rows (P6, P11, P12, P16) are based on file-existence not behavior-equivalence.** I verified that `loam-reviewer.md`, `loam-planner.md`, `loam-plan-author.md`, `/loop`, `/goal` SKILLs all exist; I did NOT compare their internal content against ECC's equivalents. The optional cross-check dispatches in Wave 3 (per P11, P12, P16) would resolve this; if maintainer wants confidence higher than "files exist," dispatch those cross-checks earlier.

7. **The "no method in this plan" discipline (per AGENT-PROMPTS-SCOPE-ONLY) is tested on the AC ladders.** Each AC.*.* sketch in §5 is outcome-shaped (passes method-in-AC test: AC.SLIH.1 "secret-pattern hook fires + blocks" can be satisfied by hook-script in Node, Python, or any other language; AC.SCG.S "persona discovers + invokes SKILL during mid-session breakpoint" can be satisfied by SKILL frontmatter, by content, by trigger-design). F4 scope-confidence: high for AC outcome shapes; low for implementation choices (intentionally — those are builder's call).

8. **F4 calibration for this plan-doc itself.** Inventory section (§3) is TIGHT-scope (per row: specific source + specific verdict + specific recommendation) — high confidence in the per-pattern call. Architecture decisions section (§4) is LOOSER (alternatives + rationale + honest doubt + reversibility) — maintainer's call to make, not mine. AC ladder sketches (§5) are LOOSE per-method but TIGHT per-outcome — per AGENT-PROMPTS-SCOPE-ONLY. Per F4: the loose/tight mix matches the confidence-shape (high on per-pattern observations, lower on architecture, low on method).

---

## §11 — FIDRAFT capture (for the maintainer to graduate or discard)

- **F-ECC-PATTERN-ABSORPTION-DISCIPLINE-AS-SKILL** — the two-filter discipline used in §3 (mechanism-without-objectives analysis + non-tech-user-frame verdict) could graduate to a SKILL the persona invokes whenever new ECC patterns surface. Captured per `feedback_durable_capture_for_planned_work`; graduate post-Wave-2 if absorption becomes a recurring activity.
- **F-VALUE-PROPOSITION-VS-CURRENT-LOAM-GAP-AUDIT** — §10 doubt #2 surfaces the gap between "non-tech-user audience" framing and current loam ergonomics. A standalone audit dispatch (different from this absorption plan) could enumerate every translation burden currently on the user; output is a punch-list of UX work parallel to the ECC absorption work.
- **F-ECC-PATTERN-WATCH-CADENCE** — §10 doubt #5: ECC ships weekly; loam should re-evaluate the surface on cadence (quarterly?). A scheduled SKILL/loop could surface new patterns for absorption-or-reject calls.

---

## §12 — Provenance trail

All citations verified Tier-0 (file-read or WebFetch on 2026-05-24).

**Maintainer directives:**
- Telegram 12235 (2026-05-24T14:59:32Z) — research ask
- Telegram 12240 (2026-05-24T15:14:38Z) — "take all the useful stuff his thing does and repackage it as part of loam"
- Telegram 12242 (2026-05-24T15:19:25Z) — non-tech user is the audience; don't adopt AGENTS.md as a whole

**Research artifact:**
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/everything-claude-code-research-2026-05-24.md` (loam-researcher dispatch 2026-05-24)

**ECC sources (verified 2026-05-24 via WebFetch):**
- README at `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/README.md` — pattern catalog, subsystem inventory, version 2.0.0-rc.1 notes
- AGENTS.md at `https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/AGENTS.md` — two-tier permissions model + orchestrator/specialist delegation
- Skills directory at `https://github.com/affaan-m/everything-claude-code/tree/main/skills` — alphabetical organization confirmed; 100+ skills sampled
- Hooks directory at `https://github.com/affaan-m/everything-claude-code/tree/main/hooks` — 5 event types, Node.js implementation, security-focused hooks (secret detection, dangerous flag blocking) confirmed

**Loam sources (verified 2026-05-24 via Read/Bash):**
- `/Users/lukeivers/loam/CLAUDE.md` — 7 lenses
- `/Users/lukeivers/loam/docs/VALUE_PROPOSITION.md` — primary persona as translation layer
- `/Users/lukeivers/loam/docs/design/principle-derivation-map.md` — F4 compose-with/independent/partial table
- `/Users/lukeivers/loam/README.md` — current public surface (lines 19, 80, 102 cited)
- `/Users/lukeivers/loam/plugins/dev-sdlc/` + `loam-skills/` directory listings — existing plugin shape
- `/Users/lukeivers/loam/.claude/agents/` — confirmed loam-{builder,documenter,plan-author,researcher,reviewer}.md exist
- `/Users/lukeivers/loam/.claude/skills/` — confirmed strategic-compact / instinct-capture / harness-health absent
- `/Users/lukeivers/loam/docs/plans/v0-1-9-master-plan.md` — master-plan shape exemplar
- `/Users/lukeivers/loam/docs/plans/sealed/amendment-141-seal-tool-section-14-backfill-decouple.md` — recent canonical-shape plan-doc exemplar (§14 D-* register pattern)

**Memory rules referenced:**
- `feedback_odd_cdc_scope.md` — dev-CDCs scope to pos-v2 / dev work only
- `feedback_compact_clear_decision_heuristic.md` — D-COMPACT.SKILL graduation candidate
- `feedback_test_outcome_altitude_required.md` — every AC family carries ≥1 outcome-altitude AC
- `feedback_durable_capture_for_planned_work.md` — graduation pattern for memory→SKILL
- `feedback_summarize_and_surface_decisions.md` — §1 executive summary format
- `feedback_serialize_amendment_builds.md` — Wave dispatch sequencing
- `feedback_translate_outbound_too.md` — §10 doubt #2 source
- `feedback_no_amend_in_agent_dispatches.md` — composes with WI-2 dangerous-flag hook

**Lens references:**
- L1 Claude-leverage-first (CLAUDE.md:22) — composes with marketplace, hooks
- L2 Harness + primary-persona value (CLAUDE.md:42; VALUE_PROPOSITION.md throughout) — non-tech-user frame
- L3 ODD authoring (CLAUDE.md:62) — D-INSTINCT.GRADUATION conflict source
- L4 Prompt scope ↔ confidence (CLAUDE.md:71) — §10 doubt #8 application
- L5 Swarming (CLAUDE.md:108) — Wave dispatch shape + EVAL_DIMENSIONS judging
- L6 Principle-conflict resolution (CLAUDE.md:158) — D-INSTINCT.GRADUATION conflict resolution methodology
- L7 Ruthless Feedback (CLAUDE.md:198) — §10 honest doubts

---

## §13 — Authoring trail

Authored 2026-05-24 by `loam-plan-author` subagent, dispatched per re-dispatch incorporating maintainer directives TG 12240 + TG 12242. Original dispatch was scope-too-broad (pre-flagged cross-tool as decision point); re-dispatch added the two load-bearing constraints (non-tech-user audience + drop AGENTS.md) and tightened the plan scope accordingly.

Plan-doc ratification: pending. Per-pattern absorption work-items dispatch on owner ruling per §8 question.

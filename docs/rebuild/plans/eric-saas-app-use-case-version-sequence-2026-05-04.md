# Eric's SaaS-app use case — version sequence to a deliverable loam

**Authored:** 2026-05-04. **Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Doc class:** planning + analysis (pre-build, doc-only). **Trigger:** Luke directive 2026-05-04 — Eric (a friend at his job) will use loam against an existing production SaaS application that processes tens-to-hundreds of thousands of dollars of real customer transactions, and the application has never had its top-level objectives written down. Loam must reverse-engineer those objectives from existing code, maintain them as the authoritative contract, gate every PR against the contract, and drive bug + feature work end-to-end with minimal Eric-input. Plus: anything dev-related goes into `plugins/dev-sdlc/`, not core `framework/`. **Length target band:** 5000–10000 words.

**Anchor sources cited inline:** `docs/rebuild/VALUE_PROPOSITION.md`; `docs/rebuild/STATE.md`; `docs/rebuild/plans/v0-1-x-roadmap.md`; `docs/rebuild/plans/value-prop-vs-actual-shape-audit-2026-05-04.md`; `docs/rebuild/FUTURE_IDEAS_DRAFT.md`; `docs/design/odd.md`; `plugins/dev-sdlc/docs/smoke-test-discipline.md`; `plugins/dev-sdlc/docs/cdcs/`; `plugins/loam-skills/skills/`; `framework/CLAUDE.md` (= top-level `CLAUDE.md`).

---

## Principles applied this turn (per session-start discipline)

- **CHANNEL** — reply lands at the dispatcher (main session); no Telegram in this dispatch context.
- **AUTONOMY** — research broadly within scope; surface findings; recommend a version sequence without check-ins.
- **F2 RUTHLESS FEEDBACK** — name where Eric's use case exposes loam gaps; name evidence; name alternatives. Apply to Luke's framing where warranted.
- **LOCKED-DESIGN-NOT-LICENSE** — the v0.1.x roadmap was sized for iterate-in-public; Eric's use case is concrete and may force re-sequencing. Surface that explicitly.
- **ODD §2.5** — every recommendation maps to a named source.
- **OUTPUT-TO-DISK** — full plan to disk; reply summary inline.
- **DURABLE-CAPTURE** — this plan-doc IS the durable surface.
- **WD-IN-DISPATCHES** — confirmed `/Users/lukeivers/ivers-corp-pos-v2/`.
- **PARTITION RULE** — anything dev-related → `plugins/dev-sdlc/`; harness-general → `framework/`. Enforced throughout, audited in §12.
- **TRANSLATION RULE** — executive summary readable by non-technical reader.

---

## Executive summary (non-technical)

A friend of Luke's named Eric works at a company that runs a software product real businesses pay it to use. That product moves a lot of money — tens to hundreds of thousands of dollars per day — for those businesses. If the software starts behaving incorrectly, real people lose real money, and the company faces real legal exposure.

Eric wants to use loam — Luke's AI-built helper for working with codebases — to help him fix bugs and add features safely. The problem: nobody at the company has ever written down what the software is *supposed* to do. They have working code, but the rules the code is enforcing are implicit. That makes safe change-making hard, because there's no way to check "did this PR violate one of the rules?" if the rules aren't written down.

Loam, today, is good at building loam itself. It has not been pointed at a foreign codebase before. To deliver to Eric, loam needs three big new capabilities and one rebalancing of an existing one:

1. **Reverse-engineer business rules from existing code.** Loam reads Eric's app and produces a written contract — the rules the app is currently enforcing — that Eric and his team can review and ratify.
2. **Gate every change against that contract.** Before any code change merges, loam checks whether it violates a rule. If it does, the change is blocked unless the rule itself is being deliberately updated.
3. **Drive change work end-to-end with minimal Eric input.** Eric describes what he wants in plain language; loam translates that into design, plan, code, tests, and PR. Eric reviews and approves; he does not micro-manage.
4. **Stay safe by default for production-stake work.** Loam already has safety primitives, but they were calibrated for Luke building loam. Eric's stakes are higher; the defaults shift toward "halt and ask" rather than "proceed autonomously."

The recommended path is **six new releases beyond the current v0.1.x roadmap** — call them v0.1.6 through v0.2.2 — sequenced over an estimated **40–80 hours of AI-time** plus Eric- and Luke-time for review checkpoints. The endpoint is a release Eric can install, point at his company's codebase, and trust to help him without putting production at risk.

The rest of this document is the technical version of that sequence.

---

## §1 — Eric's use case: formal restatement

### 1.1 — Actors

- **Eric (primary user).** Works on a foreign codebase at his job. Wants minimal-input usage — describes intent, reviews persona output, approves changes. Not a loam expert; will not author plan-docs, manifests, or seal cycles by hand.
- **Eric's team (secondary).** Reviews PRs in their normal workflow; needs PRs that look human-authored, are explainable, and pass their existing review bar.
- **Eric's company (stakeholder, never directly addressed).** Runs the production SaaS app; bears the financial / legal consequence of regressions.
- **Eric's customers (ultimate stakeholder).** Real businesses moving real money through the SaaS. A regression in payment-handling, accounting, or contract enforcement directly hits their books.
- **Loam's primary persona.** Translation layer (per `VALUE_PROPOSITION.md:17-32`); routes Eric's intent to specialists; integrates results back as one voice.
- **Per-project PM persona** (FIDRAFT entry, `docs/rebuild/FUTURE_IDEAS_DRAFT.md:25`). Per-project scoped; absorbs project-specific coordination state Luke's persona (and Eric's) shouldn't have to hold.
- **Specialist subagents** (FIDRAFT entry, `FUTURE_IDEAS_DRAFT.md:189`; v0.1.4 roadmap §2 item 1). Builder / reviewer / researcher / etc., dispatched by the PM.

### 1.2 — Inputs

- An existing running SaaS-app codebase (Python / Ruby / Node / mixed — language unknown; loam must be language-agnostic per FIDRAFT V11.C heavy-version entry, `FUTURE_IDEAS_DRAFT.md:175`).
- Existing test suite (coverage unknown).
- Existing docs, README, CHANGELOG, runbooks, deployment configs (sparseness unknown).
- Runtime behaviour observable from logs, monitoring, production traffic samples (access TBD).
- Eric's natural-language descriptions of intended changes.
- Eric's natural-language confirmations / rejections at decision points.

### 1.3 — Outputs

- **A written, ratified business-objectives contract** — what the app is supposed to do, decomposed into top-level objectives + sub-objectives + acceptance criteria — stored under the SaaS-app's own repo (not in loam's repo).
- **PRs** that look like normal PRs to Eric's team; trigger CI as they normally would; carry a standard PR description; include test coverage for any contract surface the change touches.
- **Decision-surfaces to Eric** — at moments where the persona genuinely cannot proceed without input (a contract gap, a tradeoff, a production-blast-radius decision), Eric receives a single-sentence question with options + recommendation, in his preferred channel (Telegram per Luke's stack; alternative TBD per Eric's preferences).
- **Audit trail** — every loam-driven change traceable to (a) the natural-language Eric directive that produced it, (b) the contract surface it ladders up to, (c) the test that pins it, (d) the gate(s) that approved it.

### 1.4 — Success criteria

- **SC1.** Eric describes a feature or bug-fix in one paragraph; loam produces a mergeable PR within an hour of AI-time, against a contract surface either pre-existing or newly extended-in-band per ODD §4 (the re-extension rule, `docs/design/odd.md:188-204`).
- **SC2.** A PR that would violate an objective contract is blocked at gate-time unless the contract is being deliberately updated as part of the same change-set, with the update itself approved by Eric.
- **SC3.** Across N=20+ Eric-driven change cycles, zero production regressions traceable to loam-introduced behaviour. (Strict zero-tolerance because the stakes are real money.)
- **SC4.** Eric spends < 30 minutes / day on loam interaction, of which ≥ 80% is review/approve and ≤ 20% is direction/correction.
- **SC5.** Eric's team accepts loam-authored PRs at the same rate they accept human-authored PRs, with no observable "this looks AI-written" tell that triggers extra scrutiny.

### 1.5 — Failure modes (named)

- **F1 — Hallucinated contract.** Loam derives an objective from code that doesn't actually enforce that objective, gates pass that should fail, real regression slips. Highest-blast-radius failure.
- **F2 — Missed contract.** A real business rule is not derived; loam doesn't gate against it; a PR violates the rule undetected. Same outcome as F1, different root cause.
- **F3 — Over-cautious blocking.** Every change is halted-and-surfaced; Eric does more work than he saved. Renders loam not-worth-using.
- **F4 — Foreign-language fail.** Loam's tooling assumes Python idioms (per loam's own implementation language, `STATE.md:23`) and chokes on Ruby/Node/Go/etc.
- **F5 — Production-action escalation.** Loam touches production directly (deploy, DB migration, config change) without owner approval. Out-of-bound for Eric's authority surface.
- **F6 — Audit-trail loss.** A loam-driven change merges with no provenance trail; post-incident triage cannot trace why the change happened. Composes with F1/F2.
- **F7 — Cost runaway.** A pathological codebase produces a multi-thousand-dollar token bill on first reverse-engineering pass. Cost-governance must cap.

### 1.6 — Blast-radius bands (calibration for halt-and-surface defaults)

- **Band A — zero blast.** Plan-docs, research notes, candidate-contract drafts, local test additions. Default: proceed autonomously.
- **Band B — local code change, reverted in seconds.** Test-only changes, in-branch source edits, branch-scoped commits before push. Default: proceed autonomously.
- **Band C — visible-to-team artefact.** PR opened, branch pushed to shared remote. Default: surface a one-line summary to Eric before opening.
- **Band D — merge to mainline.** Mergeable PR at green CI. Default: HALT-AND-SURFACE; Eric ratifies merge.
- **Band E — production-touching action.** Deploy trigger, DB migration, prod config edit, secrets touch. Default: HARD-REFUSE in v0.1.x (Eric does these manually); v0.2.x may admit Band E with paired-eyes.

These bands are not the same as loam's existing reversibility classes (`docs/design/odd.md` §1 constraints — fully reversible / compensatable / irreversible). The bands map to **PR-shape** (the surface Eric sees), not to **action-shape** (what the runtime does). Both apply.

---

## §2 — Capability inventory: what loam can do today

The 13 sealed components + recent amendments + sealed plugins are the substrate. This section maps Eric's required capabilities to what's already shipped, partial, or missing.

### 2.1 — Already shipped + load-bearing for Eric

| Capability | Component / source | Confidence |
|---|---|---|
| Primary persona as translator | `framework/primary-persona/`, `docs/design/primary-persona-shape.md`, `VALUE_PROPOSITION.md` | High — sealed + design-doc-articulated |
| Sealed-component amendment cycle (research → plan → manifest → seal) | `plugins/dev-sdlc/tools/loam-amend/` + `plugins/dev-sdlc/docs/conventions/amendment-cycle.md` | High — proven across ~125 amendments |
| ODD methodology (objective + AC + halt-and-surface) | `docs/design/odd.md`, `plugins/dev-sdlc/docs/odd-methodology.md` | High — published + practised |
| Workspace bootstrap | `framework/workspace-bootstrap/` | High — sealed |
| File-based memory (M-FBM) | `framework/primary-persona/` (worker) + `framework/workspace-bootstrap/` (plist) | Medium — operational-health amendment #125 just sealed (`1a1f830`); production-grade for cross-session continuity not yet field-validated outside loam-of-loam |
| Background-agent dispatch (scope-only) | `plugins/dev-sdlc/docs/cdcs/scope-only-dispatch.md` + `plugins/dev-sdlc/docs/cdcs/background-agents-default.md` | High — practised daily |
| Translation skills (5 SKILL.md packages) | `plugins/loam-skills/skills/` | High — sealed at `f04e925` |
| Telegram channel + pause-on-outage | `~/.claude/CLAUDE.md` (rule); persona-prompt observation | Medium — discipline-only; structural-enforcement deferred (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:125`) |
| Smoke-test 6-dimension discipline | `plugins/dev-sdlc/docs/smoke-test-discipline.md` | High — sealed at `4fb9e3c` |
| Graceful-fallthrough-with-detection CDC | `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md` | High — sealed; audit-pass-across-components deferred (FIDRAFT entries) |

### 2.2 — Partial / needs widening for Eric

| Capability | Status | Gap |
|---|---|---|
| Foreign-codebase comprehension | Loam reads its own codebase via Read/Grep tools. No structured reverse-engineering primitive. | V11.C heavy version (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:175`) is the placeholder; deferred from v0.1.3 to v0.1.4+ per 2026-05-04 ruling. **Currently sized for `framework/odd-extractor/` — partition rule overrides this to `plugins/dev-sdlc/odd-extractor/`.** |
| Subagent personas | FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md:189`) + scheduled v0.1.4 item. Five named personas (`loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter`). | Not yet authored. **All five are dev-specific** → `plugins/dev-sdlc/agents/<name>.md` per partition rule (NOT `.claude/agents/`-shared). |
| Per-project PM persona | FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md:25`). Per-project scoped; conversational coordinator above specialists. | Not yet authored. **PM-shape is harness-general** → `framework/per-project-pm/`. Dev-projects' PMs may then register dev-sdlc skills/subagents. |
| ODD §2.5 conformance verification | Manual (`docs/design/odd.md:174-182`); ODD-conformance sweep deferred (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:153`). | Eric needs automated verification, not manual. Composes with PR-safety gates. |
| Cost governance | Component sealed; calibrated for Luke's loam-of-loam workload. | Eric's reverse-engineering pass on a foreign SaaS may dwarf existing budget envelopes. Recalibration needed. |
| Memory backend abstraction | `MemoryProvider` Protocol stub at v0.1.0; widening at v0.1.5 (D-3/D-1/D-2). | Eric's per-project-PM context needs persistent memory keyed to his SaaS; protocol must support multiple workspace-scoped instances. Likely fine post-v0.1.5; needs validation. |

### 2.3 — Missing entirely

| Capability | Source / motivation |
|---|---|
| **PR-safety gate (contract-conformance enforcement at PR-time)** | New for Eric; nothing in current loam blocks merges against a derived contract. |
| **Production-safety mode (defaults shifted toward halt-and-surface for non-trivial blast-radius)** | New for Eric; current defaults assume Luke's tolerance for loam-of-loam autonomy. |
| **Confidence-banded contract authoring (every derived AC carries a confidence band: verified / plausible / hypothesised)** | Implied by F1/F2 risk; not in current ODD methodology. Composes with §3 ODD-RE recommendations. |
| **Foreign-language scaffold (loam tooling currently Python-first)** | Eric's app may be Ruby / TypeScript / Go / mixed. |
| **Continuous codebase-watch (codebase evolves; contract must evolve with it)** | New for Eric; one-shot RE is insufficient over the lifetime of the partnership. |
| **PM-driven decision surfacing (translate "10 background dispatches in flight" into "1 question for Eric")** | Composes with per-project PM persona but is its own discipline. |
| **Provenance-traceable PRs (every PR description carries: directive → contract surface → ACs touched → tests added → reviewer notes)** | Audit-trail requirement (`F6` failure mode). |

### 2.4 — Loam capabilities that Eric does NOT need

Important to flag because over-shipping is its own risk. These don't ladder up to Eric's use case and should NOT bundle into Eric's release path:

- Multi-LLM orchestration via OpenRouter (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:29`) — Eric uses Claude; cost-savings via DeepSeek not load-bearing for production-safety stakes.
- Anthropic Memory tool adapter (D-2 in v0.1.5) — Eric uses Claude Code, not raw Claude API.
- HeavySwarm 4-role pattern (FIDRAFT entry) — load-bearing for high-uncertainty research; Eric's work is execution against a derived contract.
- LLMCouncil + SequentialWorkflow drift_detection (FIDRAFT entries) — v0.2.x swarm-runtime niceties; not first-cut.
- PyPI publish gate (FIDRAFT entry) — release ceremony unrelated to Eric's install path; Eric installs from source.

---

## §3 — Capability gaps: what loam needs to ship for Eric

For each missing or partial capability: what loam needs, what it ladders to, AI-time band, dependencies, **placement** per the partition rule.

### G1 — Heavy ODD reverse-engineering capability (`plugins/dev-sdlc/odd-extractor/`)

**What it is.** A tool that reads a foreign codebase (its source, tests, docs, runtime behaviour where probeable) and emits a draft contract: top-level business objectives + sub-objectives + ACs, each tagged with a confidence band (verified-from-test / plausible-from-code / hypothesised) and a provenance trail (file + line + reasoning).

**Ladders to.** SC1 (Eric describes change → loam works against contract); F1/F2 (hallucinated and missed contract); §1.3 outputs item 1.

**AI-time band.** 16–32 hours. Decomposition (research-grade, then build-cycle): research artefact already exists at 907 lines (`workspace/.scratch/claude-output/odd-reverse-engineering-skill-research.md`) per FIDRAFT entry `FUTURE_IDEAS_DRAFT.md:175`; eight D-Q.RE.* sub-decisions captured. Build = Cartographer-style slice-and-swarm + four-stage init/analyze/generate/verify workflow. Largest single-component build of the Eric-deliverable path.

**Dependencies.** Lens 5 swarming runtime helpful but not required (V2.C in v0.2.x); first-cut uses background-agent dispatches per current pattern. M-FBM operational-health (#125, sealed) is the cross-session memory substrate the extractor's per-codebase state lives in.

**Placement.** **`plugins/dev-sdlc/odd-extractor/`** — dev-specific (only useful for working on codebases as a developer). Earlier FIDRAFT entries said `framework/odd-extractor/`; the partition rule overrides. The extractor's *output* (the contract document) lives in Eric's SaaS-app repo, not in loam.

**Risk.** Highest-risk single component for Eric. Hallucinated ACs + missed ACs both cost real money. Mitigation in §4.

### G2 — PR-safety gate plugin (`plugins/dev-sdlc/pr-safety/`)

**What it is.** A pre-commit / pre-push / PR-bot mechanism that, for every change-set, (a) parses the diff, (b) maps changed code to derived contract surfaces (via the extractor's provenance map), (c) runs the AC tests for any touched surface, (d) verifies no AC regression, (e) flags new code paths that don't ladder to a contract surface (ODD §2.5 violations), (f) emits a structured PR-comment / status-check.

**Ladders to.** SC2, SC3, F1, F2, F6.

**AI-time band.** 8–16 hours. Smaller than G1; G2 reuses extractor's provenance map.

**Dependencies.** G1 must ship first (no contract surface to gate against otherwise). Composes with the existing PR review skill (`plugins/dev-sdlc/skills/start-project.md`-adjacent) and with the `review` slash-command pattern.

**Placement.** **`plugins/dev-sdlc/pr-safety/`** — dev-specific. The gate runs in CI / pre-commit hooks of Eric's repo, but the *gate definition* lives in loam.

**Risk.** False-positive risk (F3) — over-cautious blocking erodes Eric's trust. Mitigation: G2 ships with explicit override workflow (Eric flags "this is a deliberate contract update; here's the new AC; merge").

### G3 — Production-safety mode (harness-level)

**What it is.** A workspace-level configuration field — `safety_profile: production-stake | dev | research` — that flips loam's defaults: blast-radius Band C surfaces by default; Band D hard-halts; Band E hard-refuses; cost-governance ceilings tighten; halt-and-surface fluency in every dispatched subagent.

**Ladders to.** SC3, F3, F5, F7.

**AI-time band.** 4–8 hours. The mechanism is small (config field + a few branch-points); the work is in identifying every default that needs flipping.

**Dependencies.** None — can ship before G1/G2 as a defensive shield. Composes with cost-governance recalibration (G7).

**Placement.** **`framework/`** — `safety_profile` is a harness-general capability (any user with high-stakes work benefits). The dev-specific *defaults applied when this profile activates* may live in `plugins/dev-sdlc/` (e.g., "in production-stake mode, the loam-builder subagent halts on every `git push` to non-feature branches").

**Risk.** Mis-calibration. Surface as named tunables; ship with conservative defaults; iterate.

### G4 — Subagent personas (`plugins/dev-sdlc/agents/`)

**What it is.** Per the FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md:189`) and the v0.1.4 roadmap §2 item 1: five named subagents (`loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter`). Each carries methodology fluency baked in; dispatches stay scope-only because the priming lives in the persona file, not in every dispatch prompt.

**Ladders to.** SC1, SC4, F3 mitigation (subagent fluency reduces persona-side coordination tokens, freeing context for Eric-translation).

**AI-time band.** 4–8 hours for five personas. Already sized in v0.1.4.

**Dependencies.** None for first-cut. Composes with G3 (production-safety mode flips subagent defaults toward halt-and-surface).

**Placement.** **`plugins/dev-sdlc/agents/`** — these are dev-specific personas. Eric's foreign-codebase work is dev work; the personas are dev-fluent. **Note: this contradicts the v0.1.4 roadmap's implicit `.claude/agents/` placement.** The partition rule says: subagent personas-dispatched-from-loam land in dev-sdlc; if Eric's project (or any user's project) wants Claude-Code-discovered subagents, those are a separate concern.

**Tension worth surfacing.** Claude Code's native subagent mechanism reads from `~/.claude/agents/<name>.md` and `<project>/.claude/agents/<name>.md`. Per Lens 1 (Claude-leverage-first), the right shape is to compose with Claude's native discovery — which means the *registration* needs to symlink-or-copy from `plugins/dev-sdlc/agents/` to `.claude/agents/` at workspace-bootstrap time. Captured as a sub-decision in §10.

### G5 — Per-project PM persona (`framework/per-project-pm/`)

**What it is.** Per the FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md:25`): per-project scoped persona that absorbs project-specific coordination state. Eric's loam workspace has a "Eric's-SaaS-app PM" that holds: the derived contract, Eric's preferences, the in-flight change list, the audit trail of past changes. The primary persona stays project-agnostic (translation across all projects); the PM is the project-domain memory.

**Ladders to.** SC4 (Eric < 30 min/day), SC1 (one persona Eric talks to is the conversational layer that *delegates to* the PM).

**AI-time band.** 8–16 hours. New persona shape; needs design-doc + contract + test surface.

**Dependencies.** Subagent personas (G4) help — the PM dispatches subagents to do build / review / research. Per-project file-based memory composes with M-FBM's workspace-state pattern (per FIDRAFT, `FUTURE_IDEAS_DRAFT.md:25`).

**Placement.** **`framework/per-project-pm/`** — PM-shape is harness-general; not dev-specific. Eric's PM happens to manage a dev project; a hypothetical writer's PM would manage a writing project; both use the same PM machinery. Per-project PMs can register dev-sdlc skills if their project is a dev project (the FIDRAFT entry suggests this).

**Risk.** New shape; worth research-grade plan-doc before build (`feedback_research_before_plan`).

### G6 — Confidence-banded contract authoring (extension to ODD methodology)

**What it is.** Every AC the extractor produces carries one of three confidence bands:

- **VERIFIED** — pinned by an existing test in the SaaS-app's repo. Loam can quote the test.
- **PLAUSIBLE** — derivable from code-shape (e.g., a Pydantic validator enforces this; the function's name + invariants strongly imply this) but no test pins it. Loam can cite the code; Eric verifies.
- **HYPOTHESISED** — derivable only from runtime behaviour, log patterns, naming, or external docs. Loam cannot independently verify; Eric must.

ACs cannot be promoted to VERIFIED without a test. Eric ratifies every PLAUSIBLE → VERIFIED promotion. HYPOTHESISED ACs cannot gate PRs (only inform).

**Ladders to.** F1 (hallucinated contract — HYPOTHESISED can't gate; PLAUSIBLE requires Eric ratification; only VERIFIED enforces); F2 (missed contract — bands surface what's *not* known so Eric can spot omissions in his domain).

**AI-time band.** 4–8 hours. Lives mostly in the extractor (G1) but is its own design discipline.

**Dependencies.** ODD methodology extension (`plugins/dev-sdlc/docs/odd-methodology.md`). G1 implements; G6 is the discipline.

**Placement.** **`plugins/dev-sdlc/docs/odd-methodology.md`** + extractor implementation in `plugins/dev-sdlc/odd-extractor/`. Pure dev-tooling.

**Risk.** Discipline drift. Mitigation: structural — confidence-band is a required field in the AC schema; missing band fails extractor self-check.

### G7 — Cost-governance recalibration for foreign-codebase pass

**What it is.** Recalibrate cost ceilings for the reverse-engineering pass. A 100K-LOC SaaS with no docs may chew through $50–500 of LLM tokens on first pass; loam's current default budgets were calibrated against loam's own ~50K-LOC codebase plus dispatches' typical scope.

**Ladders to.** F7.

**AI-time band.** 2–4 hours. Mostly calibration + budget defaults + observability; small.

**Dependencies.** Existing cost-governance component. Composes with `framework/cost-governance/`. Existing FIDRAFT entry on Opus 4.7 tokenizer-inflation calibration sweep (`FUTURE_IDEAS_DRAFT.md:137`) is partial precedent.

**Placement.** **`framework/cost-governance/`** (recalibration of existing component) + **`plugins/dev-sdlc/odd-extractor/`** (extractor-specific budget knobs). Mixed but the lion's share is harness-general.

**Risk.** Under-calibration; first real run on Eric's codebase blows budget and stops mid-pass. Mitigation: dry-run mode (per FIDRAFT V11.C D-Q.RE.4 "explicit token-budget knob with cheap dry-run").

### G8 — Provenance-traceable PR descriptions

**What it is.** PR description template that includes: (a) the natural-language Eric directive that triggered this change, (b) the contract surface(s) the change ladders to, (c) the ACs touched (verified / new / extended), (d) the tests added or modified, (e) confidence-band changes (any HYPOTHESISED → PLAUSIBLE → VERIFIED moves), (f) gate-pass record from G2.

**Ladders to.** SC5 (Eric's team accepts loam PRs at the human-PR rate), F6 (audit-trail loss).

**AI-time band.** 2–4 hours. Template + integration into PR-creation flow. Smallest gap.

**Dependencies.** G1 (contract), G2 (gate), G6 (confidence bands).

**Placement.** **`plugins/dev-sdlc/pr-safety/`** (the template + the integration) **OR** a thin SKILL package in `plugins/loam-skills/skills/provenance-pr-description/` for raw-Claude-Code use too. Recommendation: ship in dev-sdlc first, optionally lift to loam-skills if non-dev users want similar audit-trail discipline (unlikely in v0.1.x).

**Risk.** Low. Template is the easy part; integration into Eric's real repo is the work.

### G9 — Foreign-language scaffold (extractor language-agnostic skeleton)

**What it is.** Per FIDRAFT V11.C entry (`FUTURE_IDEAS_DRAFT.md:175`) D-Q.RE.2: language-agnostic skeleton + Python first-class extractor. Other languages (Ruby / TypeScript / Go) work on a code-grep + LLM-reasoning fallback path; Python gets full AST-aware parsing. Extractor must announce its capability per language so Eric knows when he's getting first-class vs fallback analysis.

**Ladders to.** F4. Avoids Python-only-tool excluding Eric's actual SaaS if it's Ruby / TS / Node.

**AI-time band.** 4–8 hours. Inside G1's scope but worth surfacing as a distinct discipline.

**Dependencies.** Inside G1.

**Placement.** **`plugins/dev-sdlc/odd-extractor/`**. Dev-specific.

**Risk.** Eric's SaaS is in a language with poor LLM coverage (e.g., COBOL, mainframe BASIC). Mitigation: declare-and-halt up-front; G3 production-safety mode forbids LOW-confidence-language proceeding.

### G10 — Continuous codebase-watch (post-onboarding maintenance)

**What it is.** Eric's SaaS evolves; the contract must evolve with it. A scheduled pass — daily / weekly — that diffs Eric's repo since last scan, detects code paths that touch existing contract surfaces (potentially invalidating ACs) or that look like new contract surfaces (candidate ACs to surface for Eric ratification).

**Ladders to.** Long-term Eric usability — without this, the contract goes stale.

**AI-time band.** 4–8 hours. Composes with G1 + scheduling primitive (loam already has scheduled-scope; not exercised post-v0.1.0 in this shape).

**Dependencies.** G1 (extractor), G3 (production-safety mode controls how aggressively the watch acts), the existing scheduled-scope primitive.

**Placement.** **`plugins/dev-sdlc/odd-extractor/`** (the watch is the extractor's incremental mode) + **`framework/`** (scheduled-scope is the harness primitive).

**Risk.** Drift. The contract diverges from the code over time. Mitigation: this gap-filler IS the mitigation.

### G11 — Decision-surfacing PM discipline (translate dispatch-status into Eric-questions)

**What it is.** Per the value-prop audit (`docs/rebuild/plans/value-prop-vs-actual-shape-audit-2026-05-04.md` §3.3 + §5 Option 5): the PM persona's job is to take the orchestration ceremony — N agents in flight, M decisions queued, K ratifications awaiting — and emit ONE Eric-question per decision-point in his preferred channel. Status-stream is the failure mode this prevents.

**Ladders to.** SC4 (< 30 min/day).

**AI-time band.** 4–6 hours. Discipline + design-note + PM-persona prompt content.

**Dependencies.** G5 (PM persona), G4 (subagents), the bidirectional-translation rule (`feedback_translate_outbound_too` per FIDRAFT `FUTURE_IDEAS_DRAFT.md:25`).

**Placement.** **`framework/per-project-pm/`** (the PM owns this discipline). PM is harness-general.

**Risk.** Discipline drift. Mitigation: design-note + observable test (subagent dispatches that bypass the PM are violations).

---

## §4 — ODD reverse-engineering at SaaS-app scale

This section is load-bearing because G1 + G6 + G9 + G10 together are the largest delivery the Eric path requires. Treating it as a single discipline rather than four siloed components.

### 4.1 — Sufficiency of the current FIDRAFT entry

The current FIDRAFT entry (`FUTURE_IDEAS_DRAFT.md:175`) describes V11.C heavy version: `framework/odd-extractor/` (NOW `plugins/dev-sdlc/odd-extractor/` per partition rule) + Cartographer-style slice-and-swarm + four-stage init/analyze/generate/verify workflow + eight D-Q.RE.* sub-decisions. Research artefact at `workspace/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines).

**Sufficient for SaaS-app scale?** **Partial.** The research targets *codebase analysis*. It does not yet address:

- **Confidence-banding** (G6) at the per-AC level. Research mentions ODD §2.5-violation-surface for coverage gaps but not the confidence-band schema.
- **Continuous incremental mode** (G10). One-shot extraction was the research scope.
- **Production-safety mode integration** (G3). Research authored before production-safety mode existed as a concept.
- **Eric-ratification workflow.** Research mentions output formats (markdown + YAML) but not the human-in-the-loop ratification cycle.
- **Test-as-AC-source priority.** Research treats tests as one input source among many; for Eric's stakes, tests should be FIRST-class — every existing test maps to an AC at VERIFIED confidence; non-test sources only fill gaps.

**Recommendation.** Re-open V11.C plan-author scope when activated to add:

1. Confidence-band schema (G6).
2. Test-first extraction priority (every test → AC; code-only → PLAUSIBLE; runtime/docs → HYPOTHESISED).
3. Ratification-cycle workflow (Eric reviews PLAUSIBLE; ratifies promotion to VERIFIED only after a pinning test exists).
4. Incremental mode for G10.
5. Integration with G3 production-safety profile (refuses to surface AC for ratification at high-cost-without-band-justification).

### 4.2 — Production-safety constraint on the extractor

Eric's SaaS handles real money. The extractor's failure modes (F1 — hallucinated contract, F2 — missed contract) directly translate into PR-gate failures. Mitigations:

**M-1 (extractor-side).** **Test-first priority.** Every existing test in Eric's repo produces a VERIFIED AC by direct extraction (test name + assertion → AC text + AC test). The extractor reads tests before reading source.

**M-2 (extractor-side).** **No silent inference.** If the extractor would emit an AC but cannot cite its source (test / code-shape / runtime / doc), it does NOT emit. Halt-and-surface the gap to Eric instead.

**M-3 (extractor-side).** **Confidence-banded by default.** No AC ships without a confidence band. Schema-level enforcement.

**M-4 (gate-side).** **Only VERIFIED ACs gate PRs.** PLAUSIBLE ACs surface as informational PR comments; HYPOTHESISED ACs are even softer. Eric controls promotion.

**M-5 (workflow-side).** **First pass is read-only.** First reverse-engineering pass produces a contract draft; ZERO source edits, ZERO PRs opened. Eric reviews the draft for a defined window before any code-change work begins.

**M-6 (cost-side).** **Dry-run before live-run.** Per D-Q.RE.4, the extractor estimates tokens-needed and surfaces the estimate before running. Eric (or Luke as installer) approves the budget.

### 4.3 — Maintenance over time

Eric's SaaS evolves. Without continuous-watch (G10):

- Six weeks post-onboarding, code touches contract surfaces; PRs that violate the *current* (stale) contract get gated incorrectly (F3).
- Six months in, the contract is decorative; nobody trusts the gate.

**Recommendation.** G10 is not optional for Eric. Sequenced into the version path; cannot defer indefinitely.

### 4.4 — Calibration: every derived AC needs a band

Already covered (G6); calling out here so the §4 reader doesn't miss it. The single biggest distinction between V11.C-as-currently-imagined and V11.C-as-Eric-needs-it is the confidence-band schema. **Every AC** carries a band, **every band has a structural enforcement** (schema-level required field), **every band-promotion is auditable** (Eric's ratification is committed to the contract repo).

---

## §5 — PR-safety gates

Detailed treatment of G2 because the architectural choice (mechanism + coverage + override + failure mode) shapes the version path.

### 5.1 — Mechanism

**Three layers, each cheaper than the next failure-class catches:**

- **Layer 1 — pre-commit hook in Eric's repo.** Before `git commit`, the hook runs the AC tests for any touched contract surface + the ODD §2.5 reverse-direction check (every code path maps to an AC). Local feedback in seconds. Fails fast on branch-local violations.
- **Layer 2 — pre-push hook in Eric's repo.** Before `git push`, expanded check: full AC suite + extractor's diff-against-contract pass. Catches things the per-touched-surface check missed.
- **Layer 3 — PR-bot / CI status check.** Once the PR is on the remote, a CI job re-runs Layer 2 in a clean environment; emits a structured status check that Eric's team's review tooling reads.

Layer 3 is required (CI is the source of truth); Layers 1+2 are speed-ups so Eric isn't waiting on CI for every iteration.

**Placement.** All three live in `plugins/dev-sdlc/pr-safety/`. The hooks install into Eric's repo via a one-time setup; the CI integration is YAML+script.

### 5.2 — Coverage

Direct AC violations are obvious. The harder cases:

- **Performance regression.** AC pinned "P95 latency < 500ms"; PR makes it 600ms. Coverage gap unless the AC test runs under load. Requires production-like fixture; expensive. Recommendation: the gate flags PRs touching code that has perf-pinned ACs, surfaces "perf-test required for this PR." Eric runs locally or in staging.
- **Contract changes in shared code.** PR touches a shared utility used by 12 contract surfaces. Direct test for the touching surface passes; one of the OTHER 12 fails because the utility's behaviour changed for it. Coverage requires running the *transitive* AC suite. Cost-bounded; default = full suite.
- **New code path with no AC.** ODD §2.5 reverse direction — every diff line has an AC. New code → either find an AC it ladders to, or surface as a candidate-AC for ratification (re-extension pattern, `docs/design/odd.md:188-204`).

### 5.3 — Override workflow

Sometimes Eric *wants* to update the contract. Workflow:

1. PR opens with both source change + contract update.
2. Gate detects the contract update; reads its provenance (which AC is being modified, what's the new shape).
3. Gate runs the new AC against the new code; both must pass.
4. Gate records the override as a separate audit-trail row: "AC.X.Y modified at <commit>; <Eric ratification commit>; new pinning test at <test path>."
5. PR-comment shows the diff against the contract for human reviewers.

The override MUST require Eric ratification (not loam-autonomous). Production-safety profile (G3) enforces this structurally.

### 5.4 — Failure modes

**False positive (F3).** Gate blocks a benign PR. Mitigation: per-AC override workflow per §5.3; AC-precision-sweep at v0.2.x to retire over-tight ACs. This is *the* risk that makes Eric stop using loam.

**False negative (F1/F2 reaching production).** Gate passes a regression. Mitigation: production-safety mode keeps the merge-decision in Eric's hands (gate is advisory, not autonomous-merge); test coverage discipline; periodic audit of merged-since-last-audit changes.

---

## §6 — Minimal-input usage shape

Eric should not micro-manage. The persona drives.

### 6.1 — Per-project PM persona shape (G5)

Per FIDRAFT, `FUTURE_IDEAS_DRAFT.md:25`: per-project scoped PM. Eric's loam workspace has *one* PM dedicated to his SaaS — call it "eric-saas-pm." It holds:

- The derived contract (delegated to G1's extractor; PM is the consumer).
- The audit trail of past changes (from G8 PR descriptions + workspace memory).
- Eric's preferences (channel, decision threshold, blast-radius tolerance).
- The in-flight change list (subagents dispatched, awaiting ratification, etc.).

The primary persona (who Eric talks to in chat) translates Eric's natural-language directive and routes it to the PM. The PM coordinates subagents and emits decisions back through the primary persona to Eric.

**Placement (re-stated).** **`framework/per-project-pm/`** for the PM-shape itself. The Eric-specific PM lives in Eric's loam workspace's `.loam/pms/eric-saas-pm/` directory (per the FIDRAFT entry's "lives in the project's workspace state directory" provision).

### 6.2 — Onboarding ritual

Eric's first session — the install + first-pass — needs a tight ritual. Estimated steps:

1. Eric installs loam from source per current docs.
2. Eric runs `loam init eric-saas-app` (workspace bootstrap) targeting his SaaS repo.
3. Loam prompts: "What's the safety profile? [production-stake / dev / research] (default production-stake)" — Eric confirms production-stake (G3).
4. Loam prompts: "Run reverse-engineering pass? Estimated AI-time 4–12 hours; estimated cost $20–200; live or dry-run?" Eric chooses (G7 cost-governance + G1 dry-run).
5. (If live) loam runs the pass. PM persona surfaces progress at decision-point intervals (not status-stream).
6. Pass produces the draft contract. Loam prompts Eric to schedule a review window.
7. Eric reviews the draft over a defined window (hours-to-days). Ratifies / amends / rejects ACs surface-by-surface.
8. After ratification, loam is ready for change-work. Eric submits his first directive.

**Autonomous in this ritual:** workspace bootstrap, extractor execution, dry-run cost estimate, contract draft generation, PM persona seeding, channel setup, subagent registration.

**Eric-input in this ritual:** safety profile choice, dry-vs-live ruling, AC ratification, channel preference. ~30 minutes total Eric-time across the install (ratification window is deliberately stretched).

### 6.3 — Decision surfacing

What loam decides autonomously:

- Sub-plan structure (per ODD methodology).
- Subagent dispatch (which subagent for which sub-task; per G4).
- Test-fixture authoring (PM ensures fixtures match contract; loam-builder authors).
- Branch naming, PR titles.
- Internal coordination (status of in-flight subagents).

What Eric must rule on:

- Safety profile (set once, revisit on demand).
- AC ratification (initial pass + every gap-driven re-extension).
- PR-merge approval (loam-merging-autonomously is not in v0.1.x; explicit Eric-approval required per G3).
- Override workflow invocation (when the contract is being deliberately updated).
- Production-touching actions (Band E hard-refused; Eric does these manually).
- Cost-budget overrides if dry-run estimate exceeds default ceiling.

### 6.4 — Communication shape

Per `docs/design/primary-persona-shape.md` and `~/.claude/CLAUDE.md` channel rules: **one voice**. The primary persona narrates outcomes; subagents + PM are invisible at user-surface (per the value-prop audit's T3 resolution, `value-prop-vs-actual-shape-audit-2026-05-04.md` §4).

**Channel.** Telegram for Luke; Eric's preference is TBD (could be Slack via a future Slack MCP, email via the email MCP, or terminal-only). Channel-abstraction lives in `framework/`; Eric-specific channel choice is workspace-config.

**Cadence.** Decision-driven, not status-driven. Eric hears from loam when:

- A decision needs Eric's input.
- A milestone closes (extractor first-pass done; PR merged; etc.).
- An anomaly surfaces (unexpected gate failure, runaway cost, environmental issue).

Eric does NOT hear from loam:
- Every dispatch starting / ending.
- Every commit landing.
- Every test passing.
- Routine progress noise.

---

## §7 — Production-safety constraints

Eric's stakes force discipline shifts. Each is a deliberate departure from current loam-of-loam defaults.

### 7.1 — Default to halt-and-surface

In current loam (loam-of-loam): autonomy is high; halt-and-surface fires on ODD violations + named scope breaches. In Eric-mode: halt-and-surface fires on (i) all the above, plus (ii) Band C+ blast-radius decisions, (iii) ANY contract-surface modification, (iv) ANY production-touching consideration. Threshold flips.

### 7.2 — Test-coverage requirements

Operational-health AC family (per `plugins/dev-sdlc/docs/smoke-test-discipline.md` 6-dimension spec) is **required**, not optional, for every contract surface. The extractor's test-first priority (M-1 above) is the inverse: every test → AC. Together they form a closed loop — every contract surface is test-pinned, every test pins a surface.

For surfaces that have no existing test (PLAUSIBLE / HYPOTHESISED ACs), Eric ratification creates the AC; the next change-work-cycle that touches that surface authors the pinning test as part of the change-set. This is the re-extension pattern (`docs/design/odd.md:188-204`) applied at production scale.

### 7.3 — Reversibility

Every loam-driven change is git-reversible (revert the commit, push). For changes that are git-reversible-but-data-irreversible (DB migration; external-side-effect call), loam refuses to author them; Eric does manually. Captured in Band E (§1.6). This is more conservative than current loam's reversibility classes but appropriate for the stakes.

### 7.4 — Audit trail

Every loam-driven change carries:

- Provenance (G8): directive → contract surface → ACs touched → tests added → reviewer notes → gate-pass record.
- Workspace-memory entry (M-FBM): per-turn markdown layout (per current pattern) capturing the directive, the persona's reasoning, the dispatched subagents.
- Contract-repo audit row (Eric's SaaS repo): every contract change committed with a reference to the loam workspace's audit trail.

Three sources, cross-referenced. Post-incident triage: Eric (or his team) can answer "why did this PR happen?" by reading any of the three.

---

## §8 — Recommended version sequence

Six new releases beyond the current v0.1.x roadmap. Re-using v-numbers post-v0.1.5 (which is currently the last roadmapped release). Total AI-time band: **40–80 hours**, midpoint **~55 hours**. Total Luke + Eric review time: **6–12 hours** distributed across ~15 review touchpoints.

| Release | Theme | What ships | AI-time | Eric closes Eric-gap |
|---|---|---|---|---|
| **v0.1.6** | Production-safety mode | G3 + G7 | 6–10 h | Defensive shield ahead of extractor work |
| **v0.1.7** | Subagent personas + PM persona | G4 + G5 + G11 | 16–24 h | Coordination machinery off persona's surface |
| **v0.1.8** | ODD reverse-engineering (heavy) | G1 + G6 + G9 | 24–40 h | Contract derivation possible |
| **v0.1.9** | PR-safety gate | G2 + G8 | 10–18 h | Contract enforcement at PR-time |
| **v0.2.0** | Continuous codebase-watch | G10 | 6–10 h | Contract evolves with codebase |
| **v0.2.1** | Eric-deliverable smoke + onboarding hardening | Onboarding ritual sealed; full documentation; live smoke against a real foreign repo | 8–14 h | Eric installs, runs end-to-end |

(v0.2.2 named in §10 Decision E but not separately scheduled here — it's the bandwidth-buffer version for known surfaces that will surface during v0.1.6–v0.2.1 work; not a feature-bearing release.)

### v0.1.6 — Production-safety mode

**Theme.** Ship the safety shield before Eric-shaped work touches anything. Production-stake users must have a profile flag and ceiling adjustments before extractor or PR-gate work goes live, even in canonical pos-v2 testing.

**What ships.**

- G3: `safety_profile: production-stake | dev | research` workspace-config field.
- G7: cost-governance recalibration with foreign-codebase budget envelope + dry-run mode.

**Placement audit.**

- G3 mechanism (`safety_profile` config + framework defaults flipping) → **`framework/`**. Harness-general.
- G3 dev-specific defaults applied when profile is production-stake (e.g., subagent halt-and-surface on push) → **`plugins/dev-sdlc/`**. Dev-specific.
- G7 budget envelopes → **`framework/cost-governance/`**. Harness-general (cost-governance is a framework component already).
- G7 extractor-specific knobs → deferred to v0.1.8 with G1.

**Enables for Eric.** Defensive shield in place before more dangerous capabilities ship. Allows v0.1.6 testing in canonical with production-stake mode active.

**Dependencies.** None (can ship before all other Eric-path versions).

**Risk + mitigation.** Mis-calibration. Mitigation: ship with conservative defaults; observable tests; iterate based on canonical behaviour before Eric installs.

**Gate to v0.1.7.** Production-stake profile observable in canonical pos-v2 sessions; cost-governance dry-run mode functional; profile-flip decisions documented.

### v0.1.7 — Subagent personas + PM persona + decision surfacing

**Theme.** Coordination machinery off the persona's user-visible surface. Per the value-prop audit (`value-prop-vs-actual-shape-audit-2026-05-04.md`) Option 5 — sharpened for Eric's stakes.

**What ships.**

- G4: 5 subagent personas (`loam-builder`, `loam-plan-author`, `loam-researcher`, `loam-reviewer`, `loam-documenter`) — per FIDRAFT `FUTURE_IDEAS_DRAFT.md:189`.
- G5: per-project PM persona (`framework/per-project-pm/`) — per FIDRAFT `FUTURE_IDEAS_DRAFT.md:25`.
- G11: decision-surfacing PM discipline.

**Placement audit.**

- G4 subagent persona definitions → **`plugins/dev-sdlc/agents/`**. Dev-specific personas. (Tension surfaced in §3 G4: registration into Claude-native `.claude/agents/` happens at workspace-bootstrap; the SOURCE files live in dev-sdlc.)
- G5 PM-shape (loader, contract, registry) → **`framework/per-project-pm/`**. Harness-general.
- G5 Eric-specific PM-instance lives in Eric's loam workspace at `.loam/pms/eric-saas-pm/` (workspace-state, not framework).
- G11 PM-discipline design-note + persona prompt content → **`framework/per-project-pm/`**.

**Enables for Eric.** PM absorbs project state; subagents do the work; primary persona stays translator-shaped. Eric talks to one voice that handles the orchestration internally.

**Dependencies.** G3 production-safety mode (v0.1.6) — subagent personas check the profile and adjust their halt-and-surface defaults accordingly.

**Risk + mitigation.** PM-persona is a new shape. Mitigation: research-grade plan-doc before build (`feedback_research_before_plan` CDC); design-note articulating the PM↔persona protocol; test surface for the boundary.

**Gate to v0.1.8.** Subagent personas dispatchable; PM persona seedable in a workspace; primary persona's user-facing channel volume returns to translation-shape per the value-prop audit's success criterion.

### v0.1.8 — ODD reverse-engineering (heavy)

**Theme.** The headline capability. `plugins/dev-sdlc/odd-extractor/` ships full Cartographer-style extractor with confidence-banding + test-first priority + language-agnostic skeleton.

**What ships.**

- G1: `plugins/dev-sdlc/odd-extractor/` heavy version.
- G6: confidence-banded contract authoring (extension to ODD methodology).
- G9: language-agnostic skeleton (Python first-class; Ruby/TS/Node fallback path).

**Placement audit.**

- G1 extractor → **`plugins/dev-sdlc/odd-extractor/`**. Dev-specific. **Correction from earlier FIDRAFT entry's `framework/odd-extractor/` placement.**
- G6 ODD-methodology extension → **`plugins/dev-sdlc/docs/odd-methodology.md`** (extension; existing doc lives in dev-sdlc).
- G6 confidence-band schema → **`plugins/dev-sdlc/odd-extractor/`**.
- G9 language adapters → **`plugins/dev-sdlc/odd-extractor/lang/`**.

**Enables for Eric.** Loam can read his SaaS and produce a draft contract.

**Dependencies.** G3 (production-safety mode), G4 (subagents — extractor uses them for slice-and-swarm), G5 (PM coordinates the extraction), G7 (cost-governance dry-run), M-FBM (cross-session memory for the per-codebase state), Lens 5 swarming patterns (text-corpus only; runtime is v0.2.x).

**Risk + mitigation.** Highest risk in the path. Hallucinated ACs (F1) directly cost Eric's company money. Mitigation:

- M-1 test-first priority (every test → VERIFIED AC; can't skip).
- M-2 no silent inference.
- M-3 confidence-banded by default (schema-enforced).
- M-5 first pass is read-only.
- M-6 dry-run before live-run.
- Smoke-test 6-dimension spec applied to the extractor itself per `plugins/dev-sdlc/docs/smoke-test-discipline.md` (build before live use).
- Live smoke against an open-source SaaS-shape repo (e.g., a flask-payment-app demo) before Eric points loam at his real codebase.

**Gate to v0.1.9.** Extractor produces a confidence-banded contract draft against a smoke-test fixture repo; dry-run cost estimate observable; Eric-ratification workflow runs end-to-end on the fixture.

### v0.1.9 — PR-safety gate

**Theme.** Contract enforcement at PR-time. Without the gate, the contract is decoration.

**What ships.**

- G2: `plugins/dev-sdlc/pr-safety/` — pre-commit hook + pre-push hook + CI status check.
- G8: provenance-traceable PR description template.

**Placement audit.**

- G2 gate definitions → **`plugins/dev-sdlc/pr-safety/`**. Dev-specific.
- G2 hook installers (the bit that sets up `.git/hooks/` in Eric's repo) → **`plugins/dev-sdlc/pr-safety/`**.
- G2 CI integration YAML/script templates → **`plugins/dev-sdlc/pr-safety/templates/ci/`**.
- G8 PR-description template → **`plugins/dev-sdlc/pr-safety/templates/pr/`**.

**Enables for Eric.** Every PR is gated; provenance trail is automatic; merges only happen with Eric ratification.

**Dependencies.** G1 (extractor) ships first — gate has no contract surface to check against otherwise.

**Risk + mitigation.** False positives (F3) erode trust. Mitigation:

- Override workflow per §5.3; well-documented.
- AC-precision-sweep follow-on (deferred-but-named) once Eric's first month of usage data informs which ACs are over-tight.
- Per-band gating (only VERIFIED gates; PLAUSIBLE informs; HYPOTHESISED is documentation-only).

**Gate to v0.2.0.** Gate runs in canonical against a smoke-test fixture; produces structured PR comments; override workflow tested; production-safety mode integration verified.

### v0.2.0 — Continuous codebase-watch

**Theme.** Contract stays alive as Eric's SaaS evolves.

**What ships.**

- G10: scheduled/incremental extractor mode in `plugins/dev-sdlc/odd-extractor/`.
- Composes with the existing scheduled-scope primitive (`framework/scope-of-work/` — sealed component).

**Placement audit.**

- G10 watch logic → **`plugins/dev-sdlc/odd-extractor/`** (incremental mode is part of the extractor).
- G10 scheduling → **`framework/scope-of-work/`** (already-existing harness primitive; reused).
- G10 PM-side decision-surfacing for newly-detected ACs → **`framework/per-project-pm/`** (PM owns the ratification queue).

**Enables for Eric.** Six-month-out: contract stays in sync with code; new ACs surface for ratification at sane cadence; stale ACs flagged for retirement.

**Dependencies.** G1 (extractor full), G5 (PM ratification queue), G3 (safety mode controls watch aggressiveness).

**Risk + mitigation.** Watch noise (PM surfaces too many AC candidates; Eric tunes out). Mitigation: confidence-band threshold for surfacing (only high-confidence candidates surface; low-confidence accumulate for batch review); Eric-tunable cadence (daily / weekly / on-PR).

**Gate to v0.2.1.** Watch runs in canonical against a fixture; surfaces newly-introduced contract-shape changes; PM queue observable; Eric-ratification batch workflow tested.

### v0.2.1 — Eric-deliverable smoke + onboarding hardening

**Theme.** The release Eric installs.

**What ships.**

- Onboarding ritual sealed (per §6.2): docs + workspace-bootstrap integration.
- Full Eric-facing documentation: install, first-pass, daily-usage, override-workflow, audit-trail.
- Live smoke pass against a real foreign open-source SaaS-shape repo (NOT Eric's actual codebase yet — public OSS for shipping verification).
- Onboarding ritual integration with Telegram or Eric's chosen channel.

**Placement audit.**

- Onboarding ritual logic → **`framework/workspace-bootstrap/`** + **`plugins/dev-sdlc/`** (workflow specifics).
- Eric-facing docs → `docs/getting-started.md` (for the loam install) + `docs/dev-mode-getting-started.md` (for production-stake projects). Mixed.
- Smoke fixtures → **`plugins/dev-sdlc/odd-extractor/tests/fixtures/`**.

**Enables for Eric.** He can install. End-of-path.

**Dependencies.** All prior versions.

**Risk + mitigation.** Smoke-pass on real OSS repo reveals a v0.1.8 / v0.1.9 issue too late. Mitigation: open-source-fixture smoke begins at v0.1.8 (extractor-only) and is re-run at every subsequent version; v0.2.1 is verification, not first-touch.

**Gate to Eric installation.** End-to-end smoke passes; Eric's first install replicates the documented onboarding ritual without surprise.

---

## §9 — Out-of-scope or deferred

These items came up in research but don't ladder to Eric's path. Brief mention each, name why deferred.

- **V2.C swarm-runtime primitive** — load-bearing for v0.2.x per existing roadmap. Eric's v0.1.8 extractor uses Lens 5 swarming patterns at text-corpus level (background-agent dispatch); runtime composition is a follow-on optimisation, not an Eric-blocker.
- **M-GMP graphiti as plugin** — useful for richer cross-codebase memory; Eric's per-project PM works fine on M-FBM at v0.1.5+.
- **Multi-LLM via OpenRouter** — Eric uses Claude; cost-saving via DeepSeek not load-bearing for production-safety stakes.
- **Anthropic Memory tool adapter (D-2 in v0.1.5)** — Eric uses Claude Code, not raw Claude API.
- **Channel-violation hook hardening (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:125`)** — Eric's channel discipline is workspace-local; structural hook is v0.2.x territory.
- **ODD-conformance sweep (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:153`)** — sweep on loam itself; Eric's path is greenfield ODD on his SaaS, not retroactive sweep on loam.
- **PyPI publish gate (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:159`)** — Eric installs from source; PyPI is v0.2.x release ceremony.
- **Foundation revisions FR.1/FR.2/FR.3** — principles spec rewrite; doesn't ladder to Eric's path.
- **Two-copies-of-loam-source friction (FIDRAFT, `FUTURE_IDEAS_DRAFT.md:181`)** — Eric trips over this at install but it's mitigated by docs-explain hedge in v0.1.2; real fix at v0.2.x PyPI publish.
- **HeavySwarm / LLMCouncil / SequentialWorkflow drift_detection / MessageTransforms / Per-run autosave** — all v0.2.x swarms-pattern entries; nice-to-have but not Eric-deliverable.
- **Ack-first persona contract amendment** — already sealed (`32ff67d`); Eric inherits this for free.
- **Memory-system silent-swallow audit / orchestrator silent-swallow patterns** — composes with G3 production-safety mode but the audit-pass is its own scope; not gating Eric's deliverable.

---

## §10 — Decisions Luke needs to rule on

Tight list. Each: yes/no or pick-from-list framing + recommendation + why.

### Decision A — Is the partition rule's reclassification of V11.C correct?

**Question.** Earlier FIDRAFT entry placed `framework/odd-extractor/`; partition rule overrides to `plugins/dev-sdlc/odd-extractor/`. Confirm.

**Recommendation.** **Confirm.** Extractor is dev-specific (only useful for working on codebases). Composes with `plugins/dev-sdlc/`'s existing surface. Lens 1 favours `.claude/skills/` integration if relevant; that's orthogonal to the dev-sdlc placement.

**Risk if wrong.** Pollutes core framework with dev-tooling; non-dev users carry weight.

### Decision B — Is six new versions (v0.1.6–v0.2.1) the right release granularity?

**Question.** Six smaller releases vs three larger releases vs one big "Eric edition" release.

**Recommendation.** **Six smaller releases.** Iterate-in-public friendly; gates at every release surface failures early; smaller blast-radius per release. Composes with existing v0.1.x cadence pattern.

**Risk if wrong.** Six release ceremonies = overhead. Mitigation: each release is hours-not-days of AI-time; release ceremony is small.

### Decision C — Do subagent personas live in `plugins/dev-sdlc/agents/` or `.claude/agents/` (or both)?

**Question.** Native Claude Code discovery wants `~/.claude/agents/` or `<project>/.claude/agents/`. Partition rule says dev-specific subagents → `plugins/dev-sdlc/agents/`. Resolution?

**Recommendation.** **Authoritative source files in `plugins/dev-sdlc/agents/`; workspace-bootstrap installs symlinks (or copies) into `<workspace>/.claude/agents/` at first-run.** This satisfies Lens 1 (Claude-native discovery works) AND the partition rule (source-of-truth lives in dev-sdlc). User can disable specific subagents per workspace by removing the symlink.

**Risk if wrong.** Discovery breaks (subagents not visible to dispatch tool) or partition rule violated (dev-stuff in core).

### Decision D — Eric's first reverse-engineering pass: dry-run-default or live-default?

**Question.** When Eric runs `loam reverse-engineer`, does dry-run or live execute by default?

**Recommendation.** **Dry-run-default with explicit Eric `--live` flag.** Production-stake stakes mean cost-runaway (F7) must be opt-in. Eric sees the budget estimate, approves, runs live. One extra confirmation step is correct for the stakes.

**Risk if wrong.** Live-default + pathological codebase = $1000+ surprise bill on Eric's first install. Trust-destroying.

### Decision E — v0.2.2 buffer release: pre-allocate or wait-and-see?

**Question.** Should the version sequence pre-allocate v0.2.2 for known-but-unsurfaced friction (similar to v0.1.2's "fix what v0.1.0 strangers will hit"), or land everything in v0.2.1 + iterate from there?

**Recommendation.** **Pre-allocate v0.2.2 as bandwidth buffer.** The Eric-deliverable v0.2.1 will surface friction even with the v0.1.6+ shielding. Pre-naming the buffer prevents the iterate-in-public temptation to keep adding to v0.2.1.

**Risk if wrong.** Wasted version-number if no friction surfaces (low probability given size of new surface area).

### Decision F — Open-source smoke fixture: which SaaS-shape repo?

**Question.** Smoke pass at v0.1.8 / v0.2.1 needs a non-Eric foreign codebase to test against. Pick.

**Recommendation.** Pick a small Python-Flask-payment-style OSS app as the v0.1.8 first fixture (Python = first-class extractor language). Add a Ruby or TS fixture for v0.1.9+ to exercise G9 fallback path. Shortlist to be authored as part of v0.1.8 plan-doc.

**Risk if wrong.** Smoke fixture too dissimilar to Eric's actual SaaS; smoke passes but Eric's first run fails. Mitigation: pick a fixture closer in shape (likely python + sqlalchemy + stripe-API + flask).

### Decision G — Production-safety mode: does it ship at v0.1.6 (defensive shield first) or land later (just-in-time)?

**Question.** v0.1.6 priority.

**Recommendation.** **Ship at v0.1.6 first.** Defensive shield BEFORE the sharp tools. The v0.1.7+ work runs in canonical with production-stake mode active; bugs in dangerous capabilities surface against the shield rather than against bare defaults.

**Risk if wrong.** Sequence wastes time if production-safety mode itself has bugs. Mitigation: small surface (config + a dozen branch-points); ship-and-iterate.

### Decision H — Per-project PM persona: ship at v0.1.7 alongside subagents, or split into its own version?

**Question.** v0.1.7 cohesion vs splitting.

**Recommendation.** **Bundle at v0.1.7.** Subagents without a PM are coordination tokens flooding the persona's context (the value-prop audit's drift). PM without subagents is a coordinator with nothing to coordinate. They ship together or neither ships.

**Risk if wrong.** v0.1.7 is the heaviest non-extractor release at 16–24 hours. If it overruns, splitting becomes the obvious response.

### Decision I — Decisions Eric defaults to ratifying vs decisions Eric must explicitly rule on?

**Question.** During each AC ratification cycle, do PLAUSIBLE→VERIFIED promotions default-to-yes (Eric overrides if wrong) or default-to-no (Eric must explicitly approve each)?

**Recommendation.** **Default-to-no.** Production-stake stakes require explicit ratification. Each PLAUSIBLE→VERIFIED promotion is a contract-binding decision; silent default-yes acceptance is the F1 failure-mode entry-point. Eric can accept-all-batched, but each batch is an explicit acceptance moment.

**Risk if wrong.** Eric finds default-to-no slow; tunes out; ratifies in bulk without reading. Mitigation: PM persona surfaces ACs in batches by domain (payment-handling / accounting / etc.); Eric reviews by domain.

---

## §11 — Honest doubts + what could go wrong

F2 RF voice. The places I am NOT confident.

### 11.1 — Confidence-band schema may not survive contact with Eric's actual codebase

The three-band schema (VERIFIED / PLAUSIBLE / HYPOTHESISED) is clean in design but real codebases produce edge cases. A test that pins a buggy behaviour is "verified" but pins the wrong thing. A code-shape that screams "this enforces X" might enforce X-and-also-something-else. The bands compress real-world ambiguity. **Mitigation hypothesis:** ship with three bands; if v0.1.8 smoke surfaces edge cases, refine the schema before v0.1.9. **Could invalidate the sequence:** if the band schema needs to be 5+ bands, G6 and G1 both expand.

### 11.2 — "Minimal-input usage" may be unrealistic for production-stake work

Luke's directive says "least possible input from him." Eric's stakes say production-safety. These pull opposite directions: fewer Eric-inputs = more loam-autonomy = higher F1/F3 risk. The reconciliation is "decision-driven, not status-driven" + production-safety profile = halt-and-surface bias, but the math may prove that for ANY non-trivial change, Eric ratification is required, which means SC4 (< 30 min/day) becomes hard. **Could invalidate.** Eric's experience may show < 30 min/day is achievable only for trivially-scoped changes; substantive changes always require ratification. Reframing: Eric's bandwidth shifts from "describe + check" to "approve + check."

### 11.3 — Foreign-language fallback (G9) may be too thin

Loam's tooling is Python-first. Ruby / TypeScript / Go fallback via grep-and-LLM-reasoning works but at materially lower confidence. If Eric's SaaS is Ruby (a common fintech language), HYPOTHESISED-band ACs may dominate the contract draft. Eric ratifies a thinner derived contract, which means thinner gate, which means thinner production safety. **Could invalidate.** May force adding a Ruby-first-class extractor to v0.1.8 (expanding scope by 8–16 hours) or accepting reduced safety for non-Python SaaS.

### 11.4 — The PR-safety gate's CI integration touches Eric's company's CI infra

G2 Layer 3 requires writing to Eric's company's CI pipeline. Permissions, secrets, integration with whatever CI provider his company uses (GitHub Actions, CircleCI, Jenkins, etc.). This is a SOCIAL problem (does his team accept loam writing to their CI?) more than a technical one. **Could invalidate.** If Eric's team rejects loam-authored CI changes, gate is local-only (Layers 1+2), which catches less.

### 11.5 — V11.C heavy version is 24–40 hours; it may be 60+

The current research artefact is 907 lines but it's research, not plan. The plan-author dispatch will surface sub-decisions (per the eight D-Q.RE.* already named, plus more on ratification + confidence-bands + incremental mode). 24–40 hours is a calibrated estimate; the unknown-unknowns could push it to 60+ hours. **Could invalidate.** v0.1.8 may need to split into v0.1.8.a (read-only extractor) + v0.1.8.b (full extractor with confidence-bands) — adding a release.

### 11.6 — "Eric's team accepts loam PRs" assumption (SC5) is untested

The audit-trail PR description (G8) and the contract-grounded reasoning are designed to make loam PRs review-cleanly. But teams have culture; some teams will reject any AI-authored PR on principle. **Could invalidate.** If Eric's team rejects loam PRs, his minimal-input-loop breaks because every PR becomes a social negotiation rather than a technical merge. Mitigation needed: Eric authors PRs as if they were his own (loam-as-his-pair); his name on the PR; the audit-trail is in the PR description but loam isn't credited at the social layer. Captures real social dynamics; worth surfacing as part of v0.2.1 onboarding.

### 11.7 — "Tens to hundreds of thousands of dollars" is real-money but I don't know Eric's domain

If it's payment-processing (Stripe-shape), there are existing audit standards (PCI-DSS) that constrain what gates are even allowed. If it's accounting (QuickBooks-shape), GAAP / regulatory considerations apply. If it's marketplace (eBay-shape), KYC + sanctions screening + dispute-handling. Each domain shapes what "production-safety" means. **Could invalidate.** Eric's domain may have specific compliance requirements that demand domain-specific safety primitives loam doesn't ship. **Mitigation:** v0.2.1 onboarding ritual asks Eric "what's your domain? what compliance constraints apply?" and surfaces compliance-aware adjustments; if compliance constraints exceed loam's support, surface that and recommend Eric supplement loam with domain-specific tooling.

### 11.8 — Luke's "minimal possible input" phrasing may need negotiation

F2 RF to Luke's framing: production-safety stakes are incompatible with autonomous loam-driven merges. The right Eric-shape is **"minimal Eric-decision-burden, non-trivial Eric-ratification-bandwidth."** Eric ratifies ACs on schedule; Eric approves merges as they come up; loam handles everything between those moments. The total wall-time Eric spends is much less than authoring himself, but it's not "click once and walk away." If "minimal possible input" means click-once-walk-away, the recommendation should be: don't ship Eric a tool that auto-merges to a real-money SaaS; the autonomy ceiling is too high. **Surfaced for ruling.**

### 11.9 — PM persona is a new shape and may need iteration

G5 is the largest unproven persona-shape addition since the primary persona itself. The FIDRAFT entry is well-formed but doesn't yet have a design-doc. v0.1.7 needs research-grade plan-doc time. **Could invalidate.** PM may turn out to be the wrong shape (too thick, too thin, wrong boundary); design iteration may push v0.1.7 into a v0.1.7.a / v0.1.7.b split.

### 11.10 — The version sequence assumes M-FBM is operationally healthy

M-FBM operational-health amendment #125 just sealed (`1a1f830`); it's hours-old in production. Cross-session continuity is the actual ship-test (`STATE.md` 2026-05-01 reframe). If M-FBM proves unhealthy in field use, the per-project-PM (G5) and continuous-watch (G10) both depend on it for state persistence; both would shift to alternate substrates. **Could invalidate.** M-FBM regression discovery in v0.1.6 or v0.1.7 forces a stabilisation amendment before v0.1.8 can build.

---

## §12 — Partition-rule placement audit

Dedicated section that confirms placement for every capability the version sequence introduces. This is the structural enforcement that the partition rule actually got applied — not just stated.

### Format

Each row: capability → placement → reasoning.

### v0.1.6 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| `safety_profile` config field | `framework/` (workspace config schema) | Harness-general; ANY user with high-stakes work benefits. |
| Default-flipping logic for production-stake | `framework/` core defaults + `plugins/dev-sdlc/` dev-specific defaults | Mixed; framework holds general defaults, dev-sdlc holds dev-specific (e.g., subagent halt-on-push). |
| Cost-governance recalibration (foreign-codebase budgets) | `framework/cost-governance/` | Cost-governance is harness-general (existing component). |
| Extractor-specific budget knobs | `plugins/dev-sdlc/odd-extractor/` (deferred to v0.1.8) | Dev-specific. |
| Dry-run mode general primitive | `framework/cost-governance/` (if generalisable) OR `plugins/dev-sdlc/odd-extractor/` (if extractor-specific) | TBD at plan-author time; recommendation: framework if generalisable. |

### v0.1.7 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| Subagent persona definitions (5 named) | `plugins/dev-sdlc/agents/<name>.md` | Dev-specific personas; symlinked into `.claude/agents/` at workspace-bootstrap. |
| Subagent persona registration mechanism | `framework/workspace-bootstrap/` | Harness-general; bootstrap is framework. |
| Per-project PM-shape (loader, contract, registry) | `framework/per-project-pm/` | PM-shape is harness-general; non-dev projects also benefit. |
| Eric-specific PM instance | Eric's loam workspace `.loam/pms/eric-saas-pm/` | Workspace-state, not framework or plugins. |
| Decision-surfacing PM discipline (design-note + persona prompt content) | `framework/per-project-pm/` | Discipline lives where the PM lives. |

### v0.1.8 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| ODD extractor (Cartographer-style heavy) | `plugins/dev-sdlc/odd-extractor/` | Dev-specific. **Correction from FIDRAFT's `framework/odd-extractor/` placement.** |
| ODD methodology extension (confidence bands) | `plugins/dev-sdlc/docs/odd-methodology.md` | Existing dev-sdlc doc; extension stays. |
| Confidence-band schema | `plugins/dev-sdlc/odd-extractor/` | Dev-specific schema for dev-specific tool. |
| Language-agnostic skeleton + Python first-class | `plugins/dev-sdlc/odd-extractor/lang/` | Dev-specific. |
| Test-first extraction priority | `plugins/dev-sdlc/odd-extractor/` | Dev-specific. |
| Eric-ratification workflow | `plugins/dev-sdlc/odd-extractor/ratification/` + `framework/per-project-pm/` (PM surfaces decisions) | Mixed. |

### v0.1.9 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| PR-safety gate | `plugins/dev-sdlc/pr-safety/` | Dev-specific. |
| Pre-commit hook installer | `plugins/dev-sdlc/pr-safety/installers/` | Dev-specific (Eric's repo, dev workflow). |
| Pre-push hook installer | `plugins/dev-sdlc/pr-safety/installers/` | Dev-specific. |
| CI status-check templates | `plugins/dev-sdlc/pr-safety/templates/ci/` | Dev-specific. |
| Provenance-traceable PR description template | `plugins/dev-sdlc/pr-safety/templates/pr/` | Dev-specific. |
| Override workflow (contract-update commit) | `plugins/dev-sdlc/pr-safety/` | Dev-specific. |

### v0.2.0 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| Continuous codebase-watch (extractor incremental mode) | `plugins/dev-sdlc/odd-extractor/` | Dev-specific (incremental mode of dev-tool). |
| Scheduling integration | `framework/scope-of-work/` | Existing harness primitive (sealed). |
| PM ratification-queue mechanics | `framework/per-project-pm/` | PM is harness-general. |
| Domain-batched AC surfacing | `framework/per-project-pm/` | PM-discipline. |

### v0.2.1 capabilities

| Capability | Placement | Reasoning |
|---|---|---|
| Onboarding ritual (`loam init` integration) | `framework/workspace-bootstrap/` + `plugins/dev-sdlc/` (dev-specific steps) | Mixed. |
| Eric-facing install docs | `docs/getting-started.md` (general) + `docs/dev-mode-getting-started.md` (production-stake) | Mixed; general user-facing docs at `docs/`. |
| Smoke fixtures | `plugins/dev-sdlc/odd-extractor/tests/fixtures/` | Dev-specific. |
| Live-OSS-smoke pass (CI artefact) | `plugins/dev-sdlc/pr-safety/tests/` + `plugins/dev-sdlc/odd-extractor/tests/` | Dev-specific. |

### Cross-cutting confirmations

- The existing `plugins/loam-skills/` stays where it is — those are general harness-translation patterns that any loam user benefits from. NOT moved into dev-sdlc.
- The existing `framework/` components stay where they are — sealed, harness-general.
- New capabilities surface in BOTH locations only when there's a genuine split (PM-shape harness-general; PM-instance workspace-state; PM-dev-specific-skills registered through dev-sdlc).
- Documentation: `docs/` for user-facing; `plugins/dev-sdlc/docs/` for dev-specific (CDCs, methodology, smoke-test discipline, ODD methodology / in-loam already there).

### No partition violations identified

Every G1–G11 capability has been audited against the partition rule. Mixed-location capabilities (G3, G7, G10) are decomposed into harness-general parts (`framework/`) and dev-specific parts (`plugins/dev-sdlc/`). No capability is wholly dev-specific in `framework/` or wholly harness-general in `plugins/dev-sdlc/`.

### Halt-and-surface: no fundamental conflicts surfaced

Per the dispatch's halt trigger ("Partition rule creates a fundamental conflict (e.g., a capability genuinely belongs in framework/ but is also dev-specific) → halt + surface"): no such conflict was found during this audit. The partition rule decomposes cleanly across all G1–G11 capabilities.

---

## Provenance trail

Every recommendation in §3, §4, §5, §6, §7, §8 carries an inline source citation. Cross-cuts:

- **`docs/rebuild/VALUE_PROPOSITION.md`** — anchors persona-as-translator + harness-test failure modes.
- **`docs/rebuild/STATE.md`** — sealed-component inventory + amendment history.
- **`docs/rebuild/plans/v0-1-x-roadmap.md`** — current 5-release sequence; Eric path extends it.
- **`docs/rebuild/plans/value-prop-vs-actual-shape-audit-2026-05-04.md`** — drift analysis + Option 5 (subagent + skill + design note); G4/G5/G11 ladder up.
- **`docs/rebuild/FUTURE_IDEAS_DRAFT.md`** — V11.C heavy (`:175`); per-project PM (`:25`); subagent personas (`:189`); vertical swarming (`:23`); ODD-conformance sweep (`:153`); memory-backend abstraction (`:147`); D-1/D-2/D-3 memory amendments (`:149`); ack-first (`:151`); two-copies friction (`:181`); production-safety / silent-swallow (`:127`/`:129`/`:133`); Anthropic-perspective ladder (`:155`); durable capture rule (`:157`).
- **`docs/design/odd.md`** — ODD methodology + §2.5 reverse direction + re-extension pattern.
- **`plugins/dev-sdlc/docs/smoke-test-discipline.md`** — 6-dimension coverage spec; required for production-stake.
- **`plugins/dev-sdlc/docs/cdcs/`** — graceful-fallthrough-with-detection (Eric stakes need detection at fallthrough); plan-before-code; research-before-plan; scope-only-dispatch.
- **`framework/CLAUDE.md`** (= top-level `CLAUDE.md`) — Lens 1 / Lens 2 / Lens 3 / Lens 4 / Lens 5; partition framing (loam is general-purpose harness; dev-mode partition).

---

## Method-decision register

(Reserved for post-build amendment SHAs as v0.1.6 → v0.2.1 land. Empty at plan-doc authoring.)

| Release | Status | Tag SHA | Notes |
|---|---|---|---|
| v0.1.6 | (planned) | — | Production-safety mode + cost-governance recalibration. |
| v0.1.7 | (planned) | — | Subagent personas + per-project PM persona + decision-surfacing discipline. |
| v0.1.8 | (planned) | — | ODD reverse-engineering heavy + confidence bands + language-agnostic skeleton. |
| v0.1.9 | (planned) | — | PR-safety gate + provenance-traceable PR template. |
| v0.2.0 | (planned) | — | Continuous codebase-watch. |
| v0.2.1 | (planned) | — | Eric-deliverable smoke + onboarding ritual hardening. |

---

*End of plan. Six new releases beyond current v0.1.x roadmap. ~40–80 hours AI-time, midpoint ~55h. Eric-deliverable at v0.2.1.*

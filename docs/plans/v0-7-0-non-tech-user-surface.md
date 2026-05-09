# v0.7.0 minor — non-tech user surface (cold-start to working software)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner ratifies before any cycle dispatches.
**Slug:** `v0-7-0-non-tech-user-surface` (descriptive-with-version-prefix; the priority-queue restructure plan-doc that would remove version prefixes is uncommitted-pending).
**Date authored:** 2026-05-09. Originally scoped as the §4 entry currently labeled v0.6.0 in `docs/release-roadmap.md`; v0.6.0 number was consumed by the just-shipped release-process work (sealed local 2026-05-09). Per Q2 ratification (class is suggestive on roadmap; plan-author rules at build-time): work is **derived as v0.7.0** at build-commence-time. Final version number is plan-author's call once builds dispatch; v0.7.0 is the recommended derivation given the work shape (new outcome capability) and the shipped chain (v0.6.0 just sealed).
**Class:** **MINOR — END-USER**. New outcome shape: a non-tech user can go from fresh install through working software via natural-language conversation only (no exposure to ODD vocabulary, no technical decision-making forced upward). Per `release-versioning-policy.md` quality gate: an END-USER minor must name a specific translation-burden delta — this work names the deltas in §4.
**Predecessor:** v0.6.0 (concrete release process; sealed local 2026-05-09; awaiting publish).
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-09 (plan-author dispatch); covers plan-doc authoring only. Build-cycle dispatch + publish remain owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

A non-technical user with a fresh `git clone lukeivers/loam`, a working Claude Code install, and no prior knowledge of ODD / objectives / acceptance criteria / loam internals can:

1. Run a single setup command (or open the workspace and trigger first-run automatically).
2. Answer a small number of plain-English questions about what they want to build and how they prefer to be talked to.
3. Say what they want — in natural language, the way they would tell a colleague.
4. Receive working software output (code that runs; or a deployed artefact at a tier they ratified) without ever being asked "what's your acceptance criterion" or "is this an MVP or a stretch?"

**Why this is the v1.0 trajectory entry.** Per `docs/release-versioning-policy.md` §1.0.0 criterion #2 ("one real user has shipped real software with loam"), v1.0 cannot ship until the non-tech-user end-to-end is empirically real. v0.7.0 makes it possible for the first time — every prior minor delivers internal substrate (ODD machinery, code-gen pipeline, release process, subagent personas) that a technically-comfortable user could leverage; v0.7.0 is the version where that substrate becomes accessible to a user who would not otherwise know to invoke any of it. The v1.0 criterion does not ship at v0.7.0 — that requires a real user actually shipping (an out-of-roadmap event) — but v0.7.0 is the prerequisite that makes the criterion reachable.

**Why now.** v0.6.0 closed the release-process gap; the substrate is otherwise stable (memory retrieval fixed at v0.4.3, subagent-personas routing at v0.5.0, working-software code-gen at v0.4.x). Every remaining gap to non-tech-user empirical use is in the user-facing surface — onboarding flow, channel default, light-touch narration, scope-tier conversation. None of those depend on further substrate work, so v0.7.0 is unblocked.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ a non-tech user reaches working software via natural
            language only (V070 outcome)
             └─ Goal #2 (loam-as-consulting-tool) becomes
                 empirically real for the first time
                  └─ v1.0 quality-bar criterion #2 ("one real user
                      has shipped real software with loam") becomes
                      reachable as a real-world event
```

The two VALUE_PROPOSITION tests:
- **Primary-persona test** — every AC in this version measures whether the user's translation burden drops. The light-touch narration AC (V070.1) and the implementation-tier picker AC (V070.7, conditional per Q3) move translation burden from user → persona; the channel-config AC (V070.2) removes the burden of remembering which surface to reply through; the workspace corpus override AC (V070.3) removes the burden of teaching the persona about the user's domain by hand-loading docs.
- **Harness test** — every AC adds to the persona's toolkit. Channel routing, tier ladder, corpus loader, memory-doc template, and onboarding flow are all primitives the persona invokes; none push work back to the user.

## §3 — Component fence

Surveyed canonical components (`framework/`); no new components warranted at this scope. Three existing components carry the work:

**PRIMARY:** `framework/workspace-bootstrap/` — onboarding flow extension. The component already implements AC.ONBOARD.{1-15} (the v0.2.1 + v0.2.2 onboarding hardening surface), including channel-preference recording (AC.ONBOARD.4). The v0.7.0 work extends the existing onboarding ritual to (a) read the channel slot at session-start and feed it to the channel-routing layer, (b) ship the workspace-corpus-override pattern with a reference example, (c) widen the survey to capture implementation-tier preference.

**PRIMARY:** `framework/primary-persona/` — light-touch education + tier picker SKILL bundle. The component already carries the persona's session-start, dispatch, and reply surface; the v0.7.0 work adds a SKILL extension (or new SKILL under `plugins/dev-sdlc/skills/` if dev-mode-only) for ambient-narration prompting, plus the tier-ladder doc + persona-prompt section the persona reads at scope-of-work negotiation time.

**SECONDARY:** `framework/tools/loam/` — `loam new-memory <slug>` orchestration (parallel to the existing `loam new-plan <slug>` if it exists, or to `pos-amend new-plan` shape per the FUTURE_IDEAS Idea 22 reference). Extends the existing `loam` CLI top-level. Also receives the `--quickstart` (or equivalent) verb that the README's "fresh install" instruction names.

**SECONDARY:** `plugins/dev-sdlc/skills/` — new SKILL or SKILL extensions for the implementation-tier conversation pattern (only if Q3 ratifies fold-in; otherwise this component stays untouched and the tier picker becomes a separate amendment).

**Untouched:** All other components. No edits to `framework/objective-tracker/`, `framework/scope-of-work/`, `framework/per-project-pm/`, `framework/cost-governance/`, `framework/safety-layer/`, `framework/orchestrator/`, `framework/dormancy/`, `framework/observability-aggregator/`, `framework/reversibility-primitive/`, `framework/self-correction/`, `framework/self-upgrade/`, `framework/telegram-interface/`, `framework/loam-init/`, `framework/hands-off-lifecycle/`, `framework/workspace-sync/`, `framework/tools/heavy-b-migrate/`, `framework/tools/` other than the `loam` CLI extension.

**New components:** None proposed at plan-time. The work fits inside three existing component fences.

## §4 — Acceptance criteria

The §4 V060.1-6 ACs from the existing roadmap entry translate to V070.1-6 with concrete deliverables; one new AC (V070.7, conditional on Q3) for the implementation-tier picker; one outcome-altitude AC (V070.6) covering the stranger-clone-to-working-software end-to-end; one seal-diff AC (V070.S).

### AC.V070.1 — Light-touch education / ambient narration

**What:** The persona surfaces a one-sentence reasoning trace alongside any structural decision it makes on the user's behalf (modality choice — one-shot vs scheduled vs background; specialist routing; tier selection; data-model framing). Format: appended to the action-confirmation reply, prefixed with a calibrated lead phrase ("I'm doing this as X because Y" / "I'll set this up as X — that way Y" / equivalent), exactly one sentence. Not interruptive (does not pause for user acknowledgement); not advisory (does not ask "is that OK"); structural (always present on these decision categories, never present on routine action-takes).

**Acceptance:** A SKILL or persona-prompt section ships at `framework/primary-persona/skills/light-touch-narration/SKILL.md` (or equivalent path; new) that names the decision categories that trigger narration (modality, specialist, tier, data-model), the one-sentence format, and the calibrated lead-phrase set. Tests: (a) golden-fixture probe — given a fixture user request that maps to a scheduled-task modality decision, the persona's reply contains a one-sentence narration in the named format; (b) negative probe — given a fixture user request that's a routine action (no structural decision), the persona's reply does NOT carry narration; (c) verbosity-tunable — survey field `education_verbosity: terse | default | richer` toggles a per-message budget (default 1 sentence; terse 0 sentences when the decision is uncontested; richer up to 3 sentences when the decision had alternatives worth naming).

`outcome-altitude: false` — implementation-altitude AC; STUB-class (golden fixtures) acceptable per the test-altitude rubric.

### AC.V070.2 — Channel config slot honored at runtime

**What:** Workspace-level config field `primary_channel: telegram | terminal | <future>` (location: extends the existing `workspace-bootstrap` manifest at `<workspace>/.pos/manifest.yaml` per AC.ONBOARD.4 precedent; `<workspace>/.pos/channel.json` is acceptable alternate per Idea 25 — builder rules at D-V070.2). Honored by the persona's reply surface: when `primary_channel = telegram`, the persona routes user-replies through `mcp__plugin_telegram_telegram__reply` and the Stop-hook contributor refuses terminal-reply on user-reply messages (terminal stays for diagnostics). When `primary_channel = terminal`, current behavior preserved (no-op).

**Acceptance:** (a) onboarding survey adds the channel-default question (or extends AC.ONBOARD.4 to cover both telegram + terminal explicitly with `primary_channel` semantics — D-V070.2.b ruling); (b) the manifest-loader exposes `primary_channel` to the persona's session-start path; (c) Stop-hook contributor at `framework/primary-persona/src/loam/primary_persona/<channel-routing>.py` reads the slot + halts terminal-reply on user-message paths when `primary_channel = telegram`; (d) tests cover the four cells (slot=telegram + reply-target=telegram → pass; slot=telegram + reply-target=terminal + user-reply → halt; slot=telegram + reply-target=terminal + diagnostic → pass; slot=terminal → no-op).

`outcome-altitude: false` — implementation-altitude AC; STUB-class acceptable.

### AC.V070.3 — Workspace corpus override pattern (documented + reference example)

**What:** Per Idea 26: the existing `_resolve_corpus_path` fall-through (already implemented at `framework/hands-off-lifecycle/` — verified via grep at plan-time) supports a workspace-specific corpus override (e.g., a domain-specific persona prompt at `<workspace>/.loam/corpus/<filename>.md` overrides the canonical default). The pattern is implemented but undocumented at the user surface. v0.7.0 ships (a) a new doc at `docs/workspace-corpus-overrides.md` (sibling to `release-process.md`) explaining the pattern + when to use it + how to author an override file; (b) one canonical reference override under `docs/examples/corpus-overrides/<example-name>.md` (e.g., a "household-finance" persona-prompt override demonstrating the pattern for a non-dev workspace).

**Acceptance:** Doc exists at canonical path; covers what the override does + reader-fall-through order + 3 use cases; reviewable in 5 minutes. Reference override exists at canonical path + parses cleanly through the existing `_resolve_corpus_path` resolver. Test: integration test loads the reference override into a fixture workspace + verifies the resolver picks it over the canonical default.

`outcome-altitude: false` — implementation-altitude AC; documentation + integration probe.

### AC.V070.4 — Memory-doc skeleton template + `loam new-memory <slug>` orchestration

**What:** Third member of the template family per Idea 22 (existing: dispatch-template, plan-doc-template). Memory-doc skeleton has frontmatter (per the existing memory-rule shape under `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md` — captured-date, composes-with, status, source, derivation-line per `feedback_principle_conflict_resolution_multi_signal`'s procedural rule), Why section, How-to-apply section. Orchestration verb `loam new-memory <slug>` (or `pos-amend new-memory <slug>` if the existing CLI shape per `pos-amend-new-plan-orchestration.md` is the canonical one — D-V070.4 builder ruling) renders the skeleton at the canonical memory path with the slug filled in.

**Acceptance:** (a) template file at `framework/tools/loam/templates/memory-doc/SKELETON.md` (or equivalent path; new); (b) CLI verb registered + invokes the renderer; (c) integration test: `loam new-memory test-rule` produces a syntactically-valid memory file at the expected path; the file's frontmatter parses + carries the required fields. Reuses the existing template-engine surface (no new engine code).

`outcome-altitude: false` — implementation-altitude AC; integration probe sufficient.

### AC.V070.5 — Real session-transcript demo (reference artefact)

**What:** A reference transcript captured + published demonstrating a non-tech user (or stand-in proxy) reaching working software output through the V070.1 + V070.2 + (V070.7 if folded) flow. Format: a stripped + annotated transcript at `docs/examples/non-tech-user-session-transcript.md` covering (a) initial onboarding question-set, (b) the user's natural-language ask, (c) the persona's tier-conversation + structural-decision narration, (d) the working-software output (with link to the produced artefact under `docs/examples/non-tech-user-session-output/` or equivalent).

**Acceptance:** Transcript file exists at canonical path; covers the named four moments; output artefact exists + is operational (script runs / page loads / equivalent per the chosen tier). Reviewable in 10 minutes. Reference user choice is owner-ratified per Q2.

`outcome-altitude: false` — this is a captured demo, not a probe; the probe is V070.6.

### AC.V070.6 — Outcome-altitude probe: stranger-clone end-to-end

**What:** A scripted end-to-end test that simulates a fresh `git clone lukeivers/loam` → run the published quickstart command → answer the onboarding survey → make a natural-language ask → receive working-software output. Not a stub — invokes the production entry-points (real `loam` CLI, real onboarding flow, real persona session-start path, real `claude -p` subprocess for the persona's reply path). Inputs are realistic (not pre-arranged state). Pass criterion: the run produces working-software output (per the chosen tier — script that executes successfully against a fixture input; or a service URL that returns a fixture-expected response) AND the user-visible surface contains zero ODD vocabulary terms (`objective`, `acceptance criterion`, `constraint`, `AC.*`, `ODD`, `methodology` outside of bracketed-citation contexts).

**Acceptance:** Test at `framework/workspace-bootstrap/tests/test_AC_V070_6_outcome_altitude_stranger_clone.py` (or equivalent path under whichever component owns the outcome-altitude probe registry). Real-execution probe per the test-altitude rubric — no pre-arranged state the production code would normally produce. The vocabulary check is a post-condition assertion against the captured user-facing surface (chat replies + CLI output + onboarding-question text). Build report records the verdict against the actual reference user (per Q2).

**Note on reference-user choice:** the exact stranger-clone-to-working-software protocol depends on the reference user (Q2). For Eric (existing loam user; not a true stranger; familiar with the substrate), the probe is shorter — the reference path is "Eric clones a fresh workspace, opts into a non-dev mode, asks for X, receives X." For a true new user (more validation; harder to arrange), the probe is the full stranger-clone path. The test code is the same shape regardless; only the live-run target changes.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required`. Risk band: **production-facing** (per the rubric sub-rule — user-visible surface; HARD per-cycle REQUIRED).

### AC.V070.7 — Implementation-tier picker conversation pattern (CONDITIONAL on Q3)

**What:** Per the FUTURE_IDEAS_DRAFT entry captured 2026-05-09 (Telegram 10575): a predefined plain-English ladder of implementation tiers + a persona-prompt SKILL section + one example onboarding flow exercising it. Five candidate tiers per the FIDRAFT entry: (1) one-time on-thread, (2) reusable script, (3) local file-based, (4) local service-based, (5) external service. Tier 5 carries an exceptionally clear risk surfacing (data exposure + auth/security obligations + ongoing operational liability); tier-5 selection requires explicit per-tier conversation about data/privacy/security.

**Acceptance:** (a) tier-ladder doc at `docs/implementation-tiers.md` (sibling to `release-process.md`); (b) SKILL file at `framework/primary-persona/skills/implementation-tier-picker/SKILL.md` (or equivalent path) containing the persona-prompt section + the five-tier ladder + the tier-5 risk surfacing template; (c) one example onboarding-shaped fixture exercising the tier conversation against a fixture ask (e.g., "I want to build a daily news digest" → persona surfaces tiers + explains the cost/capability/risk trade-off → user picks tier 2 → persona proceeds). Test: golden-fixture probe verifies the SKILL surfaces the tier conversation when the user's ask is ambiguous between tiers.

**Conditional:** This AC ships only if Q3 ratifies fold-in. If Q3 ratifies separate-amendment, V070.7 is removed at build-time + the tier picker becomes its own subsequent v0.7.x amendment (with its own plan-doc).

`outcome-altitude: false` — implementation-altitude AC; STUB-class acceptable. (The tier conversation IS exercised end-to-end inside V070.6's outcome-altitude probe if folded in.)

### AC.V070.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `framework/workspace-bootstrap/` (onboarding-flow extension + channel-slot read path + tests)
- `framework/primary-persona/` (light-touch narration SKILL + channel-routing Stop-hook contributor + tier-picker SKILL if folded + tests)
- `framework/tools/loam/` (`loam new-memory` orchestration verb + memory-doc template + `loam --quickstart` verb if shipped + tests)
- `plugins/dev-sdlc/skills/` (only if a SKILL lands at this fence rather than primary-persona; D-V070.7 ruling)
- `docs/workspace-corpus-overrides.md` (new file)
- `docs/implementation-tiers.md` (new file; conditional on Q3)
- `docs/examples/corpus-overrides/<example>.md` (new file)
- `docs/examples/non-tech-user-session-transcript.md` (new file)
- `docs/examples/non-tech-user-session-output/` (new directory; reference artefact)
- `docs/release-roadmap.md` (§2 row added for v0.7.0; §3 active-version updated; §4 entry collapsed)
- `docs/STATE.md` (v0.7.0 SHIPPED rollup)
- `docs/plans/v0-7-0-non-tech-user-surface.md` (this file; §status backfill post-seal)

Sidecar advances per sealed-component-cycle ritual.

## §5 — Decisions builder rules at build time

- **D-V070.1 (narration verbosity defaults):** default = 1 sentence. Survey field `education_verbosity` is the user-tunable override. Builder rules whether the SKILL ships with named lead-phrases (e.g., "I'm doing this as ___ because ___") OR with format-only constraint (one sentence; cause-effect shape; no specific lead). Recommend named lead-phrases for first ship; loosen if first reader finds them stilted.
- **D-V070.2.a (channel-slot location):** default = extend `<workspace>/.pos/manifest.yaml` per the existing AC.ONBOARD.4 channel-preference precedent (already in `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`). Switch to `<workspace>/.pos/channel.json` only if the manifest extension causes downstream incompat.
- **D-V070.2.b (survey-question shape):** default = extend the existing AC.ONBOARD.4 question to cover `primary_channel` explicitly with telegram + terminal options. Switch to a separate question only if the existing one's text doesn't compose cleanly.
- **D-V070.4 (CLI verb name + location):** default = `loam new-memory` under `framework/tools/loam/`. Switch to `pos-amend new-memory` if the existing dispatch-template + plan-doc-template orchestration lives under `pos-amend` exclusively + the parallelism is load-bearing.
- **D-V070.7 (tier-picker SKILL fence):** if Q3 folds tier picker IN, default = `framework/primary-persona/skills/implementation-tier-picker/SKILL.md` (under primary-persona because the SKILL is read at scope-of-work negotiation time, which is a primary-persona surface). Switch to `plugins/dev-sdlc/skills/` only if the tier conversation is dev-mode-only (it is NOT — non-tech users are the primary audience; tier conversation is a normal-use feature).
- **D-V070.6 (reference-user choice):** owner ratification per Q2. Builder records the chosen reference-user + the test's actual probe target in the build report.

## §6 — Out of scope (explicit)

- **ProgramBench v0.5 binary-feeder work** (the original §4 v0.5.0 entry — "loam builds software from minimal input"). That work is end-user-class but operates on a different inputs surface (binary + docs) than the v0.7.0 non-tech-user flow (natural language). Separate plan-doc, separate version (currently §4 placeholder labeled v0.5.0; will derive its own version when its plan dispatches).
- **Negative-alignment detection** (the original §4 v0.7.0 entry — now likely v0.8.0 in the renumbered chain). Substrate; not user-surface; not in this scope.
- **Deep personalization through interaction capture** (Idea 4; original §4 v0.9.0). Captures user patterns over time; depends on production-volume usage that v0.7.0 enables. Not in this scope.
- **Plugin suite expansion** (Idea 3; original §4 v0.10.0+). Each plugin is its own minor; not in this scope.
- **Structural enforcement of FR.1/FR.2/FR.3/F6** (the original §4 v0.7.0 META-FRAMEWORK entry — now likely v0.8.0+ in the renumbered chain). Substrate; not user-surface; not in this scope.
- **Multi-LLM via OpenRouter** (per architectural constraint, backlog only).
- **Anthropic API key paths** (per architectural constraint, never).
- **The implementation-tier picker AS A SEPARATE AMENDMENT** is in scope ONLY if Q3 ratifies fold-in; if Q3 ratifies split, the tier picker is out-of-scope-for-v0.7.0 + becomes its own subsequent amendment. Either way, the FIDRAFT entry composes with v0.7.0 — Q3 only decides timing.

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.V070.6 outcome-altitude probe RED (stranger-clone path fails to reach working-software output, OR user-visible surface contains forbidden ODD vocabulary). Halt; surface as F-DESIGN candidate (the design itself didn't survive first-real-use).
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. AI-time exceeds upper band (10 hr) by >50% → 15 hr wall-clock. Halt with current state.
6. Schema/architecture change to existing `workspace-bootstrap` onboarding manifest appears necessary beyond the channel-slot extension. Halt — out-of-scope per §6.
7. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.
8. Any `claude -p` invocation without `--strict-mcp-config` + empty MCP config tempfile (per the v0.2.5 C5 propagation invariant). Immediate halt.
9. Per Q1 ratification: if owner ratifies SPLIT (sub-cycles), each sub-cycle has its own halt envelope; if owner ratifies MONOLITH, the single-cycle envelope applies. Builder respects whichever is ratified.

## §8 — Dependencies

- **v0.6.0 (concrete release process)** — HARD on commit-graph. v0.7.0 builds on v0.6.0's HEAD; the publish ritual for v0.7.0 will use the new `loam release` CLI per AC.V060.7 dogfood follow-on.
- **v0.5.0 (subagent-personas routing)** — SOFT. The v0.7.0 work doesn't dispatch to typed personas in production; the SKILL surface composes with whichever persona is active.
- **v0.4.x (code-gen pipeline + memory retrieval fix)** — HARD on outcome. The V070.6 outcome-altitude probe requires the persona to actually produce working software for the user's ask; that path runs through the v0.4.x code-gen + v0.4.3 memory retrieval surfaces.
- **v0.2.1 onboarding hardening (AC.ONBOARD.{1-15})** — HARD. v0.7.0 extends the existing onboarding ritual; doesn't replace it.
- **v0.2.2 ODD grounding propagation** — SOFT. The persona's internal ODD framing IS the substrate that V070.1 narration translates from; v0.2.2 ensures it's loaded.
- **`framework/per-project-pm/` component** — SOFT. Composition surface; the v0.7.0 work doesn't directly extend per-project-pm but the user's natural-language asks may resolve to per-project-pm tasks.
- **`framework/hands-off-lifecycle/` component** — HARD on V070.3 (corpus override). The existing `_resolve_corpus_path` fall-through is what V070.3 documents + ships an example for. No code changes to hands-off-lifecycle expected; pure documentation + example consumption.
- **The reverse-ODD pipeline** (`plugins/dev-sdlc/odd-extractor/`) — SOFT. Composes if the user brings an existing codebase; not required for greenfield asks.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint; everything via `claude -p`).

## §9 — Open questions for owner ratification

### Q1 — One big build cycle vs split into sub-cycles

The 6 ACs (or 7 if V070.7 folds in per Q3) carry estimated 5-10 hr AI-time; that's at the upper end of single-cycle minor scope. Two options:

- **Option A — MONOLITH (single cycle).** v0.7.0 ships all ACs in one build cycle; one seal commit; one publish. Simpler bookkeeping; one outcome-altitude probe at the end.
  - Risk: longer cycle = more surface for halt-and-surface; if any AC blocks, the whole cycle stalls.
  - Risk: 5-10 hr AI-time in a single cycle pushes against the per-cycle attention budget; mid-cycle drift more likely.
- **Option B — SPLIT (v0.7.0 + v0.7.x sub-patches).** v0.7.0 ships V070.1 + V070.2 + V070.4 + V070.S (the foundational pieces — narration + channel + memory-template); v0.7.1 ships V070.3 (corpus override pattern + reference); v0.7.2 ships V070.5 + V070.6 (transcript demo + outcome-altitude probe; tier picker if folded). Each sub-cycle has its own outcome-altitude probe (V070.S equivalent + smoke).
  - Tradeoff: per-policy (`release-versioning-policy.md`), patches close defects in the current minor's outcome shape — they don't ADD outcome shape. V070.3 + V070.5 + V070.6 are ADDITIVE outcome capability, so calling them v0.7.x patches is technically a SemVer mis-classification (cf. the v0.4.1/v0.4.2 mis-classification footnote).
  - Tradeoff: if these become v0.7.0 + v0.7.1 + v0.7.2 as PROPER MINORS each (correctly-typed), that's three minors for what could be one. The surface is small enough that three minors feels like version-inflation.

**My recommendation: MONOLITH (Option A).** The 5-10 hr AI-time band is wide; the realistic single-cycle range is ~131-200 min per the v0.6.0 precedent (which had similar scope of CLI + tests + runbook). The build-forward rule (per `feedback_build_forward_on_publish_pending`) lets the cycle proceed without owner blocking on intermediate states. Mid-cycle halt-and-surface is the canonical drift-recovery shape. A monolith ships one unambiguous outcome-shape capability (non-tech-user end-to-end); splitting fragments the outcome shape into pieces that read as "incomplete v0.7.0" without the V070.5 + V070.6 ship.

**Surfacing for ratification.** If owner prefers SPLIT, the plan-doc updates to mark per-AC sub-cycle assignments + each sub-cycle gets its own outcome-altitude probe; the §13 §status section is per-sub-cycle.

### Q2 — Reference user for V070.6 outcome-altitude probe

The V070.6 AC requires a real "stranger-clone → onboarding → request → working output" probe. Options:

- **Eric** (currently using loam at Luke's ex-employer; familiar with the substrate; not a true stranger). Pros: available, willing per past engagement, has demonstrated bandwidth. Cons: contaminated reference — Eric knows what loam does + has bypassed onboarding; not a true non-tech-user surface test. Probe degrades to "Eric clones a fresh workspace, opts into non-dev mode, asks for X" — useful but doesn't validate the stranger surface.
- **A new external user** (true stranger). Pros: real validation of the stranger surface; the user-vocabulary check actually has bite. Cons: requires arranging a user (owner action; out-of-roadmap time per the existing roadmap framing); availability + scheduling friction.
- **Synthetic proxy** (a fresh-machine cold-clone executed by the dispatcher in a separate workspace, with the dispatcher stipulating non-tech-user persona constraints). Pros: zero scheduling friction; runs in dispatcher's own time. Cons: synthetic — the dispatcher knows the substrate; rigor of the vocabulary check + the "natural-language ask" depends on dispatcher discipline; not a real-world signal.

**My recommendation: Synthetic proxy as the v0.7.0 ship probe; new external user as the v1.0 quality-bar event probe.** Reasoning: V070.6 is loam's outcome-altitude AC for v0.7.0, not the v1.0 criterion. v1.0 criterion #2 ("one real user has shipped real software") is the real-user gate; v0.7.0's job is to make that gate reachable. Synthetic proxy validates the substrate is non-broken at the user-surface altitude; real-user shipping is the next-stage event. Eric is an OK fallback if synthetic-proxy is judged insufficient.

**Surfacing for ratification.** Owner picks. If Eric, owner pings Eric (out-of-band) + builder waits for Eric's run before V070.6 closes. If new external user, owner arranges. If synthetic proxy, builder runs the probe per the dispatcher's persona-stipulation discipline.

### Q3 — Implementation-tier picker fold-in vs separate amendment

The FIDRAFT entry (Telegram 10575) explicitly notes "composes with v0.6.0 non-tech-user surface" — the tier conversation IS part of the non-tech-user UX shape. Two options:

- **Option A — FOLD IN to v0.7.0.** Adds AC.V070.7 (per §4 above). Tier conversation becomes part of the V070.6 outcome-altitude probe (the user's ask exercises tier negotiation); cleaner end-to-end probe; tighter coupling between narration (V070.1) + tier picker (V070.7) — both surface the persona's reasoning-trace pattern.
  - Cost: +1-2 hr AI-time per the FIDRAFT estimate; total v0.7.0 AI-time band shifts from 5-10 hr to 6-12 hr.
- **Option B — SEPARATE AMENDMENT.** Tier picker ships as its own v0.7.x amendment after v0.7.0 lands. Cleaner v0.7.0 scope; shorter cycle.
  - Cost: V070.6 outcome-altitude probe ships without exercising the tier conversation (the AC's "no ODD vocabulary" check still passes; but the probe doesn't exercise the natural-language tier negotiation that the FIDRAFT entry calls out as critical for "loam-as-consulting-tool credibility").

**My recommendation: FOLD IN (Option A).** The tier conversation is structurally part of the non-tech-user surface — the FIDRAFT entry's own composition note acknowledges this. The +1-2 hr AI-time delta is small; the coupling to V070.6 is real. Separating would ship v0.7.0 with a known-incomplete user-surface that needs immediate v0.7.x follow-on; fold-in ships the surface complete.

**Surfacing for ratification.** Owner picks. If FOLD IN, V070.7 is in scope + AC count is 7+S (=8); if SEPARATE, V070.7 is removed + the tier picker dispatches as its own plan-doc post-v0.7.0-seal.

## §10 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — multi-component MINOR scope; tight component fence; meaningful but bounded surface.

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc authoring (this file) | 30-45 min | 38 min |
| AC.V070.1 — light-touch narration SKILL + tests | 60-120 min | 90 min |
| AC.V070.2 — channel-slot read path + Stop-hook contributor + tests | 90-150 min | 120 min |
| AC.V070.3 — corpus-override doc + reference example + integration probe | 60-90 min | 75 min |
| AC.V070.4 — memory-doc template + `loam new-memory` orchestration + tests | 60-90 min | 75 min |
| AC.V070.5 — real session-transcript capture + publish | 60-180 min | 120 min (depends on Q2 reference-user availability) |
| AC.V070.6 — outcome-altitude probe authoring + execution | 90-180 min | 135 min |
| AC.V070.7 — tier-picker doc + SKILL + fixture (CONDITIONAL on Q3 fold-in) | 60-120 min | 90 min |
| Plan-doc §13 backfill + STATE/roadmap admin + HARD smoke writeup | 30-60 min | 45 min |
| **Total v0.7.0 build (Q3 = FOLD IN, monolith)** | **8-13 hr** | **~10.7 hr** |
| **Total v0.7.0 build (Q3 = SEPARATE, monolith)** | **6.5-11 hr** | **~9.2 hr** |

The original roadmap entry estimated 5-10 hr midpoint ~7 hr. **Plan-time revision: 6.5-13 hr midpoint ~9-11 hr.** The original estimate appears to have underweighted the V070.6 outcome-altitude probe (90-180 min for real-execution probe authoring + run, not 30-60 min for in-test verification) and the V070.5 transcript capture (which depends on Q2 reference-user availability). Revised band is more honest.

**If Q1 = SPLIT,** AI-time bands per sub-cycle:
- v0.7.0 (V070.1 + V070.2 + V070.4 + V070.S): 4-6 hr
- v0.7.1 (V070.3 + reference example): 60-90 min
- v0.7.2 (V070.5 + V070.6 + V070.7 if folded): 3.5-7 hr

Total split AI-time is comparable to monolith (8.5-14 hr) plus per-sub-cycle bookkeeping overhead (~30 min × 3 = ~90 min); split adds ~10-15% bookkeeping cost.

Owner gate-review separate (ratify plan-doc shape before build dispatch + ratify dogfood publish per ASK-FIRST + ratify Q1/Q2/Q3 before any cycle starts).

## §11 — Authority chain

- `docs/release-roadmap.md` §4 v0.6.0 entry (the prior label; now derives v0.7.0 per Q2 plan-author ruling) — source of the AC sketch + objective sentence.
- `docs/release-versioning-policy.md` §1.0.0 — v1.0 quality-bar event definition; v0.7.0 makes criterion #2 reachable.
- `docs/VALUE_PROPOSITION.md` — translation-layer prime objective.
- `docs/FUTURE_IDEAS.md` Idea 2 (light-touch education), Idea 22 (memory-doc template), Idea 25 (channel slot), Idea 26 (corpus override) — source-item authority for the four core ACs.
- `docs/FUTURE_IDEAS_DRAFT.md` Telegram 10575 capture (implementation-tier picker) — source-item authority for V070.7 (conditional).
- `docs/STATE.md` v0.6.0 row — predecessor-state.
- Memory rules: `feedback_test_outcome_altitude_required.md` (V070.6 + risk-band), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_summarize_and_surface_decisions.md` (Q1/Q2/Q3 surfacing pattern), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #7), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§10).
- Lens 4 (scope-confidence) — plan authored at high confidence on the outcome shape (non-tech-user end-to-end; well-defined per VALUE_PROPOSITION) + medium confidence on the optimal AC granularity (Q1 surfaced for owner ratification rather than ruled silently); scope is correspondingly tight at outcome layer + loose at split-vs-monolith layer.

## §12 — §status

**Build cycle:** TBD — pending owner ratification of plan-doc shape + Q1 (monolith vs split) + Q2 (reference user) + Q3 (tier picker fold-in).

**Plan-doc authoring commit:** TBD-AT-COMMIT (this file lands uncommitted per dispatch instructions; owner reviews before any commits).

### AC verdict matrix

(Backfilled at build time per the v0.6.0 / v0.4.x precedent.)

| AC | Verdict | Evidence |
|---|---|---|
| AC.V070.1 — Light-touch narration | TBD | TBD-AT-BUILD |
| AC.V070.2 — Channel config slot honored | TBD | TBD-AT-BUILD |
| AC.V070.3 — Corpus override pattern | TBD | TBD-AT-BUILD |
| AC.V070.4 — Memory-doc template + new-memory verb | TBD | TBD-AT-BUILD |
| AC.V070.5 — Real session-transcript demo | TBD | TBD-AT-BUILD |
| AC.V070.6 — Outcome-altitude stranger-clone probe | TBD | TBD-AT-BUILD |
| AC.V070.7 — Implementation-tier picker (CONDITIONAL on Q3) | TBD or REMOVED | TBD-AT-BUILD |
| AC.V070.S — Seal-diff discipline | TBD | TBD-AT-BUILD |

### AI-time actuals

Backfilled at seal-cycle close per `feedback_duration_estimation_rubric` log-actuals discipline.

### Halt-and-surface findings

Backfilled at build time.

## §13 — Method decisions

Backfilled at build time per the v0.6.0 / v0.4.x precedent.

(D-V070.1 / D-V070.2.{a,b} / D-V070.4 / D-V070.6 / D-V070.7 — see §5 for the open builder rulings.)

---

*Plan-doc authored 2026-05-09. Ready for owner ratification on Q1/Q2/Q3 + plan-doc shape; build-cycle dispatch awaits ratification. Predecessor v0.6.0 awaits publish per ASK-FIRST; v0.7.0 build is build-forward-eligible per `feedback_build_forward_on_publish_pending` (sub-cycle-dispatch can proceed once v0.7.0 plan-doc is owner-ratified, regardless of v0.6.0 publish status, because component fences are non-overlapping).*

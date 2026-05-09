# Loam Release Roadmap

**Effective:** 2026-05-08.
**Status:** Forward-looking; ratified versions land here as `STATE.md` rollups when they ship.
**Composes with:** `docs/release-versioning-policy.md` (SemVer commitment), `docs/odd-semver-pinning.md` (ODD ↔ SemVer pinning), `docs/VALUE_PROPOSITION.md` (prime objective), `docs/odd-llm-grounding.lean.md` (methodology).

This file replaces the prior per-release master plans (the v0.1.x roadmap fragments and the ODD-rebuild master plan). The canonical forward-looking artefact is one file.

---

## §1 Framing

### Versions are objective targets, not feature lists

Every minor version is named by a single sentence — what a user can newly do with loam that they could not do before. Multiple ideas, fixes, and components roll up under that sentence. Anything that does not ladder up to the version's objective gets pushed to a later minor or to backlog.

The sentence is the version's identity. Acceptance criteria and constraints follow. This file does not enumerate features against versions; it enumerates outcomes against versions and lets the source items ladder up.

### Loam's prime objective shapes every entry

Loam exists to help people use LLMs to **build software** (`docs/VALUE_PROPOSITION.md`). The Dev/SDLC plugin is "Software Development Life Cycle" — `extraction is a scaffold` that places initial boundaries on what gets built; **working code is the deliverable**, not the extracted contract. Roadmap entries from v0.4.0 onward are framed against that deliverable shape.

### Architectural constraints (apply to every entry)

These are non-negotiable across the roadmap unless the policy doc itself changes:

- **No Anthropic API key anywhere in loam.** All LLM-routed paths use `claude -p` against the user's Claude Max OAuth keychain (memory rule `feedback_no_anthropic_api_key.md`, captured 2026-05-05 after the v0.2.5 C4-pivot ruling). Features that would require API-key access do not land in loam — they go to backlog.
- **`claude -p` invocations carry `--strict-mcp-config` + empty MCP config tempfile** (precedent: workspace-sync resolver client; v0.2.5 corrective C5 propagation; AC.WSα.8). Every loam subprocess that forks `claude -p` MUST scrub MCPs to avoid killing the parent's Telegram bot or other MCP servers.
- **ODD §2.5 — every line of code/branch/test maps to a named AC.** Methodology constraint. Every roadmap entry produces ACs, not vague "improvements."
- **SemVer commitment** (`docs/release-versioning-policy.md`). MAJOR=breaking, MINOR=new outcome shape, PATCH=defect closure within the most-recent minor's outcome.
- **Subscription-only (Claude Max OAuth)** is loam's distribution shape. Multi-LLM via OpenRouter or any API-keyed router is incompatible with this constraint and stays in backlog.

### How this composes with ODD-SemVer pinning

`docs/odd-semver-pinning.md` defines how ACs (the ODD acceptance-criterion units) bind to SemVer digits — VERIFIED-banded ACs in the public surface are MINOR-stable; PLAUSIBLE/HYPOTHESISED ACs are MINOR-unstable; band promotions/demotions are MINOR bumps. This roadmap document supplies the **objective sentence** for each minor; the pinning document supplies the **stability contract** within each minor.

---

## §2 Shipped (concise summary, v0.1.0 → v0.4.0)

Pulled from `docs/STATE.md`. Each entry is the minor's objective sentence + the seal anchor.

| Version | Objective sentence | Anchor |
|---|---|---|
| v0.1.0 | Loam ships publicly at `lukeivers/loam` with the Dev/SDLC plugin as the only v1 plugin, dormancy-renamed pre-launch, all pre-publish blockers closed (memory pipeline, M9 substitution, fastmcp filter, M1c-corrective). | 2026-05-01 cross-session memory probe gate; M11 dry-run gate. |
| v0.1.6 | Loam workspaces declare a `safety_profile` field with non-tunable production-stake floors and a cost-governance dry-run primitive. | seal `3f1d237`, `88674cb` |
| v0.1.7 | Loam personas, per-project PM, and layered-skill architecture move coordination machinery off the persona's user-visible surface. | seals `3aa20dd`, `73505f0`, `bcf699a`, `122a7c8` |
| v0.1.8 | Loam reverse-extracts ODD contracts (banded ACs + ratification) from Ruby/Rails and JS/TS/Playwright codebases; first 6 dev-sdlc SKILLs auto-discoverable. | seals `c1abda1` … `e4512b9` |
| v0.1.9 | Loam's PR-safety gate engine + override workflow + hook installers + 3 CI templates close the gap between contract drift and merge-time enforcement. | seals `790807d`, `0dc557e`, `3284087` |
| v0.2.0 | Loam keeps the contract alive (continuous codebase-watch + scheduling) and captures user-driven SKILLs (auto-skill-capture MVP, 3 of 6 triggers). | seals `6fef2f1`, `549fe88` |
| v0.2.1 | Loam install-time onboarding ritual hardens the first-run experience and the promotion-rubric mechanism makes SKILL graduation/demotion observable. | seals `55640b1`, `298172e`, plus correctives `ad42314`, `d82a43b` |
| v0.2.2 | Loam's ODD grounding doc auto-loads at every fresh DEV-mode session; dispatch-brief authoring SKILL propagates 5 principles to sub-agents. | seal `5eda09d` |
| v0.2.3 | Loam extracts contracts at the **objective altitude** rather than the symbol altitude (multi-source synthesis: README + design docs + tests + survey + code patterns). | seals `9b9f87c`, `857749c`, `f78bb36` |
| v0.2.4 | Loam runs a completeness interview, computes a gap analysis, and produces a "what should I build next?" output ranked against extracted objectives. | seals `d42ace9`, `9d15333`, `064cc2e` |
| v0.2.5 | Loam's reverse-ODD pipeline runs HARD smoke-clean against a real-world codebase (`rd-automation`); the `claude -p` synthesis client replaces the Anthropic SDK; subscription-only architecture verified. | seal `7f41ed0`; tag `v0.2.5` pushed 2026-05-06 |
| v0.2.5.1 | Loam respects user-declared off-limits zones, exposes a configurable synthesis timeout, and cascades capability drops when their target objectives are guarded out. | seals `b1d5f1e` (apply), `7a06034` (§14 backfill) — closes Eric's three F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN findings |
| v0.3.0 | Loam's documented features work as advertised AND loam's terminology is consistent across forward-looking surface — `docs/rebuild/` collapsed (~5300 refs scrubbed); graphiti rip-out + FBE.7 file-backed memory canonical; foundation-docs gap-fill (CLAUDE.md Lens 6/7 + principle-derivation-map port); lint pass clean (`ruff` + F821 sweep); `KNOWN_CROSS_MODE_DEBT` shrinks 1 → 0; F3 + F4 closures; `docs/glossary.md` published (12 canonical terms); feature-honesty audit 100% match post-C6.1; `claude -p --strict-mcp-config` invariant verified 3/3 production sources; ODD-conformance allowlist published (18 entries); HARD smoke GREEN against rd-automation. | Cycles 1–7 + C6.1: apply `e80437b` / seal `459c7fc` (C1); apply `39094ea` / seal `013553e` (C2); apply `ad12cc1` / seal `be48b34` (C3); apply `46fd2a7` / seal `7afb648` (C4); apply `dddaf8d` / seal `542b939` (C5); apply `f8beeaa` / seal `0734ea9` (C6); apply `9864b0a` / seal `58da132` (C6.1); apply `d849aee` / seal `3c6fdd5` (C7) |
| v0.4.0 | Loam ships a code-gen surface (`loam odd-extract <repo> --code-gen`) optimised for **extending an existing repo** — consumes objectives.yaml + gap-inventory.yaml + build-next.yaml + emits a unified diff against the source tree with each commit's `objectives:` block populated (amendment #38 `lifted_from` schema reused); `jsts-playwright-app` outcome-altitude verified end-to-end against real `claude -p` subprocess; substrate composition on Claude Code Routines (`feedback_routines_runtime_layer.md` + 1 example plan-doc) + Code Review (plan-author SKILL section + 1 example) + Outcomes-pattern ADR (`docs/design/odd-vs-outcomes.md` documenting API-key-vs-subscription divergence). **F-DESIGN-1 confirmed empirically at C4 ProgramBench v0 baseline:** Variant A (docs-only feeder → reverse-ODD → ODD-grounded code-gen) **56% (9/16)** vs direct `claude -p` baseline **100% (16/16)** on 3 small tasks; the v0.4.0 surface does NOT (yet) ship cold-start docs-only multi-file code-gen — that surface extension is named in §6 as the v0.4.1 closure path. | Cycles 1–5: apply `a7d1182` / seal `cc2efbb` (C1 code-gen-core, SOFT smoke); apply `b358646` / seal `f031c89` (C2 outcome-altitude verification on jsts-playwright-app); apply `f977185` / seal `2d1e7f0` (C3 substrate composition); apply `fdbdc91` / seal `e5c6246` (C4 ProgramBench v0 docs-only baseline); apply `1733a7d` / seal `7787a22` (C5 release-level smoke gate + ship rollup) |
| v0.4.1 | Loam closes F-DESIGN-1 with three additive sub-fixes inside `plugins/dev-sdlc/odd-extractor/`: **multi-commit-per-task emission** (LLM responses with `===COMMIT===` delimiters yield multiple `CodeGenCommit` records; single-commit responses backward-compat); **from-scratch prompt mode** (auto-detect via `_detect_from_scratch` traversal + explicit `--from-scratch` / `--no-from-scratch` CLI flags; instructs `--- /dev/null` source-side framing + encourages multi-file submissions); **build-next tie-breaker beyond alphabetical** (cluster-size desc + objective-text-length desc inserted between confidence-rank and lex fallback in `_tiebreak_key`). All three sub-fixes verified working in production via the v0.4.1 ProgramBench v0 re-run on the same 3 tasks (calculator + jsonpp + wcclone): all tasks emitted 3 commits each; all diffs use `--- /dev/null` framing; **the C4 jsonpp failure case is closed** — tie-breaker correctly ranked `formatting` over `error-handling` (vs alphabetical's wrong choice in C4); aggregate Variant A pass-rate 62.5% (10/16) RELAXED vs C4's 56%. **F-DESIGN-2 surfaced** (smaller-scope follow-on; `compile.sh` missing in 3/3 runs because the SPEC's "Test interface" section isn't passed into the prompt) — closure path named at §6 as v0.4.2 territory, NOT a v0.5.0 reframe. HARD smoke GREEN against rd-automation (267s Stage 1 wall-clock; 12.57¢ synthesis cost; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along all GREEN; subscription-only invariant preserved). | Single-cycle PATCH: plan-doc `0b2a890` + manifest baseline-update `a10350e`; sub-fix 1 (multi-commit) `1b7160c`; sub-fix 2 (from-scratch + CLI) `c27c711`; sub-fix 3 (tie-breaker) `bb62f86`; experiments doc append `946424d`; apply `450c787`; seal TBD-AT-SEAL |

**Total shipped:** 14 minor + 2 patches. v0.1.0 → v0.4.1 published. v0.3.0 ships META-FRAMEWORK foundation; v0.4.0 ships code-gen-from-objectives optimised for extend-existing-repo; v0.4.1 closes F-DESIGN-1 (multi-commit + from-scratch + tie-breaker); F-DESIGN-2 surface deferred to v0.4.2 candidate per §6 owner-action-line.

---

## §3 Active version

v0.4.0 SHIPPED + v0.4.1 patch SHIPPED (collapsed to §2). Next: **v0.5.0** binary-usage observation harness — see §4 v0.5.0 for objective + ACs + dependencies. Concurrent candidate path: **v0.4.2 patch** closing F-DESIGN-2 (compile.sh / SPEC test-interface load-bearing in from-scratch prompt) per §6 owner-action-line.

---

## §4 Mapped versions (v0.5.0 → v1.0.0)

### v0.5.0 — Loam builds software from minimal input

#### Objective

> **Loam can take a binary + documentation as input, observe the binary's behavior, reverse-engineer objectives + capabilities + constraints, and produce working source code that passes a behavioral test suite.** The cold-start case — minimal inputs — is the version's deliverable.

**Class:** END-USER

This is loam against ProgramBench's full input shape: binary + docs, no source. The new component is the binary-usage observation harness.

#### Constraints

- Binary-usage observation harness sandboxes execution (Docker-shaped or equivalent safety boundary). Per programbench-loam-benchmark-v0.md §"What this is NOT" — non-trivial.
- mini-SWE-agent harness compatibility — loam's code-gen pipeline produces output compatible with ProgramBench's evaluation harness.
- ProgramBench leaderboard submission is **the action of submitting**, not a UI feature. Submission constitutes evidence of v0.5.0's outcome.

#### Acceptance criteria

- **AC.V050.1 — Binary-usage observation harness.** New component (likely under `framework/` or as a dev-sdlc plugin extension): runs binary with sample inputs, captures stdin/stdout/exit codes/file effects/network behavior, produces structured evidence-row-equivalents for the reverse-ODD pipeline. Sandboxed.
- **AC.V050.2 — Binary-feeder mode for odd-extractor.** odd-extractor accepts evidence rows from the binary harness as a third input source alongside source-files + docs.
- **AC.V050.3 — mini-SWE-agent compatibility.** Loam's code-gen output is consumable by mini-SWE-agent's evaluation harness without manual intervention.
- **AC.V050.4 — ProgramBench v0.5 submission (Variant B).** Run docs+binary feeder → reverse-ODD → ODD-grounded code-gen on 3-5 ProgramBench tasks. Score: behavioral test pass rate. Submitted to ProgramBench leaderboard. Report at `docs/experiments/programbench-v0-5-submission.md`.
- **AC.V050.5 — Outcomes-pattern stack documentation.** When users have both `claude -p` subscription AND API-keyed Outcomes access, the pattern document names how to stack ODD authoring + Outcomes runtime grading.

#### Source items

- ProgramBench × loam v0 Variant B (docs + binary-usage feeder)
- Binary-usage observation harness (programbench-loam-benchmark-v0.md §3)
- Outcomes-pattern stacking (claude conference features research)

#### Estimated AI-time

- Binary-usage observation harness: 3-6 hours (sandboxed; new component)
- mini-SWE-agent compatibility surface: 60-120 min
- ProgramBench v0 Variant B run on 3-5 tasks: 75-150 min
- Score aggregation + report + leaderboard submission: 15-30 min

**Total v0.5.0 AI-time: 5-10 hours**, midpoint **~7 hours**.

#### Dependencies

- v0.4.0 (code-gen-from-objectives wired; ProgramBench docs-only baseline established as comparison).

---

### v0.6.0 — Loam is usable by a non-technical user from fresh install through working software

#### Objective

> **A non-technical user with a fresh install can describe what they want to build, answer light-touch onboarding questions, and reach working software output without invoking technical concepts (objectives / capabilities / acceptance criteria) directly.** The translation layer (per VALUE_PROPOSITION.md) handles the methodology shape internally.

**Class:** END-USER

This is the version where loam's value proposition (helping non-tech users use AI to build software) becomes empirically demonstrable. One real non-technical user shipping real software is a 1.0.0 gate — v0.6.0 makes it possible.

#### Constraints

- No technical-concept exposure required from the user surface (user never has to type "objective" or "AC"). Internal model stays ODD-shaped per Idea 6.
- Onboarding flow scales from 8-question survey (Eric-style) to 15-question full ritual (per AC.ONBOARD.1-15) per user signal.
- Channel config (`primary_channel` slot per Idea 25) is a workspace-level setting honored by every persona reply.
- Workspace-specific corpus overrides (Idea 26) supported by all reader paths via the `_resolve_corpus_path` fall-through.

#### Acceptance criteria

- **AC.V060.1 — Light-touch education flow.** Idea 2 — ambient narration of decisions ("I made this a scheduled task because…"); user-survey-tunable verbosity; structural-not-advisory.
- **AC.V060.2 — Channel config slot.** Idea 25 — `<workspace>/.pos/channel.json` (or persona contract field); Stop-hook contributor refuses terminal-reply when `primary_channel = telegram` and the message is a user-reply.
- **AC.V060.3 — Workspace corpus override pattern.** Idea 26 — documented; one reference override (e.g., a domain-specific persona prompt) shipped as canonical example.
- **AC.V060.4 — Memory-doc skeleton template.** Idea 22 — third member of the template family (dispatch-template + plan-doc-template + memory-doc-template); `loam new-memory <slug>` orchestration parallel to `loam new-plan <slug>`.
- **AC.V060.5 — Real session-transcript demo.** TaskList item #30 — reference transcript captured + published; demonstrates a non-tech user (or proxy) reaching working software output through the V060.1 flow.
- **AC.V060.6 — Outcome-altitude AC for non-tech user flow.** End-to-end test: stranger-clone → onboarding → request → working output, no technical concepts exposed in the user surface.

#### Source items

- Idea 2 — light-touch education
- Idea 25 — workspace-level default-conversation-channel config slot
- Idea 26 — workspace-specific corpus overrides via reader fall-through
- Idea 22 — memory-doc skeleton template
- TaskList item #30 — real session-transcript demo

#### Estimated AI-time

- Idea 2 light-touch education flow: 2-4 hours
- Idea 25 channel config + Stop-hook contributor: 60-120 min
- Idea 26 documentation + canonical reference override: 30-60 min
- Idea 22 memory-doc template + new-memory orchestration: 60-90 min
- Real session-transcript capture + publish: 90-180 min (depends on user-availability)
- Outcome-altitude AC verification: 30-60 min

**Total v0.6.0 AI-time: 5-10 hours**, midpoint **~7 hours**.

#### Dependencies

- v0.5.0 (working-software output is a precondition for non-tech-user reaching working-software output).

---

### v0.7.0 — Loam's principle foundation is named and structurally enforced

#### Objective

> **Loam's design principles (the three Lenses, plus the canonical principle map at `framework/docs/design/principle-derivation-map.md`) are named primitives in the codebase, structurally enforced via hooks/skills/Stop-hook contributors, not advisory prose.** Drift from declared principles becomes a mechanical violation, not a discipline ask.

**Class:** META-FRAMEWORK

This is the structural-enforcement substrate — A1 expanded.

#### Acceptance criteria

- **AC.V070.1 — FR.1 / FR.2 / FR.3 named primitives.** TaskList items #34 / #35 / #36 (research → plan → first implementation): the three frame-rules are declared in code, not documents-only.
- **AC.V070.2 — F6 enforcement substrate.** TaskList #37 — the lens-conflict resolution four-step process becomes a Stop-hook contributor (or equivalent structural surface).
- **AC.V070.3 — Idea 1 Step 3 enforcement mechanism.** Research-plan template requires all four research questions; gate refuses to advance if any is empty.
- **AC.V070.4 — Idea 21 persona own-behaviour structural enforcement.** Stop-hook contributor scans outbound replies for permission-asking patterns + rewrites or halts.
- **AC.V070.5 — Idea 8 structural context-load gate.** Mechanical: the primary persona cannot dispatch until relevant design docs are loaded.
- **AC.V070.6 — Idea 9 workspace-slug collision detection.** Install-time + bootstrap-time checks; disambiguation knob.
- **AC.V070.7 — Design notes #26 (terminology drift detection).** Stop-hook contributor warns on dossier-claims that disagree with git log / plan-doc §14 / manifest.
- **AC.V070.8 — Meta-decision-haiku SKILL.** A SKILL that invokes Haiku as an impartial third-party decision-maker for borderline rule-application calls (plan-doc-needed; dispatch-background-vs-inline; smoke-required-or-skippable). Tightly scoped trigger list to avoid death-by-latency. Composes with the structural-enforcement substrate as the "rule applies here?" arbiter for cases too borderline for strict rubrics yet too biased for unaided persona judgment. Captured 2026-05-08 per Luke's framing — primary persona alone tends to bypass when it thinks bypass will please the owner; Haiku has no skin in the game.

#### Source items

- TaskList #34 (FR.1), #35 (FR.2), #36 (FR.3), #37 (F6)
- Idea 1 Step 3 (three-lens enforcement programme)
- Idea 21 (persona own-behaviour structural enforcement — already 4+ documented failure modes)
- Idea 8 (structural context-load gate)
- Idea 9 (workspace-slug collision detection)
- FIDRAFT structural-enforcement candidates (default-action-verb rewrite, dossier dedup, end-of-turn trait reflection)
- Meta-decision-haiku SKILL (per Luke 2026-05-08; composes with claude_print_client primitive; ~30-60 min AI-time for the SKILL build, plus calibration of the trigger list)

#### Estimated AI-time

- FR.1 / FR.2 / FR.3 / F6 (4 named-primitive amendments): 4-8 hours total
- Idea 1 Step 3 mechanism: 60-120 min
- Idea 21 Stop-hook contributor: 90-180 min
- Idea 8 structural gate: 90-180 min
- Idea 9 collision detection: 60-120 min
- Misc structural enforcement candidates: 60-120 min

**Total v0.7.0 AI-time: 9-17 hours**, midpoint **~13 hours**. Largest minor in the roadmap; structural-enforcement work touches many surfaces.

#### Dependencies

- v0.6.0 (non-tech user surface stable enough to add structural enforcement on top of).

---

### v0.8.0 — Loam catches code that contradicts its own contract

#### Objective

> **Negative-alignment detection ships: when generated or edited code drifts from the declared objective, loam surfaces the drift before the user (or CI) sees it as a defect.** Carved out of v0.2.5; deferred until calibration data exists.

**Class:** END-USER

#### Acceptance criteria

- **AC.V080.1 — Negative-alignment detection primitive.** New component (or odd-extractor extension): given a contract + a diff, classify the diff as objective-aligned / objective-orthogonal / objective-contradicting / objective-ambiguous.
- **AC.V080.2 — Calibration data.** ≥50 real-world examples (from rd-automation, jsts-playwright-app, Eric's repos, loam itself) with ground-truth labels.
- **AC.V080.3 — PR-safety gate composition.** Negative-alignment output integrates as a band-tunable signal in the PR-safety gate; production-stake profiles HARD_BLOCK on objective-contradicting; dev profile WARN.
- **AC.V080.4 — Outcome-altitude AC.** End-to-end test against real PR diffs.

#### Source items

- v0.2.6+ negative-alignment detection (deferred-from-v0.2.5)

#### Estimated AI-time

- Detection primitive: 4-8 hours
- Calibration data collection + labeling: 90-180 min
- PR-safety integration: 60-120 min
- Outcome-altitude AC: 60-120 min

**Total v0.8.0 AI-time: 7-13 hours**, midpoint **~10 hours**.

#### Dependencies

- v0.7.0 (structural enforcement substrate provides the hook surface).
- Calibration data depends on real-world repo usage (Eric, ProgramBench experiments, loam itself).

---

### v0.9.0 — Loam's deep personalization through interaction capture

#### Objective

> **Loam captures interaction patterns over time and synthesizes them into a durable user-profile artefact that informs persona behavior — without requiring the user to teach the system anything explicitly.** Per VALUE_PROPOSITION's "trust compounds in one relationship."

**Class:** END-USER

#### Acceptance criteria

- **AC.V090.1 — Interaction capture surface.** Per Idea 4 — session transcripts (or decision-relevant subset), preferences (stated or inferred), patterns observed, reactions to system outputs.
- **AC.V090.2 — Synthesis layer (separate from raw memory).** Periodic update of a structured user-profile artefact at a stable workspace path.
- **AC.V090.3 — Privacy + audit + deletion controls.** Per Idea 4's required guarantee — every interaction visible on request; user can delete.
- **AC.V090.4 — Proactive-suggestion primitive.** Per Idea 5 — surface 1-3 suggestions per week (frequency-tunable); each dismissable without cost.
- **AC.V090.5 — GLiNER2 evaluation under volume data** (CONTINGENT). Per Idea 7 — graphiti-class re-implementation with local NER for high-volume paths; scope **only if volume data justifies**.

#### Source items

- Idea 4 (deep personalization through interaction capture)
- Idea 5 (proactive suggestions grounded in user profile)
- Idea 7 (GLiNER2 — contingent on volume data; may stay backlog)

#### Estimated AI-time

- Interaction capture surface: 3-6 hours
- Synthesis layer: 2-4 hours
- Privacy + audit + deletion: 60-120 min
- Proactive-suggestion primitive: 2-4 hours
- GLiNER2 (CONTINGENT): 4-8 hours **OR backlog**

**Total v0.9.0 AI-time: 8-14 hours non-contingent**; midpoint **~11 hours**. +4-8 hours if GLiNER2 activates.

#### Dependencies

- v0.8.0 (memory FBE.7 stable + production usage long enough to have interaction volume).

---

### v0.10.0+ — Plugin suite expansion (one minor per plugin)

#### Objective shape

> **Loam's plugin ecosystem grows beyond Dev/SDLC.** Each new plugin gets its own minor version with its own objective sentence and ACs.

**Class:** END-USER

Per Idea 3 — the plugin candidates are: project/task management overlay, communications plugin, knowledge management, finance/household-ops, creative/long-form, health/habit tracking, trading/quant research, legal/compliance.

**Plugin selection discipline (per Idea 3):** do not ship all eight. Pick two or three that maximise early loam-v2 value AND prove the plugin ecosystem; let the community build the rest.

**Sequencing: highest-leverage first.** Per Luke's prior directive, project/task management overlay (the owner's named example) and communications plugin (Gmail + Calendar MCP composition) are likely candidates for v0.10.0 and v0.11.0. Final selection happens at v0.10.0 plan time, not now.

#### Estimated AI-time per plugin minor

- 8-15 hours per plugin (range per Idea 3 per-candidate complexity; some plugins like communications compose on existing MCP surface and run cheaper).

#### Dependencies

- v0.9.0 (deep-personalization surface gives plugins a richer user model to compose on).

---

### v1.0.0 — Loam is stable

#### Objective

> **All loam-documented features work as advertised; one real non-technical user has shipped real software with loam; backwards-compatibility committed for 6 months minimum; plugin contract is stable.**

**Class:** MIXED

Per `docs/release-versioning-policy.md` §"When 1.0.0 ships." This is a quality-bar event, not a calendar event.

#### Acceptance criteria (the four named criteria from the policy)

- **AC.V100.1 — All documented features work as advertised.** Stranger-clone audit.
- **AC.V100.2 — One real user has shipped real software with loam.** Not a fixture; a real maintenance-burden codebase.
- **AC.V100.3 — Backwards-compatibility commitment.** No breaking changes for 6 months minimum from 1.0.0 ship date.
- **AC.V100.4 — Plugin contract is stable.** Third-party plugins authored against 1.0.0 work through the 0.x compatibility window.

#### Estimated AI-time

- Audit + verification + tag dance: 4-8 hours.
- Real-user-shipped-real-software is **out-of-roadmap** time (depends on adoption + user availability; not AI-time).

#### Dependencies

- v0.10.0+ to whichever-version-stabilizes-the-plugin-contract.
- Real-user adoption (external dependency, not an AI-time line).

---

## §5 Backlog reference

The `maybe-someday` list. Items here are not committed to any version; they activate when their named trigger fires (or stay deferred indefinitely).

**Authoritative source:** `docs/FUTURE_IDEAS.md` (collapses to `docs/FUTURE_IDEAS.md` per v0.3.0 AC.V030.8) + `docs/BACKLOG.md`.

### Items explicitly in backlog (not roadmap)

- **Graphiti re-implementation** (Luke's explicit ruling 2026-05-08). Graphiti rip-out is roadmap (v0.3.0); re-implementation is backlog. Trigger: if FBE.7 file-backed approach proves operationally inadequate at production-stake usage.
- **Idea 7 GLiNER2** — depends on volume data; conditionally folded into v0.9.0 above. If volume data does not materialize, stays backlog.
- **Multi-LLM via OpenRouter** (formerly TaskList #52, completed as research). Contradicts the Claude Max subscription-only architecture. Backlog. Trigger: only if loam's distribution model itself changes.
- **Idea 13 sub-plan G — M-GMP plugin-shaped graphiti.** Graphiti class. Backlog with the broader graphiti category.
- **Idea 11 — amendment-chain reseal convention.** Deferred; no concrete trigger. Trigger: when a component's amendment chain feels unwieldy.
- **Idea 14 — path-mismatch comprehensive resolver.** Deferred under Idea 13's multi-workspace umbrella. Trigger: sub-plan C reactivation (multi-workspace cycle).
- **Idea 15 — `pos_paths` helper.** Folds into Idea 14 if/when activated. Trigger: a fourth consumer of `TRACKER_DB_FILENAME` arrives, OR sub-plan C reactivation, OR a third hard-coded sibling constant.
- **Idea 16 — tracker public API for source-commit rewriting.** Deferred. Trigger: a fourth tracker SQLite consumer OR the next tracker amendment touching `lifted_from`'s shape.
- **Idea 17 — dispatch-template ↔ persona-tracker composition.** Stretch. Trigger: when both surfaces stabilize AND a concrete dispatch shape benefits.
- **Idea 18 — reusable integration-test harness extraction.** Trigger: a second integration-test pattern surfaces.
- **Idea 19 — scaffold-runner observability.** Small. Trigger: sub-plan E activation OR a second silent-failure investigation OR a future scaffold-runner amendment.
- **Idea 23 — research-dispatches scope-fence pre-filter.** Trigger: next non-trivial research-then-build amendment cycle (could fold opportunistically into v0.7.0).
- **Idea 24 — Bash-tool eval-wrapper hazards.** Trigger: third Bash-tool quirk OR structural-enforcement programme adds a fifth A-amendment slot.
- **Apply FBE.7 to pos3** (TaskList #22). Operational, not loam-codebase. Backlog as operational-task; not a version line.
- **Workspace-sync follow-on Bundle α + β residuals** (post-#56 FIDRAFT entries that weren't graduated). Trigger: workspace-sync cost re-emerges as a real bottleneck.
- **BACKLOG.md "held for post-first-release" decay-retention patches.** Six items, per `decay-retention-analysis.md`. Trigger: explicit prioritization vs roadmap items.

### Borderline classifications surfaced for owner review (judgment calls; F2 RF)

These items I classified differently than the original sketch, or where the sketch didn't speak — surfaced for ruling rather than silently committed.

1. **Idea 20 (LLM-as-classifier+verifier meta-pattern).** Already operationalized in workspace-sync Bundle α.2 + memory rules. **My call: NOT a roadmap entry.** It's a meta-pattern, not a feature. Should compose into every v0.4.0+ entry that involves LLM-routed transformations. **Surfacing:** ruling needed if you want this elevated to a named v0.X primitive (a "classifier+verifier" framework component) — currently absent from the roadmap.
2. **Idea 6 (ODD as default framing inside conversations).** Already operational via v0.2.2 ODD grounding propagation foundation. **My call: NOT a separate roadmap entry; subsumed.**
3. **Idea 12 (OSS launch).** Already shipped as v0.1.0+. **My call: shipped, not roadmap.**
4. **Idea 13 (two modes + multi-workspace umbrella).** Active part shipped (sub-plans A/E/B/F); deferred parts (C/D/G) fold under multi-workspace umbrella. **My call:** the deferred parts go to backlog under the "Workspace-sync / multi-workspace" trigger. If multi-workspace becomes a stated objective for any future minor, those re-activate. Currently no minor names multi-workspace; surfacing for ruling.
5. **Idea 10 (Project rename to loam).** Already shipped. **My call: shipped, not roadmap.** Loam-aligned-name terminology consistency pass (v0.3.0 AC.V030.7) is the residual.
6. **TaskList items #8, #9, #10, #11.** I do not have the explicit text for these; they are referenced in the dispatch brief by number alone. Best-effort reading: if these correspond to FUTURE_IDEAS Ideas 8, 9, 10, 11 — they are mapped in this roadmap (#8 → v0.7.0; #9 → v0.7.0; #10 → shipped via Idea 10; #11 → backlog). **Surfacing:** if the TaskList numbers reference different items, the mapping needs correction at owner-review time.
7. **TaskList items #55, #34-37.** #55 is referenced in the dispatch brief as a discussion item; I have not seen its explicit text. #34-37 → v0.7.0 (FR.1/FR.2/FR.3/F6 named primitives). **Surfacing:** #55 needs explicit text to classify.
8. **`KNOWN_CROSS_MODE_DEBT` shrinkage.** Sketch placed it in v0.3.0; I agreed and kept it there. F2 RF signal: this is technically debt, not a forward-looking outcome — could equally well live as a perpetual lint-pass item (composes with v0.3.0 AC.V030.6). I left it as AC.V030.10 because the discrete shrinkage event is observable; alternative is to fold into AC.V030.6 lint pass. **Surfacing:** structural choice; either resolution is fine.

---

## §6 External actions (non-version work)

These items are real work but do not name a version's outcome shape. They live here so the roadmap is complete, not just version-shaped.

| Action | Trigger | Notes |
|---|---|---|
| **Boris paper push** | Captured as session-discussion item; calibration anchor (13min wall-clock at ~76 tool calls per duration-estimation rubric). | Owner-action; not AI-routed in the version path. |
| **Eric re-engagement** | Owner directive 2026-05-06 ("ignore eric, he's busy at his real job"). v0.2.5.1 closes Eric's three findings. Re-engagement is owner-driven, not version-gated. | Surface for ruling: should v0.6.0 (non-tech user) wait on Eric re-engagement, or proceed against a synthetic non-tech-user proxy? |
| **ProgramBench leaderboard submission** | v0.5.0 AC.V050.4. The act of submitting is the action. | Submission is what makes v0.5.0's outcome public. |
| **Public-remote tag pushes** | Each minor's tag push is owner-gated. v0.2.1 / v0.2.2 / v0.2.3 / v0.2.4 / v0.1.7 / v0.1.8 / v0.1.9 / v0.2.0 currently sit as local releases per their respective STATE.md entries. | Tag push is a per-minor owner action, not a roadmap line. The roadmap names what each minor delivers; the policy doc names tag dance shape. |
| **GitHub Releases marked --latest** | Per `docs/release-versioning-policy.md` §Tagging. | Per-minor; not a roadmap line. |
| **Dispatcher-side smoke verifications** | Some ACs (V025.4 outcome-altitude, V025.5 telegram-MCP isolation outcome-altitude) require parent-session verification not visible from sub-agents. | Per-minor; documented in each minor's plan-doc. |
| **Docker-equivalent / fresh-machine FBE.7 stranger-clone verification** | v0.3.0 Cycle 6 audit (`docs/v0-3-0-feature-honesty-audit.md` §4 + §9.3) closed production-CLI altitude via `framework/primary-persona/tests/test_AC_FHA_6_stranger_clone_fbe7_outcome.py`; cross-process / fresh-install / fresh-user-account altitude verification still pending. Trigger: owner brings Docker Desktop up OR runs probe on a fresh machine. | On positive verdict, AC.FHA.2 lifts from PASS-WITH-OWNER-ACTION-LINE to PASS; on negative verdict, in-cycle fix triggers at the version then active. |
| ~~**F-DESIGN-1 closure (cold-start docs-only multi-file code-gen)**~~ **CLOSED at v0.4.1** | ~~v0.4.0 Cycle 4 ProgramBench v0 baseline confirmed empirically that the v0.4.0 code-gen surface is shaped for *"extend an existing repo"*, NOT *"write from scratch given only docs"* — Variant A 56% (9/16) vs baseline 100% (16/16).~~ **Closed by v0.4.1 patch** (sealed 2026-05-09): three sub-fixes landed (multi-commit-per-task; from-scratch prompt mode with auto-detect + explicit flags; build-next tie-breaker beyond alphabetical via cluster-size + text-length signals). v0.4.1 ProgramBench re-run on the same 3 tasks shows all three structural mechanisms working in production (3 commits per task; `--- /dev/null` framing across all diffs; `formatting` correctly ranked above `error-handling` for the C4 jsonpp failure case). Aggregate Variant A pass-rate 62.5% (10/16) RELAXED vs C4's 56%. Residual gap surfaces as F-DESIGN-2 (smaller-scope; row below). | F-DESIGN-1 architectural mechanism resolved at v0.4.1. See §2 v0.4.1 row + `docs/experiments/programbench-v0-docs-only.md` v0.4.1 re-run section. |
| **F-DESIGN-2 closure (compile.sh / SPEC test-interface load-bearing in from-scratch prompt)** | v0.4.1 patch's ProgramBench re-run (`docs/experiments/programbench-v0-docs-only.md` "v0.4.1 re-run" section) confirmed all three F-DESIGN-1 sub-fixes work as intended in production, BUT the LLM in 3/3 v0.4.1 runs did NOT author `compile.sh` + did NOT consistently match the SPEC's CLI shape (Task 3 wcclone: library-vs-CLI mismatch + multi-line vs single-line output). The from-scratch prompt instructs "create new files" + `--- /dev/null` framing but doesn't pass the SPEC's "Test interface" section as load-bearing context, so the LLM makes reasonable but spec-incompatible choices. Per the v0.4.1 plan-doc verdict bands: 57–74% = YELLOW = partial improvement; this is the structurally smaller residual gap. **Trigger:** owner ratifies the v0.4.2 patch path: pass the SPEC's Test interface section into the from-scratch prompt as load-bearing context, OR author a deterministic post-processor that synthesizes `compile.sh` from emitted source files, OR change the build-next surface to recognize "compile.sh" as a NAMED REQUIRED ARTEFACT in any task whose SPEC references it. | Plausibly v0.4.2 patch (PATCH-class per `docs/release-versioning-policy.md` — defect closure within v0.4.1's surface). Smaller scope than F-DESIGN-1 — one prompt-engineering pass. Ratification gate before patch dispatch. v0.5.0 binary-feeder Variant B is independent. |

---

## §7 Authority + change protocol

This file overrides any prior planning doc that names a version's contents, **except** `docs/release-versioning-policy.md` (the policy doc takes precedence for versioning-rule disputes — this roadmap obeys the policy).

Updates land via amendment-cycle (the same loam amend mechanism used for all sealed components when this roadmap is tracking shipped state). Adding/removing/refining versions requires a plan-doc + manifest, not a doc-only edit, when the roadmap is being treated as a contract. Pre-v0.3.0, edits are prose-only.

When a minor ships, its §3-or-§4 entry collapses into §2 with the seal anchor. That collapse is part of the minor's seal ritual.

---

*Maintained alongside `docs/release-versioning-policy.md` and `docs/odd-semver-pinning.md` as the three durable policy + plan artefacts for loam.*

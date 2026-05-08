# loam v0.1.x roadmap — five releases

**Status:** plan-doc (pre-build, plan-before-code). Authored 2026-05-03 by roadmap-author dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme predecessor:** v0.1.0 just shipped (private at `lukeivers/loam`; public flip pending owner). M11a sweep PASSed; FBE.1–FBE.11 + FBE.6{b,c,d} foldback ladder closed.
**Roadmap horizon:** five releases (v0.1.1 → v0.1.5). v0.2.0 and beyond are out of scope for this doc; deferred items listed in §3.
**Bundling logic:** highest leverage for real users + iteration coherence. NOT optimised for impressing any particular audience. Each release is small enough to ship reliably, large enough to be worth a release-note.

---

## §1. Top-line summary

Five releases. Total AI-time across all of them: **~10–18 h** (midpoint ~14 h). Total owner gate-review time: **~2–3 h** distributed across ~10 review touchpoints.

Cadence is hours-to-days between releases — iterate-in-public friendly, not a months-long programme. Each release ships a coherent bundle: v0.1.1 says what loam is; v0.1.2 fixes what v0.1.0 strangers will trip over; v0.1.3 makes memory pluggable; v0.1.4 makes loam compositional with raw Claude Code; v0.1.5 surfaces who-is-doing-what across the harness.

The story across the cadence: **v0.1.0 shipped a coherent thing; v0.1.x makes it explainable, durable, and composable.** It is not a feature-parity push. It is the first iterate-in-public arc — each release closes friction observed during the prior, and adds one small surface (memory, skills, personas) that the harness needs to stay honest about its own primitives.

| Release | One-line theme | AI-time band | Owner-time |
|---|---|---|---|
| v0.1.1 | Articulate the scaffolding choice plainly | 45–90 min | 5–10 min |
| v0.1.2 | Fix what v0.1.0 strangers will hit | 2–4 h | 30–45 min |
| v0.1.3 | loam composes with raw Claude Code | 3–5 h | 30–45 min |
| v0.1.4 | The harness gets self-aware about roles | 3–5 h | 25–35 min |
| v0.1.5 | Memory becomes pluggable | 3–5 h | 20–30 min |
| **Total** | | **~10–18 h** | **~2–3 h** |

**Reorder applied 2026-05-03 (post-v0.1.1 ship) per owner directive:** memory-pluggable moved to last; the two releases formerly behind it (loam-composes + harness-self-aware) shift forward. Each release's bundle content is unchanged; only the ordering moves. Sequencing diagram in §4 reflects the new order.

Owner-decision bottlenecks are listed in §5; most are minor and default to a recommendation.

---

## §2. Per-release detail

### v0.1.1 — "Articulate the scaffolding choice plainly"

**What this release is about.** v0.1.0's published surface describes *what* loam ships but not *why* loam is shaped the way it is. The choice that most needs articulation is the scaffolding-heavy posture: 15 components, ODD methodology, plan-docs, sealed amendments, dispatch templates. A reader who installs v0.1.0 and skims the docs reasonably asks "why this much structure?" The honest answer is design-shaped, not pitch-shaped — there's a real reason loam looks this way that has nothing to do with positioning. v0.1.1 writes that reason down. One file. No code changes.

**Bundle:**

1. **Design note: `docs/design/why-loam-scaffolds.md`** — articulates the scaffolding choice on its own merits. Provenance: dispatcher-locked content (the parallel agent authoring this note now). This is the single shipping artefact of v0.1.1.

**AI-time band:** 45–90 min (medium docs create, careful framing — done by parallel agent, not this roadmap's responsibility).

**Dependencies:** None (v0.1.0 ship is independent gate; this note is doc-only).

**Gate (closes the release):** owner reads the design note, confirms it sounds like the genuine answer (not a pitch), tags `v0.1.1`, release notes link to the note.

---

### v0.1.2 — "Fix what v0.1.0 strangers will hit"

**What this release is about.** v0.1.0 shipped clean enough to install, but the canonical pos-v2 corpus has a backlog of small known-friction items that any stranger using loam in anger will hit within their first week. None individually warrant a release; together they're a coherent "we noticed everything you'd run into and fixed it" bundle. The orchestrator is the load-bearing item — fixing the launchd plist module-name typo unblocks three sealed amendments (#38/#39/#40 sit on a working orchestrator), and the cost asymmetry (5–10 min fix vs hours of cascade-rework if ripped out) is the decision Luke pre-recorded. The rest are ergonomic — corpus-gate paths, session-start memory probe, the gh-create→push race documentation, the two-copies-of-loam friction explanation, the ack-first persona behaviour, and the three loam-amend tooling improvements that every recent FBE.x agent worked around.

**Bundle:**

1. **V11.A — orchestrator fix.** Edit launchd plist `pos_orchestrator` → `loam.orchestrator`; kill orphan PID 27100; `launchctl kickstart`; add `framework/orchestrator/` to canonical venv editable install list. Provenance: FIDRAFT entry "Orchestrator runtime-provisioning gap — `pos_orchestrator` not installed editable" (2026-04-29).
2. **V11.E — three v0.1.0 follow-on hazards.** (a) Corpus gate `_FALLBACK_BASELINE_PATHS` references dev-only paths (`docs/odd-methodology.md` + `docs/odd-in-loam.md`) — update to public-mode-appropriate paths so sessions stop showing `corpus_gate_state: partial`. (b) `pos_session_start.py` graphiti probe — graceful-skip when `memory-graphiti` is absent (M-FBM workspaces don't run a service). (c) Plist template fix in `framework/orchestrator/ops/launchd/com.loam.orchestrator.plist.tmpl` if not already shipped in v0.1.0 hot. Provenance: multi-release-roadmap §3.1 hazards 2/3/4 (Decisions 2/3/4).
3. **gh-create→push race documentation.** M12 publish-flip operator-instruction docs (oss-v0-1-0-publish-dry-run.md M11a.7 + foldback parent §4 AC.FBE.6.4) gain a 2-3s sleep-or-retry note. Provenance: FIDRAFT entry "`gh repo create` → `git push` race window" (2026-05-03).
4. **Two-copies-of-loam-source friction — docs-explain hedge (option e).** README + getting-started.md gain a short paragraph: "the install clone is disposable; the workspace's framework copy is what actually runs your sessions." This is the option-e hedge; the real fix (option d, PyPI publish) is deferred to v0.2. Provenance: FIDRAFT entry "Two-copies-of-loam-source v0.1.0 stranger-friction" (2026-05-03).
5. **Acknowledge-first persona contract amendment.** Add to primary-persona contract/prompt: "On user input requiring non-trivial work (≥3 tool calls expected, ≥1 background dispatch, decision/judgment vs pure execution, file authoring vs reading, multi-paragraph/multi-question message): the FIRST output is a short ack ('got it — doing X')." Trivial back-and-forth skips the ack. Provenance: FIDRAFT entry "Acknowledge-first on complex requests" (2026-05-03).
6. **loam-amend ergonomic improvements sweep.** Three captured tool ergonomics: (a) `loam amend apply` auto-commits the apply step (or its output explicitly notes "manually commit via …"); (b) `loam amend seal --allow-untracked-globs <pattern>` flag so dirty-FIDRAFT doesn't force stash-then-pop on every seal; (c) `loam amend apply` partner-prefix derives from manifest's `seal_test` path, not from `name` field, so `plugins/<name>/`-located components work alongside `framework/<name>/`. Provenance: FIDRAFT entries "`loam amend apply` does not commit the apply step BY DESIGN" + "`loam amend seal` requires clean working tree" + "`loam amend apply` partner-prefix derivation bug" (all 2026-05-03).

**AI-time band:** 2–4 h total. Per-item: V11.A (~10 min), V11.E (~30 min), race docs (~5 min), two-copies hedge (~10 min), ack-first amendment (~30–60 min, sealed-component touch on primary-persona), loam-amend ergonomics (~60–90 min for three sub-amendments).

**Dependencies:** v0.1.1 ships first (sequencing only — no technical dep). Items within v0.1.2 mostly parallelise; ack-first persona amendment serialises against any other primary-persona-touching work; loam-amend sweep serialises against itself.

**Gate (closes the release):** orchestrator running healthy on Luke's host; corpus-gate output clean for a public-mode session; ack-first behaviour observable in the next live session; three loam-amend ergonomic items each verified in a small smoke amendment cycle. Tag `v0.1.2`.

---

### v0.1.5 — "Memory becomes pluggable"

**What this release is about.** M-FBM (file-based memory) shipped at v0.1.0 with a `MemoryProvider` Protocol stub already authored as the seam for future providers. v0.1.3 widens that Protocol surface and ships the first two non-file-based providers: an Anthropic Memory tool adapter (Lens 1 at its purest — Anthropic's beta `memory_20250818` tool plugged in as a provider), and progressive-disclosure retrieval (L1/L2/L3 — preview-then-expand) that reduces context burn on UPS-hook retrieval. Three small amendments share one Protocol surface, so they ship as one release. Memory-as-pluggable is the load-bearing claim that makes M-GMP (graphiti as plugin, deferred to v0.2) a clean addition rather than a re-architecture.

**Bundle:**

1. **D-3 — widen `MemoryProvider` Protocol surface.** Add `expand(hash)` (D-1 needs it), `content_hash(text)` SHOULD-method (memweave + claude-mem worker pattern), `import_from(adapter_type, source)` (optional; future export/import like Letta `.af`). Doc-only Protocol-docstring widening + method signatures. Prerequisite for D-1 and D-2. Provenance: FIDRAFT entry "File-based memory systems survey — three concrete amendments worth filing" item D-3 (2026-05-01).
2. **D-1 — L1/L2/L3 progressive disclosure for UPS-hook retrieval contributor.** Return ranked list of `{chunk_hash, 200-char preview}` first; persona's `/memory:search` skill or follow-on tool call requests `expand(hash)` for full content; raw transcripts on deep-call. Saves context budget; preview enough for relevance gating, expand only on need. Provenance: same FIDRAFT entry, item D-1.
3. **D-2 — Anthropic Memory tool compatibility adapter.** Adapter maps Memory tool's `view / create / str_replace / insert / delete / rename` command surface against `<workspace>/.loam/memory/`. Lets a Claude API agent (not just Claude Code) point at a loam workspace as its memory directory. Ships as `plugins/memory-tool-adapter/`. Provenance: same FIDRAFT entry, item D-2.

**AI-time band:** 3–5 h total. Per-item: D-3 (~30–45 min, doc-only Protocol widening), D-1 (~45–90 min, contributor return-shape change + skill commands), D-2 (~90–180 min, adapter implementation as new plugin scaffold).

**Dependencies:** v0.1.2 ships first (sequencing). D-3 is internal prerequisite for D-1 and D-2; D-1 and D-2 parallelise after D-3 lands.

**Gate (closes the release):** `MemoryProvider` Protocol surface tests pass for two providers (file-based + Anthropic-tool-adapter); progressive-disclosure verified live on a UPS retrieval; Anthropic-tool-adapter smoke-tested via a minimal Claude API call against a workspace memory directory. Tag `v0.1.3`. Release notes name "memory backends are now pluggable" as the headline.

---

### v0.1.3 — "loam composes with raw Claude Code"

**What this release is about.** Lens 1 (Claude-leverage-first) is the always-on lens that asks "what Claude capability does this lean on or extend?" v0.1.0 ships zero SKILL.md packages — the harness's "translation layer" function is implicit in the persona prompt, not exposed as discoverable skills that compose with raw Claude Code. v0.1.3 fixes this: 3–5 SKILL.md packages capture loam's load-bearing translation patterns AND the first of three planned design-notes (`primary-persona-shape.md`) lands. Coherent bundle: each item is "loam's value made discoverable to people who haven't installed loam." Strangers running raw Claude Code can `pip install loam-skills` and benefit from loam's patterns without committing to the full harness.

**Bundle:**

1. **3–5 SKILL.md packages — `framework/skills/` (or `plugins/loam-skills/`).** Suggested set (final list deferred to plan-author): `memory-recall` (composes with v0.1.3's progressive-disclosure surface), `scope-decompose` (codifies the F3 swarming stopping criterion), `dispatch-with-gates` (codifies scope-only dispatch + halt-and-surface), `onboarding-conversation` (codifies the primary-persona greeting/context-restoration shape), `session-handoff` (codifies the durable-capture rule). Each is a small folder with `SKILL.md` (frontmatter: name + description) + 1–3 reference scripts. Provenance: FIDRAFT entry "Anthropic-perspective recommendation ladder (R.1-R.6)" item R.4 (2026-05-03) + Lens 1 from `framework/CLAUDE.md`.
2. **R.5 design note (1 of 3): `docs/design/primary-persona-shape.md`.** Why a single named persistent identity is a different shape than a multi-agent system or a plain Claude Code session. Composes with v0.1.1's scaffolding-choice note as the second piece of the design-notes voice. Provenance: FIDRAFT entry "Anthropic-perspective recommendation ladder" item R.5 part 1 (2026-05-03).

**AI-time band:** 3–5 h total. Per-item: SKILL packages (~2–4 h for 5 skills + registration + verification), R.5 design note (~45–90 min).

**Dependencies:** v0.1.3 ships first (sequencing). SKILL packages and design-note parallelise.

**Gate (closes the release):** at least 3 SKILL.md packages installable and visible to raw Claude Code; design note reads as builder-explaining-decision (not project-prose). Tag `v0.1.4`.

---

### v0.1.4 — "The harness gets self-aware about roles"

**What this release is about.** Three threads converge here that all touch "who's doing what." First, subagent personas — `.claude/agents/<name>.md` files that prime dispatched background agents with methodology fluency, so dispatches stay scope-only per `feedback_agent_prompts_scope_only`. Currently every dispatch re-derives fluency in-prompt; the persona files amortise that across years of dispatches. Second, the orchestrator-fix from v0.1.2 unblocks three sealed amendments (#38/#39/#40 — objective-tracker schema widening + workspace-bootstrap tracker seed + primary-persona tracker-context contributor) that surface tracker-context into the persona's session-start so the persona knows what background work is in flight. Third, the remaining two R.5 design notes (`file-based-memory-rationale.md` + `odd-for-delegation.md`) close the design-notes voice so a reader can find Luke's reasoning across the load-bearing decisions. Coherent bundle: roles get named (subagents), in-flight work gets surfaced (tracker-context contributor), and design reasoning gets articulated (design notes).

**Bundle:**

1. **V2.B — subagent personas (5 named).** Author 5 `.claude/agents/<name>.md`: `loam-builder` (sealed-component-cycle builder; ODD-fluent; commit-ladder + `loam amend apply` + seal-ritual baked in), `loam-plan-author` (research-grade plan authoring; surfaces named decisions with recommendations; outcome-shape ACs), `loam-researcher` (Lens-1/2/3 research; web-research + codebase-grep; tools restricted to read-only; reports artefact-on-disk + chat-summary), `loam-reviewer` (gate-review for sealed amendments; ODD §2.5 verification; halt-and-surface fluent), `loam-documenter` (public-docs / README / positioning authoring; non-jargon voice; ODD methodology-aware). Provenance: FIDRAFT entry "Subagent-persona priming for dispatched background agents" (2026-05-01).
2. **V11.B — three orchestrator-dependent amendments.** #38 (objective_tracker schema widening), #39 (workspace-bootstrap tracker seed), #40 (primary-persona tracker-context contributor). All three were sealed against the spec but paused on a working orchestrator; v0.1.2's V11.A unblocks them. Lands the empty `[tracker-context]` session-start contributor that's been a placeholder since the foundation audit. Provenance: STATE.md component table "amendment cycle" row + multi-release-roadmap §3.2 V11.B.
3. **R.5 design notes (2 of 3 + 3 of 3): `docs/design/file-based-memory-rationale.md` + `docs/design/odd-for-delegation.md`.** First composes with Anthropic's published "filesystem as memory" prescription (peer-engineer voice, shared instinct). Second defends ODD specifically as the methodology shape that maps to delegation contracts; composes with v0.1.1's scaffolding-choice note. Provenance: FIDRAFT entry "Anthropic-perspective recommendation ladder" item R.5 parts 2 & 3 (2026-05-03).

**AI-time band:** 3–5 h total. Per-item: subagent personas (~60–120 min for 5 files), V11.B (~60–120 min for three sealed amendments — each is small; some can parallelise as plan-author dispatches), 2 design notes (~90–180 min for two careful authored docs).

**Dependencies:** v0.1.4 ships first (sequencing). V11.B requires V11.A from v0.1.2 (orchestrator working). Subagent personas and design notes parallelise. V11.B sub-amendments serialise against each other on the primary-persona/objective-tracker fence but parallel-safe at the plan-author stage.

**Gate (closes the release):** five subagent personas registered and dispatchable; orchestrator surfaces tracker-context in the next live session-start; both design notes read as builder-voice. Tag `v0.1.5`.

---

## §3. What's NOT in v0.1.x — deferred items

These items are real but don't fit the v0.1.x shape (each is too large, requires earlier-release foundations to land first, or carries v0.2-class release ceremony). Listed with brief rationale.

- **M-GMP — graphiti as the first plugin-shaped MemoryProvider** (FUTURE_IDEAS provenance: oss-v0-1-0-publish.md §5 V2.A; multi-release-roadmap §3.3). Substantial new component (relocation + adapter rewire + partition reclassification). Plays best after the Protocol has been exercised across 2 providers (file-based + Anthropic-tool-adapter from v0.1.3) so the surface is stable. **Sequenced for v0.2.0.**
- **V2.C — swarm-runtime primitive** (FIDRAFT provenance: "Swarms 'apply-now' patterns triplet" 2026-05-03; multi-release-roadmap §3.3). Large new component (4–8 h AI critical path). PlannerWorkerSwarm + `CycleVerdict` + drift fresh-start + `EVAL_DIMENSIONS` named-axis judging. F3 principle is currently text-corpus-only; runtime-enforce is the right v0.2 move once the principle has accumulated more usage data. **Sequenced for v0.2.0.**
- **PyPI publish gate** (FIDRAFT provenance: "v0.2 PyPI publish gate" 2026-05-03). Account claims, namespace registration, signing/sigstore, README badges, package metadata polish, classifiers, project URLs, CHANGELOG conventions. Real release ceremony. Closes the two-copies-of-loam friction at its root (vs v0.1.2's docs-explain hedge). **Sequenced for v0.2.0.**
- **ODD-conformance sweep across all sealed components** (FIDRAFT provenance: "ODD-conformance sweep across all sealed components" 2026-05-03). Audit phase 4–12 h + per-component fix amendments. Decomposes via Lens 5 swarming into 15 per-component sub-audits. Benefits from one shipped release behind it (production usage surfaces additional violation patterns). **Sequenced post-v0.1.5; likely v0.2.x.**
- **V11.C — ODD-reverse-engineering skill (heavy version with `framework/odd-extractor/` Cartographer-style slice-and-swarm).** Lightweight version (thin SKILL.md only) was a workaround for broken M-FBM retrieval; deferred 2026-05-04 after M-FBM operational-health amendment scoped. Heavy version retains value for foreign codebases too large for direct read; sequenced for v0.1.4+ once M-FBM is healthy. Provenance: Luke ruling 2026-05-04 + `workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md`.
- **Foundation-revision FR.1/FR.2/FR.3** — principles spec + ODD methodology re-author + ODD-in-loam bridge re-author (FIDRAFT provenance: "Principles distribution shape" 2026-05-03 + FUTURE_IDEAS Idea 1 surfaces). Bigger than v0.1.x; substantive document re-authoring with cross-cutting impact on multiple sealed components. **Sequenced for v0.2.x.**
- **Channel-violation hook hardening** (FIDRAFT provenance: "Telegram-only channel + pause-on-outage as structural-enforcement amendment" 2026-04-29). PreToolUse hook on Agent + Bash + dispatch-shaped tools; depends on Idea 25 (workspace-level `primary_channel` config slot) graduation. **Sequenced for v0.2.x after Idea 25 graduates.**
- **Silent-swallow audit pass** (FIDRAFT provenance: "Graceful fallthrough must include detection + surface" 2026-05-01 + 7+ concrete sites captured across memory-system + orchestrator). Composes with the ODD-conformance sweep. Single audit-pass amendment surfaces all `try/except/pass` patterns; per-component remediation amendments follow. **Sequenced post-v0.1.5; likely batched with the ODD-conformance sweep.**
- **HeavySwarm 4-role pattern + LLMCouncil + SequentialWorkflow drift_detection + MessageTransforms middle-out compression + per-run autosave directory layout** (FIDRAFT provenance: each captured 2026-05-02 by swarms research agent). All compose with the swarm-runtime primitive (V2.C). **Sequenced post-V2.C; v0.2.x.**
- **Dev-mode-manifest realignment** (FIDRAFT provenance: "dev-mode-manifest.yaml broader staleness" 2026-04-29). Partition-design decision required (granular per-component vs bulk `framework/**` admission). Not blocking but real. **Sequenced post-v0.1.5; v0.2.x.**
- **Bootstrap idempotency gap — per-hook-reseater pattern generalisation** (FIDRAFT provenance: "Bootstrap idempotency gap" 2026-05-01). Per-hook reseater is sufficient until 3rd hook needs reseating. **Sequenced for whenever the 3rd reseater is needed.**
- **Plist-template reconciliation** (FIDRAFT provenance: "Plist-template divergence between `first_run_scaffold` and pos3's existing layout" 2026-05-01). Cosmetic; nothing breaks. **Sequenced for whenever a stranger reports it.**
- **Read-side success logging gap — `memory-reads.log` success records** (FIDRAFT provenance: "Read-side success logging gap" 2026-05-01). Composes with observability-aggregator. **Sequenced after one round of incident response in real use.**
- **Anthropic recommendation ladder R.6 (real session-transcript demo) + R.7 (public-presence work)** (FIDRAFT provenance: "Anthropic-perspective recommendation ladder" 2026-05-03). R.6 is a demo artefact (transcript + screenshots); R.7 is mostly Luke-time, not AI-time (HN post, blog post, Discord engagement). Outside loam-as-artefact. **Tracked separately as ongoing iteration, not a release.**
- **Opus 4.7 tokenizer-inflation calibration sweep** (FIDRAFT provenance: "Opus 4.7 tokenizer-inflation calibration sweep" 2026-04-30). Cost-governance budget verify-or-recalibrate + explicit cache-hint mechanism + agentic-cost-instrumentation pass. Calibration work, not architecture. **Sequenced when first cost-anomaly observed in real use.**
- **Cross-component substrate helpers extraction + dead-import audit + format-string drift static check + various pos-amend regex tightenings + AC anchor regex tightening + audit-log rotation + test-deletion gate + framework byte-content pin retirement** (multiple FIDRAFT entries 2026-04-28 from amendment #67/#71/#74/#75 build agents). All small dev-tooling cleanup items. Each individually too small to release-shape. **Sequenced as opportunistic batches in any v0.1.x release with bandwidth, OR rolled into a "dev-tooling cleanup sweep" at v0.2.x.**
- **Pre-existing cross-mode prose refs — 3 component-scoped scrub amendments** (FIDRAFT provenance: "Pre-existing cross-mode prose refs in 3 sealed-component artefacts" 2026-04-29). Three small scrub amendments (workspace-sync README, memory-system launchd README, primary-persona prompt-template). Allowlist invariant must shrink to empty. **Sequenced when any of those three components needs another amendment for unrelated reasons; opportunistic.**

---

## §4. Sequencing diagram

```
v0.1.0 (shipped)
  │
  ▼
v0.1.1 ── design note (why-loam-scaffolds) ✓ SHIPPED
  │
  ▼
v0.1.2 ── orchestrator fix ────────────┐
  │       v0.1.0 hot follow-ons       │
  │       gh-create→push race docs    │
  │       two-copies docs-explain     │
  │       ack-first persona contract  │
  │       loam-amend ergonomics ×3    │
  ▼                                    │
v0.1.3 ── 3-5 SKILL.md packages        │
  │       design note: primary-persona │
  ▼                                    │
v0.1.4 ── 5 subagent personas          │
  │       V11.B (#38/#39/#40) ◄────────┘  (orchestrator from v0.1.2)
  │       design notes (file-mem + odd-delegation)
  ▼
v0.1.5 ── D-3 Protocol widen
          ↓
          D-1 progressive disclosure
          D-2 Anthropic-tool adapter

v0.2.0 (out of scope)
  ├── M-GMP (graphiti as first plugin MemoryProvider) — needs v0.1.5 Protocol stable
  ├── V2.C swarm-runtime
  ├── PyPI publish gate
  └── ODD-conformance sweep + Foundation revisions + everything in §3
```

Internal-to-release dependencies:
- v0.1.4: V11.B requires V11.A from v0.1.2.
- v0.1.5: D-3 → {D-1, D-2}.
- All other items within a release are parallel-safe at the plan-author stage; build-time serialisation per `feedback_serialize_amendment_builds` (no two amendment builds in the same working tree at once).

---

## §5. Open owner-decisions

Most decisions land at recommendation; surfaced here so they're explicit and in one place.

### Decision A — v0.1.2 cadence vs hotfix-and-batch?
**Question:** ship V11.A (orchestrator fix) immediately as v0.1.1.1 hotfix, then batch the rest as v0.1.2? Or batch all of v0.1.2 into a single release?
**Recommendation:** **batch into v0.1.2.** Lower release-overhead; orchestrator fix doesn't have user-visible urgency for v0.1.0 strangers (they don't have an orchestrator instance in their workspace yet — orchestrator is dev-mode machinery). Versioning discipline is for users; users don't care about the orchestrator until it shows up in their workspace.
**Mirrors:** multi-release-roadmap §5 Decision 15 (same recommendation, same rationale).

### Decision B — ack-first amendment shape: hard rule vs heuristic?
**Question:** ack-first amendment lands as a hard rule in primary-persona contract ("first output is ALWAYS an ack on complex requests"), or a heuristic with persona judgment?
**Recommendation:** **hard rule with explicit triggers** (the five triggers in the FIDRAFT entry: ≥3 tool calls, ≥1 background dispatch, decision/judgment vs execution, file authoring vs reading, multi-paragraph/multi-question). Mirrors the F3 model-rationale absence-as-violation pattern: discipline encoded as observable habit, not as structural enforcement (no hook). Trivial back-and-forth skips per the heuristic.
**Why surfaced:** the FIDRAFT entry leaves the rule-vs-heuristic question open; shipping requires choosing.

### Decision C — D-2 Anthropic Memory tool adapter: ship as plugin or as framework component?
**Question:** D-2 ships as `plugins/memory-tool-adapter/` (per FIDRAFT recommendation) or as `framework/memory-tool-adapter/`?
**Recommendation:** **plugin.** Lens-1 leverage is purest when adapter is a plugin (composes onto loam-the-harness without entanglement). Plugin shape also makes it independently versionable so an Anthropic Memory tool API change doesn't bump loam's framework version.
**Mirrors:** FIDRAFT entry recommendation.

### Decision D — SKILL.md packages: how many, which set?
**Question:** 3, 4, or 5 skills in v0.1.4? Final naming/scope?
**Recommendation:** **5, per the suggested set above** (`memory-recall`, `scope-decompose`, `dispatch-with-gates`, `onboarding-conversation`, `session-handoff`). Each one captures a distinct loam translation pattern and each is independently usable from raw Claude Code. Ship 3 if AI-time band overruns; defer the other 2 to v0.1.5 or v0.2.x.
**Why surfaced:** R.4 in the Anthropic-bar recommendation says "3–5"; final count is judgment.

### Decision E — ODD-RE skill, eight D-Q.RE.* sub-decisions [DEFERRED 2026-05-04]
**DEFERRED 2026-05-04 to v0.1.4+ per Luke ruling.** Heavy V11.C (`framework/odd-extractor/`) retains value for foreign codebases; lightweight V11.C is workaround for broken M-FBM and obviated by the operational-health amendment now in flight. Sub-decisions re-open when V11.C is re-sequenced.
**Recommendations adopted from multi-release-roadmap §5 Decisions 5–12** (HYBRID placement, language-agnostic skeleton, markdown+YAML output, explicit token-budget knob, ODD §2.5-violation-surface for coverage gaps; sub-decisions 6–8 defer to V11.C plan-author per ODD authoring discipline).
**Owner-call only if you want to override a recommendation.** Default: accept all five recommendations and let plan-author handle the inside-the-fence sub-decisions.

### Decision F — Subagent persona scope at v0.1.5: all 5 or start narrower?
**Question:** ship all 5 named personas at v0.1.5 or start with 1–2 (e.g., loam-builder + loam-plan-author) and grow?
**Recommendation:** **ship all 5.** Each one obviates a recurring "re-derive methodology fluency in dispatch prompt" pattern; the work to author all 5 is amortised across years of dispatches. Scope-only dispatch discipline is currently broken for the methodology fluency the personas would absorb; partial coverage means the discipline stays partial.
**Mirrors:** multi-release-roadmap §5 Decision 14 (same recommendation).

### Decision G — design notes: shipped under `docs/design/` or `docs/design-notes/`?
**Question:** v0.1.1's locked content uses `docs/design/why-loam-scaffolds.md` (per dispatch). The Anthropic-bar recommendation R.5 used `docs/design-notes/` in its naming. Which path?
**Recommendation:** **`docs/design/`** — matches v0.1.1's locked path. Use `design/` consistently across v0.1.1, v0.1.4, v0.1.5 design notes.
**Why surfaced:** terminology alignment across releases; minor but worth pinning.

### Decision H — v0.1.x versioning: do design-note-only releases bump minor (v0.1.1) or patch?
**Question:** v0.1.1 is doc-only (one design note). Bumps to 0.1.1, not 0.1.0.1. Is that the convention going forward (any user-facing change → version bump) or do we want a different cadence?
**Recommendation:** **every release bumps `0.1.N`** — keeps the cadence visible, avoids the "is 0.1.0.3 a release or a hotfix?" question. Five releases at 0.1.1 → 0.1.5 in close succession is the iterate-in-public story.
**Why surfaced:** versioning convention worth one explicit ruling.

---

## §6. What this roadmap is NOT optimised for

Surfaced explicitly so future sessions don't drift the bundling logic toward a different objective.

- **Not optimised for impressing any particular audience.** v0.1.1's design note is doc-shaped because the scaffolding choice deserves articulation, not because it's pitch material. R.4 SKILL.md packages and R.5 design notes from the Anthropic-bar recommendation are included where they serve real users (Lens 1 leverage, builder-voice for any reader); they're not the load-bearing reason for the bundle they're in.
- **Not optimised for breadth.** Five releases is an honest scope; FIDRAFT has ~50+ entries and FUTURE_IDEAS has 26 numbered ideas. Many are deferred to v0.2 or beyond per §3. A kitchen-sink release would be the wrong shape.
- **Not optimised for parallelism.** Each release is small enough to ship serially within hours-to-days. The dispatch agents within a release can parallelise where the working-tree fence allows; releases themselves serialise.
- **Not optimised for foundation-perfecting.** Foundation revisions (FR.1/FR.2/FR.3), ODD-conformance sweep, silent-swallow audit pass — all deferred to v0.2.x. v0.1.x is iterate-in-public; foundation perfecting is a v0.2 cycle once iteration data is in.

---

## §7. Provenance trail

Every item in §2 carries a FIDRAFT entry name or FUTURE_IDEAS Idea number inline. Cross-cuts:

- **`docs/FUTURE_IDEAS_DRAFT.md`** — primary source for v0.1.2/v0.1.3/v0.1.4/v0.1.5 items; cited inline.
- **`docs/FUTURE_IDEAS.md`** — Idea 25 (workspace-level default-channel) referenced in §3 for channel-hook hardening sequencing.
- **`docs/STATE.md`** — sealed-amendment count + #38/#39/#40 status + amendment-cycle context for V11.B.
- **`docs/plans/oss-v0-1-0-publish.md`** — master plan for v0.1.0; multi-release-roadmap §3.3 V2.A names M-GMP shape.
- **`docs/plans/v0-1-0-foldback-scope-expansion.md`** — foldback ladder (FBE.1–11 + FBE.6{b,c,d}) that closed v0.1.0; method-decision register at §8 for what landed.
- **`workspace/.scratch/claude-output/loam-anthropic-bar-recommendation-2026-05-03.md`** — R.1–R.6 recommendations (R.4 = SKILL packages → v0.1.4; R.5 design notes split across v0.1.4 + v0.1.5; R.3 essence absorbed into v0.1.1's locked content; R.6 + R.7 deferred per §3).
- **`workspace/.scratch/claude-output/multi-release-roadmap-2026-05-03.md`** — pre-foldback roadmap whose V11.A/V11.B/V11.C/V11.D/V11.E item-IDs are reused in this roadmap for continuity (V11.A → v0.1.2, V11.B → v0.1.5, V11.C → DEFERRED to v0.1.4+ per 2026-05-04 ruling, V11.D → v0.1.3, V11.E → v0.1.2).
- **`workspace/.scratch/claude-output/odd-reverse-engineering-skill-research.md`** — 907-line research artefact for V11.C; eight D-Q.RE.* sub-decisions referenced in §5 Decision E.

---

## §8. Method-decision register (post-build, populated as releases close)

Reserved for actual amendment commit SHAs as each v0.1.N release lands. Per `feedback_loose_AC_text_fix_AC_not_implementation` and the post-amendment verification discipline.

| Release | Status | Tag SHA | Notes |
|---|---|---|---|
| v0.1.1 | (in flight; locked content authored in parallel) | — | — |
| v0.1.2 | (in flight) | — | V11.A sealed at `9d58062` (2026-05-03); V11.E sealed at `7d19a7e` (2026-05-03); ack-first persona contract sealed at `32ff67d` (2026-05-03); loam-amend ergonomics sweep sealed at `2c32c1b` (2026-05-03). |
| v0.1.3 | (in flight) | — | R.5 design note 1 (primary-persona-shape) sealed at `7ae346d` (2026-05-03); SKILL.md packages bundle (item 1) sealed at `f04e925` (2026-05-04); M-FBM operational-health AC family (`AC.MFBM-OPS.*`) sealed at `1a1f830` (2026-05-04). |
| v0.1.4 | (planned) | — | — |
| v0.1.5 | (planned) | — | — |
| v0.1.6 | (in flight) | — | Production-safety mode + 3 base-SKILL additions + 2 bug fixes. Cycle 1 (production-safety + bug fixes) sealed at `3f1d237` (2026-05-04). Cycle 2 (3 base SKILLs — translation-discipline, audit-block-on-telegram, owner-decision-summary) sealed at `88674cb` (2026-05-04). Sub-plan: `docs/plans/v0-1-6-production-safety-and-base-skills.md`. Decision P (SOC-2 audit-trail floor) RESOLVED YES per dispatcher autonomy. |
| v0.1.7 | SHIPPED 2026-05-04 (local; tag deferred) | — | Subagent personas + per-project PM + layered-skill discovery + one-question-at-a-time PM-enforced surfacing flow. Four amendment cycles, all serialized (per `feedback_serialize_amendment_builds`). Cycle 1 (5 subagent personas at `plugins/dev-sdlc/agents/` + workspace-bootstrap symlink registration into `<workspace>/.claude/agents/`) sealed at `3aa20dd` (2026-05-04). Cycle 2 (per-project PM as NEW component `framework/per-project-pm/`; queue + state-of-world + decision-surfacing API + audit-log primitive; lazy-loaded contribution at `host.per_project_pm`) sealed at `73505f0` (2026-05-04). Cycle 3 (layered-skill discovery — plugin auto-symlinking from `plugins/<plugin>/skills/` into `<workspace>/.claude/skills/` + workspace-local override semantics + cross-plugin collision halt + design-note `docs/design/layered-skill-architecture.md`) sealed at `bcf699a` (2026-05-04). Cycle 4 (one-question-at-a-time PM-enforced surfacing flow — `record_response()` + `surface_next_questions_batch()` + `PendingResponseError` blocking + `RecordedResponse` + `pending_response_for` field + `is_audit_block_trigger` property composing with v0.1.6 `audit-block-on-telegram` SKILL) sealed at `122a7c8` (2026-05-04). Decision Q (one-question-at-a-time PM-enforced) RESOLVED YES — Cycle 4 enforces structurally on the batch API; `surface_next_question` Cycle 2 contract preserved verbatim. Decision I (workspace-local skills under Anthropic-native `<workspace>/.claude/skills/`) RESOLVED YES — Cycle 3 mechanism. Decision C (subagents source in `plugins/dev-sdlc/agents/`) RESOLVED — Cycle 1. Sub-plan: `docs/plans/v0-1-7-personas-pm-layered-skills.md`. All 6 smoke dimensions PASS for the release-level rollup (HARD gate per Decision R). 114 cumulative tests pass on the per-project-pm component (64 Cycle 2 + 50 Cycle 4); 27 new tests pass on workspace-bootstrap (Cycle 3); 5 cross-component seal-tests sweep green. Tag NOT pushed (per dispatcher); v0.1.7 sits as a local release until Luke gates + migration question resolves. |
| v0.1.8 | SHIPPED 2026-05-04 (local; tag deferred) | — | ODD reverse-engineering (heavy) + Ruby/Rails + JS/TS/Playwright first-class adapters + 6 dev-sdlc SKILLs first pass. Five amendment cycles, all serialized. Cycle 1 (odd-extractor scaffolding — four-stage workflow + adapter Protocol + audit-log primitive at `plugins/dev-sdlc/odd-extractor/`) sealed at `c1abda1`. Cycle 2 (confidence bands + ratification — `BandedAC` + `Evidence` + `ConfidenceBand`; ratification mediator; per-project-pm batch extension; `odd-methodology.md` §11 confidence-band semantics) sealed at `4865028`. Cycle 3 (Ruby/Rails first-class adapter — tree-sitter Python bindings; per-Rails-idiom slicing; test-first VERIFIED granularity; heuristic HYPOTHESISED inference; synthetic in-tree Rails fixture; entry-point language-adapter registry; `odd-methodology.md` §12) sealed at `6711dd7`. Cycle 4a (JS/TS/Playwright adapter + `jsts-playwright-app` fixture — multi-grammar tree-sitter dispatch; 8 idiom recognizers Express/Playwright/page-objects/TS-types/Zod/class-validator/Jest-Mocha-Vitest/HTML; ESM+CJS; `odd-methodology.md` §13) sealed at `67dd302`. Cycle 4b (canonical `ruby-rails-payment` fixture + Ruby e2e ratification + DRY refactor of repo_sha/slugify/heuristic-helpers into `lang/_common/`; behaviour-preserving 375→501 sealed-test sweep) sealed at `c648cf9`. Cycle 5 (6 dev-sdlc SKILLs first pass — `loam-amend-cycle`, `dispatch-brief-authoring`, `plan-before-code-author`, `fidraft-capture`, `front-load-principle-walk`, `audit-finding-triage` at `plugins/dev-sdlc/skills/<name>/SKILL.md`; auto-discovery via v0.1.7 Cycle 3 mechanism; 38 new tests; total 501 dev-sdlc sealed-component tests green) sealed at `e4512b9`. Sub-plan: `docs/plans/v0-1-8-master-plan.md` (`1c2c478`; rerouted at `17f32a9`). Decision R (HARD release-level smoke gate) RESOLVED YES — all 6 dimensions PASS on canonical pos-v2: D1 banded extractions on both canonical fixtures (jsts: 12V+38P+10H = 60 ACs; ruby: 15V+48P+4H = 67 ACs; both above ≥3+5+2 floor); D2 idempotent re-run; D3/D4 n/a structurally (one-shot CLI + filesystem-state); D5 cross-session inherited from Anthropic-native discovery + extraction-state subprocess-boundary survival; D6 telemetry-floor (6+ audit-log entries per extraction). 14 SKILLs auto-symlinked into `<workspace>/.claude/skills/` (8 base loam-skills + 6 new dev-sdlc). Decision O (Ruby-first-class adapter) RESOLVED YES — Cycle 3. Tag NOT pushed (per dispatcher); v0.1.8 sits as a local release until Luke gates. Pre-existing `KNOWN_CROSS_MODE_DEBT` allowlist drift surfaced during release-smoke (audit-tool stale-allowlist independent of Cycle 5; pre-existed at HEAD `c648cf9`); captured in FIDRAFT for v0.1.9. |
| v0.1.9 | SHIPPED 2026-05-04 (local; tag deferred) | — | PR-safety gate engine + override workflow + hooks + CI templates + 6 dev-sdlc SKILLs second pass + audit-allowlist cleanup. Three-cycle decomposition. Master plan `b01d3eb`. **Cycle 1 (PR-safety gate engine + override workflow)** SEALED 2026-05-04 — NEW component `plugins/dev-sdlc/pr-safety/`; per-band gating engine (3-band × 4-shape × 3-profile = 13 cells + 6 mixed-touch pre-emption rules); override-commit recognition (`Loam-Override:` trailer + `contract-update:` prefix + `--override` flag; Decision I default-no honoured); CLI `loam pr-safety gate <repo>`; SOC-2 audit-trail floor at `<workspace>/.loam/pr-safety/audit-log/`; production-stake profile integration; classifier accuracy 100% on 12-case synthetic test set (≥90% bar; halt-trigger not fired). Plan-doc `3d5f52d`; source-edit `bb592fa`; apply `136adc6`; seal `790807d`; §14 backfill `2f154c8`. AC.PRSG.1..9 satisfied; 105 cycle tests + 392 prior odd-extractor tests = 497 green; 719 in extended dev-sdlc sweep; 0 regressions. D1+D2-idempotency+D5+D6 smoke exercised; D3/D4 n/a per smoke-test-discipline §6 (one-shot CLI). **Cycle 2 (hook installers + 3 CI templates + provenance-traceable PR description template)** SEALED 2026-05-04 — Pre-commit + pre-push installers (idempotent + husky-aware + halt-on-conflict; `LOAM_PR_SAFETY_BYPASS=1` honoured under dev/research only); 3 CI templates (GitHub Actions separate file + GitLab CI + CircleCI sentinel-block-delimited); provenance-traceable PR description template (5 sections; 60K-char overflow truncation); install ergonomics CLI (`loam pr-safety install <surface>` + `install all`; exit code 6 conflict-halt); hook-fire dispatcher (`loam pr-safety hook-fire`); `--render-pr-description` gate-mode flag. Plan-doc `48a4758`; source-edit `17d02ca`; apply `68859d9`; seal `0dc557e`; §14 backfill `a61d4ff`. AC.PRSI.1..10 satisfied; 78 new tests + 105 inherited Cycle 1 = 183 green. All 6 smoke dimensions exercised. pyproject 0.1.0→0.2.0. Cycle 1 README transparent catch-up: `plugins/dev-sdlc/README.md` Sub-packages section. **Cycle 3 (6 dev-sdlc SKILLs second pass + audit-allowlist cleanup)** SEALED 2026-05-04 — Six new SKILL.md packages at `plugins/dev-sdlc/skills/`: `seal-narrative-writer` (composes with `loam-amend-cycle`); `plan-docs-author` (composes with `plan-before-code-author`); `hook-violation-recovery` (composes with `audit-finding-triage`); `component-scaffold-author` (composes with `loam-amend-cycle`); `graceful-fallthrough-with-detection` (meta-pattern composing with every SKILL); `loam-amend-status-quick` (composes with `loam-amend-cycle`). Each SKILL body covers the FULL ritual — 6-section shape (What captures / When to use / How persona applies it / Graceful degradation / Composition / Out of scope); no stubs. Audit-allowlist `KNOWN_CROSS_MODE_DEBT` shrunk 5→1 entry at `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py` (4 stale entries graduated empirically: 1× primary-persona prompt + 3× workspace-sync README; memory-system/launchd entry stays). FIDRAFT line 143 closes. Per `feedback_loose_AC_text_fix_AC_not_implementation`: tightened `test_AC_SKILLS_DSDLC1_7`'s exact-equality check to subset check; canonical orphan/misnamed check moves to AC.SKILLS-DSDLC2.7. Plan-doc `98468ca`; source-edit `d8e3f01`; apply `6378cc5`; seal `3284087`; §14 backfill `642097b`. AC.SKILLS-DSDLC2.1..8 + AC.AUDIT-CLEANUP.1..3 satisfied (11 ACs). 1013 dev-sdlc tests green; 0 regressions. All 6 smoke dimensions exercised. `/` menu shows 20 SKILLs (8 base loam-skills + 12 dev-sdlc — 6 first pass + 6 second pass). Tag deferred until Luke gates the release. v0.1.9 sits as a local release. |
| OSS migration follow-up #132 | SEALED 2026-05-04 | — | workspace-bootstrap framework-only → main switch (sub-plan `docs/plans/workspace-bootstrap-framework-only-to-main.md`). Surfaced from OSS dev-architecture migration §8.8 halt-and-surface (sealed at `ea8c4bb`). Single-component fence on `framework/workspace-bootstrap/` — replaces `FRAMEWORK_ONLY_BRANCH = "framework-only"` constant + `_materialise_framework_only_branch` helper with `CANONICAL_BRANCH = "main"` + `_materialise_canonical_branch`; flips 3 production callsites; rewrites conftest to drop archived `loam.publish_framework_only.synth` import + use `git init --initial-branch=main`; updates 7 existing AC tests + adds 4 new (AC.WBM2M.{1,2,3,4}). Doubled-component contract (FBE.2c.5/.6) preserved verbatim. Plan-doc `926a08b`; source-edit `737c644`; manifest baseline `869d1f5`; apply auto-commit `29c1daa`; seal `a1e231c`. 310 tests pass + 11 skipped (zero regressions). D1 cold-state smoke ✓; D2 idempotency smoke ✓. With this seal, the OSS dev-architecture migration is fully complete; post-seal cleanup (delete `loam:framework-only` ref on remote) is Luke's call, recommended within 24 h. |
| v0.2.1 | SHIPPED 2026-05-05 (local; tag deferred — re-smoke verdict YELLOW; F5 dev-mode resolves for Eric via lukeivers/loam:main push) | — | THE Eric ship: install-time onboarding ritual hardening + promotion rubric mechanism + release-level HARD smoke gate execution + 2 corrective amendments. Three cycles + 2 correctives, all serialized. Master plan `2ff444e` (with single-fixture patch `2ba7fcd`; sweep `9355ef2`; FIDRAFT `df447bc`). **Cycle 1 (Eric onboarding ritual hardening)** SEALED 2026-05-04 — `framework/workspace-bootstrap/` extended with 6 new modules + 16 test files + 7 fixtures + 2 docs (1 NEW: `docs/dev-mode-getting-started.md`) + manifest extension. 15 ACs AC.ONBOARD.1-15 satisfied (including survey-as-default-source, language auto-detection, PM-mediated one-question-at-a-time per Decision Q, production-stake default for Rails per Decision P, audit-log floor per Decision P). Plan-doc `e5dd7f7`; source-edit `0bf33f1`; apply `f6b5047`; seal `55640b1`; §14 backfill `d7c5b2d`; master plan §9 backfill `4c4a1d3`. **Cycle 2 (promotion rubric mechanism)** SEALED 2026-05-04 — NEW `plugins/dev-sdlc/skills/skill-promotion-review/` with 425-line SKILL.md + 12 tests + 4 fixtures. 12 ACs AC.PROMOTE.1-12 satisfied: 3-signal MVP per Decision L (Categorization + Quality + Conflict primary; Reusability + Tests + Usage secondary discussed not blocking) + 10-row decision matrix from layered-skills §4.2 + 7-step graduation walk per §4.3 + demotion path per §4.4 + scope-of-work on-demand-only fallback (cron-trigger deferred to v0.2.x). Plan-doc `984d893`; source-edit `c01f50e`; apply `c48aa68`; seal `298172e`; §14 backfill `29b26ed`; master plan §9 backfill `5b9b3fd`. **Cycle 3 (release-level HARD smoke gate execution)** — NO new code; evidence document gating release tag. Original verdict RED (3 hard-blocking findings F1/F2/F5) at `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md`. FIDRAFT amend-cycle drift captured at `5a9dd26`. **Corrective F1 (odd-extractor contract-draft.yaml acs+unhandled_paths)** SEALED 2026-05-04 — `verify_contract()` writes `acs:` + `unhandled_paths:` into contract-draft.yaml so PR-safety gate finds VERIFIED ACs on real-fixture extractions. 5 ACs satisfied. Plan-doc `eda155c`; source-edit `330e66e`; baseline `2e74bbd`; apply `0904064`; seal `ad42314`; §14 backfill `5fea94c`. **Corrective F2 (workspace-bootstrap language-detection framework/ skip)** SEALED 2026-05-04 — `_SKIPPED_DIRS = frozenset({"framework"})` so language detection no longer mixes loam framework code with target-project code. 4 ACs satisfied. Plan-doc `92b970c`; source-edit `0efd160`; baseline `5954870`; apply `70987e5`; seal `d82a43b`; §14 backfill+auto-backfill `2520adc` + `686d65c`. **Re-smoke verdict YELLOW** — F1+F2 validated end-to-end on rd-automation (PR-safety emits HARD_BLOCK on synthetic VERIFIED-AC-touching diff; language detection returns ts/js/unknown not mixed); F5 dev-mode persists (canonical local main is legacy pos-v1) but resolves for Eric via fast-forward push of pos-v2 → lukeivers/loam:main (authorized by Luke 2026-05-05; lukeivers/loam:main currently at `ea8c4bb` v0.1.7-era, 120 commits behind pos-v2). Re-smoke evidence at `<pos3>/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-05-rerun.md`. Sub-plans: `docs/plans/v0-2-1-master-plan.md` + cycle-1 / cycle-2 / corrective-f1 / corrective-f2 sub-plan-docs. Tag NOT created until corrective-pushes complete; tag-push deferred until Luke gates Eric install. F5 dev-mode-fix + Eric-survey-response remain as gates before tag-push. v0.2.x trajectory: cross-session detection + Mode 2 structured fill-in-blanks UI + Python runtime detector module + F5 dev-mode reconciliation + FIDRAFT items captured during v0.2.1 (post-Eric). |
| v0.2.0 | SHIPPED 2026-05-04 (local; tag deferred) | — | Contract-stays-alive + Eric-patterns-captured release. Two amendment cycles, both serialized. Master plan `7c0f87b`. **Cycle 1 (continuous codebase-watch + scheduling + PM ratification-queue + domain-batched AC surfacing)** SEALED 2026-05-04 — `plugins/dev-sdlc/odd-extractor/` extended with incremental engine + diff-classifier (≥90% accuracy on synthetic test set; halt-trigger not fired) + re-extraction proposal generation + domain-batched PM enqueue (AC ID prefix primary + file-path-prefix fallback + `_uncategorised`) + scheduling-CLI primitive (`--invocation-source` flag) + production-stake honor-flow + audit-trail floor with 5 new event-kinds. Plan-doc `621ca08`; source-edit `9bed44c`; apply `faff84e`; seal `6fef2f1`; §14 backfill `fa01436`; master plan §9 backfill `11ebc76`. AC.WATCH.1..10 satisfied (10 ACs). D1+D2-idempotency+D5+D6 smoke exercised; D3/D4 n/a (one-shot CLI). **Cycle 2 (persona-driven skill capture (auto-creation MVP) + workspace-config flag + design note)** SEALED 2026-05-04 — Two-component fence (intentional exception per master plan lock). Primary `plugins/loam-skills/`: NEW `skill-capture-proposal` SKILL package codifying the persona-driven skill-capture discipline — 3 MVP triggers (explicit-request / repeated-invocation / ask-and-answer; 3 deferred to v0.2.x — CLAUDE.md drift / memory-recall hit / hook-trigger), user-ratification gate via existing v0.1.7 Cycle 4 PM batch API (enqueue_decision + surface_next_questions_batch n=1 + record_response), proposal draft to `<workspace>/.scratch/claude-output/skill-draft-<slug>.md`, write-on-Y to `<workspace>/.claude/skills/<slug>/SKILL.md`, 14-day cool-down + ≤3/week budget + 20-skill hard-cap, SOC-2 audit-trail floor with 6 named event-kinds at `<workspace>/.loam/skill-capture/audit-log/`. Triggers ship as persona-side discipline (NOT runtime detector); session-scoped at MVP (M-FBM cross-session reads deferred to v0.2.x per master plan §7.3). Universal-tier (any loam user, dev or non-dev) per layered-skill research §3.6 + Luke's 2026-05-04 universal-scope clarification. Secondary `framework/workspace-bootstrap/`: new `enable_auto_skill_capture: bool = False` field on `Manifest` dataclass — load_manifest validation mirrors `safety_profile` shape (bool-only; absent → default False; non-bool → fail-closed `MissingConfigError`). Tertiary `docs/design/auto-skill-capture-shape.md`: design note with 7 sections (Architecture / Triggers / Workflow / Cool-down + budget + hard-cap / Failure modes / Composition / Forward path) + Eric grounding. Plan-doc `d35690e`; source-edit `31dce27`; apply `5cb84a5`; seal `549fe88`; §14 backfill `cf40f53`; master plan §9 backfill `a9dea8d`. AC.SKILLCAP.1..13 satisfied (13 ACs). 754 tests green across 4 affected sealed components (loam-skills 146 + workspace-bootstrap 325 + per-project-pm 124 + dev-sdlc 159); pre-flight `test_AC_LAYERED_2_skill_symlink_registration.py` + 26 sibling LAYERED tests green (Anthropic native discovery still functional; halt-trigger not fired). All 6 release-level smoke dimensions exercised (SOFT gate per Decision R; quality-bar-non-negotiable applies). `/` menu shows 9 base loam-skills (8 from v0.1.6 close + 1 new `skill-capture-proposal`). Tag deferred until Luke gates. v0.2.1 + v0.2.x trajectory: promotion rubric + demotion path + Eric onboarding hardening (v0.2.1); 3 deferred triggers + cross-session detection + Mode 2 structured fill-in-blanks UI + Python runtime detector module (v0.2.x post-Eric). |

### v0.1.2 — V11.A (orchestrator fix) — sealed 2026-05-03

**Sub-plan:** `docs/plans/v0-1-2-V11-A-orchestrator-fix.md`.
**Manifest:** `docs/plans/v0-1-2-V11-A-orchestrator-fix.manifest.yaml` (amendment #120).
**Status file:** `<pos3>/workspace/.scratch/claude-output/v11a-orchestrator-fix-status-2026-05-03.md`.

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `e7e7925` | Sub-plan-doc; fence-one-no-edit shape per FBE.4 precedent. |
| Manifest | `d6e5498` | Amendment #120; baseline `e7e7925`; single-component fence on `framework/orchestrator/`. |
| `loam amend apply` (manual `chore(amend)`) | `1889db6` | Sidecar SEAL_COMMIT 8032348 → e7e7925; BASELINE literal bump. |
| `loam amend seal` | `9d58062` | Deterministic seal commit. Narrative at `framework/orchestrator/tests/SEAL_COMMIT.notes`. |

**Acceptance summary:**
- AC.V11.A.1 (plist template `loam.orchestrator`) — verified pre-build (already fixed at `f0c4aa9`).
- AC.V11.A.2 (`framework/orchestrator/` in install list) — verified pre-build (already present per FBE.4 at `install-from-source.txt:34` + `docs/install-from-source.md:83`).
- AC.V11.A.3 (smoke runtime contract) — passed all four contracts: PID alive after 5s, socket bound at `/tmp/v11a-smoke/.loam/orchestrator.sock` mode 0600, clean SIGTERM exit 0, empty stderr.
- AC.V11.A.4 (negative — zero source-side delta) — verified post-seal (`git diff e7e7925..9d58062 --name-only` produces only sidecars + manifest YAML).
- AC.V11.A.S (fence-one-no-edit) — verified post-seal (4 paths in fence diff; all sidecars + universal-admitted manifest).

**Surfaces recorded (out of V11.A scope; carried forward):**
- Surface #1: `pos_orchestrator` source-string vocabulary leakage in 4 docstring/help-text/operations-doc sites — FUTURE_IDEAS_DRAFT candidate (consider bundling with FBE.5 Surface #1 dev-tool description scrubs).
- Surface #5: Luke's installed plist at `~/Library/LaunchAgents/com.loam.orchestrator.plist` is STALE (pre-`f0c4aa9` content + points at `pos3/.venv` not canonical) — operator-hygiene reinstall recipe captured in status file.

### v0.1.2 — V11.E item (b) (graphiti probe graceful-skip — Resolution A) — sealed 2026-05-03

**Sub-plan:** `docs/plans/v0-1-2-V11-E-graphiti-probe-skip.md`.
**Manifest:** `docs/plans/v0-1-2-V11-E-graphiti-probe-skip.manifest.yaml` (amendment #121).
**Status file:** `<pos3>/workspace/.scratch/claude-output/v11e-graphiti-probe-skip-status-2026-05-03.md`.
**Predecessor status (4-option matrix + Resolution A justification):** `<pos3>/workspace/.scratch/claude-output/v11e-followon-hazards-status-2026-05-03.md`.

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `212f347` | Sub-plan-doc; two-component fence on `framework/orchestrator/` + `framework/primary-persona/`. |
| Source edit | `c3b74b2` | `pos_session_start.py` + `session_start_gate.py` gate memory probe on `~/Library/LaunchAgents/com.loam.memory-graphiti.plist` existence; new `_is_memory_expected` helper + new `not_expected` sentinel + new `memory_expected: bool` result-dict field. New tests + widened `test_D8_1_session_start_emission` closed-set assertion. |
| Manifest | `6c3d7c7` | Amendment #121; baseline `c3b74b2`; two-component fence. |
| `loam amend apply` (manual `chore(amend)`) | `2416661` | Both BASELINE literals + both SEAL_COMMIT sidecars bumped to `c3b74b2`. |
| `loam amend seal` | `7d19a7e` | Deterministic seal commit. Narrative at `framework/orchestrator/tests/SEAL_COMMIT.notes`. Scoped sweep (orchestrator + primary-persona only). |

**Acceptance summary:**
- AC.V11.E.1 (orchestrator probe graceful-skip when plist absent) — verified by `test_AC_V11_E_1_*` suite + smoke A (`status: ready`, `memory_expected: False`, `exit_code: 0`).
- AC.V11.E.2 (gate `_probe_memory` returns `not_expected` when plist absent) — verified by new test file + smoke C (`memory: not_expected`).
- AC.V11.E.3 (canonical plist path single source-of-truth) — verified by `test_AC_V11_E_3_canonical_plist_path_matches_orchestrator_helper`.
- AC.V11.E.4 (negative — plist-present preserves legacy behaviour) — verified by smokes B (`status: partial`, `memory_expected: True`) + D (`memory: up`).
- AC.V11.E.S (two-component fence) — verified post-seal (sealed sweep across both components passed; `git diff c3b74b2..7d19a7e --name-only` confines to fence + universal admissions).

**Items (a) and (c) of original V11.E scope — already-fixed at `f0c4aa9` per prior status file (no source delta required for V11.E):**
- (a) Corpus-gate `_FALLBACK_BASELINE_PATHS` — public-mode-clean (only `docs/design/odd.md`).
- (c) Plist template module name — `<string>loam.orchestrator</string>` post-fix; double-verified at V11.A.

**Surfaces recorded (out of V11.E scope; carried forward):**
- None new. The four resolutions from the prior V11.E status (B inventory-driven probe set, C remove probe, D workspace-config flag) remain explicitly deferred per the dispatcher's Resolution A lock. Resolution D composes with v0.1.5 D-3 / v0.2 M-GMP if a richer config slot becomes warranted.

### v0.1.2 — item 5 (ack-first persona contract amendment) — sealed 2026-05-03

**Sub-plan:** `docs/plans/v0-1-2-ack-first-persona-contract.md`.
**Manifest:** `docs/plans/v0-1-2-ack-first-persona-contract.manifest.yaml` (amendment #122).
**Status file:** `<pos3>/workspace/.scratch/claude-output/ack-first-persona-contract-status-2026-05-03.md`.
**FIDRAFT provenance:** "Acknowledge-first on complex requests" (2026-05-03).
**Decision locked:** Decision B in §5 — hard rule with 5 explicit triggers.

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `7041ac7` | Sub-plan-doc; single-component fence on `framework/primary-persona/`; AC family `AC.VPC.5.*` (collision-safe); Surface #2 in-band drift fix per `feedback_loose_AC_text_fix_AC_not_implementation`. |
| Source edit | `d2754be` | Adds `### Acknowledge first on non-trivial requests` as the first subsection under `## Operational rules` in `templates/persona-template/prompt.md` — names 5 triggers, trivial carve-out, ack-shape literal, absence-as-observable-violation framing. Widens `test_AC_O_1_six_*` → `test_AC_O_1_eight_*` (composes Surface #2 α-drift fix); renames `..._count_is_eleven` → `..._count_is_thirteen`. New test file `test_AC_VPC_5_ack_first_rule.py` (6 tests). |
| Manifest | `4672abd` | Amendment #122; baseline `d2754be`; single-component fence. |
| `loam amend apply` (manual `chore(amend)`) | `8cbab6a` | Sidecar SEAL_COMMIT 24166619 → d2754bee; BASELINE literal `c3b74b2` → `d2754be`. |
| `loam amend seal` | `32ff67d` | Deterministic seal commit. Narrative at `framework/primary-persona/tests/SEAL_COMMIT.notes`. |

**Acceptance summary:**
- AC.VPC.5.1 (ack-first subsection landed with 5 triggers + carve-out + ack-shape + absence-as-violation framing) — verified by `test_AC_VPC_5_1_*` suite (5 tests pass).
- AC.VPC.5.2 (test count widened 6→8 ops + 11→13 total in lock-step; composes new addition with α drift) — verified by widened `test_AC_O_1_eight_operational_rule_sections_present` + `test_AC_O_1_named_section_count_is_thirteen` (15 AC.O.1 tests pass).
- AC.VPC.5.3 (hard-rule shape — imperative voice + no softening language) — verified by `test_AC_VPC_5_3_hard_rule_imperative_voice`.
- AC.VPC.5.4 (`str.format` compatibility preserved) — verified by `test_AC_O_1_template_is_str_format_compatible` (no new unescaped braces in the new subsection).
- AC.VPC.5.5 (smoke: tmp-workspace scaffold) — verified by Smoke B: `_install_persona_directory` against `/tmp/ack-first-smoke-NNNNN/` produces `personas/smoke-test/prompt.md` carrying the ack-first heading + ack-shape literal + carve-out keywords verbatim.
- AC.VPC.5.S (single-component fence on `framework/primary-persona/`) — verified post-seal (`git diff 18e708c..32ff67d --name-only` produces 8 paths: 6 in `framework/primary-persona/` + 2 in `docs/plans/` universal admission; zero outside).

**Surfaces recorded (out of v0.1.2-item-5 scope; carried forward):**
- Surface #2 (in-band fixed): pre-existing α-drift in `test_AC_O_1_*` widened in lock-step with the new addition (now consistent — 8 ops, 13 total).
- UserPromptSubmit hook for automated ack emission — deferred per Decision B; FIDRAFT names as "hardening path if drift observed". Persona-level discipline is the right first cut.
- Subagent persona files (`.claude/agents/<name>.md`) inheriting the ack-first rule — v0.1.5 V2.B scope.
- Pre-existing user-edited workspace `personas/<handle>/prompt.md` files — opt-in by user re-scaffold; no migration shipped (inconsistent with the user-edited-content principle for personas).

### v0.1.2 — item 6 (loam-amend ergonomics sweep) — sealed 2026-05-03

**Sub-plan:** `docs/plans/v0-1-2-loam-amend-ergonomics.md`.
**Manifest:** `docs/plans/v0-1-2-loam-amend-ergonomics.manifest.yaml` (amendment #123).
**Status file:** `<pos3>/workspace/.scratch/claude-output/loam-amend-ergonomics-status-2026-05-03.md`.
**FIDRAFT provenance (3 entries closed; all 2026-05-03):**
- "`loam amend apply` does not commit the apply step BY DESIGN — convention is to manually create the apply commit"
- "`loam amend seal` requires clean working tree — stash-then-pop workaround used in every FBE.x"
- "`loam amend apply` partner-prefix derivation bug — derives from name field assuming `framework/<name>/`+ bare-`<name>/` shapes; misses `plugins/<name>/` shaped components"

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `be76e41` | Sub-plan-doc; single-component fence on `plugins/dev-sdlc/`; AC family `AC.LAE.*` (collision-safe). |
| Source edit | `a30a583` | Three improvements landed in `plugins/dev-sdlc/tools/loam-amend/`: (a) auto-commit in `commands/apply.py` + Co-Authored-By trailer + idempotent-skip; (b) `--allow-untracked-globs` flag in `commands/seal.py` + `cli.py`; (c) `_partner_prefix` helper in `commands/apply.py` derives from `seal_test` (4-segment + 3-segment legacy fallback). 3 new test files (`test_AC_LAE_{1,2,3}_*.py`) + 1 backwards-compat update to `test_tracker_integration.py` (`fixture: post-apply state` commit becomes conditional under the new auto-commit semantics). |
| Manifest | `46f4e0f` | Amendment #123; baseline `a30a583`; single-component fence on `plugins/dev-sdlc/`. |
| `loam amend apply` (auto-commit) | `7a41b03` | Meta-recursive: this amendment's apply step uses the auto-commit code it ships. Sidecar `18e4c136` → `7a41b03`; BASELINE literal `8032348` → `a30a583`. |
| `loam amend seal` | `2c32c1b` | Deterministic seal commit. Narrative at `plugins/dev-sdlc/tests/SEAL_COMMIT.notes`. Scoped sweep on dev-sdlc (sweep skipped per pre-existing `framework/*/tests/SEAL_COMMIT` discovery limitation; dev-sdlc seal-fence test verified passing manually + in pre-seal touched-only run). |

**Acceptance summary:**
- AC.LAE.1 (auto-commit on `loam amend apply`) — verified by `test_AC_LAE_1_apply_auto_commit.py` (5 tests pass) + Smoke A (chore(amend) commit landed with conventional subject + Co-Authored-By trailer under `CLAUDECODE=1`; idempotent re-runs skip the commit).
- AC.LAE.2 (`--allow-untracked-globs` flag) — verified by `test_AC_LAE_2_seal_allow_untracked_globs.py` (4 tests pass) + Smoke B (seal aborts WITHOUT flag; proceeds WITH flag; admitted patterns remain untracked post-seal — admission is dirty-check-only).
- AC.LAE.3 (partner-prefix from `seal_test` path) — verified by `test_AC_LAE_3_partner_prefix_from_seal_test.py` (4 tests pass) + Smoke C (mixed `framework/alpha/` + `plugins/beta/` fence — alpha admits `plugins/beta/`, beta admits `framework/alpha/`; NO buggy-shape `framework/beta/` or bare `beta/` admissions).
- AC.LAE.S (single-component fence on `plugins/dev-sdlc/`) — verified post-seal (`git diff a30a583..2c32c1b --name-only` produces 4 paths: 3 in `plugins/dev-sdlc/tests/` + 1 in `docs/plans/` universal admission; zero outside).

**Surfaces recorded (out of v0.1.2-item-6 scope; carried forward):**
- Backwards-compat for in-flight dispatch prompts that say "manually create the apply commit": now becomes a no-op (the manual commit lands as empty / no-staged-changes after auto-commit). Harmless; existing dispatch prompts not updated as part of this amendment (out-of-fence; opportunistic at next dispatch authoring touch).
- Manifest-level `allow_untracked_globs` admission — deferred. CLI flag covers immediate workflow; manifest field can land later if observed pain-point recurs.
- Migrating prior manifests' `extra_allowed_prefixes` to drop now-redundant `<name>/` bare admissions — out-of-fence; opportunistic at next per-component touch.
- Cross-component sweep discovery (`_discover_sealed_components`) globs `framework/*/tests/SEAL_COMMIT` only; misses `plugins/*/tests/SEAL_COMMIT`. Pre-existing limitation (not introduced here); composes naturally with a follow-on "extend seal-discovery to plugins/" amendment when other plugins seal.

### v0.1.3 — item 1 (SKILL.md packages bundle) — sealed 2026-05-04

**Sub-plan:** `docs/plans/v0-1-3-skill-packages.md`.
**Manifest:** `docs/plans/v0-1-3-skill-packages.manifest.yaml` (amendment #124).
**Status file:** `<pos3>/workspace/.scratch/claude-output/v0-1-3-skill-packages-status-2026-05-04.md`.
**FIDRAFT provenance:** "Anthropic-perspective recommendation ladder (R.1-R.6)" item R.4 (2026-05-03).
**Decision locked:** Decision D in §5 — ship 5 packages (final set: `memory-recall`, `scope-decompose`, `dispatch-with-gates`, `onboarding-conversation`, `session-handoff`).

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `2c95507` | Sub-plan-doc; placement decision = `plugins/loam-skills/` (NEW component); AC family `AC.LSK.*` (collision-safe); 7 surfaces named pre-build. |
| Source edit | `059dc05` | NEW component `plugins/loam-skills/` — 5 × `skills/<name>/SKILL.md` + `pyproject.toml` + `README.md` + 3 × `test_AC_LSK_{1,2,3}_*.py` (43 parametric tests) + `test_no_sealed_amendments.py` + `SEAL_COMMIT` sidecar. Tier K append in `install-from-source.txt` + `docs/install-from-source.md`. |
| Manifest | `6749f44` | Amendment #124; baseline `059dc05`; single-component fence on `plugins/loam-skills/`; `extra_allowed_files` admits Tier K install paths. |
| `loam amend apply` (auto-commit) | `bb9bcb1` | Auto-committed per v0.1.2 item 6 (`2c32c1b`). Sidecar SEAL_COMMIT `2c95507` → `059dc05`; BASELINE literal bump; `allowed_files` += `[docs/odd-in-loam.md, docs/odd-methodology.md]` (universal admissions). |
| `loam amend seal` | `f04e925` | Deterministic seal commit. Narrative at `plugins/loam-skills/tests/SEAL_COMMIT.notes`. Used `--allow-untracked-globs` for 12 unrelated dirty paths. |

**Acceptance summary:**
- AC.LSK.1 (5 SKILL.md packages present and well-formed) — verified by `test_AC_LSK_1_skill_packages_present.py` (6 tests pass: per-package shape + cross-check that exactly 5 are discovered).
- AC.LSK.2 (frontmatter follows Anthropic SKILL.md schema) — verified by `test_AC_LSK_2_frontmatter_well_formed.py` (20 tests pass: directory-name kebab-case + name-field-matches-dir + description-trigger-phrase + no-unknown-fields per package).
- AC.LSK.3 (body content shape) — verified by `test_AC_LSK_3_body_content_shape.py` (15 tests pass: required-sections + loam-pattern-reference + raw-claude-code-degradation per package).
- AC.LSK.S (single-component fence on `plugins/loam-skills/`) — verified post-seal: `git diff 2c95507..f04e925 --name-only` = 16 paths; 12 in `plugins/loam-skills/`, 1 in `docs/plans/` (universal), 2 in install-from-source admissions, 1 manifest YAML — all admitted; zero outside.

**Smokes (pre-seal):**
- Smoke A: all 5 SKILL.md frontmatters parse cleanly; descriptions 432–533 chars (well under 1536 cap); each carries trigger-phrase clause.
- Smoke C: `pip install -e ./plugins/loam-skills` → `loam-plugin-loam-skills 0.1.0`. Filesystem walk finds all 5 SKILL.md files at the canonical paths.
- Smoke E: `pytest plugins/loam-skills/tests/` → 43 passed in 0.06s.

**Surfaces recorded (out of v0.1.3-item-1 scope; carried forward):**
- Migration of existing flat-shape skills (`plugins/dev-sdlc/skills/start-project.md`, `framework/primary-persona/skills/memory-{search,archive}.md`) to modern directory-per-skill shape — out of fence; v0.2+ if Anthropic discovery requires it.
- Live `claude` binary discovery smoke (boot-claude-in-fixture) — out of fence; static-walk smoke is sufficient at amendment-cycle level. Can land in v0.2 if regression coverage is desired.
- `dev-mode-manifest.yaml` update for `plugins/loam-skills/` — `roots:` doesn't include `plugins/*` by default; same treatment as `plugins/dev-sdlc/`. Follow-on amendment if dev-mode loading wants to surface to the persona.
- PyPI publish — deferred to v0.2 per the broader publish gate.
- Cross-component sweep discovery extension to `plugins/*/tests/SEAL_COMMIT` — pre-existing limitation (not introduced here); reused workaround from v0.1.2 item 6 (touched-only run + manual verification).

### v0.1.3 — M-FBM operational-health amendment (`AC.MFBM-OPS.*`) — sealed 2026-05-04

**Sub-plan:** `docs/plans/m-fbm-operational-health.md`.
**Manifest:** `docs/plans/m-fbm-operational-health.manifest.yaml` (amendment #125).
**Status file:** `<pos3>/workspace/.scratch/claude-output/m-fbm-operational-health-status-2026-05-04.md`.
**Diagnosis trigger:** `<pos3>/workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md` — Luke's M-FBM worker died on 2026-05-01, 175-item queue backlog accumulated over 3 days while structural ACs (`AC.MFBM.*`, `AC.J.*`) passed throughout.
**FIDRAFT entry added (1):** "Stale amendment-test launchd plists litter `~/Library/LaunchAgents/` — sweeper CLI subcommand to evict orphans" — captures the empirical correction to the diagnosis's plist-Label-collision hypothesis (namespacing was already in place via amendment #6) plus the follow-on sweeper CLI item.

| Step | Commit SHA | Notes |
|---|---|---|
| Plan-doc | `f50647f` | Sub-plan-doc; two-component fence on `framework/primary-persona/` + `framework/workspace-bootstrap/`; AC family `AC.MFBM-OPS.*` (collision-safe); 7 surfaces named pre-build (incl. Surface #1 dispatch-fence-correction + Surface #2 plist-collision empirical correction). |
| Source edit | `c8de8e3` | `memory_write_queue.py`: `heartbeat_interval_iterations` key added to `DEFAULT_WORKER_CONFIG` (default 60). `memory_write_worker.py`: `run_worker_loop` emits `worker-heartbeat` NDJSON every N iterations carrying `pid` + `iteration` + `queue_depth` + `ts`. Five new test files: 4 in `framework/primary-persona/tests/` (`test_AC_MFBM_OPS_{1,2,3,6}_*.py`) + 1 in `framework/workspace-bootstrap/tests/` (`test_AC_MFBM_OPS_5_*.py`). |
| Manifest | `c7c429c` | Amendment #125; baseline `c8de8e3`; two-component fence on primary-persona + workspace-bootstrap. FIDRAFT plist-sweeper entry committed in lock-step. |
| `loam amend apply` (auto-commit) | `dc408f7` | Auto-committed per v0.1.2 item 6. Both BASELINE literals + both SEAL_COMMIT sidecars bumped to `c8de8e3`. |
| `loam amend seal` | `1a1f830` | Deterministic seal commit. Narrative at `framework/primary-persona/seals/SEAL_COMMIT.m-fbm-operational-health`. Stash-then-pop workaround for unrelated dirty paths. |

**Acceptance summary:**
- AC.MFBM-OPS.1 (queue empties under N=10 enqueue load) — verified by `test_AC_MFBM_OPS_1_queue_stability_under_load.py` (2 tests: post-drain counters all-OK + queue dir empty; FIFO ordering pin).
- AC.MFBM-OPS.2 (`service_label` workspace-slug-namespaced contract) — verified by `test_AC_MFBM_OPS_2_worker_liveness_label_contract.py` (5 tests: `pos3` slug + `alpha-ws` slug + `ivers-corp-pos-v2` slug + distinct-slugs-yield-distinct-Labels + unknown-kind-raises).
- AC.MFBM-OPS.3 (recent-episode floor) — verified by `test_AC_MFBM_OPS_3_recent_episode_floor.py` (2 tests: drain produces episode file with mtime ≥ enqueue-moment + body carries user/assistant turn text).
- AC.MFBM-OPS.5 (scaffold-output plist Label namespacing) — verified by `test_AC_MFBM_OPS_5_plist_label_workspace_slug.py` (3 tests: `pos3` workspace yields `com.loam.pos3.memory-write-worker.plist` + `alpha-ws` workspace yields `com.loam.alpha-ws.memory-write-worker.plist` + no `com.loam.ws.memory-write-worker.plist` is ever produced).
- AC.MFBM-OPS.6 (`worker-heartbeat` periodic emission) — verified by `test_AC_MFBM_OPS_6_worker_heartbeat_emission.py` (4 tests: emission-every-iteration with `every=1` + payload-shape (`pid`/`iteration`/`queue_depth`/`ts`) + emission-skipped-between-intervals with `every=10` + `queue_depth` reflects un-drained entries when client is unavailable).
- ODD §2.5 negative AC (no out-of-fence edits) — verified post-seal: fence diff confined to `framework/primary-persona/` + `framework/workspace-bootstrap/` + `docs/plans/` (universal) + `docs/FUTURE_IDEAS_DRAFT.md` (universal).

**Touched-only test verification (pre-seal):**
- `framework/primary-persona/tests/` — 544 passed.
- `framework/workspace-bootstrap/tests/` — 247 passed, 11 skipped pre-existing.

**Halt-and-surface findings (recorded; non-blocking):**
- Surface #1 — dispatch's stated fence `framework/framework/memory-system/` was incorrect; actual code lives in `framework/primary-persona/` (worker source) + `framework/workspace-bootstrap/` (plist generator). Resolved autonomously by re-fencing per ODD §1.1.
- Surface #2 — dispatch's hypothesised plist-Label collision (generic `com.loam.ws.memory-write-worker` Label hijackable across workspaces) was empirically incorrect; namespacing was already in place via amendment #6. Production plist on Luke's machine is correctly `com.loam.pos3.memory-write-worker.plist`. AC.MFBM-OPS.5 retained as regression-pin (preserves the existing namespacing as a tested invariant); FIDRAFT entry corrected from "fix collision" to "stale-plist-clutter sweeper CLI".

**Surfaces recorded (out of `AC.MFBM-OPS.*` scope; carried forward):**
- AC.MFBM-OPS.4 (retrieval-quality / non-probe-episode floor) — soft objective; deferred to v0.1.4+ if needed.
- AC.MFBM-OPS.7 (reboot resilience via bootout+bootstrap launchctl integration) — fragile in CI; deferred.
- Stale-amendment-plist sweeper CLI subcommand — captured as FIDRAFT entry; likely lands in `plugins/dev-sdlc/tools/` as a follow-on amendment.
- Log-rotation for `memory-write-worker.{out,err}.log` and `memory-writes.log` — separate FIDRAFT-worthy item; not blocking.

---

*End of v0.1.x roadmap. Five releases. ~12–22 h AI total. Iterate-in-public cadence.*

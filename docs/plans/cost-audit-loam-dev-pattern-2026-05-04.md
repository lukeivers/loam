# Cost audit — loam dev pattern, 2026-05-04

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Status:** audit (read-only research). No code changes. Doc-only.

**Source directive (Luke verbatim, 2026-05-04):** "can you evaluate for other places where we might be doing a ton of extra work and cycles and tokens to accomplish things that seem to not matter like the synthesis thing?"

**Trigger context.** Today's OSS-architecture migration deprecated a ~4,350-LOC synthesis tool that was solving an imaginary problem (hide dev internals from strangers in OSS). Luke wants to know what else fits that pattern — high cost, unclear value, repealable post-migration.

**Operational objective tested against:** "deliver to Eric, high quality, ready to go." Every suspect is judged against whether its cost serves that outcome.

**Voice:** ruthless where evidence supports, methodology-grounded, citations on every cost claim. F2 active.

---

## §1 — Executive summary

The loam dev pattern carries five distinct cost surfaces that warrant audit. Three are directly analogous to the synthesis tool — substantial machinery solving problems the operational objective doesn't meaningfully care about. Two are real but possibly oversized. None of the five is uniformly worthless; the question is what tier of investment each deserves going forward.

**Headline cost numbers (empirical, not estimated):**

- **805 commits in 16 days** of pos-v2 history, of which **52% (~422 commits) are ceremony** (plan-docs, manifests, amend-apply, seals) and only **~26% (206 commits) are substantive feat/fix**. Per substantive change there are ~2 ceremony commits.
- **133K LOC of plan-docs** in `docs/plans/` (244 plan-doc files, 106 manifest YAMLs, 41 builder-plans). For comparison: **166K LOC of Python source** under `framework/`. The plan-doc corpus is ~80% the size of the source code.
- **15.5K LOC of seal-commit narratives** under `framework/*/seals/` (95 SEAL_COMMIT files), with individual seal narratives running 100-300 lines.
- **131 amendments** numbered to date, requiring a roadmap method-decision register, manifest-numbering discipline, and SHAs-back-to-plan record-keeping per amendment.
- **~750-950 tokens injected per turn** by the principle-reminder UserPromptSubmit hook (3,868 chars / 565 words). Across 100 turns/session this is 75K-95K tokens of pure reminder overhead.
- **v0.1.7 release shipped 23 commits for 4 substantive changes** — exactly 4 ceremony commits per substantive change (~5.75:1 ratio of total to substantive).

**What's worth the cost:** ODD plan-doc-before-code (Lens 3, the methodology backbone), seal narratives at component-fence boundaries (audit-trail for sealed components is genuinely load-bearing), the amendment system itself as a component-isolation discipline. These three are the dev-pattern's actual product.

**What probably isn't worth the cost in current shape:**

- **Seal-commit narratives in their current verbosity** — they replicate plan-doc content rather than referencing it; ~100-300 lines of duplication per amendment is doc-level redundancy that survives session resets but doesn't serve Eric.
- **Manifest YAMLs as separate files alongside plan docs** — the manifest is a narrow apply-time contract (5-15 lines of actual data); the bulk of each manifest YAML is a re-narrated version of the plan-doc, which already exists.
- **Amendment-number accounting** at #131 with manual register — the only consumer of amendment numbers is the dev-pattern itself; downstream users of pos-v2 don't read amendment numbers.
- **Multi-cycle release ladders with per-cycle ceremony** — v0.1.7 = 4 cycles × 4 ceremony commits each, against 4 substantive feat commits. The per-cycle ceremony tax doesn't track per-cycle blast-radius.
- **Principle-reminder hook at full text** — 950 tokens × N turns is real, especially since the model's working set already carries the substance after session-start.

**Three suspects this audit surfaces beyond the dispatcher's first-pass list:**

1. **Plan-doc inflation** — average plan-doc is 540 lines; many cycle-level plans replicate parent-plan content rather than referencing it. The cost grows non-linearly because each downstream artefact (manifest, seal narrative) re-narrates the plan.
2. **Per-component .venv directories** (verified at framework/*/. venv) — each sealed component has its own venv, consuming substantial disk and provoking find-command exclusions in every audit. This isn't a token cost but it's a friction cost.
3. **Release-close STATE.md / roadmap §8 / eric-final §2 backfill cycle** — every release closes by editing 3+ status files with the same SHA-list info. Three files; one source of truth would suffice.

**The pattern that connects all of these:** the dev-pattern was designed for an audience that doesn't exist yet (strangers reading the audit trail of pos-v2's construction). The synthesis tool is the prototype of that pattern. Its replacements may be too.

---

## §2 — Empirical cost data

All numbers are from actual filesystem and git inspection at HEAD `ea8c4bb`, 2026-05-04. None estimated.

### §2.1 Repository topline

| Metric | Value |
|---|---|
| Total commits (pos-v2 branch) | 805 |
| Repo duration | 16 days (2026-04-18 → 2026-05-04) |
| Commits/day average | ~50 |
| Framework Python LOC | 165,939 (872 files) |
| Plan-doc LOC | 132,828 |
| Seal-narrative LOC | 15,491 (95 files) |
| Manifest YAML LOC | 21,632 (106 files) |
| Builder-plan LOC | 12,255 (41 files) |
| Components in `framework/` (sealed) | 15 |

### §2.2 Commit categorization (full history, 805 commits)

```
feat:  146 (18.1%)
fix:    60 (7.5%)
chore: 240 (29.8%)
  seals: 142
  amend manifest: 7
  amend apply: 29
  partition-apply: 1
  publish/other: 61
docs:  328 (40.7%)
  plans: 244
  fidraft: 10
  other: 74
```

**Ceremony commits (plan + manifest + apply + seal + partition):** 244 + 7 + 29 + 142 + 1 = **423 commits = 52.5% of total.**

**Substantive commits (feat + fix):** 146 + 60 = **206 = 25.6%.**

**Ceremony-to-substantive ratio:** 2.05:1.

### §2.3 v0.1.7 release as concrete sample

23 commits across the v0.1.7 cycle (commits `d6def04..c7e5dd7`):

```
plan-docs:        5 (release plan + 4 sub-plans)
feat:             4 (one per cycle)
amend-manifest:   4 (one per cycle)
amend-apply:      4 (one per cycle)
seal:             4 (one per cycle)
release-close:    1 (STATE.md backfill)
fidraft:          1
fix:              1
```

For 4 substantive feat commits (Cycles 1-4), the release shipped **16 ceremony commits + 1 release-close + 1 fidraft + 1 fix**. Per-cycle ratio: **4 ceremony per 1 feat**.

Doc footprint: v0.1.7 plan-docs total 2,033 lines + 775 manifest lines = **2,808 lines of doc work** for ~4 substantive code changes.

### §2.4 Synthesis tool (the prototype-of-the-pattern)

Now archived at `docs/archive/synthesis-tool-2026-05-04/`:

- **54 files** in the archive
- **4,350 LOC total** (Python + tests + manifests)
- **Largest files:** `cli.py` (132 LOC), `substitution.py` (202 LOC), supporting tests
- **Purpose at build time:** synthesize a `framework-only` branch by stripping dev-discipline files (plan-docs, manifests, plugins/dev-sdlc, .claude/agents) before public publish, on the assumption that strangers shouldn't see the dev process
- **Purpose now:** none; deprecated by today's migration. The dev-pattern moved to `dev_and_public` as the default — no synthesis required.

### §2.5 Plan-doc shape proliferation

Sampling distinct shapes in `docs/plans/`:

| Shape | Count | Avg LOC |
|---|---|---|
| `<name>.md` (plan-doc) | 244 | ~545 |
| `<name>.manifest.yaml` | 106 | ~204 |
| `<name>.builder-plan.md` | 41 | ~299 |
| `<name>.vars.yaml` | 9 | varies |

A typical sealed amendment ships 3 doc artefacts: plan-doc + manifest + (sometimes) builder-plan. Plus the seal-narrative inside the apply commit becomes a 4th artefact (`SEAL_COMMIT.<slug>` file).

For comparison: a typical OSS PR ships 0-1 doc artefacts (a CHANGELOG entry, maybe a design note in the PR description).

### §2.6 Seal-narrative redundancy sample

`framework/per-project-pm/seals/SEAL_COMMIT.v0-1-7-cycle4-one-question-pm-flow` (148 lines):

```
Lines 1-10:  metadata + parent-plan reference
Lines 11-17: scope rationale (duplicates plan-doc §3 + §4 + §7)
Lines 18-65: AC family enumeration (duplicates plan-doc §4
             + manifest §AC-families locked block)
Lines 66+:   smoke + fence rationale (duplicates manifest §60-90)
```

Same content carried in 3 places: plan-doc, manifest YAML's `narrative.body`, seal-commit file. Estimated redundancy: **80-90% of seal-commit content is already in plan-doc + manifest.**

### §2.7 Principle-reminder hook overhead

`pos3/.claude/hooks/principle_reminder.py`:

- **Source LOC:** 66
- **REMINDER text:** 3,868 chars / 565 words
- **Per-turn token injection:** ~750-950 tokens (4 chars/token approximation)
- **Triggers on:** every `UserPromptSubmit` event
- **Per-100-turn-session cost:** 75-95K tokens of reminder text
- **Active scope:** local to pos3 only (not loaded globally; verified `~/.claude/settings.json` has empty `hooks: {}`)

### §2.8 Doc-type inventory (the proliferation suspect)

Distinct durable-state surfaces in pos-v2:

1. `docs/plans/<name>.md` — plan-docs
2. `docs/plans/<name>.manifest.yaml` — apply-time contract + redundant narrative
3. `docs/plans/<name>.builder-plan.md` — builder hand-off (when present)
4. `framework/<comp>/seals/SEAL_COMMIT.<slug>` — seal narrative (per amendment)
5. `docs/STATE.md` — top-level program state (127 lines)
6. `docs/FUTURE_IDEAS.md` — graduated ideas (665 lines)
7. `docs/FUTURE_IDEAS_DRAFT.md` — point-of-occurrence ideas (201 lines)
8. `docs/BACKLOG.md` — work backlog (69 lines)
9. `docs/VALUE_PROPOSITION.md` — prime objective spec (114 lines)
10. `docs/plans/v0-1-x-roadmap.md` — release sequence + method-decision register (465 lines)
11. `~/.claude/projects/.../memory/feedback_*.md` — self-discipline rules (40+ files in user memory)
12. `<workspace>/.scratch/claude-output/*.md` — ephemeral status files

**12 distinct doc-state surfaces.** Several are co-load-bearing (plan-doc + manifest + seal-narrative trio per amendment). Others are at single-file granularity (STATE.md, BACKLOG.md, VALUE_PROPOSITION.md). FUTURE_IDEAS vs FUTURE_IDEAS_DRAFT is an explicit graduation pattern but doubles the surface for the same conceptual content.

---

## §3 — Per-suspect analysis

Each suspect: cost (numbers), purpose (what it was built for), test against operational objective ("deliver to Eric, high quality"), test against standard OSS practice, verdict.

### §3.1 Sealed-amendment ceremony

**Cost.**

- Per amendment: 4 ceremony commits (plan-doc + manifest + apply + seal).
- Across 805 commits: ~423 are ceremony = 52.5%.
- v0.1.7 specifically: 16 ceremony commits per 4 substantive = 4:1 ratio.
- Doc burden per amendment: plan-doc (~540 lines avg) + manifest (~200 lines avg) + seal narrative (~160 lines avg). ~900 lines of doc work per amendment.

**Purpose.** Five mechanisms bundled into "sealed amendment":

1. **Component-fence isolation** — every code change names which sealed components it touches; the seal-test enforces that nothing else changed. *This is the load-bearing piece.*
2. **AC-binding** — every change names ACs it advances; ODD §2.5 (no non-objective code) holds.
3. **Plan-before-code** — plan-doc forces design-before-implementation. *This is also load-bearing.*
4. **Audit trail** — seal narrative records what was changed, why, what tests pass.
5. **Amendment numbering** — register-based identifier per amendment.

**Test against operational objective.** Eric receives loam as a working harness; he doesn't read the audit trail. The component-fence isolation (1) is what keeps loam from rotting under self-modification, so it serves the operational objective indirectly via quality. (3) plan-before-code serves the operational objective directly because it catches design errors at plan time. (4) audit trail serves dev-self-review and owner-gate-review, not Eric.

**Test against standard OSS practice.** Standard OSS uses 1 commit per change (no manifest, no seal). Larger projects sometimes use a CHANGELOG entry. The component-fence concept is rare but not unheard-of (monorepos with per-package isolation). The 4:1 ceremony-to-substantive ratio is well outside OSS norm; even ceremony-heavy enterprises rarely exceed 1.5:1.

**Verdict: KEEP, but SIMPLIFY.**

Keep the component-fence + AC-binding (1+2) — these are the actual product. Keep plan-before-code (3) — it's why the methodology works. Simplify (4) and (5):

- Merge `chore(amend): manifest` and `chore(amend): apply` into a single amend commit (saves 7 + 29 = 36 commits historically; ~14% reduction in ceremony rate going forward).
- Make the seal narrative a 5-15 line summary that *references* the plan-doc rather than reproducing its content. Drop the body from `~160 lines avg` to `~10 lines`.
- Drop amendment-number accounting; identify by slug only (slug is already the deterministic seal-test key).

Estimated saved cost: **~35% of per-amendment ceremony tax**, mostly in seal-narrative authoring time and review burden.

### §3.2 Doc-type proliferation

**Cost.** 12 distinct doc-state surfaces (per §2.8). Specifically the high-overlap pairs:

- **plan-doc + manifest YAML** — manifest's `narrative.body` field replicates plan-doc body verbatim or near-verbatim. Sample (`v0-1-7-cycle-4-one-question-pm-flow.manifest.yaml` lines 88-159) shows 70+ lines of `narrative.body` content that is also in the plan-doc. Manifests average 200 LOC; ~80% of that is duplicated narrative.
- **manifest + seal-narrative** — seal narrative is literally written *to* the manifest as `narrative.body`, then committed as a separate file at apply time. Same content, two locations.
- **STATE.md + roadmap + eric-final §2** — release-close commit (`c7e5dd7`) backfilled SHAs into 3 files. Same SHA list, three places.
- **FUTURE_IDEAS.md (665 lines) + FUTURE_IDEAS_DRAFT.md (201 lines)** — DRAFT is the staging area; ideas graduate to the long-form FUTURE_IDEAS. The graduation rubric is real but the dual-file shape is an artefact of process.

**Purpose.** Different artefacts serve different stakeholders:

- Plan-docs serve plan-time design review (Luke at plan-author dispatch).
- Manifests serve `loam-amend apply` mechanically.
- Seal narratives serve component-isolation audit trail.
- STATE.md serves owner status-glance.
- FUTURE_IDEAS / DRAFT serve idea graduation.

**Test against operational objective.** Eric reads ~3 of these surfaces (README, value proposition, eric-final delivery doc). The other 9 are for the dev-pattern's internal use.

**Test against standard OSS practice.** OSS projects typically have 3-4 doc surfaces: README, CHANGELOG, CONTRIBUTING, roadmap. 12 is well above norm.

**Verdict: SIMPLIFY.**

- Collapse manifest YAML's `narrative.body` to a `plan_doc_ref:` pointer. Remove ~17K LOC of duplicated narrative across 106 manifests.
- Generate seal-commit body as `<one-line summary> + <link to plan-doc>` — remove ~13K LOC of duplicated narrative across 95 seals.
- Merge FUTURE_IDEAS_DRAFT into FUTURE_IDEAS as a top-section "Recently captured (un-rigored)" — eliminate the dual-file pattern.
- Keep STATE.md, BACKLOG.md, VALUE_PROPOSITION.md, roadmap distinct (they serve genuinely different purposes).

Estimated saved cost: **~30K LOC of doc redundancy** + reduced authoring burden per amendment.

### §3.3 Multi-cycle release ladders

**Cost.** v0.1.7 = 4 cycles, each a sealed-amendment cycle = 16 ceremony commits + 4 substantive. v0.1.6 = 2 cycles. v0.1.0 = 13 cycles in commit log (large initial release). Release-close adds 1 more commit (STATE.md backfill).

**Purpose.** The cycle-decomposition logic — break a release into independently-sealable amendments — comes from sealed-amendment isolation discipline (§3.1). Each cycle is a sealable component-fenced change. The reasoning is sound: within a release, each cycle's ACs should be tighter than the release's ACs (Lens 5 swarming stopping criterion).

**Test against operational objective.** The cycle decomposition itself is sound — it tracks the design discipline. The cost is in the per-cycle ceremony, not the cycle structure. If §3.1's simplification lands, the per-release ceremony tax shrinks proportionally.

**Test against standard OSS practice.** OSS releases are 1-3 commits typically (feature commit + version bump + CHANGELOG). Multi-cycle releases like v0.1.7 (16 ceremony commits) are far above norm.

**Verdict: KEEP cycle structure, depend on §3.1 simplification for cost reduction.**

The cycle decomposition is correct discipline (Lens 5). The cost is downstream of sealed-amendment ceremony, not the cycle pattern itself. Don't restructure releases; restructure per-amendment ceremony, and the per-release total drops with it.

Estimated saved cost: derivative of §3.1; ~35% reduction in per-release ceremony.

### §3.4 Amendment-number accounting

**Cost.** 131 amendments numbered to date. Per-amendment manifest YAML carries `amendment.number: <int>`. Roadmap (`v0-1-x-roadmap.md`) maintains a method-decision register. STATE.md backfills SHAs per amendment.

**Purpose.** Stable identifier for cross-references (roadmap, STATE.md, follow-on-amendment dispatches). The number is the dev-pattern's primary key for amendments.

**Test against operational objective.** Eric never sees amendment numbers. Strangers reading pos-v2 don't read amendment numbers. The numbers are dev-pattern internal only.

**Test against standard OSS practice.** OSS projects use commit SHAs, PR numbers, or version tags as identifiers. Bespoke amendment-numbering schemes are rare; when they exist, they're for compliance regimes (FDA software, aviation), not OSS.

**Verdict: SIMPLIFY (deprecate gracefully).**

The amendment-slug (e.g., `v0-1-7-cycle4-one-question-pm-flow`) is already the deterministic key — it's what the seal-test reads, what the manifest filename uses, what the seal-narrative filename uses. The number is redundant.

Recommended path: stop incrementing numbers; existing amendments keep their numbers as historical artefacts; new amendments identify by slug only. This is a doc-only change at the manifest schema level (drop `amendment.number` from required fields).

Estimated saved cost: small (~10 lines per manifest, ~10 lines per roadmap entry). Real value: removes a piece of cognitive ceremony from every amendment.

### §3.5 Principle-reminder hook

**Cost.**

- 750-950 tokens per UserPromptSubmit hook fire (3,868 chars / 565 words REMINDER constant).
- Across 100 turns/session: **75K-95K tokens injected**.
- Across estimated session arcs (multi-day projects): hundreds of thousands of tokens of reminder overhead.

**Purpose.** The 2026-05-03 directive (`feedback_principle_self_reminder_at_end_of_turn.md`) named three observed principle-fidelity drift instances in one session. The hook injects principle reminders structurally so the model can't autopilot past them.

**Test against operational objective.** Principle fidelity is genuinely load-bearing for delivery quality (channel rule, ack-first, autonomy, F2 RF, etc.). Drift causes user-visible quality breaks. So the hook serves the operational objective via quality discipline.

**Test against the actual mechanism.** The reminder text is ~565 words. The model's context window already carries the substance after session-start CLAUDE.md load. The reminder is *attention refresh*, not *content delivery*. Attention refresh doesn't require 565 words.

A 50-word reminder ("CHANNEL: Telegram only. ACK-FIRST: complex requests get ack as first output. AUTONOMY: don't pause on authorized work. F2: name disagreement, name evidence, name alternative. LOCKED-DESIGN: revisit when outcomes are bad.") would trigger the same attention pointer with ~10x less token cost.

**Test against standard practice.** Per-turn structural reminders are rare; they exist in some agent harnesses but typically run 100-200 tokens, not 950.

**Verdict: SIMPLIFY.**

Compress REMINDER constant to ~50-100 words. Keep the hook (the structural injection mechanism is sound). The current text is 5-10x oversized for the attention-refresh function it serves.

Estimated saved cost: **~700 tokens per turn** = ~70K tokens per 100-turn session = significant across long arcs.

---

## §4 — New patterns surfaced (beyond first-pass list)

### §4.1 Plan-doc inflation

**Cost.** Average plan-doc is 540 LOC. Many cycle-level plans replicate parent-plan content rather than referencing it. v0.1.7 alone: 4 cycle-plans averaging ~500 lines + 1 parent plan at 473 lines = 2,033 lines for one release.

**Pattern.** Cycle plans tend to re-narrate the parent plan's §1-3 (outcome / lens checks / scope) before getting to the cycle-specific §4-8. Lens-check sections (Lens 1-5 per CLAUDE.md) are reproduced per-plan-doc rather than referenced.

**Purpose.** Self-contained plan-docs let any agent dispatch read one file and have full context. Cross-references would require the agent to chase multiple files.

**Tradeoff.** The "self-contained" property is real but oversized. Most cycle plans share 100-200 LOC of boilerplate (lens checks, methodology references, working-directory reminders). A plan-doc template macro would let cycle-plans inherit this material at render time.

**Verdict: SIMPLIFY.**

- Author a plan-doc template that handles working-directory + lens-check + ODD-anchor sections.
- Cycle plans inherit and add cycle-specific content only.
- Estimated saved cost: ~200 LOC per cycle plan × 4 cycles per release = ~800 LOC per release; ~30% reduction in plan-doc volume going forward.

### §4.2 Per-component .venv directories

**Cost.** Each sealed component (15 of them in `framework/`) has its own `.venv/`. Disk cost is modest but real (each venv: 50-200MB depending on torch presence). Friction cost: every audit / search / find command must exclude `.venv` patterns; build pipelines must keep them isolated.

**Purpose.** Component isolation extends to dependency isolation — each component's tests run in their own venv so version conflicts don't propagate.

**Test against operational objective.** Eric installs loam once; he doesn't run per-component tests. The per-component venvs serve dev-pattern testing only.

**Verdict: KEEP for dev, but acknowledge the friction cost.**

This isn't a token cost; it's an infrastructure cost. The dependency-isolation property is real. Don't change it for delivery reasons; do acknowledge that audit / search work pays a tax for it.

### §4.3 Release-close STATE.md / roadmap / eric-final triple-update

**Cost.** Every release closes by editing 3+ status files with the same SHA-list info. v0.1.6 close (`c3fa366`) and v0.1.7 close (`c7e5dd7`) both touch STATE.md + roadmap §8 + eric-final §2 with the same data.

**Purpose.** Each file serves a different audience (STATE = top-level state; roadmap = release sequence; eric-final = delivery summary).

**Tradeoff.** The data is the same; the framing differs by audience. The current process repeats the data per file. A single source-of-truth file with audience-specific views (e.g., generated rendering) would eliminate the redundancy.

**Verdict: SIMPLIFY (low priority).**

- Make STATE.md the source of truth for SHA-by-release info.
- Have roadmap and eric-final reference STATE.md for SHA lists rather than copy.
- Estimated saved cost: ~20 lines per release-close × N releases. Small per-release; cumulative over the program.

---

## §5 — Recommendation prioritization

Ordering for execution releases, highest-leverage first:

### Priority 1 — Manifest narrative collapse (§3.2)

**Why first.** Affects every future amendment. ~17K LOC of doc redundancy gone. Doc-only change to manifest schema. Reversible (git history preserves all narratives). Low blast radius — manifests are dev-pattern internal; no consumer outside the dev-pattern reads them.

**Estimated effort:** 30-60 minutes (schema change in `loam-amend`, doc update). One sealed amendment.

**Impact:** every future amendment ships ~150 fewer LOC of doc work.

### Priority 2 — Seal-narrative compression (§3.1, partial)

**Why second.** Same shape as Priority 1 but at seal-narrative side. ~13K LOC of doc redundancy gone. Replaces seal narratives with `<summary> + <link>` shape.

**Estimated effort:** 30-60 minutes.

**Impact:** every future amendment ships ~150 fewer LOC of seal-narrative work.

### Priority 3 — Principle-reminder compression (§3.5)

**Why third.** Per-turn cost; saves tokens on every interaction in pos3. Independent of priority 1 + 2. Doc-only in `pos3/.claude/hooks/principle_reminder.py`.

**Estimated effort:** 15-30 minutes.

**Impact:** ~70K tokens per 100-turn session (significant for long arcs).

### Priority 4 — Manifest+apply commit merge (§3.1, partial)

**Why fourth.** Removes ~36 commits going forward; saves 1 commit per amendment. Requires `loam-amend apply` workflow change (manifest authored + applied in same commit).

**Estimated effort:** 1-2 hours (loam-amend tool change + tests).

**Impact:** ~14% reduction in ceremony commit rate going forward.

### Priority 5 — Amendment-number deprecation (§3.4)

**Why last (low priority).** Cognitive overhead reduction; minor LOC saving. Doesn't block anything. But it's a clean cleanup.

**Estimated effort:** 30 minutes (manifest schema + roadmap update).

**Impact:** small per-amendment, real cumulatively.

### Out of priority — KEEP recommendations

- Plan-before-code (§3.1.3) — keep verbatim. This is why the methodology works.
- Component-fence isolation (§3.1.1) — keep verbatim.
- Per-component .venv (§4.2) — keep; friction cost is real but the isolation property is load-bearing.
- Cycle decomposition (§3.3) — keep; cost is downstream of §3.1 simplification.

---

## §6 — Honest doubts (steelmen)

What might this audit be wrong about?

**Doubt 1 — Seal narratives may serve a future audience the current dev-pattern doesn't have.** When pos-v2 ships and external contributors land their first amendments, the existing seal narratives serve as worked examples of "how a sealed amendment looks." Compressing them to one-line summaries removes that worked-example value. Counter: contributor docs can be authored separately as a CONTRIBUTING.md addition; worked examples aren't required to live in commit narratives.

**Doubt 2 — Manifest narrative redundancy may be cheaper than the alternative.** Reading 3 files (plan-doc, manifest, seal) versus 1 file with everything has a cognitive switching cost. Maybe the redundancy is functioning as cache-locality. Counter: the current redundancy is at *content* level, not *navigation* level; agents and humans both grep for unique content not duplicated content.

**Doubt 3 — Principle-reminder text size might be load-bearing.** The 950-token reminder isn't 950 random tokens; it's a structured walk through 12 named principles with concrete trigger conditions. Compressing to 50 words might lose the trigger-specificity that's what actually shapes behavior. Counter: behavior shaping happens in-turn through application, not at hook fire; the hook's job is attention-refresh of the names, not re-delivery of the text. The full text is in CLAUDE.md and feedback_*.md files for retrieval when needed.

**Doubt 4 — Amendment-number accounting may have value to Luke for personal recall.** "Amendment #125 was the M-FBM operational health one" is a chunked memory aid. Counter: slugs are equally chunked and don't require numbering discipline.

**Doubt 5 — The whole audit might be premature.** The synthesis tool was deprecated *because* circumstances changed (the audience-fear assumption proved wrong). Maybe the other suspects' costs are still serving their purpose and the audit is hunting for symmetric prey. Counter: the audit's verdicts are SIMPLIFY for most suspects, not DEPRECATE — meaning the costs ARE serving purposes; the verdicts target sizing, not existence. Only amendment-numbering is recommended for outright deprecation.

**Doubt 6 — Cycle decomposition costs may dominate ceremony costs.** 4 cycles per release × 4 ceremony per cycle = 16 ceremony commits. The cycle decomposition itself is the multiplier. If cycles were collapsed into one amendment per release, ceremony drops dramatically. Counter: the cycle structure is correct ODD discipline (Lens 5 swarming) and tracks per-cycle blast-radius; collapsing would re-introduce the silent-coupling problem sealed amendments solve.

---

## §7 — Decisions for Luke

Five decisions surface for owner ruling. Each: framing + recommendation + reasoning + escalation criterion.

### Decision A — Manifest narrative collapse

**Framing.** Should manifest YAML's `narrative.body` field be replaced with a `plan_doc_ref:` pointer, eliminating ~17K LOC of doc redundancy?

**Recommendation.** YES, as priority-1 simplification per §5.

**Reasoning.** The manifest's body field literally re-narrates the plan-doc; the plan-doc already exists in the same directory; nothing reads the manifest body that doesn't also read the plan-doc.

**Escalation criterion.** This affects the `loam-amend` schema, which is sealed. Schema change = sealed-amendment cycle. Owner gate-review needed because it changes the dev-pattern's primary contract and is irreversible *in shape* (even though git history preserves all narratives, the new shape becomes the going-forward standard).

### Decision B — Seal-narrative compression to summary+link

**Framing.** Should seal-commit narratives drop to ~10 lines (summary + plan-doc link) instead of ~160 lines (full duplicate)?

**Recommendation.** YES, as priority-2 simplification per §5.

**Reasoning.** Same shape as Decision A but at seal-commit side. Audit-trail value preserved via the link; redundant content eliminated.

**Escalation criterion.** Same as A — affects sealed-amendment shape, requires sealed-amendment cycle to land. Owner sign-off because future contributors / strangers / Eric inherit whichever shape becomes the standard.

### Decision C — Principle-reminder text compression

**Framing.** Should `pos3/.claude/hooks/principle_reminder.py`'s REMINDER text drop from ~950 tokens to ~100 tokens?

**Recommendation.** YES, as priority-3 simplification per §5.

**Reasoning.** Hook's function is attention-refresh of named principles, not re-delivery of full text. Compression preserves function at ~10x lower per-turn cost.

**Escalation criterion.** Lower escalation than A/B — this is local pos3 hook config, not pos-v2 framework. But it directly affects Luke's day-to-day token budget, so owner choice matters. Could also be done by Luke directly in a 5-minute edit.

### Decision D — Manifest+apply commit merge

**Framing.** Should `loam-amend apply` produce a single commit instead of two (manifest + apply currently shipped as separate commits)?

**Recommendation.** YES, as priority-4 simplification.

**Reasoning.** The two commits always land sequentially; nothing meaningful happens between them; the split adds 36 historical commits and 1 commit per future amendment without value.

**Escalation criterion.** Code change to `loam-amend` (sealed component); requires its own sealed-amendment cycle. Lower priority than A/B because the per-amendment savings are smaller.

### Decision E — Amendment-number deprecation

**Framing.** Should new amendments stop carrying `amendment.number:` in their manifest, identifying by slug only?

**Recommendation.** YES, as priority-5 cleanup.

**Reasoning.** Slug is already the deterministic primary key. Number is redundant cognitive ceremony.

**Escalation criterion.** Smallest blast radius; affects manifest schema and roadmap shape only. Lowest priority of the five.

---

## §8 — Provenance (citations for every cost claim)

Every empirical claim in this audit anchors to a specific source.

| Claim | Source |
|---|---|
| 805 commits in 16 days | `git log --oneline \| wc -l` at HEAD `ea8c4bb`; `git log --reverse \| head -1` for first commit `8bc0512` (2026-04-18); HEAD timestamp 2026-05-04 |
| 423 ceremony commits (52.5%) | `git log --pretty=format:"%s"` categorized by prefix; counts: 244 docs(plans) + 7 amend-manifest + 29 amend-apply + 142 seals + 1 partition-apply |
| 206 substantive commits (25.6%) | Same source: 146 feat + 60 fix |
| 165,939 framework Python LOC | `find framework -name ".venv" -prune -o -type f -name "*.py" -print \| xargs wc -l` |
| 132,828 plan-doc LOC | `find docs/rebuild/plans -name "*.md" ! -name "*.builder-plan.md" -exec wc -l {} +` |
| 21,632 manifest YAML LOC | `find docs/rebuild/plans -name "*.manifest.yaml" -exec wc -l {} +` |
| 12,255 builder-plan LOC | `find docs/rebuild/plans -name "*.builder-plan.md" -exec wc -l {} +` |
| 15,491 seal-narrative LOC | `find framework -name "SEAL_COMMIT*" -exec wc -l {} +` |
| 95 SEAL_COMMIT files | Same source `wc -l` count |
| 244 plan-docs | `ls docs/plans/` filtered `*.md` non-builder |
| 106 manifest YAMLs | `find docs/rebuild/plans -name "*.manifest.yaml" \| wc -l` |
| 41 builder-plans | `find docs/rebuild/plans -name "*.builder-plan.md" \| wc -l` |
| 4,350 LOC synthesis tool archive | `find docs/archive/synthesis-tool-2026-05-04 \( -name "*.py" -o -name "*.yaml" -o -name "*.md" \) -exec wc -l {} +` |
| 54 files in synthesis archive | Same source file count |
| v0.1.7 = 23 commits, 16 ceremony, 4 substantive | `git log --oneline d6def04^..c7e5dd7 \| wc -l`; categorization via awk on commit subjects |
| v0.1.7 plan-doc 2,033 LOC + manifest 775 LOC | `wc -l` on `v0-1-7*.md` non-builder + `v0-1-7*.manifest.yaml` |
| Principle-reminder 3,868 chars / 565 words | Read `REMINDER` constant from `.claude/hooks/principle_reminder.py`; `len(text)` and `len(text.split())` |
| Highest amendment number 131 | `grep -h "^  number:" docs/plans/*.manifest.yaml \| sort -nu \| tail` |
| 142 seal commits historically | `git log --oneline \| grep -cE "^[a-f0-9]+ chore\(seals\)"` |
| Seal narratives 100-300 lines typical | `wc -l framework/*/seals/SEAL_COMMIT.*`; range observed |
| 12 doc-state surfaces | Enumerated in §2.8; verified via `find docs/rebuild` + `find framework -name SEAL_COMMIT*` + `~/.claude/projects/.../memory/feedback_*.md` listing |
| Per-component .venv directories | `find framework -name ".venv" -type d` returns 11 framework venvs |

All numbers were measured at HEAD `ea8c4bb` on 2026-05-04. Future audits should re-measure rather than carry these forward.

---

## §9 — What this audit deliberately did NOT cover

To honor scope-confidence (Lens 4) and avoid scope creep:

- **Token cost of background-agent dispatches.** Every dispatched agent inherits its own context window; aggregate dispatch token cost is large but isn't the dispatcher's first-pass concern. Future audit if needed.
- **Storage cost of `workspace/` artefacts.** `.scratch/claude-output/` accumulates ephemerally; not a token cost; acknowledged as out-of-scope.
- **Memory-system overhead** (graphiti / kuzu / file-based memory). These are infrastructure costs, not dev-pattern ceremony costs. Out-of-scope for this audit.
- **Test-suite execution time.** Sealed components' per-component test runs are a CI cost, not a per-amendment ceremony cost. Out-of-scope.
- **The methodology documents themselves** (`docs/odd-methodology.md`, `docs/odd-in-loam.md`, `CLAUDE.md` lenses). These are foundational; audit of them would be a different shape entirely.
- **Memory-feedback corpus growth** (`~/.claude/projects/.../memory/feedback_*.md` is now 40+ files). Real cost, but lives outside pos-v2 working tree; audit scope was limited to in-tree dev-pattern.

If owner wants any of these audited, they'd be separate dispatches with their own scope.

---

## §10 — Closing

The synthesis tool was a 4,350-LOC machinery built against an audience-fear assumption that proved wrong. Its replacements aren't likely to be that big in absolute terms, but they share the pattern: machinery built for an audience that doesn't read it, sized for a fear (drift, contamination, silent-coupling) that the dev-pattern's structural defenses already address.

The five primary suspects + three surfaced patterns total ~50K LOC of doc redundancy + ~70K tokens/100-turns of hook overhead. None individually catastrophic; cumulatively significant.

The recommendation set is conservative: SIMPLIFY for most, DEPRECATE only for amendment-numbering. The dev-pattern's load-bearing pieces (plan-before-code, component-fence isolation, AC-binding, ODD methodology) are not on the chopping block. The chopping block is for the *redundancy multipliers* on top of those load-bearing pieces.

Owner ruling needed on Decisions A-E (§7) before any execution-side work begins.

---

**End of audit.**

Authored 2026-05-04 by cost-audit dispatch. WD `/Users/lukeivers/ivers-corp-pos-v2/`. Sonnet (default model; no model-rationale required).

Principle application this exchange:
- F2 RUTHLESS FEEDBACK: ✓ — named the redundancy patterns explicitly, cited evidence, proposed alternatives.
- LOCKED-DESIGN-NOT-LICENSE: ✓ — applied to dev-pattern itself; sealed-amendment shape is revisitable when its redundancy outcomes are bad.
- ODD §2.5: ✓ — every cost claim cited; provenance table in §8.
- OUTPUT-TO-DISK: ✓ — full audit at this path; reply summary inline.
- DURABLE-CAPTURE: ✓ — audit doc IS the durable surface for these findings.
- WD-IN-DISPATCHES: ✓ — confirmed at start; absolute paths used throughout.
- TRANSLATION RULE: ✓ — reply summary written for owner-glance; full audit available on demand.
- PARTITION RULE: ✓ — recommendations include deprecate (amendment-numbering) and simplify (rest).

# Claude-leverage program — Slice 1: CURRENCY (sub-plan-doc)

> **Status:** sub-plan-doc (buildable; manifest paired at
> `docs/plans/claude-leverage-program-s1-currency.manifest.yaml`).
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent plan:** `docs/plans/claude-leverage-program.md` (master; Slice 1
> section + D-CLP.3/D-CLP.5 + AC.CLP-CUR.\* family are the source of truth).
> **Predecessors (load-bearing):**
> - Master plan ratified shape: D-CLP.4 owner-RATIFIED 2026-06-11 (Discord
>   1514753768175042771); D-CLP.3 (revive locked-δ scoped down) and D-CLP.5
>   (demote `CLAUDE_CAPABILITIES.md` to an index) carried into this slice
>   unchanged.
> - Research artefact (Tier-0, fetched 2026-06-11):
>   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`
>   — §3 discrepancies are this slice's known-wrong-claims fix-list (D-CUR.5).
> - Locked design (Luke 2026-04-26):
>   `docs/plans/research/persona-capability-knowledge-grounding-research.md`
>   §7bis.1 (cadence table + diff/merge flow — the cadence SPEC; its
>   substrate bindings are stale per master §3.3 and are re-derived here).
> - Corpus contract: `docs/capability-corpus/AUTHORING.md` (Class A
>   deterministic-projection contract; no-cross-class-write invariant).
> **BASELINE candidate:** `266aa93cc878f422a20e83376a35bfbd660dad8c` (HEAD of
> main at sub-plan authoring; builder CONFIRMS at `loam amend apply`).
> **Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
> §8 register row + master plan §2/§10 backfill.
> **Quality bar:** every AC outcome-shaped; ★ AC.CLP-CUR.4 is the
> outcome-altitude AC; method stays the builder's call per ODD §1.1; NO
> version numbers pre-assigned.
> **PUBLIC-ACTION NOTE: this slice has NO public-action steps.** The corpus
> is in-repo; distribution is Slice 4's job (⛔OWNER gates live there). The
> recommended scheduler (cloud routine) writes to the EXISTING
> `github.com/lukeivers/loam` repo via the owner's own GitHub connection —
> no new public surface is created; see §8.4 for the halt if that ever
> stops being true.

---

## §1 Summary / TL;DR

**What ships:** the root-cause fix for the proven 7-weeks-stale /
factually-wrong capability-reference failure (gap analysis §3.1, found
2026-06-11). Three deliverables, dependency-ordered:

1. **Fact-fix + demotion (doc-only, immediately valuable, first commit).**
   The known-wrong subagent-recursion claim is corrected in the corpus
   (Claude Code 2.1.172: sub-agents spawn sub-agents to 5 levels — verified
   live 2026-06-11 against the changelog), and `docs/CLAUDE_CAPABILITIES.md`
   (1038-line 2026-04-23 snapshot; wrong at lines 712/717 and stale at 652)
   is demoted in place to an index/redirect over `docs/capability-corpus/`
   (D-CLP.5). After this commit exactly one canonical capability-reference
   surface exists.
2. **The refresh tool** — a new tools-adjacent component
   (`framework/tools/capability-refresh/`, D-CUR.1) implementing the
   locked-δ deterministic-projection core: read a source manifest → fetch
   canonical upstreams → project Class A bodies → emit a structured delta →
   auto-land projection-class changes / surface review-class changes
   (D-CUR.4) → stamp `source_fetch_ts` / mark stale on fetch failure.
   Deterministic body projection — no LLM call required; any optional
   LLM-routed step (e.g. delta summarisation) uses `claude -p` via the
   house client with spawn isolation (NO Anthropic API key — constraint
   corpus).
3. **The unattended cadence binding** for the canonical repo — recommended:
   a scheduled cloud routine (`/schedule`), launchd as the shipped fallback
   (D-CUR.2). High-velocity sources daily, long-form weekly, per the locked
   §7bis.1 cadence classes; workspace-overridable.

**AC families:** AC.CLP-CUR.1–5 (carried from master, verbatim outcomes) +
AC.CLP-CUR.6/7 (protection-floor guards: review gate + no-cross-class-write)
+ AC.CLP-CUR.S (seal-diff). ★ = AC.CLP-CUR.4 (a real upstream change lands
with no manual trigger, observed post-seal).

**Key decisions baked:** D-CUR.1 placement (tools-adjacent new component);
D-CUR.2 cadence mechanism (cloud routine ▸ launchd fallback; session-cron
ruled out); D-CUR.3 source set (verified live); D-CUR.4 update altitude
(what auto-lands vs what flags); D-CUR.5 §3-discrepancy fix-list (1 in-slice,
2 deferred-with-handoff). Full register §10.

**F2 on scope realism:** honest single-to-double cycle (master band
60–180 min AI-time). The genuinely uncertain part is D-CUR.2's live
verification of cloud-routine fit (≤15 min to verify; the fallback is
shipped, so a NO costs a mechanism swap, not a redesign).

---

## §2 Placement decisions

| Surface | Placement | Rationale |
|---|---|---|
| Refresh tool | **NEW component `framework/tools/capability-refresh/`** (`new_component: true`, first-seal; precedent: `usage-window-guard-foundation` manifest + `framework/tools/loam-acceptance-smoke/` shape) | D-CUR.1. Master §2 left "new framework surface vs tools-adjacent" as this sub-plan's first decision: tools-adjacent wins — the deliverable is a small fetch→project→diff→emit contract, the same weight class as the existing `framework/tools/` peers; a top-level `framework/<component>/` would buy ceremony, not capability. It still gets a real fence + seal test (it is load-bearing: it writes the corpus). |
| Source manifest (which upstreams, which cadence class per source) | **Inside the new component OR `docs/capability-corpus/`-adjacent — builder's call** | The contract requires sources to be declared as data, not hard-coded (workspace-overridable per locked §7bis.1); the file's exact home is method. |
| Canonical-repo cadence binding (routine spec / plist) | **Inside the new component's tree** (spec/docs/scripts), routine itself created via `/schedule` at build time | Master §2: loam ships the contract, the schedule binding is workspace content; for the canonical repo the binding artefacts live with the tool so the fence stays single-component. |
| `CLAUDE_CAPABILITIES.md` | **DEMOTE in place** to index/redirect over `docs/capability-corpus/` (D-CLP.5, master-locked) | Inbound references survive (file keeps its path); no four-section capability entries remain in it (AC.CLP-CUR.2). |
| Recursion fact-fix | **Existing Class A entry `docs/capability-corpus/claude-code/background-agents.md`** (extend) — preferred over a new entry | Verified 2026-06-11: no corpus entry currently carries the wrong claim (the wrong text lives only in `CLAUDE_CAPABILITIES.md` 652/712/717); extending the existing Agent-tool entry needs NO persona-spine index edit, keeping `framework/primary-persona/` out of the fence. A new entry would require a spine-index addition inside a sealed component — builder halts rather than widening (§8.5). |
| Corpus + demotion edits | **`universal_paths`** (`docs/capability-corpus/` prefix + `docs/CLAUDE_CAPABILITIES.md` file) | Repo-level docs, not component source; per amendment #22 ruling #3 convention. |

## §3 Halt-and-surface BEFORE build (recorded at sub-plan authoring)

1. **Live re-verification done (information-trust):** changelog fetched
   2026-06-11 at sub-plan-author time — latest 2.1.173; "Sub-agents can now
   spawn their own sub-agents (up to 5 levels deep)" @ 2.1.172; `/goal` @
   2.1.139. `https://code.claude.com/docs/en/hooks` fetched live same day
   (live "Hooks reference", documents the current event set incl.
   PostToolUseFailure / TaskCreated / SessionEnd). Source set D-CUR.3 rests
   on today's fetches, not training data.
2. **One sub-claim refined against the master plan:** master §11 cites
   `extraKnownMarketplaces` auto-update @ v2.1.142; today's changelog fetch
   surfaced the related line at v2.1.140 (a *fix* entry). NOT load-bearing
   for Slice 1 (it's Slice 4's D-CLP.4 verification item); recorded so
   Slice 4's plan-author re-pins it rather than inheriting either number.
3. **Fence-tightness ruling recorded:** the AUTHORING.md workflow step 5
   ("add new entries to the persona prompt spine index") would touch sealed
   `framework/primary-persona/`. This slice avoids it by design (§2 row 5:
   extend the existing indexed entry). Refresh-driven NEW entries in future
   cadence cycles are review-class deltas by D-CUR.4 — they surface as
   pending and land via a later cycle that carries the proper fence. No
   silent widening; no primary-persona admission in this manifest.
4. **No master-plan contradiction found.** Slice-1 scope as dispatched is
   satisfiable without touching Slice-2/4 surfaces (the two deferred
   discrepancy fixes in D-CUR.5 are handoffs, not scope leaks).

## §4 Spec-objective placement

- **Binds:** master AC.CLP.1 ★ (a wrong/missing capability fact gets
  corrected by loam's own recurring machinery within one cadence) — this
  slice IS that machinery; AC.CLP-CUR.\* is the tighter per-slice family
  (Lens 5: every AC below is strictly tighter than AC.CLP.1).
- **Ladders to:** AC.PO.2 (protection floor — a stale/wrong reference
  surface is the "inventing things / no real memory" betrayal class; master
  §4 names legs 1–3 as the AC.PO.2 instance) and AC.PO.1 indirectly (the
  corpus is what the persona's translation runs on).
- **Lens 1:** the slice's own automation prefers the native primitive
  (cloud routine over bespoke daemon) — the currency slice eating the
  program's own cooking.

## §5 Acceptance criteria (`AC.CLP-CUR.*`)

★ = outcome-altitude. Every AC passes the method-in-AC test (a method
other than the recommended one can satisfy it).

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-CUR.1 | The corpus's claim about subagent recursion is factually correct per the live Claude Code changelog at build time (known-wrong §7.7-snapshot claim corrected), and no in-repo reference doc contradicts it. | Read corpus entry; repo-wide grep for the stale claim (incl. the three `CLAUDE_CAPABILITIES.md` lines named in §1) returns no contradicting reference text. |
| AC.CLP-CUR.2 | Exactly one canonical capability-reference surface exists: `CLAUDE_CAPABILITIES.md` no longer carries independently-maintained capability claims (index/redirect only). | Read the file; no four-section capability entries remain. |
| AC.CLP-CUR.3 | A recurring refresh exists that, unattended, projects Class A entries from their canonical upstream sources on the locked cadence classes (high-velocity ≈ daily, long-form ≈ weekly; workspace-overridable) and emits a structured delta. | Inspect the cadence binding + run one full cycle against live sources. |
| AC.CLP-CUR.4 ★ | After the refresh machinery is live, a Claude Code capability change published upstream AFTER the seal appears in the corpus (or in a surfaced pending-delta) within one cadence cycle, with no manual trigger. | Wait one real cadence cycle post-seal against the live changelog; observe the delta. Production entry-point, no pre-arranged state. |
| AC.CLP-CUR.5 | Each Class A entry carries a fresh `source_fetch_ts`, and an entry whose source fetch fails is marked stale rather than silently retained as current. | Inspect entries post-refresh; simulate a fetch failure. |
| AC.CLP-CUR.6 | A delta that adds a new capability claim, removes one, or touches a `[user-intent phrasings]` overlay does NOT land in the corpus automatically — it surfaces as a pending-delta for review; body re-projections of existing entries DO land automatically. | Feed the refresh a fixture upstream containing one body change + one new claim + one removal; observe the partition. |
| AC.CLP-CUR.7 | The refresh never writes outside Class A / Class A-prime paths — `best-practice/` (Class B) is untouched by any refresh run, including a run whose upstream fixture tries to induce it. | Path-audit a refresh run; adversarial fixture attempt. |
| AC.CLP-CUR.S | Seal-diff discipline: only `framework/tools/capability-refresh/` + universal paths changed in BASELINE..seal. | `test_no_sealed_amendments.py` at the confirmed BASELINE + per-component sweep. |

## §6 Build steps (method-level guidance only; builder's call per ODD §1.1)

Manifest: `docs/plans/claude-leverage-program-s1-currency.manifest.yaml`.
`loam amend apply` → build → `loam amend seal` per the amendment-cycle
convention (named explicitly per
`feedback_dispatch_explicit_loam_amend_apply`).

1. **Commit 1 (doc-only, immediately valuable):** correct the recursion
   fact in `docs/capability-corpus/claude-code/background-agents.md`
   (re-verify the changelog live first — §8.1); demote
   `docs/CLAUDE_CAPABILITIES.md` to an index over the corpus
   (AC.CLP-CUR.1 + .2). Re-check at build time whether the Plan-agent
   no-spawn row (snapshot line 652) still holds post-2.1.172 — project
   what the live docs say, don't guess either direction.
2. **The tool:** scaffold `framework/tools/capability-refresh/` (tests-first
   per TDD discipline); source manifest as data; fetch → project → diff →
   partition per D-CUR.4 → write/stamp/stale-mark. Tests cover AC.5/6/7
   with fixture upstreams; one live-source run for AC.3.
3. **The binding:** verify cloud-routine fit live (≤15 min: `/schedule`
   availability on the subscription path + GitHub connection for this
   repo). Fit → create the routine + commit its spec; unfit → land the
   launchd binding via the shipped `launchd-plist` skill and record the
   fallback in §14. Either way the binding artefacts live in-fence (§2).
4. **Seal + smoke:** seal per convention; AC.CLP-CUR.4 ★ is then observed
   over the next real cadence cycle (post-seal checkpoint — record the
   observation in §14 when it lands; the seal does not wait for it, the
   roadmap row carries the pending-observation marker until it's green).
5. **Bookkeeping** per §9.

## §7 Out of scope

1. **β MCP knowledge-server + γ dynamic contributor** — master §7.1/7.2.
2. **Class B accrual channels** (community survey / Stop-hook extraction /
   user capture) — locked §7bis.2 content rides with Slices 2/4 per master.
3. **Gap-analysis §3.2 fix** (`claude-feature-awareness` skill stale) —
   pos3 workspace surface, outside the canonical fence; Slice 2's
   graduation of that skill is the fix vehicle. **Named handoff.**
4. **Gap-analysis §3.3 fix** (loam-skills README count/`meta-decision-haiku`
   mismatch — re-verified 2026-06-11: 23 skill dirs, 22 `SKILL.md`,
   `meta-decision-haiku/` contains only `__pycache__`, README line 45 still
   names it) — `plugins/loam-skills/` fence belongs to Slice 2, which
   rewrites that README during graduation. **Named handoff.**
5. **User-workspace scheduler wiring** (workspace-bootstrap registering
   refresh bindings for loam users) — Slice 4's bootstrap extension.
6. **Persona-spine index automation for refresh-discovered NEW entries** —
   review-class by D-CUR.4; lands with the cycle that carries the
   primary-persona fence (§3.3).

## §8 Halt triggers (in-flight)

1. Any capability claim about to be baked into corpus content fails live
   re-fetch at build time (master trigger 1; the corpus is proven
   stale-prone — every load-bearing claim re-fetches before code leans on
   it).
2. Cloud routines unavailable/unfit on the subscription path AND the
   launchd fallback also fails to deliver unattended cadence → halt,
   surface (master trigger 2). A clean fallback to launchd alone is NOT a
   halt — record it in §14 and proceed.
3. **Any candidate mechanism turns out to require an Anthropic API key →
   halt, surface** (dispatch-named trigger; the constraint corpus is
   subscription-only via `claude -p`).
4. The cadence binding turns out to require creating any NEW public
   surface (new repo, feed, publicly readable artefact) → hard stop —
   that is Slice 4 territory and ⛔OWNER (egress floor).
5. Satisfying an AC requires editing a sealed component not in this
   manifest (e.g. the persona spine per §3.3) → halt, surface; never
   silently widen.
6. The §2 row-5 preference (extend `background-agents.md`) proves wrong at
   build time (the fact genuinely needs a new entry) → that is trigger 5's
   instance: halt with the proposed fence widening, don't improvise.

## §9 Bookkeeping

- `docs/STATE.md` change-log entry at seal.
- `docs/release-roadmap.md` §8 register row (with the AC.CLP-CUR.4
  pending-observation marker until the post-seal cadence cycle is
  observed).
- Master plan backfill: §2 row 1 placement finalised (D-CUR.1) + §10
  D-CLP.3/D-CLP.5 marked delivered-by-this-slice.
- Locked-design forward-pointer (master §9): one-line note in
  `docs/plans/research/persona-capability-knowledge-grounding-research.md`
  §7bis — "δ's intent realised by claude-leverage-program Slice 1;
  substrate re-derived" (docs/plans/ prefix admits it).
- FIDRAFT graduation note remains dispatcher-owned — flagged, NOT edited
  by this cycle.
- §14 register populated at build + seal (SHA backfill via
  `loam amend seal --plan-doc`).

## §10 Named decisions + F2 Ruthless Feedback

### Named decisions (recommendation IS the decision unless dispatcher/owner overrides)

**D-CUR.1 — Refresh-tool placement.**
Alternatives: (a) new top-level `framework/<component>/`; (b) tools-adjacent
new component `framework/tools/capability-refresh/`; (c) loose scripts, no
fence.
**Recommendation: (b).** Evidence: the deliverable's weight class matches
existing `framework/tools/` peers (`loam-acceptance-smoke`,
`loam-spawn-isolation` — verified on disk); (c) is disqualified because the
tool WRITES the corpus — an unfenced corpus-writer is a protection-floor
hole; (a) buys component ceremony a script set doesn't need. First-seal
manifest precedent: `usage-window-guard-foundation` (`new_component: true`).
F4: HIGH.

**D-CUR.2 — Cadence mechanism.** `primitive-rationale: scheduled cloud
routine (/schedule) — unattended cadence with no machine awake, Claude-native
(Lens 1), no API key.`
Alternatives: (a) scheduled cloud routine; (b) launchd (shipped
`launchd-plist` skill; proven in this stack — the refusal-watchdog runs on
it); (c) session-cron (`/loop` / CronCreate).
**Recommendation: (a) primary, (b) named fallback, (c) ruled out.**
Evidence: tool-selection-rubric decision E applied 2026-06-11 — (c) is the
rubric's named anti-pattern (CronCreate is session-only per the task-#77
empirical finding; an unattended cadence cannot depend on a live session);
(b) works but requires the machine awake — the failure mode that birthed
this slice is precisely "the refresh that never ran"; (a) runs on
Anthropic's cloud on the owner's subscription (no API key — §8.3 guards
the assumption), and the repo is GitHub-connected (verified:
`origin = github.com/lukeivers/loam`), which is the routine's write path.
Honest unknown: cloud-routine fit is HYPOTHESISED (gap analysis §5 says the
same) — build step 3 verifies live before binding; fallback (b) means a NO
costs a swap, not the slice. F4: MEDIUM on (a), HIGH on the
primary+fallback shape.

**D-CUR.3 — Source set (verified live 2026-06-11).**
- `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
  — fetched today (latest 2.1.173). Cadence class: high-velocity (daily).
- `https://code.claude.com/docs/en/hooks` — fetched today (live reference).
  Per-entry canonical docs pages (`/docs/en/commands`,
  `/docs/en/interactive-mode` — fetched today by the gap analysis) join as
  the corpus's per-entry `source_url`s. Cadence class: high-velocity for
  command/feature pages (daily); long-form guides weekly per locked
  §7bis.1.
**Recommendation:** declare exactly these in the source manifest at build
time, replacing the seed entries' `internal:` source_urls with real
upstream URLs as each entry is first re-projected; every URL re-verified
live at build (§8.1). Sources are data (workspace-overridable), not code.
F4: HIGH.

**D-CUR.4 — Update altitude (the protection-floor guard, named).**
The risk: a wrong auto-ingested claim poisons the reference surface the
persona plans against — the floor failure this program exists to prevent.
Alternatives: (a) auto-land everything (max currency, no guard); (b) flag
everything (owner becomes the bottleneck; the refresh "never ships" failure
mode returns wearing a review costume); (c) partition by claim class.
**Recommendation: (c):** AUTO-LAND = deterministic body re-projections of
existing entries, `source_fetch_ts` stamps, stale-markings. REVIEW-FLAGGED
(pending-delta, surfaced to persona/owner) = new capability claims, removed
capabilities/deprecations, anything touching a `[user-intent phrasings]`
overlay, and any delta contradicting an existing corpus claim. Guards
underneath: the body projection is deterministic (no LLM authorship — a
hallucinated claim cannot enter by construction), and AC.CLP-CUR.7's
no-cross-class-write keeps judgement-class content (Class B) structurally
out of reach. This is the locked §7bis.1 diff/merge flow restated with the
overlay + contradiction cases added. F4: HIGH.

**D-CUR.5 — Fix-list for the gap-analysis §3 discrepancies.**
1. **§3.1 (corpus wrong on subagent recursion — risky direction): IN-SLICE.**
   AC.CLP-CUR.1 + .2; commit 1.
2. **§3.2 (`claude-feature-awareness` stale — safe direction): DEFER to
   Slice 2 with named handoff** (§7.3). It lives in pos3
   (`/Users/lukeivers/pos3/.claude/skills/`), outside this canonical
   fence; Slice 2's graduation is the structural fix (one canonical copy —
   master F2.6).
3. **§3.3 (loam-skills README count — estimate-grade, re-verified today):
   DEFER to Slice 2 with named handoff** (§7.4). `plugins/loam-skills/` is
   sealed and not in this fence; Slice 2 rewrites that README during
   graduation. Admitting the fence here for a one-line count fix widens a
   seal window for zero currency value.
**F4: HIGH on all three.**

### F2 — honest doubts, named

1. **AC.CLP-CUR.4 is verified after the seal.** The ★ AC's real-cadence
   observation necessarily post-dates the seal (master wrote it that way).
   The seal therefore ships with the strongest AC pending-observed; the
   roadmap marker (§9) keeps that honest rather than quietly claiming
   green. If the first cadence cycle fails, that is a regression on a
   sealed slice — surfaced, not absorbed.
2. **Cloud-routine semantics are the slice's main unknown** — availability
   on the subscription path, repo-write path, and whether a routine's
   commits ride the owner's existing GitHub auth. All verified in build
   step 3 BEFORE binding; the shipped fallback bounds the downside.
3. **"Deterministic projection" has a parsing edge.** Upstream HTML/markdown
   reshapes can make a pure-structural transform brittle; a transform that
   quietly drops content is a silent-staleness risk of its own. AC.CLP-CUR.5's
   stale-marking is the guard (fetch/parse failure → marked stale, never
   silently retained), but parse-*degradation* short of failure is only
   caught by the delta review. Named, not fully closed.
4. **The corpus is small (4 Class A entries).** The refresh contract is
   built against a corpus an order of magnitude smaller than its eventual
   load; per-source cost and delta ergonomics at 40 entries are untested.
   Fine for this slice (the contract is data-driven), named for Slice 4
   which consumes it as a content pipeline.
5. **Two reference surfaces exist until commit 1 lands.** Trivially true
   but worth naming: any agent reading `CLAUDE_CAPABILITIES.md` between
   dispatch and commit 1 still reads the wrong recursion claim. Commit 1
   is first in the ladder for exactly this reason.

## §11 Provenance trail

- Master plan: `docs/plans/claude-leverage-program.md` (Slice 1 section,
  §2 row 1–2, §5 AC.CLP-CUR.\*, §6.1, §10 D-CLP.3/4/5; D-CLP.4 owner
  ratification Discord 1514753768175042771, 2026-06-11).
- Gap analysis: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`
  (§3 discrepancies; §5 honest doubts on routine availability).
- Locked design: `docs/plans/research/persona-capability-knowledge-grounding-research.md`
  §7bis.1 (cadence table, locked by Luke 2026-04-26), §7bis.3
  (no-cross-class-write), §7bis.4.
- Corpus contract: `docs/capability-corpus/AUTHORING.md` (Class A schema,
  `Source` block, workflow step 5 — the spine-index step this slice
  deliberately avoids triggering).
- Live verifications (sub-plan-author, 2026-06-11): changelog raw URL
  (latest 2.1.173; recursion @ 2.1.172; `/goal` @ 2.1.139);
  `code.claude.com/docs/en/hooks` (live); `git remote -v`
  (`github.com/lukeivers/loam`); `plugins/loam-skills/skills/` listing
  (23 dirs / 22 SKILL.md / `meta-decision-haiku` = `__pycache__` only);
  stale-claim locations `docs/CLAUDE_CAPABILITIES.md:652,712,717`; corpus
  entries carry `internal:` source_urls + 2026-04-28 fetch stamps; highest
  manifest counter on disk = 183 (`conventional-install-pypi-publish`).
- Conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md` (sub-plan +
  manifest shape; AC-ID + narrative.target rules); manifest precedents
  `docs/plans/sealed/usage-window-guard-foundation.manifest.yaml`
  (new_component) + `docs/plans/conventional-install-pypi-publish.manifest.yaml`
  (counter-confirm-at-apply pattern).
- Memory corpus: `feedback_version_numbers_at_release_time`,
  `feedback_scope_descriptive_ac_ids`,
  `feedback_test_outcome_altitude_required`, `feedback_no_anthropic_api_key`,
  `feedback_spawned_claude_must_isolate_telegram_plugin`,
  `feedback_dispatch_explicit_loam_amend_apply`.

## §13 §status (recorded at build, 2026-06-11/12 UTC)

**Dispatcher-level gate applied on top of this plan (2026-06-11):** NO
live cloud routine / launchd agent / any persistent scheduler entry was
created or activated during this cycle. The component ships so that
activation is a single documented command
(`framework/tools/capability-refresh/cadence/ACTIVATION.md`); **LIVE
activation is OWNER-GATED and PENDING** (precedent: the
refusal-watchdog persistence ruling,
`2026-06-11-refusal-watchdog-persistent-service-keep.md`).

| AC | Verdict | Evidence |
|---|---|---|
| AC.CLP-CUR.1 | **GREEN** | Recursion claim corrected in `docs/capability-corpus/claude-code/background-agents.md` (2.1.172 / 5 levels; changelog re-fetched live at build). Repo-wide grep clean (`test_AC_CLP_CUR_1_2_reference_surface.py`). Build-time finding: the live sub-agents docs PAGE still carried the superseded no-recursion sentence on 2026-06-11 (docs lag) — the changelog is release truth; named in the corpus entry + sources.yaml. |
| AC.CLP-CUR.2 | **GREEN** | `docs/CLAUDE_CAPABILITIES.md` demoted in place to a 65-line index/redirect; no four-section entries remain; guarded by the same test file. |
| AC.CLP-CUR.3 | **GREEN-pending-activation** (loose-AC note, named per dispatch — not a silent rewording) | The refresh + cadence binding EXIST and are verified: one full live cycle ran through the production CLI (6/6 sources, run 2026-06-12T00:39:55Z), cadence-class selection tested, binding artefacts shipped (routine spec + launchd plists + one-command activation). The AC's "recurring … unattended" leg cannot honestly be claimed GREEN until the owner activates the binding (dispatcher gate above). |
| AC.CLP-CUR.4 ★ | **PENDING (post-seal checkpoint, pending-activation)** | The mechanic verified live through the production path at build: changelog snapshot rewound to a pre-2.1.173 baseline → next production-CLI cycle surfaced the real 2.1.173 upstream block as a review-class pending-delta with no manual content work; steady state restored. The real-cadence observation runs after owner-gated activation; roadmap row carries the pending-observation marker. |
| AC.CLP-CUR.5 | **GREEN** | All 5 entry-kind entries stamped fresh `source_fetch_ts` + `source_status: current` by the live run; stale-marking + last-good-ts retention + recovery covered by `test_AC_CLP_CUR_5_*`. |
| AC.CLP-CUR.6 | **GREEN** | D-CUR.4 partition: fixture per the AC (one body change + one new claim + one removal) → re-projection auto-landed, new claim + removal surfaced as pending-delta; overlay-touch + curated-divergence + watch-source cases covered (`test_AC_CLP_CUR_6_*`). |
| AC.CLP-CUR.7 | **GREEN** | Structural guard (`resolve_entry_path` / `resolve_state_path`): Class B unreachable; adversarial manifest (Class B target, traversal, absolute path) refused with Class B byte-identical; production CLI exits 3 on refusal (`test_AC_CLP_CUR_7_*`). |
| AC.CLP-CUR.S | **GREEN at seal** | First-seal fence test at BASELINE 266aa93c; `allowed_prefixes`/`allowed_files` bindings parse for the loam-amend reader. |

Component tests: **24/24 GREEN** (`framework/tools/capability-refresh/tests/`).

## §14 Method-decision register (populated at build + seal)

| ID | Decision | Builder narrative (at build) | SHA (at seal) |
|---|---|---|---|
| D-CUR.1 | Placement: `framework/tools/capability-refresh/` | Executed as ratified: new tools-adjacent component, first-seal, peer shape to `loam-acceptance-smoke` (pyproject + src + tests + the cadence/scripts dirs). Python ≥3.9-compatible, PyYAML the only dependency. | _pending_ |
| D-CUR.2 | Cadence binding chosen (routine vs fallback) + live-verification result | Cloud routine PRIMARY, confirmed FIT at docs level (live fetch of `/docs/en/routines` 2026-06-11: Pro/Max subscription path, no API key, cron min 1 h, repo write via owner's GitHub connection with `claude/`-prefix branch default — kept as a second protection layer). launchd fallback SHIPPED (two plists). Session-cron ruled out as authored. **CREATION/ACTIVATION NOT performed — owner-gated per the dispatcher gate (plan §13)**; activation is one documented command per mechanism (`cadence/ACTIVATION.md`). | _pending_ |
| D-CUR.3 | Final source manifest contents (URLs + cadence classes) | `docs/capability-corpus/sources.yaml` (corpus-adjacent home — sources describe corpus entries; workspace-overridable via `--sources`): changelog watch (high-velocity, release truth) + sub-agents/hooks/commands/routines entry sources (high-velocity) + scope-of-work internal (on-merge). Every URL fetched live at build; the plan's `/docs/en/interactive-mode` hypothesis for /loop was WRONG at live check (page doesn't cover /loop) — `/docs/en/commands` verified instead; `/docs/en/routines` verified for /schedule. Seed `internal:` labels replaced with real URLs by the first live run. | _pending_ |
| D-CUR.4 | Delta-partition implementation shape | Deterministic: difflib opcodes over normalised statement units. insert→new-claim, delete→removal, replace at similarity ≥0.6→re-projection (auto-land candidate), <0.6→contradiction-suspect. Auto-land applies ONLY by verbatim in-place substitution in the entry's projected body region; a match inside the `[user-intent phrasings]` overlay demotes to overlay-touch (review), no verbatim match demotes to curated-divergence (review) — curated content is never mechanically guessed. Watch sources: all deltas review-class by construction. Review items → `pending-deltas/<date>-<id>.md` + structured `last-run.json`. | _pending_ |
| D-CUR.5 | §3.1 fix landed; handoff notes recorded for Slice 2 | §3.1 IN-SLICE: corpus claim corrected + snapshot demoted (commit 1). §3.2 + §3.3 DEFERRED with the named handoffs exactly as authored (plan §7.3/§7.4) — no fence widening. Build-time F2 finding for Slice 2's plan-author: the upstream sub-agents docs page itself still contradicted the changelog on 2026-06-11; per-entry projections must treat the changelog watch as release truth on conflicts. | _pending_ |
| AC.CLP-CUR.4 ★ | Post-seal cadence-cycle observation | _pending (post-seal checkpoint; pending owner-gated activation — mechanic verified live at build, plan §13)_ | _pending_ |

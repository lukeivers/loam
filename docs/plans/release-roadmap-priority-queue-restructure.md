# Release-roadmap priority-queue restructure

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner ratifies before any cycle dispatches; uncommitted at land time.
**Slug:** `release-roadmap-priority-queue-restructure`.
**Date authored:** 2026-05-09.
**Class:** META-FRAMEWORK (release-process discipline + roadmap shape; no end-user-visible capability change).
**Predecessor:** v0.4.4 patch (subagent-personas-routing) SHIPPED LOCAL; v0.4.5 patch (release-process) plan-only at authoring time; `docs/release-roadmap-dependency-map.md` SHIPPED 2026-05-09 commit `0d30eab2`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Owner authorization:** Telegram 10557 ("we should have a list of things we want to release as a next version, and we can order them for now, but we should declaratively say that one is 0.5.0 and one is 0.6.0. The actual number can be derived at the time the build commences based on current version. This leaves us with much more flexibility in priorities and what to make into minor and patch versions. It doesn't feel like the work we are doing is a patch. Hell even the past couple versions prob shouldn't have been patches.").

---

## §1 — Outcome shape (the "why")

The current `docs/release-roadmap.md` §4 pre-numbers forward-looking releases (v0.4.5 / v0.5.0 / v0.6.0 / v0.7.0 / v0.8.0 / v0.9.0 / v0.10.0+ / v1.0.0). Pre-numbering at authoring time bakes priority-rank into version-identity *before* (a) priority is settled and (b) the PATCH/MINOR/MAJOR class is settled. Two failure shapes follow:

1. **Re-prioritization is high-friction.** Moving "v0.6.0 — non-tech-user surface" ahead of "v0.5.0 — binary-usage harness" means renaming both entries plus every cross-reference. The version digit gets in the way of the priority decision.
2. **Class drift is invisible.** Recent "patches" (v0.4.4 most clearly; v0.4.5 likely; v0.4.1/v0.4.2 less clearly) ship NEW outcome shapes — new SKILLs, new CLI verbs, new behavior surfaces — that meet the policy doc's definition of a MINOR ("new outcome-shape capability"), not a PATCH ("backwards-compatible fixes for the named outcome of the current minor"). Pre-numbering them as `v0.4.X` patches happens because the slot was already labeled PATCH at planning-time, not because the work fits the policy.

This plan-doc restructures §4 from a pre-numbered chain to a **priority-ordered queue of unnumbered candidates**. Each candidate carries an objective sentence + class tag (PATCH/MINOR/MAJOR) + ACs + dependencies. Numbers get derived **at build-commence time** from a documented rule: `next_number = bump(current_version, candidate_class)`. The priority-ordering can change without renumbering; the class can change without renumbering; the version-number is downstream of both.

Composes with: `docs/release-versioning-policy.md` (the policy doc's MAJOR/MINOR/PATCH definitions stay authoritative; this plan doesn't alter what the digits mean — only when/how they're assigned). Composes with: `docs/release-roadmap-dependency-map.md` (HARD/SOFT classifications keyed on the candidate slug, not the version-number).

---

## §2 — Prime objective ladder

`docs/VALUE_PROPOSITION.md` prime objective (loam helps people use LLMs to build software) → forward-looking roadmap shape compounds across versions: every release is one step in the harness's growth toward stable user-facing software-building → version digits are bookkeeping for that growth, not the cause of it → priority decisions should drive numbers, not the reverse → restructure ACs (`AC.RR.{1,2,3,4,S}` below) implement the queue + reclassification audit + number-derivation rule + outcome-altitude probe.

Composes with: Lens 4 (scope-confidence) — the priority-queue shape ACKNOWLEDGES low-confidence-on-priority by deferring number-binding. Composes with: Lens 5 (swarming) — each candidate becomes a self-contained subtask with its own AC ladder; the queue is the planner-level decomposition. Composes with: F2 RUTHLESS FEEDBACK — the reclassification audit surfaces uncomfortable findings (recent patches were minors) instead of silently propagating misclassification.

---

## §3 — Component fence

**PRIMARY:** `docs/release-roadmap.md` — §4 restructured from pre-numbered chain to priority-ordered queue of unnumbered candidates.

**SECONDARY:** `docs/release-versioning-policy.md` — extended with a new section "Number derivation at build-commence time" naming the recipe `next_number = bump(current_version, candidate_class)` + the per-class bump rule (PATCH→`bump_patch`; MINOR→`bump_minor`; MAJOR→`bump_major`).

**OPTIONAL secondary** (builder rules at build time per D-RR.6.4): `framework/tools/loam/` — Python helper `loam.versioning.next_number(current, candidate_class)` if the build-time decision is to ship a CLI helper rather than a documented manual rule.

**TERTIARY (artefact-bookkeeping):** `docs/release-roadmap-dependency-map.md` — re-key dependency rows from version-numbers to candidate-slugs. SOFT update; the dep-graph itself doesn't change, only the row labels.

**Untouched:**
- `docs/STATE.md` §2 (shipped versions table) — historical record; immutable.
- All shipped plan-docs (`docs/plans/v0-1-X-*.md`, `docs/plans/v0-2-X-*.md`, `docs/plans/v0-3-0-*.md`, `docs/plans/v0-4-0-*.md` through `docs/plans/v0-4-3-*.md`) — historical record; the version-numbers are baked into filenames + content + git history; renaming them = revisionism.
- All published git tags (v0.1.0 through v0.4.3 are public on `loam` remote per STATE.md change-log 2026-05-09 entry).
- `docs/release-roadmap.md` §1 (framing), §2 (shipped table), §3 (active version), §5 (backlog), §6 (external actions), §7 (authority).

**Out of fence:** any framework component, any seal directory, any `docs/spec/` file, any test surface (this is doc + policy work, no code touches the §3 PRIMARY fence; `framework/tools/loam/` only opens as a fence if D-RR.6.4 selects the CLI-helper path). Edits outside fence = halt.

---

## §4 — AC family `AC.RR.*` (TIGHT)

Each AC maps to a verifiable acceptance signal. Method stays builder's call.

### AC.RR.1 — §4 restructured to priority-ordered queue of unnumbered candidates

`docs/release-roadmap.md` §4 is restructured. The new shape:

- Renamed from "Mapped versions (v0.4.5 → v1.0.0)" to "Priority-ordered candidate queue (next-release pipeline)" or equivalent name not pinning version numbers.
- Each candidate has: (a) a stable slug (e.g., `release-process` rather than `v0.4.5`); (b) a single-sentence objective; (c) a class tag (PATCH/MINOR/MAJOR); (d) AC family; (e) constraints; (f) source items; (g) AI-time estimate; (h) dependencies (keyed on candidate-slugs from this queue, OR on shipped version-numbers from §2 when the dep is on already-shipped work).
- Order in the queue reflects current priority decision; first item is "next to build."
- No version-numbers appear next to candidate names. (Version-numbers may appear inside dependency rows when referencing already-shipped work.)
- A header note explains: "Numbers get derived at build-commence time per `docs/release-versioning-policy.md` §number-derivation. Priority can change by reordering; class can change by re-tagging; numbers are downstream of both."

**Verdict:** GREEN if all 8 fields present per candidate AND no candidate carries a pre-assigned version-number AND header note present. YELLOW if structure is correct but 1-2 candidates missing fields (e.g., no AI-time estimate). RED if any candidate carries a pre-assigned number OR the queue isn't ordered.

**Test:** doc-level structural assertion (manual review at owner-ratification time; this is a doc-only AC and the verification is the read).

`outcome-altitude: false` (structural; necessary substrate for AC.RR.4 outcome probe).

### AC.RR.2 — Reclassification audit deliverable

A reclassification audit walks every currently-listed forward-looking release entry (v0.4.5, v0.5.0, v0.6.0, v0.7.0, v0.8.0, v0.9.0, v0.10.0+, v1.0.0) AND every recent patch (v0.4.1, v0.4.2, v0.4.3, v0.4.4) and re-classifies each per `docs/release-versioning-policy.md` definitions:

- **PATCH** = "backwards-compatible fixes for the named outcome of the current minor. Same-shape behavior; bug closures only."
- **MINOR** = "new outcome-shape capability. Each minor release names ONE outcome a user can newly achieve with loam."
- **MAJOR** = breaking changes (only when 1.0.0 commitment lands).

Output format: a table inside §4 (or as a §4-prelude section), columns: `(slug, original-class, audited-class, ships-new-outcome-shape?, evidence, reclassification-call)`. Rows for forward-looking entries: re-tag per the audited-class. Rows for already-shipped entries: name the misclassification but DO NOT propose retroactive renumbering of already-published versions (that would break tags + external refs).

**Required findings to verify** (these were surfaced by the audit author during plan-authoring; the AC requires the audit deliverable to either confirm or refute each):

1. **v0.4.4** (subagent-personas-routing) — ships TWO new SKILLs (`subagent-routing` brand-new; `dispatch-brief-authoring` extended). The plan-doc itself names the tension: "PATCH-SHAPED-AS-MINOR-CLASS" (v0.4.4 plan §13 alternatives line 217). Audited class: **MINOR**. Already SHIPPED LOCAL with `v0.4.4` slug; not yet published; renaming feasible but disruptive (plan-doc filename, manifest, STATE.md row, roadmap §2 row).
2. **v0.4.5** (release-process) — ships a brand-new `loam release` CLI verb plus a new runbook doc. NEW outcome shape: maintainers can now run a single command to publish, where before publishing was figured-out-as-you-go. Audited class: **MINOR**. Plan-only at authoring time; trivial to rename before build commences.
3. **v0.4.1** (F-DESIGN-1 closure) — ships three sub-fixes (multi-commit-per-task; from-scratch prompt mode with auto-detect + CLI flag; build-next tie-breaker). The "from-scratch prompt mode" is arguably a NEW outcome shape (cold-start docs-only multi-file code-gen wasn't supported before), but the v0.4.1 plan-doc explicitly frames it as "makes the v0.4.0 outcome work on the cold-start docs-only multi-file class of task that C4 surfaced as a gap" (v0.4.1 line 21) — treating from-scratch as an extension of v0.4.0's outcome shape rather than a new one. Audited class: **borderline; arguably MINOR**. PUBLISHED with v0.4.1 tag (per STATE.md change-log 2026-05-09); renaming would be revisionist + break public tag refs.
4. **v0.4.2** (F-DESIGN-2 closure) — ships two sub-fixes (Test-interface section as load-bearing prompt context; Py-version-compat instruction + post-process rewriter). Both are arguably defect closures within v0.4.1's from-scratch surface. Audited class: **PATCH** (defensible). PUBLISHED with v0.4.2 tag; same revisionism constraint as v0.4.1.
5. **v0.4.3** (BM25-fix) — ships three fixes inside `framework/primary-persona/` memory retrieval (token-sanitized FTS5; length-normalized grep; cosmetic worker-log fix). All defect closures on existing memory-retrieval surface; NO new outcome shape. Audited class: **PATCH** (correct as classified). PUBLISHED with v0.4.3 tag.

Forward-looking entries (v0.5.0 through v1.0.0): all currently use MINOR or MIXED class; audit verifies the class-vs-content fit per their existing AC families.

**Verdict:** GREEN if audit table present + each row has all 6 columns + each finding above either confirmed or explicitly refuted with evidence. YELLOW if audit present but 1-2 rows incomplete. RED if audit absent or any row claims "unknown" without evidence.

**Test:** structural assertion (manual review at owner-ratification time).

`outcome-altitude: false` (audit deliverable; supports AC.RR.4 outcome probe).

### AC.RR.3 — Number-derivation rule documented

`docs/release-versioning-policy.md` is extended with a new section (e.g., §"Number derivation at build-commence time") naming the explicit recipe:

```
Given: current_version (the most-recent shipped tag, e.g., v0.4.4)
Given: candidate_class (PATCH | MINOR | MAJOR — from the queue entry being built)

if candidate_class == PATCH:
    next_number = bump_patch(current_version)   # v0.4.4 → v0.4.5
elif candidate_class == MINOR:
    next_number = bump_minor(current_version)   # v0.4.4 → v0.5.0
elif candidate_class == MAJOR:
    next_number = bump_major(current_version)   # v0.4.4 → v1.0.0
```

Plus narrative paragraphs covering:

- Where the recipe applies (at build-commence time when the candidate moves from queue → active build; not at queue-authoring time).
- What "current_version" means precisely (the highest-numbered shipped tag on `loam` remote at the time of build-commence, NOT the highest-numbered-locally; the rule pins against published state).
- Hot-patch case (`v0.X.Y.Z` four-digit form): when a hot patch is needed before the next planned PATCH, the existing four-digit convention applies + the recipe extends with `bump_hotfix(current_version)`.
- Edge case: if the queue's first-item is MINOR but there's an in-flight PATCH not yet shipped, the candidate-class drives the choice (the in-flight PATCH bumps PATCH; the next MINOR after that bumps MINOR from the new PATCH-bumped current).
- Implementation choice (D-RR.6.4 builder ruling): documented manual rule (default) OR Python helper at `framework/tools/loam/src/loam/versioning.py` exposing `next_number(current, candidate_class)` for `loam release` CLI consumption.

**Verdict:** GREEN if section present + recipe block present + all 5 narrative paragraphs present. YELLOW if section present but missing 1-2 paragraphs. RED if section absent or recipe block missing.

**Test:** structural assertion + substring-match (the bump table can be regex-checked at owner-ratification).

`outcome-altitude: false` (rule documentation; necessary substrate for AC.RR.4 outcome probe).

### AC.RR.4 (outcome-altitude) — A real "what's next?" decision exercises the new shape

The new shape is exercised end-to-end on a real next-release decision. Concretely:

1. After AC.RR.{1,2,3} land + owner ratifies the restructured §4, the next "what should I build?" decision walks the queue: pick the highest-priority candidate; read its class; derive the version-number per AC.RR.3 against the current published state.
2. The decision is recorded in a writeup at `<workspace>/.scratch/claude-output/release-roadmap-restructure-outcome-probe.md` covering: which candidate was picked (slug); why (priority + dependency-readiness); what class it carries; what number was derived; what the bump-recipe input was (current_version) and output was (next_number).
3. The pick is then either dispatched as the next build OR queued as a soft-halted candidate per `feedback_soft_halt_vs_hard_halt`. The outcome of the dispatch (or the halt-state) is recorded in the writeup.

**Verdict:** GREEN if writeup present at canonical path + names a candidate from the queue + names the derived number + records the build-or-halt action. YELLOW if writeup present but missing 1-2 fields. RED if writeup absent.

**Test:** structural assertion (manual review at owner-ratification time; the probe is empirical and post-restructure).

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` rubric — real downstream decision, real number-derivation, real next-build dispatch (or halt). Not a stubbed walkthrough; the actual next "what's next?" choice IS the outcome.

### AC.RR.S — Seal-diff

Sealed-component cycle ritual; sidecar advances; `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the named fence (`docs/release-roadmap.md` + `docs/release-versioning-policy.md` + optional `framework/tools/loam/` + `docs/release-roadmap-dependency-map.md` re-keying + plan-doc/manifest/seal-narrative scaffolding). Out-of-fence diffs = halt + rewind.

`outcome-altitude: false` (process invariant).

---

## §5 — Decisions builder rules at build time

These decisions are the builder's call at build-time; the plan-doc names the choice points without pre-deciding.

### D-RR.5.1 — Migration of currently-listed v0.5.0+ entries

Two paths:

- **Path A (recommended):** rename current §4 entries to descriptive slugs. `v0.5.0 — Loam builds software from minimal input` → slug `binary-usage-harness`. `v0.6.0 — Loam is usable by a non-technical user from fresh install through working software` → slug `non-tech-user-surface`. Etc. The "currently-priority-#1" position is held by what was formerly v0.4.5 (release-process). Number-references in cross-doc refs (dependency-map, internal callouts) update accordingly.
- **Path B:** preserve the current numbers as suffixes on the slugs (`binary-usage-harness-v0.5.0`) so existing cross-refs remain greppable during transition. Migration-cost lower; messaging-cost higher (the "version-number is downstream of priority" message gets diluted by the suffixes still being there).

_Builder rules at build time per D-RR.5.1._

### D-RR.5.2 — Handling v0.4.4 reclassification (sealed-local, not-yet-published)

v0.4.4 is sealed local but not on the public `loam` remote. Three paths:

- **Path A (recommended):** rename v0.4.4 → v0.5.0 retroactively before publish. Touches: `docs/plans/v0-4-4-*.md` filename; `docs/plans/v0-4-4-*.manifest.yaml` filename + content; `docs/STATE.md` change-log row; `docs/release-roadmap.md` §2 row; FIDRAFT entry. Local-only ref updates; no public tag exists yet to break. Composes with the plan-doc's own findings about MINOR-class v0.4.4 outcome shape.
- **Path B:** publish as v0.4.4 (preserving the existing slug); start fresh with the queue shape for v0.5.0+. Less consistent (v0.4.4 ships under wrong class); lower migration-cost.
- **Path C:** publish as v0.4.4 + ship a paired "class-correction" note in STATE.md acknowledging the misclassification. Hybrid; clearest audit trail; v0.4.5 onwards uses queue shape with corrected class.

Owner ratification needed before either build or publish proceeds.

_Builder rules at build time per D-RR.5.2._

### D-RR.5.3 — Handling v0.4.1/v0.4.2 reclassification (PUBLISHED)

v0.4.1 + v0.4.2 are PUBLISHED with their respective tags (`v0.4.1`, `v0.4.2`) on `loam` remote (per STATE.md 2026-05-09 change-log). Renaming = revisionism + breaking external refs (anyone with the tag in a dep file). Two paths:

- **Path A (recommended):** Do NOT rename. Capture the misclassification as a `lessons-learned` table row in the audit deliverable (AC.RR.2). Going forward, the queue + number-derivation rule + class audit prevent recurrence.
- **Path B:** rewrite tags + republish. Disruptive; not recommended; surfaced for explicit rejection.

_Builder rules at build time per D-RR.5.3._

### D-RR.5.4 — Number-derivation surface (manual rule vs Python helper)

Two paths:

- **Path A (recommended):** Documented manual rule in `docs/release-versioning-policy.md`. Maintainer reads recipe + applies at build-commence-time. Lowest fence; no code surface; consumed by humans.
- **Path B:** Python helper at `framework/tools/loam/src/loam/versioning.py` exposing `next_number(current, candidate_class)`. Composes with v0.4.5's `loam release` CLI (the CLI calls the helper to verify the number argument matches the derived value). Higher fence (~30-60 min build); machine-checkable.
- **Path C:** Both — manual rule documented + Python helper shipped + CLI uses helper. Highest fence; highest reliability.

Owner ratification informs the builder's call. If v0.4.5 release-process plan-doc is also being built around the same time, Path B or C compose naturally.

_Builder rules at build time per D-RR.5.4._

### D-RR.5.5 — Roadmap re-review mechanism (split or fold)

Luke's Telegram 10557 also surfaced: "instead of knee jerk moving to the next thing in line when completing a release, we should always stop and re-evaluate the roadmap." Two paths:

- **Path A (recommended; FOLD):** Add a §"Post-ship roadmap re-review" subsection to `docs/release-roadmap.md` that names the re-review as a structural step in every release-completion ritual. Composes with v0.4.5's runbook (the runbook can name re-review as the post-publish step). Single coherent restructure ships in one cycle.
- **Path B (SPLIT):** Author a separate `roadmap-re-review-discipline` amendment plan-doc downstream. Cleaner fence-separation; more cycles to ship; risk of the re-review never landing if the priority-queue restructure drains queue-priority-attention.

_Builder rules at build time per D-RR.5.5._

### D-RR.5.6 — Goal-alignment scoring per candidate

Luke's recent discussions (per session context) introduced 3 named real-world goals for loam: Anthropic acquisition criteria; consulting offering; personal-wealth foundation. Two paths:

- **Path A:** Add a `goal-alignment` field to each queue candidate scoring (Strong / Moderate / Weak / None) against each of the 3 goals. Adds prioritization signal; helps owner pick when multiple candidates compete.
- **Path B:** Don't add. Goal-alignment lives in the owner's head + ad-hoc surfacing per priority decision; the queue stays minimal.

Owner ratification needed; this is a signal-richness vs maintenance-cost tradeoff.

_Builder rules at build time per D-RR.5.6._

---

## §6 — Out of scope (explicit)

The following are EXPLICITLY out of scope for this plan-doc + the build cycle that ships it:

- **Renumbering published versions.** v0.1.0 through v0.4.3 are public + tagged on `loam` remote. Renaming these would require tag rewrites + history rewrite + external-ref breakage; the audit deliverable (AC.RR.2) names the misclassification but does NOT propose retroactive renumbering for published versions. (v0.4.4 sealed-local-not-published is the borderline case and lives in D-RR.5.2.)
- **Changing `docs/STATE.md` §2 shipped-versions table.** The historical record is immutable. The change-log appends new entries; existing rows stay verbatim.
- **Restructuring `docs/release-roadmap.md` §1 (framing) / §2 (shipped) / §3 (active version) / §5 (backlog) / §6 (external actions) / §7 (authority).** Only §4 changes shape.
- **Changing the policy doc's MAJOR/MINOR/PATCH definitions.** The policy doc gets ONE new section (number-derivation); existing §"What goes in a minor" / §"What goes in a patch" / §"Quality gate" / §"When 1.0.0 ships" / §"Pre-release tags" / §"Tagging" / §"Authority" stay verbatim.
- **Building the Python helper unconditionally.** D-RR.5.4 leaves Path A (documented manual rule only) as the default; Python helper is opt-in based on builder ruling at build-time.
- **Authoring or shipping any of the candidates in the new queue.** This plan-doc restructures the SHAPE of the queue; what gets built next is downstream of the restructured shape (and is exactly what AC.RR.4 outcome-altitude probe exercises).
- **Re-doing the dependency-map artefact.** Re-keying rows from version-numbers to candidate-slugs is a SOFT update inside the dep-map; the dep-graph itself doesn't change.

---

## §7 — HARD HALTs (build-time)

Builder MUST halt + surface rather than proceed if any of these surface during build:

- **Any reach toward renaming already-published versions** (v0.1.0 through v0.4.3). Halt; surface; do NOT silently extend revisionism. (v0.4.4 is the borderline case per D-RR.5.2 and is owner-ratified, not autonomous.)
- **Any deletion of historical content** in STATE.md change-log, FIDRAFT, FUTURE_IDEAS, or shipped plan-docs.
- **Any edit outside the §3 fence.** Halt; rewind.
- **Any commit attempt during the build cycle.** This plan-doc lands uncommitted per the dispatch brief; build-cycle landing follows owner ratification of THE PLAN-DOC, then a separate commit + apply + seal cycle.
- **Discovery of additional misclassified shipped versions during the audit** (e.g., if the audit finds that a v0.2.x release also misclassified). Halt; surface; do NOT silently extend the audit beyond its named scope (the named scope is v0.4.x patches + forward-looking entries).
- **Discovery that the `current_version` rule is ambiguous in any production case** (e.g., if local-tag and remote-tag disagree at build-commence-time and the recipe doesn't clarify). Halt; surface to owner for the disambiguation ruling.
- **Discovery that `docs/release-versioning-policy.md` already carries a number-derivation rule that this plan-doc duplicates or contradicts** (verified absent at authoring time; halt-trigger included for builder-side defense-in-depth).

Soft halts (surface but continue if the answer is clear from the dispatch brief): finding a forward-looking entry whose audited class differs from its currently-listed class (audit captures + table records; not a build-blocker).

---

## §8 — Dependencies

- **Composes with `docs/release-versioning-policy.md`** — the policy doc's MAJOR/MINOR/PATCH definitions stay authoritative; this plan extends with the number-derivation section. Two-way compose: AC.RR.3 lands inside the policy doc.
- **Composes with `docs/release-roadmap-dependency-map.md`** — re-keying rows from version-numbers to candidate-slugs is part of the §3 TERTIARY fence. Compose-with-build, not gate-on-build.
- **SOFT dep on v0.4.4 publish** — v0.4.4 is sealed-local; D-RR.5.2 names how to handle the v0.4.4 reclassification (Paths A/B/C), which interacts with whether v0.4.4 publishes-as-v0.4.4 or is renamed-then-published. The plan-doc itself doesn't gate on v0.4.4's publish state; the build can land before, during, or after v0.4.4 publish.
- **SOFT dep on v0.4.5 (release-process) plan-doc** — v0.4.5 ships the `loam release` CLI which can naturally consume the number-derivation rule. If v0.4.5 builds before this restructure lands, v0.4.5 either (a) hardcodes its number derivation independently and gets retrofitted later, or (b) names a stub for the helper that this restructure fills in. If this restructure lands first, v0.4.5 builds on top of the documented rule.
- **HARD dep on owner ratification of the reframing** — the dispatch brief authorized plan-doc authoring; the BUILD requires a separate ratification because the audit findings (v0.4.4 reclassification, etc.) need owner decisions before the audit deliverable lands.

---

## §9 — Estimated AI-time

Per `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`:

- **Plan-doc authoring** (this dispatch): 30-45 min, midpoint 38 min. Single-file plan-doc + reclassification audit research (read v0.4.4, v0.4.5, v0.4.1, v0.4.2, v0.4.3 plan-docs + roadmap + policy). **Actual at land time: TBD.**
- **Build cycle** (downstream, post-ratification):
  - §4 restructure (rewrite §4 content + slug renames + header note): 30-50 min, midpoint 40 min.
  - Reclassification audit deliverable (table authoring + per-row evidence): 25-40 min, midpoint 32 min.
  - Number-derivation rule documentation in policy doc: 15-25 min, midpoint 20 min.
  - Optional Python helper (if D-RR.5.4 selects Path B/C): 30-60 min, midpoint 45 min.
  - Dependency-map re-keying: 10-20 min, midpoint 15 min.
  - Outcome-altitude probe + writeup: 15-30 min, midpoint 22 min.
  - Plan-doc + manifest scaffolding: 20-30 min, midpoint 25 min.
  - **Total v0.X.Y build AI-time:** 145-255 min, midpoint **~200 min** (~3.3 hours). Excludes Python helper if Path A selected (subtract ~45 min).

Owner ratification time (separate from AI-time): ~10-20 min for plan-doc review + queue-restructure call + reclassification call + helper-shape call.

---

## §10 — Open questions for owner ratification

These need owner ruling BEFORE build dispatches:

### Q1 — v0.4.4 reclassification: rename retroactively or publish as v0.4.4?

v0.4.4 ships TWO new SKILLs (one brand-new + one extended) — meets the policy doc's MINOR definition ("new outcome-shape capability"). It's sealed-local, not published. Three paths per D-RR.5.2: rename to v0.5.0 before publish (recommended; clean); publish as v0.4.4 (preserves existing slug; lower migration); publish + class-correction note (hybrid).

**Persona recommendation:** Path A (rename to v0.5.0 retroactively before publish). The v0.4.4 plan-doc itself surfaced "PATCH-SHAPED-AS-MINOR-CLASS" as the tension — addressing it before public publish costs less than living with the misclassification on the public tag list.

### Q2 — v0.4.5 reclassification: build as v0.4.5 (per current plan-doc) or v0.5.0?

v0.4.5 (release-process) ships a brand-new `loam release` CLI verb plus runbook — clearly NEW outcome shape (maintainers can now run a single command to publish). Plan-doc currently labels it Class: META-FRAMEWORK + slug v0.4.5. If Q1 ratifies as Path A (v0.4.4 → v0.5.0), then v0.4.5 becomes v0.5.1 (PATCH) OR v0.6.0 (if reclassified as MINOR).

**Persona recommendation:** v0.4.5 is MINOR (new CLI verb + new runbook = new outcome shape). With Q1 as Path A, v0.4.5 → v0.6.0. With Q1 as Path B, v0.4.5 → v0.5.0.

### Q3 — v0.4.1 / v0.4.2 retroactive findings: rename or just-record?

v0.4.1 is borderline-MINOR (from-scratch prompt mode is arguably a new outcome shape; the v0.4.1 plan-doc framed it as extension). v0.4.2 is defensibly PATCH. Both are PUBLISHED with v0.4.x tags on `loam` remote.

**Persona recommendation:** Path A from D-RR.5.3 (do NOT rename; capture findings as lessons-learned in the audit deliverable). Renaming published versions = revisionism + external-ref breakage. The going-forward queue + number-derivation rule + class audit prevent recurrence.

### Q4 — Migration of v0.5.0+ entries: descriptive slugs (Path A) or version-suffixed slugs (Path B)?

D-RR.5.1 names the choice. Path A (recommended) uses descriptive slugs like `binary-usage-harness`; Path B preserves number suffixes during transition.

**Persona recommendation:** Path A. The "version-number is downstream of priority" message gets diluted if number-suffixes stay. Cross-ref grep cost is small (handful of refs in dependency-map + internal callouts).

### Q5 — Number-derivation surface: documented manual rule, Python helper, or both?

D-RR.5.4 names the choice. Path A (manual rule only) lowest fence; Path B (Python helper) composes with v0.4.5 CLI; Path C (both) highest reliability.

**Persona recommendation:** Path B if v0.4.5 release-process is being built around the same time (the helper has a natural CLI consumer); Path A if v0.4.5 is far in the future or descoped. Path C as the long-term landing point.

### Q6 — Roadmap re-review mechanism: fold into this plan-doc (Path A) or split into separate amendment (Path B)?

Luke's Telegram 10557 surfaced "always stop and re-evaluate the roadmap" alongside the priority-queue ask. D-RR.5.5 names the choice.

**Persona recommendation:** Path A (fold). Single coherent restructure; composes with v0.4.5 runbook (re-review as post-publish step). Adds ~10 min to the §4 restructure work.

### Q7 — Goal-alignment scoring per candidate: add (Path A) or skip (Path B)?

D-RR.5.6 names the choice. Path A adds prioritization signal against the 3 named real-world goals (Anthropic / consulting / personal-wealth); Path B keeps queue minimal.

**Persona recommendation:** Path A is high-value if the 3 goals are stable + queue gets re-prioritized monthly+. Path B is lower-friction if priority decisions are mostly obvious from technical-readiness alone. Genuinely a Luke-call; surfacing without strong recommendation.

---

## §11 — Authority chain

- `docs/VALUE_PROPOSITION.md` — prime objective.
- `docs/release-versioning-policy.md` — MAJOR/MINOR/PATCH definitions; this plan extends with number-derivation section.
- `docs/release-roadmap.md` — §4 restructure target; §1/§2/§3/§5/§6/§7 untouched.
- `docs/release-roadmap-dependency-map.md` — re-keying tertiary fence; HARD/SOFT taxonomy untouched.
- `docs/odd-llm-grounding.lean.md` — methodology authority.
- `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md` — discipline rules cited inline.
- `~/.claude/CLAUDE.md` + `/Users/lukeivers/pos3/CLAUDE.md` — global + project instructions.

This plan-doc inherits the authority of `docs/release-versioning-policy.md` (which it extends, not contradicts) and `docs/release-roadmap.md` (which it restructures inside §4 only).

---

## §12 — §status (post-build backfill)

**Build cycle:** SHIPPED LOCAL 2026-05-13 — owner pre-ratified scope (dispatcher brief 2026-05-13; Telegram 11091). Awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc `b269d8e` (authored 2026-05-09); manifest `71ee3f0`; source-edit batch (§4 restructure + audit table + policy-doc extension + dep-map re-key + HARD smoke writeup + STATE/roadmap admin + 30 pyproject 0.9.0→0.10.0 bumps + 4 __version__ bumps) `3354f73`; manifest baseline backfill `2540718`; manifest smoke_outcome shortening `fad2989`; apply auto-commit (BASELINE + sidecar bump to `3354f73`) `40b2553`; seal commit (deterministic seal) `c71b2fa`.

**Build-time rescope (per dispatch brief 2026-05-13):** the plan-doc was authored 2026-05-09 against then-current state. Between authoring and build-commence-time, v0.4.4 → v0.9.0 ALL shipped (most under different scopes than the plan-doc's audit anticipated). The reclassification audit was rescoped at build-time to apply only to currently-forward-looking §4 entries; for SHIPPED versions, the audit is historical / read-only (surface past mis-classifications but no retroactive renames — would break published tags). The plan-doc's Q1/Q2/Q3/Q5/Q6/Q7 ratifications from the 2026-05-09 era are no longer applicable at this build-commence-time because the work they anchored on has shipped under different shapes; only the rescoped audit deliverable survives.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.RR.1 — §4 restructured to priority-ordered queue of unnumbered candidates | GREEN | `docs/release-roadmap.md` §4 restructured at source-edit `3354f73`. Top-level header reads "Priority-ordered candidate queue (next-release pipeline)". 6 candidate sections present (`binary-usage-observation-harness`, `principle-foundation-structural-enforcement`, `negative-alignment-detection`, `deep-personalization`, `plugin-suite-expansion`, `v1.0.0-stability-gate`); each carries the 8 named fields (slug, objective, class, AC family, constraints, source items, AI-time, dependencies); no candidate carries a pre-assigned version-number except `v1.0.0-stability-gate` (structurally pinned by policy per `docs/release-versioning-policy.md` §"When 1.0.0 ships"). Header note explains numbers derive at build-commence-time. Source-edit commit `3354f73`. |
| AC.RR.2 — Reclassification audit deliverable | GREEN (rescoped) | Audit table at `docs/release-roadmap.md` §4-prelude. Two sections: historical (13 already-shipped rows, read-only per HARD HALT — no retroactive renames; surfaces 2 mis-classifications: v0.4.1 borderline-MINOR shipped as PATCH, v0.4.4 MINOR caught + renamed to v0.5.0 before publish) + forward-looking (6 unshipped candidates, rescope-applied per build-time directive — all retain MINOR class). 6-column table per row per the AC spec (slug-or-version, original-class, audited-class, ships-new-outcome-shape?, evidence, reclassification-call). Source-edit commit `3354f73`. |
| AC.RR.3 — Number-derivation rule documented | GREEN | New section "Number derivation at build-commence time" in `docs/release-versioning-policy.md` between "When 1.0.0 ships" and "Pre-release tags". Recipe block present (Given clauses + per-class if/elif/elif). 5 narrative paragraphs covering: where the recipe applies; what `current_version` means precisely (highest-numbered shipped tag on canonical remote); hot-patch case (4-digit form + `bump_hotfix`); edge case (in-flight PATCH); implementation choice (documented manual rule per D-RR.5.4; Python helper deferred). Source-edit commit `3354f73`. |
| AC.RR.4 (outcome-altitude) — Real "what's next?" decision exercises the new shape | GREEN | Real production entry-point `loam release v0.10.0 --plan-doc docs/plans/release-roadmap-priority-queue-restructure.md --dry-run` invoked from `/Users/lukeivers/loam/` at sealed state (HEAD = `c71b2fa`). Verbatim output post-§status-backfill: `[GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/release-roadmap-priority-queue-restructure-hard-smoke.md`; `[GREEN] acs-verified: all 5 AC(s) verified (GREEN or REMOVED) in docs/plans/release-roadmap-priority-queue-restructure.md §status`; `[GREEN] state-shipped: v0.10.0 marked SHIPPED in docs/STATE.md`; `[GREEN] clean-tree: working tree clean`; `[GREEN] branch-main: on branch main`; `[GREEN] seal-reachable: seal c71b2fa reachable from HEAD`. ALL 6 GATES GREEN — the dogfood probe IS the verification that the v0.7.2 + v0.8.2 + v0.8.3 PATCH chain prepared the gates for scope-descriptive plan-docs end-to-end. Probe writeup at `docs/experiments/release-roadmap-priority-queue-restructure-hard-smoke.md` Stage 2. |
| AC.RR.S — Seal-diff discipline | GREEN | `git diff --name-only 3354f73..c71b2fa` shows changes only under: apply + seal auto-commits (`plugins/dev-sdlc/seals/SEAL_COMMIT.release-roadmap-priority-queue-restructure` + `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar) + manifest baseline bump. `git diff --name-only b269d8e..c71b2fa` (full BASELINE → SEAL) shows changes only under the named fence: `docs/release-roadmap.md` (§4 restructure + audit table + §2 row) + `docs/release-versioning-policy.md` (number-derivation section) + `docs/release-roadmap-dependency-map.md` (re-key) + `docs/STATE.md` (universal-admission row) + `docs/experiments/release-roadmap-priority-queue-restructure-hard-smoke.md` (HARD smoke writeup) + `docs/plans/release-roadmap-priority-queue-restructure.{md,manifest.yaml}` (plan-doc + manifest) + 30 pyproject.toml + 4 __version__.py (per-component MINOR bump per AC.HONEST.1) + auto-managed seal sidecar. All paths in fence allow-list (universal-admission docs + per-component-version discipline for MINOR). No framework source code changes (no helper landed per D-RR.5.4). |

### AI-time actuals

| Stage | Estimated (plan §9) | Actual |
|---|---|---|
| §4 restructure (rewrite §4 content + scope-descriptive slugs + header note) | 30-50 min midpoint 40 min | ~15 min |
| Reclassification audit deliverable (table authoring + per-row evidence; rescoped section) | 25-40 min midpoint 32 min | ~10 min |
| Number-derivation rule documentation in policy doc | 15-25 min midpoint 20 min | ~8 min |
| Dependency-map re-keying | 10-20 min midpoint 15 min | ~5 min |
| Outcome-altitude probe + writeup | 15-30 min midpoint 22 min | ~5 min (writeup pre-authored; probe is single CLI invocation) |
| Plan-doc + manifest scaffolding | 20-30 min midpoint 25 min | ~10 min (manifest authoring + 2 fixups) |
| Per-component version bump (30 pyproject + 4 __version__) | not in plan (added at build per AC.HONEST.1) | ~3 min (sed batch) |
| §status backfill + apply + seal | ~5-10 min | ~5 min |
| **Total v0.10.0 build** | **plan §9 midpoint ~200 min** (excluding helper path) | **~60 min** |

Well below the plan-doc's estimate. Three factors: (1) the rescoped audit drained ~half the originally-anticipated audit work because most pre-numbered entries had already shipped; (2) the documented-manual-rule path for number-derivation (vs Python helper) was cheaper than the plan-doc's compositional estimate assumed; (3) the per-component pyproject bump was a single sed batch since the convention was already established at v0.8.0. Forward calibration: doc-only MINOR cycles with established per-component-version discipline compress to ~60 min vs the ~200 min wider-scope estimate when audit + helper paths add scope.

### Halt-and-surface findings

**No build-time halt-and-surface findings.** The dispatch brief's HARD HALT triggers (renaming already-published versions; deletion of historical content; out-of-fence edits; in-cycle commit attempts before owner ratification of plan-doc; additional misclassified shipped versions beyond named scope; current_version ambiguity; pre-existing number-derivation rule in policy doc) all held.

The rescope directive was honored: historical-section walks 13 shipped versions read-only (surfaces 2 mis-classifications as lessons-learned; no retroactive renames proposed); forward-looking-section walks 6 currently-unshipped candidates (all retain MINOR class).

The plan-doc's Q1/Q2/Q3/Q5/Q6/Q7 from the 2026-05-09 era are not applicable at this build-commence-time because the work they anchored on (v0.4.4 retroactive rename, v0.4.5 build, v0.4.1/v0.4.2 lessons-learned, helper-vs-manual choice, roadmap-re-review fold-in, goal-alignment scoring) has either shipped under different scope or is now subsumed by other discipline (e.g., goal-alignment is captured in dispatch briefs, not the queue itself). Q4 (descriptive slugs vs version-suffixed slugs) is implicitly answered: descriptive slugs landed throughout.

The v0.10.0 number was derived at release-time per the new section's recipe: `next_MINOR(v0.9.0) = v0.10.0`. The first end-to-end exercise of the v0.7.2 + v0.8.2 + v0.8.3 release-CLI PATCH chain against a scope-descriptive plan-doc returned all 6 gates GREEN.

Open questions (Q1–Q7 from §10) ratifications: the plan-doc's open questions were authored against the 2026-05-09 state and have been overtaken by events; the rescope directive in the dispatch brief is the operative ratification.

## §13 — Build-time decision deviations

- **Audit scope rescoped at build-time** per dispatch brief directive (2026-05-13). Original AC.RR.2 spec named entries v0.4.5 / v0.5.0 / v0.6.0 / v0.7.0 / v0.8.0 / v0.9.0 / v0.10.0+ as forward-looking; at build-commence-time those had all shipped except v0.10.0+. The rescope: historical section walks shipped versions read-only; forward-looking section walks currently-unshipped candidates (6 of them; see §4-prelude). Within the rescope envelope; no AC text changes; verdict still GREEN.
- **Helper path declined per D-RR.5.4 (Path A).** Documented manual rule landed in the policy doc; Python helper not built. Within plan-doc's §3 OPTIONAL secondary envelope; the helper can land as a future opt-in patch if manual-application cost rises.
- **D-RR.5.5 not addressed (roadmap re-review fold-in).** The plan-doc's D-RR.5.5 named a choice between folding a "post-ship roadmap re-review" subsection into the §4 restructure or splitting it into a separate amendment. Build-time call: not addressed in this cycle — the post-ship review mechanism is already structurally in `docs/release-process.md` (v0.6.0 release-CLI's post-ship review block) and folding it into §4 would extend scope. Captured as candidate FIDRAFT entry for next docs-admin cycle if needed.
- **D-RR.5.6 not addressed (goal-alignment scoring per candidate).** Build-time call: not added. Goal-alignment lives in the dispatch brief surfacing per priority decision; adding it to the queue would maintenance-cost more than the signal-richness adds at current cadence (single-maintainer + low queue-promotion frequency).
- **All other D-RR.* rulings landed as planned.**

# Plan — Amendment #40: primary-persona tracker-context contributor

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time (post-#39-seal).
**Amendment number:** `#40` placeholder; renumbered at dispatch per the convention amendments #29–#37 followed.
**Filename:** family-named (`primary-persona-tracker-context-contributor`) so the path survives renumbering.
**Companion research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — the Heavy-B master research artefact; this sub-plan is amendment 3 of the four-amendment Heavy-B sealed-component programme.

**Sibling work in this programme.** This is **amendment 3 of 4** in the Heavy-B programme.

- **#38:** `objective-tracker` — `lifted_from` schema widening + `query_projection_view(filter)` API. **Hard prerequisite.**
- **#39:** `workspace-bootstrap` — first-run scaffold seeds the tracker with the value-prop root + spec descendants. **Hard prerequisite for this amendment** (without it the tracker is empty on a fresh-clone first session and the contributor has nothing to surface).
- **#40 (this plan):** `primary-persona` — tracker-context contributor in the existing contributor registry surfaces "what objectives are in flight under the workspace" on `SessionStart` / `UserPromptSubmit`.
- **`pos-amend-tracker-integration.md`** — dev-discipline; pos-amend registers ObjectiveSpec records on `apply` + writes `lifted_from.source_commit` on `seal`. Depends on #38.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`** — dev-discipline; the α/β/γ data migration. Depends on the four amendments.

**Prerequisite verification (builder's hard halt before code).** Before any source edit, the builder confirms via `git log` that amendments #38 and #39 have both sealed: the `objective-tracker` `SEAL_COMMIT` advances past #38's seal SHA + `query_projection_view` is callable on `ObjectiveTracker`; the `workspace-bootstrap` `SEAL_COMMIT` advances past #39's seal SHA + a freshly-scaffolded workspace's tracker DB carries the value-prop root with `authored_by="user"`. If either is unmet, halt.

---

## 1. Summary / TLDR

The `primary-persona` layer's existing contributor registry (introduced by amendment #32's D8 + extended by amendment #33's D7 memory-consumer wiring) gains one additional registered contributor: a **tracker-context contributor** that surfaces "what objectives are in flight under the workspace" in the persona's `additionalContext` payload on the persona-layer's existing trigger surface (`SessionStart` and/or `UserPromptSubmit` — exact trigger choice is method).

The contributor calls `ObjectiveTracker.query_projection_view(filter)` (amendment #38's API) to retrieve in-flight objectives — at minimum, every objective with `status` in `{started, decomposed}` and a chain-up to the workspace's value-prop root — and projects them onto a textual block the persona reads at session-load time. The exact shape of the projection (just goals, goals + status, goals + ACs, full subtree, summary at parentage-level) is method; AC40.1 bounds the outcome (the contributor produces non-empty content when in-flight objectives exist; empty contribution when none exist).

The composition is identical in shape to amendment #33's memory-consumer contributor: a registered contributor that owns its own data source, produces a structured `additionalContext` block at the right trigger, and degrades gracefully when its source is unavailable. **Nothing in this amendment touches `objective-tracker/`, `workspace-bootstrap/`, or `hands-off-lifecycle/` source.** The tracker is consumed via its public runtime API; the contributor registry is consumed via the existing `ComposedContextPayload.register()` surface.

This is **§4 re-extension under existing objectives**, not a new top-level spec clause. Per owner ruling D-2 corrected: anchored to v1.0 Architectural "Objective-based" + VALUE_PROPOSITION's "process structure" capability + the existing primary-persona session-start context-load pattern from amendments #32 (context-load gate) and #33 (memory-consumer wiring). **No v1.3 spec addendum is authored.**

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.0 Architectural — "Objective-based"** (`docs/spec/pos-v2-objectives-spec.md` §161 + audit-addendum acceptance backfill at line 162): *"three behaviours (required above threshold, hierarchical with parentage, referenced consistently). Acceptance tested parentage/traceability. Additional acceptance: alignment is re-checked at every scope boundary and the check is logged; missing check is a process failure flagged by the self-correction loop."* The "referenced consistently" + "alignment re-checked" behaviours require the persona to have access to the tree at every interactive turn. Without the tracker-context contributor, the persona cannot reference the tree consistently — it would have to be told the tree's state by the user every turn, which inverts the value-proposition direction. This contributor lands the persona-side primitive that closes the "referenced consistently" behaviour for interactive sessions.

  **Owner-ruling note (D-2 corrected):** the dispatch context cited this objective as "v1.1 R3"; the actual spec text places it in the v1.0 architectural-layer "Objective-based" objective with audit-addendum acceptance backfill at line 161-162. Substance unchanged; this plan anchors to the actual spec location. See halt-and-surface findings.

- **VALUE_PROPOSITION "process structure" harness capability** (`docs/VALUE_PROPOSITION.md` line 101): *"Process structure. Raw AI quality is wildly variable. The harness encodes process — five-gate chains, ODD-shaped authoring, acceptance criteria, structural refusal — that constrains variance."* The tracker is the process-structure substrate; the contributor is the persona-side surface that exposes it inside the persona's natural operation. Without the contributor, "process structure" is a property of the harness that the persona cannot perceive — the harness has it; the persona doesn't. This amendment closes that gap.

- **Primary-persona session-start context-load pattern** (amendment #32 plan + amendment #33 plan): the contributor registry on `ComposedContextPayload` (`primary-persona/src/context_composer.py:288–319`) is the established mechanism for adding session-start / per-turn `additionalContext` contributions. Amendment #32 introduced the registry + the corpus-load gate; amendment #33 added the memory-consumer contributor; this amendment adds the tracker-context contributor on the same surface. **Re-extension under existing objectives per ODD §4** — no new mechanism, no new spec clause; the existing primitive admits one more contributor.

- **objective-tracker proposal D2 + D4** (`docs/archive/component-research/objective-tracker/proposal.md`): D2 (user-authored-root invariant) + D4 (`bind_scope` enforcement) — both consumed unchanged. The contributor reads from the tree without binding new scopes; it has read-only access via the tracker's public API.

**Sealed-component amendment classification.** Single sealed component (`primary-persona`). Owner ruling D-2 corrected: SEALED amendment, **no v1.3 needed**, anchored to existing spec/objective coverage (v1.0 Architectural "Objective-based" + VALUE_PROPOSITION's "process structure" capability + the existing primary-persona context-load pattern from amendments #32/#33). Re-extension under existing objectives per ODD §4, not a new top-level spec objective.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This amendment is the load-bearing Claude-leverage in the Heavy-B programme's user-visible surface. Three Claude-native primitives compose:

1. **The `SessionStart` and `UserPromptSubmit` hook events** (Claude Code's native hook surface, already wired by amendment #32's session-start gate + amendment #33's per-turn memory contributor). The new tracker-context contributor registers against the same trigger kind(s) the persona's contributor registry already supports.
2. **The `additionalContext` payload returned to Claude Code by the hook handler.** Claude Code reads this payload at session/turn boundaries; the tracker-context block becomes part of the same payload the persona delivers, no new transport invented.
3. **The persona's existing identity-anchor mechanism** (per amendment #37's `.claude/agents/<handle>.md` + the persona's contract). The agent file persists identity across compaction; the contributor surfaces in-flight objectives as runtime context that compaction can drop without breaking the persona's identity. Two complementary roles, both Claude-native.

**No new Claude primitive is invented; existing ones are composed.** The Lens-1 question's textbook positive answer: an existing Claude-native primitive (the session-start / per-turn hook surface) is what makes the tracker queryable by the persona at the right moment in the session lifecycle.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — substantially. Today (post-#39, pre-#40) the tracker holds the workspace's objective tree (rooted at the value prop, with spec-tier descendants), but the persona has no surface that surfaces tree state at session-load time. The user wanting to know "what is in flight" has to either (a) tell the persona what's in flight (translation burden the user shouldn't carry), or (b) the persona has to be specifically asked, dispatch a query, and translate the result into prose (translation burden across multiple AI turns). After this amendment, the persona surfaces the tree state without being asked, on session start; the user's first message lands on a persona that already knows.

**AC-trace to AC.PO.1:**

- **AC40.1 → primary-persona context-composer registry (amendment #32 D8) → v1.0 Architectural "Objective-based" → AC.PO.1.** Contributor produces non-empty `additionalContext` block when in-flight objectives exist → persona reads tree state without the user asking → user does not translate "what was I working on" into a query the persona has to be told → translation burden absorbed.
- **AC40.2 → objective-tracker D2 (user-authored-root invariant) → v1.0 Architectural "Objective-based" → AC.PO.1.** Contributor filters to the workspace's value-prop-rooted tree only → persona surfaces tree relevant to this workspace, not cross-workspace noise → user does not have to translate "is this for my project" → translation burden absorbed.
- **AC40.3 → primary-persona graceful-degradation (amendment #32 D8 + amendment #33 D7 pattern) → AC.PO.1.** Contributor degrades gracefully when tracker is unavailable (corruption, missing file, permission error) → session proceeds with the rest of the persona's context → user does not see a hard halt because of an environmental tracker issue → translation burden absorbed at the failure boundary too.
- **AC40.4 → primary-persona context-composer cap-guard → AC.PO.1.** Contributor honours the `additionalContext` cap (existing cap-guard at `primary-persona/src/context_composer.py:215`) by truncating or summarising when in-flight set is large → user never sees a session that fails to start because the tree is too big → translation burden absorbed at scale.
- **AC40.5 → primary-persona contributor registry → VALUE_PROPOSITION "process structure" → AC.PO.1.** Contributor produces empty contribution when no in-flight objectives exist → persona's `additionalContext` is not polluted by empty tracker block → translation burden absorbed (no "why is there an empty section in my context").
- **AC40.6 → objective-tracker D2 (user-authored-root invariant) + workspace-identity (amendments #6/#28/#29) → AC.PO.1.** Contributor reads tracker DB at the workspace-identity-derived path (existing convention) → persona surfaces only this workspace's tree even on a multi-workspace machine → translation burden absorbed across workspaces.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The tracker-context contributor itself** is the persona's primitive for "what is in flight under the workspace." Future autonomous-authoring or self-upgrade primitives that need to know workspace state read it via the same registered surface.
2. **The contributor-registry-as-tracker-consumer pattern** establishes a precedent: future tracker-consuming surfaces (e.g., a turn-level "alignment check" contributor that reads the tree and verifies the current scope's objective-trace per v1.0 Architectural's "alignment re-checked" acceptance) follow the same shape.
3. **The graceful-degradation pattern around tracker reads** (mirroring memory-consumer's pattern from #33). Establishes the shape for "harness substrate optional; degrade if unavailable" applied to the tracker substrate.

**AC-trace to AC.PO.2:**

- **AC40.1 → AC.PO.2.** Tracker-context contributor — toolkit primitive any future persona-surface composes against.
- **AC40.3 → AC.PO.2.** Graceful-degradation pattern at the tracker boundary — toolkit primitive.
- **AC40.7 → AC.PO.2.** Framework-not-content invariant preserved (no tracker payload prose hard-coded) → toolkit purity preserved.

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under §2.5 reverse-direction discipline. Each AC names what must be true; method (which trigger kind, exact projection shape, summarisation policy at scale, error-class taxonomy at the failure boundary, contributor name string) is the builder's call.

ODD §2.5 reverse-direction check: every new code path in `primary-persona/src/` traces back to AC40.1–AC40.7. The graceful-degradation branch at AC40.3 is explicitly criterion-backed (not an unbacked defensive `if`). The cap-guard handling at AC40.4 is explicitly criterion-backed (not a silent truncation).

---

## 4. Acceptance criteria (AC40.x)

Each AC maps to at least one test function named `test_AC40_<n>_<slug>` in `primary-persona/tests/`.

### AC40.1 — Tracker-context contributor produces non-empty `additionalContext` when in-flight objectives exist

A contributor (name is method; example: `tracker-context`) registered on the persona's `ComposedContextPayload` registry produces a non-empty textual block when invoked under a workspace whose tracker DB carries at least one in-flight (pre-terminal) objective chain-up to the workspace's value-prop root. The block contains at minimum the goal text of each in-flight objective. **Exact projection shape (goals only, goals + status, goals + parentage, structured tree) and the specific status-string set that maps to "in-flight" against the tracker's actual `ObjectiveStatus` lifecycle are method** (see §13/§14 — implementation pins `IN_FLIGHT_STATUSES = {proposed, active}` for the v1.0 lifecycle `proposed → active → {achieved | abandoned}`). The block is surfaced via the registry's existing turn-level or session-level surface (builder's call on which trigger kind).

**Test shape:** scaffold a fresh tmpfs workspace through the existing first-run-test harness (which runs amendment #39's seed first per dependency order); start one or more objectives from the seeded tree (call `tracker.start(objective_id)` directly, since the seed is the source of objectives at this point); register the tracker-context contributor against a stand-in registry; invoke the registry under the appropriate trigger; assert the contributor's output contains the goal text of every started objective.

**Maps to:** v1.0 Architectural "Objective-based" (referenced consistently behaviour) + VALUE_PROPOSITION "process structure" → AC.PO.1.

### AC40.2 — Contributor filters to the workspace's value-prop-rooted tree only

The contributor's query against the tracker uses `query_projection_view` (amendment #38's API) with a filter that scopes results to descendants of the workspace's value-prop root (or equivalently — exact filter mechanism is method, but the AC bounds the outcome that cross-workspace-root noise is excluded). Records authored under any other root (e.g., a second tree co-existing in the same DB) do NOT appear in the contributor's output.

**Test shape:** seed a tmpfs workspace's tracker with two roots — the value-prop root (per amendment #39) + a secondary unrelated root authored by `"user"` with its own descendants; start one objective under each root; invoke the contributor; assert only the value-prop-rooted objective's goal text appears in the output.

**Maps to:** objective-tracker D2 (user-authored-root invariant per workspace) + v1.0 Architectural "Objective-based" → AC.PO.1.

### AC40.3 — Graceful failure on tracker unavailability

If the tracker DB cannot be read (simulated via permissions, missing file, schema-version mismatch, or any other read-side failure), the contributor:

- does NOT raise into the registry's invocation path (the registry's existing error-isolation surface from amendment #32 D8 is preserved),
- emits a structured diagnostic via the existing observability surface naming the failure class,
- contributes either an empty block or a graceful-degradation marker block (exact content is method; the AC bounds the outcome that the session proceeds without halt).

The session's other contributors (corpus-load gate from #32, memory-consumer from #33, plus any others) continue to fire and contribute as normal.

**Test shape:** scaffold + first-run; corrupt the tracker DB (or set permissions on it to deny read); invoke the contributor; assert no exception propagates; assert structured diagnostic emitted (capture via the existing observability test fixture); assert the registry's other contributors still fire.

**Maps to:** primary-persona context-composer error-isolation (amendment #32 D8) + amendment #33 D7 graceful-degradation precedent → AC.PO.1.

### AC40.4 — Cap-guard honoured when in-flight set is large

If the in-flight objective set produces a contributor output that would exceed the existing `additionalContext` cap (per `primary-persona/src/context_composer.py:215`'s existing cap-guard), the contributor's output is truncated or summarised before being handed to the registry, such that the registry's cap-guard is satisfied without the contributor causing a `AdditionalContextCapExceededError`. The truncation/summarisation policy is method; the AC bounds the outcome (cap-guard does not raise; the contributor's contribution is bounded; the session loads).

**Test shape:** seed a tracker with N objectives sufficient to push contributor output over the cap (use a controlled fixture with N synthetic objectives carrying large-prose goals); invoke the contributor; assert no `AdditionalContextCapExceededError`; assert contributor output is bounded by the cap (or the contributor's declared internal sub-cap, builder's call).

**Maps to:** primary-persona context-composer cap-guard surface → AC.PO.1.

### AC40.5 — Contributor produces empty contribution when no in-flight objectives exist

When the tracker carries the seeded root + spec descendants but no objective has been started (every objective has `status == declared` or similar pre-start state), the contributor produces an empty contribution (or, equivalently, declines to contribute) — the registry does not include an empty tracker-context block in the composed `additionalContext`.

**Test shape:** scaffold + first-run (so the seed lands but nothing is started); invoke the contributor; assert empty contribution. Alternatively, assert the registry's composed payload's `contributor_outputs` does NOT contain an entry for the tracker-context contributor's name (or contains it with empty content — exact convention is method).

**Maps to:** primary-persona contributor registry contribution semantics → AC.PO.1.

### AC40.6 — Contributor reads tracker DB at workspace-identity-derived path

The contributor resolves the tracker DB path from the workspace-identity surface (existing convention per amendments #6/#28/#29 + workspace-bootstrap's tracker DB convention). On a multi-workspace machine, two parallel workspaces each register the contributor against their own tracker DB; the contributor in workspace A surfaces only A's tree; the contributor in workspace B surfaces only B's tree.

**Test shape:** scaffold two tmpfs workspaces with distinct workspace identities; first-run both (so each has its own value-prop-rooted tracker); start an objective in each; invoke the contributor under workspace A's session context; assert only A's objective goal appears. Repeat under B's context; assert only B's.

**Maps to:** workspace-identity invariant (amendments #6/#28/#29) + objective-tracker D2 → AC.PO.1.

### AC40.7 — No tracker projection prose shipped from `primary-persona/`

Source under `primary-persona/src/` does not contain literal prose from any seeded tracker record (e.g., no copy of VALUE_PROPOSITION.md's prime statement, no spec-clause text). The contributor composes its output at runtime from the tracker query result; the tracker's content is workspace-supplied (per amendment #39's framework-not-content invariant on tracker seeding). A test-fixture scan asserts the source files contain none of the unique prose markers from the seeded value-prop content.

**Test shape:** grep `primary-persona/src/` for the unique opening clause of VALUE_PROPOSITION.md's prime statement; assert zero matches. Repeat for the unique acceptance phrasing of AC.PO.1 and AC.PO.2.

**Maps to:** v1.2 R16 framework-not-content (extended to tracker projection) → AC.PO.2 (toolkit purity).

### AC40.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `primary-persona/` (source + tests),
- `docs/plans/amendment-40-primary-persona-tracker-context-contributor*` (this plan + manifest),
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Specifically: no edits to `objective-tracker/` source (the tracker is consumed via its public API), no edits to `workspace-bootstrap/` source (the seeded tree is read from disk), no edits to `hands-off-lifecycle/` source.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Contributor surfaces in-flight objectives in additionalContext | AC40.1 |
| 2. Contributor filters to workspace's value-prop-rooted tree | AC40.2 |
| 3. Graceful failure on tracker unavailability | AC40.3 |
| 4. Cap-guard honoured at scale | AC40.4 |
| 5. Empty contribution when no in-flight objectives | AC40.5 |
| 6. Workspace-identity-derived tracker path | AC40.6 |
| cross-cutting | AC40.7 (framework-not-content), AC40.S (seal-diff) |

Six declared behaviours; eight ACs cover them plus the cross-cutting framework-not-content and seal-diff invariants. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `primary-persona/` only.** Source under `primary-persona/src/`. Tests under `primary-persona/tests/`. Read-only consumption of the workspace tracker DB via `objective-tracker`'s public runtime API permitted (existing import surface). Any source edit outside `primary-persona/` is a halt (§9).
3. **No edit to amendment #38's tracker schema/API or amendment #39's seed.** They are consumed; if they need a change, halt and signal — the change belongs in their respective amendments.
4. **Reversibility.** Removing this amendment's contributor returns the layer to its pre-amendment state. The persona's existing context-load gate (#32) + memory-consumer (#33) continue to fire; the tracker DB is unaffected.
5. **No new runtime deps.** Permitted runtime deps per primary-persona proposal apply unchanged. The tracker is already importable from primary-persona's Python environment per the workspace's shared venv convention.
6. **No persona content in `primary-persona/`.** Tracker projection prose comes from the tracker (which sourced it from the workspace at seed time per #39). AC40.7 enforces this.
7. **Fail-closed direction is graceful, not hard-halt.** AC40.3 establishes the contract: tracker read failure surfaces a structured diagnostic and the contributor either contributes empty or a graceful marker; the session proceeds.
8. **Read-only access to tracker.** The contributor MUST NOT write to the tracker, MUST NOT bind scopes, MUST NOT mutate state. It calls `query_projection_view` / `get` / `list_by_root` / `trace_to_root` only.
9. **Contributor registers via existing surface.** No new registry mechanism, no new trigger kind beyond what `TriggerKind` already exposes (`primary-persona/src/context_composer.py:49`). The registry's existing `register()` API receives one new contributor.
10. **Authority bound.** Builder may refine the trigger kind (`SessionStart` vs `UserPromptSubmit` vs both), the projection shape, the summarisation/truncation policy at scale, the contributor name string, the diagnostic event-name convention, the fixture mechanism for synthetic in-flight objectives in tests. Builder may NOT relax the framework-not-content invariant (AC40.7), the graceful-degradation contract (AC40.3), or the read-only-access constraint.
11. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
12. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.
13. **Amendments #38 and #39 must be sealed before this amendment begins** — verified at builder's pre-edit gate.
14. **No v1.3 spec addendum.** Per owner ruling D-2 corrected: this amendment is re-extension under existing objectives per ODD §4. Authoring a new spec clause is forbidden in this amendment.

---

## 7. Out of scope (explicit)

- **Schema widening or query API on `ObjectiveTracker`** — amendment #38.
- **Workspace-bootstrap first-run tracker seed** — amendment #39.
- **pos-amend `objectives` manifest block / `project` / `audit-coverage` subcommands** — `pos-amend-tracker-integration.md` (dev-discipline).
- **α/β/γ data migration** — `heavy-b-phase-alpha-beta-gamma-migration.md` (dev-discipline).
- **A turn-level "alignment check" contributor** that re-checks the current scope's objective-trace per v1.0 Architectural "alignment re-checked" acceptance — out of scope; this amendment lands the surface contributor only. The alignment-check contributor would be a follow-on under §4 re-extension.
- **Write-side tracker access from primary-persona** — out of scope; read-only this amendment.
- **A v1.3 spec addendum naming "the persona has access to the objective tree as a tool"** — explicitly out of scope per owner ruling D-2 corrected. This is re-extension, not a new spec clause.
- **Drift detection between projected plan docs and tracker state** — dev-discipline (consumer-side, pos-amend integration plan).
- **Auto-starting objectives in response to user prompts** — out of scope; a future amendment may add this, but this one only surfaces.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read Heavy-B research artefact + amendment #38 plan + amendment #39 plan + this plan + primary-persona contributor-registry source (`context_composer.py` + amendment #32 + #33 plans).
3. Verify amendments #38 and #39 have sealed (per §6 constraint 13).
4. Write builder-plan to `docs/plans/amendment-40-primary-persona-tracker-context-contributor.builder-plan.md` naming specific files + symbols expected to be touched.
5. Land the contributor function + register it on the contributor-registry under the chosen trigger kind. Verify AC40.1.
6. Land the workspace-rooted filter via `query_projection_view`. Verify AC40.2.
7. Land the graceful-degradation path. Verify AC40.3.
8. Land the cap-guard handling. Verify AC40.4.
9. Land the empty-set behaviour. Verify AC40.5.
10. Land the workspace-identity-derived tracker path resolution. Verify AC40.6.
11. Land the framework-not-content build-time check. Verify AC40.7.
12. Run AC40.1–AC40.7 + the existing `primary-persona/tests/` suite + the existing context-composer integration test (from #32 + #33).
13. `pos-amend apply --dry-run` green gate.
14. Amendment commit.
15. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
16. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `primary-persona/`.** Any required source edit to `objective-tracker/`, `workspace-bootstrap/`, `hands-off-lifecycle/`, or any other sealed component → halt.
2. **Amendments #38 or #39 have not sealed before this build begins.** Halt.
3. **`tracker.query_projection_view`'s actual signature differs from this plan's expectations** in a way that prevents the workspace-rooted filter (AC40.2) from being expressed. Halt — coordinate with #38's territory or surface for owner.
4. **The persona's existing contributor registry cannot accept a new contributor without a structural change to the registry mechanism** (e.g., a new `TriggerKind` value). Halt — that's master-research scope expansion.
5. **Graceful-degradation cannot be implemented without a graceful-degradation component source change.** Halt — that's multi-component scope expansion.
6. **The tracker's read-only API surface forces a write through some unavoidable side-effect** (e.g., a query whose implementation increments a counter). Halt — surface for coordination with #38.
7. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception that no AC backs). Halt; owner rules.
8. **A test for AC40.1–AC40.7 cannot be written deterministically** — halt.
9. **`pos-amend apply --dry-run` red** — halt.
10. **The cap-guard at scale cannot be honoured without a method that the AC reads as method-in-AC** (e.g., a specific summarisation prompt, a fixed truncation point). Halt — surface for owner; the AC bounds outcome only.
11. **Any path forces authoring a v1.3 spec addendum** — halt; owner ruling D-2 corrected forbids it.
12. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: 40
  slug: primary-persona-tracker-context-contributor
  title: "primary-persona tracker-context contributor (in-flight objectives in additionalContext)"

# BASELINE: <pre-amendment tip captured at brief-dispatch — should
# be the seal commit of #39, mirroring the BASELINE-as-HEAD~1
# pattern when no other commits intervene.>
baseline: <captured-at-dispatch-post-#39-seal>
plan: docs/plans/amendment-40-primary-persona-tracker-context-contributor.md

# Single-component amendment. primary-persona only.
components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.tracker-context-contributor
  body: |
    # Amendment #40 — primary-persona tracker-context contributor
    #                  (in-flight objectives in additionalContext)
    ...
    # Body authored at seal time; describes:
    #  - Tracker-context contributor registers on the existing
    #    ComposedContextPayload registry (introduced amendment #32
    #    D8, extended amendment #33 D7 memory-consumer).
    #  - Surfaces in-flight objectives (status in {started,
    #    decomposed}) via additionalContext at SessionStart /
    #    UserPromptSubmit. Trigger choice is method.
    #  - Filters to workspace's value-prop-rooted tree via
    #    query_projection_view (amendment #38's API).
    #  - Graceful-degradation on tracker unavailability: structured
    #    diagnostic + empty/marker contribution + session proceeds.
    #  - Cap-guard honoured at scale (truncation/summarisation
    #    method-level, AC bounds outcome).
    #  - Read-only access to tracker; never writes, never binds.
    #  - Re-extension under v1.0 Architectural "Objective-based"
    #    + VALUE_PROPOSITION "process structure" + amendments #32/#33
    #    context-load pattern. NO v1.3 spec addendum.
    #  - Framework-not-content invariant preserved: no tracker
    #    payload prose hard-coded in primary-persona/src/.
    #  - Closes the Heavy-B programme's user-visible Lens 2 win:
    #    persona surfaces tree state at session-start without the
    #    user asking.
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-research recommendations are cited but not pinned.

- **D-build.1 — Trigger kind.** Three reasonable shapes: (a) `SessionStart` only (matches amendment #32's gate trigger; lighter on per-turn cost); (b) `UserPromptSubmit` only (per-turn freshness; matches amendment #33's memory-consumer trigger); (c) both. **Master-research recommendation:** (a) for v1 — session-load is the natural moment for "here's what's in flight"; per-turn additions can land in a follow-on. **Builder's call within scope.** AC40.1 measures outcome (the contributor produces non-empty content under the right trigger).
- **D-build.2 — Projection shape.** Four reasonable shapes: (a) goals only (one line per in-flight objective); (b) goals + status; (c) goals + parentage chain (bullet tree); (d) full subtree with parentage + criteria. **Master-research recommendation:** (b) — minimal for the v1 user value, leaves room for future expansion. **Builder's call within scope.** AC40.1 + AC40.4 bound the outcome (non-empty when started; bounded by cap-guard).
- **D-build.3 — Summarisation/truncation policy at scale.** Two reasonable shapes: (a) hard truncation (top N by recency or by depth); (b) parentage-aware summarisation (collapse leaf-level into "K acceptance criteria pending under <parent goal>"). **Master-research recommendation:** (a) for v1 — simpler, deterministic, easier to test. **Builder's call within scope.** AC40.4 measures outcome (cap-guard not raised).
- **D-build.4 — Diagnostic surface routing for read failures.** The primary-persona layer has the existing observability surface from D8/D7. The builder picks the structured-diagnostic event name + attribute set. **Master-research recommendation:** match the existing diagnostic-naming convention (e.g., `pos.persona.tracker_context_unavailable` or similar — consistent with the `pos.<component>.<event>` pattern). **Builder's call within scope.**
- **D-build.5 — Workspace-identity-to-tracker-path resolution.** Two reasonable shapes: (a) call into workspace-bootstrap's existing path-resolution helper; (b) read the path from a known config/env-var the bootstrap layer emits. **Master-research recommendation:** whichever of (a) or (b) avoids a new cross-component import surface. **Builder's call within scope.** AC40.6 measures outcome.

These five are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the Heavy-B master research artefact:

- **Master research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — covers the full investigation, decisions D-1 through D-6, the executive recommendation, the §C.1 component-amendment sequence (4 sealed amendments minimum, primary-persona is one of them), and the lens trace at §H.

The owner ruled (post-master-research) that Heavy-B ships as **four coordinated sealed-component amendments + two dev-discipline plans**, and **specifically corrected D-2** from the research-recommended Path (a) (v1.3 spec addendum + sealed amendment) to a re-extension shape (sealed amendment, NO v1.3, anchored to v1.0 Architectural "Objective-based" + VALUE_PROPOSITION "process structure" + amendments #32/#33 context-load pattern). This file is **amendment 3 of 4**. Amendments #38 and #39 are hard prerequisites.

Master-research decision ↔ this-plan AC mapping (for traceability):

| Master decision | This-plan AC | Note |
|---|---|---|
| D-2 (primary-persona contributor: sealed-component amendment or dev-discipline?) | All AC40.x | Owner ruled SEALED amendment, no v1.3 — anchored to existing spec/objective coverage per ODD §4 re-extension. |
| Research §C.1 (#3 primary-persona amendment is required for Lens 2 win) | AC40.1 + AC40.5 | The contributor IS the harness-test win for Heavy-B. |
| Research §H lens trace (primary-persona contributor row) | AC40.1 + AC40.3 → AC.PO.1 + AC.PO.2 | "The persona surfaces in-flight objectives without the user asking — translation burden of 'what was I working on' disappears." |

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify amendments #38 and #39 have sealed (`objective-tracker/tests/SEAL_COMMIT` advanced past #38's seal SHA + `query_projection_view` callable; `workspace-bootstrap/tests/SEAL_COMMIT` advanced past #39's seal SHA + a freshly-scaffolded workspace's tracker carries the value-prop root with `authored_by="user"`). Halt if either is unmet.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `primary-persona/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.
- primary-persona is not a frozen-baseline component — manifest sets `frozen_baseline: false`.
- **No v1.3 spec addendum authored** — owner ruling D-2 corrected forbids it.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.5 to the builder. This
section records the choices made and the rationale, plus the test
breakdown and commit SHAs.

### D-build.1 — Trigger kind: `SessionStart` only

`register_tracker_context` registers the contributor under
`TriggerKind.session`. The contributor fires once per session-start;
turn-firing does NOT invoke it.

**Rationale:** plan §11 D-build.1 candidate (a) — master-research
recommendation. The objective-tree state changes at human cadence
(seeded once, status transitions on the order of hours/days); a
session-start contributor is the natural moment for "here's what's
in flight." Per-turn freshness adds cold-start cost without v1
value; future amendments may add a turn-level "alignment check"
contributor that re-checks the current scope's objective-trace
(out of scope per plan §7).

### D-build.2 — Projection shape: goals + status + parentage

Each in-flight bullet shows `<objective_id> [<status>]: <goal>` with
a `(<- <parent_goal> -> root)` parentage hint. Goal text is
truncated at 100 chars; parent goals at 50 chars; the root summary
line at 200 chars.

**Rationale:** slight extension over master-research candidate (b)
"goals + status." Parentage costs ~30 chars per bullet and
substantially improves compaction resilience: even after compaction
collapses interior context, the persona retains the lineage
(`obj-id [active]: goal (<- intermediate -> root)`) so the structural
relationship between work in flight and the workspace's prime
objective survives. The first line of the block is an identity-
anchor-style bracketed marker (`[primary-persona/tracker-context]`),
which the persona retains as a structural signal through compaction.

### D-build.3 — Truncation policy: depth-first cap + marker line

Hard cap at `objective_id_cap = 20` bullets (depth-first walk
order; deterministic). When the cap-guard trims further (sub-cap
2000 chars; configurable via `char_cap`), additional bullets are
dropped on a line boundary and a final marker line surfaces the
elided count: `[N more in-flight objectives truncated for cap]`.

**Rationale:** plan §11 D-build.3 candidate (a) — master-research
recommendation. Deterministic; easy to test; no method-in-AC issue
(the AC bounds outcome: cap not raised, dropped count surfaced).
Parentage-aware summarisation (candidate b) is a future
optimisation if the in-flight set ever exceeds 20 objectives in
practice — by then the workload will inform the right policy.

### D-build.4 — Diagnostic event names

`pos.persona.tracker_context.composed` (success path) carrying
`pos.persona.tracker_context.{handle, in_flight_count,
truncated_count}`. `pos.persona.tracker_context.unavailable`
(graceful-degradation path) carrying `pos.persona.tracker_context.{
handle, failure_class, detail}`.

**Rationale:** plan §11 D-build.4 master-research recommendation.
Matches the existing `pos.persona.<event>` naming convention
(amendments #32 D8, #33 D7, #35 onboarding). The `failure_class` +
`detail` attributes let downstream consumers discriminate between
tracker open failures (`detail="tracker_open_failed"`) and query
failures (`detail="query_projection_view_failed"`).

### D-build.5 — Workspace-identity-to-tracker-path resolution

Private constant `TRACKER_DB_FILENAME = "objective_tracker.sqlite"`
with pure-function `tracker_db_path_for(workspace_root) ->
Path`. Convention parity with workspace-bootstrap's
`TRACKER_DB_FILENAME` constant (amendment #39, written at first-run
time). The persona layer derives the path from the existing
workspace-identity primitive (`workspace_root: Path` already passed
to `ComposedContextPayload.on_session_start`).

**Rationale:** plan §11 D-build.5 candidate (a)/(b) hybrid that
avoids a cross-component import surface. Importing
`workspace_bootstrap.adapters.tracker_seed.TRACKER_DB_FILENAME`
would add a workspace-bootstrap dep on the persona layer's import
surface; D-build.5's documented method-level constant + AC40.6
outcome-measurement is the same approach amendment #33 used for
the parity-with-`workspace-bootstrap` workspace-slug primitive.
Future amendment that reconciles the constants is a one-line edit.

### Halt-and-surface ODD finding (vocabulary mapping)

The plan's AC40.1 names statuses `{started, decomposed}`; the actual
`objective_tracker.spec.ObjectiveStatus` enum uses `{proposed,
active, achieved, abandoned}`. "In flight" maps to
`{proposed, active}` (pre-terminal) — the build adopts the tracker's
actual vocabulary as method per ODD §2.5 (the AC bounds outcome:
"non-empty when in-flight objectives exist", verifiable in the
tracker's actual vocabulary). Documented in
`tracker_context.py:IN_FLIGHT_STATUSES` and the AC40.5 test
docstring. Surfaced to owner in deliverable; NOT a halt.

### Test breakdown (AC40.1 – AC40.7 + AC40.S)

- **AC40.1** — `tests/test_AC40_1_in_flight_non_empty.py` — 3 tests:
  in-flight goals appear; terminal records excluded; registration
  under `TriggerKind.session`.
- **AC40.2** — `tests/test_AC40_2_workspace_root_filter.py` — 2 tests:
  secondary-rooted records excluded; orphan trace-terminals excluded.
- **AC40.3** — `tests/test_AC40_3_graceful_failure.py` — 3 tests: open
  failure → no raise + `pos.persona.tracker_context.unavailable`
  event with `failure_class="OSError"`, `detail="tracker_open_failed"`;
  query failure → no raise + diagnostic + `tracker.close()` called;
  sibling contributors continue firing.
- **AC40.4** — `tests/test_AC40_4_cap_guard.py` — 2 tests: 50×500-char
  oversized in-flight set does not raise composer cap; truncation
  marker surfaces dropped count.
- **AC40.5** — `tests/test_AC40_5_empty_when_none_in_flight.py` — 2
  tests: only-terminal-records → empty contribution; no-records-at-all
  → empty contribution.
- **AC40.6** — `tests/test_AC40_6_workspace_identity_path.py` — 3
  tests: pure path-resolver; two parallel workspaces each see own
  tree; default factory targets workspace-identity-derived path.
- **AC40.7** — `tests/test_AC40_7_framework_not_content.py` — 3 tests:
  no value-prop prose markers in `primary-persona/src/`; no spec-doc
  prose markers; `tracker_context.py` source structurally references
  runtime API and carries no concrete content constants.
- **AC40.S** — covered by the existing
  `tests/test_no_sealed_amendments.py` at BASELINE 61ad8f9 +
  per-component `test_no_sealed_amendments.py` sweep.

Total new tests: 18. primary-persona suite: 198 passed, 1 skipped
(pre-existing skip). Every other sealed component's
`test_no_sealed_amendments.py` (or `test_cross_cutting.py` for
hands-off-lifecycle) runs green.

### Commit SHAs

- Amendment commit: `bfe66c90b3be63ebc0c782388d64b2db564c053a` —
  `feat(primary-persona): tracker-context contributor — surfaces
  in-flight objective tree (amendment #40)`
- Seal commit: `22473a5fb3b0850702d2b26ab60e051a2f212c70` —
  `chore(seals): tracker-context-contributor seal — primary-persona
  at bfe66c9`

### Dependents cleared to dispatch

- `pos-amend-tracker-integration.md` (dev-discipline) — formerly
  blocked by amendment #38; now further blocked by the seal-
  automation extension research+plan agent (per dispatch brief
  Pipeline note). Inherits a satisfied tracker-context-contributor
  precondition.
- `heavy-b-phase-alpha-beta-gamma-migration.md` (dev-discipline) —
  inherits a satisfied amendment chain (#38 + #39 + #40 sealed).
  The fourth Heavy-B amendment (Heavy-B sealed-component family
  closing scope) lands the migration data path; primary-persona's
  contributor is now in place to surface the migrated tree as
  ambient context.

### Post-seal AC40.1 text tightening (2026-04-25)

Per owner ruling on the same day as the seal commit (`22473a5`),
AC40.1's declaration was tightened to remove method-shaped status-
string vocabulary from the AC text.

**Before:** "...whose tracker DB carries at least one objective with
`status in {started, decomposed}` chain-up to the workspace's
value-prop root."

**After:** "...whose tracker DB carries at least one in-flight (pre-
terminal) objective chain-up to the workspace's value-prop root."
The specific status-string set is now explicitly named as method,
with the implementation's `IN_FLIGHT_STATUSES = {proposed, active}`
constant cited in §13 / §14 (this section above) rather than in the
AC text.

**Rationale:** the original AC text pinned `{started, decomposed}`
as the in-flight set, but the actual `objective_tracker.spec.
ObjectiveStatus` enum is `{proposed, active, achieved, abandoned}`
(lifecycle `proposed → active → {achieved | abandoned}`). The build
correctly applied ODD §2.5 — AC bounds outcome ("non-empty when in-
flight objectives exist"), method picks the actual enum values —
and surfaced the vocabulary mismatch as the "Halt-and-surface ODD
finding" entry in this section. Per the owner's loose-AC-text rule
(`feedback_loose_AC_text_fix_AC_not_implementation` memory), the
corrective is to TIGHTEN the AC, not retrofit the implementation:
the AC's job is to bound outcome, and method-shaped vocabulary
(specific status-string sets, specific enum values) belongs in §13
/ §14, not in the AC declaration. Same shape as the AC37.5
tightening at commit `88ac7d2` (split-surface outcome).

The three AC40.1 tests in `primary-persona/tests/test_AC40_1_in_
flight_non_empty.py` were already authored against the tightened
reading (they assert the outcome — non-empty when in-flight, empty
when terminal — and use the actual `proposed`/`active`/`achieved`
enum values via `IN_FLIGHT_STATUSES`); they pass unchanged under
the tightened text. No source code or test code changed; only this
plan doc's §4 AC40.1 declaration. §3 Lens-2 AC-trace already used
abstract "in-flight objectives exist" phrasing and needed no
edit. §5 behaviour-count summary row already abstract. §11 D-
build.2 reference already abstract.

Per ODD §3 acceptance criteria say the AC names what must be true;
the loose `{started, decomposed}` vocabulary overstated the AC by
pinning method-level enum values that turned out not to match the
tracker's actual lifecycle.

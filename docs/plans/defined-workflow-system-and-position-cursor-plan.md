# Defined-workflow system + position cursor + pause-if-lost — PLAN

**Status:** sub-plan-doc (research-grade plan; PLAN-ONLY, no code)
**Date:** 2026-05-31
**Working directory (for the eventual build):** `/Users/lukeivers/loam` (canonical loam repo)
**Plan authored in worktree:** `/Users/lukeivers/loam-wt-defworkflow` on branch `plan/defined-workflow-system`
**Parent plan:** `docs/plans/loam-vnext-build-plan.md` — item **P2.3** (§ line 150; gap-4 line 232; F4 line 248)
**Predecessors / load-bearing prior seals + artefacts:**
- `feedback_defined_workflow_in_context_pause_if_lost.md` — the owner law (Telegram 13235, 2026-05-31). The full two-part rule + the explicit "POSITION-TRACKING needs real design" flag.
- `docs/design/loam-doctrine.md` §"Follow the defined workflow; if you lose your place, pause" (lines 233-254) — the enshrined doctrine commitment (Lens 0 protection element).
- `docs/plans/loam-vnext-build-workflow.md` — **the first real flow + its §5 manual cursor.** This is the dogfood input AND the format prototype.
- `docs/plans/build-cursor.md` — **the live, hand-maintained position cursor** for the v-next build (the seed the persisted cursor replaces).
- `.claude/hooks/compaction_discipline_reinject.py` (pos3) — the re-injection hook the cursor composes on. Registered PreCompact + SessionStart(source=compact); settings.json also carries UserPromptSubmit + PreToolUse banks.
- FBM (file-based memory) — the durable store the cursor's data may live in (P1.1, built + sealed + live).
**BASELINE candidate (for the eventual manifest):** the predecessor's §14 SHA-register backfill commit (`d9ece972` is the current branch HEAD; the build's true baseline is set when P1.x/P2.x ordering fixes the predecessor at build dispatch time).
**Quality bar:** outcome-altitude AC proven by a real context-loss simulation at the real re-injection entry-point (not a stub); the cursor format dogfooded against the existing v-next build flow.

---

## §1 Summary / TL;DR

**What ships:** three composable pieces + one dogfood, behind a tight fence.

1. **A FLOW-DEFINITION format** — a single machine-readable + human-readable structured representation of a real multi-step process (steps, branch points, gates). Recommendation: **YAML front-matter + Markdown body**, where the YAML carries the machine-walkable node graph (step IDs, transitions, gate flags) and the Markdown carries the human-followable prose. This is the format the existing `loam-vnext-build-workflow.md` already approximates in prose; we formalize the machine half it lacks.
2. **★ The PERSISTED POSITION CURSOR** (the novel, under-designed piece — scoped tight here) — a "you are here" record that names `{flow, step, branch-state, updated-at}` and is (a) updated as work moves through a flow, (b) re-injected at every context-loss point, (c) the input to the pause-if-lost check. Recommendation: a **single small tracked file per active flow** (`docs/flows/<flow>.cursor.yaml` for build-methodology flows; `<workspace>/.loam/flows/<flow>.cursor.yaml` for user-state flows), updated by an explicit cursor-write step in the flow, read by the re-injection hook.
3. **The PAUSE-IF-LOST directive made structural** — not prose. A `position-check` that fires at every context-loss point and before consequential/destructive actions: if the cursor cannot be resolved to a definite `{flow, step}` (missing / stale / contradicted by ground truth), the system HALTS other work and re-establishes position before proceeding.
4. **ONE dogfood flow** — the **build-workflow** (`loam-vnext-build-workflow.md`), because it is exercised daily and its §5 manual cursor already exists as the seed. Converting it to the formal format + driving the persisted cursor off it is the dogfood and the outcome-altitude proof.

**AC families:** `AC.FLOWDEF.*` (format), `AC.CURSOR.*` (persisted cursor lifecycle), `AC.PAUSE.*` (pause-if-lost structural check), `AC.DOGFOOD.*` (the build-workflow runs on the system), `★ AC.REINJECT.1` (outcome-altitude — simulate context-loss, prove the cursor re-establishes position at the real re-injection entry-point).

**Key decisions baked:** format = YAML-frontmatter+Markdown (D1); cursor home = tracked file for methodology flows, `.loam/` for user-state flows (D2); re-injection = EXTEND the existing compaction-reinject hook, do not build a new engine (D3, Lens 1); pause-check = a positive-resolution gate, not an error-handler (D4); first cursor = single-active-flow, no concurrency (D5, scope-tight on the risk piece).

**F2 on scope realism:** the format + the pause-directive are high-confidence (the prose flow already exists and works by hand). The **cursor is the genuine risk** — the owner flagged it under-designed, and the parent plan's gap-4 says "design the cursor before building it." This plan does exactly that: §3 + §10 carry the cursor design with its open forks surfaced. The single largest realism risk is **cursor staleness** — a cursor that says "step 4" when work is really at "step 2" is *worse than no cursor* because it defeats the pause-check. The design treats staleness-detection as a first-class AC (`AC.CURSOR.3`, `AC.PAUSE.2`), not an afterthought.

---

## §2 Placement decisions

Per the partition rule (framework-code vs user-meaningful-state; methodology vs shipped surface):

| Item | Placement | Rationale |
|---|---|---|
| Flow-definition format spec | **tracked**, `docs/conventions/flow-definition.md` (eventual) + a schema under the format owner component | It is a convention/contract — methodology, not user-state. Mirrors `plan-docs.md`. |
| Flow definitions for methodology flows (build-workflow first) | **tracked**, `docs/flows/<flow>.flow.md` | Build-methodology processes are tracked (the build-cursor F2-corrective precedent: `.loam/` is gitignored, so methodology-position cannot live there). |
| Flow definitions for USER-FACING flows (book-writing etc.) | **tracked when shipped as harness capability; `.loam/` when workspace-instance-specific** | A shipped flow (e.g. a book-writing flow loam offers) is harness content; a user's *instance* of running it is user-state. |
| ★ Position cursor for methodology flows | **tracked**, `docs/flows/<flow>.cursor.yaml` | Same precedent as `build-cursor.md` — the cursor for a tracked methodology flow must be committable. (build-cursor.md §1: the P1.1 cursor was *silently dropped from a commit* because it lived under gitignored `.loam/` — a documented near-miss this design must not repeat.) |
| ★ Position cursor for user-facing flow instances | **`<workspace>/.loam/flows/<flow>.cursor.yaml`** (gitignored user-state) | A user's live position in *their* book-writing run is per-workspace user-state, not harness content. |
| Re-injection hook changes | **tracked**, extend `compaction_discipline_reinject.py` + register the same script on UserPromptSubmit + PreToolUse (consequential-action gate) | Lens 1 — compose on the built hook; do not author a parallel engine. |
| Pause-if-lost directive text | woven into the doctrine block the hook re-injects + the flow-definition convention | The directive is already enshrined doctrine (loam-doctrine.md 245-250); this gives it the structural carrier. |

---

## §3 Halt-and-surface BEFORE build (decisions recorded + named at plan-authoring)

These are the named design decisions I am recording now. Each is **autonomous + recorded** (I rule and recommend) unless tagged GATE (owner must rule before that part of the build proceeds). Full forks with recommendations in §10.

- **D1 — Format = YAML-frontmatter + Markdown body.** Autonomous. The machine graph (nodes/transitions/gate-flags) in YAML front-matter; the human-followable narrative in the Markdown body, same file. Rejected: pure-YAML (loses the human-readable flow the doctrine requires), pure-Markdown (the existing flow's gap — no machine-walkable position model), a separate `.bpmn`/graph format (Lens-1 violation; over-engineered for the in-context use). The existing `loam-vnext-build-workflow.md` is already this shape minus the YAML half.
- **D2 — Cursor home split: tracked for methodology flows, `.loam/` for user-state flow instances.** Autonomous. Driven by the build-cursor.md F2 precedent (a methodology cursor under gitignored `.loam/` was silently dropped from a commit).
- **D3 — Re-injection = EXTEND the compaction-reinject hook + register on UserPromptSubmit + PreToolUse.** Autonomous (Lens 1). The hook already owns "re-inject discipline at context-loss points"; the cursor block is one more thing it carries. No new engine.
- **D4 — Pause-check is a positive-resolution gate, not an error-handler.** Autonomous. The check passes only when the cursor resolves to a *definite* `{flow, step, branch-state}` that the agent can restate in one sentence (the build-workflow §5 test: "I am at step N of slice X, disposition D, gate G pending/clear"). Inability to fill that sentence = the pause condition. This makes "lost" the *default* until positively re-established — the safe-by-default posture the owner law demands.
- **D5 — First cursor: single-active-flow, no concurrency, no nesting.** Autonomous (scope-tight on the risk piece). One active flow at a time; the cursor names exactly one. Concurrent/nested flows (a book-writing flow running inside a build flow) are explicitly OUT of the first cursor (§7). This is the minimal-first-cursor the owner asked for.
- **D6 — GATE: which re-injection points carry the cursor block, and whether PreToolUse gating is advisory or blocking.** OWNER-GATE candidate. Re-injecting on UserPromptSubmit + SessionStart(compact) + PreCompact is non-controversial (additive context). Gating *PreToolUse* on a missing cursor — i.e. actually *blocking a consequential tool call* when position is unresolved — changes runtime behaviour and could block legitimate work. Recommendation: ship the cursor block as additive context on all four points; make the PreToolUse pause-check **advisory (warn, not block) in the first cut**, with a blocking mode behind an explicit opt-in. Surface for owner ruling because a blocking gate on every consequential tool call is an owner-class runtime-behaviour change (mirror of G3 in the build-workflow).

---

## §4 Spec-objective placement

- Binds to parent plan **P2.3** (`loam-vnext-build-plan.md` line 150) — "Defined-workflow system + position cursor + pause-if-lost."
- Ladders up to the **doctrine protection element** (Lens 0 / loam-doctrine.md "Follow the defined workflow; if you lose your place, pause") — which is itself a Pillar-2 (protection) commitment in `docs/VALUE_PROPOSITION.md` (the protection side, lines 43-52).
- Ladders up to the **prime objective** AC.PO.2 (protection: "a non-negotiable floor that catches the worst outcomes") — this system IS the structural guard against the FM.PROCESS-DRIFT failure class (process-deviation-under-pressure) the owner law names as the cause of "almost every worst outcome."

---

## §5 Acceptance criteria

AC IDs are scope-descriptive (per the AC-ID ratification). Each is outcome-shape — method-in-AC test passed (each AC is satisfiable by a method other than the one I have in mind).

### AC.FLOWDEF.* — the flow-definition format

| ID | Outcome | Verification (method = builder's call) |
|---|---|---|
| AC.FLOWDEF.1 | A flow definition carries BOTH a machine-walkable node graph (steps, transitions, branch/gate points) AND human-followable narrative, in one artefact. | Parse a flow definition; assert the machine half yields a walkable graph (every step reachable; every transition targets a declared step) AND the human half is present + non-empty. |
| AC.FLOWDEF.2 | The existing `loam-vnext-build-workflow.md` content is expressible in the format without losing any of its steps, gates, or branch points. | Express the build-workflow's 6 steps + 8 gates (§2-§3 of that doc) in the format; assert a round-trip preserves all nodes + gates. |
| AC.FLOWDEF.3 | A malformed flow definition (unreachable step, transition to an undeclared step, missing required field) is rejected with a corrective message — not silently accepted. | Feed three malformed definitions; assert each is rejected with a message naming the defect. |

### AC.CURSOR.* — the persisted position cursor

| ID | Outcome | Verification |
|---|---|---|
| AC.CURSOR.1 | A cursor names a definite position: `{flow, step, branch-state, updated-at}`, and the position references a step that exists in the named flow's definition. | Write a cursor; assert it resolves to a `{flow, step}` that exists in the flow's node graph; assert a cursor pointing at a non-existent step is treated as unresolved. |
| AC.CURSOR.2 | Advancing through the flow updates the cursor; after an advance, the cursor names the new step and the prior step is no longer the current position. | Drive a position advance; assert the cursor's `step` changed to the transition target and `updated-at` advanced. |
| AC.CURSOR.3 | A STALE cursor is detectable: when the cursor's claimed position is contradicted by ground truth (the flow's definition changed out from under it, or the named step no longer exists), the cursor resolves to UNRESOLVED, not to a false position. | Mutate a flow definition so the cursor's step vanishes; assert the cursor now resolves UNRESOLVED (triggers pause), never a wrong-but-confident position. |
| AC.CURSOR.4 | The cursor for a tracked methodology flow lives at a tracked (committable) path; the cursor for a user-state flow instance lives under `.loam/`. | Assert the methodology-flow cursor path is not gitignored and the user-state cursor path is. (Guards the build-cursor.md silent-drop near-miss.) |

### AC.PAUSE.* — pause-if-lost made structural

| ID | Outcome | Verification |
|---|---|---|
| AC.PAUSE.1 | At a context-loss point, if the cursor resolves to a definite position, the position (flow + step + the follow-it/pause-if-lost directive) is surfaced into context. | At a re-injection entry-point with a resolvable cursor, assert the injected context names the flow + current step + the directive. |
| AC.PAUSE.2 | At a context-loss point OR before a consequential action, if the cursor is UNRESOLVED (missing / stale / non-existent step), the structural response is a PAUSE signal — re-establish position before proceeding — not a silent continue. | With an unresolved cursor, assert the entry-point emits the pause signal (the "PAUSE — re-establish position" directive), not a normal continue. |
| AC.PAUSE.3 | The pause-check is positive-resolution: it passes ONLY when position resolves to a one-sentence restatement (`step N of flow X, branch B`); absence of a positive resolution defaults to the pause state. | Assert an empty / corrupt / ambiguous cursor defaults to PAUSE (not to "probably fine"). The lost state is the default. |

### AC.DOGFOOD.* — the build-workflow runs on the system

| ID | Outcome | Verification |
|---|---|---|
| AC.DOGFOOD.1 | The build-workflow is expressed as a real flow definition in the format, and its cursor (today's hand-maintained `build-cursor.md`) is driven as a persisted cursor through the system. | The build-workflow flow definition exists + validates (AC.FLOWDEF.2); a cursor read off it resolves to the same position the manual `build-cursor.md` block names today. |

### ★ AC.REINJECT.1 — outcome-altitude (the real-re-injection cold-walk)

| ID | Outcome | Verification |
|---|---|---|
| ★ AC.REINJECT.1 | With the build-workflow flow active and a cursor at a real mid-flow step, SIMULATING a context-loss event at the REAL re-injection entry-point (the extended compaction-reinject hook, invoked exactly as Claude Code invokes it — real envelope, real stdin) causes the agent's post-loss context to re-establish the correct `{flow, step, branch-state}`. **No pre-arranged in-memory state** — the cursor is read from disk by the real hook, the way it runs live. STUB-class re-injection (a hand-fed position string) does NOT satisfy this. | Set a real cursor at step K of the build-workflow flow on disk → invoke the real hook with a genuine SessionStart(source=compact) (and separately UserPromptSubmit) envelope on stdin → assert the hook's emitted additionalContext names flow + step K + branch-state + the pause-if-lost directive, read from the on-disk cursor. Then corrupt the cursor → re-invoke → assert the emitted context is the PAUSE directive (AC.PAUSE.2 at the real entry-point). |

**Outcome-altitude rationale:** AC.REINJECT.1 invokes the production entry-point (the actual hook, the actual envelope shape, the actual on-disk cursor) with no pre-arranged state — the cold-walk standard. It proves the load-bearing owner property: *position survives a real context-loss event*. Every other AC is a unit-level guard; this one is the system working end-to-end at the exact point the owner law says position must not be lost.

---

## §6 Build steps (method-level guidance only; builder's call per ODD §1.1)

Per-cycle shape for the eventual build dispatch (this plan does NOT build):

1. **Manifest:** `docs/plans/defined-workflow-system-and-position-cursor.manifest.yaml` (paired; authored at build dispatch). Components: the format/convention owner, the cursor library, the extended hook. `loam amend apply` + `loam amend seal` per the sealed-component convention — name `loam amend apply` explicitly in the build dispatch (sealed-component dispatch discipline).
2. **EXAMINE** (the build-workflow's own Step 1): confirm empirically what the compaction-reinject hook does today (read it; it is built — pos3 `.claude/hooks/compaction_discipline_reinject.py`), confirm UserPromptSubmit + PreToolUse banks exist in settings.json (they do), confirm FBM is live (P1.1 sealed). Disposition: **extend** (hook) + **build-new** (format spec + cursor library) + **leave** (FBM store, compose on it).
3. **DEFINE:** author the format spec + the cursor schema + the pause-check contract behind the methodology↔user-state boundary; author the ACs above into the slice plan-doc.
4. **BUILD (plan-before-code):** (a) the format spec + validator; (b) the cursor library (write/advance/resolve/stale-detect); (c) extend the hook to read the cursor + emit the position block + the pause directive, register on UserPromptSubmit + PreToolUse. Compose on the hook + FBM — no new engine (Lens 1).
5. **PROVE:** run AC.REINJECT.1 as a real cold-walk against the real hook entry-point (real envelope on stdin, real on-disk cursor) — the outcome-altitude proof. "It's wired" is not proof; a passing cold-walk is.
6. **INTEGRATE + RECORD:** express the build-workflow as the first flow definition; point its cursor at the live build position; author the version migration file; update the build-cursor; commit (new corrective commits, never `--amend`).

---

## §7 Out of scope (deferred + when)

- **Converting every process to a flow.** The fence is: the FORMAT + the CURSOR + the PAUSE-directive + ONE dogfood flow (the build-workflow). The pruning flow, the capability-adoption flow, the book-writing flow, the other dev flows are **downstream** — each is its own small follow-on once the format + cursor are proven. (Owner fence, load-bearing.)
- **Concurrent / nested flows.** The first cursor is single-active-flow (D5). A book-writing flow running inside a build flow, or two active flows at once, is deferred until the single-flow cursor is proven on the dogfood. (Scope-tight on the risk piece.)
- **Automatic cursor advancement / inference.** The first cursor is updated by an EXPLICIT cursor-write step in the flow (the way `build-cursor.md` is updated by hand today). Auto-detecting "which step am I really on" from runtime signals is a harder inference problem deferred to a later slice — and is exactly the kind of confident-but-wrong inference the pause-check exists to catch, so it must NOT be in the minimal first cut.
- **A graphical flow editor / renderer.** The Mermaid diagram in the build-workflow is hand-authored; auto-rendering the machine graph to a diagram is a nicety, not the load-bearing piece.

---

## §8 Halt triggers (in-flight conditions that abort the build)

- The cursor design as built cannot detect a stale cursor (AC.CURSOR.3 unprovable) → HALT. A cursor that can give a confident-but-wrong position defeats the entire owner law; do not ship it.
- AC.REINJECT.1 cannot be made to invoke the REAL hook entry-point (e.g. the hook envelope shape is not reproducible) → HALT and surface; a stub-only proof is explicitly disallowed by the owner directive.
- The PreToolUse blocking-gate design (D6) turns out to block legitimate work in testing → HALT, fall back to advisory-only, surface.
- Extending the compaction-reinject hook would change its existing PreCompact/SessionStart behaviour in a way that regresses the discipline-block it already carries → HALT (the hook's current job is load-bearing; the cursor block is additive, never replacing).
- The format cannot express the build-workflow's gates without loss (AC.FLOWDEF.2 fails) → HALT; the format is wrong, not the flow.

---

## §9 Bookkeeping

- **STATE.md / roadmap:** mark P2.3's first slice (format + cursor + pause + dogfood) in flight; note the downstream per-flow conversions remain open.
- **Parent plan §-backfill:** `loam-vnext-build-plan.md` P2.3 row → link this plan-doc; gap-4 (line 232) → mark "cursor design authored, see this plan §3 + §10."
- **build-cursor.md:** when the dogfood lands, the manual §5 block is replaced by the persisted cursor it drives (per workflow §5's own forward-reference, lines 210-213).
- **Migration file:** the build must author a declared version migration (structural-only if the cursor introduces a new tracked path; "no-op" valid only if nothing in user-state changes).
- **Failure-mode matrix:** add **FM.PROCESS-DRIFT** (process-deviation-under-pressure) with this system named as its structural guard (per the owner law's "add it to the matrix").

---

## §13 §status — SHA register + AC verdicts (backfilled post-seal)

**Amendment #160** `defined-workflow-system-and-position-cursor` — SEALED (local; not published, not merged to main — merge is dispatcher-gated).

| Commit | SHA | Role |
|---|---|---|
| BASELINE | `1d6c8705` | plan-doc commit (pre-build tip, post-rebase onto main `7af6a035`) |
| feature | `d9ed4f2c` | `feat(loam-cli)`: flows subpackage + tests + dogfood flow/cursor + convention + migration |
| apply | `73754790` | `chore(amend)`: BASELINE + sidecar bump; seal-test `allowed_prefixes += docs/flows/, docs/conventions/` |
| seal | `345d5008` | `chore(seals)`: deterministic seal at apply `73754790` |

**AC → test verdicts (all GREEN; loam-cli suite 159 passed, 26 new):**

| AC | Test (file::name) | Verdict |
|---|---|---|
| AC.FLOWDEF.1 | `test_AC_FLOWDEF_format::test_AC_FLOWDEF_1_carries_machine_graph_and_human_narrative` (+ empty-body) | GREEN |
| AC.FLOWDEF.2 | `test_AC_FLOWDEF_format::test_AC_FLOWDEF_2_build_workflow_expressible_without_loss` | GREEN |
| AC.FLOWDEF.3 | `test_AC_FLOWDEF_format::test_AC_FLOWDEF_3_malformed_rejected_with_named_defect` (parametrized) | GREEN |
| AC.FLOWDEF.4 (Fork C1) | `test_AC_FLOWDEF_format::test_AC_FLOWDEF_4_flat_action_list_rejected_as_not_a_flow` (+ admitted) | GREEN |
| AC.CURSOR.1 | `test_AC_CURSOR_position::test_AC_CURSOR_1_*` | GREEN |
| AC.CURSOR.2 | `test_AC_CURSOR_position::test_AC_CURSOR_2_*` | GREEN |
| AC.CURSOR.3 (staleness) | `test_AC_CURSOR_position::test_AC_CURSOR_3_stale_cursor_resolves_unresolved_not_false` | GREEN |
| AC.CURSOR.4 | `test_AC_CURSOR_position::test_AC_CURSOR_4_methodology_cursor_path_is_tracked` | GREEN |
| AC.PAUSE.1 | `test_AC_PAUSE_if_lost::test_AC_PAUSE_1_resolved_cursor_surfaces_position` | GREEN |
| AC.PAUSE.2 | `test_AC_PAUSE_if_lost::test_AC_PAUSE_2_*` | GREEN |
| AC.PAUSE.3 | `test_AC_PAUSE_if_lost::test_AC_PAUSE_3_lost_is_the_default` | GREEN |
| AC.DOGFOOD.1 | `test_AC_DOGFOOD_build_workflow::test_AC_DOGFOOD_1_build_workflow_validates_and_cursor_resolves` | GREEN |
| ★ AC.REINJECT.1 (outcome-altitude) | `test_AC_REINJECT_outcome_altitude::test_AC_REINJECT_1_real_hook_reestablishes_position_from_disk` (+ corrupt-cursor-PAUSE) | GREEN |
| (verb surface) | `test_AC_FLOW_cli_verb::*` (validate / position / pause through the real `loam flow` dispatch) | GREEN |

**Forks ruled to the plan's recommended options (NOT re-opened):** A1 (additive context on SessionStart-compact + PreCompact + UserPromptSubmit; PreToolUse advisory), B1 (single-active-flow), C1 (AC.FLOWDEF.4 flat-list rejection), D1 (tracked YAML file per flow).

**Follow-ons surfaced (out of this fence, per F2 / scope-discipline — NOT silently extended):**
- **build-cursor.md replacement** (plan §9): the manual §5 block in `docs/plans/build-cursor.md` is replaced by the persisted cursor it drives. Deferred to a doc-only follow-on so the dogfood's manual + persisted cursors stay cross-checkable in the same seal (AC.DOGFOOD.1 asserts they agree); flipping the manual block now would remove the cross-check the AC relies on.
- **FM.PROCESS-DRIFT matrix entry** (plan §9): adding the failure-mode-matrix row naming this system as the structural guard touches the protection-matrix component — a DIFFERENT sealed fence, out of this cycle's loam-cli fence. Owed as its own micro-amendment.
- **Live instance-config wiring** (D3 / A1): registering the framework `loam_cli.flows.reinject` hook on a live instance's `settings.json` (UserPromptSubmit / PreToolUse banks) is an instance-config step, owner-gated like G3 — outside this sealed framework cycle.

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **Cursor staleness is the real risk, not cursor absence.** *Disagreement:* a naive cursor design optimizes for "always have a position." *Evidence:* the owner law itself says "a stale flow you're forced to follow is worse than none" (memory F2 constraint; doctrine line 253), and build-cursor.md §1 documents a real near-miss where a cursor was *silently dropped from a commit*. A confidently-wrong cursor is the worst outcome — it defeats the pause-check by making the agent *think* it knows its position. *Alternative:* make staleness-detection (AC.CURSOR.3) and positive-resolution (AC.PAUSE.3, "lost is the default") first-class, not afterthoughts — which this plan does. The cursor must be willing to say "I don't know where I am" more readily than a human would.

2. **The PreToolUse blocking gate (D6) is genuinely double-edged.** *Disagreement:* "re-inject + pause before consequential actions" sounds clean but a *blocking* PreToolUse check on every consequential tool call could freeze legitimate work whenever a cursor is briefly unresolved (e.g. right after a new flow starts before its first cursor-write). *Evidence:* the build-workflow's own G3 is owner-class precisely because it changes runtime behaviour; a blocking pause-gate is the same class. *Alternative:* advisory-first (warn, surface position, don't block), blocking behind explicit opt-in — and surface to owner (D6 GATE). The pause discipline can be load-bearing *as injected context the agent must honour* without being a hard tool-blocker on cut one.

3. **The format risks ceremony the owner explicitly warned against.** *Disagreement:* a rich machine-graph format could push toward formalizing trivial flat action-lists as "flows." *Evidence:* the owner law's first F2 constraint — "define flows for true multi-step PROCESSES, not trivial flat actions, or we drown in ceremony." *Alternative:* the format spec must carry an explicit "is this a real multi-step process with branch points?" admission test; flat checklists do NOT become flows. (No AC mandates this yet — flagged gap; I recommend adding `AC.FLOWDEF.4`: a flat action-list is rejected as not-a-flow. See gap below.)

4. **Named AC gap (F2):** there is no AC asserting the ceremony-floor from doubt #3. *Recommendation:* add **AC.FLOWDEF.4** — "a definition with no branch/gate points and fewer than a threshold of steps is flagged as not-a-flow (a flat checklist), not silently accepted as a flow." I did not add it to §5 silently because it edges toward method-in-AC (it presumes a step-count threshold); I surface it as a fork (§10 fork C) rather than bake it.

5. **Single-active-flow (D5) may be too tight for the real LitRPG use.** *Disagreement:* the owner explicitly named "working LitRPG = keep the book-writing workflow in context" as a use case, and book-writing may run *concurrently* with a loam build. *Evidence:* owner law part 1 names the book-writing flow as a target; the money-push + LitRPG are concurrent live priorities (CURRENT-WORK). *Alternative:* keep single-active-flow for the *first* cursor (the dogfood is a build flow, single-active is honest there), but flag concurrency as the **first downstream follow-on**, not a distant deferral. Recorded in §7 + fork B.

---

## §11 Forks-with-recommendations (the dispatcher rules these)

**Fork A — Re-injection breadth + PreToolUse gate mode (the D6 GATE).**
- A1: Cursor block as additive context on SessionStart(compact) + PreCompact + UserPromptSubmit; PreToolUse pause-check **advisory** (warn). **← RECOMMENDED.** Lowest blast radius; honours pause discipline as context the agent must respect; defers the runtime-behaviour-changing block.
- A2: Same, but PreToolUse **blocking** on unresolved cursor before consequential/destructive tools. Stronger guarantee, owner-class runtime change, freeze risk.
- A3: SessionStart(compact) + PreCompact only (no UserPromptSubmit, no PreToolUse). Minimal; but UserPromptSubmit is the highest-frequency context-loss point in normal work, so this under-delivers the owner law.
- *Recommendation: A1.* Ship A2 as an opt-in mode in the same slice if cheap; otherwise A2 is a fast follow-on.

**Fork B — First-cursor concurrency scope.**
- B1: Single-active-flow, no nesting (D5). **← RECOMMENDED** for the first cursor — the dogfood is a single build flow, so single-active is honest and minimal (the owner asked for the minimal first cursor).
- B2: Multi-flow from the start. Higher design risk on exactly the piece the owner flagged under-designed; rejected for cut one.
- *Recommendation: B1, with concurrency as the named first downstream follow-on (not a distant deferral), because the LitRPG book-writing flow will want it (§10 doubt 5).*

**Fork C — The ceremony-floor AC (§10 gap).**
- C1: Add AC.FLOWDEF.4 (flat checklist rejected as not-a-flow). **← RECOMMENDED** — directly enforces the owner's anti-ceremony F2 constraint.
- C2: Leave it to convention/reviewer judgment (no AC). Lighter, but the owner named ceremony as a real failure mode, so a structural guard is warranted.
- *Recommendation: C1, framed to avoid method-in-AC — assert the OUTCOME "a flat action-list is not admitted as a flow" and leave the admission heuristic to the builder.*

**Fork D — Cursor data home: file vs FBM.**
- D1: Small tracked YAML file per flow (`docs/flows/<flow>.cursor.yaml` / `.loam/flows/...`). **← RECOMMENDED** — matches the build-cursor.md precedent exactly, trivially inspectable by the human operator, no FBM coupling for the first cut.
- D2: Store the cursor IN FBM (the durable store the owner named). More "composed," but couples the cursor's liveness to FBM's recall ranking and is harder to eyeball; over-coupling for cut one.
- *Recommendation: D1 for the cursor's authoritative home; the hook MAY additionally surface it through FBM context, but the file is the source of truth.*

---

## §12 Provenance trail

- Owner law (full two-part rule + "POSITION-TRACKING needs real design"): `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_defined_workflow_in_context_pause_if_lost.md`.
- Enshrined doctrine commitment (Lens 0 protection): `docs/design/loam-doctrine.md` lines 233-254.
- Parent plan P2.3 row + gap-4 + F4 deferral: `docs/plans/loam-vnext-build-plan.md` lines 150, 232, 248.
- First real flow + §5 manual cursor (format prototype + dogfood input): `docs/plans/loam-vnext-build-workflow.md` (§5 cursor block lines 192-213; §6 standing rules lines 217-244; whole-flow diagram lines 248-284).
- Live hand-maintained cursor + the `.loam/`-silent-drop near-miss precedent: `docs/plans/build-cursor.md` (lines 1-11, 94-99).
- Re-injection hook to extend (PreCompact + SessionStart(compact)): `/Users/lukeivers/pos3/.claude/hooks/compaction_discipline_reinject.py`; UserPromptSubmit + PreToolUse banks confirmed in `/Users/lukeivers/pos3/.claude/settings.json`.
- Plan-doc shape convention: `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- AC-ID convention (scope-descriptive): same doc §1; `feedback_scope_descriptive_ac_ids.md`.

---

*Principles applied at authoring: Pillar-2 protection guard (this IS the structural fix for FM.PROCESS-DRIFT — process-deviation-under-pressure); compose-don't-rebuild / Lens 1 (extend the compaction-reinject hook + compose on FBM + reuse the existing build-cursor as the dogfood seed — no new engine); scope↔confidence / F4 (tight on the format + pause-directive where the existing flow proves the shape; careful + minimal on the cursor, the owner-flagged under-designed risk — single-active-flow, explicit-write, file-home); outcome-altitude (AC.REINJECT.1 invokes the REAL hook entry-point with a real on-disk cursor + real envelope, no stub); ODD authoring (every AC outcome-shape, method-in-AC test passed, method left to the builder); F2 Ruthless Feedback (named the staleness-over-absence risk, the PreToolUse-blocking double-edge, the ceremony-floor gap with a recommended AC, and the single-flow-vs-LitRPG-concurrency tension — each with evidence + alternative).*

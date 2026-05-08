# Sub-plan G — Shared host-level memory + workspace-keying via `group_id`

**Status:** authored 2026-04-25. **DEFERRED — not part of the active
two-modes programme.** Captures the shared-memory-instance + workspace-
keying direction recorded mid-session 2026-04-25. Reactivates with the
multi-workspace cycle (FUTURE_IDEAS.md Idea 13's umbrella).

This sub-plan is a **stub** — it captures the design direction for
future expansion, not the full proposal. AC count is intentionally
small (5 ACs) and decisions remaining are large; the full proposal
shape lands when the multi-workspace cycle activates.

**Master plan:** `MASTER.md` (this directory). See §11.5 for the
deferred-sub-plans rationale.

---

## 1. Summary / TLDR

When multi-workspace lands, the memory-system needs to serve more than
one pos-v2 workspace from a single host. The naive shape — one memory-
graphiti instance per workspace — multiplies port allocations,
`launchd` agents, and on-disk graphs by N (the number of workspaces).
That cost grows with the user's workspace count and the per-instance
overhead is mostly redundant: graphiti's `group_id` parameter already
exposes a per-call partition key.

**Direction:** a single host-shared memory-graphiti instance serves
multiple workspaces; content is keyed per-workspace by graphiti's
`group_id` parameter, with an explicit "global" group for cross-
workspace memories (user preferences, identity facts, persona-style
choices that belong to the human, not the workspace).

The primary persona's memory consumer (amendment #33's wiring)
threads `workspace_id` on every read/write call. The default-read
filter is "this workspace's `group_id`"; explicit opt-in into the
"global" group surfaces cross-workspace user-level memories.

The active two-modes programme does not require this — single-
workspace pos-v2 keeps the existing memory-system shape (amendment
#29's per-workspace memory.yaml seam, default port 8765) and the
workspace-keying redesign defers to the multi-workspace cycle.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment,
name the specific spec objective (v1.0/v1.1/v1.2) the code will
satisfy."*

This is a sealed-component amendment to **memory-system** (and the
primary-persona's memory-consumer wiring at amendment #33). The spec-
clause anchors are TBD — the future builder names the specific
clause when this sub-plan activates. The memory-system proposal's
ACs (D1–D9) name the read/write contract and the per-workspace
keying property; the specific clause backing single-shared-instance-
with-keying is one the builder identifies post-reactivation.

Owner ruled (this session, 2026-04-25) that single-shared-instance-
with-keying is the right direction; the spec-clause anchor is method
within scope and the build proceeds against the named clauses once
identified.

§2.5 forward+reverse audit: when the sub-plan activates, every line
of new code in memory-system + primary-persona's memory-consumer
ladders to AC.G1–AC.G5 below. Reverse: every diff line traces back.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

The amendment leans on **graphiti's `group_id` parameter** — already
present in graphiti's API surface as the per-call partition key.
We do not implement the partitioning ourselves; we thread the workspace
identifier into graphiti's call shape. The Claude-side wiring (the
persona's memory consumer at #33) reads workspace identity from the
contract surface (sub-plan A's `dev_intent` field is the same shape;
workspace_id is a different field of the same contract). No new Claude
primitive is invoked.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden
between the user's natural-language intent and AI-effective execution?*

Yes. Without per-workspace keying, the persona either (a) sees memories
from every workspace and has to translate "is this memory relevant to
the workspace I'm in?" turn-by-turn, or (b) loses cross-workspace user-
level memories that are legitimately useful (Luke's preference for
numbered lists, his health context, his work style). The keying
direction lets the persona structurally see "this workspace's content
+ explicitly opted-in global content" without translation.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Yes — three new toolkit primitives:

1. **Workspace-keyed memory writes** (the persona's contributors call
   `memory.add(content, group_id=workspace_id)` by default).
2. **Workspace-filtered reads** (the persona's memory consumer queries
   `group_id=workspace_id` by default; explicit opt-in to `"global"`
   surfaces cross-workspace memories).
3. **A `memory_scope` field on PersonaContract** (decision D-G.2 below)
   gives the user finer-grained control: "remember this for me
   everywhere" vs "remember this for this project only."

### Lens 3 — ODD authoring

ACs below are outcome-shaped. Method (the exact `group_id` value
shape — path-derived slug? deterministic UUID? PersonaContract field?
— and the PersonaContract migration path) is the future builder's
call once the deferred decisions resolve.

---

## 4. Acceptance criteria (AC.G1–AC.G5)

This is a stub; the AC count is small. Each AC ladders to AC.PO.1 /
AC.PO.2 via the Lens-2 trace block in §9.

### AC.G1 — Workspace-keyed write API

The memory-system's write surface accepts a `workspace_id` parameter
(or equivalent) and forwards it to graphiti as the `group_id`. Calls
without `workspace_id` either default to the calling workspace's
identity (resolved from the contract) or raise structurally — choice
of default-vs-raise is method, but a silent unkeyed write is forbidden
(AC.PROG-style invariant).

**Test shape:** unit test in memory-system's test tree that calls the
write API with an explicit `workspace_id`; assert the underlying
graphiti call carried `group_id=<that id>`. Mirror test asserts a
default-resolved write carries the contract's workspace identity.

**Maps to:** AC.PO.1 (no per-call translation burden) + AC.PO.2
(workspace-keying is a toolkit primitive).

### AC.G2 — Workspace-filtered read API by default

The memory-system's read surface defaults to filtering by the calling
workspace's `group_id`. A read without explicit scope returns content
from this workspace only — never content from a sibling workspace.

**Test shape:** seed two workspaces' content (different `group_id`
values); call the read API from workspace A's context; assert workspace
B's content does not surface. Mirror test verifies explicit cross-
workspace queries are blocked at the API layer (or routed through the
"global" channel per AC.G3).

**Maps to:** AC.PO.1 (translation absorbed: persona never sees foreign
workspace content unintentionally) + AC.PO.2 (default-filter is
structural, not advisory).

### AC.G3 — Explicit "global" channel opt-in

The memory-system's read/write surface accepts an explicit opt-in to
the "global" group (e.g., `workspace_id="__global__"` or
`scope="global"` — exact spelling is method). Content written under
this channel is readable from any workspace. Use case: user-level
preferences (Luke's communication style, health context) that should
follow the user across workspaces.

**Test shape:** write a "global"-scoped fact from workspace A; read
from workspace B's context with explicit `scope="global"`; assert the
fact surfaces. Read from workspace B's context WITHOUT the explicit
scope; assert the fact does not surface (AC.G2's default-filter
holds).

**Maps to:** AC.PO.1 (cross-workspace user memory survives migration) +
AC.PO.2 (explicit opt-in is the toolkit shape).

### AC.G4 — Primary-persona memory-consumer wires `workspace_id` on every call

Amendment #33's memory consumer (the persona-side surface that calls
the memory-system) threads the calling workspace's identity on every
read and every write. The contract surface supplies the identity (the
PersonaContract carries a `workspace_id` field, or equivalent —
storage shape decided in D-G.1).

**Test shape:** integration test that loads a persona contract with a
known `workspace_id`; observes the persona's memory-consumer making a
write call; asserts the underlying memory-system invocation carried
the right `workspace_id`. Mirror for read.

**HALT TRIGGER:** if amendment #33's surface cannot be extended without
breaking AC33.x, surface — that's a #33 re-extension needing owner
approval.

**Maps to:** AC.PO.1 (persona never has to compute keys per call) +
AC.PO.2 (persona-side wiring is a single-source primitive).

### AC.G5 — Migration path for existing single-workspace memory content

Existing pos-v2 memory content (pre-this-amendment, all written without
per-workspace keying) is reachable from the canonical workspace after
the keying activates. Method options below in D-G.3; the AC measures
outcome — no orphaned memories.

**Test shape:** seed pre-amendment memory content (no `group_id`); run
the activation/migration shape (per D-G.3); assert the content surfaces
when the canonical workspace queries by its own `workspace_id` (or by
`"global"` — depends on D-G.3's choice).

**Maps to:** AC.PO.1 (no historical-memory loss) + AC.PO.2 (migration
is reproducible, not ad-hoc).

---

## 5. Out of scope (explicit)

- **Multi-host memory federation.** Sharing memories across hosts (not
  just across workspaces on one host) is a separate cycle.
- **Per-workspace memory budget / cost ceiling.** Cost-governance hooks
  for workspace-level memory caps belong in cost-governance amendments,
  not here.
- **Cross-workspace memory search UX.** A persona-layer surface that
  lets the user query "what do I remember about X across all my
  workspaces" is a future enabler that composes on G's primitives;
  out of scope for the stub.
- **Memory-graphiti port re-allocation.** Sub-plan D's per-workspace
  port allocation is orthogonal — if G ships, D's port-collision
  problem dissolves (one shared instance, one port). Sub-plan D
  reactivation can be merged into G's cycle when both activate.
- **Renaming `group_id` in the persona-facing surface.** The graphiti-
  level vocabulary is the integration's; the persona-facing field can
  be `workspace_id` / `memory_scope` / `group` — naming is method.

---

## 6. Halt triggers

1. **graphiti's `group_id` semantics turn out incompatible** with per-
   workspace keying (e.g., `group_id` is global-namespace, not per-
   instance, with cross-workspace contamination at the graph layer).
   Halt — the design assumption is wrong; surface alternatives.
2. **Existing single-workspace memory content cannot be migrated** to
   either a workspace-keyed group or the "global" group without data
   loss. Halt — D-G.3 needs a different answer.
3. **Amendment #33's memory-consumer surface cannot be extended** to
   thread `workspace_id` without breaking AC33.x tests. Halt — #33
   re-extension needs owner approval.
4. **PersonaContract migration breaks the schema** (e.g., adding
   `workspace_id` requires a Pydantic-schema break the contract
   carries). Halt; D-G.1 needs a different storage shape.
5. **The active two-modes programme (A/B/E/F) has not yet sealed**
   when G activates. G depends on A's contract surface; reactivation
   before A lands is a sequencing error.

---

## 7. Bookkeeping (when this activates)

`pos-amend` manifest fields (TBD — full manifest authored at activation
time):

- Components touched: `memory-system` + `primary-persona` (memory-
  consumer wiring at #33 territory).
- `seal_test`: per-component standard.
- `sidecar`: per-component standard.
- `frozen_baseline: false`.

Universal paths: `docs/plans/`, `CLAUDE.md`.

Narrative target: per-component seal narratives.

(Stub: full bookkeeping authored when the cycle activates.)

---

## 8. Dispatch-time additions (when this activates)

When the brief is drafted (post-reactivation):

- WD: canonical.
- A must have landed (sub-plan A's `dev_intent` field exists; G's
  `workspace_id` field extends the same contract).
- Plan-before-code.
- ODD §2.4 + §2.5 audit.
- No `git commit --amend`.
- Multi-workspace integration-test fixture available (per AC.PROG.1's
  deferred shape — when multi-workspace activates).

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 (translation burden) | AC.PO.2 (toolkit primitive) |
|----|------------------------------|------------------------------|
| AC.G1 | Persona never computes `group_id` per call. | Workspace-keyed write API. |
| AC.G2 | Persona never sees foreign-workspace content unintentionally. | Default-filter is structural. |
| AC.G3 | Cross-workspace user memory (Luke's prefs) survives. | Explicit opt-in is named. |
| AC.G4 | Persona's memory-consumer wires keys once at the seam. | Single-source wiring primitive. |
| AC.G5 | No historical-memory loss on activation. | Reproducible migration. |

---

## 10. Decision register (sub-plan-local)

These decisions remain for owner ruling **when this sub-plan
activates** (not now — the stub captures the direction; owner rules
on specifics at reactivation time).

| Code | Question | Status |
|------|----------|--------|
| D-G.1 | What is the workspace-id value shape? Path-derived slug (e.g. `pos-v2`, `pos-v2-eval`)? Deterministic UUID derived from absolute path? Persona-supplied free-form name? Stored on PersonaContract or sub-plan-A's `dev_intent` companion field? | Owner rules at reactivation. **Recommendation seed:** path-derived slug (matches amendment #6's slug-namespaced launchd labels) + collision detection per Idea 9. |
| D-G.2 | Should PersonaContract carry a `memory_scope: workspace\|global\|both` field for finer-grained user preference (per-memory rather than per-call)? | Owner rules at reactivation. **Recommendation seed:** start without it (per-call is enough for v1); add only if observed UX surfaces demand. |
| D-G.3 | Migration path for existing single-workspace memory content: (a) bulk-relabel into the canonical workspace's `group_id`; (b) bulk-relabel into the `"global"` group; (c) leave un-keyed content as a sentinel third group readable by all workspaces with explicit opt-in. | Owner rules at reactivation. **Recommendation seed:** (a) — most existing content is project-specific to canonical, not user-level. |
| D-G.4 | When activated, should this absorb sub-plan D's per-workspace port allocation (since shared instance dissolves the port-collision problem) or leave D as a separate deferred sub-plan? | Owner rules at reactivation. **Recommendation seed:** absorb — single shared instance means D's outcome is satisfied trivially; D's sub-plan file retires when G ships. |

---

## 11. Builder freedom (when this activates)

Builder chooses (within scope):

- The exact `group_id` value-shape (subject to D-G.1's owner ruling).
- The memory-consumer wiring shape on the primary-persona side
  (extend amendment #33's surface or author a thin keying wrapper).
- The migration script's home (`tools/`-resident script vs first-run
  hook vs one-shot operator-run shape).
- The "global" group's spelling (`__global__`, `global`, `*`, etc.).

Builder may NOT relax:

- AC.G2's default-filter (workspace-bounded reads is structural).
- AC.G4's wire-on-every-call (silent unkeyed writes are forbidden).
- AC.G5's no-orphan-memories outcome.

---

## 12. Test register (stub)

| AC | Suggested test home | Suggested test function |
|----|---------------------|--------------------------|
| AC.G1 | `memory-system/tests/test_workspace_keying.py` | `test_AC_G1_write_api_threads_workspace_id` |
| AC.G2 | `memory-system/tests/test_workspace_keying.py` | `test_AC_G2_default_read_is_workspace_filtered` |
| AC.G3 | `memory-system/tests/test_workspace_keying.py` | `test_AC_G3_global_channel_opt_in_surfaces_across_workspaces` |
| AC.G4 | `primary-persona/tests/test_memory_consumer_workspace_keying.py` | `test_AC_G4_consumer_wires_workspace_id_on_every_call` |
| AC.G5 | `memory-system/tests/test_workspace_keying.py` | `test_AC_G5_existing_content_reachable_post_activation` |

(Test homes are method; final builder chooses.)

---

## 13. Asymmetric observations

1. **graphiti's `group_id` is the leverage point.** The partitioning
   primitive already exists at the integration's API surface; we
   thread an identifier through, we don't author a partitioning
   layer. **Effort:** low. **Leverage:** high (one shared instance
   serves N workspaces; per-workspace overhead vanishes).

2. **PersonaContract is already the durable workspace-identity
   carrier.** Sub-plan A's `dev_intent` field is the same contract
   surface; adding `workspace_id` is one more field, same lifecycle.
   **Effort:** low (one Pydantic-schema extension, mirrored by A's).
   **Leverage:** high (every persona-layer consumer reads the contract
   once; workspace identity flows through the same channel).

3. **Sub-plan D dissolves into G if G ships first.** Per-workspace
   port allocation (D's outcome) is unnecessary when one shared
   instance serves all workspaces — the port-collision problem
   doesn't exist. The cleanest activation order at multi-workspace
   reactivation time is G → (D retires) rather than G alongside D.
   Captured in D-G.4 above.

4. **Inverse-asymmetric: a per-workspace memory-graphiti instance
   alongside G.** Tempting because it preserves data-isolation at the
   instance layer (not just the API layer), but the cost is N
   processes, N ports, N launchd agents, N graph files — for a
   property graphiti's `group_id` already gives at the API layer.
   Inverse-asymmetric (medium-high cost, low marginal leverage over
   `group_id` keying); dropped from the stub.

5. **Inverse-asymmetric: a custom partition layer in front of
   graphiti.** Tempting if graphiti's `group_id` semantics are
   weak, but the work to author + maintain a custom partition layer
   is medium-high and the leverage is paid only once, at integration
   time. Halt-trigger 1 covers the case where `group_id` is genuinely
   inadequate; otherwise dropped.

---

*Stub status: this sub-plan captures the design direction. Full
proposal authored at multi-workspace reactivation time, when D-G.1–
D-G.4 receive owner rulings and the AC surface expands beyond the
five recorded above.*

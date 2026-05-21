# Amendment plan — memory-consumer wiring, primary-persona first wave (D7)

**Amendment number:** unassigned at authoring. Assigned at
build-dispatch per owner ruling 2026-04-24. Plan filename carries no
numeric prefix.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Authored:** 2026-04-24. **Status:** plan (pre-dispatch). No code,
no manifest, no bookkeeping mutations have occurred.

**Research.** D7 cycle:
`docs/plans/research/memory-consumer-wiring-research-plan.md` →
`docs/plans/research/memory-consumer-wiring-research.md`.
Sibling D8 research for shared-composer context:
`docs/plans/research/session-start-context-load-gate-research.md`.

**Sibling amendment.** D8 (session-start structural context-load gate)
is authored in parallel as a second sibling amendment against the
primary-persona layer. Both amendments register contributors against a
shared `additionalContext` composer inside the persona layer. This
plan is authored under the assumption that **whichever amendment
lands first introduces the composer; the other registers against it.**
See §3 and §9.

---

## 1. Owner-ruling summary (scope, not method)

- **Rule A.** First-wave memory consumer = primary-persona only.
  Scope-of-work / orchestrator / objective-tracker / self-correction
  consumer wirings are deferred (research §10).
- **Rule B.** `group_id = workspace slug` at v1. Per-scope is a
  non-blocked v2 candidate; not implemented here.
- **Rule C.** Turn-close aggregation: ONE episode per user↔AI turn
  (not per state-event, not per session, not per message).
- **Rule D.** This amendment's contributor runs on `UserPromptSubmit`.
  D8's contributor runs on `SessionStart`. The composer registry is
  the shared surface; either amendment may introduce it.
- **Rule E.** Every AC is outcome-shaped per odd-methodology §2.4/§2.5.
  No method-in-AC, no non-objective-backed AC.

Research leans (context only; builder may refine): write-path async
via background-scope through the orchestrator's existing IPC;
read-path turn-start retrieval, query = user message +
last-3-turn context, `center_node_uuid` anchor from active scope when
available, top-5 semantic; retention default-normal with
persona-override.

---

## 2. Objective

The primary-persona layer participates in memory-system as a
first-class consumer. On every user-turn, the layer contributes a
memory-retrieval block to the `UserPromptSubmit` `additionalContext`
payload, keyed by the current workspace's `group_id`; on turn-close,
the layer causes one aggregated episode to be persisted for that
user↔AI turn without blocking the user. The memory-write path does
not block the interactive channel. The memory-retrieval block is
injected structurally, not by persona judgement. Both contributions
register against a shared `additionalContext` contributor registry
inside the primary-persona layer, co-owned with D8's session-level
contributor.

Five observable behaviours (mapped to ACs in §4):

1. A per-turn memory retrieval is issued, composed into the persona's
   `additionalContext` contribution, and reaches the model on
   `UserPromptSubmit`.
2. At user↔AI turn-close, exactly one aggregated episode is persisted
   for that turn.
3. The interactive turn is not blocked on the memory write.
4. Every episode written and every retrieval issued by this layer
   uses `group_id = workspace slug`.
5. The per-turn contribution is registered via a shared contributor
   registry that is compatible with D8's session-level contributor.

---

## 3. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — primary-persona layer primary.** In-scope source:
   `primary-persona/`. Test-fixture extensions permitted only in
   `orchestrator/tests/` and/or `memory-system/tests/` and only if an
   AC test genuinely requires cross-component fixture surface — no
   source edits admitted under those entries. Every other sealed
   component is off-limits (halt per §9).
3. **Shared-composer ownership resolution.** Before landing code, the
   builder checks whether D8 has already landed a contributor-registry
   primitive in `primary-persona/`. If yes: REGISTER a turn-level
   contributor against it. If no: INTRODUCE the registry (shaped to
   accept both turn- and session-level contributors, Pydantic-validated
   per ODD §5.3) and register the turn-level contributor. If
   ambiguous, halt per §9.
4. **Reversibility.** Fully reversible at the primary-persona surface.
   The retrieval contribution is additive to the existing D3
   awareness-block contribution; removing this amendment's contributor
   returns the layer to pre-amendment behaviour.
5. **No synchronous user-facing wait on memory writes.** The 113 s
   per-episode empirical cost makes sync writes a Lens-2 violation.
   The write path must be structurally non-blocking to the interactive
   channel.
6. **Retrieval payload envelope.** The per-turn memory-retrieval
   contribution shares `additionalContext` budget with the D3
   awareness block. Together they must not exceed the primary-persona
   layer's declared cap on the `UserPromptSubmit` payload. Apportioning
   is method; the AC (AC-D7.6) measures the observable cap.
7. **Dependency fence.** No new runtime deps. Permitted runtime deps
   per the primary-persona proposal apply unchanged. Test-only deps
   per STATE.md rule #8.
8. **Fail-closed direction.**
   - Memory service unreachable at retrieval time: retrieval
     contribution is empty; turn proceeds.
   - Memory write failure: turn has already returned to the user; the
     failed write surfaces as a failed scope in the awareness block on
     the next turn.
9. **CDC adherence.** Plan-before-code, background-agent default,
   scope-only dispatch, research-before-plan, the three
   amendment-dispatch speedups.
10. **Authority bound.** Builder may challenge research leans
    (aggregation granularity, async mechanism, query shape, top-N,
    retention default). Builder may not override Rules A–E without
    halt-and-signal.
11. **`pos-amend apply --dry-run` green is a hard prereq** per
    amendment #22.

---

## 4. Acceptance criteria

Each AC is outcome-shaped. The §5 table verifies behaviour coverage.
Identifiers are local (`AC-D7.n`); the build-dispatch plan may prefix
with the assigned amendment number at that time without altering
content.

### AC-D7.1 — turn-start retrieval lands in `UserPromptSubmit` additionalContext

Given the primary-persona layer loaded against a workspace whose
memory service is reachable and has at least one prior episode under
that workspace's `group_id`, a `UserPromptSubmit` event for a user
message causes the layer's `additionalContext` output to include a
memory-retrieval block whose contents are the result of issuing a
query against memory-system with the workspace's `group_id` in its
`group_ids` filter. Test-shape: seed memory with at least one episode
under the workspace `group_id`; fire the `UserPromptSubmit` entry
point for a crafted prompt; assert the emitted `additionalContext`
contains the retrieval block and that the retrieval call was issued
with the workspace slug in `group_ids`.

### AC-D7.2 — turn-close writes exactly one aggregated episode per user↔AI turn

Given a completed user↔AI turn (a user message and the persona's
reply have both landed), the primary-persona layer causes exactly one
memory-system episode to be persisted for that turn — not zero, not
two, not per-message, not per-state-event. Test-shape: drive a
single-turn fixture; assert `add_episode` received exactly one call;
assert its `group_id` equals the workspace slug; assert its body
captures both the user message and the persona reply in a single
payload. A multi-turn fixture produces one call per turn.

### AC-D7.3 — interactive turn is not blocked on the memory write

Given a fake memory boundary whose `add_episode` blocks for a
configurable duration (simulating the empirical 113 s), the user's
next turn may begin without waiting for the prior turn's memory
write to complete. Test-shape: complete one turn; start the next
turn; assert the second turn's `UserPromptSubmit` flow completes
while the first turn's write is still outstanding.

### AC-D7.4 — `group_id = workspace slug` for both read and write

Every memory-system retrieval issued by the primary-persona layer
and every memory-system episode written by the layer carries the
workspace slug in its `group_ids`/`group_id` argument. Test-shape:
drive a fixture whose workspace slug is a known value; exercise both
the AC-D7.1 and AC-D7.2 paths; assert every recorded call at the
memory-system boundary carries that slug in the appropriate argument.

### AC-D7.5 — shared contributor registry is the composition surface

The primary-persona layer exposes a single contributor registry for
`additionalContext` contributions that accepts (a) a turn-level
contributor (registered by this amendment for memory retrieval) and
(b) a session-level contributor (registered by D8). Contributors are
discovered and invoked by trigger kind, not by persona memory of their
existence. Test-shape: register a turn-level and a session-level
contributor through the registry; fire the turn-level entry point;
assert only the turn-level contributor's output appears in
`UserPromptSubmit` additionalContext. Fire the session-level entry
point; assert only the session-level contributor's output appears in
`SessionStart` additionalContext. The AC's truth does not depend on
which sibling amendment introduced the registry.

### AC-D7.6 — retrieval payload respects the persona layer's payload cap

The combined `UserPromptSubmit` `additionalContext` output of the
memory-retrieval contributor plus the existing D3 awareness-block
contributor does not exceed the primary-persona layer's declared cap.
Test-shape: construct a fixture where the awareness block alone
approaches the cap and a memory retrieval returns additional payload;
fire `UserPromptSubmit`; assert emitted `additionalContext` length ≤
cap. Which contributor is truncated and how is method.

### AC-D7.7 — memory unavailable at retrieval does not fail the turn

Given the memory service unreachable (connection refused, HTTP 5xx, or
a simulated timeout) at turn-start retrieval, the `UserPromptSubmit`
path still emits a valid `additionalContext` payload and the turn
proceeds. Test-shape: stub the memory boundary to raise on retrieval;
fire `UserPromptSubmit`; assert payload is emitted (possibly empty of
memory-retrieval content) and no exception reaches the hook-level
caller. The awareness-block path is unaffected.

### AC-D7.S — seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths under:

- `primary-persona/` (source + tests),
- `orchestrator/tests/` and/or `memory-system/tests/` if AC tests
  require cross-component fixtures (test-only, no source edits),
- `docs/plans/amendment-memory-consumer-wiring-primary-persona*`,
- `docs/plans/research/memory-consumer-wiring-research*`,
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Sealed-component source
outside `primary-persona/` is never admitted by this amendment.

---

## 5. Behaviour-count check

| Behaviour (§2) | Criterion/criteria |
|-|-|
| 1. Turn-start retrieval composed into `UserPromptSubmit` | AC-D7.1, AC-D7.6 (envelope), AC-D7.7 (fail-closed) |
| 2. Turn-close writes one aggregated episode per user↔AI turn | AC-D7.2 |
| 3. Interactive turn not blocked on memory write | AC-D7.3 |
| 4. `group_id = workspace slug` on every read and write | AC-D7.4 |
| 5. Shared contributor registry | AC-D7.5 |
| cross-cutting | AC-D7.S |

Five behaviours in §2; seven ACs cover them. No method-in-AC.

---

## 6. Implementation order (suggested; builder's call)

1. Resolve shared-composer ownership per §3 constraint 3. Halt if
   ambiguous.
2. Land (or register against) the contributor registry in
   `primary-persona/`.
3. Land the turn-level memory-retrieval contributor satisfying
   AC-D7.1, AC-D7.6, AC-D7.7.
4. Land the turn-close write-dispatch satisfying AC-D7.2 and AC-D7.3.
   Research lean: background-scope dispatched through the
   orchestrator's existing IPC. The builder may instead select
   research §3.3.2 (orchestrator-internal task) without re-ruling,
   PROVIDED no orchestrator-source amendment is required; otherwise
   halt per §9.
5. Verify `group_id = workspace slug` resolution on both paths
   (AC-D7.4).
6. Assemble and run the AC suite; verify seal-diff discipline
   (AC-D7.S).
7. `pos-amend apply --dry-run` green; amendment commit; seal commit.

---

## 7. Workspace-slug source

The workspace slug used as `group_id` is the slug the workspace
already carries for other identity purposes (per amendment #28's
workspace-identity convention and the workspace-bootstrap proposal).
The builder resolves the slug through whatever in-process primitive
the primary-persona layer already uses to identify its workspace —
no new workspace-identity surface is introduced by this amendment,
and no workspace-bootstrap / hands-off-lifecycle source is touched.
If the persona layer lacks a clean primitive for "what is this
workspace's slug at turn-start," that is a halt trigger (§9) — not a
licence to author the primitive inside this amendment.

---

## 8. Out of scope (explicit)

- Other candidate memory consumers (scope-of-work, orchestrator,
  objective-tracker, self-correction). Defer rationales in research
  §10.
- Per-scope `group_id` (Rule B restricts v1 to per-workspace).
- Session-close aggregation (research §3.3.3).
- Per-message aggregation (Rule C).
- D8's session-level contributor implementation (D8's amendment).
- Persona-authored memory query distillation (research §4.2 #3 —
  v2 concern).
- Retention-class decay/eviction policy (research §5.2 — no decay
  ships today; none introduced here).
- Memory-system source amendments — MCP surface from amendment #24
  consumed as-is.
- Orchestrator source amendments — existing IPC + scope-of-work
  runtime consumed as-is.
- Budget-attribution ruling (research §3.2). Method here: the
  builder uses the cheapest shape compatible with existing
  cost-governance without amending cost-governance source. If
  neither shape is reachable without a cost-governance amendment,
  halt per §9.
- De-duplication between D7's turn-retrieval and D8's session-corpus
  (research §6.5). v1 accepts overlap.
- New OTel spans beyond the persona layer's existing D9 surface.
- Workspace-supplied persona content (`prompt.md` / `contract.yaml`)
  is not touched — workspace personas remain workspace-owned.

---

## 9. Halt triggers

1. **Cross-component scope expansion beyond primary-persona + test
   fixtures in orchestrator/memory-system tests.** Any required source
   edit to any other sealed component — halt.
2. **Shared-composer ownership ambiguous between D7 and D8** — halt
   and signal for an owner ruling.
3. **Workspace slug lacks an in-process primitive the persona layer
   can reach** — halt (no new workspace-identity surface authored
   here).
4. **ODD break strongly required.** If an AC cannot be expressed
   outcome-shaped without prescribing method, or a behaviour cannot
   be implemented without a silent exception branch that no AC
   backs — halt. Re-extension per odd-methodology §4 requires a new
   AC with owner review, not burying.
5. **`pos-amend apply --dry-run` red** — halt.
6. **Memory-system boundary semantics disagree with research
   assumption** (e.g., `group_ids` not accepted at the signature the
   research assumed) — halt; do not mutate memory-system to fit.
7. **A test for AC-D7.1 – AC-D7.7 cannot be written deterministically**
   — halt.
8. **Budget attribution requires a cost-governance amendment** — halt
   per §8.

---

## 10. Bookkeeping surface

`pos-amend` manifest, authored at build-dispatch time once the
amendment number is assigned:

- **Primary component:** `primary-persona`. `seal_test`, `sidecar`,
  and `frozen_baseline` values resolved per the component's existing
  seal-bookkeeping convention. If the component does not yet carry a
  `tests/SEAL_COMMIT` sidecar or a seal-diff test fixture (as of plan
  authoring, standard-path sidecar is absent), the builder establishes
  the sidecar surface as part of this amendment's bookkeeping inside
  `primary-persona/` itself — this remains inside the §3 constraint-2
  fence.
- **Test-fixture components (admitted only if AC tests require):**
  `orchestrator` and/or `memory-system`, each with
  `extra_allowed_prefixes` widened to the specific test-fixture paths.
  No source admitted under those entries; manifest restricts to
  `tests/` paths.
- **Universal admissions** per amendment #22 ruling #3:
  - `universal_paths.prefixes`: `docs/plans/`
  - `universal_paths.files`: `CLAUDE.md`,
    `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
    `docs/FUTURE_IDEAS.md`, `docs/STATE.md`,
    `docs/VALUE_PROPOSITION.md`.
- **Narrative target:** a sidecar narrative under the primary-persona
  layer's seal-narrative surface (path resolved per convention; if
  not yet established, builder establishes it inside
  `primary-persona/`).
- **Plan reference:** manifest `plan:` field names this file.
- **Commits:** `fix(primary-persona): ...` or `feat(primary-persona):
  ...` at builder's judgement for the amendment commit;
  `chore(seals): ...` for the seal commit. No `--amend`.

---

## 11. Dispatch-time CDC adherence

Verified by the dispatcher before handoff:

- Plan-before-code: this plan exists at its declared path.
- Research-before-plan: D7 research landed 2026-04-24.
- Background-agent default: build-dispatch runs as background.
- Scope-only dispatch: the brief carries scope only — ACs by
  reference to this plan, not enumerated files/symbols/commit
  wording.
- Amendment-dispatch speedups (per Luke 2026-04-23): narrow
  pre-amendment test scope to `primary-persona/` + admitted
  test-fixture components; skip pre-seal full rerun when only
  sidecar edits occur between amendment and seal; inline
  odd-methodology snippets into the dispatch brief.
- Working directory explicit: `/Users/lukeivers/ivers-corp-pos-v2/`.
- No `--amend` in agent dispatches.

---

## 12. References

- D7 research plan:
  `docs/plans/research/memory-consumer-wiring-research-plan.md`
- D7 research doc:
  `docs/plans/research/memory-consumer-wiring-research.md`
- D8 research doc:
  `docs/plans/research/session-start-context-load-gate-research.md`
- Memory-system proposal:
  `docs/archive/component-research/memory-system/proposal.md`
- Memory-system MCP amendment:
  `docs/plans/amendment-24-memory-system-mcp-migration.md`
- Primary-persona layer proposal:
  `docs/archive/component-research/primary-persona-loader/proposal.md`
- Workspace-identity convention:
  `docs/plans/amendment-28-workspace-identity-routed-first-run.md`
- ODD methodology: `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`,
  `docs/FUTURE_IDEAS.md`
- Amendment-dispatch bookkeeping: `tools/pos-amend/`

# Plan — Amendment #37: hands-off-lifecycle Claude-Code default-agent wiring (`.claude/settings.json` + `.claude/agents/<handle>.md`)

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time (post-#36-seal).
**Amendment number:** `#37` placeholder; renumbered at dispatch per the convention amendments #29–#33 followed.
**Filename:** family-named (`hands-off-lifecycle-default-agent-wiring`) so the path survives renumbering.
**Companion research:** none authored separately. Master plan (`docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md`) carries the investigative narrative, including the structural-shape reference to ivers-corp's `.claude/settings.json` `"agent"` field placement and `.claude/agents/<handle>.md` frontmatter shape.

**Sibling amendments.** This is **amendment 3 of 3** in the persona-setup family.

- **#35:** `primary-persona` — `to_agent_md()` renderer + `onboarding.py` module + `is_starter` field. **Hard prerequisite** — this amendment calls the renderer.
- **#36:** `workspace-bootstrap` — first-run scaffold writes `<workspace>/personas/<handle>/`. **Hard prerequisite** — this amendment reads the scaffolded contract and projects it onto Claude Code's default-agent surface.
- **#37 (this plan):** `hands-off-lifecycle` — first-run hook merges `"agent": "<handle>"` into `<workspace>/.claude/settings.json` and writes `<workspace>/.claude/agents/<handle>.md` from the contract via amendment #35's renderer.

**Prerequisite verification (builder's hard halt before code).** Before any source edit, the builder confirms via `git log` that amendments #35 and #36 have both sealed. Specifically: `is_starter` exists on `PersonaContract`, `to_agent_md()` is importable from `primary-persona`, and the workspace-bootstrap scaffold materialises `<workspace>/personas/<handle>/` on first-run with `is_starter: true`. If either prerequisite is unmet, halt.

---

## 1. Summary / TLDR

The `hands-off-lifecycle` first-run hook gains two additive responsibilities, each at the existing first-run-time surface:

1. **Settings.json `"agent"` merge.** The existing `first_run_settings.py` merges only the `SessionStart` hook stanza into `<workspace>/.claude/settings.json`. This amendment generalises that merge to also-merge a top-level `"agent": "<handle>"` field, where `<handle>` is the resolved handle from amendment #36's scaffold (loaded from the workspace's persona directory at first-run time).
2. **Agent-file write at first-run.** The first-run hook writes `<workspace>/.claude/agents/<handle>.md` whose body is the output of amendment #35's `to_agent_md(contract)` against the loaded contract. Subsequent contract changes regenerate the file (the regeneration trigger is the persona-layer's existing reload surface; this amendment exposes the write path the regeneration calls).

The amendment composes additively with amendment #32's `SessionStart` context-load gate: the gate continues to inject runtime context as `additionalContext`; the agent file is the identity anchor Claude Code re-loads on context refresh. Two distinct roles, both Claude-native.

Graceful-degradation governs the agent-file write: if the write fails (permissions, disk full, malformed settings.json that can't merge), first-run completes with the persona scaffold in place, surfaces a structured diagnostic, and the SessionStart hook proceeds. The session degrades to generic-Claude-with-context-load-gate, not a hard halt.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.0 line 153 — Persona present in every interactive session, asserted by a session-start test** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §152–153): *"every interactive session (terminal or desktop) starts with the primary persona present by default — asserted by a session-start test."* This amendment is the structural mechanism that makes a fresh Claude Code session **land as** the workspace persona — the `.claude/settings.json` `"agent"` field + the `.claude/agents/<handle>.md` subagent file are exactly what Claude Code reads to bind a session's main-thread identity. Without this amendment, even a perfectly-scaffolded persona directory (per #36) is loadable but not session-bound.
- **v1.0 line 152 — Non-tech users — low-friction onboarding** (§152): the user does not configure `.claude/settings.json` or author `.claude/agents/<handle>.md`; the first-run hook does it.
- **v1.2 R16 — Framework-not-content** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §348–356): the agent-file body is rendered from the workspace's contract at write time; no persona prose is shipped from `hands-off-lifecycle/` source.
- **hands-off-lifecycle proposal §3.5 + §4.4** (`docs/rebuild/components/hands-off-lifecycle/proposal.md`): the first-run scaffold phase is the correct layer for new bootstrap-time additions (precedent set by Amendment #4). This amendment extends that surface without altering the phase model itself.
- **graceful-degradation** (component objective: failures degrade rather than halt): the agent-file write graceful-failure path satisfies the layer's degradation contract.

**Sealed-component amendment classification.** Single sealed component (`hands-off-lifecycle`). Amendment #35's renderer is consumed via import; amendment #36's scaffold output is read from disk. Neither involves source edits to those components.

**H19 frozen BASELINE.** Per amendment #23, hands-off-lifecycle's `H19` BASELINE is frozen at project-start. The `pos-amend` manifest sets `frozen_baseline: true` for this component (per amendment #29 + #34 precedent).

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This amendment is the load-bearing Claude-leverage in the persona-setup family. Three Claude Code primitives compose:

1. **The subagent registration surface (`.claude/agents/<handle>.md`).** Claude Code reads `.claude/agents/*.md` as subagent definitions; the frontmatter (`name`/`description`/`model`/optional `tools`) names the subagent and the body is the system prompt. This amendment writes that file from the workspace's contract via amendment #35's renderer — a deterministic projection. We do not invent persona structure; we project the existing `PersonaContract` onto Claude Code's surface.
2. **The `"agent": "<handle>"` field in `.claude/settings.json`.** This selects the default subagent for the session's main thread. The existing settings-merge surface (`first_run_settings.py`) already merges the `SessionStart` hook stanza; this amendment generalises that merge to also-merge the `"agent"` field.
3. **The `SessionStart` hook (already wired) + the D8 context-load gate.** Existing surface (amendment #32) carries the runtime additionalContext; the agent file is the identity anchor Claude Code re-loads on context refresh. The two compose: Claude Code provides identity persistence through the agent-file body; the gate provides runtime state. **No new Claude primitive is invented; existing ones are composed.**

This is the Lens-1 question's textbook positive answer: an existing Claude-native primitive provides the persona-presence machinery; this amendment composes onto it. ivers-corp's pattern (referenced for structural shape only — no content lifted) confirms the approach is the documented Claude-Code default-agent surface.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — this amendment is the closing piece. After #35 + #36, the loader passes and the elicitation flow is wired but the session's main thread is still generic Claude (because `.claude/settings.json` does not yet name the subagent). After this amendment lands, the fresh-clone first-run produces a session that **is** the workspace persona — the user's first message goes to the persona, not to generic Claude. Translation burden absorbed.

**AC-trace to AC.PO.1:**

- **AC37.1 → AC.PO.1.** First-run merges `"agent": "<handle>"` into `.claude/settings.json` (preserving prior keys per the existing settings-merge logic) → fresh Claude Code session selects the workspace persona as its default subagent → user's first message goes to the persona → translation burden absorbed.
- **AC37.2 → AC.PO.1.** First-run writes `.claude/agents/<handle>.md` from amendment #35's renderer → Claude Code re-loads the agent body on context refresh → persona identity persists across compaction → user does not have to re-explain who the persona is → translation burden absorbed across long-running sessions.
- **AC37.3 → AC.PO.1.** Re-running first-run on a workspace whose `personas/<handle>/contract.yaml` has `is_starter: false` does not regenerate the agent file (no-op) → user-edited contract content reaches the agent file via the persona-layer reload path, not via the first-run path → user's edits are durable across re-runs → translation burden absorbed.
- **AC37.4 → AC.PO.1.** Agent-file write failure degrades gracefully → session still proceeds (as generic-Claude with context-load-gate's additionalContext) → user does not see a hard halt because of an environmental issue → translation burden absorbed at the failure boundary too.
- **AC37.5 → AC.PO.1.** SessionStart additionalContext from the persona layer names the loaded persona (handle + given_name) → the gate's payload composes correctly with the agent-file identity anchor → no two-source-of-truth confusion → translation burden absorbed (no debugging "why does it call itself X but the docs say Y?").

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The settings.json deterministic-merge surface, generalised.** `first_run_settings.py` previously merged only the `SessionStart` hook; this amendment lifts that to a general-purpose merge that future first-run-time settings contributions can add to.
2. **The agent-file write surface, callable from the persona-layer reload path.** Future contract changes (whether by user edit or by amendment #35's onboarding-elicitation write-back) regenerate the agent file via a known surface.
3. **The graceful-degradation pattern around agent-file write.** Establishes the precedent for "Claude-Code-native surface optional; degrade if unavailable" — useful for future amendments wiring other Claude Code primitives whose absence should not halt the session.

**AC-trace to AC.PO.2:**

- **AC37.1 → AC.PO.2.** Generalised settings.json merge surface — toolkit primitive.
- **AC37.2 → AC.PO.2.** Agent-file write from the renderer — toolkit primitive any future persona-managing tool can invoke.
- **AC37.4 → AC.PO.2.** Graceful-degradation pattern at the Claude-Code-surface boundary — toolkit primitive.

### Lens 3 — ODD authoring

The plan authors six outcome-shaped acceptance criteria (§4) under §2.5 reverse-direction discipline. Each AC names what must be true; method (settings-merge implementation, agent-file write atomicity, diagnostic surface routing) is the builder's call.

ODD §2.5 reverse-direction check: every new code path in `hands-off-lifecycle/hooks/` traces back to AC37.1–AC37.6. The graceful-degradation branch at AC37.4 is explicitly criterion-backed (not an unbacked defensive `if`).

---

## 4. Acceptance criteria (AC37.x)

Each AC maps to at least one test function named `test_AC37_<n>_<slug>` in `hands-off-lifecycle/tests/`.

### AC37.1 — Fresh-clone first-run merges `"agent": "<handle>"` into `.claude/settings.json`

After first-run completes on a clone where the workspace-bootstrap scaffold (amendment #36) has materialised `<workspace>/personas/<handle>/contract.yaml`:

- `<workspace>/.claude/settings.json` contains `"agent": "<handle>"` at the top level,
- pre-existing keys in `settings.json` (specifically the `SessionStart` hook from amendment #32 + any user-set keys) are preserved unchanged,
- the `<handle>` value matches the handle resolved from the loaded contract.

If `<workspace>/.claude/settings.json` does not exist, the first-run hook creates it with the `"agent"` field plus the `SessionStart` hook stanza (the existing merge logic's create-on-absent path already handles this; this amendment extends it with the `"agent"` key).

**Test shape:** scaffold a fresh tmpfs workspace through the existing first-run-test harness (which runs amendment #36's scaffold first per dependency order); read `<workspace>/.claude/settings.json`; assert `"agent" == "<expected-handle>"` at top level; assert SessionStart hook stanza preserved.

**Maps to:** v1.0 line 153 (persona present every session — Claude Code default-agent binding) → AC.PO.1.

### AC37.2 — Fresh-clone first-run writes `.claude/agents/<handle>.md` from the renderer

After first-run completes:

- `<workspace>/.claude/agents/<handle>.md` exists,
- its content equals `to_agent_md(loaded_contract)` (the output of amendment #35's renderer against the loaded contract),
- frontmatter `name == handle`, `description` derived from `responsibilities.single_point_of_contact` (the renderer's contract — this AC is about the file's content matching the renderer's output, not about the renderer's projection itself, which is amendment #35 AC35.2's scope).

**Test shape:** scaffold + first-run; load the contract via `PersonaLoader`; call `to_agent_md(contract)` directly; read the on-disk `.claude/agents/<handle>.md`; assert string equality.

**Maps to:** v1.0 line 153 + amendment #35 AC35.2 (renderer contract) → AC.PO.1 + AC.PO.2.

### AC37.3 — Re-running first-run on a workspace with a non-starter persona is a no-op

If `<workspace>/personas/<handle>/contract.yaml` has `is_starter: false` (the user has either completed elicitation or hand-edited the contract), running first-run a second time:

- does NOT overwrite `<workspace>/.claude/agents/<handle>.md` (it may rewrite with identical content; the AC's outcome is "no observable change"),
- does NOT modify the `"agent"` field in `<workspace>/.claude/settings.json` (preserves whatever value is currently set),
- does NOT change the agent-file's mtime if its content equals `to_agent_md(loaded_contract)` (write-only-if-different policy, builder's call on exact mechanism — the AC bounds the user-observable outcome: a stable system stays stable).

This holds when the user has edited `<handle>` itself (e.g., changed the contract's handle field after elicitation): the scaffold's no-overwrite rule (AC36.3) means the handle is durable; this amendment's no-op rule means the agent-file path is not re-derived from a stale cached handle.

**Test shape:** scaffold + first-run; capture mtime + content hash of `.claude/agents/<handle>.md`; flip `is_starter` to `false`; first-run again; assert mtime + content hash unchanged. Repeat with a user-edited `description`-source-field on the contract; assert the second first-run does NOT overwrite (the regeneration path lives elsewhere — the persona-layer's reload path — not in first-run).

**Maps to:** v1.0 line 152 (low-friction; user edits durable) + v1.2 R16 (workspace-supplied content remains workspace-owned) → AC.PO.1.

### AC37.4 — Graceful failure on agent-file write

If `<workspace>/.claude/agents/<handle>.md` cannot be written (simulated via permissions, disk-full, or pre-existing malformed `<workspace>/.claude/settings.json` that cannot merge):

- first-run completes (does not halt),
- the persona scaffold from amendment #36 remains in place,
- a structured diagnostic surfaces via the existing observability surface naming the failure class,
- the SessionStart hook proceeds (i.e., the gate from amendment #32 still fires; the loader still loads the persona; the session degrades to generic-Claude-with-context-load-gate rather than failing closed).

**Test shape:** seed a tmpfs workspace; mark `<workspace>/.claude/` non-writable (or pre-write a malformed `settings.json` that cannot merge); run first-run; assert no exception propagates; assert structured diagnostic emitted (capture via the existing observability test fixture); assert `personas/<handle>/` was still created by the upstream scaffold; trigger the SessionStart hook (per the test harness's existing pattern); assert it completes.

**Maps to:** graceful-degradation component objective + v1.0 line 153 (degraded persona-presence is preferable to halt) → AC.PO.1.

### AC37.5 — SessionStart additionalContext names the loaded persona

After first-run + a SessionStart hook invocation against the same workspace (the integration shape amendment #32's gate establishes), the `additionalContext` payload composed by the gate names the loaded persona by `handle` and `given_name`. The agent-file's identity-anchor block is present in `<workspace>/.claude/agents/<handle>.md` (read from disk, not re-rendered for this assertion).

**Test shape:** scaffold + first-run; fire the SessionStart entry point (test harness pattern from amendment #32); inspect emitted `additionalContext`; assert it contains the persona's handle + given_name. Read `.claude/agents/<handle>.md`; assert the identity-anchor marker is present in the body (per AC35.2's renderer contract, which this AC verifies on-disk rather than in-memory).

**Maps to:** v1.0 line 153 (session-start test) + amendment #32 gate contract → AC.PO.1.

### AC37.6 — No persona content shipped from `hands-off-lifecycle/`

Source under `hands-off-lifecycle/src/` and `hands-off-lifecycle/hooks/` does not contain persona prose. The agent-file body is composed at write time by calling amendment #35's `to_agent_md(contract)`; the contract is read from `<workspace>/personas/<handle>/contract.yaml`. The framework-tree scan (`enforce_no_personas_in_core`) continues to pass.

**Test shape:** the existing framework-tree-scan test passes unchanged. Additional check: a test-fixture contract whose prose fields are unique sentinel strings produces an agent-file containing those sentinels — proving the prose came from the contract, not from a constant in `hands-off-lifecycle/` source.

**Maps to:** v1.2 R16 framework-not-content → AC.PO.2 (toolkit purity).

### AC37.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `hands-off-lifecycle/` (source + hooks + tests),
- `docs/rebuild/plans/amendment-37-hands-off-lifecycle-default-agent-wiring*` (this plan + manifest),
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Specifically: no edits to `primary-persona/` source (the renderer is imported), no edits to `workspace-bootstrap/` source (the scaffold output is read from disk).

H19's frozen BASELINE per amendment #23 holds.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. First-run merges `"agent": "<handle>"` into settings.json | AC37.1 |
| 2. First-run writes `.claude/agents/<handle>.md` from the renderer | AC37.2, AC37.6 (provenance) |
| 3. Re-run is a no-op when persona is non-starter | AC37.3 |
| 4. Graceful failure on agent-file write | AC37.4 |
| 5. SessionStart additionalContext names the loaded persona | AC37.5 |
| cross-cutting | AC37.S (seal-diff) |

Five declared behaviours; six ACs cover them plus the cross-cutting seal-diff invariant. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `hands-off-lifecycle/` only.** Source under `hands-off-lifecycle/src/` and `hands-off-lifecycle/hooks/`. Tests under `hands-off-lifecycle/tests/`. Read-only consumption of the scaffolded persona directory + import of amendment #35's renderer permitted (existing surfaces). Any source edit outside `hands-off-lifecycle/` is a halt (§9).
3. **No edit to amendment #35's renderer or amendment #36's scaffold.** They are consumed; if they need a change, halt and signal — the change belongs in their respective amendments.
4. **Reversibility.** Removing this amendment's first-run-hook extension returns the layer to its pre-amendment state. Already-written `.claude/settings.json` `"agent"` fields and `.claude/agents/<handle>.md` files on existing workspaces are durable artefacts — removing the amendment does not require deleting them, just stops re-writing them on subsequent first-runs.
5. **No new runtime deps.** Permitted runtime deps per hands-off-lifecycle proposal apply unchanged.
6. **No persona content in `hands-off-lifecycle/`.** Agent-file body comes from the renderer; the renderer composes from the contract; the contract comes from the workspace.
7. **Fail-closed direction is graceful, not hard-halt.** AC37.4 establishes the contract: failure surfaces a structured diagnostic and proceeds. Hard-halt on agent-file write failure is forbidden — it would defeat the v1.0 line 153 contract by making a transient environmental issue (temp permissions glitch) take down session-start.
8. **Settings.json merge preserves prior content.** The merge surface is additive over a pre-existing `settings.json`; existing keys remain. Test exercises the pre-existing `SessionStart` hook stanza specifically (most common prior-content case).
9. **Authority bound.** Builder may refine settings-merge implementation, agent-file write atomicity (atomic-rename vs direct-write), diagnostic surface routing, write-only-if-different policy. Builder may not relax the framework-not-content invariant (AC37.6) or the graceful-degradation contract (AC37.4).
10. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
11. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.
12. **Amendments #35 and #36 must be sealed before this amendment begins** — verified at builder's pre-edit gate.

---

## 7. Out of scope (explicit)

- **Renderer + onboarding work** — amendment #35.
- **Workspace-bootstrap scaffold work** — amendment #36.
- **Per-session subagent invocation** (`/agents` command flow) — out of scope; default-agent at the top-level `"agent"` field is the chosen surface (master plan D1 (a)).
- **Composing the persona prompt into project-level `CLAUDE.md`** — explicitly rejected at master plan D1 (c). `CLAUDE.md` is for codebase instructions, not persona identity.
- **Claude Code skill alternative** — out of scope; D1 (d) rejected.
- **Drift-detector for hand-edited agent files** — defer (master plan R4).
- **Agent-file regeneration on contract change** at the persona-layer reload surface — the **write surface** lands here (callable from anywhere); the **trigger** lives in the persona layer's existing reload path, which is amendment #35's territory (covered by AC35.5 — renderer regenerates given a changed contract). This amendment's AC37.2 verifies the first-run-time write; the persona-layer-driven re-write path is verified at amendment #35 AC35.5.
- **`tools:` frontmatter on the agent file** (per master plan §6.2 constraint 5) — omitted by default (Claude Code's default = inherit all). If a workspace's contract carries an explicit tool-restriction in some future field, the renderer (amendment #35) projects it into frontmatter; out of scope here.
- **Multi-persona-in-one-workspace settings.json wiring** (e.g., a `subagents:` array) — orthogonal; primary persona only here.
- **Prior pos-v2 first-run state file routing changes** — amendment #28 closed those hazards.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read master plan + amendment #35 plan + amendment #36 plan + their seal narratives + this plan.
3. Verify amendments #35 and #36 have sealed (per §6 constraint 12).
4. Write builder-plan to `docs/rebuild/plans/amendment-37-hands-off-lifecycle-default-agent-wiring.builder-plan.md` naming specific files + symbols expected to be touched.
5. Generalise the existing settings.json merge in `first_run_settings.py` to also-merge the `"agent"` field. Verify AC37.1.
6. Land the agent-file write inside the first-run hook. Use amendment #35's `to_agent_md()` + amendment #36's scaffolded contract. Verify AC37.2 + AC37.6.
7. Land the no-overwrite policy for the re-run case. Verify AC37.3.
8. Land the graceful-degradation path for write failures. Verify AC37.4.
9. Verify AC37.5 — SessionStart additionalContext names the loaded persona — using amendment #32's gate test harness.
10. Run AC37.1–AC37.6 + the existing hands-off-lifecycle seal-diff suite + the existing first-run integration test.
11. `pos-amend apply --dry-run` green gate (with `frozen_baseline: true` for hands-off-lifecycle per amendment #23).
12. Amendment commit.
13. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
14. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `hands-off-lifecycle/`.** Any required source edit to `primary-persona/` or `workspace-bootstrap/` (or any other sealed component) → halt.
2. **Amendments #35 or #36 have not sealed before this build begins.** Halt.
3. **`to_agent_md()`'s output shape conflicts with what Claude Code currently accepts** (per https://docs.claude.com/en/docs/claude-code/sub-agents). Halt; the renderer's projection contract change is amendment #35's territory.
4. **The settings.json merge cannot accept a top-level `"agent"` key without a structural change to the merge surface that affects amendment #32's `SessionStart` stanza.** Halt; coordinate scope.
5. **Graceful-degradation cannot be implemented without a graceful-degradation component source change.** Halt — that's multi-component scope expansion.
6. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception that no AC backs). Halt; owner rules.
7. **`pos-amend apply --dry-run` red** — halt.
8. **A test for AC37.1–AC37.6 cannot be written deterministically** — halt.
9. **The Claude Code default-agent surface (settings.json `"agent"` field, agents/ directory, frontmatter shape) has changed in a way that breaks the amendment's projection contract.** Halt — that's the master plan R3 risk, and the renderer change at amendment #35 is the upstream remediation.
10. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: 37
  slug: hands-off-lifecycle-default-agent-wiring
  title: "hands-off-lifecycle Claude-Code default-agent wiring"

# BASELINE: <pre-amendment tip captured at brief-dispatch — should
# be the seal commit of #36>. Note: hands-off-lifecycle's H19
# BASELINE is frozen per amendment #23; the manifest sets
# frozen_baseline: true on the component.
baseline: <captured-at-dispatch-post-#36-seal>
plan: docs/rebuild/plans/amendment-37-hands-off-lifecycle-default-agent-wiring.md

components:
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true   # H19 pinned at project-start per #23
    extra_allowed_prefixes: []

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.default-agent-wiring
  body: |
    # Amendment #37 — hands-off-lifecycle Claude-Code default-agent
    #                  wiring (`.claude/settings.json` "agent" field
    #                  + `.claude/agents/<handle>.md`)
    ...
    # Body authored at seal time; describes:
    #  - settings.json merge generalised to also-merge "agent":
    #    "<handle>" (preserves SessionStart hook stanza per
    #    amendment #32 contract)
    #  - agent-file written via amendment #35's to_agent_md(loaded_
    #    contract); content composed from workspace contract
    #  - no-overwrite policy on re-run when contract is non-starter
    #  - graceful-degradation on write failure: structured
    #    diagnostic + first-run completes + SessionStart proceeds
    #    with generic-Claude + context-load-gate's additionalContext
    #  - framework-not-content invariant preserved
    #  - closes the v1.0 line 153 acceptance ("every interactive
    #    session starts with the primary persona present by default
    #    — asserted by a session-start test") on a fresh clone
    #  - composes additively with amendment #32 (SessionStart gate
    #    runtime context) — agent-file is identity anchor; gate is
    #    runtime context; both Claude-native
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-plan recommendations are cited but not pinned.

- **D-build.1 — Settings.json merge generalisation shape.** Two reasonable shapes: (a) extend the existing `first_run_settings.py` merge with another stanza-handler for top-level keys; (b) refactor `first_run_settings.py` into a small generic merger that accepts a list of contributions. **Master-plan recommendation:** (a) — minimal blast radius. **Builder's call within scope.** AC37.1 measures the outcome (the field is merged, prior keys preserved); AC37.S enforces no-cross-component-spillover.
- **D-build.2 — Agent-file write atomicity.** Atomic-write-and-rename vs direct-write. **Master-plan recommendation:** atomic-rename is safer (interrupted writes don't leave partial agent files that Claude Code might attempt to parse), but direct-write is simpler. **Builder's call within scope.** The graceful-degradation contract (AC37.4) bounds the failure-mode behaviour either way.
- **D-build.3 — Diagnostic surface routing for write failures.** The hands-off-lifecycle layer has an existing observability surface (per H21 / D9 conventions). The builder picks the structured-diagnostic event name + attribute set. **Master-plan recommendation:** match the existing diagnostic naming convention (e.g., `pos.firstrun.agent_file_write_failed` or similar — consistent with the `pos.<component>.<event>` pattern). **Builder's call within scope.**
- **D-build.4 — Write-only-if-different policy.** AC37.3 bounds the user-observable outcome but not the on-disk write mechanism. The builder picks (a) compare existing-file content to `to_agent_md(contract)` output, write only if different (avoids mtime churn) or (b) rewrite unconditionally on every first-run-completion (simpler; mtime churn is acceptable since agent-file is a regenerable derived artefact). **Master-plan recommendation:** (a) — preserves user-visible mtime stability + plays nicer with file-watch tooling. **Builder's call within scope.**

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the master research+plan artefact:

- **Master plan:** `docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md` — covers the full investigation, all six master-plan decisions (D1–D6), the three-lens analysis applied to the combined scope, the ten master-plan ACs, and the multi-component-amendment classification per §10.

The owner ruled (post-master-plan) that the work ships as **three coordinated sealed-component amendments**. This file is **amendment 3 of 3**. Amendment 1 (`amendment-35-primary-persona-renderer-and-onboarding.md`) and amendment 2 (`amendment-36-workspace-bootstrap-persona-scaffold.md`) are **hard prerequisites**.

Master-plan AC ↔ this-plan AC mapping (for traceability):

| Master AC | This-plan AC | Note |
|---|---|---|
| AC2 (fresh-clone first-run wires Claude Code default-agent) | AC37.1 + AC37.2 | This is the headline behaviour of #37. |
| AC3 (fresh-clone Session 1 lands as the persona — agent-file body side) | AC37.5 (additionalContext) + AC37.2 (identity-anchor block in agent file) | Master AC3 is split: the additionalContext side ships at amendment #35 AC35.3 (contributor); the on-disk-agent-file identity-anchor side ships here. |
| AC6 (re-running first-run on a workspace with a non-starter persona is a no-op — settings/agent-file side) | AC37.3 | The scaffold side of master AC6 ships at #36 AC36.3. |
| AC8 (graceful failure on agent-file write) | AC37.4 | The headline graceful-degradation behaviour. |
| AC9 (pOS core ships zero persona content) | AC37.6 | Verified at the agent-file write boundary. |

Master ACs 1, 4, 5, 7, 10 land in amendments #35 + #36.

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify amendments #35 and #36 have sealed (`primary-persona/tests/SEAL_COMMIT` advanced past #35's seal SHA + `to_agent_md()` importable + `is_starter` field on `PersonaContract`; `workspace-bootstrap/tests/SEAL_COMMIT` advanced past #36's seal SHA + scaffold materialises `personas/<handle>/` on first-run). Halt if either is unmet.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `hands-off-lifecycle/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.
- H19 frozen BASELINE per amendment #23 — manifest sets `frozen_baseline: true` for hands-off-lifecycle.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.4 to the builder. This
section records the choices made and the rationale.

### D-build.1 — Settings.json merge generalisation shape: parameterise `merge_session_start`

`merge_session_start(...)` gains an optional keyword argument
`agent_handle: str | None = None`. When non-None the merger sets
`existing["agent"] = agent_handle` after the SessionStart-stanza
merge; when None (the default — backwards-compatible with every
pre-amendment-#37 call site) the field is left untouched.

**Rationale:** plan §11 D-build.1 candidate (a) — minimal blast
radius. The existing settings-merge surface is well-tested (T11–T18,
detachment + workspace-identity-routing tests); a generic merger
refactor (candidate b) would have widened the seal-diff surface
without buying a measurable AC outcome. The parameter is additive;
no callers need to migrate. AC37.1 measures the outcome (`"agent"`
field present, prior keys preserved, `agent_handle=None` is a no-op)
without method-in-acceptance.

### D-build.2 — Agent-file write atomicity: `.tmp` sibling + `os.replace`

`agent_file_authoring.write_agent_file()` writes the encoded body
to `<target>.tmp`, then `os.replace(tmp, target)`. On success the
target file is either fully the new bytes or fully the old bytes
— never a partial concatenation. On any OSError during the write
or rename, the `.tmp` sibling is best-effort-unlinked and the
original target is left intact (verified by AC37.4).

**Rationale:** plan §11 D-build.2 recommendation. Mirrors the
existing settings-merge atomic-write pattern in
`first_run_settings.py`. Direct-write would be simpler but loses
the crash-safety contract; the atomic rename costs one extra
file-creation per first-run.

### D-build.3 — Diagnostic surface routing: `_advance_state` with `phase-4c-agent-file-authorship`

Every Phase 4c failure branch (subprocess timeout, JSON parse
error, runner non-zero exit, write-permission denied, JSON
envelope missing fields, settings-merge OSError) calls
`_advance_state("running", phase="phase-4c-agent-file-authorship",
detail=<failure-class>:<error>)`. State stays `running` (the
failure is non-fatal); the next phase proceeds. The detail string
follows a `<failure-class>:<exception-info>` shape so log readers
can route on the prefix.

**Rationale:** plan §11 D-build.3 recommendation. Matches the
existing observability surface (`_advance_state` is the helper's
canonical state-update channel). No new event taxonomy invented;
the existing pattern carries the new phase name.

### D-build.4 — Write-only-if-different: byte-compare existing target before write

`write_agent_file()` reads the existing file's bytes (best-effort;
read failure falls through to write) and compares to the encoded
body. On equality the call returns `reason="skipped-identical"`
without touching the file (mtime preserved). On inequality (or
absence) the atomic-rename write proceeds.

**Rationale:** plan §11 D-build.4 recommendation. Single
`read_bytes()` per first-run is trivially cheap on a file
expected to be a few kilobytes. Preserves mtime stability across
re-runs (AC37.3 measures this) and avoids file-watch tooling
churn for editors / IDEs that watch `.claude/agents/`.

### Test breakdown

- Hands-off-lifecycle: **104 passed** (75 baseline + 29 new
  AC37.x tests). Test files added:
  `tests/test_AC37_1_settings_agent_merge.py` (7 tests),
  `tests/test_AC37_2_agent_file_written.py` (4),
  `tests/test_AC37_3_rerun_no_op.py` (5),
  `tests/test_AC37_4_graceful_failure.py` (5),
  `tests/test_AC37_5_session_start_names_persona.py` (4),
  `tests/test_AC37_6_no_persona_content_in_source.py` (4).
- Existing T1–T18 + AC29 + detachment + workspace-identity-routing +
  pyyaml-reachability suites: no regressions.
- Cross-component seal-diff (per amendment-dispatch-speedups):
  every other sealed component's `test_no_sealed_amendments.py`
  green (self-correction, memory-system, graceful-degradation,
  cost-governance, workspace-bootstrap, reversibility-primitive,
  safety-layer, orchestrator, observability-aggregator,
  telegram-interface, primary-persona).
- `pos-amend apply --dry-run`: green pre-amendment-commit and
  post-seal-commit (frozen_baseline=true suppresses the BASELINE
  literal bump per amendment #23 convention).
- H19 cross-cutting test: green at frozen BASELINE 3780603 with
  `primary-persona` admitted in this amendment's window (the
  admission was deferred from amendment #35 to #37 per the
  per-invariant-BASELINE convention — H19 trips when the
  SEAL_COMMIT window first surfaces a new top-level surface, and
  hands-off-lifecycle's SEAL_COMMIT advances to amendment #37's
  commit at this seal moment).

### H19 admission record

This amendment widens the H19 frozen-BASELINE allowed-set in
`hands-off-lifecycle/tests/test_cross_cutting.py` to admit
`primary-persona` (introduced into the SEAL_COMMIT window by
amendment #35; surfaced now because hands-off-lifecycle's
SEAL_COMMIT advances past that window for the first time at this
amendment). Rationale documented inline in the test source.

### Commit SHAs

- Amendment commit: `d9ec507858ce51e76c7c467183177edb99aeb524` —
  `feat(hands-off-lifecycle): Claude-Code default-agent wiring — amendment #37`
- Seal commit: `c97472ecdba9689ec4a2086ba4077ec1aa967bac` —
  `chore(seals): default-agent-wiring seal — hands-off-lifecycle at d9ec507`

### Dependents cleared to dispatch

The first-run primary-persona-default-agent-wiring family is now
complete (#35 + #36 + #37 sealed). The Heavy-B chain inherits a
satisfied persona-setup precondition:

- **#38** (objective-tracker schema widening) — no remaining
  persona-setup dependency.
- **#39** (workspace-bootstrap tracker seed) — no remaining
  persona-setup dependency.
- **#40** (primary-persona tracker context contributor) — depends
  on #38 + #39, not on persona-setup; persona-setup precondition
  satisfied.
- Dev-discipline plans — no remaining persona-setup dependency.

All four Heavy-B dependents are cleared to dispatch from a
persona-setup perspective.

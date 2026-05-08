# Research plan — session-start structural context-load gate (D8)

**Status:** research-plan for the D8 research cycle. Authored 2026-04-24. Promotes `FUTURE_IDEAS.md` Idea 8 from future-idea to active research. Sibling cycle to D7 (memory-consumer-wiring) — natural composition at the session-start injection surface.

**Session-start corpus:** research agent reads all five mandatory paths in `CLAUDE.md`'s session-start-discipline section. Additional reads: `FUTURE_IDEAS.md` Idea 8 verbatim; `POST_FIRST_RUN_REVIEW.md` entry #5; `orchestrator/scripts/pos_session_start.py` (the current supervisor stanza's additionalContext emission surface).

---

## 1. Context

The 2026-04-23 pos3 session surfaced two failure modes the current session-start path doesn't prevent:

1. **Advisory session-start discipline.** `CLAUDE.md` names a required-reads list for any non-trivial pos-v2 turn. The rule is prose; nothing structural prevents a session from proceeding without the corpus loaded. I skipped the read on this session's opening turn.
2. **Minimal steady-state visibility.** The supervisor's `pos_session_start.py::main` emits a single-line `additionalContext` — `"pos v2 ready"` on healthy steady-state, one-line diagnostic otherwise. No visibility into recent first-run state, service warnings, background-task count, cost-governance state, or in-flight amendments. Users see "ready" or a terse diagnostic; primary personas land in a session with effectively zero pos-v2 context beyond what they already knew.

`FUTURE_IDEAS.md` Idea 8 names the structural fix: a hook that loads the required corpus + injects it as `additionalContext` synchronously, refusing to complete if any mandatory path is missing. The idea's text enumerates open questions already; this research cycle closes them and produces a proposal.

The Lens-1 composition (what Claude capability does this lean on?) is explicit: Claude Code's `SessionStart` and `UserPromptSubmit` hooks support `additionalContext` injection. The `SessionStart` hook is already the harness's structural injection point (first-run dispatch + post-first-run supervisor both use it). This is an extension of existing Lens-1 composition, not a new one.

## 2. Questions for the research agent

### 2.1 Idea 8 open questions (from the idea's verbatim text)

**Owner ruling (2026-04-24): the gate lives in the primary-persona layer, for now.** Research does NOT re-open the persona-vs-harness layer question; it operates inside the persona-layer scope. BUT: if the research surfaces evidence the ruling should be revisited (e.g., a requirement that can't be satisfied cleanly inside the persona layer, a Claude-Code primitive that only binds at the harness layer), flag it — don't silently re-rule.

Remaining open questions:
- Which contexts trigger the gate — build-dispatches only, or every pos-v2 work turn including questions and reviews?
- How does "relevant design docs" get computed without the user enumerating them? Static mapping (component → doc set)? Dynamic lookup against the component's proposal/seal sidecar? Compose with the Claude-capabilities map (Idea 1 Step 1)? Something else?
- How does the gate compose with Claude's existing SessionStart hooks (the supervisor stanza already owns the slot) and with the skills ecosystem? Is this a skill, a hook, or a persona primitive (three variants within the persona-layer scope)?
- Workspace-wide (one gate across all pos-v2 work) vs component-scoped (each component declares its context set; the gate consults the declaration)?

### 2.2 Concrete payload enrichment (from the 2026-04-23 session)

- What should the supervisor's `additionalContext` actually emit beyond `"pos v2 ready"`? Candidate fields, each ruled in/out with reasoning:
  - Recent first-run completion time + generation number
  - Warnings from the most-recent first-run cycle (surface the "phase-4b returned 200 but service was crashlooping" pattern if it recurs)
  - Per-service state (memory-sidecar up + bound-to-port? orchestrator socket reachable? any crashloop recorded in launchd's LastExitStatus?)
  - Background-task count (scope-of-work active scopes, orchestrator-managed tasks)
  - Cost-governance month-to-date spend + ceiling headroom
  - In-flight amendment list (any `docs/plans/amendment-*.md` with a status that implies "in progress" at this moment)
  - Session-start-corpus load status (structural — the corpus itself is injected, not just summarised; this is the core of Idea 8)

### 2.3 Composition with D7

**Owner ruling (2026-04-24):** D7 and D8 share a common `additionalContext`-emitter layer. Research does NOT re-litigate merge-vs-adjacent; that's ruled.

Research focuses on the SHAPE of the shared layer:
- How does the layer dispatch between session-start and turn-start (`UserPromptSubmit`) triggers? Shared entry point with a trigger-kind parameter? Two entry points funnelling to a shared payload-composer? Something else?
- What's the ordering model — session-level context loaded once per session, turn-level retrieval interleaved per prompt, or both as a merged stream with an explicit composition rule?
- What's the contract between D7's write (turn-level memory-retrieval) and D8's write (session-level corpus + service state)? Specifically: can D8's heavy payload one-time warm a buffer that D7's turns augment, reducing per-turn cost?
- Convergence implication: if the shared-layer shape argues for one unified research-and-build cycle rather than two parallel ones, flag it (halt trigger #4) and owner rules on merge.

### 2.4 Refusal semantics

- What happens when the gate CANNOT complete (required path missing, service unreachable, cost-governance tripwire)? Candidate refusal shapes: hard-fail the hook (user sees no session until fixed); inject a diagnostic additionalContext and proceed (user sees a warning but Claude runs); pre-emptive Claude-Code-side error that the user's session shell doesn't start at all. The ODD-preferred shape is structural refusal — the question is which shape that is here.

### 2.5 Cold-start cost

- The hook adds latency to every session start (for D8) and every user prompt submit (if D7 attaches). What's the empirical cold-start cost of a hook that reads the corpus + probes service state + injects N KB of additionalContext? Budget constraint: the existing first-run-hook returns "in well under 1s" per settings.json's comment; the supervisor hook has a 20s timeout. Measure whether D8's enriched shape stays inside that budget.

### 2.6 Flagged inferences

- Default assumption: the gate runs synchronously in the `SessionStart` hook's `async: false` mode (matches existing supervisor stanza). Flagged.
- Default assumption: Claude Code's hook infrastructure stays backwards-compatible through pos-v2's rollout. Flagged.
- Default assumption: the session-start-corpus injection is text (additionalContext is text-shaped by the hook contract), not structured data. Flagged for challenge if the research surfaces a better shape.

## 3. Scope

- Read-only research. No source edits.
- Working directory `/Users/lukeivers/ivers-corp-pos-v2/`.
- The agent may read Claude Code's public documentation for hook semantics (Lens 1 composition), cited explicitly in the research doc.
- Cap: ~1000 lines (one notch smaller than D7 because Idea 8 already enumerates the question surface).

## 4. Halt triggers

1. **Claude Code capabilities required by the gate don't exist** (e.g., the desired refusal semantics require a hook feature Claude Code doesn't ship). Halt; owner rules on alternative shapes.
2. **Research surfaces that the gate must live inside a component that isn't sealed yet or doesn't exist** (e.g., "the gate is a new primary-persona primitive"). Halt; owner rules on whether D8's cycle produces a new sealed-component proposal or amends an existing one.
3. **Cold-start latency budget cannot be met** with the researched payload set. Halt; owner rules on payload trimming vs budget widening.
4. **Convergence with D7** turns out to require one unified cycle rather than two parallel ones. Halt; owner decides on merge.
5. **ODD break detected as strongly required.** Halt and signal.

## 5. Acceptance (research-plan gate)

Research document at `docs/plans/research/session-start-context-load-gate-research.md` answering §2.1–§2.5, each with evidence / citation / empirical measurement as appropriate. Executive summary ≤15 lines naming: gate location (persona vs harness layer), scope (workspace-wide vs component-scoped), payload composition, refusal semantics, composition with D7, top-3 owner decisions.

## 6. CDC adherence

- **Plan-before-code:** this research plan exists.
- **Research-before-plan:** research step precedes the proposal step.
- **Scope-only dispatch:** scope-material only; no prescription of hook-script filename, function names, or Claude Code settings layout.
- **Background-agent-default:** research step dispatches background.
- **Session-start corpus:** mandatory; noted in §header.

## 7. Composition note

Parallel dispatch with D7 permitted. If the two research docs converge on a shared additionalContext-emitter layer, the proposal phase decides whether to merge them or propose adjacent amendments. Either is fine; the research doesn't commit to a shape.

# Flow-definition + position-cursor convention

> **A FLOW is the durable representation of a real multi-step PROCESS — its steps, its branch points, and its owner-decision gates — carried in one artefact that is BOTH machine-walkable (a node graph a position cursor can walk) AND human-followable (the prose a builder reads to actually run it). A POSITION CURSOR is the "you are here" dot the flow is useless without; PAUSE-IF-LOST is the standing rule that the lost state is the default until position is positively re-established.**

This document codifies the defined-workflow system's authoring shape. It is the structural answer to the **FM.PROCESS-DRIFT** failure class (process-deviation-under-pressure): almost every loam catastrophe was a *process* failure under stress, not a knowledge failure. Full design rationale: `docs/plans/defined-workflow-system-and-position-cursor-plan.md` (P2.3).

## 1. Flow-definition shape (D1 — YAML front-matter + Markdown body)

A flow definition is a single file at `docs/flows/<flow>.flow.md` (tracked methodology flows) carrying two halves:

- **YAML front-matter** (between `---` fences) — the machine-walkable node graph. Required keys: `flow` (the flow id), `steps` (a non-empty list of step mappings). Optional: `title`, `entry` (defaults to the first step), `gates` (owner-decision points).
- **Markdown body** (after the closing `---`) — the human-followable narrative. Required: non-empty.

Each step mapping carries `id` (required), `name`, `transitions` (a list of declared step ids it can move to), and an optional `gate: true` flag. Each gate mapping carries `id` and `name`.

```yaml
---
flow: my-process
title: My process
entry: step_a
steps:
  - id: step_a
    name: 1 First
    transitions: [step_b]
  - id: step_b
    name: 2 Second
    transitions: [step_a, step_c]   # a branch point
  - id: step_c
    name: 3 Third
    transitions: []
gates:
  - id: G1
    name: Owner ratification
---
# My process — the flow
<human-followable narrative>
```

## 2. Validation rules (what a malformed definition is rejected for)

`loam flow validate <flow.md>` (and the library `parse_flow_definition`) reject, with a corrective message naming the defect:

- A missing required field (`flow`, `steps`, or a step `id`).
- A transition targeting an undeclared step.
- A step unreachable from `entry`.
- A duplicate step id.
- An empty human-followable body.
- **A flat action-list that is not a multi-step process** (fewer than 3 steps AND no branch point AND no gate). Flat checklists are NOT admitted as flows — this enforces the owner's anti-ceremony constraint ("define flows for true multi-step PROCESSES, not trivial flat actions, or we drown in ceremony").

## 3. The position cursor (D2 / D5 / Fork D1)

A cursor is a small YAML record at `<flow>.cursor.yaml` naming a definite position: `{flow, step, branch_state, updated_at}`. It is the source of truth for "you are here."

- **Single-active-flow** (D5): one cursor names exactly one flow + one step. Concurrent / nested flows are a downstream follow-on, not the first cut.
- **Explicit-write** (D5 / plan §7): the cursor advances by an explicit, validated call (`advance_cursor` — the target must be a declared transition of the current step), never by inference from runtime signals.
- **Staleness over absence** (the load-bearing F2): a cursor resolves against its flow definition; if the named step has vanished (the flow changed out from under it), it resolves **UNRESOLVED**, never a wrong-but-confident position. A confidently-wrong cursor is worse than no cursor.

### Cursor home (D2 — the build-cursor.md silent-drop guard)

- **Methodology-flow cursors** live at the TRACKED path `docs/flows/<flow>.cursor.yaml` — build-methodology is committable (the P1.1 cursor was once silently dropped from a commit because it lived under gitignored `.loam/`; this convention prevents the repeat).
- **User-facing flow-INSTANCE cursors** live under gitignored `<workspace>/.loam/flows/<flow>.cursor.yaml` — a user's live position in *their* run is per-workspace user-state.

## 4. Pause-if-lost (D4 — positive-resolution gate)

The pause check passes **only** when the cursor resolves to a definite one-sentence restatement: "step N of flow X, branch B." The inability to fill that sentence is the pause condition — the lost state is the **default**, and positive resolution is required to clear it. An empty / corrupt / ambiguous / stale cursor defaults to PAUSE, never to "probably fine."

## 5. Re-injection (D3 / Fork A1 — compose, don't rebuild)

The position is re-injected at every context-loss point by a hook that composes on the SAME re-injection mechanism the framework's SessionStart-family hooks already use (read a Claude Code envelope on stdin → read the cursor from disk → emit `additionalContext` on stdout). No new engine.

- Additive context on **SessionStart(source=compact)**, **PreCompact**, and **UserPromptSubmit** (the highest-frequency context-loss point).
- **PreToolUse** is **advisory** in the first cut (Fork A1): it surfaces the position / PAUSE directive as context the agent must honour before a consequential action; it does NOT hard-block the tool call. A blocking mode is an owner-gated follow-on.

## 6. Scope (the first cut)

In: the format + validator, the cursor library, the pause check, the re-injection hook, and ONE dogfood flow (`loam-vnext-build`). Out (downstream follow-ons): converting every process to a flow; concurrent / nested flows; automatic cursor advancement; a graphical flow editor; the PreToolUse blocking gate. See plan §7.

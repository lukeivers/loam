# Per-project PM — design

**Status:** v0.1.7 Cycle 2 (NEW component).
**Plan-doc:** `docs/plans/v0-1-7-cycle-2-per-project-pm.md`.

This document articulates the design rationale for the per-project PM
component. It is the AC.PPM.9 deliverable: PM/M-FBM boundary, workspace-state
shape, lifecycle, and composition surfaces are named explicitly so future
amendments compose against a stable contract.

## 1. Purpose

Per-project PM = workspace-scoped project manager. Each project (canonical
pos-v2 self, eric-saas, hypothetical writer's-novel, etc.) gets its own PM.
PM is **harness-general** — not dev-only, not methodology-specific. A
writer's PM uses the same machinery as a dev PM; the difference is the PM's
authored `contract.yaml` content (project_kind = "writing" vs "dev"), not
the runtime shape.

PM responsibilities at Cycle 2:

- Hold project-domain **decision/ratification state** (FIFO decision queue
  + append-only audit log of surfacings).
- Hold project-domain **state-of-world snapshot** (in-flight items, queue
  depth, last surfaced-at, free-form notes) the persona pulls on demand.
- Surface decisions one at a time via `surface_next_question()` (Cycle 2
  ships the queue + API; Cycle 4 wires the one-question-at-a-time
  persona-side flow).

PM responsibilities deferred to Cycle 4:

- `record_response()` answer-tracking API.
- `surface_next_questions_batch()` batched surfacing.
- `require_owner_response`-blocking enforcement.
- `onboarding_mode` enforcement on the persona-side flow.

PM responsibilities deferred to v0.2.0+:

- Auto-creation of skills by PM (Eric synthesis Decision H — primary persona
  for now).
- PM-driven dispatch loop (consuming `composes_with_agents` to dispatch to
  named subagents).
- Auto-load of `composes_with_skills` skills when PM activates.

## 2. PM/M-FBM boundary

This is the **largest design surface** at Cycle 2 — a contradiction here
would force a re-plan. The boundary is named explicitly:

| | PM (per-project-pm) | M-FBM (primary-persona/file_memory) |
|---|---|---|
| **What it owns** | Project-domain decision/ratification state. | Per-turn episode memory + retrieval. |
| **Granularity** | Project-scoped, decision-grain. | Turn-scoped, message-grain. |
| **Storage** | `<workspace>/workspace/.loam/pms/<handle>/` | `<workspace>/workspace/.loam/memory/` |
| **State files** | `contract.yaml`, `state.yaml`, `decision-queue.yaml`, `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` | `episodes/<workspace-slug>/<YYYY-MM-DD>/<turn-id>.md`, `search-index.sqlite`, `archived/` |
| **Read/write surface** | `PMRuntime` API (this component). | `FileMemoryStore` + `MemoryProvider` (primary-persona component). |
| **Lifecycle** | Lazy on-demand load via `host.per_project_pm.runtime_for(pm_name)`. | Eager-loaded contributor at session-start. |
| **Schema versioning** | `schema_version: 1` per state file; `PMStateCorruptedError` on mismatch. | M-FBM stores markdown + sqlite-FTS5 index; no schema_version in episode files (markdown is forward-compatible). |

**They are siblings, not parents/children.** Both live under
`<workspace>/workspace/.loam/`. Neither writes into the other's directory.
The boundary test (`test_AC_PPM_7_*`) verifies this with canary files +
directory-listing comparison: a full PM lifecycle (load → enqueue → surface)
produces zero writes to `<workspace>/workspace/.loam/memory/` and zero
writes to `<workspace>/.claude/skills/`.

**Composition possibilities (out of Cycle 2 scope, named for future
amendments):**

- An M-FBM episode entry MAY cite an audit-log path for provenance — that's
  M-FBM citing PM, not M-FBM owning PM data.
- A PM-mediated decision-surfacing event MAY trigger an M-FBM episode write
  (when the persona surfaces the question to the user, the resulting
  conversation turn is a normal episode write) — PM doesn't initiate; the
  per-turn episode writer does.
- Future amendments might add an M-FBM retrieval provider that surfaces
  PM audit-log entries via the search-index — that would be a NEW provider
  module under primary-persona, not a write into PM state by M-FBM.

## 3. Workspace-state directory shape

PM workspace-state lives at `<workspace>/workspace/.loam/pms/<handle>/`.

The path-resolution invariant: every code path routes through
`loam.workspace_bootstrap.workspace_paths.workspace_state_dir(workspace_root)`,
NOT through a hand-rolled `Path(workspace_root) / "workspace" / ".loam"`.
This inherits the HC#6 structural guard (`WorkspaceLayout` Pydantic
validator refuses `workspace_root` whose basename is `framework`).

```
<workspace>/workspace/.loam/pms/<handle>/
  contract.yaml          # PM contract — operator-authored OR scaffold-generated
  state.yaml             # PM-held project state — runtime-managed
  decision-queue.yaml    # FIFO decision queue — runtime-managed
  audit-log/             # append-only audit log — runtime-managed
    <YYYY-MM-DD>-<NNNN>.yaml
```

### File schemas

**contract.yaml** (operator-authored at PM-creation time):

```yaml
schema_version: 1
handle: "eric-saas-pm"
project_name: "eric-saas"
project_kind: "dev"           # "dev" | "writing" | "research" | "ops" | "general"
owner_name: "Eric"
workspace_root: "/Users/eric/projects/eric-saas"  # absolute
decision_surfacing_policy:
  onboarding_mode: false
  max_questions_per_turn: 1
  cool_down_seconds: 0
  require_owner_response: true
composes_with_skills: []      # advisory at Cycle 2
composes_with_agents: []      # advisory at Cycle 2
```

**state.yaml** (runtime-managed; minimal Cycle 2 shape):

```yaml
schema_version: 1
in_flight: []          # operator-recorded in-flight tasks (free-form)
last_surfaced_at: null # ISO 8601 of most recent surface_next_question()
notes: ""              # free-form operator-authored project notes
```

**decision-queue.yaml** (runtime-managed):

```yaml
schema_version: 1
queue:
  - text: "Should we ship D5 with degraded mode or hold for fix?"
    provenance: "cycle-3-design-review"  # optional, may be null
    enqueued_at: "2026-05-04T10:30:00+00:00"
```

**audit-log/<YYYY-MM-DD>-<NNNN>.yaml** (one file per surfaced question):

```yaml
schema_version: 1
event_kind: surface_question
timestamp: "2026-05-04T10:35:00+00:00"
pm_handle: "eric-saas-pm"
question_text: "..."
question_provenance: "..."     # may be null
queue_position_pre: 1          # 1-based; the position consumed
queue_depth_pre: 3
queue_depth_post: 2
```

`<NNNN>` is a 4-digit zero-padded monotonic counter scoped to (pm-name,
UTC date), reset to `0001` at midnight UTC. Computed at write time by
reading the directory listing and incrementing the max suffix found
(stdlib only; no SQLite).

### Atomicity

State writes (state.yaml, decision-queue.yaml) use the tmp+rename pattern:
write to `<file>.tmp`, fsync, rename to `<file>`. Partial writes are refused.
Audit-log writes use the same pattern (tmp+rename onto the dated filename).
This is the same atomic-write convention as
`framework/primary-persona/src/loam/primary_persona/file_memory.py`.

## 4. Lifecycle

PM is **per-workspace, not session-bound**. State persists to disk; survives
process/session restart (D3/D5 smoke). No transient in-memory state: every
write is fsync'd before return.

PM is **lazy-loaded on demand**. `PerProjectPMContribution` (registered via
the `loam.bootstrap.contributions` entry-point) publishes a
`PerProjectPMRuntime` factory on `host.per_project_pm`. The factory's
`runtime_for(pm_name)` method loads the named PM:

- If `<workspace>/workspace/.loam/pms/<pm_name>/contract.yaml` exists →
  return a hydrated `PMRuntime`.
- Otherwise → raise `PMNotFoundError` (the PM has not been authored yet;
  the caller decides whether to interpret this as an empty project or
  prompt the operator to author).

Empty-project shape: `PMRuntime.empty_state_for(workspace_root)` returns an
empty `StateOfWorld` (`pm_loaded=False`, all other fields `None` / `0` /
empty tuple) without raising. This is the D1 cold-state path.

The directory `<workspace>/workspace/.loam/pms/` is created lazily by
`enqueue_decision()` / `surface_next_question()` on first write
(`mkdir(parents=True, exist_ok=True)`). Empty workspace = no `pms/` dir;
that's the expected D1 cold-state shape.

## 5. Per-workspace, not session-bound

PM state is on-disk; there is no in-memory cache that lives across calls.
Every `state_of_world()` call re-reads the YAML files. This is the
correctness-over-performance trade-off: state is small (one queue, a
directory of audit entries), file IO is fast, and the alternative
(in-memory cache + invalidation) introduces a class of bugs not worth the
performance gain at Cycle 2's scale.

If profiling later shows a measurable cost (Cycle 4+), an LRU cache with
file-mtime-based invalidation can be layered without changing the API.

## 6. Composition surfaces (advisory at Cycle 2)

`PMContract.composes_with_skills` and `PMContract.composes_with_agents` are
**advisory metadata** at Cycle 2 — the contract carries them, validation
accepts them, but the runtime does NOT enforce or invoke them. Composition
wiring (skill auto-load when PM activates; subagent dispatch by handle)
lands at v0.2.0+ when the PM-driven dispatch loop is wired.

This is named explicitly to prevent over-scoping at Cycle 2 and to give
operator-authored contracts a stable forward-compat surface.

## 7. Communication shape (translation rule applied bidirectionally)

PM-internals stay opaque to the persona (no jargon-leak from PM to persona);
persona-supplied state gets translated to PM-domain shape on enqueue (no
jargon-leak from persona-internals into the PM queue).

Concretely:

- `enqueue_decision(question_text, provenance=None)` accepts plain
  human-readable text. The PM does not parse `question_text` for
  PM-internal markers; the text is stored verbatim. This means a persona
  can always pre-translate a project-domain question into owner-facing
  language before enqueuing; the PM doesn't second-guess.
- `state_of_world()` returns a `StateOfWorld` dataclass with named fields
  (`queue_depth`, `pending_questions`, `last_surfaced_at`). The persona
  reads named fields; no YAML inspection, no path-walking, no schema
  knowledge required.
- `surface_next_question()` returns a `SurfacedQuestion` with named
  fields. The persona reads `question.text` (already translated to
  owner-facing language at enqueue time) and the provenance string;
  surfaces to the user; logs the audit_path for traceability.

## 8. Out of scope at Cycle 2 (deferred to Cycle 4)

The following are **not implemented** at Cycle 2 and are explicitly named
here so the surface area is predictable:

- `record_response(question_id, response)` — answer-tracking API. The
  Cycle 2 audit-log records *surface* events, not response events. Cycle 4
  adds a separate audit-log event_kind for response recording.
- `surface_next_questions_batch(n)` — batched surfacing API. Cycle 2 ships
  one-at-a-time only (`surface_next_question()`).
- `require_owner_response`-blocking enforcement — at Cycle 2 the policy
  field is recorded on the contract but blocking enforcement is not wired.
  Cycle 4 enforces: with `require_owner_response=True`, attempting to
  surface a question while a prior question is still unanswered raises
  `PendingResponseError`.
- `onboarding_mode` enforcement on the persona-side flow — at Cycle 2 the
  policy field is recorded but the persona-side flow that consumes it is
  not wired. Cycle 4 wires the persona-side check ("am I in onboarding
  mode? — surface exactly one question this turn").
- `PendingResponseError` exception class — Cycle 4.
- D6 telemetry-floor for production-stake mode (OTEL spans for
  PM-mediated dispatches) — Cycle 4 wires the OTEL emission. Cycle 2's
  audit-log is the primitive Cycle 4 builds on.

## 9. Quality bar — what shipped vs what we promised

The release-note promise (per dispatch quality-bar): "PM holds project-domain
state; persona pulls state-of-world on demand; PM surfaces decisions
needing user attention; PM auto-loads when persona begins work in that
project's workspace."

Cycle 2 shipping:

- ✓ "PM holds project-domain state" — `state.yaml` + `decision-queue.yaml`,
  PM-managed.
- ✓ "persona pulls state-of-world on demand" — `state_of_world()` API.
- ✓ "PM surfaces decisions needing user attention" — `surface_next_question()`
  + audit-log primitive. (Persona-side flow that calls it is Cycle 4.)
- ✓ "PM auto-loads when persona begins work in that project's workspace" —
  `host.per_project_pm.runtime_for(pm_name)` lazy resolution; called when
  persona begins work.

All four release-note promises have tested + reliable behavior at Cycle 2's
boundary. Cycle 4 extends the surfacing into the persona-side flow.

## 11. One-question-at-a-time flow (Cycle 4)

Cycle 4 lands the persona-side surfacing flow that Cycle 2 deferred.
Three new surfaces; one extension to existing state.

### 11.1. New API methods on `PMRuntime`

- `surface_next_questions_batch(n=None)` — surfaces up to `n` questions
  in one call. The effective batch size is computed from policy:
  - With `onboarding_mode=True`: forced to `1` regardless of `n` or
    `max_questions_per_turn`. **This is the structural enforcement of
    Eric synthesis Decision Q (one-question-at-a-time PM-enforced).**
  - With `onboarding_mode=False`: `min(n_or_max,
    max_questions_per_turn, len(queue))` where `n_or_max` defaults to
    `max_questions_per_turn` when `n is None`.
  - Raises `PendingResponseError` immediately (no partial surface) when
    `require_owner_response=True` AND `pending_response_for` is non-null.

- `record_response(surfaced_audit_path, response_text)` — records the
  owner's response, writes a sibling `record_response`-kind audit-log
  entry, clears the `pending_response_for` flag in `state.yaml`.
  Idempotent: a second call against the same `surfaced_audit_path`
  returns the previously-recorded `RecordedResponse` without writing
  a duplicate audit entry.

### 11.2. State extension — `pending_response_for` field

`state.yaml` gains a new field:

```yaml
schema_version: 1
in_flight: []
last_surfaced_at: "2026-05-04T11:30:00+00:00"
notes: ""
pending_response_for: "Should we ship D5 with degraded mode?"   # NEW
```

Semantics:

- Set to the surfaced question's text when a `surface_*` call lands
  under `require_owner_response=True`.
- Cleared (set to `null`) when `record_response` writes the linked
  response.
- When non-null AND `require_owner_response=True`, the next call to
  `surface_next_questions_batch` raises `PendingResponseError`.
- Backward-compat: a Cycle 2 `state.yaml` without the field loads as
  `pending_response_for: null` (no blocking).

### 11.3. Blocking enforcement — batch API only

`surface_next_question()` (the Cycle 2 API) is **preserved verbatim**
— it does NOT enforce blocking. This keeps Cycle 2 callers' contract
intact. The structural one-question-at-a-time discipline lives on the
Cycle 4 batch API:

```python
# Onboarding mode — exactly one question per call, every call:
runtime.contract.decision_surfacing_policy.onboarding_mode == True
batch = runtime.surface_next_questions_batch()  # always len <= 1
```

The persona-side flow (which lands in primary-persona at v0.2.0+
alongside auto-creation) calls `surface_next_questions_batch()` to
get the questions to relay to the user this turn — onboarding-mode
enforcement is structural at the batch API, not advisory.

### 11.4. Audit-log entry shape — `record_response` event

```yaml
schema_version: 1
event_kind: record_response                              # vs surface_question
timestamp: "2026-05-04T11:42:00+00:00"
pm_handle: "test-pm"
response_text: "Hold for fix; ship in v0.1.8."
surfaced_audit_path: "audit-log/2026-05-04-0001.yaml"    # relative
surfaced_question_text: "Should we ship D5 with degraded mode?"
responded_at: "2026-05-04T11:42:00+00:00"
```

The `<NNNN>` counter is shared across both event_kinds within
(pm-name, UTC date). A `surface_question` at `0001` and a
`record_response` at `0002` share the same monotonic sequence — the
audit-log is fully ordered.

### 11.5. Idempotency of `record_response`

The audit-log is the source of truth (per Cycle 2 design rule).
`record_response` scans `audit-log/` for an existing
`record_response`-kind entry whose `surfaced_audit_path` matches the
caller's argument; on hit, returns the prior `RecordedResponse`
without writing a duplicate entry. This prevents double-recording
when the persona retries after a transient error.

## 12. Composition with `audit-block-on-telegram` SKILL

Per AC.QSURF.8 (Cycle 4) — composition with the
`audit-block-on-telegram` SKILL (sealed v0.1.6 at
`plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md`).

### 12.1. The SKILL's surface-when-meaningful rule

The audit-block SKILL surfaces a structured trailer (Executed /
Deferred-to-owner / Missed) under user-visible replies when at least
one of four conditions holds. The relevant condition for PM
composition:

> **A decision was made** — the persona made a non-trivial ruling
> autonomously and the user should see it.

PM surfacings AND PM-recorded responses are exactly that: a decision
was made (the persona is asking the user to decide → surfacing; OR
the user made the decision → response recorded). Both events satisfy
the SKILL's "decision was made" trigger condition.

### 12.2. Programmatic composition surface — `is_audit_block_trigger`

`SurfacedQuestion` and `RecordedResponse` both expose:

```python
@property
def is_audit_block_trigger(self) -> bool:
    """Whether this PM event satisfies the
    audit-block-on-telegram SKILL's 'decision was made'
    trigger condition.
    """
    return True
```

A persona authoring a Telegram reply that includes a PM event checks
the property to know whether to surface the audit-block:

```python
surfaced = pm.surface_next_questions_batch()
for sq in surfaced:
    if sq.is_audit_block_trigger:
        # SKILL's "decision was made" condition fires; surface the
        # audit-block in this Telegram reply.
        ...
```

Cycle 4 returns `True` unconditionally. Future cycles may gate on
event metadata — e.g., a "low-stakes status update" event shape that
doesn't trigger the audit-block. The property mechanism (vs an
always-True field) is the forward-compat extension point.

### 12.3. One-way composition

PM produces events the SKILL consumes. The SKILL does not produce
events PM consumes. Cycle 4 ships ONLY the consumption contract on
the PM side; Cycle 4 does NOT modify the
`audit-block-on-telegram` SKILL itself (it's a v0.1.6 sealed
artefact). This keeps the Cycle 4 fence on
`framework/per-project-pm/`.

### 12.4. Cross-reference invariant

The composition contract is verified structurally by
`tests/test_AC_QSURF_8_audit_block_composition.py`:

1. Both `SurfacedQuestion` and `RecordedResponse` expose
   `is_audit_block_trigger` returning `True`.
2. This design-note carries the path
   `plugins/loam-skills/skills/audit-block-on-telegram/` and the
   exact "decision was made" trigger condition string.
3. The SKILL.md file at the referenced path actually exists and
   contains the named trigger string.

If any of those three structural facts is false, the test fails.

## 13. References

- **Plan-doc:** `docs/plans/v0-1-7-cycle-2-per-project-pm.md`.
- **Parent plan:** `docs/plans/v0-1-7-personas-pm-layered-skills.md`.
- **Eric synthesis Decision G5** — PM-shape is harness-general.
- **Eric synthesis Decision Q (RESOLVED YES)** — one-question-at-a-time
  PM-enforced; Cycle 4.
- **Eric synthesis Decision I** — workspace-local skills under Anthropic-
  native `<workspace>/.claude/skills/<name>/SKILL.md`; PM does not own.
- **`framework/primary-persona/src/loam/primary_persona/contract.py:211`** —
  `PersonaContract` Pydantic precedent for `PMContract`.
- **`framework/primary-persona/src/loam/primary_persona/file_memory.py`** —
  M-FBM (the boundary partner).
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/workspace_paths.py`** —
  `WORKSPACE_STATE_SUBDIR` canonical convention.
- **FIDRAFT entries on per-project PM** (committed `0f70c06` + `ccd48d4`).

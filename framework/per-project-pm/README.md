# framework/per-project-pm

Per-project PM persona for loam — workspace-scoped project-manager that holds
project-domain decision/ratification state, surfaces decisions needing user
attention, and auto-loads when a persona begins work in the workspace.

**Status:** v0.1.7 Cycle 4 (sealed-component discipline applies — initial
seal at v0.1.7 Cycle 2; Cycle 4 extends with the deferred surfacing flow).

**Plan-docs:**
- Cycle 2 (initial component): `docs/rebuild/plans/v0-1-7-cycle-2-per-project-pm.md`.
- Cycle 4 (one-question-at-a-time PM-enforced surfacing flow):
  `docs/rebuild/plans/v0-1-7-cycle-4-one-question-pm-flow.md`.

## What this component is

PM = workspace-scoped project manager. Each project gets its own PM (one per
workspace, named at PM-creation). PM is **harness-general** — not dev-only;
a hypothetical writer's PM uses the same machinery.

PM is responsible for:

1. **Project-domain decision/ratification state** — a FIFO queue of decisions
   awaiting owner attention, with an append-only audit log of when/how each
   was surfaced.
2. **State-of-world snapshot** — a structured view (active goals, in-flight
   items, queue depth, last-surfaced-at, free-form notes) the persona pulls on
   demand.
3. **Decision-surfacing API** — `surface_next_question()` consumes the head of
   the FIFO queue and returns a `SurfacedQuestion` with provenance + audit
   path. Cycle 2 establishes the queue + API; Cycle 4 wires the
   one-question-at-a-time persona-side flow + response tracking.

## What this component is NOT

- **NOT M-FBM episode memory.** M-FBM (file-based memory at
  `<workspace>/workspace/.loam/memory/`) owns turn-grain episode markdown.
  PM owns project-domain decision state. They are siblings under
  `<workspace>/workspace/.loam/`. The boundary is articulated in
  `docs/design.md`.
- **NOT workspace-local skills.** Per Eric synthesis Decision I,
  workspace-local skills live under Anthropic-native
  `<workspace>/.claude/skills/<name>/SKILL.md`. The PM may *reference* a
  skill set in its `composes_with_skills` advisory metadata but does not own
  the skills.
- **NOT eager-loaded.** Per cycle-2 plan §4 Surface #6 (F2.C), PMs are loaded
  lazily on demand via `host.per_project_pm.runtime_for(pm_name)`. Empty
  workspace = no PM authored = no `<workspace>/workspace/.loam/pms/` dir;
  not an error.

## Workspace-state shape

```
<workspace>/workspace/.loam/pms/<handle>/
  contract.yaml          # PM contract (handle, project_name, project_kind, owner, scope, policy)
  state.yaml             # current PM-held project state (in-flight items, last_surfaced_at, notes)
  decision-queue.yaml    # FIFO decision queue
  audit-log/             # append-only event log; one YAML file per surfaced question
    <YYYY-MM-DD>-<NNNN>.yaml
```

`<NNNN>` is a 4-digit zero-padded monotonic counter scoped to (pm-name, UTC date),
reset to `0001` at midnight UTC.

## API surface

```python
from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.errors import (
    PMNotFoundError,
    PMStateCorruptedError,
    PendingResponseError,  # Cycle 4
)

# Lazy load — raises PMNotFoundError if no contract.yaml.
runtime = PMRuntime.from_workspace(workspace_root, "eric-saas-pm")

# Empty-project state-of-world (no PM authored yet).
empty = PMRuntime.empty_state_for(workspace_root)

# Read state-of-world snapshot.
state = runtime.state_of_world()
# state.queue_depth, state.pending_questions, state.last_surfaced_at,
# state.pending_response_for (Cycle 4: question awaiting response, or None)

# Append a decision.
position = runtime.enqueue_decision(
    "Should we ship D5 with degraded mode or hold for fix?",
    provenance="cycle-3-design-review",
)

# Consume next question (returns None on empty queue — empty is normal).
# Cycle 2 API; preserved verbatim. Does NOT block on pending_response_for.
question = runtime.surface_next_question()
if question is not None:
    # question.text, question.provenance, question.queue_position,
    # question.surfaced_at, question.audit_path,
    # question.is_audit_block_trigger (Cycle 4: True — composes with
    # audit-block-on-telegram SKILL)
    ...

# Cycle 4 — batch surfacing (the structural one-question-at-a-time API).
# With onboarding_mode=True, returns at most 1 question regardless of n.
# Raises PendingResponseError when require_owner_response=True AND a
# prior surfacing is unanswered.
batch = runtime.surface_next_questions_batch(n=3)  # tuple of SurfacedQuestion

# Cycle 4 — record an owner response (clears blocking).
response = runtime.record_response(
    surfaced_audit_path=question.audit_path,
    response_text="Hold for fix; ship in v0.1.8.",
)
# response.text, response.surfaced_audit_path,
# response.surfaced_question_text, response.responded_at,
# response.audit_path, response.is_audit_block_trigger (True)
```

## Contribution registration

`PerProjectPMContribution` registers via the `loam.bootstrap.contributions`
entry-point group. The contribution publishes a `PerProjectPMRuntime` factory
on `host.per_project_pm` — call `host.per_project_pm.runtime_for(pm_name)` to
get a `PMRuntime` for a named PM. Phase: `after_orchestrator_ready`. After:
`("primary_persona",)`.

## Boundary with M-FBM

PM does NOT write to M-FBM episode store. PM does NOT write to
`<workspace>/.claude/skills/`. The boundary test (`test_AC_PPM_7_*`) verifies
this with canary files + directory-listing comparison.

## Cycle 4 surfaces (landed)

Cycle 4 ships the deferred decision-surfacing + one-question-at-a-time
flow on top of Cycle 2's queue + API:

- `record_response()` — answer-tracking API; idempotent on duplicate.
- `surface_next_questions_batch()` — batched surfacing API. Forces
  exactly 1 question per call when `onboarding_mode=True` (structural
  Eric synthesis Decision Q enforcement). Raises
  `PendingResponseError` when `require_owner_response=True` AND a
  prior surfacing is unanswered.
- `pending_response_for` field in `state.yaml` — blocking flag.
- `RecordedResponse` dataclass — return value of `record_response()`.
- `PendingResponseError` exception class.
- `is_audit_block_trigger` property on both `SurfacedQuestion` and
  `RecordedResponse` — composes with the
  `audit-block-on-telegram` SKILL (sealed v0.1.6 at
  `plugins/loam-skills/skills/audit-block-on-telegram/`).

The single-question API `surface_next_question()` is preserved
verbatim from Cycle 2 — does NOT enforce blocking; the structural
discipline lives on the batch API. See `docs/design.md` §11 + §12 for
the full rationale.

## Composition with `audit-block-on-telegram` SKILL

Both `SurfacedQuestion` and `RecordedResponse` carry
`is_audit_block_trigger=True`. A persona authoring a Telegram reply
that includes a PM event checks the property to know whether to
surface the SKILL's structured audit-block trailer (Executed /
Deferred-to-owner / Missed). Cycle 4 always returns `True`; future
cycles may gate. See `docs/design.md` §12.

## See also

- Cycle 2 plan-doc: `docs/rebuild/plans/v0-1-7-cycle-2-per-project-pm.md`.
- Cycle 4 plan-doc: `docs/rebuild/plans/v0-1-7-cycle-4-one-question-pm-flow.md`.
- Parent plan: `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md`.
- Design rationale: `docs/design.md` (this component).
- M-FBM: `framework/primary-persona/src/loam/primary_persona/file_memory.py`.
- Composing SKILL: `plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md`.

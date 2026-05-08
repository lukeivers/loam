# per-project-pm

## What it does

`per-project-pm` is the workspace-scoped project-manager
component. Each loam workspace gets its own PM (one per
workspace, named at PM-creation). The PM holds project-domain
decision and ratification state — distinct from the persona's
session-bridging memory, which lives in the
[`memory`](memory.md) component.

A PM is responsible for three things:

- **Project-domain decision/ratification state.** A FIFO queue
  of decisions awaiting owner attention, with an append-only
  audit log of when and how each was surfaced.
- **State-of-world snapshot.** A structured view (active goals,
  in-flight items, queue depth, last-surfaced-at, free-form notes)
  the persona pulls on demand.
- **Decision-surfacing API.** A one-question-at-a-time flow the
  persona uses to bring decisions to the user, with response
  tracking that prevents question-bombing.

PM is **harness-general**, not dev-only — a hypothetical writer's
PM uses the same machinery as a developer PM. PMs are
**lazy-loaded**: an empty workspace has no PM authored, no PM
state on disk, and that is not an error.

## How to invoke

You do not invoke `per-project-pm` directly from a shell. The
persona invokes it programmatically:

```python
from loam.per_project_pm.runtime import PMRuntime

# Lazy load — raises PMNotFoundError if no contract exists.
runtime = PMRuntime.from_workspace(workspace_root, "<pm-name>")

# Read state-of-world snapshot.
state = runtime.state_of_world()

# Append a decision to the queue.
runtime.enqueue_decision("<question>", provenance="<source>")

# Surface the next pending decision.
question = runtime.surface_next_questions_batch(n=1, onboarding_mode=True)

# Record the owner's response.
runtime.record_response(surfaced_audit_path=question[0].audit_path,
                        response_text="<answer>")
```

The contribution registers via the `loam.bootstrap.contributions`
entry-point group; `workspace-bootstrap` exposes a
`PerProjectPMRuntime` factory on `host.per_project_pm` after the
orchestrator is ready.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **PM state on disk.** Lives at
  `<workspace>/workspace/.loam/pms/<handle>/`:
  - `contract.yaml` — PM contract (handle, project, owner, scope).
  - `state.yaml` — current state-of-world snapshot.
  - `decision-queue.yaml` — FIFO decision queue.
  - `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` — append-only event log;
    one YAML file per surfaced question.
- **OTel spans.** `loam.per_project_pm.*` namespace. Each
  `surface_next_questions_batch` call emits a span; each
  `record_response` emits a span; queue mutations emit spans.
- **The persona's surfacing.** When the PM has pending decisions,
  the persona surfaces them one-at-a-time through the configured
  user-visible channel; the surfacing carries the
  `is_audit_block_trigger` property which composes with the
  `audit-block-on-telegram` skill from the loam-skills plugin.

## Stable surfaces (for plugin authors)

- **`PMRuntime` API.** The class methods listed under "How to
  invoke" are stable from v0.1.7 onward. Plugin authors writing
  domain-specific PMs (e.g. an extraction-pipeline PM) compose
  with this API; they do not subclass `PMRuntime`.
- **`RatificationBatch`.** The `loam.per_project_pm.ratification`
  helper composes confidence-banded AC-ratification questions
  through the PM's decision queue. Used by the dev-sdlc
  `odd-extractor` to enqueue per-AC ratification questions
  with structured provenance.
- **Boundary with [`memory`](memory.md).** PM does not write to
  the memory store; memory does not write to the PM's state.
  Both live under `<workspace>/workspace/.loam/` as siblings;
  the boundary is enforced by tests.

For internal implementation detail see
[`framework/per-project-pm/README.md`](../../framework/per-project-pm/README.md).

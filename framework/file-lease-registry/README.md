# file-lease-registry (WS-B1)

A local, per-machine registry that grants an agent dispatch an exclusive
claim over a set of file globs **at grant time — before any worktree
exists**. It prevents two agents from being dispatched with overlapping
file claims, makes the dependency-manifest set single-writer, and caps
the number of concurrent in-flight dispatches (the admission throttle).

## Why this exists (and what it deliberately does NOT do)

Worktree isolation (`.claude/worktrees/<agent-id>/`) isolates the
*checkout*. The lease isolates the *logical claim* — the piece worktrees
structurally cannot provide.

**Known blind spot — leases and the merge queue are a pair, not a
substitute for each other.** Leases prevent **textual** collisions only:
two dispatches editing the same file. They do **not** catch **semantic**
collisions — dispatch A changes a function signature and dispatch B calls
it the old way in a file A never touched. That produces zero git conflict
and a broken main, and no lease can see it. The structural catch for
semantic breakage is the batching **merge queue** (WS-B2): tested-SHA ==
merged-SHA, bisect-on-fail. Ship both; neither alone suffices. This
component does not oversell the lease as a complete collision guard.

**Overlap detection is a conservative approximation.** Precise
glob-intersection is undecidable in general, so uncertain overlap counts
as a conflict (see `overlap.py`). A false conflict costs a serialized
dispatch; a false non-conflict would cost the exact textual collision the
lease exists to prevent — so the bias is toward refusing.

## Scope boundary — enforcement logic vs mandatory-path wiring

WS-B1 delivers the registry primitive **and its enforcement logic**,
exposed at the production entry point `LeaseRegistry.grant_or_refuse(...)`
— the grant path a dispatcher calls before dispatching. **Wiring this
check into the mandatory dispatch path so it fires structurally on every
dispatch is a named follow-up, not WS-B1.** The only chokepoints that
would make the check unavoidable are the sealed dispatch wrapper
(`primary-persona`, a sealed fence) or a `.claude/settings.json` hook —
both out of WS-B1's fence. The enforcement logic here is complete and
tested end-to-end; only the mandatory-path attachment is deferred.

## Usage

```python
from loam.file_lease_registry import LeaseRegistry, Lease, LeaseRefusal

reg = LeaseRegistry("/path/to/leases.json", max_concurrent_leases=8)

result = reg.grant_or_refuse("dispatch-42", ["src/auth/**"], run_dir="/runs/42")
if isinstance(result, LeaseRefusal):
    print(result.kind, result.message)   # "overlap" | "deps_manifest" | "admission"
else:
    ...                                   # dispatch with the lease
    reg.release("dispatch-42")            # on completion / failure

reg.reap()   # release leases whose holder is artifact-probe-dead
```

- **release** ends a lease on terminal state (completion / failure).
- **reap** releases leases whose holder is artifact-probe-dead, judged by
  the shared `probe_liveness()` reader from `handsoff_loop/convergence.py`
  (the same reader the fleet collector uses — never a second hand-rolled
  one), guarded by a startup-grace window so a live agent still spinning
  up (no artifacts yet) keeps its claim.

Per-machine scope only: cross-operator collisions are the CODEOWNERS +
merge-queue's job, never a distributed lease store.

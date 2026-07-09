# Plan — WS-B1: File-lease registry + admission throttle

**Status:** plan (pre-code). 2026-07-09.
**Working directory:** `/Users/lukeivers/loam`.
**Authored against HEAD:** `c53458da`.
**Source of scope:** `workspace/strategy/ai-shop-backplane/BACKPLANE-PLAN.md`
§5 Track B, WS-B1 (also §4 build #8). This plan builds **only** WS-B1.
**Persona:** loam-builder. Plan-before-code hard gate satisfied by this doc.

---

## 1. Summary / TLDR

Two agents must not be dispatched with overlapping file claims; a
dependency-manifest touch is single-writer; concurrent in-flight
dispatches are capped. All enforced at **grant time**, before any
worktree exists. WS-B1 delivers this as a **new standalone component**
`framework/file-lease-registry/` — a local on-disk lease store with a
grant/release/reap API. A lease is a set of file globs granted to one
dispatch and released on terminal state (complete / fail /
artifact-probe-dead). Overlap detection is conservative (uncertain
overlap = conflict). Dead-holder reaping reuses the **existing shared
reader** `probe_liveness()` in `handsoff_loop/convergence.py` — never a
second hand-rolled liveness reader.

## 2. Seal classification + scope boundary (read this first)

**Seal state: NEW STANDALONE code, NOT a `loam amend` cycle.**

- WS-B1's spec says compose "additively as a sidecar, the reference
  pattern being how `scope_objective_binding` extended the sealed
  objective tracker **without modifying it**." Verified in-repo:
  `scope_objective_binding` is an additive "sidecar enforcement table"
  in `objective-tracker/src/.../store.py` (line 19-20) + `events.py`
  (line 127) — additive, non-modifying.
- WS-B1 therefore touches **no existing sealed component**. It is a new
  component under `framework/`. New loam components are not born sealed
  (sealing is a later milestone freeze ritual). So: **standard
  build+test discipline (plan + tests + pytest), no `loam amend`
  apply/seal cycle, no `SEAL_COMMIT` sidecar.**
- The sealed dispatch wrapper (`framework/primary-persona/src/loam/
  primary_persona/dispatch_wrapper.py`, primary-persona SEALED) is
  **not modified**. `.claude/settings.json` is **not touched**.

**Scope boundary (stated consciously, per the A8 "primitive with no
consumer is a §2.5 violation" ruling):** WS-B1 delivers the lease
registry primitive **and its enforcement logic**, exposed at a
production entry point (`grant_or_refuse`). **Wiring the registry into
the mandatory dispatch path is a NAMED FOLLOW-UP, not WS-B1.** Reason
it is deferred, not omitted: the only chokepoints that would make the
check structurally mandatory are (a) the sealed dispatch wrapper
(primary-persona — sealed fence, would require an amend cycle) or (b) a
`.claude/settings.json` hook — **both explicitly forbidden by this
dispatch's hard constraints.** The enforcement logic is complete and
exercised end-to-end; only the mandatory-path attachment is parked.
This is the same shape as A8 parking its persona-prompt consumer
(A8 plan §9). The follow-up is recorded in the component README.

The production entry point the outcome-altitude test hits is
`LeaseRegistry.grant_or_refuse(...)` — the grant path a dispatcher
calls before dispatching. It is "the production dispatch path" from the
lease's perspective: it either returns a granted `Lease` or a
structured `LeaseRefusal`, against a real on-disk store, no pre-set
in-memory state.

## 3. Three-lens check

- **Lens 1 (Claude leverage):** reuses `handsoff_loop.probe_liveness`
  (artifact-probe liveness the isolated-agent run records already
  produce) rather than re-reading process state; composes on
  `.claude/worktrees/` isolation (the lease adds the *logical* claim
  worktrees structurally cannot provide).
- **Lens 2 (harness/persona):** adds a toolkit primitive every future
  dispatcher composes against; reduces the operator's burden of
  manually tracking which agent owns which files.
- **Lens 3 (ODD):** ACs below are outcome-shaped; every code branch
  maps to a named AC (§5 reverse-trace at §6).

## 4. Objective

A dispatcher can, at grant time, atomically acquire an exclusive claim
over a set of file globs for one dispatch. A grant whose globs overlap
a live lease is refused with a structured refusal naming the holder. A
grant touching the dependency-manifest set acquires one named exclusive
lease regardless of globs. Grants beyond the configured concurrent-lease
ceiling are refused with an admission-control refusal. A lease whose
holder is artifact-probe-dead (past a startup grace) is reapable, after
which its globs are grantable again. All state is on-disk (files-are-
memory), per-machine (no distributed store).

## 5. Acceptance criteria (outcome-shaped)

### AC.LEASE.1 — Grant / overlap-refuse / grant *(outcome-altitude)*
Against a real on-disk store with no pre-set state, through the
production grant entry point: (a) grant globs `src/auth/**` → returns a
granted lease; (b) a request for `src/auth/login.py` → returns a
refusal whose reason is overlap and whose message names the holding
dispatch of (a); (c) a request for `src/billing/**` → returns a granted
lease. Overlap detection is conservative: a descendant/ancestor/
same-tree glob pair conflicts; a disjoint-subtree pair does not.

### AC.LEASE.2 — Dependency-manifest single-writer
Two grants each requesting a path in the dependency-manifest set
(`package.json`, lockfiles, the DB schema dir — a configured set): the
first is granted; the second is refused with a refusal naming the
deps-manifest exclusive lease, regardless of whether the two grants'
other globs overlap. After the first releases, the second is granted.

### AC.LEASE.3 — Admission throttle
With the concurrent-lease ceiling set to N, N non-overlapping grants
succeed and the (N+1)th non-overlapping grant is refused with an
admission-control refusal (categorically distinct from an overlap
refusal). Releasing one active lease admits a subsequent request.

### AC.LEASE.4 — Dead holder is reapable and its globs re-grantable
A lease whose holder is artifact-probe-dead — run dir stale beyond the
probe's stale window, judged by the shared `probe_liveness()` reader —
is released by `reap()`, and a post-reap request for the reaped globs
is granted.

### AC.LEASE.5 — Startup grace: a newborn lease is not reaped
A freshly granted lease whose run dir has no artifacts yet, within the
configured startup-grace window, is **not** reaped by `reap()` (a
live-but-not-yet-producing agent must not lose its claim). Only after
the grace window elapses without fresh artifacts does the probe-dead
judgment make it reapable.

### AC.LEASE.6 — Documented blind spot (lease ↔ merge queue pairing)
The component README states the known blind spot: leases prevent
**textual** collisions only; **semantic** collisions (A changes a
signature, B calls it the old way in a file A never touched — zero git
conflict, broken main) are the batching merge queue's catch (WS-B2).
The doc presents the pair; it does not oversell the lease as a complete
collision guard. The README also names the deferred mandatory-path
wiring (§2 boundary) and the conservative-overlap approximation.

### AC.LEASE.7 — Concurrent grants of overlapping globs: exactly one wins
Two concurrent grant requests for overlapping globs against the same
store resolve to exactly one granted lease and one refusal — the
critical section is serialized so the overlap check and the write are
atomic (the objective's "structurally cannot" must hold under a race,
not only in sequence).

### 5.x Behaviour-count (forward)
| # | Behaviour | AC |
|---|-----------|-----|
| 1 | grant, overlap-refuse (conservative), disjoint-grant | AC.LEASE.1 |
| 2 | deps-manifest exclusive single-writer | AC.LEASE.2 |
| 3 | concurrent-lease ceiling refusal + admit-on-release | AC.LEASE.3 |
| 4 | reap probe-dead holder; regrant reaped globs | AC.LEASE.4 |
| 5 | startup grace: newborn not reaped | AC.LEASE.5 |
| 6 | README blind-spot + boundary + approximation doc | AC.LEASE.6 |
| 7 | atomic grant under concurrency | AC.LEASE.7 |

7 behaviours, 7 ACs. No method-in-AC.

## 6. Design (method — builder's call, not in the ACs)

- **Component:** `framework/file-lease-registry/`, package
  `loam.file_lease_registry`, pyproject name
  `loam-file-lease-registry`. Layout mirrors sibling components
  (`src/loam/file_lease_registry/`, `tests/`, `pyproject.toml`,
  `README.md`).
- **Store:** a single JSON file (default under a registry dir; path
  injectable for tests), read-modify-write guarded by a combined
  intra-process `threading.Lock` + inter-process `fcntl.flock` on a
  lockfile, so grant/release/reap are atomic (AC.LEASE.7).
- **Lease record:** `{lease_id, dispatch_id, globs, deps_manifest,
  run_dir, granted_at}`. One record per active lease inside the store.
- **Overlap:** conservative. `_glob_prefix(p)` = leading path with no
  glob metachar. Two globs conflict if one prefix is an ancestor-or-
  equal of the other, OR either glob (as a recursive-glob regex,
  `**`→`.*`, `*`→`[^/]*`, `?`→`[^/]`) matches the other's prefix.
- **Deps set:** configured tuple of patterns (`package.json`,
  `*.lock`, `package-lock.json`, `poetry.lock`, `Cargo.lock`,
  `yarn.lock`, `pnpm-lock.yaml`, a schema-dir glob). A request touching
  any deps pattern also claims the reserved `__deps_manifest__`
  exclusive key.
- **Reap:** for each active lease, `alive = probe_liveness(run_dir)
  ["alive"]`; a lease is reapable iff `not alive AND (now - granted_at)
  > startup_grace_s`. Single import site for `probe_liveness` via a
  thin path-bootstrap module; no second reader.
- **Refusal:** `LeaseRefusal(kind, message, holder_dispatch_id)` where
  `kind ∈ {"overlap","deps_manifest","admission"}`. Returned as a
  value, not raised (domain outcome).

Reverse-trace: every branch (overlap conflict, deps claim, ceiling,
reap, grace) backs a named AC. No defensive branch without an AC.

## 7. Hard constraints

1. No `git commit --amend`; corrective commits only.
2. No edit to any sealed component; `dispatch_wrapper.py` untouched.
3. `.claude/settings.json` untouched.
4. `probe_liveness()` reused, not re-rolled (single import site).
5. Per-machine scope only; no distributed lease store.
6. Nothing outside `framework/file-lease-registry/` + this plan doc.
7. Halt-and-surface any ODD violation or sealed-fence need rather than
   working around it.

## 8. Out of scope (named)
- Wiring the registry into the mandatory dispatch path (§2 boundary —
  named follow-up; needs the sealed wrapper or a settings.json hook).
- WS-B2 (product-repo federation / merge queue) and every other
  workstream (WS-A*, WS-C*, WS-D*, WS-F*).
- Cross-operator / distributed leases (CODEOWNERS + merge queue's job).
- Sealing this component (future milestone ritual).

# Research — memory-sidecar port workspace-scoping

**Authored:** 2026-04-23.
**Status:** RESEARCH-ONLY (read-only task). No code edits, no test
runs, no agent dispatches. Owner rulings requested at §10.
**Triggered by:** two pos-v2 workspaces on one host
(`/Users/lukeivers/ivers-corp-pos-v2` + `/Users/lukeivers/pos3`), both
launchd-namespaced per amendment #6, both binding `127.0.0.1:8765`.
Second-booted sidecar crashloops on `[Errno 48] address already in use`.
**Working directory throughout:** canonical tree only.
**Prior art:**
- `docs/archive/component-research/namespaced-labels-and-bootout/proposal.md`
  (amendment #6 — launchd-label namespacing, AC6 multi-workspace
  coexistence).
- `docs/plans/amendment-28-workspace-identity-routed-first-run.md`
  + its research doc (first-run state workspace-routing; the second
  sibling defect in the same workspace-identity family).
- `docs/FUTURE_IDEAS.md` Idea 9 (slug-collision detection; explicitly
  open; 2026-04-23 update notes state-routing closed, slug-collision open,
  does not name ports).

---

## 1. Executive summary (≤10 lines)

1. **Problem.** Two pos-v2 workspaces on one host cannot run their
   memory sidecars concurrently: both bind the same hardcoded TCP port
   `127.0.0.1:8765`, so only whichever `launchctl bootstrap`s first
   gets the port and the other sidecar crashloops on `EADDRINUSE`.
2. **Spec objective coverage — HALT TRIGGER #1 HIT.** No objective in
   `docs/spec/pos-v2-objectives-spec.md` v1.0, v1.1, or v1.2
   governs multi-workspace service isolation, port allocation, or
   concurrent-workspace coexistence. Precedent (amendment #6 AC6,
   amendment #28 AC10/AC11) shows the workspace-identity family has
   landed as amendment-level re-extensions without naming a spec
   objective; whether that precedent was correct under CLAUDE.md's
   "name the spec objective or the work is dev-discipline" operational
   caution is an owner decision (D1 below). §3 + §10 elaborate.
3. **Candidate solution shapes (no recommendation — owner rules).**
   S1 per-workspace config write-through the existing `memory.yaml`
   port seam; S2 bootstrap-time auto-probe for a free port;
   S3 first-run-scaffold-assigned port derived from workspace slug /
   hash; S4 switch transport to a unix-domain socket under the
   workspace tree. §7 has owning-component + cost table.
4. **Owner decisions required (see §10).** D1 — whether to enter a
   spec v1.x amendment first, or admit this as a §4 re-extension under
   Idea 9's expanded scope (as amendment #28 did with state-routing).
   D2 — owning-component boundary: memory-system vs workspace-bootstrap
   vs hands-off-lifecycle vs a multi-component amendment. D3 — chosen
   solution shape from §7.

---

## 2. Background — what pos3 actually hit

Observed on this host 2026-04-23:

- `/Users/lukeivers/ivers-corp-pos-v2` has slug `ivers-corp-pos-v2`; its
  plist `com.pos-v2.ivers-corp-pos-v2.memory-graphiti.plist` is
  installed and loaded.
- `/Users/lukeivers/pos3` has slug `pos3`; its plist is correctly
  namespaced per amendment #6.
- Both plists invoke `<workspace>/memory-system/.venv/bin/python -m
  src.service`, which reads `GRAPHITI_SERVICE_HOST` /
  `GRAPHITI_SERVICE_PORT` from env. Neither plist's
  `<key>EnvironmentVariables</key>` sets those variables.
- Both processes therefore fall to the `service.py` defaults
  `127.0.0.1` / `8765`. The second process to start hits
  `[Errno 48] address already in use`.

Symptom is a **port-value** collision, not a launchd-label collision.
Amendment #6 closed the label-collision sibling; amendment #28 closed
the state-file-routing sibling; port binding is the third sibling in
the workspace-identity family (see §8 on the family classification).

---

## 3. Spec objective survey (v1.0 + v1.1 + v1.2)

**Primary-source file:**
`docs/spec/pos-v2-objectives-spec.md` (356 lines).

Exhaustive grep of the spec for terms `port`, `network`, `bind`,
`socket`, `host`, `service`, `sidecar`, `isolat`, `multi-workspace`,
`concurrent` returns zero matches that name workspace-level isolation
of a running service or port assignment. The spec covers:

- Session-resilience (restart/compaction survival — all *within a
  single workspace*).
- Self-upgrade invariants (a..g; clause (g) is about installed-change
  fidelity, not cross-workspace concurrency).
- Channel-agnostic interaction (R13 — about user-facing channels, not
  backend service ports).
- Memory-system behaviours (accrual / retrieval / temporal /
  retention / provenance / supersession — all single-workspace).
- Observability (OTel emission; no port / multi-workspace framing).
- No "workspace isolation" or "multi-workspace coexistence" appears
  anywhere in v1.0, v1.1, or v1.2.

### 3.1 Halt trigger #1 fires

Per this task's halt-trigger #1 and `CLAUDE.md` §"Operational
cautions": if no spec objective in v1.0/v1.1/v1.2 governs
multi-workspace service isolation, **halt and report**. The text is
explicit: "Before scoping anything as a sealed-component amendment,
name the specific spec objective (v1.0/v1.1/v1.2) the code will
satisfy. If I can't name one, the work is dev-discipline …, not a
sealed-component cycle."

Two paths forward the owner must choose between (D1 in §10):

- **Path A — spec amendment first.** Propose a new spec clause (v1.3
  addendum, or a v1.2.1 sub-cycle) that names multi-workspace
  coexistence as an objective of the foundational layer. Acceptance
  could read e.g.: "Two pos-v2 workspaces on the same host can be
  first-run'd sequentially without either's long-running services
  evicting, crashing, or stalling the other's. Services include the
  memory sidecar, the orchestrator, and any other long-running
  process the framework installs under launchd." After landing, the
  port-scoping fix follows under that objective.
- **Path B — §4 re-extension under an existing amendment-chain
  objective.** Amendment #6 AC6 is the objective-level anchor:
  *"Scaffold on workspace A (slug `alpha`) and on workspace B (slug
  `beta`) in sequence. Both `com.pos-v2.alpha.orchestrator` and
  `com.pos-v2.beta.orchestrator` are loaded simultaneously;
  `launchctl print` for each reports a program path rooted at its
  own workspace. B's scaffold does not evict A."* AC6 as written
  scoped to label + program-path, not to ports — but its objective
  ("multi-workspace coexistence") is the one the port defect
  violates. Re-extension per ODD §4 (the canonical pattern
  `odd-methodology.md` §4.1) would add a new AC (AC15 or AC10-series
  under the revised AC#-numbering amendment #28 uses) reading
  something like: *"When workspaces A and B both have `launch: true`
  in their `memory.yaml`, both memory sidecars bind and stay
  `RunAtLoad=true` without either evicting the other."*

### 3.2 Precedent — amendment #28 did Path B

Amendment #28 (workspace-identity-routed-first-run) closed the
state-file-routing sibling of this family **without naming a spec
objective**. It framed itself as an ODD §4 re-extension of AC6 (plan
doc §11, research doc §6) and satisfied §2.5 by mapping every new
code path to the new ACs AC10–AC14. That precedent could be read two
ways:

1. As establishing that the workspace-identity family can land via
   amendment-chain re-extension without a spec amendment.
2. As itself a CLAUDE.md §operational-caution violation that the
   owner may want to retroactively correct (either by backing AC10–
   AC14 with a spec addendum, or by accepting the amendment-chain
   precedent as the operational norm for workspace-identity
   hazards).

Owner rules (D1). The research halts short of recommending either —
CLAUDE.md §operational-cautions is explicit that *the assistant* is
obliged to halt here, but the owner's judgment governs whether to
interpret that as Path A or Path B in the specific case of
workspace-identity hazards.

---

## 4. Port-origin trace — where 8765 is configured and who reads it

Static analysis only (authority bound: no running probe, no
launchctl). Grep of the canonical tree for literal `8765` and the
env-var names yields the following call-graph:

### 4.1 Authoritative source of the port value

`memory-system/src/service.py:96-97`:

```python
host = os.environ.get("GRAPHITI_SERVICE_HOST", "127.0.0.1")
port = int(os.environ.get("GRAPHITI_SERVICE_PORT", "8765"))
```

This is where the port is *read at service-process start*. Everything
else either (a) writes into these env vars, or (b) reads a config
file for a second copy of the value to construct health-probe URLs.

### 4.2 Who writes the env vars into the sidecar's process env

**Today: nobody, in the non-test path.** The launchd plist template at
`workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py:488-509`
defines the `EnvironmentVariables` dict as:

```xml
<key>EnvironmentVariables</key>
<dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
```

No `GRAPHITI_SERVICE_PORT`, no `GRAPHITI_SERVICE_HOST`. The in-tree
plist at `memory-system/launchd/com.pos-v2.memory-graphiti.plist:39-43`
is the same shape — a reference plist checked into the component, not
the templated one workspace-bootstrap renders at first-run. Both leave
the sidecar reading service.py defaults.

Test-only: `memory-system/tests/test_service.py:334-335` sets both
env vars via `monkeypatch.setenv`. Production-path processes don't see
either variable.

**Inference flag 1 (§9).** A `memory-system/.env.example:30-31` file
exists showing `GRAPHITI_SERVICE_HOST=127.0.0.1` and
`GRAPHITI_SERVICE_PORT=9876` (note: *9876*, not 8765). Whether this
is a stale example, a pending-use template, or a marker that a local
dev workflow picks it up through some mechanism I haven't traced is
unclear from static analysis alone. If `.env.example` is consumed by
something (dotenv loader inside service.py? a dev shell-sourcing
pattern?), the whole port-wiring story changes. Grep of `service.py`
for `dotenv`, `load_env`, `.env` returns zero matches — the file
appears unconsumed, but flagging for owner challenge.

### 4.3 Who reads the port *value* separately (health-probe paths)

Four independent readers:

1. **`workspace-bootstrap/src/workspace_bootstrap/adapters/memory_system.py:64`**
   reads `port` from `~/.pos/memory.yaml` (fallback 8765), constructs
   `url = f"http://{host_}:{port}{health_path}"`, and probes `/health`
   before declaring the sidecar healthy. This adapter **does** carry
   a per-workspace config read path (via `host.config_dir`), but the
   scaffolded `memory.yaml` hardcodes `port: 8765` in every workspace
   — see 4.4 below. The adapter *could* respect a per-workspace port
   if one were written in; today it doesn't observe a difference
   because both workspaces scaffold the same value.

2. **`workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py:204`**
   writes the `_MEMORY_YAML` block into `<host.config_dir>/memory.yaml`
   during first-run. The block hardcodes `port: 8765`. This is the
   scaffold that every workspace's first-run produces — identical
   across workspaces.

3. **`first-run-inventory.yaml:75`** declares `port: 8765` in the
   `services:` block. Read by
   `hands-off-lifecycle/hooks/first_run_helper.py` via the
   stdlib-only YAML subset parser (per file header comments). This
   file is checked into the repo and shared across workspace clones —
   two workspaces carry byte-identical copies, both declaring 8765.

4. **`orchestrator/scripts/pos_session_start.py:71`** declares
   `port: int = 8765` as the probe default in `probe_memory()`. This
   is the SessionStart-hook probe that confirms the memory sidecar is
   up. Again: hardcoded default; not parameterised by workspace.

### 4.4 Who "owns" the port value (responsibility surface)

Three candidate owners, mapped to the seam each controls:

| Owner | Seam it controls | Port lives where in that seam |
|---|---|---|
| **memory-system** (sealed) | `service.py` reads env → binds port at launch. | `os.environ.get("GRAPHITI_SERVICE_PORT", "8765")`. Also `launchd/com.pos-v2.memory-graphiti.plist` (reference, not templated). |
| **workspace-bootstrap** (sealed) | Renders plist template + writes `~/.pos/memory.yaml` scaffold + runs memory-system adapter probe. | Plist template `EnvironmentVariables` dict (does not set port). `_MEMORY_YAML` block (hardcodes 8765). `adapters/memory_system.py` config read (accepts `cfg.get("port")`). |
| **hands-off-lifecycle** (sealed) | Reads `first-run-inventory.yaml` during first-run-helper's phase-4b health poll. | `first-run-inventory.yaml:75` — workspace-shared declaration of `port: 8765`. |

No component **uniquely** owns the port. The value is materialised in
three places (env-var default, scaffolded `memory.yaml`, inventory
YAML) and read by four independent readers. The port is a
cross-component convention rather than a single-owner seam.

**Inference flag 2 (§9).** Whether this is "distributed convention"
(many consumers agreeing on a well-known default) or "accidental
duplication" (a centralising refactor is overdue) is a judgment call
the owner should rule on. Solution shapes in §7 differ in whether
they centralise or leave the duplication intact.

---

## 5. How amendment #6 and amendment #28 scoped their fixes

### 5.1 Amendment #6 — namespaced-labels-and-bootout

**Component reach:** multi-component — `workspace-bootstrap` +
`hands-off-lifecycle`.

**Seam touched:** service-manager-facing surface only — label
derivation (`workspace_slug`), plist-template parameterisation
(`{label}` substitution in `_LAUNCHD_TEMPLATES`), bootout-before-
bootstrap sequencing in `ServiceManagerRunner.bootstrap`. The seam is
the boundary between workspace identity (basename-derived slug) and
the service-manager identity (launchd `Label` key).

**AC naming style:** AC1 (slug derivation), AC2 (macOS plist naming),
AC4 (bootout sequencing), AC5 (stale-path replacement), AC6
(multi-workspace coexistence), AC7 (health-poll targets computed
labels), AC8 (unrepresentable slug refused structurally).

**Explicit known limitation (proposal §5 #3):** *"No collision
detection. Two distinct paths producing the same slug (e.g.
`/a/pos-v2` and `/b/pos-v2`) will collide on the service label.
Collision detection requires persistent state across workspaces and
is out of scope; treat as known limitation."* The port-collision
hazard this research addresses was **not in amendment #6's scope at
all** — amendment #6 solved *label* identity, not *service-endpoint*
identity.

**Classification:** amendment #6 touched the workspace-identity →
launchd-label seam. Port binding lives at a different seam
(sidecar-process → bound-network-endpoint). Same family of
workspace-identity hazards; different seam.

### 5.2 Amendment #28 — workspace-identity-routed-first-run

**Component reach:** single-component — `hands-off-lifecycle` only.

**Seam touched:** state-file layout and dispatcher-routing logic in
`hooks/first_run_state.py` + `hooks/first_run_dispatch.py`. The seam
is the boundary between workspace identity and persisted first-run
state.

**AC naming style:** AC10 (end-to-end multi-workspace dispatch,
explicitly re-extended from AC6 per ODD §4), AC11 (state carries
workspace identity), AC12 (self-workspace recognition preserved),
AC13 (corrupt state → fresh-spawn), AC14 (silent-death diagnosis per
workspace).

**Classification:** amendment #28 touched the workspace-identity →
persisted-state-file seam. Port binding lives at a third seam
(sidecar-process → bound-network-endpoint). Same family; different
seam.

### 5.3 Where port binding sits in the family

Family: **workspace-identity hazards** — each hazard is a failure of
one workspace's identity to route correctly through a
cross-workspace-shared surface.

| Seam | Shared surface | Identity-enforcement mechanism | Closed by |
|---|---|---|---|
| launchd labels | `~/Library/LaunchAgents/` namespace | Basename-derived slug in label string | Amendment #6 (label naming) |
| first-run state | `~/.pos/first-run.state` (pre-#28) | workspace_root field + path (post-#28) | Amendment #28 (per-workspace state) |
| **memory-sidecar port** | **`127.0.0.1:*` port space on the host** | **none today — hardcoded 8765** | **this research** |
| launchd label slug collision | same-basename workspaces → same slug | none today | Idea 9 (open) |

The port-binding seam is the third sibling. It is distinct from the
first two because:

- **Label seam** is namespaced (labels are arbitrary strings, the
  slug just needs to be appended).
- **State-file seam** is namespaced (filesystem paths are a naturally
  hierarchical namespace; routing by workspace-root path is
  structural).
- **Port seam** is the first sibling that fights over a *shared
  finite resource* — the IPv4 localhost port number space. Two
  workspaces' identities must resolve to *different* elements of
  that shared resource; "just append the slug" is not an option (a
  port is a uint16, not a string).

This difference shapes §7's candidate solutions. It also echoes the
`namespaced-labels-and-bootout` proposal's §5 #3 inference:
slug-collision is a real hazard at the label seam because **labels
draw from a slug-derived namespace**; ports don't even have that
partial protection — every workspace converges on 8765 regardless of
slug.

### 5.4 Is a new seam required, or does port-scoping ride an existing one?

Two options exist, and §7's solution shapes split on which seam they
use:

- **S1 rides the workspace-bootstrap → memory-system config seam**
  already established: `memory.yaml`'s `port` field (the field exists
  at `adapters/memory_system.py:13`, is read at line 64, and is
  documented as a config field). The scaffold currently writes 8765
  into every workspace's `memory.yaml`; S1 changes the scaffold (and
  the adapter's plist rendering if env-var-based) so each workspace
  gets a *different* port in its `memory.yaml`, and the value
  propagates to the sidecar.

- **S2 introduces a new runtime-probing seam** inside the sidecar
  process (probe for a free port, write the bound value back to
  `memory.yaml`, the workspace-bootstrap adapter re-reads before
  probing health).

- **S3 introduces a new first-run-scaffold seam** — a deterministic
  port-derivation function `workspace_port(slug: str) -> int`, wired
  at scaffold-time, analogous to `workspace_slug`.

- **S4 retires the port seam entirely** and switches transport to
  unix-domain sockets (paths under the workspace tree; the path seam
  is already structurally workspace-scoped).

---

## 6. Relevant sealed-component surfaces (what any fix must respect)

### 6.1 Memory-system seal integrity

- `memory-system/tests/test_no_sealed_amendments.py` is the seal-diff
  test. BASELINE advances when a new amendment opens memory-system;
  SEAL_COMMIT sidecar is at `memory-system/tests/SEAL_COMMIT`.
- Amendment #24 (memory-system-mcp-migration) was the most recent
  opening of memory-system's surface; it established the env-var
  contract `GRAPHITI_SERVICE_HOST` / `GRAPHITI_SERVICE_PORT` as the
  public interface for transport binding (AC24.6 in
  `amendment-24-memory-system-mcp-migration.md:92-99`). The env-var
  contract is the stable seam — any fix that writes into these
  variables composes without reopening memory-system's contract.

### 6.2 Workspace-bootstrap seal integrity

- `workspace-bootstrap/tests/test_no_sealed_amendments.py` is its
  seal-diff test.
- The `memory_system` adapter lives inside workspace-bootstrap's
  package (`workspace-bootstrap/src/workspace_bootstrap/adapters/
  memory_system.py`) and the plist template lives in
  `first_run_scaffold.py`. Both edits land under
  `workspace-bootstrap/` and require workspace-bootstrap's BASELINE
  to advance if touched.

### 6.3 Hands-off-lifecycle seal integrity

- `hands-off-lifecycle/tests/test_cross_cutting.py` has a frozen
  BASELINE per amendment #23 (§10.1 of `odd-in-pos.md`). The
  allowed_prefixes tuple must widen if a new file surface lands
  inside hands-off-lifecycle.
- `first-run-inventory.yaml` (repo-root) is not under any sealed
  component's `src/` tree — it is a workspace-top-level config file
  consumed by hands-off-lifecycle hooks. Edits to it may require
  hands-off-lifecycle's allowed_files widening per
  `pos-amend` manifest.

### 6.4 Cross-component amendment risk (halt-trigger #2 scan)

- **S1 (per-workspace config)** — minimally requires
  workspace-bootstrap edit (scaffold the per-workspace port) and
  may require memory-system edit (if the env-var contract needs
  changing, which amendment #24 AC24.6 already secured, so probably
  no). Possibly touches `first-run-inventory.yaml`
  (hands-off-lifecycle allowed_files). Two-component amendment at
  minimum if env-vars are used; three-component if inventory is
  edited. Precedent: amendment #6 ran as a two-component amendment.

- **S2 (runtime probe)** — memory-system edit (service.py probes) +
  workspace-bootstrap edit (adapter reads the bound port after
  probe). Two-component. Additional concern: writing the bound port
  back requires a new IPC between the sidecar and the adapter
  (file-write-then-reread, or a `/health` response-field extension).

- **S3 (deterministic first-run port)** — workspace-bootstrap edit
  (scaffold derives port from slug). May also require
  hands-off-lifecycle edit (first-run-inventory.yaml templating).
  And memory-system edit if the env-var contract is the propagation
  mechanism. Two-to-three-component.

- **S4 (unix socket)** — memory-system edit (service.py binds socket
  instead of port) + workspace-bootstrap edit (adapter probes unix
  socket; plist template changes WorkingDirectory / arg layout if
  needed) + hands-off-lifecycle edit
  (`orchestrator/scripts/pos_session_start.py:probe_memory` changes
  from HTTP-port to HTTP-over-unix — orchestrator is another sealed
  component). Potentially four-component. Also: FastMCP's
  streamable-HTTP transport is the landed transport per amendment
  #24; switching to unix-domain sockets may not be supported by the
  transport at all — an empirical question outside this research's
  authority bound.

**Halt-trigger #2 assessment:** every shape touches ≥2 sealed
components; S4 potentially touches 4. Owner rules whether to
authorise a multi-component amendment (precedent exists — amendments
#6 + #28 both touched multiple components at the component-grouping
boundary) or to restructure the fix into single-component shape.

---

## 7. Candidate solution shapes

Six shapes, enumerated without recommendation. Each is named by its
seam choice. `odd-methodology.md` §5.1 (structural-over-advisory) and
CLAUDE.md Lens-1 (Claude-leverage-first) are applied as evaluation
lenses but not as tie-breakers.

### 7.1 S1 — per-workspace port written through `memory.yaml`

**Shape:** the first-run-scaffold writes a workspace-unique port into
each workspace's `~/.pos/memory.yaml` (e.g., `port:
<slug-derived-or-assigned>`), and the plist template's
`EnvironmentVariables` dict gains `GRAPHITI_SERVICE_PORT` set to that
same value. Adapter and health-probe paths already read
`memory.yaml`; no new readers needed. The env-var contract is the
sidecar's entry point (amendment #24 AC24.6).

**Owning component:** workspace-bootstrap (primary; scaffold + plist
template + adapter). memory-system surface untouched if env-var
contract holds. hands-off-lifecycle touched only if
`first-run-inventory.yaml`'s `port` field is removed or templated.

**Sealed-component amendment cost:** 1 component (workspace-bootstrap)
+ possibly hands-off-lifecycle if inventory YAML changes. Two-
component amendment at most.

**Compatibility cost:** low. Every existing reader (adapter probe,
session-start probe, inventory) continues to read 8765 unless
upgraded. Workspaces first-run'd before the fix have `port: 8765` in
`memory.yaml`; post-fix scaffold writes a workspace-unique value.
Migration shape: same as amendment #28's pre-existing state-file
handling — the old file stays, the new one uses the new layout; no
forced migration.

**Compose-with-existing-primitives shape:** high. The `port` field on
`memory.yaml` already exists. The env-var contract on the sidecar
already exists. The `EnvironmentVariables` dict on the plist template
already exists (with `PYTHONUNBUFFERED`). The fix wires three
existing surfaces together.

**Identity-enforcement mechanism:** port assignment derives from slug
(deterministic, hash-based) OR from an ordered workspace registry
(`~/.pos/ports.yaml` or similar). Slug-derivation inherits Idea 9's
slug-collision hazard (same slug → same port). Registry-based
eliminates that hazard but introduces persistent cross-workspace
state — a sibling concern to the one `docs/FUTURE_IDEAS.md`
Idea 9 §5.1 names for labels.

**Claude-leverage evaluation (Lens 1):** no Claude primitive
obviously applies. Claude's MCP transport doesn't provide a port-
allocation service; this is a vanilla macOS launchd/BSD-sockets
concern.

### 7.2 S2 — auto-probe at bind-time, write back bound port

**Shape:** `service.py` attempts to bind its configured port (8765
default); on `EADDRINUSE`, probes upward (8766, 8767, …) until a free
port is found; writes the bound port to a known location (e.g.,
`<workspace>/memory-system/data/bound_port`); the adapter + session-
start probe read this file before probing health.

**Owning component:** memory-system (primary — bind-loop +
write-back), workspace-bootstrap (adapter reads the file),
hands-off-lifecycle / orchestrator (`pos_session_start.py` reads the
file).

**Sealed-component amendment cost:** 2–3 components. memory-system's
env-var contract (amendment #24 AC24.6) tightens to "honours the env
var, else probes" — an extension, not a replacement, but the
contract extension needs AC backing under ODD §4.

**Compatibility cost:** medium. Workspaces that currently rely on 8765
(none observed in the codebase outside test fixtures and the
sidecar's own default) continue working. First workspace booted gets
8765 by luck; second gets 8766 by probe. Order-dependence is a
property the owner must rule acceptable or not.

**Compose-with-existing-primitives shape:** medium. Introduces a new
inter-component file (`bound_port`) the adapter must read before
health-probing. The file becomes a new workspace-local artefact; its
atomic-write semantics need to match amendment #28's atomic-rename
precedent.

**Identity-enforcement mechanism:** *not identity-based at all* —
first-come-first-served. The workspace that boots first gets the
lower port; the other gets whatever's free. That's a property the
owner should examine — it breaks the "structural" flavour of the
workspace-identity family (structural = the identity is in the
resource's name, not in run-order).

**Claude-leverage evaluation:** no Claude primitive applies.

### 7.3 S3 — deterministic port derivation at first-run

**Shape:** introduce `workspace_port(slug: str) -> int` alongside
`workspace_slug`. Derivation: a hash of the slug mapped into a
reserved range (e.g., 8765 + `hash(slug) % 100`, or a dedicated
49152–65535 ephemeral-range window). The scaffold writes the derived
port into `memory.yaml` and the plist's `EnvironmentVariables`.

**Owning component:** workspace-bootstrap (pure — lives alongside
`workspace_slug`). memory-system unchanged (reads the env var;
amendment #24 AC24.6 suffices). hands-off-lifecycle's inventory YAML
either inherits the function's output or drops the `port` field and
routes through `memory.yaml`.

**Sealed-component amendment cost:** 1 component primarily
(workspace-bootstrap); possibly hands-off-lifecycle if inventory
changes. Same shape as amendment #6's `workspace_slug` addition.

**Compatibility cost:** low. Pre-existing `memory.yaml` files with
`port: 8765` stay — the scaffold only writes new workspaces. Existing
workspaces' ports don't change unless re-scaffolded.

**Compose-with-existing-primitives shape:** very high. The pattern
parallels amendment #6's `workspace_slug` exactly:
- `workspace_slug(workspace_root: Path) -> str` was added as a pure
  function with structural refusal for unrepresentable cases
  (AC8: `WorkspaceSlugUnrepresentableError`).
- `workspace_port(slug: str) -> int` would be a pure function. Its
  structural refusal case: two workspaces whose slug-derived ports
  collide (same slug → same port; the Idea 9 slug-collision hazard
  manifests at the port seam too).

**Identity-enforcement mechanism:** slug-derived → structural in the
slug, but inherits the Idea 9 slug-collision hazard: two workspaces
with the same basename produce the same slug and the same port. The
hazard is identical to (and a manifestation of) the open Idea 9
concern.

**Claude-leverage evaluation:** no Claude primitive applies.

### 7.4 S4 — retire the port; switch to unix-domain sockets

**Shape:** memory-system binds a unix-domain socket at
`<workspace>/memory-system/data/graphiti.sock` (or `~/.pos/memory-
<slug>.sock`) instead of a TCP port. Adapter and session-start probes
use `AF_UNIX` connects. The port space is never shared; paths are
per-workspace (or slug-scoped).

**Owning component:** memory-system (transport change) +
workspace-bootstrap (adapter) + hands-off-lifecycle / orchestrator
(`pos_session_start.py`).

**Sealed-component amendment cost:** 3–4 components. Likely the
largest amendment in the table.

**Compatibility cost:** highest. FastMCP's streamable-HTTP transport
is what amendment #24 landed; whether FastMCP supports
unix-domain-socket transport at all is not verified in this static
analysis (the `mcp` package's transport surface was not inspected as
part of this research). **Inference flag 4 (§9).**

**Compose-with-existing-primitives shape:** low-medium. The
filesystem-path seam is workspace-scoped by construction (the
workspace path *is* the namespace), but the transport change ripples
through every client that expected HTTP-over-TCP.

**Identity-enforcement mechanism:** structural — the path *is* the
workspace identity. Matches amendment #28's Option C (workspace-local
state) in philosophy: `structural-over-advisory` par excellence.

**Claude-leverage evaluation:** Claude's MCP specification does
support stdio transport for MCP servers natively; whether Claude
Code's MCP client supports unix-domain-socket transport for a
streamable-HTTP server is a documentation question outside this
research's authority bound. Flag 4 cross-references.

### 7.5 S5 — host-local loopback-address allocation (`127.0.0.2`, …)

**Shape:** each workspace binds on a different loopback address in
the 127.0.0.0/8 block (`127.0.0.1` for workspace A, `127.0.0.2` for
workspace B, …) while keeping port 8765. The host field, not the port
field, carries workspace identity.

**Owning component:** workspace-bootstrap (scaffold writes per-
workspace `host` into `memory.yaml`) + plist template's
`GRAPHITI_SERVICE_HOST`. memory-system honours the env var.

**Sealed-component amendment cost:** 1–2 components. Mechanically
very similar to S1.

**Compatibility cost:** medium. Loopback-address aliasing requires
`ifconfig lo0 alias 127.0.0.2 up` on macOS (not automatic);
persistent aliasing across reboots needs additional plumbing. The
"user doesn't configure" value proposition bleeds out.

**Compose-with-existing-primitives shape:** medium. The host env var
already exists; only the value changes. Similar seam to S1 but on the
address field.

**Identity-enforcement mechanism:** slug-derived address → structural,
but inherits slug-collision + adds an admin-setup step (loopback
alias creation). Breaks the `hands-off-lifecycle` spirit — sessions
can't come up clean on a reboot until loopback aliases are
re-established.

**Claude-leverage evaluation:** none applies.

### 7.6 S6 — refuse concurrent workspaces structurally

**Shape:** the first-run scaffold (or the SessionStart hook) detects
that another pos-v2 workspace on the host already has its memory
sidecar running and **refuses to install** the second workspace,
pointing the user at a disambiguation path (workspace rename,
explicit port override, run-only-one policy).

**Owning component:** hands-off-lifecycle (first-run detection) or
workspace-bootstrap (install-time detection) — same dual-owner
tension Idea 9 names.

**Sealed-component amendment cost:** 1 component (either side); the
"refuse" path is a structural check + diagnostic.

**Compatibility cost:** high — refuses a valid current workflow
(pos3 ↔ ivers-corp-pos-v2 parallel operation is what Luke does
today). Changes the multi-workspace story from "supported with some
limits" to "explicitly one-at-a-time with disambiguation ritual."

**Compose-with-existing-primitives shape:** low. Introduces a new
cross-workspace detection surface.

**Identity-enforcement mechanism:** refusal — workspace identity
continues to fail to disambiguate, but the failure is loud and
redirected.

**Claude-leverage evaluation:** none applies. This shape is a
retreat, not a fix.

### 7.7 Summary table

| Shape | Owning component(s) | Amendment cost | Compat cost | Compose | Identity mech |
|---|---|---|---|---|---|
| S1 per-workspace `memory.yaml` port | workspace-bootstrap (+ hands-off-lifecycle) | 1–2 | low | high | slug-derived or registry-assigned |
| S2 auto-probe at bind | memory-system + workspace-bootstrap + hands-off-lifecycle | 2–3 | medium | medium | run-order (not structural) |
| S3 deterministic `workspace_port(slug)` | workspace-bootstrap (+ hands-off-lifecycle) | 1–2 | low | very high | slug-derived (inherits Idea 9 hazard) |
| S4 unix-domain socket | memory-system + workspace-bootstrap + hands-off-lifecycle + orchestrator | 3–4 | high | low-medium | path-structural |
| S5 loopback-address alias | workspace-bootstrap (+ hands-off-lifecycle) | 1–2 | medium | medium | slug-derived address (+ admin step) |
| S6 structural refusal | hands-off-lifecycle or workspace-bootstrap | 1 | high (retreat) | low | refusal |

---

## 8. Relationship to Idea 9 and amendment #28

**Idea 9 (slug-collision detection, `FUTURE_IDEAS.md` §"Idea 9"):**
amendment #28 expanded Idea 9's scope (in its 2026-04-23 update) to
cover state-file routing; the slug-collision hazard at the
launchd-label layer remains open. The port-collision hazard this
research addresses is a new third scope for Idea 9: shared-finite-
resource collision at the TCP-port layer. Owner may choose to:

1. Widen Idea 9 again (three scopes: label slugs, launchd-label slug
   collision, port binding) and treat this research as the
   port-scope research cycle.
2. Spin a new Idea (Idea 13 — workspace-concurrent service port
   scoping) and keep Idea 9 focused on label-slug collision
   specifically.
3. Address ports and slug-collision together (S3's deterministic
   port derivation inherits the slug-collision hazard, so solving
   one partially solves the other).

Owner decision (D4 in §10).

**Amendment #28's ODD §4 framing:** AC10–AC14 re-extended AC6 (from
amendment #6) without a new spec objective. Amendment #28's plan doc
§8 also contained a `FUTURE_IDEAS.md` catalogue-update line as part
of the amendment's own doc surface. If Path B is chosen (D1) the same
shape applies here — a port-scoping amendment would add AC15 (or
whatever the next AC number is in the amendment-chain sequence) and
update Idea 9 accordingly.

---

## 9. Flagged inferences (owner may challenge)

1. **`memory-system/.env.example` consumption is unclear.** The file
   declares `GRAPHITI_SERVICE_PORT=9876`, not 8765, but no loader in
   `service.py` reads it. Possibilities: (a) stale artefact;
   (b) consumed by a dev-time `source .env` pattern I haven't
   traced; (c) pending-use template for a future amendment. Solution
   shapes assume it is **not** consumed at runtime; if it is,
   §4.2's "nobody writes the env vars" statement is wrong and the
   whole trace needs revising.

2. **Centralise vs accept duplication.** §4.4 observes the port value
   is materialised in three in-tree places (service.py default,
   `_MEMORY_YAML` scaffold, `first-run-inventory.yaml`) and read by
   four places. Whether that is a refactor target or accepted
   convention is an owner call the solution shapes do not
   pre-resolve. Pointing out that amendment #28 observed analogous
   distribution at the state-file layer and chose centralisation
   (Option C — single per-workspace state file).

3. **ODD §2.5 compliance for solution shapes.** Every shape lands
   code handling a case (multi-workspace coexistence) that does not
   have a spec-v1.0/v1.1/v1.2 objective. §3.1 names the tension. If
   the owner rules Path B (amendment-chain re-extension without
   spec amendment), the code backs to the newly-authored AC. If
   Path A (spec amendment first), the code backs to the new spec
   clause. If neither path is acceptable, none of the shapes can
   land as a sealed-component amendment — the work reframes as
   dev-discipline (CLAUDE.md edits, CDC text, tools/ entries) and
   the symptom stays open.

4. **S4 (unix-domain socket) — FastMCP transport support unknown.**
   Amendment #24 landed FastMCP streamable-HTTP transport. Whether
   FastMCP supports unix-domain-socket transport for MCP (or only
   TCP HTTP) is not verified in this static analysis. The owner
   should not pick S4 without empirical verification; the `mcp`
   package documentation is the source.

5. **Registry-based port assignment (S1 / S3 variant) introduces
   persistent cross-workspace state.** `~/.pos/ports.yaml` or
   equivalent is a new singleton artefact that every workspace
   reads and writes. That is the same kind of shared-state surface
   amendment #28's Option C deliberately avoided in favour of
   workspace-local files. The owner may want to avoid it for the
   same reason.

6. **`workspace_slug` already exists; `workspace_port` is a
   plausible sibling.** S3's naming parallels amendment #6's. This
   research doc deliberately does not invent the function's exact
   signature or derivation formula — that is method, and the
   builder's call under ODD §1.1. Flagging that the owner may have
   views on whether slug-derived-hash vs slug-ordinal-position vs
   slug-as-string-into-a-hash-table is the right derivation.

7. **Whether amendment #28 itself was CLAUDE.md-compliant.** Same
   pattern as this proposed work: no spec objective named;
   re-extended AC6 under ODD §4; CLAUDE.md §operational-cautions
   was in force at the time the amendment landed. The owner may
   want to rule retroactively on whether #28's compliance strategy
   is acceptable going forward for the whole workspace-identity
   family, which would make Path B (in §3.1) the settled default
   and remove the ambiguity for this amendment.

---

## 10. Owner decisions required (before a plan can be authored)

**D1 — spec path or amendment-chain path?** Per §3.1 and flag #3:

- D1.A — author a spec v1.x addendum naming multi-workspace service
  isolation as a foundational objective, then author the amendment
  against that new objective.
- D1.B — accept amendment #28's precedent, treat the port-binding
  fix as a §4 re-extension of AC6 from amendment #6, and land
  without a spec amendment.
- D1.C — rule that neither path is acceptable; the symptom reframes
  as dev-discipline (run one workspace at a time, document the
  constraint in CLAUDE.md). No code lands.

**D2 — owning-component boundary.** Given §6.4 shows every shape
touches ≥2 sealed components, and CLAUDE.md does not forbid multi-
component amendments outright (amendments #6 + #28 establish precedent
for two-component amendments):

- D2.A — authorise a multi-component amendment (2–4 components
  depending on shape chosen in D3).
- D2.B — insist on single-component; then only a shape that fits
  single-component scope is admissible (S3 in a single-component
  configuration might come closest, and only if
  `first-run-inventory.yaml`'s port stays untouched).

**D3 — shape choice from §7.** The owner picks one shape (or one
composition of shapes) for the plan-authoring phase. Recommendation
withheld per task scope; the table at §7.7 is the decision surface.

**D4 — Idea 9 catalogue posture.** Per §8:

- D4.A — widen Idea 9 to cover ports explicitly (third scope).
- D4.B — spin a new Idea (Idea 13) for port scoping.
- D4.C — roll ports into a combined "workspace-identity for
  finite-resource sharing" idea along with slug-collision at the
  label layer.

**D5 — flag #1 inference check.** Is `.env.example` consumed at
runtime anywhere? If yes, §4.2 and §4.4 need correcting.

**D6 — flag #7 retroactive ruling.** Does amendment #28's
"re-extend AC6 without a spec amendment" precedent become the
settled default for the workspace-identity family? Yes simplifies
D1 to D1.B by default; no forces D1 to weigh against amendment
#28's own legitimacy.

---

## 11. What would NOT be in scope for the eventual plan

Following `odd-methodology.md` §2.5 (no non-objective code):

- Loopback alias setup helpers (admin-level concern; outside any
  current objective).
- A port-reservation registry at OS-level (`ephemeral-port-
  registry` kind of surface) — too broad for the stated problem.
- A general "service discovery" layer — Claude-leverage Lens 1
  prefers leaning on existing primitives; service-discovery is not
  a Claude primitive and is broader than the port-binding defect.
- Any retrofit of already-scaffolded `memory.yaml` files in
  existing workspaces (amendment #28's non-migration pattern
  applies: old file stays; new scaffold writes new value; no
  forced migration).

---

## 12. Primary-source citations

- `memory-system/src/service.py:96-97` — port-read, authoritative
  source.
- `memory-system/launchd/com.pos-v2.memory-graphiti.plist:39-43` —
  reference plist; no `GRAPHITI_SERVICE_PORT` env var.
- `memory-system/.env.example:30-31` — example env with port 9876
  (inference flag 1).
- `memory-system/tests/test_service.py:334-335` — test-only env-var
  set.
- `workspace-bootstrap/src/workspace_bootstrap/adapters/memory_system.py:13,64`
  — adapter config read surface.
- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py:200-208`
  — `_MEMORY_YAML` scaffold; port 8765 hardcoded.
- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py:488-509`
  — plist template; `EnvironmentVariables` dict lacks port.
- `first-run-inventory.yaml:75` — workspace-shared `port: 8765`.
- `orchestrator/scripts/pos_session_start.py:71` —
  `probe_memory(port=8765)` default.
- `docs/archive/component-research/namespaced-labels-and-bootout/proposal.md`
  — amendment #6 scope, §3 ACs, §5 #3 known-limitation.
- `docs/plans/amendment-28-workspace-identity-routed-first-run.md`
  — amendment #28 scope, §4 AC10–AC14 re-extension framing, §11 ODD
  compliance note.
- `docs/plans/research/amendment-28-workspace-identity-routed-first-run-research.md`
  — §4 "Why this is distinct from Idea 9", §5 options A/B/C
  precedent that §7 mirrors.
- `docs/FUTURE_IDEAS.md` Idea 9 — slug-collision; 2026-04-23
  update noting state-routing closed, label-slug still open.
- `docs/plans/amendment-24-memory-system-mcp-migration.md:92-99`
  — AC24.6, env-var contract `GRAPHITI_SERVICE_HOST` /
  `GRAPHITI_SERVICE_PORT`.
- `docs/spec/pos-v2-objectives-spec.md` — survey (zero
  matches for workspace-level service isolation).
- `docs/odd-methodology.md` §2.5, §4, §5.1 — governing rules.
- `CLAUDE.md` §"Operational cautions" — spec-objective-first rule.

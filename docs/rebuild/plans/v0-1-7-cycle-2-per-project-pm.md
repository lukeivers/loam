# v0.1.7 Cycle 2 — per-project PM persona (NEW component)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-04.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md` (§3 Surface #7 + §5 AC.PPM.* + §6 Cycle 2).
**Predecessor (Cycle 1 seal):** `3aa20dd` — v0.1.7 Cycle 1 seal (5 subagent personas + symlink registration).
**BASELINE candidate (this cycle's source-edit commit will land on top of):** `3aa20dd`.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-7-cycle-2-status-2026-05-04.md`.
**Quality bar:** WOW Eric. No partial features. All 6 smoke dimensions exercised. Every release-note promise tested.

---

## §1. Summary / TL;DR

Cycle 2 ships **one NEW component** under `framework/per-project-pm/` — a workspace-scoped
project-manager persona. Per the FIDRAFT entry (committed `0f70c06` + `ccd48d4`),
each project has its own PM scoped to workspace; harness-general (not dev-only).
PM holds project-domain state; persona pulls state-of-world on demand; PM surfaces
decisions needing user attention; PM auto-loads when persona begins work in that
project's workspace.

**Single-component fence** on `framework/per-project-pm/`. Plan-before-code lands
this sub-plan + manifest before any source code.

**Scope split inside Cycle 2** (per parent §3 Surface #7 + §6 Cycle 2):
- **Cycle 2.a** — design-note + scaffold + contract.py (no runtime). Land FIRST as part of
  Cycle 2 BASELINE source-edit commit; design-note is the gate before runtime is authored.
  Halt-and-surface BEFORE 2.b if design surfaces a contradiction with M-FBM workspace-state
  shape OR if the path-convention in the parent plan needs adjustment.
- **Cycle 2.b** — runtime + loader + integration tests. Lands as the Cycle 2 source-edit
  commit's runtime portion (still single seal, single manifest).

**ACs delivered (per parent §5):** AC.PPM.{1..9} — component scaffold present; `PMContract`
+ `DecisionSurfacingPolicy` Pydantic models present + validate; `PMRuntime` loader resolves
workspace-state; `surface_next_question()` API; `enqueue_decision()` API; PM does NOT write
to M-FBM episode store; `PerProjectPMContribution` registers; design-note articulates
PM/M-FBM boundary.

**Out of scope (deferred to Cycle 4):** `record_response()`, `surface_next_questions_batch()`,
`require_owner_response`-blocking, `onboarding_mode` enforcement at the persona-side flow,
`audit_trail_floor` AC. Cycle 2 establishes the queue+API; Cycle 4 wires the user-facing flow.

---

## §2. F2 Ruthless Feedback — surfaced this turn before code lands

### F2.A — Path-convention deviation in parent plan (NOT a contradiction; a correction)

**The parent plan §3 Surface #3 places PM workspace-state at `<workspace>/.loam/pms/<pm-name>/`.**
The actual canonical convention per `framework/workspace-bootstrap/src/loam/workspace_bootstrap/workspace_paths.py:99`
is `<workspace>/workspace/.loam/<...>` — workspace-state lives under the
`WORKSPACE_STATE_SUBDIR = "workspace"` partition (D-migration D.2, amendment #63).
M-FBM at `framework/primary-persona/src/loam/primary_persona/file_memory.py:103-120`
uses `<workspace>/workspace/.loam/memory/`.

**Resolution (autonomous, in-cycle):** PM workspace-state lives at
`<workspace>/workspace/.loam/pms/<pm-name>/` — sibling of `<workspace>/workspace/.loam/memory/`.
This is NOT a contradiction with M-FBM; it adopts the same canonical convention so
PM and M-FBM live as siblings under the same workspace-state root. The HC#6
structural guard (`WorkspaceLayout` Pydantic validator) refuses
workspace-roots whose basename is `framework`; PM inherits that guarantee by
routing through the same `WorkspaceLayout` helper.

**Effect on Cycle 2:** the design-note + every code path that resolves the PM
workspace-state directory routes through `loam.workspace_bootstrap.workspace_paths.workspace_state_dir(workspace_root) / ".loam" / "pms" / pm_name`,
NOT through a hand-rolled `Path(workspace_root) / ".loam" / "pms"`. This is a
method-level decision under Cycle 2's scope; not an escalation.

### F2.B — `composes_with_skills` / `composes_with_agents` are advisory metadata at Cycle 2

The parent plan §3 Surface #4 names `composes_with_skills: list[str]` and
`composes_with_agents: list[str]` on `PMContract`. At Cycle 2 these are **advisory
declarations** — the contract carries them, validation accepts them, but the runtime
does NOT enforce or invoke them. Composition wiring (skill auto-load when PM activates;
subagent dispatch by handle) lands at v0.2.0+ when the PM-driven dispatch loop is wired.
Cycle 2 records the metadata so future runtimes can read it without re-authoring the
contract. This is named explicitly to prevent Cycle 2 from over-scoping into
composition-wiring.

### F2.C — Contribution wiring depth at Cycle 2

`PerProjectPMContribution` is published on `host.per_project_pm` per parent §3 Surface #7.
At Cycle 2, the contribution publishes a **factory** that lazily resolves a PM for a
named handle (`host.per_project_pm.runtime_for(pm_name)` returns a `PMRuntime` or
raises `PMNotFoundError`). The contribution does NOT eagerly load every PM at boot —
that would force every workspace to author a PM contract before running. Lazy resolution
matches the auto-load semantics ("PM auto-loads when persona begins work in that
workspace") without requiring PM authoring at workspace-bootstrap time.

### F2.D — `PMNotFoundError` is a normal not-found, not a fault

When `PMRuntime.from_workspace(workspace_root, pm_name)` is called for a PM that has
no `contract.yaml` yet, the contract is "not authored yet" — that's the empty-project
state, not a failure. Per parent §5 AC.PPM.4 the loader raises `PMNotFoundError` —
correct, but the dispatch surface (D1 cold-state smoke) interprets `PMNotFoundError`
as "the project hasn't been initialised" and returns an empty state-of-world snapshot.
Cycle 2 ships both: the named exception class (fail-loud at the loader boundary) AND
a `PMRuntime.empty_state_for(workspace_root)` helper that returns an empty `StateOfWorld`
without raising, so D1 can verify "expected shape on empty project" per dispatch.

### F2.E — Audit-log filename collision

The parent plan §3 Surface #3 shape `audit-log/<YYYY-MM-DD>-<seq>.yaml` is correct
in shape but the `<seq>` semantic was not specified. Cycle 2 fixes: `<seq>` is a
4-digit zero-padded monotonic counter scoped to (pm-name, date), reset to `0001` at
midnight UTC. Multiple writes in the same UTC day produce
`2026-05-04-0001.yaml`, `2026-05-04-0002.yaml`, etc. Counter is computed at write
time by reading the directory listing and incrementing the max suffix found
(stdlib only; no SQLite). Test asserts atomic increment under sequential writes.
Cycle 4 may switch to `record_response()` provenance which adds question_id keys.

---

## §3. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| Per-project PM-shape (contract, loader, runtime, surfacing) | `framework/per-project-pm/` (NEW component) | Per parent §3 Surface #7 + Eric synthesis G5: PM-shape is harness-general, not dev-specific. A hypothetical writer's PM uses the same machinery. |
| Decision-surfacing API (PM-side question batching + single-question-per-turn skeleton) | `framework/per-project-pm/src/loam/per_project_pm/` | PM is the question owner; surfacing protocol is PM-internal. Cycle 2 ships the queue+API; Cycle 4 ships the user-facing flow. |
| Workspace-local PM state (instance) | `<workspace>/workspace/.loam/pms/<pm-name>/` | Per F2.A — adopts canonical workspace-state convention; sibling of `<workspace>/workspace/.loam/memory/`. |
| Pydantic models (`PMContract`, `DecisionSurfacingPolicy`, etc.) | `framework/per-project-pm/src/loam/per_project_pm/contract.py` | Mirrors `framework/primary-persona/src/loam/primary_persona/contract.py:211` precedent. |
| Loader / runtime / surfacing (Cycle 2.b) | `framework/per-project-pm/src/loam/per_project_pm/{loader,runtime,surfacing}.py` | Mirrors split in primary-persona (loader.py + memory_consumer.py + ...). |
| Errors module | `framework/per-project-pm/src/loam/per_project_pm/errors.py` | Named exceptions per ODD §2.5: `PMNotFoundError`, `PMStateCorruptedError`. (`PendingResponseError` deferred to Cycle 4.) |
| Contribution class | `framework/per-project-pm/src/loam/per_project_pm/contribution.py` | Mirrors `plugins/dev-sdlc/src/loam/plugins/dev_sdlc/contribution.py` precedent. |
| Component design-note | `framework/per-project-pm/docs/design.md` | Per AC.PPM.9 — articulates PM/M-FBM boundary; harness-general design rationale. |
| Seal-test + sidecar | `framework/per-project-pm/tests/test_no_sealed_amendments.py` + `framework/per-project-pm/tests/SEAL_COMMIT` | Per amendment-22 ruling: NEW component lands seal-test + sidecar in same cycle. Pattern mirrors `plugins/loam-skills/tests/test_no_sealed_amendments.py`. |
| `framework/first-run-inventory.yaml` admission | edit `shared_venv.components` adding `per-project-pm` | NEW component must be installed by the shared venv at first-run. Universal-file admission per amendment #22 ruling #3. |

---

## §4. Halt-and-surface BEFORE build (recorded; no halt yet)

### Surface #1 (no halt — recorded; PM/M-FBM boundary)

PM owns project-domain decision/ratification state (decision queue + audit log + PM-held
state-of-world snapshot). M-FBM owns turn-grain episode memory (markdown files at
`<workspace>/workspace/.loam/memory/episodes/<workspace-slug>/<YYYY-MM-DD>/<turn-id>.md`)
and search-index. They DON'T duplicate: PM's audit-log records WHEN-and-HOW questions
were surfaced + responded; M-FBM's episode files record WHAT-the-persona-said in a turn.
A PM-mediated decision-surfacing event produces an audit-log entry; M-FBM's per-turn
markdown may CITE that audit-log path (provenance), but M-FBM does not own the entry.
The boundary is articulated in the design-note. **Halt-trigger:** if during build the
PM-state shape collides with an M-FBM convention (e.g., M-FBM's search index claims
the queue file as source-data), halt + surface.

### Surface #2 (no halt — recorded; workspace-identity primitive)

Per dispatch halt-trigger: "Per-project PM design surfaces that 'per-project' requires
a workspace-identity primitive that doesn't exist yet → halt + surface."

**Decision (autonomous):** "per-project" is workspace-scoped. The workspace-identity is
the workspace_root path (`<workspace>/workspace/.loam/pms/<pm-name>/`). The
`<pm-name>` is operator-authored at PM-creation time and stored in the contract's
`handle` field. Multi-PM-per-workspace is admitted by the directory shape (each PM at
`<workspace>/workspace/.loam/pms/<handle>/`). The default project's PM is operator-named;
common convention `<project-slug>-pm` (e.g., `eric-saas-pm`, `loam-self-pm`).

This DOES require a stable workspace-root identity, which the existing `WorkspaceLayout`
provides. No new primitive needed. **Halt-trigger discharged.**

### Surface #3 (no halt — recorded; `pyproject.toml` shape)

`framework/per-project-pm/pyproject.toml` declares:
- `[project] name = "loam-per-project-pm"`, `version = "0.1.0"`, `description = ...`,
  `requires-python = ">=3.13"`.
- `dependencies = ["pydantic>=2", "PyYAML>=6", "loam-workspace-bootstrap"]`.
  - `loam-workspace-bootstrap` for `WorkspaceLayout` + `BaseContribution` + `Phase`.
  - `PyYAML` for state.yaml + decision-queue.yaml + contract.yaml read/write.
  - `pydantic` for the contract models.
- `[project.optional-dependencies] test = ["pytest>=8.0"]`.
- `[project.entry-points."loam.bootstrap.contributions"] per_project_pm = "loam.per_project_pm.contribution:PerProjectPMContribution"`.
- `[tool.setuptools] package-dir = {"loam.per_project_pm" = "src/loam/per_project_pm"}`,
  `packages = ["loam.per_project_pm"]`.
- `[tool.pytest.ini_options] testpaths = ["tests"]`.

### Surface #4 (no halt — recorded; PM contract dataclass shape)

Per parent §3 Surface #4, with F2.B refinement (composes_with_* are advisory metadata):

```python
class PMContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    handle: str = Field(min_length=1)             # e.g., "eric-saas-pm"
    project_name: str = Field(min_length=1)       # e.g., "eric-saas"
    project_kind: Literal["dev", "writing", "research", "ops", "general"]
    owner_name: str = Field(min_length=1)         # owner's preferred name
    workspace_root: Path                          # absolute path PM is anchored to
    decision_surfacing_policy: DecisionSurfacingPolicy
    composes_with_skills: tuple[str, ...] = ()    # advisory; not enforced at Cycle 2
    composes_with_agents: tuple[str, ...] = ()    # advisory; not enforced at Cycle 2

    @field_validator("workspace_root")
    @classmethod
    def _absolute_path(cls, v: Path) -> Path:
        if not v.is_absolute():
            raise ValueError(f"workspace_root must be absolute, got: {v}")
        return v
```

`DecisionSurfacingPolicy`:

```python
class DecisionSurfacingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    onboarding_mode: bool = False             # Cycle 4 wires enforcement
    max_questions_per_turn: int = Field(default=1, ge=1)
    cool_down_seconds: int = Field(default=0, ge=0)
    require_owner_response: bool = True       # Cycle 4 wires enforcement
```

`extra="forbid"` rejects unknown keys at load (catches typos in operator-authored
contract.yaml). `frozen=True` matches the workspace-bootstrap `ContributionMetadata`
precedent (immutable at runtime); state mutation happens via `state.yaml`/`decision-queue.yaml`,
not via mutating the contract.

### Surface #5 (no halt — recorded; runtime API surface — Cycle 2 portion)

```python
class PMRuntime:
    """Workspace-scoped PM runtime; loaded via from_workspace()."""

    @classmethod
    def from_workspace(cls, workspace_root: Path, pm_name: str) -> "PMRuntime":
        """Load PM at <workspace>/workspace/.loam/pms/<pm_name>/.
        Raises PMNotFoundError if contract.yaml absent.
        Raises PMStateCorruptedError on schema mismatch."""

    @classmethod
    def empty_state_for(cls, workspace_root: Path) -> "StateOfWorld":
        """Return empty state-of-world (no PM authored)."""

    @property
    def contract(self) -> PMContract: ...

    @property
    def workspace_state_dir(self) -> Path:
        """<workspace>/workspace/.loam/pms/<handle>/"""

    def state_of_world(self) -> StateOfWorld:
        """Snapshot of current PM-held project state.
        Reads state.yaml + decision-queue.yaml; returns dataclass."""

    def enqueue_decision(self, question_text: str, *, provenance: str | None = None) -> int:
        """Append to FIFO decision-queue.yaml; return the enqueued position.
        Persists synchronously (no in-memory drift). Returns 1-based position."""

    def surface_next_question(self) -> SurfacedQuestion | None:
        """Consume head of FIFO queue. Returns SurfacedQuestion (text + provenance +
        queue_position + audit_path) or None when queue empty (empty is normal,
        not an exception). Writes audit-log/<YYYY-MM-DD>-<seq>.yaml with timestamp +
        question + queue-state-pre + queue-state-post."""
```

`StateOfWorld` (dataclass):

```python
@dataclass(frozen=True)
class StateOfWorld:
    pm_loaded: bool                   # True if PM contract found, False on empty
    handle: str | None                # PM handle, None on empty
    project_name: str | None
    queue_depth: int                  # decisions awaiting surfacing
    pending_questions: tuple[str, ...]  # text snapshot of pending queue
    last_surfaced_at: str | None      # ISO 8601, None if nothing surfaced yet
    workspace_state_dir: Path | None  # None on empty
```

`SurfacedQuestion` (dataclass):

```python
@dataclass(frozen=True)
class SurfacedQuestion:
    text: str
    provenance: str | None            # e.g., caller-supplied tag
    queue_position: int               # 1-based position before surfacing
    surfaced_at: str                  # ISO 8601 timestamp
    audit_path: Path                  # path to the audit-log entry just written
```

### Surface #6 (no halt — recorded; contribution shape)

Per F2.C — lazy resolution:

```python
@dataclass
class PerProjectPMRuntime:
    """Lightweight handle published on host.per_project_pm.

    Holds workspace_root so persona/CLI invocations agree on workspace.
    Provides a factory `runtime_for(pm_name)` that lazily loads PMs."""
    workspace_root: Path

    def runtime_for(self, pm_name: str) -> PMRuntime: ...


class PerProjectPMContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="per_project_pm",
        phase=Phase.after_orchestrator_ready,
        after=("primary_persona",),
    )

    def contribute(self, host: Any) -> None:
        host.per_project_pm = PerProjectPMRuntime(workspace_root=host.workspace_root)
```

### Surface #7 (no halt — recorded; state.yaml + decision-queue.yaml schemas)

`state.yaml` (operator-authored OR PM-managed; minimal Cycle 2 shape):

```yaml
schema_version: 1
in_flight: []          # operator-recorded in-flight tasks (free-form strings)
last_surfaced_at: null # ISO 8601 of most recent surface_next_question()
notes: ""              # free-form operator-authored project notes
```

`decision-queue.yaml`:

```yaml
schema_version: 1
queue:
  - text: "..."
    provenance: "..."  # optional
    enqueued_at: "..."  # ISO 8601
```

`audit-log/<YYYY-MM-DD>-<NNNN>.yaml`:

```yaml
schema_version: 1
event_kind: surface_question
timestamp: "..."       # ISO 8601 UTC
pm_handle: "..."
question_text: "..."
question_provenance: "..."  # may be null
queue_position_pre: 1   # 1-based; the position consumed
queue_depth_pre: N
queue_depth_post: N - 1
```

### Surface #8 (no halt — recorded; M-FBM-no-write boundary test)

Per AC.PPM.7 — the test pre-creates `<workspace>/workspace/.loam/memory/.canary` and
`<workspace>/.claude/skills/.canary` files; runs a full PM lifecycle (load empty → enqueue
3 decisions → surface them all); asserts both `.canary` files unchanged in mtime + size,
and asserts `<workspace>/workspace/.loam/memory/` directory listing unchanged (no new
files written). Belt-and-suspenders: also verify no path under
`<workspace>/workspace/.loam/memory/` was opened for write by the PM runtime
(via mock filesystem + tracking).

### Surface #9 (no halt — recorded; design-note articulation per AC.PPM.9)

`framework/per-project-pm/docs/design.md` body:
1. **Purpose.** Workspace-scoped PM persona; harness-general; per-project.
2. **PM/M-FBM boundary.** PM owns project-domain decision/ratification state +
   state-of-world snapshot. M-FBM owns turn-grain episode memory.
3. **Workspace-state directory shape.** `<workspace>/workspace/.loam/pms/<handle>/`,
   files inside per Surface #7.
4. **Lifecycle.** PM auto-loads when persona begins work in workspace (Cycle 2:
   lazy on-demand via `host.per_project_pm.runtime_for(pm_name)`).
5. **PM is per-workspace, not session-bound.** State persists to disk; survives
   process/session restart (D3/D5 smoke).
6. **Composition surfaces (advisory at Cycle 2).** `composes_with_skills` /
   `composes_with_agents` are recorded but not enforced; Cycle 4+ wires.
7. **Communication shape (translation rule applied bidirectionally).** PM-internals
   stay opaque to persona (no jargon-leak); persona-supplied state gets translated to
   PM-domain shape on enqueue.
8. **Out of scope at Cycle 2 (deferred to Cycle 4).** `record_response()`,
   `surface_next_questions_batch()`, `require_owner_response`-blocking enforcement,
   `onboarding_mode` enforcement on the persona-side flow.

### Surface #10 (no halt — recorded; first-run-inventory admission)

`framework/first-run-inventory.yaml` `shared_venv.components` list gets `per-project-pm`
appended after `workspace-bootstrap`. This is universal-file admission per amendment #22
ruling #3. The seal-test admits this universal file via `allowed_files`.

### Surface #11 (no halt — recorded; sub-plan vs builder-plan vs amendment-plan)

This document is the **Cycle 2 sub-plan-doc**. The parent plan
(`v0-1-7-personas-pm-layered-skills.md`) is the v0.1.7 sub-plan-doc. Both compose:
the parent declares 4 cycles; each cycle gets its own sub-plan-doc + manifest. The
amendment manifest (`v0-1-7-cycle-2-per-project-pm.manifest.yaml`) is the third
artefact; it points at THIS plan-doc.

---

## §5. Spec-objective placement

**Binds to:**

- **AC.PO.1 + AC.PO.2** (prime objective per VALUE_PROPOSITION.md) — PM absorbs
  project-domain coordination off persona's user-visible surface (translation-shape
  returns); decision-surfacing API enables single-question-at-a-time owner-friendly
  flow (Cycle 4 wires the persona-side enforcement; Cycle 2 ships the queue).
- **Eric-final-delivery §2 v0.1.7** — coordination machinery off persona's user-visible
  surface; PM ships.
- **Eric synthesis Decision Q (RESOLVED YES)** — one-question-at-a-time PM-enforced;
  Cycle 4 wires structurally; Cycle 2 establishes the queue + API.
- **Eric synthesis Decision G5** — PM-shape is harness-general, not dev-specific
  (drives placement under `framework/per-project-pm/`, not under `plugins/dev-sdlc/`).

**Ladders to:** AC.PPM.{1..9} → v0.1.7 Cycle 2 seal → v0.2.0 (PM ratification queue
mechanics + domain-batched AC surfacing wire to runtime) → AC.PO.

---

## §6. Acceptance criteria (per parent §5 AC.PPM.* family)

- **AC.PPM.1 — component scaffold present.** `framework/per-project-pm/` exists
  with `pyproject.toml` (declares `loam.bootstrap.contributions` entry-point
  `per_project_pm = "loam.per_project_pm.contribution:PerProjectPMContribution"`),
  `src/loam/per_project_pm/` package, `tests/test_no_sealed_amendments.py` seal-test,
  `tests/SEAL_COMMIT` sidecar (written at apply time), `README.md`, `docs/design.md`.
- **AC.PPM.2 — `PMContract` Pydantic model present + validates.**
  `from loam.per_project_pm.contract import PMContract` resolves; contract carries
  the 8 fields per Surface #4; pydantic validation rejects malformed contracts
  (empty handle → ValidationError; invalid project_kind → ValidationError;
  non-absolute workspace_root → ValidationError naming the field).
- **AC.PPM.3 — `DecisionSurfacingPolicy` Pydantic model present + defaults correct.**
  Default `max_questions_per_turn = 1`; default `onboarding_mode = False`; default
  `require_owner_response = True`; default `cool_down_seconds = 0`. Validation rejects
  `max_questions_per_turn < 1` and `cool_down_seconds < 0`.
- **AC.PPM.4 — `PMRuntime.from_workspace()` loader resolves workspace-state.**
  Reads `<workspace>/workspace/.loam/pms/<pm_name>/contract.yaml` + `state.yaml`
  + `decision-queue.yaml`. Returns hydrated runtime. Raises `PMNotFoundError`
  (named exception) when `contract.yaml` absent. Raises `PMStateCorruptedError`
  on schema mismatch (e.g., contract.yaml present but missing required field).
  `PMRuntime.empty_state_for(workspace_root)` returns an empty `StateOfWorld`
  without raising.
- **AC.PPM.5 — `surface_next_question()` API.** Method on `PMRuntime`. Consumes
  head of FIFO queue; returns `SurfacedQuestion` (text + provenance +
  queue_position + surfaced_at + audit_path); writes
  `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` with timestamp + question + queue-state-pre
  + queue-state-post + pm_handle. Returns `None` when queue empty (not exception —
  empty is normal). `<NNNN>` is 4-digit zero-padded monotonic counter scoped to
  (pm-name, UTC date), reset to `0001` at midnight UTC.
- **AC.PPM.6 — `enqueue_decision()` API.** Method on `PMRuntime`. Appends to
  FIFO `decision-queue.yaml`; returns 1-based enqueued position. Persists to
  `decision-queue.yaml` synchronously (atomic write via tmp+rename — no in-memory
  drift; partial writes refused). `enqueued_at` ISO 8601 timestamp recorded
  in the queue entry.
- **AC.PPM.7 — PM does NOT write to M-FBM episode store or `.claude/skills/`.**
  Per Surface #8 boundary test: full PM lifecycle (load → enqueue → surface)
  produces zero writes to `<workspace>/workspace/.loam/memory/` and zero writes
  to `<workspace>/.claude/skills/`. Verified via canary files + directory-listing
  comparison.
- **AC.PPM.8 — `PerProjectPMContribution` registers correctly.** Contribution
  metadata: `name="per_project_pm"`, `phase=after_orchestrator_ready`,
  `after=("primary_persona",)`. Test asserts entry-point discovery + host
  attribute publication (`host.per_project_pm` is a `PerProjectPMRuntime` with
  `workspace_root` set + `runtime_for(pm_name)` factory method present).
- **AC.PPM.9 — design-note articulates PM/M-FBM boundary.**
  `framework/per-project-pm/docs/design.md` exists; body covers the 8 sections
  per Surface #9 (Purpose / Boundary / Workspace-state shape / Lifecycle /
  Per-workspace not session-bound / Composition advisory / Communication shape /
  Out of scope at Cycle 2). Test asserts file presence + each section header
  present (markdown heading match).

### AC.V0.1.7.S — fence (single-component, NEW)

- **Cycle 2 fence:** `framework/per-project-pm/` (NEW component) only, plus
  `docs/rebuild/plans/` (universal admission for sub-plan + manifest), plus
  `framework/first-run-inventory.yaml` (universal-file admission).

### AC.V0.1.7.SMOKE — 6-dimension smoke (per dispatch)

- **D1 cold-state:** PM auto-loads when persona starts in canonical pos-v2 workspace;
  `host.per_project_pm.runtime_for(pm_name)` resolves to a `PMRuntime` for an
  authored PM; `state_of_world()` returns expected shape on empty project (via
  `PMRuntime.empty_state_for(workspace_root)`) AND on authored project.
- **D2 steady-state:** PM holds state across 5+ enqueue/surface cycles in a single
  process; state queries return consistent results; queue advances by 1 per surface.
- **D3 restart:** PM state persisted to disk; survives process restart (verified
  by writing state in process-A, reading in process-B — same `PMRuntime.from_workspace()`
  call, fresh Python process, same workspace).
- **D4 reboot:** PM state survives macOS reboot equivalent (`launchctl bootout` +
  `bootstrap` cycle simulated; or simply: state files persist in workspace tree,
  no transient in-memory state, no ~/.loam/ ephemera). Cycle 2 ships file-only
  state — survives any process death.
- **D5 cross-session:** PM state visible across `/clear`. State files on disk;
  re-instantiating `PMRuntime.from_workspace()` reads state; no session-scoped state.
  THE ship-test per STATE.md.
- **D6 telemetry-floor:** PM-mediated dispatches log per audit-trail floor — Cycle 2
  ships per-question audit-log entries (Surface #7); Cycle 4 wires production-stake
  mode floor enforcement. **For Cycle 2's D6 smoke,** assert audit-log entry written
  per `surface_next_question()` call — file exists, schema validates, timestamp
  within ±5s of call time. Production-stake mode floor (telemetry to OTEL) is
  Cycle 4's wire-up; Cycle 2 confirms the audit primitive is operating.

---

## §7. Build steps

### Plan-doc + manifest land first (this commit + next)

1. **Plan-doc** lands: this file at `docs/rebuild/plans/v0-1-7-cycle-2-per-project-pm.md`.
2. **Manifest** lands: `docs/rebuild/plans/v0-1-7-cycle-2-per-project-pm.manifest.yaml`
   declaring single-component fence on `framework/per-project-pm/`, BASELINE = source-edit
   commit, universal admissions for `framework/first-run-inventory.yaml`.

### Cycle 2.a — design-note + scaffold + contract.py (no runtime)

3. **Source edits — Cycle 2.a:**
   - `framework/per-project-pm/pyproject.toml` (NEW) — per Surface #3.
   - `framework/per-project-pm/README.md` (NEW) — orient to component.
   - `framework/per-project-pm/docs/design.md` (NEW) — per AC.PPM.9 + Surface #9.
   - `framework/per-project-pm/src/loam/per_project_pm/__init__.py` (NEW) — public re-exports.
   - `framework/per-project-pm/src/loam/per_project_pm/errors.py` (NEW) —
     `PMNotFoundError`, `PMStateCorruptedError`. (`PendingResponseError` deferred to Cycle 4.)
   - `framework/per-project-pm/src/loam/per_project_pm/contract.py` (NEW) —
     `PMContract`, `DecisionSurfacingPolicy` Pydantic models per Surface #4.
4. **Halt-check Cycle 2.a:** read design-note; assess against M-FBM convention;
   if contradiction observed (per dispatcher halt-trigger), halt + surface BEFORE 2.b.

### Cycle 2.b — runtime + loader + integration tests

5. **Source edits — Cycle 2.b:**
   - `framework/per-project-pm/src/loam/per_project_pm/loader.py` (NEW) —
     workspace-state load + YAML read with schema_version validation.
   - `framework/per-project-pm/src/loam/per_project_pm/runtime.py` (NEW) —
     `PMRuntime` with `from_workspace`, `empty_state_for`, `state_of_world`,
     `enqueue_decision`, `surface_next_question`. Atomic write via tmp+rename.
   - `framework/per-project-pm/src/loam/per_project_pm/state.py` (NEW) —
     `StateOfWorld`, `SurfacedQuestion` dataclasses; `QueueEntry` model.
   - `framework/per-project-pm/src/loam/per_project_pm/contribution.py` (NEW) —
     `PerProjectPMRuntime` + `PerProjectPMContribution` per Surface #6.
   - `framework/per-project-pm/tests/__init__.py` (NEW; empty).
   - `framework/per-project-pm/tests/test_no_sealed_amendments.py` (NEW) —
     BASELINE-aware seal-test mirroring `plugins/loam-skills/tests/test_no_sealed_amendments.py`.
     `BASELINE = "<source-edit-SHA>"`; `SEAL_COMMIT_PATH` sidecar logic.
   - `framework/first-run-inventory.yaml` — append `per-project-pm` to
     `shared_venv.components`. (Universal-file admission per amendment #22 ruling #3.)

6. **Tests authored:**
   - `tests/test_AC_PPM_1_scaffold_present.py` — pyproject.toml + src/ + tests/ +
     docs/design.md + README.md present; entry-point declared.
   - `tests/test_AC_PPM_2_PMContract_validates.py` — instantiate valid; reject
     empty handle / invalid project_kind / non-absolute workspace_root with
     ValidationError naming the field.
   - `tests/test_AC_PPM_3_DecisionSurfacingPolicy.py` — defaults correct;
     reject `max_questions_per_turn < 1`; reject `cool_down_seconds < 0`.
   - `tests/test_AC_PPM_4_runtime_loader.py` — load valid PM; raise
     `PMNotFoundError` on missing contract.yaml; raise `PMStateCorruptedError`
     on schema mismatch; `empty_state_for()` returns empty `StateOfWorld`.
   - `tests/test_AC_PPM_5_surface_next_question.py` — surface returns
     `SurfacedQuestion`; writes audit-log entry; `<NNNN>` increments; returns
     `None` on empty queue; queue advances; audit-log schema validates.
   - `tests/test_AC_PPM_6_enqueue_decision.py` — enqueue persists to YAML
     atomically; returns 1-based position; multiple enqueues advance position;
     `enqueued_at` ISO 8601.
   - `tests/test_AC_PPM_7_boundary_no_mfbm_writes.py` — canary file pattern;
     full lifecycle produces zero writes outside PM state dir.
   - `tests/test_AC_PPM_8_contribution_registers.py` — entry-point discovery;
     metadata correct; `host.per_project_pm` published; `runtime_for(pm_name)`
     factory present.
   - `tests/test_AC_PPM_9_design_note_present.py` — design.md exists; 8 section
     headers present per Surface #9.

7. **Touched-tests run** (from `framework/per-project-pm/`).

8. **`loam amend apply`** — auto-commit lands (NOT `--amend`).

9. **`loam amend seal`** — deterministic seal commit; sidecar advances to seal SHA;
   narrative appended.

10. **Smoke (all 6 dimensions per AC.V0.1.7.SMOKE):** record outcomes in status file.

---

## §8. Halt triggers (in-flight)

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt.
- Cycle 2.a design-note surfaces a contradiction with M-FBM workspace-state → halt + surface.
- Per-project PM design surfaces a workspace-identity primitive that doesn't exist → halt + surface.
- More than 5 in-build decisions need Luke escalation → halt + describe.
- Cycle 2 wall-clock exceeds 5 hours → halt with partial findings.
- Any AC ships partial → halt + reframe.
- Pydantic dependency import path resolves wrong (e.g., contract.py imports the wrong
  Pydantic) → halt + diagnose.
- Cycle 2 seal fails → halt; do NOT proceed; report.
- D5 (cross-session) smoke fails → halt (THE ship-test per STATE.md).
- M-FBM episode store gets a write during the boundary test → halt + diagnose;
  PM has crossed boundary.

---

## §9. Bookkeeping

- `loam amend apply` per cycle (NOT `git commit --amend`; create NEW corrective
  commits if a file is missed — per `feedback_no_amend_in_agent_dispatches`).
- Single semantic commit message for the source-edit BASELINE.
- Backfill of v0.1.7 release-level rows (STATE.md, roadmap §8, eric-final §2)
  DEFERRED to v0.1.7 RELEASE close per Cycle 1's recommendation. Cycle 2 SHAs
  documented in status file for eventual backfill.
- DO NOT push tags.

---

## §10. F2 Ruthless Feedback (additional gaps named this turn)

Beyond §2:

- **Lazy resolution risks "PM not auto-loaded" misperception.** Per F2.C, Cycle 2
  publishes a factory, not eager-loaded PMs. The smoke must explicitly test "calling
  `host.per_project_pm.runtime_for('eric-saas-pm')` works from session-zero" —
  otherwise the dispatcher's "PM auto-loads when persona begins work" sounds like
  eager-load and could be misread by Eric. The README + design-note name "lazy
  on-demand resolution" explicitly so the perception aligns with the implementation.

- **`record_response()` is a Cycle 4 API; the queue at Cycle 2 has no notion of
  "this question has been answered."** That's intentional (Cycle 2 = enqueue +
  surface; Cycle 4 = answer-tracking + blocking). The audit-log records surface
  events but not response events. The README + design-note name this explicitly so
  Cycle 4's surface area is predictable.

- **Pydantic v2 vs v1 import surface.** Pydantic v2 uses `model_config = ConfigDict(...)`,
  `field_validator`, `model_validator`. The component's `pyproject.toml` pins
  `pydantic>=2`. Existing components (primary-persona, workspace-bootstrap) use v2
  shape; per-project-pm follows that.

- **`schema_version: 1` in state.yaml + decision-queue.yaml + audit-log/*.yaml.**
  Forward-compat hook; Cycle 2 reads schema_version=1 only; future schema bumps
  raise `PMStateCorruptedError`. Same pattern as `framework/first-run-inventory.yaml`.

- **Workspace-bootstrap doesn't auto-create `<workspace>/workspace/.loam/pms/`.**
  By design — the directory is created lazily by `PMRuntime.enqueue_decision()` /
  `PMRuntime.surface_next_question()` on first write (parent dir mkdir(parents=True,
  exist_ok=True)). Empty workspace = no `pms/` dir; that's the expected D1
  cold-state shape. The PM is created when an operator authors `contract.yaml`;
  no scaffold-time sentinel needed (unlike `<workspace>/.claude/skills/.gitkeep`,
  which exists because Anthropic's Claude Code requires the directory present
  before live-detection works).

---

## §11. Provenance trail

- **Parent plan** `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md` (committed
  `d6def04`) — §3 Surface #3, #4, #5, #7 + §5 AC.PPM.* + §6 Cycle 2 build steps.
- **Cycle 1 seal** `3aa20dd` (BASELINE for Cycle 2).
- **Eric synthesis Decision G5** — PM-shape is harness-general (drives placement under
  `framework/per-project-pm/`).
- **Eric synthesis Decision Q (RESOLVED YES)** — one-question-at-a-time PM-enforced;
  Cycle 4 wires; Cycle 2 establishes queue + API.
- **`framework/primary-persona/src/loam/primary_persona/contract.py:211`** — `PersonaContract`
  Pydantic model precedent for `PMContract` shape.
- **`framework/primary-persona/src/loam/primary_persona/file_memory.py:103-120`** — M-FBM
  workspace-state path pattern; PM adopts same `<workspace>/workspace/.loam/...`
  convention per F2.A.
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/workspace_paths.py:99`** —
  `WORKSPACE_STATE_SUBDIR = "workspace"` canonical convention.
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py`** — `BaseContribution`
  + `ContributionMetadata` + `Phase` precedent for `PerProjectPMContribution`.
- **`plugins/dev-sdlc/src/loam/plugins/dev_sdlc/contribution.py`** — entry-point pattern
  precedent for `loam.bootstrap.contributions` registration.
- **`plugins/loam-skills/tests/test_no_sealed_amendments.py`** — NEW-component seal-test
  pattern precedent.
- **FIDRAFT entries on per-project PM** (committed `0f70c06` + `ccd48d4`) — durable
  capture this builds against.

---

*End of v0.1.7 Cycle 2 sub-plan-doc.*

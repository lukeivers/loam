# Research — dispatcher-side test-stub authoring

**Status:** research-only artefact (no code, no commits). Authored 2026-04-28.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Sibling plan-doc:** `docs/rebuild/plans/dispatcher-side-test-stub-authoring.md`.
**Captures (FIDRAFT):** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 151 — "Dispatcher-side test-stub authoring" (captured 2026-04-28 by amendment #71 (A3) build agent).
**Composes on (sealed):**
- Amendment #51 — A1 substrate (`framework/objective-tracker/src/runtime.py` manifest API; `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py`).
- Amendment #52 — A8 dispatch wrapper (`framework/primary-persona/src/dispatch_wrapper.py`).
- Amendment #70 — A2 objective-binding gate (`framework/hands-off-lifecycle/hooks/objective_binding_gate.py`).
- Amendment #71 — A3 TDD-guard (`framework/hands-off-lifecycle/hooks/tdd_guard.py` + `_gate_helpers.py`).
- Amendment #72 — A4 Bash/Agent guards (planned; not yet sealed at authoring).
- Amendment #73 — corpus-inlining session-start hook.

---

## 0. Pre-flight verification (mandatory)

`git log --grep="test-stub|test.stub|dispatch.*stub|dispatcher.*stub"` returns exactly one commit: `9b928c8 docs(rebuild): capture amendment #71 build-findings — direction-B placeholder, audit-log rotation, test-deletion gate, dispatcher-stub-authoring, pytest collection collision`. The hit is the FIDRAFT capture commit (one bullet appended to `FUTURE_IDEAS_DRAFT.md` line 151), not a shipped feature.

`ls docs/rebuild/plans/ | grep -iE "test.stub|dispatch.*stub"` returns nothing.

`framework/primary-persona/src/dispatch_wrapper.py` does not call `register_source_binding`, does not call `write_active_scope_sentinel`, and does not author any test files. The only sentinel/manifest writers in production are the test fixtures + the build agent's manual orchestration. Pre-flight is clean.

---

## 1. Problem statement (the failure class A2/A3 leave open)

After A1 + A2 + A3 + A52 land, the **happy-path build sequence for an amendment that authors NEW ACs** is:

1. Build agent's first action (must precede any source edit, per A2):
   `tracker.register_source_binding(component=..., ac_id=..., source_path_glob=...)` for each new AC.
2. Build agent's second action (must precede any source edit for new ACs, per A3):
   author `framework/<comp>/tests/test_AC_<NORM>_<descriptor>.py` containing `def test_AC_<NORM>_<descriptor>(...)`.
3. Build agent's third action: write a sentinel binding the dispatched agent to those rows
   (`active_scope_sentinel.write_active_scope_sentinel(...)` with `ScopeBinding(component, ac_id)`). Without this, A2 denies the first source edit even if rows exist (AC.OBG.1 — sentinel-presence).
4. THEN the agent edits source for the new ACs, with A2 + A3 admitting each edit.

In production today, this 3-step setup is **the build agent's responsibility**. The dispatcher (the persona authoring the build dispatch via `dispatch_with_scope`) hands off a brief carrying the plan-doc reference and the dispatched agent figures out the sequence. Three observed failure modes:

| # | Failure mode                          | Symptom                                                                                                | Frequency                                        |
| - | ------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| 1 | Agent has no scope (sentinel missing) | A2 denies first edit (AC.OBG.1). Agent has to halt-and-surface, dispatcher re-dispatches with sentinel | known to occur — empirically caught 2026-04-26+  |
| 2 | Agent forgets to author the test      | A3 denies source edit for new AC. Agent adds the test, retries.                                        | reduced by A3 deny diagnostic but still a round-trip |
| 3 | Agent improvises a test name          | Test exists but pattern mismatches `test_AC_<NORM>_*` glob. A3 still denies. Agent renames.            | low post-A3 deny diagnostic but real             |

Each failure mode is a round-trip: dispatch fires, agent attempts a source edit, gate denies, agent reads the deny diagnostic, agent does the missing setup work, source edit succeeds. The dispatch wrapper has the information needed (the plan's AC list) BEFORE the agent runs; doing the setup at dispatch time (not at first-edit time) eliminates the round-trip.

This is the same observation FIDRAFT line 151 records: "extend the dispatch wrapper to author empty test stubs at scope-creation time so the new-AC sequence is structurally 'register manifest row + scope sentinel + test stub on disk BEFORE agent first edit.'"

---

## 2. Composition surface (what's already built and load-bearing)

### 2.1 `dispatch_with_scope` (amendment #52)

**File:** `framework/primary-persona/src/dispatch_wrapper.py`. **Public callable:** `async def dispatch_with_scope(shape: DispatchShape, *, agent_runner, workspace_root, objective_id=None, owner_persona="primary", ipc_socket_path=None) -> DispatchOutcome | DispatchRefusal`.

Today, the wrapper:

1. Builds a `ScopeSpec` from the dispatch shape (AC.A8.1).
2. Resolves objective_id (caller / ambient seed / fallback).
3. Resolves orchestrator socket path; falls back if unreachable (AC.A8.6).
4. Calls `activate_scope_with_spec` IPC (AC.A8.3) — gates fire here.
5. Invokes `agent_runner` on approval.
6. Calls `record_dispatch_close` IPC.
7. Returns `DispatchOutcome` or `DispatchRefusal`.

The wrapper has **no relationship to A1 substrate** (manifest table, sentinel) or **A3 test convention** today. Adding stub authoring is a new step in this scope-creation phase — natural placement: between step 3 (resolve socket) and step 4 (call activate_scope_with_spec), OR between step 4 and step 5 (call activate-scope first, then on approval do the bookkeeping THEN run the agent). The natural placement question is itself a design decision (D-DSA.7 below).

The wrapper currently reads two paths (workspace orchestrator socket; ambient-objective seed) but writes only one (the diagnostic NDJSON log on fallback). The proposed extension would have the wrapper write THREE artefacts at scope-creation time: (a) manifest rows, (b) test stubs, (c) sentinel.

### 2.2 A1 substrate APIs

**Manifest API** (`framework/objective-tracker/src/runtime.py:669`):
```python
def register_source_binding(self, *, component: str, ac_id: str, source_path_glob: str) -> None
def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict[str, Any]]
```
Idempotent on duplicate. `created_at` is set by SQLite trigger inside `_store.insert_manifest_row`.

**Sentinel API** (`framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:115`):
```python
def write_active_scope_sentinel(workspace_root, *, scope_id, plan_path,
    bindings: list[ScopeBinding] | tuple[ScopeBinding, ...],
    session_id: str | None = None) -> ActiveScopeWriteResult
```
Atomic write via `.tmp` + `os.replace`. Idempotent on byte-equal content. `created_at` is `_now_iso()` at write time.

**Critical timing detail for A3 "new AC" detection (AC.TDG.4 / D-A3.4 lock):** A3 considers an AC "new in this diff" when at least one manifest row's `created_at` is **strictly after** the sentinel's `created_at`. The dispatcher's sequencing must therefore be:

1. **First:** write the active-scope sentinel.
2. **Then:** register manifest rows (so rows have `created_at` > sentinel `created_at`).

If the dispatcher reverses this, A3 treats the ACs as "existing in-AC modifications" (AC.TDG.4) and never enforces the test-pinning. That's a silent failure: the dispatcher's setup work is invisible to A3, even though A2 admits. **D-DSA.4 below names sequencing explicitly.**

A simpler shape: stamp the sentinel first, sleep until next ISO-second tick, then register manifest rows. Sub-second skew is the issue per A3's R3 risk register; ISO-8601 second-resolution timestamps from `_now_iso` collapse the difference. Empirically: any test that registers a row immediately after sentinel write should observe row.created_at >= sentinel.created_at; the strict-after comparison is the gate's predicate.

### 2.3 A3 pinned-test convention (`framework/hands-off-lifecycle/hooks/tdd_guard.py:123`)

```python
def _normalise_ac_id(ac_id: str) -> str:
    s = ac_id
    if s[:3].lower() == "ac.":
        s = s[3:]
    s = s.replace(".", "_")
    return s.upper()

def _expected_test_glob(component: str, ac_id: str) -> str:
    return f"framework/{component}/tests/test_AC_{_normalise_ac_id(ac_id)}_*.py"

def _function_prefix(ac_id: str) -> str:
    return f"test_AC_{_normalise_ac_id(ac_id)}_"
```

A3 enforces TWO predicates on a "new AC" source edit:

1. At least one file matching the glob exists in `framework/<comp>/tests/` (rglob, recursive into subdirs).
2. At least one file matching the glob contains a `def test_AC_<NORM>_<word>(` (regex, multiline).

Stub authoring must satisfy BOTH: file exists AND function exists.

---

## 3. Design space — stub content shape

### 3.1 Candidates

| ID  | Stub body                                         | Pollutes test count? | Convention-marker?       | A3-passing? |
| --- | ------------------------------------------------- | -------------------- | ------------------------ | ----------- |
| α   | `def test_AC_<NORM>_placeholder(): pass`          | YES — passes by default | weak             | YES (file + fn exist) |
| β   | `def test_AC_<NORM>_placeholder(): pytest.skip("stub authored by dispatcher; replace with real test")` | no — skipped | strong (skip reason) | YES |
| γ   | `def test_AC_<NORM>_placeholder(): pytest.fail("stub authored by dispatcher; replace with real test")` | no — fails | very strong | YES (A3 only checks fn exists) but breaks pre-amendment test sweep |
| δ   | `def test_AC_<NORM>_placeholder(): raise NotImplementedError("...")` | no — errors | strong | YES but breaks pre-amendment test sweep |
| ε   | docstring + skip + fixture skeleton (richer)      | no — skipped | strong; high-information | YES |

### 3.2 Trade-off analysis

**α (pass-by-default) is wrong.** The brief is explicit: "the stub must not POLLUTE the test count with passes-by-default — A3's predicate is 'pinned test exists on disk + named correctly,' not 'test passes.'" A passing stub silently inflates the green-test count and sets up the failure mode where a builder seals an amendment with stub-only coverage that passes review.

**γ / δ (fail/raise) break pre-amendment test sweeps.** `pos-amend apply --dry-run` runs the scoped tests as part of the seal-diff sweep (AC.D-sa.x). A stub that hard-fails turns the `--dry-run` red on the amendment's first authored test — a hard prereq violation. The build agent is forced to delete or rewrite stubs immediately. That's the same round-trip the stub aims to eliminate.

**β (skip with reason) is the correct shape.** It:
- Satisfies A3's file-exists + function-exists predicates.
- Reports as `skipped` (not `passed`, not `failed`) in pytest output — visible in the test count without polluting green or red.
- Carries the convention marker (the skip reason names the dispatcher and the replacement contract).
- Is idempotent: replacing a skipped test with a real test is the build agent's normal authoring action; no special "remove the skip first" step.

**ε (richer)** adds value if the dispatcher knows enough to author a partial body (reference to AC text, expected fixtures, expected assertion shape). The dispatcher does have access to the plan doc's AC text. But authoring a partial body leaks design from the dispatcher into the build agent's working context — the build agent should be the one shaping test bodies. **Recommendation: skip-with-reason (β) for the structural primitive; rich ε is a future amendment.**

### 3.3 Function name

A3 admits any function whose name **starts with** `test_AC_<NORM>_` and continues with `\w*` (word chars). Candidates:

- `test_AC_<NORM>_placeholder` — descriptive, signals stub status.
- `test_AC_<NORM>_stub` — shorter, same signal.
- `test_AC_<NORM>_dispatcher_stub` — names the author.

Recommendation: `test_AC_<NORM>_placeholder`. Mirrors common pytest stub naming.

### 3.4 File name

A3 admits any file matching `test_AC_<NORM>_*.py`. Candidates:

- `test_AC_<NORM>_placeholder.py` — single stub per AC.
- `test_AC_<NORM>_stub.py` — short.
- `test_AC_<NORM>_dispatcher_stub.py` — names the author.

Recommendation: `test_AC_<NORM>_placeholder.py`. Symmetric with function name; discoverable.

### 3.5 Stub body (recommended shape, β)

```python
"""Dispatcher-authored placeholder for AC.<id>.

This file was created by the dispatcher at scope-creation time
(amendment #<N>; plan: <plan-path>; scope_id: <scope_id>) to
satisfy A3's pinned-test predicate. The build agent is expected
to replace the placeholder function with real test(s) for AC.<id>
during the build.

A3 admits any test_AC_<NORM>_* function in this file; the build
agent may rename or augment as needed.
"""

import pytest


def test_AC_<NORM>_placeholder() -> None:
    pytest.skip(
        "stub authored by dispatcher; replace with real test for AC.<id>"
    )
```

Bare-stdlib + pytest. No fixtures imported (the build agent imports what it needs).

---

## 4. Design space — stub-replacement contract

### 4.1 Modify-in-place vs. sibling

| Approach          | Build agent action                                        | Pros                                          | Cons                                   |
| ----------------- | --------------------------------------------------------- | --------------------------------------------- | -------------------------------------- |
| Modify-in-place   | Edit the placeholder file: rename fn, fill body            | Simple; one file per AC; no dead stubs       | A3 fires on Edit; gate must allow self-edit of test path (AC.TDG.3 already handles) |
| Sibling           | Author `test_AC_<NORM>_<descriptor>.py` next to placeholder | Keep stub as a "dispatcher-was-here" marker; clear audit trail | Two files per AC (placeholder + real); cleanup question; convention drift |

**Modify-in-place is structurally simpler.** A3's chicken-and-egg avoidance (AC.TDG.3) already allows ALL test-tree edits regardless of new-AC state, so the build agent can rename/refactor freely. The placeholder is a substrate, not a marker — it disappears when the agent authors the real test. **D-DSA.2 names this.**

Sibling has a real cost: every amendment that author N new ACs ends with N placeholder files that are skipped forever. The amendment's sealed test count grows by N skip-only tests. That's clutter; cleanup needs a future amendment. Reject.

### 4.2 Multiple-test case

A build agent may want >1 test per AC (separate happy-path + edge-cases). Modify-in-place handles this naturally: the agent renames the placeholder to (e.g.) `test_AC_<NORM>_happy_path` and adds `test_AC_<NORM>_edge_case_x` in the same file or a new sibling file. A3 admits both. No design tension.

### 4.3 Stub-deletion behaviour

The brief asks: "If the build agent decides an AC isn't worth a separate test (consolidated into another), what happens to the unused stub? Auto-delete on seal? Manual cleanup?"

Three subcases:

- **AC consolidated into another AC's test file.** The build agent edits AC X's test file to also exercise AC Y's behaviour. AC Y's placeholder is now redundant. A3 still admits a source edit for AC Y if Y's manifest row is registered AND any file matching Y's glob has any function matching Y's prefix (the placeholder). The placeholder is harmless but redundant.
- **AC dropped from the plan during build.** The build agent decides AC Y isn't a real AC — it should never have been a separate row. The right action is to remove the manifest row (NOT delete the placeholder) and update the plan doc to remove AC Y. The placeholder then has no manifest row pointing to it; it's an orphan test file (skips on every run, harmlessly).
- **AC subsumed entirely.** Same as case 1; the placeholder remains harmless.

**Recommendation:** the dispatcher does NOT auto-delete stubs. The build agent's seal-diff includes either (a) modified-in-place stubs (real tests now) or (b) untouched stubs (skipped, harmless, audit trail).

A future amendment could ship a "post-seal stub-cleanup pass" but that's out of this amendment's scope (D-DSA.5 is the explicit OOS).

---

## 5. Design space — where stubs land

### 5.1 Per-AC vs. consolidated

| Layout                                                                                | Pros                                | Cons                              |
| ------------------------------------------------------------------------------------- | ----------------------------------- | --------------------------------- |
| One file per AC: `tests/test_AC_<NORM>_placeholder.py`                                 | Matches A3's per-AC convention; obvious 1:1 mapping | More files per amendment       |
| Consolidated: `tests/test_AC_<NORM>_stubs.py` with multiple `def test_AC_<NORM>_*` fns | Fewer files                         | Different AC IDs collide on filename; A3's glob `test_AC_<NORM>_*.py` would need different normalisation per AC |

**Per-AC wins by A3's existing convention.** Every existing test in `framework/*/tests/test_AC_*.py` follows the one-file-per-AC pattern. Consolidating breaks the convention; A3's glob is per-AC by design. **D-DSA.3 names per-AC.**

### 5.2 Component fence

The dispatcher needs to know which component owns each AC (so it puts the stub in the correct `framework/<comp>/tests/` directory). The plan doc's AC list should declare the component for each AC. Two sources:

1. **Plan-doc parsed.** The dispatcher reads the plan-doc's AC list (`AC.X.1`, `AC.X.2`, ...) and maps each to a component via the manifest YAML (`components: - name: <comp>`).
2. **Caller-supplied.** The persona dispatch shape carries `(component, ac_id, source_path_glob)` triples explicitly.

**Caller-supplied is the correct shape.** Plan-doc parsing is brittle (the same brittleness that disqualified A3 D-A3.3 candidate γ). The dispatcher's input shape (the persona's authoring of the dispatch) carries the AC list; the persona reads the plan doc and explicit-passes the (component, ac_id, source_path_glob) triples. **D-DSA.6 names this.**

The shape of the input is a `tuple[NewACSpec, ...]` where:
```python
@dataclass(frozen=True)
class NewACSpec:
    component: str
    ac_id: str           # e.g. "AC.OBG.1" or "OBG.1"
    source_path_glob: str  # e.g. "framework/hands-off-lifecycle/hooks/objective_binding_gate.py"
```

If `new_acs` is empty, the dispatcher skips the stub-authoring step entirely. (This is the "research+plan dispatch authoring the plan itself" failure mode in the brief — see §7 below.)

### 5.3 Path canonicalisation

A1's manifest stores `source_path_glob` as a workspace-relative path; `_workspace_relative` (now in `_gate_helpers.py`) is the canonical converter. The dispatcher must use the same helper so the stub-author's resolved path matches A3's filesystem scan path.

A1's sentinel file is at `<workspace>/workspace/.pos/active-scope.json` (D-migration D.2). The stub files land at `<workspace_root>/framework/<comp>/tests/test_AC_<NORM>_placeholder.py` — a workspace-relative path inside the framework tree.

---

## 6. Design space — composition with `dispatch_with_scope`

### 6.1 The new step's placement

`dispatch_with_scope` today has 7 steps (§2.1). The new step (sentinel + manifest + stub authoring) has THREE candidate placements:

| Candidate | Placement                                                                        | Pros                                                  | Cons                                                                      |
| --------- | -------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------- |
| A         | BEFORE `activate_scope_with_spec`                                                | Simple; setup before gates fire; on refusal stubs are harmless | Stubs persist on gate refusal (if cost-gov refuses the dispatch, stubs still exist on disk) |
| B         | AFTER `activate_scope_with_spec` (gate-approved), BEFORE invoking `agent_runner` | Stubs only on approved dispatches; clean             | Adds a window where activate-scope succeeded but stubs failed → inconsistent |
| C         | DURING `activate_scope_with_spec` (push to orchestrator-side)                    | Atomicity                                             | Massive scope expansion (orchestrator gains stub-authoring concern); rejected |

**Candidate A wins.** The persistence concern is benign: on gate refusal, the stubs remain in workspace as `pytest.skip` files. They DON'T register as tests passing or failing; they're present on disk but inert. The next dispatch with the same AC list either finds them already there (idempotent skip via byte-equal check) or overwrites them (idempotent overwrite). On gate refusal, the operator sees the refusal in the diagnostic log; the stubs are an audit-trail artefact of the attempt.

Candidate B's window-of-inconsistency is real but minor: the dispatcher could fail to write a stub mid-creation, leaving (e.g.) 2 of 3 stubs on disk. The build agent's first edit then encounters "1 of 3 ACs missing test" — A3 denies the third, the agent re-runs the dispatcher's stub step (or surfaces). Since stub authoring is idempotent, this is recoverable.

**Recommendation: Candidate A.** Setup phase: open IPC client; resolve socket; resolve objective_id; write sentinel; register manifest rows; write stubs; THEN call `activate_scope_with_spec`. **D-DSA.7 names this.**

### 6.2 Idempotency

Stub authoring must be idempotent. A retry of the same dispatch (same AC list) must not corrupt existing stubs. Concrete shape:

- **Sentinel write:** A1's `write_active_scope_sentinel` is byte-equal-idempotent (returns `wrote=False, reason="skipped-identical"` on no-op).
- **Manifest rows:** A1's `register_source_binding` is idempotent on duplicate (per its docstring).
- **Stub files:** byte-equal-idempotent. If `framework/<comp>/tests/test_AC_<NORM>_placeholder.py` already exists with the expected content, no-op. If exists with different content (build agent already started authoring), DO NOT OVERWRITE — log a diagnostic, skip the write. Otherwise, write.

The "already authored" detection: read existing file; if file contains a function matching `test_AC_<NORM>_\w+(` AND the function body is NOT `pytest.skip(...stub authored by dispatcher...)`, treat as authored — skip. This is the safest default; the build agent's authoring takes precedence over the dispatcher's stub.

### 6.3 Failure modes during stub authoring

What if the dispatcher can't write a stub (permission error, disk full, path missing)?

| Failure                          | Behaviour                                                                                  |
| -------------------------------- | ------------------------------------------------------------------------------------------ |
| Sentinel write fails              | A1 already returns `ActiveScopeWriteResult` with `wrote=False, reason="failed-*"`. Dispatcher logs a diagnostic and CONTINUES (does not fail the dispatch). The agent will hit A2 and surface. |
| `register_source_binding` raises  | Tracker is unreachable (DB lock, file missing). Dispatcher logs diagnostic and CONTINUES. The agent will hit A2 and surface. |
| Stub-file write fails             | OSError on filesystem write. Dispatcher logs diagnostic and CONTINUES. The agent will hit A3 and surface. |

In all three cases, the dispatcher does NOT fail the dispatch. The substrate's gates (A2, A3) remain the structural enforcement; the dispatcher's stub authoring is a SETUP CONVENIENCE, not a structural prereq.

**Why this is the right choice:** the dispatcher's stub-authoring is a productivity primitive that eliminates round-trips on the happy path. On the unhappy path (substrate broken), the gate denies and the operator sees it. Failing the dispatch on stub-authoring failure would couple the productivity primitive to the dispatch path's reliability — a regression vs. AC.A8.6's fail-soft principle.

### 6.4 Pre-flight failure mode — research+plan dispatches

The brief asks: "What if the dispatcher can't predict which ACs will be authored? (e.g. research+plan agent invents new ACs during research). Then the dispatcher CAN'T pre-author stubs."

**Correct.** The shape applies cleanly to BUILD dispatches against an existing plan doc. A research+plan dispatch (the kind dispatched on this very task) authors the plan and its ACs as its OUTPUT; the dispatcher cannot know the ACs at dispatch time.

Resolution: the `new_acs` field on `DispatchShape` is OPTIONAL; when absent or empty, the dispatcher SKIPS the stub-authoring step. The research+plan dispatch shape has `new_acs=()`. The build dispatch shape (against an existing plan) has `new_acs=(NewACSpec(...), ...)`.

A research+plan dispatch's edit operations are limited to authoring the plan doc and research doc — both under `docs/rebuild/plans/`, which is universally admitted (A2's carve-out admits documented universal-paths). A2 doesn't deny the research+plan dispatch; A3 doesn't either (research+plan dispatches don't edit `framework/*/` source). The gate composition is correct without dispatcher stubs.

**D-DSA.1 names this:** the stub-authoring shape applies only to BUILD dispatches with declared new ACs.

---

## 7. Design space — A2/A3 in-vivo composition test

After this lands, a build dispatch against an existing plan should sail through A2 + A3 checks WITHOUT the build agent thinking about either gate. The gates become invisible in the happy path.

### 7.1 The composition contract

For a build dispatch with `new_acs = (NewACSpec("comp_X", "AC.X.1", "framework/comp_X/src/foo.py"), ...)`:

1. Dispatcher writes sentinel binding `(comp_X, AC.X.1)`.
2. Dispatcher registers manifest row `(comp_X, AC.X.1, "framework/comp_X/src/foo.py")`.
3. Dispatcher writes stub `framework/comp_X/tests/test_AC_X_1_placeholder.py` with `def test_AC_X_1_placeholder(): pytest.skip(...)`.
4. Dispatcher calls `activate_scope_with_spec` → cost/safety/reversibility gates fire.
5. On approval, dispatcher invokes agent_runner.
6. Agent's first edit (e.g. `framework/comp_X/src/foo.py`):
   - A2 fires: sentinel admits `(comp_X, AC.X.1)`; manifest admits glob → ALLOW.
   - A3 fires: sentinel admits `(comp_X, AC.X.1)`; manifest row's `created_at` > sentinel's `created_at` (NEW AC); test stub exists at expected glob; function `test_AC_X_1_placeholder` matches `test_AC_X_1_*` prefix → ALLOW.

### 7.2 Verification path

A composition test would assert:

- After dispatcher's setup (sentinel + manifest + stub), A2's `evaluate(...)` returns ALLOW for a hypothetical edit at `framework/comp_X/src/foo.py`.
- After dispatcher's setup, A3's `evaluate(...)` returns ALLOW for the same hypothetical edit.

The test does NOT need to actually run the gates as a child process — it can call A2's + A3's `evaluate` functions directly with the workspace_root + tool_input shape, asserting the Decision return.

This is an outcome-shaped AC (AC.DSA.A1 in §9 — "build dispatch with declared new_acs sails through A2 + A3 without round-trip").

---

## 8. Pre-flight failure modes (recap from §6.4 + new)

1. **Research+plan dispatch (no `new_acs`):** dispatcher skips stub authoring (D-DSA.1). Composition: research+plan dispatches edit only universally-admitted paths, so A2/A3 don't fire on them.
2. **Build dispatch authoring NEW plan from research:** doesn't apply — research+plan + build is two dispatches; the research+plan dispatch produces the plan-doc, then the build dispatch (separate, with explicit `new_acs`) does the build.
3. **Build dispatch with mid-build AC re-extension (ODD §4):** the build agent re-extends AC X.Y mid-build (e.g. AC.X.A1 added per §4 protocol). The dispatcher's stub set was authored for AC.X.1..AC.X.S; AC.X.A1 has no stub. The build agent must register the new manifest row + author the test (mirroring §4 protocol); A2/A3 fire normally for the new AC. Dispatcher's role doesn't extend mid-build; the agent's role does. This is the same failure class A3 catches today.
4. **Build dispatch with workspace not yet bootstrapped:** sentinel path missing, manifest DB unreachable. Dispatcher logs diagnostic and continues; activate_scope_with_spec hits the AC.A8.6 fallback path; agent runs unwrapped. Stubs may or may not exist depending on which write step failed. This is a "harness absent" workspace; the gates also don't fire on a non-bootstrapped workspace, so the failure is contained.
5. **Race with another dispatcher:** two dispatches in the same workspace at the same time. The sentinel is single-tenant per workspace (one active scope at a time); a second dispatcher's sentinel write overwrites the first. This is an existing A1 design choice — not a stub-authoring concern.

---

## 9. Structural-enforcement classification

Per A1's D4 lock and A3's D-A3.6 lock, structural-enforcement features partition into UNIVERSAL (fire in NORMAL USE workspaces) and DEV-MODE-only.

The dispatcher's stub-authoring composes with A2 + A3, both DEV-MODE-only. **The stub-authoring is also DEV-MODE-only.** In NORMAL USE workspaces:

- A2 doesn't deny edits.
- A3 doesn't deny edits.
- The dispatcher has no need to author stubs; the gates won't refuse.

Concretely: the dispatcher's stub-authoring step is wrapped in a `read_workspace_mode_or_normal_use(workspace_root) == "dev-mode"` guard. NORMAL USE workspaces skip it entirely. **D-DSA.8 names this.**

This matches A4's mode partition (A4's universal classes: secret/blast-radius; A4's DEV-MODE classes: ODD-discipline; this amendment's class: ODD-discipline → DEV-MODE).

---

## 10. Composition with amendment #73 (corpus-inlining hook)

The brief says: "Composes with amendment #73's corpus-inlining hook — completes the 'fully-set-up session-start' picture."

Amendment #73 inlines the corpus at session-start. The dispatcher's stub-authoring inlines the scope-context at dispatch-start. Together, the build agent's first turn has:

1. Corpus inlined (#73): the agent has the methodology + plan doc in context.
2. Manifest rows registered (this amendment): A2 admits the agent's first edit.
3. Sentinel written (this amendment): A2 + A3 sentinel-presence checks pass.
4. Test stubs on disk (this amendment): A3's pinned-test predicate passes.

The agent's first edit is a real source edit, not a setup edit. **The "fully-set-up session-start" picture is complete.**

This composition does not affect this amendment's scope (no edits to amendment #73's surfaces). It's a downstream observation worth recording in the plan's §13 "Ladder to AC.PO.1 / AC.PO.2."

---

## 11. Summary of named decisions surfaced for owner ruling

D-DSA.1, D-DSA.2, D-DSA.3, D-DSA.4, D-DSA.5, D-DSA.6, D-DSA.7, D-DSA.8 — see plan-doc §6 / §9 for the full list with recommendations. (This research artefact informs the plan; the plan surfaces the decisions to owner with recommendations + alternatives.)

## 12. References

- FIDRAFT capture: `docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 151.
- Amendment #52 plan: `docs/rebuild/plans/agent-dispatch-as-scope-wrapper.md`.
- Amendment #52 wrapper code: `framework/primary-persona/src/dispatch_wrapper.py`.
- Amendment #52 manifest: `docs/rebuild/plans/agent-dispatch-as-scope-wrapper.manifest.yaml`.
- Amendment #51 (A1) substrate plan: `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- Amendment #51 substrate APIs:
  - `framework/objective-tracker/src/runtime.py:669` (`register_source_binding`).
  - `framework/objective-tracker/src/runtime.py:695` (`manifest_rows_for_ac`).
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:115` (`write_active_scope_sentinel`).
- Amendment #70 (A2) plan: `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.md`.
- Amendment #70 (A2) gate code: `framework/hands-off-lifecycle/hooks/objective_binding_gate.py`.
- Amendment #71 (A3) plan: `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`.
- Amendment #71 (A3) gate code: `framework/hands-off-lifecycle/hooks/tdd_guard.py` (especially `_normalise_ac_id`, `_expected_test_glob`, `_function_prefix`).
- A3 helpers (potential composition): `framework/hands-off-lifecycle/hooks/_gate_helpers.py`.
- ODD methodology: `docs/odd-methodology.md` §3.3, §4, §5.1.1, §7.4, §8.
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` (translation-layer §; AC.PO.1, AC.PO.2).
- Memory bullets carried forward: `feedback_summarize_and_surface_decisions`, `feedback_subagent_odd_violation_halt`, `feedback_no_amend_in_agent_dispatches`, `feedback_dispatch_explicit_pos_amend_apply`, `feedback_amendment_dispatch_speedups`, `feedback_serialize_amendment_builds`.
- pos-amend §14 regex narrowness: `framework/tools/pos-amend/src/pos_amend/commands/seal.py:285` — `^## 14[.\s]` accepts `## 14.` or `## 14 ` only.

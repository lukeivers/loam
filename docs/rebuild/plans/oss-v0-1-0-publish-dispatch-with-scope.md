# OSS v0.1.0 publish — M4 — wire `dispatch_with_scope` as the persona's actual Agent-dispatch path — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (master plan §5 M4 row + §6 sequencing rule #3).
**Programme predecessor:** M3.wire-clis (sealed `95f1ab2` 2026-04-29; §14 backfill `6751b94`). M3 itself composed on M2.partition (sealed `4cda805`) + M1.rename series (sealed M1a..M1g; M1g seal `f6c22fd`).

**Authority documents:**
- Master plan §5 M4 row + §6 sequencing rule #3 (M3/M4/M5 are independent in scope; M4 is "architecturally most significant of the wire-or-strip amendments").
- Programme AC: AC.OSS.2 (D-1) — `docs/rebuild/plans/oss-v0-1-0-publish.md` §3.
- Feature-usage audit D-1 — `dispatch_with_scope` has zero non-test callers.
  Path: `.scratch/claude-output/feature-usage-audit.md` §D-1 (line 366).
- VALUE_PROPOSITION (prime objective hook): `docs/rebuild/VALUE_PROPOSITION.md` —
  the primary-persona test (translation-burden absorption) + harness test
  (toolkit-primitive growth). M4 wires the prime structural surface.
- Existing dispatch wrapper (DO NOT MODIFY): `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py` (amendment #52 + #74 sealed; AC.A8.1..AC.A8.11 + AC.DSA.1..AC.DSA.10).
- Existing PreToolUse-hook precedent (compose alongside): `framework/hands-off-lifecycle/hooks/agent_guard.py` (matcher `Task`) + `objective_binding_gate.py` + `tdd_guard.py` + `bash_guard.py`.
- Existing setup-phase substrate (the disk-side gates the hook applies): `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (`write_active_scope_sentinel`) + `loam.objective_tracker.ObjectiveTracker.register_source_binding` + (NEW per AC.OSS-M4.4) a public stub-writer extracted from `dispatch_wrapper._write_stub_idempotent`.

---

## 1. Summary / TLDR

**M4 authors a PreToolUse hook on the `Task` tool that, when the dispatch
prompt carries a structured AC declaration, performs the
amendment-#74 disk-side setup phase (sentinel + manifest rows + test
stubs) BEFORE the underlying Task tool call fires.** This wires the
structural-enforcement value of `dispatch_with_scope` into the
persona's actual Agent-dispatch path without requiring the persona to
explicitly invoke the wrapper from a Claude Code session (where the
Task tool is the only available Agent-dispatch verb).

Today, every persona-issued Agent dispatch in a Claude Code session
calls `Task` directly. The four-gate setup chain authored at
amendments #52 / #74 (`dispatch_with_scope` + `_run_setup_phase`) has
zero non-test callers (feature-usage audit §D-1). Per the master plan
§5 M4 row + §6 sequencing rule #3, M4 wires the persona's real Task
calls through the setup-phase gates so the value-add fires in
production.

**Critical architectural finding (halt-and-surface trigger #5/#6,
surfaced at plan-authoring time — not blocking; design accommodation
recorded):** Claude Code's PreToolUse hook can only emit a
`permissionDecision` of `allow` / `deny` / `ask`; it CANNOT run the
agent on Claude's behalf nor "wrap" the tool call. So M4's hook
cannot fully replicate `dispatch_with_scope`'s end-to-end flow (which
includes IPC-bound `activate_scope_with_spec` → cost-governance
reservation → record_dispatch_close). The dispatch carefully scopes
M4 to **the four gates the hook CAN apply** — all four are disk-side
side-effects that the setup phase performs:

  1. **AC manifest registration** — `tracker.register_source_binding(component, ac_id, source_path_glob)` per AC.DSA.1.
  2. **Scope sentinel creation** — `write_active_scope_sentinel(workspace_root, scope_id, plan_path, bindings)` per AC.DSA.3.
  3. **Test stub authoring** — placeholder `pytest.skip(...)` test file per AC at the A3-expected glob per AC.DSA.2.
  4. **Plan-doc reference recording** — `plan_path` field on the sentinel record (already part of #2 above; named separately because the dispatch language enumerates four).

The IPC-bound chain (cost / safety / reversibility / orchestrator gate
chain that fires inside `activate_scope_with_spec`) is **out of M4's
scope** — that chain only runs for explicit in-process callers of
`dispatch_with_scope`. M4 closes the dominant production gap (every
Task dispatch acquires the disk-side gates) while leaving the IPC-side
chain as the explicit-call surface. A future amendment can extend the
hook to fire IPC-side gates if the cost-governance ledger needs to
fill from PreToolUse-time reservations; that is **NOT** in M4. See §6
D-build.M4.1.

**Three downstream design points surfaced for §10 (recommendations
locked, not requiring owner ruling):**

- **D-build.M4.2 — AC declaration format in dispatch prompts.**
  Recommended: an HTML-style block marker
  `<AC-MANIFEST>` … `</AC-MANIFEST>` carrying one CSV row per declared AC
  (`component,ac_id,source_path_glob`). Stdlib-parseable from a hook
  without a YAML dependency; visually scannable by a human reading
  the dispatch prompt; namespace-segregated (the marker name is unique
  to loam tooling, no collision risk with existing prompt content).
- **D-build.M4.3 — passthrough vs refusal on dispatches without an AC declaration.**
  Recommended: **passthrough with a one-line NDJSON deprecation log**
  per dispatch's option 3. Hard refusal (option 2) would break every
  research/plan dispatch (which carries `new_acs=()` per AC.DSA.10
  backwards-compat) — those are legitimate Task dispatches that
  intentionally don't author new ACs. Passthrough preserves
  backwards-compat AND makes the gap observable for future audits.
  The wrapper already supports `new_acs=()` as a fully-supported call
  path; mirror that semantic in the hook.
- **D-build.M4.4 — recursion handling.**
  Recommended: an environment-variable bypass (`LOAM_DISPATCH_BYPASS_HOOK=1`)
  + a sentinel-already-written short-circuit. Today no production code
  invokes `dispatch_with_scope`, so recursion is theoretical; M4
  records the design awareness so future wiring of `dispatch_with_scope`'s
  `agent_runner` to call the Task tool internally has a clean
  bypass surface. The setup phase is idempotent per AC.DSA.4 — even
  without the bypass, re-fire is safe but wasteful.

**Halt-and-surface findings encountered at plan-authoring (full list
in §11):** none block dispatch; six observations recorded for
builder awareness.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Prime objective:** VALUE_PROPOSITION's two tests
(harness-test + primary-persona-test). Per
`feedback_value_proposition_as_prime_objective`, every component /
feature / amendment / AC ladders up.

**Programme objective:** AC.OSS.2 — wired-feature-density:
"Every sealed component in the public set is wired and exercised by
primary persona's normal operation."

**M4-specific scope:** AC.OSS.2 (D-1) — `dispatch_with_scope` is
authored but has no production caller. M4 wires the disk-side setup
gates of the four-gate chain into the persona's actual Agent-dispatch
path via a PreToolUse hook on `Task`.

**Lens 1 — Claude-leverage-first:** **strong pass.** M4 leverages
Claude Code's native PreToolUse hook event on `Task` (the same surface
A4's `agent_guard.py` already inspects). No bespoke dispatch protocol
required; the hook composes alongside A2/A3/A4 in the existing
multi-contributor PreToolUse stanza per `merge_pre_tool_use`. The
four gates become a Claude-native interception surface — exactly the
shape master plan §12 Lens 1 names.

**Lens 2 — Harness + primary-persona test:**

- *Primary-persona test:* **strong pass.** Pre-M4, the persona's
  natural-language intent ("dispatch a sub-agent to do X with new ACs
  Y/Z") translates to a raw Task call that mints no manifest rows /
  no sentinel / no test stubs — the harness is half-asleep around the
  dominant traffic shape. Post-M4, the persona's Task dispatches with
  AC declarations automatically acquire the disk-side gates the
  harness was authored to provide. Translation burden between
  "persona declares ACs in the prompt" and "ACs are actually
  registered + sentinels written + stubs authored" drops from "manual
  multi-call orchestration" to "structural side-effect of a Task
  dispatch."
- *Harness test:* **strong pass.** The hook adds a queryable surface
  ("which Task dispatches authored which ACs?") downstream features
  can read via the agent-guard-style audit log. The four-gate setup
  primitive becomes a toolkit primitive the persona invokes
  implicitly — the same primitive sealed at amendment #74 — instead
  of a dormant export.

**Lens 3 — ODD authoring:** ODD §2.5 enforced — every changed line
maps to an explicit AC under AC.OSS-M4.1..AC.OSS-M4.7 (see §4).
Hook + helper + tests are the entire diff; no "while we're here"
edits.

---

## 3. Three-lens analysis

(Condensed — see §2 for the per-lens answers.)

### Lens 1 — Claude-leverage-first

PreToolUse hook on `Task` is the architecturally-aligned binding
mechanism per master plan §12 Lens 1 (already named in the plan).
Composes alongside A2/A3/A4's existing PreToolUse stanza. No new
hook event, no bespoke dispatch protocol, no MCP server. The hook
inspects `tool_input["prompt"]` for the AC-declaration marker and
applies the four gates before allowing the Task tool to fire — the
exact shape `dispatch_with_scope`'s setup phase authored at amendment
#74.

### Lens 2 — Harness + primary-persona value

The persona gains a structural-enforcement primitive that fires
implicitly on every AC-declaring Task dispatch. Pre-M4, the persona's
prompt could declare ACs verbally but no machinery would record them;
the dispatched agent could author code that no manifest row gates
(A2's objective-binding gate fires at first-edit time but reads the
manifest table, which would be empty for the new ACs). Post-M4, the
manifest rows + sentinel + stubs are in place before the agent's
first edit, so the agent's edits compose with A2/A3 cleanly.

### Lens 3 — ODD authoring

Every line in the M4 diff maps to one of the seven ACs (M4.1..M4.7).
ODD §2.5 enforced. No defensive `if` branches without a backing AC.

---

## 4. Acceptance criteria — AC.OSS-M4.*

### AC.OSS-M4.1 — PreToolUse hook on `Task` performs the disk-side setup phase

A new hook script `framework/hands-off-lifecycle/hooks/dispatch_setup_hook.py`
ships, registered in the multi-contributor PreToolUse stanza per
`merge_pre_tool_use` alongside A2/A3/A4. Matcher: `Task` (the same
matcher `agent_guard.py` uses; matcher independence — see master
plan precedent — means A4_task and the new dispatch_setup_hook share
the matcher and run sequentially per Claude Code's
deterministic-order semantics).

Given:
- workspace mode == `dev-mode`,
- a Task tool call whose `tool_input["prompt"]` contains an
  `<AC-MANIFEST>` … `</AC-MANIFEST>` block with one or more
  CSV rows of shape `component,ac_id,source_path_glob`,

the hook performs (in order, per AC.DSA.3):

  1. Writes the active-scope sentinel via
     `active_scope_sentinel.write_active_scope_sentinel(workspace_root, scope_id, plan_path, bindings)`.
  2. For each declared AC, calls
     `tracker.register_source_binding(component, ac_id, source_path_glob)`
     on the workspace's `ObjectiveTracker`.
  3. For each declared AC, writes the placeholder test stub at
     `framework/<component>/tests/test_AC_<NORM>_placeholder.py` via
     a NEW public helper `dispatch_wrapper.write_dispatcher_stub(...)`
     extracted from the existing `_write_stub_idempotent` (per
     AC.OSS-M4.4 below — this is the only addition to the
     `dispatch_wrapper.py` module: a thin public surface that
     re-exports the existing private helper's behaviour. The
     existing private helper + its callers stay untouched).
  4. Allows the Task tool to fire (empty stdout = allow per the
     A2/A3/A4 convention).

**Verification:** a unit test feeds the hook a synthetic PreToolUse
envelope with an `<AC-MANIFEST>` block and asserts (a) the sentinel
file exists at the expected path, (b) the tracker has manifest rows
for each declared AC, (c) the test stub files exist with the
expected content shape, (d) the hook's stdout is empty (allow).

**Test:** `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_1_setup_phase_runs.py` (new).

### AC.OSS-M4.2 — AC-declaration parsing handles well-formed and malformed input

The hook's parser:
- Recognises the `<AC-MANIFEST>` … `</AC-MANIFEST>` block (case-sensitive on the marker).
- Parses each non-empty interior line as `component,ac_id,source_path_glob` (CSV; `csv.reader` from stdlib).
- Skips blank lines and lines starting with `#` (comments).
- Treats a malformed row (wrong column count, empty component / ac_id / glob) as a parse failure that emits an NDJSON diagnostic and **does NOT halt the dispatch** (passthrough — fail-soft per AC.DSA.5 mirror).
- Treats a missing `<AC-MANIFEST>` block (the dispatch declares no
  ACs) as the legitimate `new_acs=()` case per AC.DSA.10 — passthrough,
  no setup phase fired.

**Verification:** unit tests covering: well-formed multi-row block;
single-row block; block with comment lines; block with blank lines;
malformed row (wrong column count); empty block; absent block;
case-sensitivity of the marker name.

**Test:** `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_2_ac_declaration_parsing.py` (new).

### AC.OSS-M4.3 — Composition with A2/A3/A4 + multi-contributor PreToolUse stanza

After M4, the multi-contributor PreToolUse outer list carries five
inner-hook envelopes:

  1. `objective_binding_gate.py` — matcher `Edit|Write|MultiEdit`.
  2. `tdd_guard.py` — matcher `Edit|Write|MultiEdit`.
  3. `bash_guard.py` — matcher `Bash`.
  4. `agent_guard.py` — matcher `Task`.
  5. `dispatch_setup_hook.py` — matcher `Task` (NEW).

A4's `agent_guard.py` and the new `dispatch_setup_hook.py` share the
`Task` matcher; they run sequentially per Claude Code's
deterministic-order semantics. **A4 runs first** (per the
established order in `_maybe_merge_pre_tool_use` — A2 → A3 →
A4_bash → A4_task; the new hook is appended in 5th position).
A4 may DENY the Task call (wrong-WD / method-enumerated /
stale-dispatch); the new hook is **idempotent** on re-fire and is
**NOT a refusal gate** — it always allows (or surfaces a parse
failure as a structured NDJSON diagnostic, then allows).

When A4 denies, Claude Code does not fire the underlying Task
tool, so the dispatch_setup_hook's disk-side side-effects are
**still authored** (the hook fires before the deny short-circuits
the tool execution). This is acceptable per AC.DSA.4 idempotency —
a re-dispatched Task with the same AC declarations will see the
sentinel + manifest rows already in place and short-circuit
correctly. The hook does NOT need to be conditional on A4's
verdict.

**Verification:** test composes a settings.json with the post-M4
PreToolUse stanza shape via `_maybe_merge_pre_tool_use` and asserts
all five inner hooks are registered in the expected order with the
expected matchers.

**Test:** `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_3_pre_tool_use_composition.py` (new).

### AC.OSS-M4.4 — Public stub-writer surface in `dispatch_wrapper`

`framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py`
gains exactly one NEW public function:

```python
def write_dispatcher_stub(
    workspace_root: Path,
    spec: NewACSpec,
    *,
    scope_id: str,
    plan_path: str,
) -> dict[str, Any]:
    """Public surface for the dispatcher-stub-authoring helper.

    Wraps the existing private `_write_stub_idempotent` so the
    PreToolUse hook (M4) can author placeholder test stubs without
    duplicating the byte-content shape (AC.DSA.2) outside its
    canonical owner. Idempotent per AC.DSA.4 — re-call on existing
    sentinel-authored stub returns ``"skipped-identical"`` /
    ``"skipped-agent-authored"`` per the existing semantics.

    Backs AC.OSS-M4.4 (M4 wire-dispatch) — the only addition to
    this module in M4. The existing `_write_stub_idempotent`,
    `_run_setup_phase`, `dispatch_with_scope`, and every other
    public/private surface stays untouched.
    """
    return _write_stub_idempotent(
        workspace_root, spec, scope_id=scope_id, plan_path=plan_path
    )
```

**Why this thin shape (D-build.M4.5):** the dispatch's out-of-scope
clause is "Changes to dispatch_with_scope itself (it's already
authored at amendments #52/#74)". A NEW additive public surface that
re-exports an existing helper's behaviour is **not a change to
dispatch_with_scope** — it's an additive export. The alternative
(replicating ~30 lines of stub-authoring logic in the hook) violates
DRY across two components and means any future change to
AC.DSA.2's byte-content shape needs to land in two places.

The function is exported from
`loam.primary_persona.dispatch_wrapper`; the hook imports it lazily
(stdlib-style `from loam.primary_persona.dispatch_wrapper import
write_dispatcher_stub`) inside the per-fire code path.

**Verification:** `from loam.primary_persona.dispatch_wrapper import
write_dispatcher_stub` succeeds; the function's behaviour matches
`_write_stub_idempotent` byte-for-byte (a single delegation
assertion).

**Test:** `framework/primary-persona/tests/test_AC_OSS_M4_4_public_stub_writer.py` (new).

### AC.OSS-M4.5 — Hook short-circuits on NORMAL USE workspaces

Per AC.DSA.6 mirror: the hook reads workspace mode via
`corpus_load_sentinel.workspace_mode(workspace_root)` and short-circuits
to `allow` (empty stdout, no setup phase) when mode != `dev-mode`. This
mirrors A2/A3/A4's mode-bit handling exactly — the structural-enforcement
gates are dev-only.

**Verification:** unit test feeds the hook a NORMAL USE workspace
mode + a well-formed `<AC-MANIFEST>` block; asserts (a) no sentinel
written, (b) no manifest rows registered, (c) no stub files authored,
(d) stdout empty (allow).

**Test:** `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_5_normal_use_short_circuit.py` (new).

### AC.OSS-M4.6 — Hook is fail-soft on substrate failures + emits structured NDJSON

Per AC.DSA.5 / AC.DSA.9 mirrors:
- Tracker unavailable / `register_source_binding` raises → emit one
  NDJSON line to `<workspace>/workspace/.pos/dispatch-setup-hook.log`,
  continue.
- Sentinel write fails → emit NDJSON, continue.
- Stub write fails → emit NDJSON, continue.
- Hook process exits 0 on every path (stdout empty = allow) per
  A2/A3/A4 fail-soft convention.

The audit log shape mirrors agent-guard's per-fire schema
(`ts`, `tool`, `prompt_length`, `cwd`, `mode`, `decision`,
`acs_declared`, `setup_outcome` per-step). The full prompt is NOT
recorded (privacy + size); the AC declarations + per-step outcomes
are.

**Verification:** unit tests covering: tracker unavailable; sentinel
write fails (read-only filesystem fixture); stub write fails. Each
asserts (a) hook exits 0, (b) NDJSON line appended, (c) the
non-failed steps still execute (e.g. sentinel succeeds even when
manifest fails).

**Test:** `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_6_fail_soft_diagnostic.py` (new).

### AC.OSS-M4.7 — No work outside the named surfaces (negative AC)

The M4 diff is contained to:

- `framework/hands-off-lifecycle/hooks/dispatch_setup_hook.py` (new — hook script, ~250-350 LOC including parser + setup-phase invocation + audit log + main).
- `framework/hands-off-lifecycle/hooks/first_run_helper.py` (extend `_maybe_merge_pre_tool_use` to register the new stanza; extend `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS` in `first_run_settings.py`; add `_dispatch_setup_hook_stanza(loam_root)` builder).
- `framework/hands-off-lifecycle/hooks/first_run_settings.py` (add `dispatch_setup_hook.py` marker to `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS`).
- `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py` (add NEW public function `write_dispatcher_stub` + add to `__all__`; ~10 LOC).
- `framework/primary-persona/src/loam/primary_persona/__init__.py` (re-export `write_dispatcher_stub`; ~2 LOC).
- `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_1_setup_phase_runs.py` (new, ~80 LOC).
- `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_2_ac_declaration_parsing.py` (new, ~120 LOC).
- `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_3_pre_tool_use_composition.py` (new, ~50 LOC).
- `framework/primary-persona/tests/test_AC_OSS_M4_4_public_stub_writer.py` (new, ~40 LOC).
- `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_5_normal_use_short_circuit.py` (new, ~40 LOC).
- `framework/hands-off-lifecycle/tests/test_AC_OSS_M4_6_fail_soft_diagnostic.py` (new, ~80 LOC).
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.oss-v0-1-0-publish-dispatch-with-scope` (new — narrative anchor).
- `docs/rebuild/plans/oss-v0-1-0-publish-dispatch-with-scope.md` (this plan-doc).
- `docs/rebuild/plans/oss-v0-1-0-publish-dispatch-with-scope.manifest.yaml` (the manifest).
- `framework/primary-persona/tests/SEAL_COMMIT` + `framework/hands-off-lifecycle/tests/SEAL_COMMIT` (sidecar bumps automatic via `loam amend seal`).

No other files are touched. No env-var renames. No CLI changes. No
existing test edits beyond the new-test-file additions.

**Verification:** `git diff BASELINE..HEAD --stat` post-build shows
only the surfaces listed above.

### AC.OSS-M4.S — Sealed-component fence: 2 components

The sealed-component fence covers exactly:

1. `primary-persona` (one new public function in `dispatch_wrapper.py` + one new test).
2. `hands-off-lifecycle` (one new hook + 5 new tests + minor extensions to first_run_helper.py + first_run_settings.py + a new narrative file at `framework/hands-off-lifecycle/seals/`).

Each component's seal-test (`framework/<comp>/tests/test_no_sealed_amendments.py`)
runs as part of the per-component sweep. The sidecar bump
(`framework/<comp>/tests/SEAL_COMMIT`) for each of the 2 happens at
seal time via `loam amend seal`.

### Behaviour-count check (ODD §3.3 forward)

**7 ACs (M4.1–M4.7) + 1 sealed-component AC (M4.S) = 8 named
acceptance points.** Each maps to a unique change in the diff. No
behaviour without a named AC.

---

## 5. Hard constraints (M4-specific)

1. **Plan-before-code.** This plan-doc is committed before any
   source edit. Sub-plan §14 anchor lives in this doc.
2. **`loam amend apply` runs BEFORE seal commit.** No exceptions
   per `feedback_dispatch_explicit_pos_amend_apply`.
3. **No `git commit --amend`.** Corrective commits are NEW commits
   per `feedback_no_amend_in_agent_dispatches`.
4. **AC.OSS.2 fence — every assertion is "Task tool calls with an
   AC declaration in the prompt cause the four disk-side gates to
   fire; AC declarations are parsed correctly; backwards-compat
   passthrough on no-AC dispatches is preserved."** No behaviour
   assertions about IPC-bound gates (those are out of scope per §6
   D-build.M4.1).
5. **Hard cutover, no transitional dual-path.** The hook is added
   to the PreToolUse stanza in a single commit; the new public
   stub-writer is added in the same commit. The dispatch's option-3
   passthrough-with-deprecation-log is NOT a transitional dual code
   path — it's the always-on behaviour for no-AC dispatches per
   AC.OSS-M4.2.
6. **Test scope narrow.** 6 new test files (5 in hands-off-lifecycle,
   1 in primary-persona). No regression re-runs of the full
   per-component test suites beyond what `loam amend seal --scoped-sweep`
   does automatically. Skip pre-seal full-suite per `feedback_amendment_dispatch_speedups`.
7. **Halt and surface** if the build agent encounters:
   - The PreToolUse hook chain has structural concerns that resist
     M4's addition (e.g. ordering matters with A1-A4 in unexpected
     ways) — pre-verified at plan-authoring: agent_guard's `Task`
     matcher is independent of A2/A3's `Edit|Write|MultiEdit` and
     A4_bash's `Bash`. A4_task (agent_guard) and dispatch_setup_hook
     (M4) share the `Task` matcher and run sequentially. No
     ordering inversion needed (agent_guard is a refusal gate;
     dispatch_setup_hook is not — they don't conflict on
     verdict).
   - `dispatch_with_scope` interface doesn't cleanly accept a
     Task-tool-call payload — pre-verified: the hook does NOT call
     `dispatch_with_scope` (which is async + IPC-bound); it calls
     the disk-side helpers directly (`write_active_scope_sentinel`,
     `tracker.register_source_binding`, `write_dispatcher_stub`).
     Surfaces if any of those helpers' signatures don't match the
     hook's needs.
   - AC declaration parsing requires a structured format the
     dispatch protocol hasn't standardized — resolved at plan time
     by D-build.M4.2 (`<AC-MANIFEST>` CSV format; recommendation
     locked).
   - ODD §2.5 violations.
   - PreToolUse hook can't access the `Task` tool's input — pre-
     verified: agent_guard.py reads `tool_input.get("prompt")` (line
     298) and the prompt is reliably a string in Claude Code's
     PreToolUse JSON envelope.
   - The hook fires recursively when `dispatch_with_scope` itself
     dispatches sub-agents — resolved at plan time by D-build.M4.4
     (env-var bypass + sentinel-already-written short-circuit). Today
     no production caller invokes `dispatch_with_scope` so recursion
     is theoretical; the bypass surface lands as design-for-future,
     not a behavioural test.
8. **Strict autonomy.** The build agent does not pause on
   authorized work per `feedback_strict_autonomy_no_pause_for_authorized_work`.
   The hook + helper + 6 tests + composition + seal flow are all
   in-scope and authorized; the agent completes them autonomously.

---

## 6. Out of scope (named explicitly per ODD §2.5)

- **Any change to the IPC-bound four-gate chain.** `activate_scope_with_spec`,
  `record_dispatch_close`, cost-governance reservation, safety wrap,
  reversibility wrap, orchestrator wrap — all stay exactly as
  amendments #52 / #74 sealed them. M4 wires the disk-side setup
  phase only (per §1's critical architectural finding).
- **Any change to `dispatch_with_scope`'s end-to-end flow.** The
  async wrapper, the IPC client opening, the IPC method calls, the
  budget reservation, the agent_runner invocation, the
  record_dispatch_close emit — all preserved untouched.
- **Any change to `_run_setup_phase` or `_write_stub_idempotent`.**
  M4 adds a NEW thin public wrapper `write_dispatcher_stub` that
  delegates; the existing private helpers stay byte-identical.
- **Any change to A2/A3/A4 hooks.** The new hook composes alongside;
  no edits to objective_binding_gate.py / tdd_guard.py / bash_guard.py
  / agent_guard.py.
- **Persona prompt edits.** Per dispatch out-of-scope: persona-
  prompt-driven routing is the alternative mechanism we're declining;
  M4 chooses the structural enforcement path.
- **PostToolUse hook on `Task` for `record_dispatch_close`.** A
  future amendment could close the IPC chain end-to-end via a
  PostToolUse hook that records the dispatch close. NOT in M4 scope
  per §1 — IPC chain stays out.
- **CLI for the dispatch-setup hook.** The hook is invoked by
  Claude Code, not by an operator. No `loam-dispatch-setup` binary.
- **Plan-doc reference recording as a separate field.** The
  dispatch's enumeration of four gates names "plan-doc reference
  recording" as gate #4; the existing sentinel record's `plan_path`
  field already covers it (per AC.DSA.3 sentinel content schema).
  M4 does not author a new field — it surfaces the existing one
  into the hook's input.
- **M5 / M6 / M7 / M8 / M9 / M10 / M11 / M12.**

---

## 7. Implementation order (suggested — builder's call to refine)

The build agent's exact ordering is its call. Suggested order
(designed to keep the tree in a passing state at each step):

1. **Author the manifest.** `docs/rebuild/plans/oss-v0-1-0-publish-dispatch-with-scope.manifest.yaml`.
2. **Add `write_dispatcher_stub` to `dispatch_wrapper.py`** + add to `__all__`. Add to `framework/primary-persona/src/loam/primary_persona/__init__.py`'s exports.
3. **Author the unit test for the public stub-writer surface.** `framework/primary-persona/tests/test_AC_OSS_M4_4_public_stub_writer.py`. Run it; confirm green.
4. **Author the hook script.** `framework/hands-off-lifecycle/hooks/dispatch_setup_hook.py`. Stdlib + sibling-import for `active_scope_sentinel`, lazy import for `loam.primary_persona.dispatch_wrapper.write_dispatcher_stub` and `loam.objective_tracker.ObjectiveTracker` (mirrors agent_guard's lazy-import pattern). The hook's `evaluate(...)` function returns a `Decision` containing the parse outcome + per-step setup results. The hook's `main(argv)` reads the PreToolUse JSON envelope from stdin and emits empty stdout (allow) on every path.
5. **Author 5 hooks tests.** Each is a stdlib-only test that
   stubs `corpus_load_sentinel` + `loam.objective_tracker` modules
   via monkeypatch (mirrors the test_AC_AG_*.py pattern) and feeds
   synthetic envelopes:
   - `test_AC_OSS_M4_1_setup_phase_runs.py` — well-formed
     `<AC-MANIFEST>` block; assert sentinel + manifest rows + stubs
     authored.
   - `test_AC_OSS_M4_2_ac_declaration_parsing.py` — parser unit
     tests covering all parse cases.
   - `test_AC_OSS_M4_3_pre_tool_use_composition.py` — composition
     test using `_maybe_merge_pre_tool_use` + asserting 5-stanza
     outer list.
   - `test_AC_OSS_M4_5_normal_use_short_circuit.py` — NORMAL USE
     mode short-circuit.
   - `test_AC_OSS_M4_6_fail_soft_diagnostic.py` — fail-soft on
     tracker / sentinel / stub failures.
6. **Extend `first_run_helper.py`** with `_dispatch_setup_hook_stanza(loam_root)` builder and add it to the list passed to `merge_pre_tool_use`.
7. **Extend `first_run_settings.py`** by appending `"dispatch_setup_hook.py"` to `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS`.
8. **Run the 6 new tests.** Confirm green.
9. **Run touched-component tests** — `pytest framework/{primary-persona,hands-off-lifecycle}/tests/` — confirm no regressions (the additions are additive; existing tests don't import the new hook or new public stub-writer surface).
10. **Feature commit.** `feat(wire-dispatch): M4 PreToolUse hook on Task routes through four-gate setup phase`.
11. **`loam amend apply`** with the M4 manifest. Verify it produces the expected sidecar bumps + narrative file.
12. **Apply commit.** `chore(wire-dispatch-apply): loam amend apply for amendment #85 (M4 wire dispatch-with-scope)`.
13. **`loam amend seal`** — runs touched + sweep tests + writes deterministic seal commit + verifies post-seal `apply --dry-run`.
14. **Post-seal:** §14 method-decision register filled in this plan-doc with actual SHAs; §14 backfill commit per M2/M3 precedent.

---

## 8. Halt triggers (M4-specific)

The build agent halts and surfaces if any of these occur:

1. **A2/A3/A4 hooks have moved or renamed since plan-authoring.**
   Pre-verified at plan-authoring: `_maybe_merge_pre_tool_use` lives at
   `framework/hands-off-lifecycle/hooks/first_run_helper.py:576-607`
   with explicit registrations of objective_binding_gate, tdd_guard,
   bash_guard, agent_guard. If at build time any of those four are
   moved / renamed / replaced, HALT and surface — the hook chain
   composition assumptions might no longer hold.
2. **`active_scope_sentinel.write_active_scope_sentinel` signature has
   changed.** Pre-verified: signature is `(workspace_root, *, scope_id,
   plan_path, bindings) -> Result`. If at build time the signature
   differs, surface; the hook's call site must match exactly.
3. **`tracker.register_source_binding` API has changed.** Pre-verified:
   the tracker accepts `(component, ac_id, source_path_glob)` per
   amendment #74 wiring. Surface if the API differs.
4. **`_write_stub_idempotent` signature has changed.** Pre-verified:
   `(workspace_root, spec, *, scope_id, plan_path) -> dict`. Surface
   if differs.
5. **The `<AC-MANIFEST>` marker name collides with existing
   prompt-template content.** Pre-verified at plan-authoring time via
   `grep -rn "AC-MANIFEST" framework/ docs/` — no matches outside
   this plan-doc. If at build time a collision exists, surface and
   propose an alternative marker (`<LOAM-AC-MANIFEST>` or
   `<DISPATCH-ACS>`).
6. **ODD §2.5 violation discovered in surrounding hook code.** Per
   `feedback_subagent_odd_violation_halt`, the build agent must halt
   if the new hook (or any code it touches) carries a path without
   AC backing. Surface; do not silently extend.
7. **The PreToolUse stanza schema has changed.** Pre-verified:
   `merge_pre_tool_use` accepts `new_entries: list[dict]` per
   `first_run_settings.py:627-665`. Surface if the schema differs.
8. **`loam amend apply` rejects the manifest** for any reason —
   surface and resolve before proceeding (per
   `feedback_dispatch_explicit_pos_amend_apply`).
9. **Seal-test failure on either component** after the changes —
   surface; the additions are additive but the seal test inspects
   the diff against the manifest's allowed prefixes.
10. **Cross-component import circularity.** The hook imports
    `loam.primary_persona.dispatch_wrapper.write_dispatcher_stub` —
    primary-persona currently has no import dependency on
    hands-off-lifecycle's hooks (the dispatch_wrapper itself uses
    lazy imports for `active_scope_sentinel`). The new hook's
    direction is hands-off-lifecycle → primary-persona, which is
    the same direction primary-persona's existing tests import (no
    cycle). Verify at build time; surface if a cycle emerges.

---

## 9. Risks (M4-specific)

1. **Hook short-circuits on A4 deny.** When A4's agent_guard denies
   a Task call (wrong-WD, method-enumerated, stale-dispatch), Claude
   Code does not fire the underlying Task tool, but the new
   dispatch_setup_hook still fires (it runs in PreToolUse before
   tool execution). This means the disk-side gates are authored
   even for denied dispatches. Mitigation: AC.DSA.4 idempotency —
   re-fire on a corrected re-dispatch is safe. The "wasted" disk
   writes are bounded (one sentinel + N manifest rows + N stubs per
   denied dispatch); negligible vs the alternative of inspecting
   A4's verdict from the new hook (which would require reading
   agent-guard.log and is fragile). Builder records the actual
   behaviour at build time in §14 D-build.M4.6.
2. **AC declaration format requires builder vigilance in dispatch
   prompts.** Post-M4, dispatches that author new ACs MUST include
   an `<AC-MANIFEST>` block in the prompt. This is a process
   change for the dispatcher (the persona / the builder writing
   sub-plans). Mitigation: option-3 passthrough on no-AC
   dispatches preserves backwards-compat; the deprecation NDJSON
   surfaces no-AC build dispatches for audit. Persona-prompt
   guidance for the AC declaration shape is OUT of M4 scope per §6;
   it lands in M7's docs lane or in a future amendment.
3. **Lazy-import path for `loam.primary_persona`.** The hook is
   invoked by Claude Code under `${LOAM_REPO}/.venv/bin/python`
   (per the agent_guard stanza pattern). The shared venv has
   primary-persona installed editable, so
   `loam.primary_persona.dispatch_wrapper` is importable. If at
   build time the venv is stale, the import fails — fail-soft
   per AC.OSS-M4.6 means the hook emits an NDJSON diagnostic and
   passes through without authoring stubs. The sentinel + manifest
   rows still fire (those don't depend on primary-persona's import).
   Mitigation: editable-install refresh is M3-precedent (`pip install
   -e framework/primary-persona/`); the venv is current as of M3
   seal `95f1ab2`. M4 doesn't add new pyproject changes, so no
   refresh needed.
4. **Recursion concern (theoretical).** If a future amendment wires
   `dispatch_with_scope`'s `agent_runner` to call the Task tool
   from inside Claude (rather than via SDK direct), the new hook
   would re-fire on each inner dispatch. AC.DSA.4 idempotency makes
   re-fire safe but wasteful. Mitigation: D-build.M4.4 records
   `LOAM_DISPATCH_BYPASS_HOOK=1` env-var as a future bypass surface;
   the hook checks for this env-var early and short-circuits when
   set. Today no production caller invokes `dispatch_with_scope`,
   so the env-var is design-for-future.
5. **`merge_pre_tool_use` displaces prior PreToolUse stanzas.** The
   merge function is amendment-#45-style multi-contributor — appending
   a 5th entry should be additive, not displacing. Verify at build
   time that the existing 4 entries remain after the merge.

---

## 10. Decisions remaining for owner ruling

**None requiring owner ruling.** The plan resolves every design
decision via dispatch authority (master plan §5 + dispatch
constraints) + plan-side recommendations. Decisions are recorded
below for the §14 register.

### D-build.M4.1 — Setup-phase-only hook vs full IPC chain

**Decision:** the M4 hook applies the **disk-side setup phase only**
(sentinel + manifest rows + test stubs + plan-doc reference via
sentinel's plan_path field). The IPC-bound chain (cost / safety /
reversibility / orchestrator gate chain inside `activate_scope_with_spec`)
stays as the explicit-call surface for in-process callers of
`dispatch_with_scope`. The dispatch's enumeration of "four gates" is
satisfied by the four disk-side gates per §1.

**Why this shape over alternatives:**
- *Alternative: hook calls `dispatch_with_scope` directly via async-loop
  spin-up.* Rejected — Claude Code's PreToolUse hook is a sync stdlib
  process that cannot easily run an async IPC client + agent_runner;
  the wrapper's IPC chain assumes the orchestrator socket is reachable
  + budget reservation can be debited; both are heavy operations
  unsuitable for a 5-second-timeout PreToolUse hook.
- *Alternative: hook performs disk-side gates AND opens an IPC client
  to call `activate_scope_with_spec` (no agent_runner; the underlying
  Task tool runs separately).* Rejected — the IPC method is designed
  for full lifecycle (`activate_scope_with_spec` + `record_dispatch_close`).
  Without `record_dispatch_close` the scope state never transitions
  to terminal; the cost ledger leaks. A future PostToolUse-hook
  amendment could close this loop, but it's NOT in M4.
- *Alternative: hook denies non-`dispatch_with_scope` Task calls,
  forcing all dispatches through the persona-callable wrapper.*
  Rejected — Claude Code's Task tool is the only Agent-dispatch
  surface available to the persona inside a Claude Code session;
  denying Task with no alternative routing path bricks the persona's
  dispatch capability.

### D-build.M4.2 — AC declaration format in dispatch prompts

**Decision:** an HTML-style block marker
`<AC-MANIFEST>` … `</AC-MANIFEST>` carrying CSV rows of shape
`component,ac_id,source_path_glob`. Stdlib-parseable (csv.reader);
visually scannable; namespace-segregated.

Example:

```
<AC-MANIFEST>
primary-persona,AC.A8.1,framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py
primary-persona,AC.A8.2,framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py
hands-off-lifecycle,AC.AG.1,framework/hands-off-lifecycle/hooks/agent_guard.py
</AC-MANIFEST>
```

**Why this shape over alternatives:**
- *Alternative: YAML frontmatter at the top of the prompt.* Rejected —
  YAML in stdlib is `pyyaml`; the hook is stdlib-only per the
  established hook convention. Adding a YAML dependency for hook
  parsing is overkill.
- *Alternative: JSON block.* Rejected — JSON's quoting requirements
  make multi-row declarations unreadable in a natural-language
  prompt.
- *Alternative: ad-hoc regex parsing of natural-language AC mentions.*
  Rejected — false-positive prone; a structured marker disambiguates.

### D-build.M4.3 — Passthrough vs refusal on no-AC dispatches

**Decision:** **passthrough with one-line NDJSON deprecation log** per
dispatch's option 3. The wrapper itself supports `new_acs=()` as a
fully-supported call path (AC.DSA.10 backwards-compat); mirror that
semantic in the hook. Hard refusal would break every research/plan
dispatch.

The deprecation log is one NDJSON line per fire to
`<workspace>/workspace/.pos/dispatch-setup-hook.log` carrying
`{"event":"no-ac-declaration","prompt_length":N,"cwd":...,"ts":...}`.
Future amendments can audit this log to characterise the no-AC
traffic shape and rule on whether tightening to refusal is
warranted.

### D-build.M4.4 — Recursion handling for `dispatch_with_scope` sub-dispatches

**Decision:** env-var bypass `LOAM_DISPATCH_BYPASS_HOOK=1` + sentinel-already-written short-circuit (idempotency per AC.DSA.4 covers this implicitly).

Today no production caller invokes `dispatch_with_scope`, so recursion is theoretical. M4 records the design awareness:
- The hook checks `os.environ.get("LOAM_DISPATCH_BYPASS_HOOK") == "1"` early; if set, short-circuit to allow without authoring.
- Any future wiring of `dispatch_with_scope`'s `agent_runner` to call the Task tool sets the env-var on the inner dispatch.

The env-var name is `LOAM_*` per M1b's rebrand convention.

### D-build.M4.5 — `write_dispatcher_stub` placement (in dispatch_wrapper vs in hook)

**Decision:** add a NEW thin public function `write_dispatcher_stub` to `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py`. The function delegates to the existing private `_write_stub_idempotent`. Existing helper + every existing caller stays untouched.

**Why this shape over alternatives:**
- *Alternative: replicate `_write_stub_idempotent` inline in the hook.* Rejected — DRY violation; AC.DSA.2 byte-content shape lives in two places.
- *Alternative: rename `_write_stub_idempotent` to public.* Rejected — invasive change to existing module's public surface; risk of breaking implicit API contracts of the existing helper.
- *Alternative: import the private `_write_stub_idempotent` from the hook.* Rejected — leaking-abstraction; private symbols shouldn't be imported across components per Python convention.

The public surface adds ~10 LOC (a docstring + a one-line delegation). Out-of-scope-clause respected: the IPC-bound dispatch_with_scope flow + the existing private helper + every existing caller stays byte-identical.

### D-build.M4.6 — Sealed-component fence membership

**Decision:** the 2 components — `primary-persona` and `hands-off-lifecycle`. Both have real diff (primary-persona: 1 new public function + 1 new test; hands-off-lifecycle: 1 new hook + 5 new tests + minor helper.py extensions + narrative file). Both bump sidecars at seal time.

### D-build.M4.7 — Test layout: per-component split

**Decision:** 5 tests in hands-off-lifecycle, 1 test in primary-persona — matches per-component test ownership. Total: 6 new test files.

---

## 11. Halt-and-surface findings encountered during plan authoring

### Finding #1 — Claude Code PreToolUse hooks cannot wrap tool execution

**Surface:** Claude Code's PreToolUse hook protocol allows only `permissionDecision: "allow" | "deny" | "ask"` outputs; it cannot run the agent on Claude's behalf nor substitute the tool's execution. The existing hooks (objective_binding_gate, tdd_guard, bash_guard, agent_guard) all operate as gate-only refusal/allow surfaces — they do not "wrap" the underlying tool.

**Resolution:** §1 + §6 + D-build.M4.1 — the M4 hook performs the disk-side setup phase (sentinel + manifest rows + test stubs + plan-doc reference) BEFORE allowing the Task tool to fire. The IPC-bound chain (activate_scope_with_spec / record_dispatch_close / cost-governance reservation) is OUT of M4 scope. The dispatch's enumeration of four gates is satisfied by the disk-side four — which IS what amendments #52 / #74 named the setup-phase gates.

**Audit consequence:** the dispatch language "routes through `dispatch_with_scope`" is conceptually accurate but mechanically reframed: the hook applies the same disk-side side-effects that `dispatch_with_scope`'s setup phase applies, without invoking the wrapper itself. This preserves the dispatch's dispatch-authority intent while accommodating Claude Code's hook-protocol reality.

### Finding #2 — `dispatch_with_scope` is async; hooks are sync

**Surface:** `dispatch_with_scope` is `async def` (line 795) and uses `await client.connect()` / `await client.call(...)`. The PreToolUse hook is invoked as a sync stdlib subprocess.

**Resolution:** the hook does NOT call `dispatch_with_scope`; it calls the disk-side helpers directly (`write_active_scope_sentinel`, `tracker.register_source_binding`, `write_dispatcher_stub`). Each of these is sync — verified at plan-authoring.

### Finding #3 — `_write_stub_idempotent` is private; hook needs a public surface

**Surface:** the stub-authoring logic lives at `dispatch_wrapper.py:514-589` as `_write_stub_idempotent(workspace_root, spec, *, scope_id, plan_path)`. Private (leading `_`). The hook needs to call this logic without violating Python's "private symbols stay in-module" convention.

**Resolution:** AC.OSS-M4.4 + D-build.M4.5 — add a NEW public function `write_dispatcher_stub` that delegates to the existing private helper. ~10 LOC additive change. Out-of-scope clause respected (existing dispatch_with_scope flow + private helper + every existing caller untouched).

### Finding #4 — The `<AC-MANIFEST>` marker is unused elsewhere in the tree

**Surface:** verified at plan-authoring time:

```
$ grep -rn "AC-MANIFEST" framework/ docs/ 2>/dev/null
(no matches outside this plan-doc)
```

**Resolution:** safe to use as the namespace-segregated marker per D-build.M4.2. No collision risk.

### Finding #5 — A4's `agent_guard.py` and the new dispatch_setup_hook share matcher `Task`

**Surface:** `agent_guard.py` matcher is `Task` (per `_agent_guard_stanza`); the new dispatch_setup_hook matcher must also be `Task`. Claude Code admits multiple matcher entries under one event and runs them sequentially per matcher.

**Resolution:** AC.OSS-M4.3 documents the composition. Order: A4 runs first (refusal gate); dispatch_setup_hook runs second (non-refusal; always allows). When A4 denies, the dispatch_setup_hook still fires before Claude Code short-circuits the tool — wasted-side-effect risk noted in §9.1; mitigated by AC.DSA.4 idempotency.

### Finding #6 — No HC#4 byte-content sample paths under primary-persona or hands-off-lifecycle impacted by the M4 diff

**Surface:** verified at plan-authoring time — the M4 diff is (a) ~10 LOC additive in `dispatch_wrapper.py` (NEW function `write_dispatcher_stub`, NEW name in `__all__`), (b) ~250-350 LOC NEW hook script, (c) minor extensions to `first_run_helper.py` + `first_run_settings.py` (additive list extension), (d) 6 new test files, (e) NEW narrative file under HOL/seals. None of these touch existing HC#4 sample paths.

**Resolution:** NO RETIRE-AND-REBASELINE. HC#4 invariant expected to remain GREEN through M4.

---

## 12. Method-decision register (placeholder)

(See §14 for the post-build narratives + commit SHAs.)

---

## 13. Test breakdown (post-build)

Six new test files, total ~410-430 LOC across all six:

1. **`framework/hands-off-lifecycle/tests/test_AC_OSS_M4_1_setup_phase_runs.py`** — feeds a synthetic PreToolUse envelope with a well-formed `<AC-MANIFEST>` block; asserts sentinel exists, manifest rows registered, stub files authored.
2. **`framework/hands-off-lifecycle/tests/test_AC_OSS_M4_2_ac_declaration_parsing.py`** — parser unit tests covering: well-formed multi-row, single-row, comment lines, blank lines, malformed row, empty block, absent block, marker-name case-sensitivity.
3. **`framework/hands-off-lifecycle/tests/test_AC_OSS_M4_3_pre_tool_use_composition.py`** — composes settings.json via `_maybe_merge_pre_tool_use` and asserts 5-stanza outer list with expected matchers + commands.
4. **`framework/primary-persona/tests/test_AC_OSS_M4_4_public_stub_writer.py`** — `write_dispatcher_stub` exists, is exported from `loam.primary_persona`, and delegates to the existing private helper.
5. **`framework/hands-off-lifecycle/tests/test_AC_OSS_M4_5_normal_use_short_circuit.py`** — NORMAL USE workspace-mode short-circuit (no setup phase fires).
6. **`framework/hands-off-lifecycle/tests/test_AC_OSS_M4_6_fail_soft_diagnostic.py`** — fail-soft on tracker / sentinel / stub failures + structured NDJSON appended.

**No end-to-end Claude-runtime test.** Per dispatch constraint "test scope narrow"; the unit tests assert each AC's outcome at the function-boundary level. Integration with a real Claude Code session is a deployment-time concern verified by the persona authoring its first AC-declaring dispatch post-M4.

### Cross-tree verification

The hook imports `loam.primary_persona.dispatch_wrapper.write_dispatcher_stub`. The primary-persona installable distribution must be on the shared venv's `sys.path` for the import to resolve. M3 sealed at `95f1ab2` confirmed editable-install for primary-persona (and 4 other components). M4 adds no pyproject changes — no editable-install refresh needed.

### Backwards-compat verification

- Existing `_write_stub_idempotent` function in `dispatch_wrapper.py` preserved byte-identical.
- Existing `_run_setup_phase` function preserved byte-identical.
- Existing `dispatch_with_scope` callable preserved byte-identical.
- All existing AC.A8.* and AC.DSA.* tests continue passing (no API change).
- Existing PreToolUse stanza shape (4 inner hooks) extends to 5; A2/A3/A4 entries preserved exactly.

### HC#4 byte-content sample status

NO RETIRE-AND-REBASELINE per §11 finding #6.

### Dependents cleared to dispatch (post-M4)

- M5 (wire-dormancy) — independent in scope from M4 (touches workspace-bootstrap + dormancy + orchestrator). Cleared.
- M6, M7, M8, M9 — not gated on M4.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill;
method-decision narratives populated by builder during build.)

### D-build.M4.1 — Setup-phase-only hook vs full IPC chain

(Populated at build time. Recommendation per §10 D-build.M4.1: hook
applies disk-side setup phase only; IPC chain stays as explicit-call
surface. Builder records actual hook scope + any deviation.)

### D-build.M4.2 — AC declaration format in dispatch prompts

(Populated at build time. Recommendation per §10 D-build.M4.2:
`<AC-MANIFEST>` … `</AC-MANIFEST>` CSV block. Builder records actual
marker name used + any deviations.)

### D-build.M4.3 — Passthrough vs refusal on no-AC dispatches

(Populated at build time. Recommendation per §10 D-build.M4.3:
passthrough with NDJSON deprecation log. Builder records actual
behaviour + log shape.)

### D-build.M4.4 — Recursion handling

(Populated at build time. Recommendation per §10 D-build.M4.4:
`LOAM_DISPATCH_BYPASS_HOOK=1` env-var bypass + sentinel-already-written
idempotency. Builder records actual env-var name used + bypass
mechanism.)

### D-build.M4.5 — `write_dispatcher_stub` placement

(Populated at build time. Recommendation per §10 D-build.M4.5: NEW
public function in `dispatch_wrapper.py` delegating to existing private
helper. Builder records actual signature + LOC delta.)

### D-build.M4.6 — Sealed-component fence membership

(Populated at build time. Recommendation per §10 D-build.M4.6:
2 components — primary-persona + hands-off-lifecycle. Builder records
actual fence + sidecar bumps.)

### D-build.M4.7 — Test layout

(Populated at build time. Recommendation per §10 D-build.M4.7:
5 tests in HOL, 1 in primary-persona. Builder records actual layout +
LOC totals.)

### Commit SHAs

- Plan-doc commit: `<TBD>`
- Manifest commit (often same as plan-doc commit): `<TBD>`
- Feature commit: `<TBD>`
- Apply commit: `<TBD>`
- Corrective commits (if any): `<TBD>`
- Seal commit: `<TBD>`
- §14 SHA-register backfill commit: `<TBD>`

---

## 15. References

- **Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md`
  (M4 row in §5; sequencing rule #3 in §6; AC.OSS.2 in §3).
- **Programme predecessors:**
  - M1.rename series — sealed M1a..M1g 2026-04-29 (M1g seal `f6c22fd`; §14 backfill `d5b8dcd`).
  - M2.partition — sealed `4cda805` 2026-04-29 (§14 backfill `bb3574c`).
  - M3.wire-clis — sealed `95f1ab2` 2026-04-29 (§14 backfill `6751b94`).
- **Authority documents (inherited from programme master):**
  - `.scratch/claude-output/feature-usage-audit.md` D-1 (line 366 — `dispatch_with_scope` has zero non-test callers).
- **Existing wrapper (DO NOT MODIFY beyond the AC.OSS-M4.4 thin public addition):**
  - `framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py` (amendment #52 + #74 sealed; AC.A8.1..AC.A8.11 + AC.DSA.1..AC.DSA.10).
- **Existing PreToolUse hooks (compose alongside):**
  - `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (matcher `Edit|Write|MultiEdit`).
  - `framework/hands-off-lifecycle/hooks/tdd_guard.py` (matcher `Edit|Write|MultiEdit`).
  - `framework/hands-off-lifecycle/hooks/bash_guard.py` (matcher `Bash`).
  - `framework/hands-off-lifecycle/hooks/agent_guard.py` (matcher `Task`).
- **Existing setup-phase substrate:**
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (`write_active_scope_sentinel`).
  - `framework/objective-tracker/src/loam/objective_tracker/__init__.py` (`ObjectiveTracker.register_source_binding`).
- **Hook composition site:**
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py:576-607` (`_maybe_merge_pre_tool_use`).
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py:148-162` (`_LOAM_PRE_TOOL_USE_COMMAND_MARKERS`).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-loam:** `docs/odd-methodology.md`, `docs/odd-in-loam.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward:**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
  - `feedback_critical_thinking_on_deviations`.
  - `feedback_strict_autonomy_no_pause_for_authorized_work`.
  - `feedback_value_proposition_as_prime_objective`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.manifest.yaml` (M3 — closest predecessor; multi-component fence shape).
  - `docs/rebuild/plans/agent-dispatch-as-scope-wrapper.manifest.yaml` (amendment #52 — original `dispatch_with_scope` authoring).

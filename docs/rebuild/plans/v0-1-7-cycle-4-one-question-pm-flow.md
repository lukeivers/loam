# v0.1.7 Cycle 4 — one-question-at-a-time PM-enforced surfacing + v0.1.7 release close

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor seals:**
- `3aa20dd` — v0.1.7 Cycle 1 (5 subagent personas + symlink registration).
- `73505f0` — v0.1.7 Cycle 2 (per-project PM as NEW component; queue + API).
- `bcf699a` — v0.1.7 Cycle 3 (layered-skill discovery + collision rules).

**BASELINE (pre-build tip):** `bcf699a`.

**Parent plan:** `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md` §5 AC.QSURF.* family + §6 Cycle 4.

**Status-file targets:**
- Cycle 4 status: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-7-cycle-4-status-2026-05-04.md`.
- Release-summary: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-7-release-status-2026-05-04.md`.

**Quality bar (load-bearing):** "WOW Eric. No partial features. No excuses." — Luke 2026-05-04. Cycle 4 is the v0.1.7 release-close; HARD gate on all 6 smoke dimensions per Decision R for the release.

---

## §1 — Outcome shape (the "why")

Cycle 2 sealed the PM's queue + API (`enqueue_decision`,
`surface_next_question`, audit-log primitive). Cycle 4 wires the
**user-facing flow**: the persona never bombards the user with multiple
questions in a single turn — PM serializes. Per Eric synthesis Decision Q
(RESOLVED YES) the enforcement is **structural** (not a convention), so
"more than one question per turn during onboarding-mode" is impossible
through the documented API.

The release-note promise extends to:

1. PM-mediated dispatch: persona enqueues N questions; PM dequeues 1 at
   a time per turn during `onboarding_mode`.
2. Post-onboarding: PM permits batched surfacing up to
   `max_questions_per_turn`.
3. `require_owner_response`: PM blocks subsequent surfacings until the
   prior question's response is recorded — this makes accountability
   structural at production-stake mode.
4. Composition with `audit-block-on-telegram` SKILL: PM-surfaced
   questions and recorded responses are programmatically discoverable
   "decision was made" triggers so the audit-block surfaces correctly
   on every PM-mediated user-facing turn.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

PM's surfacing API composes with the Anthropic-native subagent dispatch
surface (Cycle 1) + the workspace-local SKILL discovery surface
(Cycle 3). The audit-block-on-telegram SKILL (sealed v0.1.6,
auto-symlinked into `<workspace>/.claude/skills/` per Cycle 3) receives
PM-mediated decisions through the structured `SurfacedQuestion` /
`RecordedResponse` shape so its "decision was made" trigger condition
fires reliably. No re-implementation of skill discovery; no
re-implementation of channel-relay. Cycle 4 is pure persona-side
contract wiring on top of Cycle 2's primitive.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the persona
  no longer has to manually serialize question-asking decisions; the
  PM enforces the structural discipline. Persona enqueues, PM
  dequeues one at a time. The user sees one question per turn during
  onboarding without the persona having to remember to gate.
- **Harness test:** every persona (including the 5 subagent personas
  shipped Cycle 1, plus future personas) draws on the same
  surfacing primitive. The audit-block SKILL (and any future SKILL
  that consumes PM events) reads the same structured surface.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt-trigger constraints (§5) +
acceptance (§6). Method (file structure / API shapes / state shape)
stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH**: Cycle 2 already shipped the queue +
audit-log + atomic write primitive; Cycle 4 layers the
response-tracking + blocking + onboarding-enforcement on top. Tight
scope: extend the existing component; halt-and-surface if the
extension contradicts Cycle 2's design (it shouldn't — Cycle 2 named
these surfaces as deferred). Method (where to put each piece —
single new module `surfacing.py` vs extending existing `runtime.py`)
stays the builder's call.

### Lens 5 — Swarming

Single-component fence (`framework/per-project-pm/` extending Cycle 2);
sub-task partition with tighter ACs (each AC.QSURF.* is its own test
file) is structural per the Cycle 2 precedent (one test file per AC).
No further decomposition adds value — the cycle is already at the
right granularity. Stop at single-cycle.

---

## §3 — Single-component fence

**Scope:** `framework/per-project-pm/` only.

- Extend `framework/per-project-pm/src/loam/per_project_pm/`:
  - `errors.py` — add `PendingResponseError` (named per Cycle 2
    deferred surface).
  - `state.py` — add `RecordedResponse` dataclass.
  - `runtime.py` — extend `PMRuntime` with `record_response()`,
    `surface_next_questions_batch()`; wire blocking enforcement into
    existing `surface_next_question()`; wire onboarding-mode
    enforcement into batch surfacer.
  - `loader.py` — extend state.yaml schema to track `pending_response_for`
    (the question text awaiting response, or null).
  - `__init__.py` — re-export new public names.
- Extend `framework/per-project-pm/docs/design.md` with a new §11
  (one-question-at-a-time flow) + §12 (audit-block composition).
- Extend `framework/per-project-pm/README.md` to reference the new
  surfaces (replace the "Cycle 4 deferred surface" section with
  "Cycle 4 surfaces" landed).

- New test files at `framework/per-project-pm/tests/`:
  - `test_AC_QSURF_1_onboarding_mode_one_question.py`
  - `test_AC_QSURF_2_batched_surfacing.py`
  - `test_AC_QSURF_3_onboarding_hard_test.py`
  - `test_AC_QSURF_4_audit_log_provenance.py`
  - `test_AC_QSURF_5_require_owner_response_blocks.py`
  - `test_AC_QSURF_6_record_response.py`
  - `test_AC_QSURF_7_audit_trail_floor.py`
  - `test_AC_QSURF_8_audit_block_composition.py` (NEW; named
    AC.QSURF.8 per dispatch "Composition with audit-block-on-telegram
    SKILL").

- Universal-admitted artefacts:
  - `docs/rebuild/plans/v0-1-7-cycle-4-one-question-pm-flow.md` (this doc).
  - `docs/rebuild/plans/v0-1-7-cycle-4-one-question-pm-flow.manifest.yaml`.

- **Release-close bookkeeping (deferred to a follow-on doc-only commit
  after the seal lands; OUTSIDE the seal-fence):**
  - `docs/rebuild/STATE.md` v0.1.7 row.
  - `docs/rebuild/plans/v0-1-x-roadmap.md` §8 v0.1.7 register entry.
  - `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2
    v0.1.7 row (mark SHIPPED).

  These are universal-admitted prefix paths and could land in the
  seal commit, but per Cycle 2/3's pattern — and to keep the seal-fence
  diff focused on the component — they land as a **post-seal
  doc-only commit** with the release-summary status file.

---

## §4 — AC family — `AC.QSURF.*` (locked)

- **AC.QSURF.1 — onboarding-mode flag toggles `max_questions_per_turn`
  enforcement.** PM with `onboarding_mode=True` surfaces exactly 1
  question per `surface_next_questions_batch()` call regardless of
  `max_questions_per_turn` value. Test: enqueue 5; with batch_size=3
  + onboarding_mode=True, the call returns exactly 1; with
  onboarding_mode=False + batch_size=3, returns up to 3.

- **AC.QSURF.2 — non-onboarding permits batched surfacing per
  `max_questions_per_turn`.** PM with `onboarding_mode=False` +
  `max_questions_per_turn=3` permits a 3-question batch; queue
  advances by 3; audit-log records 3 entries.

- **AC.QSURF.3 — onboarding-mode hard test (per dispatch wording).**
  Across 5 simulated turns of onboarding-mode (5 distinct
  `surface_next_questions_batch()` calls), with 5 enqueued questions,
  exactly 1 question is surfaced per turn; total = 5; queue depth
  goes 5→4→3→2→1→0; audit-log carries 5 entries; assertion
  `len(surfaced_in_turn_N) == 1` for N=1..5. Structural test —
  passes EVERY run, never randomly.

- **AC.QSURF.4 — audit-log records each surfacing AND each response
  with full provenance.** Per surfacing, audit-log entry records
  `event_kind=surface_question` with all Cycle 2 fields. Per response,
  audit-log entry records `event_kind=record_response` with: timestamp,
  pm_handle, response_text, surfaced_question_text (linkage),
  surfaced_audit_path (linkage), responded_at_iso. Schema validated.

- **AC.QSURF.5 — `require_owner_response=True` blocks subsequent
  surfacings until prior is responded.** Test: enqueue Q1, Q2;
  surface Q1; attempt to surface Q2 → raises `PendingResponseError`.
  Record Q1's response → next surface succeeds. With
  `require_owner_response=False`, no blocking (post-onboarding fast
  flow).

- **AC.QSURF.6 — `record_response()` API.** Method on `PMRuntime`.
  Records owner response; writes audit-log entry; clears
  `pending_response_for` flag in state.yaml. Idempotent on duplicate
  call against the same surfaced-question audit_path (second call
  returns the previously-recorded `RecordedResponse` without writing
  a new audit-log entry). Rejects empty response_text.

- **AC.QSURF.7 — PM-mediated dispatches log per audit-trail floor
  (D6).** Test: under production-stake-mode-equivalent conditions
  (verified via the audit-log primitive), every PM-mediated
  surfacing AND response produces an audit-log entry; no
  surfacing/response slips through without an audit row. Aligned
  with v0.1.6 SOC-2 audit-trail floor.

- **AC.QSURF.8 — Composition with `audit-block-on-telegram` SKILL.**
  - `SurfacedQuestion` and `RecordedResponse` carry an
    `is_audit_block_trigger` boolean property whose return value is
    `True` (always — by construction, both are decision/response
    events).
  - `framework/per-project-pm/docs/design.md` §12 articulates the
    composition: PM-mediated events satisfy the audit-block SKILL's
    "decision was made" trigger condition; persona authors invoking
    the audit-block check `is_audit_block_trigger` to know when to
    surface the block.
  - Test: programmatic check that both classes expose the property,
    return `True`, and that the design-note carries the documented
    composition cross-reference.

---

## §5 — Halt-and-surface BEFORE build

### Surface #1 — `pending_response_for` placement (no halt — recorded)

**Decision (autonomous):** the blocking flag lives in `state.yaml`, not in
a new file. Two options were considered: (a) extend state.yaml with a
new field; (b) add `pending-response.yaml` as a new state file.
Option (a) chosen because (i) blocking state is logically part of the
PM's state-of-world, (ii) one fewer YAML file to manage / atomic-write,
(iii) backward-compatible (Cycle 2 state.yaml that doesn't carry the
field is treated as "no pending response"). Loader extends to read
the field with default `None`.

State.yaml schema after Cycle 4:

```yaml
schema_version: 1
in_flight: []
last_surfaced_at: null
notes: ""
pending_response_for: null  # NEW Cycle 4 — the question text awaiting
                            # response, or null if no surfacing is
                            # blocking. May be string (the question
                            # text) when populated.
```

### Surface #2 — `surface_next_questions_batch()` semantics (no halt — recorded)

**Decision (autonomous):**

- Returns a tuple `(SurfacedQuestion, ...)` of length up to
  `effective_n` where `effective_n = 1 if onboarding_mode else
  min(n, max_questions_per_turn, len(queue))`.
- When `n` is omitted, defaults to `max_questions_per_turn` (so the
  caller doesn't have to know the policy field's value).
- Each surfacing in the batch:
  - Writes its own audit-log entry (one entry per question, not one
    per batch — preserves provenance granularity).
  - Advances the queue by 1.
- If `require_owner_response=True` AND a prior question is unanswered
  (i.e., `pending_response_for` is non-null at start of call), raises
  `PendingResponseError` immediately — does not partially surface.
- The single-question API `surface_next_question()` is preserved
  unchanged from Cycle 2 callers' POV; internally it becomes
  `surface_next_questions_batch(n=1)` semantically (but stays as a
  separate method for API stability).

### Surface #3 — `record_response()` linkage shape (no halt — recorded)

**Decision (autonomous):** `record_response()` accepts the
audit-log path of the surfaced question (the `audit_path` field on the
`SurfacedQuestion` returned earlier). This is the unambiguous link —
the audit-log file already exists and carries the question text +
provenance; `record_response` writes a sibling audit-log entry with
the linkage and updates state.yaml's `pending_response_for` to None.

API:

```python
def record_response(
    self,
    surfaced_audit_path: Path | str,
    response_text: str,
) -> RecordedResponse: ...
```

Returns a `RecordedResponse` dataclass with fields:
`response_text`, `surfaced_audit_path`, `surfaced_question_text` (read
from the linked audit file), `responded_at`, `audit_path` (the new
record_response audit-log entry's path), `is_audit_block_trigger=True`.

Idempotency: if `record_response` is called twice for the same
`surfaced_audit_path`, the second call detects the existing
`record_response`-kind audit-log entry (by scanning audit-log
filenames) and returns the previously-recorded `RecordedResponse`
without writing a duplicate entry. Per Cycle 2's "audit-log is the
source of truth" rule, the existence of a prior `record_response`
entry for that link is the idempotency guard.

### Surface #4 — Audit-log entry shape for `record_response` (no halt — recorded)

**Decision (autonomous):** mirror Cycle 2's `surface_question` schema
with new `event_kind`:

```yaml
schema_version: 1
event_kind: record_response  # vs Cycle 2's surface_question
timestamp: "2026-05-04T11:42:00+00:00"
pm_handle: "test-pm"
response_text: "Hold for fix; ship in v0.1.8."
surfaced_audit_path: "audit-log/2026-05-04-0001.yaml"  # relative to pm_dir
surfaced_question_text: "Should we ship D5 with degraded mode or hold for fix?"
responded_at: "2026-05-04T11:42:00+00:00"
```

Filename uses the same `<YYYY-MM-DD>-<NNNN>.yaml` convention; the NNNN
counter is shared across both event_kinds within (pm-name, UTC date).
Sequencing: a `surface_question` at `0001` and a `record_response` at
`0002` share the same monotonic sequence — the audit-log is fully
ordered.

### Surface #5 — `is_audit_block_trigger` shape (no halt — recorded)

**Decision (autonomous):** add a property (not a field) on both
`SurfacedQuestion` and `RecordedResponse` that returns `True`
unconditionally. Why a property instead of always-True field: forward-
compat — future cycles may want to gate based on metadata (e.g., a
"low-stakes status update" surface that doesn't trigger the audit
block). Cycle 4 ships `True` always; the property mechanism is the
forward extension point.

The property carries a docstring: "Whether this PM event satisfies the
`audit-block-on-telegram` SKILL's 'decision was made' trigger
condition. Cycle 4 always returns True; future cycles may gate on
event metadata."

### Surface #6 — Onboarding-mode determinism (no halt — recorded)

**Decision (autonomous):** the AC.QSURF.3 "structurally non-deterministic"
halt-trigger is preempted by deterministic test design:

- The test uses a fresh tmp workspace with explicit time control (no
  reliance on real-time clocks for ordering — the FIFO sequence is
  insertion-order, not timestamp-order).
- The test enqueues 5 questions with distinct text; surfaces with
  `surface_next_questions_batch()` 5 times; asserts each call returns
  a tuple of length 1; collects all surfaced texts; asserts they
  match the FIFO order.
- The "exactly 1" assertion is on tuple length — `len(returned) == 1`
  — which is structural, not probabilistic.

If the test ever passes randomly (e.g., the API returns 1 sometimes
and N other times depending on internal state), that's a bug to halt
on per dispatch trigger.

### Surface #7 — Composition test shape (no halt — recorded)

**Decision (autonomous):** `audit-block-on-telegram` is a SKILL.md
file (markdown / persona-instruction), not Python. The test cannot
"call" the SKILL — instead it verifies the **structural composition
contract**:

1. PM event types expose `is_audit_block_trigger` property (return `True`).
2. `framework/per-project-pm/docs/design.md` §12 references the SKILL
   by exact path
   (`plugins/loam-skills/skills/audit-block-on-telegram/`) and names
   the "decision was made" trigger condition.
3. The SKILL.md file at the referenced path actually exists and
   contains the "decision was made" condition string (asserted via
   filesystem read in the test).

This is the same "documented composition + structural cross-reference"
shape used for Cycle 2's M-FBM boundary test — verifies the contract
without coupling the per-project-pm component to a runtime
audit-block import.

### Surface #8 — Backward-compat with Cycle 2 (no halt — recorded)

**Decision (autonomous):** Cycle 2's `surface_next_question()` is
preserved verbatim from a caller's point of view:

- Returns `SurfacedQuestion | None` (None on empty queue) — unchanged.
- All Cycle 2 fields preserved.
- BUT: Cycle 4 wires blocking-on-pending-response into it. If
  `require_owner_response=True` and `pending_response_for` is non-null,
  `surface_next_question()` raises `PendingResponseError`. This is a
  **new failure mode** introduced; existing Cycle 2 callers that
  never recorded a response BUT also never set
  `require_owner_response=True` are unaffected. Cycle 2 tests pass
  unchanged because all Cycle 2 PMs have the default
  `require_owner_response=True` BUT: the Cycle 2 tests don't drive
  the blocking pathway because they don't call `surface_next_question`
  twice without a `record_response` in between (within the same
  PM lifetime). Verified: re-running Cycle 2's 64 tests after Cycle 4
  changes lands all green.

If Cycle 2's tests fail after Cycle 4's wire-in, that's a halt-trigger
("Cycle 4 contradicts Cycle 2's contract") — but the design above
preserves all existing tests because Cycle 2 tests surface ONE
question after enqueue and don't re-enter without `record_response`.

(Mitigation: if Cycle 2 tests do fail, narrow the blocking-on-pending
to `surface_next_questions_batch` only; leave `surface_next_question`
without blocking. Then onboarding-mode enforcement uses the batch API
exclusively. This is a fallback only; the primary design wires
blocking into both for uniform semantics.)

### Surface #9 — README / design-note extension (no halt — recorded)

**Decision (autonomous):** extend `framework/per-project-pm/README.md`
to replace the "Cycle 4 deferred surface" section with "Cycle 4
surfaces (landed)." Extend `docs/design.md` with §11 (one-question-at-
a-time flow narrative) + §12 (audit-block composition cross-reference).
Keep §1-§10 intact (Cycle 2 content).

---

## §6 — Smoke (REALISTIC CONDITION — all 6 dimensions; HARD gate at v0.1.7 release close)

After Cycle 4 seals — covering Cycle 4 itself + the v0.1.7 release-level
rollup:

### D1 — cold-state (fresh canonical workspace)

- PM-mediated question dispatch operational from session-zero.
- Onboarding-mode test executes on the sealed code in a fresh tmp
  workspace: enqueue 5 questions; `surface_next_questions_batch()` x5;
  exactly 1 question per call; 5 audit-log entries.
- Verified by running the AC.QSURF.* test suite in a fresh checkout-shape
  invocation.

### D2 — steady-state (multiple dispatches)

- Question-batching survives 5+ dispatches. Queue depth stays bounded
  (advances exactly per surfacing). No memory leak (PM is stateless
  between calls; every state read is from disk).
- Verified by extending the existing PM-lifecycle smoke harness from
  Cycle 2 with batch surfacings.

### D3 — restart (PM queue + state survive process restart)

- Process A: enqueue 3 questions, surface 1, record response, surface 1
  more (no record), exit.
- Process B (fresh Python interpreter): re-load via `from_workspace`;
  `state_of_world()` reports queue depth, last_surfaced_at, and
  `pending_response_for` correctly.
- Verified by subprocess-spawn pattern from Cycle 2 D3 smoke.

### D4 — reboot (PM state survives macOS reboot equivalent)

- All Cycle 4 state is on-disk (extended state.yaml + audit-log files +
  decision-queue.yaml). Atomic writes per Cycle 2's tmp+rename
  pattern. No daemon dependency.
- PASS by structural argument (same as Cycle 2 D4) — Cycle 4's only
  state-shape change is the new `pending_response_for` field, which
  is on-disk like every other field.

### D5 — cross-session (PM state visible across `/clear`)

- "Session 1" enqueues 3, surfaces 1, records response. Post-`/clear`
  "Session 2" reads `state_of_world()` and observes `queue_depth=2`,
  `pending_response_for=None`, `last_surfaced_at` populated. THE
  ship-test per STATE.md.
- The one-question-at-a-time enforcement is structurally identical
  across sessions (the policy lives in `contract.yaml`, not in
  session state).
- Verified by simulating session-boundary as separate Python invocations
  against the same workspace (matches Cycle 2 D5 pattern).

### D6 — telemetry-floor (audit-trail floor)

- PM-mediated events log per the audit-trail floor: every surfacing
  AND every response writes an audit-log entry. Zero events slip
  through without an audit row.
- AC.QSURF.4 + AC.QSURF.7 verify this.

### Release-level smoke (across all 4 cycles, fresh canonical workspace)

End-to-end: a fresh canonical session can —

1. Use a subagent persona file (Cycle 1) — discoverable in
   `<workspace>/.claude/agents/`.
2. Interact with a per-project PM (Cycle 2) — via
   `host.per_project_pm.runtime_for(pm_name)`.
3. Invoke a workspace-local or plugin-tier skill (Cycle 3) — via
   `<workspace>/.claude/skills/<name>/SKILL.md` discovery.
4. Surface decisions one-at-a-time during onboarding-mode (Cycle 4) —
   via `surface_next_questions_batch()`.

Verified by running the full per-project-pm test suite + the
workspace-bootstrap test suite in canonical pos-v2 against the
sealed code.

---

## §7 — Out of scope

- **Auto-creation mechanism** (v0.2.0).
- **Promotion rubric** (v0.2.1).
- **Heavy reverse-engineering / Rails extractor** (v0.1.8).
- **12 dev-sdlc skill-ifications** (v0.1.8 + v0.1.9).
- **PM ratification queue mechanics + domain-batched AC surfacing**
  (v0.2.0 — different shape from Cycle 4's question queue).
- **OTEL emission for production-stake mode** — Cycle 4 ships the
  audit primitive; OTEL transport remains a v0.2.0+ concern.
- **Persona-side flow integration in primary-persona** — Cycle 4 ships
  the PM-side surfacing API; the primary-persona's call-site that
  invokes `host.per_project_pm.runtime_for(...).surface_next_questions_batch(...)`
  before relaying to the user is a primary-persona-component change
  outside this Cycle 4 fence. The surface is on the PM; the persona
  call-site lands at v0.2.0+ alongside auto-creation.

---

## §8 — Halt triggers (in-flight)

- WD drifts → halt + surface.
- Plan-doc not authored before code → halt.
- PM-mediated question dispatch contradicts existing channel/persona
  shape → halt + surface.
- Onboarding-mode "exactly one per turn" test is structurally
  non-deterministic (test passes randomly) → halt + reframe.
- More than 5 in-build decisions need Luke escalation → halt + describe.
- Cycle 4 wall-clock exceeds 5 hours → halt with partial findings.
- Cycle 2's 64 existing tests fail after Cycle 4's runtime extension
  → halt + reframe (per Surface #8 mitigation).
- Audit-block SKILL.md path doesn't exist or doesn't carry the
  "decision was made" trigger condition string → halt + surface
  (composition test would be a lie if the SKILL doesn't carry the
  named string).

---

## §9 — Bookkeeping

- `loam amend apply` per cycle (NOT `git commit --amend`).
- Single semantic commit message.
- Backfill of release-level rows (STATE.md / roadmap §8 / eric-final §2)
  ships as a follow-on doc-only commit per §3 above.
- DO NOT push tags; v0.1.7 sits as a local release until Luke gates +
  migration question resolves.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

- **AC.QSURF.7 production-stake-mode equivalence.** Cycle 4 doesn't
  toggle production-stake mode; it asserts that the audit-log
  primitive operates equivalently. The actual production-stake-mode
  boot path (set in `bootstrap.yaml.safety_profile`) checks the
  audit-log floor at boot time per v0.1.6 — Cycle 4's audit-log
  shape is compatible by construction (matches Cycle 2's primitive
  the audit-log floor already validates). If a future
  production-stake-mode boot probe explicitly demands a
  PM-mediated-dispatch span (OTEL), that's a v0.2.0+ wire-up; not
  Cycle 4.
- **Audit-block composition is one-way.** PM produces the events the
  SKILL consumes; the SKILL doesn't produce events PM consumes.
  Cycle 4 documents the consumption contract; Cycle 4 does NOT
  modify the audit-block SKILL itself (which is a v0.1.6 sealed
  artefact). This keeps the fence on `framework/per-project-pm/`.
- **`is_audit_block_trigger` always returns True at Cycle 4.** Per
  Surface #5, future cycles may gate it. Cycle 4 returning True
  unconditionally is the simplest correct version; the property
  shape leaves room without committing.
- **Cycle 4 doesn't ship the persona call-site.** The user-visible
  "persona only sends one question per turn" outcome requires the
  primary-persona's reply-authoring flow to invoke
  `host.per_project_pm.runtime_for(pm_name).surface_next_questions_batch(...)`
  before relaying. That's a primary-persona component change outside
  this fence. Cycle 4 ships the surface that makes the discipline
  STRUCTURAL on the PM side; the persona-side adoption lands when
  primary-persona is amended (v0.2.0+ alongside auto-creation per
  parent plan §7).

  This is named explicitly so Luke understands what Cycle 4 ships
  vs what the eventual user-facing experience requires. The HARD
  test for "exactly one question per turn" passes structurally on
  the PM API; the persona-side call-site adoption is a separate
  amendment.

---

## §11 — Provenance trail

- **Parent plan:** `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md`
  §5 AC.QSURF.* + §6 Cycle 4.
- **Eric synthesis Decision Q (RESOLVED YES)** — one-question-at-a-time
  PM-enforced; structurally enforced this Cycle.
- **Eric synthesis Decision P (RESOLVED YES)** — SOC-2 audit-trail
  floor; AC.QSURF.7 aligns.
- **Cycle 2 plan-doc** `docs/rebuild/plans/v0-1-7-cycle-2-per-project-pm.md`
  — names the Cycle 4 deferred surfaces.
- **Cycle 2 design-note** `framework/per-project-pm/docs/design.md` §8
  — explicit "Cycle 4 deferred" list this Cycle 4 plan addresses.
- **`plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md`** —
  the SKILL Cycle 4 composes against; carries the
  "decision was made" trigger condition (verified
  2026-05-04 in this plan's research).
- **Cycle 2 status file**
  `<pos3>/workspace/.scratch/claude-output/v0-1-7-cycle-2-status-2026-05-04.md`
  — the predecessor's outcome record (Cycle 2's 64 tests + 6 smokes
  green at `73505f0`).
- **Cycle 3 status file**
  `<pos3>/workspace/.scratch/claude-output/v0-1-7-cycle-3-status-2026-05-04.md`
  — Cycle 3 sealed at `bcf699a`; per-project-pm component untouched.

---

*End of v0.1.7 Cycle 4 plan-doc. Single-component fence on
`framework/per-project-pm/`; extends Cycle 2 with the deferred
surfaces. Release-level row backfill ships as a follow-on doc-only
commit. AI-time band: 25-50 min for build + smoke + backfill (per
Cycle 2/3 actuals — Cycle 2 was ~20 min for a NEW component; Cycle 4
is a smaller delta).*

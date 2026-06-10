# frame-kernel — real-dispatch memory tier (task-text derivation + standing decision floor)

> **Status:** plan-doc (ODD-shaped). Small single-purpose amendment.
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 via AC.SACH.3 / AC.DMP.1 — the
> SubagentStart bundle's memory tier must actually populate on REAL dispatches;
> a tier that only works on synthetic envelopes delivers nothing.
> **Confidence (Lens 4):** HIGH on the gap (Tier-0, twice-captured real
> envelopes); HIGH on the fix shape after the timing probe (see §2). Tight
> scope; method below is the builder's call where not pinned by evidence.

---

## §1 Objective

On a REAL SubagentStart envelope (common fields only: `session_id`,
`transcript_path`, `cwd`, `agent_id`, `agent_type`, `hook_event_name`), the
composed bundle's memory tier produces relevant records for the dispatched
agent's actual task — instead of degrading to
`[memory unavailable — no live store or query]` on every real dispatch.

## §2 Predecessors + Tier-0 evidence (probe captures, 2026-06-10)

- **`frame-kernel-subagent-envelope-cwd-fallback` (sealed `c39de619`)** —
  fixed workspace-root resolution (`cwd` fallback). Microkernel tier now
  populates on real dispatches. Memory tier still degrades: `parse_envelope`
  seeds `task_text` from envelope fields (`prompt`/`task`/`description`) that
  real envelopes do not carry.
- **Probe harness** (`/tmp/loam-sas-probe`, two real `claude -p` runs via
  `loam_spawn_isolation.spawn_isolated_claude`, each dispatching a Task
  subagent, with a SubagentStart capture hook dumping the envelope + a
  byte-snapshot of `transcript_path` at fire time). Findings, n=2 consistent:
  1. **Envelope fields are exactly the documented common six.** No
     `prompt`/`task`/`description`/`workspace`. The existing field reads stay
     as forward-compat first priority but never fire today.
  2. **`transcript_path` points at the PARENT session's transcript**
     (`session_id` matches the parent), and at SubagentStart fire time the
     file EXISTS and already contains the parent turn's real user message.
     Mechanism (a) is timing-feasible.
  3. **The in-flight Task tool_use is NOT yet flushed at fire time** (latest
     flushed assistant record was the PRIOR tool call in both runs). The
     dispatch prompt is therefore NOT reliably recoverable from a Task
     tool_use record — and scanning for "the last Task tool_use" would risk
     picking up a PREVIOUS dispatch's prompt once one flushes (stale-dispatch
     hazard under serial/parallel multi-dispatch).
- Capture artefacts: `/tmp/loam-sas-probe/captures/envelope-1781107056784.json`
  + `envelope-1781107233853.json` (+ transcript snapshots beside them).

**Named decision D-RDM.1 (evidence-pinned):** derive the task text from the
transcript's LAST REAL USER MESSAGE (the current ask the dispatch serves —
the same seed the parent's own per-turn retrieval contributor uses), NOT from
a Task tool_use scan. Rationale: the tool_use is empirically absent at fire
time (finding 3) and a stale one is actively wrong; the user message is
empirically present (finding 2) and semantically the work-anchor of the turn
that produced the dispatch.

**Named decision D-RDM.2 (layering):** mechanisms (a) + (b) layered. (a)
transcript-derived task text feeds the EXISTING gated retrieval unchanged;
(b) when no task text is derivable at all (no/unreadable/empty transcript,
no user message), a query-less STANDING FLOOR injects the workspace's open +
recent ruled decision records whole — dispatches always carry the
load-bearing rulings. The floor reuses the sealed `decision_ledger` read
surface (`open_decisions` / `iter_decisions` / `record_text`) — no new
ledger machinery, no `primary-persona` edits.

**Workstream-tier triage (dispatch secondary item):** its placeholder is NOT
the same class — `_resolve_workstream` reads on-disk state files that simply
don't exist in the observed workspace; the envelope shape is not involved.
Left unchanged (out of scope).

## §3 Scope

**In scope (frame-kernel only):**
- `bundle.py` — `parse_envelope` task-text derivation gains the transcript
  fallback (envelope fields first, unchanged); `_render_memory_tier` gains
  the standing-floor branch when `task_text` is empty.
- New AC.RDM.* tests (one file per AC) including the outcome-altitude test
  through the production hook entry-point with a real-shape envelope + a
  real-shape transcript fixture.

**Out of scope:**
- `primary-persona` (sealed; imported read-only as today), `frame_judge.py`,
  the hook script, the workstream tier, fail-soft contract changes, any
  AC.SACH./AC.DMP./AC.SSFC./AC.EWR. contract or test edit, live settings
  wiring, publish/push.

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.RDM.1` | Given a real-shape envelope (common fields only) whose `transcript_path` names a real-shape JSONL transcript, `parse_envelope` derives `task_text` from the transcript's last real user message — skipping tool_result-only records, the local-command/caveat preambles, and `<task-notification>` synthetic turns. Envelope `prompt`/`task`/`description` still win when present; a missing/unreadable transcript yields empty task_text (fail-soft, no raise). | Unit: real-shape transcript fixture → task_text == the planted user message; priority + skip + fail-soft cases parametrized. |
| `AC.RDM.2` | Given a real-shape envelope with NO derivable task text, in a workspace whose decision ledger is populated, the memory tier renders the STANDING FLOOR: open + recent ruled decision records WHOLE (question/ruling/reasoning/source/status), newest-first, within the existing injection char budget; with an empty/absent ledger the tier degrades to the existing markers byte-identically as before. | Unit: planted ledger → floor present, records whole, budget respected; no ledger → existing marker. |
| `AC.RDM.S` **(OUTCOME-ALTITUDE)** | The production hook entry-point (`subagent_start_context.py` as a subprocess — the AC.SACH.S/AC.EWR.S pattern), driven with the REAL captured envelope shape (common fields only) + a real-shape transcript fixture whose last user message is relevant to a planted RULED decision record, emits an `additionalContext` whose memory tier is NON-degraded and carries the planted record. No pre-arranged bundle state. | Real subprocess, real-shape fixtures, assert planted ruling text present + unavailable-marker absent + exit 0. |

Dispatch-AC mapping: dispatch AC1 → AC.RDM.1+AC.RDM.2; AC2 → AC.RDM.S;
AC3 (existing tests green, fail-soft unchanged, budget respected) → §15.

**Method-in-AC test:** each AC pins outcome only (what the tier carries, not
how the transcript is parsed or the floor assembled); satisfiable by other
methods. Confirmed.

**Ladder-up:** AC.RDM.* → AC.SACH.3 + AC.DMP.1 (memory reaches real
dispatched subagents) → AC.PO.1 + AC.PO.2.

## §5 Sealed-component fence

- **`frame-kernel`** (EXTEND; `frozen_baseline: false`) — `bundle.py` + new
  tests only.
- Universal admissions: `docs/plans/` (this plan + manifest).
- **No other component touched.** `primary-persona` surfaces are imported,
  never edited.

## §6 Build steps

1. `bundle.py`: transcript task-text derivation (tail-bounded read; reuse
   `frame_judge`'s record/role/text parsing helpers — same package, in-fence).
2. `bundle.py`: standing-floor branch in the memory tier (sealed
   `decision_ledger` reads via the existing live-config resolution; floor
   capped by the existing injection budget).
3. Tests AC.RDM.1 / AC.RDM.2 / AC.RDM.S (one file per AC).
4. Full frame-kernel suite green; RED-on-revert check on AC.RDM.S.
5. Commit ladder: plan+manifest (`docs(plans):`) → source+tests
   (`feat(frame-kernel):`) → `loam amend apply` → `loam amend seal` → §14
   backfill. Source commits land BEFORE apply. No push.

## §7 Halt triggers (in-flight)

1. WD drift from `/Users/lukeivers/loam` → halt.
2. The standing floor turns out to require editing `primary-persona` (a
   sealed contract violation) → halt + surface, don't improvise.
3. Fix requires touching anything beyond `bundle.py` + new tests → halt.
4. Any existing frame-kernel test fails post-edit → halt; never loosen.
5. Evidence contradicting the probe findings (e.g. a real envelope DOES
   carry the dispatch prompt) → halt + surface.

## §14 Method-decision register (populated at build time)

- D-RDM.1 / D-RDM.2 — see §2 (ruled at plan time, evidence-pinned).
- D-build.1 — transcript read is TAIL-BOUNDED (last 1 MiB, complete lines
  only) rather than reusing `frame_judge._load_transcript_records`'s full
  read: SubagentStart fires per-dispatch inside a 10s hook timeout against
  potentially-large parent transcripts; the last user message lives at the
  tail. Record parsing reuses `frame_judge._record_message`/`_block_text`
  unchanged.
- D-build.2 — floor caps reuse the sealed constants (`OPEN_DECISION_CAP`,
  `DECISION_TOP_N`, `INJECTION_CHAR_CAP`) with fail-soft local fallbacks, so
  no second budget exists to drift.
- D-build.3 — RED-on-revert: to be verified at build (the new ACs must fail
  against pre-fix `bundle.py`); result recorded here at backfill.

**Cycle SHAs (backfilled post-seal):**

| Step | SHA |
|---|---|
| Plan + manifest (`docs(plans):`) | `f6ee0945` |
| Source + tests (`feat(frame-kernel):`) | _backfilled post-seal_ |
| Apply (`chore(amend):`) | _backfilled post-seal_ |
| **Seal** (`chore(seals):`) | _backfilled post-seal_ |

## §15 Backwards-compat verification

All existing frame-kernel tests pass untouched (baseline green verified
pre-edit). Fail-soft contracts unchanged: a degenerate envelope (no fields)
still composes a degraded bundle exit-0; an envelope-field task text still
wins; with no transcript AND no ledger the memory tier renders exactly the
pre-cycle markers. The memory tier's budget remains the existing injection
char cap (floor included).

## §16 Halt-and-surface findings (plan-authoring)

- Non-blocking: the workstream tier's placeholder on real dispatches is an
  absent-state-file condition, not an envelope-contract bug (§2 triage) —
  surfaced for a separate decision if the owner wants the pos3 workspace to
  carry an active-workstream file.
- Non-blocking: probe 2 of 3 was refused by the model as injection-shaped
  (a split-marker construction); the structural finding was confirmed by
  probes 1 + 3 instead. No bearing on the build.

# frame-kernel — stop-judge objective from the agent transcript (+ advisory provenance)

> **Status:** plan-doc (ODD-shaped). Small single-purpose corrective amendment —
> third in the frame-kernel real-envelope lineage (c39de619 envelope-cwd,
> 9eeef654 memory-tier task-text).
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 via AC.SSFC.2 — the out-of-band
> frame-judge must judge a finished subagent's result against THAT subagent's
> actual dispatched objective; a judge fed the wrong objective manufactures
> false advisories that reach the owner (live incident, 2026-06-10).
> **Confidence (Lens 4):** HIGH on the gap (Tier-0, live incident + n=2 fresh
> probe captures); HIGH on the fix shape (the real envelope carries the
> subagent's own complete transcript). Tight scope; method is the builder's
> call where not pinned by evidence.

---

## §1 Objective

On a REAL SubagentStop envelope, the frame-judge's composed prompt carries, as
its "stated objective" block, the dispatched subagent's ACTUAL task text — and
the emitted off-frame flag self-identifies as a frame-judge advisory naming
the judged dispatch, so a human reading it out of context understands what it
is.

## §2 The live bug + Tier-0 evidence

**The incident (2026-06-10 ~11:16 CDT):** the judge-session episode at pos3
`workspace/.loam/memory/episodes/pos3/2026-06-10/turn:68e8ecee-…:d2a864fa12b5.md`
shows the judge prompt carrying, as `=== subagent stated objective ===`, a
CHANNEL message from the OWNER sent 2026-06-09 19:26 ("give me the current
state and what's next", discord 1513987674) — while the judged RESULT was a
2026-06-10 memory-probe report. The judge (correctly, given garbage inputs)
flagged OFF_FRAME; the bare verdict auto-routed to the owner with no
provenance and caused warranted confusion.

**The mechanism (code):** `read_subagent_result` loads records from the
envelope's `transcript_path` and `_extract_objective` takes the FIRST user
message — but `transcript_path` points at the PARENT session's transcript
(established Tier-0 by the 9eeef654 probes at SubagentStart, re-confirmed at
SubagentStop below), whose first user message is the owner's channel message.
Same root-cause family as the two earlier correctives: dispatch context
derived from the parent transcript.

**Fresh probe captures (n=2 consistent, 2026-06-10, the 9eeef654 technique —
real `claude -p` runs via `loam_spawn_isolation.spawn_isolated_claude`, each
dispatching a Task subagent under a SubagentStop capture hook dumping the
envelope + snapshotting every path-like field at fire time; harness
`/tmp/loam-ssp-probe`, captures `envelope-1781109287936.json` +
`envelope-1781109406943.json` + transcript snapshots beside them; Claude Code
2.1.170):**

1. The envelope carries `agent_transcript_path` — the SUBAGENT'S OWN
   transcript (`<session>/subagents/agent-<agent_id>.jsonl`). It EXISTS and
   is readable at fire time, and its FIRST user message IS the literal
   dispatch prompt (planted marker `SSP_PROBE_MARKER_88456` leading, both
   runs). Record shape is the documented
   `{"type":"user","message":{"role":"user","content":…}}` flavor
   `_record_message` already parses.
2. `transcript_path` points at the PARENT session's transcript (`session_id`
   matches the parent) — the live bug's wrong objective source.
3. The envelope carries `last_assistant_message` — the subagent's final
   output text (planted result marker present, both runs). The agent
   transcript's final assistant TEXT record is NOT reliably flushed at fire
   time (absent in run 1, present in run 2) — so result extraction must keep
   preferring the envelope field (it already does).
4. The envelope also carries `agent_id` + `agent_type` (and `session_id`,
   `cwd`, `permission_mode`, `effort`, `hook_event_name`, `stop_hook_active`,
   `background_tasks`, `session_crons`). No `description`/`prompt` field —
   the dispatch's Task-tool `description` is only recoverable by a parent
   -transcript tool_use scan, which the 9eeef654 probes proved stale-hazardous
   (rejected for provenance; see D-FJO.2).

**Named decision D-FJO.1 (evidence-pinned):** `agent_transcript_path` is the
SOLE transcript source for the judge path — objective (first user message),
result fallback (tail), and the consequential cue are ALL read off the
subagent's own transcript. The parent `transcript_path` is NEVER loaded for
the judge seed; when `agent_transcript_path` is absent (older Claude Code),
the path degrades fail-soft (no records → no cue → silent no-op; missing
-markers) rather than approximating from parent-message heuristics — a wrong
advisory (the live incident) is strictly worse than no advisory.

**Named decision D-FJO.2 (advisory provenance):** the flag self-identifies
from authoritative envelope/transcript sources only — "frame-judge advisory
on dispatch" + `agent_type` + subagent id + a first-line excerpt of the
judged objective. NO parent-transcript Task-tool_use scan for the dispatch
`description` (stale-dispatch hazard, 9eeef654 probe finding 3).

**Named decision D-FJO.3 (cue source correction):** `is_consequential`
currently scans the PARENT transcript — counting the parent session's own
writes as the subagent's. Switching the record source (D-FJO.1) corrects the
cue to the subagent's actual actions as a direct consequence.

## §3 Scope

**In scope (frame-kernel only):**
- `frame_judge.py` — `StopContext` + `parse_stop_envelope` gain
  `agent_transcript_path`/`agent_type`; `read_subagent_result` reads the
  agent transcript only; `render_surface` self-identifying advisory text;
  docstring corrections (the transcript_path-is-the-subagent claim is
  empirically false).
- `subagent_stop_frame_check.py` — docstring correction only (same false
  claim); no behavior change.
- `tests/conftest.py` — `make_stop_envelope` reshaped to the REAL captured
  envelope (agent transcript routed to `agent_transcript_path`; a decoy
  parent transcript with a must-not-leak marker + a Write cue at
  `transcript_path`), so every existing SSFC test pins the corrected source.
- New AC.FJO.* tests (one file per AC).

**Out of scope:** `bundle.py` and all AC.SACH./AC.DMP./AC.RDM./AC.EWR.
surfaces; the SubagentStart hook; fail-soft/exit-0/non-blocking contract
changes; settings wiring; publish/push.

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.FJO.1` | Given a real-shape SubagentStop envelope (captured 2.1.170 shape), the judge seed's stated-objective block carries the subagent transcript's first user message (the literal dispatch prompt) — never any content from the parent `transcript_path` transcript; the consequential cue is computed from the subagent transcript only; envelope objective fields (`prompt`/`task`/…) keep first priority; result keeps `last_assistant_message` priority with agent-transcript-tail fallback; an absent/unreadable `agent_transcript_path` degrades fail-soft (missing-markers, no cue, no judge spawn, NO parent fallback). | Unit: planted dispatch-prompt + decoy parent fixtures → seed carries the dispatch prompt, parent marker absent; cue/priority/degraded cases parametrized. |
| `AC.FJO.2` | The emitted off-frame flag self-identifies as a frame-judge advisory naming the judged dispatch: the `systemMessage` carries "frame-judge advisory", the dispatch's `agent_type` + subagent id, and a first-line excerpt of the judged objective — readable out of context. | Unit: off-frame verdict via `evaluate` with a stubbed judge → message carries all provenance elements; `render_surface` without a result still renders sanely. |
| `AC.FJO.S` **(OUTCOME-ALTITUDE)** | The production hook entry-point (`subagent_stop_frame_check.py` `main()`, the AC.SSFC.S posture — stub ONLY the `subprocess.run` boundary inside the sealed spawn surface), driven with the REAL captured envelope shape (all fields, `transcript_path` → a parent fixture whose first user message is a channel-shaped owner message, `agent_transcript_path` → an agent fixture whose first user message is the planted dispatch prompt, `last_assistant_message` → the planted result), composes a judge prompt whose objective block carries the planted dispatch prompt and NOT the channel message; the off-frame flag self-identifies per AC.FJO.2; exit 0. | Real hook entry-point, real-shape fixtures, spawn-boundary stub; assert prompt contents + flag text + rc. |

Dispatch-AC mapping: dispatch AC1 → AC.FJO.1; AC2 → AC.FJO.S; AC3 (existing
tests green; fail-soft/exit-0/non-blocking unchanged) → §15; AC4 → AC.FJO.2.

**Method-in-AC test:** each AC pins outcome only (what the seed/flag carries,
not how the transcript is parsed or the message assembled); satisfiable by
other methods. Confirmed.

**Ladder-up:** AC.FJO.* → AC.SSFC.2 + AC.SSFC.4 (the judge judges the actual
dispatch; the surface is intelligible) → AC.PO.1 + AC.PO.2.

## §5 Sealed-component fence

- **`frame-kernel`** (EXTEND; `frozen_baseline: false`) — `frame_judge.py`,
  `subagent_stop_frame_check.py` (docstring), `tests/conftest.py`, new
  AC.FJO.* tests.
- Universal admissions: `docs/plans/` (this plan + manifest), `docs/STATE.md`.
- **No other component touched.**

## §6 Build steps

1. `frame_judge.py`: `StopContext`/`parse_stop_envelope` field additions
   (defaulted, so direct constructions stay valid); `read_subagent_result`
   source switch; `render_surface` advisory text (optional `result` param —
   existing call shapes stay valid); docstring corrections.
2. `subagent_stop_frame_check.py`: docstring correction.
3. `tests/conftest.py`: `make_stop_envelope` → real captured shape + decoy
   parent transcript.
4. Tests AC.FJO.1 / AC.FJO.2 / AC.FJO.S (one file per AC).
5. Full frame-kernel suite green under the venv Python; RED-on-revert check
   on the new ACs.
6. Commit ladder: plan+manifest (`docs(plans):`) → source+tests
   (`feat(frame-kernel):`) → `loam amend apply` → `loam amend seal` → §14
   backfill. Source commits land BEFORE apply. No push.

## §7 Halt triggers (in-flight)

1. WD drift from `/Users/lukeivers/loam` → halt.
2. The real envelope had carried NO path to the subagent's transcript or
   objective → halt with capture evidence (RESOLVED at plan time: it does —
   `agent_transcript_path`, n=2).
3. Fix requires touching anything beyond §3's in-scope list → halt.
4. Any existing frame-kernel test fails post-edit for reasons other than the
   conftest envelope-shape correction → halt; never loosen.
5. Scope past a small-medium amendment → halt.

## §14 Method-decision register (populated at build time)

- D-FJO.1 / D-FJO.2 / D-FJO.3 — see §2 (ruled at plan time, evidence-pinned).
- D-build.1 — conftest's `make_stop_envelope` reshaped to the captured real
  envelope rather than adding a parallel fixture: every existing SSFC test
  now exercises the corrected source, and the decoy parent transcript
  (must-not-leak marker + Write cue) turns any future parent-read regression
  into a visible marker leak / false cue. Existing assertions untouched.
- D-build.2 — `StopContext`'s new fields (`agent_transcript_path`,
  `agent_type`) and `render_surface`'s `result` param are DEFAULTED, keeping
  every existing construction/call shape valid (AC.SSFC.4's direct
  `render_surface(verdict, ctx)` test passes unchanged).
- D-build.3 — RED-on-revert verified: with the `frame_judge.py` +hook edits
  stashed, 11 of the 13 new tests FAIL and 2 pass pre-fix BY DESIGN
  (preserved-behavior pins: envelope-field objective priority; the
  missing-objective marker never excerpted). All 13 pass post-fix; full
  suite 92/92 (79 pre-existing + 13 new) under the venv Python.
- D-build.4 — seal-time dirty-tree handling repeated from the previous two
  cycles: the 13 pre-existing untracked plan-docs from other in-flight
  cycles were scoped-stashed (`git stash push -u <paths>`) around the seal,
  then popped — all 13 restored; no unrelated path entered any commit.
- D-build.5 — mid-cycle corrective `415fcdea`: the manifest's baseline
  carried an UNVERIFIED full-SHA expansion of short `976959f8` (caught by
  apply's diff walk failing; `git rev-parse <40-hex>` echoes well-formed hex
  back without verifying, which masked it). Corrected to the
  `rev-parse --verify`-confirmed SHA via a NEW commit (never `--amend`).
  Lesson re-affirmed: full SHAs are Tier-0-verified, never expanded by hand.

**Cycle SHAs (backfilled post-seal):**

| Step | SHA |
|---|---|
| Plan + manifest (`docs(plans):`) | `00fe86fc` (+ baseline correction `415fcdea`) |
| Source + tests (`feat(frame-kernel):`) | `5a75d832` |
| Apply (`chore(amend):`) | `9a808123` |
| **Seal** (`chore(seals):`) | `9e4c0727` |

## §15 Backwards-compat verification

All existing frame-kernel tests pass (baseline green verified pre-edit).
Fail-soft contracts unchanged: every error path still exits 0 / returns
`None`; the surface stays a non-blocking `systemMessage` (no `decision`);
degenerate envelopes degrade silently. The conftest reshape routes existing
fixtures through the corrected source without weakening any assertion —
existing tests go RED on the pre-fix code under the corrected (real) envelope
shape, which is the desired pin.

## §16 Halt-and-surface findings (plan-authoring)

- Non-blocking: `is_consequential` was silently reading the PARENT
  transcript's tool uses (D-FJO.3) — the judge could fire on a read-only
  subagent whenever the parent session had written anything. Fixed as a
  direct consequence of D-FJO.1; named here because it widens the incident's
  blast-radius understanding (false advisories were possible on trivial
  dispatches too).
- Non-blocking: on envelopes WITHOUT `agent_transcript_path` (older Claude
  Code), the judge now degrades to silent no-op instead of judging
  parent-derived garbage — a deliberate behavior change inside the corrective
  intent (no advisory is strictly better than a wrong advisory).

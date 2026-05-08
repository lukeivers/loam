# Plan — memory-system live client + Stop-hook turn-close write

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `de5fe11`.
**Pre-amendment tip:** placeholder — captured at brief-dispatch
(`baseline: <sha>` in the manifest, BASELINE-as-HEAD~1 pattern per
amendments #29 / #34-#47).
**Amendment number:** unassigned at authoring; assigned at dispatch.
Plan filename carries the family slug, no numeric prefix on the
umbrella; per-amendment manifest slug placeholder
`memory-system-live-client-and-stop-hook-write` (revisable).
**Research:**
`docs/plans/research/memory-system-live-client-and-stop-hook-write-research.md`.
**Composes on (sealed):** `primary-persona` (amendments #32, #33,
#35–#37, #40, #46), `hands-off-lifecycle` (amendments #37, #45, #46),
`workspace-bootstrap` (amendment #47 — `.mcp.json` is in place).

---

## 1. Summary / TLDR

Two production-wiring gaps remain after #46/#47. This plan closes
both in one amendment cycle:

1. **Live MCP memory client in the persona venv.** Replace
   `_default_memory_client_factory` in
   `primary-persona/src/session_start_emitter.py:74` (currently
   `return None`) with a live streamable-HTTP MCP client adapter
   that conforms to the existing `MemoryClient` Protocol. After
   this lands, `register_memory_retrieval` actually registers in
   the persona-layer's UserPromptSubmit composer; per-turn
   retrieval blocks reach `additionalContext`.
2. **Stop-hook turn-close write.** Add a new `stop` CLI
   subcommand on `primary_persona.cli` that reads Claude Code's
   Stop envelope from stdin, recovers the user message + persona
   reply from `transcript_path`, derives a stable turn id, and
   spawns a detached background subprocess that drives
   `TurnAggregator.close_turn(...)` to completion against the
   live MCP client. A new `merge_stop` in
   `hands-off-lifecycle/hooks/first_run_settings.py` registers
   the Stop hook in `.claude/settings.json`. After this lands,
   every user↔AI turn produces exactly one aggregated episode in
   the memory graph.

Both pieces share the live MCP client; both ride one amendment.
Sealed-component fence: `primary-persona/` +
`hands-off-lifecycle/`. No other component is touched.

Per CLAUDE.md output convention, owner reads from §6 (decisions
for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **v1.0 architectural — "persistent + retrievable memory"**
  (objectives spec §1; VALUE_PROPOSITION §"Unpacking the toolkit"
  item 1: *"Today's response is informed by yesterday's
  decisions."*). #46 + #47 made the substrate reachable; this
  amendment makes it **live** — without a live client the
  retrieval block is empty; without a Stop-hook caller no episodes
  are written; "today's response informed by yesterday's
  decisions" is impossible.
- **D7 (amendment #33) AC-D7.1 + AC-D7.2 production-completion.**
  AC-D7.1's outcome ("a `UserPromptSubmit` event causes the
  layer's `additionalContext` output to include a memory-retrieval
  block") is currently latent — the contributor exists but is
  never registered in the production path because
  `_default_memory_client_factory` returns None. AC-D7.2's
  outcome ("at user↔AI turn-close, exactly one aggregated episode
  is persisted for that turn") is currently latent — the
  aggregator exists but has no production caller. This amendment
  closes both production paths.
- **v1.2 R16 — Framework-not-content.** Pure framework wiring:
  no persona content, no memory content, no policy authored.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* persona answers from
    accumulated memory. Live client + write path = memory exists
    to answer from.
  - *Harness test (AC.PO.2):* live MCP client adapter and
    Stop-hook handler are reusable primitives every future
    persona-side memory consumer + Stop-event handler composes
    against.

**Sealed-component amendment classification.** Two sealed
components touched:

- `primary-persona`: new MCP-client adapter + new `stop`
  CLI subcommand + new `stop_emitter` module + small change to
  `_default_memory_client_factory`. Pure-additive at the public
  surface (the factory's signature is unchanged; only its body
  changes). Tests added.
- `hands-off-lifecycle`: new `merge_stop` + `_is_pos_v2_owned_stop`
  + marker set in `first_run_settings.py`; new
  `_persona_stop_stanza` + `_maybe_merge_stop` + three call-site
  invocations in `first_run_helper.py`. Pure-additive. H19
  frozen-BASELINE per amendment #23. Tests added.

**ODD §2.5 reverse direction.** Every code path, branch,
dependency, and test in this amendment must trace back to a named
AC under §5. No silent branches; no defensive `if`s without
backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?** Two:

1. **Claude Code's `Stop` hook.** Claude-native, fires once per
   turn-close, payload includes `transcript_path` (the canonical
   surface for recovering user+reply). The plan registers a new
   inner-hook entry in `.claude/settings.json` under
   `hooks.Stop`. No custom polling, no orchestrator-side daemon,
   no recurring scope.
2. **Claude / MCP's streamable-HTTP client surface.** The `mcp`
   Python package's `streamable_http_client` + `ClientSession`
   pair is the canonical client for a FastMCP server. The
   persona consumes the same protocol Claude Code itself uses
   (per amendment #47's `.mcp.json` registration); a single
   memory service serves both clients without protocol
   re-implementation.

This is textbook Lens 1: existing Claude primitives, composed.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation
burden?* YES — load-bearing. Before this amendment, every user
turn is a fresh conversation in memory's eyes. The user says
"like we discussed yesterday" and the persona has no record. The
translation layer cannot translate intent that depends on
history because no history exists. After this amendment,
`add_episode` runs on every turn and `search` runs on every
prompt; the persona answers from accumulated state.

**Harness test.** *Does this add to the toolkit the primary
persona can draw from?* YES. Two reusable primitives:

- The live MCP client adapter is the primitive every future
  persona-side memory consumer (awareness-block memory, proactive
  surfacing, cross-domain synthesis) draws against.
- The Stop-hook handler is the primitive every future
  Stop-event handler composes alongside (workflow-end emitter,
  scope-close logger, end-of-session compaction primer).

### Lens 3 — ODD authoring

ACs are outcome-shaped. No method in any AC. Behaviour-count
forward direction in §5. Reverse direction is the builder's
audit; the plan is structured so reverse-trace is mechanical
(every behaviour maps to one AC; every code path the eventual
builder produces traces back to one AC).

---

## 4. Objective

The primary-persona layer participates in the memory system as a
live first-class consumer. Both halves of the consumer's
substrate — UserPromptSubmit retrieval (AC-D7.1) and turn-close
write (AC-D7.2) — operate against a real MCP client adapter
constructed from the workspace's locally-running memory-graphiti
service. Turn-close writes are triggered by Claude Code's
`Stop` hook (Luke 2026-04-26 ruling, locked); the Stop-hook
handler is fail-soft (exits 0 on every path), recovers the user
message + persona reply from the Stop envelope's
`transcript_path`, derives a stable per-turn id, deduplicates
on re-firing Stops, and detaches the actual `add_episode` write
to a background subprocess so the hook itself returns in
milliseconds. The live MCP client and the Stop handler are
co-shipped because they share dependencies; the amendment fence
is `primary-persona/` + `hands-off-lifecycle/` only.

---

## 5. Acceptance criteria

Each AC is outcome-shaped. Forward behaviour-count check in §5.x.
The §2.5 reverse direction is the builder's pre-seal audit
(restated as halt-and-signal trigger in §8).

### AC.M.1 — Live MCP client returns a usable MemoryClient

Given a workspace whose memory-graphiti service is running on
its allocated port (per amendment #29 + #47), the persona's
default memory-client factory returns a non-None object that
satisfies the existing `MemoryClient` Protocol. Issuing
`await client.search(query=..., group_ids=[slug],
num_results=5, center_node_uuid=None)` against the live service
returns a dict with the documented `{"query": str, "results":
list}` shape. Issuing `await client.add_episode(name=...,
body=..., source_description=..., reference_time=...,
source="message", group_id=slug)` against the live service
returns a dict with the documented `{"episode_uuid": str,
"nodes_extracted": int, "edges_extracted": int}` shape.

### AC.M.2 — Per-turn retrieval block reaches additionalContext

Given the workspace's memory-graphiti service is reachable AND
contains at least one prior episode keyed to the workspace's
slug, the persona's `cli user-prompt-submit` subcommand for a
crafted prompt that semantically overlaps the seeded episode
emits an `additionalContext` payload to stdout that contains the
retrieved episode's fact text. (AC-D7.1 production-completion.)

### AC.M.3 — Memory service unreachable: graceful empty + exit 0

Given the memory-graphiti service is unreachable (port closed,
HTTP refusal, or simulated timeout), the persona's
`cli user-prompt-submit` subcommand emits an empty (or non-memory
contributing) `additionalContext` payload and exits 0. The hook
fan-out is not blocked. (AC-D7.7 production-completion.)

### AC.M.4 — Stop-hook subcommand exists, exits 0 on every path

A `stop` subcommand exists on `primary_persona.cli` that reads
Claude Code's Stop envelope from stdin (JSON shape per Claude
Code Stop-hook contract) and exits 0 unconditionally — including
on stdin-read failure, JSON parse failure, transcript-read
failure, and any internal exception. No traceback reaches stdout
or stderr.

### AC.M.5 — Stop-hook recovers turn content from transcript_path

Given a Stop envelope whose `transcript_path` points at a
well-formed JSONL transcript carrying at least one user message
and one assistant reply, the Stop subcommand extracts the most
recent user message text AND the most recent assistant reply
text, derives a stable turn id from those + `session_id`, and
hands them to the turn-close write path. (Behaviour: the test
asserts the write path was invoked with the recovered content.)

### AC.M.6 — Stop-hook write path persists exactly one episode per turn

For a given Stop event with recoverable user message + assistant
reply, exactly one `add_episode` call lands at the memory
service for that turn — not zero, not two, not per-message. The
episode body contains both the user message and the assistant
reply. The episode's `group_id` equals the workspace slug.
(AC-D7.2 + AC-D7.4 production-completion via the Stop hook.)

### AC.M.7 — Stop-hook returns in milliseconds; write completes async

The Stop-hook subprocess returns (exit 0) within 200ms p95,
independent of the memory service's `add_episode` cost (which is
empirically 113s per amendment #33). The actual write completes
in a detached background process whose lifetime is independent
of the Stop subprocess. (AC-D7.3 production-completion.)

### AC.M.8 — Re-firing Stop on the same turn does not double-write

Given two consecutive Stop firings whose `transcript_path` and
last-user-message both resolve to the same turn (i.e., the
second firing is a recursive / `/compact` / interrupt-replay
re-fire), exactly one `add_episode` lands at the memory service
across both firings. The deduplication mechanism is method;
the AC measures observable count.

### AC.M.9 — Transcript unreadable / unrecognised: graceful no-op

Given a Stop envelope whose `transcript_path` is missing,
unreadable, malformed JSONL, or contains no user message or no
assistant reply (e.g., post-`/compact` shape or post-ESC-
interrupt empty reply), the Stop subcommand exits 0 and writes
zero episodes. No traceback. No partial-episode write.

### AC.M.10 — Live client failure during write: fail-soft + diagnostic

Given the memory-graphiti service is unreachable when the
detached write subprocess attempts `add_episode`, the
subprocess exits cleanly (no zombie), surfaces a structured
diagnostic to a workspace-local log file, and does not affect
the main session in any way (no state change to settings.json,
no persona contract mutation, no orchestrator surface touched).

### AC.M.11 — Settings.json registers the Stop hook in three call-sites

`hands-off-lifecycle/hooks/first_run_settings.py` exposes a
public `merge_stop` function. Calling it on a fresh
`.claude/settings.json` writes the persona's Stop inner-hook
entry under `hooks.Stop` (single entry list). Calling it on a
settings.json whose existing `hooks.Stop` is pos-v2-owned
(matches the persona's command markers) replaces it without
backup. Calling it on a settings.json whose existing
`hooks.Stop` is user-authored creates a timestamped backup of
the prior settings.json before replacing.
`hands-off-lifecycle/hooks/first_run_helper.py` invokes
`merge_stop` (via a `_maybe_merge_stop` fail-soft helper) at
each of the three SessionStart-merge call sites where
`_maybe_merge_user_prompt_submit` already runs (Phase 3d, Phase
4c, Phase 6). Other top-level keys (`hooks.SessionStart`,
`hooks.UserPromptSubmit`, `hooks.<other>`, `agent`, etc.) are
preserved unchanged.

### AC.M.12 — Backwards-compat: existing #46/#47 behaviours unchanged

Existing tests in `primary-persona/tests/`,
`hands-off-lifecycle/tests/`, and `workspace-bootstrap/tests/`
(notably `test_AC46_*`, `test_AC.45_*`, `test_AC37_*`,
`test_AC47_*`, `test_no_sealed_amendments.py` for every sealed
component) stay green after this amendment lands.

### AC.M.13 — ODD §2.5 reverse direction

Every code path, branch, dependency, and test in the amendment
diff traces back to AC.M.1 – AC.M.12. The builder audits both
directions before seal. (Halt-and-signal if any code path lacks
backing.)

### AC.M.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths
under: `primary-persona/src/`, `primary-persona/tests/`,
`primary-persona/pyproject.toml`,
`hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`, and
the universal-paths admissions
(`docs/plans/`, `CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md`).
Anything outside this set is a halt condition.

### 5.x — Behaviour-count check (forward)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Live MCP client conforms to the MemoryClient Protocol on the live service | AC.M.1 |
| 2 | Per-turn retrieval block reaches additionalContext | AC.M.2 |
| 3 | Memory service unreachable: graceful empty | AC.M.3 |
| 4 | Stop-hook subcommand exists; exits 0 on every path | AC.M.4 |
| 5 | Stop-hook recovers user message + assistant reply from transcript | AC.M.5 |
| 6 | Stop-hook write path persists exactly one episode per turn | AC.M.6 |
| 7 | Stop-hook returns fast; write completes async | AC.M.7 |
| 8 | Re-firing Stop on same turn does not double-write | AC.M.8 |
| 9 | Transcript unreadable / unrecognised: graceful no-op | AC.M.9 |
| 10 | Live-client failure during write: fail-soft + diagnostic | AC.M.10 |
| 11 | Settings.json registers Stop hook at three call sites; preserves user keys | AC.M.11 |
| 12 | Backwards-compat with #46/#47 + earlier | AC.M.12 |
| 13 | ODD §2.5 reverse direction | AC.M.13 |
| cross-cutting | Seal-diff window respected | AC.M.S |

13 behaviours, 14 ACs (one cross-cutting). No method-in-AC.

---

## 6. Decisions for owner (read this first)

The plan-author has made the following inferences. Each names a
recommendation; Luke rules from this block, not from reading the
full plan.

### D1 — Where the live MCP client lives

- **Recommendation:** new module
  `primary-persona/src/mcp_memory_client.py` exposing
  `LiveMCPMemoryClient` and `build_live_mcp_memory_client(
  workspace_root: Path) -> MemoryClient | None`. The
  `_default_memory_client_factory` in `session_start_emitter.py`
  becomes `return build_live_mcp_memory_client(workspace_root)`.
- **Why:** keeps MCP-protocol concerns out of the emitter
  module; matches amendment #46's separation
  (`session_start_emitter.py` orchestrates, callable peers carry
  protocol detail).
- **Alternative:** inline the adapter inside
  `session_start_emitter.py`. Smaller diff, less testable surface
  per AC.M.1.

### D2 — Where the Stop CLI handler lives

- **Recommendation:** new module
  `primary-persona/src/stop_emitter.py` exposing
  `cli_stop(workspace_root)` + `handle_stop_envelope(envelope,
  workspace_root)`. The `cli.py` gets a new `stop` subparser
  routing to `cli_stop`.
- **Why:** mirrors amendment #46's
  `session_start_emitter.cli_session_start` /
  `cli_user_prompt_submit` shape exactly. One file per emit
  responsibility keeps the surface scannable.
- **Alternative:** add to `session_start_emitter.py` directly.
  Tighter coupling; bigger file; same outcome.

### D3 — Detachment shape for the background write subprocess

- **Recommendation:** Python `subprocess.Popen(...,
  start_new_session=True, stdin=DEVNULL, stdout=DEVNULL,
  stderr=DEVNULL)` from inside `cli_stop`. The detached child
  invokes a new `python -m primary_persona.cli memory-write`
  subcommand that does the actual `add_episode` call.
- **Why:** Python-native; testable (the Popen call site is the
  unit-test boundary); precedent in pos-v2 is fork-and-disown
  via shell (`first-run.sh`), but the Python pattern is cleaner
  for a Python-already-running process.
- **Alternative (a):** drive the write synchronously in
  `cli_stop`. Bad — see research §6.2; the 113s extraction would
  block subsequent Stops.
- **Alternative (b):** spawn via `os.fork` + `os.execv`. Lower-
  level; harder to test on macOS.
- **Caveat:** the new `memory-write` subcommand IS a public
  CLI entry point; the AC.M.S seal-diff window covers it.

### D4 — Turn-id derivation + idempotency

- **Recommendation:** turn id = `f"{session_id}:{user_message_sha256[:12]}"`.
  Idempotency mechanism: write a per-workspace marker file at
  `<workspace>/.pos/last-turn-id` BEFORE detaching the write
  subprocess; on Stop firing, if the read-back equals the
  current turn id, skip the detach (already-handled).
- **Why:** stable across `/compact` / ESC re-fires (same
  session_id, same last user message). Workspace-local marker
  survives between hook invocations (each is a fresh process);
  no in-process state needed.
- **Alternative:** use the transcript JSONL line count as the
  id seed. Equivalent; brittle if transcript schema changes.

### D5 — `mcp` Python package version pin

- **Recommendation:** pin to the exact version present in
  `memory-system/.venv` (read it at plan-author time; manifest
  documents the exact version).
- **Why:** persona client must speak the same MCP protocol
  version the server (memory-system) speaks. A floating bound
  risks protocol drift.
- **Alternative:** add a minimum bound (`>=`) and let resolver
  pick. Rejected — the persona venv is shared with the rest of
  pos-v2; shipping a bound that resolves to a different version
  than memory-system's pinned one is asking for trouble.

### D6 — Stop-hook timeout

- **Recommendation:** `"timeout": 5` seconds (matches the
  loam-mode + persona session-start + persona user-prompt-submit
  inner hooks per amendment #45 / #46 D-build.7).
- **Why:** the hook detaches the actual write and returns in
  milliseconds. 5s is generous. 600s default would let a hung
  detach-call wedge the user's UX.

### D7 — Memory service down at Stop time

- **Recommendation:** Stop subprocess spawns the detached
  write subprocess unconditionally; the detached child catches
  the connection failure, logs a structured diagnostic to
  `<workspace>/.pos/memory-writes.log`, and exits cleanly.
- **Why:** the Stop subprocess can't easily probe service
  health in <200ms; cheaper to detach optimistically and let
  the child handle failure. The diagnostic surface is the
  workspace-local log; future awareness-block contributors can
  surface from there.

### D8 — Diagnostic log location

- **Recommendation:** `<workspace>/.pos/memory-writes.log` —
  newline-delimited JSON, one entry per write attempt
  (success or failure).
- **Why:** workspace-local (every other workspace artefact
  follows this convention since amendment #28); composes
  naturally with future awareness-block contributors that
  surface "memory writes failing"; outside any sealed
  component's source tree.
- **Alternative:** orchestrator's scope-of-work event log.
  Rejected — composing onto a sealed-component surface; would
  break the amendment fence.

### D9 — Where the `mcp` runtime dep is declared

- **Recommendation:** add `mcp` to the `[project] dependencies`
  in `primary-persona/pyproject.toml`. Persona venv installer
  picks it up.
- **Why:** declared deps are the documented persona runtime
  surface; method-level which version, but the AC is "live
  client constructible at runtime" — that requires the package
  to be importable.
- **Alternative:** vendor the `mcp` source. Rejected —
  duplicative; the package is well-maintained and Apache-2.0.

### D10 — Recursive-Stop empirical verification

- **Recommendation:** the plan is robust against any of the
  three possible recursive-Stop semantics (always-fires,
  never-fires, fires-with-`stop_hook_active=True`) via the
  turn-id idempotency in D4. **No empirical verification needed
  before build;** the build CAN proceed with the dedupe-first
  design.
- **Why:** the dedupe is the structural defence; the
  `stop_hook_active` field, if it arrives, is a free signal
  that we can also short-circuit on, but the dedupe handles
  the case independently.
- **Caveat:** the builder should still write a quick
  empirical-verification fixture during build (cat the
  envelope to a tmp file from one Stop firing in pos3) and
  document the actual observed shape in the builder plan.

### D11 — Stop hook on `/compact` and ESC interrupt

- **Recommendation:** treat both as graceful no-op cases.
  The transcript walk in `handle_stop_envelope` returns empty
  user_message OR empty assistant_reply for these cases;
  AC.M.9 says zero-write zero-traceback for that shape.
- **Why:** persisting a compaction prompt as if it were a user
  message would corrupt the memory graph. Persisting an
  empty-reply turn produces low-value episodes. Better to skip.
- **Caveat:** the builder should log "skipped: <reason>" to the
  diagnostic log so the operator can verify the skip rate is
  sane.

### D12 — Amendment scope: single amendment vs split

- **Recommendation:** SINGLE amendment.
- **Why:** the live MCP client and the Stop handler are tightly
  coupled (the Stop handler needs the live client to write).
  Splitting would require a stub-client interim that adds zero
  value. Per amendment-#33's "no synchronous user-facing wait"
  design, the asyncio pattern shipped there is exactly what the
  Stop handler reuses; one cycle is the cleanest shape.

---

## 7. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence.** In-scope source: `primary-persona/src/`,
   `primary-persona/tests/`, `primary-persona/pyproject.toml`,
   `hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`.
   Any edit elsewhere (other than the universal-paths
   admissions in §10) is a halt trigger (§8).
3. **Reversibility.** Fully reversible. The factory change is
   additive (factory still returns `None` when the live client
   can't construct, preserving #46's graceful-empty path); the
   Stop hook is additive (registering it doesn't disturb
   SessionStart or UserPromptSubmit).
4. **No synchronous user-facing wait on memory writes.** The
   detachment pattern (D3) is the structural enforcement of
   AC.M.7. Any AC method that drives `add_episode`
   synchronously inside the Stop subprocess is a halt trigger.
5. **Stop-hook subprocess exits 0 unconditionally.** A non-zero
   exit blocks Claude Code's normal stop behaviour (per docs
   `Stop` exit-2 semantics) — that's the OPPOSITE of what we
   want. Builder may not introduce any path that returns
   non-zero from `cli_stop`.
6. **Dependency fence.** Add only `mcp` to the persona venv as
   a runtime dep. Test-only deps per STATE.md rule #8 (already
   in place — pytest, etc.).
7. **Fail-closed direction.**
   - Memory service unreachable at retrieval time: empty
     payload, exit 0 (AC.M.3).
   - Memory service unreachable at write time: detached
     subprocess catches the error, logs, exits cleanly
     (AC.M.10).
   - Transcript unreadable: zero episodes, exit 0 (AC.M.9).
   - Recursive Stop: dedupe via turn id (AC.M.8).
8. **CDC adherence.** Plan-before-code (this plan), background-
   agent default for the build, scope-only dispatch, research-
   before-plan (research doc landed at the same time).
9. **`pos-amend apply --dry-run` green is a hard prereq** per
   amendment #22.
10. **AC35.3 / AC.45.S / AC46.S / AC47.S preservation.** The
    starter-pending marker prefix (AC35.3), the loam-mode
    SessionStart hook (AC.45), the persona session-start +
    user-prompt-submit hooks (AC46), and the `.mcp.json`
    contents (AC47) are all unchanged after this amendment.
11. **`stop_hook_active` field is not assumed.** The dedupe
    mechanism (D4) does not require the field to be present.
    If the builder discovers it during empirical verification,
    using it as an additional short-circuit is fine; it must
    not be the load-bearing dedupe.
12. **Stop-hook stdout is not load-bearing.** Per docs,
    Stop-hook stdout goes to debug log only — not
    additionalContext. The Stop subprocess writes nothing
    visible to the model. (No method-in-AC; this is a Stop-hook
    contract observation that the build must respect.)
13. **No edits to `personas/`.** Persona content authoring is
    out of scope (umbrella plan §4c, deferred Q1).

---

## 8. Halt triggers

Any of the following → halt and signal back to the dispatcher;
do NOT silently work around:

1. **Cross-component scope expansion.** Any required source
   edit to a sealed component outside the §7 fence — halt.
2. **AC cannot be expressed outcome-shaped.** If during build an
   AC requires method to express, halt; the AC needs re-
   authoring at the dispatcher's level.
3. **`pos-amend apply --dry-run` red** at any point — halt.
4. **Stop hook turns out to be unsuitable.** If empirical
   verification in pos3 reveals Stop does not fire reliably (or
   fires only on some turn shapes), or `transcript_path` is
   not consistently populated, or the transcript JSONL schema
   diverges materially from the assumed `user`/`assistant` walk
   — halt. Do not silently work around with a different
   trigger.
5. **`mcp` package not installable in the persona venv.** If
   the dep cannot be added (resolver conflict, build failure,
   etc.) — halt.
6. **MCP protocol mismatch.** If `client.search` or
   `client.add_episode` returns a shape inconsistent with
   the existing `MemoryClient` Protocol — halt; the Protocol
   is sealed (it lives in `memory_consumer.py`, sealed since
   amendment #33), so a mismatch is a Protocol violation that
   needs ruling.
7. **§2.5 violation in surrounding code.** If during build the
   builder discovers any branch in `memory_consumer.py`,
   `session_start_emitter.py`, `first_run_settings.py`, or
   `first_run_helper.py` that has no backing AC — halt. Do
   NOT extend a violating surface.
8. **Detachment fails on macOS.** If `Popen(...,
   start_new_session=True)` produces a child that doesn't
   actually outlive the parent — halt; alternative shapes need
   ruling.
9. **A test for any AC.M.x cannot be written deterministically.**
   Halt.

---

## 9. Out of scope (named explicitly per ODD §2.5)

- **Persona content authoring.** Umbrella plan §4c Q1 deferral
  remains in effect.
- **Auto-memory ↔ graphiti unification.**
- **Memory seeding.** Real episodes accumulate organically once
  this amendment lands.
- **Cross-workspace memory keying.** group_id = workspace slug,
  per Rule B in amendment #33.
- **Per-scope group_id.** v2 candidate per Rule B.
- **Per-message aggregation.** Rule C (turn-aggregate).
- **Awareness-block contributor for "memory writes failing."**
  The diagnostic log lands; surfacing it as an awareness-block
  category is a future amendment.
- **Live client used by orchestrator / objective-tracker /
  scope-of-work / self-correction.** First-wave consumer remains
  primary-persona only (Rule A from amendment #33).
- **Multi-contributor `hooks.Stop` registry.** Single-contributor
  for now (mirrors amendment #46's UserPromptSubmit single-
  contributor); generalisation analogous to amendment #45's
  SessionStart registry is a future amendment.
- **MCP client connection pooling / reuse across hook
  invocations.** Each hook subprocess opens-and-closes its own
  client; per-call MCP handshake is microseconds on loopback,
  not worth optimising.
- **`SubagentStop` registration.** Not in scope; Stop-only.
- **Stop-hook stdout as additionalContext.** Per Claude Code
  docs, Stop stdout doesn't reach additionalContext. We don't
  attempt it.

If any of these surface as hard prerequisites during the build,
halt-and-signal; do not silently expand scope.

---

## 10. Bookkeeping surface (`pos-amend` manifest sketch)

Per amendment #22's `pos-amend` convention. Manifest YAML at
build-dispatch, schema:

```yaml
schema_version: 1
amendment:
  number: <assigned-at-dispatch>
  slug: memory-system-live-client-and-stop-hook-write
  title: "primary-persona live MCP memory client + Stop-hook turn-close write"

baseline: <pre-amendment-tip-sha>   # HEAD~1 of amendment commit

plan: docs/plans/memory-system-live-client-and-stop-hook-write.md

seal_description: "primary-persona live MCP client + Stop-hook turn-close"

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true   # H19 frozen-BASELINE per amendment #23

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.<assigned-slug>
  body: |
    # Amendment #<n> — primary-persona live MCP memory client +
    #                  Stop-hook turn-close write
    (body authored by builder at seal time; references
     AC.M.1 – AC.M.S, the umbrella plan, and the research doc.)
```

**Universal admissions** per amendment #22 ruling #3 cover
`docs/plans/`, `CLAUDE.md`, `docs/odd-*.md`, and
`docs/FUTURE_IDEAS.md`. No other paths admitted.

**Test scope per amendment-dispatch CDC speedups (Luke
2026-04-23):** narrow pre-amendment test scope to
`primary-persona/tests/` + `hands-off-lifecycle/tests/`; skip
pre-seal full-suite rerun (sidecar-only edits between
amendment and seal); inline odd-methodology snippets into the
dispatch brief.

**Commits:**
- Amendment commit: `feat(primary-persona, hands-off-lifecycle):
  wire live MCP memory client + Stop-hook turn-close write
  (amendment #<n>, AC.M.1–AC.M.S)`.
- Seal commit: `chore(seals): primary-persona live MCP client +
  Stop-hook turn-close — primary-persona+hands-off-lifecycle at
  <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the prereq
to amendment commit; `pos-amend seal --plan-doc <abs-path>`
finalises.

---

## 11. Risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Transcript JSONL schema diverges from assumption | medium | Stop write degrades to graceful-no-op | AC.M.9 fail-soft + builder verifies schema empirically before relying (research §10 Q2) |
| Recursive Stop double-write | medium | Duplicate episodes corrupt graph | turn-id idempotency (D4); AC.M.8 measures observable count |
| `mcp` package version drift between persona and memory-system | low | Protocol error at runtime | D5 recommends exact-version pin; halt-trigger #6 catches mismatch |
| Detached subprocess leaves zombies on shutdown | low | Process accumulation | `start_new_session=True` + DEVNULL streams; child exits cleanly on every path; AC.M.10 |
| `add_episode`'s 113s cost saturates Claude Max | low | Subscription throughput pressure | Per-turn rate is bounded (one episode per turn-close); 20 turns/day × 113s = ~38min/day background; subscription absorbs |
| Stop-hook stdout accidentally reaches additionalContext | very low | Confuses Claude with internal text | Stop-hook stdout goes to debug log only per docs; AC measures observable contract; constraint 12 is the explicit reminder |
| `start_new_session=True` portability issue on macOS | low | Detachment fails | halt-trigger #8; alternative shapes ruled at halt |
| Live client's per-call handshake exceeds 5s timeout | low | Stop hook times out | Per-call handshake is microseconds on loopback; if it ever exceeds, halt-trigger #4 covers it |

---

## 12. Three-lens AC trace

| AC | Lens 1 (Claude) | Lens 2 (Translation / Toolkit) | Lens 3 (ODD) |
|----|------------------|---------------------------------|--------------|
| AC.M.1 | leverages mcp.client.streamable_http | toolkit primitive — every future memory consumer composes against | outcome-shaped |
| AC.M.2 | composes onto UserPromptSubmit additionalContext | translation: persona answers from accumulated memory | outcome-shaped |
| AC.M.3 | composes onto stdout-as-additionalContext failure shape | failure absorbed at boundary | outcome-shaped |
| AC.M.4 | leverages Stop hook (Claude-native) | toolkit primitive — every future Stop handler composes alongside | outcome-shaped |
| AC.M.5 | leverages transcript_path (Claude-native) | translation: turn content recovered without user effort | outcome-shaped |
| AC.M.6 | composes onto MCP add_episode | toolkit primitive — write path | outcome-shaped, count-bound |
| AC.M.7 | composes onto Stop's exit-0-allows-stop semantics | translation: user not blocked on memory writes | outcome-shaped, latency-bound |
| AC.M.8 | composes onto Stop firing semantics | translation: dedupe absorbed at framework | outcome-shaped, count-bound |
| AC.M.9 | composes onto JSONL transcript shape | failure absorbed at boundary | outcome-shaped |
| AC.M.10 | composes onto MCP error responses | failure absorbed at boundary | outcome-shaped |
| AC.M.11 | composes onto Claude Code's hooks.Stop registration | toolkit primitive — every future Stop registration | outcome-shaped |
| AC.M.12 | preserves all earlier Claude-native shapes | toolkit backwards-compat | structural |
| AC.M.13 | n/a | n/a | review-time audit |
| AC.M.S | n/a | n/a | structural |

---

## 13. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC.M.1, AC.M.2, AC.M.6 → AC.PO.1.** Live client + retrieval +
  write = persona answers from accumulated state. Translation
  burden absorbed.
- **AC.M.4, AC.M.5, AC.M.7, AC.M.8, AC.M.9 → AC.PO.1.** Stop-hook
  handler runs invisibly; user does not know memory is being
  persisted; translation absorbed at the framework layer.
- **AC.M.1, AC.M.4, AC.M.11 → AC.PO.2.** Three reusable toolkit
  primitives: live MCP client adapter, Stop CLI handler, Stop
  hook registration plumbing. Future contributors compose
  against them.
- **AC.M.3, AC.M.10 → AC.PO.1.** Failures absorbed at the
  boundary; user never sees memory-system errors as their
  problem.

---

## 14. Execution sequencing (suggested; builder's call to refine)

1. **Now — Luke rules on §6 decisions D1-D12.** Plan stays
   pre-dispatch until rulings land.
2. **Empirical verification in pos3 (during plan-author or
   build-dispatch prep).** Capture one Stop envelope to
   `/tmp/stop-envelope.json`; capture two consecutive transcript
   JSONL lines (one user, one assistant) to verify shape;
   document observed `stop_hook_active` field presence/absence.
3. **Build dispatch** (background agent, working dir
   `/Users/lukeivers/ivers-corp-pos-v2/`, brief carries scope
   only — AC.M.1–AC.M.S + halt triggers + ODD-check + the
   `pos-amend apply --dry-run` then commit then `pos-amend
   seal --plan-doc <abs-path>` flow).
4. **Verify in pos3:** restart Claude Code; one user prompt;
   confirm UserPromptSubmit emits a retrieval block (after at
   least one episode is in the graph); confirm Stop fires;
   confirm `<workspace>/.pos/last-turn-id` updates; confirm a
   new episode appears in the graph (verify via the
   memory-graphiti MCP tools — `mcp__memory-graphiti__search`
   for "<last user message>" returns the just-written episode).
5. **Append findings** to `FUTURE_IDEAS_DRAFT.md` per the
   no-overhead capture pattern.
6. **Update `STATE.md`** if this lands during a Phase milestone.

Per `feedback_amendment_dispatch_speedups`: the dispatch scopes
test rerun to `primary-persona/tests/` +
`hands-off-lifecycle/tests/` only.
Per `feedback_subagent_odd_violation_halt`: the dispatch carries
the explicit halt-and-surface-ODD-violations-in-surrounding-code
clause.
Per `feedback_dispatch_explicit_pos_amend_apply`: the dispatch
names `pos-amend apply --dry-run` + `pos-amend apply` +
`pos-amend seal --plan-doc <abs-path>` explicitly as the
bookkeeping mechanism.
Per `feedback_no_amend_in_agent_dispatches`: corrective commits
only; no `git commit --amend`.
Per `feedback_always_specify_wd_in_dispatches`: the dispatch
specifies WD `/Users/lukeivers/ivers-corp-pos-v2/`.

---

### Commit SHAs

- Amendment commit: `a193c32ce4e98186c2b341d7dbe191961db69892` —
  `chore(primary-persona, hands-off-lifecycle): advance BASELINE + SEAL_COMMIT for amendment #48 window`
- Seal commit: `452e7d45feb63d4024d7d6bd123b65f1e5da7ffe` —
  `chore(seals): primary-persona live MCP client + Stop-hook turn-close — primary-persona+hands-off-lifecycle at a193c32`
## 15. References

- Research doc:
  `docs/plans/research/memory-system-live-client-and-stop-hook-write-research.md`
- Umbrella plan (parent of #46/#47, this amendment composes onto):
  `docs/plans/memory-into-context-integration.md`
- Amendment #33 (D7) plan + research:
  `docs/plans/amendment-33-memory-consumer-wiring-primary-persona.md`,
  `docs/plans/research/amendment-33-memory-consumer-wiring-research.md`
- Amendment #46 builder plan (sibling pattern for hook-CLI authoring):
  `docs/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
- Amendment #47 builder plan (sibling pattern for `.mcp.json`):
  `docs/plans/amendment-47-workspace-local-mcp-json-writer.builder-plan.md`
- Memory consumer substrate (`MemoryClient` Protocol, `TurnAggregator`,
  `register_memory_retrieval`, `resolve_workspace_slug`):
  `primary-persona/src/memory_consumer.py`
- Where `_default_memory_client_factory` lives:
  `primary-persona/src/session_start_emitter.py:74`
- Persona CLI (where the new `stop` subcommand goes):
  `primary-persona/src/cli.py`
- Settings.json merge surface (where `merge_stop` goes):
  `hands-off-lifecycle/hooks/first_run_settings.py`
- First-run helper (where `_maybe_merge_stop` calls land):
  `hands-off-lifecycle/hooks/first_run_helper.py`
- Memory-system MCP service (FastMCP / streamable-HTTP):
  `memory-system/src/service.py`
- `mcp` Python client (in-tree reference):
  `memory-system/.venv/lib/python3.13/site-packages/mcp/client/streamable_http.py`
- Claude Code hooks docs:
  <https://code.claude.com/docs/en/hooks>
- ODD methodology + ODD-in-pos:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- VALUE_PROPOSITION:
  `docs/VALUE_PROPOSITION.md`
- STATE / FUTURE_IDEAS:
  `docs/STATE.md`, `docs/FUTURE_IDEAS.md`
- Amendment-dispatch bookkeeping:
  `tools/pos-amend/`

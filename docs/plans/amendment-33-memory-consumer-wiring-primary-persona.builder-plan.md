# Builder plan — amendment #33 — memory-consumer wiring (D7)

**Amendment number:** 33 (next sequential after #32 session-start
context-load gate; verified via repo tip `8e7c558`).

**BASELINE:** `8e7c558` (pre-amendment tip — amendment #32 seal
commit, `chore(seals): session-start-context-load-gate seal —
primary-persona at d2601dc`).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Authored:** 2026-04-23. **Status:** pre-code. Written BEFORE any
source edit per the plan-before-code CDC.

**Governing plan:**
`docs/plans/amendment-memory-consumer-wiring-primary-persona.md`.

This builder plan binds every method-level choice to a §4 AC-D7.N in
the governing plan. Method details below (file names, symbol names,
test layouts) are ODD-method, not ACs — ACs stay outcome-shaped.

---

## 1. Resolved context (from session-start read)

- **Shared composer is live.** `primary-persona/src/context_composer.py`
  ships `ComposedContextPayload` with `register(name, trigger_kind,
  fn)` plus `on_user_prompt_submit(prompt, resolved_component,
  memory_client)`. D8 entry-point and cap enforcement are structural.
  Per plan §3 constraint 3: D7 REGISTERS a turn-level contributor
  against this existing registry — does NOT introduce the registry.
- **Session-payload propagation.** `TurnPayload` already carries
  `corpus_gate_state` and `missing_paths`, so the D7 contributor sees
  corpus-gate state via the context dict's `session_payload`.
- **`session_payload` is in the context dict** per `context_composer.py:
  414` — `"session_payload": self._session_payload`.
- **Workspace slug primitive.** The sealed `workspace-bootstrap`
  component owns `workspace_slug(workspace_root)` at
  `workspace-bootstrap/src/workspace_bootstrap/adapters/
  first_run_scaffold.py:108`. `hands-off-lifecycle/hooks/
  first_run_helper.py:114` ships an inline stdlib-only parity copy.
  Precedent: parity-test the sanitisation against the canonical.
  The pragmatic reading of plan §7 ("no new workspace-identity
  surface") — matching the existing sanitisation convention is reuse
  of an existing in-process identity convention, not a new surface.
  The persona layer already holds `workspace_root: Path` (per
  `loader.py`, `authoring.py`, `introduction.py`, and the new D8
  composer) — deriving a slug via `Path.name` + the documented
  sanitisation is `workspace_root`'s basename transformed, not new
  identity. Parity test will verify the derivation matches the
  canonical `workspace-bootstrap.workspace_slug` sanitisation on a
  fixture set (tests-only cross-component import, permitted by
  plan §3 constraint 2 — test-fixture extensions allowed).
- **MCP tool surface (amendment #24).** `memory-system/src/service.py`
  exposes four tools: `add_episode(name, body, source_description,
  reference_time, source, group_id)` and `search(query, group_ids,
  num_results, center_node_uuid)`. `group_ids` is list[str] | None;
  `group_id` is str. The wiring binds against a MemoryClient
  protocol the builder defines locally — D7 does not import
  memory-system source (plan §8: "Memory-system source amendments
  — MCP surface from amendment #24 consumed as-is").
- **Non-blocking write.** Plan §3 constraint 5: 113 s empirical
  per-episode cost cannot block the interactive turn. Research
  lean §3.3.1 is background-scope via orchestrator, but that
  requires a scope-of-work amendment (verified by reading
  scope_of_work runtime — no "memory-writer" scope kind exists).
  Plan §6 item 4 permits research §3.3.2 (orchestrator-internal
  task) PROVIDED no orchestrator-source amendment is required —
  also requires an amendment. The cheapest non-amendment shape
  compatible with the plan: **asyncio.create_task() + fire-and-
  forget on an injected MemoryClient.** Structurally non-blocking,
  zero cross-component source touches, AC-D7.3 test uses a
  blocking stub and asserts the interactive turn proceeds.

---

## 2. Build surfaces inside `primary-persona/` (method, not AC)

### 2.1 New module `primary-persona/src/memory_consumer.py`

- `class MemoryClient(Protocol)` — narrow surface:
  `async def add_episode(*, name, body, source_description,
  reference_time, source, group_id) -> dict`; `async def search(*,
  query, group_ids, num_results, center_node_uuid) -> dict`.
  Binds exactly against the amendment-#24 MCP tool surface.
- `def resolve_workspace_slug(workspace_root: Path) -> str` —
  pure-function basename sanitisation matching
  `workspace-bootstrap.adapters.first_run_scaffold.workspace_slug`
  (re.sub `[^a-z0-9-]+` → `-`; collapse `-+`; strip `-`; raise
  `WorkspaceSlugUnrepresentableError` on empty). Test parity-verifies
  against the canonical on a fixture set.
- `class TurnAggregator` — collects user-message + persona-reply
  per turn; emits one episode on turn-close. API:
  `open_turn(turn_id) -> TurnContext`;
  `close_turn(turn_id, user_message, persona_reply) -> None`
  (schedules the async write via asyncio.create_task).
- `def build_memory_retrieval_contributor(...) -> Callable` —
  the function registered on `ComposedContextPayload.register(
  name="memory-retrieval", trigger_kind=TriggerKind.turn,
  fn=...)`. Receives the composer's context dict; issues a memory
  search; returns a text payload. On memory failure, returns empty
  string (fail-closed per plan §3 constraint 8 / AC-D7.7).
- `def build_turn_close_writer(...) -> Callable` — dispatch surface
  for turn-close. Fires `asyncio.create_task(client.add_episode(
  ..., group_id=slug))`. Never awaited on the user-facing path.
- Payload envelope cap: `MEMORY_RETRIEVAL_TOKEN_CAP = 400` (matches
  research §4.3's 200–400-token budget). Enforced structurally by
  trimming retrieval output. AC-D7.6's "cap" is the composer's
  10 000-char structural cap from D8 — the turn contributor keeps
  its own output well below that.

### 2.2 Extensions to existing modules — NONE

No edits to `context_composer.py`, `session_start_gate.py`,
`monitor.py`, `loader.py`, or any other existing primary-persona
source. The D7 wiring is purely additive via the new module.

### 2.3 Test files (one per AC, 1:1)

- `primary-persona/tests/test_D7_1_turn_start_retrieval.py` —
  AC-D7.1: seed a FakeMemoryClient with a recorded episode under
  the workspace slug; register the D7 contributor; fire
  `on_user_prompt_submit`; assert retrieval result is present in
  `turn.contributor_outputs["memory-retrieval"]`; assert the fake's
  `search` was called with `group_ids=[<slug>]`.
- `primary-persona/tests/test_D7_2_turn_close_one_episode.py` —
  AC-D7.2: drive a single turn through the aggregator;
  FakeMemoryClient records `add_episode` calls; assert exactly one
  call; assert `group_id == slug`; assert body includes both the
  user message and the persona reply. Second test: 3-turn fixture
  produces exactly 3 `add_episode` calls.
- `primary-persona/tests/test_D7_3_nonblocking_turn.py` — AC-D7.3:
  FakeMemoryClient whose `add_episode` blocks on
  `asyncio.Event().wait()`. Complete turn 1 (write is scheduled
  but unfinished); start turn 2's `on_user_prompt_submit` and
  assert it returns in well under 1 s while the first write is
  still pending.
- `primary-persona/tests/test_D7_4_group_id_is_workspace_slug.py`
  — AC-D7.4: single-turn fixture with known workspace basename;
  run AC-D7.1 + AC-D7.2 paths; inspect recorded calls; assert
  every `search` `group_ids` list contains only the slug and every
  `add_episode` `group_id` equals the slug. Includes
  parity-test against canonical
  `workspace_bootstrap.adapters.first_run_scaffold.workspace_slug`
  on at least three fixture basenames.
- `primary-persona/tests/test_D7_5_shared_registry_contract.py` —
  AC-D7.5: register BOTH a session-level (synthetic) and a
  turn-level (D7 memory-retrieval) contributor on one composer;
  fire session entry point — assert only the session contributor's
  output appears; fire turn entry point — assert only the turn
  contributor's output appears. Truth does not depend on which
  sibling introduced the registry (it's D8's, verified by import
  path in the test).
- `primary-persona/tests/test_D7_6_retrieval_payload_cap.py` —
  AC-D7.6: FakeMemoryClient returns a long retrieval payload;
  register the D7 contributor; fire `on_user_prompt_submit`;
  assert `len(turn.additional_context_text) <=
  ADDITIONAL_CONTEXT_CAP` (the composer's 10 000-char structural
  refusal). Demonstrates co-existence with D3 awareness-block
  contribution (synthetic contributor mimicking a large D3 block).
- `primary-persona/tests/test_D7_7_memory_unavailable_fail_closed.py`
  — AC-D7.7: FakeMemoryClient whose `search` raises
  `ConnectionRefusedError` / `RuntimeError(HTTP 5xx)` / a
  simulated `asyncio.TimeoutError`. Fire `on_user_prompt_submit`;
  assert no exception propagates; assert
  `turn.additional_context_text` is a valid non-crashing payload
  (memory-retrieval contributor's output is the empty string / a
  structured "[memory unavailable]" diagnostic — builder's call;
  AC measures "turn proceeds and payload emits" not exact text).

### 2.4 Seal-diff test

Already established at
`primary-persona/tests/test_no_sealed_amendments.py` by amendment
#32. This amendment extends the allowed-paths set only via `pos-amend
apply` which rewrites allowed_prefixes/files per the manifest. D7
does NOT touch the test source directly — `pos-amend apply` owns
the BASELINE advance + admissions.

---

## 3. Method → AC mapping (plan §2.5 audit, both directions)

| Method-level code / test | AC-D7.N |
|---|---|
| `MemoryClient` protocol + `FakeMemoryClient` fixture | AC-D7.1, AC-D7.2 (test surface) |
| `resolve_workspace_slug()` | AC-D7.4 |
| `build_memory_retrieval_contributor()` | AC-D7.1, AC-D7.7 |
| `TurnAggregator` + `build_turn_close_writer()` | AC-D7.2, AC-D7.3 |
| `asyncio.create_task` fire-and-forget on write | AC-D7.3 |
| Register via `composer.register(TriggerKind.turn, ...)` | AC-D7.5 |
| Memory-retrieval payload trim to ≤400 tokens | AC-D7.6 (envelope share) |
| Fail-closed catch on `search` exceptions → empty string | AC-D7.7 |
| Seal-diff test path allowances | AC-D7.S |

Reverse direction — every AC is backed:

- AC-D7.1 ← `test_D7_1_...` drives retrieval contributor.
- AC-D7.2 ← `test_D7_2_...` drives aggregator.
- AC-D7.3 ← `test_D7_3_...` drives blocking-stub.
- AC-D7.4 ← `test_D7_4_...` + parity test.
- AC-D7.5 ← `test_D7_5_...` exercises registry.
- AC-D7.6 ← `test_D7_6_...` exercises composer cap.
- AC-D7.7 ← `test_D7_7_...` exercises fail-closed.
- AC-D7.S ← manifest allowed_prefixes + pos-amend seal-diff test.

No non-objective code. No method-in-AC. No silent exception branch
that lacks an AC backing it.

---

## 4. Halt-trigger audit

1. **Cross-component scope expansion.** No source edits outside
   `primary-persona/`. Test-fixture cross-import of
   `workspace_bootstrap.workspace_slug` is tests-only (parity test
   under AC-D7.4) — explicitly admitted by plan §3 constraint 2.
   No additional component source touched. **CLEAR.**
2. **Shared-composer ownership ambiguity.** D8 already sealed;
   registry exists; D7 REGISTERS against it. **CLEAR.**
3. **Workspace-slug primitive reachability.** Per §1, persona
   layer's in-process workspace identity is `workspace_root: Path`.
   Slug is `Path.name` sanitised per the documented convention;
   matching the canonical is reuse of the existing identity
   convention. Parity-tested. Precedent:
   hands-off-lifecycle duplicates the primitive with the same
   parity pattern. **CLEAR — not halting per the precedent; if
   owner disagrees on this reading, this is the flag to revisit.**
4. **ODD break strongly required.** No. All ACs outcome-shaped;
   no silent exception branches unbacked by ACs. **CLEAR.**
5. **`pos-amend apply --dry-run` fails.** Verify before commit.
6. **Memory-system boundary semantics disagree with research.**
   Verified: amendment #24 `search(group_ids: list[str] | None)`
   and `add_episode(group_id: str)` match the research's
   assumption. **CLEAR.**
7. **AC test cannot be written deterministically.** FakeMemoryClient
   is fully deterministic; asyncio.create_task waits on an Event
   for the blocking test. **CLEAR.**
8. **Budget attribution.** Plan §8: "the builder uses the cheapest
   shape compatible with existing cost-governance without amending
   cost-governance source." Fire-and-forget asyncio task has no
   scope-of-work budget attribution — there is no triggering-scope
   scope to debit. Research §3.2 flagged both candidate shapes as
   proposal-phase decisions; neither requires cost-governance
   source to ship. **CLEAR — no amendment needed.**

---

## 5. Manifest + bookkeeping

- Manifest filename:
  `docs/plans/amendment-33-memory-consumer-wiring-primary-persona.manifest.yaml`.
- Rename governing plan to
  `amendment-33-memory-consumer-wiring-primary-persona.md` +
  research files to `amendment-33-...-research*.md` for sequential
  discipline (the current plan filename carries no number; per plan
  authoring note this is expected).
- `components:` single entry — `primary-persona`, `seal_test:
  primary-persona/tests/test_no_sealed_amendments.py`, `sidecar:
  primary-persona/tests/SEAL_COMMIT`, `frozen_baseline: false`,
  `extra_allowed_prefixes: []`.
- No test-fixture admissions needed under `orchestrator/tests/` or
  `memory-system/tests/` — the AC tests are deterministic via
  FakeMemoryClient inside `primary-persona/tests/`.
- Universal admissions same as #32.
- Narrative target:
  `primary-persona/seals/SEAL_COMMIT.memory-consumer-wiring`.

---

## 6. Sequence

1. Install primary-persona if needed (done).
2. Rename governing plan + research files; commit trivially under
   pos-amend umbrella. Actually — rename is bookkeeping and
   requires admission under `docs/plans/` which is
   universal-admitted. Do the rename inside the amendment commit.
3. Author `memory_consumer.py` with Pydantic-free narrow surfaces
   (it's an integration primitive — fake client is a Protocol
   impl; no user-facing model needed).
4. Author the 7 AC test files + conftest helpers.
5. Run primary-persona full suite.
6. Author manifest YAML.
7. `pos-amend validate` then `pos-amend apply --dry-run` — hard
   prereq per amendment #22.
8. `pos-amend apply`.
9. Amendment commit (`feat(primary-persona): memory-consumer wiring
   — amendment #33`).
10. Seal-diff-only tests across other sealed components.
11. `pos-amend seal`.
12. Seal commit (`chore(seals): memory-consumer-wiring seal —
    primary-persona at <AMENDMENT_SHA>`).
13. Re-run seal-diff-only tests across every sealed component +
    `pos-amend apply --dry-run` green.

NO `--amend`. Corrective commits only on mistakes.

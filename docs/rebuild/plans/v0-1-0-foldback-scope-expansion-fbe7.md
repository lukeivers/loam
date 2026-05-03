# FBE.7 sub-plan — Drop graphiti from v0.1.0 first-run shape (M-FBM is the v0.1.0 floor)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.7 added post-FBE.2; parent §8 register is backfilled by this amendment).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.1 sealed at `21b9480`; FBE.2 sealed at `8d2b770`. FBE.3..FBE.6 + FBE.2b sequence post-FBE.7.
**BASELINE:** `40423d5` — current canonical pos-v2 HEAD pre-FBE.7 (the FBE.2 §8-backfill commit).

---

## 1. Summary / TLDR

Luke ruled (2026-05-03 16:53 + 16:55 UTC): **graphiti must NOT ship enabled in v0.1.0.** M-FBM (file-based memory; built at `framework/primary-persona/src/loam/primary_persona/file_memory.py`) becomes the default memory backing for stranger-clone workspaces. Direct Python calls into `FileMemoryStore`; no MCP server, no port, no service.

The infrastructure is already 80% built: the `MemoryProvider` Protocol stub, `FileMemoryStore`, `FileBackedMemoryClient` adapter, and the file-based retrieval contributor all exist with explicit M-FBM framing ("Zero MCP instantiation in the runtime path" per the docstring). The runtime production paths inside primary-persona ALREADY route to `FileBackedMemoryClient`:

  - **Session-start retrieval:** `session_start_emitter._default_memory_client_factory` returns `None`; `build_session_composer`'s `else` branch registers the file-based contributor unconditionally (lines 197-216 of `session_start_emitter.py`).
  - **Stop-hook write (production):** `stop_emitter._spawn_memory_write` enqueues to disk; the long-running worker (`memory_write_worker.drain_once`) defaults to `build_file_backed_memory_client` (lines 311-319 of `memory_write_worker.py`).

The remaining net work for FBE.7 is the **workspace-bootstrap first-run scaffold:**

1. Remove `"memory-graphiti"` from the auto-launchd-supervised `_SERVICE_KINDS` set so fresh workspaces don't try to launch the graphiti service.
2. Stop writing the `memory-graphiti` registration into `<workspace>/workspace/.mcp.json` so Claude Code doesn't probe a service that isn't running.
3. Update the affected workspace-bootstrap tests (whose AC contracts were authored when graphiti was the v0.1.0 default).

`mcp_memory_client.py` stays in the tree but goes dormant (M-GMP plugin, post-v0.1.0, brings it back as a graphiti-substrate plugin against the `MemoryProvider` Protocol). `framework/memory-system/` is already partition-classified `dev_only` (not in shipping); out of fence.

Establishes a single sealed-component fence at `framework/workspace-bootstrap/` (existing seal anchor — sidecar at `framework/workspace-bootstrap/tests/SEAL_COMMIT`). Primary-persona is NOT in the fence: FBE.7 verifies its production paths already satisfy the contract; no source edits land there.

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; production runtime in primary-persona ALREADY uses M-FBM)

**Verified at planning (read primary-persona source):**

- `framework/primary-persona/src/loam/primary_persona/session_start_emitter.py`:
  - `_default_memory_client_factory` (lines 88-106) already returns `None` per AC.MFBM.5.
  - `build_session_composer` (lines 191-216) registers `register_file_memory_retrieval` directly when the factory returns None — file-based store is the production runtime path.
- `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py`:
  - `drain_once` (lines 310-319) defaults `client_factory` to `build_file_backed_memory_client` when caller doesn't override.
- `framework/primary-persona/src/loam/primary_persona/stop_emitter.py`:
  - `_spawn_memory_write` (lines 345-381) — production stop-hook write path. Just enqueues to disk via `_mwq.enqueue`. Does NOT call `build_live_mcp_memory_client`. The worker (above) drains the queue with the file-based client.

**Implication:** the dispatch's AC #2 + AC #3 + AC #4 are ALREADY SATISFIED in the primary-persona production runtime path. FBE.7's net source edits are scoped entirely to workspace-bootstrap.

### Surface #2 (admit; explained — `cli_memory_write` retains `build_live_mcp_memory_client` for legacy test surface)

**`stop_emitter.cli_memory_write` (line 551) still calls `build_live_mcp_memory_client(workspace_root)`.** This function is the legacy synchronous entry point — pre-amendment-J (the queue + worker pivot) it WAS the production path; post-J the worker drains the queue and `cli_memory_write` is preserved as a "still-callable surface for tests that exercise the per-turn-record write contract directly" per its docstring (lines 36-37, 518-527).

Three tests depend on `cli_memory_write` calling `build_live_mcp_memory_client` so they can monkeypatch `mcp_memory_client.build_live_mcp_memory_client` and exercise the legacy code path:

  - `framework/primary-persona/tests/test_AC_J_8_backwards_compat_with_amendment_48.py:140-172` (test_AC_J_8_existing_cli_memory_write_path_still_callable).
  - `framework/primary-persona/tests/test_AC_M_10_live_client_failure_during_write.py:55,82,110` (three AC.M.10 fail-soft variants).
  - `framework/primary-persona/tests/test_AC_J_2_stop_hook_enqueues_for_async_drain.py:111` (uses the patch site to assert the queue path doesn't reach the live client).

**Multi-signal conflict resolution** (per `feedback_principle_conflict_resolution_multi_signal`):

  - **Conflict named:** dispatch AC #3 ("stop_emitter.py uses FileBackedMemoryClient directly for writes") vs preserving the AC.J.8 + AC.M.10 + AC.J.2 backwards-compat contracts (which depend on `build_live_mcp_memory_client` being the patch site inside `cli_memory_write`).
  - **Signals:**
    - **Information asymmetry:** dispatcher likely read AC #3 as a wholesale `cli_memory_write` edit; the production-runtime path in stop_emitter is `_spawn_memory_write` → queue → worker → `FileBackedMemoryClient`, which already satisfies "no MCP HTTP roundtrip in the production path".
    - **Blast radius:** literal AC #3 edit breaks 3+ standing AC contracts (AC.J.8 explicitly says "legacy detached-child entry point remains callable for backward-compat" — a contract, not just a test).
    - **Reversibility:** high — both directions are reversible.
    - **Scope-tightness:** dispatch hard halt: "Existing tests assert behaviour that contradicts FBE.7's objective (e.g., a test asserting the persona MUST use LiveMCPMemoryClient with no fallback) → halt + surface". The cli_memory_write tests don't assert "MUST use Live"; they assert "the legacy surface still exists". Different shape.
    - **Dispatch's "DO NOT edit mcp_memory_client.py":** intentionally keeps the M-GMP path open. Editing cli_memory_write to drop the build_live_mcp_memory_client call wouldn't violate that literally, but it WOULD remove the test patch-point that exercises mcp_memory_client.
  - **Call (autonomous):** **Do NOT edit `cli_memory_write`.** The production runtime path satisfies the dispatch's intent ("no MCP HTTP roundtrip"). `cli_memory_write` stays as the legacy test-callable surface. AC #3 reading: "stop_emitter's production-runtime write path uses FileBackedMemoryClient (via the worker → queue → file-store chain)" — which is already true.
  - **Surface to dispatcher:** YES, in the FBE.7 status report. Non-obvious enough that a different reasonable person would read AC #3 literally and edit cli_memory_write.

### Surface #3 (admit; explained — `mcp_json_writer.py` only writes the memory-graphiti entry; the writer becomes a no-op consumer if memory-graphiti is removed)

`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/mcp_json_writer.py` is **single-purpose**: its only consumer-emitted entry is the `memory-graphiti` server registration (`MEMORY_GRAPHITI_SERVER_NAME = "memory-graphiti"` is the lone server name; the writer's docstring + every code path is graphiti-specific).

Per dispatch AC #6's branch ("decide whether to keep the writer entirely if it has other consumers, or stub it out if memory-graphiti was its only entry"): **memory-graphiti IS its only entry** → the writer's first-run consumer (the `_run_mcp_json_writer` helper inside `first_run_scaffold`) becomes a no-op for v0.1.0.

**Resolution:** rather than delete `mcp_json_writer.py` (which would dramatically widen the diff and break tests like AC47.1, AC47.2 which exercise the pure-function builders independently of first_run_scaffold integration), STOP CALLING IT from `first_run_scaffold.run_first_run_scaffold`. The pure functions (`build_memory_graphiti_entry`, `merge_mcp_json`, `write_mcp_json`) stay in the tree, dormant, ready for M-GMP to wire them back into a graphiti-plugin's first-run path.

**Test impact:** AC47.1, AC47.2, D.2 HC#4 (`test_HC4_mcp_json_byte_content_match`) all assert the .mcp.json IS written by the scaffold. AC47.1 + AC47.2 also have direct unit tests against the pure builders. The pure-builder tests (AC47.1's `build_memory_graphiti_entry`, AC47.2's `merge_mcp_json`) survive byte-identically. The scaffold-integration test (`test_AC47_1_fresh_clone_writes_mcp_json_with_memory_graphiti_entry`) is the one that needs invertingto assert "scaffold does NOT write .mcp.json on fresh-clone v0.1.0" (per FBE.7 contract). Same shape for `test_HC4_mcp_json_byte_content_match`.

### Surface #4 (admit; explained — `_SERVICE_KINDS` mutation breaks D5 + AC29 + AC.J.5 plist tests)

Removing `"memory-graphiti"` from `_SERVICE_KINDS` (line 223 of `first_run_scaffold.py`) means:

- The `_LAUNCHD_TEMPLATES` dict's `"memory-graphiti"` entry becomes unused.
- `service_label("memory-graphiti", slug)` raises `ValueError` (the `if kind not in _SERVICE_KINDS` guard at line 232).
- Tests that exercise the graphiti plist:
  - `test_first_run_scaffold.py` line 96-100 (the labels-set assertion).
  - `test_AC29_scaffold_memory_port.py` (asserts the graphiti plist carries `GRAPHITI_SERVICE_PORT`).
  - `test_D5_plist_path_emission.py` (D5.1 reaches /health on the graphiti service; D5.2 compares graphiti and orchestrator PATH; D5.3 compares EnvironmentVariables key sets).
  - `test_AC_J_5_memory_write_worker_plist.py` (compares the worker plist to the graphiti shape).

**Decision (autonomous):** keep the `_LAUNCHD_TEMPLATES["memory-graphiti"]` template definition + the `service_label` mapping for `"memory-graphiti"` (so the symbol round-trips and M-GMP can re-admit it as one line), but REMOVE `"memory-graphiti"` from `_SERVICE_KINDS` (the auto-launched set). This means `service_label("memory-graphiti", slug)` will raise ValueError post-FBE.7 — that's the test-impact surface. Affected tests get updated or marked skipped per AC#7.

**Alternative considered:** keep `"memory-graphiti"` in `_SERVICE_KINDS` but skip the `bootstrap` call for it. **Rejected** because it leaves the plist file installed on disk + launchd has the label registered; first-run is supposed to look CLEAN. The plist-file write IS the user-visible surface that says "graphiti is part of v0.1.0". Removing the kind from `_SERVICE_KINDS` is the cleanest way to prevent the plist file from being written at all.

### Surface #5 (no halt; recorded — Protocol verification)

The dispatch's hard halt requires that `FileBackedMemoryClient` satisfies the `MemoryClient` Protocol returned by `_default_memory_client_factory`. Verified at planning:

  - **`MemoryClient` Protocol** (memory_consumer.py:99-139):
    - `async def add_episode(*, name, body, source_description, reference_time, source, group_id) -> dict[str, Any]`
    - `async def search(*, query, group_ids, num_results, center_node_uuid) -> dict[str, Any]`
  - **`FileBackedMemoryClient`** (file_memory.py:765-825):
    - `async def add_episode(*, name, body, source_description, reference_time, source, group_id) -> dict[str, Any]` — matches.
    - `async def search(*, query, group_ids, num_results, center_node_uuid: str | None = None) -> dict[str, Any]` — matches structurally; `center_node_uuid` carries a default value (Protocol declares it required; Python Protocol is duck-typed, so callers passing the kwarg work; callers omitting it also work since `FileBackedMemoryClient` has the default). Documented as "accepted for Protocol parity but ignored at v0.1.0 (graph traversal is M-GMP)" per the docstring at lines 815-819.

**Conformance: structural.** AC #2's "FileBackedMemoryClient instead of LiveMCPMemoryClient" reading is satisfied by the existing infrastructure; `_default_memory_client_factory` returning None and the file-based contributor being registered in the else-branch is the production-runtime equivalent (see Surface #1).

### Surface #6 (no halt; recorded — pos3 cleanup is OUT OF SCOPE)

The dispatch explicitly notes: "Pos3 (the dev workspace) will get an analogous local cleanup AFTER FBE.7 lands (out of FBE.7's scope; sequenced as a separate operation post-seal)." FBE.7 is canonical-only edits.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — making fresh stranger-clone workspaces install + run cleanly without a graphiti service is the core "stranger can install" promise. Today, a fresh v0.1.0 workspace would auto-launch a graphiti service that may not have its sidecar deps installed → broken first-run UX.
- **Reviewer foldback (post-M11a-3)** — Luke's M-FBM pivot ruling closes the operational risk that graphiti's sidecar install path adds friction to v0.1.0 launch.
- **AC.MFBM.1..7** (oss-v0-1-0-publish-memory-pivot.md) — M-FBM's substrate ACs are already met inside primary-persona; FBE.7 closes the workspace-bootstrap-side gap (don't auto-launch graphiti; don't register it in .mcp.json).

**Ladders to:** AC.FBE.7.* → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.7.*)

AC family **`AC.FBE.7.*`** — collision-safe (verified: `grep -rE "AC\.FBE\.7" docs/` returns no prior hits).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.7.1** | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`'s `_SERVICE_KINDS` tuple no longer contains `"memory-graphiti"`. The remaining auto-launched kinds are `("orchestrator", "memory-write-worker")`. | `python -c "from loam.workspace_bootstrap.adapters.first_run_scaffold import _SERVICE_KINDS; assert 'memory-graphiti' not in _SERVICE_KINDS"` |
| **AC.FBE.7.2** | `_LAUNCHD_TEMPLATES["memory-graphiti"]` entry remains in the dict (preserves the plist template for M-GMP re-admission post-v0.1.0). `service_label("memory-graphiti", slug)` raises `ValueError` post-FBE.7 because `"memory-graphiti"` is no longer in `_SERVICE_KINDS` (the same guard at line 232 governs both reads). | Direct read of source + assertion in updated test fixture. |
| **AC.FBE.7.3** | `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`'s `run_first_run_scaffold` no longer calls `_run_mcp_json_writer` on the v0.1.0 production path. The pure-function builders (`build_memory_graphiti_entry`, `merge_mcp_json`, `write_mcp_json`) remain in `mcp_json_writer.py` (preserved for M-GMP). | `grep -n '_run_mcp_json_writer' framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` returns no callers; the helper itself remains for tests + M-GMP. |
| **AC.FBE.7.4** | `ScaffoldResult.mcp_json_*` fields gain neutral default values when the writer isn't invoked: `mcp_json_path=None`, `mcp_json_wrote=False`, `mcp_json_reason="skipped_v0_1_0_no_graphiti"`. The dataclass shape is preserved (back-compat for any consumer reading the fields); the values communicate "v0.1.0 didn't write the file by design". | `_default_factory` test of `ScaffoldResult` + scaffold-integration test asserting the new reason value. |
| **AC.FBE.7.5** | Updated tests at `framework/workspace-bootstrap/tests/`: (a) `test_first_run_scaffold.py` line 96-100 labels-set asserts `{"com.loam.pos-v2.orchestrator", "com.loam.pos-v2.memory-write-worker"}` (memory-graphiti dropped); (b) `test_AC29_scaffold_memory_port.py` updated to assert the graphiti plist is NOT installed (or marked skipped with FBE.7 attribution); (c) `test_D5_plist_path_emission.py`'s D5.1 (graphiti /health probe) marked skipped with FBE.7 attribution; D5.2 + D5.3 either skip or update to compare orchestrator + memory-write-worker; (d) `test_AC_J_5_memory_write_worker_plist.py`'s memory-graphiti-shape comparison either updates to compare to the orchestrator shape or skips the comparison; (e) `test_AC47_1_fresh_clone_writes_mcp_json.py`'s scaffold-integration test inverts to assert .mcp.json is NOT written (or is skipped with FBE.7 attribution); the pure-function builder tests stay byte-identical; (f) `test_AC47_2_deep_merge_preserves_user_entries.py`'s pure-function tests stay; if it has scaffold-integration variants, they invert; (g) `test_d2_workspace_state_scaffold.py`'s `test_HC4_mcp_json_byte_content_match` marked skipped with FBE.7 attribution. | `pytest framework/workspace-bootstrap/tests/` returns green (counts may shift due to skips; net pass ≥ baseline-skips). |
| **AC.FBE.7.6** | Negative AC: zero edits to `framework/primary-persona/src/loam/primary_persona/mcp_memory_client.py`. (Per dispatch: stays dormant; M-GMP brings it back.) | `git diff BASELINE..SEAL_COMMIT -- framework/primary-persona/src/loam/primary_persona/mcp_memory_client.py` is empty. |
| **AC.FBE.7.7** | Negative AC: zero source edits to `framework/primary-persona/src/loam/primary_persona/{session_start_emitter.py,stop_emitter.py,memory_write_worker.py,file_memory.py}`. The production-runtime FBE.7 contract is satisfied by the existing M-FBM infrastructure (verified at §2 Surface #1 + Surface #5). | `git diff BASELINE..SEAL_COMMIT -- framework/primary-persona/src/loam/primary_persona/` is empty. |
| **AC.FBE.7.8** | Negative AC: zero edits to `framework/memory-system/`. The component is already partition-classified `dev_only`; FBE.7 doesn't reach inside it. | `git diff BASELINE..SEAL_COMMIT -- framework/memory-system/` is empty. |
| **AC.FBE.7.9** | `framework/primary-persona/tests/` continues to pass byte-identically (521/521 pre-FBE.7, target 521/521 post-FBE.7). The M-FBM contract was already in place; FBE.7 doesn't touch primary-persona source or tests. | `pytest framework/primary-persona/tests/` returns 521 passed. |
| **AC.FBE.7.S** | Sealed-component fence: `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under `framework/workspace-bootstrap/` (the sealed component) + `docs/rebuild/plans/` (universal_paths.prefixes; sub-plan + manifest YAML + parent backfill). | `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py` invariant + manual `git diff --name-only` check at seal time. |

**ACs deliberately out of scope (NOT in FBE.7):**
- `cli_memory_write` edit to drop `build_live_mcp_memory_client` (Surface #2 conflict-resolution call: keep the legacy test surface; production runtime already uses M-FBM via the queue → worker chain).
- `mcp_memory_client.py` edits (dispatch hard constraint; AC.FBE.7.6).
- Pos3 dev-workspace local cleanup (out of scope per dispatch + Surface #6).
- `framework/memory-system/` source/scaffold edits (already `dev_only`; AC.FBE.7.8).
- M-GMP (graphiti plugin) wiring (post-v0.1.0).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
The .mcp.json surface IS the Claude Code MCP-discovery primitive — FBE.7's restraint here (NOT writing a memory-graphiti registration when the substrate isn't ready) avoids leveraging Claude Code's MCP infrastructure for a service that doesn't exist in the workspace. Correctly STOPS leveraging Claude's MCP probe when there's no service to find. The substrate-composition Protocol (`MemoryProvider`) keeps the M-GMP plugin path open.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Removes the "you need to start a graphiti sidecar" friction from fresh-clone first-run. The persona's memory retrieval still works (file-based store). The user's experience is "loam init then claude" — no manual sidecar launch.
- **Harness test:** PASS. Preserves the harness's runtime memory toolkit (file-based retrieval + write); removes a runtime dependency that wasn't ready for v0.1.0 stranger-clone.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which constants get edited, which test expectations invert, which tests get skipped vs updated) is builder's call. No "options to rule on" framed inside this plan-doc — every edit maps to AC.FBE.7.{1..9,S}.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape (Luke's two explicit rulings; M-FBM substrate already 80% built; the runtime-side primary-persona work is done). Tight scope. ACs name observable outputs; method (which YAML lines, which tuple entry, which test patches) is inferable from the existing surface without prescription.

### Lens 5 — Swarming
FBE.7 is a leaf in the foldback's planner-output (added post-FBE.2 ruling). Internally the ACs do not partition further: each binds to a single observable surface (constants tuple, helper-call removal, dataclass defaults, test set updates, fence diff). Each is leaf-scoped. No sub-decomposition.

---

## 6. File-by-file map

### Edits within sealed-component fence (`framework/workspace-bootstrap/`):

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`:
  - `_SERVICE_KINDS` tuple (line 223-227): REMOVE `"memory-graphiti"`. Add a 4-line provenance comment naming FBE.7 + the parent foldback plan-doc.
  - `_LAUNCHD_TEMPLATES["memory-graphiti"]` entry (lines 1011-1031): KEPT (preserved for M-GMP re-admission post-v0.1.0; commented as such).
  - `run_first_run_scaffold` (lines 707-712): REMOVE the `_run_mcp_json_writer` invocation; replace with a literal `MCPJsonWriteResult(wrote=False, reason="skipped_v0_1_0_no_graphiti", path=None)` so the `ScaffoldResult` fields downstream (lines 770-772) carry meaningful neutral defaults. The `_run_mcp_json_writer` helper itself (lines 776-799) stays in the tree (preserved for M-GMP + tests).
  - `MCPJsonWriteResult.path` field type (mcp_json_writer.py:113 — but that's outside this file): see below.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/mcp_json_writer.py`:
  - **NO source edits** to the writer itself. The writer's pure functions (`build_memory_graphiti_entry`, `merge_mcp_json`, `write_mcp_json`) stay byte-identical for M-GMP. The only delta is that `first_run_scaffold` no longer calls `write_mcp_json` on the v0.1.0 production path.
  - **Adjustment to `MCPJsonWriteResult` literal-construction in `first_run_scaffold`:** since we construct one with `path=None` post-FBE.7, the `path: Path` field type in `MCPJsonWriteResult` either widens to `path: Path | None` (one-line edit at line 116 of mcp_json_writer.py) or the scaffold constructs a sentinel path. **Decision:** widen the type (one-line edit, preserves dataclass usage shape; `path` is not a key field consumers branch on per AC47.x).
- `framework/workspace-bootstrap/tests/test_first_run_scaffold.py`:
  - Lines 94-100: update labels-set assertion to drop `"com.loam.pos-v2.memory-graphiti"`. Add inline FBE.7 attribution comment.
- `framework/workspace-bootstrap/tests/test_AC29_scaffold_memory_port.py`:
  - Update to assert the graphiti plist is NOT installed post-FBE.7 (the path doesn't exist), OR mark the test skipped with FBE.7 attribution. **Choice:** mark skipped (the AC.29 contract was specifically about graphiti port wiring; that AC is moot at v0.1.0).
- `framework/workspace-bootstrap/tests/test_D5_plist_path_emission.py`:
  - D5.1 (`test_D5_1_memory_graphiti_scaffold_plist_reaches_health_200`): mark skipped with FBE.7 attribution.
  - D5.2 (`test_D5_2_orchestrator_plist_carries_same_path_as_memory_graphiti`): the function fixture `_scaffold_fresh_sandbox` returns both plists; post-FBE.7 the graphiti plist is absent. Mark skipped with FBE.7 attribution (the path-shared invariant is moot when only one plist exists).
  - D5.3 (`test_D5_3_emitted_plists_carry_only_authored_environment_keys`): same as D5.2; mark skipped.
- `framework/workspace-bootstrap/tests/test_AC_J_5_memory_write_worker_plist.py`:
  - Lines 22, 46 reference the memory-graphiti shape as the comparison target. The actual assertion is on the worker plist's structure; the comparison-to-graphiti was illustrative. Update the assertion to compare to the orchestrator shape (which still ships) OR mark the comparison-helper skipped while keeping the worker-plist-exists assertion. **Choice:** the test asserts the worker plist's content directly — keep the assertions, update inline comments to drop graphiti references (text-only, no behaviour change).
- `framework/workspace-bootstrap/tests/test_AC47_1_fresh_clone_writes_mcp_json.py`:
  - The scaffold-integration test (`test_AC47_1_fresh_clone_writes_mcp_json_with_memory_graphiti_entry`): mark skipped with FBE.7 attribution. The pure-function builder tests in the same file (if any) stay.
- `framework/workspace-bootstrap/tests/test_AC47_2_deep_merge_preserves_user_entries.py`:
  - Pure-function tests stay byte-identical. Scaffold-integration variants (if any) mark skipped with FBE.7 attribution. Verify at build time which is which.
- `framework/workspace-bootstrap/tests/test_d2_workspace_state_scaffold.py`:
  - `test_HC4_mcp_json_byte_content_match` (lines 311-323): mark skipped with FBE.7 attribution.

### NEW file under sealed-component fence — none.

(`framework/workspace-bootstrap/tests/SEAL_COMMIT` already exists; FBE.7 bumps it via `loam amend apply` + `loam amend seal`.)

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register: ADD a NEW `### FBE.7 — Drop graphiti from v0.1.0 first-run shape` subsection with apply commit SHA + seal commit SHA. The parent plan was authored before FBE.7 existed; this is a structural addition.

**TOTAL fence diff:** 1 source file + 1 mcp_json_writer single-line type widening + 7 test files within `framework/workspace-bootstrap/` + plan-doc + manifest YAML (universal-admitted) + parent plan-doc backfill (universal-admitted).

---

## 7. Hard constraints

- Single sealed-component fence: `framework/workspace-bootstrap/` (existing seal anchor at `framework/workspace-bootstrap/tests/SEAL_COMMIT`).
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.7.*` (collision-safe; verified).
- Auto-memory `MEMORY.md` NOT touched.
- Zero edits to `framework/primary-persona/src/loam/primary_persona/mcp_memory_client.py` (AC.FBE.7.6 forbids; dispatch constraint).
- Zero source edits to `framework/primary-persona/src/loam/primary_persona/` (AC.FBE.7.7 forbids; M-FBM contract already satisfied).
- Zero edits to `framework/memory-system/` (AC.FBE.7.8 forbids; partition classifies it `dev_only`).
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`:
  - `framework/workspace-bootstrap/tests/` (full component sweep).
  - `framework/primary-persona/tests/` (verify the M-FBM contract still passes 521/521 with no source edits).

---

## 8. Out of scope (per ODD §2.5)

- `cli_memory_write` edit to drop `build_live_mcp_memory_client` (Surface #2 conflict-resolution).
- `mcp_memory_client.py` edits (dispatch + AC.FBE.7.6).
- M-GMP plugin authoring (post-v0.1.0).
- Pos3 dev-workspace local cleanup (sequenced as a separate operation post-seal).
- `framework/memory-system/` source/scaffold edits.
- Synth pipeline path-rewrite fix (parent Decision D; FBE.2b).

---

## 9. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** Discover an additional shipping component (per partition classification) that imports `LiveMCPMemoryClient` or otherwise depends on graphiti at runtime → halt; widen FBE.7 scope after surfacing.
- **HT-2:** A test failure post-edit that asserts behaviour FBE.7's contract OBSERVES SHOULD CHANGE (e.g., a test asserting the persona MUST find a live MCP client at first-run) → halt; surface the test for owner ruling. Don't silently extend the patch.
- **HT-3:** `mcp_json_writer` removal from the scaffold's call site causes the writer to fail import (e.g. an unused-import lint trip) → keep the import in the scaffold (the helper `_run_mcp_json_writer` stays in the tree per AC.FBE.7.3); only the call from `run_first_run_scaffold` is removed.
- **HT-4:** Building the `ScaffoldResult(... mcp_json_path=None ...)` literal raises (because the dataclass field types assume non-None) → widen the type at `MCPJsonWriteResult.path` to `Path | None` (one-line edit; documented at AC.FBE.7.3 file-by-file map).
- **HT-5:** `loam amend apply` against the FBE.7 manifest fails with a fence breach diagnostic → surface; the manifest's `extra_allowed_files` / `universal_paths` block needs adjustment.
- **HT-6:** Wall-time exceeds 100 min (dispatch hard cap) → halt with partial findings.
- **HT-7:** WD drifts to pos3 → halt immediately.
- **HT-8:** A surrounding-code ODD §2.5 violation discovered in `first_run_scaffold.py` or another touched file → surface; do NOT silently extend or fix in-band.
- **HT-9:** `cli_memory_write` Surface #2 ruling needs revision (e.g. the dispatcher rules that AC #3 IS literal and `cli_memory_write` MUST be edited) → halt; this is post-seal escalation not in-FBE.7 scope.

---

## 10. Risks

- **Risk: tests skipped under FBE.7 attribution become a debt.** Several tests get marked `pytest.mark.skip(reason="FBE.7 — memory-graphiti not in v0.1.0; M-GMP restores")`. M-GMP (post-v0.1.0) will need to un-skip these. Mitigation: every skip reason carries the exact FBE.7 + M-GMP attribution so the un-skip path is mechanical.
- **Risk: a fresh-clone v0.1.0 user installs the workspace, opens claude, and the persona's session-start retrieval surfaces nothing useful (because the file-based store has zero episodes on first turn).** Mitigation: this is the M-FBM design — first-turn empty is the documented graceful-empty state (AC.MFBM.2 / AC46.2). The retrieval block emits the empty shape; the turn proceeds.
- **Risk: workspace-bootstrap component's own tests carry implicit assumptions that the .mcp.json file IS in `<workspace>/workspace/`.** Mitigation: the file isn't required to exist; tests that assert presence get updated/skipped per AC.FBE.7.5.
- **Risk: the dispatcher's literal AC #3 reading is the right one and Surface #2's "do not edit cli_memory_write" call is wrong.** Mitigation: Surface #2 explicitly surfaces this in the FBE.7 status report; if owner rules differently, a corrective amendment edits cli_memory_write + updates the AC.J.8 + AC.M.10 + AC.J.2 tests in lockstep.

---

## 11. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Source + test edits commit** — single commit covering: `_SERVICE_KINDS` mutation, `_run_mcp_json_writer` removal from `run_first_run_scaffold`, `MCPJsonWriteResult.path` type widening, `ScaffoldResult` literal default, 7 test file updates. Verify `pytest framework/workspace-bootstrap/tests/ framework/primary-persona/tests/` returns green.
3. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.manifest.yaml`.
4. **`loam amend apply`** — invoke against the manifest. Produces the apply-bookkeeping commit (BASELINE bump in `test_no_sealed_amendments.py`, sidecar bump in `SEAL_COMMIT`).
5. **`loam amend seal`** — produces the deterministic seal commit; sidecar `SEAL_COMMIT` advances to the seal SHA; narrative file written at `tests/SEAL_COMMIT.notes`.
6. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 add NEW `### FBE.7` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
7. **Status file** — write `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe7-status-2026-05-03.md` (outside canonical tree; the dispatcher reads it).

NO `git commit --amend` at any point. NO push to any remote.

---

## 12. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (§8 backfilled by FBE.7 itself).
- **Memory-pivot plan:** `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md` (M-FBM ACs already met inside primary-persona).
- **FBE.1 status (precedent):** `<workspace>/.scratch/claude-output/fbe1-status-2026-05-03.md`.
- **FBE.2 status (precedent):** parent plan §8 FBE.2 backfill (no separate status file shown in canonical; the §8 entry is the precedent).
- **FBE.1 sub-plan / manifest YAML (shape precedent):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe1.{md,manifest.yaml}`.
- **FBE.2 sub-plan / manifest YAML:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe2.{md,manifest.yaml}`.
- **M-FBM substrate source (READ ONLY at FBE.7):** `framework/primary-persona/src/loam/primary_persona/file_memory.py`.
- **Touched scaffold source:** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`.
- **Touched mcp_json source (one-line type widening only):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/mcp_json_writer.py`.
- **Memory-pivot test (M-FBM AC.5 verification):** `framework/primary-persona/tests/test_AC_MFBM_5_no_mcp_runtime_instantiation.py`.
- **MCP client (READ ONLY at FBE.7; preserved dormant):** `framework/primary-persona/src/loam/primary_persona/mcp_memory_client.py`.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_loose_AC_text_fix_AC_not_implementation` (Surface #2 + AC.FBE.7.5 disambiguate "tests pass" via explicit per-test edit/skip enumeration).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §11).
  - `feedback_subagent_odd_violation_halt` (HT-1, HT-2, HT-8 cover ODD violations).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to two components touched).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–6 explicit in §2; Surface #2 surfaces the cli_memory_write call for the dispatcher).
  - `feedback_principle_conflict_resolution_multi_signal` (Surface #2 names the conflict, signals, call, and surface step explicitly).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at planning" claim has a path/line citation).
  - `feedback_critical_thinking_on_deviations` (Surface #2 + Surface #3 + Surface #4 enumerate alternatives weighed by outcome × cost × risk).

---

## 13. AI-time band

- Predicted: **30–55 min, midpoint 40 min**; dispatch hard cap 100 min.
- Justification: small source edit (one tuple, one helper-call removal, one default-literal, one type widening) + 7 test file updates (each ~3-15 line edit or `pytest.mark.skip` decoration) + manifest authoring + apply + seal + backfill + status. Per rubric category: amendment-build (multi-component-aware single-fence) → 20–45 min midpoint 32; widen to 30–55 min for the cross-component test verification (primary-persona AC.FBE.7.7 + AC.FBE.7.9 sweep) and the conflict-resolution surface authoring overhead.

---

## 14. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source + test edits commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.7 sub-plan-doc. Ready to build.*

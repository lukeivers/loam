# Plan — memory-pipeline-fix (Stop hook re-seating + retrieval visibility + group_id alignment)

**Status:** authored 2026-04-29 by builder (task #21 in dispatcher queue — LAST PRE-PUBLISH BLOCKER per owner directive 2026-05-01).
**Predecessors (all sealed):** Memory-sidecar-recovery (`8ee241b`), M1c-corrective (`603e953`), Post-M6 partition-realignment (`e2828ba`).
**Successor candidate:** M11 dry-run (synthesis) with owner gate review.
**Authority:** dispatcher directive 2026-05-01.
**Companion research:** `.scratch/claude-output/stop-hook-and-retrieval-diagnostic.md` — diagnostic-agent report 2026-04-29 with empirical evidence (jsonl event counts; lsof; live MCP probe; settings.json keys; episode group_id audit). Research-before-plan gate is satisfied by that report; no separate research artefact authored here.

---

## 1. Summary / TLDR

The memory pipeline does not function end-to-end. Three coupled defects, plus two cosmetic / diagnostic CDC violations, identified by the diagnostic agent at five named file:line sites:

1. **Stop hook never registered in pos3** (Surface 1). `_maybe_merge_stop` only fires from `first_run_helper.py`'s first-run-only Phase 3d / Phase 4c / Phase 6 paths. Pos3's first-run completed 2026-04-23 16:23 UTC and has not re-run; the Stop stanza never landed. **Fix:** lift the Stop-merge into a session-start re-seating surface invoked by `pos_session_start.py` on every session-start. The merge logic is already idempotent over pos-v2-owned stanzas (`test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py`).

2. **Retrieval contributor returns silent `""` on empty results** (Surface 2c). `memory_consumer.py:305-307` `_render_retrieval` returns `""` when results are empty. The contributor runs (~1.2s, exit 0), search returns 0 results, contributor returns `""`, composer emits `[memory-retrieval]\n    \n`. **Fix:** return a structured `"[memory-retrieval]\n  (no results for this query)"` instead, making the empty-state observable in the UPS hook stdout per M6c graceful-fallthrough-with-detection CDC.

3. **Retrieval contributor swallows exceptions silently** (Surface 2c — companion to #2). `memory_consumer.py:256-261` try/except returns `""` on any boundary error (connection refused, HTTP 5xx, timeout, garbage response). **Fix:** add a `_append_diag` (mirror of write-side `memory-writes.log` mirror) that writes one diagnostic line to `<workspace>/.pos/memory-reads.log` carrying exception type + workspace slug. M6c CDC compliance.

4. **Cosmetic dead-code drop** (Surface 2c — cosmetic). `context_composer.py:543-546` `or [""]` fallback emits a trailing whitespace-only line for empty contributor output. Once Fix #2 lands the empty-text path is reachable only when a contributor genuinely returns `""` (for which the composer-side tolerance is no longer load-bearing). **Fix:** drop the `or [""]` fallback and `continue` on empty-text contributors instead. Marked optional in the diagnostic but cleaner: it removes the only non-graceful trailing whitespace surface.

5. **Write/read group_id misalignment** (Surface 2a). Diagnostic found 3 episodes in kuzu under `group_id="pos-v2_default"` (memory-system's `default_scope_id` per `memory.yml:72`); persona's read path queries with `group_ids=[workspace_slug]` = `["pos3"]`. **Fix:** option (i) per dispatch recommendation — write-side adopts `workspace_slug`. Persona's `TurnAggregator.close_turn` already writes with `group_id=workspace_slug` (per `memory_consumer.py:183`); the orphan `pos-v2_default` data is verification-scaffolding from an earlier path (likely amendment #74 verification) and is accepted as lost. **No source change required for write-side (already correct);** the alignment is already in place at the persona layer. The fix here is documentation of the convention + explicit AC fixing the convention so a future write-path additions don't drift.

   - **Halt-and-surface (HSF#1, see §16):** the diagnostic noted that `group_ids=["pos-v2_default"]` returns 0 results while `group_ids=None` returns 3, even though the data is in kuzu under that group_id. This suggests the FastMCP service's `group_ids` filter is broken or non-functional. **Empirical re-test during build:** if the filter is reproducibly broken, halt and surface for a separate FastMCP-investigation amendment; the other 4 fixes still land. The `pos3` write/read alignment doesn't depend on the FastMCP filter working — both writes AND reads carry `group_id=workspace_slug=pos3`; if the filter is broken, search would return 0 for any specific group_ids, but the `group_ids=None` path would still surface results. The contributor passes a non-None list, so retrieval would fall back to 0 results — observable per Fix #2. So the FastMCP filter is **separable** from this amendment's outcome; complete the 5 fixes as a coherent unit and surface FastMCP-filter as a follow-on.

The five fixes ship as one amendment because (a) they share the `pos-v2_default` / Stop-hook-not-firing root cause-cluster, (b) Fix #1 unblocks the empirical end-to-end verification that motivates Fix #5's documentation, and (c) Fix #2 + #3 + #4 are all M6c CDC operationalisation on the read side, structurally adjacent to Fix #1's write-side restoration.

**The pos3 settings.json edit** to apply the Stop stanza directly (as an immediate operational unblock for pos3 BEFORE next session-start) is named in dispatch halt trigger #7. The structural fix (Fix #1) handles all post-fix workspaces; for pos3 specifically, the operator can trigger re-seat by starting a new Claude session in pos3 (which fires `pos_session_start.py`, which now re-seats Stop). **No direct settings.json edit by this amendment** — the structural fix is sufficient and the operator can take the new session.

---

## 2. Research findings (inlined)

### 2.1 Diagnostic-agent report

`.scratch/claude-output/stop-hook-and-retrieval-diagnostic.md` carries the full investigation. Key citations:

- **Surface 1 evidence:** pos3's `.claude/settings.json` carries SessionStart (2 inner) + UserPromptSubmit (1 inner) but NO `hooks.Stop` key. Session jsonl shows 0 Stop firings vs 68 UserPromptSubmit firings vs 2 SessionStart firings. No `.pos/memory-write-queue/`, no `.pos/memory-writes.log`, no `.pos/last-turn-id` anywhere in pos3's tree. Persona's `stop` CLI subcommand exists at `cli.py:112-122`; emitter at `stop_emitter.py:439-477` is correct. The merge code at `first_run_helper.py:340-387` (`_persona_stop_stanza` + `_maybe_merge_stop`) is correct. Three call sites at lines 1671, 2110, 2328 — all under first-run-only fences.

- **Surface 2 evidence:** UPS hook attachment in session jsonl at 2026-05-01T18:38:30Z carries `[memory-retrieval]\n    \n` — exactly what `context_composer._serialise_turn` emits when contributor text is `""`. Contributor runs (~1.2s, exit 0); the empty body comes from `_render_retrieval`'s `if not results: return ""` branch. Live MCP probe via the persona's own `LiveMCPMemoryClient`:

```
gid=['pos3']                       -> 0 results
gid=['pos-v2_default']             -> 0 results
gid=None                           -> 3 results
```

  Episodes in kuzu carry `group_id="pos-v2_default"` (per `memory-system/data/scope_registry.json:11-12` + `data/observability/spans.jsonl:41-44` `memory.ingest` spans). Persona reads with `group_ids=["pos3"]`. Read/write misalign.

### 2.2 Why the existing merge logic is idempotent (re-merge is safe)

`framework/hands-off-lifecycle/tests/test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py` exercises:

```python
merge_stop(settings_path=settings_path, new_entry=_persona_envelope(tmp_path))
result = merge_stop(settings_path=settings_path, new_entry=_persona_envelope(tmp_path))
assert result.wrote is True
assert result.backup_path is None  # no backup made — pos-v2-owned stanzas replace cleanly
assert result.prior_session_start_displaced is False
```

Re-running `merge_stop` over a pos-v2-owned settings.json is safe — replaces in place without backup, no displacement. So calling `_maybe_merge_stop` from `pos_session_start.py` on every session-start is structurally safe — first call writes the stanza, subsequent calls re-write the same shape (idempotent).

### 2.3 The `_maybe_install_status_line` precedent in pos_session_start.py

`framework/orchestrator/scripts/pos_session_start.py:263-297` already contains a `_maybe_install_status_line` helper that does exactly the same shape we need — existing-workspace retrofit on the supervisor path:

```python
def _maybe_install_status_line(loam_root: Path) -> None:
    """Existing-workspace retrofit for the top-level ``statusLine`` entry.
    Mirrors the ``_maybe_merge_status_line`` shape used by the worker
    side (``first_run_helper.py``) but lives on the supervisor path
    so workspaces already past first-run gain the entry without re-
    bootstrapping. ..."""
```

Called from `main()` at line 309. **The Stop-hook re-seat helper is structurally a sibling of this — same module, same call-from-main shape, same fail-soft contract.** Locked plan §6 D5 already names this surface ("supervisor's settings-touch path") for amendment #49; we're reusing the established pattern.

### 2.4 The empty-state output — what UPS hook attachment will look like post-fix

Pre-fix:
```
contributor_outputs:
  [memory-retrieval]
      
```

Post-Fix #2:
```
contributor_outputs:
  [memory-retrieval]
      (no results for this query)
```

Post-Fix #2 + #4: empty-state still shows `[memory-retrieval] / (no results for this query)`; the cosmetic Fix #4 only removes whitespace pollution for the (now-rare) case where a contributor returns `""` despite Fix #2.

Post-Fix #3 (boundary error path — separate from empty-state):
- Contributor still returns `""` (fail-closed per AC-D7.7); UPS hook attachment shows the same empty `[memory-retrieval]` block (because the rendering path doesn't fire — exception happens before `_render_retrieval`).
- BUT `<workspace>/.pos/memory-reads.log` now carries one NDJSON line: `{"timestamp": "...", "exception_type": "...", "exception_message": "...", "workspace_slug": "pos3", "query_preview": "..."}`. Operator inspecting the log can distinguish empty-state from boundary-error.

### 2.5 Sealed-test impact

Three components touched: primary-persona, hands-off-lifecycle, orchestrator. All three are sealed components.

- **Primary-persona** (`framework/primary-persona/tests/test_no_sealed_amendments.py`): seal-diff test admits `framework/primary-persona/`, `framework/hands-off-lifecycle/`, `framework/orchestrator/` already (allowed_prefixes lines 105-153). BASELINE advances to current HEAD `e3e3e17` (post-#94 §14 SHA backfill).
- **Hands-off-lifecycle**: no per-component seal-test exists at `framework/hands-off-lifecycle/tests/test_no_sealed_amendments.py`. Surface admitted via primary-persona's seal-test (which carries hands-off-lifecycle in allowed_prefixes) + universal_paths.prefixes admission for our manifest.
- **Orchestrator**: per-component seal-test exists at `framework/orchestrator/tests/test_no_sealed_amendments.py`. BASELINE advances; allowed_prefixes likely already admits cross-component touches (verify before seal).

Mirroring the M9 (substitution-pass) precedent: a multi-component amendment with primary-persona as the lead seal-test surface; the other two components admitted via cross-component allow-prefixes.

### 2.6 Test scope per dispatch + amendment #23 narrow-test-scope CDC

Per dispatch: "narrow to touched components + an integration test that empirically verifies (a) Stop hook fires write, (b) UPS hook retrieval surface is visible, (c) write-then-read round-trip works."

Touched components:
- `framework/primary-persona/tests/` — runs Fix #2 + #3 unit tests on memory_consumer + Fix #4 unit test on context_composer.
- `framework/hands-off-lifecycle/tests/` — no source edit here; existing `test_AC_M_11_*` tests still pass (structural shape unchanged).
- `framework/orchestrator/tests/` — runs new Fix #1 unit test on `pos_session_start.py::_maybe_reseat_stop_hook`.

Integration test: an in-process test that:
- (a) Constructs a fake `Stop` envelope, calls `cli_stop`, asserts `memory_write_queue.enqueue` fired (existing AC.M.* tests cover this — no new test needed).
- (b) Constructs a `ComposedContextPayload` with a memory-retrieval contributor wired to a FakeMemoryClient that returns 0 results, exercises `_serialise_turn`, asserts the rendered output contains `(no results for this query)` instead of trailing whitespace (Fix #2 unit test covers this).
- (c) Round-trip: write+read with same `group_id` via FakeMemoryClient — Fix #5 has no source surface; this is a documentation amendment + AC. Existing `test_D7_4_group_id_is_workspace_slug.py` covers the slug parity.

**An empirical end-to-end test using the live sidecar is OUT of in-process pytest scope** (sidecars are not deterministic enough; live MCP roundtrip times in the 100s of seconds for `add_episode` due to LLM extraction). Operational verification per §15 happens via raw HTTP curl + MCP tool calls during the build, recorded in §14 D-build.MPF.5.

---

## 3. Decisions (recommendations stated)

### D1 — Lift only `_maybe_merge_stop` vs all four `_maybe_merge_*` helpers

**Recommendation: lift only `_maybe_merge_stop`.** The dispatch authorises lifting siblings "if they share the same first-run-only constraint", but:

- Pos3 has UserPromptSubmit registered (per the settings.json read). UPS hook is firing (68× per session).
- pre-tool-use and status-line are not in dispatch scope — they're amendment #49 / structural-enforcement A2 surfaces. Their absence in pos3 is not the empirical bug.
- **Minimal-scope:** a cleaner Fix #1 lifts only Stop. The structural gap (any future hook added to first_run_helper.py won't reseat) is captured as HSF#3 for FIDRAFT.

**Rejected alternative:** lift all four into a `reseat_session_start_hooks(loam_root, settings_path)` umbrella surface. Defensible, but expands scope beyond the dispatch's empirical objective; the four other helpers are not currently broken in pos3.

### D2 — Where the Stop re-seat helper lives

**Recommendation: import `_maybe_merge_stop` from `first_run_helper` directly into `pos_session_start.py` and call it from `main()`.** Mirrors the `_maybe_install_status_line` pattern at lines 263-297 verbatim. No need to extract `_maybe_merge_stop` into a new module — it's already importable from `first_run_helper`. Concrete:

```python
def _maybe_reseat_stop_hook(loam_root: Path) -> None:
    """Existing-workspace retrofit for hooks.Stop.

    Mirrors ``_maybe_install_status_line`` shape (amendment #49 D5):
    workspaces past first-run gain hooks.Stop on next session-start
    without re-bootstrapping. Fail-soft per locked plan §5; any
    failure here must not block the supervisor's main path.

    The merge is idempotent over pos-v2-owned stanzas
    (test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py).
    """
    try:
        hooks_dir = loam_root / "framework" / "hands-off-lifecycle" / "hooks"
        if not hooks_dir.is_dir():
            return
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        from first_run_helper import _maybe_merge_stop  # type: ignore[import-not-found]

        settings_path = loam_root / ".claude" / "settings.json"
        _maybe_merge_stop(loam_root=loam_root, settings_path=settings_path)
    except Exception:  # noqa: BLE001 — fail-soft per locked plan §5
        return
```

Called from `main()` immediately after the existing `_maybe_install_status_line(loam_root)` call.

**Rejected alternative:** extract `_maybe_merge_stop` into a new `framework/hands-off-lifecycle/hooks/reseat.py` module. Cleaner long-term, but expands surface change beyond the dispatch's empirical objective; the existing private helper is fine to import from a sibling.

### D3 — Empty-state rendering string for Fix #2

**Recommendation: `"[memory-retrieval]\n  (no results for this query)"`** verbatim per dispatch text. Two-space indent matches the composer's `f"    {ln}"` four-space indent (which adds another four-space prefix when serialised). Final output:

```
[pos-v2 user-prompt-submit]
contributor_outputs:
  [memory-retrieval]
      (no results for this query)
```

(Inside `_render_retrieval`'s string the indent is two spaces; the composer adds another four, totalling six visible. Matches the "(no results for this query)" pattern's readability.)

### D4 — `memory-reads.log` shape for Fix #3

**Recommendation: NDJSON, one line per retrieval boundary error.** Mirror `memory-writes.log` shape (sibling diagnostic per dispatch). Schema:

```json
{"timestamp": "<ISO-8601>", "exception_type": "<class.name>", "exception_message": "<str>", "workspace_slug": "<slug>", "query_preview": "<first-80-chars>"}
```

Path: `<workspace>/.pos/memory-reads.log`. Append-only. Workspace `.pos/` directory is created by workspace-bootstrap; if missing, `_append_diag` swallows the OSError silently (fail-soft per AC-D7.7's outer envelope).

**Optional (FIDRAFT-tracked, NOT in scope):** also log successful reads with results_count + latency_ms (the diagnostic's gap #5 — read-side observability). In-scope for this amendment is exception-only logging; success-logging is an additive surface that doesn't unblock publish.

### D5 — Whether to drop `or [""]` fallback in context_composer

**Recommendation: drop it (Fix #4 in-scope).** The diagnostic noted the change is "cosmetic" but recommended the alternative — skip the contributor block entirely when text is empty (`if not text.strip(): continue`). After Fix #2, the empty-text path from memory-retrieval is gone; the only remaining empty-text path is a contributor that genuinely returns `""` — for which "skip the block" is preferable to "emit whitespace-padded header". Per the diagnostic's own analysis: "Fix #1 [#2 here] is preferable" because the empty case is now visible in the contributor's own output.

Concrete change at `context_composer.py:541-546`:

```python
# BEFORE
if contributor_outputs:
    lines.append("contributor_outputs:")
    for name, text in contributor_outputs:
        lines.append(f"  [{name}]")
        for ln in text.splitlines() or [""]:
            lines.append(f"    {ln}")
# AFTER
if contributor_outputs:
    rendered_any = False
    for name, text in contributor_outputs:
        if not text.strip():
            continue
        if not rendered_any:
            lines.append("contributor_outputs:")
            rendered_any = True
        lines.append(f"  [{name}]")
        for ln in text.splitlines():
            lines.append(f"    {ln}")
```

This shape skips empty contributors AND skips the `contributor_outputs:` header when no contributor produced text. Symmetric with the `if missing_paths:` and `if resolved_component:` guards.

### D6 — Fix #5 (group_id alignment) — does any source change land?

**Recommendation: no source change required for Fix #5.** Per dispatch + diagnostic re-analysis:

- The persona layer ALREADY writes with `group_id=workspace_slug` (per `memory_consumer.py:183`, `_compose_episode_body` + `add_episode(group_id=self.workspace_slug, ...)`).
- The persona layer ALREADY reads with `group_ids=[workspace_slug]` (per `memory_consumer.py:251`).
- Reads + writes are aligned at the persona surface.
- The orphan `pos-v2_default` data was written by a DIFFERENT path (memory-system's own ingest under `default_scope_id`), not by the persona — likely amendment #74 verification scaffolding. **Accepted as lost** per dispatch.

What lands as Fix #5: an explicit AC documenting the convention, an inline plan §13 D-Q decision lock that workspace-keyed writes match Idea 13's multi-workspace direction, and a regression-prevention pytest assertion on the persona's invariant (verifying `TurnAggregator.close_turn` invokes `add_episode(group_id=workspace_slug)` exactly).

**Rejected alternative:** edit `memory.yml:72` to make `default_scope_id` match `workspace_slug`. Rejected — `default_scope_id` is memory-system-internal mock-scope fallback (per the YAML comment "scope-of-work PRIMITIVE RUNTIME is not yet built"); changing it doesn't affect the persona path. The fix is at the consumer (persona) layer's invariant, not at memory-system's defaults.

### D7 — Sealed-component fence

**Recommendation: 3 components.**

1. `framework/primary-persona/` — receives Fix #2, #3, #4, AC tests, plus a regression-prevention test for Fix #5 (the persona's write-side group_id invariant).
2. `framework/orchestrator/` — receives Fix #1 (the new `_maybe_reseat_stop_hook` helper in `pos_session_start.py`, called from `main()`).
3. `framework/hands-off-lifecycle/` — no source edit; admitted via primary-persona's allowed_prefixes for the manifest's universal-path admission only.

BASELINE = current HEAD `e3e3e17` (post-amendment-#94 §14 SHA backfill). Sub-plan + manifest land first (BASELINE..feature commit narrows the seal-diff to this amendment).

**Primary-persona is the lead seal-test surface** because (a) it has the broadest allowed_prefixes (already admits hands-off + orchestrator + memory-system + many others — see `test_no_sealed_amendments.py:105-153`), (b) it's where the bulk of source change lands (3 of 5 fixes touch primary-persona). Orchestrator's seal-test runs as second pass (verifying its own surface admits the change).

### D8 — Test shape for Fix #1

**Recommendation: in-process unit test on `_maybe_reseat_stop_hook`.** Build a tmp_path workspace with a settings.json carrying SessionStart + UserPromptSubmit only (matching pos3's pre-fix shape). Set up a fake `loam_root` path with a fake `framework/hands-off-lifecycle/hooks/` directory that exposes a stub `_maybe_merge_stop`. Call `_maybe_reseat_stop_hook(loam_root)`. Assert:
- The stub was called once with the expected args.
- Settings.json post-call contains `hooks.Stop` with the persona envelope shape (when called against a real `_maybe_merge_stop`).
- Idempotent re-call: second call leaves settings.json unchanged.

Mirrors `test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py` shape. Lands at `framework/orchestrator/tests/test_AC_MPF_1_reseat_stop_hook.py`.

### D9 — Test shape for Fix #2

**Recommendation: in-process unit test on `_render_retrieval`.** Call with `result={"results": []}`, assert return value is `"[memory-retrieval]\n  (no results for this query)"`. Call with `result={"query": "x", "results": [{"fact": "test fact"}]}`, assert return value contains `[memory-retrieval]` + `- test fact`. Lands at `framework/primary-persona/tests/test_AC_MPF_2_render_retrieval_empty_state_visible.py`.

### D10 — Test shape for Fix #3

**Recommendation: in-process unit test on `build_memory_retrieval_contributor` exception path.** Build a `FakeMemoryClient` that raises `ConnectionError` on `search`. Build a contributor pointing to a tmp_path workspace with `.pos/` already created. Call the contributor with a prompt. Assert:
- Returned text is `""` (fail-closed contract preserved).
- `<workspace>/.pos/memory-reads.log` exists and contains one NDJSON line with `exception_type="ConnectionError"`, `workspace_slug="<tmp slug>"`.

Lands at `framework/primary-persona/tests/test_AC_MPF_3_memory_reads_log_on_exception.py`.

### D11 — Test shape for Fix #4

**Recommendation: in-process unit test on `_serialise_turn`.** Two cases:
- (a) `contributor_outputs=[("memory-retrieval", "")]`: assert returned text does NOT contain `[memory-retrieval]` (empty contributor skipped) AND does NOT contain `contributor_outputs:` (header skipped when no contributor produced text).
- (b) `contributor_outputs=[("a", "alpha"), ("b", ""), ("c", "gamma")]`: assert returned text contains `[a]\n    alpha`, does NOT contain `[b]`, contains `[c]\n    gamma`.

Lands at `framework/primary-persona/tests/test_AC_MPF_4_serialise_turn_skips_empty_contributors.py`.

### D12 — Test shape for Fix #5

**Recommendation: regression-prevention pytest on `TurnAggregator.close_turn`.** Build a `FakeMemoryClient` that records `add_episode` calls. Build a `TurnAggregator(memory_client=fake, workspace_slug="test-slug")`. Call `close_turn(...)`. Assert exactly one `add_episode` invocation; assert its `group_id` arg is `"test-slug"` (matches the workspace_slug, not any other value). Lands at `framework/primary-persona/tests/test_AC_MPF_5_turn_aggregator_writes_with_workspace_slug.py`.

---

## 4. Acceptance criteria

AC family **AC.MPF.\*** (memory-pipeline-fix). Each AC ladders to D7 (memory-consumer wiring per primary-persona spec) → D1 (memory-system v1.0 spec) → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.MPF.1 | Stop hook is re-seated on every session-start. `pos_session_start.py::main()` calls `_maybe_reseat_stop_hook(loam_root)` after `_maybe_install_status_line(loam_root)`. The helper is fail-soft (any exception caught, returns silently). | `framework/orchestrator/tests/test_AC_MPF_1_reseat_stop_hook.py` — exercises the helper against a tmp_path workspace; asserts hooks.Stop appears post-call; asserts idempotent re-call. |
| AC.MPF.2 | Retrieval contributor's empty-results path emits a visible diagnostic string. `_render_retrieval(result)` returns `"[memory-retrieval]\n  (no results for this query)"` when `results` is empty (was: `""`). | `framework/primary-persona/tests/test_AC_MPF_2_render_retrieval_empty_state_visible.py` — unit test on `_render_retrieval`; covers empty + non-empty cases. |
| AC.MPF.3 | Retrieval contributor's exception path appends one NDJSON line to `<workspace>/.pos/memory-reads.log` recording exception type + slug + query preview. The contributor still returns `""` (fail-closed contract preserved). | `framework/primary-persona/tests/test_AC_MPF_3_memory_reads_log_on_exception.py` — exercises the FakeMemoryClient-raises-ConnectionError path; asserts log file exists + contains expected fields. |
| AC.MPF.4 | `_serialise_turn` skips contributors whose text is empty (no header for that contributor; no whitespace-padded line). When NO contributor produced text, the `contributor_outputs:` header itself is omitted. | `framework/primary-persona/tests/test_AC_MPF_4_serialise_turn_skips_empty_contributors.py` — unit test on `_serialise_turn`; covers all-empty + mixed cases. |
| AC.MPF.5 | `TurnAggregator.close_turn` invokes `add_episode` with `group_id=workspace_slug` exactly. Convention documented in module docstring + plan §3 D6 ruling. | `framework/primary-persona/tests/test_AC_MPF_5_turn_aggregator_writes_with_workspace_slug.py` — regression-prevention test; asserts `group_id` arg is `workspace_slug`. |
| AC.MPF.6 | Operational verification (post-amendment, against running pos3 sidecar): a manual round-trip via raw HTTP curl produces a successful `add_episode` write under `group_id=pos3`, followed by a successful `search` returning that episode. | Manual curl sequence during build's verification step. Recorded in §14 D-build.MPF.6. |
| AC.MPF.S | `git diff --name-only BASELINE..SEAL_COMMIT` produces only paths under `framework/primary-persona/`, `framework/orchestrator/`, `framework/hands-off-lifecycle/`, or universal-paths. | `framework/primary-persona/tests/test_no_sealed_amendments.py::test_D8_S_only_primary_persona_surfaces_changed` passes against new BASELINE `e3e3e17`. `framework/orchestrator/tests/test_no_sealed_amendments.py` passes. |

---

## 5. Sealed-component fence

**Components touched (3):**

1. **`framework/primary-persona/`** — receives:
   - `src/loam/primary_persona/memory_consumer.py:305-307` edit (Fix #2): `return ""` → `return "[memory-retrieval]\n  (no results for this query)"`.
   - `src/loam/primary_persona/memory_consumer.py:243-264` extension (Fix #3): wrap `try/except` to call new `_append_diag` helper before `return ""`. New `_append_diag(workspace_root, exception, query)` function; new module-level constant `MEMORY_READS_LOG_NAME = "memory-reads.log"` for symmetry with write side.
   - `src/loam/primary_persona/context_composer.py:541-546` edit (Fix #4): replace `for ln in text.splitlines() or [""]` with `if not text.strip(): continue` + skip empty-only header.
   - `src/loam/primary_persona/memory_consumer.py` docstring edit (Fix #5): explicit "Conv: writes use `group_id=workspace_slug`; reads use `group_ids=[workspace_slug]`. The two paths agree by construction. Verification-write paths that bypass the persona may write under different group_ids (e.g. memory-system's `default_scope_id`); those are not retrievable via the persona's read path."
   - 4 new AC tests under `tests/test_AC_MPF_*.py` (AC.MPF.2..MPF.5).

2. **`framework/orchestrator/`** — receives:
   - `scripts/pos_session_start.py` extension: new `_maybe_reseat_stop_hook(loam_root)` helper (mirrors `_maybe_install_status_line` shape verbatim). Called from `main()` after `_maybe_install_status_line(loam_root)`.
   - 1 new AC test under `tests/test_AC_MPF_1_reseat_stop_hook.py` (AC.MPF.1).

3. **`framework/hands-off-lifecycle/`** — NO source edit. The existing `_maybe_merge_stop` in `first_run_helper.py:366-387` is imported AS-IS by the new orchestrator-side helper. The component is "touched" only in that primary-persona's seal-diff allow-prefix lists already admit it; manifest's universal_paths.prefixes covers `docs/rebuild/plans/` for our sub-plan.

**Universal admissions** (per amendment #22 ruling #3):
- `docs/rebuild/plans/` — for this sub-plan + manifest.

**Lead seal-test:** `framework/primary-persona/tests/test_no_sealed_amendments.py` (broadest allowed_prefixes).
**Cross-component seal-test verifications:** `framework/orchestrator/tests/test_no_sealed_amendments.py` (verify allowed_prefixes admits the change; if not, expand it AS PART OF this amendment's source surface — same in-band ODD §4 expansion as M1c-corrective).

**HC#4 byte-content invariant:** edits land in source + test files; none are HC#4 sample paths in any seal-fence config (verified at `framework/primary-persona/tests/test_no_sealed_amendments.py` — no HC#4 sample list maintained; same for orchestrator). NO RETIRE-AND-REBASELINE.

---

## 6. Halt triggers

- HT-1: FastMCP `group_ids` filter is empirically broken when re-tested at build time (§15 verification). **Halt action:** complete Fixes #1, #2, #3, #4, #5 as scoped; surface FastMCP-filter-broken as a separate amendment for next-task in dispatcher queue. Document the gap in §14 D-build.MPF.6 and append to FUTURE_IDEAS_DRAFT.md per FIDRAFT discipline.
- HT-2: The Stop hook re-seating surface needs more refactoring than dispatch implies (e.g. `_maybe_merge_*` siblings have circular dependencies with first-run-specific state). **Halt action:** stop and surface; consider lifting all four into a `reseat_session_start_hooks` umbrella vs minimal-Stop-only fix.
- HT-3: Plug-in side hook paths require updates that interact with task #20's recently-sealed partition realignment. **Halt action:** stop and surface; the partition realignment moved hook-source classifications, and a re-classification mismatch could break the synthesis path.
- HT-4: Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band — escalate.
- HT-5: ODD §2.5 violations encountered in surrounding source while editing — capture for FIDRAFT, do not expand scope.
- HT-6: Wall-clock approaches 90 min — surface for continuation rather than stalling.
- HT-7: The pos3 settings.json edit is needed to operationally unblock pos3 BEFORE next session-start. **Action (per dispatch trigger #7):** the structural fix (Fix #1) handles all post-fix workspaces; for pos3 specifically, the operator simply starts a new Claude session in pos3 (which fires `pos_session_start.py`, which now re-seats Stop). No direct settings.json edit by this amendment. Document in §14 D-build.MPF.6 that pos3 picks up the fix on next session-start.
- HT-8: Cross-component seal-test (orchestrator) does NOT admit primary-persona/ in its allowed_prefixes — expand the allow-list AS PART OF this amendment in primary-persona's seal-test scope (in-band ODD §4 expansion; record in §14 D-build.MPF.S).

---

## 7. Ship shape (commit ladder)

1. **Sub-plan + manifest commit.** This file + `memory-pipeline-fix.manifest.yaml`. Message: `docs(plans): memory-pipeline-fix sub-plan + manifest`.
2. **Feature commit.** All five fix shapes + new tests + any in-band sealed-test allow-list expansion in one commit (the surfaces are coherent — they share the diagnostic's root-cause-cluster). Message: `feat: memory-pipeline-fix — Stop reseat + retrieval visibility + group_id convention`.
3. **Apply commit.** `loam amend apply --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/memory-pipeline-fix.manifest.yaml` — runs against the plugin-side `loam-amend` package. Updates objective-tracker (no objectives declared; no-op) + applies any apply-step renames (none expected). Message auto-generated: `chore(loam-amend-apply): loam amend apply for memory-pipeline-fix`.
4. **Seal commit.** `loam amend seal --plan-doc <abs-path> <abs-manifest>` runs against plugin-side binary. Records SHA in §14 register; seal-test passes against BASELINE `e3e3e17`. Message auto-generated: `chore(seals): memory-pipeline-fix — primary-persona+orchestrator at <feat-sha>`.
5. **§14 SHA backfill commit.** `docs(plans): record memory-pipeline-fix commit SHAs in §14 method-decision register`. Per recent amendments' pattern.

No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`. Corrective commits if tests fail post-feature: NEW commits, never amend.

---

## 8. Out of scope (per dispatch + named here)

- FastMCP `group_ids` filter brokenness (HSF#1 — surface as separate amendment if reproducible at build-time).
- Lifting `_maybe_merge_user_prompt_submit` / `_maybe_merge_status_line` / `_maybe_merge_pre_tool_use` into the session-start re-seating surface (HSF#3 — only `_maybe_merge_stop` is empirically broken in pos3; the structural gap is FIDRAFT-tracked).
- Read-side success logging in `memory-reads.log` (only exception logging in this amendment; success logging is FIDRAFT-tracked per the diagnostic's gap #5).
- Direct edit of pos3's `.claude/settings.json` to land hooks.Stop synchronously (HT-7 — operator triggers re-seat by starting a new session; structural fix is sufficient).
- Refactoring `retention.py`'s name to `schema_migrations.py` (memory-sidecar-recovery's HSF#2 — out-of-scope rename).
- `KuzuDriver.close()` unmap verification (memory-sidecar-recovery's FIDRAFT).
- Per-session lifespan model (memory-sidecar-recovery's FIDRAFT).
- M6c's graceful-fallthrough-with-detection CDC retroactive operationalisation across the rest of memory-system (memory-sidecar-recovery's FIDRAFT — this amendment operationalises ONLY the persona's read-side paths).
- launchd label `com.pos-v2.*` → `com.loam.*` rename for pos3's installed plist (M1c-corrective — pos3 picks up via re-bootstrap or its own scheduled rename; not part of memory-pipeline-fix).

---

## 9. Backwards-compat verification

- **Fix #1.** `_maybe_reseat_stop_hook` is fail-soft. On any exception (missing hooks_dir, ImportError, settings.json unwriteable), returns silently. Workspaces that had Stop already registered (pos-v2-owned-stanza re-merge) are no-op writes per AC.M.11 idempotency. Workspaces that had user-authored Stop stanzas are NOT touched per `merge_stop`'s prior-stanza-displacement logic (`prior_session_start_displaced` would be False for pos-v2-owned, True with backup for user-authored — handled by `merge_stop`, not by us).
- **Fix #2.** `_render_retrieval`'s contract is "return text payload for the contributor". Returning `"[memory-retrieval]\n  (no results for this query)"` instead of `""` is a STRICTER contract (more visible) — no caller depends on the empty-string sentinel because the only caller is the composer's `_serialise_turn`, which iterates over `text.splitlines()` regardless. Fix #4 then skips the now-non-empty contributor in `_serialise_turn` — but only if text is empty after strip. `(no results for this query)` survives `.strip()` non-empty, so Fix #2's output renders. No regression.
- **Fix #3.** `_append_diag` is fail-soft (any OSError on log file open swallows silently). The contributor's existing fail-closed contract (return `""` on any exception) is unchanged. The new log file is additive; no existing caller reads `memory-reads.log`.
- **Fix #4.** `_serialise_turn`'s contract is "produce text emitted as UserPromptSubmit additionalContext". Skipping empty contributors REDUCES output bytes, never increases them. No caller depends on the trailing-whitespace artefact. Existing tests on `_serialise_turn` (if any) should be re-run; if any depend on empty-contributor-still-renders-header behaviour, that's a sealed-test in-band retire (record in §14 D-build.MPF.S).
- **Fix #5.** No source change. The persona's existing write/read invariants are codified by the new AC.MPF.5 test; existing behaviour is preserved.
- **HC#4 byte-content invariant:** NO RETIRE-AND-REBASELINE.

---

## 10. AI-time prediction

Per `feedback_duration_estimation_rubric` calibration table:

- **Predicted (calibrated):** 30-60 min — three-component amendment, five narrow source edits + four new test files + plan + manifest + seal cycle. Comparable to amendment #94 (post-M6 partition realignment; ~50 min actual) but slightly tighter scope. Memory-sidecar-recovery (#92) was 15-30 min for a single-component, two-edit amendment; this is 1.5-2× more surface.
- **Plan rubric (uncalibrated 1-min-per-tool-call):** 60-120 min.
- **Actual:** populated post-build in §14 D-build.MPF.0.

Calibration row appended to `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md` post-build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.MPF.0 — AI-time actuals

(Populated post-build.)

### D-build.MPF.1 — Fix #1 implementation actuals

(Populated post-build: did the `_maybe_install_status_line` mirror suffice, or did the import-from-first_run_helper require additional sys.path or lazy-import handling?)

### D-build.MPF.2 — Fix #2 implementation actuals

(Populated post-build: empty-state string verbatim per dispatch; any deviation rationale.)

### D-build.MPF.3 — Fix #3 implementation actuals

(Populated post-build: log file path + NDJSON shape; how `.pos/` directory creation is handled when missing.)

### D-build.MPF.4 — Fix #4 implementation actuals

(Populated post-build: did dropping `or [""]` break any sealed test? If yes, in-band retire path.)

### D-build.MPF.5 — Fix #5 implementation actuals

(Populated post-build: regression-prevention test + docstring update. Does any existing test already cover this invariant?)

### D-build.MPF.6 — Operational verification + FastMCP filter re-test

(Populated post-build: raw HTTP curl sequence + outcomes. FastMCP `group_ids` filter re-test result — broken / working / inconclusive. If broken, FIDRAFT entry appended.)

### D-build.MPF.S — Sealed-test allow-list expansion (if needed)

(Populated post-build: did any sealed-test's allowed_prefixes need expansion in-band? Document the expansion + rationale.)

### Commit SHAs

- Amendment commit: `7e7f958b6274cc48c5813479d04346fe00a573c4` —
  `fix(primary-persona): test_AC_DSA_8 HOOKS_DIR follow post-M6 partition realignment`
- Seal commit: `67968b7e8b09b470bb5af72946fa4fee9c294fa1` —
  `chore(seals): memory-pipeline-fix — primary-persona+orchestrator at 7e7f958`
## 15. Post-build verification checklist

- [ ] `pytest framework/primary-persona/tests/` passes (touched-component scope; new AC.MPF.2..MPF.5 tests).
- [ ] `pytest framework/orchestrator/tests/` passes (touched-component scope; new AC.MPF.1 test).
- [ ] `pytest framework/hands-off-lifecycle/tests/test_AC_M_11_*` passes (existing tests; no regression).
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` returns clean (zero missing admissions, zero skipped reasons).
- [ ] `loam amend seal --plan-doc <abs-path> <abs-manifest>` produces seal commit; seal-test passes; sidecars + narrative advance.
- [ ] `loam amend apply --plan-doc <abs-path> --dry-run` rerun POST-seal returns clean.
- [ ] **Operational verification (manual, against pos3 sidecar at 127.0.0.1:8765):**
  - [ ] Raw HTTP curl: `add_episode` with body `"test-episode-mpf"` under `group_id="pos3"` returns success.
  - [ ] Raw HTTP curl: `search` with `query="test-episode-mpf"` and `group_ids=["pos3"]` returns the just-written episode.
  - [ ] Raw HTTP curl: `search` with `query="test-episode-mpf"` and `group_ids=None` returns the just-written episode (sanity check that filter is consistent).
  - [ ] If `group_ids=["pos3"]` returns 0 but `group_ids=None` returns the episode, FastMCP filter is broken — surface as separate amendment per HT-1.
- [ ] FUTURE_IDEAS_DRAFT.md appended with FIDRAFT entries from any HT-5 surface findings (HSF#1 — FastMCP filter; HSF#3 — partial-lift of `_maybe_merge_*`; HSF#5 — read-side success logging).
- [ ] `feedback_duration_estimation_rubric.md` calibration row appended.

---

## 16. Halt-and-surface findings encountered during plan authoring

- **HSF#1 (deferred to build-time HT-1).** FastMCP `group_ids` filter behaviour is suspect per the diagnostic's empirical probe. Re-test during build via raw HTTP curl. If broken, complete the 5 fixes as scoped and surface a separate FastMCP-investigation amendment.

- **HSF#2 (informational, NOT in scope).** `default_scope_id` in `memory.yml:72` is a memory-system-internal mock-scope fallback (per the YAML comment "scope-of-work PRIMITIVE RUNTIME is not yet built"); changing it doesn't affect the persona path. The fix for write/read alignment is at the persona layer's invariant (already in place); no `memory.yml` edit needed.

- **HSF#3 (informational, FIDRAFT-tracked).** Lifting only `_maybe_merge_stop` (per D1) leaves the other three `_maybe_merge_*` helpers in first-run-only fences. The structural gap (any future hook added to `first_run_helper.py` won't reseat) is FIDRAFT-tracked. Resolution shape: a `reseat_session_start_hooks(loam_root, settings_path)` umbrella that calls all four (or N going forward); fired from `pos_session_start.py::main()` after `_maybe_install_status_line` + the new `_maybe_reseat_stop_hook`. Out of scope this amendment per minimal-fix discipline.

- **HSF#4 (informational, FIDRAFT-tracked).** The persona's `add_episode` write path uses `group_id=workspace_slug`, but other paths to the same kuzu (e.g. memory-system internal ingest, verification harnesses) use `default_scope_id`. There's no shared "workspace-shared group_id" both paths agree on; per-source isolation is the current convention. If a future agent / harness wants to write data the persona can later retrieve, the convention needs locking down — which group_id is the "shared workspace" group? Out of scope this amendment; the diagnostic's gap #4 captures it cleanly.

- **HSF#5 (informational, FIDRAFT-tracked).** Read-side observability (`memory-reads.log` for SUCCESS reads — query, slug, results_count, latency_ms) is the diagnostic's gap #5. In-scope this amendment is exception-only logging; success logging is additive surface that doesn't unblock publish. FIDRAFT-tracked.

Plan is authorised to proceed.

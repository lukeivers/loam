# Amendment #46 — primary-persona session-start + turn-start emitters, contributor wiring, starter-pending body completion (builder plan)

**Status:** authoring 2026-04-25.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `19108ea`.
**Authoritative scope:** `docs/rebuild/plans/memory-into-context-integration.md` §4a — AC46.1 through AC46.S.
**Halt-trigger research outcome:** none of the six halt triggers fired. Surface confirmations recorded in §6.

This is the per-amendment builder plan: it records files-changed, ACs-satisfied (cited by AC46.x ID), validation strategy, halt-trigger checks, and the §2.5 reverse-direction trace. Method (file paths, exact symbol names, validator shapes, AC test names) lives here per scope-only-dispatch CDC.

---

## 1. Objective

Land the primary-persona session-start + turn-start runtime — composer construction, contributor registration, two CLI subcommands, two new hands-off-lifecycle hook entries, and the starter-pending body widening — so every Claude Code session in a pos-v2 workspace receives:

1. The persona's session-level structured payload (corpus refs, in-flight amendments, service state, cost headroom, gate sentinel, tracker context, starter-pending instructions when applicable) as `SessionStart` `additionalContext`.
2. Per-turn memory retrieval based on the user's prompt as `UserPromptSubmit` `additionalContext`.

After this amendment lands, the substrate built across #32 (D8 composer), #33 (D7 memory consumer), #35 (onboarding contributor), #40 (tracker context contributor), and #45 (`extra_inner_hooks` registry) becomes load-bearing — the runtime caller exists.

---

## 2. ACs satisfied

| AC | Behaviour | Test name(s) |
|----|-----------|--------------|
| AC46.1 | SessionStart CLI emits structured `additionalContext` (corpus paths, amendments_in_flight, service state, cost headroom, sentinel, first-run completion, generation marker, tracker context output, starter-pending block when starter), within 10k cap | `test_AC46_1_session_start_cli_emits_structured_payload`, `test_AC46_1_payload_within_10k_cap`, `test_AC46_1_starter_pending_block_present_when_starter` |
| AC46.2 | UserPromptSubmit CLI consumes Claude Code's stdin JSON (`prompt` field), emits memory-retrieval contributor output; empty-graceful when memory down/empty | `test_AC46_2_user_prompt_submit_cli_emits_retrieval`, `test_AC46_2_empty_graceful_when_memory_down`, `test_AC46_2_reads_prompt_from_stdin_json` |
| AC46.3 | Missing-baseline-corpus produces structured diagnostic + sentinel `partial`/`missing`; both CLIs exit 0 | `test_AC46_3_missing_corpus_diagnostic_and_sentinel`, `test_AC46_3_clis_exit_zero_on_missing_corpus` |
| AC46.4 | Composer-construction-failure: empty payload OR single diagnostic line, exit 0, no traceback | `test_AC46_4_clis_fail_soft_on_composer_construction_failure` |
| AC46.5 | `build_first_run_stanza` + `build_supervisor_stanza` accept new persona-session-start inner hook via `extra_inner_hooks`; new `merge_user_prompt_submit` writes UserPromptSubmit hook entry | `test_AC46_5_first_run_stanza_carries_persona_session_start_hook`, `test_AC46_5_supervisor_stanza_carries_persona_session_start_hook`, `test_AC46_5_settings_json_carries_user_prompt_submit_hook` |
| AC46.6 | Backwards-compat: `extra_inner_hooks=None` produces identical envelopes; existing #32/#33/#37/#45 suites stay green; UserPromptSubmit is single-contributor (future generalisation deferred) | `test_AC46_6_backwards_compat_extra_inner_hooks_none`, `test_AC46_6_user_prompt_submit_single_contributor` |
| AC46.7 | Starter-pending body: first line is `STARTER_PENDING_MARKER`, body lists each `OnboardingQuestion` id+prompt + write-back instruction lines (mentions `persist_elicitation_transcript`, contract path, invocation pattern); fits in ≤2,000 chars; non-starter returns `""` | `test_AC46_7_starter_body_contains_question_ids_and_prompts`, `test_AC46_7_starter_body_contains_writeback_instructions`, `test_AC46_7_starter_body_within_2000_char_budget`, `test_AC46_7_non_starter_returns_empty` |
| AC46.8 | End-to-end interview path: starter contract → SessionStart CLI → parse questions → synthetic transcript → `persist_elicitation_transcript` → `is_starter` flips False, answers on contract | `test_AC46_8_end_to_end_starter_interview_path` |
| AC46.9 | ODD §2.5 reverse direction (every code path/branch/dep/test traces to AC46.x) — audit performed pre-seal | builder audit (no new test) |
| AC46.S | Seal-diff confined to `primary-persona/`, `hands-off-lifecycle/`, `docs/rebuild/plans/` | existing `primary-persona/tests/test_no_sealed_amendments.py` + `hands-off-lifecycle/tests/test_cross_cutting.py` H19 |

---

## 3. Files changed

### `primary-persona/src/`

1. **`session_start_emitter.py`** (NEW) — owns the SessionStart + UserPromptSubmit emit functions and inner-hook builders.
   - `build_session_composer(workspace_root)` → constructs `ComposedContextPayload(session_builder=compose_session_fields)`, registers `tracker-context` (via `register_tracker_context`), `starter-pending` (via `build_starter_pending_contributor` after loading the primary persona), `memory-retrieval` (via `register_memory_retrieval` with a real or stub MemoryClient — see §3.1.3 for client choice).
   - `emit_session_start_context(workspace_root)` → calls `build_session_composer(...)` + `composer.on_session_start(workspace_root)`; returns `payload.additional_context_text` on success; returns empty string on any failure path (AC46.4 fail-soft).
   - `emit_user_prompt_submit_context(workspace_root, prompt)` → constructs the composer, runs `on_session_start` to seed the session payload (required by composer's structural refusal), then `composer.on_user_prompt_submit(prompt=prompt)` and returns `payload.additional_context_text`. Fail-soft per AC46.4.
   - `build_persona_session_start_inner_hook(pos_v2_root)` → returns the inner-hook dict (matcher pattern, command pointing at `<venv>/bin/python -m primary_persona.cli session-start`, async False, timeout 5).
   - `build_persona_user_prompt_submit_inner_hook(pos_v2_root)` → same shape, command points at `... session-start`-equivalent: `<venv>/bin/python -m primary_persona.cli user-prompt-submit`, timeout 5.
   - `cli_session_start(workspace_root)` → reads stdin (Claude Code passes a JSON envelope to SessionStart too, but we ignore it), invokes `emit_session_start_context`, prints to stdout, returns 0 unconditionally (AC46.4).
   - `cli_user_prompt_submit(workspace_root)` → reads JSON from stdin, parses `prompt` field, invokes `emit_user_prompt_submit_context`, prints to stdout, returns 0 (AC46.4).

2. **`cli.py`** (NEW) — `argparse`-based entry point matching loam-mode's pattern. Subparsers: `session-start`, `user-prompt-submit`. Each routes to the corresponding `cli_*` function in `session_start_emitter.py`. `main(argv)` returns int; the `if __name__ == "__main__"` guard exits with `main()`.

3. **`onboarding.py`** (MODIFY) — widen `build_starter_pending_contributor`'s body per AC46.7. Preserves AC35.3 marker prefix + AC.A.4 question-count text. Adds:
   - One block per `OnboardingQuestion`: `f"  - id={q.id!s} required={q.required} prompt={q.prompt}"`.
   - Write-back instruction block referencing `persist_elicitation_transcript`, the contract path (passed in via the contributor's context dict OR available via the loaded persona's `directory` attribute), and a one-line synthetic invocation example.
   - Length check: if the constructed body would exceed 2,000 chars, the question prompts get truncated (with each question's id retained) — defensive cap. Halt-trigger 5 verified empirically (§6).

4. **`__init__.py`** (MODIFY) — add public re-exports of the new emitter / CLI surface so `from primary_persona import emit_session_start_context, emit_user_prompt_submit_context, cli_session_start, cli_user_prompt_submit` works (mirrors loam-mode pattern). The `cli` module is exposed as `primary_persona.cli` via the top-level package.

5. **`pyproject.toml`** (MODIFY) — no changes needed; `setuptools` already maps `primary_persona = src` so `primary_persona.cli` works as a runnable module.

### `primary-persona/tests/`

6. **One test file per AC**, mirroring the #41 one-file-per-AC convention:
   - `test_AC46_1_session_start_cli_emits_structured_payload.py`
   - `test_AC46_2_user_prompt_submit_cli_emits_retrieval.py`
   - `test_AC46_3_missing_corpus_diagnostic_and_sentinel.py`
   - `test_AC46_4_clis_fail_soft_on_composer_failure.py`
   - `test_AC46_6_backwards_compat_extra_inner_hooks_none.py` (covers existing-suite-stays-green via assertion that the helper functions still produce identical envelopes for `extra_inner_hooks=None`)
   - `test_AC46_7_starter_pending_body_widening.py`
   - `test_AC46_8_end_to_end_starter_interview_path.py`
   
   AC46.5 + AC46.9 + AC46.S are tested in hands-off-lifecycle (AC46.5) and via existing seal tests (AC46.S) plus builder audit (AC46.9).

### `hands-off-lifecycle/hooks/`

7. **`first_run_settings.py`** (MODIFY) — add new public function `merge_user_prompt_submit(*, settings_path, new_entry, now_iso=None)`. It mirrors `merge_session_start`'s shape but operates on `hooks.UserPromptSubmit`. Single-entry list (no multi-contributor generalisation; AC46.6 defers that). The function:
   - Loads existing settings.json.
   - Writes `hooks["UserPromptSubmit"] = [new_entry]` — overwrites any prior pos-v2-owned entry; user-authored UserPromptSubmit entries are backed up via the same pattern as `merge_session_start` (`_is_pos_v2_owned`-equivalent predicate scoped to UserPromptSubmit's expected commands).
   - Atomic write via `.tmp` + rename (matches existing convention).
   
   New helper `_is_pos_v2_owned_user_prompt_submit(stanza_entries)` recognises the persona's `user-prompt-submit` command marker (`primary_persona.cli user-prompt-submit` and `-m primary_persona`).

   Also: extend `_POS_V2_COMMAND_MARKERS` (or analogue) to include `primary_persona.cli session-start` so `_is_pos_v2_owned` recognises the new SessionStart inner hook on re-merge (mirrors how amendment #45 added `loam_mode.cli session-start` markers).

8. **`first_run_helper.py`** (MODIFY) — at the same call sites that currently call `_loam_mode_inner_hooks(pos_v2_root)`, add `_persona_inner_hooks(pos_v2_root)` and concatenate so the SessionStart envelope's inner-hook list is `[first_run_or_supervisor, persona, loam_mode]` (probe → persona → loam-mode, per umbrella plan D5).
   
   New helper `_persona_inner_hooks(pos_v2_root)` mirrors `_loam_mode_inner_hooks` shape: lazy import of `primary_persona.session_start_emitter.build_persona_session_start_inner_hook`, fail-soft return of `[]` on ImportError or any exception. The combined helper:
   ```python
   def _persona_inner_hooks(pos_v2_root: Path) -> list[dict]: ...
   def _extra_session_start_hooks(pos_v2_root: Path) -> list[dict]:
       return _persona_inner_hooks(pos_v2_root) + _loam_mode_inner_hooks(pos_v2_root)
   ```
   
   Three call sites to update: Phase 3d (~line 1518), Phase 4c re-merge (~line 1707), Phase 6 self-retire (~line 1101) all change from `extra_inner_hooks=_loam_mode_inner_hooks(pos_v2_root)` to `extra_inner_hooks=_extra_session_start_hooks(pos_v2_root)`.
   
   Also: at each of those three call sites, add a sibling `merge_user_prompt_submit(settings_path=..., new_entry=_persona_user_prompt_submit_stanza(pos_v2_root))` invocation. New helper `_persona_user_prompt_submit_stanza(pos_v2_root)` returns the full envelope `{"matcher": "", "hooks": [build_persona_user_prompt_submit_inner_hook(pos_v2_root)]}`. Lazy-imported with fail-soft; if the import fails, the merge is skipped (degrades to no UserPromptSubmit hook — pre-amendment behaviour).

### `hands-off-lifecycle/tests/`

9. **`test_AC46_5_first_run_stanza_carries_persona_session_start_hook.py`** — assert `_extra_session_start_hooks` (or whatever name; test imports + calls the helper) returns a list whose order is persona-first then loam-mode-second, AND that `build_first_run_stanza(pos_v2_root, extra_inner_hooks=...)` carries the persona inner-hook in the second position (after first-run.sh).

10. **`test_AC46_5_supervisor_stanza_carries_persona_session_start_hook.py`** — same for `build_supervisor_stanza`.

11. **`test_AC46_5_settings_json_carries_user_prompt_submit_hook.py`** — assert `merge_user_prompt_submit(...)` writes a `hooks.UserPromptSubmit` array containing the persona's user-prompt-submit envelope; user-authored other-keys preserved.

### `docs/rebuild/plans/`

12. **`amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`** (this file).
13. **`amendment-46-persona-session-start-turn-start-emitters.manifest.yaml`** (NEW) — pos-amend manifest.
14. **`memory-into-context-integration.md`** (untracked → committed by the amendment as the umbrella plan).

### `.scratch/claude-output/` (NOT committed)

Intermediate verification artefacts only. None should appear in the seal diff.

---

## 3.1 Method-level decisions (D-build.x)

### D-build.1 — Composer's public callable for "rendered text from workspace_root"

**Halt-trigger 1 check:** `ComposedContextPayload.on_session_start(workspace_root: Path) -> SessionPayload` and the resulting `payload.additional_context_text: str` IS the documented rendered-text surface. Confirmed by `context_composer.py` lines 348–380 + 205–212. **Halt trigger 1 does NOT fire.** The emitter calls `payload.additional_context_text` directly — no wrapper needed.

### D-build.2 — `extra_inner_hooks` parameter shape

**Halt-trigger 2 check:** `build_first_run_stanza` and `build_supervisor_stanza` accept `extra_inner_hooks: list[dict[str, Any]] | None = None` per `first_run_settings.py` lines 140–215. Confirmed list-typed; `None` and `[]` both produce single-inner-hook envelope. **Halt trigger 2 does NOT fire.**

### D-build.3 — UserPromptSubmit hook input contract

**Halt-trigger 3 check:** Claude Code's UserPromptSubmit hook passes a JSON envelope on **stdin**. Shape:
```json
{"session_id": "...", "transcript_path": "...", "cwd": "...", "permission_mode": "...", "hook_event_name": "UserPromptSubmit", "prompt": "<user text>"}
```
Confirmed via `https://code.claude.com/docs/en/hooks` (research time <30 min). The CLI reads `sys.stdin.read()`, parses as JSON, extracts the `prompt` key. **Halt trigger 3 does NOT fire.**

Output: any non-JSON text on stdout becomes `additionalContext`. Same convention as SessionStart per the docs. The emitter prints plain text.

### D-build.4 — Memory client construction in production CLI path

The emitter needs a `MemoryClient` for `register_memory_retrieval`. Production: a real MCP HTTP client against the per-workspace memory-graphiti port. Test: `_helpers_d7.FakeMemoryClient` already exists.

For the CLI's production path, the UserPromptSubmit emitter needs to construct a real client. Options:
- (a) Import a real client from somewhere — out of scope for #46 (no MCP client lives in the persona layer today; #47 is what wires `.mcp.json` so MCP tools become callable).
- (b) Construct a minimal HTTP client inline in the emitter that calls memory-graphiti's `/search` endpoint directly (bypasses MCP, talks straight to the FastMCP/streamable-HTTP service).
- (c) Skip the memory contributor on the production path until #47 lands; register a no-op stub.

**Decision: (c).** AC46.2 says "when the memory service is up and contains episodes, the output includes retrieved episode text; when memory is down or empty, the output is the empty string (graceful, not error)." The graceful-empty path is the dominant production state pre-#47. A no-op stub satisfies this; tests inject `FakeMemoryClient` to exercise the populated path. This keeps #46 strictly framework-wiring; the live memory client lands in #47 (which writes `.mcp.json`).

The emitter's production client factory: `_default_memory_client(workspace_root)` returns either:
- A live `MemoryClient` if the workspace exposes one (deferred to #47 — for now, returns `None`).
- `None` when no client is available — `register_memory_retrieval` is skipped, the contributor is not registered, the turn payload simply omits the retrieval block (graceful empty).

Tests inject the fake client via a `memory_client_factory` parameter on `build_session_composer`.

### D-build.5 — Loaded-persona resolution for the starter-pending contributor

The starter-pending contributor takes a `loaded_persona` argument. The CLI must construct one. Path: `PersonaLoader(workspace_root).primary()`. Failure modes:
- No `personas/` directory → `PersonaDirectoryNotFoundError`. Fail-soft: skip starter-pending registration.
- Multiple primaries / no primary → `PersonaValidationError`. Fail-soft: skip.

When the loader fails, no starter-pending contributor is registered (graceful empty per AC46.4).

### D-build.6 — Inner-hook ordering (umbrella plan D5)

Per umbrella plan §6 D5: probe (existing first-run.sh / pos_session_start.py) → **persona emit (NEW)** → loam-mode emit (#45). Implementation: `_extra_session_start_hooks` returns `_persona_inner_hooks() + _loam_mode_inner_hooks()`. Each helper is independent + fail-soft. The `extra_inner_hooks` parameter compose those after the base (first-run shim or supervisor) so the final order is: base → persona → loam-mode.

### D-build.7 — Inner-hook timeout

Both new inner hooks use `timeout: 5` seconds, matching loam-mode's #45 precedent. The session-start work is bounded (services probed for ~250ms each per `_probe_memory` / `_probe_orchestrator`; corpus discovery is filesystem reads; tracker query is a single SQLite read; persona load is two filesystem reads). UserPromptSubmit's memory retrieval is bounded by the soft cap (5 results, 1600 char cap) — single HTTP call to local memory-graphiti, sub-second when service is up.

### D-build.8 — Test mode for the CLI

The CLI tests use `subprocess.run` with the workspace `.venv/bin/python -m primary_persona.cli session-start --workspace <tmp_path>` invocation pattern (matching loam-mode tests). Stdin for the user-prompt-submit subcommand is fed via `subprocess.run(input=json.dumps({"prompt": "..."}))`.

For unit-level coverage of the emit functions (without subprocess overhead), tests call `emit_session_start_context(workspace_root)` and `emit_user_prompt_submit_context(workspace_root, prompt)` directly.

---

## 4. Validation strategy

1. **Plan + manifest authored before any code edit** (this file + the manifest).
2. **`pos-amend apply --dry-run` smoke test** against the empty-diff manifest (should fail until baseline + components are correct).
3. Author source edits in order: (a) `onboarding.py` body widening, (b) `session_start_emitter.py`, (c) `cli.py`, (d) `__init__.py` re-exports, (e) `first_run_settings.py` `merge_user_prompt_submit` + marker extension, (f) `first_run_helper.py` `_persona_inner_hooks` + UserPromptSubmit invocations.
4. Author tests in matching order; run them as each lands (`/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/pytest primary-persona/tests/test_AC46_*.py -q`).
5. Run touched-component full suites (`primary-persona/tests/`, `hands-off-lifecycle/tests/`).
6. Run `pos-amend apply --dry-run` against the manifest — expect exit 0 (clean).
7. Run `pos-amend apply` — applies tuple/sidecar edits.
8. Stage + commit (amendment commit). Subject: `feat(primary-persona): wire session-start + user-prompt-submit emitters + starter-pending body`.
9. Run `pos-amend seal --plan-doc <abs-path>` to advance sidecars + run sweep + create seal commit.
10. Verify: amendment SHA + seal SHA both present in repo HEAD log.

Per amendment-dispatch CDC: skip pre-seal full-suite rerun (sidecar-only edits). Touched components only run their suites. All other sealed components run only their `test_no_sealed_amendments.py` (sweep step 5 of `pos-amend seal`).

---

## 5. ODD §2.5 reverse-direction trace (AC46.9)

Forward direction confirmed by §2 table. Reverse trace (every code path → AC):

- `session_start_emitter.build_session_composer` → AC46.1 (composer construction is the precondition for emit), AC46.2 (same composer composes both entry points), AC46.4 (composer-construction-failure path).
- `session_start_emitter.emit_session_start_context` → AC46.1, AC46.3 (forwards corpus-gate-state diagnostic), AC46.4.
- `session_start_emitter.emit_user_prompt_submit_context` → AC46.2.
- `session_start_emitter.cli_session_start` → AC46.1 (production entry point), AC46.4 (exit-0 contract).
- `session_start_emitter.cli_user_prompt_submit` → AC46.2, AC46.4.
- `session_start_emitter.build_persona_session_start_inner_hook` → AC46.5 (the SessionStart hook entry hands-off-lifecycle composes against).
- `session_start_emitter.build_persona_user_prompt_submit_inner_hook` → AC46.5 (UserPromptSubmit hook entry).
- `cli.py` argparse subparsers → AC46.1 + AC46.2.
- `cli.py` main → AC46.1 + AC46.2 + AC46.4 (exit-0 contract).
- `onboarding.py` body widening — question loop → AC46.7 (question text + prompts in body), AC46.8 (parsing surface for E2E).
- `onboarding.py` write-back instruction lines → AC46.7 (instruction block), AC46.8 (path closure).
- `onboarding.py` size cap branch → AC46.7 ≤2,000 char budget.
- `__init__.py` new exports → AC46.1 + AC46.2 (public surface for the CLI / external invocation).
- `first_run_settings.merge_user_prompt_submit` → AC46.5.
- `first_run_settings._POS_V2_COMMAND_MARKERS` extension → AC46.6 (pos-v2-owned-stanza re-merge recognition).
- `first_run_helper._persona_inner_hooks` → AC46.5.
- `first_run_helper._extra_session_start_hooks` aggregation → AC46.5 + D-build.6 (ordering).
- `first_run_helper._persona_user_prompt_submit_stanza` → AC46.5.
- `first_run_helper.merge_user_prompt_submit` invocations at three call sites → AC46.5.
- Each test file in §3 → its named AC.

No code path lacks an AC anchor. No defensive `if` without backing AC. Pre-seal audit will re-walk the diff and confirm.

---

## 6. Halt-trigger verification (per umbrella plan §11 + dispatch §6)

| Halt trigger | Status | Evidence |
|--------------|--------|----------|
| 1. Composer's public API | DOES NOT FIRE | `ComposedContextPayload.on_session_start` returns `SessionPayload.additional_context_text`; `context_composer.py` lines 348–380. |
| 2. `extra_inner_hooks` is list-accepting | DOES NOT FIRE | `first_run_settings.py` lines 140–215; type is `list[dict[str, Any]] | None`. |
| 3. UserPromptSubmit input channel | DOES NOT FIRE | Claude Code docs confirm stdin JSON with `prompt` field; researched in <5 min. |
| 4. Persona contract unloadable in test fixture | DOES NOT FIRE | `tests/conftest.py` exposes `workspace_with_primary` fixture + `write_persona_dir`; `PersonaLoader(workspace, enforce_no_personas_in_core=False).primary()` works in tests. |
| 5. Starter-pending body widening exceeds 2,000 chars | TBD AT BUILD-TIME | Estimated body size: 4 questions × ~150 chars/question + ~200 chars instructions = ~800 chars. Well under cap. Verified empirically in `test_AC46_7_starter_body_within_2000_char_budget`. |
| 6. Sealed-component outside fence appears in diff | DOES NOT FIRE | Diff is confined to `primary-persona/` + `hands-off-lifecycle/` + `docs/rebuild/plans/`. Verified via `pos-amend apply --dry-run`. |

§2.5 violations in surrounding code: spot-checked `context_composer.py`, `session_start_gate.py`, `onboarding.py`, `tracker_context.py`, `memory_consumer.py`, `first_run_settings.py`. All branches map to known ACs (AC-D8.x, AC-D7.x, AC35.x, AC.A.x, AC40.x, AC.45.x). **No §2.5 violations to surface.**

---

## 7. Out-of-scope (named explicitly)

Per umbrella plan §4c:

- **Persona content authoring** (Q1 deferred). `personas/primary/contract.yaml` + `prompt.md` remain EXAMPLE template scaffolds. Untracked in canonical tree at the time of this amendment.
- **`.mcp.json` writer** — that's amendment #47.
- **Live memory MCP client wiring** — pre-#47, the emitter uses no-op memory client (D-build.4); the contributor is not registered; turn payload simply omits the retrieval block.
- **Multi-contributor UserPromptSubmit registry** — single-contributor for now (AC46.6); future generalisation is a separate amendment.
- **Starter-pending body extension to dynamic instruction generation** — instructions are static text in this amendment; future personalisation is out of scope.

If any surfaces as a hard prereq, halt-and-surface (umbrella plan §11).

---

## 8. Commit-SHAs (to be backfilled by `pos-amend seal --plan-doc`)

```
Amendment commit:  <pending>
Seal commit:       <pending>
```

Per pos-amend-seal-automation-extension's §14 backfill convention.

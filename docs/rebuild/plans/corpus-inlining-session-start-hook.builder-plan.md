# Corpus-inlining SessionStart hook — Builder plan

**Status:** authored 2026-04-28 (build-time, post-dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Plan-doc (governs):** `docs/rebuild/plans/corpus-inlining-session-start-hook.md`.
**Research artefact:** `docs/rebuild/plans/research/corpus-inlining-session-start-hook-research.md`.
**Manifest:** `docs/rebuild/plans/corpus-inlining-session-start-hook.manifest.yaml`.
**Amendment number:** 73.

This builder plan records the D-build choices the build agent picked per the plan-doc's "method per ODD §7.4 — builder's call" clauses.

---

## 1. D-build register

### D-build.1 — Always-load tier (consumes owner D-CI.1 = lean)

**Choice:** the always-load tier is a static set of three workspace-relative paths embedded in the hook source:

```
{"CLAUDE.md", "docs/rebuild/VALUE_PROPOSITION.md", "docs/rebuild/STATE.md"}
```

**On-demand tier:** a static set of three workspace-relative paths embedded as path-pointer references:

```
{"docs/odd-methodology.md", "docs/odd-in-pos.md", "docs/rebuild/FUTURE_IDEAS.md"}
```

**Rationale:** D-CI.1.(a) lean. Methodology docs surface as path-pointers per D-CI.2.(a) / D-build.5 (no section-anchor extraction in this hook). The static set is intentional — A1's `compute_corpus_paths_required` returns the manifest's full `always_loaded` set including non-corpus globs (component source globs `cost-governance/**` etc.), which are not corpus-shaped. Filtering by file extension is one approach; a static lean tier is simpler, smaller diff, and matches the plan §6 D-build.1 ruling on the lean-tier reading. The plan §7 out-of-scope explicitly admits "manifest tightening" as a future amendment — until then, the lean tier is named in code, not derived from the manifest.

### D-build.2 — Path-resolver helper (D-CI.4.(b) duplicate)

**Choice:** duplicate `_resolve_corpus_path` as a 6-line module-private function `_resolve_corpus_path` inside `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py`. Same fall-through semantics as `framework/primary-persona/src/session_start_gate.py::_resolve_corpus_path`: probe `<workspace>/<rel>`, fall through to `<workspace>/framework/<rel>`, return workspace-root path when neither exists (caller's existence check surfaces absence).

**Rationale:** D-CI.4.(b). Matches A1's `WORKSPACE_STATE_SUBDIR` precedent. Tests verify fall-through against both shapes (workspace-root + framework subdir).

### D-build.3 — Per-file size ceiling

**Choice:** `_PER_FILE_CEILING = 50_000` chars per file. Truncation marker format:

```
[truncated at 50000 chars; full file at <workspace-relative-path>]
```

**Rationale:** D-CI.7 / plan §6 D-build.3. Largest current always-load file (VALUE_PROPOSITION.md at 11.5k chars) is well under the ceiling. The marker is byte-grep-able for AC.CI.6 verification.

### D-build.4 — Hook ordering in SessionStart fan-out (D-CI.6 / D-build.4)

**Choice:** reorder `_extra_session_start_hooks` so the relative composition becomes:

```
probe (base) → corpus-load (A1) → corpus-inline (NEW) → persona → loam-mode
```

A1 fires FIRST; corpus-inline fires SECOND (reads + emits content; updates A1's sentinel `corpus_paths_loaded`); persona fires THIRD (its dossier reads A1's sentinel post-inline, so a future micro-amendment can grow a `corpus_inlined: true` marker without re-ordering); loam-mode keeps its position.

**Rationale:** D-build.4 names the relative order A1 → corpus-inline → persona. Existing AC46.5 stanza-builder tests do NOT pin the order out of `_extra_session_start_hooks` — they pass extras directly to the builder. Re-ordering `_extra_session_start_hooks` is internal composition, AC46.5 unaffected.

### D-build.5 — A1 sentinel surface extension (D-build.6 → option A)

**Choice:** extend `write_corpus_load_sentinel` with an optional keyword-only `corpus_paths_loaded: list[str] | tuple[str, ...] | None = None` argument. When None, the existing behaviour is byte-identical (sentinel written with `corpus_paths_loaded: []` per A1's contract). When provided, the loaded list is serialised into the sentinel JSON.

**Rationale:** A1's signature already has `*` keyword-only args (`session_id`, `mode`); adding a third keyword-only is additive; existing call sites pass only `session_id` (and optionally `mode`). The new corpus-inline hook calls `write_corpus_load_sentinel(workspace_root, session_id=..., mode=..., corpus_paths_loaded=[...])` to overwrite A1's prior empty-list sentinel with the inlined paths. This satisfies AC.CI.4 (D-CI.5.(a) update A1's sentinel).

The `state` field semantics shift slightly: previously `state` was derived from path-existence at write time; with `corpus_paths_loaded`, when the caller passes a list, `state` is recomputed from `corpus_paths_loaded` membership against `corpus_paths_required`:
- `loaded` — every required path is in `corpus_paths_loaded`.
- `partial` — at least one but not all required paths.
- `missing` — none of the required paths present in `corpus_paths_loaded` (or `corpus_paths_required` is empty).

When the caller does NOT pass `corpus_paths_loaded`, the state is computed via `_classify_corpus_state` from path-existence, exactly as before (A1 backwards-compat).

### D-build.6 — Hook stdout format

**Choice:** the hook writes raw text to stdout, mirroring loam-mode + persona emitter precedent. Claude Code captures stdout into `additionalContext` automatically. No `hookSpecificOutput` JSON envelope authored by this hook (per the established convention — loam-mode + persona use raw stdout).

Format (per AC.CI.1 / AC.CI.2):

```
=== pos-v2 always-loaded corpus (DEV MODE) ===

--- CLAUDE.md ---
<content>

--- docs/rebuild/VALUE_PROPOSITION.md ---
<content>

--- docs/rebuild/STATE.md ---
<content>

=== pos-v2 on-demand corpus (read via Read tool when relevant) ===
- docs/odd-methodology.md
- docs/odd-in-pos.md
- docs/rebuild/FUTURE_IDEAS.md
```

Missing always-load files:
```
--- docs/rebuild/STATE.md ---
[missing] file not found at workspace-root or framework subdir
```

Truncated files:
```
--- docs/rebuild/STATE.md ---
<first 50000 chars>
[truncated at 50000 chars; full file at docs/rebuild/STATE.md]
```

Missing on-demand files: omitted from the pointer block (AC.CI.2 contract).

### D-build.7 — Caching across sessions (D-CI.3.(a) re-emit)

**Choice:** none. Re-emit every session. No cache file.

### D-build.8 — Mode-partition (D-CI.8.(DEV-MODE-only))

**Choice:** the hook reads workspace_mode via `corpus_load_sentinel.workspace_mode(workspace_root)`. NORMAL USE → exit 0 with empty stdout, no sentinel update. DEV MODE → emit + sentinel update.

---

## 2. Files touched

### New files

- `framework/hands-off-lifecycle/hooks/corpus_inline_session_start.py` — the SessionStart inner hook script.
- `framework/hands-off-lifecycle/tests/test_AC_CI_1_always_load_content_emitted.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_2_on_demand_pointer_block.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_3_normal_use_no_op.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_4_sentinel_corpus_paths_loaded.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_5_path_resolver_fall_through.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_6_per_file_ceiling_truncation.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_7_envelope_and_fail_soft.py`
- `framework/hands-off-lifecycle/tests/test_AC_CI_S_seal_diff_window.py`
- `framework/hands-off-lifecycle/seals/SEAL_COMMIT.corpus-inlining-session-start-hook` — sealed sidecar advanced by `pos-amend seal`.
- `docs/rebuild/plans/corpus-inlining-session-start-hook.builder-plan.md` (this file)
- `docs/rebuild/plans/corpus-inlining-session-start-hook.manifest.yaml`

### Edited files

- `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` — add optional `corpus_paths_loaded` parameter to `write_corpus_load_sentinel`. Backwards-compat (default None preserves existing behaviour).
- `framework/hands-off-lifecycle/hooks/first_run_settings.py` — add `corpus_inline_session_start.py` substring to `_POS_V2_COMMAND_MARKERS`.
- `framework/hands-off-lifecycle/hooks/first_run_helper.py` — add `_corpus_inline_inner_hooks` builder; reorder `_extra_session_start_hooks` to `corpus-load → corpus-inline → persona → loam-mode`.

---

## 3. AC-to-test mapping

| AC | Test file | What it verifies |
|---|---|---|
| AC.CI.1 | `test_AC_CI_1_always_load_content_emitted.py` | DEV MODE stdout contains content from every always-load file; missing files emit `[missing]` marker |
| AC.CI.2 | `test_AC_CI_2_on_demand_pointer_block.py` | DEV MODE stdout contains a pointer block listing on-demand workspace-relative paths; missing on-demand files are omitted (no `[missing]` marker) |
| AC.CI.3 | `test_AC_CI_3_normal_use_no_op.py` | NORMAL USE workspace fires hook, exits 0, empty stdout, no sentinel update |
| AC.CI.4 | `test_AC_CI_4_sentinel_corpus_paths_loaded.py` | A1 sentinel's `corpus_paths_loaded` populated post-fire; state field reflects loaded subset; `write_corpus_load_sentinel` accepts the new param additively |
| AC.CI.5 | `test_AC_CI_5_path_resolver_fall_through.py` | Path resolver probes workspace-root then framework-subdir (matches #67 contract); both shapes verified |
| AC.CI.6 | `test_AC_CI_6_per_file_ceiling_truncation.py` | A 50_000-char ceiling caps per-file content; truncation marker emitted; other files in same fire are unaffected |
| AC.CI.7 | `test_AC_CI_7_envelope_and_fail_soft.py` | Hook completes <5s; exits 0 on every error path (malformed envelope, missing manifest, unreadable file, sentinel write failure) |
| AC.CI.S | `test_AC_CI_S_seal_diff_window.py` | Seal-diff window confined to `hands-off-lifecycle/{hooks,tests,seals}/` + universal-paths admissions |

Total new tests: 8 files (AC.CI.1–7 + AC.CI.S). Existing 388 hands-off-lifecycle tests stay GREEN per regression contract.

---

## 4. Reverse-direction §2.5 audit

Every code path / branch / dependency / test in the diff traces back to a named AC:

- `corpus_inline_session_start.py::main` — reads SessionStart envelope → AC.CI.7 (envelope + fail-soft on every error path).
- `_resolve_corpus_path` helper → AC.CI.5.
- `_ALWAYS_LOAD` static set → AC.CI.1.
- `_ON_DEMAND` static set → AC.CI.2.
- `_PER_FILE_CEILING = 50_000` constant + truncate-marker emission → AC.CI.6.
- workspace-mode short-circuit → AC.CI.3 + plan §6 D-build.8 (DEV-MODE-only).
- `write_corpus_load_sentinel(..., corpus_paths_loaded=...)` call → AC.CI.4.
- `corpus_load_sentinel.write_corpus_load_sentinel` extension (new optional kwarg) → AC.CI.4.
- `first_run_helper._corpus_inline_inner_hooks` → AC.CI.7 (composes hook into envelope) + plan §6 D-build.4 (ordering).
- `first_run_settings._POS_V2_COMMAND_MARKERS` extension → re-merge does not displace pos-v2-owned hook (plan §5 constraint 9 + AC.45.x marker discipline).
- `first_run_helper._extra_session_start_hooks` reorder → AC.CI.4 + D-build.4 ordering contract.
- 8 test files → 8 ACs (1:1 mapping above).

No silent branches. No defensive `if`s without backing AC. The fail-soft `try/except` blocks are AC.CI.7's named contract.

---

## 5. Halt-trigger checks (build-time)

1. **Pre-flight staleness** — `git log --grep=...` returns only `76cec04`. Cleared.
2. **A1 substrate gap** — A1's `write_corpus_load_sentinel` signature accepts an additional keyword-only param without breaking existing call sites (existing call sites pass `session_id` + optional `mode` only; new param defaults to None). Verified: extension is additive.
3. **A1 manifest read API** — `compute_corpus_paths_required` is read-only consumer; this hook does NOT call it (uses static lean tier per D-build.1). No surface change required.
4. **#67 path-resolver semantics drift** — duplicated helper is byte-equivalent to `framework/primary-persona/src/session_start_gate.py::_resolve_corpus_path`. AC.CI.5 fixtures verify both implementations produce identical results.
5. **ODD §2.5 violation in surrounding code** — none surfaced; existing hooks are §2.5-clean.
6. **SessionStart envelope budget** — disk reads of 3 small files (~27k chars) on local SSD: <5ms. Hook timeout: 5s; envelope is well within budget.
7. **AC method-prescription** — every AC is outcome-shaped; method (file paths, exact stdout shape, ceiling literal, marker format) lives in this builder plan, not in the AC text.
8. **Token-budget breach** — measured: 4778 + 11479 + 10948 = 27,205 chars ≈ 6800 tokens. Within plan §6 D-CI.1 expected ~6.8k. No breach.

---

## 6. pos-amend bookkeeping flow (per dispatch + feedback_dispatch_explicit_pos_amend_apply)

1. Author manifest at `docs/rebuild/plans/corpus-inlining-session-start-hook.manifest.yaml` with BASELINE = `b8caf7f` (pre-amendment HEAD).
2. Author all source edits + tests + sidecar; commit as the amendment commit on branch `pos-v2`.
3. `pos-amend apply --dry-run <manifest>` — must exit 0.
4. `pos-amend apply <manifest>` — advances BASELINE literals + writes SEAL_COMMIT sidecars.
5. `pos-amend seal --plan-doc <builder-plan> <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
6. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.

---

## 14. Method-decision register (post-build)

| ID | Decision | Choice | Rationale |
|---|---|---|---|
| D-build.1 | Always-load tier source | Static set of 3 paths in hook source | Avoids manifest-tightening dependency; matches D-CI.1.(a) lean ruling |
| D-build.2 | Path-resolver helper | Duplicate inside hook module | D-CI.4.(b); matches A1's `WORKSPACE_STATE_SUBDIR` precedent |
| D-build.3 | Per-file ceiling | 50_000 chars; marker = `[truncated at <N> chars; full file at <path>]` | D-CI.7; surfaces truncate path if a corpus file ever grows that large |
| D-build.4 | Hook ordering | corpus-load → corpus-inline → persona → loam-mode | D-build.4 / D-CI.6.(a); persona dossier sees post-inline sentinel |
| D-build.5 | A1 sentinel extension | New optional keyword arg `corpus_paths_loaded` on `write_corpus_load_sentinel` | Smaller diff than sibling function; backwards-compat by default-None |
| D-build.6 | Hook stdout format | Raw text with `=== ... ===` section headers + `--- <path> ---` per-file delimiters | Matches loam-mode + persona raw-stdout precedent; no `hookSpecificOutput` JSON envelope |
| D-build.7 | Caching | None — re-emit every session | D-CI.3.(a); sessions are isolated context windows |
| D-build.8 | Mode-partition | DEV MODE only via `corpus_load_sentinel.workspace_mode` | D-CI.8; consumer-only on A1 |

### Commit SHAs

- Amendment commit: `d0a65390d4309614d65080d4a56877ba71c5b90f` —
  `docs(plans): normalize corpus-inlining plan §14 heading for pos-amend backfill`
- Seal commit: `b9c1d202f79ca9e6e477bf84a67ca507148dacb7` —
  `chore(seals): corpus-inlining SessionStart hook (DEV-MODE-only inline of always-load corpus + on-demand path-pointers; A1 sentinel corpus_paths_loaded populated) — hands-off-lifecycle at d0a6539`

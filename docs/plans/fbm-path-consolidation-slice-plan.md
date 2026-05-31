# FBM Path Consolidation — slice plan

**Branch:** `slice/p1.2-loam-layout`
**Status:** Phase 0 PLAN — PROCEED (no design fork; blast radius == "repoint the live hook's memory contributor + retire one redundant ungated surfacing").
**Date:** 2026-05-31

---

## 1. Problem (verified Tier-0 this session)

loam's primary persona surfaces memory into the UserPromptSubmit prompt via
TWO parallel code paths that produce two different blocks:

1. **Ungated `file_memory` path (path 1)** — `register_file_memory_retrieval`
   (`file_memory.py:1711`) → `build_file_memory_retrieval_contributor`
   (`file_memory.py:1640`) → `FileMemoryStore.search()` →
   `memory_consumer._render_retrieval` → a `[memory-retrieval]` contributor
   block listing past-conversation EPISODES. **NO salience gate.** This is the
   source of the task-notification junk Luke sees.

2. **Gated `keep_pace` path (path 2)** — `keep_pace.retrieval.retrieve()`
   (`retrieval.py:290`) → `_episode_hits` (carries `_salience`, computed live
   from the episode body) + corpus `index.search` → `_merge_by_score`
   (rank-normalize + rule-weight/hard-floor + **salience gate**) →
   `_render_injection` → a `[keep-pace]` block surfacing corpus/rules AND
   episodes, junk-gated. Sealed on this branch (7e9af6b, 81c7780, fb26be2,
   c82131e).

The just-built quartet (rank-normalize / rule-weight+floor / salience gate)
lives in path 2. **The live junk surfaces via path 1.**

### Live-hook reality (Tier-0)

- `/Users/lukeivers/pos3/.claude/settings.json` UserPromptSubmit registers
  exactly ONE loam memory hook: `python -m loam.primary_persona.cli
  user-prompt-submit`. **The keep_pace hook
  (`hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py`) is NOT wired
  live in pos3.** So the gated path 2, though sealed, never runs in the live
  session — only ungated path 1 does.
- That CLI subcommand → `cli_user_prompt_submit` (`session_start_emitter.py:474`)
  → `emit_user_prompt_submit_context` (`:331`) → `build_session_composer` (`:109`)
  → in the **production client-None branch** (`:190–216`) registers the ungated
  `register_file_memory_retrieval` contributor under name `memory-retrieval` at
  `TriggerKind.turn` → `composer.on_user_prompt_submit` runs it →
  `_serialise_turn` emits the `[memory-retrieval]` block.

---

## 2. Consumer inventory (the EXAMINE step)

### Path-1 (`build_file_memory_retrieval_contributor` / `register_file_memory_retrieval` / `_render_retrieval`)

| Consumer | Kind | Disposition |
|---|---|---|
| `session_start_emitter.py:207` — the production client-None branch | **LIVE PRODUCTION** | **REPOINT** to the gated contributor. The ONE site that surfaces ungated episodes live. |
| `session_start_emitter.py:182` — `register_memory_retrieval` (MCP client branch) | test/future-graphiti only (production factory returns None) | UNCHANGED — different function (`memory_consumer.register_memory_retrieval`), not the file-based one. |
| `__init__.py:99/101/176/194` — re-exports | public API | UNCHANGED — functions stay defined + exported; only the registration call site changes. |
| `test_AC_FBMT2_PLBLA_1`, `test_AC_FBMT2_S`, `test_AC_MFBM_2` | tests of the file-based contributor | UNCHANGED — they call `build_file_memory_retrieval_contributor` directly; the function is preserved. |
| `test_AC_MPF_2`, `test_AC_FGF_3`, `test_AC_FGF_4` | tests of `_render_retrieval` | UNCHANGED — `_render_retrieval` is preserved (still used by the MCP branch + the file contributor). |
| `hands-off-lifecycle/tests/test_d1_byte_content_match.py` | comment reference only | UNCHANGED. |

### Path-2 (`keep_pace.retrieval` / `retrieve` / `_merge_by_score` / `build_keep_pace_contributor`)

| Consumer | Kind | Disposition |
|---|---|---|
| `hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py:92` — `build_keep_pace_contributor()` | a hook NOT wired live in pos3 | UNCHANGED — keep the keep_pace chain hook intact; we do not touch it. |
| `test_AC_FBMU_*`, `test_AC_FBM_W_*`, `test_AC_FBM_SAL_*`, `test_AC_KP1_*` | tests of `retrieve`/`_merge_by_score` | UNCHANGED — production `retrieve()` signature is preserved. |

**Conclusion:** the ONLY live-context site that surfaces ungated episodes is
`session_start_emitter.py:207`. Repointing it is the entire consolidation. No
consumer needs `register_file_memory_retrieval` deleted; nothing else can't be
cleanly repointed. **No fork → PROCEED.**

---

## 3. Consolidation design

### Canonical path
The GATED keep_pace `retrieve()` is the canonical target — it already carries
the quartet (rank-normalize + rule-weight/hard-floor + salience gate) and
already merges corpus/rules + episodes under one top-N + byte budget. CONFIRMED
viable: its `prompt`-driven entry-point and `RetrievalConfig` accept everything
the composer can supply.

### Mechanism — a new gated contributor builder in `keep_pace.retrieval`
Add `register_keep_pace_turn_contributor(composer, *, workspace_root, workspace_slug)`
(name TBD by builder; one new function) that:
1. Resolves a `RetrievalConfig` explicitly from `workspace_root` (NOT from an
   envelope `workspace.project_dir`, which the composer does not supply): sets
   `memory_dir` (corpus), `objectives_home`/`claude_homes` (`~/.claude`), and
   `episode_memory_dir` via `memory_dir_for_workspace(workspace_root)` so the
   gated path reads the SAME live episode store path-1 reads.
2. Registers a `fn(context) -> str` at `TriggerKind.turn` under name
   **`memory-retrieval`** (KEEP the same contributor name so no downstream
   consumer keying on the block name changes) that calls
   `retrieve(prompt=context["prompt"], config=cfg)` and **coerces the result to
   a string** (`retrieve` already returns `""` on no-match; the adapter guards
   `None` → `""` so `_serialise_turn`'s `text.strip()` never sees a non-str).
3. Fail-soft: any error → empty string (matches AC46.2 graceful-empty +
   AC.MFBM.2 fail-closed contract the old contributor honored).

This keeps the rewire inside the keep_pace component (where the quartet lives)
plus a 3-line repoint in `session_start_emitter.py`. `register_file_memory_retrieval`
+ `build_file_memory_retrieval_contributor` + `_render_retrieval` stay defined
and exported (tests + MCP branch use them) — minimal-blast-radius retirement is
"stop registering the ungated one in the live branch," not "delete it."

### Repoint
In `build_session_composer`, the production client-None branch
(`session_start_emitter.py:190–216`) swaps the
`register_file_memory_retrieval(...)` call for
`register_keep_pace_turn_contributor(composer, workspace_root=…, workspace_slug=…)`.
The active-thread block (`:228–257`, TriggerKind.session) is untouched.

### Unified output shape the user sees after consolidation
ONE turn-level contributor named `memory-retrieval` whose body is the
`[keep-pace]` gated block: "On-file context relevant to what you're working
on:" + top-N pointers drawn from BOTH the rules/corpus AND the episode store,
salience-gated (task-notification / empty-channel / bare-ack episodes dropped),
rule-weighted with the hard-floor pin honored, under the keep_pace top-N(≤5) +
`INJECTION_CHAR_CAP` budget. The ungated `[memory-retrieval]`-style raw episode
dump is no longer emitted in the live context.

(Note: the contributor *name* stays `memory-retrieval`; the *block heading text*
inside is keep_pace's `[keep-pace] On-file context…`. Both are non-load-bearing
for any AC per `context_composer._serialise_turn`'s docstring — ACs check
structural membership, not textual equality.)

---

## 4. Migration

Pure rewire — no schema/shape change to the episode store, the corpus index, or
any on-disk artefact. Migration file is a **no-op marker** documenting the
rewire (consistent with the seal ladder); the corpus index is rebuilt at Phase 2
activation as a hygiene step, not because the shape changed.

---

## 5. AC ladder

- **AC-FBM-CON-1** (rewire wiring) — `build_session_composer` in the production
  (client-None) branch registers the keep_pace-backed gated contributor under
  name `memory-retrieval` at `TriggerKind.turn`, and does NOT register the
  ungated `register_file_memory_retrieval`. Verified by inspecting the composer's
  registered turn contributors.
- **AC-FBM-CON-2** (string-coercion safety) — the gated contributor returns a
  `str` (never `None`) so `_serialise_turn`'s `text.strip()` is safe; a no-match
  prompt yields `""` and the turn renders no contributor block.
- **AC-FBM-CON-3** (no-regression: real memory surfaces) — through the composer,
  a query matching a real corpus rule + a real episode surfaces the gated block
  with both.
- **★ AC-FBM-CON-S (OUTCOME-ALTITUDE — the bar)** — invokes the REAL production
  entry-point `cli_user_prompt_submit` (the function the live
  `python -m loam.primary_persona.cli user-prompt-submit` hook calls), feeding a
  representative UserPromptSubmit JSON envelope on stdin (monkeypatched) against
  a TEMP workspace seeded with a COPY of real-shape episodes (a real
  `<task-notification>` junk turn + a real `<channel>`-wrapped substantive turn)
  + a weighted/pinned corpus rule, with NO pre-arranged retrieval state, and
  asserts on the RENDERED stdout block:
  - (a) the task-notification junk episode does NOT appear;
  - (b) a real memory (the `<channel>` substantive episode OR the corpus rule)
        DOES appear;
  - (c) a weighted/pinned rule surfaces correctly (hard-floor honored);
  - (d) no exception; exit 0.
  This AC is `outcome-altitude:true` and invokes the true CLI entry-point, NOT
  an inner module — the load-bearing lesson from the failed rounds.

Every line of the rewire maps to one of these ACs (ODD §2.5). No non-objective
code.

---

## 6. Build + seal (Phase 1)

- Implement §3 on `slice/p1.2-loam-layout`. New code: one builder in
  `keep_pace/retrieval.py`; a 3-line repoint in `session_start_emitter.py`.
- New tests: `test_AC_FBM_CON_1`…`_3` + `test_AC_FBM_CON_S` (the outcome-altitude
  CLI-hook test).
- Full primary-persona suite green + seal-fence (`test_no_sealed_amendments`)
  green + the new outcome-altitude AC green.
- Migration no-op marker doc.
- `loam amend apply` the manifest; advance the seal sidecar.
- Commit on the branch — NO `--amend`, NO push; commit only the files this slice
  touches; leave pre-existing dirty/untracked files untouched.

---

## 7. Activate + prove (Phase 2, on live pos3)

1. Fresh backup to `.scratch/fbm-activation-backup-<stamp>/`: vendored
   primary-persona tree (file_memory.py, memory_consumer.py, keep_pace/,
   session_start_emitter.py, context_composer.py), the LIVE store
   `workspace/.loam/memory/` (verify episode count + md5 a sample), the corpus
   index. Confirm complete before mutating.
2. `cp`-swap the consolidation's changed files from loam@HEAD into the pos3
   vendored tree. Sanity-check each delta.
3. Apply the no-op migration; rebuild the corpus index cleanly.
4. ★ SMOKE AGAINST THE REAL HOOK — run `python -m loam.primary_persona.cli
   user-prompt-submit` with a representative prompt on stdin (the way the live
   hook is invoked) and inspect the RENDERED memory block. Confirm: (a) NO
   task-notification/junk; (b) a real memory surfaces; (c) a weighted/pinned
   rule behaves; (d) no exception. Capture before (old code from backup) vs
   after.
5. If junk still appears in the real-hook output OR anything fails → ROLL BACK
   (restore vendored tree + index from backup), verify old behavior + live store
   intact (count + md5), HALT with report.
6. Note: vendored tree is untracked in pos3 git — no commit there.

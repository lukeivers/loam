# keep-pace-with-user MVP — sub-plan-doc (KP0 / KP1 / KP5 / KP9 / KP7)

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-28.
**Working directory:** `/Users/lukeivers/loam/`.
**Parent design:** `docs/design/keep-pace-with-user.md` (the FINAL design + folded adversarial critique; §3 MVP table is the phasing this plan executes).
**Storage foundation it composes on:** `docs/design/memory-architecture.md` (index-vs-detail, hot cap, hot/warm/cold tiering). **NOTE — the storage doc carries a false-claim this plan does NOT inherit:** see §10 RF item RF-1. This plan assumes ONLY the file-based memory reality (S1 CLAUDE.md hierarchy + S2 `feedback_*.md` corpus); it does NOT assume the graphiti/S3 store is live.
**Predecessors (load-bearing):**
- `c88bd0b` — current loam HEAD (BASELINE candidate; pre-build tip).
- `8fea4b9` — last sealed amendment (#148, loam-bafi-stale-test-retire) per STATE.md.
- `docs/design/keep-pace-with-user.md` — research/design artefact this plan operationalises (on disk, dated 2026-05-28).
- `docs/design/memory-architecture.md` — storage-layer design this plan composes against (on disk).

**BASELINE (pre-build tip):** `c88bd0b` (re-confirm at apply-time; advance to the source-edit commit per cycle).
**Amendment number:** derived sequentially at `loam amend apply` time per cycle (NOT pre-allocated, per `feedback_version_numbers_at_release_time` applied to the amendment counter — STATE.md counter base is #148; the manifest's `amendment.number` is filled in by the builder against the live counter at apply).
**Status-file target:** `/Users/lukeivers/loam/workspace/.scratch/claude-output/keep-pace-mvp-status-2026-05-28.md`.
**Quality bar:** the MVP must fix tonight's failure (the persona forgetting on-file context *while actively working on the related topic*). Every user-facing surface stays plain-language. No partial features. Fail-open-whole-chain is non-negotiable — a broken memory hook must NEVER break the live session.

---

## §1. Summary / TL;DR

This sub-plan ships the **5-item MVP** of the keep-pace system as **four serialized amendment cycles** (per `feedback_serialize_amendment_builds` — one git tree, builds do not parallelise):

- **Cycle 1 — KP0: wire the hook chain.** There are currently **zero wired hooks** (global `settings.json` `hooks` = `{}`; no project settings; no plugin `hooks.json`). KP0 wires `UserPromptSubmit` + `PreToolUse` into the settings surface, adds a per-turn total-latency budget, and proves **fail-open-whole-chain** (a hook timeout/crash lets the turn proceed). KP0 is also where the FD-inheritance + Claude-Code-`#15174` (SessionStart-compact) risk surfaces live, so its smoke probes the installed CLI's actual event behaviour **before** any dependent build.
- **Cycle 2 — KP5 + KP1: register + work-anchored retrieval.** KP5 creates `OBJECTIVES.md` (index/detail shape, seeded with the two real current objectives — the fiction pipeline + the revenue push — named distinct from loam's dev-ODD). KP1 is the load-bearing piece: a `UserPromptSubmit` retrieval hook that scores a **work-anchored key** (`prompt + active-objective + active-subgoal + last-turn topic`) via **BM25/FTS5** over the markdown corpus, injects top-N ≤5 as `additionalContext`, silent on no-match, fresh read each turn. KP5 ships first in the same cycle because KP1 reads it for the anchor.
- **Cycle 3 — KP9: abstraction-voice + constraint-check draft gate.** A NEW `PreToolUse` hook reusing the existing `translation-discipline` jargon logic: **Layer 1** deterministic jargon lint (blocks file-names/paths/IDs/un-introduced ALLCAPS) + **Layer C** draft-vs-active-constraint-memory check (the mid-draft tonight-failure catch the prompt-hook structurally cannot see). Routes **every** user-facing surface.
- **Cycle 4 — KP7: SessionStart objective + last-state surface.** A NEW surfacing step on the existing `pos_session_start.py`: plain-language "last session you were on X; next likely Y," routed through KP9's gate, re-asserted via the first `UserPromptSubmit` so a compaction can't evaporate it (the `#15174` mitigation).

**AC families:** `AC.KP0.*` (hook chain + fail-open), `AC.KP1.*` (work-anchored retrieval), `AC.KP5.*` (objectives register), `AC.KP9.*` (voice + constraint gate), `AC.KP7.*` (session-start surface), `AC.KP.S` (live-session-safety fence). One outcome-altitude AC: `AC.KP1.6` (cold-walk: a vague "continue" on litrpg work surfaces the canon pointer through the production entry-point with no pre-arranged retrieval state).

**Key decisions baked (already owner-ruled — encoded, not re-opened):** sparse-first BM25/FTS5 (no API key, no embeddings); compactor cadence = SessionStart-fold; drift-audit = PROPOSE-AND-SURFACE (auto-update only soft bookkeeping); register-judge gating = pre-filter-then-judge, fail-open, log-to-tune; `OBJECTIVES.md` scope = user-level for top-level objectives + per-workspace files for project-local subgoals. See §3.

**F2 on scope realism:** the MVP is ~2.5–4.5 build-hours of AI-time across four cycles plus one week of score-logging before KP2 (post-MVP) can steer. The honest residual: injecting a pointer ≠ the model attending to it (lost-in-the-middle applies to the pointer too). KP9 Layer C closes more of the gap by checking the generated text. The build substantially improves the failure; it does not claim to eliminate it. See §10.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| KP0 hook wiring | `~/.claude/settings.json` `hooks` block (user-scope) + a loam-owned hook-script directory under `framework/hands-off-lifecycle/hooks/` (existing hook home — `corpus_inline_session_start.py` already lives there) | The settings surface is user-scope (the live harness Luke runs); the hook *scripts* are loam source under the existing hands-off-lifecycle hooks home so they seal under that component's fence. |
| KP1 retrieval hook + BM25/FTS5 index | `framework/hands-off-lifecycle/hooks/` (the hook) + a loam-owned retrieval module (new `keep_pace/` package under the same component, or `framework/primary-persona/` if it shares the memory-read surface — **builder's call per ODD §1.1**, constrained to one component fence per cycle) | Read-path is harness-general; lives with the other session hooks. The FTS5 index file is a runtime artefact in `<workspace>/.scratch/` (gitignored), not committed source. |
| KP5 `OBJECTIVES.md` register (top-level) | user-scope: `~/.claude/.../OBJECTIVES.md` (mirrors the MEMORY.md / CLAUDE.md user-scope hierarchy) | Owner-ruled user-scope for top-level objectives (the two objectives span workspaces). The *schema/template* + the *seed content* are authored as loam source; the live user-scope file is written by the build's seed step. |
| KP5 per-workspace subgoal files | `<workspace>/` project-local (e.g. the litrpg workspace) | Owner-ruled: project-local subgoals ladder up to the user-level objectives, mirroring the CLAUDE.md hierarchy. |
| KP9 draft-gate hook (Layer 1 + Layer C) | `framework/hands-off-lifecycle/hooks/` (new `PreToolUse` hook) reusing the `translation-discipline` jargon logic | The jargon logic currently lives in the `translation-discipline` SKILL + the deterministic jargon-guard ODD component; KP9 extracts/reuses that module into a `PreToolUse` hook (NEW wiring, not "extend a running hook" — there is no running jargon hook). |
| KP7 SessionStart surface step | `framework/orchestrator/scripts/pos_session_start.py` (existing real SessionStart hook) — add a surfacing step | `pos_session_start.py` is a real SessionStart hook (currently service-health probing only); KP7 adds a new surface step to it. Re-assert routes via the KP1 `UserPromptSubmit` hook (the `#15174` mitigation). |

---

## §3. Halt-and-surface BEFORE build (owner rulings encoded + autonomous shape decisions recorded)

### Surface #1 (NO halt — owner-ruled; retrieval substrate = sparse-first)

**Decision (owner-ruled, encoded):** retrieval is **BM25/FTS5 over the markdown corpus** — no Anthropic API key, no embeddings (honors `feedback_no_anthropic_api_key`). Dense/MCP-vector is reserved as an optional later hybrid **only on observed keyword-miss**, and post-MVP KP2's miss-gate is the instrument that would tell us if it's ever warranted. Recommendation: build sparse, defer dense indefinitely. **This fork is closed — do not re-open.**

### Surface #2 (NO halt — owner-ruled; compactor cadence = SessionStart-fold)

**Decision (owner-ruled, encoded):** the compactor / journal-fold cadence is **SessionStart-fold** (folds happen at session start, not on a timer/cron). MVP does not build the compactor (KP3/KP4 are post-MVP), but KP7's SessionStart step is authored so the later fold composes onto the same event. **Closed.**

### Surface #3 (NO halt — owner-ruled; drift-audit = PROPOSE-AND-SURFACE)

**Decision (owner-ruled, encoded):** the objective-drift audit **never silently rewrites an objective's status.** Any status change (active↔dormant↔retired) is **surfaced as a proposal, owner-gated.** Auto-update is permitted ONLY for soft bookkeeping (`last-touched` timestamp, cadence counter). MVP does not build the drift engine (KP8 is post-MVP + last), but KP5's `OBJECTIVES.md` schema reserves the `status` field as owner-gated-write and the `last-touched`/`cadence` fields as soft-auto-write. **Closed.**

### Surface #4 (NO halt — owner-ruled; register-judge gating = pre-filter-then-judge, fail-open, log-to-tune)

**Decision (owner-ruled, encoded):** the Layer-2 `claude -p` register judge (post-MVP KP10) runs **only when a cheap deterministic pre-filter flags the draft as plausibly-technical**; it **fails open** (judge unavailable/timeout → draft passes); every invocation logs for later threshold tuning. MVP ships only KP9 Layer 1 (deterministic lint) + Layer C (constraint-check) — both deterministic, both fail-open. The judge itself is post-MVP. KP9 is authored so the pre-filter hook-point exists for KP10 to attach. **Closed.**

### Surface #5 (NO halt — owner-ruled; OBJECTIVES.md scope split)

**Decision (owner-ruled, encoded):** `OBJECTIVES.md` is **user-scope** for top-level life/work objectives (`~/.claude/.../OBJECTIVES.md`), with **per-workspace files** allowed for project-local subgoals that ladder up (mirrors the CLAUDE.md hierarchy). The two seeded objectives (fiction pipeline, revenue push) are user-scope because they span workspaces. **Closed.**

### Surface #6 (NO halt — recorded; OBJECTIVES.md named distinct from dev-ODD)

**Decision (autonomous, per design §2 Dimension C):** the register is named `user-objectives` in its header/schema to prevent agent confusion with loam's `dev-ODD`. The objective entries are NOT ODD objectives; they are the user's current-focus rotation key. `OBJECTIVES.md` is added to memory-architecture M2's **audited-surface list** (it is an always-load index-shaped surface and inherits the byte-budget discipline) — recorded here so the later M2 budget-guard does not silently omit it.

### Surface #7 (NO halt — recorded; `w_s` objective-weight capped low — but post-MVP)

**Decision (autonomous, per design §2 fragility note):** the architecture's own fragility is that objectives→rotation rests on the weakest, last-built component (KP8). The mitigation is to start the objective-match weight `w_s` LOW and let recency+frequency carry rotation until objectives are proven current. **MVP impact:** KP1's retrieval key INCLUDES the active-objective text as a scoring term, but MVP does NOT yet do hotness rotation (KP4 is post-MVP). So `w_s`-capping is a KP4 concern; for MVP the objective text is simply one of four anchor terms in the BM25 query, weighted equally with the others unless the builder observes objective-term over-domination during KP1 smoke (in which case down-weight and record). Recorded so it is not lost.

### Surface #8 (NO halt — recorded; serialization between cycles)

**Decision (autonomous, per `feedback_serialize_amendment_builds`):** the four cycles seal in order (KP0 → KP5+KP1 → KP9 → KP7), each with its own manifest, `loam amend apply`, and seal commit. No two build agents run in this one git tree concurrently. Cycle N+1 does not start until Cycle N seals green.

---

## §4. Spec-objective placement

**Binds to:**

- **The prime objective (`docs/VALUE_PROPOSITION.md` — the primary-persona test + the harness test).** The MVP is a direct primary-persona-test win: it reduces the user's translation burden (the right context surfaces against the live work; the user never holds a file name; objectives stay current) and a harness-test win (it adds work-anchored recall, the draft-gate catch, and objective-tracking to the persona's toolkit). Maps to `memory-architecture.md` P1 (transparent continuity), P2 (trust — never silently lose context), P3 (graceful scaling).
- **`docs/design/keep-pace-with-user.md` §3 MVP table** — KP0/KP1/KP5/KP9/KP7 are the five MVP rows; this plan executes exactly that phasing.
- **`docs/design/keep-pace-with-user.md` §1 spine** — the work-anchored retrieval key (fix #1) + the draft-to-send gate (fix #2) are the two corrections that reshape the spine to actually catch tonight's failure.

**Ladders to:** `AC.KP0.*` + `AC.KP1.*` + `AC.KP5.*` + `AC.KP9.*` + `AC.KP7.*` → the keep-pace MVP outcome (persona stops forgetting on-file context mid-task; objectives stay current; user-facing surfaces stay plain-language) → the VALUE_PROPOSITION primary-persona + harness tests (the prime objective). Post-MVP KP2/KP3/KP4/KP6/KP8/KP10 ladder onto the same hook surfaces this MVP wires.

---

## §5. Acceptance criteria

All ACs are outcome-shaped (method is the builder's call per ODD §1.1). The method-in-AC test has been applied to each: every AC below can be satisfied by a method other than the one the author has in mind.

### AC.KP0.* family — hook chain wired + fail-open + event probe

- **AC.KP0.1 — `UserPromptSubmit` + `PreToolUse` hooks fire on the installed CLI.** A no-op probe hook registered on each event is observed to execute when a prompt is submitted and when a tool is about to run, on the Claude Code version installed on this machine. Verification: the probe writes a timestamped marker; the marker appears for both events. (This is the **VERIFY-FIRST gate** — it runs BEFORE KP1/KP9 build; if either event does not fire, halt and surface per §8.)
- **AC.KP0.2 — `InstructionsLoaded` event behaviour probed.** The probe records whether the `InstructionsLoaded` event fires and can emit into context on the installed version. Outcome recorded (fires / does-not-fire); a non-firing result does NOT block the MVP (it blocks only the post-MVP memory-architecture M2 guard) but is surfaced. (VERIFY-FIRST.)
- **AC.KP0.3 — `#15174` SessionStart-compact behaviour probed; re-injection route confirmed.** The probe records whether a SessionStart-injected surface survives a compaction on the installed version. If it does not (the `#15174` bug is live), KP7's re-assert is confirmed to route via `UserPromptSubmit` instead. Outcome recorded. (VERIFY-FIRST.)
- **AC.KP0.4 — fail-open-whole-chain on hook timeout/crash.** A deliberately-failing (or sleeping-past-budget) test hook is registered; the turn is observed to **proceed** (the user's prompt is answered) rather than hang or error. The per-turn total-latency budget is observable in the smoke log. Outcome: a broken memory hook never breaks the live session.
- **AC.KP0.5 — per-hook latency observable.** The smoke logs per-hook wall-clock latency for the wired chain, so the per-turn budget can be reasoned about. (Status-file recorded.)

### AC.KP5.* family — OBJECTIVES.md register + seed

- **AC.KP5.1 — `OBJECTIVES.md` exists at user-scope with the index/detail schema.** The file exists at the user-scope path; each entry carries: scope-descriptive slug, `status` (`active`/`dormant`/`retired`), `last-touched`, `cadence`, objective text + completion criterion, subgoal state, detail-path. Header names the register `user-objectives` (distinct from dev-ODD).
- **AC.KP5.2 — two real objectives seeded `active`.** The fiction-pipeline objective and the revenue-push objective are both present, both `status: active`, each with a completion criterion and at least one subgoal.
- **AC.KP5.3 — register loads within the hot byte-budget.** The register's index surface is under the memory-architecture hot-index budget (≤ ~20KB headroom target per memory-architecture §5 #5); a too-large register is caught (the entry detail lives in the detail-path file, not inlined into the index).
- **AC.KP5.4 — `status` field is owner-gated-write; `last-touched`/`cadence` are soft-auto-write.** The schema/loader distinguishes the owner-gated `status` field from the soft-auto bookkeeping fields (encodes Surface #3's PROPOSE-AND-SURFACE ruling at the schema level). Verification: a test asserts the loader exposes the field-class distinction.
- **AC.KP5.5 — KP1's anchor can read the active-objective text.** The retrieval read-path (AC.KP1.*) can extract the active-objective text from the register for use as an anchor term. (Cross-AC binding; verified at the KP1 layer.)

### AC.KP1.* family — work-anchored per-prompt retrieval

- **AC.KP1.1 — BM25/FTS5 index over the markdown corpus builds and updates.** An index over the `feedback_*.md` corpus (+ CLAUDE.md hierarchy + OBJECTIVES.md) builds; a corpus write is reflected in the index within single-digit-ms on the next read. No embeddings, no API call.
- **AC.KP1.2 — work-anchored retrieval key.** The retrieval key is composed of `prompt + active-objective text + active-subgoal + last-turn topic` (NOT the typed prompt alone). Verification: a test asserts all four components contribute to the query when present, and the query degrades gracefully (still functions) when a component is absent.
- **AC.KP1.3 — top-N ≤5 injected as `additionalContext`.** A prompt mentioning a known on-file topic causes the correct pointer(s) to be injected as `additionalContext`, capped at N ≤ 5. Verification: a prompt naming a known topic → the corresponding `feedback_*.md` pointer appears in the injected context.
- **AC.KP1.4 — silent on no-match; skip trivial prompts.** A prompt with no corpus match injects nothing (no noise); trivial prompts (greetings, acks) are skipped. Verification: a no-match prompt → empty injection; a trivial prompt → skipped.
- **AC.KP1.5 — fresh read each turn.** The store is re-read each turn (a corpus change between turns is reflected on the next turn without a session restart). Verification: write a new corpus entry mid-session-equivalent; next retrieval sees it.
- **AC.KP1.6 — `outcome-altitude: true` — cold-walk: vague "continue" on litrpg work surfaces the canon pointer.** Invoking the production retrieval entry-point with **no pre-arranged retrieval state**, with a vague prompt ("continue the batch" / "keep going") AND an active-objective set pointing at the fiction pipeline, surfaces the litrpg canon pointer via the objective anchor (the term the bare prompt cannot supply). This is the direct test of tonight's failure. **No fixture pre-loads the canon pointer into the working set** — it must be retrieved by the work-anchor. (Outcome-altitude per `feedback_test_outcome_altitude_required`: production entry-point, no pre-arranged state.)

### AC.KP9.* family — abstraction-voice Layer 1 lint + Layer C constraint-check

- **AC.KP9.1 — Layer 1 deterministic jargon lint blocks leaks.** A draft containing a file-path (`/Users/...`), a `.md` filename, an AC-ID, or an un-introduced ALLCAPS token is blocked before send. Verification: each leak class → block; a clean plain-language draft → pass. Reuses the `translation-discipline` jargon logic.
- **AC.KP9.2 — Layer C constraint-check flags draft-vs-active-constraint contradiction.** A draft that contradicts an active high-salience constraint-memory (a seeded canon rule, a sealed ruling) is flagged before send. Verification: a litrpg draft contradicting a seeded canon rule → flagged; a compliant draft → pass. **This is the mid-draft tonight-failure catch the `UserPromptSubmit` hook structurally cannot make.**
- **AC.KP9.3 — routes EVERY user-facing surface.** The gate fires on persona free-text, drift proposals, the SessionStart summary, and any surfaced miss-recovery — every outbound user-facing surface, not just persona free-text. Verification: a non-free-text surface (e.g. a session-start summary string) carrying a leak is also blocked.
- **AC.KP9.4 — gate feedback stays model-facing; fail-open.** The gate's own block/flag reason is emitted model-facing (stderr/hook-reason), never as a user-visible "your reply was blocked by the register judge" message (that would itself be a mechanism-leak). On gate error/timeout the draft passes (fail-open). Verification: gate-error → draft sent; block-reason absent from user-visible output.

### AC.KP7.* family — SessionStart objective + last-state surface

- **AC.KP7.1 — session opens with a plain-language last-state surface.** On session start, the persona surfaces "last session you were on X; next likely Y" in plain language (active objectives + last subgoal + likely-next-action), routed through KP9's gate (so no file-names/IDs leak). Verification: session-start surface present + passes KP9's lint.
- **AC.KP7.2 — survives one compaction via `UserPromptSubmit` re-assert.** The session-start surface is re-asserted via the first `UserPromptSubmit` after a compaction, so a compaction (incl. the `#15174` SessionStart-compact bug, if live per AC.KP0.3) cannot evaporate it. Verification: simulate a compaction; the re-assert restores the surface.
- **AC.KP7.3 — surface describes itself in plain language.** When the surface reports on the memory system's own behaviour ("I've been keeping your fiction work close at hand"), it uses plain words, never internal terms ("ARC-promoted," "w_s," "objective-match"). Verification: the surface string contains no internal-jargon tokens (composes with AC.KP9.1).

### AC.KP.S — live-session-safety fence (every cycle)

- **AC.KP.S.1 — the running session + in-flight litrpg production are protected.** No cycle modifies a sealed component without a manifest entry; no cycle wires a hook that can hang or break the live session (AC.KP0.4 fail-open is the structural guarantee); no cycle touches the live litrpg workspace content (only its workspace-local subgoal file under KP5, additively). Verification: per-cycle fence diff confined to the declared component(s) + universal paths; fail-open smoke green before any hook is left wired.

---

## §6. Build steps

Method-level guidance only (the builder's call per ODD §1.1). Each cycle: manifest → source edits → tests → touched-test run → `loam amend apply` → `loam amend seal` → smoke.

### Cycle 1 — KP0 (hook chain + fail-open + VERIFY-FIRST probe) — single/low-touch fence

1. **Manifest** authored: `docs/plans/keep-pace-with-user-mvp-kp0.manifest.yaml` — fence on the hook-script home component (hands-off-lifecycle) + the user-scope `settings.json` wiring documented as an out-of-tree side-effect (the settings file is user-scope, not committed loam source; the *scripts* are the sealed artefacts).
2. **VERIFY-FIRST probe FIRST** (AC.KP0.1/.2/.3): a ~5-line probe hook on `UserPromptSubmit` + `PreToolUse` + a SessionStart marker; run it against the installed CLI; record which events fire, whether `InstructionsLoaded` fires + emits, and the `#15174` SessionStart-compact behaviour. **If `UserPromptSubmit` or `PreToolUse` does not fire → HALT and surface (§8).**
3. **Source edits** (in order; builder's call on exact module layout):
   - Hook scripts under `framework/hands-off-lifecycle/hooks/` (the existing hook home).
   - A per-turn total-latency budget + fail-open-whole-chain wrapper.
   - The `~/.claude/settings.json` `hooks` block wiring (user-scope; documented in the status file as the live-harness change, not a committed source edit).
4. **Tests** authored: `test_AC_KP0_4_fail_open_whole_chain.py` (deliberately-failing hook → turn proceeds), `test_AC_KP0_5_per_hook_latency.py` (latency observable). KP0.1/.2/.3 are probe-recorded (status-file), not unit-asserted against the live CLI.
5. **Touched-tests run** (the new tests + the hands-off-lifecycle component tests).
6. **`loam amend apply`** (NOT `--amend`; new corrective commits if a file is missed).
7. **`loam amend seal`**.
8. **Smoke:** wired chain fires both events; fail-open verified live (a broken hook does not break the session).

### Cycle 2 — KP5 + KP1 (register first, then retrieval) — single-component fence

1. **Manifest** authored: `docs/plans/keep-pace-with-user-mvp-kp5-kp1.manifest.yaml`.
2. **KP5 source edits** (first — KP1 reads it): `OBJECTIVES.md` schema/template + seed of the two objectives + the loader distinguishing owner-gated `status` from soft-auto `last-touched`/`cadence`. The user-scope live file is written by the seed step; the schema/template is sealed loam source.
3. **KP1 source edits:** the BM25/FTS5 index builder over the markdown corpus + the `UserPromptSubmit` retrieval hook (work-anchored key; top-N ≤5; silent-on-no-match; skip-trivial; fresh-read). Index file is a runtime artefact in `<workspace>/.scratch/` (gitignored), not committed.
4. **Tests** authored: `test_AC_KP5_{1,2,3,4}_*.py`, `test_AC_KP1_{1,2,3,4,5}_*.py`, and the outcome-altitude `test_AC_KP1_6_cold_walk_vague_continue_surfaces_canon.py` (production entry-point, no pre-arranged state, vague prompt + active fiction objective → canon pointer surfaces).
5. **Touched-tests run.**
6. **`loam amend apply`** → **`loam amend seal`**.
7. **Smoke:** a known-topic prompt injects the right pointer; a vague "continue" on litrpg work surfaces the canon pointer via the objective anchor (the tonight-failure smoke).

### Cycle 3 — KP9 (voice + constraint draft gate) — single-component fence

1. **Manifest** authored: `docs/plans/keep-pace-with-user-mvp-kp9.manifest.yaml`.
2. **Source edits:** a NEW `PreToolUse` hook reusing the `translation-discipline` jargon logic (Layer 1 lint) + Layer C draft-vs-active-constraint-memory check; routes every user-facing surface; gate feedback model-facing only; fail-open; a deterministic pre-filter hook-point reserved for the post-MVP KP10 judge.
3. **Tests** authored: `test_AC_KP9_{1,2,3,4}_*.py` (each leak class blocked; constraint-contradiction flagged; non-free-text surface gated; fail-open + model-facing-only feedback).
4. **Touched-tests run.**
5. **`loam amend apply`** → **`loam amend seal`**.
6. **Smoke:** a draft with a path/filename/AC-ID is blocked; a litrpg draft contradicting a seeded canon rule is flagged before send.

### Cycle 4 — KP7 (SessionStart surface) — single-component fence

1. **Manifest** authored: `docs/plans/keep-pace-with-user-mvp-kp7.manifest.yaml`.
2. **Source edits:** a new surfacing step on `framework/orchestrator/scripts/pos_session_start.py` (active objectives + last subgoal + likely-next-action, plain-language, routed through KP9's gate); re-assert via the first `UserPromptSubmit` (the `#15174` mitigation, per AC.KP0.3's recorded behaviour).
3. **Tests** authored: `test_AC_KP7_{1,2,3}_*.py` (session-start surface present + passes lint; survives one compaction via re-assert; self-description uses plain words).
4. **Touched-tests run.**
5. **`loam amend apply`** → **`loam amend seal`**.
6. **Smoke:** session opens with a plain-language last-state surface; survives one simulated compaction.

### Post-all-cycles

- Update the status file with all probe outcomes + per-cycle smoke results.
- Backfill bookkeeping per §9.

---

## §7. Out of scope (deferred — named so they're not lost)

- **KP2 — context-miss gate.** Post-MVP; dark-launched (log-only) inside KP1 week 1, steers after the threshold is calibrated from the observed score distribution. Gate to start: KP1 has logged a week of real scores.
- **KP3 — session journal + cross-session fold.** Post-MVP; append-only partition per session, hook reads all partitions fresh + folds by timestamp. **Needs its own n=1 two-session proof** (one two-session liveness demonstration — `feedback_n1_architectural_vs_n3_statistical`: architectural question, prior-informed, large effect, binary verifier → n=1 sufficient). Gate: MVP loop observed working single-session.
- **KP4 — ARC hotness rotation.** Post-MVP; `usage-counters.json` + compactor scores `w_f·freq + w_r·recency + w_s·objective-match` with **`w_s` capped low initially** (Surface #7). Gate: memory-architecture M1+M2 landed; frequency data accruing.
- **KP6 — objective-lifecycle SKILL over the register.** Post-MVP; create/replace/pause→dormant/done→retired(keep entry)/status. NOT a `/goal` mutation (`/goal` stays the driver). Gate: KP5 exists (it will, after this MVP).
- **KP8 — objective-drift audit.** Post-MVP, LAST (highest annoyance risk). Commission/omission proxies over git+tasks+touched-files; SURFACE proposals only (Surface #3 owner-gated). **KP2 threshold + KP8 proxies are n≥3 statistical-quality** (`feedback_n1_architectural_vs_n3_statistical`: tuning/quality questions need statistical confidence) — note for their phases. Gate: objectives manually curated for a while; `w_s` proven safe.
- **KP10 — Layer-2 register judge.** Post-MVP; independent `claude -p` via `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py` (the real wrapper path; Sonnet default), 4-axis rubric, surgical rewrite, conditional on the pre-filter, fail-open, log-to-tune. Gate: KP9 + re-injection observed insufficient on semantic leaks.
- **memory-architecture M1–M5** (the storage-layer cycle) — separate plan; this plan composes ON the storage design but does not build the M-items. KP5 adds `OBJECTIVES.md` to M2's audited-surface list (Surface #6) for when M2 lands.

---

## §8. Halt triggers (in-flight)

- **VERIFY-FIRST failure:** `UserPromptSubmit` or `PreToolUse` does not fire on the installed CLI (AC.KP0.1) → HALT; the whole MVP rests on these events. Surface with the probe evidence.
- WD drifts from `/Users/lukeivers/loam/` → halt + surface.
- A hook leaves the live session able to hang or error (fail-open AC.KP0.4 not provable) → HALT; do NOT leave the hook wired.
- Any cycle would touch a sealed component without a manifest entry → HALT (do not silently widen the fence).
- Any cycle would modify live litrpg workspace **content** (only the workspace-local subgoal file is in-scope, additively) → HALT + surface.
- Any AC ships partial → halt + reframe (no partial features per the quality bar).
- More than ~5 in-build decisions need owner escalation → halt + describe (apply the operational-objective test first; only escalate critical-call / public-action / financial).
- Cycle N seal fails → halt; do NOT start Cycle N+1 (serialization, Surface #8).
- An AC turns out to be method-in-AC on closer build inspection → halt + surface for an AC tightening (fix the AC, not the implementation, per `feedback_loose_AC_text_fix_AC_not_implementation`).

---

## §9. Bookkeeping

- `loam amend apply` + `loam amend seal` on each of the four cycles (NOT `git commit --amend`; new corrective commits if a file is missed, per `feedback_no_amend_in_agent_dispatches`).
- One semantic commit message per cycle.
- Backfill `docs/release-roadmap.md` with the keep-pace-MVP arc + per-cycle apply/seal SHAs.
- Update `docs/STATE.md` with the keep-pace-MVP cycles + the advanced amendment counter (base #148).
- Record all VERIFY-FIRST probe outcomes (AC.KP0.1/.2/.3) in the status file — these are load-bearing for the post-MVP phases (`#15174` route, `InstructionsLoaded` availability).
- **Correct `docs/design/memory-architecture.md` §1 + §3.5 false-claim** (RF-1 below) as part of this work — a doc-only correction (the graphiti/S3 store is NOT live; current memory is file-based only). This is in the `docs/` universal-admission prefix and rides any cycle's fence.
- Populate §14 method-decision register (below) at build time; backfill SHAs at seal time via `loam amend seal --plan-doc`.

---

## §10. F2 — Ruthless Feedback (honest doubts + design risks named)

- **RF-1 (the dispatch-flagged false claim — verified Tier-0, corrected here).** `docs/design/memory-architecture.md` §1 (table row S3) + §3.5 (line 118) present the **graphiti / S3 store as operative** — "Retrieved per-turn via `search(group_ids=[slug])`," "`memory_consumer.py` already fires a per-turn search... renders the top-N facts/episodes... fail-closed." **Evidence (Tier-0, 2026-05-28):** `python3 -c "import graphiti_core"` → `ModuleNotFoundError: No module named 'graphiti_core'`; no `kuzu_db` directory exists anywhere on disk (`find / -name kuzu_db -type d` → empty); `memory_consumer.py` exists but its own docstring states it "never imports memory-system source; the Protocol is sufficient" — it is a Protocol shim with no live backend. **The alternative (what this plan assumes):** the current memory reality is **file-based only** — S1 (CLAUDE.md hierarchy) + S2 (`feedback_*.md` corpus + MEMORY.md index). This plan's KP1 retrieves over the **markdown corpus**, not the graph. **Correction action:** §9 includes a doc-only fix to memory-architecture.md §1/§3.5 marking S3-graphiti as not-currently-live (design-aspirational, not operative). This is RF, not silent acceptance.
- **RF-2 (the residual the design itself names — restated so the builder does not over-claim).** Injecting a pointer ≠ the model attending to it; lost-in-the-middle applies to the injected pointer too. KP1 raises the *probability* the right memory is in context; KP9 Layer C closes more of the gap by checking the generated text. **Neither guarantees zero drift.** The MVP substantially improves tonight's failure; it does not eliminate it. Any status-file or owner report MUST state this honestly (no "memory is now perfect" framing).
- **RF-3 (the architecture's own fragility — objectives→rotation).** The correctness pivot (active-objective set as the retrieval anchor / rotation key) rests on the objective model being current. If `OBJECTIVES.md` goes stale, every work-anchored retrieval is mis-targeted. **MVP mitigation:** KP1 weights the objective term equally (not dominantly) with the other three anchor terms; rotation (KP4) is post-MVP; drift-audit (KP8) is propose-and-surface only. **But:** the MVP seeds the objectives ONCE; there is no MVP mechanism to keep them current (KP6 lifecycle SKILL + KP8 audit are both post-MVP). So the MVP relies on the owner manually keeping `OBJECTIVES.md` current for the first phase. Named so it is not a silent assumption.
- **RF-4 (KP9 Layer C is the load-bearing tonight-failure catch, and it is the riskier of the two layers).** Layer 1 (jargon lint) is deterministic and low-risk. Layer C (draft-vs-constraint-memory) requires identifying *which* constraint-memories are "active high-salience" for the current draft — a relevance judgement on a deterministic-only budget (no judge until post-MVP KP10). The risk: Layer C either over-flags (annoying, but fail-open so non-blocking) or misses a real contradiction (the tonight-failure recurs). **Alternative if Layer C proves unreliable in smoke:** scope Layer C narrowly to the *seeded canon rules + sealed rulings* (a small, explicitly-tagged active-constraint set) rather than the whole corpus, and expand only when KP10's judge lands. Recommend starting narrow.
- **RF-5 (the FTS5 cost figures are claude-mem's, not loam's).** The design's "$0 / 45ms" are claude-mem's measured numbers. loam's first-build numbers are TBD. Do NOT import them as loam's; KP0.5's per-hook latency log produces loam's actuals. Named so no report quotes claude-mem's numbers as loam's.
- **RF-6 (KP0 user-scope settings.json is an out-of-tree live-harness change).** Wiring `~/.claude/settings.json` is not a committed loam source edit — it modifies the live harness Luke runs *right now*, in *this* session. The fail-open guarantee (AC.KP0.4) MUST be proven before the hook is left wired, or a bug in KP1/KP9 could degrade Luke's live sessions. This is the single highest-blast-radius step in the MVP; it is also why KP0 is first and why fail-open is a halt trigger.

---

## §11. Provenance trail

- `docs/design/keep-pace-with-user.md` (2026-05-28) — the FINAL design: §1 spine (work-anchored key fix #1 + draft-gate fix #2), §3 MVP table (KP0/KP1/KP5/KP9/KP7), §6 owner-asks (the two forks + the deferred decisions), §0 verified-machine-state table.
- `docs/design/memory-architecture.md` (2026-05-28) — storage foundation: §2 P1/P2/P3, §3.2 tiering, §3.3 index-vs-detail, §5 #5 (~20KB hot-budget headroom). RF-1 corrects its §1/§3.5 graphiti-live claim.
- Tier-0 machine-state verification (2026-05-28, `/Users/lukeivers/loam`):
  - `~/.claude/settings.json` `hooks` = `{}` (zero wired hooks) — confirms KP0 is first work.
  - No project `settings*.json`; no plugin `hooks.json`.
  - `framework/orchestrator/scripts/pos_session_start.py` exists (real SessionStart hook) — KP7 target confirmed.
  - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py` exists (the real `claude -p` wrapper) — post-MVP KP10 target confirmed.
  - `OBJECTIVES.md` absent anywhere — confirms KP5 creates it.
  - `queue_status_inject.py` + `translation_jargon_check.py` absent — confirms the design's §0 correction (these phantom hooks do not exist).
  - `translation-discipline` lives as a SKILL (`plugins/loam-skills/skills/translation-discipline/SKILL.md`) — confirms KP9 reuses-the-module, not extends-a-running-hook.
  - `import graphiti_core` → ModuleNotFoundError; no `kuzu_db` on disk — confirms RF-1 (file-based memory only).
  - Current HEAD `c88bd0b`; last sealed amendment #148 at `8fea4b9` (STATE.md); current published `v0.13.0`.
- Conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md` (plan-doc + manifest shape); `feedback_serialize_amendment_builds`, `feedback_no_amend_in_agent_dispatches`, `feedback_test_outcome_altitude_required`, `feedback_no_anthropic_api_key`, `feedback_version_numbers_at_release_time`, `feedback_n1_architectural_vs_n3_statistical`, `feedback_loose_AC_text_fix_AC_not_implementation`.

---

## §14. Method-decision register (populated at build time; SHAs backfilled at seal)

| ID | Decision | Builder narrative (build-time) | Apply SHA | Seal SHA |
|---|---|---|---|---|
| D-KP0.1 | hook-script home + settings wiring shape | Scripts in a `keep_pace/` subpackage under `framework/hands-off-lifecycle/hooks/` (groups KP0/KP1/KP9 keep-pace scripts, distinct from the flat hook files; keeps the seal under hands-off-lifecycle's fence). Settings wiring = a STAGED `settings.fragment.json` next to the scripts, NOT a live `~/.claude/settings.json` edit — live activation is the GATED final step (RF-6). | `a5946f3` | `ccfdc22` |
| D-KP0.2 | fail-open-whole-chain mechanism | `chain_runner.run_chain` runs each contributor in a daemon thread under a per-hook timeout (`thread.join(timeout)`; wedged threads abandoned, never block the turn) + a cumulative per-turn budget (later contributors `skipped-budget` once crossed). Every failure mode (raise / timeout / non-str / non-callable) is isolated into a `ContributorResult`; `run_chain` itself is wrapped to never raise; CLI entries exit 0 on every path. Daemon-thread abandonment is the only in-process timeout safe for arbitrary callables on a must-exit-promptly hook. | `a5946f3` | `ccfdc22` |
| D-KP1.1 | FTS5 index module layout + component fence | A `keep_pace/` subpackage under `framework/primary-persona/src/loam/primary_persona/` (the memory read-path component, the manifest fence): `corpus_index.py` (a NEW FTS5 index over the markdown corpus — distinct from `file_memory.py`'s episode index; indexes feedback_*.md + CLAUDE.md hierarchy + OBJECTIVES.md), `objectives.py` (KP5), `work_anchor.py` (the key), `retrieval.py` (production entry-point + chain contributor factory). Index file is a runtime artefact at `<ws>/.scratch/keep-pace/corpus-index.sqlite` (gitignored). The index is mtime-driven incremental + re-syncs on every search (AC.KP1.5 fresh-read). **Fence decision (recorded):** KP1's chain registration into the KP0 `user_prompt_submit.py` `contributors()` surface (in the hands-off-lifecycle component) is part of GATED live wiring — STAGED not done this cycle (matches KP0's staged-settings posture, RF-6); `retrieval.build_keep_pace_contributor()` is the Contributor.fn-shaped import target the staged wiring binds. This keeps the cycle-2 fence to `primary-persona` only, matching the manifest. | `0b8c843` | `aadf2b7` |
| D-KP1.2 | work-anchored key term-weighting (per Surface #7) | The four key components (prompt + active-objective text + active-subgoal + last-turn topic) are merged into ONE deduped OR-token FTS5 query — the objective term weighted EQUALLY with the others (Surface #7: no boost; `w_s` rotation-capping is post-MVP KP4). **Build-time finding (RF):** the term-rich key (76 tokens on the live corpus) makes low-IDF common words ("notes", "work", "keep") produce spurious single-word FTS5 matches; BM25 scores these ~0 while genuine multi-term objective matches score 13+. Resolved with a `MIN_RELEVANCE_SCORE = 0.1` floor (drops zero-IDF noise; AC.KP1.4 silent-on-no-match honestly = "nothing scored above noise") — NOT a stopword expansion (would risk dropping signal). Also recorded: the OBJECTIVES register indexes per AC.KP1.1 but surfaces with an EMPTY pointer (it is the anchor SOURCE, not a user-facing on-file topic). | `0b8c843` | `aadf2b7` |
| D-KP5.1 | OBJECTIVES.md schema + owner-gated/soft-auto field split | Markdown index format (`# user-objectives` header per Surface #6 + one `## <slug>` section per entry, flat `key: value` + `subgoals:` list); stdlib loader (no YAML dep). Field-class split exposed via `field_class()` / `OWNER_GATED_FIELDS={status}` / `SOFT_AUTO_FIELDS={last-touched,cadence}` (Surface #3 PROPOSE-AND-SURFACE at the schema level; the loader EXPOSES the distinction, write-side enforcement is owner-gated for `status`). Seeded the two real objectives from CURRENT-WORK.md (revenue-independence + litrpg-fiction-pipeline), both active. `load_user_scope_register` falls back to the in-source SEED when no live file exists — this is what lets AC.KP1.6 surface the canon pointer with NO pre-arranged state. **Seed posture (recorded):** the live user-scope `~/.claude/OBJECTIVES.md` write is STAGED (a sealed-source `OBJECTIVES.seed.md` artefact), NOT written live — bundled into the single GATED activation step alongside KP0's settings wiring (KP1 is unwired so the live file is non-load-bearing for this cycle; seed fallback covers correctness). | `0b8c843` | `aadf2b7` |
| D-KP9.1 | jargon-module reuse mechanism (extract vs import) | EXTRACT, not import (D-KP9.1). The deterministic jargon logic lives in `handsoff_loop.intake._JARGON_PATTERNS`/`assert_plain_language` (the tools/handsoff-loop component) + the translation-discipline SKILL prose. A live session hook must NOT take a cross-component runtime import that could fail to load and wedge the turn, and the SKILL is prose (not importable). So `draft_gate.py` (in the keep_pace hook home) carries a SELF-CONTAINED `_LAYER1_PATTERNS` mirroring intake.py's exact token-boundary pattern shapes (AC.PBF.3 discipline — match a genuine jargon TOKEN, never a naive substring) EXTENDED to the abstraction-first leak classes the SKILL names: file paths, `.md`/source file names, AC-IDs, commit SHAs, §-doc pointers, internal-mechanism tokens, un-introduced ALLCAPS (with an ordinary-English allowlist). Neither intake.py nor the SKILL is mutated (§15 backwards-compat verified — full hands-off-lifecycle suite 700 passed). | `1a31765` | `6b37490` |
| D-KP9.2 | Layer C active-constraint scope (per RF-4 — narrow-first) | NARROW-first per RF-4 (D-KP9.2). Layer C scopes to the explicitly-tagged in-source `SEEDED_CONSTRAINTS` (canon rules + sealed rulings), NOT the whole corpus — mirrors KP5's `SEEDED_OBJECTIVES` posture (precision-first seed, expanded only when KP10's judge lands). A `Constraint` carries `topic_tokens` (draft must be ON-topic), `correct_value`, and `violation_values`; a draft on-topic that asserts a violation value AND not the correct value is FLAGGED (deterministic, no judge). Seeded the tonight-failure case (Aaron-at-Priya's-pod canon — the exact ch1→ch2 continuity rule recently sealed in the litrpg workstream) + the metaphysical-overreach-personification editor catch + the no-Anthropic-API-key sealed ruling. Over-flag is fail-open (annoying, non-blocking); a missed contradiction re-arms tonight's failure, so narrow = precision-first. KP10 pre-filter hook-point reserved via `is_plausibly_technical()` (Surface #4), not called this cycle. | `1a31765` | `6b37490` |
| D-KP7.1 | SessionStart surface step + `#15174` re-assert route | NEW self-contained module `framework/orchestrator/scripts/session_surface.py` (orchestrator fence) holding `build_session_surface()` (active objectives + last subgoal + plain-language likely-next-action, de-slugged, first-sentence headline) ROUTED through KP9's `draft_gate.gate(surface_kind="session-start-summary")` — BLOCK → surface SUPPRESSED (never leak), FLAG/PASS → emitted; and `reassert_surface_for_user_prompt_submit()` returning the IDENTICAL gated surface for the first `UserPromptSubmit` (the `#15174` route, confirmed live by AC.KP0.3's recorded probe: model echoed the re-assert token verbatim). `pos_session_start.py main()` gains `_emit_keep_pace_surface()` — appends the surface as a SECOND additionalContext line AFTER the existing health line (probe behaviour PRESERVED, AC.KP.S.1), fail-soft. **Cross-component reads (objectives + draft_gate) are BEST-EFFORT lazy imports** (same D-KP9.1 discipline — a live SessionStart hook must never wedge on a sibling component absent/mid-edit): objectives reader raising → silent ''; gate raising → fail-OPEN (text passes); whole-surface raising → health line + exit 0 unchanged. Only ACTIVE objectives surface (filtered regardless of inject-vs-live path). Live activation of the surface (it reads the live `~/.claude/OBJECTIVES.md`, falling back to the in-source SEED) is non-load-bearing this cycle — the seed fallback covers correctness; the live user-scope write stays bundled in the single GATED activation step. **Build-time finding (RF):** the orchestrator suite carried TWO PRE-EXISTING stale assertions (`test_pos_session_start.py` expected `"pos v2 ready"` while the source has emitted `"loam ready"` since commit `1f6d4c1` "docs(rebrand)... cosmetic" — the rename updated the source string but left the two test assertions stale; only references in the repo). In-fence (orchestrator, this cycle's component), zero-ambiguity (impl-matches-intent, stale test text), trivially reversible → fixed both assertions to `"loam ready"` (sibling of `feedback_loose_AC_text_fix_AC_not_implementation`) rather than halting; surfaced here per F2. | _(apply)_ | _(seal)_ |
| D-KP7.2 (build-finding) | pre-existing stale-test fix (orchestrator, in-fence) | `test_pos_session_start.py` lines 65 + 165: `"pos v2 ready"` → `"loam ready"` (matches the long-standing source emit since `1f6d4c1`). Not caused by KP7; surfaced by KP7's full-suite seal gate. In-fence + reversible + zero-ambiguity → fixed, not halted. | _(apply)_ | _(seal)_ |
| D-RF1 | memory-architecture.md §1/§3.5 false-claim correction | Re-verified Tier-0 (`import graphiti_core` → ModuleNotFoundError; no `kuzu_db` on disk; consumer is a Protocol shim) then marked the S3 graphiti store DESIGN-ASPIRATIONAL-NOT-LIVE at every operative-presented site: §1 table S3 row + a marked note, §1 consumer-machinery line, §2 P1 line, §3.5 search line, §6 Lens-1 "already exists and is sealed" line. Marked-not-deleted (design intent preserved; running-shape corrected). | `a5946f3` | `ccfdc22` |

## §15. Backwards-compat verification

- Existing hands-off-lifecycle component tests pass (KP0/KP1/KP9 share its hook home).
- Existing `pos_session_start.py` service-health probing behaviour is preserved (KP7 ADDS a step, does not replace the health probe).
- Existing `translation-discipline` SKILL is unchanged (KP9 reuses its logic via extraction/import, does not mutate the SKILL).
- No sealed-component seal-test regresses (per-cycle seal-test green: hands-off-lifecycle = `test_cross_cutting.py` (frozen_baseline, H19); primary-persona + orchestrator = `test_no_sealed_amendments.py`).

## §16. Halt-and-surface findings (raised + ruled at plan-authoring)

- **F-1 — memory-architecture.md §1/§3.5 false graphiti-live claim.** RAISED (dispatch flagged it; Tier-0 confirmed it is real and more precisely a "presented-as-operative" claim, not a "sealed" claim). RULED: corrected in-plan (RF-1 + §9 doc-fix action); the plan assumes file-based-only reality throughout. No owner halt needed — the correction is doc-only and the dispatch pre-authorized it.
- **F-2 — amendment number / version not pre-allocated.** RAISED: STATE.md counter base is #148 but `docs/plans/` manifests already carry numbers up to 152 (in-flight/other-base). RULED: per `feedback_version_numbers_at_release_time`, the manifest's `amendment.number` is filled by the builder against the live counter at apply-time, not pre-baked here. No owner halt.
- **F-3 — all five owner forks already ruled.** RAISED: the dispatch carried five fork rulings (substrate, cadence, drift-autonomy, judge-gating, register-scope). RULED: all five encoded as Surfaces #1–#5 (closed, do-not-re-open). No owner halt; nothing left unrecommended.
- **F-4 — no NEW owner-ask surfaced by this plan.** The two genuine forks from design §6 are both resolved by the dispatch's rulings (register-scope = Surface #5; substrate = Surface #1). No new fork requires an owner ruling before the build. The build is dispatch-authorized once this plan + the four manifests are on disk.

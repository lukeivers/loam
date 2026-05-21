# Amendment #134 — FBM Tier 1 foundations (supersession marker + encoding-context + FIDRAFT cleanup + plan archive)

**Status:** plan-doc, plan-before-code. Authored 2026-05-21.
**Working directory:** `/Users/lukeivers/loam/`.
**Parent research artefact:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbm-end-to-end-rethink-v2-synthesized-2026-05-21.md` — the v2 design this plan implements (Tier 1, four scope-disjoint items).
**Predecessors (load-bearing):**
- `1a1f830` — M-FBM operational-health AC family seal (v0.1.x baseline for file-backed memory).
- canonical loam HEAD at plan-author time — BASELINE candidate; pinned at apply time.
**BASELINE (pre-build tip):** TBD — pinned in the manifest at apply time; the build agent records the SHA into §14 at apply.
**Quality bar:** four scope-disjoint AC families each verified by unit + the outcome-altitude smoke (`AC.FBMT1.S`); no method-in-AC; canonical loam component fence respected.

---

## §1. Objective / Summary / TL;DR

Ship **four scope-disjoint write-side / discipline primitives** that close the F-CONTRADICTION and F-WRITE-SIDE failure modes named in the v2 FBM rethink, and (subject to the in-flight F-ENCODING-CONTEXT-LOSS ruling that landed YES per TG 11804/11805) capture the encoding-context substrate that Tier 2 retrieval will later consume. Per Q2 owner ratification (TG 11808 + 11809), the four items ship as a **single multi-component amendment** rather than four serialized cycles.

The four primitives (each tiny — see §5 ACs for outcome shapes):

1. **T1.1 Supersession-marker frontmatter convention** (`AC.FBMT1.SUPM`) — a `superseded-by: <relative-path>` field on memory files; retrieval ranker applies a multiplicative penalty (recommended `0.1×`); file stays visible, just demoted. Mark-don't-delete per the v2 research's reading of Anderson & Green 2001.
2. **T1.2 Encoding-context capture at write-time** (`AC.FBMT1.ENCC`) — newly-written memory files carry a `context:` frontmatter block with the **minimal four-field set** (`triggering_msg_id`, `active_task_id`, `cwd`, `active_files`). Per owner-ratified schema-minimal directive (TG 11805), schema does NOT speculatively add fields against future hypothetical retrieval; lock-in is the failure mode this directive prevents.
3. **T1.3 FIDRAFT cleanup-on-seal** (`AC.FBMT1.FCS`) — a post-seal hook reads the seal commit's plan-doc, finds matching FIDRAFT entries by slug-overlap, and **surfaces a "did you mark this actioned?" prompt** to the operator. Owner-gated edit (never auto-rewrites FIDRAFT).
4. **T1.4 Amendment-plan archive-on-seal** (`AC.FBMT1.APS`) — `loam amend seal` moves the plan-doc + manifest from `docs/plans/` into `docs/plans/sealed/` as part of the seal commit; session-start "amendments-in-flight" surfaces then naturally show only unsealed plans.

Plus one outcome-altitude smoke (`AC.FBMT1.S`) that exercises all four in a single end-to-end synthetic flow.

**Per Q3 owner ratification (TG 11809):** both forward (T1.4 applies to new seals) AND **one-shot retroactive seed** (existing sealed-but-not-archived plan-docs in `docs/plans/` get a tagged sweep into `docs/plans/sealed/` as part of this amendment's plan-doc bookkeeping commit; see §9). The retroactive sweep is in-scope.

**Owner-ratification record (durable, recorded here per `feedback_record_owner_ratification_before_dispatch`):**

| msg-ID | ts (UTC) | Owner ruling |
|---|---|---|
| TG 11804 | 2026-05-21T16:10:07Z | Q1 = (a) keep T1.2 (F-ENCODING-CONTEXT-LOSS lands as a real failure mode). |
| TG 11805 | 2026-05-21T16:11:00Z | Schema-minimal caveat on T1.2 — keep fields to 3-4; do not speculatively expand. |
| TG 11807 | 2026-05-21T16:13:00Z | Q2 framed. |
| TG 11808 | 2026-05-21T16:14:01Z | "Trust you on build strategies" — build-strategy delegation ratified. |
| TG 11809 | 2026-05-21T16:15:00Z | Q2 = (b) parallel multi-component fence; Q3 = both forward + one-shot retroactive seed. |

**F2 Ruthless Feedback on scope realism (§10):** four primitives in a single multi-component fence is at the upper edge of what a single build agent can cleanly seal. The decomposition is in §6 (four AC families + one smoke; sequenced source-edit ladder) rather than a cycle-split, because the four items genuinely don't block each other and the build savings are real. If the build agent halts on fence-pressure mid-flight, the natural escape hatch is to seal T1.1+T1.2 first (memory schema cluster) then T1.3+T1.4 second (seal-time cluster). Documented in §8 halt triggers.

**Pre-flight verification (per `feedback_verify_fidraft_against_canonical_before_dispatch`):**

- `grep -rn 'superseded-by\|encoding.context.capture\|FIDRAFT.cleanup\|superseded_by' framework/ --include='*.py'` — only matches are test-fixture references to a historical AC3 supersedes marker (unrelated); **no T1.1/T1.2 implementation exists**.
- `git log --oneline --grep='superseded\|encoding-context\|FIDRAFT.cleanup' --all | head -20` — no seal commit for any T1 item.
- `ls framework/*/seals/ 2>/dev/null | grep -iE 'fbm|memory.system.t1|encoding'` — only `SEAL_COMMIT.m-fbm-operational-health` matches (that is the v0.1.x M-FBM file-based memory baseline, NOT a T1 implementation).

Pre-flight clean. Building forward is correct.

---

## §2. Predecessors / context

This amendment composes against:

- **Memory substrate** at `framework/primary-persona/src/loam/primary_persona/file_memory.py` + `memory_write_worker.py` + `memory_write_queue.py`. T1.1's ranker penalty extends the retrieval contributor; T1.2's frontmatter extends the worker's write path. M-FBM seal `1a1f830` is the baseline.
- **pos-amend tool** at `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py`. T1.4 extends the seal step to perform the plan-doc move; T1.3 hooks into the seal lifecycle (post-seal).
- **FIDRAFT** at `docs/FUTURE_IDEAS_DRAFT.md`. T1.3 reads this file at seal time.

---

## §3. Scope

### In-scope

- T1.1 supersession-marker convention + retrieval-ranker branch.
- T1.2 encoding-context frontmatter (minimal four-field schema only).
- T1.3 FIDRAFT cleanup-on-seal surfacing hook.
- T1.4 amendment-plan archive-on-seal (forward + retroactive sweep).
- The outcome-altitude smoke (`AC.FBMT1.S`) wiring up an end-to-end exercise.

### Out of scope (deferred)

- **Tier 2 retrieval mechanics** — B.1 co-citation graph + spreading activation; A.1 power-law base-level activation. Separate amendment (Tier 2 plan, not yet authored).
- **Tier 3 orchestration** — C.1 session-end consolidation + C.2 scheduled consolidation routine. Depends on Tier 1 + Tier 2 done first.
- **T2.3 pinned working set** — biggest behavioral change; deferred to a separate design conversation per Q4 (not yet ruled).
- **Speculative T1.2 schema expansion** — additional fields beyond the four-field minimum are explicitly out-of-scope per TG 11805. New fields require a future amendment with a named retrieval consumer.
- **Auto-edit of FIDRAFT by T1.3** — T1.3 surfaces only; the owner-gated edit is by design.
- **Memory-rule archive directory** (`~/.claude/projects/*/memory/archive/`) — the v1 rethink proposed it; v2 supersedes with the `superseded-by` marker. Mark-don't-delete makes archive unnecessary at this Tier.
- **Retroactive memory-rule supersedes annotation pass** — surfacing existing contradictions in the corpus (`principle_application_front_load_and_audit` vs newer refinements; `principle_self_reminder_at_end_of_turn` vs newer scoping) is a separate cleanup amendment. T1.1 ships the primitive; the cleanup pass uses it.

---

## §4. Acceptance criteria

AC IDs per `feedback_scope_descriptive_ac_ids` — scope-descriptive (FBMT1.*), NOT version-packed.

### AC.FBMT1.SUPM family — supersession-marker convention + ranker branch

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT1.SUPM.1** | Memory files carrying `superseded-by: <relative-path>` in YAML frontmatter parse without error; the value is exposed on the parsed memory-file representation. | Test loads a memory file with the field set, asserts the parsed representation carries the value as a string; loads a memory file without the field, asserts parsed representation reports `None` / absent. |
| **AC.FBMT1.SUPM.2** | Retrieval ranker observably demotes superseded memory files relative to non-superseded files of comparable content overlap. | Test constructs two memory files with comparable content; marks one `superseded-by`; runs the retrieval contributor against a query that lexically matches both; asserts the superseded file's final rank score is strictly less than the unsuperseded file's score (multiplicative penalty observable). |
| **AC.FBMT1.SUPM.3** | Superseded files are still returned (not filtered) when they fall above the score-threshold despite the penalty. | Test constructs a superseded memory file with very high lexical-match score against a query; asserts the file IS in the returned candidate set (just demoted), not filtered out. |
| **AC.FBMT1.SUPM.4** | A `superseded-by:` value pointing at a non-existent file is a soft error (logged; ranker still applies penalty; not a crash). | Test sets the field to a path that doesn't exist; asserts retrieval still runs to completion; asserts a warning is observable in the diagnostic surface. |

### AC.FBMT1.ENCC family — encoding-context capture at write-time

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT1.ENCC.1** | New memory writes (via the memory-write worker's drain path) emit a `context:` frontmatter block containing **exactly the four named fields**: `triggering_msg_id`, `active_task_id`, `cwd`, `active_files`. | Test drives a queue entry through the worker; reads the resulting memory file; asserts the YAML frontmatter contains a `context:` key with exactly those four keys (no more, no less). |
| **AC.FBMT1.ENCC.2** | The four fields carry values when the worker's input carries them; carry `null` (and the YAML field is still present) when the input does not. | Test enqueues entries with and without each field set; asserts on-disk frontmatter reflects input or `null` as appropriate. |
| **AC.FBMT1.ENCC.3** | `active_files` is a list of relative paths (zero or more); the schema rejects non-list inputs. | Test enqueues an entry with `active_files` as a string; asserts the worker logs a schema-validation error and either coerces to a single-element list or surfaces the validation failure (builder's call which). |
| **AC.FBMT1.ENCC.4** | Existing memory files written by the M-FBM worker (pre-amendment) are still readable by the retrieval contributor and the FileMemoryStore — backwards-compat verification. | Test loads a memory file that has no `context:` block (pre-amendment shape); asserts the retrieval contributor returns it without error; asserts the parsed representation reports `context = None` or empty. |

### AC.FBMT1.FCS family — FIDRAFT cleanup-on-seal surfacing hook

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT1.FCS.1** | After `loam amend seal` completes successfully, a process reads the just-sealed plan-doc, scans `docs/FUTURE_IDEAS_DRAFT.md` for entries whose slug-overlap with the plan-doc's slug exceeds the confidence threshold, and emits a structured surfacing payload (NOT a file edit). | Test seals a synthetic amendment whose plan-doc slug matches a FIDRAFT entry; asserts the post-seal surface (stdout / NDJSON / Telegram-reply payload — builder's call) names the matching FIDRAFT entry and asks "did you mark this actioned?" |
| **AC.FBMT1.FCS.2** | The hook never writes to `docs/FUTURE_IDEAS_DRAFT.md`. | Test captures the SHA + mtime of `docs/FUTURE_IDEAS_DRAFT.md` before sealing; asserts they are unchanged after the hook fires. |
| **AC.FBMT1.FCS.3** | Zero false-positive surfacing when the seal commit's plan-doc has no FIDRAFT match (slug-overlap below threshold for every entry). | Test seals an amendment whose plan-doc slug is invented (e.g. `zzz-no-fidraft-match-zzz`) and asserts no FIDRAFT-cleanup surface fires. |
| **AC.FBMT1.FCS.4** | The hook is skippable via a flag for emergency seals where the operator wants to bypass. | Test seals with `--skip-fidraft-cleanup` (or equivalent flag — exact name builder's call); asserts the hook does not fire. |

### AC.FBMT1.APS family — amendment-plan archive-on-seal

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT1.APS.1** | After `loam amend seal` completes for an amendment whose manifest's `plan:` points at `docs/plans/<slug>.md`, the plan-doc + manifest YAML are at `docs/plans/sealed/<slug>.md` + `docs/plans/sealed/<slug>.manifest.yaml`, and the seal commit includes the rename. | Test seals a synthetic amendment; asserts `docs/plans/<slug>.md` no longer exists in the worktree; asserts `docs/plans/sealed/<slug>.md` exists; asserts `git log -- docs/plans/sealed/<slug>.md` shows the rename in the seal commit (not a separate later commit). |
| **AC.FBMT1.APS.2** | The plan-doc's internal cross-references (other plan-docs, doc paths) remain functional — the move does not break content. | Test reads the moved plan-doc; asserts the content body is byte-identical to the pre-move version; asserts any internal links to `docs/plans/<other-slug>.md` are still valid relative paths from the new `docs/plans/sealed/` location (or have been path-adjusted — builder's call which). |
| **AC.FBMT1.APS.3** | The retroactive one-shot sweep (per Q3 ratification) moves every already-sealed plan-doc (every plan-doc whose corresponding seal commit exists in the git log) into `docs/plans/sealed/` as part of this amendment's bookkeeping commit; in-flight plan-docs (no seal commit found) stay in `docs/plans/`. | Test runs the retroactive sweep against a tmpfs git repo with a mix of sealed + in-flight plan-docs; asserts only sealed plan-docs moved; asserts in-flight ones remain in `docs/plans/`. |
| **AC.FBMT1.APS.4** | Session-start "amendments-in-flight" contributor reads `docs/plans/` directly (not `docs/plans/sealed/`), and therefore naturally lists only unsealed plans after T1.4 ships. | Test runs the session-start contributor against a worktree with 5 in-flight plan-docs in `docs/plans/` and 50 sealed in `docs/plans/sealed/`; asserts the surface lists exactly 5. |

### AC.FBMT1.S — outcome-altitude smoke (single end-to-end exercise)

**Marked `outcome-altitude: true` per `feedback_test_outcome_altitude_required`.** Invokes the production code paths with no pre-arranged state; verifies all four behaviors in one synthetic flow.

| ID | Outcome | Verification |
|---|---|---|
| **AC.FBMT1.S** | A single test exercises: (a) write a memory file via the worker — verify `context:` block present (T1.2); (b) write a second memory file with `superseded-by:` pointing at the first — verify the retrieval ranker demotes the second (T1.1); (c) seal a synthetic amendment in a tmpfs repo where the plan-doc slug overlaps a seeded FIDRAFT entry — verify the cleanup hook fires its surface (T1.3); (d) verify the plan-doc moved from `docs/plans/` to `docs/plans/sealed/` in the seal commit (T1.4). | The test invokes the production memory-write worker, the production retrieval contributor, the production `loam amend seal` CLI, and the production FIDRAFT cleanup hook in sequence; no pre-arranged state beyond the synthetic memory files and the synthetic plan-doc + manifest at test setup. All four assertions land green. |

---

## §5. Sealed-component fence (multi-component)

**Components touched:**

- `framework/primary-persona/` — file-memory frontmatter schema (`file_memory.py`), retrieval-contributor ranker branch (`file_memory.py` or sibling), memory-write worker schema-emit (`memory_write_worker.py`). T1.1 + T1.2 land here.
- `plugins/dev-sdlc/tools/loam-amend/` — `loam amend seal` extension for plan-doc archive (`commands/seal.py`); FIDRAFT cleanup hook composed into the seal lifecycle (`commands/seal.py` or new sibling). T1.3 + T1.4 land here.

**Universal admissions** (per amendment #22 ruling #3):

- `docs/plans/` prefix (this plan-doc, manifest, and the retroactive-sweep moves of sealed plan-docs).
- `docs/FUTURE_IDEAS_DRAFT.md` — explicitly NOT modified by T1.3 (AC.FBMT1.FCS.2 forbids it); admitted in the universal paths because the retroactive sweep may incidentally trigger a graduation pass.
- `docs/STATE.md` — bookkeeping update (§9).

**Out of fence (halt-and-surface trigger):**

- Any other component under `framework/` or `plugins/`.
- Any edit to `docs/spec/` (objectives spec; outside any cycle's fence per persona instructions).

**Halt-and-surface finding on fence correction (per `feedback_subagent_odd_violation_halt`):** The dispatching brief named `framework/memory-system/` and `framework/pos-amend/` as the fence. Canonical loam does not have those components — the memory implementation lives inside `framework/primary-persona/` (per `docs/components/memory.md`: "The memory component is documented under its own `docs/components/memory.md` because it is a load-bearing user-facing contract; the implementation lives inside the `primary-persona` component… There is no separate `framework/memory/` directory.") and the pos-amend tool lives at `plugins/dev-sdlc/tools/loam-amend/`. **The corrected fence is the one named above.** Recorded in §16 finding #1.

---

## §6. Build steps (multi-component, single cycle)

**Sequencing within the cycle.** The four items are scope-disjoint, but the source edits are sequenced for clean commit ladders + clean test runs. The builder's call per ODD §1.1.

1. **Plan-doc lands** (this file) + manifest YAML.
2. **Source edits — primary-persona cluster (T1.1 + T1.2):**
   - `framework/primary-persona/src/loam/primary_persona/file_memory.py` — extend the memory-file YAML frontmatter parser to recognize `superseded-by` + `context:` blocks; extend the retrieval-ranker scoring to apply the multiplicative penalty when `superseded-by` is present.
   - `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py` — extend the write path to emit the `context:` block with the four named fields; default to `null` when the queue entry doesn't carry a value.
   - `framework/primary-persona/src/loam/primary_persona/memory_write_queue.py` — extend the queue entry schema to carry the four context fields (so the worker can read them on drain).
3. **Tests authored — T1.1 + T1.2:**
   - `framework/primary-persona/tests/test_AC_FBMT1_SUPM_1_frontmatter_parses.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_SUPM_2_ranker_demotes.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_SUPM_3_not_filtered.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_SUPM_4_missing_path_soft_error.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_ENCC_1_four_field_emit.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_ENCC_2_null_when_absent.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_ENCC_3_active_files_list_shape.py`
   - `framework/primary-persona/tests/test_AC_FBMT1_ENCC_4_backwards_compat.py`
4. **Source edits — loam-amend cluster (T1.3 + T1.4):**
   - `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — extend the seal step to perform the plan-doc + manifest move into `docs/plans/sealed/` as part of the deterministic seal commit; add the `--skip-fidraft-cleanup` flag wiring; invoke the FIDRAFT cleanup hook post-commit.
   - `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/` — new module (e.g. `fidraft_cleanup.py`) implementing the slug-overlap match heuristic and the surfacing payload emission.
5. **Tests authored — T1.3 + T1.4:**
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_FCS_1_post_seal_surface_fires.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_FCS_2_no_fidraft_write.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_FCS_3_no_false_positive.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_FCS_4_skip_flag.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_1_plan_doc_moved.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_2_content_unchanged.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_3_retroactive_sweep.py`
   - `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_FBMT1_APS_4_session_start_in_flight.py`
6. **Outcome-altitude smoke:**
   - `framework/primary-persona/tests/test_AC_FBMT1_S_end_to_end_smoke.py` (or `plugins/dev-sdlc/tools/loam-amend/tests/` — builder's call which component owns the smoke; it crosses the fence by design).
7. **Touched-tests run** (only the new tests + their existing-component tests under `framework/primary-persona/tests/` and `plugins/dev-sdlc/tools/loam-amend/tests/`).
8. **One-shot retroactive sweep (per Q3):** the build agent runs a script that walks `docs/plans/*.md`, identifies which have corresponding seal commits in the git log, and `git mv`s those into `docs/plans/sealed/`. This is one bookkeeping commit, BEFORE `loam amend apply`, so the apply step's seal-diff window sees a clean fence. The retroactive sweep is in-scope per Q3 owner ratification; the script itself is ephemeral (not landed as production code) — its outcome IS the commit.
9. **`loam amend apply`** — auto-commit lands per v0.1.2 ergonomics.
10. **`loam amend seal`** — deterministic seal commit; this seal is itself the **first user of T1.4** (the plan-doc archives itself on seal, eating its own dog food).
11. **Smoke (D1 cold-state):** fresh workspace → memory write emits `context:` block; second write with `superseded-by:` ranks below first; seal of a synthetic amendment archives plan-doc + fires FIDRAFT surface.

---

## §7. Ship shape

**Single cycle, multi-component.** No sub-amendment series. The four AC families ship under one manifest + one apply commit + one seal commit. The retroactive sweep is one bookkeeping commit prior to apply.

**Commit ladder (expected):**

1. plan-doc + manifest commit (this file).
2. Retroactive sweep commit — `docs(plans): one-shot retroactive sweep of sealed plan-docs to docs/plans/sealed/ — per amendment #134 §6 Q3 ratification`.
3. Source-edits commit — `feat(primary-persona, loam-amend): FBM Tier 1 foundations (T1.1 supersession-marker + T1.2 encoding-context + T1.3 FIDRAFT cleanup-on-seal + T1.4 amendment-plan archive-on-seal)`.
4. `loam amend apply` auto-commit.
5. `loam amend seal` deterministic seal commit (this commit DOES the T1.4 move on itself).

---

## §8. Halt triggers (in-flight)

- WD drifts (anything other than `/Users/lukeivers/loam`) → halt + surface.
- Any source edit outside the two-component fence → halt + surface.
- Any AC ships partial → halt + reframe; do NOT seal partial.
- Outcome-altitude smoke `AC.FBMT1.S` fails after all unit ACs green → halt + investigate; the unit tests passing without the smoke is a known method-in-AC red flag.
- T1.4's "seal commit includes the move" requirement turns out to require a structural change to the seal commit's deterministic-content invariant — halt + surface (T1.4 may need to be a separate follow-up commit rather than embedded in the seal commit; the v2 plan calls for embedded, but ODD §1.1 leaves method as builder's call).
- The retroactive sweep finds a plan-doc whose seal-commit attribution is ambiguous (multiple commits touch it, none clearly "the seal") — halt + surface that plan-doc, leave it in `docs/plans/` for human review.
- The slug-overlap confidence threshold for T1.3 turns out unauthorable cleanly (every reasonable threshold either over- or under-fires on the test corpus) — halt + surface; recommend per §14 D-T1.3.MATCH alternative.
- Fence-pressure: build agent finds it cannot cleanly seal all four in one cycle and surfaces the natural split (T1.1+T1.2 first, T1.3+T1.4 second) per §1 F2-RF note → halt + surface to dispatcher; this is the documented escape hatch.

---

## §9. Bookkeeping

- `loam amend apply` (NOT `git commit --amend`; per `feedback_no_amend_in_agent_dispatches`).
- One semantic commit per ladder step (see §7).
- Update `docs/STATE.md` with the amendment #134 row.
- §14 method-decision register populated by the builder.
- §14 SHA backfill via `loam amend seal --plan-doc docs/plans/amendment-134-fbm-tier1-foundations.md` (which, post-T1.4, will land at `docs/plans/sealed/amendment-134-fbm-tier1-foundations.md`).
- The retroactive sweep (§6 step 8) is itself a bookkeeping commit; the script is ephemeral.

---

## §10. F2 Ruthless Feedback (honest doubts)

Four named doubts on this plan, surfaced per `feedback_ruthless_feedback`:

1. **Fence size.** Four primitives in a single cycle is at the upper bound of clean-sealability. The natural split (T1.1+T1.2 memory cluster, then T1.3+T1.4 seal-time cluster) is documented as the in-flight escape hatch in §8, but the persona dispatching this build should weigh whether to pre-split it. The reason I recommend single-cycle: the four items are genuinely independent at the code level, and the build savings from one apply/seal cycle vs two are real (~30-40% of total build time). Owner ratified single-cycle in Q2 (TG 11809), so the recommendation is to ship single-cycle and let the in-flight halt fire if the builder discovers fence-pressure.

2. **T1.3's slug-overlap heuristic.** Slug-overlap is the obvious first cut but is brittle: a FIDRAFT entry titled "Add FIDRAFT cleanup-on-seal hook" and a plan-doc slug `amendment-134-fbm-tier1-foundations` won't overlap on slug tokens (the entry talks about THIS amendment but uses different words). The recommendation in §14 D-T1.3.MATCH is slug-overlap with **a confidence threshold loose enough to fire surfacing prompts liberally** — operator triages out the false positives. Alternative is full-text similarity (more accurate, more invasive — needs embedding or sklearn dep). The owner-gated surfacing means false positives are cheap; false negatives are the expensive failure mode. Loose threshold is correct for this shape.

3. **T1.4 embedded in seal commit vs follow-up commit.** The plan calls for the rename to be IN the seal commit. The seal commit today is deterministic (specific content invariant); embedding the rename may require a structural change to that invariant. The builder may find that a follow-up commit (immediately after seal, same atomic flow) is cleaner. §8 halt trigger covers this case; the seal commit's deterministic-content invariant is the test.

4. **F-ENCODING-CONTEXT-LOSS is still hypothesis-class.** Q1 ruled YES on keeping T1.2, but the failure mode itself has no concrete forensic-evidence smoking gun in the corpus (per the v2 artifact, this was an "agent-surfaced candidate" with no observed-failure-instance count). T1.2 is small (~10 LOC), so the cost of shipping it on a hypothesis is low; the cost of shipping it and NOT having a retrieval consumer for the captured fields is the schema-lock-in failure mode TG 11805 explicitly named. The schema-minimal directive mitigates this. The four-field minimum IS minimal; the verification is in §5 AC.FBMT1.ENCC.1 ("exactly the four named fields").

---

## §14. Method-decision register

**Ratification table (recorded at plan-doc commit time, per `feedback_record_owner_ratification_before_dispatch`):**

| Decision | Recommendation | Ratified by | Authority |
|----------|----------------|-------------|-----------|
| D-T1.2.SCHEMA | minimal 4-field set (`triggering_msg_id`, `active_task_id`, `cwd`, `active_files`) | persona (Example) | Owner build-strategy delegation TG 11808 + schema-minimal directive TG 11805 |
| D-T1.1.PENALTY | `0.1×` multiplicative penalty, hard-coded at v0.1 | persona (Example) | Owner build-strategy delegation TG 11808 |
| D-T1.3.MATCH | slug-overlap, ~30% token threshold, owner-gated surface | persona (Example) | Owner build-strategy delegation TG 11808 |
| D-T1.4.DIR | `docs/plans/sealed/` sibling directory | persona (Example) | Owner build-strategy delegation TG 11808 |

Ratification rationale: owner's TG 11808 explicitly delegated build-strategy decisions to the persona ("trust you on build strategies; happy to provide input if you're not confident"). All four §14 decisions are build-strategy detail (penalty value, threshold value, directory location, schema field set). Persona confident on all four per the plan-author's rationale below; no owner escalation needed.

Populated at build time + sealed in by `loam amend seal --plan-doc`. The four method-decisions named here at plan-time:

### D-T1.2.SCHEMA — Encoding-context field set

**Decision (recommendation):** minimal four-field set per TG 11805 schema-minimal ratification:

- `triggering_msg_id` — the inbound message-ID that triggered this memory-write turn (Telegram msg-ID where available; null for non-Telegram triggers like CLI invocations).
- `active_task_id` — the persona's task-tracker task ID currently in flight at write-time (null when no task is active).
- `cwd` — the working directory of the persona at write-time (string path).
- `active_files` — list of files the persona had open / Read recently at write-time (zero or more relative paths from `cwd`).

**Rationale per field:** triggering_msg_id is the encoding cue (Tulving 1973 encoding-specificity — match retrieval on the original triggering input); active_task_id is the task-scoped retrieval cue (memories written during task T are more relevant to future task-T continuations); cwd is the spatial cue (memories written from project A are project-A relevant); active_files is the document-context cue (cross-file association).

**Alternatives weighed:** (a) larger field set (active_persona, active_agent_chain, parent_task_id, …) — rejected per schema-lock-in directive; (b) minimal two-field set (triggering_msg_id + cwd) — rejected as under-cued for task-scoped retrieval.

### D-T1.1.PENALTY — Ranker multiplicative penalty value

**Decision (recommendation):** `0.1×` multiplicative penalty applied to superseded files at the final-rank-score step, per the v2 research's anchoring on "mark, don't delete" (Anderson & Green 2001 partial-fit transferred).

**Rationale:** `0.1×` keeps superseded files visible in the candidate set when their content match is strong (a `score=10` superseded file beats a `score=0.5` unsuperseded file), but demotes them below every comparably-scored unsuperseded file. Aligns with the mark-not-delete framing.

**Alternative:** configurable via env var or config-file. **Recommendation:** ship as hard-coded `0.1` at v0.1; expose configurability only when a concrete tuning request lands.

### D-T1.3.MATCH — FIDRAFT slug-overlap heuristic + threshold

**Decision (recommendation):** slug-overlap with **loose threshold (~30% token overlap between plan-doc slug tokens and FIDRAFT-entry slug/title tokens)**. Tokenization splits on `-`, `_`, whitespace; lowercased; stopwords (`amendment`, `the`, `a`, etc.) removed. The hook surfaces ALL entries above threshold, ranked; the operator triages.

**Rationale:** loose threshold optimizes for the cheap-false-positive / expensive-false-negative cost asymmetry (per §10 F2-RF doubt #2). The owner-gated surface means a false positive costs one "no, that's not it" click; a false negative leaves FIDRAFT stale (the very failure mode this AC family closes).

**Alternative:** full-text similarity (embedding or sklearn TF-IDF). **Recommendation:** defer until evidence of slug-overlap being insufficient lands. Slug-overlap has zero dependency cost.

### D-T1.4.DIR — Sealed plan-doc directory location

**Decision (recommendation):** `docs/plans/sealed/` — sibling to in-flight plans, NOT per-component.

**Rationale:** plan-docs are universal admissions (per amendment #22 ruling #3); they don't live under any single component's fence. A sibling sealed/ directory matches the conceptual model (a flat list of all plans, sealed-or-not, partitioned only by status). Per-component would fragment cross-component amendments like this one across multiple sealed/ subdirs.

**Alternative:** per-component `framework/<comp>/seals/plans/`. **Recommendation:** rejected — fragments multi-component plans.

---

## §15. Backwards-compat verification

Tests that must still pass after this amendment seals:

- All existing tests under `framework/primary-persona/tests/` — memory-write worker + retrieval contributor + file-memory store. Specifically the M-FBM family (`AC.MFBM.*`) and the J family (`AC.J.*`).
- All existing tests under `plugins/dev-sdlc/tools/loam-amend/tests/` — seal command (`test_seal.py`), apply (`test_AC_D_1_5_3_dry_run_reports.py`, et al.), baseline, narrative.
- `AC.FBMT1.ENCC.4` explicitly verifies pre-amendment memory files (without `context:`) still parse and retrieve cleanly.
- The retroactive sweep MUST NOT break session-start contributors. `AC.FBMT1.APS.4` verifies the contributor returns the right count after the sweep.

---

## §16. Halt-and-surface findings

### Finding #1 (no halt — fence corrected at plan-author time)

**Surface:** the dispatching brief named `framework/memory-system/` and `framework/pos-amend/` as the component fence. Canonical loam has neither component. Per `docs/components/memory.md` and `framework/primary-persona/src/loam/primary_persona/{file_memory,memory_write_worker,memory_write_queue,stop_emitter}.py`, the file-based memory implementation lives inside `framework/primary-persona/`. Per `plugins/dev-sdlc/tools/loam-amend/`, the pos-amend tool is a dev-sdlc plugin tool, not a top-level framework component.

**Resolution (autonomous, plan-author):** corrected fence to `framework/primary-persona/` + `plugins/dev-sdlc/tools/loam-amend/`. Recorded in §5. T1.3 placement (which the brief framed as "framework/primary-persona/ or a new sub-component") resolves cleanly to `plugins/dev-sdlc/tools/loam-amend/` per the partition rule: a post-seal hook composed into `loam amend seal` is dev-sdlc-tool scope.

**Why this is not a halt-and-surface back to dispatcher:** the fence correction is a Tier-0-verified factual reading of canonical loam against the dispatching brief's claim. The dispatch's named ACs and intent are unaffected; the only change is which directory the source edits land in. Per `feedback_test_against_operational_objective_before_escalating`, the operational objective (ship the four T1 primitives) implies a clear answer (use the components where the relevant code actually lives), so this is autonomous correction not owner-escalation.

### Finding #2 (no halt — schema-minimal directive baked into §5 ACs)

**Surface:** TG 11805 ratified a schema-minimal directive on T1.2: do not speculatively add fields against future hypothetical retrieval. The natural failure mode is the plan-author or builder expanding the schema "while we're in there" (`session_id`, `parent_task_id`, `active_persona`, `agent_chain`, …).

**Resolution (autonomous, plan-author):** §5 AC.FBMT1.ENCC.1 verifies **exactly** the four named fields — adding a fifth field IS a test failure. This structurally enforces the schema-minimal directive at build time.

### Finding #3 (no halt — retroactive sweep scoped correctly)

**Surface:** Q3 ratified BOTH forward AND one-shot retroactive seed. The retroactive sweep is ambiguous on edge cases: plan-docs with no clear single seal commit, plan-docs that are research artifacts not amendments, plan-docs that pre-date the seal-commit convention.

**Resolution (autonomous, plan-author):** §6 step 8 + §8 halt trigger #5 cover this. The sweep moves only plan-docs with a clearly-attributable seal commit; ambiguous ones halt-and-surface for human review.

### Finding #4 (no halt — F-ENCODING is still hypothesis-class)

**Surface:** TG 11804 ruled YES on F-ENCODING-CONTEXT-LOSS as a real failure mode, but the v2 artifact itself flags it as "agent-surfaced candidate; owner ruling pending" with no concrete forensic evidence. T1.2 ships on hypothesis-class evidence + schema-minimal directive.

**Resolution (autonomous, plan-author):** §10 F2-RF doubt #4 names this explicitly; the schema-minimal directive (§16 finding #2) bounds the cost. T1.2 ships per owner ratification; future evidence of F-ENCODING firing in operation will inform whether the schema needs expansion.

---

## §17. Composition (M5 derivation line)

- **Composes with** `feedback_verify_fidraft_against_canonical_before_dispatch` — T1.3 is the structural cure for the dispatch-discipline rule the FIDRAFT case taught us; pre-flight in §1 follows that rule.
- **Composes with** `feedback_record_owner_ratification_before_dispatch` — §1 owner-ratification table makes the five msg-IDs Tier-0-verifiable durable artifact.
- **Composes with** `feedback_scope_descriptive_ac_ids` — AC.FBMT1.* are scope-descriptive; no version-packing.
- **Composes with** `feedback_version_numbers_at_release_time` — no version number assigned at plan-author time; version derives when this amendment publishes.
- **Composes with** `feedback_subagent_odd_violation_halt` — Finding #1 (fence correction) is the surfaced ODD violation in the dispatching brief, autonomously corrected per the operational-objective test.
- **Independent of** F4 (scope-confidence) — discipline-scope work, not prompt-scope work.
- **Supersedes** the v1 FBM rethink's Tier 1 framing (which proposed memory-rule supersedes-annotation + archive directory; v2 supersedes with mark-don't-delete + no archive).

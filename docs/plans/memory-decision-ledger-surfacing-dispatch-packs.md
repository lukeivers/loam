# MEMORY RECALL CYCLE — decision ledger + surfacing rebuild + dispatch memory packs + decision-claim guard

**Status:** sub-plan-doc, **OWNER-RATIFIED 2026-06-09 — build authorized.** Summary okayed + **D2 ruled (a)** — persona writes the ledger record at ruling time, deterministic steer-on-miss — by Luke (Discord msg 1514065518493958214, 2026-06-09 19:35 CDT, answer "1. Agree with you" to the D2 question delivered at Discord msg 1514060265568735313). Builds serialize in this tree; the predecessor FBM-correctness cycle is SEALED-LOCAL (apply commit `3b060f14`, all three SEAL_COMMIT sidecars verified 2026-06-09) so the serialization constraint is already satisfied — dispatch on ratification. · **Date:** 2026-06-09
**WD:** `/Users/lukeivers/loam` (canonical loam)
**Parent / motivating artefacts:** the owner's verbatim objective (Telegram, 2026-06-09): *"I don't want to ever catch you unprepared with the latest information, full context, etc on anything that I ask. Just by me asking, it should load up everything related, and focus on the components that are most related to the prompt I sent in."* Reconciled from the A/B north-star pair per the dispatcher's comparison + ratified merge weighting: `pos3/workspace/.scratch/claude-output/memory-northstar-plan-A.md` (Fable — empiricist, live-probed), `…-plan-B.md` (Opus — theorist, tier framing), `…-ab-comparison-2026-06-09.md` (merge spine: convergent core + A's mechanisms + B's narrative + the anachronism exclusion).

---

## OWNER SUMMARY (rule from this — full detail below)

1. **What this is:** the single merged build plan from the two memory plans you A/B-tested. Both independently landed on the same core; this is the one contract, weighted toward the plan that verified its claims (A), framed by the other's clearest idea (B): the build this week was the *guard* (stops me stating false things); this cycle is the *recall* (loads the right things before I start).
2. **The one new thing — a decision ledger.** Every ruling you make gets written down at the moment you make it, as a small record carrying the names, the decision, and the why. Asking about a topic then loads the ruling whole — number AND reasoning — before I draft a word. The $750k Tilth ruling was unfindable because it was never written as a decision, only as chat.
3. **Three repairs to what exists:** (a) your June-7 measurement ruled the memory-association layer makes retrieval worse on every metric — it's still running; deleting it is a measured ~2× quality win sitting on the floor; (b) the memory I'm shown each turn is 1,200 characters of truncated pointers with the file paths stripped — it becomes ~5KB of substantive lines with paths, and decision records get injected whole; (c) background agents currently receive zero memory — the already-built dispatch-context carrier gets relevant rulings packed into every agent's briefing.
4. **Backstop:** the claim guard sealed this week learns decision claims too — if I'm about to say "we never decided X" and the ledger says we did, I get corrected with the ruling before the words reach you.
5. **Both June-9 failures become standing automated tests** — the $750k ruling must load when Tilth comes up; "the migration isn't planned" must get caught — and they run on every future memory change forever.
6. **One call I need from you (D2):** who writes the ledger record — I write it at ruling time and a deterministic check nags me next turn if I miss (recommended — I have the context, the record carries the right names), versus auto-extracting records from the conversation (cheaper-feeling, riskier records).
7. **Cost:** ~2.5–4.5 hours of agent build time across five sequenced steps, each with a pass/fail measurement. Stops three standing burdens: hand-maintained status prose, tending the dead association machinery, and re-litigating settled rulings.
8. **Status:** RATIFIED (D2 = (a), Discord 1514065518) — build dispatched 2026-06-09.

---

## Header detail

**Predecessors (load-bearing prior seals, Tier-0 verified on disk + git 2026-06-09):**
- **FBM-correctness cycle (the GUARD tier — sealed-local this session)** — slice commits `6f7deb1f` (plan-state index, AC.PSI.\*), `10776ee5` (claim guard, AC.CLG.\*), `7f163755` (supersession, AC.SUP.\*); apply `3b060f14`; all three SEAL_COMMIT sidecars read = `3b060f14`. Delivered surfaces this cycle CONSUMES, never re-implements: `keep_pace/plans_state.py` (321 lines), `supersession.py` (148 lines), the claim-guard layer on the KP9 draft-gate. **This plan is the RECALL tier on top of that guard tier (B's framing, adopted as the cycle's narrative).**
- **Frame-kernel SubagentStart auto-context bundle (sealed `69e28416`)** — `framework/frame-kernel/src/loam/frame_kernel/bundle.py`: three-tier dispatch bundle (microkernel / workstream / MEMORY), memory tier reusing the persona's sealed retrieval surface via `mcp_memory_client` → `memory_consumer._render_retrieval`. **The natural carrier for dispatch memory packs — verified built + sealed but NOT yet registered in any live `settings.json`** (grep of `~/.claude/settings.json` + `pos3/.claude/settings.json`: zero subagent entries; the fragment at `framework/frame-kernel/hooks/settings.fragment.json` is explicitly staged-not-live, dispatcher-timed).
- **Workspace-sync settings-fragment auto-composer (sealed `45cdf973`, 2026-06-08)** — discovers every `framework/*/hooks/**/settings.fragment.json` on a successful pos-sync and composes the hooks blocks into the workspace's `.claude/settings.json` additively/idempotently. **The frame-kernel fragment's "workspace-sync does NOT auto-compose fragments today" comment is now STALE — RF-1 is closed; activation rides the next pos-sync** (or `--no-compose` defers it).
- **The June-7 eval verdict (UNEXECUTED — this cycle executes it)** — `pos3/workspace/.scratch/claude-output/fbm-eval-results-2026-06-07.md`, re-read this session: spread → KILL (recall@10 −12% rel, precision@10 −15% rel, MRR −0.035, latency 58→116ms; phrasing-mismatch recall 0.0000→0.0000); activation → FIX-not-kill (BM25-floor beats live ranker ~2×: recall@10 0.0727 vs 0.0373, MRR 0.8059 vs 0.5887, miss@10 0.055 vs 0.267). **Verified live this session: `file_memory.py:~1545` still builds the co-citation graph inside `_compose_score_and_spread` on every search** (`cocitation_graph.py` = 429 lines).
- **The surfacing throttles (verified in source this session)** — `keep_pace/retrieval.py`: `INJECTION_CHAR_CAP = 1200`, `_EPISODE_POINTER_CAP = 160`, and `_render_injection`'s "plain English, NO file paths" rule (a KP9 Cycle-3 lint applied to MODEL-facing context — scope error). **Second render path found during this reconciliation (named in neither A nor B):** `memory_consumer.py` (`MEMORY_RETRIEVAL_CHAR_CAP = 1600`, `_render_retrieval`) is what the frame-kernel bundle uses — the surfacing rebuild must cover BOTH paths or dispatch packs inherit the old render.
- **Episode-store machinery reused (never rebuilt)** — `file_memory.py:477 write_episode` (frontmatter'd markdown, atomic write, encoding-context block) — decision records are an episode-adjacent structured record reusing this orbit; `stop_emitter.py` (`handle_stop_envelope`, `cli_stop`) — the turn-close seam the ruling detector extends.

**BASELINE candidate:** walked at apply-time per the #142 baseline-walk pattern (`baseline: null` in the draft manifest). At authoring time the tree tip is `3b060f14` with the correctness cycle's sealed-plan renames pending commit — the walk starts from whatever commit carries this plan.
**Components:** three, all sealed, all additive — `primary-persona` (Slices 1–3) + `frame-kernel` (Slice 4) + `hands-off-lifecycle` (Slice 5). One amendment, five sequenced slices (D4).
**Status-file target:** `docs/STATE.md` + FBM roadmap backfill (§9).
**Quality bar:** ODD §2.5 — every AC outcome-shape, method-in-AC test passed on each; ≥1 outcome-altitude AC per family (production entry points, no pre-arranged state); no LLM/API call in any hot path (`feedback_no_anthropic_api_key`; all per-turn/per-send/per-dispatch detection is deterministic).

---

## §1 Summary / TL;DR

**What ships — the recall tier:** (1) a **decision ledger** — owner rulings as first-class structured records (entities + aliases, question, ruling, reasoning, source pointer, workstream, status) written at ruling time into the workspace memory tree, indexed into unified retrieval, with a deterministic turn-close steer when a ruling-shaped turn produced no record and a session-start catch-up sweep; (2) a **surfacing rebuild** — model-facing memory injection carries file paths, substantive pointer text (never channel-envelope/notification junk), a ~5KB-class budget, and WHOLE-record injection for structured hits, on BOTH render paths (per-turn keep-pace + the dispatch-bundle memory tier); (3) **eval-verdict execution** — the June-7 measured KILL of the co-citation spread finally lands (delete), and power-law activation neutralizes to 1.0 behind a default-off flag (FIX-not-kill, per the eval's own caveat); (4) **dispatch memory packs** — the sealed frame-kernel SubagentStart bundle becomes decision-aware (relevant ledger records injected whole into every dispatched agent's context) and its staged hooks fragment activates via the sealed auto-composer, closing the agents-are-memory-blind-by-construction hole; (5) **decision-claim guard** — the sealed claim guard's ground truth widens to the ledger, so "X is open / we never decided X" drafts get steered with the ruling's evidence.

**The failures this kills (2026-06-09, live, owner-caught):** the $750k Tilth ruling was unretrievable by construction (the deciding turn contains neither "Tilth" nor "750" — write-side gap), invisible even when retrievable (1,200-char path-less pointer injection), and absent from the planning agent's context (dispatch blindness) — three legs, Slices 3/2/4 respectively. The "unplanned migration" failure is closed by the sealed guard tier; Slice 5 extends the same protection to decision-state claims. **Both failures become standing in-tree regression tests via the OA ACs** (B's standing-regression idea, delivered structurally — OA tests ride along on every future seal by construction).

**AC families:** `AC.EVX.*` (eval-verdict execution), `AC.SRF.*` (surfacing), `AC.DLG.*` (decision ledger), `AC.DMP.*` (dispatch memory packs), `AC.DCG.*` (decision-claim guard) — each with its own outcome-altitude AC.

**Key decisions baked (full list + recommendations in §3):** merge weighting per the ratified comparison, anachronism excluded (D1); ledger write authority = persona-writes + deterministic steer-on-miss (D2 ★ — the one owner call); dispatch packs ride the sealed frame-kernel carrier, NOT a new pack CLI (D3 — named deviation from Plan A, Tier-0 grounded); one amendment, five slices, A's ordering (D4); spread deleted / activation neutralized-behind-flag (D5); MEMORY.md full derivation deferred, CURRENT-WORK slim-down ships as bookkeeping (D6 — named B-disagreement).

**F2 RF on scope realism:** this cycle makes rulings durable, loaded-before-drafting, dispatch-inherited, and contradiction-guarded. It does NOT make every oblique ruling capturable (detector honest limit, §10 #1), does NOT index scratch artefacts or non-primary-session channels (§7), and does NOT fully derive the owner-side memory index (D6, §7). Named deferrals with reasoning, not silent drops.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| Spread deletion + activation neutralization (Slice 1) | **`primary-persona`** (`file_memory.py` compose path; `cocitation_graph.py` removed) | The machinery lives there; the eval harness's floor arm is the target configuration. |
| Surfacing rebuild (Slice 2) | **`primary-persona`** — BOTH `keep_pace/retrieval.py` (per-turn) AND `memory_consumer.py` (dispatch-bundle render) | The two render paths are siblings in one component; fixing one and not the other leaves dispatch packs on envelope-junk render (Tier-0 finding, this reconciliation). |
| Decision-record write surface + schema (Slice 3) | **`primary-persona`** (`file_memory.py` orbit — episode-adjacent structured record under the workspace memory tree) | `write_episode` (`:477`) is the proven atomic frontmatter'd writer; decisions reuse the orbit, no second store (B's Lens-1 argument, adopted). |
| Ruling detector + steer (Slice 3) | **`primary-persona`** (`stop_emitter.py` seam — the turn-close hook that already fires per turn) | Extends a seam that exists; no new event, no new cadence. Deterministic only (D2/D4 of the sealed cycle's posture). |
| Ledger retrieval integration (Slice 3) | **`primary-persona`** keep-pace (unified retrieval + whole-record injection per Slice 2's contract) | KP1 already merges episode + corpus hits; ledger records are a third merged source with guaranteed-vocabulary frontmatter. |
| Dispatch memory packs (Slice 4) | **`frame-kernel`** (`bundle.py` memory tier — decision-aware, whole-record) + activation via the sealed workspace-sync composer | The sealed carrier already composes a memory tier per dispatch; this teaches it the ledger + the Slice-2 render. Lens 1: compose on the sealed primitive, never a parallel pack path (D3). |
| Decision-claim guard (Slice 5) | **`hands-off-lifecycle`** (the sealed claim-guard layer on the KP9 draft-gate gains the ledger as a ground-truth source) | The guard is a consumer of ground-truth surfaces by design (sealed cycle §2); the ledger is one more source, same steer/fail-open contracts. |
| CURRENT-WORK.md slim-down + record backfill | **pos3 owner-side bookkeeping** (§9), NOT a loam component | Workspace content, not framework source; reversible via git; measured by the 7-day prediction. |

**Out of placement (NOT this cycle):** full MEMORY.md derivation (D6/§7); scratch-artefact indexing; non-primary-session channel capture; consolidation (roadmap Cycle 3); premise-flip auto-detection (sealed cycle's D5 deferral stands).

---

## §3 Named decisions (with recommendations) — surface to Luke

★ flags the one genuine owner call; the rest are autonomous method-calls recorded for the trail.

### D1 — Governing framing: the ratified merge weighting, anachronism excluded. **Autonomous (the comparison doc IS the dispatcher's ratified weighting); recorded.**
- Convergent core from both plans (decision ledger, write-side contract as the load-bearing piece, BM25 kept, relational layer stays dead); A's three mechanism fixes + eval discipline; B's guard-tier/recall-tier + decision-grain/turn-grain narrative and corpus-drift findings. **B's "CURRENT-WORK line 24 was present at failure time" claim is excluded as evidence — verified anachronistic (the line was added ~70 minutes after the failure).** B's generic point (dense prose anchors are unreliable recall surfaces under attention load) survives via the triple-representation finding and does not depend on the broken proof case.

### D2 — ★ Ledger write authority: persona-writes-at-ruling-time + deterministic steer-on-miss (A) vs auto-extraction at turn-close (B). **RECOMMEND: persona writes; the Stop-seam detector steers next turn when a ruling-shaped turn closed with no record; session-start catch-up sweeps misses. The one owner call.**
- *Why:* the in-session persona holds the entity context — it writes "Tilth, Alan, Eric, raise, valuation" into the record because it KNOWS that's what "the raise" meant; an extractor re-deriving entities from a deixis-heavy turn is exactly the inference gap that caused the failure. Auto-extraction also risks confidently-wrong records, which are worse than missing ones (they pass the guard).
- *The owner alternative:* turn-close auto-extraction with a confirm-steer on low confidence (B's shape). Honest cost of the recommendation: capture depends on the persona acting on the steer — a persistently-ignored steer loses records (mitigated by the catch-up sweep + AC.DLG.2 making the steer deterministic and evidence-bearing, and the residual failure visible).

### D3 — Dispatch-pack mechanism: the sealed frame-kernel SubagentStart carrier vs Plan A's new `loam memory pack` CLI + PreToolUse steer on packless briefs. **RECOMMEND: the carrier. Named deviation from A, Tier-0 grounded; autonomous.**
- *Why:* A authored its S4 without knowledge of the frame-kernel seal — the carrier verified this session: sealed `69e28416`, three-tier bundle with a memory tier already running per-dispatch retrieval. Building a pack CLI + brief-composer convention beside it would duplicate a sealed primitive (Lens 1 violation). With the hook registered, EVERY dispatched agent gets the bundle structurally — strictly stronger than a steer-enforced brief convention (structural beats advisory). Slice 4 therefore = make the memory tier decision-aware + whole-record (inheriting Slice 2's render) + activate the staged fragment.
- *Activation timing:* the fragment composes into workspace settings on the next pos-sync via the sealed auto-composer (`45cdf973`); live activation in pos3 changes every dispatch's context and stays a dispatcher-timed step (the fragment's own gating posture) — named here so ratifying this plan ratifies the activation intent, with the timing left to the dispatcher.

### D4 — One amendment, five sequenced slices, A's ordering (1 kill → 2 surfacing → 3 ledger → 4 packs → 5 guard) vs two amendments or B's capture-first ordering. **RECOMMEND: one amendment, A's ordering. Method-call.**
- *Why one amendment:* the slices share a fence ruling, review, and seal window; builds serialize in one tree regardless; Slices 4–5 consume Slice 2–3 surfaces, so separate amendments re-impose the same ordering with 3× bookkeeping (the sealed cycle's D3 reasoning, re-applied). Honest cost: a Slice-5 halt stalls the seal of 1–4; acceptable — Slice 5 extends an already-precision-proven detection grammar (AC.CLG.3 corpus) to one new claim class, the lowest-risk slice in the set.
- *Why A's ordering over B's capture-first:* Slices 1–2 are independent of the ledger, cheap, and measured — and Slice 3's whole-record injection NEEDS Slice 2's budget + render contract to land visibly. B's capture-before-recall argument is honored WHERE it bites: within the cycle, the write surface (AC.DLG.1) is built and tested before the retrieval integration (AC.DLG.3).

### D5 — Spread: DELETE; activation: NEUTRALIZE to 1.0 behind a default-off flag, not delete. **Autonomous (executes the owner's own June-7 eval verdict verbatim — KILL vs FIX respectively).**
- The eval's caveat is honored both ways: the kill is unconditional ("don't carry it dark; re-add with evidence if a live-store re-run ever justifies it" — re-adding means re-building from git history, which preserves the audit trail); activation is sound theory broken by store-freeze, so it stays in code, off, gated on a live-log re-measurement.

### D6 — Owner-side corpus: CURRENT-WORK.md slims to a ≤5KB pointer file + MEMORY.md work-state entries retire (stays rules-index only); FULL MEMORY.md derivation (B's BUILD ④) deferred. **Method-call; B-disagreement named.**
- *Why defer the derivation:* it tools the owner-side memory corpus (pos3, not loam framework) — auto-rewriting the user's memory index needs its own trust ruling; and the sharpest drift legs are already covered (sealed supersession honor + the ledger). *B's counter, honestly:* triple-representation is itself a correctness risk and a derived index is the structural fix — carried as a named follow-on in §7, not dropped. The slim-down ships now as reversible bookkeeping with a measured 7-day prediction.

---

## §4 Spec-objective placement

- **Binds to:** the owner's verbatim 2026-06-09 objective (header) — the recall half; the sealed FBM-correctness cycle is the guard half of the same objective. Jointly they replace the failed behavioral rules the corpus itself escalated (`feedback_published_state_only_from_git_refs`, `feedback_notes_and_users_are_pointers_evidence_resolves`).
- **Ladders up to:** **VALUE_PROPOSITION prime objective / Lens 0** — "no real memory" is a named betray-any-user failure mode on the protection floor; a persona that re-opens the user's settled rulings (the $750k case) spends exactly the owner attention loam exists to protect. The ledger is per-user-tuned translation MADE DURABLE: the record carries the user's OWN vocabulary at encode time, which is what makes ask-time loading possible.
- **The relational tension resolved (both plans, convergent):** Luke's "human memory follows trails" intuition is honored at ENCODE time — the in-session persona writes the links (entities, workstream, supersedes) into the record — not by recall-time co-occurrence statistics, which the eval measured net-harmful. Outcome-human-likeness via a mechanism measurement supports. Standing bar unchanged: recall-time relational machinery must beat BM25-floor on the harness before it ships.

---

## §5 Sealed-component fence

**Three components touched; all with manifest entries; additive except the named Slice-1 deletion (which executes a ratified measurement verdict).**

1. **`primary-persona`** (SEALED, live sidecar) — Slices 1–3. **Fence:** Slice 1 may DELETE the spread path + `cocitation_graph.py` and neutralize the activation multiplier behind a default-off flag — the ONLY non-additive edits in the cycle, pre-authorized by the eval verdict; every existing retrieval test must pass post-deletion (tests asserting spread/activation behavior are updated to the floor configuration as part of the slice — that is the verdict's meaning, not fence-drift). Slices 2–3 additive: render changes within the two named render paths; new decision-record module(s) in the `file_memory` orbit; detector extension on the `stop_emitter` seam; ledger as an additive merged retrieval source. **Forbidden without a halt:** changing `write_episode`'s contract or the episode never-not-store invariant; breaking any `AC.KP1.*` / `AC.PSI.*` / `AC.SUP.*` / retrieval-metric (P@5 guard) test (except the named spread/activation updates); changing episode-side `SUPERSEDED_PENALTY` semantics; any LLM/API call on the Stop/turn/dispatch hot paths.
2. **`frame-kernel`** (SEALED `69e28416`) — Slice 4. **Fence:** the bundle's memory tier may gain decision-awareness + the Slice-2 render + a raised tier budget; tier ORDER, the microkernel tier's verbatim-read contract, and the fail-soft never-block-a-dispatch contract (`AC.SACH.4`) are preserved byte-for-byte in outcome; the staged fragment's hook entries keep their fail-soft exit-0 shape. **Forbidden without a halt:** any path where a degraded memory tier aborts a dispatch; touching `subagent_stop_frame_check.py` (Slice 1b surface — not this cycle's scope).
3. **`hands-off-lifecycle`** (SEALED, `frozen_baseline` pinned per #23) — Slice 5. **Fence:** the claim-guard layer gains the decision ledger as an additional ground-truth source + the decision-state assertion class; the gate's fail-open, model-facing-only, no-LLM contracts and every `AC.KP9.*` / `AC.CLG.*` behavior are preserved. **Forbidden without a halt:** any blocked send; any user-facing guard text; precision regression on the existing AC.CLG.3 corpus.

Seal via `loam amend apply` + `loam amend seal` — **name `loam amend apply` explicitly in the build dispatch** (`feedback_dispatch_explicit_loam_amend_apply`); serialize all slices in one tree (`feedback_serialize_amendment_builds`); no `--amend` (`feedback_no_amend_in_agent_dispatches`).

---

## §6 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

AC IDs scope-descriptive. Each AC is satisfiable by more than one method; method is the builder's call.

### AC.EVX.\* — eval-verdict execution (Slice 1)

**AC.EVX.1** — Production memory search ranks with zero contribution from co-citation spread on every query, and the spread machinery no longer executes in any search path; the ranking for any query equals what the June-7 harness's floor configuration produces (BM25 × supersession, neutral activation). *(Outcome: the measured-harmful step is out of production; deletion mechanics are the builder's call.)*

**AC.EVX.2** — Power-law activation contributes a neutral factor by default; a named switch re-enables it with no code change, and default-off is verifiable from production configuration. *(Outcome: FIX-not-kill per the eval; switch mechanics are the builder's call.)*

**AC.EVX.OA (outcome-altitude: true)** — Against the live workspace store with NO pre-arranged state, the production search entry point returns ranked results whose scores carry no spread/activation contribution, at single-search latency consistent with the floor arm. *(Production entry point, real store. The full-harness re-run is the slice's measured prediction (§ build path), reported at build time — the store is live and evolving, so the harness numbers gate the slice rather than ride as a frozen test.)*

### AC.SRF.\* — surfacing rebuild (Slice 2 — BOTH render paths)

**AC.SRF.1** — Model-facing memory injection includes the source path for every memory pointer it surfaces, on both injection surfaces (the per-turn keep-pace block and the dispatch-bundle memory tier); user-facing prose surfaces remain path-free (the KP9 lint keeps its correct scope). *(Outcome: followable pointers for the model, clean prose for the user.)*

**AC.SRF.2** — Surfaced pointer text is substantive — derived from salient content, never a channel envelope, task-notification header, or structural-metadata prefix — on both surfaces. *(Outcome: no junk lines; salience mechanics are the builder's call.)*

**AC.SRF.3** — The per-turn injection budget accommodates at least three whole structured records (a named, tunable ~5KB-class constant), and small structured hits (decision records and equivalents) are injected WHOLE — ruling + reasoning + source pointer — never truncated to a one-line pointer; the dispatch-bundle memory tier honors the same whole-record contract within its own named budget. *(Outcome: a hit means the substance arrives; budget values + render shape are the builder's call within the keep-pace latency/char discipline.)*

**AC.SRF.OA (outcome-altitude: true)** — Through the production user-prompt-submit entry point against the live store with NO pre-arranged state, a work-anchored query yields an injected block of ≥3 substantive lines, each carrying a path, with zero lines beginning with a channel or task-notification envelope. *(The Plan-A live probe, replayed as a standing test.)*

### AC.DLG.\* — decision ledger (Slice 3)

**AC.DLG.1** — A production write surface persists an owner ruling as a structured decision record at ruling time — entities + aliases, question, ruling, reasoning, source message pointer, workstream, status (open / ruled / superseded) — machine-readable, in the workspace memory tree, append-not-rewrite (supersession marks, never edits-in-place), atomic. *(Outcome: rulings are first-class records; schema serialization + write mechanics are the builder's call.)*

**AC.DLG.2** — A turn that closes ruling-shaped with no corresponding decision record draws a deterministic model-facing steer on the existing turn-close seam (steer-not-block, fail-open, no LLM/API call), and a session-start catch-up surfaces ruling-shaped turns since the last sweep that still lack records. On a labeled sample of ≥20 real turns the detector reaches ≥80% precision with no steer on ordinary prose. *(Outcome: the write-side contract is gate-backed, not promised, without alarm fatigue; detection grammar is the builder's call.)*

**AC.DLG.3** — Decision records participate in unified retrieval: a topic query matching a record's entity vocabulary returns the record positioned for whole-record injection (per AC.SRF.3); records with `status: open` on an active workstream surface without an explicit query; a record can mark a corpus rule superseded via the sealed supersession mechanism and the existing honor applies. *(Outcome: written decisions are loaded decisions; ranking integration is the builder's call.)*

**AC.DLG.OA (outcome-altitude: true)** — **The $750k replay.** With the backfilled June-7 Tilth ruling record on disk and NO other pre-arranged state, the production ask-time path for a "draft the Tilth workstream plan"-class prompt injects the ruling WHOLE — value, reasoning, and source pointer all present in the rendered context — before any drafting surface is reached. *(The literal 2026-06-09 failure, replayed against production machinery and passing; rides along on every future memory-touching seal.)*

### AC.DMP.\* — dispatch memory packs (Slice 4)

**AC.DMP.1** — Every dispatched subagent's composed context bundle carries a memory tier in which decision records relevant to the task text are injected whole (per the AC.SRF.3 contract), within the tier's named budget; the bundle's fail-soft contract is preserved — a degraded or empty memory tier never blocks or aborts a dispatch. *(Outcome: agents inherit rulings structurally; tier composition mechanics are the builder's call.)*

**AC.DMP.2** — The frame-kernel hooks fragment composes into a workspace's `.claude/settings.json` through the sealed workspace-sync auto-composer with no hand-editing, idempotently, preserving non-loam entries — demonstrated against a fixture workspace. Live pos3 activation is dispatcher-timed (D3), not a build step. *(Outcome: activation is push-button at the dispatcher's chosen moment.)*

**AC.DMP.OA (outcome-altitude: true)** — **The June-9 dispatch replay.** Through the production SubagentStart entry point, with the live ledger (Tilth record present) and NO other pre-arranged state, a dispatch whose task text concerns Tilth planning yields a composed bundle containing the $750k ruling whole. *(The memory-blind planning agent, replayed and structurally impossible.)*

### AC.DCG.\* — decision-claim guard (Slice 5)

**AC.DCG.1** — When an outbound draft asserts decision-state — "X is open / undecided / unresolved" or "we never decided X" — about a subject resolvable to a `status: ruled` decision record, the guard steers with the record's ruling + source evidence before the send, under the sealed guard's existing contracts (model-facing-only, steer-not-block, fail-open, no LLM/API). *(Outcome: settled questions can't be silently re-opened; detection grammar extension is the builder's call.)*

**AC.DCG.2** — True decision-state claims (genuinely-open questions called open) and ordinary prose pass with no steer, and the existing work-state precision corpus (AC.CLG.3) still passes unchanged. *(Outcome: no alarm-fatigue regression.)*

**AC.DCG.OA (outcome-altitude: true)** — Through the production gate entry point against the live ledger with NO pre-arranged state: a draft asserting the Tilth raise size "is an open contradiction" draws a steer citing the $750k ruling; a draft calling a genuinely-open ledger question open draws none. *(The second half of the $750k failure-surface, replayed and caught.)*

---

## §7 Out of scope (deferred + when)

- **Full MEMORY.md derivation (B's BUILD ④)** — owner-side corpus tooling; needs its own trust ruling on auto-rewriting the user's memory index (D6). Named follow-on; the slim-down + ledger + sealed supersession cover the live drift legs now.
- **Scratch-artefact indexing** (`.scratch/claude-output/`) — stands deferred per the sealed cycle's §7; unchanged here.
- **Non-primary-session capture** — rulings made while the persona is down, or in channels not flowing through hooks, produce no episode and no record (A's honest limit #4). The transcript backstop covers primary-session turns only. A capture-path widening is its own future cycle.
- **LLM-assisted ruling extraction** — D2's rejected alternative; revisitable with evidence if the deterministic detector's measured precision/recall on real turns proves insufficient (that evidence arrives via AC.DLG.2's labeled sample + the catch-up sweep's miss log).
- **Consolidation (roadmap Cycle 3), premise-flip auto-detection, MM2 claim metadata, MM3 storage lint** — all stand as the sealed cycle left them.
- **Re-enabling activation** — gated on a live-access-log re-run of the June-7 harness beating the floor arm; the flag exists (AC.EVX.2), the measurement is the gate.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **Ruling-detector precision <80%** on the labeled sample, or it steers on ordinary prose in build-time testing — halt + surface a mechanism ruling (the D2 alternative becomes live); never a silent LLM call on a hot path.
2. **Any floor-arm harness metric missed after the Slice-1 deletion** (recall@10 < 0.072, MRR < 0.80, miss@10 > 6%, median latency > 60ms) — halt; the deletion should land exactly on the measured floor configuration, a miss means something else changed.
3. **The budget raise produces a measurable per-turn latency or context-bloat regression** beyond the keep-pace discipline — halt; surface a budget ruling (the #80 anti-bloat mandate).
4. **Any path where a bundle/dispatch change can block or abort a dispatch**, or a guard change can block a send — halt; the fail-soft/fail-open contracts are load-bearing.
5. **A Slice-1 test update would weaken a non-spread/non-activation retrieval guarantee** (AC.KP1.\*/P@5/supersession semantics) — halt; the verdict authorizes removing the measured-harmful machinery, nothing else.
6. **The decision-record schema would require changing `write_episode`'s contract or any episode-store invariant** — halt; records compose beside episodes, never reshape them.
7. **An AC drifts to method-in-AC during build** — fix the AC text (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, never the implementation.
8. **ODD violation discovered in the work or surrounding code** — halt and surface per `feedback_subagent_odd_violation_halt`; never silently extend.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — record the recall cycle: eval-verdict execution + surfacing rebuild + decision ledger (primary-persona), dispatch memory packs (frame-kernel), decision-claim guard (hands-off-lifecycle).
- **FBM roadmap** (`docs/design/fbm-state-and-memory-roadmap-2026-05-29.md`) — dated addendum: the recall tier delivered (this cycle) atop the guard tier (correctness cycle); the June-7 eval verdict executed; activation re-enable gated on a live-log re-run.
- **pos3 owner-side (post-seal):** backfill ≥5 recent rulings as ledger records (the Tilth $750k seed first — it is also the OA fixture); slim CURRENT-WORK.md to a ≤5KB pointer file + retire MEMORY.md work-state entries (D6 — reversible; **measured prediction: zero stale-state corrections needed over the following 7 days**); dated note on `fbm-eval-results-2026-06-07.md` that the verdict is executed; dated reconciled-into pointers on plan-A / plan-B / the comparison doc.
- **Master work queue** — completion notes on the memory-objective items this closes; dispatcher times the frame-kernel fragment's live pos3 activation (D3).

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **The detector will miss oblique rulings.** *Disagreement with the cycle's own promise:* "every ruling captured" is not literally achievable — a ruling phrased obliquely in a turn the persona also fails to recognize is lost as a record (it survives as episode + transcript, findable by topic, not guaranteed-surfaced). *Evidence:* the $750k deciding turn itself is pure deixis — the canonical hard case. *Alternative (baked in):* the persona-writes design (D2) puts the entity-aware writer at encode time, the steer + catch-up close the detectable-miss class, and AC.DLG.2's precision floor keeps the detector honest about what it claims to catch.
2. **A-vs-B ordering disagreement, resolved not averaged.** *The conflict:* B argues capture-first (S1=ledger); A puts the measured kills/surfacing first. *Resolution (A's order):* Slices 1–2 are ledger-independent, cheap, measured, and Slice 3's whole-record injection lands visibly only on Slice 2's budget; B's capture-before-recall principle is honored inside Slice 3 (write surface before retrieval integration). *Evidence:* AC.SRF.3 is a stated dependency of AC.DLG.OA's "injected whole."
3. **B's flagship proof case excluded.** The "CURRENT-WORK line 24 at failure time" claim is anachronistic (line added ~70 min post-failure, verified by the dispatcher); this plan carries B's recall-under-load point only in its generic form, supported by the triple-representation finding instead.
4. **The two-render-path discovery is new risk surface.** Neither A nor B named that the dispatch bundle renders via `memory_consumer.py`, not `keep_pace/retrieval.py` (found during this reconciliation). Slice 2 covering both is now explicit (AC.SRF.1–3 "both surfaces"); the residual risk is a third render path nobody has named — the builder should grep for additional `_render_retrieval`-class consumers and halt-and-surface any found (§8 #8 territory if one embeds the old contract).
5. **The 7-day CURRENT-WORK prediction is a slow-burn metric** — it cannot gate the seal; it gates the D6 follow-on (full derivation) instead. Named so the seal isn't blocked on a week-long measurement.
6. **Live activation of dispatch packs changes every dispatch in pos3.** The fail-soft contract bounds the blast radius (worst case: a degraded tier adds nothing), but the dispatcher should time the activation (D3) away from a critical in-flight workstream and watch the first few dispatches — a named operational caution, not a build risk.
7. **Scope-confidence (F4) per slice:** Slice 1 TIGHT (executing a measured verdict; outcome fully pinned). Slice 2 TIGHT (constraints pin outcome; render mechanics free). Slice 3 MEDIUM — schema + steer outcomes pinned hard, detection grammar deliberately loose (the genuinely-uncertain part; its halt trigger is #1). Slice 4 TIGHT (sealed carrier + sealed composer; smallest delta). Slice 5 TIGHT-MEDIUM (extends a precision-proven grammar to one new class). The dispatch brief should carry these annotations.

---

## §11 Provenance trail (all Tier-0 verified on disk/git 2026-06-09 in `/Users/lukeivers/loam` unless noted)

- Owner objective — verbatim, carried in the reconciliation dispatch brief (Telegram, 2026-06-09).
- Source plans + ratified weighting — `pos3/workspace/.scratch/claude-output/memory-northstar-plan-A.md`, `…-plan-B.md`, `…-ab-comparison-2026-06-09.md` (merge spine + anachronism exclusion).
- Correctness cycle SEALED-LOCAL — slice commits `6f7deb1f` / `10776ee5` / `7f163755`, apply `3b060f14`; `framework/{tools/loam,primary-persona,hands-off-lifecycle}/tests/SEAL_COMMIT` all read `3b060f14` (this session). Delivered: `keep_pace/plans_state.py` (321 lines), `supersession.py` (148 lines), claim-guard layer.
- Spread still live — `framework/primary-persona/src/loam/primary_persona/file_memory.py` `_compose_score_and_spread` builds the graph via `_cocitation_graph.build_cocitation_graph` (~`:1545`, read this session); `cocitation_graph.py` 429 lines, `access_log.py` 258 lines (wc, this session).
- Eval verdict + floor-arm numbers — `pos3/workspace/.scratch/claude-output/fbm-eval-results-2026-06-07.md` (re-read this session): spread KILL falsification line met exactly; floor arm recall@10 0.0727 / MRR 0.8059 / miss@10 0.055 / latency ~58.5ms; activation FIX-not-kill with the live-log caveat.
- Surfacing throttles — `keep_pace/retrieval.py`: `INJECTION_CHAR_CAP = 1200`, `_EPISODE_POINTER_CAP = 160`, `_render_injection` "NO file paths" docstring (read this session). Second render path: `memory_consumer.py` `MEMORY_RETRIEVAL_CHAR_CAP = 1600`, `_render_retrieval` at `:410` (read this session).
- Frame-kernel carrier — `framework/frame-kernel/src/loam/frame_kernel/bundle.py` (three tiers; memory tier via `mcp_memory_client` + `memory_consumer`; fail-soft AC.SACH.4), sealed `69e28416` (`tests/SEAL_COMMIT`, this session); staged fragment `framework/frame-kernel/hooks/settings.fragment.json` (read this session — explicitly not-live, dispatcher-timed); **no SubagentStart entries in `~/.claude/settings.json` or `pos3/.claude/settings.json`** (grep, this session).
- Auto-composer — `45cdf973` `feat(workspace-sync): settings-fragment auto-composer (RF-1 closure)` (git show, this session): globs `framework/*/hooks/**/settings.fragment.json`, composes additively/idempotently on terminal-success sync.
- Episode writer + Stop seam — `file_memory.py:477 write_episode` (frontmatter contract, atomic); `stop_emitter.py` `handle_stop_envelope` / `cli_stop` (read this session).
- $750k unretrievability + injection probe + agent blindness — Plan A §2.1/§2.2/§2.5 (live probes, A's session; the in-tree claims they ground — caps, no-paths, spread-live — independently re-verified here as above).
- Anachronism finding — comparison doc, dispatcher-verified (B's §2c proof case excluded).

---

## §14 Method-decision register (populated at build time)

*Placeholder — D1..D6 narratives + commit SHAs backfilled by the builder + `loam amend seal --plan-doc`.*

---

## Build path + effort estimate (AI-time per the duration rubric; ranges with midpoint)

Sequence: S1 → S2 → S3 → S4 → S5, one amendment, one tree (builds serialize). Each slice's measured prediction is logged per the tracked-value-predictions rule and reported in the seal summary.

| Slice | What | AI-time | Measured prediction (pass/fail) |
|---|---|---|---|
| **S1 — eval-verdict execution** | delete spread + `cocitation_graph.py`; activation → neutral behind default-off flag; update spread/activation tests to floor config | 15–30 min (mid 22) | Harness re-run on the live store: recall@10 ≥ 0.072, MRR ≥ 0.80, miss@10 ≤ 6%, median latency ≤ 60ms (the measured floor arm) |
| **S2 — surfacing rebuild (both render paths)** | paths in model-facing pointers; salient pointer text; ~5KB-class budget; whole-record contract; `memory_consumer` render aligned | 25–50 min (mid 35) | The live probe re-run injects ≥3 substantive path-bearing lines, zero envelope/notification lines (AC.SRF.OA, standing) |
| **S3 — decision ledger** | record schema + write surface; ruling-detector Stop steer + session-start catch-up; unified-retrieval integration; ≥5-ruling backfill (Tilth seed) | 45–90 min (mid 65) | (a) Tilth replay: ruling injected whole (AC.DLG.OA); (b) seeded ruling-turn-without-record → steer fires; (c) detector ≥80% precision on a 20-turn labeled sample |
| **S4 — dispatch memory packs** | bundle memory tier decision-aware + whole-record + raised budget; composer activation proven on fixture workspace | 20–40 min (mid 30) | Recomposed Tilth-planning dispatch bundle contains the ruling whole (AC.DMP.OA); fixture-workspace compose idempotent |
| **S5 — decision-claim guard** | guard ground truth widens to the ledger; decision-state assertion class; precision corpus extended | 20–40 min (mid 30) | "Raise size is open" draft steered with the $750k ruling (AC.DCG.OA); existing AC.CLG.3 corpus still passes clean |
| Apply + seal + bookkeeping | amendment mechanics + §9 | 10–20 min (mid 15) | — |
| **Total** | | **135–270 min, midpoint ≈ 200 min (~3.3 h)** | |

Owner gate-review time is a separate line item (owner availability). Post-seal slow-burn metric: zero stale-state corrections to the slimmed CURRENT-WORK.md over 7 days (gates the D6 follow-on, not the seal). Log actuals post-build for calibration.

---

## Stop-doing list (maintenance this cycle retires)

1. **Hand-maintaining work-state prose** — CURRENT-WORK.md in-flight sections + MEMORY.md work-state entries (~30KB + entries across the 154-file corpus, B's measured count); replaced by derived surfaces (sealed plan-state index, WMS census) + open-decision injection (AC.DLG.3).
2. **Tending the associative ranking machinery** — co-citation graph + activation-decay care; deleted/neutralized by measurement (S1).
3. **Writing further "verify before claiming / check the ledger" behavioral rules** — the guard tier + recall tier ARE the structure; rule-writing on this axis stops.
4. **Per-session "where were we / what did we decide" reconstruction searches** — ambient plan-state (sealed) + open-decision injection + whole-record loading make these redundant in the common case.
5. **Re-litigating settled rulings** — the costliest burden, paid in owner attention; the ledger + dispatch packs + decision-claim guard close all three legs of the $750k case.

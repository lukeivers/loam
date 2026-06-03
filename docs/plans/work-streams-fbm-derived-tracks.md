# WORK-STREAMS — FBM-derived cross-cutting attention tracks

**Status:** sub-plan-doc (PLAN ONLY — no build) · **Date:** 2026-06-03 · **Owner:** Luke (greenlit task #70, Telegram 13652/13654)
**WD:** `/Users/lukeivers/loam` (canonical loam checkout)
**Parent plan:** `workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (the FBM quality+accuracy program, task #69) — this is the *consumer* layer that sits on Slices C/D/E.
**Predecessors (load-bearing prior seals, Tier-0 read at plan-time):**
- Slice C — `docs/plans/fbm-cairn-state-probe-project-registry.md` → `framework/tools/loam/src/loam_cli/audit/registry.py` (`derive_project_state` / `PROJECT_REGISTRY` / `registered_project_names`). The STATE data source.
- Slice D — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` (`render_project_state_block` / `register_project_state_contributor`). The per-turn STATE surfacer + TTL cache + char-cap. The surfacing engine.
- Slice E — `framework/primary-persona/src/loam/primary_persona/work_visibility.py` (the read-only multi-source work snapshot). The aggregation precedent.
- KP5 — `framework/primary-persona/src/loam/primary_persona/keep_pace/objectives.py` (the `OBJECTIVES.md` `# user-objectives` register: `Objective` schema, `load_objectives`, `render_register`, `SEEDED_OBJECTIVES`, `~/.claude/OBJECTIVES.md`). **The substrate this plan extends.**
- N4 — `framework/primary-persona/src/loam/primary_persona/keep_pace/interaction_model.py` (the adaptive interaction-model reader; task #34). The per-user surfacing-preference source.
- Composer — `framework/primary-persona/src/loam/primary_persona/context_composer.py` (`TriggerKind.turn`, `register`, the 10k char cap). The registration seam.
**BASELINE candidate:** current `main` tip at build time (the plan-doc commit's parent). Component is decided in §2 + Decision D1 below — recommendation: **extend `primary-persona` (keep-pace), NOT a new component.**
**Status-file target:** `docs/STATE.md` + roadmap §8 + parent FBM plan backfill (see §9).
**Quality bar:** ODD §2.5 — every AC outcome-shape; ≥1 outcome-altitude AC exercising the live FBM STATE through a real turn with no pre-arranged state. Lens-1 (compose on the shipped FBM/keep-pace primitives, do NOT re-implement state-tracking).

---

## §1 Summary / TL;DR

**What ships:** a WORK-STREAMS layer that formalizes Luke's hand-maintained `CURRENT-WORK.md` "WORK STREAMS" section (Money / LitRPG / loam / Cairn / Personal-Home, extensible) into a durable register, where each stream's **STATE + NEXT-ACTION is DERIVED from real project status via the FBM `derive_project_state` engine** (Slice C) and **surfaced concisely every turn through the keep-pace lens** (Slice D), with **deep-dive** (mute the other streams' nudges) and **pause** (stop one stream's nudges) controls. A stream may span projects and/or nest under one. Staleness is flagged quietly; an expected-vs-real deviation is routed to the memory-reality mismatch side-channel (task #71). The backlog from three currently-disconnected sources (FIDRAFT, the persona task list, the loam-dev `workstream-queue.yaml`) is imported/consolidated into the stream structure.

**AC families:**
- `AC.WS.REG.*` — the stream register: schema, projects-mapping, attention-state, load + render.
- `AC.WS.DERIVE.*` — each stream's STATE + NEXT-ACTION derived from FBM `derive_project_state`, never stored stale.
- `AC.WS.SURFACE.*` — concise per-turn surfacing through the keep-pace lens; deep-dive / pause attention-state honored; char-budget respected (no context re-bloat).
- `AC.WS.DEVIATE.*` — expected-vs-real deviation detected and routed to the mismatch side-channel (#71).
- `AC.WS.IMPORT.*` — the three backlog sources imported/consolidated; the `ws-*` naming-collision reconciled.
- `AC.WS.LIVE.*` — **outcome-altitude**: a real turn surfaces an accurate per-stream STATE + next-action derived from the live FBM STATE, no pre-arranged state.

**Key decisions baked (full list + recommendations in §3):**
1. **Extend keep-pace (primary-persona), not a new component** — the stream register is a superset of the existing `OBJECTIVES.md` register; the surfacer is a sibling keep-pace turn-contributor next to `project-state`.
2. **A stream extends the `Objective` schema** with `projects: [...]` (the FBM-registry names it binds to) + `attention: active|deep-dive|paused` + `nest-under: <stream-slug>?`.
3. **NEXT-ACTION is derived, not stored** — the register stores the *derivation binding* (which projects + which subgoals), and the surfacer composes the live FBM STATE block into a per-stream "where it's at + next" at render time.
4. **Surfacing reuses Slice D's renderer discipline** (one short line per stream, TTL-cached, hard char-cap, fail-soft) — the per-turn block does NOT re-bloat context; it *replaces and subsumes* the raw project-state block rather than adding a second wall of text.
5. **Import = one-time consolidation pass + a documented standing reconciliation**; the `ws-*` dev-queue is RENAMED in concept to "dev-queue items" and mapped UNDER the `loam` stream, resolving the naming collision.

**F2 RF on scope realism (full treatment in §10):** the honest tension is per-turn surfacing vs the context-bloat the FBM load-filter (#80) and Slice D char-cap just fought. Resolution: the stream block **subsumes** the project-state block (one block, not two) and inherits Slice D's hard cap. If the stream count grows past the cap, the surfacer shows deep-dived/active streams in full and collapses paused/stale ones to a count — never spills the cap. This is a constraint, recorded as a halt trigger (§8) if a builder finds it cannot be met within the cap.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|------|-----------|-----------|
| Stream register schema + loader/renderer | `primary-persona` keep-pace (`.../keep_pace/work_streams.py`, sibling to `objectives.py`) | The register is a superset of the `OBJECTIVES.md` register; co-locating reuses the index/detail parse discipline + the same `~/.claude/` user-scope home. |
| Per-turn stream surfacer (turn-contributor) | `primary-persona` keep-pace (sibling to `project_state.py`) | The surfacer IS a keep-pace `TriggerKind.turn` contributor; it composes Slice D's `render_project_state_block` output rather than re-deriving. |
| STATE/NEXT-ACTION derivation | **reused verbatim** from `loam_cli.audit.registry.derive_project_state` (Slice C) | Lens-1 — do not re-implement state-tracking; the stream layer is a pure consumer. |
| Deviation → mismatch channel wiring | `primary-persona` keep-pace, calling the #71 side-channel entry point | #71 owns the mismatch surface; the stream layer only *detects expected-vs-real* and *emits* a structured mismatch record. |
| Backlog import/consolidation | a one-time authoring pass writing into the register's detail-paths + a documented standing reconciliation note | The three sources stay their own systems; the register becomes the *index* that points at them (index/detail shape, KP5 precedent). |
| The `ws-*` dev-queue naming | reconciled in-doc (Decision D6) — dev-queue items map UNDER the `loam` stream; no rename of the file | The `workstream-queue.yaml` is the dev *build* queue (decoupled, per `feedback_build_forward_on_publish_pending`), distinct from cross-cutting attention streams; reconciliation is conceptual, not a file move. |

---

## §3 Named decisions (with recommendations) — surface to Luke

Every decision carries a recommendation. These are the design forks Luke should eyeball; the builder takes method from here.

### D1 — New component vs extension of keep-pace. **RECOMMEND: extend keep-pace (primary-persona). Not a new component.**
- Why: the stream register is a *superset of the already-shipped `OBJECTIVES.md` register* (`keep_pace/objectives.py`), and the surfacer is *the same shape as the already-shipped `project-state` turn-contributor* (`keep_pace/project_state.py`). A new component would duplicate the loader, the `~/.claude/` home, the composer registration, and the TTL/cap discipline. Lens-1 + Lens-2 both point at compose-don't-rebuild.
- Cost honestly: it grows the `primary-persona` component's surface; the keep-pace package gains one module pair (`work_streams.py` + a surfacer). That is a single-component amendment, not a new BASELINE.

### D2 — Where stream definitions live. **RECOMMEND: extend the `Objective` dataclass into a `WorkStream` in a NEW user-scope register file `~/.claude/WORK-STREAMS.md`, header `# work-streams`, same index/detail markdown shape as `OBJECTIVES.md`.**
- Why a new *file* but a shared *schema*: a stream is a longer-lived, cross-project, attention-bearing thing; mixing it into `OBJECTIVES.md` (which N4/KP1 read for the retrieval anchor) would change a predecessor contract two other systems bind to. A sibling file with the same parse discipline keeps the contracts clean while reusing all the machinery.
- Alternative considered: collapse OBJECTIVES into WORK-STREAMS (one register). Rejected for this cycle — OBJECTIVES is a read-contract for KP1 retrieval + N4; collapsing it is a larger, riskier change. Recommend keeping them sibling for now; a later cycle MAY unify if the duplication proves real.

### D3 — How a track maps to projects. **RECOMMEND: a `projects: [<registry-name>, ...]` field on each stream, listing the FBM `PROJECT_REGISTRY` names the stream binds to; PLUS an optional `nest-under: <stream-slug>` for sub-streams.**
- Why: this is the literal binding that lets the surfacer call `derive_project_state(name)` per bound project and compose a real STATE per stream. A stream can span projects (list >1) and nest (the `loam` stream's substreams like FBM-quality, usage-guard).
- Honest gap (F2, see §10 #2): the FBM registry today registers only `loam` + `cairn`. The Money / LitRPG / Personal-Home streams have **no registered project** — their STATE has no ground-truth git derivation. RECOMMEND: a stream with no registered project derives its next-action from its `detail-path` doc's status + `last-touched`/`cadence` staleness, and is flagged "no ground-truth project bound" rather than faking a derived STATE. Registering litrpg-writer + a money-tracker as FBM projects is a **named follow-on** (out of scope here, §7).

### D4 — Surfacing format + cadence. **RECOMMEND: reuse Slice D's exact renderer discipline — one short line per stream, modules/next grouped, TTL-cached, hard char-cap — and SUBSUME the project-state block (one block, not two). Cadence = every turn (like Slice D), verbosity tuned by N4.**
- Format: `  - Money [active]: revenue-independence — next: <derived>` ; `  - loam [active, 3 substreams]: <lead substream STATE> — next: <derived>`.
- Cadence/verbosity is a **per-user preference** (Lens #34 / N4): the surfacer reads the interaction-model cell for the work area and tunes how much it shows (terse for low learning-appetite, fuller for high). RECOMMEND wiring N4's reader the same way the other keep-pace contributors will; if N4's two-axis MVP doesn't expose a verbosity axis yet, default to Slice D's terse one-line-per-stream and record the N4-verbosity tie as a follow-on.

### D5 — Deep-dive / pause mechanics. **RECOMMEND: an `attention:` field per stream with values `active` | `deep-dive` | `paused`, owner-gated write (PROPOSE-AND-SURFACE, like KP5 `status`), plus a plain-language control verb.**
- `active`: surfaces its concise line + may nudge on staleness.
- `deep-dive`: this stream surfaces in full; ALL OTHER streams' nudges are muted (their lines still render, but no staleness nudge fires). Exactly one stream may be `deep-dive` at a time (a second deep-dive demotes the first to active — surfaced).
- `paused`: no line, no nudge, no staleness flag; stays in the register, collapsed to a count in the block.
- Control: a plain-language path ("deep-dive on Money", "pause LitRPG") flips the field; the write is owner-gated (no automated path mutates `attention`). This mirrors the KP5 owner-gated-write discipline exactly.

### D6 — Import/consolidation strategy + the `ws-*` naming collision. **RECOMMEND: a one-time consolidation authoring pass + a documented standing reconciliation; the dev-queue maps UNDER the `loam` stream as "dev-queue items", no file rename.**
- The three sources and where each lands:
  1. **FIDRAFT** (`docs/FUTURE_IDEAS_DRAFT.md` + `docs/FUTURE_IDEAS.md`) — idea-capture; its graduated items become subgoals/detail-path entries under the relevant stream (mostly `loam`). FIDRAFT stays the capture surface (per `feedback_future_ideas_draft_workflow`); the register *indexes* graduated items, doesn't absorb the raw draft.
  2. **Persona task list** (the TaskCreate backlog, #1–#83) — each task tagged to a stream; the register's per-stream detail-path links the task IDs. The task list stays the live tracker (per `feedback_task_tracking_discipline`); the register groups tasks by stream for the surfacer.
  3. **loam-dev `workstream-queue.yaml`** (`/Users/lukeivers/pos3/.claude/workstream-queue.yaml`) — this is the dev *build/amend* queue (`ws-*` items, decoupled publish-vs-build per `feedback_build_forward_on_publish_pending`). It is NOT a cross-cutting attention stream. RECOMMEND: name it "dev-queue items", map it UNDER the `loam` stream as one of its substreams, and document the distinction in the register header so the `ws-*` prefix collision is explicit-and-resolved, not silent. No file move (it's load-bearing for the dev-amend cadence).
- The standing reconciliation: a short note in the register's header naming the three sources + how each flows in, so a future agent doesn't re-disconnect them.

### D7 — How deviation → mismatch-channel wires. **RECOMMEND: the surfacer compares the stream's *expected* state (its `detail-path` doc's recorded status / `last-touched`) against the *derived* FBM STATE; a divergence emits a structured mismatch record to the #71 side-channel entry point, fail-soft.**
- Example: the `loam` stream's detail doc says "FBM overhaul in flight" but `derive_project_state("loam")` shows those modules MERGED → that is an expected-vs-real deviation → emit `{stream, expected, derived, evidence}` to #71. This is the self-healing tie.
- Dependency honestly named (§8 halt): #71's side-channel entry point must exist for this wiring. #71 is currently `pending`. RECOMMEND building the *detection* here behind a fail-soft seam that no-ops if #71's entry point is absent, and naming the #71-entry-point wiring as the integration AC — so this cycle ships detection + a clean seam even if #71 lands after.

---

## §4 Spec-objective placement

- Binds to: the keep-pace prime capability ("keep pace with the user" — memory recall + live objectives + plain-language abstraction; task #12, the pitch-critical flagship).
- Ladders up to: **VALUE_PROPOSITION prime objective** (per `feedback_value_proposition_as_prime_objective`) — Lens-2 primary-persona test: this surface *reduces Luke's translation burden* by maintaining + surfacing accurate per-stream state so he never has to ask "where is each track and what's next" or hand-maintain the `CURRENT-WORK.md` section. That IS the value.
- Prime directive tie (Lens-0): per-user-tuned translation — the surfacing cadence/verbosity is tuned per-user via N4 (D4).

---

## §5 Acceptance criteria (outcome-shape; method-in-AC test passed on each)

Each AC states an *outcome*, satisfiable by methods other than the one in mind. Each maps to a named test at build time.

**AC.WS.REG.1** — The stream register loads from a user-scope file into a list of streams, each carrying its slug, attention-state, bound projects, optional nest-parent, and detail-path; round-trips through render→load unchanged. *(Outcome: a register exists and is parseable; method — file format, dataclass — is the builder's call.)*

**AC.WS.REG.2** — A stream may bind zero, one, or many projects AND may nest under another stream; a stream that spans multiple projects and a stream that nests both resolve correctly when read. *(Honors the Luke-13511 span-AND-nest design intent.)*

**AC.WS.DERIVE.1** — For a stream bound to ≥1 registered FBM project, its surfaced STATE + next-action is composed from a FRESH `derive_project_state` call (the Slice C production entry point), never from a stored/cached-stale status string. Mutating the underlying repo state and re-reading the stream reflects the change without editing the register. *(Outcome: derived-not-stored, verifiable by changing ground truth; method is the builder's call.)*

**AC.WS.DERIVE.2** — A stream bound to NO registered project (e.g. Money) surfaces a next-action from its detail-path/cadence staleness AND is explicitly marked "no ground-truth project bound" — it never fabricates a derived build-STATE. *(Honors D3's honest gap.)*

**AC.WS.SURFACE.1** — On a real turn, the keep-pace lens surfaces ONE concise block covering all non-paused streams, one short line per stream, within a hard character cap; the block subsumes (does not duplicate) the Slice-D project-state block. *(Outcome: concise, capped, single block — no context re-bloat; method is the builder's call.)*

**AC.WS.SURFACE.2** — Setting a stream to `deep-dive` surfaces that stream in full and mutes every OTHER stream's staleness nudge; setting a stream to `paused` removes its line and nudge entirely; both states are owner-gated (no automated path mutates `attention`). *(Honors the deep-dive/pause design intent + KP5 owner-gated-write.)*

**AC.WS.SURFACE.3** — When the rendered block would exceed the cap, active/deep-dived streams render in full and paused/stale streams collapse to a count; the cap is never exceeded. *(The F2 anti-bloat constraint as an AC.)*

**AC.WS.DEVIATE.1** — When a stream's expected state (detail-path recorded status / last-touched) diverges from its derived FBM STATE, a structured deviation record `{stream, expected, derived, evidence}` is emitted to the memory-reality mismatch side-channel; if that channel's entry point is absent the detection no-ops fail-soft (never crashes the turn). *(Outcome: deviation detected + routed; the #71 wiring is the integration point.)*

**AC.WS.IMPORT.1** — The register, after the consolidation pass, indexes the backlog from all three sources (FIDRAFT graduated items, persona task list, dev-queue `ws-*` items) grouped by stream; the dev-queue items resolve UNDER the `loam` stream and the register header documents the `ws-*`-vs-cross-cutting-stream distinction. *(Outcome: the three sources are connected + the collision is documented; method is the builder's call.)*

**AC.WS.LIVE.1 (OUTCOME-ALTITUDE, `outcome-altitude:true`)** — Run the production surfacer through a real keep-pace turn against the LIVE loam + cairn repos with NO pre-arranged state: the surfaced block names the streams, and for a stream bound to a registered project (e.g. the `loam` stream → `loam`, the `Cairn` stream → `cairn`) shows a STATE + next-action DERIVED from the live `derive_project_state` (e.g. Cairn's verify/ledger/execute as built) — so the persona cannot, from this block, mis-state a bound project's status. Invokes the production entry point, no fixtures, no pre-arranged state. *(This is the literal answer to Luke's "proper context/state for projects is maintained and surfaced during conversations.")*

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

Single-component amendment on `primary-persona`. Per-cycle shape:
1. Manifest at `docs/plans/work-streams-fbm-derived-tracks.manifest.yaml` (paired, below).
2. Source: add `keep_pace/work_streams.py` (register schema + loader/renderer, modeled on `objectives.py`); add the per-turn surfacer (modeled on `project_state.py`, composing `render_project_state_block` + per-stream `derive_project_state`); add the register's user-scope path resolver + seed (the 5 streams from `CURRENT-WORK.md`).
3. Wire the surfacer as a keep-pace `TriggerKind.turn` contributor; ensure it subsumes (replaces) the bare project-state block so there is one block, not two.
4. Wire the deviation→#71 seam fail-soft.
5. Author the consolidation pass (D6) writing the register seed + the three-source reconciliation header.
6. Tests authored per AC (each AC → a named test file; `AC.WS.LIVE.1` is the outcome-altitude live-repo test).
7. `loam amend apply` (sealed-component bookkeeping — name it explicitly in the dispatch per `feedback_dispatch_explicit_loam_amend_apply`); seal; smoke (a real turn renders the block).

---

## §7 Out of scope (deferred + when)

- **Registering Money / LitRPG / Personal-Home as FBM projects** (so they get a true ground-truth derivation) — a named follow-on; needs a per-project marker spec (like Cairn's). Until then those streams use the detail-path/cadence path (AC.WS.DERIVE.2). Deferred to a post-cycle FBM-registry extension.
- **Collapsing OBJECTIVES.md into WORK-STREAMS.md** — kept sibling this cycle (D2); a unification cycle MAY follow if duplication proves real.
- **The #71 mismatch side-channel itself** — this cycle ships the *detection + emit seam*; #71 owns the channel + the ground-truth auto-correct. Wired fail-soft so order doesn't block.
- **Auto-mutating `attention` from behavioural signals** — owner-gated only this cycle (D5), mirroring N4's MVP fence (cells move only by explicit statement).
- **N4 verbosity-axis tuning** — if N4's MVP doesn't expose a verbosity axis, default terse + record the tie (D4); the full per-user verbosity adaptation is a later N4 slice.

---

## §8 Halt triggers (abort the in-flight build + surface)

1. **The surfacer cannot fit all active streams within Slice D's char-cap even after the collapse rule (AC.WS.SURFACE.3).** Halt — the anti-bloat constraint is load-bearing (F2 #1); surface for a cap-vs-content ruling rather than spilling.
2. **Extending the surfacer would require modifying the `OBJECTIVES.md` read-contract** that KP1/N4 bind to. Halt — that touches a predecessor contract (a sealed surface) without a manifest entry; surface rather than silently widen.
3. **The #71 side-channel entry point shape is undecided at build time AND the fail-soft seam is ambiguous** (what a no-op deviation-emit looks like). Halt — surface the seam shape for a #71-coordination ruling.
4. **The FBM `derive_project_state` call is too slow per-turn even with Slice D's TTL cache** when fanned out across N streams. Halt — surface a caching/fan-out ruling rather than introduce a per-turn latency regression (Slice D's whole point was LESS junk + zero steady-state I/O).
5. **An AC drifts to method-in-AC during build** (the test can only pass one specific way). Halt + fix the AC (doc-only) per `feedback_loose_AC_text_fix_AC_not_implementation`, not the implementation.

---

## §9 Bookkeeping (backfill on seal)

- **`docs/STATE.md`** — add the WORK-STREAMS surface under primary-persona/keep-pace.
- **Roadmap §8** — record the work-streams cycle (the FBM-consumer layer atop Slices C/D/E).
- **Parent FBM plan** (`...loam-fbm-quality-and-accuracy-unified-plan.md`) — backfill: the consumer layer that closes Luke's "context/state maintained + surfaced during conversations" requirement.
- **`CURRENT-WORK.md`** — once the register seed lands, mark the interim "WORK STREAMS" section as FORMALIZED-BY the register (it stays as the human-readable mirror; the register is the machine surface).
- **Task #70** → completed on seal; **task #71** gets a `blocked-by`/integration note (the deviation seam expects its entry point).
- **`feedback_*` memory** — none new required; this cycle *consumes* existing principles. (If the OBJECTIVES-vs-WORK-STREAMS sibling-vs-unify question recurs, capture then.)

---

## §10 F2 Ruthless Feedback (honest doubts + named design risks)

1. **Per-turn surfacing vs the context-bloat we just fought (THE central tension).** *Disagreement:* a naive "surface every stream every turn" would re-bloat the exact context the FBM load-filter (#80) and Slice D's char-cap just shrank. *Evidence:* `project_state.py` `_STATE_BLOCK_CHAR_CAP = 600` + the explicit "do not trade removed junk for a wall of text" comment; the #80 P@5=0.0 de-flood fix. *Alternative (the resolution baked in):* the stream block SUBSUMES the project-state block (one block, not two — D4), inherits the hard cap, and collapses paused/stale streams to a count (AC.WS.SURFACE.3). If even that can't fit, halt (§8 #1). This is the right resolution but it is a real constraint the builder must hold.

2. **Half the streams have no ground-truth project to derive from.** *Disagreement:* the headline "STATE derived from real project status" is only literally true for `loam` + `cairn` (the two registered FBM projects). Money / LitRPG / Personal-Home have no registered derivation today. *Evidence:* `registry.py` `_default_registry()` registers exactly `loam` + `cairn`. *Alternative:* AC.WS.DERIVE.2 makes the no-project case explicit (detail-path/cadence staleness + a "no ground-truth project bound" mark) rather than faking a derived STATE; registering litrpg-writer + a money surface is a named follow-on (§7). The honest framing for Luke: this cycle delivers true ground-truth derivation for loam + Cairn now, and a clean staleness-based next-action for the rest, with the path to upgrade them named.

3. **#71 is pending — a forward dependency.** *Disagreement:* the deviation→mismatch tie (the self-healing point Luke called load-bearing) depends on a channel that doesn't exist yet. *Evidence:* task #71 status `pending`. *Alternative:* ship detection + a fail-soft emit seam now (AC.WS.DEVIATE.1), name the #71 entry-point wiring as the integration AC, build #71 next. The deviation is *detected* this cycle regardless; only the *routing* awaits #71.

4. **OBJECTIVES.md vs WORK-STREAMS.md duplication risk.** *Disagreement:* two sibling user-scope registers with near-identical schemas could drift. *Evidence:* the `Objective` schema (KP5) is ~80% of the proposed `WorkStream` schema. *Alternative:* keep sibling this cycle (D2, lower risk — OBJECTIVES is a read-contract for KP1/N4), and name unification as a candidate later cycle if the duplication proves real rather than speculative. Surfaced so it's a conscious choice, not silent precedent (Lens 6).

5. **Scope-confidence (F4) note.** Design confidence is MODERATE, not high — the compositional shape (extend keep-pace, consume FBM STATE, sibling register) is high-confidence; the surfacing-format details, the N4-verbosity tie, and the #71 seam shape are the genuinely open forks. Per F4 I have NAMED those as decisions (D2/D4/D7) with recommendations and left method to the builder, rather than locking method in ACs. The ACs are outcome-shape; the forks are surfaced for Luke.

---

## §11 Provenance trail (load-bearing sources)

- Slice C STATE engine — `framework/tools/loam/src/loam_cli/audit/registry.py` (`derive_project_state` L117–139, `PROJECT_REGISTRY` L89, `registered_project_names` L108).
- Slice D surfacer — `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py` (`render_project_state_block` L168–227, `_STATE_BLOCK_CHAR_CAP=600` L66, `_STATE_TTL_SECONDS=60` L62, `register_project_state_contributor` L250–269, the outcome-altitude note L182–186).
- Slice E aggregation precedent — `framework/primary-persona/src/loam/primary_persona/work_visibility.py` (read-only multi-source snapshot, fail-soft discipline L1–50).
- KP5 register substrate — `framework/primary-persona/src/loam/primary_persona/keep_pace/objectives.py` (`Objective` L120–134, `OBJECTIVES.md` path L102–114, `SEEDED_OBJECTIVES` L144–193, owner-gated-write discipline L24–32).
- N4 interaction-model (per-user verbosity tie) — `framework/primary-persona/src/loam/primary_persona/keep_pace/interaction_model.py` (the MVP two-axis read, fail-open L14–70).
- Composer registration seam — `framework/primary-persona/src/loam/primary_persona/context_composer.py` (`TriggerKind.turn` L63–67, `register` L335, 10k cap L60/L135–143).
- Interim surface this formalizes — `~/.claude/projects/-Users-lukeivers-pos3/memory/CURRENT-WORK.md` "WORK STREAMS" section (5 tracks: Money / LitRPG / loam / Cairn / Personal-Home).
- Backlog sources — `docs/FUTURE_IDEAS_DRAFT.md` + `docs/FUTURE_IDEAS.md` (FIDRAFT); the persona task list (#1–#83); `/Users/lukeivers/pos3/.claude/workstream-queue.yaml` (dev `ws-*` queue).
- Owner mandate — Telegram 13652 (import/consolidate the three sources), 13654 (the FBM-STATE tie is load-bearing), 13511/13517 (span-AND-nest, deep-dive/pause, derived-not-stored, deviation→mismatch design intent).

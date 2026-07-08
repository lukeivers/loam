# Memory redesign — Stage 4: Rules store + situational recall (the third leg of the three-way split)

**Status:** BUILD-READY PENDING OWNER GO on the §10 forks. Plan-only; no implementation code authored.
**Component (sealed):** `framework/primary-persona` — advances the existing sidecar (`new_component: false`).
**Design source:** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (Stage 4) + owner refinements (`owner-refinements-2026-07-02.md` #4, `owner-refinements-round2-2026-07-02.md` — the fact/rule cleave + conservative high-threshold extraction).
**Predecessors (landed):** S1a ground-floor extraction (`RANK_CONSTITUTIONAL_FLOOR = False`, sealed); standing retrieval telemetry (`retrieval_telemetry.py`, sealed `a2ce742`); S2 ranker — relevance-threshold recall + bounded event-recency prioritizer (sealed, `origin/main` tip `a0444859`).

---

## §1 Objective

Stand up the SEPARATE rules store (store **c**) — behavioral directives, each auditable to the fact(s) that justify it — with its OWN **situational** recall so a rule fires only when the turn's situation matches, never always-on; kept lean by a hard context-budget cap so behavioral rules cannot bloat the per-turn context that the whole redesign protects.

One sentence: **give loam a place to keep "how to behave" as prompts distinct from "what happened" as facts, and recall those prompts by the situation the turn is in, under a hard budget, reversibly.**

---

## §2 Predecessors / context

This plan composes against, and does not reshape, three sealed slices:

1. **S1a — ground-floor extraction.** The always-on constitutional floor (store **a**) is carved out of the ranked pool and injected unconditionally by the floor surfaces (`RANK_CONSTITUTIONAL_FLOOR = False`). S4 adds store **c** as a *second* non-topical channel that is NOT always-on — it sits between the floor (a) and the topical facts (b).
2. **Standing retrieval telemetry.** `keep_pace/retrieval_telemetry.py` logs `{prompt → candidates+scores → injected}` per turn, fail-open, no-op unless a sink is configured. S4 extends the *same* recorder with a `{situation → rules fired}` record so both situational-recall failure directions (over-fire / under-fire) are measurable before store (c) is trusted.
3. **S2 ranker — relevance-threshold recall + event-recency prioritizer.** `_merge_by_score` in `keep_pace/retrieval.py` is the store-(b) fact/episode/decision pipeline. S4 does NOT touch its semantics; rules are a *separate* channel with a *separate* recall discipline (this separation is the load-bearing point of the whole three-way split — one ranker for three jobs is the measured failure).

The store-(c) record mirrors the sealed decision-ledger pattern exactly (`primary_persona/decision_ledger.py`: frontmatter'd markdown, one file per record, atomic tmp+`os.replace`, append-not-rewrite, supersession-by-marking, human-readable). Rules are the natural home of the *behavioral half* of a decision record the design's "where the decision-ledger cleaves" section describes; S4 stands up that home and its recall.

---

## §3 Scope

### In scope (S4)
1. **The rules store (c).** A new `primary_persona/rules_store.py` (sibling of `decision_ledger.py`) with the write/read/situational-match API; records land under `<memory_dir>/rules/` (sibling of `decisions/`). Frontmatter'd markdown, mirroring the decision-ledger write discipline.
2. **Write-side fact/rule classification.** The rule write API requires a directive + situation-tags + ≥1 provenance pointer to a store-(b) record; classification is at *write time* (fact and rule authored apart), never read-time scoring. The store-(b) facts-only discipline is left intact.
3. **Situational recall.** A separate rules contributor/block in `keep_pace/retrieval.py` that surfaces a rule ONLY when the turn's detected situation is in the rule's situation-tag set — exact set-membership, no relevance score — on a separate labeled block and a separate hard budget, NOT merged into `_merge_by_score`.
4. **The context-budget dial.** A named `SITUATIONAL_RULE_CAP` (hard cap on rules per pull) + a byte sub-budget; the governing lever the owner named.
5. **A conservative situation detector as a named, pluggable seam.** Reads the signals available at the recall surface (prompt + work-anchor + workspace) and emits the current turn's situation tags; designed so richer signals (tool-events, threaded task-context) can feed it in a later stage without reshaping the store.
6. **A small hand-seeded / at-ruling-time authored rule set** (extend the sealed D2 "persona writes at ruling time" discipline: when a fact has an obvious behavioral consequence, author the rule alongside it) — enough to exercise recall end-to-end.
7. **Telemetry extension** `{situation → rules fired}` on the existing recorder.
8. **Reversibility lever** — a named master flag that reverts (c) to a no-op (byte-identical to pre-S4).

### Out of scope (deferred — see §7 sequencing)
- **S1b — physically moving the situational design-lenses out of the always-on `CLAUDE.md` into store (c).** S4 *creates the destination*; the *removal* of the lenses from always-on is a separate gated flip sequenced immediately AFTER S4 proves recall (§10 Fork G). No `CLAUDE.md` file is edited in S4.
- **S5 — automated offline rule-EXTRACTION/consolidation** (deriving rules from accumulated facts at the high frustration/outcome/idea threshold). S4 ships the store + situational recall + *manual/seeded* authoring; S5 is the offline engine that populates (c) in bulk (§10 Fork G).
- **Richer situation-detection surfaces** (PreToolUse tool-event detection, threaded persona task-context). S4 ships the detector seam; the richer signals are follow-on.
- **Bulk migration of existing decision records into (c).** The cleave is available (a rule can cite a decision as provenance) but no mass migration runs in S4.

---

## §4 — Acceptance criteria

AC IDs are scope-descriptive: **AC.RSR.\*** (Rules-Store + Situational-Recall). Each is outcome-shape — the method (exact-tag match, separate block, named constants) is inferable from the constraints but no AC states HOW.

### AC.RSR.1 — the rules store exists and is distinct from facts
A behavioral rule is persisted as a structured record carrying, at minimum, a directive (the behavioral instruction), a situation representation, a provenance pointer set, and a status; it is stored apart from store-(b) facts and store-(a) floor content, and is human-readable and prunable on disk. Reading the store back returns the authored rule. *Verified:* `test_AC_RSR_1_*` — write a rule, read it back, assert its fields + that it lands in a store distinct from `decisions/` and the corpus.

### AC.RSR.2 — write-side classification: rules are directives auditable to evidence; facts stay facts
A rule write is REJECTED (or flagged invalid) when it carries no provenance pointer to a store-(b) record — a rule is auditable to the fact(s) that justify it (info-trust applied to (c)). The store-(b) facts-only discipline is unchanged by S4 (a fact write still stores a fact, never a directive). Classification is at write time: the fact-half and rule-half of the same event are authored into different stores, not scored together at read time. *Verified:* `test_AC_RSR_2_*` — a provenance-less rule write fails; a fact write is unchanged; a fact + its derived rule land in two stores.

### AC.RSR.3 — situational recall: a rule fires only on a matching situation, never always-on
Over the recall path, a rule surfaces on a turn whose detected situation is in the rule's situation set, and surfaces to NO turn whose situation is outside it. No relevance/BM25 score can admit a rule (a rule is not "topically relevant" to the turn's subject — it is relevant to the turn's *situation*). A rule with an empty situation set never fires through (c). *Verified:* `test_AC_RSR_3_*` — same rule, two turns: matching-situation turn surfaces it, non-matching turn does not; a high-topical-overlap non-matching turn still does not surface it.

### AC.RSR.4 — separate recall channel: rules do not compete with facts
Rules inject in a distinct, labeled block on a budget separate from the store-(b) fact/episode/decision pool; the store-(b) recall output for a given turn is byte-identical whether or not any rule fires (rules never enter `_merge_by_score`, never occupy a fact slot, never crowd a topical fact). *Verified:* `test_AC_RSR_4_*` — the fact block for a fixed turn is identical with the rules channel empty vs populated; the rules block is separately labeled.

### AC.RSR.5 (context-budget-bound) — a hard cap on rules per pull
On any single situational pull, at most `SITUATIONAL_RULE_CAP` rules inject regardless of how many match the situation, and the rules block respects its byte sub-budget; the cap is a named, tunable lever (raising it admits more; lowering it fewer). Excess matching rules are dropped by a deterministic priority, never half-emitted. *Verified:* `test_AC_RSR_5_*` — a store with `> cap` rules all matching one situation injects exactly `cap`; the block stays within budget; the cap constant reorders the outcome.

### AC.RSR.6 (reversibility) — a named master lever reverts (c) to a no-op
With the situational-rules master lever OFF (or `SITUATIONAL_RULE_CAP = 0`), the recall output is byte-identical to pre-S4 (no rules block emitted); flipping it on re-admits rules with nothing on disk deleted. *Verified:* `test_AC_RSR_6_*` — lever-off output equals the pre-S4 baseline byte-for-byte; lever-on re-admits; the store files are untouched by the flip.

### AC.RSR.7 (outcome-altitude) — situational behavioral injection, end-to-end, no pre-arranged state
Over the production recall entry-point invoked with no pre-arranged retrieval state, against a seeded rules store: a turn whose situation matches a seeded rule surfaces that rule's directive in the labeled rules block; a turn whose situation does not match surfaces no rule; and the topical fact recall on the same turns is intact — proving the store recalls behavioral prompts *situationally* (not always-on) through the real entry-point. *Verified:* `test_AC_RSR_7_OA_*` — the production resolver + entry-point, seeded store, two contrasting turns, all three assertions.

### AC.RSR.8 — no regression on the sealed recall surface
The KP1 / FBMU / FBM-FILTER / SRF / RDP / RTEL / DLG suites stay green: S4 adds a channel and never alters the fact/episode/decision pipeline, the telemetry pure-observation guarantee, or the fail-open-whole-chain contract. *Verified:* full-suite run + `test_AC_RSR_8_*` (fail-open: a broken/absent rules store yields no rules block and never breaks the turn).

**Ladder-up.** AC.RSR.\* → the memory-redesign objective (best on-file context per turn with no over-injection) → AC.PO.1 (reduce the user's translation burden — the learned behavioral rules ARE the per-user customization Lens 0 names) + AC.PO.2 (add to the harness toolkit — a reusable behavioral-rule store + situational recall) → Lens 0 prime directive. The context-budget cap is the *protection* half of Lens 0 (a guard sized to the damage its failure does: context-window bloat that makes the whole system stop working).

---

## §5 Sealed-component fence

**Component:** `framework/primary-persona` (advances the sidecar; `new_component: false`).

**Touched:**
- NEW `framework/primary-persona/src/loam/primary_persona/rules_store.py` — the store write/read/situational-match API (mirrors `decision_ledger.py`).
- EDIT `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py` — the separate rules contributor + labeled block + named levers (`SITUATIONAL_RULE_CAP`, the master flag) + the situation-detector seam; wired into the two live resolvers only (`_resolve_live_config`, `_resolve_composer_config`) as a separate channel.
- EDIT `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval_telemetry.py` — the additive `{situation → rules fired}` record (pure-observation, fail-open).
- NEW `framework/primary-persona/tests/test_AC_RSR_*`.

**NOT touched (fence integrity):** `_merge_by_score` and the store-(b) pipeline semantics; `decision_ledger.py` core; `file_memory.py` core; `corpus_index.py`; the floor surfaces (`corpus_inline_session_start.py`, the frame-kernel `bundle.py`, `principle_reminder.py`); any `CLAUDE.md` file; `settings.json`; `RetrievalConfig`'s existing fields' semantics (new fields are additive with no-op defaults, mirroring the telemetry-dir pattern so direct-config callers stay byte-identical).

**Blast radius:** the rules channel rides the same live per-turn path as `retrieve()` (main-session UserPromptSubmit + composer + subagent memory tier), but only ADDS a fail-open channel behind a master lever; every existing contract is a no-op-by-default extension.

**Rollback:** git-revert the seal, OR flip the master lever off / `SITUATIONAL_RULE_CAP = 0` to revert to byte-identical pre-S4 recall (store files on disk untouched).

---

## Primitive check (new mechanism introduced)

| New mechanism | Native primitive considered | Choice |
|---|---|---|
| Per-workspace behavioral-rule store | Claude Code memory / CLAUDE.md; the sealed decision-ledger + episode stores | **bespoke — mirror the sealed `decision_ledger.py` store** (frontmatter'd markdown, atomic write, supersession). No Claude primitive provides a per-workspace, provenance-bearing, situationally-recalled behavioral-rule store; consistency with the existing sealed stores beats a novel surface. |
| Situational recall (fire on the turn's situation) | Claude Code hook events — `UserPromptSubmit` (current recall surface) vs `PreToolUse` on `Task`/reply tools (the ACT the situation IS) | **Compose on the EXISTING `keep_pace` contributor surface** (UserPromptSubmit / composer turn) in S4, with the situation detector as a named seam. The richer `PreToolUse` tool-event detection (Lens 1 — the hook fires on the act of dispatching / outbound-text) is named as the follow-on signal, deliberately deferred so S4 ships the store + recall on a proven surface first. |
| Context-budget cap | n/a — a named module constant | bespoke constant, mirroring `DEFAULT_TOP_N` / `DECISION_TOP_N` / `INJECTION_CHAR_CAP`. |

---

## §6 Halt triggers (builder stops + surfaces)

1. **Situation-match would need a relevance score.** If exact tag-membership cannot express a needed situation and the builder is tempted to add a BM25/keyword *score* to admit a rule, HALT — that is the killed co-citation failure reborn inside (c) (design §"biggest residual risk"). Surface for a ruling before widening the match to a score.
2. **A rule write with no derivable provenance.** If the seed/at-ruling-time authoring can't point a rule back to a store-(b) fact, HALT — an un-auditable rule violates the owner's facts-only/evidence discipline; surface rather than write a floating rule.
3. **The fence would touch a floor surface or a `CLAUDE.md` file.** S4 must not move any lens or edit any floor surface (that is S1b). If wiring the promote-to-floor mitigation (§10 Fork B) requires editing `corpus_inline` / `bundle` / a `CLAUDE.md`, HALT — that crosses into S1b's fence; carry the promote-flag in the schema only and surface the wiring as a follow-on.
4. **The rules block cannot be proven byte-separate from the fact block.** If the separate-channel AC (RSR.4) can't hold — rules leak into `_merge_by_score` or perturb the fact output — HALT; the whole point of the three-way split is that the recall disciplines don't re-merge.
5. **`RetrievalConfig` change would break a direct-config caller.** If a new field can't default to a no-op that keeps direct-config callers byte-identical (the telemetry-dir precedent), HALT and surface.

---

## §7 Ship shape + S4 / S1b / S5 sequencing

Single-component amendment on `framework/primary-persona`; one seal. Commit ladder: source edits → tests → `loam amend apply` → `loam amend seal` (standard sealed-component ritual; the builder's method per ODD §1.1).

**Recommended sequence (see §10 Fork G for the reasoning):**
1. **S4 (this plan)** — store + write-side classification + situational recall + budget cap + telemetry + a small seeded rule set. Runs live; telemetry `{situation → rules fired}` accumulates.
2. **S1b (immediately after S4, gated on S4 telemetry)** — move the situational design-lenses out of the always-on `CLAUDE.md` into store (c) and drop them from the corpus-inline always-load. Gated on evidence from S4 that situational recall reliably fires on the design-lens situation, so the lenses do not leave the floor before recall is proven to catch them. Small, reversible follow-on.
3. **S5 (later)** — automated offline rule-extraction/consolidation at the high frustration/outcome/idea threshold, populating (c) in bulk + fitting retrieval parameters against the telemetry. Separate, harder, LLM-requiring, offline.

---

## §10 Owner-decision forks (surface for GO) + recommendations

Each fork names the decision, the options, and my recommendation. Where the design under-determines, I have LOOSENED and named the fork rather than silently picking (F4).

### Fork A — where the rules store lives + its schema
**Options:** (1) sibling `<memory_dir>/rules/` markdown store mirroring `decision_ledger.py`; (2) reuse the corpus (`feedback_*.md`); (3) a DB table.
**Recommendation: (1).** Composes with the sealed decision/episode store patterns (atomic write, supersession, human-prunable — the owner's round-2 "rule-list stays human-reviewable/prunable"); stdlib-only, no API key, no embeddings. Reusing the corpus (2) is wrong — the corpus is the always-on-ranked pool S1a is *carving away from*; rules are situational, not topical. Proposed schema fields: `directive`, `situation` (tag set — see Fork B), `provenance` (paths to (b) records), `status`, `strength` (optional budget-arbitration weight), `floor_promote` (Fork B mitigation flag), `date`, `source`. *Confidence: high.*

### Fork B — how a rule's situation is represented + matched (THE load-bearing fork)
**Options for representation:** (1) controlled-vocabulary situation TAGS matched by exact set-membership; (2) keyword/predicate triggers (statistical); (3) embedding similarity; (4) hybrid.
**Recommendation: (1) — explicit situation tags, exact-match.** This is the *structural* guarantee over the *statistical* one: a rule fires only when the turn's situation is in its tag set — no score, no relevance race — so the design's #1 risk (over-injection reborn inside (c)) cannot enter through loose matching. Reject (2)/(3): keyword/embedding matching IS the co-citation-style statistical trigger the design killed for measuring net-harmful, and (3) needs an API key (forbidden).

**Sub-fork B2 — how the current turn's situation is DETECTED (the biggest open design question).** The recall envelope is thin: it carries `prompt`, `workspace.project_dir`, `keep_pace.last_topic` — it does NOT announce "I am about to dispatch an agent" or "I am writing outbound text." Detecting the situation reliably is the hard part.
- **B2a** detect from prompt+anchor text (deterministic classifier) — available day-one, but weak (the prompt rarely announces the situation).
- **B2b** detect from tool-use events (`PreToolUse` on `Task` = dispatching; on a reply tool = outbound-text) — the Claude-native, structurally-correct signal (the hook fires on the *act*), but a bigger surface + a different injection channel.
- **B2c** detect from a threaded persona task-context slot — cleanest, but needs a producer that doesn't exist yet.

**Recommendation for B2:** ship the store + tag schema + exact-match recall with a **conservative B2a detector as a NAMED, pluggable seam**, and design it so B2b/B2c signals feed the same seam later without reshaping the store. Lean the detector toward UNDER-firing (high precision): the error asymmetry says over-fire = over-injection reborn (expensive, the failure the whole redesign fights); under-fire = a missed rule (bad, but the design's own mitigation covers it — promote an important-but-hard-to-detect rule to the always-on floor (a) via the `floor_promote` flag rather than fire it loosely). *Confidence: medium on the representation (high), lower on detection — this is the fork most worth the owner's eye.*

### Fork C — the context-budget dial
**Two numbers:** (1) per-pull rule cap; (2) the fact→rule extraction threshold.
**Recommendation:** (1) a named `SITUATIONAL_RULE_CAP` hard cap (propose **3**, mirroring `DECISION_TOP_N`) + a byte sub-budget within the existing 5000-char ceiling — a structural guarantee the owner's governing constraint demands, tunable and reversible-to-zero. (2) the extraction *threshold* is primarily S5's dial (automated derivation); in S4 the "threshold" is human judgment at authoring time, and the schema records WHY a rule cleared it (a `frustration`/`bad-outcome`/`key-idea` marker + provenance) so S5 has a target to fit. *Confidence: high on the cap; the threshold value itself is S5's to tune.*

### Fork D — rule ↔ fact provenance
**Recommendation:** `provenance:` = a list of paths to store-(b) records (decision records / episodes / corpus); a rule with no provenance is invalid by construction (write API rejects — AC.RSR.2). This makes every rule auditable to evidence — info-trust applied to the rule store, which is the discipline the owner already runs. *Confidence: high.*

### Fork E — how situational rules compose with the floor (a) + the fact recall (b)
**Recommendation:** rules inject as a SEPARATE labeled block (e.g. `[behavioral-rules]`) on a SEPARATE budget, NOT merged into `_merge_by_score`. Context order: floor (a) unconditional → situational rules (c) → topical facts (b). This preserves the design's "separate recall disciplines" and is what structurally prevents rules from crowding facts (AC.RSR.4). *Confidence: high on the separation; the exact ordering is minor.*

### Fork F — reversibility (this changes behavioral injection every turn)
**Recommendation:** the entire (c) injection sits behind a named master lever (mirroring `RANK_CONSTITUTIONAL_FLOOR`); `SITUATIONAL_RULE_CAP = 0` or the flag off reverts to byte-identical pre-S4 (AC.RSR.6). Rules live in a separate store that can be pruned/emptied without touching facts. *Confidence: high.*

### Fork G — S4 / S1b / S5 sequencing
**Recommendation:**
- **S1b sequences immediately AFTER S4, not within it.** S4 *creates* the situational-recall destination, so S1b *can* co-land — but moving the load-bearing design lenses off the always-on floor onto brand-new, unproven recall is a high-cost bet: if situational recall under-fires on a design turn, a design lens silently goes missing from loam's own build methodology. Apply the design's own "prove before you flip live behavior" logic (S1a already deferred S1b for exactly this): S4 can author the lens rules INTO the store (ready, still also on the floor), but the *removal* from always-on is a separate gated flip after S4 telemetry shows the design-lens situation reliably matches. S1b becomes a small, safe, reversible follow-on.
- **S4 / S5 split at store-vs-extraction.** S4 ships the store + situational recall + write API + a small manual/seeded rule set; S5 is the automated offline extraction engine that derives rules from accumulated facts at the high threshold. Splitting tightens both ACs (store+recall is structural, bounded risk; extraction-judgment is a harder, LLM-requiring, offline problem the owner explicitly wants kept conservative and not an "unbounded auto-writer"). Shipping them together would couple a structural change to an unproven judgment engine. *Confidence: high on both.*

---

## §15 Backwards-compat verification

The KP1 / FBMU / FBM-FILTER / SRF / RDP / RTEL / DLG suites must stay green (AC.RSR.8). New `RetrievalConfig` fields default to no-ops so direct-config callers (tests, the omnibus-penalty suite) are byte-identical (the telemetry-dir precedent). The fact/episode/decision recall output is unchanged for any turn regardless of the rules channel.

## §16 Halt-and-surface findings (raised at plan-authoring)

1. **The situation-detection surface is genuinely under-determined by the design (F2, named risk).** The design specifies situational recall but not how a turn's situation is known; the current recall envelope carries only prompt + last-topic + workspace. This is the load-bearing open question (Fork B2). Named rather than silently resolved; recommendation is the conservative-detector-as-seam + promote-uncertain-to-floor, but the owner's eye is wanted here.
2. **The three-way split's derivation dependency persists (design §"second risk").** A fact whose rule is never authored is behaviorally inert. S4's at-ruling-time authoring + S5's offline pass mitigate but do not eliminate it; something still has to notice a fact *should* change behavior. Carried, not solved, in S4.
3. **`floor_promote` wiring crosses into S1b's fence.** The mitigation (promote an uncertain-situation rule to the always-on floor) requires the floor surfaces to read the flag — but editing those surfaces is S1b, not S4. S4 carries the flag in the schema only; the actual floor-wiring is a follow-on (Halt trigger 3). Named so it isn't silently widened.

## §14 Method-decision register (populated at build + seal)

*Placeholder — populated by the builder at build time (D-Q.\* fork resolutions from §10) and by `loam amend seal --plan-doc` (commit SHAs) at seal time.*

- **D-Q.A** — store location + schema (Fork A): _pending build._
- **D-Q.B** — situation representation + detection seam (Fork B): _pending build._
- **D-Q.C** — budget cap value + threshold marker (Fork C): _pending build._
- **D-Q.D** — provenance validation (Fork D): _pending build._
- **D-Q.E** — separate-channel injection + ordering (Fork E): _pending build._
- **D-Q.F** — reversibility lever (Fork F): _pending build._
- **D-build.\*** — source / apply / seal SHAs: _backfilled at seal._

---

## §11 Provenance trail

- Design: `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` — §"The three stores + their distinct recall mechanisms" (the (c) row: situational recall, small budget, provenance→(b)); §"the single biggest residual risk" (situational recall unproven, over-injection-reborn failure mode + promote-uncertain-to-floor mitigation); Stage 4 in the staged build plan.
- Owner refinements: `owner-refinements-2026-07-02.md` #4 (the three-way split; "guidance on how to behave is not a memory, it's a prompt"); `owner-refinements-round2-2026-07-02.md` (a single utterance → a memory always, a rule only sometimes; LIBERAL fact ingest / CONSERVATIVE high-threshold rule extraction; the context-window budget as the governing dial; rules carry provenance; rule-list stays human-reviewable/prunable).
- Landed code pinned Tier-0: `keep_pace/retrieval.py` (`_merge_by_score` store-(b) pipeline, `_decision_hits` third-source pattern, `RANK_CONSTITUTIONAL_FLOOR` reversibility-lever pattern at :222, the two live resolvers `_resolve_live_config` :1167 / `_resolve_composer_config` :1301, the envelope shape at the contributor :1283); `keep_pace/retrieval_telemetry.py` (the pure-observation fail-open recorder to extend); `decision_ledger.py` (`write_decision` :145, `DecisionRecord` :96 — the store shape to mirror; `DECISION_TOP_N` :64).
- Predecessor plans: `docs/plans/memory-redesign-s1-ground-floor-extraction.md` §5 (S1b deferral gated on S4's situational-recall destination); `docs/plans/memory-redesign-s2-recency-relocation-discovery-prioritization.md` (the store-(b) discovery/prioritization split S4 leaves intact).

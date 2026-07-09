# Memory redesign — Write-side facts-discipline (the write contract for the three-way split's store (b))

**Status:** BUILD-READY PENDING OWNER GO on the §10 forks. Plan-only; no implementation code authored.
**Component (sealed):** `framework/primary-persona` — advances the existing sidecar (`new_component: false`).
**Design source:** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (Stage 4's "write-side fact/rule discipline" half + the "facts-only writes — adopted, scoped to (b)" push-back) + owner refinements (`owner-refinements-2026-07-02.md` #3/#4, `owner-refinements-round2-2026-07-02.md` — a single utterance → a memory always / a rule only sometimes; LIBERAL fact ingest / CONSERVATIVE high-threshold rule extraction).
**Predecessors (landed):** S1a ground-floor extraction (sealed); standing retrieval telemetry (sealed); S2 ranker — relevance-threshold recall + event-recency prioritizer (sealed); S4 rules store + situational recall + the RULE-write provenance validation (sealed, `origin/main` tip `a1166b8d`); the sealed volatility classifier (`classify_volatility`, `file_memory.py`) and the decision-ledger write-side + steer (`decision_ledger.py`, D2 — persona writes the record at ruling time).

---

## §1 Objective

Give store (b) — the facts/memory store — a WRITE-SIDE discipline that keeps it a store of *provable facts*, not the model's thoughts: every memory written is either a record of something that specifically happened (event / state-after-work / verified finding) or an ATTRIBUTED expression ("X said/assessed/predicted/planned Y on date Z"), never a bare opinion / speculation / plan asserted as truth — and the fact-vs-rule cleave is drawn at write time (a memory always; a rule only sometimes), so a behavioral consequence lands in store (c) as a provenance-bearing rule rather than as a truth-claim in (b).

One sentence: **make "only write provable facts" a structural property of every store-(b) write — by typing each record's epistemic kind at write time and never serving a non-fact AS a fact — WITHOUT adding an admission gate that would suppress the owner's LIBERAL fact-ingest.**

This stage is the FACT half of S4's "write-side fact/rule discipline." S4-as-built delivered the RULE half (the store (c) + situational recall + the rule-write provenance requirement). The fact-side "facts only, not thoughts" discipline was named in the design but not built; this stage builds it.

---

## §2 Predecessors / context

This plan composes against, and does not reshape, five sealed surfaces:

1. **The volatility classifier (`classify_volatility`, `file_memory.py`).** A deterministic, stdlib-only, write-time classifier that TAGS a record's operational-freshness kind at ingest and leans fail-safe (any error → DURABLE / visible, never drops). This stage adds a SIBLING classifier on a *different* epistemic axis (provable-fact vs opinion/speculation/plan) with the *same* shape: tag at write, never reject, fail-safe toward FACT, read-side annotates rather than excludes. The volatility axis (how fresh) and the epistemic axis (is-it-a-fact) are orthogonal and both apply.
2. **The liberal-ingest write path (`write_episode` + the salience gate, `file_memory.py`).** A turn the salience gate calls JUNK is still WRITTEN — diverted to `COLD_SUBDIR` (not indexed, never served from the hot pool), never dropped. That is the owner's liberal-ingest policy already in code: *write everything; gate what is SERVED; never delete.* This stage's discipline is the same shape one axis over: write everything, TAG epistemic kind, gate what is served AS A FACT, never delete. The liberal-ingest premise is preserved by construction (§10 Fork C).
3. **The decision-ledger write-side + D2 (`decision_ledger.py`).** D2 (2026-06-09, owner-ratified): the in-session persona — which HOLDS the entity context — writes the record at ruling time; auto-extraction risks confidently-wrong records. This stage COMPOSES with D2: the write-side facts-discipline is the persona applying "write it as a provable fact + classify fact-vs-rule" as it writes, NOT a new auto-extractor. A decision is already a fact by construction (the EVENT "Luke ruled X on date Y, source Z" is provable even when the ruling's CONTENT is a preference) — so decision records are fact-typed and untouched.
4. **S4's rule-write provenance contract (`rules_store.py`, `write_rule`).** A rule is REJECTED without ≥1 provenance pointer to a store-(b) record (`RuleValidationError`). The fact-vs-rule cleave this stage draws at write time TERMINATES in that existing contract: when a fact carries a behavioral consequence over the high threshold, the persona authors the rule via `write_rule`, pointing provenance back at the fact just written. This stage adds the DISCIPLINE + the default (fact-only unless the threshold is cleared); it does not reshape `write_rule`.
5. **The decision-ledger ruling-gap steer (`detect_and_flag_ruling_gap` / `consume_pending_steer` / `run_catch_up_sweep`).** The proven steer-not-block, fail-open enforcement pattern: a turn-close detector flags a pending steer; the next turn reads-and-clears a model-facing nag. §10 Fork D reuses this exact pattern (as an option) for the epistemic discipline; it is NOT rebuilt.

The load-bearing point the design names: loam's memory only earns the owner's trust if a record it serves as a fact IS a fact. The volatility work closed one leak (stale operational status served as current); this stage closes the sibling leak (a thought served as a verified fact — the confidently-wrong-recall failure Lens 0's protection floor forbids).

---

## §3 Scope

### In scope (this stage)
1. **The verifiability discipline (the write contract).** A written, applyable test — given a candidate memory, is it fact-eligible for store (b)? — covering the fact classes (event / state-after-work / verified finding / attributed expression) and the non-fact classes (bare opinion / speculation / plan). Discoverable at the write surface. This is the human-facing contract; the classifier (below) is its machine backstop.
2. **A deterministic epistemic-type classifier at write time.** A `classify_epistemic_type` sibling of `classify_volatility` in `file_memory.py`: stdlib-only, no LLM/API, tags each store-(b) write with a machine-readable epistemic kind, fail-safe toward FACT (only affirmative opinion/speculation/plan grammar tags a record non-fact; ambiguity and any classifier error → FACT). Emitted as an additive frontmatter field (the AC-driven schema-field precedent set by `volatility:`).
3. **The read-side protection.** A non-fact-typed record is never served AS a verified fact: it is annotated on recall (mirroring `VOLATILE_SOFT_ANNOTATION`) so the substance is still exposed but marked not-a-verified-fact — never silently withheld (liberal-ingest + never-drop preserved).
4. **The attribution rule.** The discipline + classifier recognize that an opinion/prediction/plan authored WITH an attribution (who + when) is fact-eligible (a provable record that it was expressed); the same content as a bare truth-claim is not. This is how "facts only" keeps the owner's "record that he said it" (round 2) without storing unprovable claims.
5. **The fact-vs-rule write-time cleave + the observed-preference resolution.** The documented default: a memory always; a rule only when the high behavioral threshold is cleared (significant frustration / bad-enough outcome / key idea), authored via S4's `write_rule` with provenance back to the fact. Resolves the owner's open boundary question: an observed preference writes the OBSERVATION as a fact in (b) and the behavioral PRIOR as a provenance-bearing rule in (c) — never the inferred generalization as a bare fact in (b).
6. **A named reversibility lever** — reverts the discipline to a no-op (writes byte-identical to pre-stage; read-side byte-identical).

### Out of scope (deferred)
- **S5 — automated offline rule-EXTRACTION / consolidation.** This stage ships the WRITE-TIME discipline + a deterministic epistemic TAG applied AS FACTS ARE WRITTEN (D2, persona-driven). S5 is the OFFLINE engine that later MINES accumulated facts to DERIVE rules in bulk at the high threshold and fits retrieval parameters. The boundary line: this stage produces clean, epistemic-typed facts; S5 consumes them. This stage runs NO extraction engine, makes NO algorithmic "was the frustration significant enough" judgment, and mines NO accumulated corpus. (§10 Fork E.)
- **S1b — moving the situational design-lenses off always-on `CLAUDE.md`.** Unrelated fence (the floor surfaces); sequenced separately per S4 §7.
- **An LLM-grade verifiability judge.** True verifiability ("does a source exist that confirms this") is the persona's judgment (D2), not something a regex can decide. The deterministic classifier is a crude-tell backstop, not a verifier. Any LLM judge is out (no API key; hot-path LLM forbidden).
- **Retro-typing the existing episode corpus.** No migration; pre-stage records are untyped and read-side fail-safe treats an absent tag as FACT (byte-identical to today). Bulk retro-typing, if ever wanted, is an S5-adjacent offline pass.

---

## §4 — Acceptance criteria

AC IDs are scope-descriptive: **AC.WFD.\*** (Write-side Facts-Discipline). Each is outcome-shape — the method (which grammar tells, regex vs table, exact field name, annotation string) is inferable from the constraints but no AC states HOW.

### AC.WFD.1 — the verifiability discipline classifies candidates correctly
Given a fixture of candidate memories spanning the fact classes (an event that occurred; state after work; a verified finding) and the non-fact classes (a bare opinion; a bare prediction/speculation; a bare plan/intent), the discipline yields the fact-eligible verdict for the fact classes and the not-a-fact verdict for the non-fact classes. *Verified:* `test_AC_WFD_1_*` — a labeled candidate fixture is classified with the expected fact/non-fact verdict per row.

### AC.WFD.2 — every store-(b) write carries a deterministic epistemic type, fail-safe to fact
A record written to store (b) carries a machine-readable epistemic-type assigned at write time with no LLM/API call; a clearly event/state/finding body is typed fact, a clearly opinion/speculation/plan body is typed non-fact, and an ambiguous body OR any classifier error yields fact (the never-suppress direction). *Verified:* `test_AC_WFD_2_*` — write three bodies (clear-fact, clear-opinion, ambiguous), read them back, assert the type field + that the ambiguous and the error path both resolve to fact.

### AC.WFD.3 — a non-fact is never served AS a verified fact
Over the read path, a record typed non-fact surfaces marked as not-a-verified-fact (its substance still exposed — never silently withheld), and a record typed fact surfaces unmarked. No recall path presents a non-fact-typed record as a verified fact. *Verified:* `test_AC_WFD_3_*` — recall a non-fact-typed record and assert the not-a-verified-fact marker on it and its absence on a fact-typed record.

### AC.WFD.4 — attribution converts a thought into a fact
A thought/opinion/prediction/plan authored WITH an attribution (an author + a time — "Luke called the design elegant on <date>") is fact-eligible; the same content as a bare truth-claim ("the design is elegant") is not. *Verified:* `test_AC_WFD_4_*` — the attributed form classifies fact-eligible; the bare form classifies not-a-fact.

### AC.WFD.5 — the fact-vs-rule cleave at write time; observed-preferences resolved
An observed preference produces a fact recording the OBSERVATION (always) and, only when the behavioral threshold is cleared, a SEPARATE rule in store (c) carrying provenance back to that fact; the fact store never holds the inferred generalization as a bare fact, and the default when the threshold is NOT cleared is fact-only (no rule). *Verified:* `test_AC_WFD_5_*` — authoring an observed preference lands the observation in (b) and (threshold cleared) the behavioral prior as a provenance-bearing rule in (c); with the threshold not cleared, only the (b) fact is written and no rule appears.

### AC.WFD.6 (outcome-altitude) — the discipline operates end-to-end through the real write + read path, no pre-arranged state
Through the production fact-write entry-point invoked with no pre-arranged state: an event/state/finding body is written fact-typed and recalls unmarked as a fact; an opinion-shaped body is written non-fact-typed and recalls marked not-a-verified-fact; BOTH are written to disk (neither is suppressed). *Verified:* `test_AC_WFD_6_OA_*` — the production write path + the production recall entry-point, two contrasting bodies, all three assertions (typed-correctly / marked-correctly-on-recall / both-persisted).

### AC.WFD.7 (liberal-ingest preservation) — no write is suppressed by the discipline
The set of records WRITTEN to disk for a given candidate is identical with the discipline active vs the named lever off: the discipline ADDS an epistemic tag + a read-side marker and never rejects, drops, gates, or re-routes a write away from disk. *Verified:* `test_AC_WFD_7_*` — the on-disk write set (paths + bodies modulo the added tag) is identical lever-on vs lever-off; no candidate that wrote before fails to write now.

### AC.WFD.8 (reversibility) — a named lever reverts to byte-identical pre-stage writes + recall
With the discipline's lever off, fact writes carry no epistemic tag and the read-side renders byte-identical to pre-stage; nothing on disk is migrated or deleted; a record written before the stage (no tag) reads back fail-safe as a fact; flipping the lever on re-applies typing to new writes. *Verified:* `test_AC_WFD_8_*` — lever-off write + recall equal the pre-stage baseline byte-for-byte; a tagless legacy record recalls as a fact; the store files are untouched by the flip.

### AC.WFD.9 — no regression; deterministic-only; S5 boundary held
The KP1 / FBMU / FBM-FILTER / SRF / VOL / SUP / DLG / RSR suites stay green; the discipline adds no LLM/API call to any write or read path; no offline extraction/consolidation engine is introduced (the S5 boundary). Fail-open: a classifier error yields a fact-typed write and never breaks the turn. *Verified:* full-suite run + `test_AC_WFD_9_*` (a raised classifier error routes to fact and the write completes).

**Ladder-up.** AC.WFD.\* → the memory-redesign objective (store (b) holds provable facts, so the best on-file context per turn is TRUE context, no confidently-wrong recall) → AC.PO.1 (reduce the user's translation burden — a memory the user can trust is the Lens-0 protection half: no inventing, no confabulation) + AC.PO.2 (add to the harness toolkit — a reusable write-time epistemic-typing discipline other stores can adopt) → Lens 0 prime directive. The never-serve-a-thought-as-a-fact guarantee is squarely the Lens-0 "protection: avoid the known ways AI betrays its users by default (inventing things)" — sized to the damage its failure does (a trusted-but-false memory poisons every downstream decision).

---

## §5 Sealed-component fence

**Component:** `framework/primary-persona` (advances the sidecar; `new_component: false`).

**Touched:**
- EDIT `framework/primary-persona/src/loam/primary_persona/file_memory.py` — a NEW `classify_epistemic_type` (sibling of `classify_volatility`), its named tell-patterns + the attribution recognizer, the additive `epistemic:` frontmatter field emitted by `write_episode`, and the named reversibility lever. Mirrors the volatility classifier's structure and fail-safe direction exactly.
- EDIT `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py` — the read-side not-a-verified-fact annotation on a non-fact-typed record (mirroring the `VOLATILE_SOFT_ANNOTATION` application at retrieval.py:~598), gated behind the same lever, additive and fail-open.
- NEW discipline doc — the verifiability test + the fact-vs-rule cleave + the attribution rule + the observed-preference resolution, at a durable path the persona reads (builder's call per ODD §1.1; suggested `docs/design/memory-write-side-facts-discipline.md`).
- NEW `framework/primary-persona/tests/test_AC_WFD_*`.

**NOT touched (fence integrity):** `classify_volatility` (a sibling is ADDED beside it; the volatility axis is unchanged); `write_decision` / `decision_ledger.py` core (a decision is fact-typed by construction); `write_rule` / `rules_store.py` core (the rule-write provenance contract is REUSED, not reshaped); `_merge_by_score` and the store-(b) relevance/recency ranking semantics; the salience gate + `COLD_SUBDIR` routing (the liberal-ingest tier is orthogonal and unchanged); the floor surfaces (`corpus_inline_session_start.py`, `bundle.py`, `principle_reminder.py`); any `CLAUDE.md` file; `settings.json`; `RetrievalConfig`'s existing fields' semantics (any new field is additive with a no-op default — the telemetry-dir precedent).

**Blast radius:** `write_episode` and `retrieve()` are on the live per-turn path (main-session turn-close write + UserPromptSubmit/composer/subagent recall), but the change only ADDS a tag at write and an annotation at read, both behind a named lever, both fail-open, and neither rejects a write nor removes a record from recall.

**Rollback:** git-revert the seal, OR flip the lever off — new writes carry no tag and recall renders byte-identical to pre-stage; nothing on disk is deleted or migrated (a tagless legacy record reads back as a fact).

---

## Primitive check (new mechanism introduced)

| New mechanism | Native primitive considered | Choice |
|---|---|---|
| Write-time epistemic-type classification of a memory | Claude Code memory / an LLM classifier at write; the sealed `classify_volatility` deterministic write-time classifier | **bespoke — mirror the sealed `classify_volatility`** (deterministic, stdlib-only, tag-at-write, fail-safe, read-side annotate). No Claude primitive types a per-record epistemic kind; an LLM classifier is forbidden on the hot write path (no API key) and D2 already puts the real verifiability judgment in the persona — the deterministic layer is only the crude-tell backstop, exactly the role `classify_volatility` plays for staleness. |
| Read-side not-a-verified-fact annotation | n/a — reuse the `VOLATILE_SOFT_ANNOTATION` render path | bespoke constant + the existing annotation seam in `retrieval.py`. |
| Write-side discipline enforcement (optional steer) | Claude Code hook / the sealed decision-ledger `detect_and_flag_ruling_gap` steer | **compose on the EXISTING steer pattern** if the steer fork (§10 Fork D) is taken — the proven Stop-seam detector + next-turn nag, steer-not-block, fail-open; NOT a new mechanism. Recommended DEFER (the tag + read-annotation already deliver the protection; §10 Fork D). |

---

## §6 Halt triggers (builder stops + surfaces)

1. **The classifier would REJECT a write.** If the epistemic discipline is tempted to block, drop, or re-route a store-(b) write (rather than tag-and-annotate), HALT — that breaks the owner's LIBERAL fact-ingest (the #1 F2 tension, §10 Fork C). The discipline tags; it never gates admission.
2. **The classifier would fail toward NON-FACT on ambiguity.** If a classifier error or an ambiguous body would resolve to a non-fact tag (suppressing a legitimate fact on recall), HALT — the fail-safe direction is FACT (mirror `classify_volatility`'s never-drop floor); leaning the other way manufactures the suppression the liberal-ingest premise forbids.
3. **The fence would touch `classify_volatility`, `write_decision`, `write_rule`, or `_merge_by_score`.** The epistemic axis is a SIBLING, not a modification of the volatility axis or the ranking pipeline; a decision/rule already has its store. If closing an AC seems to require editing those cores, HALT — the outcome should be reachable by an additive sibling classifier + a read annotation.
4. **A `RetrievalConfig` / schema change would break a direct-config caller or the schema-minimal parser.** If the new `epistemic:` field can't default to a no-op that keeps direct-config callers and legacy tagless records byte-identical (fail-safe to fact), HALT and surface.
5. **The discipline would require an LLM/API call on the write or read path.** True verifiability is the persona's judgment (D2), not the classifier's; if an AC seems to need an LLM verdict at write/read time, HALT — that is either a persona-discipline item (documented, not coded) or an S5 offline item, never a hot-path model call.
6. **The build would start an extraction engine.** If the fact-vs-rule cleave tempts an automated pass that mines accumulated facts to derive rules, HALT — that is S5, out of this fence (§10 Fork E). This stage authors a rule only via the persona's at-write-time `write_rule`, one record at a time.

---

## §7 Ship shape + sequencing

Single-component amendment on `framework/primary-persona`; one seal. Commit ladder: source edits → tests → `loam amend apply` → `loam amend seal` (the standard sealed-component ritual; the builder's method per ODD §1.1).

Sequencing: this stage sits AFTER S4 (it completes S4's write-side fact half; it reuses S4's `write_rule` provenance contract) and is INDEPENDENT of S1b (different fence) and S5 (this stage produces the clean typed facts S5 will consume). It can land immediately; S5 depends on it, not the reverse.

---

## §10 Owner-decision forks (surface for GO) + recommendations

Each fork names the decision, the options, and my recommendation. Where the design under-determines, I have LOOSENED and named the fork rather than silently picking (F4).

### Fork A — the verifiability test (what makes a candidate a fact)
**Options:** (1) event/state/finding + attributed-expression are fact-eligible, bare opinion/speculation/plan are not; (2) only literal events (no findings, no attributed expressions); (3) anything the persona is confident of.
**Recommendation: (1).** It matches the owner's words exactly ("records of things that specifically happened: decisions, things learned, state after work") AND keeps the owner's round-2 "record that he said it" without storing unprovable claims — via the attribution move (Fork B). Option (2) loses verified findings ("the ranked-pool cap is `DEFAULT_TOP_N=5`") which are provable and load-bearing. Option (3) reintroduces exactly the thoughts-as-facts leak the stage exists to close. **The test, in one line:** *"Could someone else, given the cited source, confirm this happened or is true? An event / state / verified finding → yes → fact. A bare how-I-feel / what-I-predict / what-I-plan → no → not a fact; attribute it or route its consequence to a rule."* *Confidence: high — it is the owner's own definition, mechanised.*

### Fork B — how an opinion/plan/prediction can still be recorded (the attribution move) — THE tension-dissolving fork
**The tension (F2):** the owner says BOTH "only provable facts" AND "record that he said 'god damn it that was annoying'." A bare opinion is not provable; but the EVENT of it being expressed is.
**Recommendation: ATTRIBUTION.** A thought becomes a fact by attribution — "the design is elegant" (opinion, not a fact) is recorded as "Luke assessed the design as elegant on <date>" (a fact about an utterance, provable: he said it). So "facts only" does NOT mean discard thoughts; it means record them AS attributed events, never as bare truth-claims. This is the structural partition that dissolves the whole "provable-only vs record-everything" tension: liberal ingest preserved (we record that the thought was expressed), facts-only preserved (what is stored is the provable utterance-event), and the read-side never serves "the design is elegant" as ground truth — only "Luke called it elegant on <date>," which is true. *Confidence: high — this is the load-bearing insight of the stage; it is why the classifier can be tag-only and never needs to reject.*

### Fork C — enforcement shape (the liberal-ingest safety fork)
**Options:** (1) a documented DISCIPLINE only (persona judgment, no code); (2) discipline + a deterministic TAG-and-ANNOTATE backstop (no admission gate); (3) a hard verifiability GATE that rejects non-fact writes.
**Recommendation: (2).** Reject (3) outright — a reject-gate suppresses legitimate facts and BREAKS the owner's LIBERAL ingest (disk is cheap, condense later); it is the #1 halt trigger. Reject (1)-alone — a pure-prose discipline is a behavioral promise with no enforceable, testable outcome, and loam's own doctrine escalates a discipline that matters to STRUCTURAL enforcement. (2) is the structural-over-behavioral answer: the persona's judgment (D2) is the primary classifier; a deterministic `classify_epistemic_type` (sibling of `classify_volatility`) is the backstop that (a) makes the outcome machine-testable, (b) gives the read-side a signal to annotate, and (c) NEVER rejects — it tags, and the read-side annotates. The liberal-ingest premise is a structural invariant (AC.WFD.7): the write SET is unchanged; only typing + rendering are added. *Confidence: high on tag-and-annotate; the exact tell-set is the builder's to tune (Fork F).*

### Fork D — the optional write-time steer
**Options:** (1) tag + read-annotation only; (2) additionally a next-turn STEER (reuse `detect_and_flag_ruling_gap`'s pattern) when a fact-labeled write carries strong opinion/speculation tells, or when a fact with an obvious behavioral consequence was written with no rule authored.
**Recommendation: (1) for this stage; carry (2) as a named follow-on.** The tag + read-annotation already delivers the protection (a thought is never served as a fact) with a tight, single-surface fence. The steer adds a Stop-seam surface + a next-turn nag — worthwhile for the fact-vs-rule "you should have authored a rule" nudge, but it is additive and better sequenced after the typing is live and telemetry shows how often the persona under-authors rules. Deferring keeps this stage lean (remove-before-add). *Confidence: medium-high — the steer is genuinely optional; the owner may want the rule-authoring nudge sooner, which is why it is a fork not a silent drop.*

### Fork E — the S5 boundary (what this stage does NOT do)
**Recommendation:** this stage is the WRITE-TIME discipline + a deterministic epistemic TAG applied as the persona writes (D2, one record at a time). It runs NO offline engine, mines NO accumulated corpus, and makes NO algorithmic "was the frustration significant enough for a rule" judgment — those are S5. The clean line: **this stage produces epistemic-typed facts; S5 consumes them to derive rules in bulk + fit parameters.** The `trigger` marker S4 already records on a rule (`frustration`/`bad-outcome`/`key-idea`) is the seam S5 will fit against; this stage populates it only when the persona authors a rule by hand. *Confidence: high — the split mirrors S4/S5's own store-vs-extraction cleave.*

### Fork F — the epistemic tell-set + fail-safe direction
**Recommendation:** name the crude opinion/speculation/plan tells (e.g. bare-leading "I think / probably / likely / it seems / in my opinion" for opinion/speculation; "next I'll / the plan is / I'm going to / TODO" for plan/intent) as a deterministic pattern set, with the fail-safe direction FACT (only an affirmative non-fact tell ABSENT an attribution and ABSENT a durable-fact signal tags non-fact; ambiguity → fact), exactly mirroring `classify_volatility`'s "hard tell absent a durable veto" structure. The attribution recognizer (Fork B) is the veto that de-escalates a tell back to fact. The exact regex set is the builder's to author + tune against the AC.WFD.1 fixture. *Confidence: high on the fail-safe direction + the attribution veto; medium on any specific tell (tunable, and backstopped by the persona's judgment + the never-drop floor, so a missed tell only under-annotates, never suppresses).*

### Fork G — the reversibility lever + legacy records
**Recommendation:** a single named module lever (mirroring `RANK_CONSTITUTIONAL_FLOOR`); off → no `epistemic:` field emitted + no read-side annotation → byte-identical pre-stage. Legacy tagless records read back fail-safe as FACT (absent tag ⇒ fact), so no migration and no retro-typing. Flipping on applies typing to NEW writes only. *Confidence: high.*

---

## §15 Backwards-compat verification

The KP1 / FBMU / FBM-FILTER / SRF / VOL / SUP / DLG / RSR suites must stay green (AC.WFD.9). The `epistemic:` frontmatter field is additive and AC-driven (the `volatility:` precedent — a purposeful field tied to an AC, not a speculative schema expansion); the schema-minimal parser accepts what the writer emits. A legacy record with no `epistemic:` field reads back as a fact (fail-safe). Direct-config callers and the store-(b) recall output for a fact-typed turn are byte-identical to pre-stage. No data migration; the episodes/decisions/rules stores and the derived index are untouched.

## §16 Halt-and-surface findings (raised at plan-authoring)

1. **The "provable facts only" vs "LIBERAL ingest" tension is real and is resolved structurally, not balanced (F2, named).** They conflict only if "provable-only" is read as an admission GATE. It is not: LIBERAL governs VOLUME (write everything), provable-only governs CONTENT-KIND (type each record; never serve a thought as a fact). The partition — write-set unchanged, epistemic typing added — is AC.WFD.7, and the attribution move (Fork B) means even a thought is recordable (as an attributed event). The reject-gate reading is Halt trigger 1. This is the single most important thing to get right; it is why the enforcement is tag-and-annotate, never gate.
2. **The deterministic classifier is a crude backstop, not a verifier (F2, named limitation).** `classify_volatility` works because operational tells are crisp; opinion/speculation tells are crisp at the GRAMMAR level but not at the SEMANTIC level ("I think the test passed" is a hedged FACT; "I think this is elegant" is an opinion). The classifier cannot always tell these apart — which is exactly why it is a backstop behind the persona's judgment (D2), tag-only, fail-safe-to-fact, and read-annotate (not reject). The residual error is mild over-annotation, never a lost fact or a hard-false fact. Named, not hand-waved.
3. **The derivation dependency persists (design §"second risk", carried from S4 §16.2).** A fact whose behavioral consequence SHOULD become a rule but the persona does not author one at write time is behaviorally inert until S5. This stage's default is deliberately conservative (owner's high rule-extraction threshold), so it INTENTIONALLY under-authors rules and leans on S5 for bulk derivation. The gap is carried, not closed; Fork D's optional steer is the mitigation if the owner wants earlier nudging.
4. **The attribution move could become a loophole — and it is benign by construction (F2, named).** If "attribute it" makes any opinion fact-eligible, the model could attribute everything and re-bloat (b) with attributed-opinions. Under the owner's liberal-ingest + relevance-gated recall + the read-side not-a-verified-fact annotation, this is harmless: volume does not hurt (relevance-gated), and an attributed-opinion is never served as ground truth (annotated). Named so it is not mistaken for a defect.

## §14 Method-decision register (populated at build + seal)

*Placeholder — populated by the builder at build time (D-Q.\* fork resolutions from §10) and by `loam amend seal --plan-doc` (commit SHAs) at seal time.*

- **D-Q.A** — the verifiability test (Fork A): _resolved at build._
- **D-Q.B** — the attribution move (Fork B): _resolved at build._
- **D-Q.C** — enforcement shape: tag-and-annotate, no gate (Fork C): _resolved at build._
- **D-Q.D** — optional steer defer/take (Fork D): _resolved at build._
- **D-Q.E** — S5 boundary (Fork E): _resolved at build._
- **D-Q.F** — tell-set + fail-safe direction (Fork F): _resolved at build._
- **D-Q.G** — reversibility lever + legacy handling (Fork G): _resolved at build._
- **D-build.\*** — source / apply / seal SHAs: _backfilled at seal._

### Commit SHAs

- Amendment commit: `9549c8d66d21660c7e20e4e7ffa412da4e5a18bb` —
  `chore(amend): memory-redesign-write-side-facts-discipline manifest+apply — primary-persona BASELINE+sidecar bump to 9d3f0f0`
- Seal commit: `6010edc05f79e56b2983d8cce6eda5803b828e1d` —
  `chore(seals): memory-redesign-write-side-facts-discipline — primary-persona at 9549c8d`
## §11 Provenance trail

- Design: `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` — §"What changed from v1" #3 ("facts-only writes — adopted, scoped to (b)"; "(b) holds facts only; (c) holds derived directives, each carrying a provenance pointer"); §"Where the decision-ledger cleaves" (the fact/rule cleave + the observed-preference resolution: evidence is a fact in (b), the behavioral prior is a rule in (c)); Stage 4's "write-side fact/rule discipline" half.
- Owner refinements: `owner-refinements-2026-07-02.md` #3 (memories must be FACTS; memory ≠ opinion/speculation/plan) + #4 (the three-way split; "guidance on how to behave is not a memory, it's a prompt") + the boundary question (where observed-preferences sit); `owner-refinements-round2-2026-07-02.md` (a single utterance → a memory always / a rule only sometimes; "record the memory (he said it), extract a rule only if the outcome was bad enough"; LIBERAL fact ingest / CONSERVATIVE high-threshold rule extraction; the context-window budget as the governing dial; keep the rule-list human-reviewable).
- Landed code pinned Tier-0: `file_memory.py` (`classify_volatility` :386 — the deterministic write-time classifier to mirror; `write_episode` :615 — the fact-write surface + the additive-frontmatter precedent; `SALIENCE_JUNK`/`COLD_SUBDIR` :111/:135/:697 — the liberal-ingest write-everything-gate-what-is-served precedent; `VOLATILE_SOFT_ANNOTATION` :325 + the read-side application at `keep_pace/retrieval.py` :587-603 — the read annotation to mirror; the schema-minimal parser note :1407); `decision_ledger.py` (D2 write-at-ruling-time discipline :24-26; `detect_and_flag_ruling_gap`/`consume_pending_steer` :482/:531 — the steer pattern; a decision is a fact by construction); `rules_store.py` (`write_rule` :144 + `RuleValidationError` :80 — the rule-write provenance contract the fact-vs-rule cleave terminates in; the `trigger` marker :77 as S5's seam).
- Predecessor plans: `docs/plans/sealed/memory-redesign-s4-rules-store-situational-recall.md` (§3 write-side classification, §16.2 the derivation dependency this stage carries forward, §7 S4/S1b/S5 sequencing); `docs/plans/memory-redesign-s1-ground-floor-extraction.md` (the store-(a) floor this stage does not touch).

# Memory redesign — write-side facts-discipline (the FACT half of the three-way split's write contract)

Per `docs/plans/memory-redesign-write-side-facts-discipline.md`
(build-ready pending owner GO on the §10 forks) and the ratified design
`workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md`
(Stage 4's "write-side fact/rule discipline" half + the "facts-only writes — adopted,
scoped to (b)" push-back) + owner refinements (#3 memories must be FACTS, memory ≠
opinion/speculation/plan; round 2 — a single utterance is a memory always, a rule only
sometimes; LIBERAL fact ingest / CONSERVATIVE high-threshold rule extraction). Single-
component amendment on the EXISTING `framework/primary-persona/` component; advances the
sidecar. Completes the FACT half of S4's write-side discipline (S4-as-built delivered the
RULE half — the store (c) + situational recall + the rule-write provenance requirement).

The load-bearing design point: loam's memory only earns the owner's trust if a record it
serves as a fact IS a fact. The sealed volatility work closed one leak (stale operational
status served as current); this stage closes the sibling leak (a thought served as a
verified fact — the confidently-wrong-recall failure Lens 0's protection floor forbids).
It composes with D2 (the persona writes the record at write time; the deterministic
classifier is the crude-tell backstop, not a verifier) and terminates the fact-vs-rule
cleave in S4's already-sealed `write_rule` provenance contract:

  - A deterministic `classify_epistemic_type` — a SIBLING of the sealed `classify_volatility`
    on an orthogonal axis (provable-fact vs opinion/speculation/plan): stdlib-only, no LLM,
    tags each store-(b) write, fail-safe toward FACT (ambiguity + any error => FACT).
  - An additive `epistemic:` frontmatter field on `write_episode` (the AC-driven schema-field
    precedent set by `volatility:`).
  - The ATTRIBUTION move — a thought authored WITH an author+time is fact-eligible (a provable
    utterance-event); a bare truth-claim is not. This keeps the owner's "record that he said
    it" without storing unprovable claims, and is the structural partition that dissolves the
    provable-only vs LIBERAL-ingest tension.
  - A read-side not-a-verified-fact annotation on a non-fact-typed record (mirroring
    `VOLATILE_SOFT_ANNOTATION`) — substance exposed, marked, NEVER silently withheld.
  - The documented fact-vs-rule write-time cleave + the observed-preference resolution: the
    OBSERVATION is a fact in (b); the behavioral PRIOR is a provenance-bearing rule in (c) via
    S4's `write_rule`, only when the high behavioral threshold is cleared.
  - A NAMED reversibility lever (mirroring `RANK_CONSTITUTIONAL_FLOOR`): off => byte-identical
    pre-stage writes + recall; legacy tagless records read back fail-safe as FACT; nothing
    migrated or deleted.

LOAD-BEARING invariant: the discipline TAGS and ANNOTATES; it NEVER rejects, drops, gates, or
re-routes a store-(b) write away from disk (AC.WFD.7 — the write SET is unchanged; only typing
+ rendering are added). A reject-gate would break the owner's LIBERAL fact-ingest — the #1
named F2 tension. No LLM/API call on any write or read path; no offline extraction engine
(the S5 boundary).

  - AC.WFD.1 — the verifiability discipline classifies a labeled candidate fixture correctly.
  - AC.WFD.2 — every store-(b) write carries a deterministic epistemic type, fail-safe to fact.
  - AC.WFD.3 — a non-fact is never served AS a verified fact (annotated, never withheld).
  - AC.WFD.4 — attribution converts a thought into a fact.
  - AC.WFD.5 — the fact-vs-rule cleave at write time; observed-preferences resolved (observation
    => fact in (b); behavioral prior => provenance-bearing rule in (c), only over threshold).
  - AC.WFD.6 (outcome-altitude) — end-to-end through the real write + recall path, no pre-arranged
    state: a fact-body recalls unmarked, an opinion-body recalls marked, BOTH persist.
  - AC.WFD.7 (liberal-ingest preservation) — no write is suppressed; the on-disk write set is
    identical lever-on vs lever-off.
  - AC.WFD.8 (reversibility) — the named lever reverts to byte-identical pre-stage; nothing deleted.
  - AC.WFD.9 — no regression: KP1/FBMU/FBM-FILTER/SRF/VOL/SUP/DLG/RSR suites green; deterministic-
    only; S5 boundary held; fail-open on a classifier error.

Deferred (plan §7 + §10 Fork D/E): S5 (automated offline rule-extraction that mines accumulated
facts to derive rules at the high threshold) is a separate later stage — this stage produces the
typed facts S5 consumes. An optional write-time steer (reusing the sealed decision-ledger
ruling-gap pattern) is a named follow-on. No ODD violation in surrounding code; the change is a
named additive sibling classifier + a read annotation behind a named reversible lever, no
defensive code for unnamed cases.

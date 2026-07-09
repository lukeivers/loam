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

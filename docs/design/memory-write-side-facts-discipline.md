# Memory write-side facts-discipline (store (b) — the write contract)

**Status:** active. Built by `memory-redesign-write-side-facts-discipline`
(the FACT half of S4's write-side fact/rule discipline; S4-as-built landed
the RULE half). Machine backstop: `classify_epistemic_type` in
`framework/primary-persona/src/loam/primary_persona/file_memory.py`.

This is the human-facing write contract the persona applies as it writes a
store-(b) memory (D2 — the in-session persona holds the entity context and
writes the record at write time). The deterministic classifier is the
crude-tell backstop behind this judgment, not a replacement for it.

---

## The one-line test

> **Could someone else, given the cited source, confirm this happened or
> is true?**
>
> - An **event** that occurred, a **state after work**, or a **verified
>   finding** → yes → it is a FACT. Write it.
> - A bare **how-I-feel** / **what-I-predict** / **what-I-plan** → no → it
>   is NOT a fact. Either **attribute** it (below) or route its behavioral
>   consequence to a **rule** (store (c)).

Store (b) holds provable facts, not the model's thoughts. loam's memory
only earns the owner's trust if a record it serves AS a fact IS a fact
(Lens-0 protection: no confidently-wrong recall).

## The fact classes (fact-eligible)

1. **Event** — something that specifically happened: "we sealed the
   volatility amendment", "Luke ruled X on 2026-06-09", "the CI run passed".
2. **State after work** — the world's state at a checkpoint: "the build
   branch is at `a1166b8d` after the apply", "3 PRs are open".
3. **Verified finding** — a checkable property: "the ranked-pool cap is
   `DEFAULT_TOP_N = 5`", "the FTS index ranks via BM25".
4. **Attributed expression** — an opinion / prediction / plan recorded WITH
   an author + a time (see below).

## The non-fact classes (NOT fact-eligible as bare claims)

- **Bare opinion** — "the design is elegant", "this refactor is the
  cleanest approach".
- **Bare prediction / speculation** — "the funding will probably come
  through", "I suspect the bug is in the parser".
- **Bare plan / intent** — "next I'll wire the read side", "the plan is to
  seal tonight". (Guidance on how to behave is not a memory — it is a
  prompt. A behavioral consequence belongs in a rule, store (c).)

## The attribution move — how a thought is still recorded

"Facts only" does NOT mean discard thoughts. It means record a thought as
an **attributed utterance-event**, never as a bare truth-claim:

| Bare (not a fact) | Attributed (a fact) |
|---|---|
| the design is elegant | Luke assessed the design as elegant on 2026-07-02 |
| that was annoying | Luke said "god damn it that was annoying" on 2026-06-14 |
| this will probably work | Luke predicted on 2026-07-02 that it would work |

The bare claim is unprovable; the utterance-EVENT is provable. Attribution
requires BOTH an author and a time (who + when). The read side never serves
"the design is elegant" as ground truth — only "Luke called it elegant on
<date>", which is true. This is the partition that dissolves the
provable-only vs LIBERAL-ingest tension: liberal ingest is preserved (the
thought is recorded), facts-only is preserved (what is stored is the
provable utterance-event).

## The fact-vs-rule cleave at write time

A single utterance is **a memory always; a rule only sometimes.** The
cleave is drawn at write time:

- **Always:** write the FACT (the observation / the attributed utterance)
  to store (b).
- **Only when the high behavioral threshold is cleared** — significant
  frustration, a bad-enough outcome, or a key idea — additionally author a
  behavioral **rule** in store (c) via `write_rule`, carrying a provenance
  pointer back to the fact just written. The default when the threshold is
  NOT cleared is fact-only (no rule). LIBERAL fact ingest; CONSERVATIVE,
  high-threshold rule extraction — the context-window budget is the
  governing dial.

**Observed preferences resolve here.** An observed preference writes the
OBSERVATION as a fact in (b) ("Luke chose the long-term fix over the patch
on <date>"); the behavioral PRIOR ("prefer the long-term fix") lands as a
provenance-bearing rule in (c) — never the inferred generalization as a
bare fact in (b).

## Enforcement — tag-and-annotate, never gate

The persona's judgment (D2) is the primary classifier. The deterministic
`classify_epistemic_type` is the backstop:

- It TAGS each write with a machine-readable `epistemic:` kind. It NEVER
  rejects, drops, gates, or re-routes a write away from disk — a reject
  gate would break the owner's LIBERAL fact-ingest (write everything; gate
  what is SERVED; never delete).
- It fails safe TOWARD FACT: only an affirmative opinion / speculation /
  plan tell, absent an attribution and absent a durable-fact signal, tags
  non-fact. Ambiguity and any error → fact. A missed tell only
  under-annotates; it never loses or falsifies a fact.
- The read side ANNOTATES a non-fact record (`[NOT A VERIFIED FACT — …]`)
  so its substance is still exposed but marked not ground truth — never
  silently withheld.

The classifier is a crude GRAMMAR backstop: "I think the test passed" is a
hedged FACT (durable-fact signal vetoes the hedge); "I think this is
elegant" is an opinion. It cannot always tell these apart, which is exactly
why it is tag-only + fail-safe + backed by the persona's judgment.

## Reversibility

The module lever `EPISTEMIC_TYPING_ENABLED` (in `file_memory.py`) reverts
the discipline to a no-op: off → no `epistemic:` field emitted, no read-side
annotation, writes + recall byte-identical to pre-stage, nothing on disk
migrated or deleted. A legacy tagless record reads back as a FACT. Flipping
on re-applies typing to new writes only.

## Boundary — this stage vs S5

This is the WRITE-TIME discipline + a deterministic tag applied as the
persona writes, one record at a time. It runs no offline engine, mines no
accumulated corpus, and makes no algorithmic "was the frustration
significant enough" judgment — those are S5, which will consume the clean
epistemic-typed facts this stage produces to derive rules in bulk and fit
retrieval parameters.

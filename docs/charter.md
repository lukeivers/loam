# loam Charter

This file is loam's root objective-contract: the owner's own words,
captured **verbatim**, append-only, hash-chained. Every objective,
acceptance criterion, plan, and component in this repository ladders —
directly or through intermediate criteria — to an entry in this file.
Nothing in this file is paraphrase; the statements are the owner's
words exactly as ratified, and they bind until superseded by a later
ratified entry (append-only supersession — entries are never edited or
deleted).

**Hash discipline.** Each entry carries `content-sha256` = the SHA-256
hex digest of the UTF-8 bytes of its verbatim statement (the text
between the `statement:` quote marks, no surrounding quotes, no
trailing newline). The chain rule for entries after #0:
`chain-sha256(N) = SHA-256(chain-sha256(N-1) + "\n" + statement(N))`.
Entry #0 is the genesis record: its chain value IS its content hash.

**Amendment asymmetry.** Entries are appended only on owner
ratification. An AI may *propose* an entry (as a staged candidate in
the decisions ledger or a plan-doc); it may never *enact* one. This
file is tamper-evident, not tamper-proof: chain verification detects
out-of-band mutation; it does not prevent it.

---

## Entry #0 — the founding intent (genesis record)

- **statement (verbatim):** "Make a harness which can run entirely off of the Claude Max subscription whose purpose is to make a tool for people to more effectively be hands-off while an AI does the development for them."
- **captured:** 2026-06-10 14:49 CDT
- **source:** owner, Discord message 1514355792709685389 (ledger record
  `2026-06-10-loam-founding-intent-statement-root-contract.md`,
  pos3 workspace decisions ledger)
- **ratified:** owner, 2026-06-10 15:06 CDT (Discord 1514360242,
  "Make it so" — ratification of the methodology-synthesis verdict
  installing this statement as Charter entry #0)
- **content-sha256:** `6fdc3b4f69ba5169662f08a8c1460a737fba03571edba4937ca82be7adf360fe`
- **chain-sha256:** `6fdc3b4f69ba5169662f08a8c1460a737fba03571edba4937ca82be7adf360fe` (genesis)
- **status:** active
- **first derived criteria:** `AC.PO.1` / `AC.PO.2` — the two feature
  tests in `docs/VALUE_PROPOSITION.md`, recorded there as the first
  criteria derived from this entry.

### The bootstrap exception (documented, not silently exempted)

This genesis entry and its first derived criteria were hand-written
and owner-ratified **before** the structural binding that will enforce
the Charter existed (the append-only enforcement hook, the
charter-hash gate binding, and the conversation-blind judge land in
the KEEL adoption program's Cycles A–C, after this entry). That is the
one step in the chain that the machinery cannot retroactively verify:
it rests on the ratification record above, not on a gate. Per the
ratified verdict §4.2 (KEEL b.8.1), the exception is named here as
part of the genesis record rather than silently assumed. Every entry
after #0 is expected to land through the production append path once
it exists.

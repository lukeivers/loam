# Scope-of-work — bundled documentation (v1.1 R4)

This directory ships alongside the code per pOS v1.1 objective R4
("human-readable documentation bundled alongside every component").

## Reading order

1. **prose-explanation.md** — what the primitive is and why it exists.
   Start here if you have never read about scope-of-work before.
2. **architecture.md** — the technical shape: event-sourced FSM, SQLite
   substrate, projection cache, concurrency model, upgrade story.
3. **data-flow.md** — a representative scope lifecycle walked
   step-by-step, including LLM-call debits, an extension request, and
   an escalation.
4. **relationship-map.md** — what subscribes to this primitive (memory
   today; future components named in the brief).
5. **api-reference.md** — one page covering the complete public API.

## Self-check (R4 acceptance)

> "A representative non-technical reader can answer 'what does this
> component do and how does it fit with the others' from the bundled
> docs alone."

The pair of `prose-explanation.md` (the *what* + *why*) and
`relationship-map.md` (the *how it fits*) is designed to satisfy this
test. The architecture and data-flow documents add depth for technical
readers; the API reference is for callers writing code.

# What we built and why — prose explanation

The pOS v2 memory system stores everything the system has ever known
in a way that the primary persona can ask for it later. "Everything"
means conversations, decisions, research, work — not just structured
records. "Ask for it later" means at the right moment, in the right
context, distinguishing what was true then from what is true now.

This prototype was the first concrete commitment toward how that gets
done. We tested four things in the prototyping phase, returning
information rather than building the whole memory system:

1. Whether the chosen knowledge engine (Graphiti) actually works the
   way the proposal claimed.
2. Whether a fabricated test set covering the four retrieval modes
   pOS cares about can be designed cheaply enough.
3. Whether the locally-run embedding model can keep retrieval quality
   high enough to be the production choice.
4. Whether the per-episode token cost on the chosen LLM (Anthropic
   Claude via Max) is in line with what the proposal projected.

All four are now answered. The full-build brief can proceed.

## Why Graphiti

The memory-system spec asks for several things that are individually
solvable but expensive to retrofit if the substrate doesn't ship them:
bitemporal time-tracking (when did we know X vs when was X true),
pointered supersession (when X is replaced by Y, you can ask "what
was X superseded by"), and first-class namespace partitioning (so a
scope of work can scope its own slice of memory).

Graphiti has all three natively. It also accepts Anthropic's Claude as
the LLM driver out of the box, runs against an embedded graph DB
(Kuzu), and is Apache-2.0 self-hostable. The bet was that adopting
Graphiti would mean we write nine small adaptation layers instead of a
custom temporal graph engine.

The prototype confirms that bet at the level required to commit:
Graphiti runs locally, ingests the synthetic episodes, returns correct
results from the four query types pOS cares about, and the round-trip
costs and latencies are reasonable. Two real bugs in graphiti-core's
Kuzu integration were discovered and worked around in the prototype's
factory module — both small, both upstream-able.

## Why a synthetic test set

Two reasons. First, the brief constrained the prototype to "synthetic
data only — zero carryover from current pOS / ivers-corp." Reading old
memory to seed the new one defeats the point of a clean rebuild;
existing entities and decisions would silently shape the test set in
ways that would not generalise.

Second, retrieval quality is the spec's hardest acceptance criterion
to write a test for. "The right thing at the right time" needs ground
truth, and ground truth needs Luke. The fabricated world (Aldermere
Strategic Group, six client engagements over two years) gives Luke a
small, self-contained universe where he can read each Q/A pair and
say "yes, that's a fair test" or "no, the expected facts should be
narrower." The world is sized to give multi-hop and context-aware
queries somewhere to walk: 6 engagements × 2 Aldermere staff per
engagement × cross-engagement patterns (recurring approver, recurring
introducer, recurring delivery partner) yields enough graph density
that retrieval mode differences actually show.

The test set is the shape pOS will keep using forever — every memory-
component upgrade replays it as the upgrade gate. Getting Luke's
calibration on the labels now pays compound returns.

## Why local Ollama embeddings

Anthropic does not offer an embedding API. The proposal accepted
embedding as the one capability outside Max coverage, evaluated on
merit, and recommended local-only via Ollama. Two candidate models
were tested: nomic-embed-text (already installed in pOS, 768-
dimensional) and bge-large (the proposal's listed alternate, 1024-
dimensional). qwen3-embedding (the proposal's other suggestion) is
not in Ollama's model catalog as a standalone embedder; the chat-LLM
qwen3:8b is a different beast.

Both candidates clear the entity-lookup retrieval bar on the
synthetic test set. The detailed numbers are in `docs/findings.md`.
The recommendation falls out of the data: there's a clear winner
between the two on the metrics that matter for the spec.

## Why measure cost up front

The Max-budget conversation is downstream of "how many extraction
calls per episode and how big are they." The cost-baseline script
(`scripts/cost_baseline.py`) measures this on the same synthetic
episodes. Not "what does each Anthropic call cost in dollars" — the
useful question is "how many episodes can we ingest before this
becomes uncomfortable." The projection block translates per-episode
cost into daily / weekly / monthly / yearly / 5-year budgets at
representative event volumes, with assumptions stated.

The conclusion is in `docs/findings.md`. Headline: at the projected
3,000 events/year, the implied API equivalent is comfortably under
typical Max-plan usage; Sonnet would shift it materially; Opus would
break the budget. Default to Haiku for extraction.

## What we did NOT build

The full-build proposal lists nine adaptation layers that wrap
Graphiti to deliver the parts of the spec Graphiti doesn't supply
natively (ephemerality filter, scope-of-work mapper, observability
emission, upgrade fidelity, retention class, process-of-arrival
capture, and so on). None of those are in this prototype. Each is
named in `docs/architecture.md` under "What is NOT in this prototype"
so it's clear what remains.

The prototype's job was to answer: should we proceed to build those
nine layers on top of Graphiti? The answer is yes — proceed with the
specifics flagged in `docs/findings.md`.

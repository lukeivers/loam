# Capability corpus — authoring guide

This guide defines the section schemas for entries in the
two-class capability corpus consumed by the primary persona's
**Capability leverage spine** (in
`framework/primary-persona/templates/persona-template/prompt.md`).
The corpus is partitioned into three classes; each class has
a distinct authoring contract. Per the locked design research
(`docs/plans/research/persona-capability-knowledge-grounding-research.md`,
§2.6) the partition is structural — it determines how each
entry is refreshed (Class A by deterministic projection;
Class B by synthesis-and-curation) and how β's MCP
knowledge-server will partition its resource URIs.

The directory layout mirrors β's eventual URI partition
exactly (D-OWNER.4 (a)):

- `claude-code/<name>.md` → resource URI `capability:claude-code:<name>` (Class A)
- `harness/<name>.md` → resource URI `capability:harness:<name>` (Class A-prime)
- `best-practice/<topic>.md` → resource URI `capability:best-practice:<topic>` (Class B)

## Class A — Anthropic-canonical reference

**Definition.** The objective, Anthropic-published feature
surface — what each Claude primitive *is*, what its
inputs/outputs/contracts are, what its envelope shapes look
like. Class A entries describe Claude Code, Claude API, and
Anthropic SDK content.

**Authoring contract — deterministic projection from canonical
source.** A Class A doc is not authored by judgement — it is
*projected* from the upstream documentation by a structural
transform (fetch, parse, normalise, emit). A human (or the
persona) curates the index entry and the
`[user-intent phrasings]` overlay; the body of each Class A
doc is a deterministic rendering of the upstream truth. This
makes Class A refreshable: re-projecting from a newer upstream
is mechanical and yields a clean diff. δ's projection refresh
amendment lands the automation.

**Required sections per Class A doc:**

- `## Surface` — one to three sentences naming the primitive.
- `## Inputs/outputs` — the contract: what the primitive
  accepts, what it returns, what side effects it has.
- `## Composition notes` — how the primitive composes with
  other primitives (which hooks fire when invoked, what other
  primitives commonly precede or follow it).
- `## [user-intent phrasings]` — a list of natural-language
  phrasings a user would invoke this primitive with. ≥ 3
  phrasings per entry. The persona's spine routes via this
  list: when the user's prompt matches a phrasing, the spine
  names the primitive.
- `## Source` — the projection source metadata block:
  - `source_url:` the canonical upstream source (HTTP URL
    when public; `internal:<path>` when sourced from in-repo
    docs or in-session skill descriptions);
  - `source_fetch_ts:` ISO-8601 timestamp of when the source
    was fetched / read for this projection.

## Class A-prime — pos-v2 harness primitives

**Definition.** Same shape as Class A applied to pos-v2's own
harness primitives. Sourced from `docs/archive/component-research/<name>/`,
the sealed-component contracts in `framework/<comp>/docs/`, and
the `STATE.md` ladder rather than from Anthropic.

**Authoring contract.** Identical to Class A — deterministic
projection from in-repo canonical sources. The required
sections are identical to Class A's. The only difference is
the `source_url` form: `internal:framework/<comp>/docs/<file>`
or `internal:docs/archive/component-research/<comp>/...`.

## Class B — Best-practices wisdom

**Definition.** The community-accumulated and owner-articulated
synthesis layer — *when* to use a primitive, *how* it
composes with others in practice, *what* anti-patterns to
guard against. Class B entries are not derivable from the
upstream docs alone; they capture experiential knowledge.

Sources:

- Anthropic's prompt library (the published examples).
- Internal pos-v2-session observations (when a primitive is
  observed to work or fail repeatedly).
- User-supplied capture (when the owner explicitly directs
  that a pattern be persisted).

**Authoring contract — synthesis + curation, not deterministic
projection.** A Class B doc is authored by judgement: gather
candidate patterns, weigh evidence, write a synthesis,
curate against the existing corpus to dedup or supersede.
δ's deterministic-projection refresh **never** writes to
Class B; β's accrual channels (community-survey scope +
internal Stop-hook learning-extraction + user capture) write
to Class B but never to Class A.

**Required sections per Class B doc:**

- `## Pattern` — one to three sentences naming the pattern.
- `## Conditions` — the conditions under which this pattern
  applies. When does the persona reach for it?
- `## Failure modes` — what this pattern guards against.
  Naming the failure modes is what makes the pattern
  load-bearing rather than advisory.
- `## Cross-references` — one or more `[primitive: <class>:<name>]`
  entries pointing at paired Class A or Class A-prime
  entries. The retrieval contract: when the persona fetches
  a primitive that has Class B entries cross-referencing it,
  it fetches both before planning.
- `## Trust marker` — the structural trust block:
  - `sources_count:` integer ≥ 1 — how many independent
    sources support this pattern;
  - `validation_count:` integer ≥ 0 — how many times this
    pattern has been observed to work (in pos-v2 sessions
    or community-reported);
  - `supersession_chain:` string (possibly empty) —
    references to prior Class B entries this one supersedes
    (if any);
  - `owner_acked:` boolean — has the workspace owner
    explicitly endorsed this pattern? Owner-acked patterns
    have higher trust than community-survey patterns.

## Cross-class — paired-fetch convention

When a Class A or Class A-prime primitive has one or more
Class B entries cross-referencing it via
`[primitive: <class>:<name>]`, the persona's leverage check
fetches **both** classes' entries before planning the action.
The Class A entry provides the *contract* (what the primitive
is); the Class B entries provide the *judgement* (when and how
to use it).

The persona's prompt.md spine names this convention; the
operational rule **Lean on the corpus** is the hook. Pre-β,
the persona uses the Read tool to fetch corpus-doc paths.
Post-β, the same convention runs against
`mcp__knowledge__resources/read`.

## No-cross-class-write — invariant

The two-class partition is a **structural** rule, not an
advisory one. δ's deterministic projection refresh consumes
upstream Anthropic / pos-v2 sources and writes to Class A /
Class A-prime entries only — δ never writes to Class B. β's
accrual channels (community-survey scope, Stop-hook
learning-extraction with `source_description="capability-best-practice"`,
user-driven capture) write to Class B only — they never
write to Class A.

This invariant is load-bearing: a deterministic-projection
refresh that overwrote Class B would destroy hard-won
synthesis; a synthesis-and-curation refresh that touched
Class A would inject judgement into content that should be
mechanically projected. β's resource-path partition enforces
the rule structurally (separate paths, separate write
channels).

## Authoring workflow — quick reference

For a new Class A or Class A-prime entry:

1. Identify the canonical source (Anthropic doc, pos-v2
   component doc, in-session skill description).
2. Project the relevant content into the required sections
   (`Surface`, `Inputs/outputs`, `Composition notes`).
3. Curate the `[user-intent phrasings]` overlay — list ≥ 3
   natural-language phrasings a user would invoke this
   primitive with.
4. Populate the `Source` block with the canonical URL (or
   `internal:<path>`) and the ISO-8601 fetch timestamp.
5. Add the entry to the persona's prompt.md spine
   capability index with a one-line summary + the path.

For a new Class B entry:

1. Identify the pattern (owner directive, observed
   repetition in sessions, community-report synthesis).
2. Author `Pattern`, `Conditions`, `Failure modes`.
3. Cross-reference paired Class A / Class A-prime entries
   via `[primitive: <class>:<name>]`.
4. Populate the `Trust marker` block — count sources,
   count validations, note any superseded predecessors,
   record owner-ack status.
5. Add the entry to the persona's prompt.md spine
   capability index when the pattern becomes load-bearing
   on a recurring user-intent shape.

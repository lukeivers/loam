# Primary-persona layer — prose explanation

## What this layer is

The primary-persona layer is the half of pOS that turns a workspace
directory into a loaded persona, keeps the persona aware of everything
happening in the background, and lets the persona autonomously author
new specialists when the existing roster is not enough. It is the
trust-and-coordination substrate every interactive session runs on top
of.

It has three tightly-coupled halves that share a single persona
contract:

1. **Loader + validator** — reads the workspace's `personas/` directory
   on session start, validates each persona's `contract.yaml` against
   a Pydantic schema, and fails closed on any invalidity. No persona
   in the workspace means no session starts. No persona content ships
   in pOS core — every persona is workspace-supplied.
2. **Background-work monitor** — a long-lived asyncio coroutine that
   subscribes to scope-of-work's pyee emitter and produces a
   capped structured awareness block injected into every
   `UserPromptSubmit`. Stuck scopes are detected deterministically
   using scope-of-work's `expected_duration_seconds` field (D0
   amendment) via the rule: elapsed > 2 × expected with no state
   events since start.
3. **Autonomous-authoring framework** — a creation-trigger detector
   plus a four-step Claude-via-Max pipeline that produces a new
   persona directory passing the contract by construction, with a
   mandatory user-introduction gate before any message from that
   persona can be delivered.

## Why it exists

The primitive-level rebuild of pOS names a **primary persona** as one
of three core primitives. A valid primary persona is a workspace's
single point of contact, ongoing-context holder, and escalation judge.
pOS core does not supply any persona content — a workspace without
a primary persona is misconfigured, not serviceable. This layer is the
machinery that enforces the contract, loads the content, and keeps the
persona competent during long interactive sessions.

Three specific failure modes this layer closes:

- **Lost track of background work.** A persona that is handling many
  in-flight scopes forgets which are still active, which escalated,
  which finished. STATE.md rule #7 mandates that an interactive session
  never loses awareness of active background work. The monitor
  delivers this structurally: the awareness block is injected on every
  `UserPromptSubmit`, not as an instruction the persona might forget.
- **Lost identity after compaction.** The Claude context window is not
  infinite; the compactor can discard the persona's identity, current
  scope context, pending decisions, and recent corrections. The D4
  compaction-survival mechanism re-injects those five things from
  authoritative sources on the first post-compaction prompt — no
  reliance on a saved snapshot, because snapshots drift.
- **Missing expertise.** A workspace's roster is rarely complete on
  day one. Historically this meant the user had to notice the gap and
  author a new persona by hand. The autonomous-authoring framework
  lets the primary persona recognise the gap (five deterministic
  signals), judge it, and author a new specialist — with a strict
  introduction gate so the user always knows what just joined the
  roster.

## How the three halves fit together

The loader, monitor, and authoring framework all consume the same
persona contract. The loader produces `LoadedPersona` objects; the
monitor reads scope-of-work state for its awareness block; the
authoring framework produces new persona directories that the loader
then loads on the next session start (or via explicit reload).

The introduction protocol sits between authoring and activation: a
new persona exists on disk but cannot send any message until the user
has been introduced to it and acknowledged it (the
`is_addressable` flag flips on the user's next non-retire message).
Group-channel introductions are forbidden by construction — the
`OneOnOneChannel` type rejects `is_group=True`, the dispatcher
re-checks at construction time, and the persona list per channel is
a named-allowlist write by design.

Retirement is the inverse of authoring: a persona directory moves to
`personas/_retired/<handle>-<timestamp>/`, the active loader ignores
it, and memory/scope references to the retired handle continue to
resolve via the preserved directory contents.

## Five-item compaction-survival list

The spec names five things that must survive compaction. Each is
replayed from an authoritative source, never from a snapshot:

| Item | Source |
|---|---|
| persona identity | loaded contract (`contract.yaml`) |
| authority boundary | loaded contract (`authority_boundary`) |
| current scope context | scope-of-work `list()` |
| pending decisions | scope-of-work `list(include_pending_extension=True)` |
| recent corrections | memory-system (via a callable provider) |

## Observability

Every operation emits OpenTelemetry spans and events per v1.1 R11.
The layer does not assume a downstream consumer exists (the A1
correction) — emission uses the OTel no-op default when no consumer
is attached, and the component functions identically either way.

## Permitted dependencies

Python stdlib, pydantic, pyee, opentelemetry-api/sdk, PyYAML. Anything
else requires halt-and-signal per STATE.md rule 8.

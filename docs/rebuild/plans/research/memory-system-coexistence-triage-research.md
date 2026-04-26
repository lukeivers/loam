# Research — memory-system coexistence triage (Claude Code auto-memory ↔ graphiti)

**Authored:** 2026-04-26 (background-agent dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `de5fe11`.
**Driver:** owner directive 2026-04-26 — once the memory-system live-client + Stop-hook write amendment lands (research at
`docs/rebuild/plans/research/memory-system-live-client-and-stop-hook-write-research.md`,
plan at `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`),
the persona will be writing to graphiti per turn AND Claude Code's
built-in auto memory will continue writing to
`~/.claude/projects/<slug>/memory/MEMORY.md`. Two parallel memory
systems is a chaos surface; this research scopes how pos-v2 should
handle the coexistence.
**Scope clarification:** owner framed disabling Claude Code's
auto-memory feature as "not a hard requirement, just a way to avoid
confusion" — this research is allowed to recommend a non-disable
triage if it cleanly solves the chaos surface.
**Sibling research:** a Claude Code knowledge corpus dispatch is in
flight (none of its output present at research-author time —
verified in `docs/rebuild/plans/research/`). This artefact stands on
its own; the corpus dispatch will reference it.

---

## TLDR / one-page summary

**Recommendation: Hybrid F — Disable-when-healthy with file-based
fallback + auto-heal ingestion on recovery.** Specifically:

1. **Default state (graphiti healthy):** auto-memory is **disabled**
   via project-scoped `autoMemoryEnabled: false` in
   `.claude/settings.json`. Graphiti is the sole memory store. The
   persona writes via Stop-hook (per the live-client amendment); the
   persona reads via UserPromptSubmit retrieval block.
2. **Fallback state (graphiti unhealthy):** auto-memory is **re-
   enabled** by a hooks-driven mutator that flips
   `autoMemoryEnabled` to `true` on detection of unhealthiness. The
   persona stops writing to graphiti (the live-client adapter
   already fail-softs); Claude Code's auto-memory takes over for
   the duration of the outage.
3. **Recovery state (graphiti returns healthy):** the same probe
   that detects unhealthiness detects recovery, flips
   `autoMemoryEnabled` back to `false`, AND triggers a one-shot
   ingestion job that reads everything written to MEMORY.md +
   feedback_*.md during the outage and writes it as graphiti
   episodes. Once ingestion completes, the auto-memory directory is
   either cleared or moved to a dated archive (decision below).

**Why not the alternatives.** Option B (intercept-and-route via a
Write-tool hook) is technically reachable but fragile: auto-memory
writes don't have a documented "this is auto-memory" tool-name
surface, so a PreToolUse intercept would have to pattern-match
on path, which is brittle. Option C (layered, both active) is the
status quo and is exactly the chaos surface we're trying to avoid.
Option D (subordinate via digest-into-MEMORY.md) loses the auto-
heal property. Option E (do nothing, let prompt rules resolve) is
not implementable — the persona's prompt cannot reliably win over
auto-memory's first-200-lines-of-MEMORY.md auto-load when both
contain the same kind of content.

**Three implicit goals — how F satisfies them:**

1. **No parallel-memory chaos.** Default is one canonical store
   (graphiti). Fallback is one canonical store (auto-memory). The
   transition window is the only time both have content, and the
   recovery ingestion drains the fallback into graphiti.
2. **Auto-heal fallback.** Probe detects graphiti down →
   auto-memory takes over → user keeps working with no visible
   hiccup.
3. **Ingestion on recovery.** Probe detects graphiti up →
   ingestion job replays the file-based content → graphiti is the
   sole store again.

**Cost realism for ingestion.** the user's current pos3 auto-memory
is 26 files / 612 lines / 74KB. At amendment #33's ~113s/episode,
**26 episodes × 113s ≈ 49 minutes** of extraction. Inside the halt-
trigger threshold (>50 episodes / hours-of-work). Realistic outages
will produce fewer episodes — most fallback windows are minutes to
hours, not weeks. Halt only triggers if the user lives in fallback
for weeks/months without recovery.

**Decisions for owner:** 5 (D1–D5 below).

**Plan-doc shape:** the recommended design IS concrete enough to
plan as a single amendment. Sealed-component fence is
`workspace-bootstrap` + `hands-off-lifecycle` + a new tiny
`memory-coexistence/` component (or a free-standing emitter under
`primary-persona`). The amendment is **NOT** authored as part of
this research dispatch; that's a follow-on. Recommended amendments
named in §10.

---

## 1. Question set

The five blocks of questions in the dispatch order:

- **Q-A. How does Claude Code's built-in memory feature actually
  work?** — surface, paths, controls.
- **Q-B. Conflict surface.** — where do graphiti and auto-memory
  collide?
- **Q-C. Design options.** — A through F, weighed.
- **Q-D. Auto-heal implementation surface.**
- **Q-E. Recommendation.**

---

## 2. Q-A — How Claude Code's built-in memory feature works (verified against docs)

**Source:** <https://code.claude.com/docs/en/memory> fetched
2026-04-26. <https://code.claude.com/docs/en/settings> consulted
same date. <https://code.claude.com/docs/en/hooks> consulted same
date for hook-based intercept analysis.

### 2.1 Two distinct mechanisms — CLAUDE.md vs. auto memory

The docs use the umbrella term "memory" for two distinct things:

| | CLAUDE.md files | Auto memory |
|---|---|---|
| Who writes it | the user | Claude Code (autonomously) |
| What it contains | Instructions and rules | Learnings and patterns |
| Scope | Project / user / org | Per working tree |
| Loaded into | Every session | Every session (first 200 lines or 25KB of MEMORY.md) |

Quoted from the docs:

> *"Claude Code has two complementary memory systems. Both are
> loaded at the start of every conversation. Claude treats them as
> context, not enforced configuration."*

> *"Auto memory lets Claude accumulate knowledge across sessions
> without you writing anything. Claude saves notes for itself as it
> works ... Claude doesn't save something every session. It decides
> what's worth remembering based on whether the information would
> be useful in a future conversation."*

**For the coexistence problem, only auto-memory is the conflict
surface.** CLAUDE.md files are user-authored context that the
persona's job is to compose against, not duplicate. Graphiti is not
"competing with" CLAUDE.md any more than it competes with the
project's source code; CLAUDE.md is *static rules*, graphiti is
*accumulated learnings*. The two are complements.

The conflict is: **auto-memory and graphiti are both "Claude
accumulating learnings."** They are doing the same job in two
stores.

### 2.2 Where auto-memory lives

> *"Each project gets its own memory directory at
> `~/.claude/projects/<project>/memory/`. The `<project>` path is
> derived from the git repository, so all worktrees and
> subdirectories within the same repo share one auto memory
> directory."*

> *"The directory contains a `MEMORY.md` entrypoint and optional
> topic files."*

Verified in the user's setup: the pos3 workspace's auto-memory
directory `~/.claude/projects/-Users-lukeivers-pos3/memory/` contains
`MEMORY.md` (an index) plus 25 `feedback_*.md` topic files (the
detailed notes), totalling 612 lines / 74KB. Topic files match the
patterns the docs describe; MEMORY.md is the bullet-list index.

### 2.3 When auto-memory writes

> *"Claude reads and writes memory files during your session. When
> you see 'Writing memory' or 'Recalled memory' in the Claude Code
> interface, Claude is actively updating or reading from
> `~/.claude/projects/<project>/memory/`."*

> *"When you ask Claude to remember something, like 'always use
> pnpm, not npm' or 'remember that the API tests require a local
> Redis instance,' Claude saves it to auto memory."*

**Two trigger shapes:**

1. **Autonomous.** Claude decides during the session that a
   correction or preference is worth remembering. Writes happen
   mid-session. Cadence: opportunistic, not every turn.
2. **User-prompted.** the user asks Claude to remember something.
   Auto-memory is the default destination unless the user says "add
   this to CLAUDE.md."

### 2.4 When auto-memory reads

> *"The first 200 lines of `MEMORY.md`, or the first 25KB,
> whichever comes first, are loaded at the start of every
> conversation. Content beyond that threshold is not loaded at
> session start. Claude keeps `MEMORY.md` concise by moving
> detailed notes into separate topic files."*

> *"Topic files like `debugging.md` or `patterns.md` are not loaded
> at startup. Claude reads them on demand using its standard file
> tools when it needs the information."*

**Loading is via the system context, not a tool call.** The
auto-memory content reaches the model the same way CLAUDE.md does:
Claude Code injects the first 200 lines of MEMORY.md into the
session's startup context. Topic files are read on-demand via the
Read tool when the model decides to (typically when an MEMORY.md
bullet references the topic file path).

This matters for the conflict-surface analysis (§3): MEMORY.md and
the persona's UserPromptSubmit retrieval block both inject content
into context at session-start / turn-start. They overlap.

### 2.5 How to disable auto-memory — three documented surfaces

Quoted directly from the docs:

> *"Auto memory is on by default. To toggle it, open `/memory` in a
> session and use the auto memory toggle, or set
> `autoMemoryEnabled` in your project settings:*
> ```json
> {
>   "autoMemoryEnabled": false
> }
> ```
> *To disable auto memory via environment variable, set
> `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`."*

**Three controls:**

1. `/memory` slash-command toggle — interactive, user-driven.
2. `autoMemoryEnabled: false` in `.claude/settings.json` — project-
   scoped, persistent. **Critically, the docs explicitly say "in
   your project settings"** — auto-memory IS controllable from
   `.claude/settings.json` (unlike `autoMemoryDirectory`, which is
   blocked from project scope per the docs to prevent shared repos
   from redirecting writes to sensitive locations).
3. `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` env var — process-scoped.

**Implication for coexistence design:** option A (disable when
graphiti healthy) is **fully implementable** — pos-v2 can write
`autoMemoryEnabled: false` into the workspace's
`.claude/settings.json` at first-run, mirroring the existing
`hooks.SessionStart` / `hooks.UserPromptSubmit` merge pattern from
amendments #37 / #46.

There is no documented PreMemoryWrite, MemoryWrite, or MemoryRead
hook event (verified by enumerating the hooks docs — see §6). Option
B (intercept-and-route via hook) is **not** implementable through a
documented surface; the only adjacency would be a PreToolUse hook
matching on the Write tool with a path filter, which the docs do
not commit to as a stable surface for auto-memory writes
(implementation detail not documented).

### 2.6 Auto-memory dir is per-git-repo, machine-local

> *"Auto memory is machine-local. All worktrees and subdirectories
> within the same git repository share one auto memory directory.
> Files are not shared across machines or cloud environments."*

This means a single auto-memory dir at
`~/.claude/projects/<repo-slug>/memory/` exists for the user's
workspace. pos-v2 first-run can compute the slug deterministically
(it's the workspace path with `/` → `-`). The recovery ingestion
(§5) reads this canonical location.

### 2.7 What `/memory` shows the user

> *"The `/memory` command lists all CLAUDE.md, CLAUDE.local.md, and
> rules files loaded in your current session, lets you toggle auto
> memory on or off, and provides a link to open the auto memory
> folder."*

When pos-v2 disables auto-memory, the user can still open
`/memory` and see the toggle is off. This is a desirable user-
visible signal: the user knows pos-v2 has taken over and the
file-based store is dormant. The slash-command surface is
preserved.

---

## 3. Q-B — Conflict surface (where graphiti and auto-memory collide)

Four collision points, ordered by user-visible severity:

### 3.1 Both inject context at session/turn start

- **Auto-memory:** first 200 lines of MEMORY.md auto-loaded at
  session start.
- **Graphiti (post live-client amendment):** retrieval block on
  every UserPromptSubmit, surfaced via `additionalContext`.

When both are active, the persona sees two separate, potentially
contradictory memory surfaces every turn. The persona's prompt
cannot reliably resolve "auto-memory says X, retrieval says ¬X" —
both look like authoritative learnings about the user.

**Severity:** high. The persona's translation-layer behaviour
(VALUE_PROPOSITION §"primary persona") depends on consistent
memory; inconsistent memory is exactly the failure mode where the
translation breaks.

### 3.2 Both write learnings

- **Auto-memory:** Claude decides mid-session to save a learning;
  writes to MEMORY.md / a topic file.
- **Graphiti (post live-client amendment):** Stop-hook drains the
  turn into a graphiti episode after every turn.

When both write, "what the persona has learned about the user"
diverges across two stores over time. Worse: auto-memory writes are
opportunistic (Claude's discretion), so the divergence is non-
deterministic.

**Severity:** medium-high. Divergence accumulates silently. By the
time the user notices, neither store is authoritative.

### 3.3 User-visible artefacts

The user can `/memory` open the auto-memory folder; the user can
edit MEMORY.md by hand. There is no equivalent file-system surface
for graphiti — graphiti is a Kuzu graph DB queryable only via MCP.

When a user edits MEMORY.md, they expect that edit to be honoured.
If graphiti is the canonical store, that edit is visible at session-
start (auto-loaded into context) but is not in graphiti, so the
persona's retrieval block won't surface it next turn.

**Severity:** medium. User confusion about "where is my correction
actually stored."

### 3.4 "Remember X" addressing

The user says "remember that the API tests need Redis." Auto-memory
catches this and writes to MEMORY.md. The persona, post live-client
amendment, also catches this in the Stop-hook turn-aggregate and
writes to graphiti. The same atom of knowledge ends up in both
stores, addressed differently.

**Severity:** medium. Predictable; manageable by deduplication
heuristics. Worse if the two stores diverge in subsequent turns
(see §3.2).

---

## 4. Q-C — Design options (six options weighed)

Each option is evaluated on six axes:

- **Implementable?** Can pos-v2 actually do this with documented
  surfaces?
- **Goal 1 (no chaos)?** Does it avoid parallel-store divergence?
- **Goal 2 (auto-heal)?** Does it preserve memory when graphiti is
  unhealthy?
- **Goal 3 (ingestion)?** Does content captured during fallback
  reach graphiti on recovery?
- **User-visible surface.** What does the user see?
- **ODD-shape.** Is the failure surface clean (named ACs) or does
  it leak into silent branches?

### 4.1 Option A — Disable auto-memory when graphiti is healthy (single-store)

- Implementable: **YES.** `autoMemoryEnabled: false` is documented
  for project settings (§2.5). Workspace-bootstrap merges that key
  alongside `hooks.SessionStart` / `hooks.UserPromptSubmit` /
  `agent` (precedent in amendments #37, #46, #47).
- Goal 1: **YES.** One store at all times.
- Goal 2: **NO** — if graphiti goes down with auto-memory disabled,
  the user has no memory at all during the outage.
- Goal 3: N/A — no fallback content to ingest.
- User-visible: `/memory` shows the toggle off. User knows pos-v2
  is in charge. Minor learning curve.
- ODD-shape: clean. One settings.json field; one merge call.

**Verdict:** strict-A is goal-incomplete (fails goal 2). Forms the
spine of the recommended hybrid F.

### 4.2 Option B — Intercept and route through a hook

The idea: don't disable auto-memory; instead, intercept the writes
(via a hook or wrapper MCP server) and redirect them to graphiti.

- Implementable: **NO** through a documented surface. The hooks
  docs enumerate event names (verified §6 below); none is
  `MemoryWrite` or `PreMemoryWrite`. The only adjacency is
  `PreToolUse` matching the `Write` tool with a path-glob filter
  on `~/.claude/projects/.../memory/`, but the docs do not commit
  to auto-memory using the public Write tool — it may be a
  privileged internal write. **Brittle and undocumented.**
- Goal 1: tentatively yes if the intercept works.
- Goal 2: depends on intercept fidelity.
- Goal 3: N/A — captures everything in graphiti directly.
- User-visible: opaque. User sees `/memory` claim writes happened;
  reality is they went elsewhere. Confusing if reality diverges
  from the slash-command surface.
- ODD-shape: bad. Path-pattern matching = silent branches.

**Verdict:** rejected. The undocumented-write-path risk is the
killer; even if it works today, a Claude Code release could change
the internal write mechanism and break the intercept silently.
Option F (the recommended hybrid) achieves the same outcome via
documented controls.

### 4.3 Option C — Layered (both active, declare canonical)

Both stores stay active. The persona's prompt declares one
canonical (graphiti), the other ephemeral cache. A sync primitive
periodically reconciles.

- Implementable: yes mechanically.
- Goal 1: **NO.** This is exactly the chaos surface the owner is
  asking about. "Both stores remain active, declare a winner" is
  the status quo plus a prompt-level instruction. Promp-level
  conflict resolution is unreliable (per VALUE_PROPOSITION §"The
  problem pOS is closing" — the persona is supposed to absorb
  translation burden, not push it to the user via "if your memory
  feels confused, here's why").
- Goal 2: yes (auto-memory always available).
- Goal 3: yes via the sync primitive.
- User-visible: confusing; two stores visible.
- ODD-shape: poor; the sync primitive is full of method-laden
  reconciliation logic with no clean AC for "stores agree."

**Verdict:** rejected. Failing goal 1 is dispositive — the user
explicitly asked for this not to be chaotic.

### 4.4 Option D — Subordinate auto-memory (digest-into-MEMORY.md)

The persona writes to graphiti exclusively. A separate hook
periodically dumps a digest of graphiti's recent episodes into
MEMORY.md so Claude Code's auto-loader keeps surfacing it.

- Implementable: yes mechanically (the hook writes the file).
- Goal 1: yes — auto-memory is just a cache of graphiti.
- Goal 2: **NO.** If graphiti is unhealthy, the digest hook can't
  read graphiti, so MEMORY.md goes stale. No fallback writes happen
  anywhere — the persona has no place to record corrections during
  the outage.
- Goal 3: N/A — auto-memory doesn't write during fallback.
- User-visible: user sees a file-based mirror. Reasonable.
- ODD-shape: clean for the digest hook; nothing to reconcile.

**Verdict:** rejected. Fails goal 2 in the same way option A does
without the auto-heal escape hatch. (D is "A with a digest mirror";
strictly worse than F because F adds the auto-heal property.)

### 4.5 Option E — Don't suppress; resolve in prompt

Both stores active. The persona's prompt says "when memory
contributors disagree, defer to graphiti." Hope.

- Implementable: trivially.
- Goal 1: **NO.** Prompt-level conflict resolution is the wrong
  layer; the persona is a translation layer, not a memory
  arbitrator. (This is identical to option C without even the sync
  primitive. Worse.)
- Goal 2: yes.
- Goal 3: nothing happens automatically.
- User-visible: confusing.
- ODD-shape: bad — every prompt is a "if memory disagrees" branch
  that can never be tested deterministically.

**Verdict:** rejected. Same as C, worse.

### 4.6 Option F — Hybrid: A while healthy, fallback on unhealth, ingest on recovery

This is the recommendation. Three states, deterministic transitions:

**State 1 — Healthy (default).**
- `autoMemoryEnabled: false` in `.claude/settings.json`.
- Graphiti is sole store. Persona reads via UserPromptSubmit
  retrieval; persona writes via Stop-hook turn-close.

**State 2 — Unhealthy (fallback).**
- A health probe detects graphiti is down (HTTP refusal, MCP
  handshake failure, repeated errors from `health` tool).
- A hooks-driven mutator flips `autoMemoryEnabled` to `true` in
  `.claude/settings.json`. Claude Code picks this up on the next
  session (per the docs, settings.json is read at session start).
  An optional in-session signal — e.g. a SessionStart contributor
  emitting an `additionalContext` line "graphiti unhealthy; falling
  back to file-based memory" — is helpful but not load-bearing.
- the user keeps working. Auto-memory writes mid-session in the
  normal Claude Code way.

**State 3 — Recovered (ingestion).**
- Same probe (or a paired one) detects graphiti is healthy again.
- The mutator flips `autoMemoryEnabled` back to `false`.
- A one-shot ingestion job reads MEMORY.md and every
  `feedback_*.md` written **during the outage window**, formats
  each as a graphiti episode (via the live MCP client + the
  `add_episode` tool the live-client amendment lands), and waits
  for them to extract.
- After successful ingestion, the post-outage window's content is
  archived (D5 — see decisions). Graphiti is the sole store again.

- Implementable: **YES.** All controls are documented. The
  ingestion job is the same `add_episode` MCP call the persona's
  Stop-hook uses post-live-client amendment.
- Goal 1: **YES.** One canonical store at any moment in time. The
  transition windows have content in both stores, but ingestion
  drains the fallback store into graphiti and the design declares
  the file-based store dormant after recovery.
- Goal 2: **YES.** Auto-memory takes over during outages.
- Goal 3: **YES.** Recovery ingestion replays the file content.
- User-visible: `/memory` toggle reflects current state; user can
  see when pos-v2 is in fallback. Auto-memory directory is left
  alone (or archived) so the user can audit.
- ODD-shape: clean. The state machine has three states with
  deterministic transitions; each transition has a documented
  trigger; the ingestion job has a well-defined input (the
  fallback-window file set) and output (episodes in graphiti).

**Verdict:** **Recommended.**

### 4.7 Decision matrix summary

| Option | Implementable | Goal 1 | Goal 2 | Goal 3 | ODD-shape |
|---|---|---|---|---|---|
| A — disable always | YES | YES | NO | N/A | clean |
| B — intercept | brittle | partial | partial | N/A | bad |
| C — layered | YES | NO | YES | YES | poor |
| D — subordinate | YES | YES | NO | N/A | clean |
| E — prompt-resolve | YES | NO | YES | NO | bad |
| **F — hybrid (A + fallback + ingest)** | **YES** | **YES** | **YES** | **YES** | **clean** |

---

## 5. Q-D — Auto-heal implementation surface

### 5.1 Health probe — already exists (amendment #34)

The memory-graphiti service exposes a `GET /health` Starlette route
alongside the MCP surface. From `memory-system/src/service.py`
(per amendment #34's eager-lifespan conformance work):

- `health` MCP tool — returns `{"healthy": bool, "components":
  {...}}` per `_impl_health`.
- `GET /health` HTTP endpoint — same payload, accessible without
  MCP session establishment.

Either surface is suitable for the probe. The HTTP endpoint is
strictly cheaper (no MCP handshake) and is available the same way
launchctl's KeepAlive uses it.

**Probe shape:** an HTTP GET against
`http://127.0.0.1:<sidecar-port>/health` with a 1s timeout. Three
outcomes:
- 200 + healthy: graphiti is up. State 1.
- 200 + unhealthy / 500 / connection refused / timeout: graphiti
  is down. State 2.
- The ambiguous middle (200 + degraded): treat as healthy unless
  unhealth is repeated N times consecutively (debounce).

### 5.2 Probe cadence — three candidate shapes

1. **Per-session-start.** Probe runs at SessionStart;
   `autoMemoryEnabled` reflects the result. This catches the
   "Claude Code restarted while graphiti was down" case naturally.
   It does **NOT** catch mid-session graphiti crashes.
2. **Per-turn (UserPromptSubmit / Stop).** Probe runs every turn.
   Catches mid-session crashes but adds latency to every turn.
3. **Background daemon.** A separate process (e.g. a launchctl
   service or a recurring scope) probes every N seconds and
   updates settings.json out-of-band.

**Research lean:** **(1) at session start + light per-turn check
in the UserPromptSubmit retrieval contributor.** The retrieval
contributor already runs every turn, already gracefully empties on
unhealth (AC.M.3 in the live-client plan), and already pays the
loopback latency. Augmenting it to *also* trigger the
`autoMemoryEnabled` mutator on extended unhealth is small. The
session-start probe handles the cold-start case; the per-turn
check handles mid-session.

A background daemon is overkill — the failure mode "graphiti
crashed but the user isn't using Claude" doesn't matter; nobody is
losing memory during that interval.

### 5.3 Mutator shape — write-then-read

The mutator writes `autoMemoryEnabled` into
`<workspace>/.claude/settings.json`. Per amendment #46's precedent:
the merge function lives in `hands-off-lifecycle/hooks/
first_run_settings.py`; a new `set_auto_memory_enabled(*, settings_
path, enabled: bool)` function alongside `merge_session_start` /
`merge_user_prompt_submit` is the natural shape.

**Atomicity:** mirror the existing `tmp.replace(settings_path)`
atomic-write pattern. No partial writes.

**Backup:** a flip from True to False (or vice versa) is reversible
without backup; the value is binary. Backups exist for displacing
user-authored stanzas (e.g. SessionStart). For a single boolean
field, no backup needed — the prior value is implicit.

**Settings-layer scope:** project (`<workspace>/.claude/settings.
json`). User-level (`~/.claude/settings.json`) is untouched. Local
(`<workspace>/.claude/settings.local.json`) is untouched. This is
intentional — the user's user-level auto-memory preference for
non-pos-v2 workspaces is theirs to govern. pos-v2 only flips its
own workspace's project-scope key.

### 5.4 Detection of the fallback window — when does it open / close?

The mutator needs a "this is when the fallback started" stamp so
the ingestion job knows what files are new. Options:

1. **mtime-based.** When the mutator flips `autoMemoryEnabled` to
   true, write a marker file
   `<workspace>/.pos/memory-fallback-started-at` containing the
   ISO-8601 timestamp. The recovery ingestion reads every
   `~/.claude/projects/<slug>/memory/*.md` whose mtime is newer
   than that timestamp.
2. **File-list-snapshot-based.** When the mutator flips to true,
   snapshot the current contents of the auto-memory directory.
   Recovery diffs current vs. snapshot.

**Research lean:** mtime-based. Cheaper, no diff machinery, robust
to file content changes (e.g., the user manually editing a topic
file during fallback — that edit is captured because the mtime
updates).

### 5.5 Ingestion job — shape and cost

The job runs once on recovery. Steps:

1. Read `<workspace>/.pos/memory-fallback-started-at`.
2. Enumerate `~/.claude/projects/<slug>/memory/*.md` with mtime
   newer than that timestamp.
3. For each file: read content, format as a graphiti episode (the
   `add_episode` payload schema is documented per amendment #33
   research §4 — `name`, `body`, `source_description`,
   `reference_time`, `source="message"`, `group_id=<workspace
   slug>`).
4. Issue one `add_episode` MCP call per file.
5. Wait for each call to return (~113s/episode per amendment #33).
6. On success: archive (D5) and clear the fallback marker.
7. On any partial failure: log to
   `<workspace>/.pos/memory-writes.log` (precedent in the
   live-client amendment plan §6 D8); do not loop. The next probe
   cycle retries.

**Cost — one realistic outage scenario.** A typical graphiti
crash-and-recover window might be 1 hour during which the user has
3 turns. Each turn potentially produces 0–1 auto-memory writes. So
the typical recovery is 0–3 episodes — **0–6 minutes of extraction
work**. Trivially absorbed.

**Cost — pathological scenario (cold start of pos-v2 over an
existing user workspace with pre-existing auto-memory).** This is
the upper bound: a user enables pos-v2 over a workspace that has
been accumulating auto-memory for months. the user's pos3 dir is
**26 files / 612 lines / 74KB**. At amendment #33's empirical
~113s/episode, **26 × 113s ≈ 49 minutes** of background work. This
is below the halt-trigger threshold (>50 episodes) but real.
Mitigations:

1. The ingestion job runs **detached** (per the live-client
   amendment plan's §6.2 detachment pattern); the user is not
   blocked.
2. The first-run path is the only place pre-existing auto-memory
   gets bulk-ingested; after that, the steady-state is per-outage
   (small).
3. The cold-start ingestion can be **opt-in** at first-run if the
   user wants to defer (D2 — see decisions).

### 5.6 What happens during fallback — who writes what?

During fallback (state 2), the persona is **NOT** writing to
graphiti via the Stop hook (the live-client amendment has the
Stop-hook subprocess detect unhealth and exit clean, per AC.M.10
in that plan). Auto-memory is the sole writer, and it writes
exactly the way Claude Code natively does — Claude decides
mid-session, no pos-v2 wiring.

This is critical for goal 2: pos-v2 is not "tunneling" writes
through anything during fallback. Claude Code's native behaviour
takes over. Auto-memory has been working for users since v2.1.59
without pos-v2's help; we let it.

The persona's UserPromptSubmit retrieval contributor in fallback
mode emits an empty / fail-soft block (AC.M.3 in the live-client
amendment). The persona answers from auto-memory's first-200-lines
of MEMORY.md (loaded at session start) plus what's in the
conversation. Less expressive than graphiti retrieval, but
functional.

### 5.7 Edge cases to design around

- **User manually toggles `/memory` on while graphiti is healthy.**
  pos-v2 detects the override (the settings.json field flipped to
  true while the probe says healthy) and flips it back next probe
  cycle. **OR** pos-v2 honours the user override and stays in
  state-2-like (both active) until the user toggles back.
  Recommendation in D3: flip back. The user's `/memory` toggle is
  a session-level UI; the project-level intent is that pos-v2
  manages the setting. Surfacing a "pos-v2 has auto-memory
  disabled per its design — to override permanently, set
  `autoMemoryEnabled: true` in settings.local.json which pos-v2
  doesn't touch" notice in the persona is the user-facing
  resolution.
- **Graphiti is partially up.** `/health` says healthy but
  `add_episode` is failing. The probe's debounce (§5.1) handles
  this; the live-client AC.M.10 fail-soft path handles the
  per-call case. No new design surface needed.
- **The user disables pos-v2 (clones a fresh workspace).** The
  fresh workspace has no
  `<workspace>/.claude/settings.json autoMemoryEnabled: false`
  yet, so auto-memory is on by default. pos-v2's first-run sets
  it on first invocation. Until first-run completes, auto-memory
  runs once or twice — accept this. The cold-start ingestion (D2)
  picks those up.
- **The fallback window is "always" (graphiti never started).** A
  user without graphiti running at all. The probe never finds
  health; auto-memory stays on. pos-v2 never imposes the disable.
  This is correct behaviour — pos-v2 is fail-soft about its own
  features.

---

## 6. Hooks docs cross-check (negative result)

Verified against <https://code.claude.com/docs/en/hooks>: the
documented hook event names are SessionStart, UserPromptSubmit,
UserPromptExpansion, PreToolUse, PermissionRequest,
PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch,
Notification, SubagentStart, SubagentStop, TaskCreated,
TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded,
ConfigChange, CwdChanged, FileChanged, WorktreeCreate,
WorktreeRemove, PreCompact, PostCompact, Elicitation,
ElicitationResult, SessionEnd. No PreMemoryWrite, MemoryWrite, or
MemoryRead.

`FileChanged` could in principle watch `MEMORY.md` for writes; this
gives an after-the-fact signal that auto-memory wrote, useful for a
"detect manual auto-memory write while in healthy state and warn"
contributor. Not load-bearing for the recommended design but a
candidate small extension (D4 — see decisions).

`SessionEnd` fires on session termination with a `reason` matcher
(`clear`, `resume`, `logout`, `prompt_input_exit`,
`bypass_permissions_disabled`, `other`). Could be used to flush
unfinished ingestion work. Not load-bearing.

---

## 7. ODD/§2.5 reverse direction — does the surrounding code allow this?

Surrounding code that the recommended design touches:

- **`<workspace>/.claude/settings.json`.** Currently authored by
  `hands-off-lifecycle/hooks/first_run_settings.py` (merge_*
  functions). Adding a `set_auto_memory_enabled` function follows
  the established pattern. **Inside fence.**
- **`hands-off-lifecycle/hooks/first_run_helper.py`.** Currently
  invokes the merge_* functions via `_maybe_merge_*` fail-soft
  helpers at three call sites (Phase 3d, Phase 4c, Phase 6). Same
  pattern for the new mutator. **Inside fence.**
- **A new probe surface.** No precedent inside primary-persona /
  hands-off-lifecycle for "probe at session-start + per-turn." The
  per-turn case can compose onto the existing UserPromptSubmit
  retrieval contributor (already runs, already calls graphiti's
  search). The session-start case can compose onto the persona's
  SessionStart emitter (amendment #46). **Inside fence.**
- **A new ingestion surface.** Pure-additive. New module under
  `primary-persona` (or a new sealed component
  `memory-coexistence`) — designable without touching surrounding
  code beyond the live-client adapter the in-flight amendment lands.
  **Inside fence.**

**No surrounding §2.5 violations spotted.** The design composes on
documented surfaces (auto-memory disable, MCP add_episode,
SessionStart / UserPromptSubmit hooks already wired) and adds new
ACs around new behaviour. No silent branches needed.

---

## 8. Cost / latency budget

- **Per-session probe overhead:** one HTTP GET on loopback, ~ms.
- **Per-turn probe overhead:** the existing UserPromptSubmit
  contributor already pays this; reusing it is free.
- **Per-fallback-recovery ingestion:** O(N × 113s) where N is the
  count of MEMORY.md + feedback_*.md files written during the
  outage window. Realistic outage = 0–3 episodes = 0–6 minutes
  detached background work. Cold-start over pre-existing 26-file
  workspace = ~49 minutes detached background work.
- **Subscription throughput:** absorbed by Claude Max. No new
  pay-per-token spend at typical workload. Cold-start is bounded
  one-time.

---

## 9. Decisions for owner (rule from this block)

The plan-author has made the following inferences. Each names a
recommendation; Luke rules from this block.

### D1 — Probe mechanism: HTTP GET vs MCP `health` tool

- **Recommendation:** HTTP GET on `http://127.0.0.1:<sidecar-port>
  /health`. Cheaper, no MCP handshake, available cross-process.
- **Why:** the per-session probe runs in the SessionStart hook
  subprocess, which has no MCP client. Spinning one up just for a
  health check is wasteful.
- **Alternative:** MCP `health` tool. Would require an MCP client
  even in the SessionStart probe. Rejected on cost.

### D2 — Cold-start ingestion: opt-in or automatic?

- **Recommendation:** **opt-in at first-run.** The persona
  surfaces "I detected pre-existing auto-memory in this workspace
  (~74KB / 26 files); should I bulk-ingest it into graphiti? This
  takes ~50 minutes of background work, after which auto-memory
  is disabled in pos-v2's favour." The user says yes/no.
- **Why:** automatic 49-minute background work on first-run is
  surprising. The opt-in respects the user's autonomy and matches
  the VALUE_PROPOSITION's "user is entitled to ignore tokens" lens
  (the user shouldn't be forced into unexpected token spend).
  Defaulting to "yes" is fine; defaulting to "no" leaves the user
  with auto-memory on but inaccessible-to-graphiti, which is
  acceptable degraded operation.
- **Alternative:** automatic. Faster path to single-store
  steady-state but surprising.

### D3 — User toggles `/memory` on while pos-v2 has it off — flip back?

- **Recommendation:** **flip back, with persona-surfaced notice.**
  pos-v2's intent is that the project-scope setting is
  authoritative. The persona surfaces "I noticed you re-enabled
  auto-memory; pos-v2 keeps it disabled while graphiti is healthy
  to avoid two parallel memory stores. To override permanently,
  add `autoMemoryEnabled: true` to `.claude/settings.local.json`
  (pos-v2 doesn't manage that file)."
- **Why:** preserves pos-v2's design intent without locking the
  user out. The user has an escape hatch (settings.local.json,
  which pos-v2 explicitly doesn't touch — see §5.3).
- **Alternative:** honour the user override silently; let the user
  live with two stores. Worse UX (no signal to the user about why
  the design preference exists).

### D4 — Watch MEMORY.md via `FileChanged` for "auto-memory wrote while disabled"?

- **Recommendation:** **NO** — not in the first amendment. The
  recommended design's correctness doesn't depend on detecting
  rogue writes; the design assumes auto-memory is honestly off
  while disabled (which it is, per docs). A FileChanged contributor
  that warns "MEMORY.md was modified outside fallback" is a useful
  diagnostic but not load-bearing.
- **Why:** smaller first amendment. The diagnostic can land later
  if a real surface arises.
- **Alternative:** include FileChanged contributor. Would catch
  edge cases (e.g., user manually edits MEMORY.md while pos-v2 is
  managing it) but adds surface area without clear AC backing.

### D5 — Post-ingestion: archive auto-memory or leave it?

- **Recommendation:** **leave it**, plus mark as ingested by
  appending a comment block at the top of MEMORY.md noting "this
  content was ingested into graphiti at <timestamp>; further
  edits won't be auto-ingested unless graphiti goes unhealthy
  again." The user can browse / archive it themselves; pos-v2
  doesn't delete user-visible content.
- **Why:** the user-visible auto-memory dir is a long-running
  persona artefact that the user has been editing for weeks/months.
  Auto-deleting it (or moving to a dated archive) on first-run
  would be surprising and might lose user-authored content the
  user expects to find.
- **Alternative (a):** move to
  `~/.claude/projects/<slug>/memory.archived-<timestamp>/` after
  ingestion. Cleaner state but destroys user expectation that
  `/memory` shows their content.
- **Alternative (b):** delete after ingestion. Worst — destructive.

---

## 10. Recommended amendments (plan-doc shape — NOT authored here)

The recommended design F decomposes into one umbrella amendment
naming three smaller pieces, OR three independent amendments. The
research lean is **single amendment** — the three pieces are
tightly coupled and share the same workspace-bootstrap surface.

**Slug suggestion:**
`memory-system-coexistence-disable-and-auto-heal`

**Component fence:**
`workspace-bootstrap` (first-run authoring of
`autoMemoryEnabled: false` in `.claude/settings.json`) +
`hands-off-lifecycle` (settings mutator + the runtime probe call
sites) + `primary-persona` (the per-turn unhealth observer +
recovery ingestion job).

**Behaviour outline (the plan author will translate into ACs):**

- **B1.** First-run authors `autoMemoryEnabled: false` into
  `.claude/settings.json` alongside the existing
  `hooks.SessionStart` / `hooks.UserPromptSubmit` / `agent` keys.
- **B2.** First-run probes graphiti health; if healthy, B1 stands;
  if unhealthy, B1 still stands (pos-v2 is going to rely on
  graphiti once it comes up; offering memory-via-auto in the
  meantime is fine — see B5 — but the project-scope default is
  off).
- **B3.** First-run, IF pre-existing auto-memory is present in
  the workspace's
  `~/.claude/projects/<slug>/memory/`, prompts the user (D2)
  whether to bulk-ingest into graphiti.
- **B4.** Per-turn UserPromptSubmit contributor probes graphiti
  health (sidesteps via a probe call that's already on the
  retrieval path); on N consecutive unhealth events, flips
  `autoMemoryEnabled` to true and stamps
  `<workspace>/.pos/memory-fallback-started-at`.
- **B5.** Recovery: same probe detects healthy; flips
  `autoMemoryEnabled` back to false; spawns detached ingestion job
  (mirrors the live-client Stop-hook detachment shape) that reads
  files newer-than-mtime and add_episode's each.
- **B6.** Persona surfaces a "memory-system state" bullet in its
  per-turn awareness block (composable onto whatever awareness
  contributor lands; if no awareness contributor exists yet, this
  bullet is the first one — small new surface).

The plan author should treat these as outcome-shaped behaviours,
add ACs, and translate into the §5 / §6 / §7 plan structure used by
the in-flight live-client plan. The B1–B6 list is a research
sketch, not the AC list.

**Cross-reference:** the live-client amendment plan
(`docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`)
must land **before** this amendment. The recommended design depends
on the live MCP client adapter (B5's add_episode call) and the
fail-soft retrieval path (B4 reuses the same path).

---

## 11. Halt conditions / ODD violations surfaced

None during research. The amendment scope as designed is clean per
§7. No surrounding §2.5 violations spotted.

**Specifically NOT halt-triggered:**
- Cost of cold-start ingestion (~49 minutes for typical workspace
  size) is below the dispatcher's threshold (>50 episodes / hours).
  D2's opt-in path absorbs the surprise.
- Recommended design forces a sealed-component edit only inside
  `workspace-bootstrap`, `hands-off-lifecycle`, and
  `primary-persona` — all three are existing sealed components
  with established merge patterns.

---

## 12. Three-lens read

- **Lens 1 (Claude leverage).** The design composes on documented
  Claude Code primitives only: `autoMemoryEnabled` in settings.json,
  `/memory` slash-command toggle (left to the user), the existing
  `SessionStart` / `UserPromptSubmit` / `Stop` hooks, the
  documented `health` tool / `/health` endpoint on graphiti. No
  custom polling daemon, no orchestrator-side reconciler. **Pure
  composition.**
- **Lens 2 (Translation / Toolkit).**
  - *Primary-persona test:* YES. The user never has to think about
    "is my memory in graphiti or in MEMORY.md right now?" — the
    persona always answers from whatever is healthy, the user's
    natural-language "remember X" gets honoured wherever it lands.
    Translation burden absorbed.
  - *Harness test:* YES. The settings-mutator `set_auto_memory_
    enabled` is a reusable primitive. The probe pattern (HTTP
    health check + per-turn observer + state-flip mutator) is the
    template for any future "external dependency that needs auto-
    heal" work. The ingestion job is reusable for any future
    "import file-shaped content into graphiti" need.
- **Lens 3 (ODD authoring).** ACs map cleanly to outcome-shaped
  behaviours (states, transitions, post-conditions). Reverse
  direction is constrained: every code path the eventual builder
  produces traces back to a named AC.

---

## 13. References

- Claude Code memory docs:
  <https://code.claude.com/docs/en/memory> (fetched 2026-04-26)
- Claude Code settings docs:
  <https://code.claude.com/docs/en/settings> (fetched 2026-04-26)
- Claude Code hooks docs:
  <https://code.claude.com/docs/en/hooks> (fetched 2026-04-26)
- Live-client amendment plan (the prerequisite):
  `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`
- Live-client amendment research (the prerequisite):
  `docs/rebuild/plans/research/memory-system-live-client-and-stop-hook-write-research.md`
- Memory-system component proposal:
  `docs/rebuild/components/memory-system/proposal.md`
- Memory-system component research (cites Claude Code memory as
  candidate #8): `docs/rebuild/components/memory-system/research.md`
- Settings.json merge precedent (amendment #37, #46, #47):
  `hands-off-lifecycle/hooks/first_run_settings.py`,
  `hands-off-lifecycle/hooks/first_run_helper.py`
- Workspace-bootstrap precedent (amendment #36, #47):
  `workspace-bootstrap/src/`
- Memory-graphiti health surface (amendment #34):
  `memory-system/src/service.py:329` (`/health` Starlette route)
- VALUE_PROPOSITION:
  `docs/rebuild/VALUE_PROPOSITION.md`
- ODD methodology + ODD-in-pos:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- STATE / FUTURE_IDEAS:
  `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`

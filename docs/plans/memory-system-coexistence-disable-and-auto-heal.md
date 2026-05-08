# Plan — memory-system coexistence: disable Claude Code auto-memory + auto-heal fallback

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** `de5fe11`.
**Pre-amendment tip:** placeholder — captured at brief-dispatch
(`baseline: <sha>` in the manifest, BASELINE-as-HEAD~1 pattern per
amendments #29 / #34–#48).
**Amendment number:** unassigned at authoring; assigned at dispatch.
Plan filename carries the family slug, no numeric prefix on the
umbrella; per-amendment manifest slug placeholder
`memory-system-coexistence-disable-and-auto-heal` (revisable).
**Research (locked, governs):**
`docs/plans/research/memory-system-coexistence-triage-research.md`
(1003 lines, owner-locked recommendation Hybrid F + D1–D5
2026-04-26).
**Composes on (sealed):** `workspace-bootstrap` (amendment #47 —
`.mcp.json` writer + scaffolding patterns), `hands-off-lifecycle`
(amendments #37, #45, #46, #48 — settings.json merge surface), and
`primary-persona` (amendments #32, #33, #35–#37, #40, #46, #48 —
session-start emitter, user-prompt-submit retrieval contributor,
live MCP client, Stop-hook write path).
**Hard prerequisite (landed):** memory-system live MCP client +
Stop-hook turn-close write — amendment commit `74cdf4e`, seal
`452e7d4` (per
`docs/plans/memory-system-live-client-and-stop-hook-write.md`
§14 commit-SHAs block). This amendment composes on the live-client
adapter `primary-persona/src/mcp_memory_client.py` and the
`add_episode` write path that landed there.

---

## 1. Summary / TLDR

Two parallel "Claude accumulating learnings" memory stores —
Claude Code's built-in auto-memory at
`~/.claude/projects/<slug>/memory/` and the persona's graphiti
graph via the live MCP client — coexist after the live-client
amendment landed. Both inject context at session/turn start; both
write learnings; both can capture the same "remember X" intent.
The user named this a chaos surface and ruled the outcome
"no parallel-memory confusion."

This amendment closes the chaos surface by implementing the
research's locked **Hybrid F** design across three states:

1. **Healthy state (default):** workspace-bootstrap authors
   `autoMemoryEnabled: false` into `.claude/settings.json` at
   first-run; graphiti is the sole memory store; the persona's
   live MCP client (post-#48) is the sole writer/reader.
2. **Unhealthy state (fallback):** the persona's per-turn health
   probe detects graphiti unhealth on a debounce; a settings
   mutator flips `autoMemoryEnabled` to `true` and stamps a
   workspace-local fallback marker carrying the start timestamp.
   Claude Code's native auto-memory takes over without further
   pos-v2 wiring.
3. **Recovery state (ingestion):** the same probe detects
   graphiti returning healthy; the mutator flips
   `autoMemoryEnabled` back to `false`; a detached background
   ingestion job reads MEMORY.md + every `feedback_*.md` whose
   mtime is newer than the fallback marker and `add_episode`s
   each into graphiti, then non-destructively appends an
   ingestion-timestamp marker comment at the top of MEMORY.md.

The five D-decisions are owner-locked 2026-04-26 (research §9):
HTTP GET probe (D1); opt-in cold-start ingestion (D2); flip-back
on user-toggle with persona-surfaced notice + `.claude/settings.local.json`
escape hatch (D3); no FileChanged watcher (D4); leave MEMORY.md
with timestamp marker, non-destructive (D5).

Sealed-component fence: `workspace-bootstrap/` +
`hands-off-lifecycle/` + `primary-persona/`. No other component
is touched.

Per CLAUDE.md output convention, owner reads from §6 (decisions
for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **v1.0 architectural — "persistent + retrievable memory"**
  (objectives spec §1; VALUE_PROPOSITION §"Unpacking the
  toolkit" item 1: *"Today's response is informed by yesterday's
  decisions."*). #48 made the persona memory live; this amendment
  ensures the live store is **canonical** rather than competing
  with a parallel auto-memory surface — without coexistence
  resolution, "today's response informed by yesterday's
  decisions" is confused by two stores disagreeing.
- **v1.2 R16 — Framework-not-content.** Pure framework wiring:
  no persona content, no memory content, no policy authored.
  The mutator + probe + ingestion job are framework primitives.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* the user does not need to
    think about "is my correction in graphiti or in MEMORY.md
    right now?" — translation burden absorbed at the framework
    layer. The persona always answers from whatever store is
    healthy; recovery ingestion drains the fallback into
    graphiti. The user is entitled to ignore the substrate.
  - *Harness test (AC.PO.2):* `set_auto_memory_enabled` (the
    settings mutator), the HTTP-loopback health probe pattern,
    and the recovery ingestion job are reusable primitives.
    Future "external dependency that needs auto-heal" features
    compose against the same template.

**Sealed-component amendment classification.** Three sealed
components touched:

- `workspace-bootstrap`: new first-run authoring of
  `autoMemoryEnabled: false` (composes onto the existing
  `.claude/settings.json` initialisation surface). Pure-additive
  at the public surface. Tests added.
- `hands-off-lifecycle`: new `set_auto_memory_enabled` +
  `_is_pos_v2_owned_auto_memory_setting` helpers in
  `first_run_settings.py`; new probe-and-flip helper +
  fallback-marker write in `first_run_helper.py` or a new sibling
  module; new bookkeeping for the fallback marker file location.
  Pure-additive. H19 frozen-BASELINE per amendment #23. Tests
  added.
- `primary-persona`: new HTTP-loopback health probe primitive
  (composes onto the per-turn UserPromptSubmit retrieval
  contributor existing in `memory_consumer.py` /
  `session_start_emitter.py`); new recovery ingestion CLI
  subcommand on `primary_persona.cli` that reads the fallback
  marker, enumerates auto-memory files newer-than-mtime, and
  drives `add_episode` against the live MCP client; new
  persona-surfaced notice contributor for the user-toggle
  override case (D3). Pure-additive. Tests added.

**ODD §2.5 reverse direction.** Every code path, branch,
dependency, and test in this amendment must trace back to a named
AC under §5. No silent branches; no defensive `if`s without
backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?** Three
documented Claude Code primitives, composed:

1. **`autoMemoryEnabled` in `.claude/settings.json`.** Documented
   project-scope setting; the canonical disable surface for
   Claude Code's auto-memory feature. Research §2.5 verified
   this is the documented control. The amendment writes / flips
   exactly one boolean field; no path-pattern matching, no
   intercept-and-route, no undocumented internal-write
   reverse-engineering.
2. **`SessionStart` + `UserPromptSubmit` hooks.** The probe
   composes onto the existing per-turn retrieval contributor
   (already runs every turn; already calls graphiti's `search`;
   already pays the loopback latency). Augmenting it to also
   trigger the settings mutator on debounced unhealth is
   small-additive.
3. **Graphiti's `/health` HTTP route.** Sidecar service exposes
   `GET /health` (amendment #34); cheaper than the MCP `health`
   tool (no MCP handshake required). Probe is one HTTP GET on
   loopback.

The design is textbook Lens 1: documented surfaces composed; no
undocumented intercept; no custom polling daemon.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation
burden?* YES — load-bearing. Without coexistence resolution, the
user has to know which of two stores their correction landed in,
why the persona sometimes answers from one and sometimes the
other, and how to manually reconcile when they diverge.
The translation layer is leaking memory-substrate detail into the
user's mental model. This amendment absorbs the substrate
question at the framework layer: one canonical store at any
moment, recovery ingestion drains fallback content into the
canonical store, the user never has to know which store an
answer came from.

**Harness test.** *Does this add to the toolkit the primary
persona can draw from?* YES. Three reusable primitives:

- `set_auto_memory_enabled(*, settings_path, enabled)` — every
  future feature that needs to flip a boolean field in the
  workspace's `.claude/settings.json` (analogous future work:
  an "expert-mode" flip, a "verbose-logging" flip, a "telemetry-
  paused" flip) composes against this primitive.
- The HTTP-loopback health probe pattern (probe → debounce →
  flip-side-effect on threshold) — every future "external
  dependency that needs auto-heal" feature reuses this template.
- The recovery ingestion job (read marker → enumerate by mtime →
  format as episodes → detached `add_episode` per file) — every
  future "import file-shaped content into graphiti" need reuses
  this template.

### Lens 3 — ODD authoring

ACs are outcome-shaped. No method in any AC. Behaviour-count
forward direction in §5.x. Reverse direction is the builder's
audit; the plan is structured so reverse-trace is mechanical
(every behaviour maps to one AC; every code path the eventual
builder produces traces back to one AC).

---

## 4. Objective

The pos-v2 workspace operates with exactly one canonical memory
store at every moment. While graphiti is healthy, the workspace's
`.claude/settings.json` carries `autoMemoryEnabled: false` so
Claude Code's auto-memory is dormant; graphiti is the sole store.
While graphiti is unhealthy on a debounced threshold, the same
settings file carries `autoMemoryEnabled: true` and a
workspace-local fallback marker stamp records the transition;
Claude Code's native auto-memory takes over without further
pos-v2 wiring. On graphiti recovery the setting flips back to
`false`, and a detached background ingestion job reads every
auto-memory file (`MEMORY.md` + `feedback_*.md`) whose mtime is
newer than the fallback marker, formats each as a graphiti
episode, and writes via the live MCP client; on success the
ingestion job appends a non-destructive timestamp marker comment
at the top of MEMORY.md. The user never has to know which store
holds a given correction; opt-in cold-start bulk-ingestion runs
once at first-run if pre-existing auto-memory content is
present; persona surfaces a notice when the user manually
overrides the auto-memory toggle and points them at
`.claude/settings.local.json` as the escape hatch. Failures at
every level are fail-soft — the user's session is never blocked.

---

## 5. Acceptance criteria

Each AC is outcome-shaped. Forward behaviour-count check in §5.x.
The §2.5 reverse direction is the builder's pre-seal audit
(restated as halt-and-signal trigger in §8).

### AC.MC.1 — First-run authors `autoMemoryEnabled: false`

Given a fresh workspace bootstrapped via `workspace-bootstrap`,
the produced `<workspace>/.claude/settings.json` contains the
top-level key `autoMemoryEnabled` set to `false`. Other top-level
keys (`hooks.SessionStart`, `hooks.UserPromptSubmit`, `hooks.Stop`,
`agent`, `statusLine`, etc.) are preserved unchanged. When
settings.json does not pre-exist, the merge creates it with
`autoMemoryEnabled: false` plus whatever other stanzas the
bootstrap adapter chain authors.

### AC.MC.2 — Mutator flips `autoMemoryEnabled` atomically

`hands-off-lifecycle/hooks/first_run_settings.py` exposes a
public `set_auto_memory_enabled(*, settings_path, enabled: bool)`
function. Calling it on an existing settings.json updates only
the `autoMemoryEnabled` key to the requested boolean and
preserves every other top-level key byte-for-byte. The write is
atomic (no partial-write window observable to a concurrent
reader). Calling on a settings.json whose
`autoMemoryEnabled` is already at the requested value is a no-op
(no file mtime change, no spurious write).

### AC.MC.3 — Health probe distinguishes healthy / unhealthy / debounce

A health-probe primitive in `primary-persona/src/` issues
`GET http://127.0.0.1:<sidecar-port>/health` with a bounded
timeout and returns one of three observable outcomes:

- **healthy** — HTTP 200 with `{"healthy": true, ...}` payload.
- **unhealthy** — HTTP 200 with `{"healthy": false, ...}`, or
  HTTP non-200, or connection-refused, or timeout.
- **degraded-debounce** — the probe must not declare unhealthy
  on a single transient failure; only after N consecutive
  unhealthy observations within a bounded window does the
  caller treat the state as unhealthy.

The `<sidecar-port>` is recovered from the workspace's
per-workspace memory sidecar config (per amendment #29). N (the
debounce threshold) is method; the AC measures the observable
"single transient failure does NOT trigger fallback; sustained
unhealth DOES."

### AC.MC.4 — Sustained unhealth flips to fallback + stamps marker

Given the per-turn observer detects sustained graphiti unhealth
(per AC.MC.3 debounce), the settings mutator (AC.MC.2) flips
`autoMemoryEnabled` to `true` AND a workspace-local fallback
marker file (`<workspace>/.pos/memory-fallback-started-at` or
sibling location) is created carrying the ISO-8601 timestamp of
the transition. If a marker already exists (re-entrancy), it is
not overwritten (fallback windows do not nest).

### AC.MC.5 — Recovery flips back + spawns ingestion

Given a fallback marker exists AND the per-turn observer detects
sustained graphiti health (per AC.MC.3), the settings mutator
flips `autoMemoryEnabled` back to `false` AND a detached
background ingestion job is spawned via the same detachment
pattern the live-client Stop-hook uses (amendment #48 D3 —
`subprocess.Popen(..., start_new_session=True, ...)`). The
spawning hook returns within milliseconds independent of the
ingestion's runtime.

### AC.MC.6 — Ingestion writes one episode per fallback-window file

The ingestion job reads the fallback marker timestamp,
enumerates every file under
`~/.claude/projects/<workspace-slug>/memory/*.md` whose mtime is
strictly greater than the marker timestamp, formats each file's
content as a graphiti episode (one episode per file; episode
body contains the file's text; `group_id` equals the workspace
slug; `source="message"`; `reference_time` derived from file
mtime; `name` derived from filename), and issues exactly one
`add_episode` MCP call per file via the live client landed in
amendment #48. On success across all files, the ingestion job
clears the fallback marker.

### AC.MC.7 — Ingestion appends non-destructive timestamp marker

On successful ingestion (AC.MC.6), the ingestion job appends a
timestamp-bearing comment block at the top of
`~/.claude/projects/<workspace-slug>/memory/MEMORY.md` recording
the ingestion completion timestamp. The original auto-memory
content (MEMORY.md body + every feedback_*.md file) is preserved
byte-for-byte; the marker is additive. The marker shape is
unambiguously identifiable (a documented sentinel string) so a
future ingestion run can detect "this content was already
ingested" and skip files dated before the marker. (D5 lock.)

### AC.MC.8 — Cold-start ingestion is opt-in

At first-run, IF pre-existing auto-memory content is detected in
the workspace's `~/.claude/projects/<workspace-slug>/memory/`
directory (one or more `*.md` files dated before the workspace's
first-run timestamp), the persona surfaces an opt-in choice to
the user — yes/no, with the file count and an estimated
extraction duration — and proceeds with bulk-ingestion ONLY when
the user opts in. Declining leaves the auto-memory dir untouched
and proceeds with steady-state behaviour (auto-memory disabled,
graphiti the sole forward-store). The choice is persisted to
the workspace so first-run idempotency does not re-prompt on
subsequent runs. (D2 lock.)

### AC.MC.9 — User toggle override surfaces notice + escape hatch

Given the user manually re-enables auto-memory via the
`/memory` slash-command toggle (which writes
`autoMemoryEnabled: true` into the project-scope settings file)
while graphiti is healthy, on the next per-turn observer cycle
the mutator flips it back to `false` AND the persona surfaces a
single user-visible notice (via the appropriate
`additionalContext` / awareness surface) explaining that pos-v2
keeps the project-scope toggle off while graphiti is healthy and
pointing the user at `<workspace>/.claude/settings.local.json`
as the permanent override surface (which pos-v2 explicitly does
NOT touch). The notice is rate-limited to one surface per
toggle-flip event (not every turn). (D3 lock.)

### AC.MC.10 — All failure paths are fail-soft

Every component of the design exits 0 / fails-soft on every
error path:

- **Probe failure** — probe primitive cannot reach loopback,
  resolver-error, etc.: probe returns "unhealthy"; the user's
  retrieval block on that turn is empty per existing AC.M.3
  (live-client amendment); the per-turn observer logs and
  proceeds.
- **Mutator failure** — settings.json unwritable, malformed,
  etc.: mutator surfaces a structured diagnostic to the
  workspace-local memory log (per amendment #48 D8) and
  returns; no traceback reaches the user.
- **Ingestion partial failure** — one or more `add_episode`
  calls fail mid-batch: completed episodes stay; uncompleted
  files remain in the auto-memory dir; fallback marker is NOT
  cleared; structured diagnostic logged; the next probe cycle
  re-attempts via the marker. No zombie subprocess.
- **Marker-write failure** — fallback marker directory missing
  or unwritable: the mutator skips the flip (does not flip
  without the marker stamp; consistency over availability) and
  logs.

No path raises through to user-visible stdout/stderr; no path
blocks the user's next turn.

### AC.MC.11 — Backwards-compat: existing #46/#47/#48 behaviours unchanged

Existing tests in `primary-persona/tests/`,
`hands-off-lifecycle/tests/`, and `workspace-bootstrap/tests/`
(notably `test_AC46_*`, `test_AC.45_*`, `test_AC37_*`,
`test_AC47_*`, `test_AC.M.*` from amendment #48,
`test_no_sealed_amendments.py` for every sealed component) stay
green after this amendment lands. The live-client adapter
surface (post-#48) is consumed unchanged; the Stop-hook
turn-close write path is unchanged; the per-turn retrieval
contributor's existing fail-soft empty-block path (AC.M.3) is
unchanged.

### AC.MC.12 — ODD §2.5 reverse direction

Every code path, branch, dependency, and test in the amendment
diff traces back to AC.MC.1 – AC.MC.11. The builder audits both
directions before seal. (Halt-and-signal if any code path lacks
backing.)

### AC.MC.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths
under: `workspace-bootstrap/src/`, `workspace-bootstrap/tests/`,
`workspace-bootstrap/pyproject.toml`,
`primary-persona/src/`, `primary-persona/tests/`,
`primary-persona/pyproject.toml`,
`hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`, and
the universal-paths admissions (`docs/plans/`,
`CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
`docs/FUTURE_IDEAS.md`). Anything outside this set is a
halt condition.

### 5.x — Behaviour-count check (forward)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | First-run writes `autoMemoryEnabled: false` to project settings | AC.MC.1 |
| 2 | Mutator flips the field atomically; preserves siblings | AC.MC.2 |
| 3 | Health probe distinguishes healthy / unhealthy with debounce | AC.MC.3 |
| 4 | Sustained unhealth flips field to true + stamps fallback marker | AC.MC.4 |
| 5 | Recovery flips field back + spawns detached ingestion | AC.MC.5 |
| 6 | Ingestion writes exactly one episode per fallback-window file | AC.MC.6 |
| 7 | Ingestion appends non-destructive timestamp marker to MEMORY.md | AC.MC.7 |
| 8 | Cold-start ingestion at first-run is opt-in | AC.MC.8 |
| 9 | User toggle override → flip-back + persona-surfaced notice + escape-hatch | AC.MC.9 |
| 10 | All failure paths are fail-soft | AC.MC.10 |
| 11 | Backwards-compat with #46/#47/#48 + earlier | AC.MC.11 |
| 12 | ODD §2.5 reverse direction | AC.MC.12 |
| cross-cutting | Seal-diff window respected | AC.MC.S |

11 declared behaviours, 13 ACs (one cross-cutting + the §2.5
audit). No method-in-AC.

---

## 6. Decisions for owner (read this first)

The five primary D-decisions D1–D5 are **owner-locked 2026-04-26**
per the research §9 block. They are restated here for the
builder's reference and are NOT requesting new rulings:

- **D1 — Probe mechanism: HTTP GET on
  `http://127.0.0.1:<sidecar-port>/health`** (locked).
- **D2 — Cold-start ingestion is opt-in at first-run** (locked).
- **D3 — User-toggle override: flip back + persona-surfaced
  notice + `.claude/settings.local.json` escape hatch** (locked).
- **D4 — No FileChanged watcher in this amendment** (locked).
- **D5 — Leave MEMORY.md non-destructively with appended
  ingestion-timestamp marker** (locked).

The plan-author has surfaced the following genuinely-uncertain
decisions during plan authoring. Each names a recommendation; Luke
rules from this block, not from reading the full plan.

### D-plan.1 — Where the per-turn health probe lives

- **Recommendation:** new module
  `primary-persona/src/memory_health_probe.py` exposing a
  `probe_memory_health(*, sidecar_port, timeout) -> ProbeResult`
  primitive AND a debounce wrapper
  `observe_memory_health(workspace_root) -> HealthState`
  that maintains the consecutive-failure counter via a
  workspace-local state file. The existing UserPromptSubmit
  retrieval contributor calls `observe_memory_health` and acts on
  the result (flip mutator on sustained unhealth → fallback;
  flip mutator on sustained health if a marker exists →
  recovery+ingestion).
- **Why:** keeps probe-protocol concerns out of the retrieval
  contributor module; matches amendment #48's separation
  (`mcp_memory_client.py` is a callable peer of the orchestrating
  emitters). The debounce state must persist across hook
  invocations (each is a fresh process), so a workspace-local
  state file is the natural shape.
- **Alternative:** inline the probe inside
  `memory_consumer.py`. Smaller diff but couples probe protocol
  to the retrieval contract.

### D-plan.2 — Where the recovery ingestion CLI lives

- **Recommendation:** new module
  `primary-persona/src/memory_recovery.py` exposing
  `ingest_fallback_window(workspace_root) -> IngestResult` AND a
  new `recover-memory` CLI subcommand on `primary_persona.cli`
  routing to it. The detached subprocess invokes
  `python -m primary_persona.cli recover-memory` after the
  per-turn observer flips the setting back.
- **Why:** mirrors amendment #48 D2 / D3 shape (`stop_emitter.py`
  + `cli stop` + `cli memory-write` detached subprocess). One
  module per recovery responsibility keeps the surface scannable.
- **Alternative:** add to `mcp_memory_client.py`. Tighter
  coupling; bigger file.

### D-plan.3 — Where the settings mutator's call sites live

- **Recommendation:** the mutator invocation lives in
  `primary-persona/src/memory_health_probe.py` (the per-turn
  observer module) — it owns the state-machine transition logic
  and calls the
  `hands_off_lifecycle.hooks.first_run_settings.set_auto_memory_enabled`
  function as a peer dependency. Workspace-bootstrap's first-run
  authoring (AC.MC.1) calls the mutator at scaffold time (a
  one-shot write of `autoMemoryEnabled: false`), via a tiny
  bootstrap adapter or extension to an existing adapter (D-plan.5
  below).
- **Why:** the per-turn observer is the long-running owner of
  the state-flip decision; bootstrap does the one-shot baseline
  write. Both call into the same mutator, no duplication.
- **Alternative:** put the per-turn flip logic in
  `hands-off-lifecycle/hooks/first_run_helper.py` alongside
  `_maybe_merge_*`. Rejected — first_run_helper is bootstrap-
  scoped; per-turn observation is a runtime concern owned by
  the persona layer.

### D-plan.4 — Fallback marker file path

- **Recommendation:** `<workspace>/.pos/memory-fallback-started-at`
  — newline-terminated ISO-8601 timestamp on a single line.
- **Why:** workspace-local convention `.pos/` is established
  since amendment #28; co-located with `.pos/memory-writes.log`
  (amendment #48 D8) and `.pos/last-turn-id` (amendment #48
  D4). Consistent surface.
- **Alternative:** under `~/.claude/projects/<slug>/memory/` so
  the marker is co-located with auto-memory content. Rejected —
  pos-v2 does not own that directory; the marker is a pos-v2
  bookkeeping artefact and belongs in pos-v2's bookkeeping
  surface.

### D-plan.5 — Where the bootstrap adapter that writes `autoMemoryEnabled: false` lives

- **Recommendation:** extend the existing
  `workspace-bootstrap/src/workspace_bootstrap/adapters/primary_persona.py`
  (or sibling `first_run_scaffold.py`) to call
  `set_auto_memory_enabled(settings_path=..., enabled=False)`
  as part of the persona-related scaffold pass. No new adapter
  file; the auto-memory setting is conceptually persona-scoped
  framework wiring.
- **Why:** the workspace-bootstrap adapter set is one-adapter-
  per-component; `autoMemoryEnabled` is a Claude-Code-feature
  setting that pos-v2 controls in service of the persona's
  memory consumer. Putting it in the persona adapter keeps the
  registration count constant.
- **Alternative:** a new `auto_memory_disable.py` adapter.
  Rejected — adds a registration line + a manifest entry for
  one boolean; not worth the surface area.
- **Caveat:** the builder may discover during scaffold-graph
  ordering that the auto-memory setting must land BEFORE or
  AFTER another stanza for ordering consistency. If so, the
  adapter ordering decision is method (within the
  workspace-bootstrap framework's published extension protocol);
  not an AC concern.

### D-plan.6 — Debounce shape (consecutive count vs windowed)

- **Recommendation:** consecutive-count threshold of 3 (three
  successive unhealthy observations across consecutive turns
  flip to fallback; one healthy observation resets to zero).
- **Why:** simple, deterministic, easy to test. The per-turn
  observer is the natural rhythm — turns happen on the order of
  minutes, so three turns is ~3-5 minutes of sustained unhealth
  before fallback engages. This is fast enough to catch real
  outages and slow enough to absorb transient blips. The threshold
  is method (the AC says "single transient failure does NOT
  trigger fallback; sustained unhealth DOES" — three is the
  builder's reasonable choice).
- **Alternative:** windowed (N failures in T seconds). More
  expressive but requires a clock-aware state file. Not worth it
  at this scope.

### D-plan.7 — Cold-start opt-in surface

- **Recommendation:** the opt-in prompt fires on the FIRST user
  turn after first-run scaffold completes. The persona's
  UserPromptSubmit retrieval contributor surfaces an
  `additionalContext` block on that first turn explaining the
  detected auto-memory content + estimated duration + the
  interactive choice; persona prompt instructs to ask the user
  yes/no. Choice is recorded in
  `<workspace>/.pos/memory-cold-start-decision` (one of `yes` /
  `no` / `pending`) and re-checked on subsequent first-run
  invocations until non-pending.
- **Why:** uses the existing UserPromptSubmit surface (no new
  hook event); persona is the natural layer for "ask the user a
  yes/no question"; the workspace-local file is the
  idempotency anchor.
- **Alternative:** drive the prompt from a SessionStart contributor
  rather than UserPromptSubmit. SessionStart fires before the
  user has typed anything; UserPromptSubmit fires when there's a
  real conversational moment. UserPromptSubmit is the cleaner
  surface.

### D-plan.8 — Notice rate-limiting (D3 lock implementation)

- **Recommendation:** workspace-local sentinel file
  `<workspace>/.pos/memory-toggle-notice-last-shown-at` storing
  ISO-8601 timestamp of the last notice surface. Notice
  surfaces only when the per-turn observer detects a
  user-toggle override (settings.json has `autoMemoryEnabled:
  true` while probe says healthy AND no fallback marker
  exists), AND either the sentinel is missing OR its timestamp
  is older than N hours (recommendation: 24h).
- **Why:** prevents the persona from nagging the user every
  turn while still re-surfacing the notice if the user re-
  toggles the next day.
- **Alternative:** surface once-per-toggle-event-detection
  without a time-based reset. Rejected — if the user toggles
  back and forth across days, they may want the reminder again.

---

## 7. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence.** In-scope source: `workspace-bootstrap/src/`,
   `workspace-bootstrap/tests/`, `workspace-bootstrap/pyproject.toml`,
   `primary-persona/src/`, `primary-persona/tests/`,
   `primary-persona/pyproject.toml`,
   `hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`.
   Any edit elsewhere (other than the universal-paths admissions
   in §10) is a halt trigger (§8).
3. **Reversibility.** Fully reversible. The settings field
   defaults of Claude Code (auto-memory on) are restored simply
   by deleting `autoMemoryEnabled` from the file. The fallback
   marker is a pos-v2 artefact; deleting it returns the system
   to "no fallback active." MEMORY.md is never destructively
   modified (D5 lock; AC.MC.7).
4. **No destructive auto-memory edits.** Per D5 lock and
   AC.MC.7, the ingestion job NEVER deletes, truncates, moves,
   or rewrites existing auto-memory content. Append-only
   timestamp marker; nothing else.
5. **No FileChanged watcher.** Per D4 lock, the design does
   NOT register a `hooks.FileChanged` contributor for the
   auto-memory directory in this amendment. (Future amendment
   may add a diagnostic contributor; not now.)
6. **No new top-level objective.** Per the locked research
   constraint, this work satisfies existing memory-system D1
   (graphiti as canonical) + the spec's "persistent +
   retrievable memory" objective. No new spec-level objective
   is created.
7. **No edit to user-level or local-scope settings files.**
   The mutator writes ONLY `<workspace>/.claude/settings.json`.
   `~/.claude/settings.json` and
   `<workspace>/.claude/settings.local.json` are explicitly
   not touched. The local-scope file is the user's documented
   override surface (D3 lock; AC.MC.9).
8. **Dependency fence.** No new runtime dependencies. The
   probe uses `urllib` (stdlib); the ingestion job uses the
   `mcp` package already added in amendment #48; the mutator
   uses `json` (stdlib). Test-only deps per STATE.md rule #8
   (already in place — pytest, etc.).
9. **Fail-closed direction.**
   - Probe failure: treat as one unhealthy observation, do not
     panic-flip on first error (AC.MC.3).
   - Mutator write failure: log diagnostic, do not flip without
     marker stamp (AC.MC.10).
   - Ingestion partial failure: leave marker intact for
     re-attempt; no destructive ops (AC.MC.10).
   - Marker missing during recovery: skip flip-back; preserve
     fallback state until marker is recoverable (AC.MC.10).
10. **CDC adherence.** Plan-before-code (this plan), background-
    agent default for the build, scope-only dispatch, research-
    before-plan (research doc landed at the same time and locked
    the design).
11. **`pos-amend apply --dry-run` green is a hard prereq** per
    amendment #22.
12. **AC35.3 / AC.45.S / AC46.S / AC47.S / AC.M.S preservation.**
    The starter-pending marker prefix (AC35.3), loam-mode
    SessionStart hook (AC.45), persona session-start +
    user-prompt-submit hooks (AC46), `.mcp.json` contents
    (AC47), and the live-client + Stop-hook write surface
    (amendment #48) are all unchanged after this amendment.
13. **Persona content untouched.** No edits to `personas/`.
    Persona content authoring is umbrella-deferred (Q1 from
    the umbrella plan); the notice text in AC.MC.9 is
    framework-side wording rendered into `additionalContext`,
    not persona content.
14. **Live-client amendment is a hard prerequisite.** The
    ingestion job in AC.MC.6 calls `add_episode` via the live
    client landed in amendment #48 (`mcp_memory_client.py`).
    If the live client is not present at the AC.MC.5
    detached-subprocess invocation site, halt.

---

## 8. Halt triggers

Any of the following → halt and signal back to the dispatcher;
do NOT silently work around:

1. **Cross-component scope expansion.** Any required source
   edit to a sealed component outside the §7 fence — halt.
2. **AC cannot be expressed outcome-shaped.** If during build
   an AC requires method to express, halt; the AC needs
   re-authoring at the dispatcher's level.
3. **`pos-amend apply --dry-run` red** at any point — halt.
4. **`autoMemoryEnabled` setting docs diverge from research.**
   If empirical verification reveals the field isn't honoured
   at project scope (Claude Code release behaviour change),
   halt; the fallback design is built on this surface.
5. **§2.5 violation in surrounding code.** If during build the
   builder discovers any branch in `memory_consumer.py`,
   `session_start_emitter.py`, `mcp_memory_client.py`,
   `stop_emitter.py`, `first_run_settings.py`,
   `first_run_helper.py`, or any of the workspace-bootstrap
   adapters it touches that has no backing AC — halt. Do NOT
   extend a violating surface.
6. **A test for any AC.MC.x cannot be written deterministically.**
   Halt.
7. **The 5 locked decisions (D1–D5) turn out to need
   re-ruling.** If empirical reality during build contradicts
   one of the locked decisions in a way the builder cannot
   work around — halt and surface to the dispatcher; do not
   silently re-rule.
8. **Required new top-level objective surfaces.** If during
   build a required behaviour cannot be traced to an existing
   spec objective AND requires authoring a new one — halt
   immediately; new top-level objectives are owner-only
   territory.
9. **Required source edit outside the §7 fence.** Any necessary
   edit to a sealed component beyond the named fence is a halt
   condition (mirrors halt #1; restated for emphasis).
10. **Auto-memory write paths turn out to use a privileged
    internal mechanism that the disable flag doesn't fully
    suppress.** If empirical verification reveals
    `autoMemoryEnabled: false` does NOT actually stop
    auto-memory writes, halt; the design's correctness depends
    on the documented disable working as documented.
11. **Detachment fails on macOS.** If `Popen(...,
    start_new_session=True)` produces an ingestion subprocess
    that doesn't actually outlive the parent — halt;
    alternative shapes need ruling.

---

## 9. Out of scope (named explicitly per ODD §2.5)

- **FileChanged watcher on MEMORY.md.** Per D4 lock; future
  amendment may add a diagnostic contributor.
- **Destructive auto-memory directory operations.** Per D5
  lock; this amendment is non-destructive only.
- **User-level (`~/.claude/settings.json`) auto-memory
  control.** Out of scope; pos-v2 only manages its own
  workspace's project-scope setting.
- **`<workspace>/.claude/settings.local.json` writes.** Per
  D3 lock; the local-scope file is the user's escape-hatch
  and pos-v2 explicitly does not write to it.
- **Auto-memory directory bulk-archive on first-run.** Per D5
  lock; non-destructive only.
- **Cross-workspace memory unification.** Out of scope;
  group_id keeping is per amendment #33's Rule B.
- **Awareness-block contributor for "graphiti unhealthy" /
  "memory writes failing."** Diagnostic logs land at
  `<workspace>/.pos/memory-writes.log` and the new fallback
  marker; surfacing them as awareness-block categories is a
  future amendment.
- **Generalised "external dependency auto-heal" framework.**
  This amendment hardcodes graphiti as the dependency; the
  pattern can be lifted into a primitive in a future
  amendment but doing so now would over-generalise.
- **Multi-contributor `hooks.UserPromptSubmit` registry for
  the probe-and-flip logic.** The probe-observer composes
  onto the existing single-contributor UserPromptSubmit
  retrieval emitter (amendment #46); registry generalisation
  out of scope.
- **Probing mid-Stop-hook invocation.** The probe runs at
  UserPromptSubmit (per-turn) and at SessionStart (cold-
  start); not inside the Stop hook (which exits in
  milliseconds per amendment #48 AC.M.7).
- **Per-scope group_id for ingested fallback episodes.** All
  ingested episodes land under the workspace slug
  `group_id` per Rule B (amendment #33). Per-scope keying is
  a future amendment.
- **Backup of `.claude/settings.json` before flip.** Per
  research §5.3; the flip is a single boolean, no backup
  needed (the prior value is implicit).
- **Probe daemon (out-of-process background poller).** Per
  research §5.2; the per-turn observer at UserPromptSubmit
  is sufficient.

If any of these surface as hard prerequisites during the build,
halt-and-signal; do not silently expand scope.

---

## 10. Bookkeeping surface (`pos-amend` manifest sketch)

Per amendment #22's `pos-amend` convention. Manifest YAML at
build-dispatch, schema:

```yaml
schema_version: 1
amendment:
  number: <assigned-at-dispatch>
  slug: memory-system-coexistence-disable-and-auto-heal
  title: "memory-system coexistence: disable Claude Code auto-memory + auto-heal fallback"

baseline: <pre-amendment-tip-sha>   # HEAD~1 of amendment commit

plan: docs/plans/memory-system-coexistence-disable-and-auto-heal.md

seal_description: "memory-system coexistence — disable + auto-heal"

components:
  - name: workspace-bootstrap
    seal_test: workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: workspace-bootstrap/tests/SEAL_COMMIT
    frozen_baseline: false
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true   # H19 frozen-BASELINE per amendment #23

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.<assigned-slug>
  body: |
    # Amendment #<n> — memory-system coexistence: disable
    #                  Claude Code auto-memory + auto-heal fallback
    (body authored by builder at seal time; references
     AC.MC.1 – AC.MC.S, this plan, and the locked research
     `docs/plans/research/memory-system-coexistence-triage-research.md`.)
```

**Universal admissions** per amendment #22 ruling #3 cover
`docs/plans/`, `CLAUDE.md`, `docs/odd-*.md`, and
`docs/FUTURE_IDEAS.md`. No other paths admitted.

**Test scope per amendment-dispatch CDC speedups (Luke
2026-04-23):** narrow pre-amendment test scope to
`workspace-bootstrap/tests/` + `primary-persona/tests/` +
`hands-off-lifecycle/tests/`; skip pre-seal full-suite rerun
(sidecar-only edits between amendment and seal); inline
odd-methodology snippets into the dispatch brief.

**Commits:**
- Amendment commit: `feat(workspace-bootstrap, primary-persona,
  hands-off-lifecycle): memory-system coexistence — disable
  Claude Code auto-memory + auto-heal fallback (amendment
  #<n>, AC.MC.1–AC.MC.S)`.
- Seal commit: `chore(seals): memory-system coexistence —
  disable + auto-heal — workspace-bootstrap+primary-persona+
  hands-off-lifecycle at <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the prereq
to amendment commit; `pos-amend seal --plan-doc <abs-path>`
finalises.

---

## 11. Risks + mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `autoMemoryEnabled` doesn't fully suppress writes (Claude Code internal write bypasses the flag) | low | Two stores still active during healthy state; goal 1 fails silently | Empirical verification in pos3 before build (per dispatch verification clause); halt-trigger #10 catches it |
| Probe debounce too aggressive: false-fallback thrashing | low-medium | User flipped to auto-memory unnecessarily during graphiti hiccups | D-plan.6 conservative threshold (3 consecutive); structured diagnostic on every flip surfaces miscalibration |
| Cold-start ingestion exceeds estimated ~50min | low | User surprise + token spend on a longer batch than predicted | D2-locked opt-in absorbs the surprise; user says yes/no with the count visible; batch is detached so user is not blocked |
| User edits MEMORY.md by hand during steady-state | medium | Edit is invisible to graphiti; persona retrieval doesn't know about it | Out-of-scope — D4 disabled the FileChanged watcher; a future amendment can add a diagnostic. AC.MC.7's marker is the user-visible signal that the directory IS being managed |
| Recovery ingestion partial failure leaves graphiti and auto-memory diverged | low-medium | Some episodes ingested, others remain only in MEMORY.md | AC.MC.10 fail-soft: marker stays until full success, next probe cycle re-attempts; structured diagnostic surfaces the partial state |
| Marker file race (two probe observers fire simultaneously) | very low | Double-flip / double-ingestion attempts | Per-turn observer is single-threaded per Claude Code session; concurrent sessions on the same workspace would race but cold-start single-prompt model makes this unlikely; if observed, halt-trigger #5 covers |
| `autoMemoryEnabled: false` requires Claude Code restart to take effect mid-session | medium | Flip-on-recovery is delayed until next session | Acceptable: the recovery-state semantics ("auto-memory disabled, graphiti is sole store") are user-visible only at next session start. The mutator stamps the file synchronously; auto-memory's mid-session writes during fallback are accepted and ingested on recovery |
| Ingestion job's `add_episode` calls saturate the live client's connection pool | low | Recovery is slow but completes | Detached subprocess; one connection per call; if pool pressure observed, halt-trigger #5 / future amendment for pooling |
| User-toggle-override notice surface conflict with future awareness-block contributor | low | Two surfaces racing for the same user-attention slot | D-plan.8 rate-limits the notice; future awareness-block amendment can absorb / replace the surface cleanly |

---

## 12. Three-lens AC trace

| AC | Lens 1 (Claude) | Lens 2 (Translation / Toolkit) | Lens 3 (ODD) |
|----|------------------|---------------------------------|--------------|
| AC.MC.1 | leverages `autoMemoryEnabled` (Claude-native) | toolkit primitive — first-run setting authoring | outcome-shaped |
| AC.MC.2 | composes on `.claude/settings.json` schema | toolkit primitive — `set_auto_memory_enabled` reusable mutator | outcome-shaped |
| AC.MC.3 | composes on graphiti `/health` HTTP route | toolkit primitive — health-probe-with-debounce reusable template | outcome-shaped |
| AC.MC.4 | composes on UserPromptSubmit + settings flip | translation: substrate decision absorbed at framework layer | outcome-shaped |
| AC.MC.5 | composes on Popen-detachment (precedent #48) | translation: recovery is invisible to the user | outcome-shaped |
| AC.MC.6 | composes on live MCP `add_episode` (post-#48) | translation: fallback content surfaces in graphiti as if always there | outcome-shaped, count-bound |
| AC.MC.7 | composes on filesystem-append (no Claude surface) | translation: user can audit the marker; graphiti is canonical | outcome-shaped, non-destructive |
| AC.MC.8 | composes on `additionalContext` (UserPromptSubmit) | translation: cold-start opt-in respects user autonomy | outcome-shaped |
| AC.MC.9 | composes on `additionalContext` (UserPromptSubmit) | translation: persona surfaces the design intent + escape hatch | outcome-shaped |
| AC.MC.10 | composes on stdout-as-additionalContext failure shape (existing #48) | failures absorbed at boundary | outcome-shaped |
| AC.MC.11 | preserves all earlier Claude-native shapes | toolkit backwards-compat | structural |
| AC.MC.12 | n/a | n/a | review-time audit |
| AC.MC.S | n/a | n/a | structural |

---

## 13. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC.MC.1, AC.MC.2, AC.MC.4, AC.MC.5 → AC.PO.1.** One canonical
  store at every moment; substrate-decision absorbed at the
  framework layer; the user does not need to know which store
  holds an answer. Translation burden absorbed.
- **AC.MC.6, AC.MC.7 → AC.PO.1.** Recovery ingestion drains
  fallback content into graphiti without user effort or
  awareness. Non-destructive marker leaves the user-visible
  artefact intact; they can audit but don't have to.
- **AC.MC.8 → AC.PO.1.** Cold-start opt-in respects user
  autonomy; the user is entitled to ignore tokens but is
  surfaced the choice before pos-v2 commits ~50min of
  background work.
- **AC.MC.9 → AC.PO.1.** Notice + escape hatch close the loop:
  a user who manually flips the toggle is not silently
  overridden; the persona explains and points at the documented
  override surface.
- **AC.MC.2, AC.MC.3 → AC.PO.2.** `set_auto_memory_enabled` is
  the reusable settings-mutator primitive; the HTTP-loopback
  health-probe-with-debounce is the reusable external-
  dependency-auto-heal template. Future contributors compose
  against them.
- **AC.MC.10 → AC.PO.1.** Failures absorbed at the boundary;
  user never sees memory-system errors as their problem.

---

## 14. Execution sequencing (suggested; builder's call to refine)

1. **Now — Luke rules on §6 D-plan.x decisions.** Plan stays
   pre-dispatch until rulings land. The 5 main D-decisions
   D1–D5 are owner-locked 2026-04-26 and need no re-ruling.
2. **Empirical verification in pos3 (during plan-author or
   build-dispatch prep).** Confirm Claude Code v2.x honours
   `autoMemoryEnabled: false` at project-scope settings.json
   (writes to MEMORY.md cease while flag is false; reads from
   MEMORY.md may still occur from cached context but new
   writes don't land). Capture the empirical observation in
   the builder's plan.
3. **Build dispatch** (background agent, working dir
   `/Users/lukeivers/ivers-corp-pos-v2/`, brief carries scope
   only — AC.MC.1–AC.MC.S + halt triggers + ODD-check + the
   `pos-amend apply --dry-run` then commit then `pos-amend
   seal --plan-doc <abs-path>` flow).
4. **Verify in pos3:** restart Claude Code; confirm
   `.claude/settings.json` carries `autoMemoryEnabled: false`;
   confirm the `/memory` slash-command shows the auto-memory
   toggle as off; force graphiti-down (kill the sidecar);
   confirm after debounce the field flips to `true` and
   `.pos/memory-fallback-started-at` exists; restart graphiti;
   confirm the field flips back to `false` and the ingestion
   subprocess runs detached; confirm new graphiti episodes
   appear (verify via `mcp__memory-graphiti__search` for the
   ingested file content); confirm MEMORY.md gained the
   non-destructive marker comment at top; confirm
   `~/.claude/projects/-Users-lukeivers-pos3/memory/` content
   is otherwise byte-for-byte unchanged.
5. **Append findings** to `FUTURE_IDEAS_DRAFT.md` per the
   no-overhead capture pattern.
6. **Update `STATE.md`** if this lands during a Phase milestone.

Per `feedback_amendment_dispatch_speedups`: the dispatch scopes
test rerun to `workspace-bootstrap/tests/` +
`primary-persona/tests/` + `hands-off-lifecycle/tests/` only.
Per `feedback_subagent_odd_violation_halt`: the dispatch
carries the explicit halt-and-surface-ODD-violations-in-
surrounding-code clause.
Per `feedback_dispatch_explicit_pos_amend_apply`: the dispatch
names `pos-amend apply --dry-run` + `pos-amend apply` +
`pos-amend seal --plan-doc <abs-path>` explicitly as the
bookkeeping mechanism.
Per `feedback_no_amend_in_agent_dispatches`: corrective commits
only; no `git commit --amend`.
Per `feedback_always_specify_wd_in_dispatches`: the dispatch
specifies WD `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## 15. References

- Locked research (governs):
  `docs/plans/research/memory-system-coexistence-triage-research.md`
- Hard prerequisite (live-client + Stop-hook write — landed):
  `docs/plans/memory-system-live-client-and-stop-hook-write.md`
  (commit `74cdf4e`, seal `452e7d4`)
- Live-client research:
  `docs/plans/research/memory-system-live-client-and-stop-hook-write-research.md`
- Umbrella plan (parent of #46/#47/#48 and this amendment):
  `docs/plans/memory-into-context-integration.md`
- Amendment #33 (D7) plan + research:
  `docs/plans/amendment-33-memory-consumer-wiring-primary-persona.md`,
  `docs/plans/research/amendment-33-memory-consumer-wiring-research.md`
- Amendment #34 (eager-lifespan + `/health` route):
  `docs/plans/amendment-34-memory-system-eager-lifespan-d1-conformance.md`
- Amendment #46 builder plan (sibling pattern for hook-CLI authoring):
  `docs/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
- Amendment #47 builder plan (sibling pattern for `.mcp.json` + workspace-bootstrap adapter shape):
  `docs/plans/amendment-47-workspace-local-mcp-json-writer.builder-plan.md`
- Live MCP client adapter (post-#48):
  `primary-persona/src/mcp_memory_client.py`
- Persona memory consumer substrate
  (`MemoryClient` Protocol, `TurnAggregator`,
  `register_memory_retrieval`, `resolve_workspace_slug`):
  `primary-persona/src/memory_consumer.py`
- Persona session-start emitter (where the per-turn observer
  composes):
  `primary-persona/src/session_start_emitter.py`
- Persona Stop emitter (sibling pattern for the recovery
  CLI subcommand + detached subprocess):
  `primary-persona/src/stop_emitter.py`
- Persona CLI (where the new `recover-memory` subcommand goes):
  `primary-persona/src/cli.py`
- Settings.json merge surface (where `set_auto_memory_enabled`
  goes):
  `hands-off-lifecycle/hooks/first_run_settings.py`
- First-run helper (where `_maybe_*` calls land):
  `hands-off-lifecycle/hooks/first_run_helper.py`
- Workspace-bootstrap adapters (where the first-run
  `autoMemoryEnabled: false` write goes):
  `workspace-bootstrap/src/workspace_bootstrap/adapters/primary_persona.py`
  (or sibling — D-plan.5)
- Memory-system MCP service + `/health` route:
  `memory-system/src/service.py`
- Claude Code memory docs:
  <https://code.claude.com/docs/en/memory>
- Claude Code settings docs:
  <https://code.claude.com/docs/en/settings>
- Claude Code hooks docs:
  <https://code.claude.com/docs/en/hooks>
- ODD methodology + ODD-in-pos:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- VALUE_PROPOSITION:
  `docs/VALUE_PROPOSITION.md`
- STATE / FUTURE_IDEAS:
  `docs/STATE.md`, `docs/FUTURE_IDEAS.md`
- Amendment-dispatch bookkeeping:
  `tools/pos-amend/`

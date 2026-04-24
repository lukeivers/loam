# Research — session-start structural context-load gate (D8)

**Status:** research artefact for the D8 research cycle. Authored
2026-04-24. Answers the question set in
`docs/rebuild/plans/research/session-start-context-load-gate-research-plan.md`.
Promoted from `FUTURE_IDEAS.md` Idea 8. Sibling cycle to D7
(memory-consumer-wiring).

**Working directory of record:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Session-start corpus loaded:** `docs/odd-methodology.md`,
`docs/odd-in-pos.md`, `docs/rebuild/VALUE_PROPOSITION.md`,
`docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md` (Idea 8 verbatim),
D8 research plan, `POST_FIRST_RUN_REVIEW.md` entry #5,
`orchestrator/scripts/pos_session_start.py`, the
`primary-persona-loader/` component directory (proposal +
`component.md` + `primary-persona/src/monitor.py`), Claude Code public
hook docs at
[code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)
and skills docs at
[code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).

**Owner rulings already baked in.** §2.1 layer → primary-persona
layer for now; §2.3 D7-composition → shared `additionalContext`-emitter
layer (shape is open). Research does not re-litigate either; any
evidence that argues for revisiting is flagged under §9.

---

## 1. Executive summary (≤ 15 lines)

1. **Gate location (ruled):** primary-persona layer. No evidence
   emerged to revisit. Bootstrap/harness layer is structurally weaker
   (see §4.1) — `SessionStart` cannot block.
2. **Scope:** component-scoped, composed from a workspace-wide baseline
   corpus + a per-component declaration each proposal already carries.
   Pure workspace-wide over-loads; pure component-scoped cannot
   self-bootstrap.
3. **Payload composition:** session-level baseline (corpus + service
   state + in-flight amendments + cost-headroom) emitted at
   `SessionStart`; turn-level component overlay + memory retrieval
   (D7) at `UserPromptSubmit` via a shared payload-composer the
   persona owns. Both trigger surfaces funnel through one composer.
4. **Refusal semantics:** `UserPromptSubmit` hook-layer `decision:
   "block"` with a structured `reason` is the structural refusal;
   `SessionStart` cannot block (Claude Code limitation), so session-level
   failures emit a loud diagnostic `additionalContext` and mark a
   persona-layer sentinel that the `UserPromptSubmit` gate consults.
5. **Composition with D7:** shared layer has one entry point per
   trigger (`on_session_start`, `on_user_prompt_submit`), both
   delegating to a `ComposedContextPayload` builder whose inputs are
   declarative — no merge-vs-adjacent argument survives. D7 and D8
   can proceed as two proposals landing against the same persona-layer
   contract.
6. **Cold-start cost:** measured at 2 ms p50 / 7 ms p95 for the full
   D8 payload on warm cache (corpus + probes + amendment glob), 104 ms
   including first-run memory HTTP probe timing. Well inside the
   current 20 s supervisor budget. No halt.
7. **Top 3 owner decisions (§8):** (D-1) component-set source for
   relevance resolution; (D-2) refusal shape — loud-diagnostic vs
   `UserPromptSubmit`-hard-block for the missing-corpus case; (D-3)
   whether the shared-layer proposal lands as one amendment to
   primary-persona or as two sibling amendments (D7 and D8).

---

## 2. Layer location — primary-persona (ruled), evidence re-examined

### 2.1 Why persona-layer is structurally viable

- Persona is already the session-scoped entity that owns
  `UserPromptSubmit` injection (`primary-persona/src/monitor.py` injects
  the awareness block every turn). A context-load gate at the same
  surface composes with an existing primitive rather than creating
  a new one.
- The plan's §2.1 open question "is this a skill, a hook, or a persona
  primitive?" resolves as *hook-backed persona primitive*: the hook
  script is the mechanical surface Claude Code exposes, but the
  authoritative logic lives in the persona component and the hook
  delegates to it.

### 2.2 Counter-pressures that could argue for revisiting

Flagged but not advising re-ruling:

- **`SessionStart` cannot block** (Claude Code hook contract —
  "SessionStart cannot block the session start. Exit code 2 produces a
  non-blocking error and session continues. Use `continue: false` to
  stop Claude entirely"). Blocking refusals only land via
  `UserPromptSubmit`. If the owner treats "must block session entry"
  as a hard requirement, the persona-layer surface is strictly weaker
  than nothing for that purpose — but so is the harness/bootstrap
  layer, because both share the same Claude-Code-side limitation.
  Neither layer can hard-block the session.
- **First-run/supervisor already owns `SessionStart`** per
  `.claude/settings.json`. Placing another stanza would layer
  correctly (multiple hooks allowed on one event), but the cleaner
  shape is to fold D8's emission into the existing supervisor path
  or wrap it — both sit at the harness layer by construction. This is
  the closest the research came to evidence for revisiting the
  layer ruling.

**Judgement:** the ruling holds. The persona layer is the right home
for *what to emit and why*; the hook script at the harness layer is
the *carrier*. Cleanest composition is the persona-owned composer
invoked by an updated supervisor stanza (see §6).

---

## 3. Gate scope — workspace-wide vs component-scoped (§2.1)

### 3.1 The two degenerate shapes

- **Pure workspace-wide:** one corpus, one gate, every turn. Fails
  plan-scale — the corpus is already 40 k tokens at today's size
  (measured in §7.1). Injecting the entire thing every session blows
  past the 10 k-character `additionalContext` cap (Claude Code hooks
  spec: "additionalContext is capped at 10,000 characters. Output
  exceeding this is saved to a file and replaced with a preview +
  file path"). Functional but degraded — Claude ends up with a file
  path, not the content — the gate's intent is defeated.
- **Pure component-scoped:** each component declares its own context
  set; gate consults per-component declarations. Fails bootstrap — a
  new-session turn without a named component has no declaration to
  consult, so the baseline (ODD methodology, VALUE_PROPOSITION, STATE,
  FUTURE_IDEAS — the "session-start discipline" list) has nowhere
  to live.

### 3.2 The composition that works

Two-level declaration:

1. **Baseline set** (workspace-wide, always emits): the session-start
   corpus — `odd-methodology.md`, `odd-in-pos.md`, VALUE_PROPOSITION,
   STATE, FUTURE_IDEAS, `CLAUDE.md`, any in-flight
   `amendment-*.md`. This is the "before acting on any non-trivial
   pos-v2 work" list from `CLAUDE.md`.
2. **Component overlay** (turn-scoped, resolved when the turn names
   a component): the component's proposal + research + seal
   narrative, plus any `amendment-*.md` amending it. Turn-scoping is
   what keeps the payload inside the 10 k-char cap — the baseline
   stays session-level (injected once at `SessionStart`) and the
   overlay is a per-`UserPromptSubmit` contribution sized to what
   the turn actually referenced.

The baseline is injected as paths-plus-summary, not as full content
(§7 explains why). The overlay is injected as full content (small
enough to fit) when a turn names a component; it is absent when the
turn doesn't, which is correct for informational turns per the
`CLAUDE.md` carve-out.

### 3.3 Computing "relevant design docs" without the user enumerating

Three candidate sources surveyed; the research ranks them:

- **A — Static mapping in persona config.** A
  `{component → doc_set}` YAML inside the persona contract. Cheapest;
  stale fastest. **Rank:** fallback only.
- **B — Dynamic lookup against the component's proposal/seal sidecar.**
  `docs/rebuild/components/<name>/` is the canonical directory; every
  sealed component has `proposal.md`, `research.md`, `component.md`,
  usually a seal-narrative sidecar. Lookup = list that directory +
  filter for `.md`. **Rank:** first-choice. Self-maintaining — new
  components land with the doc set; no persona-side update needed.
- **C — Compose with the future Claude-capabilities map (Idea 1 Step
  1).** The capabilities map is not built yet; composing on an
  unbuilt primitive is premature. **Rank:** later (not in D8's
  proposal scope).

Research recommends **B**; owner ruling in §8 as D-1.

---

## 4. Hook vs skill vs persona primitive — the three variants (§2.1)

All three live inside the persona-layer ruling. Which shape the
mechanics take is open.

### 4.1 Hook-backed (Claude Code `SessionStart` + `UserPromptSubmit`)

- **Mechanics:** two hook stanzas in `.claude/settings.json`; scripts
  call into the persona-layer composer; stdout/JSON is
  `additionalContext`.
- **Synchronous, blocking-ish:** `UserPromptSubmit` supports `exit 2`
  with stderr (blocking-error) or `decision: "block"` with
  structured `reason` (structured refusal). `SessionStart` supports
  only `continue: false` (stop Claude) — no structured block.
- **Timeout:** 600 s default for command hooks; configurable. The
  existing supervisor stanza uses 60 s; D8's emission can reuse that
  budget safely (§7 measures).
- **Pros:** structural — refusal lives in the Claude Code contract,
  not in persona memory. Aligns with ODD §5.1 preference for
  structural over advisory.
- **Cons:** one stanza per event per settings file; ordering across
  multiple stanzas is not explicitly documented, so composing with
  the existing first-run/supervisor stanza needs a clear sequencing
  rule.

### 4.2 Skill-based (`disable-model-invocation: false`)

- **Mechanics:** a `.claude/skills/session-start-context-load/` skill
  with a `SKILL.md` describing the corpus; Claude auto-loads when
  relevant.
- **Not structural:** skill invocation is Claude's judgement, not a
  deterministic gate. Violates ODD §5.3 ("structural where possible,
  advisory only where structure cannot reach") — the load-before-acting
  guarantee is exactly the kind of thing structure can reach.
- **Skill `hooks` frontmatter** does support scoped hook registrations,
  but the trigger surface for *session start* goes through the same
  `SessionStart` hook event in the end.

Skill-based is not the right shape for the gate itself. It is the
right shape for the *authored guidance* about how to interpret the
loaded corpus (a companion skill could wrap "now that corpus is
loaded, here's how to use it"), but that's a later concern.

### 4.3 Persona primitive (authoritative; hook is the carrier)

- **Mechanics:** persona contract grows an
  `additional_context_emitters` field; persona exports a
  `compose_session_start_context(workspace_root)` and
  `compose_user_prompt_context(prompt, known_component)` pair. Hook
  scripts are ~10 lines — import the persona, call the function,
  print JSON.
- **Pros:** persona owns what gets emitted; hook is mechanism, not
  policy. Preserves the persona-layer ruling. Hot-swappable per
  workspace (workspace supplies the persona; persona declares its
  emitters).
- **Cons:** persona contract needs a small amendment to grow the
  emitters field (low cost — primary-persona-loader already has the
  amendment machinery, and this is a field addition not a semantic
  change).

**Research recommends 4.3 + 4.1 combined:** persona primitive is
the authoritative layer; two hook stanzas are the carriers. This is
the shape D8's proposal should propose.

---

## 5. Concrete payload composition (§2.2)

Ruling on each candidate field from the plan's §2.2 list. Budget
driver is the 10 k-char `additionalContext` cap; D8's goal is to
stay well inside it after D7's overlay is added.

| Candidate | Include in baseline? | Include in overlay? | Reasoning |
|-----------|---------------------|--------------------|-----------|
| Session-start corpus (paths + one-line summary) | **Yes** (paths only) | — | Paths fit the cap; the persona can re-read on demand if a turn needs the full content. The gate's guarantee is "the persona has the paths loaded and knows to read them"; injecting full content every session defeats Claude's context economy. |
| Session-start corpus full content | **No** — paths only | — | 40 k tokens measured; exceeds cap. Re-reading on demand is fine because Claude Code read latency is sub-ms on warm fs (§7). |
| Recent first-run completion time + generation number | **Yes** | — | One int + one timestamp; negligible cost. POST_FIRST_RUN_REVIEW entry #5 flagged this. |
| Warnings from most-recent first-run cycle | **Yes** — only if present | — | Surfacing "phase-4b returned 200 but service was crashlooping" when it recurs. Empty when clean. |
| Per-service state (memory, orchestrator) | **Yes** | — | Already measured by the existing supervisor; D8 extends emission, not measurement. |
| Background-task count | **Yes** (one line) | — | Scope-of-work exposes `list(filter)` per STATE.md rule #7 wiring. A count line is cheap. |
| Cost-governance MTD spend + ceiling headroom | **Yes** (one line) | — | Persona cannot sensibly plan under a 95%-headroom condition without knowing. |
| In-flight amendment list | **Yes** | — | `amendment-*.md` with an in-progress marker; glob-and-filter is measured at 0.4 ms (§7). |
| Corpus-load status sentinel | **Yes** | — | The D8-core payload: a struct that says "corpus paths listed, baseline complete, missing=[]". UserPromptSubmit reads this sentinel and refuses-or-proceeds. |
| Memory-retrieval results (D7's concern) | — | **Yes** | D7's composition point. D8 pre-warms the session; D7 adds per-turn retrieval. |
| Turn-referenced component overlay | — | **Yes** | §3.2 explains. |

### 5.1 Structural shape of the emitted object

Two JSON objects, one per trigger:

- `SessionStart`: `hookSpecificOutput.additionalContext` = a
  structured-text block: `session_id`, `corpus_paths`, `corpus_cap`,
  `first_run_completion`, `service_state`, `background_task_count`,
  `cost_headroom`, `amendments_in_flight`, `corpus_gate_state`
  (`loaded | partial | missing`). Plain text serialisation because the
  hook contract is text-shaped (plan §2.6 flagged this; confirmed
  against the hook docs).
- `UserPromptSubmit`: `hookSpecificOutput.additionalContext` = per-turn
  overlay text: `referenced_components`, `component_overlay_paths`,
  `memory_retrieval_block` (D7's contribution), and — critically —
  `gate_refusal` (empty on pass, populated on refuse). When
  populated, the payload also sets `decision: "block"` with
  `reason = gate_refusal.reason` (structured refusal per §6.2).

### 5.2 Ruled-out fields

None in the plan's §2.2 list were ruled out. The carve-out is
on the *granularity*: corpus paths (yes) vs corpus content (no) for
the baseline.

---

## 6. Shape of the shared D7/D8 `additionalContext`-emitter layer (§2.3)

### 6.1 One composer, two entry points

```
persona.context.ComposedContextPayload
├── on_session_start(workspace_root) → SessionPayload
│     emits: baseline corpus refs, service state, amendments, cost,
│     sentinel
└── on_user_prompt_submit(prompt, resolved_component, memory_client)
          → TurnPayload
     emits: overlay (§3.2), memory retrieval (D7's write), refusal
```

Both entry points return a Pydantic-validated payload; the hook
script serialises the payload to `additionalContext`. The validator
enforces the 10 k-char cap at construction — invalid payloads cannot
reach the hook script's stdout.

### 6.2 D7-write vs D8-write contract

- **D8 writes** `SessionPayload` once per session. It lives as a
  persona-layer attribute for the session's lifetime.
- **D7 writes** `TurnPayload.memory_retrieval_block` per turn. It
  reads the `SessionPayload.corpus_gate_state` sentinel to know whether
  the baseline was loaded; if `missing`, D7's retrieval is skipped
  (no point searching memory for scopes tied to components whose
  context is not loaded) and the refusal path fires instead.
- **Ordering:** session-level payload is composed once (at
  `SessionStart`); per-turn payload is composed lazily each
  `UserPromptSubmit`. No shared buffering beyond the persona-layer
  attribute — the 104 ms session-start cost (§7.2) is paid once, not
  per turn.

### 6.3 Does a heavy baseline warm a D7 buffer?

Plan §2.3 asks whether D8's baseline can warm D7's per-turn work. The
answer is **yes, partially**: the baseline's `corpus_paths` makes it
deterministic which paths D7's memory retrieval should avoid
re-searching for (the session-start corpus is not memory content).
But the large win — caching memory-retrieval results — is D7's own
concern and not a D8 contribution.

### 6.4 Convergence implication

The plan's halt trigger #4 (convergence requires one unified cycle)
is **not hit**. Research shows D7 and D8 can share the composer
layer as two sibling proposals against primary-persona, each
amending it independently. The shared-layer shape is declarative
enough that neither proposal blocks the other.

Two amendments landing in sequence is the cleaner fit to the
amendment-chain discipline than one large amendment trying to do
both. Owner decision D-3 confirms or overturns this (§8).

---

## 7. Cold-start cost (§2.5) — empirical

### 7.1 Method

Measured against the live `/Users/lukeivers/ivers-corp-pos-v2/` tree.
Probe imitates D8's planned work: (a) read all six session-start
corpus paths; (b) probe memory sidecar at `http://127.0.0.1:8765/health`
(2 s timeout); (c) probe orchestrator unix socket at
`~/.pos/orchestrator.sock`; (d) glob `docs/rebuild/plans/amendment-*.md`
for in-flight-amendment inventory; (e) serialise a JSON payload. The
probe reused an already-running Python interpreter because the live
supervisor stanza will likely reuse the first-run helper's Python
process, not cold-spawn.

### 7.2 Results

Corpus read (warm fs, 6 paths, 161 kB total, 40 k-token estimate
at 4 chars/token):
- p50 over 5 runs: **2.0 ms**
- p95 over 5 runs: **7.2 ms**

Full D8 hook simulation (corpus + two probes + glob + serialise):
- one-shot: **104 ms** with services up; **~1.5 s** worst case when
  the memory HTTP probe has to time out at the 1.5 s budget.

Python interpreter cold-start (`python3 -c pass`): ~19 ms. If the
hook spawns a fresh Python process, add ~19 ms to the above; still
well inside the 20 s supervisor budget and comfortably inside the
60 s hook timeout on the existing stanza.

### 7.3 Budget adherence

- **20 s supervisor budget** (from the existing stanza comment):
  **passed** — worst case ~1.5 s is 7.5% of budget.
- **60 s hook timeout** (the stanza's `timeout: 60`): **passed**.
- **10 k-char `additionalContext` cap**: with paths-only baseline, a
  worst-case payload is ~1.5 k chars (paths + one-line summaries + service
  state + amendments + cost headroom + sentinel). **Passed** with
  85% headroom for D7's per-turn overlay.

### 7.4 No halt-trigger-3 condition

Plan halt trigger #3 (cold-start latency budget cannot be met) is
**not hit**.

---

## 8. Refusal semantics (§2.4)

Three candidate shapes were proposed. Research evaluates:

### 8.1 Hard-fail the hook (no session until fixed)

`SessionStart` cannot hard-block (§2.2). The only way to stop the
session at `SessionStart` is `continue: false`, which stops Claude
entirely and provides no UX for "fix the gate and retry." Too strong
for the failure modes this gate catches (missing corpus file while
the rest of the system is fine).

### 8.2 Inject a diagnostic `additionalContext` and proceed

Applicable at `SessionStart` — emit a warning-shaped additionalContext
string naming the missing paths, and let the session proceed. Matches
the existing supervisor behaviour for `partial` state (the script
already prints a named diagnostic on partial bring-up). Persona-layer
sentinel stores the fact of the failure.

### 8.3 Pre-emptive Claude-Code-side error

Not a real shape — the user's Claude Code install has no hook that
refuses outside a stanza Claude Code itself owns. Not investigated
further.

### 8.4 Composite: session-level soft-fail + turn-level hard-block

**Recommendation:** pair 8.2 at `SessionStart` with a `UserPromptSubmit`
hard-block (`decision: "block"`, structured `reason`) on the first
turn that tries to act on pos-v2-dev work while the sentinel says
`missing`. This gives ODD's structural-refusal at the first
mechanically-available surface (the `UserPromptSubmit` is where
blocking is supported by the Claude Code contract), while preserving
the session's ability to run informational turns that do not trigger
the gate.

**Sentinel behaviour:**
- `SessionStart` sets `corpus_gate_state` to `loaded`, `partial`, or
  `missing`.
- `UserPromptSubmit` reads the sentinel + classifies the prompt:
  - pos-v2-dev work (per plan §2.1 "build-dispatches only, or every
    pos-v2 work turn…"): `missing` → block with structured reason
    naming missing paths; `partial` → warn via `systemMessage` but
    allow; `loaded` → pass.
  - Informational/conversational turns: always pass (matches
    `CLAUDE.md`'s "Purely conversational / informational turns do not
    require the read" carve-out).

### 8.5 ODD compliance

This shape is structural in the ODD §5.3 sense at the
`UserPromptSubmit` surface (Pydantic-validated
`ComposedContextPayload.gate_refusal` + hook emits structured
decision). It is advisory at the `SessionStart` surface by necessity
(Claude Code doesn't support structural there). The plan's §2.4 is
satisfied: "The ODD-preferred shape is structural refusal — the
question is which shape that is here" — the answer is "the
`UserPromptSubmit` hard-block path is structural; `SessionStart` has
no structural surface to use."

### 8.6 No ODD-break-required halt

Plan halt trigger #5 (ODD break strongly required) is **not hit**.
The advisory fallback at `SessionStart` is not an ODD break because
Claude Code structurally cannot support it — ODD §5.4 explicitly
sanctions advisory fallback when structure cannot reach.

---

## 9. Flagged inferences (§2.6 + new surfaces)

Flagged for owner challenge per ODD authoring §7.4:

1. **Default assumption: the gate runs synchronously in `SessionStart`
   `async: false`.** Confirmed matches the existing supervisor stanza
   and the Claude Code hook contract for blocking-ish UserPromptSubmit.
   **Hold.**
2. **Default assumption: Claude Code hook infrastructure stays
   backwards-compatible through pos-v2's rollout.** Reasonable — the
   plan flagged; research did not find any announced deprecation on
   `SessionStart`/`UserPromptSubmit`/`additionalContext`. **Hold.**
3. **Default assumption: session-start-corpus injection is text, not
   structured data.** Confirmed by the hook docs — `additionalContext`
   is a string. JSON-inside-a-string is permitted but the container
   is text. **Hold.**
4. **New inference: component overlay resolution uses directory
   listing (§3.3 variant B).** Empirically cheapest and self-maintaining
   against future components, but the overlay can miss components that
   don't follow the `docs/rebuild/components/<name>/` convention.
   **Challenge-if-wrong:** Phase 4+ plugin components may not land in
   that directory tree at all.
5. **New inference: the workspace-wide baseline is the same six paths
   `CLAUDE.md` names.** Confirmed against the current `CLAUDE.md`
   session-start-discipline section. If that list grows, the
   baseline grows automatically — as long as the D8 loader reads it
   dynamically, which the proposal should make a hard acceptance.
6. **New inference: persona-layer sentinel is stored as a
   session-scoped attribute on the loaded persona object.** The
   primary-persona-layer is session-alive; no additional persistence
   needed. Cross-session checks fire fresh at each `SessionStart`.
   **Hold.**
7. **New inference: the existing supervisor stanza composes with D8's
   emission by wrap-and-extend rather than stanza-multiplication.**
   One `SessionStart` stanza invokes a wrapper that runs both the
   existing supervisor probes and the D8 persona-composer call; one
   stdout emission. Rationale: the wrap preserves the first-run
   self-retire semantics (CDC: setup scripts self-retire on success)
   because the supervisor stanza is the one that survives first-run.
   D8 does not self-retire. **Hold.**

---

## 10. Mapping back to the three lenses (harness CLAUDE.md design review)

Not required by the plan's acceptance, but noted for the proposal
author.

- **Lens 1 (Claude-leverage):** the gate composes on Claude Code's
  `SessionStart` + `UserPromptSubmit` hooks + `additionalContext`
  field. All three are existing Claude primitives. The hook-backed
  persona primitive shape (4.3 + 4.1) *extends* the Claude-native
  hook path with pos-v2 policy — the canonical Lens 1 answer shape.
- **Lens 2 (harness + persona value):** reduces the translation
  burden (primary-persona test) — the user never has to remember to
  tell the persona "load the methodology first" because the gate
  does it. Adds to the persona's toolkit (harness test) — the persona
  gains a `ComposedContextPayload` primitive it can re-use for any
  future "inject session-level baseline" work (e.g., cost-governance
  could emit MTD spend via the same surface; a future amendment
  could add an in-flight-scopes baseline without new hook plumbing).
- **Lens 3 (ODD authoring):** acceptance criteria in the proposal
  must be outcome-shaped. Examples for the proposal author:
  - *Outcome:* "A `UserPromptSubmit` turn that matches pos-v2-dev
    work classification and finds `corpus_gate_state == missing` is
    refused structurally." (test-shaped — bad sentinel + matching
    prompt → `decision: "block"` + structured reason.)
  - *Outcome:* "Cold-start cost p95 of `on_session_start` ≤ 500 ms
    on warm fs." (timing-inclusive per ODD §3.4.)
  - *Outcome:* "`ComposedContextPayload` raises at construction when
    the serialised `additionalContext` would exceed 10,000
    characters." (structural refusal per §5.3.)
  - *Outcome:* "Every `amendment-*.md` marked in-progress at
    `SessionStart` appears in the session-level payload within 50
    ms of hook start." (timing + count.)
  - *Outcome:* "A component in
    `docs/rebuild/components/<name>/` gains a new proposal artefact;
    the next `UserPromptSubmit` that references it by name
    automatically includes the new artefact in the overlay." (B18-style
    — the extension act is the test.)

---

## 11. Halt-trigger audit

Per plan §4:

1. **Claude Code capability gap.** Partial: `SessionStart` cannot
   hard-block. Does not require halt because the gate's refusal
   surface moves cleanly to `UserPromptSubmit`, which does support
   structural block. Flagged for owner awareness (§8).
2. **Gate must live inside an unsealed component.** Not hit —
   primary-persona-layer is sealed and the persona contract is the
   amendment surface.
3. **Cold-start latency cannot be met.** Not hit — measured (§7).
4. **D7 convergence requires unified cycle.** Not hit — §6.4.
5. **ODD break strongly required.** Not hit — §8.6.

No halt.

---

## 12. Top 3 owner decisions for the proposal

Restated from the exec summary; these are the decisions the proposal
author needs an answer on before drafting AC prose.

- **D-1. Component-set resolution source.** Research recommends
  directory-listing of `docs/rebuild/components/<name>/` (§3.3
  variant B). Static-mapping (variant A) is the fallback; the
  capabilities-map composition (variant C) is deferred.
  - *Owner ruling required if:* there's intent to move component
    artefacts out of `docs/rebuild/components/`, or to house
    plugins outside that tree.
- **D-2. Refusal shape for the missing-corpus case.** Research
  recommends the composite shape (§8.4) — `SessionStart` soft-fail
  + `UserPromptSubmit` structural block gated by prompt
  classification + persona-layer sentinel.
  - *Owner ruling required if:* a stricter shape (block the session
    entirely via `continue: false` on `SessionStart`) or a looser
    shape (always proceed, warn-only) is preferred.
  - *Subsidiary:* the classification rule "pos-v2-dev work vs
    informational turn" is the load-bearing boundary. Research
    recommends the existing `CLAUDE.md` carve-out verbatim as the
    classifier: any turn that mentions editing, dispatching, or
    proposing pos-v2-dev work triggers the hard path;
    conversational/informational turns pass. If this classifier
    is wrong, the gate either over-refuses or under-refuses — a
    second-order owner decision worth naming in the proposal.
- **D-3. Proposal-count — one amendment or two (D7 + D8 siblings).**
  Research recommends two sibling proposals against primary-persona.
  D7 proposes the memory-retrieval turn-payload contribution; D8
  proposes the session-payload composer + the two hook stanzas.
  Both land against the same composer contract.
  - *Owner ruling required if:* the owner prefers one unified
    amendment (reduces amendment count, increases amendment size;
    trade-off is the amendment-chain reseal convention, Idea 11).

---

## 13. Pointers to cited artefacts

- Session-start corpus: `docs/odd-methodology.md`;
  `docs/odd-in-pos.md`;
  `docs/rebuild/VALUE_PROPOSITION.md`;
  `docs/rebuild/STATE.md`;
  `docs/rebuild/FUTURE_IDEAS.md` (Idea 8 verbatim at §Idea 8).
- Supervisor stanza: `orchestrator/scripts/pos_session_start.py`
  (lines 167–248 — main `run_session_start` control flow).
- Persona-layer surface: `primary-persona/src/monitor.py` (the
  `UserPromptSubmit` awareness-block injection already composing with
  `additionalContext`); `primary-persona/src/loader.py` (contract
  load);
  `docs/rebuild/components/primary-persona-loader/proposal.md` (D3
  and D4 are the existing composition points).
- Post-first-run review: `docs/rebuild/POST_FIRST_RUN_REVIEW.md`
  entry #5 (supervisor minimality).
- Hook/skill docs: Claude Code public documentation at
  `https://code.claude.com/docs/en/hooks` and
  `https://code.claude.com/docs/en/skills` (fetched 2026-04-24;
  content used for §4 capability survey and §2.2 blocking semantics).
- D7 research plan: `docs/rebuild/plans/research/memory-consumer-wiring-research-plan.md`
  (shared-layer composition §2.5 cross-reference).

---

## 14. What the proposal author should author next

Scope-only (not in this research's remit, named for continuity):

- One proposal (or two — per D-3) against primary-persona
  that adds:
  - `ComposedContextPayload` Pydantic model with a `model_validator`
    that enforces the 10 k-char cap structurally.
  - `on_session_start` and `on_user_prompt_submit` composer methods.
  - Two hook stanzas in `.claude/settings.json`
    (`SessionStart` wrapper + `UserPromptSubmit`).
  - Acceptance criteria in the outcome-shape §10 anticipates (timing,
    refusal structurality, auto-discovery of new components, cap
    enforcement).

This research step completes here.

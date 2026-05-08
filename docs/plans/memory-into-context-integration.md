# Memory into context — integration plan

**Status:** authored 2026-04-25 in interactive session.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch.
**Authored against HEAD:** `19108ea`.
**Driver:** Luke's 2026-04-25 question "is the memory system working properly? are we storing things into it? is it getting loaded into context?" — answer was: service healthy, no real data, **not loaded into context**. Substrate is built (amendments #32 D8 gate, #33 D7 memory consumer, #34 eager lifespan, #35–#37 persona scaffold + agent file, #40 tracker contributor, #41 sub-plan A, #45 multi-contributor SessionStart). The runtime caller that actually invokes the composer at SessionStart was never written.

---

## 1. Summary / TLDR

Two small sealed-component amendments close the gap between the built memory + composer substrate and a live SessionStart that actually emits memory + tracker + corpus state into Claude Code's `additionalContext`.

1. **Amendment #46 — primary-persona SessionStart emitter.** A `primary_persona.session_start_emitter` module + `python -m primary_persona.cli session-start` CLI invokes `compose_session_fields(workspace_root)` + `ComposedContextPayload.on_session_start(...)` and prints the rendered additionalContext to stdout. `hands-off-lifecycle`'s `first_run_settings.merge_session_start` registers the new inner hook via the `extra_inner_hooks` registry generalised in #45. After #46 lands, every fresh Claude Code session sees the persona's structured `additionalContext` (memory retrieval, tracker context, corpus refs, service state, in-flight amendments, cost headroom, corpus-gate sentinel, first-run completion timestamp).

2. **Amendment #47 — workspace-local `.mcp.json` writer.** First-run scaffold writes `<workspace>/.mcp.json` registering the per-workspace `memory-graphiti` service (port from amendment #29 allocation) under the `streamable-http` transport. After #47 lands, Claude Code can call the memory-system's MCP tools (`add_episode`, `search`, etc.) during turns — turn-time semantic memory retrieval, not just session-start composed payload.

Persona-content authoring (the `personas/primary/contract.yaml` + `prompt.md` are still EXAMPLE template scaffolds) is **explicitly out of scope** for #46/#47 — surfaced as a follow-up question in §7.

The two amendments are independent (different sealed components, different surfaces) and can land in either order. #46 is recommended first because it's the load-bearing piece for "memory loaded into context"; #47 is additive for turn-time tool availability.

Per "scope-only-dispatch" CDC, the per-amendment ACs in §4a + §4b carry outcome only — files, symbols, layout, validator names belong in each amendment's builder plan, not here.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this plan satisfies:**

- **v1.0 line 153** — *"every interactive session (terminal or desktop) starts with the primary persona present by default — asserted by a session-start test."* Amendment #37 wires the persona's identity-anchor agent file into Claude Code's default-agent surface; **#46 is what makes the persona's SESSION-LEVEL CONTEXT (memory, tracker, corpus refs) actually present in every session.** Without #46, the agent file binds the session to the persona's identity but the persona's contributors are dead code.
- **v1.0 Architectural — "Persistent + retrievable memory"** (objectives spec §1 / VALUE_PROPOSITION §"Unpacking the toolkit", item 1: *"Today's response is informed by yesterday's decisions."*). #46 + #47 together make memory persistent AND retrievable: #46 surfaces eager retrieval at session-start; #47 surfaces lazy retrieval (MCP tools) at turn-time.
- **v1.2 R16 — Framework-not-content.** Both amendments are framework wiring; no persona content, no memory content, no policy. Workspace owns content.
- **D8 gate (amendment #32) + D7 memory consumer (amendment #33).** The composer + contributors exist in `primary-persona/src/`; #46 is the runtime call site they were built for.
- **#45's `extra_inner_hooks` registry.** #45 generalised `merge_session_start` to compose multiple SessionStart contributors; #46 is the second concrete consumer of that registry (loam-mode was the first).

**Sealed-component amendment classification.**

- **#46:** two sealed components — `primary-persona` (new module + CLI subcommand + tests) + `hands-off-lifecycle` (registration via existing `extra_inner_hooks` surface + tests). Scope is additive for both.
- **#47:** one sealed component — `workspace-bootstrap` (new scaffold step writing `<workspace>/.mcp.json` + tests). Reuses the deep-merge / no-clobber pattern established by #36's persona scaffold + #37's settings.json merge.

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in both amendments must trace back to a named AC under §4a or §4b. No silent branches; no defensive `if`s without backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

- **#46:** the `SessionStart` hook's stdout-as-additionalContext convention (Claude-native). The composer (#32) was built against `additionalContext`'s 10,000-char cap. #46 is the runtime that actually delivers payload through that cap. Composes with #45's multi-contributor registry: the persona's payload is one inner hook; loam-mode's mode-aware fragment selection is another; `pos_session_start.py`'s probe is a third. All three fan-out into the session via Claude Code's hook list shape — no bespoke composition.
- **#47:** the `.mcp.json` MCP-server registration surface (Claude-native). Claude Code reads `.mcp.json` at session-load to discover MCP servers; the memory-system's existing FastMCP/streamable-HTTP service exposes tools (`add_episode`, `search`, `find_nodes`, etc.) that become callable from the session as `mcp__<server>__<tool>`. No new server, no new transport — the service has been running for weeks; #47 is the registration that makes it visible.

Both amendments are textbook Lens 1: existing Claude primitives, composed.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden?*

- **#46:** YES — load-bearing. Before #46, the persona's tracker context, memory retrieval, corpus gate, and service-state contributors are coded but never reach the session. Luke asks "what's the workspace working on?" — without #46, the persona answers from the user's previous chat or guesses; with #46, the persona reads the structured payload (in-flight amendments, tracker state, recent memory) and answers directly. **AC46.1–AC46.5 → AC.PO.1.**
- **#47:** YES — turn-time. Before #47, semantic memory queries during a turn require shelling out via Bash (e.g. `curl http://127.0.0.1:8765/...`) — translation work the user shouldn't have to do. After #47, the persona calls `mcp__memory-graphiti__search` natively as a tool. **AC47.1–AC47.3 → AC.PO.1.**

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

- **#46:** the persona-side SessionStart emitter is a toolkit primitive every future SessionStart contributor (light-touch education, plugin hooks, scope-of-work overlay) composes against via the same `extra_inner_hooks` pattern. **→ AC.PO.2.**
- **#47:** workspace-local MCP-server registration becomes the pattern for every future per-workspace MCP server (future plugins, future integration adapters). **→ AC.PO.2.**

### Lens 3 — ODD authoring

Both amendments author outcome-shaped ACs. Method (file paths, validator shapes, exact merge algorithm) is the builder's call. No method-in-acceptance. Every code path traces forward to AC and reverse to AC (§2.5).

---

## 4. Amendments

### 4a. Amendment #46 — primary-persona session-start + turn-start emitter, contributor wiring, starter-pending body completion

**Sealed components touched:** `primary-persona` (new emitter modules + CLI subcommands + onboarding contributor body widening + tests), `hands-off-lifecycle` (extra-inner-hook registration + new UserPromptSubmit hook + tests).

**Updated 2026-04-25 mid-session** to absorb three findings surfaced during the dispatch-prep verification pass:

> 1. No runtime constructs `ComposedContextPayload` or registers the contributors. The factories (`build_starter_pending_contributor`, `register_tracker_context`, `register_memory_retrieval`) all exist but are never instantiated outside tests. #46 owns the entire wiring path: composer construction, contributor registration, both entry-point invocations.
> 2. Memory retrieval (D7, amendment #33) registers as `TriggerKind.turn`, not `session`. For "memory loaded into context" to actually deliver memory through the composer, #46 must wire a UserPromptSubmit hook in addition to the SessionStart hook. Otherwise #33 remains dead code.
> 3. The starter-pending contributor body (amendment #35's onboarding) emits only a 2-line marker — the question list is held in `ONBOARDING_QUESTIONS` and never reaches `additionalContext`. For the post-launch interview to work without persona-prompt customisation (the persona prompt is still EXAMPLE template content per Q1's "defer" not chosen), the body must carry the question prompts + write-back instructions so any persona reading the additionalContext can conduct the elicitation. AC35.3 measures only the marker prefix; widening the body content is method (no AC conflict).

**Objective.** The primary-persona layer exposes two CLI subcommands — `session-start` and `user-prompt-submit` — that construct a `ComposedContextPayload` instance, register the layer's contributors (tracker-context, starter-pending, memory-retrieval), invoke the appropriate composer entry point, and print the rendered `additionalContext` to stdout. `hands-off-lifecycle`'s first-run scaffold + supervisor stanza register the session-start subcommand as a SessionStart inner hook via #45's `extra_inner_hooks` parameter and add a new UserPromptSubmit hook entry pointing at the turn subcommand. The starter-pending contributor's body is widened to carry the question list + write-back instructions inline so a persona on EXAMPLE template content can still conduct the interview from additionalContext alone. After this amendment lands, every Claude Code session in a pos-v2 workspace receives (a) the persona's session-level payload — corpus refs, in-flight amendments, service state, cost headroom, gate sentinel, tracker context, and starter-pending instructions when applicable — as SessionStart `additionalContext`, and (b) per-turn memory retrieval based on the user's prompt as UserPromptSubmit `additionalContext`.

**Hard constraints.**

1. **Dependency fence.** Source-edit scope is `primary-persona/src/` + `primary-persona/tests/` + `hands-off-lifecycle/hooks/` + `hands-off-lifecycle/tests/`. Any edit elsewhere is a halt trigger.
2. **Reversibility.** Fully reversible. No persona-side surface is retracted; only additive emitters + a contributor body widening (preserving AC35.3's marker prefix).
3. **Budget.** SessionStart hook stays inside the supervisor's existing 20s budget. UserPromptSubmit hook's per-turn p95 is bounded by the gate's session-warmup envelope (~100ms with live services) plus the memory-consumer retrieval budget (#33's measured envelope). The CLI's per-invocation timeout is 5s for SessionStart (matches loam-mode #45 precedent) and 5s for UserPromptSubmit (memory retrieval is bounded by `num_results` cap at 5 + char-cap from `MEMORY_RETRIEVAL_CHAR_CAP`).
4. **Fail-soft.** Both CLI subcommands exit 0 on every path (a non-zero exit blocks Claude Code's hook fan-out). On any error the CLI prints an empty payload or a structured diagnostic line and proceeds.
5. **`additionalContext` cap.** The composer's existing 10,000-char structural refusal (#32 D8.5) is unchanged. The starter-pending body widening must keep the full SessionStart payload inside the cap; the contributor's own portion is bounded to a fraction (recommended: ≤2,000 chars) so other session-level contributors fit alongside.
6. **AC35.3 preservation.** The starter-pending contributor body must continue to begin with `STARTER_PENDING_MARKER` as its first line. Any addition appears after the marker.
7. **No `--amend`.** Corrective commits only.
8. **ODD §2.5.** Every code path, branch, dependency, and test maps to AC46.1–AC46.S.
9. **Backwards-compat.** Workspaces without the persona registered (e.g. a hypothetical first-run-failed state where `personas/<handle>/` is absent) get probe-only output for SessionStart and an empty UserPromptSubmit payload — both unchanged from pre-#46. Existing #32 + #33 + #37 + #45 test suites stay green.

**Acceptance criteria (AC46.x).**

- **AC46.1** — `python -m primary_persona.cli session-start` (or builder's chosen module-name; the surface is `<workspace-venv>/bin/python -m <module> session-start`) in a fully-scaffolded workspace produces a non-empty `additionalContext` string on stdout whose serialised form contains: the corpus_paths list, amendments_in_flight list, service_state fields (memory + orchestrator), cost_headroom, corpus_gate_state sentinel, first-run-completion timestamp + generation marker, the tracker-context contributor's output (when in-flight objectives exist), AND the starter-pending block when `is_starter=True`. Total payload fits within the composer's 10,000-char cap.
- **AC46.2** — `python -m primary_persona.cli user-prompt-submit` (invoked by Claude Code's UserPromptSubmit hook) produces an `additionalContext` string containing the memory-retrieval contributor's output for the user's prompt. The CLI receives the prompt via stdin or env-var per Claude Code's UserPromptSubmit hook contract; method (which channel) is the builder's call to confirm against the hook docs. When the memory service is up and contains episodes, the output includes retrieved episode text; when memory is down or empty, the output is the empty string (graceful, not error).
- **AC46.3** — On a workspace with missing baseline corpus (one or more files in the corpus-gate's expected list absent), the SessionStart CLI produces a structured diagnostic naming the missing paths AND a `corpus_gate_state` sentinel of `partial` or `missing`. Both CLIs exit 0 (graceful refusal, not block).
- **AC46.4** — On a workspace where the composer fails to construct (e.g. persona contract unloadable, an internal error), both CLIs print either an empty payload OR a single diagnostic line naming the failure class, exit 0, and do NOT raise. No traceback reaches stdout.
- **AC46.5** — `hands-off-lifecycle`'s `build_first_run_stanza` and `build_supervisor_stanza` both emit a `.claude/settings.json` envelope whose `hooks.SessionStart` inner-hook list contains the new persona-side session-start inner hook in the position registered by `extra_inner_hooks` (probe → persona session-start → loam-mode emit, deterministic order; exact ordering is the builder's call so long as probe runs before persona emit), AND whose `hooks.UserPromptSubmit` list contains a new inner hook pointing at the persona's user-prompt-submit subcommand. Existing first-run / supervisor probe inner hook is unchanged.
- **AC46.6** — Backwards-compat: when `extra_inner_hooks` is unset or empty, `merge_session_start` produces output byte-identical to the pre-amendment code path's SessionStart envelope. Existing #32 + #33 + #37 + #45 test suites stay green. The new UserPromptSubmit hook entry is single-contributor; if a future contributor lands, generalisation analogous to #45 is a future amendment (not this one).
- **AC46.7** — Starter-pending contributor body widening: when `contract.is_starter=True`, the contributor returns a string whose first line is `STARTER_PENDING_MARKER` (preserves AC35.3) AND whose body includes (a) each `OnboardingQuestion`'s `id` + `prompt` text in a structurally-detectable list, and (b) one or more lines telling whatever-persona-is-loaded how to write the transcript back (specifically: the existence of `persist_elicitation_transcript`, the contract path, and a one-line invocation pattern). When `contract.is_starter=False`, the contributor returns the empty string (unchanged from pre-#46). The widened body fits inside the per-contributor budget from constraint 5 (≤2,000 chars).
- **AC46.8** — End-to-end interview path is exercisable: a test scenario where (i) the contract has `is_starter=True`, (ii) the SessionStart CLI is invoked, (iii) its stdout is parsed for the question list, (iv) a synthetic transcript is constructed with non-empty answers for all required questions, (v) `persist_elicitation_transcript` is called, (vi) the contract's `is_starter` is now False AND the answer fields appear on the contract. (Method: stub the persona "asking and capturing" as a test fixture; the AC measures that the framework path from contributor body → write-back closes.)
- **AC46.9** — ODD §2.5 reverse direction: every code path / branch / dependency / test in the amendment diff traces back to AC46.1–AC46.8. The builder audits both directions before seal.
- **AC46.S** — Seal-diff: changes confined to `primary-persona/src/`, `primary-persona/tests/`, `hands-off-lifecycle/hooks/`, `hands-off-lifecycle/tests/`, and the relevant plan + manifest docs. No surface change to other sealed components. (`hands-off-lifecycle`'s H19 frozen BASELINE per amendment #23 — manifest sets `frozen_baseline: true` for that component.)

**Behaviour-count check (forward).**

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | SessionStart CLI emits structured additionalContext including tracker + starter-pending | AC46.1 |
| 2 | UserPromptSubmit CLI emits memory-retrieval additionalContext | AC46.2 |
| 3 | Missing-corpus graceful diagnostic + sentinel | AC46.3 |
| 4 | Composer-construction-failure graceful refusal (both CLIs) | AC46.4 |
| 5 | Both stanzas register both hooks in deterministic order | AC46.5 |
| 6 | Backwards-compat with zero extra contributors | AC46.6 |
| 7 | Starter-pending body carries questions + write-back instructions | AC46.7 |
| 8 | End-to-end interview path is exercisable | AC46.8 |
| 9 | ODD §2.5 reverse direction | AC46.9 |
| 10 | Seal-diff window respected | AC46.S |

**Halt triggers.** Any of:

- The composer's public API does not expose a callable that returns the rendered `additional_context_text` from a `workspace_root` argument — halt and surface (the composer was built to be called this way per #32's plan §2; if the surface is harder than expected, escalate).
- `extra_inner_hooks` is not actually a list-accepting parameter on `build_first_run_stanza` / `build_supervisor_stanza` — halt and surface (#45 promised the registry; if the implementation differs, escalate to #45's author / re-plan).
- Claude Code's UserPromptSubmit hook contract for receiving the prompt (stdin / env var / argv) cannot be determined from the available docs in <30 minutes of research — halt and surface (block on Luke ruling on the contract; do not guess).
- The persona's contract is unloadable in any test fixture without test-side workarounds — halt and surface.
- The starter-pending body widening cannot fit within the per-contributor budget without dropping question text — halt and surface (re-extend the budget or trim instructions; method but the trade-off needs a ruling).
- Any sealed component outside the dependency fence shows up in the diff — halt and surface (this would be an ODD §2.5 violation — re-extend the plan, do not silently expand scope).

### 4b. Amendment #47 — workspace-local `.mcp.json` writer

**Sealed component touched:** `workspace-bootstrap` (new scaffold step + tests).

**Objective.** The `workspace-bootstrap` first-run scaffold writes `<workspace>/.mcp.json` registering the per-workspace `memory-graphiti` service as an MCP server under the `streamable-http` transport at the workspace's allocated port (per #29 per-workspace port allocation). After this amendment lands, Claude Code sessions discover and bind the memory-system's MCP tools at session-start, making them callable as `mcp__memory-graphiti__<tool>` during turns.

**Hard constraints.**

1. **Dependency fence.** Source-edit scope is `workspace-bootstrap/src/` + `workspace-bootstrap/tests/`. Any edit elsewhere is a halt trigger.
2. **Reversibility.** Fully reversible. The `.mcp.json` write is additive; deleting the file restores pre-#47 state.
3. **No-clobber.** Re-running first-run on a workspace whose `.mcp.json` already contains user-added MCP servers must deep-merge the `memory-graphiti` entry without disturbing the user's entries. (Precedent: #37's settings.json merge.)
4. **Fail-soft.** Write failure (permissions, disk full, malformed pre-existing `.mcp.json`) surfaces a structured diagnostic, first-run completes, the SessionStart hook proceeds. The session degrades to "no memory MCP tools available" rather than failing closed. (Precedent: #37 AC37.4.)
5. **Per-workspace port.** The MCP server URL uses the port allocated by amendment #29 (per-workspace memory-sidecar port), NOT the legacy hardcoded 8765. Method: read from the same source #29 writes to.
6. **No `--amend`.** Corrective commits only.
7. **ODD §2.5.** Every code path / branch / dependency / test maps to AC47.1–AC47.4.

**Acceptance criteria (AC47.x).**

- **AC47.1** — After first-run completes on a fresh-clone workspace, `<workspace>/.mcp.json` exists and contains exactly one entry under `mcpServers` with key `memory-graphiti` (or the workspace-namespaced equivalent — method) whose `transport` is `streamable-http` and whose `url` resolves to the per-workspace port allocated by amendment #29.
- **AC47.2** — Re-running first-run on a workspace whose `.mcp.json` contains pre-existing user-added MCP server entries deep-merges the `memory-graphiti` entry without removing or modifying the user's entries. The user's `mcpServers` entries appear unchanged after the merge.
- **AC47.3** — On a write failure (simulated via permissions / pre-existing-malformed-`.mcp.json` / disk full), first-run completes, surfaces a structured diagnostic via the existing observability surface (matching the failure-class shape #37 AC37.4 established), and the SessionStart hook proceeds. The session degrades; it does not halt.
- **AC47.4** — ODD §2.5 reverse direction: every code path / branch / dependency / test in the diff traces back to AC47.1–AC47.3.
- **AC47.S** — Seal-diff: changes confined to `workspace-bootstrap/src/`, `workspace-bootstrap/tests/`, and the relevant plan + manifest docs.

**Behaviour-count check (forward).**

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | First-run writes workspace-local `.mcp.json` with memory-graphiti entry | AC47.1 |
| 2 | Re-run deep-merges without clobbering user entries | AC47.2 |
| 3 | Write-failure graceful refusal | AC47.3 |
| 4 | ODD §2.5 reverse direction | AC47.4 |
| 5 | Seal-diff window respected | AC47.S |

**Halt triggers.**

- Amendment #29's per-workspace port is not actually exposed to workspace-bootstrap's scaffold layer (port discovery requires a surface that does not exist) — halt and surface.
- Writing `.mcp.json` requires Claude-Code-config-schema knowledge the workspace-bootstrap component does not currently consume — halt and surface (escalate to a research step on schema validation if necessary).
- Any sealed component outside the dependency fence shows up in the diff — halt and surface.

### 4c. Out-of-scope for #46/#47 (named here so it is not silently absorbed)

- **Persona content authoring.** `personas/primary/contract.yaml` is the EXAMPLE scaffold with `given_name: Example` and template responsibilities prose. The agent file (`.claude/agents/primary.md`) re-renders from this contract via #35's `to_agent_md()`. Neither #46 nor #47 modifies the contract. Customising the persona is content-authoring; tracked as a follow-up question in §7.
- **Auto-memory ↔ graphiti unification.** The Claude Code auto-memory (`/Users/lukeivers/.claude/projects/-Users-lukeivers-pos3/memory/`) and the pos-v2 graphiti memory-system are distinct persistence surfaces with different shapes (preferences/feedback vs interaction-history-derived semantic memory). Architecturally complementary (per VALUE_PROPOSITION + Idea 4). No unification is in scope here.
- **Memory seeding.** kuzu_db has only test fixtures (Halcyon scenario world). After #46/#47 land, real memories accumulate organically through use; auto-seeding would violate ODD §2.5 (no objective names "seed initial memories"). Tracked as a follow-up if Luke wants a head start.
- **`extra_inner_hooks` registry surface widening.** If #46 surfaces that #45's registry is per-call (passed at stanza-build time) rather than per-component-registered (declarative), expanding the registry to a declarative shape is outside #46's scope. Re-extend up if needed.

---

## 5. Three-lens AC trace

| AC | Lens 1 (Claude) | Lens 2 (Translation / Toolkit) | Lens 3 (ODD) |
|----|------------------|---------------------------------|--------------|
| AC46.1 | composes onto SessionStart `additionalContext` | reduces translation: persona answers from structured state, not user re-explanation | outcome-shaped, deterministic, test-shaped |
| AC46.2 | leverages `additionalContext` as the diagnostic surface (no separate channel) | translation absorbed at the failure boundary | outcome-shaped, deterministic |
| AC46.3 | leverages stdout as the only emit surface (Claude-native) | failure does not push translation work to the user | outcome-shaped |
| AC46.4 | composes onto #45's registry (Claude-native multi-contributor) | toolkit primitive — every future contributor uses the same surface | outcome-shaped |
| AC46.5 | preserves Claude-native single-contributor emit shape | toolkit backwards-compat | structural |
| AC47.1 | composes onto Claude Code's `.mcp.json` registration (Claude-native) | tools become callable as `mcp__<server>__<tool>` natively | outcome-shaped |
| AC47.2 | composes onto MCP's deep-merge convention | toolkit primitive — every future workspace-local MCP server uses this surface | outcome-shaped |
| AC47.3 | graceful degradation matches #37 AC37.4's pattern | translation absorbed at the failure boundary | outcome-shaped |

---

## 6. Named decisions with recommendations

### D1 — Single combined amendment vs split (#46 + #47)

- **Recommendation: SPLIT.**
- Rationale: different sealed components, independent blast radii, easier review, easier rollback. Per "serialize amendment builds in same tree" memory, two serialised builds are clean; combined would entangle the two surfaces unnecessarily.
- Choice: split, #46 first (load-bearing for "loaded into context"), #47 second (turn-time additive).

### D2 — Where the SessionStart emitter module lives

- **Recommendation: `primary-persona/src/session_start_emitter.py` + a CLI subcommand under `primary_persona.cli`.**
- Rationale: precedent matches `tools/loam-mode/src/loam_mode/session_start.py` + `loam_mode.cli session-start` from #45. The emitter invokes a primary-persona public function (`compose_session_fields`); it lives next to that function. Builder may refine to a different module name; the location (under `primary-persona/`) is constraint, the exact module name is method.

### D3 — MCP transport choice (#47)

- **Recommendation: `streamable-http`.**
- Rationale: the memory-graphiti service exposes MCP via FastMCP/streamable-HTTP (confirmed at `/health` probe). No wrapper needed; the URL points directly at the service. stdio transport would require a stdio-bridge subprocess, adding complexity without benefit.

### D4 — `.mcp.json` location (workspace-local vs user-global)

- **Recommendation: workspace-local (`<workspace>/.mcp.json`).**
- Rationale: per #28 + #29's workspace-locality pattern, and because the memory-graphiti service is per-workspace (workspace-namespaced launchd label, per-workspace port). User-global would conflict across multiple pos-v2 workspaces. Workspace-local also matches Claude Code's own `<workspace>/.claude/` + `~/.claude/` convention.

### D5 — Inner-hook ordering for the persona contributor

- **Recommendation: probe (existing `pos_session_start.py`) → persona emit (new) → loam-mode emit (#45).**
- Rationale: probe surfaces "services up" first so the persona's emit (which queries those services) has a fresh state. Persona emit before loam-mode emit so the persona's structured payload appears before the dev-mode-conditional CLAUDE.md fragment. Method choice; builder may refine.

### D6 — Auto-seeding initial memories

- **Recommendation: NO. Defer.**
- Rationale: ODD §2.5 — no objective names "seed initial memories." Memory grows organically through use. If Luke wants a head start later, that becomes its own scope.

### D7 — Persona content authoring (block #46/#47?)

- **Recommendation: PROCEED with #46/#47 regardless of persona content state.**
- Rationale: the wiring delivers value (memory retrieval, tracker context, corpus refs, service state, in-flight amendments, cost headroom) regardless of persona prompt content. Persona content authoring is its own pass and surfaces separately as a follow-up question (§7 Q1).

---

## 7. Critical questions for Luke (only the ones methodology cannot answer)

### Q1 — Persona content authoring trigger

`personas/primary/contract.yaml` + `prompt.md` are the EXAMPLE template scaffolds (`given_name: Example`, "Describe, in one sentence, what this persona is the sole contact for", etc.). The agent file (`.claude/agents/primary.md`) regenerates from this contract. After #46 lands, the persona's session-level state (memory, tracker, corpus) reaches the session, but the persona's IDENTITY (voice, responsibilities, escalation taxonomy, persona prose) is still the template.

Three options, in order of effort:

- **(a) Defer.** Land #46/#47, work productively against the template-persona surface. Address persona-content authoring as a separate cycle when Luke is ready to write it. **(Recommended — keeps the work-on-memory critical path narrow.)**
- **(b) Hand-edit.** Luke writes the contract.yaml fields (given_name, responsibilities, authority_boundary, escalation_taxonomy) + the prompt.md prose directly. Lands as a content commit, not an amendment.
- **(c) Run onboarding-elicitation.** Amendment #35 / sub-plan A (#41) built the elicitation flow; running it generates contract content from interactive Q&A. **Method-uncertainty:** the elicitation runner needs a surface that exposes it as a callable; whether that surface is fully wired is a research question.

**Surfaced because:** Luke's ruling on persona content shape is content-authoring authority — not a methodology call. Recommendation is (a); Luke may prefer (b) or (c).

### Q2 — Order of operations

Two concrete orderings are reasonable:

- **(α) #46 → #47 → resume.** Land memory-into-context first; MCP tools added second.
- **(β) #46 + #47 in parallel** (different sealed components, no source overlap, per "Serialize amendment builds in the same working tree" they CAN parallel-dev IF worktree-isolated per the amendment-#23 + worktree-research convention).

**Recommendation: (α) serial.** Faster review, smaller blast radius per commit. Parallel offers minimal time savings for two small amendments.

**Surfaced because:** Luke has occasionally chosen parallel for time-pressure builds.

---

## 8. Execution sequencing

Assuming Luke's defaults on Q1 (defer) and Q2 (serial):

1. **Now — finalise plan.** This document. Author per-amendment manifest YAMLs (`amendment-46-...manifest.yaml`, `amendment-47-...manifest.yaml`).
2. **Amendment #46 build dispatch** (background agent, working dir `/Users/lukeivers/ivers-corp-pos-v2/`). Brief carries: objective + scope + AC46.1–AC46.S + halt triggers + ODD-check + the `pos-amend apply --dry-run` then commit then `pos-amend seal --plan-doc <abs-path>` flow.
3. **Verify #46 in pos3** by restarting Claude Code (the workspace's SessionStart should now emit the persona's structured `additionalContext`). Inspect the emitted text for shape; confirm services up, corpus refs visible, tracker context loaded.
4. **Amendment #47 build dispatch** (same working dir). Brief carries the AC47 set + halt triggers.
5. **Verify #47 in pos3** by restarting Claude Code (Claude Code should discover `mcp__memory-graphiti__*` tools at session-start). Confirm `mcp__memory-graphiti__search` is callable.
6. **Append findings** to `FUTURE_IDEAS_DRAFT.md` per the no-overhead capture pattern. Update STATE.md if appropriate.
7. **Surface follow-up Q1 ruling** to Luke (persona content authoring); proceed against the ruling.

Per "amendment-dispatch test & context scope" CDC: each dispatch scopes full test-suite to components actually touched, skips pre-seal full rerun (sidecar-only), inlines methodology snippets in the prompt. Per "scope-only-dispatch": the brief carries scope only — no file enumeration, no symbol names, no AC prose, no commit-message wording.

Per "subagent ODD-violation halt" feedback: each dispatch carries an explicit "halt and surface ODD violations in your work or surrounding code" clause.

---

## 9. Three-lens recap (one-line per amendment)

- **#46:** Lens 1 — composes onto Claude's SessionStart `additionalContext` + #45's registry. Lens 2 — load-bearing for memory + tracker + corpus reaching the session. Lens 3 — outcome-shaped ACs, structural where possible, §2.5 reverse-direction-clean.
- **#47:** Lens 1 — composes onto Claude's `.mcp.json` MCP-server registration. Lens 2 — turn-time tool availability for memory queries. Lens 3 — outcome-shaped ACs, §2.5 reverse-direction-clean.

---

## 10. Out-of-scope (named explicitly per ODD §2.5)

- Persona content authoring (§7 Q1).
- Auto-memory ↔ graphiti unification (§4c).
- Memory seeding (§4c, §6 D6).
- `extra_inner_hooks` registry shape widening (§4c).
- Cross-workspace memory keying (sub-plan G in Idea 13's deferred parts).
- The dispatch-template engine ↔ persona-tracker composition (Idea 17, deferred stretch).

If any of these surface as hard prerequisites during the build, halt-and-surface; do not silently expand scope.

---

## 11. Halt-and-signal triggers (umbrella)

- Any precondition discovered missing (composer's public API gap, #45 registry gap, #29 port-discovery gap, persona contract unloadable).
- Any sealed component outside the per-amendment dependency fence appears in the diff.
- Any AC discovered to be method-prescribing during build (re-extend or tighten the AC, do not silently work around).
- Any §2.5 violation in extending code (the new code's neighbour has `AC:none` — surface and propose the remedy: re-extend up, or refuse to extend until a remedy is scoped).

Halt → surface to main session → ruling → resume against ruling.

---

## 12. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC46.1–.5 → AC.PO.1.** Memory + tracker + corpus reach the session at SessionStart → persona answers from structured state → translation burden absorbed.
- **AC47.1–.3 → AC.PO.1.** Memory tools callable from turns → persona looks up by entity / time / topic without bash shell-out → translation burden absorbed.
- **AC46.4–.5 + AC47.1–.2 → AC.PO.2.** Both add reusable toolkit primitives: `extra_inner_hooks`-via-persona-emitter pattern; workspace-local-MCP-server pattern. Future contributors / future per-workspace MCP servers compose against these.

---

*Plan authored 2026-04-25 in interactive session per "plan before code" CDC. Builder dispatches consume sections §4a + §4b + §11 as the per-amendment scope; this umbrella governs ordering + cross-amendment composition.*

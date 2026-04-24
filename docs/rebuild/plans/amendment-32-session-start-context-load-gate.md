# Plan — Amendment: session-start context-load gate (D8)

**Amendment number:** unassigned at authoring time (assigned at
build-dispatch per owner ruling 2026-04-24).
**BASELINE (pre-amendment tip):** captured at dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored:** 2026-04-24.
**Component scope:** `primary-persona-loader` (the persona layer) +
test-fixture helpers only.
**Research plan:** `docs/rebuild/plans/research/session-start-context-load-gate-research-plan.md`
**Research doc:** `docs/rebuild/plans/research/session-start-context-load-gate-research.md`
**Sibling cycle:** D7 memory-consumer-wiring; both land against a
shared persona-layer `additionalContext`-contributor surface. Builder
owns whether the shared `ComposedContextPayload` composer is
introduced by this amendment or D7 (see §8 halt triggers).

---

## 1. Owner rulings summary (binding, treat as scope)

- **D-1 component-set source.** Relevance is computed from the
  per-component declaration each proposal already carries (research
  §3.3 variant B). No static persona-config mapping; no
  capabilities-map dependency.
- **D-2 refusal shape — GRACEFUL.** Missing / partial corpus emits a
  loud-diagnostic `additionalContext` with structured reason; session
  proceeds. NOT a `UserPromptSubmit` hard-block. `graceful
  degradation` is the governing pOS philosophy.
- **D-3 split.** Two sibling amendments (D7 + D8). D8 delivers the
  context-load gate + shared-composer entry points + session-level
  contributor; D7 registers the memory-retrieval contributor.
- **Gate location.** Primary-persona layer (confirmed by research).
- **Shared-emitter layer.** Two entry points: `on_session_start`
  (corpus refs + service state + amendment list + cost-headroom)
  and `on_user_prompt_submit` (D7's memory-retrieval contributor
  lives here; D8's corpus payload is NOT re-emitted per turn).
- **Empirical Claude Code constraints.** `SessionStart` cannot
  structurally refuse; `continue: false` kills the session and is
  not the tool for this. `UserPromptSubmit` supports
  `decision: "block"` but D-2 forbids use of it here.
  `additionalContext` capped at 10,000 chars — baseline payload is
  paths + metadata, not corpus content.
- **Cold-start budget.** Research measured 2–7 ms warm / 104 ms with
  live services / ~1.5 s worst-case. Must stay well inside the
  existing 20 s supervisor budget.

---

## 2. Objective

The session-start injection surface of the primary-persona layer
emits a structured `additionalContext` payload on every `SessionStart`
that (a) references the workspace-baseline corpus by path, (b) carries
the enumerated session-level state (service state, in-flight
amendments, cost-headroom, corpus-gate sentinel), and (c) degrades
gracefully with a loud structured diagnostic when any baseline path
is missing. A shared persona-layer composer exposes a companion
`on_user_prompt_submit` entry point that D7's turn-level contributor
writes against; invoking that entry point on a session whose
`SessionStart` payload was not emitted is not representable because
the shared composer refuses to construct a turn payload without a
session-level sentinel in scope.

---

## 3. Hard constraints

1. **Dependency fence — persona layer only.** Amends
   `primary-persona/` (source + tests) plus test-fixture helpers.
   Any edit to another sealed component's source is a halt trigger.
   The supervisor stanza in `.claude/settings.json` (owned by
   hands-off-lifecycle / true-first-run) is not modified here;
   composition with it is out of D8's scope.
2. **Reversibility.** Fully reversible. The shared composer is a new
   primitive; no existing persona surface is retracted.
3. **Budget.** Cold-start p95 on warm caches stays inside the
   research-measured envelope (2–7 ms assembly; 104 ms with live
   service probes). Worst-case ~1.5 s with a timed-out probe is
   allowed; any invocation exceeding the 20 s supervisor budget is
   a halt trigger.
4. **`additionalContext` cap.** Serialised payload size is bounded
   at construction; exceeding 10,000 characters is structurally
   refused at the composer layer, not after-the-fact at the hook.
5. **No `--amend`.** Corrective commits only.
6. **No method prescription for D7.** This amendment commits to a
   `ComposedContextPayload` contract with two entry points; it does
   not enumerate the turn-payload fields D7 populates.
7. **ODD §2.5.** Every code path, branch, dependency, and test in
   the diff maps back to an AC. Builder audits in both directions
   before seal.
8. **Graceful degradation governs refusals.** No
   `UserPromptSubmit` hard-block; no `continue: false`. Structured
   diagnostic + session proceeds.

---

## 4. Acceptance criteria

Each AC is outcome-shaped, deterministic, and test-shaped per
ODD §3. Criterion IDs use the `D8.N` namespace to avoid collision
with prior amendment AC sequences; the builder's tests name
themselves `test_D8_<n>_<slug>`.

### D8.1 — `SessionStart` additionalContext emission, paths-and-metadata baseline

On a workspace whose baseline corpus is present, a single invocation
of the persona-layer session-start composer returns an
`additionalContext`-shaped payload whose serialised form contains:
(a) the baseline corpus paths listed in `CLAUDE.md`'s session-start
discipline section, each associated with a file-present indicator,
(b) any in-flight `amendment-*.md` paths under
`docs/rebuild/plans/`, (c) service-state fields for the memory
sidecar and orchestrator, (d) cost-governance month-to-date + ceiling
headroom, (e) a `corpus_gate_state` sentinel with value `loaded`,
`partial`, or `missing`, and (f) a recent-first-run-completion
timestamp plus generation marker. The serialised payload's byte
length is strictly less than 10,000 characters in the baseline
workspace shape.

### D8.2 — Graceful refusal on missing corpus

On a workspace where at least one baseline corpus path is absent, the
session-start composer returns an `additionalContext` payload whose
`corpus_gate_state` sentinel is `partial` or `missing` and whose
body names every missing baseline path in a structured diagnostic
block. The session proceeds — the composer does not raise and does
not request `continue: false`. A subsequent `on_user_prompt_submit`
invocation on the same session observes the `missing` / `partial`
sentinel via the shared composer and does not block the turn — D7
and any other contributors receive the sentinel and may choose to
narrow their own contribution, but the gate itself issues no
structural refusal.

### D8.3 — `UserPromptSubmit` contributor dispatch

The shared composer exposes an `on_user_prompt_submit` entry point
that accepts a user prompt + resolved-component hint + optional
memory-client handle and returns a turn-payload object carrying the
session-level sentinel plus a registered-contributor collection.
Invoking the entry point on a process whose session-level payload
was never composed is not representable — the composer refuses at
construction. The turn-payload surface exposes a registration
mechanism a sibling amendment (D7) can bind a memory-retrieval
contributor to without amending D8's scope. D8 itself registers no
turn-level contributor; the corpus baseline is session-level only.

### D8.4 — Cold-start latency within budget

On a warm filesystem cache with the memory sidecar and orchestrator
reachable, ten consecutive invocations of the session-start composer
against a live baseline corpus complete with a p95 wall-time of
at most 500 ms. With a memory-sidecar probe forced to time out at
its configured budget, the single-shot wall-time remains strictly
below the 20 s supervisor hook budget.

### D8.5 — Shared-composer contract (D7 sibling consumer)

A `ComposedContextPayload` primitive is exposed at the persona-layer
surface with two entry points (`on_session_start`,
`on_user_prompt_submit`) and a registration surface for
`additionalContext` contributors. The primitive refuses at
construction when the serialised payload produced by any entry
point would exceed 10,000 characters. A synthetic turn-level
contributor registered in the test fixture and invoked via
`on_user_prompt_submit` has its contribution observable in the
returned turn-payload — the registration-and-invocation path is
exercised end-to-end without any D7 amendment being present.

### D8.S — Seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths under
`primary-persona/`,
`docs/rebuild/plans/amendment-session-start-context-load-gate*`,
`docs/rebuild/plans/research/session-start-context-load-gate-*`,
and paths admitted under primary-persona-loader's existing
allowed-prefix set plus universal-paths admissions. Anything
outside that set is a halt condition.

### 4.1 Behaviour-count check

| Behaviour declared in §2 | AC coverage |
|---|---|
| Session-start emission references baseline corpus + session-state | D8.1 |
| Graceful refusal on missing corpus (loud-diagnostic; session proceeds) | D8.2 |
| `UserPromptSubmit` contributor-dispatch surface exists and is D7-bindable | D8.3, D8.5 |
| Cold-start stays inside budget on warm cache | D8.4 |
| Shared composer's 10 k-char cap is structural (not advisory) | D8.5 |
| Seal diff bounded to persona layer + plan artefacts | D8.S |

Six behaviours; six criteria; one per declared behaviour.

---

## 5. Implementation order (suggested, builder's call to refine)

1. Read the mandatory session-start corpus. Read the D8 research doc
   and research plan. Read D7's research doc for the turn-payload
   shape D7 will register against.
2. Capture pre-amendment BASELINE tip. Run `primary-persona/` full
   suite (pre-touch green). Run seal-diff-only tests across every
   other sealed component (untouched-component discipline per the
   amendment-dispatch CDC).
3. Introduce the `ComposedContextPayload` shared composer primitive
   with the two entry points and the contributor-registration
   surface. Structurally enforce the 10 k-char cap at construction.
4. Implement D8's session-level payload assembly — corpus-path
   listing, in-flight amendment discovery, service-state probe, cost
   headroom readout, sentinel computation. Graceful refusal path
   materialises the sentinel + diagnostic block.
5. Author tests for D8.1–D8.5 + D8.S. One test function per
   criterion; test names map 1:1 to the ID.
6. Run `primary-persona/` full suite post-touch. Run seal-diff-only
   tests across every other sealed component.
7. Run `pos-amend apply --dry-run` — hard prereq per amendment #22.
8. Amendment commit (not `--amend`).
9. Run `pos-amend seal` to advance sidecars + append narrative.
10. Seal commit. Re-run seal-diff-only tests across every sealed
    component (post-seal verification only; full-suite rerun skipped
    per amendment-dispatch CDC).

---

## 6. Out of scope

- Hard-block refusal via `UserPromptSubmit` `decision: "block"`
  (forbidden by D-2). Gate never blocks.
- Session-start memory retrieval — turn-level, D7's amendment.
- Schema changes to per-component proposal declarations that source
  D-1's relevance computation. Field additions would be their own
  amendment.
- Any edit outside `primary-persona/` + test-fixture helpers. The
  supervisor script at `orchestrator/scripts/pos_session_start.py`
  is not modified here.
- Claude-capabilities-map composition (research §3.3 variant C) —
  deferred.
- Static persona-config `{component → doc_set}` mapping (variant
  A) — ruled out by D-1.
- Skill-based delivery of the gate. The gate's structural contract
  lives in the persona-layer primitive; skill-wrapping of
  interpretive guidance remains possible as future work.
- Cross-session persistence of the corpus-gate sentinel — sentinel
  is session-scoped, recomputed each `SessionStart`.
- D7's turn-payload fields. D8 exposes the registration surface
  only.

---

## 7. Halt triggers

1. **ODD break.** An AC cannot be satisfied without
   method-in-acceptance or non-objective code.
2. **Cross-component scope expansion** beyond
   `primary-persona/` + test-fixture helpers.
3. **Shared-composer ownership ambiguity with D7** — D7 landed first
   with an incompatible `ComposedContextPayload` contract.
4. **Cold-start budget exceeded** — warm-cache p95 above 500 ms, or
   any single-shot invocation above the 20 s supervisor budget.
   Payload trimming is the first proposed mitigation; budget
   widening is the owner's call.
5. **`additionalContext` 10 k-char cap breached** by a realistic
   baseline-workspace payload — the baseline list is the question,
   not the cap enforcement.
6. **Claude Code hook contract drift** between research and build
   time on `SessionStart` / `UserPromptSubmit` / `additionalContext`.
7. **`pos-amend apply --dry-run` fails.**

---

## 8. Bookkeeping surface

- **Manifest components:** `primary-persona-loader` — the only
  sealed component this amendment amends.
  `seal_test: primary-persona/tests/test_no_sealed_amendments.py`,
  `sidecar: primary-persona/tests/SEAL_COMMIT`,
  `frozen_baseline: false` (floating-BASELINE per amendment #23
  convention).
- **Universal-paths admissions.** Plan + research docs under
  `docs/rebuild/plans/`. `CLAUDE.md`, `docs/odd-methodology.md`,
  `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md` included on
  the universal-paths allow-list.
- **Narrative target.** Primary-persona seal-narrative sidecar
  (builder's call which specific sidecar file under
  `primary-persona/seals/` — convention per the component's existing
  narrative layout).
- **Error codes.** Any new failure-mode codes reuse the
  persona-layer's existing error-code namespace; no new code-range
  allocation as part of this amendment.
- **FUTURE_IDEAS.md Idea 8 retirement.** On seal, append a forwarding
  reference to Idea 8 pointing at this amendment's plan + the
  component that now owns the gate (per the catalogue-discipline
  rule at the bottom of `FUTURE_IDEAS.md`).

---

## 9. Dispatch-time CDC adherence

- **Plan-before-code** + **research-before-plan** satisfied by this
  plan and the cited research doc.
- **Scope-only dispatch.** Builder owns file paths, symbol names,
  test names, commit wording, and the serialisation shape of the
  `additionalContext` payload.
- **Background-agent-default.** Execution dispatches to a
  background agent; plan authoring stays in the main session.
- **Amendment-dispatch speedups (amendment #22 + #26 CDCs).**
  Full-suite runs scoped to `primary-persona/`; other sealed
  components get seal-diff-only. Pre-seal full-suite rerun skipped;
  post-seal verification is seal-diff-only. Methodology excerpts
  inlined in the dispatch prompt.
- **529 overload recovery.** Corrective commits only; never
  `--amend`.
- **Session-start corpus.** Builder reads the mandatory corpus per
  `CLAUDE.md` session-start-discipline before authoring.

# Context-Management — SEE / BUDGET / EVICTION-DISCIPLINE (master plan)

> **Status:** master plan-doc (ODD-shaped). Splits into three sub-plans, one per
> shippable cycle. PLAN ONLY — no build dispatched off this doc until the owner
> greenlights each cycle in order.
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent objective:** AC.PO.1 + AC.PO.2 (prime objective — per-user-tuned
> translation + the protection floor — `docs/VALUE_PROPOSITION.md`).
> **Research artefact (load-bearing):**
> `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-context-management-research-2026-06-05.md`
> (LIVE-web-sourced 2026-06-05; trust-banded; re-verify capability claims before each cycle's build).
> **Owner ratification:** Luke 2026-06-05 (Telegram 13853 thread) — BUILD the SEE
> layer + context-budget + eviction-discipline; SKIP the API auto-clear path
> (stay subscription-only); lean-mode is PLAN-ONLY (documented-deferred §7).
> **Quality bar:** every AC outcome-shaped; ≥1 outcome-altitude AC per built
> component; method stays the builder's call per ODD §1.1 + the scope-only-dispatch CDC.

---

## §1 Summary / TL;DR

**What ships (three cycles, in dependency order):**

1. **Cycle 1 — SEE layer (sensor).** A new `context-management` framework
   component carrying (a) a stdlib-only statusline script that parses Claude
   Code's stdin `context_window` JSON envelope every turn and writes a live
   context meter to `<workspace>/.loam/context-meter.json`, and (b) a `read()`
   production entry-point that returns the live occupancy reading (or a
   fail-open "unavailable" sentinel). This is the sensor loam is missing today —
   the exact analog of `usage-window-guard`'s token-budget read, for the
   *context* window. **HIGH confidence, tight scope, independently shippable.**

2. **Cycle 2 — context budget.** A budget computation in the same component:
   occupancy-vs-ceiling-with-reserves math (`remaining = window − reserve_out −
   reserve_work − occupied`), with measured thresholds (<60% / 60–85% / >85% /
   >92%). It feeds the *measured* number into the existing `strategic-compact`
   SKILL's branch-1 estimate step, retiring the "utilization isn't directly
   exposed as a number → heuristic only" honest-limit at
   `plugins/loam-skills/skills/strategic-compact/SKILL.md:143-144`. **HIGH-MEDIUM
   confidence; depends on Cycle 1's sensor.**

3. **Cycle 3 — eviction discipline.** The achievable substitute for the
   runtime-forbidden "strike out specific content": a `context-hygiene`
   discipline SKILL in `loam-skills` encoding input-discipline (cap tool-return
   size, keep MCP deferred), fork-by-default for noisy read work, and
   externalize-early — the three runtime-legal doors that together produce the
   *effect* of evicting content that was never resident. **MEDIUM confidence;
   discipline + composition, not a deterministic mechanism.**

**AC families:** `AC.CTXSEE.*` (Cycle 1), `AC.CTXBUD.*` (Cycle 2),
`AC.CTXEVICT.*` (Cycle 3). Each family carries ≥1 outcome-altitude AC.

**Key decisions baked at plan-author time (full register §10):**
- **Stay subscription-only; SUBSTITUTE for the forbidden delete-message**
  (★OWNER-resolved per Luke 2026-06-05). The plan requires no Anthropic API key
  and nothing on the `context-management-2025-06-27` / `compact_20260112` beta
  path. Per `feedback_no_anthropic_api_key`.
- **NEW `context-management` framework component, not an extension of an existing
  one** (Rec, not owner-gated — §2 + §10 D-CTX.COMPONENT).
- **Context budget uses occupancy-vs-ceiling math, NOT the token-budget `/n`
  even-pacing formula** (not owner-gated; research §5.2 explicit).
- **Lean-mode (32k pure-local fallback) is PLAN-ONLY** (★OWNER-resolved —
  documented-deferred §7, no build scope).

**F2 on scope realism:** Cycle 1 is genuinely tight (the statusline-script +
file-writer pattern is already proven in-repo at
`framework/hands-off-lifecycle/hooks/statusline.py`, and the live-read +
fail-open + outcome-altitude shape is proven at
`framework/usage-window-guard/`). Cycle 3 is the soft one — a discipline SKILL's
"outcome" is a behavioural disposition, not a deterministic branch, so its
outcome-altitude AC tests a *composition surface* (the fork primitive actually
keeps tool calls out of the caller's window), not a behaviour. Named honestly in
§10 F2.

---

## §2 Placement decisions (extend-vs-new)

| Surface | Placement | Rationale |
|---|---|---|
| SEE-layer statusline script + meter file writer + `read()` entry-point | **NEW component `framework/context-management/`** | No existing component owns "read the live context window." The closest twin, `usage-window-guard`, reads the *token* (rolling-cap) window — a sibling concern, not the same surface; co-locating would conflate two different live-reads with different sources (OAuth-usage endpoint vs statusline stdin JSON) under one seal. A new component gives the sensor its own fence + seal test + outcome-altitude AC, mirroring `usage-window-guard`'s clean shape. |
| Context-budget math (occupancy / reserves / thresholds) | **Same NEW component `context-management`** (Cycle 2) | The budget is a pure function of the sensor's reading; it belongs with the sensor, exactly as `usage-window-guard` carries both `read()` and the window model together. |
| Feeding the measured number into the compact decision | **EXTEND `plugins/loam-skills/skills/strategic-compact/SKILL.md`** (Cycle 2) | The decision rubric already exists; Cycle 2 replaces its branch-1 "infer heuristically" step with "read the measured number from the context budget." Doc/SKILL edit, not new mechanism. |
| Eviction discipline (input-discipline / fork-by-default / externalize-early) | **NEW SKILL `plugins/loam-skills/skills/context-hygiene/`** (Cycle 3) | Discipline that the persona applies; the auto-discoverable SKILL is the correct primitive (same graduation pattern as `strategic-compact`). Composes with `precompact-hook` + `loam-spawn-isolation`. |
| Lean-mode dispatch-budget gate + lean-brief shaping | **DEFERRED — documented plan only (§7)** | Owner ruling 2026-06-05: plan-only for the pure-local fallback case; no build scope. |

**Net component count for the build:** one new framework component
(`context-management`, Cycles 1+2) + one extended SKILL + one new SKILL in the
existing `loam-skills` component (Cycle 3).

---

## §3 Predecessors / context

- **`framework/usage-window-guard/`** — the structural twin. The
  context-management `read()` entry-point mirrors its
  `usage_window_guard.probe.read()` shape: real production default path, injectable
  transport for fixtures, fail-open sentinel on any failure, outcome-altitude AC
  exercising the real path with no pre-arranged state (`AC.USG.S`). **Re-read
  before Cycle 1 build.**
- **`framework/hands-off-lifecycle/hooks/statusline.py`** — the proven
  statusline-script pattern: stdlib-only, reads stdin JSON envelope, fail-closed
  exit 0, never raises/blocks/spams. The SEE-layer script mirrors this contract.
- **`plugins/loam-skills/skills/strategic-compact/SKILL.md`** — the decision
  rubric Cycle 2 feeds the measured number into. The honest-limit seam to retire
  is at lines 143–144 + 171 + 254.
- **`plugins/loam-skills/skills/precompact-hook/SKILL.md`** — composes with Cycle
  3 (block + log at PreCompact; cannot steer the summary on the subscription
  path — research §2.3 F2 correction).
- **`loam-spawn-isolation`** (per research §1 / contingency-plan §3.2) — the
  fork/subagent isolation muscle Cycle 3's fork-by-default discipline points at.
- **`feedback_no_anthropic_api_key`** — the reason the API context-editing path
  is skipped, not deferred-for-later.

**BASELINE per cycle:** walked at apply-time from the canonical-clean
pre-amendment HEAD (per the #142 D-PASH.BASELINE-WALK pattern the manifests use).
Amendment numbers assigned at apply-time — the global counter sits at ~#183 as
of 2026-06-05; do NOT pre-bake a number (per `feedback_version_numbers_at_release_time`).

---

## §4 Spec-objective placement (ladder-up)

The whole build ladders to **AC.PO.1 + AC.PO.2** (the two VALUE_PROPOSITION
tests, which are the prime objective's ACs per
`feedback_value_proposition_as_prime_objective`):

- **AC.PO.1 (per-user-tuned translation):** the persona today *guesses* context
  pressure and surfaces a heuristic. The SEE layer + budget turn that guess into
  a measured number, so the persona translates the user's real-world need ("is
  this session about to lose state / get expensive / degrade?") into a grounded,
  honest answer instead of a hedge. Lens 2 primary-persona test: YES — reduces
  the translation burden from "trust my guess" to "here is the measured number."
- **AC.PO.2 (the protection floor — guard the known AI failure modes):** "no real
  memory / breaks the surrounding work" is the betrayal context-management guards.
  Eviction discipline (externalize-early + fork-isolate) is the intra-session
  mirror of the memory-system's cross-session protection: it keeps load-bearing
  state from being silently compacted away. Lens 2 harness test: YES — adds a
  read-occupancy sensor + a context budget + a hygiene discipline to the toolkit.

No new spec clause is required: this is load-bearing wiring under existing
objectives (re-extension per ODD §4), the same shape as amendment #49's
statusline build.

---

## §5 Acceptance criteria (per cycle — full text in each sub-plan)

Each cycle's sub-plan carries its full AC table. Summary of families + the
outcome-altitude AC per family:

**Cycle 1 — `AC.CTXSEE.*`** (sub-plan
`context-management-see-budget-eviction-c1-see.md`):
- `AC.CTXSEE.1` — given a stdin envelope carrying a `context_window` object, the
  script writes a meter file containing the occupancy reading (percentage +
  token counts + window size + timestamp).
- `AC.CTXSEE.2` — given a stdin envelope with NO `context_window` field
  (older CC version / missing), the script writes/leaves an "unavailable"
  sentinel and exits 0 (fail-open; never fabricates a number).
- `AC.CTXSEE.3` — `read()` returns the live occupancy reading from the meter
  file, or an "unavailable" sentinel on any failure (mirrors
  `usage-window-guard` fail-open).
- `AC.CTXSEE.S` — **OUTCOME-ALTITUDE:** invoking the production statusline entry
  with a realistic `context_window` envelope and no pre-arranged meter file
  produces a meter file whose occupancy reading equals the envelope's reported
  occupancy. No fixture state pre-staged.

**Cycle 2 — `AC.CTXBUD.*`** (sub-plan
`context-management-see-budget-eviction-c2-budget.md`):
- `AC.CTXBUD.1` — `remaining` is computed as `window − reserve_out −
  reserve_work − occupied`; given a known reading, the computed remaining +
  occupancy-percentage match the arithmetic.
- `AC.CTXBUD.2` — the threshold classifier maps a reading to exactly one band
  (<60% continue / 60–85% externalize-early / >85% recommend compact / >92% hard
  surface).
- `AC.CTXBUD.3` — the `strategic-compact` SKILL's decision step consumes the
  measured occupancy (the branch-1 "infer heuristically" honest-limit text is
  replaced by "read the measured number; fall back to heuristic only when the
  sensor reports unavailable").
- `AC.CTXBUD.S` — **OUTCOME-ALTITUDE:** a cold session reading that crosses 85%
  occupancy, fed through the production budget path with no pre-arranged state,
  yields the compact-recommendation band off the MEASURED number — not a guess.

**Cycle 3 — `AC.CTXEVICT.*`** (sub-plan
`context-management-see-budget-eviction-c3-eviction.md`):
- `AC.CTXEVICT.1` — the `context-hygiene` SKILL is discoverable (valid
  frontmatter; reachable via the `_symlink_plugin_skills` walk) and its body
  carries the three doors (input-discipline / fork-by-default / externalize-early)
  + the F2 note that delete-message is not a runtime primitive on the
  subscription path.
- `AC.CTXEVICT.2` — the SKILL names its composition surfaces:
  `loam-spawn-isolation` (fork), `precompact-hook` (block+log, cannot steer
  summary), the context budget (the >60% trigger for externalize-early).
- `AC.CTXEVICT.S` — **OUTCOME-ALTITUDE:** an empirical probe shows that work run
  in an isolated fork does NOT add its tool-call tokens to the caller's
  `context_window` occupancy reading — i.e. the fork lever actually keeps content
  out (verifies research §7's UNVERIFIED token-attribution doubt before the
  discipline relies on it). RED if the probe shows fork tokens leaking into the
  parent reading.

**Method-in-AC test (ODD §2.5):** each AC above is satisfiable by methods other
than the one I have in mind (the meter file format, the budget data structure,
the SKILL prose, the probe harness are all the builder's call). None states HOW.
Confirmed outcome-shape.

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

Per the scope-only-dispatch CDC, the dispatch carries scope; method stays the
builder's. Each cycle's sub-plan + manifest drives `loam amend apply` +
`loam amend seal`. Per-cycle shape:

1. **Cycle 1 (SEE):** new `framework/context-management/` package (mirror
   `usage-window-guard`'s `src/loam/context_management/` layout); statusline
   entry-point script + meter writer + `read()`; one-file-per-AC tests; apply via
   the cycle's manifest; seal; HARD-smoke ride-along only at the minor's last
   cycle per `feedback_hard_smoke_per_minor_before_publish`.
2. **Cycle 2 (budget):** budget function + threshold classifier in the same
   component; edit `strategic-compact` SKILL branch-1 (consume measured number,
   keep heuristic fallback for the unavailable sentinel); tests; apply; seal.
3. **Cycle 3 (eviction):** new `context-hygiene` SKILL package; the fork-isolation
   empirical probe test; apply; seal.

Dispatches are serialized in the same tree (per `feedback_serialize_amendment_builds`);
SEE-layer (Cycle 1) is independently shippable and may publish before Cycles 2–3
are authored. Each sealed-component dispatch explicitly names `loam amend apply`
as the bookkeeping mechanism (per `feedback_dispatch_explicit_loam_amend_apply`).

---

## §7 Lean-mode (32k pure-local fallback) — DOCUMENTED-DEFERRED (plan only, no build)

**Owner ruling (Luke 2026-06-05):** lean-mode is for the **purely-local,
no-external-LLM fallback** (privacy / outage / last-resort), and the want is a
**PLAN, not a build**. It is NOT in the build scope above. Captured here so the
plan is durable (per `feedback_durable_capture_for_planned_work`).

**The shape, when it is built (future cycle, separate greenlight):**

- **Verdict (research §4, F2 stress-test):** medium shift, concentrated in
  dispatch/routing — NOT a harness rewrite. Do not run the rich primary loop in
  32k; run a big-context orchestrator that dispatches narrow, self-contained
  small-context worker passes (extract / transform / regression) that never
  needed the whole context. loam is already pointed here (contingency-plan §4c;
  Lens-5 swarming).
- **The two genuinely-new primitives:** (1) a **dispatch-time context-budget
  gate** — estimate a pass's required context; refuse / repartition if
  `required_context > worker.window − reserve` (this is Cycle 2's budget math
  pointed at a *worker* window instead of the *session* window — direct reuse);
  (2) **lean self-contained brief shaping** — carry the slice inline, strip the
  worker's resident load (function-not-persona, the Client SDK path).
- **Reuse:** repartition (Lens-5 decompose) + strip-resident-MCP
  (`ENABLE_TOOL_SEARCH` keep-deferred) already exist.
- **Gate before trusting it:** the 32k-worker reliability benchmark
  (contingency-plan) is a prerequisite — research §7 marks 32k-worker
  reliability for loam's structured passes as PLAUSIBLE-not-verified. Do not
  dispatch real lean-mode work until that benchmark runs.
- **Dual-use note:** the dispatch-budget gate cuts frontier cost TODAY (sizing
  worker dispatches), so when it is greenlit it is not lean-mode-only spend.

---

## §8 Out of scope (build)

- **The API / SDK context-editing path** (`clear_tool_uses_20250919`,
  `compact_20260112`, the `context-management-2025-06-27` beta header) — skipped
  by owner ruling, not deferred. loam has no Anthropic API key
  (`feedback_no_anthropic_api_key`); the substitute is externalize-early +
  fork-isolate + deliberate-compact.
- **Arbitrary "strike out message X" deletion** — the runtime forbids it on the
  subscription path (research §2.1). Substituted by the eviction discipline.
- **Steering what `/compact` summarizes** — API-only (`compact_20260112`); the
  PreCompact hook can block + log but cannot steer the summary on the
  subscription path (research §2.3 F2 correction).
- **Autonomous `/compact` / `/clear` firing** — stays owner-class (per the
  `strategic-compact` D-COMPACT.TRIGGER lock); Cycle 2 supplies the measured
  number to the rubric, it does NOT auto-fire.
- **Per-category context composition view** (the `/context` breakdown) — research
  marks the per-category programmatic read PLAUSIBLE-not-verified (§7); Cycle 1
  ships the VERIFIED top-line occupancy only. Per-category is a future enhancement
  contingent on verifying the read.
- **Lean-mode build** (§7 — plan only).
- **The 32k-worker reliability benchmark** (a separate research/build, gates
  lean-mode).

---

## §9 Halt triggers (in-flight — abort the build + surface)

1. **WD drift** — any cycle's build not confirmed `cd /Users/lukeivers/loam`
   before source edits → halt.
2. **`context_window` field absent from the live statusline envelope** — if a
   Tier-0 check of the real CC version's statusline stdin (min-version 2.1.132
   per research §2.2) shows no `context_window` object, the sensor's premise
   fails → halt + surface (the SEE layer cannot be built against a field that
   isn't there). Verify empirically before Cycle 1 source edits.
3. **Fork token-attribution probe (AC.CTXEVICT.S) shows fork tokens leak into the
   parent reading** — research §7 flags this UNVERIFIED. If the probe shows
   leakage, the fork-by-default lever's premise is wrong → halt Cycle 3 + surface
   (the discipline would over-promise).
4. **An AC about to be authored is method-in-AC and can't be reframed
   outcome-shape** → halt (per the plan-author halt-and-surface discipline).
5. **A fence would touch a sealed component without a manifest entry** → halt
   rather than silently widen.
6. **Research capability claim fails re-verification** (surfaces move weekly per
   research §9) — if the statusline JSON schema, microcompact behaviour, or
   PreCompact block contract has changed at build time → halt + re-research.

---

## §10 Method-decision register + F2 Ruthless Feedback

### Named decisions (recommendations are decisions on in-scope authorized work)

- **D-CTX.SUBSCRIPTION (★OWNER — RESOLVED 2026-06-05).** Stay subscription-only;
  substitute fork/externalize/compact for the forbidden delete-message. *Ruled:
  YES (Luke).* The plan requires no API key / beta header. Per
  `feedback_no_anthropic_api_key`.
- **D-CTX.COMPONENT (Rec — not owner-gated).** New `framework/context-management/`
  component rather than extending `usage-window-guard` or `observability-aggregator`.
  *Rec: NEW.* Different live-read source (statusline stdin vs OAuth-usage endpoint),
  different window (context vs rolling-cap); co-locating conflates two seals.
  Mirrors the clean `usage-window-guard` shape. Builder may surface a counter at
  build time if the package boilerplate proves to dominate.
- **D-CTX.BUDGET-MATH (Not owner-gated).** Occupancy-vs-ceiling-with-reserves,
  NOT the token-budget `/n` even-pacing formula. *Ruled: occupancy-vs-ceiling*
  (research §5.2 explicit — context is occupancy-vs-ceiling, not time-paced; copy
  the live-read + reserve-floor + threshold SHAPE, not the even-pacing proof).
- **D-CTX.RESERVES (Rec — not owner-gated, builder-tunable).** `reserve_out`
  ≈ 15% (output + next-turn growth); `reserve_work` for in-flight growth. *Rec:
  start at research §5.2's 15% reserve_out; expose as named constants so the band
  is tunable without a code rewrite.* The exact percentages are the builder's
  call; the AC tests the arithmetic, not the constant.
- **D-CTX.THRESHOLDS (Rec — not owner-gated).** <60% continue / 60–85%
  externalize-early / >85% recommend compact / >92% hard surface. *Rec: adopt
  research §5.2's bands; they align with the existing `strategic-compact`
  60/85 split so the measured number drops into the rubric without re-deriving
  the thresholds.*
- **D-CTX.COMPACT-TRIGGER (Not owner-gated — inherited lock).** Manual
  `/compact` / `/clear` stays owner-class; microcompact = always-on cheap floor;
  Cycle 2 feeds the measured number to the rubric, does NOT auto-fire. Per the
  existing D-COMPACT.TRIGGER lock.
- **D-CTX.LEAN-MODE (★OWNER — RESOLVED 2026-06-05).** Lean-mode is plan-only
  (§7), documented-deferred, no build scope. *Ruled: PLAN ONLY (Luke).*

**No remaining ★OWNER decisions block the build.** Both genuinely-his calls
(subscription-substitute; lean-mode-plan-only) are resolved. The remaining
decisions are builder-tunable recommendations stated as decisions.

### F2 Ruthless Feedback — honest doubts + design risks

1. **Cycle 3's "outcome" is soft.** A discipline SKILL has no deterministic
   branch to test — its value is a behavioural disposition. I have made its
   outcome-altitude AC test a *composition surface* (the fork lever actually
   keeps tokens out — `AC.CTXEVICT.S`) rather than a behaviour, which is the
   honest version. But the SKILL's *real* payoff (the persona actually forks
   noisy work by default) is unmeasurable in a seal test. Name this when
   dispatching Cycle 3: its confidence is MEDIUM and its AC tests the lever's
   mechanics, not the discipline's adoption.
2. **The fork token-attribution claim is UNVERIFIED (research §7 + §10
   halt-trigger 3).** The whole "fork = zero main-window cost" premise rests on a
   claim the research itself marks unverified. `AC.CTXEVICT.S` is deliberately the
   verifier: if it fails, the eviction discipline's highest-leverage lever
   evaporates and Cycle 3 must be re-scoped to externalize-early + input-discipline
   only. Do NOT let Cycle 3 ship without this probe going green.
3. **Per-category context view is NOT in scope and the user may expect it.**
   Luke's ask was "see what's in context." Cycle 1 delivers the top-line
   occupancy number (VERIFIED), not the per-category breakdown
   (system/MCP/memory/skills/messages — PLAUSIBLE-not-verified, research §7). If
   the user's mental picture is the `/context` pie-chart, the SEE layer will feel
   thinner than expected on first contact. Recommend surfacing this gap to Luke at
   Cycle 1 dispatch so the expectation is set: "measured occupancy %, not the
   per-category breakdown — that's a verified-then-build follow-on."
4. **Re-verify before each build.** Research §9 warns these surfaces move weekly.
   The statusline `context_window` schema, microcompact semantics, and the
   PreCompact block-only contract are all live-sourced 2026-06-05. Each cycle's
   dispatch must carry a "re-verify the load-bearing capability claim against the
   live doc first" instruction (per `feedback_high_trust_content_requires_per_claim_fetch`,
   instanced for capability claims).
5. **No disagreement with the owner framing.** The owner's rulings
   (subscription-substitute, lean-mode-plan-only) are well-founded and match the
   research's own F2 verdicts. Nothing to push back on at the framing level.

---

## §11 Provenance trail

- Research artefact (all capability claims + trust bands):
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-context-management-research-2026-06-05.md`
  (§2 capabilities, §5 layer design, §6 named decisions, §7 honest doubts, §9 sources).
- Statusline-script pattern: `framework/hands-off-lifecycle/hooks/statusline.py`
  (stdlib-only, stdin JSON, fail-closed exit 0).
- Live-read twin: `framework/usage-window-guard/src/loam/usage_window_guard/probe.py`
  (`read()` production entry-point, fail-open sentinel, `AC.USG.S` outcome-altitude shape).
- Compact rubric + honest-limit seam: `plugins/loam-skills/skills/strategic-compact/SKILL.md`
  (lines 143–144 / 171 / 254 — "utilization isn't directly exposed as a number").
- PreCompact composition: `plugins/loam-skills/skills/precompact-hook/SKILL.md`.
- Skill-component seal pattern: `docs/plans/strategic-compact-skill-graduation.manifest.yaml`
  (loam-skills component shape; apply-time number; BASELINE-walk).
- Statusline-component seal pattern: `docs/plans/bootstrap-progress-statusline.manifest.yaml`
  (amendment #49 — the in-repo statusline build).
- Plan-doc conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- Prime-objective ladder: `docs/VALUE_PROPOSITION.md` (AC.PO.1 / AC.PO.2);
  `feedback_value_proposition_as_prime_objective`.
- Governing memory rules: `feedback_no_anthropic_api_key`,
  `feedback_version_numbers_at_release_time`, `feedback_scope_descriptive_ac_ids`,
  `feedback_test_outcome_altitude_required`, `feedback_serialize_amendment_builds`,
  `feedback_dispatch_explicit_loam_amend_apply`, `feedback_durable_capture_for_planned_work`.

---

## §14 Method-decision register (per-cycle, populated at build time)

Each cycle's sub-plan carries its own §14 populated by the builder + SHA-backfilled
by `loam amend seal --plan-doc`. This master plan's §10 holds the plan-author-time
decisions; the build-time D-build.* decisions live in the sub-plans.

## §15 Backwards-compat verification

- Cycle 1: no existing component touched; new `context-management` package only.
  The statusline script is additive — it composes onto the CC `statusLine`
  primitive without displacing the existing `hands-off-lifecycle` first-run
  statusline (different workspace state; verify no `statusLine` settings
  collision at build time).
- Cycle 2: `strategic-compact` SKILL edit is additive to branch-1 (heuristic
  fallback retained for the unavailable sentinel — no existing AC.COMPACT.* test
  regresses). `loam-skills` seal test (`test_no_sealed_amendments.py`) must pass.
- Cycle 3: new SKILL package only; `_symlink_plugin_skills` discoverability of
  existing SKILLs unchanged.

## §16 Halt-and-surface findings (plan-authoring)

- **Resolved at author time:** both ★OWNER decisions (subscription-substitute;
  lean-mode-plan-only) carry the 2026-06-05 Luke ruling. No owner gate blocks the
  build.
- **Surfaced for Cycle-dispatch attention (not blocking):** F2 items 1–4 above —
  Cycle 3 softness, the unverified fork-attribution claim (gated by
  `AC.CTXEVICT.S`), the per-category expectation gap, and the re-verify-before-build
  obligation.
